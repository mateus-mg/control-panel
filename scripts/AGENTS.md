# Scripts - Python Modules

**Purpose:** Backup subsystem and Python CLI for Control Panel

## STRUCTURE

```
scripts/
├── cli_manager.py        # Main CLI dispatcher (Rich interface)
├── backup_cli.py         # Backup subcommand handler
├── backup_config.py      # JSON config persistence
├── backup_daemon.py      # Background scheduler daemon
├── backup_manager.py     # rsync backup execution
├── log_config.py         # Structured logging setup
└── log_formatter.py      # Custom log formatting
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add backup subcommand | `backup_cli.py` | Add an argparse subparser and register it in the local `commands` mapping |
| Change backup behavior | `backup_manager.py` | rsync args, retention logic |
| Modify scheduling | `backup_daemon.py` | Cron-like loop, sleep intervals |
| Update config schema | `backup_config.py` | JSON structure, validation |
| Change logging | `log_config.py` | Log levels, file rotation |
| Add main CLI command | `cli_manager.py` | `COMMANDS` dict + method |

## CONVENTIONS

### Module Design
- **NO `__init__.py`** — modules are standalone, not a package
- **Import pattern:** `from scripts.backup_config import X` (never relative)
- **One class per module:** Each `backup_*.py` exports one primary class

### Configuration
- Backup data directory: `~/.local/share/control-panel/backup/`
- Config file: `.backup_config`
- State/history files: `.backup_state.json`, `backup_history.json`
- Backup destination path stored in config (not hardcoded)

## ANTI-PATTERNS

### What NOT To Do
- Don't import with `from backup_config import X` — always use `scripts.` prefix
- Don't catch bare `except:` — use `except Exception as e:` minimum
- Don't modify files in `~/scripts/` directly — use project dir
- Don't add `__init__.py` — breaks the standalone module pattern

### Common Issues
| Issue | Solution |
|-------|----------|
| Missing scripts prefix | Use `from scripts.backup_config import X` |
| Broad exception catching | Catch specific exceptions |
| Real path in tests | Patch `Path.home()` with `tmp_path` |

## TESTING

### Test File Mapping
| Module | Test File |
|--------|-----------|
| `backup_config.py` | `tests/test_backup_config.py` |
| `backup_manager.py` | `tests/test_backup_manager.py` |
| `backup_daemon.py` | `tests/test_backup_daemon.py` |
| `cli_manager.py` | `tests/test_cli_manager_init.py` |

### Required Setup
Every test file MUST mock `log_config` BEFORE importing backup modules:
```python
sys.modules['log_config'] = MagicMock()
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.backup_config import BackupConfigManager
```

### Fixtures
- `mock_backup_structure` — autouse fixture (from conftest.py)
- `tmp_path` + `monkeypatch` — for mocking `Path.home()`

## COMMANDS

```bash
pytest tests/test_backup_config.py -v     # Run specific test
pytest tests/                            # Run all tests
pytest tests/ --cov=scripts              # Optional: run with coverage (requires pytest-cov)
python3 -c "from scripts.backup_config import BackupConfigManager; print('OK')"
```
