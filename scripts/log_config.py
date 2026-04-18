#!/usr/bin/env python3
"""
Centralized logging configuration for Control Panel System
"""

from typing import Optional
import uuid
import logging
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler
from logging.handlers import RotatingFileHandler

console = Console()

# Log symbols
SYMBOLS = {
    'success': '✓',
    'error': '✗',
    'warning': '!',
    'info': 'i',
    'mount': '[MOUNT]',
    'docker': '[DOCKER]',
    'systemd': '[SYSTEMD]',
    'status': '[STATUS]',
    'cleanup': '[CLEANUP]',
    'network': '[NETWORK]',
    'service': '[SERVICE]',
    'process': '[PROCESS]',
    'security': '[SECURITY]',
    'config': '[CONFIG]',
    'storage': '[STORAGE]',
    'system': '[SYSTEM]',
    'power': '[POWER]',
    'swap': '[SWAP]',
    'sync': '[SYNC]',
    'time': '[TIME]'
}


class ControlPanelLogger:
    """Centralized logger for Control Panel System"""

    def __init__(self, name: str = "ControlPanel", log_file: str = None):
        self.name = name
        self.logger = logging.getLogger(name)

        # Avoid duplicate handlers
        if self.logger.handlers:
            return

        # Get log level from environment or default to INFO
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Console handler with Rich
        console_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
            markup=True,
            show_path=False,  # Don't show file path and line number
            show_time=False   # Don't show timestamp (already in message for some logs)
        )
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            "%(message)s",
            datefmt="[%X]"
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # File handler with rotation
        if log_file is None:
            # Use ~/.local/share/control-panel/ for logs (follows XDG Base Directory Specification)
            log_dir = Path.home() / '.local' / 'share' / 'control-panel'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / 'control_panel.log'

        # Use rotating file handler with max size of 10MB and up to 5 backup files
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        """Return the configured logger"""
        return self.logger

    @staticmethod
    def format_message(symbol_key: str, message: str) -> str:
        """Format message with symbol"""
        symbol = SYMBOLS.get(symbol_key, '')
        return f"{symbol} {message}" if symbol else message


# Global request ID for tracking related operations
_current_request_id = None


def set_request_id(request_id: Optional[str] = None):
    """Set a request ID for tracking related operations"""
    global _current_request_id
    _current_request_id = request_id or str(uuid.uuid4())[:8]


def get_request_id() -> Optional[str]:
    """Get the current request ID"""
    return _current_request_id


def clear_request_id():
    """Clear the current request ID"""
    global _current_request_id
    _current_request_id = None


def format_log_message(message: str, include_request_id: bool = True) -> str:
    """Format a log message with optional request ID"""
    if include_request_id and _current_request_id:
        return f"[{_current_request_id}] {message}"
    return message

# Create default logger instance


def get_logger(name: str = "ControlPanel") -> logging.Logger:
    """Get or create a logger instance"""
    return ControlPanelLogger(name).get_logger()


# Convenience functions for formatted logging
def log_success(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log success message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'success', formatted_message))


def log_error(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log error message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.error(ControlPanelLogger.format_message(
        'error', formatted_message))


def log_warning(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log warning message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.warning(ControlPanelLogger.format_message(
        'warning', formatted_message))


def log_info(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log info message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'info', formatted_message))


def log_mount(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log mount operation message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'mount', formatted_message))


def log_docker(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log Docker operation message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'docker', formatted_message))


def log_systemd(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log systemd operation message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'systemd', formatted_message))


def log_status(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log status message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'status', formatted_message))


def log_cleanup(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log cleanup message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'cleanup', formatted_message))


def log_network(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log network operation message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'network', formatted_message))


def log_service(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log service operation message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'service', formatted_message))


def log_process(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log process operation message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'process', formatted_message))


def log_security(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log security operation message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'security', formatted_message))


def log_config(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log config operation message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'config', formatted_message))


def log_storage(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log storage operation message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'storage', formatted_message))


def log_system(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log system operation message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'system', formatted_message))


def log_power(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log power operation message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'power', formatted_message))


def log_swap(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log SWAP operation message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message('swap', formatted_message))


def log_sync(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log sync operation message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'sync', formatted_message))


def log_time(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log time-related message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.info(ControlPanelLogger.format_message(
        'time', formatted_message))


def log_debug(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log debug message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.debug(formatted_message)


def is_verbose_logging() -> bool:
    """Check if verbose logging is enabled (DEBUG level)"""
    return os.getenv('LOG_LEVEL', 'INFO').upper() == 'DEBUG'


def set_console_log_level(level: int = logging.WARNING):
    """Set console logging level for all loggers

    Args:
        level: logging level (logging.WARNING, logging.ERROR, etc.)

    Use this to suppress INFO logs from console when running CLI commands.
    File logging will continue to capture all levels.
    """
    # Get all loggers
    for logger_name in logging.root.manager.loggerDict:
        logger_obj = logging.getLogger(logger_name)

        # Find RichHandler (console handler) and update its level
        for handler in logger_obj.handlers:
            if isinstance(handler, RichHandler):
                handler.setLevel(level)
