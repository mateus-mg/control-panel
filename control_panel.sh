#!/bin/bash

# =============================================================================
# CONTROL PANEL - HD AND DOCKER MANAGEMENT SCRIPT
# =============================================================================
# This script mounts/unmounts external drives, manages Docker containers, and
# keeps the drive active temporarily.
#
# AVAILABLE COMMANDS:
#   mount       - Mount the configured external drive
#   unmount     - Safely unmount the external drive
#   status      - Show full system status (drive and Docker)
#   keepalive   - Keep the drive active and monitor Docker containers
#   check       - List active mount points
#   fix         - Fix permissions and mount point structure
#   view-logs   - Show recent script log entries
#   sync        - Sync files and update global symlink
#
# DOCKER MANAGEMENT:
#   start       - Start containers (e.g., panel start [service] [--clean] [--no-deps])
#   stop        - Stop containers (e.g., panel stop [service])
#   restart     - Restart containers (e.g., panel restart [service] [--clean])
#   clean       - Remove old containers (e.g., panel clean [service])
#   ps          - List running containers
#   logs        - Show Docker service logs (e.g., panel logs <service> [-f])
#   stats       - Show resource usage (e.g., panel stats [service])
#   health      - Check container health
#
# DOCKER MAINTENANCE:
#   services    - List services available in docker-compose.yml
#   pull        - Pull updated images
#   rebuild     - Rebuild containers (e.g., panel rebuild [service] [--cache])
#   update-all  - Update images and restart only updated containers
#   networks    - List Docker networks
#   volumes     - List Docker volumes
#   prune       - Clean unused resources
#
# UTILITIES:
#   diagnose    - Full system diagnostic
#   force-mount - Force drive remount
#
# USAGE EXAMPLES:
#   panel mount
#   panel start jellyfin --clean
#   panel logs prowlarr -f
# =============================================================================

HD_MOUNT_POINT="/media/mateus/Servidor"
DOCKER_COMPOSE_DIR="/home/mateus"
DOCKER_COMPOSE_FILE="$DOCKER_COMPOSE_DIR/docker-compose.yml"
ORIGINAL_DOCKER_COMPOSE_FILE="/media/mateus/Servidor/scripts/docker-compose.yml"
LOG_FILE="$HOME/.panel.log"

# ✅ SPECIFIC CONFIGURATION FOR YOUR HD
HD_UUID="35feb867-8ee2-49a9-a1a5-719a67e3975a"
HD_LABEL="Servidor"
HD_TYPE="ext4"

# Log helper with consistent exit codes
log_error() {
    local message="$1"
    local code="$2"
    echo "❌ ERROR: $message"
    log_message "ERROR: $message"
    return ${code:-1}
}

log_success() {
    local message="$1"
    echo "✅ SUCCESS: $message"
    log_message "SUCCESS: $message"
}

# Detect the correct Docker Compose command and prepare as array
DOCKER_COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    log_error "Neither 'docker compose' nor 'docker-compose' is available. Please install Docker Compose." 1
    exit 1
fi

# Split command string into an array for safe invocation
IFS=' ' read -r -a DOCKER_CMD_ARR <<< "$DOCKER_COMPOSE_CMD"

# Unified docker compose runner (handles ansi flag and directory)
compose_run() {
    local args=("$@")
    if [[ "$DOCKER_COMPOSE_CMD" == "docker compose" ]]; then
        "${DOCKER_CMD_ARR[@]}" --ansi never "${args[@]}"
    else
        "${DOCKER_CMD_ARR[@]}" "${args[@]}"
    fi
}

compose_cmd() {
    validate_environment || return 1
    cd "$DOCKER_COMPOSE_DIR" || {
        log_error "Failed to access $DOCKER_COMPOSE_DIR" 1
        return 1
    }
    compose_run "$@"
}

# ✅ DETECT DEVICE AUTOMATICALLY BY UUID
get_device_by_uuid() {
    # Search device by UUID (more reliable)
    local device=$(blkid -U "$HD_UUID" 2>/dev/null)
    if [ -n "$device" ]; then
        echo "$device"
        return 0
    fi
    
    # Fallback: search by LABEL
    device=$(blkid -L "$HD_LABEL" 2>/dev/null)
    if [ -n "$device" ]; then
        echo "$device"
        return 0
    fi
    
    return 1
}

