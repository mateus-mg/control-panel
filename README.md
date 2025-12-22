# 🎛️ Control Panel - Server Manager

Bash script to manage external HD and Docker containers on a home server.


## 🚀 Installation

### Recommended Structure (with external HD support)

```bash
# 1. Copy script to home (ALWAYS available)
cp control_panel.sh /path/to/home/control_panel.sh
chmod +x /path/to/home/control_panel.sh

# 2. Create global symlink
sudo ln -s /path/to/home/control_panel.sh /usr/local/bin/panel


# Test
panel status
```


## 📋 Quick Usage

### Server Startup
```bash
panel mount        # Mount external HD
panel start        # Start all containers
panel keepalive    # Keep system active (Ctrl+C to exit)
```

### Server Shutdown
```bash
panel stop         # Stop containers
panel unmount      # Unmount HD
```

### Manage Specific Services
```bash
panel services                      # List available services
panel start jellyfin                # Start only Jellyfin
panel start jellyfin --no-deps      # Start without dependencies
panel stop qbittorrent              # Stop only qBittorrent
panel restart plex                  # Restart only Plex
panel restart plex --clean          # Restart and clean containers
panel logs prowlarr -f              # View Prowlarr logs in real time
```


## 📚 Commands

### HD Management
| Command | Description |
|---------|-------------|
| `panel mount` | Mount external HD |
| `panel unmount` | Unmount HD (stops containers first) |
| `panel check` | Show active mounts |
| `panel fix` | Fix mount point |
| `panel force-mount` | Force full remount |

### Docker Management
| Command | Description |
|---------|-------------|
| `panel start [service] [--clean] [--no-deps]` | Start containers (all or specific, with options) |
| `panel stop [service]` | Stop containers (all or specific) |
| `panel restart [service] [--clean]` | Restart containers (all or specific, with cleanup) |
| `panel clean [service]` | Remove orphan containers (all or specific) |
| `panel ps` | List running containers |
| `panel logs <service> [-f]` | Show service logs (use -f to follow) |
| `panel stats [service]` | Show real-time CPU/memory usage |
| `panel health` | Check health of all containers |

### Docker Maintenance & Utilities
| Command | Description |
|---------|-------------|
| `panel services` | List all available services |
| `panel pull` | Pull updated images |
| `panel rebuild [service] [--cache]` | Rebuild containers (NO cache by default, or with cache) |
| `panel update-all` | Smart update: pull images, restart only updated containers |
| `panel networks` | List Docker networks |
| `panel volumes` | List Docker volumes |
| `panel prune` | Remove unused resources |
| `panel diagnose` | Detailed diagnostic (HD & Docker) |

### Monitoring
| Command | Description |
|---------|-------------|
| `panel status` | Full system status |
| `panel keepalive` | Continuous monitoring mode with retry limits |

### Log Management
| Command | Description |
|---------|-------------|
| `panel view-logs [n]` | View the last `n` lines of the script log file (default: 50) |
| `panel view-logs [n]` | View the last `n` lines of the script log file (default: 50) |

### Example: View Logs
```bash
panel view-logs 100  # View the last 100 lines of the script log file
```

### Updated Error Handling
- Improved error messages for better debugging.
- Logs now include detailed context for easier troubleshooting.


## 🔄 Sync Files

### Synchronize Files and Create Symlink
```bash
panel sync
```

This command performs the following actions:
1. Copies the `control_panel.sh` script and `docker-compose.yml` from the external HD to the home directory.
2. Creates or updates a global symlink at `/usr/local/bin/panel` pointing to the script.
3. Ensures the files are up-to-date before copying.

### Example
```bash
panel sync  # Synchronize files and update symlink
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

### .service File
If using the `.service` file for automatic mounting, update the `ExecStart` line to match your HD configuration:

```ini
ExecStart=/usr/bin/mount UUID=your-hd-uuid /path/to/mount
```


## 🕒 Keepalive Mode

Keeps the HD active and monitors containers:

```bash
panel keepalive
```

- Checks HD every **2 minutes**
- Automatically remounts if disconnected (up to 5 retries)
- Restarts stopped containers
- **Ctrl+C to stop**

---

## 📄 View Logs

View the last `n` lines of the script log file:

```bash
panel view-logs [n]
```

- Default: Shows the last 50 lines if `n` is not specified.
- Example:

```bash
panel view-logs 100  # View the last 100 lines of the script log file
```


## 🐛 Troubleshooting

### HD does not mount
```bash
panel fix           # Fix mount point
panel force-mount   # Force mount
lsblk                # Check device
```

### Containers do not start
```bash
panel status                    # Check system
panel logs <service-name>       # View logs
panel diagnose                  # Full diagnostic
```


## 📝 Logs

The panel logs are stored in the file `~/.panel.log`. Each message includes a timestamp in ISO format (`YYYY-MM-DD HH:MM:SS`).

### Example Logs
```log
2025-12-20 16:31:01 - Service stopped: qbittorrent
2025-12-20 16:35:22 - Service started: cloudflared
```

### Log Rotation
- The system keeps only the last 500 lines in the main file.
- To avoid data loss, it is recommended to implement a manual or automatic archiving system (e.g., `panel.log.1`, `panel.log.2`).

### Troubleshooting Logs
- **Repetitive messages**: Check for redundancy in the script.
- **Specific errors**: Consult the detailed messages in the log to identify failures in Docker commands or HD mounting.


## 🛠️ Original .service Configuration

The original configuration of the `hdmount.service` file is as follows:

```ini
[Unit]
Description=Mount external HD before Docker
DefaultDependencies=no
After=local-fs.target
Before=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/mount /media/mateus/Servidor

[Install]
WantedBy=multi-user.target
```

### Instructions Before Moving

1. Ensure the `.service` file is correctly configured for your system.
2. Move the file to the systemd directory:
   ```bash
   sudo mv /path/to/hdmount.service /etc/systemd/system/
   ```
3. Reload systemd to recognize the new service:
   ```bash
   sudo systemctl daemon-reload
   ```
4. Enable the service to start on boot:
   ```bash
   sudo systemctl enable hdmount.service
   ```
5. Start the service manually to test:
   ```bash
   sudo systemctl start hdmount.service
   ```

