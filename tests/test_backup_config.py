"""Tests for Backup Configuration Manager."""
import pytest
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

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

from scripts.backup_config import BackupConfigManager


class TestBackupConfigManagerInit:
    """Test BackupConfigManager initialization."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create a temporary config directory."""
        return tmp_path / '.local' / 'share' / 'control-panel' / 'backup'

    @pytest.fixture
    def config_manager(self, tmp_path, monkeypatch):
        """Create a BackupConfigManager with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            manager = BackupConfigManager()
            yield manager

    def test_initialization_creates_config_files(self, config_manager, tmp_path):
        """Test that initialization creates config and state files."""
        config_dir = tmp_path / '.local' / 'share' / 'control-panel' / 'backup'
        assert (config_dir / '.backup_config').exists()
        assert (config_dir / '.backup_state.json').exists()
        # History file is created on first backup, not on init
        assert not (config_dir / 'backup_history.json').exists()

    def test_default_config_structure(self, config_manager):
        """Test that default config has expected structure."""
        config = config_manager.get_config()
        assert 'version' in config
        assert 'destination' in config
        assert 'schedule' in config
        assert 'retention' in config
        assert 'sources' in config
        assert 'options' in config

    def test_default_destination(self, config_manager):
        """Test default destination configuration."""
        dest = config_manager.get_backup_destination()
        assert 'base_path' in dest
        assert 'backup_folder' in dest
        assert 'full_path' in dest
        assert dest['auto_create'] is True

    def test_default_schedule(self, config_manager):
        """Test default schedule configuration."""
        schedule = config_manager.get_schedule()
        assert schedule['enabled'] is True
        assert schedule['frequency'] == 'daily'
        assert schedule['time'] == '02:00'

    def test_default_retention(self, config_manager):
        """Test default retention configuration."""
        retention = config_manager.get_retention()
        assert retention['daily_count'] == 7
        assert retention['weekly_count'] == 4
        assert retention['monthly_count'] == 6
        assert retention['max_age_days'] == 180


class TestBackupConfigDestination:
    """Test destination configuration methods."""

    @pytest.fixture
    def config_manager(self, tmp_path, monkeypatch):
        """Create a BackupConfigManager with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            manager = BackupConfigManager()
            yield manager

    def test_set_backup_destination_valid_path(self, config_manager, tmp_path):
        """Test setting destination with valid path."""
        test_path = str(tmp_path / 'backups')
        Path(test_path).mkdir(parents=True, exist_ok=True)

        result = config_manager.set_backup_destination(test_path, 'custom_backups')
        assert result is True

        dest = config_manager.get_backup_destination()
        assert dest['base_path'] == str(Path(test_path).resolve())
        assert dest['backup_folder'] == 'custom_backups'

    def test_set_backup_destination_invalid_path(self, config_manager):
        """Test setting destination with invalid path returns False."""
        result = config_manager.set_backup_destination('/nonexistent/path')
        assert result is False

    def test_check_destination_space(self, config_manager, tmp_path):
        """Test checking destination space."""
        test_path = str(tmp_path / 'backups')
        Path(test_path).mkdir(parents=True, exist_ok=True)
        config_manager.set_backup_destination(test_path)

        space = config_manager.check_destination_space()
        assert space['exists'] is True
        assert 'total_gb' in space
        assert 'free_gb' in space
        assert 'usage_percent' in space
        assert space['is_sufficient'] is True


