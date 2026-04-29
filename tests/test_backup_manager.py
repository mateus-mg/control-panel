"""Tests for Backup Manager."""
import pytest
import json
import sys
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open

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

from scripts.backup_manager import BackupManager
from scripts.backup_config import BackupConfigManager


class TestBackupManagerInit:
    """Test BackupManager initialization."""

    @pytest.fixture
    def config_manager(self, tmp_path, monkeypatch):
        """Create a BackupConfigManager with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            with patch.object(BackupConfigManager, '_ensure_backup_structure'):
                manager = BackupConfigManager()
                # Override destination to use temp path
                manager.config['destination']['base_path'] = str(tmp_path)
                manager.config['destination']['full_path'] = str(tmp_path / 'backups')
                yield manager

    def test_initialization_with_rsync(self, config_manager):
        """Test that BackupManager initializes when rsync is available."""
        with patch('shutil.which', return_value='/usr/bin/rsync'):
            manager = BackupManager()
            assert manager.rsync_path == '/usr/bin/rsync'

    def test_initialization_without_rsync(self, config_manager):
        """Test that BackupManager raises error when rsync is not available."""
        with patch('shutil.which', return_value=None):
            with pytest.raises(RuntimeError, match="rsync not found"):
                BackupManager()


class TestBackupManagerBackupType:
    """Test backup type determination."""

    @pytest.fixture
    def backup_manager(self, tmp_path, monkeypatch):
        """Create a BackupManager with mocked dependencies."""
        with patch.object(Path, 'home', return_value=tmp_path):
            with patch.object(BackupConfigManager, '_ensure_backup_structure'):
                with patch('shutil.which', return_value='/usr/bin/rsync'):
                    manager = BackupManager()
                    # Override destination to use temp path
                    manager.config_manager.config['destination']['base_path'] = str(tmp_path)
                    manager.config_manager.config['destination']['full_path'] = str(tmp_path / 'backups')
                    yield manager

    def test_get_backup_type_monthly(self, backup_manager):
        """Test monthly backup on 1st of month."""
        now = datetime(2026, 4, 1, 2, 0)
        backup_type = backup_manager._get_backup_type(now)
        assert backup_type == 'monthly'

    def test_get_backup_type_weekly(self, backup_manager):
        """Test weekly backup on Sunday."""
        # April 5, 2026 is a Sunday
        now = datetime(2026, 4, 5, 2, 0)
        backup_type = backup_manager._get_backup_type(now)
        assert backup_type == 'weekly'

    def test_get_backup_type_daily(self, backup_manager):
        """Test daily backup on regular day."""
        # April 2, 2026 is a Thursday
        now = datetime(2026, 4, 2, 2, 0)
        backup_type = backup_manager._get_backup_type(now)
        assert backup_type == 'daily'


class TestBackupManagerShouldBackup:
    """Test backup scheduling logic."""

    @pytest.fixture
    def backup_manager(self, tmp_path, monkeypatch):
        """Create a BackupManager with mocked dependencies."""
        with patch.object(Path, 'home', return_value=tmp_path):
            with patch.object(BackupConfigManager, '_ensure_backup_structure'):
                with patch('shutil.which', return_value='/usr/bin/rsync'):
                    manager = BackupManager()
                    # Override destination to use temp path
                    manager.config_manager.config['destination']['base_path'] = str(tmp_path)
                    manager.config_manager.config['destination']['full_path'] = str(tmp_path / 'backups')
                    yield manager

    def test_should_backup_now_disabled(self, backup_manager):
        """Test that disabled schedule prevents backup."""
        source = {
            'schedule': {
                'enabled': False,
                'frequency': 'daily',
                'time': '02:00'
            }
        }
        now = datetime(2026, 4, 2, 2, 0)
        assert backup_manager._should_backup_now(source, now) is False

    def test_should_backup_now_wrong_time(self, backup_manager):
        """Test that wrong time prevents backup."""
        source = {
            'schedule': {
                'enabled': True,
                'frequency': 'daily',
                'time': '02:00'
            }
        }
        now = datetime(2026, 4, 2, 10, 0)
        assert backup_manager._should_backup_now(source, now) is False

    def test_should_backup_now_correct_time(self, backup_manager):
        """Test that correct time allows backup."""
        source = {
            'schedule': {
                'enabled': True,
                'frequency': 'daily',
                'time': '02:00'
            }
        }
        now = datetime(2026, 4, 2, 2, 3)
        assert backup_manager._should_backup_now(source, now) is True

    def test_should_backup_now_weekly_wrong_day(self, backup_manager):
        """Test weekly backup on wrong day."""
        source = {
            'schedule': {
                'enabled': True,
                'frequency': 'weekly',
                'time': '02:00',
                'days_of_week': ['sunday']
            }
        }
        # Thursday
        now = datetime(2026, 4, 2, 2, 0)
        assert backup_manager._should_backup_now(source, now) is False

    def test_should_backup_now_weekly_correct_day(self, backup_manager):
        """Test weekly backup on correct day."""
        source = {
            'schedule': {
                'enabled': True,
                'frequency': 'weekly',
                'time': '02:00',
                'days_of_week': ['sunday']
            }
        }
        # Sunday
        now = datetime(2026, 4, 5, 2, 3)
        assert backup_manager._should_backup_now(source, now) is True

    def test_should_backup_now_monthly_wrong_day(self, backup_manager):
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
        assert backup_manager._should_backup_now(source, now) is False

    def test_should_backup_now_monthly_correct_day(self, backup_manager):
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
        assert backup_manager._should_backup_now(source, now) is True


class TestBackupManagerRsyncStats:
    """Test rsync stats parsing."""

    @pytest.fixture
    def backup_manager(self, tmp_path, monkeypatch):
        """Create a BackupManager with mocked dependencies."""
        with patch.object(Path, 'home', return_value=tmp_path):
            with patch.object(BackupConfigManager, '_ensure_backup_structure'):
                with patch('shutil.which', return_value='/usr/bin/rsync'):
                    manager = BackupManager()
                    # Override destination to use temp path
                    manager.config_manager.config['destination']['base_path'] = str(tmp_path)
                    manager.config_manager.config['destination']['full_path'] = str(tmp_path / 'backups')
                    yield manager

    def test_parse_rsync_stats_complete(self, backup_manager):
        """Test parsing complete rsync stats output."""
        output = """Number of files: 1500
