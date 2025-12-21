"""
RetroAuto v2 - Autosave Manager

Automatic backup saves with configurable interval.
"""

import threading
import time
from collections.abc import Callable
from pathlib import Path

from infra.logging import get_logger

logger = get_logger("Autosave")


class AutosaveManager:
    """
    Manages automatic saving of script at regular intervals.

    Features:
    - Configurable interval (default 60s)
    - Backup rotation (keep last N backups)
    - Only saves if changes detected
    - Thread-safe
    """

    def __init__(
        self,
        interval_seconds: int = 60,
        max_backups: int = 5,
    ) -> None:
        """
        Initialize autosave manager.

        Args:
            interval_seconds: Save interval in seconds
            max_backups: Maximum backup files to keep
        """
        self._interval = interval_seconds
        self._max_backups = max_backups
        self._thread: threading.Thread | None = None
        self._running = False
        self._dirty = False
        self._save_callback: Callable[[], bool] | None = None
        self._backup_dir: Path | None = None

    def start(
        self,
        save_callback: Callable[[], bool],
        backup_dir: Path,
    ) -> None:
        """
        Start autosave thread.

        Args:
            save_callback: Function that performs save, returns True on success
            backup_dir: Directory for backup files
        """
        if self._running:
            return

        self._save_callback = save_callback
        self._backup_dir = backup_dir
        self._running = True
        self._thread = threading.Thread(target=self._autosave_loop, daemon=True)
        self._thread.start()
        logger.info("Autosave started (interval=%ds)", self._interval)

    def stop(self) -> None:
        """Stop autosave thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("Autosave stopped")

    def mark_dirty(self) -> None:
        """Mark that changes need to be saved."""
        self._dirty = True

    def mark_clean(self) -> None:
        """Mark that no changes need to be saved."""
        self._dirty = False

    def _autosave_loop(self) -> None:
        """Background autosave loop."""
        while self._running:
            time.sleep(self._interval)

            if not self._running:
                break

            if self._dirty and self._save_callback:
                try:
                    self._create_backup()
                    if self._save_callback():
                        self._dirty = False
                        logger.info("Autosave completed")
                except Exception as e:
                    logger.exception("Autosave failed: %s", e)

    def _create_backup(self) -> None:
        """Create backup before saving."""
        if not self._backup_dir:
            return

        backup_dir = self._backup_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Get existing backups
        backups = sorted(backup_dir.glob("script_*.yaml"))

        # Rotate if needed
        while len(backups) >= self._max_backups:
            oldest = backups.pop(0)
            try:
                oldest.unlink()
                logger.debug("Removed old backup: %s", oldest.name)
            except Exception:
                pass

        # Create new backup name
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"script_{timestamp}.yaml"

        # Copy current script to backup
        script_path = self._backup_dir / "script.yaml"
        if script_path.exists():
            import shutil

            backup_path = backup_dir / backup_name
            shutil.copy(script_path, backup_path)
            logger.debug("Created backup: %s", backup_name)
