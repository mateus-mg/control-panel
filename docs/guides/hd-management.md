# HD Management Guide

## Overview

The Control Panel provides comprehensive external HD drive management with UUID-based detection, automatic mounting, and keepalive monitoring.

## Key Features

- **UUID-based detection**: Mounts drives by UUID, not device name (stable across reboots)
- **Automatic directory creation**: Creates mount point with correct permissions
- **Keepalive monitoring**: Prevents drive from sleeping/spinning down
- **Safe unmount**: Syncs data before unmounting

## Configuration

Edit these variables in `scripts/cli_manager.py`:

```python
self.hd_mount_point = "/media/<username>/<drive>"
self.hd_uuid = "<your-hd-uuid>"
self.hd_label = "<your-drive-label>"
self.hd_type = "ext4"  # filesystem type
```

### Finding Your Drive UUID

```bash
sudo blkid
```

Look for your drive (e.g., `/dev/sdb1`) and copy the UUID.

## Commands

### Mount HD

```bash
control-panel mount
```

This will:
1. Check if already mounted
2. Create mount point directory if needed
3. Set correct ownership
4. Mount the drive by UUID
5. Verify mount was successful

### Unmount HD

```bash
control-panel unmount
```

This will:
1. Stop all Docker containers
2. Sync filesystem
3. Unmount the drive safely

### Check Mount Status

```bash
control-panel check
```

Shows all current mounts and their usage.

### Force Remount

```bash
control-panel force-mount
```

Forces a complete remount cycle (unmount → fix → mount).

### Fix Mount Point

```bash
control-panel fix
```

Repairs mount point permissions and structure.

## Keepalive Mode

Keepalive prevents the drive from sleeping and ensures it remounts if disconnected.

### Automatic (Recommended)

Install the systemd service:

```bash
sudo ln -s /path/to/control-panel/panel-keepalive.service /etc/systemd/system/
sudo systemctl enable panel-keepalive.service
sudo systemctl start panel-keepalive.service
```

### Manual

```bash
control-panel keepalive
```

The keepalive service:
- Checks mount status every 60 seconds
- Touches a marker file every 10 minutes
- Retries mount up to 5 times on failure
- Logs all operations

## Troubleshooting

### Drive Not Mounting

```bash
# Check if drive is detected
sudo blkid

# Check mount point permissions
ls -la /media/<username>/<drive>

# Check dmesg for errors
dmesg | tail
```

### Permission Denied

Ensure your user owns the mount point:

```bash
sudo chown -R $USER:$USER /media/<username>/<drive>
```

### Docker Containers Can't Access Drive

Add your user to the docker group and ensure mount point has correct permissions.