Number of regular files transferred: 50
Total file size: 104857600
Total bytes sent: 5242880"""

        stats = backup_manager._parse_rsync_stats(output)
        assert stats['files_count'] == 1500
        assert stats['files_transferred'] == 50
        assert stats['total_size'] == 104857600
        assert stats['bytes_sent'] == 5242880

    def test_parse_rsync_stats_empty(self, backup_manager):
        """Test parsing empty rsync stats output."""
        stats = backup_manager._parse_rsync_stats('')
        assert stats == {}

    def test_parse_rsync_stats_partial(self, backup_manager):
        """Test parsing partial rsync stats output."""
        output = "Number of files: 100\n"
        stats = backup_manager._parse_rsync_stats(output)
        assert stats['files_count'] == 100
        assert 'total_size' not in stats


class TestBackupManagerCleanup:
    """Test backup cleanup logic."""

    @pytest.fixture
    def backup_manager(self, tmp_path, monkeypatch):
        """Create a BackupManager with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            # Create backup destination
            backup_dir = tmp_path / 'backups'
            backup_dir.mkdir(parents=True, exist_ok=True)
            (backup_dir / 'daily').mkdir(exist_ok=True)
            (backup_dir / 'weekly').mkdir(exist_ok=True)
            (backup_dir / 'monthly').mkdir(exist_ok=True)
            (backup_dir / 'logs').mkdir(exist_ok=True)

            # Create some old backups
            for i in range(10):
                old_backup = backup_dir / 'daily' / f'backup-2026-04-{i+1:02d}_02-00'
                old_backup.mkdir(parents=True, exist_ok=True)
                (old_backup / 'test.txt').write_text('test')

            with patch('shutil.which', return_value='/usr/bin/rsync'):
                manager = BackupManager()
                yield manager

    def test_cleanup_old_backups_by_count(self, backup_manager, tmp_path):
        """Test cleanup removes backups exceeding count limit."""
        # Configure destination to tmp_path
        backup_manager.config_manager.set_backup_destination(str(tmp_path), 'backups')

        backup_manager.cleanup_old_backups()

        daily_dir = tmp_path / 'backups' / 'daily'
        backups = list(daily_dir.glob('backup-*'))
        assert len(backups) <= 7  # Default daily retention is 7

    def test_cleanup_old_backups_by_age(self, backup_manager, tmp_path):
        """Test cleanup removes backups exceeding age limit."""
        # Configure destination to tmp_path
        backup_manager.config_manager.set_backup_destination(str(tmp_path), 'backups')

        # Create a very old backup
        old_backup = tmp_path / 'backups' / 'daily' / 'backup-2025-01-01_02-00'
        old_backup.mkdir(parents=True, exist_ok=True)
        (old_backup / 'test.txt').write_text('test')

        backup_manager.cleanup_old_backups()

        assert not old_backup.exists()


