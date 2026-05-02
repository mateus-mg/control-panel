# Control Panel - Project Knowledge Base

**Generated:** 2026-05-02T23:46:42+01:00  
**Commit:** 16cb879  
**Branch:** fix/documentation-links

## OVERVIEW

Hybrid Bash/Python home server management system. Manages external HD mounts, Docker containers (media stack), and automated backups. Designed for personal/home server use with systemd service integration.

**Core Stack:** Bash (orchestration) + Python 3.12 (complex logic) + systemd + Docker + rsync

## STRUCTURE

```
./
├── control_panel.sh          # Main entry (929 lines, all-in-one bash)
├── control-panel             # Bash wrapper (auto-syncs from HD → Python)
├── scripts/                  # Python modules (backup subsystem + CLI)
│   ├── cli_manager.py        # Python CLI dispatcher
│   ├── backup_*.py           # Backup system (cli, config, daemon, manager)
│   └── log_*.py              # Logging utilities
├── tests/                    # pytest suite (mirrors scripts/ structure)
├── docs/                     # MkDocs documentation site
├── *.service                 # systemd unit files
└── mkdocs.yml                # Documentation config
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new CLI command | `scripts/cli_manager.py` | Update the `main()` if/elif dispatch chain and any interactive menu handling; implement the command method |
| Modify backup behavior | `scripts/backup_manager.py` | rsync logic, retention cleanup |
| Change backup scheduling | `scripts/backup_daemon.py` | Cron-like scheduler loop |
| Update backup config | `scripts/backup_config.py` | Persistence in `~/.local/share/control-panel/backup/` (`.backup_config`, `.backup_state.json`) |
| Add test for backup | `tests/test_backup_*.py` | Mirror scripts/ structure |
| Change HD mount logic | `control_panel.sh` | UUID-based mounting |
| Modify Docker commands | `control_panel.sh` (lines 700+) | docker-compose wrapper |
| Update docs | `docs/` | Auto-deploys to GitHub Pages |
| Service configuration | `*.service` files | Hardcoded paths: `/home/mateus`, `/media/mateus/Servidor` |

## CODE MAP

### Entry Points
| Symbol | Type | File | Role |
|--------|------|------|------|
| `control_panel.sh` | Script | root | Main orchestration (HD + Docker) |
| `auto_sync()` | Function | `control-panel` | Wrapper: sync → venv → Python |
| `CLIManager` | Class | `cli_manager.py` | Python command dispatcher |
| `BackupCLI` | Class | `backup_cli.py` | Backup subcommand handler |

### Key Classes (Python)
| Symbol | File | Purpose |
|--------|------|---------|
| `BackupConfigManager` | `backup_config.py` | JSON config CRUD |
| `BackupManager` | `backup_manager.py` | Execute rsync, manage retention |
| `BackupDaemon` | `backup_daemon.py` | Background scheduler |
| `LogConfig` | `log_config.py` | Structured logging setup |

## CONVENTIONS

### File Organization
- **Bash**: Single monolithic script (`control_panel.sh`) over modular files
- **Python**: Flat `scripts/` directory, typically used without `__init__.py`
- **Tests**: Mirror `scripts/` → `tests/` naming (e.g., `test_backup_manager.py`)
- **Imports**: Dual-mode. Use direct sibling imports like `from backup_config import X` when modules run with `scripts/` on `sys.path`; `scripts.*` imports may also work when `scripts` is imported as a namespace package. Follow the surrounding file's existing style, and do not assume a single import form is universal.

### Testing
- Framework: pytest
- Fixtures: `conftest.py` with `autouse=True` mocks
- Pattern: Patch `Path.home()` → `tmp_path` for isolation
- Required: Mock `log_config` module before importing backup modules

### Configuration
- Backup config: XDG-compliant (`~/.local/share/control-panel/`)
- Log file: `~/.control-panel.log` (not standard Python logging)
- Hardcoded paths: `/media/mateus/Servidor`, `/home/mateus`

### Documentation
- MkDocs Material with Mermaid diagrams
- Auto-deploys to GitHub Pages on push to main
- Python API docs via mkdocstrings

## ANTI-PATTERNS (THIS PROJECT)

### Code Quality Issues
| Issue | Location | Fix |
|-------|----------|-----|
| Bare `except:` | `cli_manager.py:1057` | Use `except Exception as e:` |
| Catch-all `except Exception` | `cli_manager.py` (30+ times) | Catch specific exceptions |
| Hardcoded user paths | `*.service` files, config | Extract to env vars |

### What NOT To Do
- **Don't** add `__init__.py` to `scripts/` — modules are standalone, not a package
- **Don't** use `pytest.ini` — project uses defaults (no config file exists)
- **Don't** expect dev/prod requirements split — only `requirements-test.txt`
- **Don't** modify `~/scripts/` directly — always edit in project dir and run `control-panel sync`

## UNIQUE STYLES

### Auto-Sync Architecture
The `control-panel` wrapper performs auto-sync on every invocation:
1. Check if HD mounted at `/media/mateus/Servidor/scripts/control-panel/`
2. Copy `.py` files from HD to `~/scripts/`
3. Activate venv, delegate to Python CLI

**Implication:** Scripts in `~/scripts/` are ephemeral copies. Always edit in project dir.

### Hybrid Command Dispatch
Commands flow: `control_panel.sh` → `control-panel` wrapper → `cli_manager.py` → `backup_cli.py` (if backup subcommand)

Some commands stay in Bash (mount/unmount), others forwarded to Python.

### Systemd Integration
- **keepalive service**: Touches HD every 10min to prevent sleep
- **backup-daemon**: Runs backup scheduler in background
- Both use hardcoded user paths — not portable

## COMMANDS

```bash
# Development
pytest tests/                    # Run all tests
pytest tests/test_backup_config.py -v   # Run specific test file
bash -n control_panel.sh         # Syntax check bash

# Documentation
mkdocs serve                     # Preview docs locally
mkdocs build                     # Build to site/

# Installation
./scripts/install-service.sh              # Install systemd keepalive
./scripts/install-backup-service.sh       # Install backup daemon
./scripts/install-global.sh               # Global symlink setup
```

## NOTES

### Hardcoded Values (Non-Portable)
```bash
HD_UUID="35feb867-8ee2-49a9-a1a5-719a67e3975a"
HD_MOUNT_POINT="/media/mateus/Servidor"
DOCKER_COMPOSE_DIR="/home/mateus"
```

### CI Behavior
- Tests run with mocked `Path.home()` to avoid touching real directories
- `conftest.py` patches `_ensure_backup_structure` automatically
- Shellcheck runs but errors suppressed (`|| true`)

### Log Rotation
- Main log uses size-based rotation via `RotatingFileHandler`
- Log file rotates when it reaches 10 MB, keeping up to 5 backup files
- Old logs are archived automatically as rotated log files

### Backup Storage Layout
```
<destination>/backups/
├── daily/backup-YYYY-MM-DD_HH-MM/
├── weekly/backup-YYYY-Www_HH-MM/
├── monthly/backup-YYYY-MM_HH-MM/
└── logs/
```

Each backup contains: files + `_metadata.json`
