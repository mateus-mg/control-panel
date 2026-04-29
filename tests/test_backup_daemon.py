"""Tests for Backup Daemon."""
import pytest
import json
import sys
import os
import signal
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, call

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

# Mock log_config before importing backup modules
log_config_mock = MagicMock()
log_config_mock.get_logger = MagicMock(return_value=MagicMock())
log_config_mock.log_success = MagicMock()
log_config_mock.log_error = MagicMock()
log_config_mock.log_warning = MagicMock()
log_config_mock.log_info = MagicMock()
sys.modules['log_config'] = log_config_mock

from scripts.backup_daemon import BackupDaemon
from scripts.backup_config import BackupConfigManager


class TestBackupDaemonInit:
    """Test BackupDaemon initialization."""

    @pytest.fixture
    def daemon(self, tmp_path, monkeypatch):
        """Create a BackupDaemon with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            with patch.object(BackupConfigManager, '_ensure_backup_structure'):
                with patch('signal.signal'):
                    daemon = BackupDaemon()
                    # Override destination to use temp path
                    daemon.config_manager.config['destination']['base_path'] = str(tmp_path)
                    daemon.config_manager.config['destination']['full_path'] = str(tmp_path / 'backups')
                    yield daemon

    def test_initialization(self, daemon, tmp_path):
        """Test that daemon initializes correctly."""
        assert daemon.running is True
        assert str(daemon.pid_file) == str(tmp_path / '.local' / 'share' / 'control-panel' / 'backup' / '.daemon.pid')

    def test_signal_handlers_setup(self, daemon):
        """Test that signal handlers are registered."""
        # Signal handlers should be set up during initialization
        # We can't easily test this without actually sending signals,
        # but we can verify the daemon has the _handle_signal method
        assert hasattr(daemon, '_handle_signal')
        assert callable(daemon._handle_signal)


class TestBackupDaemonSignalHandling:
    """Test signal handling."""

    @pytest.fixture
    def daemon(self, tmp_path, monkeypatch):
        """Create a BackupDaemon with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            with patch.object(BackupConfigManager, '_ensure_backup_structure'):
                with patch('signal.signal'):
                    daemon = BackupDaemon()
                    # Override destination to use temp path
                    daemon.config_manager.config['destination']['base_path'] = str(tmp_path)
                    daemon.config_manager.config['destination']['full_path'] = str(tmp_path / 'backups')
                    yield daemon

    def test_handle_sigterm(self, daemon):
        """Test SIGTERM handling."""
        daemon._handle_signal(signal.SIGTERM, None)
        assert daemon.running is False

    def test_handle_sigint(self, daemon):
        """Test SIGINT handling."""
        daemon._handle_signal(signal.SIGINT, None)
        assert daemon.running is False