class TestBackupManagerVerify:
    """Test backup verification."""

    @pytest.fixture
    def backup_manager(self, tmp_path, monkeypatch):
        """Create a BackupManager with mocked dependencies."""
        with patch.object(Path, 'home', return_value=tmp_path):
            with patch.object(BackupConfigManager, '_ensure_backup_structure'):
                with patch('shutil.which', return_value='/usr/bin/rsync'):
                    manager = BackupManager()
                    # Override destination to use temp path
                    manager.config_manager.config['destination']['base_path'] = str(tmp_path)
                    manager.config_manager.config['destination']['full_path'] = str(tmp_path / 'backups')
                    yield manager

    def test_verify_backup_valid(self, backup_manager, tmp_path):
        """Test verifying a valid backup."""
        backup_dir = tmp_path / 'valid_backup'
        backup_dir.mkdir()
        metadata = {'status': 'success'}
        (backup_dir / '_metadata.json').write_text(json.dumps(metadata))

        is_valid, errors = backup_manager.verify_backup(str(backup_dir))
        assert is_valid is True
        assert len(errors) == 0

    def test_verify_backup_missing_metadata(self, backup_manager, tmp_path):
        """Test verifying backup without metadata."""
        backup_dir = tmp_path / 'no_metadata'
        backup_dir.mkdir()

        is_valid, errors = backup_manager.verify_backup(str(backup_dir))
        assert is_valid is False
        assert len(errors) > 0

    def test_verify_backup_nonexistent(self, backup_manager):
        """Test verifying nonexistent backup."""
        is_valid, errors = backup_manager.verify_backup('/nonexistent/backup')
        assert is_valid is False
        assert len(errors) > 0

    def test_verify_backup_invalid_status(self, backup_manager, tmp_path):
        """Test verifying backup with invalid status."""
        backup_dir = tmp_path / 'invalid_status'
        backup_dir.mkdir()
        metadata = {'status': 'failed'}
        (backup_dir / '_metadata.json').write_text(json.dumps(metadata))

        is_valid, errors = backup_manager.verify_backup(str(backup_dir))
        assert is_valid is False
        assert len(errors) > 0


