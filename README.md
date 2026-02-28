# 🎛️ Control Panel - Server Manager

Bash script to manage external HD and Docker containers on a home server.


## 🚀 Installation

### Recommended Structure (with external HD support)

```bash
# 1. Copy script to home (ALWAYS available)
cp control_panel.sh /path/to/home/control_panel.sh
chmod +x /path/to/home/control_panel.sh

# 2. Create global symlink
sudo ln -s /path/to/home/control_panel.sh /usr/local/bin/control-panel


# Test
control-panel status
```


## 📋 Quick Usage

### Server Startup
```bash
control-panel mount        # Mount external HD (automatic via systemd)
control-panel start        # Start all containers
# Keepalive runs automatically via systemd service
```

### Server Shutdown
```bash
control-panel stop         # Stop containers
control-panel unmount      # Unmount HD
```

### Manage Specific Services
```bash
control-panel services                      # List available services
control-panel start jellyfin                # Start only Jellyfin
control-panel start jellyfin --no-deps      # Start without dependencies
control-panel stop qbittorrent              # Stop only qBittorrent
control-panel restart plex                  # Restart only Plex
control-panel restart plex --clean          # Restart and clean containers
control-panel logs prowlarr -f              # View Prowlarr logs in real time
```


## 📚 Commands

### HD Management
| Command | Description |
|---------|-------------|
| `control-panel mount` | Mount external HD |
| `control-panel unmount` | Unmount HD (stops containers first) |
| `control-panel check` | Show active mounts |
| `control-panel fix` | Fix mount point |
| `control-panel force-mount` | Force full remount |

### Docker Management
| Command | Description |
|---------|-------------|
| `control-panel start [service] [--clean] [--no-deps]` | Start containers (all or specific, with options) |
| `control-panel stop [service]` | Stop containers (all or specific) |
| `control-panel restart [service] [--clean]` | Restart containers (all or specific, with cleanup) |
| `control-panel clean [service]` | Remove orphan containers (all or specific) |
| `control-panel ps` | List running containers |
| `control-panel logs <service> [-f]` | Show service logs (use -f to follow) |
| `control-panel stats [service]` | Show real-time CPU/memory usage |
| `control-panel health` | Check health of all containers |

### Docker Maintenance & Utilities
| Command | Description |
|---------|-------------|
| `control-panel services` | List all available services |
| `control-panel pull` | Pull updated images |
| `control-panel rebuild [service] [--cache]` | Rebuild containers (NO cache by default, or with cache) |
| `control-panel update-all` | Smart update: pull images, restart only updated containers |
| `control-panel networks` | List Docker networks |
| `control-panel volumes` | List Docker volumes |
| `control-panel prune` | Remove unused resources |
| `control-panel diagnose` | Detailed diagnostic (HD & Docker) |

### Monitoring
| Command | Description |
|---------|-------------|
| `control-panel status` | Full system status |
| `control-panel keepalive` | Manual keepalive mode (runs automatically via systemd) |

### Log Management
| Command | Description |
|---------|-------------|
| `control-panel view-logs [n]` | View the last `n` lines of the script log file (default: 50) |

### Example: View Logs
```bash
control-panel view-logs 100  # View the last 100 lines of the script log file
```

### Updated Error Handling
- Improved error messages for better debugging.
- Logs now include detailed context for easier troubleshooting.


## 🔄 Sync Files

### Synchronize Files and Create Symlink
```bash
control-panel sync
```

This command performs the following actions:
1. Copies the `control_panel.sh` script and `docker-compose.yml` from the external HD to the home directory.
2. Creates or updates a global symlink at `/usr/local/bin/control-panel` pointing to the script.
3. Ensures the files are up-to-date before copying.

### Example
```bash
control-panel sync  # Synchronize files and update symlink
```


## ⚙️ Configuration

### HD Configuration
Update the following variables in the script to match your system:

```bash
HD_MOUNT_POINT="/path/to/mount"
HD_UUID="your-hd-uuid"
HD_LABEL="your-hd-label"
HD_TYPE="ext4"
DOCKER_COMPOSE_DIR="/path/to/docker-compose"
```

