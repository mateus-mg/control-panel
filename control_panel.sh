#!/bin/bash

# =============================================================================
# CONTROL PANEL - HD AND DOCKER MANAGEMENT SCRIPT
# =============================================================================
# This script now integrates with the new Python CLI system with Rich interface
# and structured logging. This file remains for backward compatibility and
# as a bridge to the new system.
#
# The new system features:
# - Rich interactive menus
# - Structured logging with rotation
# - Better error handling
# - Improved status reporting
#
# AVAILABLE COMMANDS (forwarded to Python CLI):
#   interactive - Start the new interactive menu
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
#   start       - Start containers (e.g., control-panel start [service] [--clean] [--no-deps])
#   stop        - Stop containers (e.g., control-panel stop [service])
#   restart     - Restart containers (e.g., control-panel restart [service] [--clean])
#   clean       - Remove old containers (e.g., control-panel clean [service])
#   ps          - List running containers
#   logs        - Show Docker service logs (e.g., control-panel logs <service> [-f])
#   stats       - Show resource usage (e.g., control-panel stats [service])
#   health      - Check container health
#
# DOCKER MAINTENANCE:
#   services    - List services available in docker-compose.yml
#   pull        - Pull updated images
#   rebuild     - Rebuild containers (e.g., control-panel rebuild [service] [--cache])
#   update-all  - Update images and restart only updated containers
#   networks    - List Docker networks
#   volumes     - List Docker volumes
#   prune       - Clean unused resources
#
# SYSTEMD MANAGEMENT:
#   keepalive-status    - Check keepalive service status
#   keepalive-start     - Start keepalive service
#   keepalive-restart   - Restart keepalive service
#   keepalive-stop      - Stop keepalive service
#   keepalive-enable    - Enable keepalive service (start on boot)
#   keepalive-disable   - Disable keepalive service
#   keepalive-logs      - View keepalive logs (add -f to follow)
#   service-status      - Check any systemd service status
#   service-start       - Start any systemd service
#   service-restart     - Restart any systemd service
#   service-logs        - View logs for any service (add -f to follow)
#
# UTILITIES:
#   diagnose    - Full system diagnostic
#   force-mount - Force drive remount
#
# USAGE EXAMPLES:
#   control-panel interactive (NEW - recommended)
#   control-panel mount
#   control-panel start jellyfin --clean
#   control-panel logs prowlarr -f
#   control-panel keepalive-status
#   control-panel keepalive-restart
# =============================================================================

HD_MOUNT_POINT="/media/mateus/Servidor"
DOCKER_COMPOSE_DIR="/home/mateus"
DOCKER_COMPOSE_FILE="$DOCKER_COMPOSE_DIR/docker-compose.yml"
ORIGINAL_DOCKER_COMPOSE_FILE="/media/mateus/Servidor/scripts/docker-compose.yml"
LOG_FILE="$HOME/.control-panel.log"
WRAPPER_NAME="control-panel"
LOCAL_BIN_DIR="$HOME/.local/bin"
GLOBAL_SYMLINK="$LOCAL_BIN_DIR/control-panel"
WRAPPER_SYMLINK="$LOCAL_BIN_DIR/$WRAPPER_NAME"

# ✅ SPECIFIC CONFIGURATION FOR YOUR HD
HD_UUID="35feb867-8ee2-49a9-a1a5-719a67e3975a"
HD_LABEL="Servidor"
HD_TYPE="ext4"

# ✅ SYSTEMD SERVICES CONFIGURATION
SYSTEMD_KEEPALIVE_SERVICE="control-panel-keepalive.service"
SYSTEMD_HDAUTO_SERVICE="hdmount.service"
SYSTEMD_USER_MODE=false  # Set to true if using user services, false for system-wide with sudo

# Redirect all commands to the new Python CLI
# This maintains backward compatibility while using the new system
redirect_to_python_cli() {
    # Find the project directory (where this script is located)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR" || exit 1
    
    # Activate virtual environment if it exists
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    # Pass all arguments to the Python CLI manager
    python3 scripts/cli_manager.py "$@"
}

# ✅ LOCAL INSTALLATION CHECK
check_local_installation() {
    if [ ! -f "$HOME/scripts/control_panel.sh" ]; then
        echo "⚠️  WARNING: Local copy not found at ~/scripts/control_panel.sh" >&2
        echo "💡 Run 'control-panel sync' to create a fault‑resistant copy" >&2
        echo ""
    fi
}

# Executar verificação silenciosamente
check_local_installation 2>/dev/null || true

# Log helper with consistent exit codes (maintained for compatibility)
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