class TestBackupConfigSchedule:
    """Test schedule configuration methods."""

    @pytest.fixture
    def config_manager(self, tmp_path, monkeypatch):
        """Create a BackupConfigManager with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            manager = BackupConfigManager()
            yield manager

    def test_set_schedule_valid(self, config_manager):
        """Test setting schedule with valid parameters."""
        result = config_manager.set_schedule(
            enabled=True,
            frequency='weekly',
            time='03:00'
        )
        assert result is True

        schedule = config_manager.get_schedule()
        assert schedule['frequency'] == 'weekly'
        assert schedule['time'] == '03:00'

    def test_set_schedule_invalid_frequency(self, config_manager):
        """Test setting schedule with invalid frequency returns False."""
        result = config_manager.set_schedule(frequency='invalid')
        assert result is False

    def test_set_schedule_invalid_time(self, config_manager):
        """Test setting schedule with invalid time returns False."""
        result = config_manager.set_schedule(time='25:00')
        assert result is False

        result = config_manager.set_schedule(time='not-a-time')
        assert result is False

    def test_get_next_scheduled_time_daily(self, config_manager):
        """Test calculating next scheduled time for daily backup."""
        config_manager.set_schedule(frequency='daily', time='02:00')
        next_time = config_manager.get_next_scheduled_time()

        assert isinstance(next_time, datetime)
        assert next_time.hour == 2
        assert next_time.minute == 0

    def test_get_next_scheduled_time_custom(self, config_manager):
        """Test calculating next scheduled time for custom frequency."""
        config_manager.set_schedule(
            frequency='custom',
            time='02:00',
            days_of_week=['monday', 'wednesday', 'friday']
        )
        next_time = config_manager.get_next_scheduled_time()

        assert isinstance(next_time, datetime)
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        assert day_names[next_time.weekday()] in ['monday', 'wednesday', 'friday']


class TestBackupConfigRetention:
    """Test retention configuration methods."""

    @pytest.fixture
    def config_manager(self, tmp_path, monkeypatch):
        """Create a BackupConfigManager with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            manager = BackupConfigManager()
            yield manager

    def test_set_retention_valid(self, config_manager):
        """Test setting retention with valid parameters."""
        result = config_manager.set_retention(
            daily_count=14,
            weekly_count=8,
            monthly_count=12
        )
        assert result is True

        retention = config_manager.get_retention()
        assert retention['daily_count'] == 14
        assert retention['weekly_count'] == 8
        assert retention['monthly_count'] == 12

    def test_set_retention_negative_values(self, config_manager):
        """Test setting retention with negative values returns False."""
        result = config_manager.set_retention(daily_count=-1)
        assert result is False


class TestBackupConfigSources:
    """Test source management methods."""

    @pytest.fixture
    def config_manager(self, tmp_path, monkeypatch):
        """Create a BackupConfigManager with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            manager = BackupConfigManager()
            yield manager

    @pytest.fixture
    def test_source_dir(self, tmp_path):
        """Create a test source directory."""
        source_dir = tmp_path / 'test_source'
        source_dir.mkdir()
        return str(source_dir)

    def test_add_source_valid(self, config_manager, test_source_dir):
        """Test adding a valid source."""
        result = config_manager.add_source(
            path=test_source_dir,
            priority='high',
            description='Test source'
        )
        assert result is True

        sources = config_manager.get_sources()
        assert len(sources) > 0
        assert any(s['path'] == test_source_dir for s in sources)

    def test_add_source_duplicate(self, config_manager, test_source_dir):
        """Test adding duplicate source returns False."""
        config_manager.add_source(path=test_source_dir)
        result = config_manager.add_source(path=test_source_dir)
        assert result is False

    def test_add_source_invalid_path(self, config_manager):
        """Test adding source with invalid path returns False."""
        result = config_manager.add_source(path='/nonexistent/path')
        assert result is False

    def test_remove_source(self, config_manager, test_source_dir):
        """Test removing a source."""
        config_manager.add_source(path=test_source_dir)
        result = config_manager.remove_source(test_source_dir)
        assert result is True

        sources = config_manager.get_sources()
        assert not any(s['path'] == test_source_dir for s in sources)

    def test_remove_source_nonexistent(self, config_manager):
        """Test removing nonexistent source returns False."""
        result = config_manager.remove_source('/nonexistent/path')
        assert result is False

    def test_toggle_source(self, config_manager, test_source_dir):
        """Test toggling source enabled status."""
        config_manager.add_source(path=test_source_dir)

        # Toggle off
        result = config_manager.toggle_source(test_source_dir)
        assert result is False

        # Toggle on
        result = config_manager.toggle_source(test_source_dir)
        assert result is True

    def test_get_enabled_sources(self, config_manager, test_source_dir):
        """Test getting only enabled sources."""
        config_manager.add_source(path=test_source_dir)
        config_manager.toggle_source(test_source_dir)

        enabled = config_manager.get_enabled_sources()
        assert not any(s['path'] == test_source_dir for s in enabled)

    def test_set_source_schedule(self, config_manager, test_source_dir):
        """Test setting individual source schedule."""
        config_manager.add_source(path=test_source_dir)

        result = config_manager.set_source_schedule(
            path=test_source_dir,
            frequency='weekly',
            time='04:00'
        )
        assert result is True

    def test_set_source_schedule_invalid(self, config_manager, test_source_dir):
        """Test setting invalid source schedule returns False."""
        config_manager.add_source(path=test_source_dir)

        result = config_manager.set_source_schedule(
            path=test_source_dir,
            frequency='invalid'
        )
        assert result is False


class TestBackupConfigState:
    """Test state and history management."""

    @pytest.fixture
    def config_manager(self, tmp_path, monkeypatch):
        """Create a BackupConfigManager with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            manager = BackupConfigManager()
            yield manager

    def test_update_state(self, config_manager):
        """Test updating state."""
        config_manager.update_state(daemon={'status': 'running'})
        state = config_manager.get_state()
        assert state['daemon']['status'] == 'running'

    def test_add_history_entry(self, config_manager):
        """Test adding history entry."""
        entry = {
            'id': 'backup-test-001',
            'type': 'daily',
            'status': 'success'
        }
        config_manager.add_history_entry(entry)
        history = config_manager.get_history(limit=1)
        assert len(history) == 1
        assert history[0]['id'] == 'backup-test-001'

    def test_get_history_limit(self, config_manager):
        """Test history limit parameter."""
        for i in range(5):
            config_manager.add_history_entry({'id': f'backup-{i}'})

        history = config_manager.get_history(limit=3)
        assert len(history) == 3