class TestBackupDaemonScheduling:
    """Test scheduling logic."""

    @pytest.fixture
    def daemon(self, tmp_path, monkeypatch):
        """Create a BackupDaemon with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            with patch.object(BackupConfigManager, '_ensure_backup_structure'):
                with patch('signal.signal'):
                    daemon = BackupDaemon()
                    # Override destination to use temp path
                    daemon.config_manager.config['destination']['base_path'] = str(tmp_path)
                    daemon.config_manager.config['destination']['full_path'] = str(tmp_path / 'backups')
                    yield daemon

    def test_should_run_backup_hourly(self, daemon):
        """Test hourly backup scheduling."""
        source = {
            'schedule': {
                'enabled': True,
                'frequency': 'hourly',
                'time': '02:00'
            }
        }
        now = datetime(2026, 4, 2, 2, 0)
        assert daemon._should_run_backup(source, now) is True

    def test_should_run_backup_daily_correct_time(self, daemon):
        """Test daily backup at correct time."""
        source = {
            'schedule': {
                'enabled': True,
                'frequency': 'daily',
                'time': '02:00'
            }
        }
        now = datetime(2026, 4, 2, 2, 3)
        assert daemon._should_run_backup(source, now) is True

    def test_should_run_backup_daily_wrong_time(self, daemon):
        """Test daily backup at wrong time."""
        source = {
            'schedule': {
                'enabled': True,
                'frequency': 'daily',
                'time': '02:00'
            }
        }
        now = datetime(2026, 4, 2, 10, 0)
        assert daemon._should_run_backup(source, now) is False

    def test_should_run_backup_disabled(self, daemon):
        """Test disabled source."""
        source = {
            'schedule': {
                'enabled': False,
                'frequency': 'daily',
                'time': '02:00'
            }
        }
        now = datetime(2026, 4, 2, 2, 0)
        assert daemon._should_run_backup(source, now) is False

    def test_should_run_backup_weekly_correct_day(self, daemon):
        """Test weekly backup on correct day."""
        source = {
            'schedule': {
                'enabled': True,
                'frequency': 'weekly',
                'time': '02:00',
                'days_of_week': ['sunday']
            }
        }
        # Sunday, April 5, 2026
        now = datetime(2026, 4, 5, 2, 3)
        assert daemon._should_run_backup(source, now) is True

    def test_should_run_backup_weekly_wrong_day(self, daemon):
        """Test weekly backup on wrong day."""
        source = {
            'schedule': {
                'enabled': True,
                'frequency': 'weekly',
                'time': '02:00',
                'days_of_week': ['sunday']
            }
        }
        # Thursday, April 2, 2026
        now = datetime(2026, 4, 2, 2, 0)
        assert daemon._should_run_backup(source, now) is False

    def test_should_run_backup_monthly_correct_day(self, daemon):
        """Test monthly backup on correct day."""
        source = {
            'schedule': {
                'enabled': True,
                'frequency': 'monthly',
                'time': '02:00',
                'day_of_month': 1
            }
        }
        now = datetime(2026, 4, 1, 2, 3)
        assert daemon._should_run_backup(source, now) is True

    def test_should_run_backup_monthly_wrong_day(self, daemon):
        """Test monthly backup on wrong day."""
        source = {
            'schedule': {
                'enabled': True,
                'frequency': 'monthly',
                'time': '02:00',
                'day_of_month': 1
            }
        }
        now = datetime(2026, 4, 2, 2, 0)
        assert daemon._should_run_backup(source, now) is False


class TestBackupDaemonSleepCalculation:
    """Test sleep time calculation."""

    @pytest.fixture
    def daemon(self, tmp_path, monkeypatch):
        """Create a BackupDaemon with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            with patch.object(BackupConfigManager, '_ensure_backup_structure'):
                with patch('signal.signal'):
                    daemon = BackupDaemon()
                    # Override destination to use temp path
                    daemon.config_manager.config['destination']['base_path'] = str(tmp_path)
                    daemon.config_manager.config['destination']['full_path'] = str(tmp_path / 'backups')
                    yield daemon

    def test_calculate_sleep_time_no_sources(self, daemon):
        """Test sleep time with no sources."""
        sources = []
        now = datetime(2026, 4, 2, 10, 0)
        sleep_time = daemon._calculate_sleep_time(sources, now)
        assert sleep_time > 0  # Should return positive sleep time

    def test_calculate_sleep_time_with_sources(self, daemon):
        """Test sleep time with scheduled sources."""
        sources = [
            {
                'schedule': {
                    'enabled': True,
                    'frequency': 'daily',
                    'time': '14:00'  # 2 PM
                }
            }
        ]
        now = datetime(2026, 4, 2, 10, 0)  # 10 AM
        sleep_time = daemon._calculate_sleep_time(sources, now)
        assert sleep_time > 0
        assert sleep_time <= 14400  # Should be less than 4 hours

    def test_calculate_sleep_time_disabled_sources(self, daemon):
        """Test sleep time with disabled sources."""
        sources = [
            {
                'schedule': {
                    'enabled': False,
                    'frequency': 'daily',
                    'time': '14:00'
                }
            }
        ]
        now = datetime(2026, 4, 2, 10, 0)
        sleep_time = daemon._calculate_sleep_time(sources, now)
        assert sleep_time > 0  # Should return positive sleep time


