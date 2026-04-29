"""Shared test fixtures and configuration."""
import pytest
import sys
from pathlib import Path
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


@pytest.fixture(autouse=True)
def mock_backup_structure():
    """Automatically mock _ensure_backup_structure for all backup tests.
    
    This prevents RuntimeError when /media/mateus/Servidor does not exist
    (e.g., in CI environments).
    """
    # Patch both possible module paths (local vs CI import)
    patches = []
    for module_name in ['scripts.backup_config', 'backup_config']:
        try:
            mod = __import__(module_name, fromlist=['BackupConfigManager'])
            patches.append(patch.object(mod.BackupConfigManager, '_ensure_backup_structure'))
        except (ImportError, AttributeError):
            pass
    
    for p in patches:
        p.start()
    yield
    for p in patches:
        p.stop()
