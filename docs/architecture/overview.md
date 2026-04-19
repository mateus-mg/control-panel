# Architecture Overview

## System Design

The Control Panel follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│  Entry Points                                                │
│  ├── control-panel (Bash wrapper → Python CLI)               │
│  ├── control_panel.sh (Legacy compatibility)                 │
│  └── Python CLI (cli_manager.py)                            │
├─────────────────────────────────────────────────────────────┤
│  CLI Layer (cli_manager.py)                                 │
│  └── Rich-based interactive menus                           │
├─────────────────────────────────────────────────────────────┤
│  Backup Subsystem                                           │
│  ├── backup_cli.py      (CLI interface)                     │
│  ├── backup_manager.py  (Business logic - rsync execution)  │
│  ├── backup_config.py   (Configuration persistence)         │
│  └── backup_daemon.py   (Background scheduler)              │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure                                             │
│  ├── log_config.py      (Logging with rotation)            │
│  ├── log_formatter.py   (Structured log formatting)        │
│  ├── Docker             (Container platform)                │
│  └── systemd            (Service management)                │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Dual Entry Points

The system uses both Bash and Python:
- **Bash** (`control_panel.sh`): Legacy compatibility, simple commands, systemd integration
- **Python** (`cli_manager.py`): Interactive menus, complex logic, Rich UI

### 2. Backup Strategy

The backup subsystem uses **rsync with hard links** for efficient incremental backups:

- First backup: Full copy
- Subsequent backups: Hard links to unchanged files
- Only modified files consume additional disk space

### 3. Configuration Storage

Configuration is stored in `~/.local/share/control-panel/` following XDG Base Directory Specification:

```
~/.local/share/control-panel/
├── backup/
│   ├── .backup_config       # Main configuration
│   ├── .backup_state.json   # Runtime state
│   ├── backup_history.json  # Backup records
│   └── .daemon.pid          # Daemon PID file
└── control_panel.log        # Application logs
```

### 4. Service Architecture

Two systemd services manage background operations:

| Service | Purpose | Trigger |
|---------|---------|---------|
| `panel-keepalive.service` | Keep HD active, auto-remount | Always running |
| `backup-daemon.service` | Scheduled backups | Timer-based |

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Primary Language | Python 3.12 | Core logic |
| UI Framework | Rich | Terminal UI |
| Backup Tool | rsync | File synchronization |
| Container Platform | Docker | Service isolation |
| Service Manager | systemd | Background services |
| Logging | logging + RotatingFileHandler | Log rotation |

## Docker Services Managed

| Service | Image | Purpose |
|---------|-------|---------|
| nextcloud | linuxserver/nextcloud | Cloud storage |
| nextcloud-db | postgres:15-alpine | Nextcloud database |
| nextcloud-redis | redis:7-alpine | Nextcloud cache |
| onlyoffice | onlyoffice/documentserver | Document editing |
| kavita | jvmilazz0/kavita | E-book reader |
| navidrome | deluan/navidrome | Music streaming |