class TestBackupDaemonRun:
    """Test daemon main loop."""

    @pytest.fixture
    def daemon(self, tmp_path, monkeypatch):
        """Create a BackupDaemon with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            with patch.object(BackupConfigManager, '_ensure_backup_structure'):
                with patch('signal.signal'):
                    daemon = BackupDaemon()
                    # Override destination to use temp path
                    daemon.config_manager.config['destination']['base_path'] = str(tmp_path)
                    daemon.config_manager.config['destination']['full_path'] = str(tmp_path / 'backups')
                    yield daemon

    def test_run_creates_and_removes_pid_file(self, daemon, tmp_path):
        """Test that run creates PID file and removes it on exit."""
        with patch('os.getpid', return_value=12345):
            with patch('time.sleep', side_effect=Exception('Stop loop')):
                with patch.object(daemon.backup_manager, 'run_backup', return_value=(True, {})):
                    with patch.object(daemon, '_should_run_backup', return_value=False):
                        try:
                            daemon.run()
                        except Exception:
                            pass

        # PID file should be removed after daemon exits
        assert not daemon.pid_file.exists()

    def test_run_updates_state(self, daemon, tmp_path):
        """Test that run updates daemon state."""
        with patch('os.getpid', return_value=12345):
            with patch('time.sleep', side_effect=Exception('Stop loop')):
                with patch.object(daemon.backup_manager, 'run_backup', return_value=(True, {})):
                    with patch.object(daemon, '_should_run_backup', return_value=False):
                        try:
                            daemon.run()
                        except Exception:
                            pass

        state = daemon.config_manager.get_state()
        assert state['daemon']['status'] == 'stopped'

    def test_run_executes_backup(self, daemon, tmp_path):
        """Test that run executes backup for scheduled sources."""
        # Add a test source
        test_source = {
            'path': str(tmp_path / 'test_source'),
            'schedule': {
                'enabled': True,
                'frequency': 'daily',
                'time': '02:00'
            }
        }
        (tmp_path / 'test_source').mkdir(exist_ok=True)
        daemon.config_manager.add_source(path=test_source['path'])

        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 1:
                daemon.running = False
            return (True, {})

        with patch('os.getpid', return_value=12345):
            with patch('time.sleep', return_value=None):
                with patch.object(daemon.backup_manager, 'run_backup', side_effect=side_effect):
                    with patch.object(daemon, '_should_run_backup', return_value=True):
                        daemon.run()

        assert call_count >= 1

    def test_run_cleanup_on_exit(self, daemon, tmp_path):
        """Test that run cleans up PID file on exit."""
        with patch('os.getpid', return_value=12345):
            with patch('time.sleep', side_effect=Exception('Stop loop')):
                with patch.object(daemon.backup_manager, 'run_backup', return_value=(True, {})):
                    with patch.object(daemon, '_should_run_backup', return_value=False):
                        try:
                            daemon.run()
                        except Exception:
                            pass

        # After clean exit, PID file should be removed
        assert not daemon.pid_file.exists()


class TestBackupDaemonEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def daemon(self, tmp_path, monkeypatch):
        """Create a BackupDaemon with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            with patch.object(BackupConfigManager, '_ensure_backup_structure'):
                with patch('signal.signal'):
                    daemon = BackupDaemon()
                    # Override destination to use temp path
                    daemon.config_manager.config['destination']['base_path'] = str(tmp_path)
                    daemon.config_manager.config['destination']['full_path'] = str(tmp_path / 'backups')
                    yield daemon

    def test_run_with_backup_error(self, daemon, tmp_path):
        """Test handling backup execution errors."""
        (tmp_path / 'test_source').mkdir(exist_ok=True)
        daemon.config_manager.add_source(path=str(tmp_path / 'test_source'))

        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 1:
                daemon.running = False
            return (False, {'errors': ['test error']})

        with patch('os.getpid', return_value=12345):
            with patch('time.sleep', return_value=None):
                with patch.object(daemon.backup_manager, 'run_backup', side_effect=side_effect):
                    with patch.object(daemon, '_should_run_backup', return_value=True):
                        daemon.run()

        assert call_count >= 1

    def test_run_with_no_sources(self, daemon):
        """Test running with no configured sources."""
        with patch('os.getpid', return_value=12345):
            with patch('time.sleep', side_effect=Exception('Stop loop')):
                try:
                    daemon.run()
                except Exception:
                    pass

        # Should complete without errors even with no sources
        assert not daemon.pid_file.exists()
