#!/bin/bash

# =============================================================================
# CONTROL PANEL - FULL VERSION WITH DOCKER AND KEEPALIVE
# =============================================================================

# Settings
HD_MOUNT_POINT="/media/mateus/Servidor"
DOCKER_COMPOSE_DIR="/home/mateus"
DOCKER_COMPOSE_FILE="$DOCKER_COMPOSE_DIR/docker-compose.yml"
LOG_FILE="$HOME/.painel.log"

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

# ✅ FUNCTION: Check Docker environment
check_docker_environment() {
    if ! command -v docker &> /dev/null; then
        return 1
    fi
    
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
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

# ✅ FUNCTION: Stop Docker containers (now accepts specific service)
stop_docker_services() {
    local service="$1"
    
    echo "🐳 Stopping Docker services..."
    echo ""
    
    if ! check_docker_environment; then
        echo "⚠️  Docker not available"
        return 1
    fi
    
    cd "$DOCKER_COMPOSE_DIR" || return 1
    
    # If a specific service was informed
    if [ -n "$service" ]; then
        echo "⏹️  Stopping specific service: $service"
        echo ""
        
        # Use docker stop directly (more reliable than compose stop)
        docker stop "$service" --timeout 10
        
        log_message "Service stopped: $service"
    else
        # Stop all services
        if load_docker_services; then
            echo "🛑 Stopping all services: ${DOCKER_SERVICES[*]}"
            echo ""
            for service_item in "${DOCKER_SERVICES[@]}"; do
                echo "⏹️  Stopping: $service_item"
                docker stop "$service_item" --timeout 10
                log_message "Service stopped: $service_item"
            done
        else
            echo "🛑 Stopping all containers..."
            docker stop $(docker ps -q) --timeout 10
            log_message "All services stopped"
        fi
    fi
    
    sleep 3
    echo ""
    echo "✅ Docker services stopped"
    echo ""
}

# ✅ FUNCTION: Start Docker containers (now accepts specific service and --clean flag)
start_docker_services() {
    service=""
    clean_mode=false
    no_deps=false
    
    # Parse de argumentos (aceita: service, --clean, --no-deps ou combinações)
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
    
    if ! check_docker_environment; then
        echo "❌ Docker not available"
        return 1
    fi
    
    # Check if HD is mounted before starting
    if ! is_hd_mounted; then
        echo "❌ HD is not mounted. Mount first with: painel mount"
        return 1
    fi
    
    cd "$DOCKER_COMPOSE_DIR" || return 1
    
    # Clean old containers if --clean was passed
    if [ "$clean_mode" = true ]; then
        echo ""
        clean_old_containers "$service"
        echo ""
    fi
    
    # If a specific service was informed
    if [ -n "$service" ]; then
        echo "▶️  Starting specific service: $service"
        
        # Automatically detect if service uses 'build:' and force --no-deps
        if grep -q "^  $service:" "$DOCKER_COMPOSE_FILE" && \
           grep -A 5 "^  $service:" "$DOCKER_COMPOSE_FILE" | grep -q "build:"; then
            echo "🔨 Service uses build, forcing --no-deps"
            no_deps=true
        fi
        
        if [ "$no_deps" = true ]; then
            echo "⚠️  Mode: Ignoring dependencies (--no-deps)"
        fi
        echo ""
        
        # Remove orphan containers automatically (force remove)
        echo "🧹 Removing orphan containers..."
        docker rm -f "$service" 2>/dev/null || true
        
        if [ "$no_deps" = true ]; then
            docker compose up -d --no-deps "$service"
            log_message "Service started: $service (no dependencies)"
        else
            docker compose up -d "$service"
            log_message "Service started: $service"
        fi
    else
        # Start all services
        if load_docker_services; then
            echo "🚀 Starting all services: ${DOCKER_SERVICES[*]}"
            echo ""
            
            # Remove orphan containers for all services (force)
            echo "🧹 Removing orphan containers..."
            for service_item in "${DOCKER_SERVICES[@]}"; do
                docker rm -f "$service_item" 2>/dev/null || true
            done
            
            for service_item in "${DOCKER_SERVICES[@]}"; do
                echo "▶️  Starting: $service_item"
                docker compose up -d "$service_item"
                log_message "Service started: $service_item"
            done
        else
            echo "🚀 Starting all containers..."
            docker compose down 2>/dev/null || true
            docker compose up -d
            log_message "All services started"
        fi
    fi
    
    sleep 4
    echo ""
    echo "✅ Docker services started"
    echo ""
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
    
    if ! is_hd_mounted; then
        echo "❌ HD is not mounted. Mount first with: painel mount"
        return 1
    fi
    
    # If a specific service was informed
    if [ -n "$service" ]; then
        echo "🔄 Restarting specific service: $service"
        echo ""
        cd "$DOCKER_COMPOSE_DIR" || return 1
        
        if [ "$clean_mode" = true ]; then
            # Stop, remove and start
            docker compose stop "$service"
            log_message "Service stopped for cleaning: $service"
            sleep 1
            clean_old_containers "$service"
            echo ""
            docker compose up -d "$service"
            log_message "Service restarted after cleaning: $service"
        else
            # Simple restart
            docker compose restart "$service"
            log_message "Service restarted: $service"
        fi
    else
        # Restart all services
        stop_docker_services
        sleep 2
        
        if [ "$clean_mode" = true ]; then
            echo ""
            clean_old_containers
            echo ""
        fi
        
        start_docker_services
    fi
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
        echo "❌ HD não detectado (UUID: $HD_UUID)"
        echo "💡 Verifique se o HD está conectado: lsblk"
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
    
    # Sync before unmount (flush buffers)
    sync
    
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
        if [ -n "$2" ]; then
            # Validar se serviço existe
            if load_docker_services && [[ " ${DOCKER_SERVICES[@]} " =~ " $2 " ]]; then
                cd "$DOCKER_COMPOSE_DIR" && docker compose logs "$2" "${@:3}"
            else
                echo "❌ Serviço '$2' não encontrado"
                echo "💡 Serviços disponíveis:"
                echo ""
                if load_docker_services; then
                    printf "  - %s\n" "${DOCKER_SERVICES[@]}"
                fi
                exit 1
            fi
        else
            echo "❌ Especifique um serviço: painel logs <servico> [-f]"
            echo "💡 Use 'painel services' para ver serviços disponíveis"
            exit 1
        fi
        ;;
    "services")
        echo "📋 Serviços disponíveis no docker-compose:"
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
        echo "🏥 HEALTH CHECK DOS SERVIÇOS"
        echo "============================"
        echo ""
        
        if ! load_docker_services; then
            echo "❌ Não foi possível carregar serviços"
            exit 1
        fi
        
        for service in "${DOCKER_SERVICES[@]}"; do
            health=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null)
            status=$(docker inspect --format='{{.State.Status}}' "$service" 2>/dev/null)
            
            if [ -z "$status" ]; then
                echo "❌ $service: NÃO EXISTE"
            elif [ "$status" != "running" ]; then
                echo "🔴 $service: $status"
            elif [ -n "$health" ] && [ "$health" != "healthy" ]; then
                echo "⚠️  $service: running mas $health"
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
            # Stats de serviço específico
            docker stats "$2"
        else
            # Stats de todos os containers
            docker stats
        fi
        ;;
    "pull")
        echo "⬇️  ATUALIZANDO IMAGENS"
        echo ""
        if ! check_docker_environment; then
            echo "❌ Docker não disponível"
            exit 1
        fi
        cd "$DOCKER_COMPOSE_DIR" || exit 1
        docker compose pull
        echo ""
        echo "✅ Imagens atualizadas!"
        echo "💡 Use 'painel restart' para aplicar as atualizações"
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
    *)
        echo "🎛️  AVAILABLE COMMANDS:"
        echo ""
        echo "  mount       - Mount HD"
        echo "  unmount     - Unmount HD" 
        echo "  status      - Full system status"
        echo "  keepalive   - Keepalive mode (keep HD active)"
        echo "  check       - Show mounts"
        echo "  fix         - Fix mount point"
        echo ""
        echo "🐳 DOCKER MANAGEMENT:"
        echo "  start       - Start containers (painel start [service] [--clean] [--no-deps])"
        echo "  stop        - Stop containers (painel stop [service])"
        echo "  restart     - Restart containers (painel restart [service] [--clean])"
        echo "  clean       - Remove old containers (painel clean [service])"
        echo "  ps          - Running containers"
        echo "  logs        - View logs (painel logs <service> [-f])"
        echo "  stats       - Resource usage (painel stats [service])"
        echo "  health      - Check container health"
        echo ""
        echo "💡 Use --clean when starting/restarting to remove old containers"
        echo "   Use --no-deps when starting to ignore dependencies"
        echo "   Example: painel start cloudflared --no-deps"
        echo ""
        echo "🔄 DOCKER MAINTENANCE:"
        echo "  services    - List available services"
        echo "  pull        - Pull updated images"
        echo "  rebuild     - Rebuild containers WITHOUT cache (painel rebuild [service] [--cache])"
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
