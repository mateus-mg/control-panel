# Systemd Services Guide

## Overview

The Control Panel uses systemd services for background operations that need to run automatically on boot.

## Installed Services

### panel-keepalive.service

Keeps the external HD active and ensures it remounts if disconnected.

**Service file:** `panel-keepalive.service`

**Features:**
- Starts automatically on boot
- Checks mount status every 60 seconds
- Touches marker file every 10 minutes to prevent drive sleep
- Retries mount up to 5 times on failure
- Auto-restarts on failure

### backup-daemon.service

Runs scheduled backups in the background.

**Service file:** `backup-daemon.service`

**Features:**
- Starts automatically on boot
- Runs backups according to configured schedule
- Manages individual schedules per source
- Cleans up old backups based on retention policy

## Managing Services

### Check Status

```bash
# Keepalive service
control-panel keepalive-status

# Backup daemon
control-panel backup daemon-status

# Any systemd service
control-panel service-status <service-name>
```

### Start/Stop/Restart

```bash
# Keepalive
control-panel keepalive-start
control-panel keepalive-stop
control-panel keepalive-restart

# Backup daemon
control-panel backup daemon-start
control-panel backup daemon-stop
control-panel backup daemon-restart

# Generic (any service)
control-panel service-start <service-name>
control-panel service-stop <service-name>
control-panel service-restart <service-name>
```

### View Logs

```bash
# Keepalive logs
control-panel keepalive-logs
control-panel keepalive-logs -f  # follow mode

# Backup daemon logs
control-panel backup daemon-logs

# Generic logs
control-panel service-logs <service-name>
control-panel service-logs <service-name> -f  # follow mode
```

### Enable/Disable on Boot

```bash
# Enable (start on boot)
control-panel keepalive-enable

# Disable (don't start on boot)
control-panel keepalive-disable
```

## Manual Service Management

You can also use systemctl directly:

```bash
# Check status
sudo systemctl status control-panel-keepalive.service

# View logs
sudo journalctl -u control-panel-keepalive.service -f

# Start/Stop
sudo systemctl start control-panel-keepalive.service
sudo systemctl stop control-panel-keepalive.service

# Restart
sudo systemctl restart control-panel-keepalive.service

# Enable on boot
sudo systemctl enable control-panel-keepalive.service

# Disable on boot
sudo systemctl disable control-panel-keepalive.service
```

## Service Files Location

System-wide services:
```
/etc/systemd/system/
```

Project source files:
```
/path/to/control-panel/panel-keepalive.service
/path/to/control-panel/backup-daemon.service
```

## Installation

To install a service:

```bash
# Create symlink
sudo ln -s /path/to/control-panel/panel-keepalive.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable --now control-panel-keepalive.service
```

## Troubleshooting

### Service Won't Start

```bash
# Check detailed logs
sudo journalctl -u control-panel-keepalive.service -n 50

# Verify service file exists
ls -la /etc/systemd/system/control-panel-keepalive.service

# Reload systemd
sudo systemctl daemon-reload
```

### Service Starts but Stops Immediately

```bash
# Check for crashes
sudo journalctl -u control-panel-keepalive.service --since "5 minutes ago"

# Verify the ExecStart path is correct in the service file
```

### Service Not Starting on Boot

```bash
# Check if enabled
sudo systemctl is-enabled control-panel-keepalive.service

# Check boot logs
sudo journalctl -b -u control-panel-keepalive.service
```