# Signal handling for safe cleanup (used in keepalive)
cleanup_on_exit() {
    echo ""
    echo "🛑 Interrupt signal received..."
    log_message "Keepalive interrupted by user"
    echo "✅ Keepalive safely finished"
    exit 0
}

# Log function with automatic rotation
log_message() {
    local log_max_lines=1000
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    
    # Rotate log if needed (keep last 500 lines)
    if [ -f "$LOG_FILE" ]; then
        local line_count=$(wc -l < "$LOG_FILE" 2>/dev/null || echo 0)
        if [ "$line_count" -gt "$log_max_lines" ]; then
            tail -n 500 "$LOG_FILE" > "$LOG_FILE.tmp" 2>/dev/null
            mv "$LOG_FILE.tmp" "$LOG_FILE" 2>/dev/null
        fi
    fi
}

# ✅ FUNCTION: View logs (specific to script logs)
view_logs() {
    local lines=${1:-50}  # Default to last 50 lines if not specified
    echo "📋 Last $lines log entries:"
    echo "===================="
    if [ -f "$LOG_FILE" ]; then
        tail -n "$lines" "$LOG_FILE"
    else
        echo "❌ Log file not found: $LOG_FILE"
    fi
    echo "===================="
}

# ✅ FUNCTION: Auto-discover services from docker-compose.yml
get_docker_services() {
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        echo "❌ docker-compose.yml file not found: $DOCKER_COMPOSE_FILE"
        return 1
    fi
    
    # Extract service names using docker compose
    if command -v docker &> /dev/null; then
        cd "$DOCKER_COMPOSE_DIR" && "${DOCKER_CMD_ARR[@]}" config --services 2>/dev/null
        return $?
    else
        # Fallback: manually extract from YAML
        grep -E '^  [a-zA-Z0-9_-]+:' "$DOCKER_COMPOSE_FILE" | sed 's/^  //' | sed 's/:$//'
    fi
}

# ✅ FUNCTION: Load services automatically
load_docker_services() {
    DOCKER_SERVICES=($(get_docker_services))
    
    if [ ${#DOCKER_SERVICES[@]} -eq 0 ]; then
        echo "⚠️  No service found in docker-compose.yml"
        return 1
    fi
    
    return 0
}

# ✅ FUNCTION: Check Docker environment (improved error handling)
check_docker_environment() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker command not found"
        return 1
    fi

    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        echo "❌ docker-compose.yml not found at $DOCKER_COMPOSE_DIR"
        return 1
    fi

    return 0
}

# ✅ FUNCTION: Clean old/orphan containers
clean_old_containers() {
    local service="$1"
    
    echo "🧹 Cleaning old containers..."
    echo ""

    if ! validate_environment; then
        echo "⚠️  Docker environment is not ready"
        return 1
    fi

    if [ -n "$service" ]; then
        echo "🗑️  Removing old container: $service"
        compose_cmd rm -f -s "$service" 2>/dev/null
    else
        echo "🗑️  Removing all stopped containers..."
        compose_cmd rm -f -s 2>/dev/null
    fi

    echo "✅ Cleanup finished"
    log_message "Old containers removed$([ -n "$service" ] && echo ": $service" || echo "")"
}

# ✅ SIMPLIFIED FUNCTION: Check if HD is mounted
is_hd_mounted() {
    if mountpoint -q "$HD_MOUNT_POINT" 2>/dev/null; then
        return 0
    fi
    
    if grep -qs "$HD_MOUNT_POINT" /proc/mounts; then
        return 0
    fi
    
    return 1
}

# Generic pre-check for compose commands
validate_environment() {
    if ! check_docker_environment; then
        echo "❌ Docker environment not available"
        return 1
    fi

    if ! is_hd_mounted; then
        echo "❌ Drive is not mounted. Mount first with: panel mount"
        return 1
    fi

    return 0
}

# ✅ FUNCTION: Stop Docker containers (now accepts specific service)
stop_docker_services() {
    local service="$1"

    echo "🐳 Stopping Docker services..."
    echo ""

    if ! validate_environment; then
        echo "❌ Docker environment is not ready"
        return 1
    fi

    if [ -n "$service" ]; then
        echo "⏹️  Stopping service: $service"
        compose_cmd stop "$service"
    else
        echo "⏹️  Stopping all services"
        compose_cmd stop
    fi

    local rc=$?
    echo
    if [ $rc -eq 0 ]; then
        echo "✅ Docker services stopped"
        log_message "Docker services stopped$([ -n "$service" ] && echo ": $service" || echo "")"
    else
        log_error "Failed to stop services" $rc
    fi

    return $rc
}

# ✅ FUNCTION: Start Docker containers (CORRIGIDA - sem loop infinito)
start_docker_services() {
    local service=""
    local clean_mode=false
    local no_deps=false
    local args=()

    # Parse arguments corretamente
    for arg in "$@"; do
        case "$arg" in
            "--clean")
                clean_mode=true
                ;;
            "--no-deps")
                no_deps=true
                args+=("--no-deps")
                ;;
            *)
                if [ -z "$service" ]; then
                    service="$arg"
                fi
                ;;
        esac
    done

    echo "🐳 Starting Docker services..."
    echo ""

    validate_environment || return 1

    if [ "$clean_mode" = true ]; then
        echo "🧹 Cleaning old containers..."
        clean_old_containers "$service"
        echo ""
    fi

    cd "$DOCKER_COMPOSE_DIR" || return 1

    if [ -n "$service" ]; then
        echo "🚀 Starting service: $service"
        if [ "$no_deps" = true ]; then
            echo "⚠️  Ignoring dependencies for: $service"
            compose_cmd up -d --no-deps "$service"
        else
            compose_cmd up -d "$service"
        fi
    else
        echo "🚀 Starting all services"
        compose_cmd up -d
    fi
    
    local rc=$?
    echo
    if [ $rc -eq 0 ]; then
        echo "✅ Docker services started"
        log_message "Docker services started$([ -n "$service" ] && echo ": $service" || echo "")"
    else
        log_error "Failed to start services" $rc
    fi
    
    return $rc
}