class TestBackupConfigPersistence:
    """Test configuration persistence."""

    @pytest.fixture
    def config_manager(self, tmp_path, monkeypatch):
        """Create a BackupConfigManager with temp directory."""
        with patch.object(Path, 'home', return_value=tmp_path):
            manager = BackupConfigManager()
            yield manager

    def test_config_saved_to_disk(self, config_manager, tmp_path):
        """Test that config is saved to disk."""
        config_manager.set_schedule(frequency='weekly')

        config_file = tmp_path / '.local' / 'share' / 'control-panel' / 'backup' / '.backup_config'
        assert config_file.exists()

        with open(config_file) as f:
            saved = json.load(f)
        assert saved['schedule']['frequency'] == 'weekly'

    def test_config_loaded_from_disk(self, tmp_path, monkeypatch):
        """Test that config is loaded from disk on initialization."""
        # Create a config file with custom schedule
        config_dir = tmp_path / '.local' / 'share' / 'control-panel' / 'backup'
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / '.backup_config'
        custom_config = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'destination': {
                'base_path': str(tmp_path),
                'backup_folder': 'backups',
                'full_path': str(tmp_path / 'backups'),
                'auto_create': True,
                'min_free_space_gb': 5
            },
            'schedule': {
                'enabled': True,
                'frequency': 'monthly',
                'time': '04:00',
                'timezone': 'America/Sao_Paulo',
                'days_of_week': ['sunday'],
                'day_of_month': 1
            },
            'retention': {
                'daily_count': 7,
                'weekly_count': 4,
                'monthly_count': 6,
                'max_age_days': 180,
                'min_free_space_gb': 10,
                'emergency_cleanup_threshold_gb': 5
            },
            'sources': [],
            'options': {}
        }
        config_file.write_text(json.dumps(custom_config, indent=2))

        # Also create state and history files
        (config_dir / '.backup_state.json').write_text('{"daemon": {"status": "stopped"}}')
        (config_dir / 'backup_history.json').write_text('[]')

        # Also create the backup directory structure to avoid errors
        backup_dir = tmp_path / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        (backup_dir / 'daily').mkdir(exist_ok=True)
        (backup_dir / 'weekly').mkdir(exist_ok=True)
        (backup_dir / 'monthly').mkdir(exist_ok=True)
        (backup_dir / 'logs').mkdir(exist_ok=True)

        with patch.object(Path, 'home', return_value=tmp_path):
            manager = BackupConfigManager()
            schedule = manager.get_schedule()
            assert schedule['frequency'] == 'monthly'
            assert schedule['time'] == '04:00'
