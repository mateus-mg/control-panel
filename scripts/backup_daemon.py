#!/usr/bin/env python3
"""
Backup Daemon

Background service for scheduled backups.
Manages individual schedules per source directory.
"""

import time
import signal
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

# Add scripts directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from backup_config import BackupConfigManager
from backup_manager import BackupManager
from log_config import get_logger, log_success, log_error, log_warning, log_info

logger = get_logger("Backup")


class BackupDaemon:
    """Background daemon for scheduled backups"""

    def __init__(self):
        self.config_manager = BackupConfigManager()
        self.backup_manager = BackupManager()
        self.running = True
        self.pid_file = Path.home() / '.local' / 'share' / 'control-panel' / 'backup' / '.daemon.pid'

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        log_info(logger, "Received shutdown signal")
        self.running = False

    def run(self):
        """Main daemon loop"""
        # Write PID file
        self.pid_file.write_text(str(os.getpid()))

        # Update state
        self.config_manager.update_state(
            daemon={
                'status': 'running',
                'started_at': datetime.now().isoformat(),
                'pid': os.getpid(),
                'uptime_seconds': 0
            }
        )

        log_info(logger, "Backup daemon started")
        start_time = time.time()

        try:
            while self.running:
                now = datetime.now()
                sources = self.config_manager.get_enabled_sources()

                # Check each source for backup
                for source in sources:
                    if self._should_run_backup(source, now):
                        success, stats = self.backup_manager.run_backup(source=source)

                        if success:
                            log_success(logger, f"Backup completed for {source['path']}")
                        else:
                            log_error(logger, f"Backup failed for {source['path']}: {stats.get('errors', [])}")

                # Cleanup old backups after any backup run
                self.backup_manager.cleanup_old_backups()

                # Update uptime
                uptime = int(time.time() - start_time)
                state = self.config_manager.get_state()
                state['daemon']['uptime_seconds'] = uptime
                self.config_manager._save_state(state)

                # Sleep until next check (max 60 seconds)
                sleep_time = self._calculate_sleep_time(sources, now)
                time.sleep(min(60, sleep_time))

        except Exception as e:
            log_error(logger, f"Daemon error: {e}")
        finally:
            # Cleanup
            self.pid_file.unlink(missing_ok=True)
            self.config_manager.update_state(
                daemon={'status': 'stopped'}
            )
            log_info(logger, "Backup daemon stopped")

    def _should_run_backup(self, source: Dict, now: datetime) -> bool:
        """Check if a backup should run for this source now"""
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

        # Check if backup already ran today for this source
        last_backup = self.config_manager.get_state().get('last_backup')
        if last_backup:
            last_backup_time = datetime.fromisoformat(last_backup['started_at'])
            if last_backup_time.date() == now.date():
                return False

        return True

    def _calculate_sleep_time(self, sources: list, now: datetime) -> float:
        """Calculate seconds until next backup check"""
        min_sleep = 60.0  # Default check interval

        for source in sources:
            schedule = source.get('schedule', {})
            if not schedule.get('enabled', True):
                continue

            schedule_time = schedule.get('time', '02:00')
            hour, minute = map(int, schedule_time.split(':'))

            # Calculate next occurrence of this time
            next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_time <= now:
                next_time += timedelta(days=1)

            # Adjust for weekly/monthly schedules
            frequency = schedule.get('frequency', 'daily')
            if frequency == 'weekly':
                allowed_days = schedule.get('days_of_week', ['sunday'])
                day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                while day_names[next_time.weekday()] not in allowed_days:
                    next_time += timedelta(days=1)
            elif frequency == 'monthly':
                day_of_month = schedule.get('day_of_month', 1)
                while next_time.day != day_of_month:
                    next_time += timedelta(days=1)

            sleep_time = (next_time - now).total_seconds()
            min_sleep = min(min_sleep, sleep_time)

        return max(0, min_sleep)

    def is_running(self) -> bool:
        """Check if daemon is running"""
        if not self.pid_file.exists():
            return False

        try:
            pid = int(self.pid_file.read_text())
            os.kill(pid, 0)  # Check if process exists
            return True
        except (ProcessLookupError, ValueError):
            return False

    def get_status(self) -> Dict:
        """Get daemon status"""
        state = self.config_manager.get_state()
        return {
            'running': self.is_running(),
            **state.get('daemon', {})
        }

    def stop(self):
        """Stop the daemon"""
        if not self.pid_file.exists():
            return False

        try:
            pid = int(self.pid_file.read_text())
            os.kill(pid, signal.SIGTERM)
            return True
        except (ProcessLookupError, ValueError):
            return False


def run_daemon():
    """Run the backup daemon"""
    daemon = BackupDaemon()
    daemon.run()


def stop_daemon():
    """Stop the backup daemon"""
    daemon = BackupDaemon()
    if daemon.stop():
        log_success(logger, "Backup daemon stopped")
    else:
        log_warning(logger, "Backup daemon is not running")


def daemon_status():
    """Show daemon status"""
    daemon = BackupDaemon()
    status = daemon.get_status()

    if status['running']:
        print("Backup Daemon Status")
        print("  Status: running")
        print(f"  PID: {status.get('pid', 'N/A')}")
        print(f"  Started: {status.get('started_at', 'N/A')}")
        print(f"  Uptime: {status.get('uptime_seconds', 0)} seconds")
    else:
        print("Backup Daemon Status")
        print("  Status: stopped")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "stop":
            stop_daemon()
        elif command == "status":
            daemon_status()
        else:
            print(f"Unknown command: {command}")
            print("Usage: backup_daemon.py [run|stop|status]")
    else:
        run_daemon()