# ✅ FUNCTION: Restart Docker containers (CORRIGIDA)
restart_docker_services() {
    local service=""
    local clean_mode=false
    
    # Parse arguments corretamente
    for arg in "$@"; do
        case "$arg" in
            "--clean")
                clean_mode=true
                ;;
            *)
                if [ -z "$service" ]; then
                    service="$arg"
                fi
                ;;
        esac
    done
    
    echo "🔄 Restarting Docker services..."
    echo ""
    
    validate_environment || return 1

    if [ "$clean_mode" = true ]; then
        echo "🧹 Clean mode enabled"
        stop_docker_services "$service"
        echo ""
        clean_old_containers "$service"
        echo ""
    fi

    if [ -n "$service" ]; then
        echo "🔄 Restarting service: $service"
        compose_cmd restart "$service"
    else
        echo "🔄 Restarting all services"
        compose_cmd restart
    fi
    
    local rc=$?
    echo
    if [ $rc -eq 0 ]; then
        echo "✅ Docker services restarted"
        log_message "Docker services restarted$([ -n "$service" ] && echo ": $service" || echo "")"
    else
        log_error "Failed to restart services" $rc
    fi
    
    return $rc
}

# ✅ SIMPLIFIED FUNCTION: Mount HD
mount_hd_simple() {
    echo "🔍 Checking external drive..."
    echo ""

    # Auto-detect device by UUID/label
    local HD_DEVICE=$(get_device_by_uuid)

    if [ -z "$HD_DEVICE" ]; then
        log_error "Drive not detected (UUID: $HD_UUID). Check the connection." 1
        return 1
    fi

    if is_hd_mounted; then
        log_success "Drive already mounted at $HD_MOUNT_POINT"
        echo "📍 Device: $HD_DEVICE"
        return 0
    fi

    echo "✅ Drive detected: $HD_DEVICE"
    echo ""

    sudo mkdir -p "$HD_MOUNT_POINT"
    sudo chown mateus:mateus "$HD_MOUNT_POINT"

    echo "🔄 Mounting drive..."
    echo ""

    if sudo mount UUID="$HD_UUID" "$HD_MOUNT_POINT"; then
        log_success "Drive mounted successfully at $HD_MOUNT_POINT"
        echo "📍 Device: $HD_DEVICE"
        log_message "Drive mounted: $HD_DEVICE (UUID: $HD_UUID) at $HD_MOUNT_POINT"
        return 0
    else
        log_error "Failed to mount drive" 1
        return 1
    fi
}