# Redirect all commands to the new Python CLI by default
# If no arguments provided, default to interactive mode
if [ $# -eq 0 ]; then
    redirect_to_python_cli "interactive"
else
    redirect_to_python_cli "$@"
fi
exit 0

# =============================================================================
# SYSTEMD MANAGEMENT FUNCTIONS
# =============================================================================

# ✅ FUNCTION: Check systemd service status
check_systemd_service() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        echo "❌ Service name not specified"
        return 1
    fi
    
    echo "🔍 Checking systemd service: $service_name"
    echo "===================="
    
    if command -v systemctl &> /dev/null; then
        if [ "$SYSTEMD_USER_MODE" = true ]; then
            systemctl --user status "$service_name" --no-pager
        else
            sudo systemctl status "$service_name" --no-pager
        fi
    else
        echo "❌ systemctl command not found"
        return 1
    fi
}

# ✅ FUNCTION: Start systemd service
start_systemd_service() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        echo "❌ Service name not specified"
        return 1
    fi
    
    echo "🚀 Starting systemd service: $service_name"
    echo "===================="
    
    if command -v systemctl &> /dev/null; then
        if [ "$SYSTEMD_USER_MODE" = true ]; then
            if systemctl --user start "$service_name"; then
                echo "✅ Service started successfully"
                log_message "Systemd service started: $service_name"
                
                # Show status after starting
                sleep 2
                systemctl --user status "$service_name" --no-pager | head -20
                return 0
            else
                log_error "Failed to start service: $service_name" 1
                return 1
            fi
        else
            if sudo systemctl start "$service_name"; then
                echo "✅ Service started successfully"
                log_message "Systemd service started: $service_name"
                
                # Show status after starting
                sleep 2
                sudo systemctl status "$service_name" --no-pager | head -20
                return 0
            else
                log_error "Failed to start service: $service_name" 1
                return 1
            fi
        fi
    else
        echo "❌ systemctl command not found"
        return 1
    fi
}

# ✅ FUNCTION: Restart systemd service
restart_systemd_service() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        echo "❌ Service name not specified"
        return 1
    fi
    
    echo "🔄 Restarting systemd service: $service_name"
    echo "===================="
    
    if command -v systemctl &> /dev/null; then
        if [ "$SYSTEMD_USER_MODE" = true ]; then
            if systemctl --user restart "$service_name"; then
                echo "✅ Service restarted successfully"
                log_message "Systemd service restarted: $service_name"
                
                # Show status after restarting
                sleep 2
                systemctl --user status "$service_name" --no-pager | head -20
                return 0
            else
                log_error "Failed to restart service: $service_name" 1
                return 1
            fi
        else
            if sudo systemctl restart "$service_name"; then
                echo "✅ Service restarted successfully"
                log_message "Systemd service restarted: $service_name"
                
                # Show status after restarting
                sleep 2
                sudo systemctl status "$service_name" --no-pager | head -20
                return 0
            else
                log_error "Failed to restart service: $service_name" 1
                return 1
            fi
        fi
    else
        echo "❌ systemctl command not found"
        return 1
    fi
}

# ✅ FUNCTION: Stop systemd service
stop_systemd_service() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        echo "❌ Service name not specified"
        return 1
    fi
    
    echo "⏹️  Stopping systemd service: $service_name"
    echo "===================="
    
    if command -v systemctl &> /dev/null; then
        if [ "$SYSTEMD_USER_MODE" = true ]; then
            if systemctl --user stop "$service_name"; then
                echo "✅ Service stopped successfully"
                log_message "Systemd service stopped: $service_name"
                return 0
            else
                log_error "Failed to stop service: $service_name" 1
                return 1
            fi
        else
            if sudo systemctl stop "$service_name"; then
                echo "✅ Service stopped successfully"
                log_message "Systemd service stopped: $service_name"
                return 0
            else
                log_error "Failed to stop service: $service_name" 1
                return 1
            fi
        fi
    else
        echo "❌ systemctl command not found"
        return 1
    fi
}

# ✅ FUNCTION: Enable systemd service (start on boot)
enable_systemd_service() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        echo "❌ Service name not specified"
        return 1
    fi
    
    echo "🔧 Enabling systemd service: $service_name (start on boot)"
    echo "===================="
    
    if command -v systemctl &> /dev/null; then
        if [ "$SYSTEMD_USER_MODE" = true ]; then
            if systemctl --user enable "$service_name"; then
                echo "✅ Service enabled successfully"
                log_message "Systemd service enabled: $service_name"
                return 0
            else
                log_error "Failed to enable service: $service_name" 1
                return 1
            fi
        else
            if sudo systemctl enable "$service_name"; then
                echo "✅ Service enabled successfully"
                log_message "Systemd service enabled: $service_name"
                return 0
            else
                log_error "Failed to enable service: $service_name" 1
                return 1
            fi
        fi
    else
        echo "❌ systemctl command not found"
        return 1
    fi
}

