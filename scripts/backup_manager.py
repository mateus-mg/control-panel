#!/usr/bin/env python3
"""
Backup Manager

Handles backup execution using rsync with hard links for incremental backups.
Supports individual schedules and retention policies per source directory.
"""

import subprocess
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from backup_config import BackupConfigManager


class BackupManager:
    """Manages backup operations"""

    def __init__(self):
        self.config_manager = BackupConfigManager()
        self.rsync_path = shutil.which('rsync')
        if not self.rsync_path:
            raise RuntimeError("rsync not found in PATH")

    def run_backup(self, source: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """
        Execute a backup operation.

        Args:
            source: Specific source to backup. If None, backs up all enabled sources.

        Returns:
            Tuple of (success, stats_dict)
        """
        config = self.config_manager.get_config()
        destination_base = Path(config['destination']['full_path'])

        # Determine backup type and directory
        now = datetime.now()
        backup_type = self._get_backup_type(now)
        timestamp = now.strftime('%Y-%m-%d_%H-%M')
        backup_dir = destination_base / backup_type / f'backup-{timestamp}'
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Get previous backup for hard links
        previous_backup = self._get_previous_backup(backup_type)

        stats = {
            'started_at': now.isoformat(),
            'path': str(backup_dir),
            'backup_type': backup_type,
            'sources': [],
            'errors': [],
            'total_files': 0,
            'total_size': 0
        }

        success = True

        # Determine which sources to backup
        sources_to_backup = []
        if source:
            # Backup specific source
            sources_to_backup = [source]
        else:
            # Backup all enabled sources
            sources_to_backup = self.config_manager.get_enabled_sources()

        # Backup each source
        for src in sources_to_backup:
            source_path = Path(src['path'])
            if not source_path.exists():
                stats['errors'].append(f"Source not found: {source_path}")
                success = False
                continue

            # Check if this source should be backed up now
            if not self._should_backup_now(src, now):
                continue

            # Build rsync command
            cmd = [
                self.rsync_path,
                '-av',
                '--delete',
                '--stats'
            ]

            # Add hard link option if previous backup exists
            if previous_backup:
                cmd.extend(['--link-dest', str(previous_backup)])

            # Add exclude patterns
            for pattern in src.get('exclude_patterns', []):
                cmd.extend(['--exclude', pattern])

            # Calculate relative path for destination
            rel_path = source_path.relative_to(Path(src['path']).anchor)
            dest_path = backup_dir / str(rel_path).lstrip('/')

            # Add source and destination
            cmd.extend([f'{source_path}/', str(dest_path)])

            # Execute
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode not in (0, 24):  # 24 = some files vanished
                stats['errors'].append(f"rsync failed for {source_path}: {result.stderr}")
                success = False

            # Parse stats from rsync output
            source_stats = self._parse_rsync_stats(result.stdout)
            source_stats['path'] = str(source_path)
            stats['sources'].append(source_stats)
            stats['total_files'] += source_stats.get('files_count', 0)
            stats['total_size'] += source_stats.get('total_size', 0)

        # Write metadata
        stats['finished_at'] = datetime.now().isoformat()
        stats['duration_seconds'] = (
            datetime.fromisoformat(stats['finished_at']) -
            datetime.fromisoformat(stats['started_at'])
        ).total_seconds()
        stats['status'] = 'success' if success and not stats['errors'] else 'partial'
        self._write_metadata(backup_dir, stats)

        # Update state
        self.config_manager.update_state(
            last_backup=stats
        )

        # Add to history
        self.config_manager.add_history_entry({
            'id': f'backup-{timestamp}',
            'type': backup_type,
            'started_at': stats['started_at'],
            'finished_at': stats['finished_at'],
            'duration_seconds': stats['duration_seconds'],
            'status': stats['status'],
            'total_files': stats['total_files'],
            'total_size': stats['total_size'],
            'path': str(backup_dir),
            'errors': stats['errors']
        })

        # Cleanup old backups
        self.cleanup_old_backups()

        return success, stats

    def _get_backup_type(self, now: datetime) -> str:
        """Determine backup type based on current date"""
        # Monthly backup on 1st of month
        if now.day == 1:
            return 'monthly'
        # Weekly backup on Sunday
        if now.weekday() == 6:  # Sunday
            return 'weekly'
        # Daily backup otherwise
        return 'daily'

    def _should_backup_now(self, source: Dict, now: datetime) -> bool:
        """Check if a source should be backed up at this time"""
        schedule = source.get('schedule', {})

        if not schedule.get('enabled', True):
            return False

        frequency = schedule.get('frequency', 'daily')
        schedule_time = schedule.get('time', '02:00')

        # Parse scheduled time
        hour, minute = map(int, schedule_time.split(':'))

        # Check if current time matches scheduled time (within 5 minute window)
        if not (now.hour == hour and abs(now.minute - minute) <= 5):
            return False

        # Check frequency-specific conditions
        if frequency == 'weekly':
            allowed_days = schedule.get('days_of_week', ['sunday'])
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            if day_names[now.weekday()] not in allowed_days:
                return False

        elif frequency == 'monthly':
            day_of_month = schedule.get('day_of_month', 1)
            if now.day != day_of_month:
                return False

        elif frequency == 'custom':
            allowed_days = schedule.get('days_of_week', [])
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            if day_names[now.weekday()] not in allowed_days:
                return False

        return True

    def _get_previous_backup(self, backup_type: str) -> Optional[Path]:
        """Get the most recent backup for hard links"""
        config = self.config_manager.get_config()
        backup_dir = Path(config['destination']['full_path']) / backup_type

        if not backup_dir.exists():
            return None

        backups = sorted(backup_dir.glob('backup-*'), reverse=True)
        # Skip the current backup directory
        return backups[1] if len(backups) > 1 else None

    def _parse_rsync_stats(self, output: str) -> Dict:
        """Parse rsync --stats output"""
        stats = {}
        for line in output.split('\n'):
            if 'Number of files' in line:
                try:
                    stats['files_count'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'Number of regular files transferred' in line:
                try:
                    stats['files_transferred'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'Total file size' in line:
                try:
                    stats['total_size'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'Total bytes sent' in line:
                try:
                    stats['bytes_sent'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
        return stats

    def _write_metadata(self, backup_dir: Path, stats: Dict):
        """Write backup metadata"""
        metadata_file = backup_dir / '_metadata.json'
        metadata_file.write_text(json.dumps(stats, indent=2))

    def get_backup_history(self, limit: int = 10) -> List[Dict]:
        """Get list of recent backups"""
        return self.config_manager.get_history(limit)

    def get_space_used(self) -> int:
        """Calculate total space used by backups"""
        config = self.config_manager.get_config()
        backup_dir = Path(config['destination']['full_path'])

        if not backup_dir.exists():
            return 0

        total = 0
        for f in backup_dir.rglob('*'):
            if f.is_file():
                total += f.stat().st_size
        return total

    def get_space_info(self) -> Dict:
        """Get detailed space information"""
        config = self.config_manager.get_config()
        backup_path = Path(config['destination']['full_path'])

        if not backup_path.exists():
            return {"error": "Backup directory does not exist"}

        try:
            total, used, free = shutil.disk_usage(str(backup_path))
            return {
                "total_gb": round(total / (1024 ** 3), 2),
                "used_gb": round(used / (1024 ** 3), 2),
                "free_gb": round(free / (1024 ** 3), 2),
                "usage_percent": round((used / total) * 100, 1),
                "backups_size_gb": round(self.get_space_used() / (1024 ** 3), 2)
            }
        except Exception as e:
            return {"error": str(e)}

    def cleanup_old_backups(self):
        """Remove backups exceeding retention policy"""
        config = self.config_manager.get_config()
        retention = config['retention']
        backup_base = Path(config['destination']['full_path'])

        # Cleanup each backup type
        for backup_type in ['daily', 'weekly', 'monthly']:
            backup_dir = backup_base / backup_type
            if not backup_dir.exists():
                continue

            backups = sorted(backup_dir.glob('backup-*'))

            # Determine retention count based on type
            if backup_type == 'daily':
                max_count = retention.get('daily_count', 7)
            elif backup_type == 'weekly':
                max_count = retention.get('weekly_count', 4)
            else:  # monthly
                max_count = retention.get('monthly_count', 6)

            # Remove oldest backups exceeding count
            if len(backups) > max_count:
                for backup in backups[:-max_count]:
                    shutil.rmtree(backup)

        # Remove backups exceeding max age
        max_age_days = retention.get('max_age_days', 180)
        if max_age_days > 0:
            cutoff = datetime.now() - timedelta(days=max_age_days)
            for backup_type in ['daily', 'weekly', 'monthly']:
                backup_dir = backup_base / backup_type
                if not backup_dir.exists():
                    continue

                for backup in backup_dir.glob('backup-*'):
                    # Get backup date from directory name
                    try:
                        backup_date_str = backup.name.replace('backup-', '')
                        backup_date = datetime.strptime(backup_date_str.split('_')[0], '%Y-%m-%d')
                        if backup_date < cutoff:
                            shutil.rmtree(backup)
                    except (ValueError, OSError):
                        continue

    def verify_backup(self, backup_path: str) -> Tuple[bool, List[str]]:
        """
        Verify backup integrity.

        Args:
            backup_path: Path to backup directory

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        backup_dir = Path(backup_path)

        if not backup_dir.exists():
            errors.append(f"Backup directory does not exist: {backup_path}")
            return False, errors

        # Check metadata file
        metadata_file = backup_dir / '_metadata.json'
        if not metadata_file.exists():
            errors.append("Metadata file missing")
            return False, errors

        try:
            metadata = json.loads(metadata_file.read_text())
            if metadata.get('status') not in ['success', 'partial']:
                errors.append(f"Backup status is not success: {metadata.get('status')}")
        except json.JSONDecodeError:
            errors.append("Invalid metadata file")

        return len(errors) == 0, errors

    def restore_file(self, backup_path: str, file_path: str, dest_path: str) -> bool:
        """
        Restore a specific file from backup.

        Args:
            backup_path: Path to backup directory
            file_path: Relative path of file in backup
            dest_path: Destination path for restored file

        Returns:
            True if successful, False otherwise
        """
        backup_dir = Path(backup_path)
        source_file = backup_dir / file_path
        dest_file = Path(dest_path)

        if not source_file.exists():
            return False

        # Create destination directory if needed
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(source_file, dest_file)
        return True

    def restore_directory(self, backup_path: str, dest_path: str) -> bool:
        """
        Restore entire backup to destination.

        Args:
            backup_path: Path to backup directory
            dest_path: Destination path for restoration

        Returns:
            True if successful, False otherwise
        """
        backup_dir = Path(backup_path)

        if not backup_dir.exists():
            return False

        # Use rsync for restoration
        cmd = [
            self.rsync_path,
            '-av',
            f'{backup_dir}/',
            dest_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
