# 📦 Backup System Architecture

## Overview

The backup subsystem follows the same architecture pattern as the existing keepalive service, using Python for the daemon logic and systemd for service management.

## Architecture

### Service Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      System Boot                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              systemd reads unit files                        │
│         /etc/systemd/system/control-panel-backup-daemon.service │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           Service enabled? (systemctl is-enabled)            │
│                    YES → Start service                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              ExecStart: control-panel backup-daemon-run      │
│              (via /home/mateus/.local/bin/control-panel)     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              cli_manager.py receives command                 │
│              command == "backup-daemon-run"                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              from backup_daemon import run_daemon            │
│              run_daemon()                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              BackupDaemon.run() - Main loop                  │
│              - Check each source schedule                    │
│              - Run backup if due                             │
│              - Cleanup old backups                           │
│              - Sleep 60 seconds                              │
│              - Repeat                                        │
└─────────────────────────────────────────────────────────────┘
```

## Files Structure

```
/media/mateus/Servidor/scripts/control-panel/
├── scripts/
│   ├── cli_manager.py          # Main CLI entry point
│   ├── backup_config.py        # Configuration management
│   ├── backup_manager.py       # Backup execution (rsync)
│   ├── backup_daemon.py        # Daemon logic
│   └── backup_cli.py           # CLI commands
├── backup-daemon.service       # Systemd unit file
└── install-backup-service.sh   # Installation script
```

## Systemd Service

### Unit File: `backup-daemon.service`

```ini
[Unit]
Description=Control Panel Backup Daemon
After=network.target local-fs.target

[Service]
Type=simple
User=mateus
ExecStart=/home/mateus/.local/bin/control-panel backup-daemon-run
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
```

### Key Points

1. **No dedicated Python script for daemon** - Uses `cli_manager.py` like keepalive
2. **Wrapper script** - `/home/mateus/.local/bin/control-panel` routes commands
3. **Auto-start on boot** - `systemctl enable` creates symlink in `multi-user.target.wants`
4. **Restart policy** - Restarts on failure after 5 minutes

## Installation

```bash
sudo ./install-backup-service.sh
```

This script:
1. Stops existing service (if running)
2. Copies unit file to `/etc/systemd/system/`
3. Reloads systemd daemon
4. **Enables service** (starts on boot)
5. Starts service
6. Verifies enablement

## Boot Sequence

1. **System boots**
2. **systemd starts** and reads all unit files
3. **Finds enabled services** in `/etc/systemd/system/*.wants/`
4. **Starts `control-panel-backup-daemon.service`** (if enabled)
5. **Service runs** `control-panel backup-daemon-run`
6. **Daemon loop begins** - checks schedules every 60 seconds

## Manual Control

```bash
# Start (now)
sudo systemctl start control-panel-backup-daemon.service

# Stop
sudo systemctl stop control-panel-backup-daemon.service

# Restart
sudo systemctl restart control-panel-backup-daemon.service

# Enable (boot)
sudo systemctl enable control-panel-backup-daemon.service

# Disable (boot)
sudo systemctl disable control-panel-backup-daemon.service

# Status
sudo systemctl status control-panel-backup-daemon.service

# Logs
sudo journalctl -u control-panel-backup-daemon.service -f
```

## Verification

```bash
# Check if enabled for boot
systemctl is-enabled control-panel-backup-daemon.service
# Output: enabled (will start on boot)

# Check if running
systemctl is-active control-panel-backup-daemon.service
# Output: active (running)

# View PID
systemctl show --property MainPID control-panel-backup-daemon.service
```

## Comparison: Keepalive vs Backup Daemon

| Aspect | Keepalive | Backup Daemon |
|--------|-----------|---------------|
| Service | `control-panel-keepalive.service` | `control-panel-backup-daemon.service` |
| Command | `control-panel keepalive` | `control-panel backup-daemon-run` |
| Entry | `cli_manager.py` | `cli_manager.py` |
| Function | `keepalive_hd_optimized()` | `run_daemon()` |
| Install | `install-service.sh` | `install-backup-service.sh` |
| Boot start | `systemctl enable` | `systemctl enable` |

## Configuration

Backup configuration is stored in:
```
~/.local/share/control-panel/backup/.backup_config
```

State file:
```
~/.local/share/control-panel/backup/.backup_state.json
```

## Daemon Behavior

The backup daemon:
1. **Wakes up every 60 seconds**
2. **Checks each enabled source** for scheduled backup time
3. **Runs backup** if current time matches source schedule
4. **Cleans up** old backups based on retention policy
5. **Updates state** file with statistics
6. **Sleeps** until next check

## Schedule Checking

For each source, daemon checks:
- Is schedule enabled?
- Is current time within 5 minutes of scheduled time?
- Is it the correct day (for weekly/monthly)?
- Did backup already run today?

If all conditions match → run backup.

## Backup Execution

Uses rsync with hard links:
```bash
rsync -av --delete --stats --link-dest=<previous-backup> \
  /source/path/ /backup/destination/daily/backup-2026-02-27_02-00/
```

Benefits:
- **Incremental** - Only changed files are copied
- **Hard links** - Unchanged files use links (save space)
- **Full appearance** - Each backup looks complete
- **Fast restore** - Direct file access, no extraction needed

## Troubleshooting

### Service not starting on boot

```bash
# Check if enabled
systemctl is-enabled control-panel-backup-daemon.service

# If not enabled
sudo systemctl enable control-panel-backup-daemon.service
```

### Service failed to start

```bash
# Check status
sudo systemctl status control-panel-backup-daemon.service

# View logs
sudo journalctl -u control-panel-backup-daemon.service -n 50

# Common issues:
# - Python import errors (check scripts are in place)
# - Permission errors (check User=mateus)
# - Path errors (check ExecStart path)
```

### Daemon running but not backing up

```bash
# Check configuration
control-panel backup config

# Check sources
control-panel backup list-sources

# Check next backup times
# (shown in list-sources output)

# Manual backup to test
control-panel backup run
```

## Best Practices

1. **Install and enable service** after configuration
2. **Test with manual backup** before relying on schedule
3. **Monitor logs** for first few days
4. **Verify boot start** after system reboot
5. **Check disk space** regularly

## Security

- Runs as user `mateus` (not root)
- Read access to source directories only
- Write access to backup destination only
- No network access required (local backups)
