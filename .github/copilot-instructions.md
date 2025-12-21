````````instructions
```````instructions
``````instructions
# Copilot Instructions - Control Panel

## Project Overview
Bash script for managing external HD and Docker containers in a home server. Handles mounting/unmounting of HD and Docker operations with temporary keepalive mode. Located in `panel-control/`.

## Architecture

**Main Script:** `panel-control/panel.sh` (~450 lines)
- Single bash script with modular functions
- No external dependencies beyond standard Unix tools (mountpoint, grep, sed, docker)
- Auto-discovers services from docker-compose.yml
- Temporary keepalive system until NAS acquisition

**Key Components:**
- `is_hd_mounted()`: Validates HD mount status (mountpoint + /proc/mounts fallback)
- `mount_hd_simple()`: Mounts HD with permission handling
- `unmount_hd_forced()`: Stops Docker, syncs, unmounts (safe shutdown)
- `keepalive_hd_optimized()`: Monitors HD/containers every 30s, auto-remounts
- `get_docker_services()`: Auto-discovers services from docker-compose.yml

## Critical Patterns

### HD Configuration
Update the following variables in the script to match your system:

```bash
HD_MOUNT_POINT="/path/to/mount"
HD_UUID="your-hd-uuid"
HD_LABEL="your-hd-label"
HD_DEVICE="/dev/sdX"
HD_TYPE="ext4"
DOCKER_COMPOSE_DIR="/path/to/docker-compose"
```

### Mount Verification
The `is_hd_mounted` function checks if the HD is mounted. Ensure the `HD_MOUNT_POINT` variable is correctly set to your desired mount point.

### Service Auto-Discovery
The `get_docker_services` function assumes your `docker-compose.yml` file is located in the directory specified by `DOCKER_COMPOSE_DIR`. Update this variable as needed.

### Keepalive Loop
The keepalive loop monitors the HD and Docker containers. Adjust the monitoring interval or behavior as required for your system.

## Developer Workflows

**Install globally:**
```bash
sudo cp panel.sh /usr/local/bin/panel
sudo chmod +x /usr/local/bin/panel
panel status
```

**Typical startup:**
```bash
panel mount           # Mount HD
panel start           # Start all containers
panel keepalive       # Activate monitoring (Ctrl+C to stop)
```

**Service-specific operations:**
```bash
panel start jellyfin      # Start only Jellyfin
panel restart qbittorrent # Restart qBittorrent
panel logs prowlarr -f    # Follow Prowlarr logs
```

## Command Reference

**HD Management:**
- `panel mount` - Mounts external HD
- `panel unmount` - Stops Docker, unmounts HD safely
- `panel check` - Shows active mounts
- `panel fix` - Recreates mount point with correct permissions
- `panel force-mount` - Force complete remount sequence
- `panel sync` - Sync script and docker-compose.yml from HD

**Docker Operations:**
- `panel start [service] [--clean] [--no-deps]` - Start all or specific container (with options)
- `panel stop [service]` - Stop all or specific container
- `panel restart [service] [--clean]` - Restart all or specific container (with cleanup)
- `panel clean [service]` - Remove orphan containers (all or specific)
- `panel ps` - List running containers
- `panel logs <service>` - View service logs
- `panel services` - List available services
- `panel pull` - Pull updated images
- `panel rebuild [service] [--cache]` - Rebuild containers (NO cache by default, or with cache)
- `panel update-all` - Smart update: pull images, restart only updated containers
- `panel networks` - List Docker networks
- `panel volumes` - List Docker volumes
- `panel prune` - Remove unused resources

**Monitoring:**
- `panel status` - Complete system status
- `panel keepalive` - Continuous monitoring mode
- `panel diagnose` - Full diagnostic report

## Key Conventions

1. **Always verify mount before Docker operations**: Prevents data corruption
2. **Stop Docker before unmounting**: Ensures clean shutdown
3. **Use sudo only when necessary**: mount/umount operations only
4. **Service names match docker-compose.yml**: Auto-discovered, no hardcoding
5. **Logging pattern**: Timestamps in ISO format to `~/.painel.log`
6. **Return codes**: 0=success, 1=error (consistent across functions)

## Integration Points

**External dependencies:**
- Docker Compose v2: Service management (required)
- mountpoint: Mount verification (required)
- lsof: Process checking (optional, for safety)
- findmnt/lsblk: Diagnostics (optional)

**File system:**
- HD mounts at `/media/mateus/Servidor`
- Docker compose at `/home/mateus/docker-compose.yml`
- Logs at `~/.painel.log`

## Common Issues

**HD won't mount:** Check device exists (`lsblk`), fix mount point (`panel fix`), force mount (`panel force-mount`)

**Containers won't start:** Verify HD is mounted first, check docker-compose.yml exists, review logs

**Keepalive fails:** Check HD connection, review `~/.painel.log`, verify Docker status

## Critical Safety Patterns

**Pre-unmount validation:**
```bash
# MUST stop Docker before unmounting
stop_docker_services
sleep 3  # Allow containers to release files
sync     # Flush filesystem buffers
```

**Mount point creation:**
```bash
# MUST set correct ownership
sudo mkdir -p "$HD_MOUNT_POINT"
sudo chown mateus:mateus "$HD_MOUNT_POINT"
sudo chmod 755 "$HD_MOUNT_POINT"
```

**Docker startup validation:**
```bash
# MUST verify HD mounted before starting
if ! is_hd_mounted; then
    echo "❌ HD not mounted. Mount first: painel mount"
    return 1
