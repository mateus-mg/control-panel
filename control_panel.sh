#!/bin/bash

# =============================================================================
# CONTROL PANEL - FULL VERSION WITH DOCKER AND KEEPALIVE
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
    echo "📋 Últimos $lines registros do log:"
    echo "===================="
    if [ -f "$LOG_FILE" ]; then
        tail -n "$lines" "$LOG_FILE"
    else
        echo "❌ Arquivo de log não encontrado: $LOG_FILE"
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
        cd "$DOCKER_COMPOSE_DIR" && docker compose config --services 2>/dev/null
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
        log_error "Docker command not found" 127
        return 1
    fi

    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        log_error "docker-compose.yml not found at $DOCKER_COMPOSE_DIR" 1
        return 1
    fi

    return 0
}

# ✅ FUNCTION: Clean old/orphan containers
clean_old_containers() {
    local service="$1"
    
    echo "🧹 Cleaning old containers..."
    echo ""
    
    if ! check_docker_environment; then
        echo "⚠️  Docker not available"
        return 1
    fi
    
    cd "$DOCKER_COMPOSE_DIR" || return 1
    
    # If a specific service was informed
    if [ -n "$service" ]; then
        echo "🗑️  Removing old container: $service"
        docker compose rm -f -s "$service" 2>/dev/null
    else
        echo "🗑️  Removing all stopped containers..."
        docker compose rm -f -s 2>/dev/null
    fi
    
    echo "✅ Cleanup finished"
    log_message "Old containers removed$([ -n "$service" ] && echo ": $service" || echo "")"
}

# Função genérica para validação de pré-requisitos
validate_environment() {
    if ! check_docker_environment; then
        echo "❌ Docker environment not available"
        return 1
    fi

    if ! is_hd_mounted; then
        echo "❌ HD is not mounted. Mount first with: panel mount"
        return 1
    fi

    return 0
}

# Função genérica para executar comandos Docker Compose com validação
execute_docker_compose() {
    local command="$1"
    local service="$2"

    validate_environment || return 1

    cd "$DOCKER_COMPOSE_DIR" || {
        echo "❌ Failed to access $DOCKER_COMPOSE_DIR"
        return 1
    }

    if [ -n "$service" ]; then
        docker compose "$command" "$service"
    else
        docker compose "$command"
    fi
}

# ✅ FUNCTION: Stop Docker containers (now accepts specific service)
stop_docker_services() {
    local service="$1"

    echo "🐳 Stopping Docker services..."
    echo ""
    
    validate_environment || return 1

    execute_docker_compose "stop" "$service" || {
        echo "❌ Failed to stop services"
        return 1
    }

    echo "✅ Docker services stopped"
}

# ✅ FUNCTION: Start Docker containers (improved error handling)
start_docker_services() {
    service=""
    clean_mode=false
    no_deps=false

    # Parse arguments
    for arg in "$@"; do
        if [ "$arg" = "--clean" ]; then
            clean_mode=true
        elif [ "$arg" = "--no-deps" ]; then
            no_deps=true
        elif [ -n "$arg" ]; then
            service="$arg"
        fi
    done

    echo "🐳 Starting Docker services..."
    echo ""

    validate_environment || return 1

    if [ "$clean_mode" = true ]; then
        echo "🧹 Cleaning old containers..."
        clean_old_containers "$service"
    fi

    execute_docker_compose "up -d" "$service" || {
        echo "❌ Failed to start services"
        return 1
    }

    echo "✅ Docker services started"
}