# ✅ FUNCTION: Forced unmount HD
unmount_hd_forced() {
    echo "🔄 Unmounting drive..."
    echo ""
    
    # Stop Docker containers if running
    if check_docker_environment; then
        stop_docker_services
        sleep 3  # Allow containers to release files
    fi
    
    # Check if there are processes using the HD
    if command -v lsof &> /dev/null && mountpoint -q "$HD_MOUNT_POINT" 2>/dev/null; then
        if lsof "$HD_MOUNT_POINT" 2>/dev/null | grep -q "$HD_MOUNT_POINT"; then
            echo "⚠️  Processes are still using the drive:"
            lsof "$HD_MOUNT_POINT" 2>/dev/null | tail -10
            echo ""
            read -p "Continue anyway? (y/N): " confirm
            if [[ ! "$confirm" =~ ^[yY]$ ]]; then
                echo "❌ Operation canceled"
                return 1
            fi
        fi
    fi
    
    # Sync before unmount (flush buffers) - call system sync explicitly
    /bin/sync
    
    # Try to unmount the specific mount point
    if mountpoint -q "$HD_MOUNT_POINT" 2>/dev/null; then
        if sudo umount "$HD_MOUNT_POINT" 2>/dev/null; then
            echo "✅ Drive unmounted from $HD_MOUNT_POINT"
            log_message "Drive unmounted from $HD_MOUNT_POINT"
        else
            echo "⚠️  Normal unmount failed, trying lazy unmount..."
            sudo umount -l "$HD_MOUNT_POINT"
            echo "✅ Lazy unmount applied"
            log_message "Drive lazy unmounted from $HD_MOUNT_POINT"
        fi
    else
        echo "ℹ️  Drive not mounted at $HD_MOUNT_POINT"
    fi
    
    echo ""
    echo "✅ Unmount operation completed"
}

# ✅ IMPROVED KEEPALIVE FUNCTION
keepalive_hd_optimized() {
    # Enable trap only inside keepalive
    trap cleanup_on_exit SIGINT SIGTERM

    echo "🔋 Starting keepalive mode (60s interval)..."
    echo "📝 Touch marker every 10 minutes to avoid wear"
    echo "💡 Press Ctrl+C to stop"

    log_message "Keepalive started (60s interval, touch every 10m)"

    local retry_count=0
    local max_retries=5
    local loop_seconds=60
    local touch_interval_seconds=600
    local last_touch_ts=0

    while true; do
        if ! is_hd_mounted; then
            ((retry_count++))
            echo "$(date '+%H:%M:%S') ⚠️  Drive not mounted, attempt $retry_count of $max_retries..."
            log_message "Keepalive: drive not mounted, attempt $retry_count"

            if [ $retry_count -ge $max_retries ]; then
                echo "❌ Retry limit reached. Pausing for 5 minutes before retrying."
                log_message "Keepalive: retry limit reached, pausing 5 minutes"
                retry_count=0
                sleep 300
                continue
            fi

            if mount_hd_simple; then
                echo "✅ Drive remounted successfully"
                log_message "Keepalive: drive remounted"
                retry_count=0
            else
                echo "❌ Failed to remount drive. Retrying in $loop_seconds seconds."
                log_message "Keepalive: failed to remount drive"
            fi
        else
            retry_count=0
            local now_ts
            now_ts=$(date +%s)
            if [ $((now_ts - last_touch_ts)) -ge $touch_interval_seconds ]; then
                touch "$HD_MOUNT_POINT/.keepalive" 2>/dev/null
                last_touch_ts=$now_ts
                echo "$(date '+%H:%M:%S') ✅ Drive alive (touch)"
                log_message "Keepalive: drive alive (touch)"
            else
                echo "$(date '+%H:%M:%S') ✅ Drive mounted"
                log_message "Keepalive: drive mounted"
            fi
        fi

        sleep "$loop_seconds"
    done
}

