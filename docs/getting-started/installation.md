# Installation Guide

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- rsync
- systemd (for background services)
- External HD with ext4 filesystem

## Installation Steps

### 1. Clone or Copy the Repository

```bash
git clone https://github.com/mateus/control-panel.git
cd control-panel
```

### 2. Run Initial Sync

The `sync` command copies scripts to `~/scripts/` and creates a global symlink:

```bash
./control_panel.sh sync
```

This will:
- Create `~/scripts/` directory
- Copy Python scripts to `~/scripts/`
- Create symlink at `~/.local/bin/control-panel`
- Verify installation

### 3. Verify Installation

```bash
control-panel status
```

### 4. Install Systemd Services (Optional)

For automatic keepalive:

```bash
sudo ln -s /path/to/control-panel/panel-keepalive.service /etc/systemd/system/
sudo systemctl enable panel-keepalive.service
sudo systemctl start panel-keepalive.service
```

For automatic backups:

```bash
sudo ln -s /path/to/control-panel/backup-daemon.service /etc/systemd/system/
sudo systemctl enable backup-daemon.service
sudo systemctl start backup-daemon.service
```

## Configuration

Edit configuration in `scripts/cli_manager.py`:

```python
self.hd_mount_point = "/media/mateus/Servidor"
self.hd_uuid = "35feb867-8ee2-49a9-a1a5-719a67e3975a"
self.hd_label = "Servidor"
self.docker_compose_dir = Path("/home/mateus")
```

Or in `scripts/backup_config.py` for backup settings.

## Docker Setup

Ensure your `docker-compose.yml` is in the configured directory with your services defined.

## Troubleshooting

### Python Import Errors

Ensure you're using the correct Python path:

```bash
which python3
./venv/bin/python3 scripts/cli_manager.py
```

### Permission Denied

The script uses `sudo` for mount operations. Ensure your user has sudo access without password prompt for specific commands, or add your user to appropriate groups.