class TestBackupManagerRestore:
    """Test restore functionality."""

    @pytest.fixture
    def backup_manager(self, tmp_path, monkeypatch):
        """Create a BackupManager with mocked dependencies."""
        with patch.object(Path, 'home', return_value=tmp_path):
            with patch.object(BackupConfigManager, '_ensure_backup_structure'):
                with patch('shutil.which', return_value='/usr/bin/rsync'):
                    manager = BackupManager()
                    # Override destination to use temp path
                    manager.config_manager.config['destination']['base_path'] = str(tmp_path)
                    manager.config_manager.config['destination']['full_path'] = str(tmp_path / 'backups')
                    yield manager

    def test_restore_file(self, backup_manager, tmp_path):
        """Test restoring a single file."""
        backup_dir = tmp_path / 'backup'
        backup_dir.mkdir()
        (backup_dir / 'test.txt').write_text('backup content')

        dest_path = tmp_path / 'restored.txt'
        result = backup_manager.restore_file(
            str(backup_dir),
            'test.txt',
            str(dest_path)
        )
        assert result is True
        assert dest_path.read_text() == 'backup content'

    def test_restore_file_nonexistent(self, backup_manager, tmp_path):
        """Test restoring nonexistent file."""
        backup_dir = tmp_path / 'backup'
        backup_dir.mkdir()

        result = backup_manager.restore_file(
            str(backup_dir),
            'nonexistent.txt',
            str(tmp_path / 'dest.txt')
        )
        assert result is False

    def test_restore_directory(self, backup_manager, tmp_path):
        """Test restoring entire directory."""
        backup_dir = tmp_path / 'backup'
        backup_dir.mkdir()
        (backup_dir / 'file1.txt').write_text('content1')
        (backup_dir / 'subdir').mkdir()
        (backup_dir / 'subdir' / 'file2.txt').write_text('content2')

        dest_dir = tmp_path / 'restored'
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = backup_manager.restore_directory(str(backup_dir), str(dest_dir))
            assert result is True

    def test_restore_directory_nonexistent(self, backup_manager):
        """Test restoring nonexistent directory."""
        result = backup_manager.restore_directory('/nonexistent/backup', '/tmp/dest')
        assert result is False


class TestBackupManagerSpace:
    """Test space calculation methods."""

    @pytest.fixture
    def backup_manager(self, tmp_path, monkeypatch):
        """Create a BackupManager with mocked dependencies."""
        with patch.object(Path, 'home', return_value=tmp_path):
            # Create backup destination
            backup_dir = tmp_path / 'backups'
            backup_dir.mkdir(parents=True, exist_ok=True)
            (backup_dir / 'daily').mkdir(exist_ok=True)
            (backup_dir / 'weekly').mkdir(exist_ok=True)
            (backup_dir / 'monthly').mkdir(exist_ok=True)
            (backup_dir / 'logs').mkdir(exist_ok=True)

            with patch('shutil.which', return_value='/usr/bin/rsync'):
                manager = BackupManager()
                yield manager

    def test_get_space_used(self, backup_manager, tmp_path):
        """Test calculating space used by backups."""
        # Configure destination to tmp_path
        backup_manager.config_manager.set_backup_destination(str(tmp_path), 'backups')

        # Create some backup files
        daily_dir = tmp_path / 'backups' / 'daily'
        test_backup = daily_dir / 'backup-2026-04-01_02-00'
        test_backup.mkdir(parents=True, exist_ok=True)
        (test_backup / 'test.txt').write_text('a' * 1000)

        space_used = backup_manager.get_space_used()
        assert space_used >= 1000

    def test_get_space_info(self, backup_manager, tmp_path):
        """Test getting detailed space information."""
        # Ensure backup directory exists
        backup_dir = tmp_path / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        (backup_dir / 'daily').mkdir(exist_ok=True)
        info = backup_manager.get_space_info()
        assert 'total_gb' in info
        assert 'free_gb' in info
        assert 'usage_percent' in info

    def test_get_space_info_nonexistent(self, backup_manager, tmp_path):
        """Test getting space info for nonexistent directory."""
        with patch.object(backup_manager.config_manager, 'get_config', return_value={
            'destination': {'full_path': '/nonexistent/path'}
        }):
            info = backup_manager.get_space_info()
            assert 'error' in info
