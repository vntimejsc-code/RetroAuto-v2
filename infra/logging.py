"""
RetroAuto v2 - Windows Automation Tool

Logging infrastructure with rotating file handler and GUI integration.
"""

import logging
import sys
from collections.abc import Callable
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Default log directory
LOG_DIR = Path.home() / ".retroauto" / "logs"


class LogEmitter:
    """Bridge between logging and GUI log panel."""

    def __init__(self) -> None:
        self._callbacks: list[Callable[[str, str, str], None]] = []

    def add_callback(self, callback: Callable[[str, str, str], None]) -> None:
        """Register callback: (level, timestamp, message) -> None."""
        self._callbacks.append(callback)

    def emit(self, level: str, timestamp: str, message: str) -> None:
        """Emit log to all registered callbacks."""
        import contextlib

        for cb in self._callbacks:
            with contextlib.suppress(Exception):
                cb(level, timestamp, message)


# Global emitter for GUI integration
log_emitter = LogEmitter()


class GUIHandler(logging.Handler):
    """Handler that emits logs to GUI via LogEmitter."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            message = self.format(record)
            log_emitter.emit(record.levelname, timestamp, message)
        except Exception:
            self.handleError(record)


def setup_logging(
    level: int = logging.INFO,
    log_dir: Path | None = None,
    max_bytes: int = 5 * 1024 * 1024,  # 5MB
    backup_count: int = 3,
    enable_gui: bool = True,
) -> logging.Logger:
    """
    Configure application logging.

    Args:
        level: Log level (default INFO)
        log_dir: Directory for log files
        max_bytes: Max size per log file
        backup_count: Number of backup files
        enable_gui: Enable GUI handler

    Returns:
        Root logger for RetroAuto
    """
    if log_dir is None:
        log_dir = LOG_DIR

    log_dir.mkdir(parents=True, exist_ok=True)

    # Format
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, date_fmt)

    # Root logger
    logger = logging.getLogger("RetroAuto")
    logger.setLevel(level)
    logger.handlers.clear()

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler with rotation
    log_file = log_dir / "retroauto.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)  # File gets everything
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # GUI handler
    if enable_gui:
        gui_handler = GUIHandler()
        gui_handler.setLevel(level)
        gui_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(gui_handler)

    logger.info("Logging initialized: %s", log_file)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under RetroAuto namespace."""
    return logging.getLogger(f"RetroAuto.{name}")