# ✅ FUNCTION: Restart Docker containers (now accepts specific service and --clean flag)
restart_docker_services() {
    service=""
    clean_mode=false
    
    # Parse de argumentos (aceita: service, --clean, ou ambos)
    for arg in "$@"; do
        if [ "$arg" = "--clean" ]; then
            clean_mode=true
        elif [ -n "$arg" ]; then
            service="$arg"
        fi
    done
    
    echo "🔄 Restarting Docker services..."
    echo ""
    
    validate_environment || return 1

    if [ "$clean_mode" = true ]; then
        stop_docker_services "$service"
        clean_old_containers "$service"
    fi

    execute_docker_compose "restart" "$service" || {
        echo "❌ Failed to restart services"
        return 1
    }

    echo "✅ Docker services restarted"
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

# ✅ SIMPLIFIED FUNCTION: Mount HD
mount_hd_simple() {
    echo "🔍 Checking external HD..."
    echo ""
    
    # Automatically detect device by UUID
    local HD_DEVICE=$(get_device_by_uuid)
    
    if [ -z "$HD_DEVICE" ]; then
        echo "❌ HD not detected (UUID: $HD_UUID)"
        echo "💡 Check if the HD is connected: lsblk"
        return 1
    fi
    
    # Check if already mounted
    if is_hd_mounted; then
        echo "✅ HD is already mounted at: $HD_MOUNT_POINT"
        echo "📍 Device: $HD_DEVICE"
        return 0
    fi
    
    echo "✅ HD detected: $HD_DEVICE"
    echo ""
    
    # Create mount point if it doesn't exist
    sudo mkdir -p "$HD_MOUNT_POINT"
    sudo chown mateus:mateus "$HD_MOUNT_POINT"
    
    echo "🔄 Mounting HD..."
    echo ""
    
    # Try to mount by UUID (more reliable)
    if sudo mount UUID="$HD_UUID" "$HD_MOUNT_POINT"; then
        echo "✅ HD successfully mounted at: $HD_MOUNT_POINT"
        echo "📍 Device: $HD_DEVICE"
        log_message "HD mounted: $HD_DEVICE (UUID: $HD_UUID) at $HD_MOUNT_POINT"
        return 0
    else
        echo "❌ Error mounting HD"
        return 1
    fi
}

# ✅ FUNCTION: Forced unmount HD
unmount_hd_forced() {
    echo "🔄 Unmounting HD..."
    echo ""
    
    # Stop Docker containers if running
    stop_docker_services
    sleep 3  # Dar tempo para containers liberarem arquivos
    
    # Check if there are processes using the HD
    if command -v lsof &> /dev/null && mountpoint -q "$HD_MOUNT_POINT" 2>/dev/null; then
        if lsof "$HD_MOUNT_POINT" 2>/dev/null | grep -q "$HD_MOUNT_POINT"; then
            echo "⚠️  Processes are still using the HD:"
            lsof "$HD_MOUNT_POINT" 2>/dev/null | tail -10
            echo ""
            read -p "Continue anyway? (y/N): " confirm
            if [[ ! "$confirm" =~ ^[yY]$ ]]; then
                echo "❌ Operation cancelled"
                return 1
            fi
        fi
    fi
    
    # Sync before unmount (flush buffers) - call system sync explicitly
    /bin/sync
    
    # Try to unmount the specific mount point
    if mountpoint -q "$HD_MOUNT_POINT" 2>/dev/null; then
        if sudo umount "$HD_MOUNT_POINT" 2>/dev/null; then
            echo "✅ HD unmounted from $HD_MOUNT_POINT"
        else
            echo "⚠️  Normal unmount failed, trying lazy unmount..."
            sudo umount -l "$HD_MOUNT_POINT"
            echo "✅ Lazy unmount applied"
        fi
    fi
    
    echo ""
    echo "✅ Unmount operation completed"
}

# ✅ IMPROVED KEEPALIVE FUNCTION
keepalive_hd_optimized() {
    # Enable trap only inside keepalive
    trap cleanup_on_exit SIGINT SIGTERM
    
    echo "🔋 Starting keepalive mode..."
    echo "📝 Monitoring HD and Docker containers every 30 seconds"
    echo "💡 Press Ctrl+C to stop"
    echo ""
    
    log_message "Starting keepalive mode"
    
    # Load services once at the beginning
    load_docker_services
    
    # Counters for optimization
    local retry_count=0
    local max_retries=3
    local touch_counter=0
    
    while true; do
        if ! is_hd_mounted; then
            ((retry_count++))
            
            echo "$(date '+%H:%M:%S') ⚠️  HD not mounted, trying to remount... (attempt $retry_count/$max_retries)"
            log_message "Keepalive: HD not mounted, trying to remount (attempt $retry_count)"
            
            # If failed too many times, pause for 5 minutes
            if [ $retry_count -ge $max_retries ]; then
                echo "❌ ERROR: Failed after $max_retries consecutive attempts"
                echo "⏸️  Pausing for 5 minutes before trying again..."
                log_message "Keepalive: Multiple failures detected, pausing for 5 minutes"
                retry_count=0
                sleep 300  # 5 minutes
                continue
            fi
            
            # Try to mount
            if mount_hd_simple; then
                echo "✅ Successful reconnection!"
                log_message "Keepalive: HD successfully remounted"
                retry_count=0  # Reset counter on success
                
                # Start containers after mounting HD
                start_docker_services
            else
                echo "❌ Reconnection failed, trying again in 30s..."
            fi
        else
            retry_count=0  # Reset counter when HD is mounted
            
            # Touch only every 10 minutes (20 cycles of 30s)
            ((touch_counter++))
            if [ $((touch_counter % 20)) -eq 0 ]; then
                touch "$HD_MOUNT_POINT/.keepalive" 2>/dev/null
            fi
            
            # Check if containers should be running but are not
            if check_docker_environment && [ ${#DOCKER_SERVICES[@]} -gt 0 ]; then
                local stopped_services=()
                
                for service in "${DOCKER_SERVICES[@]}"; do
                    # Use grep -x for exact match (avoid false positives)
                    if ! docker ps --format "{{.Names}}" | grep -qx "$service"; then
                        stopped_services+=("$service")
                    fi
                done
                
                if [ ${#stopped_services[@]} -gt 0 ]; then
                    echo "⚠️  Stopped services detected: ${stopped_services[*]}"
                    echo "🔄 Restarting services..."
                    for service in "${stopped_services[@]}"; do
                        start_docker_services "$service"
                    done
                fi
            fi
            
            echo "$(date '+%H:%M:%S') ✅ HD mounted and active"
        fi
        
        sleep 30
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
        echo "💡 Device: $HD_DEVICE"
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
        
        if docker ps --quiet | read; then
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

# ✅ SAFE FUNCTION FOR DOCKER COMMANDS
docker_compose_safe() {
    local command="$1"
    local service="$2"
    
    if ! check_docker_environment; then
        echo "❌ Docker environment not available"
        return 1
    fi
    
    cd "$DOCKER_COMPOSE_DIR" || {
        echo "❌ Could not access: $DOCKER_COMPOSE_DIR"
        return 1
    }
    
    case "$command" in
        "up")
            if [ -n "$service" ]; then
                docker compose up -d "$service"
            else
                docker compose up -d
            fi
            ;;
        "stop"|"restart"|"logs")
            if [ -n "$service" ]; then
                docker compose "$command" "$service"
            else
                echo "❌ Service not specified."
                return 1
            fi
            ;;
        *)
            docker compose "$command"
            ;;
    esac
}

# ✅ FUNCTION: Sync files from HD to local home and create global symlink
sync() {
    echo "🔁 Iniciando sincronização de arquivos..."

    # Verify HD mounted
    if ! is_hd_mounted; then
        echo "❌ HD não está montado. Abortando sync."
        log_error "sync: HD not mounted" 1
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
                echo "ℹ️  Script já está atualizado em $dest_script"
                log_message "sync: script already up-to-date"
            else
                cp -p "$src_script" "$dest_script" && chmod +x "$dest_script"
                echo "✅ Script atualizado: $dest_script"
                log_message "sync: script updated to $dest_script"
            fi
        else
            cp -p "$src_script" "$dest_script" && chmod +x "$dest_script"
            echo "✅ Script copiado para $dest_script"
            log_message "sync: script copied to $dest_script"
        fi
    else
        echo "⚠️  Script de origem não encontrado: $src_script"
        log_error "sync: source script not found: $src_script" 2
    fi

    # Check and copy docker-compose
    if [ -f "$src_compose" ]; then
        if [ -f "$dest_compose" ]; then
            if cmp -s "$src_compose" "$dest_compose"; then
                echo "ℹ️  docker-compose.yml já está atualizado em $dest_compose"
                log_message "sync: docker-compose already up-to-date"
            else
                cp -p "$src_compose" "$dest_compose"
                echo "✅ docker-compose.yml atualizado: $dest_compose"
                log_message "sync: docker-compose updated to $dest_compose"
            fi
        else
            cp -p "$src_compose" "$dest_compose"
            echo "✅ docker-compose.yml copiado para $dest_compose"
            log_message "sync: docker-compose copied to $dest_compose"
        fi
    else
        echo "⚠️  docker-compose.yml não encontrado em: $src_compose"
        log_error "sync: source docker-compose not found: $src_compose" 3
    fi

    # Create global symlink (/usr/local/bin/panel)
    local symlink_path="/usr/local/bin/panel"
    if [ -L "$symlink_path" ]; then
        local current_target
        current_target=$(readlink -f "$symlink_path")
        if [ "$current_target" = "$dest_script" ]; then
            echo "ℹ️  Symlink já existe e aponta para $dest_script"
            log_message "sync: symlink already present"
        else
            sudo ln -sf "$dest_script" "$symlink_path"
            sudo chmod +x "$dest_script"
            echo "✅ Symlink atualizado: $symlink_path -> $dest_script"
            log_message "sync: symlink updated to $dest_script"
        fi
    else
        # Create symlink (requires sudo to write to /usr/local/bin)
        sudo ln -sf "$dest_script" "$symlink_path"
        sudo chmod +x "$dest_script"
        echo "✅ Symlink criado: $symlink_path -> $dest_script"
        log_message "sync: symlink created to $dest_script"
    fi

    echo "🔚 Sincronização concluída"
    return 0
}

# =============================================================================
# MAIN COMMANDS - FULL VERSION
# =============================================================================

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
            SERVICE_IMAGES[$service]=$(docker compose config | awk -v svc="$service" '$1==svc":" {found=1} found && $1=="image:" {print $2; found=0}')
        done

        docker compose pull
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

        if [ ${#UPDATED_SERVICES[@]} -eq 0 ]; then
            echo "✅ No image was updated. No containers will be restarted."
            log_message "update-all: No image updated."
        else
            echo "🛠️  2/3: Restarting updated containers: ${UPDATED_SERVICES[*]}"
            for service in "${UPDATED_SERVICES[@]}"; do
                docker compose up -d "$service"
                echo "✅ $service restarted with new image (${NEW_IMAGES[$service]})"
                log_message "update-all: Service $service restarted with new image (${NEW_IMAGES[$service]})"
            done
            echo ""
            echo "✅ Update complete! Updated services: ${UPDATED_SERVICES[*]}"
            log_message "update-all: Updated services: ${UPDATED_SERVICES[*]}"
        fi
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
        start_docker_services "$2" "$3" "$4"
        ;;
    "stop")
        stop_docker_services "$2"
        ;;
    "restart")
        restart_docker_services "$2" "$3"
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
            echo "❌ Especifique o serviço para visualizar os logs."
            exit 1
        fi
        docker_compose_safe logs "$2"
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
            cd "$DOCKER_COMPOSE_DIR" && docker compose config --services
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
        echo "📊 USO DE RECURSOS (pressione Ctrl+C para sair)"
        echo ""
        if [ -n "$2" ]; then
            # Stats for specific service
            docker stats "$2"
        else
            # Stats for all containers
            docker stats
        fi
        ;;
    "pull")
        echo "⬇️  ATUALIZANDO IMAGENS"
        echo ""
        if ! check_docker_environment; then
            echo "❌ Docker not available"
            exit 1
        fi
        cd "$DOCKER_COMPOSE_DIR" || exit 1
        docker compose pull
        echo ""
        echo "✅ Imagens atualizadas!"
        echo "💡 Use 'panel restart' para aplicar as atualizações"
        ;;
    "sync")
        sync
        ;;
    "rebuild")
        echo "🔨 REBUILD DE CONTAINERS"
        echo ""
        if ! is_hd_mounted; then
            echo "❌ HD não está montado"
            exit 1
        fi
        cd "$DOCKER_COMPOSE_DIR" || exit 1
        
        # Por padrão usa --no-cache, a menos que --cache seja passado
        no_cache="--no-cache"
        service=""
        for arg in "$2" "$3"; do
            if [ "$arg" = "--cache" ]; then
                no_cache=""
                echo "💾 Modo: COM CACHE (rebuild rápido)"
                echo ""
            elif [ -n "$arg" ]; then
                service="$arg"
            fi
        done
        
        # Mostra modo padrão se não passou --cache
        if [ "$no_cache" = "--no-cache" ]; then
            echo "🚫 Modo: SEM CACHE (rebuild completo)"
            echo ""
        fi
        
        if [ -n "$service" ]; then
            echo "🔨 Rebuild do serviço: $service"
            docker compose build $no_cache "$service"
            docker compose up -d "$service"
        else
            echo "🔨 Rebuild de todos os serviços"
            docker compose build $no_cache
            docker compose up -d
        fi
        echo ""
        echo "✅ Rebuild concluído!"
        ;;
    # update command removed, use update-all only
    "networks")
        echo "🌐 REDES DOCKER"
        echo "==============="
        echo ""
        docker network ls
        echo ""
        ;;
    "volumes")
        echo "💾 VOLUMES DOCKER"
        echo "================="
        echo ""
        docker volume ls
        echo ""
        ;;
    "prune")
        echo "🧹 LIMPEZA DE RECURSOS NÃO UTILIZADOS"
        echo ""
        read -p "Isso removerá containers parados, redes não usadas, imagens órfãs e cache. Continuar? (s/N): " confirm
        if [[ "$confirm" =~ ^[sS]$ ]]; then
            echo ""
            echo "🗑️  Removendo containers parados..."
            docker container prune -f
            echo ""
            echo "🗑️  Removendo redes não utilizadas..."
            docker network prune -f
            echo ""
            echo "🗑️  Removendo imagens órfãs..."
            docker image prune -f
            echo ""
            echo "🗑️  Removendo cache de build..."
            docker builder prune -f
            echo ""
            echo "✅ Limpeza concluída!"
        else
            echo "❌ Operação cancelada"
        fi
        ;;
    "diagnose")
        echo "🔍 DIAGNÓSTICO COMPLETO:"
        echo ""
        echo "HD:"
        echo "  UUID: $HD_UUID"
        echo "  Label: $HD_LABEL"
        detected_device=$(get_device_by_uuid)
        if [ -n "$detected_device" ]; then
            echo "  Dispositivo detectado: $detected_device"
        else
            echo "  Dispositivo detectado: ❌ NÃO ENCONTRADO"
        fi
        echo "  Ponto de montagem: $HD_MOUNT_POINT"
        echo "  Montado: $(is_hd_mounted && echo 'SIM' || echo 'NÃO')"
        if is_hd_mounted; then
            echo "  Uso do disco:"
            df -h "$HD_MOUNT_POINT" | tail -1 | awk '{print "    "$2" total, "$3" usado, "$4" livre ("$5" usado)"}'
        fi
        echo ""
        echo "Docker:"
        echo "  Docker disponível: $(check_docker_environment && echo 'SIM' || echo 'NÃO')"
        echo "  Containers rodando: $(docker ps -q | wc -l)"
        if load_docker_services; then
            echo "  Serviços detectados: ${DOCKER_SERVICES[*]}"
        fi
        echo ""
        ;;
    "force-mount")
        echo "⚡ MONTAGEM FORÇADA"
        echo ""
        unmount_hd_forced
        sleep 2
        fix_mount_point
        sleep 1
        mount_hd_simple
        ;;
    "sync")
        sync_files
        ;;
    *)
        echo "🎛️  AVAILABLE COMMANDS:"
        echo ""
        echo "  mount       - Mount HD"
        echo "  unmount     - Unmount HD" 
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