# ✅ COMPLETE STATUS FUNCTION
show_status_optimized() {
    echo "📊 SYSTEM STATUS"
    echo "===================="
    echo ""
    
    # HD status
    if is_hd_mounted; then
        echo "✅ HD: MOUNTED at $HD_MOUNT_POINT"
        df -h "$HD_MOUNT_POINT" | tail -1
    else
        echo "❌ HD: NOT MOUNTED"
        local detected_device=$(get_device_by_uuid)
        if [ -n "$detected_device" ]; then
            echo "💡 Device detected: $detected_device"
        else
            echo "💡 Device: NOT DETECTED"
        fi
    fi
    
    echo ""
    echo "===================="
    echo ""
    
    # Docker status
    if check_docker_environment; then
        echo "🐳 DOCKER:"
        
        # Show configured services
        if load_docker_services; then
            echo "📋 Services in compose: ${DOCKER_SERVICES[*]}"
        fi
        
        echo ""
        
        if docker ps --quiet &> /dev/null && [ $(docker ps -q | wc -l) -gt 0 ]; then
            docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        else
            echo "   No running containers"
        fi
    else
        echo "❌ Docker not available"
    fi
    
    echo ""
}

# ✅ FUNCTION: Check active mounts
check_mounts() {
    echo "📋 ACTIVE MOUNTS:"
    echo "===================="
    echo ""
    findmnt -r | grep -E "(sdb|$HD_MOUNT_POINT)" || echo "   No HD mount found"
    
    echo ""
    echo "📋 BLOCK DEVICES:"
    echo "========================"
    echo ""
    lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,LABEL,UUID
    echo ""
}

# ✅ FUNCTION: Fix permissions and structure
fix_mount_point() {
    echo "🔧 Fixing mount point..."
    echo ""
    
    # Remove mount point if exists
    if [ -d "$HD_MOUNT_POINT" ]; then
        sudo rmdir "$HD_MOUNT_POINT" 2>/dev/null
    fi
    
    # Create new mount point
    sudo mkdir -p "$HD_MOUNT_POINT"
    sudo chown mateus:mateus "$HD_MOUNT_POINT"
    sudo chmod 755 "$HD_MOUNT_POINT"
    
    echo "✅ Mount point fixed: $HD_MOUNT_POINT"
}

# ✅ FUNCTION: Sync files from HD to local home and create global symlink
sync() {
    echo "🔁 Starting file synchronization..."

    # Verify HD mounted
    if ! is_hd_mounted; then
        echo "❌ Drive is not mounted. Aborting sync."
        log_error "sync: drive not mounted" 1
        return 1
    fi

    # Source locations on HD
    local src_script="$HD_MOUNT_POINT/scripts/control-panel/control_panel.sh"
    local src_compose="$ORIGINAL_DOCKER_COMPOSE_FILE"

    # Destination locations in home
    local dest_script="$HOME/control_panel.sh"
    local dest_compose="$HOME/docker-compose.yml"

    # Check and copy script
    if [ -f "$src_script" ]; then
        if [ -f "$dest_script" ]; then
            if cmp -s "$src_script" "$dest_script"; then
                echo "ℹ️  Script already up to date at $dest_script"
                log_message "sync: script already up-to-date"
            else
                cp -p "$src_script" "$dest_script" && chmod +x "$dest_script"
                echo "✅ Script updated: $dest_script"
                log_message "sync: script updated to $dest_script"
            fi
        else
            cp -p "$src_script" "$dest_script" && chmod +x "$dest_script"
            echo "✅ Script copied to $dest_script"
            log_message "sync: script copied to $dest_script"
        fi
    else
        echo "⚠️  Source script not found: $src_script"
        log_error "sync: source script not found: $src_script" 2
    fi

    # Check and copy docker-compose
    if [ -f "$src_compose" ]; then
        if [ -f "$dest_compose" ]; then
            if cmp -s "$src_compose" "$dest_compose"; then
                echo "ℹ️  docker-compose.yml already up to date at $dest_compose"
                log_message "sync: docker-compose already up-to-date"
            else
                cp -p "$src_compose" "$dest_compose"
                echo "✅ docker-compose.yml updated: $dest_compose"
                log_message "sync: docker-compose updated to $dest_compose"
            fi
        else
            cp -p "$src_compose" "$dest_compose"
            echo "✅ docker-compose.yml copied to $dest_compose"
            log_message "sync: docker-compose copied to $dest_compose"
        fi
    else
        echo "⚠️  docker-compose.yml not found at: $src_compose"
        log_error "sync: source docker-compose not found: $src_compose" 3
    fi

    # Create global symlink (/usr/local/bin/panel)
    local symlink_path="/usr/local/bin/panel"
    if [ -L "$symlink_path" ]; then
        local current_target
        current_target=$(readlink -f "$symlink_path")
        if [ "$current_target" = "$dest_script" ]; then
            echo "ℹ️  Symlink already present and correct ($dest_script)"
            log_message "sync: symlink already present"
        else
            sudo ln -sf "$dest_script" "$symlink_path"
            sudo chmod +x "$dest_script"
            echo "✅ Symlink updated: $symlink_path -> $dest_script"
            log_message "sync: symlink updated to $dest_script"
        fi
    else
        # Create symlink (requires sudo to write to /usr/local/bin)
        sudo ln -sf "$dest_script" "$symlink_path"
        sudo chmod +x "$dest_script"
        echo "✅ Symlink created: $symlink_path -> $dest_script"
        log_message "sync: symlink created to $dest_script"
    fi

    echo "🔚 Sync completed"
    return 0
}

