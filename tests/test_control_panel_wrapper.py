"""Tests for control-panel wrapper logic and command parsing."""
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


class TestWrapperPaths:
    """Test that wrapper script paths are correctly configured."""

    def test_docker_compose_paths(self):
        """Test Docker compose file paths."""
        manager = CLIManager()
        assert manager.docker_compose_dir == Path("/home/mateus")
        assert manager.docker_compose_file == Path("/home/mateus/docker-compose.yml")

    def test_hd_configuration(self):
        """Test HD configuration values."""
        manager = CLIManager()
        assert manager.hd_mount_point == "/media/mateus/Servidor"
        assert manager.hd_uuid == "35feb867-8ee2-49a9-a1a5-719a67e3975a"
        assert manager.hd_label == "Servidor"


class TestCommandDispatch:
    """Test command dispatching logic."""

    def test_manager_has_required_methods(self):
        """Test that manager has all required command methods."""
        manager = CLIManager()
        required_methods = [
            'show_interactive_menu',
            'get_docker_services',
            'select_docker_service',
            'show_docker_menu',
            'show_systemd_menu',
            'show_hd_menu',
            'show_backup_menu',
            'mount_hd_interactive',
            'unmount_hd_interactive',
            'is_hd_mounted',
            'show_status_interactive',
            'sync_interactive',
            'view_logs_interactive',
            'diagnostics_interactive',
            'clean_swap_interactive',
        ]
        for method in required_methods:
            assert hasattr(manager, method), f"Missing method: {method}"
            assert callable(getattr(manager, method)), f"Method not callable: {method}"


class TestBackupMethods:
    """Test backup-related methods."""

    def test_backup_methods_exist(self):
        """Test that backup methods exist."""
        manager = CLIManager()
        backup_methods = [
            'show_backup_menu',
            'show_backup_daemon_menu',
            'show_backup_sources_menu',
            'backup_daemon_start',
            'backup_daemon_stop',
            'backup_daemon_restart',
            'backup_daemon_status',
            'backup_set_destination',
            'backup_set_schedule',
            'backup_set_retention',
            'backup_add_source',
            'backup_remove_source',
            'backup_toggle_source',
            'backup_list_sources',
            'backup_run_now',
            'backup_show_stats',
            'backup_show_history',
            'backup_show_config',
        ]
        for method in backup_methods:
            assert hasattr(manager, method), f"Missing backup method: {method}"
