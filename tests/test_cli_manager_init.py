"""Tests for CLI Manager initialization and basic configuration."""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock rich modules before importing cli_manager
rich_mock = MagicMock()
sys.modules['rich'] = rich_mock
sys.modules['rich.console'] = MagicMock()
sys.modules['rich.table'] = MagicMock()
sys.modules['rich.panel'] = MagicMock()
sys.modules['rich.box'] = MagicMock()
sys.modules['rich.prompt'] = MagicMock()

# Mock log_config
log_config_mock = MagicMock()
log_config_mock.get_logger = MagicMock(return_value=MagicMock())
log_config_mock.log_success = MagicMock()
log_config_mock.log_error = MagicMock()
log_config_mock.log_warning = MagicMock()
log_config_mock.log_info = MagicMock()
log_config_mock.log_mount = MagicMock()
log_config_mock.log_docker = MagicMock()
log_config_mock.log_systemd = MagicMock()
log_config_mock.log_swap = MagicMock()
sys.modules['log_config'] = log_config_mock

from scripts.cli_manager import CLIManager


class TestCLIManagerInit:
    """Test CLIManager initialization."""

    def test_default_initialization(self):
        """Test that CLIManager initializes with correct default values."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('os.getcwd', return_value='/tmp/test'):
                manager = CLIManager()
                
                assert manager.hd_mount_point == "/media/mateus/Servidor"
                assert manager.hd_uuid == "35feb867-8ee2-49a9-a1a5-719a67e3975a"
                assert manager.hd_label == "Servidor"
                assert str(manager.docker_compose_dir) == "/home/mateus"
                assert str(manager.docker_compose_file) == "/home/mateus/docker-compose.yml"

    def test_custom_script_path(self):
        """Test that CLIManager respects SCRIPT_PATH environment variable."""
        with patch.dict('os.environ', {'SCRIPT_PATH': '/custom/path'}):
            manager = CLIManager()
            assert str(manager.script_dir) == "/custom/path"
            assert str(manager.pid_file) == "/custom/path/.daemon.pid"
            assert str(manager.log_file) == "/custom/path/logs/daemon.log"

    def test_find_project_root_returns_path(self):
        """Test _find_project_root returns a Path object."""
        manager = CLIManager()
        root = manager._find_project_root()
        assert isinstance(root, Path)
        assert root.name == "control-panel"


class TestCLIManagerDocker:
    """Test Docker-related methods."""

    def test_get_docker_services_empty(self):
        """Test get_docker_services returns empty list when docker is not available."""
        manager = CLIManager()
        services = manager.get_docker_services()
        assert isinstance(services, list)

    def test_select_docker_service_no_services(self):
        """Test select_docker_service returns False when no services found."""
        manager = CLIManager()
        with patch.object(manager, 'get_docker_services', return_value=[]):
            result = manager.select_docker_service()
            assert result is False


class TestCLIManagerHD:
    """Test HD-related methods."""

    def test_is_hd_mounted_returns_bool(self):
        """Test is_hd_mounted returns a boolean."""
        manager = CLIManager()
        result = manager.is_hd_mounted()
        assert isinstance(result, bool)

    def test_get_device_by_uuid_returns_none_or_str(self):
        """Test get_device_by_uuid returns None or string."""
        manager = CLIManager()
        result = manager.get_device_by_uuid()
        assert result is None or isinstance(result, str)