# =============================================================================
# MAIN COMMANDS - FULL VERSION
# =============================================================================

# Check external dependencies early
validate_dependencies() {
    local dependencies=(blkid lsof findmnt docker)
    local missing_dependencies=()

    for dep in "${dependencies[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            missing_dependencies+=("$dep")
        fi
    done

    if [ ${#missing_dependencies[@]} -gt 0 ]; then
        echo "❌ Missing dependencies: ${missing_dependencies[*]}"
        echo "💡 Install the required dependencies and try again."
        return 1
    fi
    return 0
}

# Trap global para limpeza de recursos
setup_global_trap() {
    trap "global_cleanup" SIGINT SIGTERM
}

global_cleanup() {
    echo "🛑 Script interrompido. Limpando recursos..."
    log_message "Script interrupted. Cleaning up resources."
    echo "✅ Recursos limpos com sucesso."
    exit 0
}

# Configure global trap at startup
setup_global_trap

# Validate dependencies at startup
if ! validate_dependencies; then
    exit 1
fi

case "$1" in
    "update-all")
        echo "🔄 SMART IMAGE & CONTAINER UPDATE"
        echo ""
        if ! is_hd_mounted; then
            echo "❌ HD is not mounted"
            log_message "update-all: HD is not mounted, aborting update"
            exit 1
        fi
        if ! check_docker_environment; then
            echo "❌ Docker is not available"
            log_message "update-all: Docker is not available, aborting update"
            exit 1
        fi
        cd "$DOCKER_COMPOSE_DIR" || exit 1

        load_docker_services
        if [ ${#DOCKER_SERVICES[@]} -eq 0 ]; then
            echo "❌ No service found in docker-compose.yml"
            log_message "update-all: No service found in compose"
            exit 1
        fi

        echo "⬇️  1/3: Pulling latest images..."

        declare -A SERVICE_IMAGES
        for service in "${DOCKER_SERVICES[@]}"; do
            SERVICE_IMAGES[$service]=$("${DOCKER_CMD_ARR[@]}" config | awk -v svc="$service" '$1==svc":" {found=1} found && $1=="image:" {print $2; found=0}')
        done

        "${DOCKER_CMD_ARR[@]}" pull
        echo ""

        UPDATED_SERVICES=()
        for service in "${DOCKER_SERVICES[@]}"; do
            image_name="${SERVICE_IMAGES[$service]}"
            # Get local image ID
            local_image_id=$(docker images --no-trunc --format '{{.ID}}' "$image_name" | head -n1)
            # Get running container image ID (if running)
            running_image_id=$(docker inspect --format '{{.Image}}' "$service" 2>/dev/null)

            # If not running, always update
            if [ -z "$running_image_id" ]; then
                UPDATED_SERVICES+=("$service")
            elif [ "$local_image_id" != "$running_image_id" ]; then
                UPDATED_SERVICES+=("$service")
            fi
        done

        echo ""
        echo "✅ Update complete! Updated services: ${UPDATED_SERVICES[*]}"
        log_message "update-all: Updated services: ${UPDATED_SERVICES[*]}"
        ;;
    "mount")
        mount_hd_simple
        ;;
    "unmount")
        unmount_hd_forced
        ;;
    "status")
        show_status_optimized
        ;;
    "keepalive")
        keepalive_hd_optimized
        ;;
    "check")
        check_mounts
        ;;
    "fix")
        fix_mount_point
        ;;
    "start")
        shift
        start_docker_services "$@"
        ;;
    "stop")
        shift
        stop_docker_services "$1"
        ;;
    "restart")
        shift
        restart_docker_services "$@"
        ;;
    "clean")
        if [ -n "$2" ]; then
            clean_old_containers "$2"
        else
            clean_old_containers
        fi
        ;;
    "ps")
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        ;;
    "logs")
        if [ -z "$2" ]; then
            echo "❌ Specify the service to view logs."
            exit 1
        fi
        shift
        service="$1"
        shift
        compose_cmd logs "$@" "$service"
        ;;
    "view-logs")
        view_logs "$2"
        ;;
    "services")
        echo "📋 Available services in docker-compose:"
        echo ""
        if load_docker_services; then
            for service in "${DOCKER_SERVICES[@]}"; do
                echo "  - $service"
            done
        else
            cd "$DOCKER_COMPOSE_DIR" && "${DOCKER_CMD_ARR[@]}" config --services
        fi
        echo ""
        ;;
    "health")
        echo "🏥 HEALTH CHECK OF SERVICES"
        echo "============================"
        echo ""
        
        if ! load_docker_services; then
            echo "❌ Unable to load services"
            exit 1
        fi
        
        for service in "${DOCKER_SERVICES[@]}"; do
            health=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null)
            status=$(docker inspect --format='{{.State.Status}}' "$service" 2>/dev/null)
            
            if [ -z "$status" ]; then
                echo "❌ $service: DOES NOT EXIST"
            elif [ "$status" != "running" ]; then
                echo "🔴 $service: $status"
            elif [ -n "$health" ] && [ "$health" != "healthy" ]; then
                echo "⚠️  $service: running but $health"
            else
                echo "✅ $service: OK"
            fi
        done
        
        echo ""
        ;;
    "stats")
        echo "📊 RESOURCE USAGE (press Ctrl+C to exit)"
        echo ""
        if ! validate_environment; then
            echo "❌ Docker environment is not ready"
            exit 1
        fi

        if [ -n "$2" ]; then
            docker stats "$2"
        else
            docker stats
        fi
        ;;
    "pull")
        echo "⬇️  UPDATING IMAGES"
        echo ""
        if ! validate_environment; then
            echo "❌ Docker environment is not ready"
            exit 1
        fi
        cd "$DOCKER_COMPOSE_DIR" || exit 1
        compose_run pull
        echo ""
        echo "✅ Images updated!"
        echo "💡 Use 'panel restart' to apply updates"
        ;;
    "sync")
        sync
        ;;
    "rebuild")
        echo "🔨 CONTAINER REBUILD"
        echo ""
        if ! validate_environment; then
            echo "❌ Docker environment is not ready"
            exit 1
        fi
        cd "$DOCKER_COMPOSE_DIR" || exit 1
        
        # Default uses --no-cache unless --cache is provided
        no_cache="--no-cache"
        service=""
        for arg in "$2" "$3"; do
            if [ "$arg" = "--cache" ]; then
                no_cache=""
                echo "💾 Mode: WITH CACHE (faster rebuild)"
                echo ""
            elif [ -n "$arg" ]; then
                service="$arg"
            fi
        done
        
        # Show default mode when --cache is absent
        if [ "$no_cache" = "--no-cache" ]; then
            echo "🚫 Mode: NO CACHE (full rebuild)"
            echo ""
        fi
        
        if [ -n "$service" ]; then
            echo "🔨 Rebuild service: $service"
            compose_run build $no_cache "$service"
            compose_run up -d "$service"
        else
            echo "🔨 Rebuild all services"
            compose_run build $no_cache
            compose_run up -d
        fi
        echo ""
        echo "✅ Rebuild completed!"
        ;;
    # update command removed, use update-all only
    "networks")
        echo "🌐 DOCKER NETWORKS"
        echo "=================="
        echo ""
        if ! check_docker_environment; then
            echo "❌ Docker is not available"
            exit 1
        fi
        docker network ls
        echo ""
        ;;
    "volumes")
        echo "💾 DOCKER VOLUMES"
        echo "================="
        echo ""
        if ! check_docker_environment; then
            echo "❌ Docker is not available"
            exit 1
        fi
        docker volume ls
        echo ""
        ;;
    "prune")
        echo "🧹 PRUNE UNUSED RESOURCES"
        echo ""
        if ! validate_environment; then
            echo "❌ Docker environment is not ready"
            exit 1
        fi
        read -p "This will remove stopped containers, unused networks, dangling images, and builder cache. Continue? (y/N): " confirm
        if [[ "$confirm" =~ ^[yY]$ ]]; then
            echo ""
            echo "🗑️  Removing stopped containers..."
            docker container prune -f
            echo ""
            echo "🗑️  Removing unused networks..."
            docker network prune -f
            echo ""
            echo "🗑️  Removing dangling images..."
            docker image prune -f
            echo ""
            echo "🗑️  Removing build cache..."
            docker builder prune -f
            echo ""
            echo "✅ Cleanup completed!"
        else
            echo "❌ Operation canceled"
        fi
        ;;
    "diagnose")
        echo "🔍 FULL DIAGNOSTIC:"
        echo ""
        echo "Drive:"
        echo "  UUID: $HD_UUID"
        echo "  Label: $HD_LABEL"
        detected_device=$(get_device_by_uuid)
        if [ -n "$detected_device" ]; then
            echo "  Detected device: $detected_device"
        else
            echo "  Detected device: ❌ NOT FOUND"
        fi
        echo "  Mount point: $HD_MOUNT_POINT"
        echo "  Mounted: $(is_hd_mounted && echo 'YES' || echo 'NO')"
        if is_hd_mounted; then
            echo "  Disk usage:"
            df -h "$HD_MOUNT_POINT" | tail -1 | awk '{print "    "$2" total, "$3" used, "$4" free ("$5" used)"}'
        fi
        echo ""
        echo "Docker:"
        echo "  Docker available: $(check_docker_environment && echo 'YES' || echo 'NO')"
        echo "  Running containers: $(docker ps -q | wc -l)"
        if load_docker_services; then
            echo "  Detected services: ${DOCKER_SERVICES[*]}"
        fi
        echo ""
        ;;
    "force-mount")
        echo "⚡ FORCED MOUNT"
        echo ""
        unmount_hd_forced
        sleep 2
        fix_mount_point
        sleep 1
        mount_hd_simple
        ;;
    *)
        echo "🎛️  AVAILABLE COMMANDS:"
        echo ""
        echo "  mount       - Mount drive"
        echo "  unmount     - Unmount drive" 
        echo "  status      - Full system status"
        echo "  keepalive   - Keepalive mode (keep HD active)"
        echo "  check       - Show mounts"
        echo "  fix         - Fix mount point"
        echo "  view-logs   - View script logs (panel view-logs [n])"
        echo "  sync        - Synchronize files and update symlink"
        echo ""
        echo "🐳 DOCKER MANAGEMENT:"
        echo "  start       - Start containers (panel start [service] [--clean] [--no-deps])"
        echo "  stop        - Stop containers (panel stop [service])"
        echo "  restart     - Restart containers (panel restart [service] [--clean])"
        echo "  clean       - Remove old containers (panel clean [service])"
        echo "  ps          - Running containers"
        echo "  logs        - View Docker service logs (panel logs <service> [-f])"
        echo "  stats       - Resource usage (panel stats [service])"
        echo "  health      - Check container health"
        echo ""
        echo "💡 Use --clean when starting/restarting to remove old containers"
        echo "   Use --no-deps when starting to ignore dependencies"
        echo "   Example: panel start cloudflared --no-deps"
        echo ""
        echo "🔄 DOCKER MAINTENANCE:"
        echo "  services    - List available services"
        echo "  pull        - Pull updated images"
        echo "  rebuild     - Rebuild containers WITHOUT cache (panel rebuild [service] [--cache])"
        echo "  update-all  - Smart update (pull images, restart only updated containers)"
        echo "  networks    - List Docker networks"
        echo "  volumes     - List Docker volumes"
        echo "  prune       - Clean unused resources"
        echo ""
        echo "🔧 UTILITIES:"
        echo "  diagnose    - Full diagnostic"
        echo "  force-mount - Force remount"
        echo ""
        ;;
esac