# 🎛️ Control Panel - Server Manager

![GitHub release (latest by date)](https://img.shields.io/github/v/release/mateus-mg/control-panel?label=release)

Bash script to manage external HD and Docker containers on a home server.


## 🚀 Installation

### Recommended Structure (with external HD support)

```bash
# 1. Copy script to home (ALWAYS available)
cp painel.sh /home/mateus/painel.sh
chmod +x /home/mateus/painel.sh

# 2. Create global symlink
sudo ln -s /home/mateus/painel.sh /usr/local/bin/painel

# 3. Create sync script
# (already created at /home/mateus/sync-painel.sh)

# 4. Add to crontab for sync at boot
crontab -e
# Add: @reboot /home/mateus/sync-painel.sh

# 5. Create alias for convenience
echo "alias sync-painel='/home/mateus/sync-painel.sh'" >> ~/.bashrc
source ~/.bashrc

# Test
painel status
```


## 📋 Quick Usage

### Server Startup
```bash
painel mount        # Mount external HD
painel start        # Start all containers
painel keepalive    # Keep system active (Ctrl+C to exit)
```

### Server Shutdown
```bash
painel stop         # Stop containers
painel unmount      # Unmount HD
```

### Manage Specific Services
```bash
painel services                      # List available services
painel start jellyfin                # Start only Jellyfin
painel start jellyfin --no-deps      # Start without dependencies
painel stop qbittorrent              # Stop only qBittorrent
painel restart plex                  # Restart only Plex
painel restart plex --clean          # Restart and clean containers
painel logs prowlarr -f              # View Prowlarr logs in real time
sync-painel                          # Sync script (after editing)
```


## 📚 Commands

### HD Management
| Command | Description |
|---------|-------------|
| `painel mount` | Mount external HD |
| `painel unmount` | Unmount HD (stops containers first) |
| `painel check` | Show active mounts |
| `painel fix` | Fix mount point |
| `painel force-mount` | Force full remount |

### Docker Management
| Command | Description |
|---------|-------------|
| `painel start [service]` | Start containers (all or specific) |
| `painel start [service] --no-deps` | Start without recreating dependencies |
| `painel start [service] --clean` | Remove orphan containers before starting |
| `painel stop [service]` | Stop containers (all or specific) |
| `painel restart [service]` | Restart containers (all or specific) |
| `painel restart [service] --clean` | Restart with orphan container cleanup |
| `painel clean [service]` | Remove orphan containers (all or specific) |
| `painel ps` | List running containers |
| `painel logs <service> [-f]` | Show service logs (use -f to follow) |
| `painel stats [service]` | Show real-time CPU/memory usage |
| `painel health` | Check health of all containers |

### Docker Maintenance
| Command | Description |
|---------|-------------|
| `painel services` | List all available services |
| `painel pull` | Pull updated images |
| `painel rebuild [service]` | Rebuild containers (NO cache by default) |
| `painel rebuild [service] --cache` | Rebuild with cache (faster) |
| `painel update-all` | Smart update: pull images, restart only updated containers |
## 🔄 Smart Update: update-all


The `painel update-all` command automates image updates and container restarts in a safe and efficient way:

- Checks if the external HD is mounted and Docker is available
- Pulls the latest images for all services defined in your docker-compose.yml
- For each service, compares the Image ID (hash) of the local image (after pull) with the Image ID used by the running container (using `docker inspect`).
- Restarts only the containers whose running image is different from the latest local image, ensuring that only truly updated containers are recreated.
- If a container is not running, it will also be recreated to use the latest image.
- Logs all actions and updates to `~/.painel.log`
- Prints notifications in the terminal for each updated service

**Usage:**

```bash
painel update-all
```

If no image was updated, no containers will be restarted. If one or more images were updated, only the affected containers will be restarted, minimizing downtime and unnecessary restarts.

All output and logs are in English, following project conventions.
| `painel networks` | List Docker networks |
| `painel volumes` | List Docker volumes |
| `painel prune` | Remove unused resources |

### Monitoring
| Command | Description |
|---------|-------------|
| `painel status` | Full system status |
| `painel keepalive` | Continuous monitoring mode |
| `painel diagnose` | Detailed diagnostic |


## ⚙️ Configuration

Edit the variables at the beginning of the script:
```bash
HD_MOUNT_POINT="/media/mateus/Servidor"
DOCKER_COMPOSE_DIR="/home/mateus"
HD_DEVICE="/dev/sdb1"
```


## 🔋 Keepalive Mode

Keeps the HD active and monitors containers:

```bash
painel keepalive
```

- Checks HD every 30 seconds
- Automatically remounts if disconnected
- Restarts stopped containers
- **Ctrl+C to stop**


## 🐛 Troubleshooting

### HD does not mount
```bash
painel fix           # Fix mount point
painel force-mount   # Force mount
lsblk                # Check device
```

### Containers do not start
```bash
painel status                    # Check system
painel logs <service-name>       # View logs
painel diagnose                  # Full diagnostic
```


## 📝 Logs

