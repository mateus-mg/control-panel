# 🎛️ Control Panel - Server Manager

Bash and Python system for managing external HD drives and Docker containers on a home server.

> **Documentation:** Full documentation is now available at [https://mateus-mg.github.io/control-panel](https://mateus-mg.github.io/control-panel)

---

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

Automated backup system with individual schedules and retention policies per source directory.

### Features

- **Individual Schedules**: Each source can have its own backup frequency (hourly, daily, weekly, monthly)
- **Flexible Retention**: Configure retention policies per source
- **Incremental Backups**: Uses rsync with hard links for efficient storage
- **Automated Daemon**: Background service for scheduled backups
- **Interactive CLI**: Menu-driven interface and command-line options

### Quick Setup

```bash
# Install backup service (enables auto-start on boot)
sudo ./scripts/install-backup-service.sh

# Configure destination
control-panel backup set-destination /path/to/your/storage backups

# Add sources with individual schedules
control-panel backup add-source /path/to/docker/config \
  --frequency daily --time 02:00 \
  --priority high \
  --description "Docker configurations"

control-panel backup add-source /path/to/scripts \
  --frequency weekly --time 03:00 --day-of-week sunday \
  --priority medium \
  --description "Custom scripts"

# Start daemon
control-panel backup daemon-start
```

### Usage

#### Interactive Menu
```bash
control-panel backup
```

#### Daemon Management
```bash
# Start/Stop/Restart/Status
control-panel backup daemon-start
control-panel backup daemon-stop
control-panel backup daemon-restart
control-panel backup daemon-status
```

#### Source Management
```bash
# List all configured sources
control-panel backup list-sources

# Add source with custom schedule
control-panel backup add-source /path/to/source \
  --frequency monthly --day 1 --time 04:00 \
  --recursive \
  --exclude "*.tmp,*.log"

# Remove or toggle source
control-panel backup remove-source /path/to/source
control-panel backup toggle-source /path/to/source

# Configure individual source schedule
control-panel backup set-source-schedule /path/to/source \
  --frequency weekly --time 03:00 --day-of-week sunday

# Configure individual source retention
control-panel backup set-source-retention /path/to/source \
  --daily 0 --weekly 12 --monthly 6 --max-age 365
```

#### Schedule Configuration
```bash
# Global schedule (default for new sources)
control-panel backup set-schedule --frequency daily --time 02:00

# Custom schedule (specific days)
control-panel backup set-schedule --frequency custom --time 02:00 --days mon,wed,fri
```

#### Retention Configuration
```bash
# Global retention policy
control-panel backup set-retention \
  --daily 7 \
  --weekly 4 \
  --monthly 6 \
  --max-age 180 \
  --min-space 10
```

#### Backup Execution
```bash
# Run backup for all enabled sources
control-panel backup run

# Run backup for specific source
control-panel backup run --source /path/to/source
```

#### Statistics and History
```bash
# View statistics
control-panel backup stats

# View backup history
control-panel backup history --limit 10

# View full configuration
control-panel backup config

# Check destination space
control-panel backup check-destination
```

### Configuration Options

#### Backup Schedule Options

| Frequency | Parameters | Description |
|-----------|------------|-------------|
| `hourly` | - | Every hour |
| `daily` | `--time` | Once per day |
| `weekly` | `--time`, `--day-of-week` | Once per week |
| `monthly` | `--time`, `--day` | Once per month |
| `custom` | `--time`, `--days` | Specific days |

#### Retention Policy

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--daily` | 7 | Daily backups to keep |
| `--weekly` | 4 | Weekly backups to keep |
| `--monthly` | 6 | Monthly backups to keep |
| `--max-age` | 180 | Maximum age in days (0 = unlimited) |
| `--min-space` | 10 | Minimum free space in GB |

#### Source Priority

| Priority | Description |
|----------|-------------|
| `high` | Critical data, backs up first |
| `medium` | Normal data |
| `low` | Large volumes, changes rarely |

### Backup Storage Structure

```
<destination>/backups/
├── daily/
│   ├── backup-2026-02-27_02-00/
│   ├── backup-2026-02-28_02-00/
│   └── ...
├── weekly/
│   ├── backup-2026-W08_03-00/
│   └── ...
├── monthly/
│   ├── backup-2026-02_04-00/
│   └── ...
└── logs/
```

Each backup directory contains:
- Backed up files with original structure
- `_metadata.json` - Backup metadata and statistics

### Examples

#### Example 1: Critical Configurations (Daily)
```bash
control-panel backup add-source /path/to/docker/config \
  --frequency daily --time 02:00 \
  --daily-retention 7 --weekly-retention 4 --monthly-retention 6 \
  --priority high \
  --description "Docker configurations" \
  --exclude "*.tmp,*.log"
```

#### Example 2: Scripts (Weekly)
```bash
control-panel backup add-source /path/to/scripts \
  --frequency weekly --time 03:00 --day-of-week sunday \
  --weekly-retention 12 --monthly-retention 6 \
  --priority medium \
  --description "Custom scripts" \
  --exclude "*.pyc,__pycache__,.git"
```

#### Example 3: Large Media Files (Monthly)
```bash
control-panel backup add-source /path/to/media/files \
  --frequency monthly --time 04:00 --day 1 \
  --monthly-retention 6 --max-age 365 \
  --priority low \
  --description "Media files" \
  --exclude "*.tmp,*.part,@eaDir"
```

### Systemd Service

The backup daemon runs as a systemd service:

```bash
# Check service status
sudo systemctl status control-panel-backup-daemon.service

# View logs
sudo journalctl -u control-panel-backup-daemon.service -f

# Stop/Start service
sudo systemctl stop control-panel-backup-daemon.service
sudo systemctl start control-panel-backup-daemon.service
```

### Best Practices

1. **Schedule backups during low-usage hours** (e.g., 2:00-5:00 AM)
2. **Use appropriate retention policies** based on data importance
3. **Exclude temporary and cache files** to save space
4. **Monitor disk space** regularly with `check-destination`
5. **Test restoration** periodically to ensure backup integrity
6. **Set different priorities** for different data types

### Troubleshooting

#### Daemon Not Starting
```bash
# Check service status
sudo systemctl status control-panel-backup-daemon.service

# View logs
sudo journalctl -u control-panel-backup-daemon.service -n 50
```

#### Backup Failing
```bash
# Check destination space
control-panel backup check-destination

# View backup history for errors
control-panel backup history --limit 5
```

#### Source Not Found
```bash
# List configured sources
control-panel backup list-sources

# Verify path exists
ls -la /path/to/source
```

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