### Docker Compose
Ensure your `docker-compose.yml` file is located in the directory specified by `DOCKER_COMPOSE_DIR`.


## 🕒 Keepalive Mode

**Keepalive runs automatically** via systemd service (`control-panel-keepalive.service`).

### Automatic Behavior:
- ✅ Starts automatically on boot
- ✅ Checks the drive every **60 seconds**
- ✅ Touch marker only every **10 minutes** to reduce wear
- ✅ Retries remount up to **5 times**, then pauses 5 minutes before retrying
- ✅ Restarts if fails (managed by systemd)
- ℹ️ Does NOT restart containers (they restart themselves via Docker restart policies)

### Manual Mode (optional):
```bash
control-panel keepalive  # Run manually if needed
```

### Manage Systemd Service:
```bash
sudo systemctl status control-panel-keepalive.service   # Check status
sudo systemctl stop control-panel-keepalive.service     # Stop service
sudo systemctl start control-panel-keepalive.service    # Start service
sudo journalctl -u control-panel-keepalive.service -f   # View logs
```

---

## 📦 Backup Subsystem

Automated backup system with individual schedules and retention policies.

### Quick Setup

```bash
# Install backup service
sudo ./scripts/install-backup-service.sh

# Configure destination
control-panel backup set-destination /path/to/your/storage backups

# Add sources
control-panel backup add-source /path/to/important/data --frequency daily --time 02:00
control-panel backup add-source /path/to/config/files --frequency weekly --time 03:00

# Start daemon
control-panel backup daemon-start
```

### Usage

```bash
# Interactive menu
control-panel backup

# View statistics
control-panel backup stats

# View history
control-panel backup history

# Run backup now
control-panel backup run
```

For complete documentation, see [BACKUP.md](BACKUP.md).

---

## 📄 View Logs

View the last `n` lines of the script log file:

```bash
control-panel view-logs [n]
```

- Default: Shows the last 50 lines if `n` is not specified.
- Example:

```bash
control-panel view-logs 100  # View the last 100 lines of the script log file
```


## 🐛 Troubleshooting

### HD does not mount
```bash
control-panel fix           # Fix mount point
control-panel force-mount   # Force mount
lsblk                # Check device
```

### Containers do not start
```bash
control-panel status                    # Check system
control-panel logs <service-name>       # View logs
control-panel diagnose                  # Full diagnostic
```


## 📝 Logs

The control-panel logs are stored in the file `~/.control-panel.log`. Each message includes a timestamp in ISO format (`YYYY-MM-DD HH:MM:SS`).

### Example Logs
```log
2025-12-20 16:31:01 - Service stopped: qbittorrent
2025-12-20 16:35:22 - Service started: cloudflared
```

### Log Rotation
- The system keeps only the last 500 lines in the main file.
- To avoid data loss, it is recommended to implement a manual or automatic archiving system (e.g., `control-panel.log.1`, `control-panel.log.2`).

### Troubleshooting Logs
- **Repetitive messages**: Check for redundancy in the script.
- **Specific errors**: Consult the detailed messages in the log to identify failures in Docker commands or HD mounting.


## 🛠️ Systemd Services

### Active Services:

#### 1. `hdmount.service` - HD Auto-Mount
Mounts the external HD automatically before Docker starts.

```bash
sudo systemctl status hdmount.service
```

#### 2. `control-panel-keepalive.service` - Automatic Keepalive
Keeps the HD active and monitors it continuously.

```bash
sudo systemctl status control-panel-keepalive.service
```

### Service Files Location:
- `/etc/systemd/system/hdmount.service`
- `/etc/systemd/system/control-panel-keepalive.service`
- Source: `<project-directory>/panel-keepalive.service`

### Useful Commands:
```bash
# View keepalive logs in real-time
sudo journalctl -u control-panel-keepalive.service -f

# Restart services
sudo systemctl restart hdmount.service
sudo systemctl restart control-panel-keepalive.service

# Disable auto-start (if needed)
sudo systemctl disable control-panel-keepalive.service
```

