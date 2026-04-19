# Quick Start Guide

## Common Operations

### Starting the Server

```bash
# Mount external HD
control-panel mount

# Start all Docker containers
control-panel start

# Check status
control-panel status
```

### Stopping the Server

```bash
# Stop all Docker containers
control-panel stop

# Unmount HD (waits for sync)
control-panel unmount
```

### Interactive Menu

For a menu-driven interface:

```bash
control-panel
```

This opens an interactive menu with all available operations.

### Managing Docker Containers

```bash
# Start specific service
control-panel start nextcloud

# Stop specific service
control-panel stop navidrome

# Restart with clean containers
control-panel restart kavita --clean

# View logs
control-panel logs onlyoffice -f

# Check health
control-panel health
```

### Managing Backups

```bash
# View backup status
control-panel backup stats

# Run backup now
control-panel backup run

# Add new source
control-panel backup add-source /path/to/data \
  --frequency daily --time 02:00 --priority high
```

### Viewing Logs

```bash
# View script logs
control-panel view-logs 100

# Follow Docker logs
control-panel logs nextcloud -f

# Systemd logs
sudo journalctl -u panel-keepalive.service -f
```

## Keyboard Shortcuts

In interactive menu:
- `Ctrl+C`: Cancel current operation
- `Enter`: Confirm selection
- Numbers `1-9`: Direct menu selection