#!/usr/bin/env python3
"""
Backup Configuration Manager

Handles backup configuration, state, and history persistence.
Manages individual schedule and retention settings per source directory.
"""

import json
import shutil
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class BackupDestination:
    """Backup destination configuration"""
    base_path: str
    backup_folder: str = "backups"
    auto_create: bool = True
    min_free_space_gb: int = 5

    @property
    def full_path(self) -> str:
        return os.path.join(self.base_path, self.backup_folder)


@dataclass
class BackupSchedule:
    """Backup schedule configuration"""
    enabled: bool = True
    frequency: str = "daily"  # hourly, daily, weekly, monthly, custom
    time: str = "02:00"  # HH:MM format
    timezone: str = "America/Sao_Paulo"
    days_of_week: List[str] = field(default_factory=lambda: [
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
    ])
    day_of_month: Optional[int] = None  # 1-28 for monthly backups


@dataclass
class RetentionPolicy:
    """Backup retention policy"""
    daily_count: int = 7
    weekly_count: int = 4
    monthly_count: int = 6
    max_age_days: int = 180
    min_free_space_gb: int = 10
    emergency_cleanup_threshold_gb: int = 5


class BackupConfigManager:
    """Manages backup configuration persistence"""

    def __init__(self):
        self.config_dir = Path.home() / '.local' / 'share' / 'control-panel' / 'backup'
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / '.backup_config'
        self.state_file = self.config_dir / '.backup_state.json'
        self.history_file = self.config_dir / 'backup_history.json'

        self.config = self._load_or_create_config()
        self.state = self._load_or_create_state()

        # Ensure backup destination structure exists
        self._ensure_backup_structure()

    def _load_or_create_config(self) -> Dict:
        """Load existing config or create default"""
        if self.config_file.exists():
            return json.loads(self.config_file.read_text())

        default = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),

            "destination": {
                "base_path": "/media/mateus/Servidor",
                "backup_folder": "backups",
                "full_path": "/media/mateus/Servidor/backups",
                "auto_create": True,
                "min_free_space_gb": 5
            },

            "schedule": {
                "enabled": True,
                "frequency": "daily",
                "time": "02:00",
                "timezone": "America/Sao_Paulo",
                "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                "day_of_month": None
            },

            "retention": {
                "daily_count": 7,
                "weekly_count": 4,
                "monthly_count": 6,
                "max_age_days": 180,
                "min_free_space_gb": 10,
                "emergency_cleanup_threshold_gb": 5
            },

            "sources": [
                {
                    "id": "src_001",
                    "path": "/media/mateus/Servidor/containers/config",
                    "recursive": True,
                    "enabled": True,
                    "added_at": datetime.now().isoformat(),
                    "exclude_patterns": ["*.tmp", "*.log", "__pycache__"],
                    "schedule": {
                        "enabled": True,
                        "frequency": "daily",
                        "time": "02:00",
                        "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                        "day_of_month": None
                    },
                    "retention": {
                        "daily_count": 7,
                        "weekly_count": 4,
                        "monthly_count": 6,
                        "max_age_days": 180
                    },
                    "priority": "high",
                    "description": "Docker configurations - daily critical backup"
                },
                {
                    "id": "src_002",
                    "path": "/media/mateus/Servidor/scripts",
                    "recursive": True,
                    "enabled": True,
                    "added_at": datetime.now().isoformat(),
                    "exclude_patterns": ["*.pyc", "__pycache__", ".git"],
                    "schedule": {
                        "enabled": True,
                        "frequency": "weekly",
                        "time": "03:00",
                        "days_of_week": ["sunday"],
                        "day_of_month": None
                    },
                    "retention": {
                        "daily_count": 0,
                        "weekly_count": 12,
                        "monthly_count": 6,
                        "max_age_days": 365
                    },
                    "priority": "medium",
                    "description": "Custom scripts - weekly backup"
                }
            ],

            "options": {
                "compression": False,
                "verify_after_backup": True,
                "notify_on_error": True,
                "notify_on_success": False,
                "max_log_size_mb": 10,
                "log_rotation_count": 5,
                "rsync_options": ["-a", "-v", "--delete", "--stats"],
                "checksum_verification": True,
                "parallel_backups": False,
                "stop_on_error": False
            }
        }
        self._save_config(default)
        return default

    def _ensure_backup_structure(self):
        """Verify and create backup directory structure if needed"""
        dest = self.config['destination']
        backup_path = Path(dest['full_path'])

        # Check if base path exists
        if not Path(dest['base_path']).exists():
            raise RuntimeError(f"Base path does not exist: {dest['base_path']}")

        # Create backup folder if auto_create is enabled
        if dest.get('auto_create', True) and not backup_path.exists():
            try:
                backup_path.mkdir(parents=True, exist_ok=True)
                backup_path.chmod(0o755)

                # Create subdirectories
                (backup_path / 'daily').mkdir(exist_ok=True)
                (backup_path / 'weekly').mkdir(exist_ok=True)
                (backup_path / 'monthly').mkdir(exist_ok=True)
                (backup_path / 'logs').mkdir(exist_ok=True)

            except PermissionError:
                raise RuntimeError(f"No permission to create backup directory: {backup_path}")
            except OSError as e:
                raise RuntimeError(f"Failed to create backup directory: {e}")

        # Verify write permissions
        if not os.access(str(backup_path), os.W_OK):
            raise RuntimeError(f"No write permission for backup directory: {backup_path}")

        # Check available space
        try:
            total, used, free = shutil.disk_usage(str(backup_path))
            free_gb = free / (1024 ** 3)
            min_free = dest.get('min_free_space_gb', 5)

            if free_gb < min_free:
                print(f"⚠️  WARNING: Low disk space on backup destination: {free_gb:.1f}GB free (minimum: {min_free}GB)")

        except Exception:
            pass  # Ignore if can't check disk space

    def _load_or_create_state(self) -> Dict:
        """Load existing state or create default"""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())

        default = {
            "daemon": {
                "status": "stopped",
                "started_at": None,
                "pid": None,
                "uptime_seconds": 0
            },
            "last_backup": None,
            "next_backup": None,
            "statistics": {
                "total_backups": 0,
                "successful_backups": 0,
                "failed_backups": 0,
                "total_space_used_bytes": 0
            }
        }
        self._save_state(default)
        return default

    def _save_config(self, config: Dict):
        """Save configuration to file"""
        self.config_file.write_text(json.dumps(config, indent=2))

    def _save_state(self, state: Dict):
        """Save state to file"""
        self.state_file.write_text(json.dumps(state, indent=2))

    # ========== Destination Configuration Methods ==========

    def set_backup_destination(self, base_path: str, backup_folder: str = "backups") -> bool:
        """Set the backup destination path"""
        base_path = str(Path(base_path).resolve())

        if not Path(base_path).exists():
            return False

        self.config['destination']['base_path'] = base_path
        self.config['destination']['backup_folder'] = backup_folder
        self.config['destination']['full_path'] = os.path.join(base_path, backup_folder)
        self.config['updated_at'] = datetime.now().isoformat()

        # Re-validate structure
        self._ensure_backup_structure()
        self._save_config(self.config)
        return True

    def get_backup_destination(self) -> Dict:
        """Get current backup destination configuration"""
        return self.config['destination']

    def check_destination_space(self) -> Dict:
        """Check available disk space on backup destination"""
        dest = self.config['destination']
        backup_path = Path(dest['full_path'])

        if not backup_path.exists():
            return {"exists": False, "error": "Destination does not exist"}

        try:
            total, used, free = shutil.disk_usage(str(backup_path))
            return {
                "exists": True,
                "total_gb": round(total / (1024 ** 3), 2),
                "used_gb": round(used / (1024 ** 3), 2),
                "free_gb": round(free / (1024 ** 3), 2),
                "usage_percent": round((used / total) * 100, 1),
                "minimum_free_gb": dest.get('min_free_space_gb', 5),
                "is_sufficient": (free / (1024 ** 3)) >= dest.get('min_free_space_gb', 5)
            }
        except Exception as e:
            return {"exists": True, "error": str(e)}

    # ========== Global Schedule Configuration Methods ==========

    def set_schedule(self, enabled: bool = True, frequency: str = "daily",
                     time: str = "02:00", days_of_week: List[str] = None) -> bool:
        """Configure global backup schedule"""
        valid_frequencies = ["hourly", "daily", "weekly", "monthly", "custom"]
        if frequency not in valid_frequencies:
            return False

        # Validate time format (HH:MM)
        try:
            hours, minutes = map(int, time.split(':'))
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                return False
        except ValueError:
            return False

        self.config['schedule']['enabled'] = enabled
        self.config['schedule']['frequency'] = frequency
        self.config['schedule']['time'] = time
        if days_of_week:
            self.config['schedule']['days_of_week'] = days_of_week
        self.config['updated_at'] = datetime.now().isoformat()
        self._save_config(self.config)
        return True

    def get_schedule(self) -> Dict:
        """Get current schedule configuration"""
        return self.config['schedule']

    def get_next_scheduled_time(self) -> datetime:
        """Calculate next scheduled backup time (global)"""
        schedule = self.config['schedule']
        now = datetime.now()

        # Parse scheduled time
        hour, minute = map(int, schedule['time'].split(':'))

        # Start with today at scheduled time
        next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If already passed today, start from tomorrow
        if next_time <= now:
            next_time += timedelta(days=1)

        # For custom frequency, check days of week
        if schedule['frequency'] == 'custom':
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            allowed_days = schedule.get('days_of_week', day_names)

            while day_names[next_time.weekday()] not in allowed_days:
                next_time += timedelta(days=1)

        return next_time

    # ========== Global Retention Configuration Methods ==========

    def set_retention(self, daily_count: int = 7, weekly_count: int = 4,
                      monthly_count: int = 6, max_age_days: int = 180,
                      min_free_space_gb: int = 10) -> bool:
        """Configure global retention policy"""
        if any(x < 0 for x in [daily_count, weekly_count, monthly_count, max_age_days, min_free_space_gb]):
            return False

        self.config['retention'] = {
            "daily_count": daily_count,
            "weekly_count": weekly_count,
            "monthly_count": monthly_count,
            "max_age_days": max_age_days,
            "min_free_space_gb": min_free_space_gb,
            "emergency_cleanup_threshold_gb": max(1, min_free_space_gb // 2)
        }
        self.config['updated_at'] = datetime.now().isoformat()
        self._save_config(self.config)
        return True

    def get_retention(self) -> Dict:
        """Get current retention policy"""
        return self.config['retention']

    # ========== Source Management Methods ==========

    def add_source(self, path: str, recursive: bool = True,
                   exclude_patterns: List[str] = None,
                   schedule: Dict = None,
                   retention: Dict = None,
                   priority: str = "medium",
                   description: str = "") -> bool:
        """Add a new backup source with individual schedule and retention"""
        path = str(Path(path).resolve())

        # Check if path exists
        if not Path(path).exists():
            return False

        # Check if already exists
        for source in self.config['sources']:
            if source['path'] == path:
                return False

        source_id = f"src_{len(self.config['sources']) + 1:03d}"

        # Default schedule (uses global settings if not specified)
        default_schedule = {
            "enabled": True,
            "frequency": "daily",
            "time": "02:00",
            "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            "day_of_month": None
        }

        # Default retention (uses global settings if not specified)
        default_retention = {
            "daily_count": 7,
            "weekly_count": 4,
            "monthly_count": 6,
            "max_age_days": 180
        }

        self.config['sources'].append({
            "id": source_id,
            "path": path,
            "recursive": recursive,
            "enabled": True,
            "added_at": datetime.now().isoformat(),
            "exclude_patterns": exclude_patterns or [],
            "schedule": schedule or default_schedule,
            "retention": retention or default_retention,
            "priority": priority,
            "description": description
        })
        self.config['updated_at'] = datetime.now().isoformat()
        self._save_config(self.config)
        return True

    def remove_source(self, path: str) -> bool:
        """Remove a backup source"""
        original_count = len(self.config['sources'])
        self.config['sources'] = [
            s for s in self.config['sources'] if s['path'] != path
        ]

        if len(self.config['sources']) < original_count:
            self.config['updated_at'] = datetime.now().isoformat()
            self._save_config(self.config)
            return True
        return False

    def toggle_source(self, path: str) -> Optional[bool]:
        """Toggle source enabled status"""
        for source in self.config['sources']:
            if source['path'] == path:
                source['enabled'] = not source['enabled']
                self.config['updated_at'] = datetime.now().isoformat()
                self._save_config(self.config)
                return source['enabled']
        return None

    def get_sources(self) -> List[Dict]:
        """Get all configured sources"""
        return self.config['sources']

    def get_enabled_sources(self) -> List[Dict]:
        """Get only enabled sources"""
        return [s for s in self.config['sources'] if s['enabled']]

    # ========== Individual Source Configuration Methods ==========

    def set_source_schedule(self, path: str, frequency: str = None,
                            time: str = None, days_of_week: List[str] = None,
                            day_of_month: int = None, enabled: bool = None) -> bool:
        """Configure individual schedule for a specific source directory"""
        path = str(Path(path).resolve())

        for source in self.config['sources']:
            if source['path'] == path:
                if frequency is not None:
                    valid_frequencies = ["hourly", "daily", "weekly", "monthly", "custom"]
                    if frequency not in valid_frequencies:
                        return False
                    source['schedule']['frequency'] = frequency

                if time is not None:
                    try:
                        hours, minutes = map(int, time.split(':'))
                        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                            return False
                    except ValueError:
                        return False
                    source['schedule']['time'] = time

                if days_of_week is not None:
                    source['schedule']['days_of_week'] = days_of_week

                if day_of_month is not None:
                    if not (1 <= day_of_month <= 28):
                        return False
                    source['schedule']['day_of_month'] = day_of_month

                if enabled is not None:
                    source['schedule']['enabled'] = enabled

                self.config['updated_at'] = datetime.now().isoformat()
                self._save_config(self.config)
                return True

        return False

    def set_source_retention(self, path: str, daily_count: int = None,
                             weekly_count: int = None, monthly_count: int = None,
                             max_age_days: int = None) -> bool:
        """Configure individual retention for a specific source directory"""
        path = str(Path(path).resolve())

        for source in self.config['sources']:
            if source['path'] == path:
                if daily_count is not None:
                    if daily_count < 0:
                        return False
                    source['retention']['daily_count'] = daily_count

                if weekly_count is not None:
                    if weekly_count < 0:
                        return False
                    source['retention']['weekly_count'] = weekly_count

                if monthly_count is not None:
                    if monthly_count < 0:
                        return False
                    source['retention']['monthly_count'] = monthly_count

                if max_age_days is not None:
                    if max_age_days < 0:
                        return False
                    source['retention']['max_age_days'] = max_age_days

                self.config['updated_at'] = datetime.now().isoformat()
                self._save_config(self.config)
                return True

        return False

    def get_source_schedule(self, path: str) -> Optional[Dict]:
        """Get schedule configuration for a specific source"""
        path = str(Path(path).resolve())

        for source in self.config['sources']:
            if source['path'] == path:
                return source['schedule']
        return None

    def get_source_retention(self, path: str) -> Optional[Dict]:
        """Get retention configuration for a specific source"""
        path = str(Path(path).resolve())

        for source in self.config['sources']:
            if source['path'] == path:
                return source['retention']
        return None

    def get_source_next_backup(self, path: str) -> Optional[datetime]:
        """Calculate next backup time for a specific source"""
        schedule = self.get_source_schedule(path)
        if not schedule or not schedule['enabled']:
            return None

        now = datetime.now()
        hour, minute = map(int, schedule['time'].split(':'))
        next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if next_time <= now:
            next_time += timedelta(days=1)

        frequency = schedule['frequency']

        if frequency == 'weekly':
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            allowed_days = schedule.get('days_of_week', ['sunday'])
            while day_names[next_time.weekday()] not in allowed_days:
                next_time += timedelta(days=1)

        elif frequency == 'monthly':
            day_of_month = schedule.get('day_of_month', 1)
            while next_time.day != day_of_month:
                next_time += timedelta(days=1)
                if next_time.month != now.month:
                    break

        elif frequency == 'custom':
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            allowed_days = schedule.get('days_of_week', day_names)
            while day_names[next_time.weekday()] not in allowed_days:
                next_time += timedelta(days=1)

        return next_time

    def list_sources(self) -> List[Dict]:
        """List all configured sources with their schedules"""
        sources = []
        for source in self.config['sources']:
            sources.append({
                "id": source['id'],
                "path": source['path'],
                "enabled": source['enabled'],
                "frequency": source['schedule']['frequency'],
                "time": source['schedule']['time'],
                "next_backup": self.get_source_next_backup(source['path']),
                "priority": source.get('priority', 'medium'),
                "description": source.get('description', '')
            })
        return sources

    # ========== State Management Methods ==========

    def update_state(self, **kwargs):
        """Update state fields"""
        for key, value in kwargs.items():
            if key in self.state:
                self.state[key] = value
        self._save_state(self.state)

    def get_config(self) -> Dict:
        """Get full configuration"""
        return self.config

    def get_state(self) -> Dict:
        """Get current state"""
        return self.state

    def add_history_entry(self, backup_info: Dict):
        """Add entry to backup history"""
        history = []
        if self.history_file.exists():
            history = json.loads(self.history_file.read_text())

        history.insert(0, backup_info)

        # Keep only last 100 entries
        history = history[:100]
        self.history_file.write_text(json.dumps(history, indent=2))

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get backup history"""
        if not self.history_file.exists():
            return []

        history = json.loads(self.history_file.read_text())
        return history[:limit]