# ✅ FUNCTION: Disable systemd service
disable_systemd_service() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        echo "❌ Service name not specified"
        return 1
    fi
    
    echo "🔧 Disabling systemd service: $service_name"
    echo "===================="
    
    if command -v systemctl &> /dev/null; then
        if [ "$SYSTEMD_USER_MODE" = true ]; then
            if systemctl --user disable "$service_name"; then
                echo "✅ Service disabled successfully"
                log_message "Systemd service disabled: $service_name"
                return 0
            else
                log_error "Failed to disable service: $service_name" 1
                return 1
            fi
        else
            if sudo systemctl disable "$service_name"; then
                echo "✅ Service disabled successfully"
                log_message "Systemd service disabled: $service_name"
                return 0
            else
                log_error "Failed to disable service: $service_name" 1
                return 1
            fi
        fi
    else
        echo "❌ systemctl command not found"
        return 1
    fi
}

# ✅ FUNCTION: Show systemd service logs
show_systemd_logs() {
    local service_name="$1"
    local follow="${2:-false}"
    
    if [ -z "$service_name" ]; then
        echo "❌ Service name not specified"
        return 1
    fi
    
    echo "📋 Systemd logs for: $service_name"
    echo "===================="
    
    if command -v journalctl &> /dev/null; then
        if [ "$follow" = true ]; then
            echo "📡 Following logs in real-time (press Ctrl+C to stop)..."
            echo ""
            if [ "$SYSTEMD_USER_MODE" = true ]; then
                journalctl --user -u "$service_name" -f
            else
                sudo journalctl -u "$service_name" -f
            fi
        else
            if [ "$SYSTEMD_USER_MODE" = true ]; then
                journalctl --user -u "$service_name" --no-pager -n 50
            else
                sudo journalctl -u "$service_name" --no-pager -n 50
            fi
            echo ""
            echo "💡 Use 'control-panel service-logs $service_name -f' to follow logs in real-time"
        fi
    else
        echo "❌ journalctl command not found"
        return 1
    fi
}

