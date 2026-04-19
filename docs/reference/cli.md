# CLI Reference

## Main Commands

### control-panel

Main entry point. Without arguments, starts interactive menu.

```bash
control-panel [command] [options]
```

### HD Management

| Command | Description |
|---------|-------------|
| `control-panel mount` | Mount external HD |
| `control-panel unmount` | Unmount HD (syncs first) |
| `control-panel status` | Show HD and Docker status |
| `control-panel check` | List active mounts |
| `control-panel fix` | Fix mount point permissions |
| `control-panel keepalive` | Manual keepalive mode |
| `control-panel force-mount` | Force remount sequence |

### Docker Management

| Command | Description |
|---------|-------------|
| `control-panel start [service]` | Start containers |
| `control-panel stop [service]` | Stop containers |
| `control-panel restart [service]` | Restart containers |
| `control-panel ps` | List running containers |
| `control-panel logs <service>` | View service logs |
| `control-panel stats [service]` | Show resource usage |
| `control-panel health` | Check container health |

### Docker Maintenance

| Command | Description |
|---------|-------------|
| `control-panel services` | List available services |
| `control-panel pull` | Pull updated images |
| `control-panel rebuild [service]` | Rebuild containers |
| `control-panel update-all` | Smart update |
| `control-panel networks` | List Docker networks |
| `control-panel volumes` | List Docker volumes |
| `control-panel prune` | Clean unused resources |

### Backup Subsystem

| Command | Description |
|---------|-------------|
| `control-panel backup daemon-start` | Start backup daemon |
| `control-panel backup daemon-stop` | Stop backup daemon |
| `control-panel backup daemon-status` | Check daemon status |
| `control-panel backup set-destination <path>` | Set backup location |
| `control-panel backup list-sources` | List backup sources |
| `control-panel backup add-source <path>` | Add backup source |
| `control-panel backup remove-source <path>` | Remove source |
| `control-panel backup run` | Run backup now |
| `control-panel backup stats` | Show backup statistics |
| `control-panel backup history` | Show backup history |
| `control-panel backup config` | Show configuration |

### Systemd Services

| Command | Description |
|---------|-------------|
| `control-panel keepalive-status` | Check keepalive service |
| `control-panel keepalive-start` | Start keepalive |
| `control-panel keepalive-stop` | Stop keepalive |
| `control-panel keepalive-restart` | Restart keepalive |
| `control-panel keepalive-logs [-f]` | View logs |
| `control-panel service-<action> <name>` | Manage any service |

### Utilities

| Command | Description |
|---------|-------------|
| `control-panel view-logs [n]` | View script logs |
| `control-panel sync` | Sync scripts to ~/scripts |
| `control-panel diagnose` | Full diagnostic |

## Options

### Global Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help |
| `--version` | Show version |

### Service Options

| Option | Description |
|--------|-------------|
| `--clean` | Remove old containers |
| `--no-deps` | Skip dependencies |
| `--cache` | Use build cache |

### Backup Options

| Option | Description |
|--------|-------------|
| `--frequency` | Backup frequency |
| `--time` | Backup time (HH:MM) |
| `--recursive` | Include subdirectories |
| `--exclude` | Exclude patterns |