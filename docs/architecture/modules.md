# Module Reference

## Module Relationships

The system consists of these Python modules organized by responsibility:

```
CLI Layer
├── cli_manager.py        # Main entry point, interactive menus
└── backup_cli.py        # Backup subsystem CLI

Backup Subsystem
├── backup_manager.py     # Backup execution (rsync)
├── backup_config.py      # Configuration persistence
└── backup_daemon.py     # Background scheduler

Logging
├── log_config.py        # Centralized logging
└── log_formatter.py     # Structured formatting
```

**Dependencies:**
- `backup_cli.py` imports from `backup_manager`, `backup_config`, `backup_daemon`
- All modules use `log_config.py` for logging

---

## cli_manager.py

**Purpose:** Main entry point providing interactive CLI menus using Rich library.

**Key Classes:**
- `CLIManager`: Main CLI controller

**Key Methods:**

| Method | Description |
|--------|-------------|
| `show_interactive_menu()` | Display main menu loop |
| `show_docker_menu()` | Docker management submenu |
| `show_backup_menu()` | Backup subsystem submenu |
| `show_hd_menu()` | HD drive management submenu |
| `show_systemd_menu()` | Systemd service management submenu |
| `mount_hd_interactive()` | Mount external drive |
| `unmount_hd_interactive()` | Unmount external drive |
| `start_docker_interactive()` | Start Docker containers |
| `stop_docker_interactive()` | Stop Docker containers |
| `keepalive_hd_interactive()` | Monitor and keep HD active |

**Configuration Example:**
```python
hd_mount_point = "/media/<username>/<drive>"
hd_uuid = "<your-hd-uuid>"
hd_label = "<your-drive-label>"
docker_compose_dir = Path.home() / "path/to/docker-compose"
```

---

## backup_cli.py

**Purpose:** Command-line interface for backup subsystem.

**Key Classes:**
- `BackupCLI`: Backup command handler

**Key Methods:**

| Method | Description |
|--------|-------------|
| `daemon_start()` | Start backup daemon |
| `daemon_stop()` | Stop backup daemon |
| `daemon_restart()` | Restart backup daemon |
| `daemon_status()` | Show daemon status |
| `set_destination()` | Configure backup location |
| `add_source()` | Add backup source |
| `remove_source()` | Remove backup source |
| `list_sources()` | List configured sources |
| `run_backup()` | Execute manual backup |
| `show_stats()` | View backup statistics |
| `show_history()` | View backup history |
| `set_schedule()` | Configure global schedule |
| `set_retention()` | Configure retention policy |

---

## backup_manager.py

**Purpose:** Core backup execution logic using rsync.

**Key Classes:**
- `BackupManager`: Backup orchestration

**Key Methods:**

| Method | Description |
|--------|-------------|
| `run_backup(source)` | Execute backup for source(s) |
| `_get_backup_type()` | Determine daily/weekly/monthly |
| `_should_backup_now()` | Check if backup should run |
| `_parse_rsync_stats()` | Parse backup statistics |
| `cleanup_old_backups()` | Apply retention policy |
| `verify_backup()` | Validate backup integrity |
| `restore_file()` | Restore single file |
| `restore_directory()` | Restore directory |

**Backup Types:**
- `daily`: Regular backups (all other days)
- `weekly`: Sunday backups
- `monthly`: 1st of month backups

---

## backup_config.py

**Purpose:** Configuration persistence and management.

**Key Classes:**
- `BackupDestination`: Destination configuration dataclass
- `BackupSchedule`: Schedule configuration dataclass
- `RetentionPolicy`: Retention configuration dataclass
- `BackupConfigManager`: Configuration CRUD operations

**Key Methods:**

| Method | Description |
|--------|-------------|
| `set_backup_destination()` | Set backup location |
| `set_schedule()` | Configure global schedule |
| `set_retention()` | Configure retention policy |
| `add_source()` | Add backup source |
| `remove_source()` | Remove backup source |
| `get_enabled_sources()` | Get active sources |
| `set_source_schedule()` | Per-source schedule |
| `set_source_retention()` | Per-source retention |
| `get_history()` | Retrieve backup history |
| `check_destination_space()` | Verify available space |

**Config Location:** `~/.local/share/control-panel/backup/.backup_config`

---

## backup_daemon.py

**Purpose:** Background service for scheduled backups.

**Key Classes:**
- `BackupDaemon`: Background scheduler

**Key Methods:**

| Method | Description |
|--------|-------------|
| `run()` | Main daemon loop |
| `_should_run_backup()` | Check if source should backup |
| `_calculate_sleep_time()` | Compute until next backup |
| `is_running()` | Check daemon status |
| `stop()` | Graceful shutdown |

**Daemon Loop:**
1. Write PID to file
2. Update state to "running"
3. Check each enabled source
4. Run backup if scheduled time matches
5. Sleep until next check (max 60 seconds)
6. Repeat

---

## log_config.py

**Purpose:** Centralized logging with rotation.

**Key Functions:**

| Function | Description |
|----------|-------------|
| `get_logger(name)` | Get or create logger instance |
| `log_success()` | Log success message |
| `log_error()` | Log error message |
| `log_warning()` | Log warning message |
| `log_info()` | Log info message |
| `log_mount()` | Log mount operation |
| `log_docker()` | Log Docker operation |
| `log_systemd()` | Log systemd operation |
| `set_request_id()` | Enable operation tracking |
| `is_verbose_logging()` | Check DEBUG level |
| `set_console_log_level()` | Suppress console output |

**Log Files:**
- Console: Rich-formatted output
- File: `~/.local/share/control-panel/control_panel.log`
- Rotation: 10MB max, 5 backup files

---

## log_formatter.py

**Purpose:** Structured log formatting utilities.

**Key Classes:**
- `LogSection`: Hierarchical log formatter
- `LogBuilder`: Fluent log builder

**Key Methods (LogSection):**

| Method | Description |
|--------|-------------|
| `major_header()` | Section header (level 1) |
| `minor_header()` | Subsection header (level 2) |
| `section()` | Multi-item section |
| `inline_section()` | Compact inline section |
| `progress_line()` | Progress indicator |
| `error_block()` | Error display |
| `format_duration()` | Human-readable duration |
| `format_size()` | Human-readable file size |