# ✅ FUNCTION: Manage keepalive service
manage_keepalive() {
    local action="$1"
    
    case "$action" in
        "status")
            check_systemd_service "$SYSTEMD_KEEPALIVE_SERVICE"
            ;;
        "start")
            start_systemd_service "$SYSTEMD_KEEPALIVE_SERVICE"
            ;;
        "restart")
            restart_systemd_service "$SYSTEMD_KEEPALIVE_SERVICE"
            ;;
        "stop")
            stop_systemd_service "$SYSTEMD_KEEPALIVE_SERVICE"
            ;;
        "enable")
            enable_systemd_service "$SYSTEMD_KEEPALIVE_SERVICE"
            ;;
        "disable")
            disable_systemd_service "$SYSTEMD_KEEPALIVE_SERVICE"
            ;;
        "logs")
            show_systemd_logs "$SYSTEMD_KEEPALIVE_SERVICE" "false"
            ;;
        "logs-follow")
            show_systemd_logs "$SYSTEMD_KEEPALIVE_SERVICE" "true"
            ;;
        *)
            echo "🎛️  KEEPALIVE SERVICE MANAGEMENT"
            echo "================================"
            echo ""
            echo "Commands:"
            echo "  control-panel keepalive-status    - Check keepalive service status"
            echo "  control-panel keepalive-start     - Start keepalive service"
            echo "  control-panel keepalive-restart   - Restart keepalive service"
            echo "  control-panel keepalive-stop      - Stop keepalive service"
            echo "  control-panel keepalive-enable    - Enable service (start on boot)"
            echo "  control-panel keepalive-disable   - Disable service"
            echo "  control-panel keepalive-logs      - View service logs"
            echo "  control-panel keepalive-logs -f   - Follow logs in real-time"
            echo ""
            echo "Current service: $SYSTEMD_KEEPALIVE_SERVICE"
            echo ""
            # Show current status
            if command -v systemctl &> /dev/null; then
                echo "📊 Current status:"
                if [ "$SYSTEMD_USER_MODE" = true ]; then
                    systemctl --user is-active "$SYSTEMD_KEEPALIVE_SERVICE" 2>/dev/null && echo "  Active: ✅ Yes" || echo "  Active: ❌ No"
                    systemctl --user is-enabled "$SYSTEMD_KEEPALIVE_SERVICE" 2>/dev/null && echo "  Enabled: ✅ Yes" || echo "  Enabled: ❌ No"
                else
                    systemctl is-active "$SYSTEMD_KEEPALIVE_SERVICE" 2>/dev/null && echo "  Active: ✅ Yes" || echo "  Active: ❌ No"
                    systemctl is-enabled "$SYSTEMD_KEEPALIVE_SERVICE" 2>/dev/null && echo "  Enabled: ✅ Yes" || echo "  Enabled: ❌ No"
                fi
            fi
            ;;
    esac
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
    echo "🛑 Script interrupted. Cleaning up resources..."
    log_message "Script interrupted. Cleaning up resources."
    echo "✅ Resources cleaned successfully."
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
        echo "💡 Use 'control-panel restart' to apply updates"
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
    # Systemd Service Management Commands
    "keepalive-status")
        manage_keepalive "status"
        ;;
    "keepalive-start")
        manage_keepalive "start"
        ;;
    "keepalive-restart")
        manage_keepalive "restart"
        ;;
    "keepalive-stop")
        manage_keepalive "stop"
        ;;
    "keepalive-enable")
        manage_keepalive "enable"
        ;;
    "keepalive-disable")
        manage_keepalive "disable"
        ;;
    "keepalive-logs")
        if [ "$2" = "-f" ]; then
            manage_keepalive "logs-follow"
        else
            manage_keepalive "logs"
        fi
        ;;
    "service-status")
        check_systemd_service "$2"
        ;;
    "service-start")
        start_systemd_service "$2"
        ;;
    "service-restart")
        restart_systemd_service "$2"
        ;;
    "service-logs")
        if [ "$3" = "-f" ]; then
            show_systemd_logs "$2" "true"
        else
            show_systemd_logs "$2" "false"
        fi
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
        echo -n "This will remove stopped containers, unused networks, dangling images, and builder cache. Continue? (y/N): "
        read confirm
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
        echo "Systemd Services:"
        echo "  Keepalive service: $SYSTEMD_KEEPALIVE_SERVICE"
        echo "  HD Auto-mount service: $SYSTEMD_HDAUTO_SERVICE"
        echo "  Systemd available: $(command -v systemctl &> /dev/null && echo 'YES' || echo 'NO')"
        if command -v systemctl &> /dev/null; then
            if [ "$SYSTEMD_USER_MODE" = true ]; then
                echo "  Keepalive active: $(systemctl --user is-active "$SYSTEMD_KEEPALIVE_SERVICE" 2>/dev/null && echo 'YES' || echo 'NO')"
                echo "  Keepalive enabled: $(systemctl --user is-enabled "$SYSTEMD_KEEPALIVE_SERVICE" 2>/dev/null && echo 'YES' || echo 'NO')"
            else
                echo "  Keepalive active: $(systemctl is-active "$SYSTEMD_KEEPALIVE_SERVICE" 2>/dev/null && echo 'YES' || echo 'NO')"
                echo "  Keepalive enabled: $(systemctl is-enabled "$SYSTEMD_KEEPALIVE_SERVICE" 2>/dev/null && echo 'YES' || echo 'NO')"
            fi
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
        echo "  view-logs   - View script logs (control-panel view-logs [n])"
        echo "  sync        - Synchronize files and update symlink"
        echo ""
        echo "🐳 DOCKER MANAGEMENT:"
        echo "  start       - Start containers (control-panel start [service] [--clean] [--no-deps])"
        echo "  stop        - Stop containers (control-panel stop [service])"
        echo "  restart     - Restart containers (control-panel restart [service] [--clean])"
        echo "  clean       - Remove old containers (control-panel clean [service])"
        echo "  ps          - Running containers"
        echo "  logs        - View Docker service logs (control-panel logs <service> [-f])"
        echo "  stats       - Resource usage (control-panel stats [service])"
        echo "  health      - Check container health"
        echo ""
        echo "🔄 SYSTEMD SERVICE MANAGEMENT:"
        echo "  keepalive-status    - Check keepalive service status"
        echo "  keepalive-start     - Start keepalive service"
        echo "  keepalive-restart   - Restart keepalive service"
        echo "  keepalive-stop      - Stop keepalive service"
        echo "  keepalive-enable    - Enable keepalive service (start on boot)"
        echo "  keepalive-disable   - Disable keepalive service"
        echo "  keepalive-logs      - View keepalive logs (add -f to follow)"
        echo "  service-status      - Check any systemd service status"
        echo "  service-start       - Start any systemd service"
        echo "  service-restart     - Restart any systemd service"
        echo "  service-logs        - View logs for any service (add -f to follow)"
        echo ""
        echo "💡 Use --clean when starting/restarting to remove old containers"
        echo "   Use --no-deps when starting to ignore dependencies"
        echo "   Example: control-panel start cloudflared --no-deps"
        echo ""
        echo "🔄 DOCKER MAINTENANCE:"
        echo "  services    - List available services"
        echo "  pull        - Pull updated images"
        echo "  rebuild     - Rebuild containers WITHOUT cache (control-panel rebuild [service] [--cache])"
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