fi
```

## Keepalive Behavior

**Purpose:** Temporary solution until NAS acquisition - keeps HD active and monitors containers

**Operation:**
- Checks HD mount every 30 seconds
- Auto-remounts on disconnect
- Restarts stopped containers
- Maintains HD activity with touch

**Optimization tips:**
- Use 60s interval for lighter load
- Replace `touch` with `dd` read for less wear
- Touch only every 10 minutes (300s)
- Don't verify containers constantly (Docker manages)

**Exit:** Press Ctrl+C (should implement trap for clean exit)

## Known Limitations

1. **Race condition in grep:** `grep -q "$service"` matches partial names (e.g., "jellyfin" matches "jellyfin-backup")
   - **Fix:** Use `grep -qx` for exact match or `docker compose ps`

2. **Infinite retry loop:** No backoff on repeated failures
   - **Fix:** Add retry counter with 5-min pause after 3 failures

3. **No signal handling:** Ctrl+C may leave inconsistent state
   - **Fix:** Add `trap cleanup_on_exit SIGINT SIGTERM`

4. **Unsafe unmount:** Doesn't check for open files
   - **Fix:** Use `lsof` to verify no processes using HD

5. **Aggressive touch:** Writes to disk every 30s
   - **Fix:** Read-only check or touch every 10 minutes

6. **No log rotation:** `~/.painel.log` grows indefinitely
   - **Fix:** Tail last 500 lines on rotation

## Best Practices

**When editing:**
1. Test mount/unmount before Docker operations
2. Always validate return codes
3. Use absolute paths (no relative paths)
4. Quote variables: `"$var"` not `$var`
5. Prefer `[[ ]]` over `[ ]` for conditionals
6. Use `local` for function variables

**Error handling:**
```bash
# GOOD: Check return and provide context
if ! mount_hd_simple; then
    echo "❌ Failed to mount HD"
    return 1
fi

# BAD: Silent failure
mount_hd_simple
```

**Service validation:**
```bash
# GOOD: Validate service exists
if [[ " ${DOCKER_SERVICES[@]} " =~ " $service " ]]; then
    docker compose restart "$service"
fi

# BAD: No validation
docker compose restart "$2"
```

## Troubleshooting Commands

```bash
# Check HD status
lsblk | grep sdb
sudo blkid | grep Servidor
mountpoint /media/mateus/Servidor

# Check mounts
findmnt | grep sdb
cat /proc/mounts | grep Servidor

# Check Docker
cd /home/mateus && docker compose config --services
docker ps -a

# Check processes using HD
lsof /media/mateus/Servidor

# View logs
tail -f ~/.painel.log
```

## Future Improvements (Post-NAS)

- [ ] Remove keepalive (not needed with NAS)
- [ ] Simplify mounting (permanent mount in fstab)
- [ ] Add automatic backups
- [ ] Integrate systemd for auto-start
- [ ] Add web interface (optional)
- [ ] Notification system (desktop/mobile)

## Implemented Improvements

#### Generic Functions
1. **`validate_environment`**:
   - Centralizes Docker environment validation and mounted HD verification.
   - Replaces repetitive validations in multiple functions.

2. **`execute_docker_compose`**:
   - Abstracts Docker Compose command execution with prior validation.
   - Reduces code duplication in `start_docker_services`, `stop_docker_services`, and `restart_docker_services` functions.

#### Updates to Existing Functions
- **`start_docker_services`**:
  - Now uses `validate_environment` for initial validations.
  - Uses `execute_docker_compose` to start services.

- **`stop_docker_services`**:
  - Replaces redundant validations and commands with calls to generic functions.

- **`restart_docker_services`**:
  - Integrates `validate_environment` and `execute_docker_compose`.
  - Simplifies restart logic with optional cleanup.

#### Benefits
- **Reduced Redundancy**: Cleaner and easier to maintain code.
- **Reusability**: Generic functions can be used in future implementations.
- **Reliability**: Centralized validations reduce potential errors.

## Project Rules and Guidelines

### General Language Requirement
- All project documentation, code comments, and user-facing messages must be written in English to ensure consistency and accessibility for a broader audience.

### Structure and Organization
1. **Centralization of Generic Functions**:
   - Whenever possible, use generic functions to avoid code duplication.
   - Functions such as validations and service handling should be reusable.

2. **Log Messages**:
   - All important messages must be logged using `log_message`.
   - Use clear and standardized messages to facilitate diagnostics.

3. **Pre-requisite Validation**:
   - Before executing any Docker command or HD operation, validate the environment with dedicated functions.
   - Use `validate_environment` to ensure the HD is mounted and Docker is available.

### Coding Best Practices
1. **Use of Local Variables**:
   - Always declare variables as `local` within functions to avoid global conflicts.

2. **Error Handling**:
   - Always validate the return of critical commands and provide detailed error messages.
   - Use consistent return codes: `0` for success and `1` for errors.

3. **Code Readability**:
   - Use clear comments to explain complex parts of the code.
   - Keep the code organized and avoid overly long lines.

### Docker and HD
1. **Safe Operations**:
   - Always stop Docker services before unmounting the HD.
   - Use `sync` to ensure filesystem buffers are flushed before unmounting.

2. **Container Maintenance**:
   - Use commands like `clean_old_containers` to avoid the accumulation of unnecessary resources.
   - Prefer restarting only the necessary services instead of all containers.

### Logs and Diagnostics
1. **Log Rotation**:
   - Keep the log file to a maximum of 1000 lines, using automatic rotation.

2. **Diagnostics**:
   - Provide detailed information in the `diagnose` command to facilitate problem resolution.

### Contributions
1. **Code Standards**:
   - Follow the guidelines above to ensure code consistency.
   - Test all changes before submitting.

2. **Documentation**:
   - Update this file whenever new rules or guidelines are added.

These rules ensure that the project remains organized, efficient, and easy to maintain.
``````
