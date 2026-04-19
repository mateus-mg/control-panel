# Control Panel - Server Management System

A comprehensive server management system for home servers, providing unified control over external HD drives and Docker containers through an interactive CLI interface.

## Features

- **HD Management**: Mount/unmount external drives with UUID-based detection, keepalive monitoring
- **Docker Container Management**: Start/stop/restart containers, view logs, pull images
- **Backup Subsystem**: Automated incremental backups with rsync and hard links
- **Systemd Integration**: Keepalive and backup daemon services
- **Interactive CLI**: Rich terminal UI with menus and colored output

## Quick Start

```bash
# Install (creates symlink)
./control-panel sync

# Interactive menu
control-panel

# Mount HD
control-panel mount

# Start Docker containers
control-panel start

# View status
control-panel status
```

## Architecture

The system consists of several Python modules organized by responsibility:

| Module | Purpose |
|--------|---------|
| `cli_manager.py` | Main CLI entry point with interactive menus |
| `backup_cli.py` | Backup subsystem command-line interface |
| `backup_manager.py` | Backup execution with rsync |
| `backup_config.py` | Configuration and state persistence |
| `backup_daemon.py` | Background backup scheduler |
| `log_config.py` | Centralized logging with rotation |

## Documentation

- [Installation Guide](getting-started/installation.md)
- [Quick Start](getting-started/quick-start.md)
- [Architecture Overview](architecture/overview.md)
- [CLI Reference](reference/cli.md)
- [Backup System Guide](guides/backup-guide.md)