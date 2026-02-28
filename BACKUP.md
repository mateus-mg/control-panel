# 📦 Backup Subsystem

Automated backup system with individual schedules and retention policies per source directory.

## Features

- **Individual Schedules**: Each source can have its own backup frequency (hourly, daily, weekly, monthly)
- **Flexible Retention**: Configure retention policies per source
- **Incremental Backups**: Uses rsync with hard links for efficient storage
- **Automated Daemon**: Background service for scheduled backups
- **Interactive CLI**: Menu-driven interface and command-line options
- **Space Management**: Automatic cleanup based on retention policies

## Quick Start

### 1. Install the Backup Service

```bash
cd /media/mateus/Servidor/scripts/control-panel
sudo ./scripts/install-backup-service.sh
```

This installs and **enables the service to start on boot**.

### 2. Configure Backup Destination

```bash
control-panel backup set-destination /media/mateus/Servidor backups
```

### 3. Add Backup Sources

```bash
# Docker configurations - daily backup
control-panel backup add-source /media/mateus/Servidor/containers/config \
  --frequency daily --time 02:00 \
  --priority high \
  --description "Docker configurations"

# Scripts - weekly backup
control-panel backup add-source /media/mateus/Servidor/scripts \
  --frequency weekly --time 03:00 --day-of-week sunday \
  --priority medium \
  --description "Custom scripts"
```

### 4. Start the Backup Daemon

```bash
control-panel backup daemon-start
```

## Usage

### Interactive Menu

```bash
control-panel backup
```

This opens the interactive backup management menu with options for:
- Daemon management (start/stop/restart/status)
- Source management (add/remove/configure)
- Destination configuration
- Schedule and retention settings
- Statistics and history

### Command-Line Interface

#### Daemon Management

```bash
# Start backup daemon
control-panel backup daemon-start

# Stop backup daemon
control-panel backup daemon-stop

# Restart backup daemon
control-panel backup daemon-restart

# Check daemon status
control-panel backup daemon-status
```

#### Destination Configuration

```bash
# Set backup destination
control-panel backup set-destination /media/mateus/Servidor backups

# Check destination space
control-panel backup check-destination
```

#### Global Schedule Configuration

```bash
# Set global schedule (default for new sources)
control-panel backup set-schedule --frequency daily --time 02:00

# Custom schedule (specific days)
control-panel backup set-schedule --frequency custom --time 02:00 --days mon,wed,fri
```

#### Global Retention Configuration

```bash
control-panel backup set-retention \
  --daily 7 \
  --weekly 4 \
  --monthly 6 \
  --max-age 180 \
  --min-space 10
```

#### Source Management

```bash
# Add a source with individual schedule
control-panel backup add-source /path/to/source \
  --frequency daily \
  --time 02:00 \
  --recursive \
  --daily-retention 7 \
  --weekly-retention 4 \
  --monthly-retention 6 \
  --priority high \
  --description "Important data" \
  --exclude "*.tmp,*.log,__pycache__"

# List all sources
control-panel backup list-sources

# Remove a source
control-panel backup remove-source /path/to/source

# Enable/disable a source
control-panel backup toggle-source /path/to/source

# Configure source schedule
control-panel backup set-source-schedule /path/to/source \
  --frequency weekly \
  --time 03:00 \
  --day-of-week sunday

# Configure source retention
control-panel backup set-source-retention /path/to/source \
  --daily 0 \
  --weekly 12 \
  --monthly 6 \
  --max-age 365
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
```

## Configuration Structure

### Backup Schedule Options

| Frequency | Parameters | Description |
|-----------|------------|-------------|
| `hourly` | - | Every hour |
| `daily` | `--time` | Once per day |
| `weekly` | `--time`, `--day-of-week` | Once per week |
| `monthly` | `--time`, `--day` | Once per month |
| `custom` | `--time`, `--days` | Specific days |

### Retention Policy

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--daily` | 7 | Daily backups to keep |
| `--weekly` | 4 | Weekly backups to keep |
| `--monthly` | 6 | Monthly backups to keep |
| `--max-age` | 180 | Maximum age in days (0 = unlimited) |
| `--min-space` | 10 | Minimum free space in GB |

### Source Priority

| Priority | Description |
|----------|-------------|
| `high` | Critical data, backs up first |
| `medium` | Normal data |
| `low` | Large volumes, changes rarely |

## Backup Storage Structure

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

## Examples

### Example 1: Critical Configurations (Daily)

```bash
control-panel backup add-source /media/mateus/Servidor/containers/config \
  --frequency daily --time 02:00 \
  --daily-retention 7 --weekly-retention 4 --monthly-retention 6 \
  --priority high \
  --description "Docker configurations" \
  --exclude "*.tmp,*.log"
```

### Example 2: Scripts (Weekly)

```bash
control-panel backup add-source /media/mateus/Servidor/scripts \
  --frequency weekly --time 03:00 --day-of-week sunday \
  --weekly-retention 12 --monthly-retention 6 \
  --priority medium \
  --description "Custom scripts" \
  --exclude "*.pyc,__pycache__,.git"
```

### Example 3: Large Media Files (Monthly)

```bash
control-panel backup add-source /media/mateus/Servidor/media \
  --frequency monthly --time 04:00 --day 1 \
  --monthly-retention 6 --max-age 365 \
  --priority low \
  --description "Media files" \
  --exclude "*.tmp,*.part,@eaDir"
```

## Systemd Service

The backup daemon runs as a systemd service:

```bash
# Check service status
sudo systemctl status control-panel-backup-daemon.service

# View logs
sudo journalctl -u control-panel-backup-daemon.service -f

# Stop service
sudo systemctl stop control-panel-backup-daemon.service

# Start service
sudo systemctl start control-panel-backup-daemon.service
```

## Best Practices

1. **Schedule backups during low-usage hours** (e.g., 2:00-5:00 AM)
2. **Use appropriate retention policies** based on data importance
3. **Exclude temporary and cache files** to save space
4. **Monitor disk space** regularly with `check-destination`
5. **Test restoration** periodically to ensure backup integrity
6. **Set different priorities** for different data types

## Troubleshooting

### Daemon Not Starting

```bash
# Check service status
sudo systemctl status control-panel-backup-daemon.service

# View logs
sudo journalctl -u control-panel-backup-daemon.service -n 50
```

### Backup Failing

```bash
# Check destination space
control-panel backup check-destination

# View backup history for errors
control-panel backup history --limit 5
```

### Source Not Found

```bash
# List configured sources
control-panel backup list-sources

# Verify path exists
ls -la /path/to/source
```

## Files

| File | Description |
|------|-------------|
| `scripts/backup_config.py` | Configuration management |
| `scripts/backup_manager.py` | Backup execution (rsync) |
| `scripts/backup_daemon.py` | Background daemon |
| `scripts/backup_cli.py` | Command-line interface |
| `backup-daemon.service` | Systemd service definition |
| `~/.local/share/control-panel/backup/` | Configuration and state |

## Related Commands

```bash
# Full system status including backup
control-panel status

# Interactive menu with backup option
control-panel interactive
```
