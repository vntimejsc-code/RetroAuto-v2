"""
RetroAuto v2 - Hot Reload

Live code updates without restarting scripts.
Part of RetroScript Phase 8 - Runtime + Distribution.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Thread
from typing import Any


@dataclass
class WatchedFile:
    """A file being watched for changes."""

    path: Path
    last_hash: str = ""
    last_modified: float = 0.0


@dataclass
class ReloadEvent:
    """Event fired when a file changes."""

    path: Path
    event_type: str  # "modified", "created", "deleted"
    timestamp: float


class FileWatcher:
    """Watch files for changes.

    Usage:
        watcher = FileWatcher()
        watcher.add("script.retro")
        watcher.on_change = lambda e: print(f"Changed: {e.path}")
        watcher.start()
    """

    def __init__(self, poll_interval: float = 0.5) -> None:
        self._files: dict[str, WatchedFile] = {}
        self._poll_interval = poll_interval
        self._running = False
        self._stop_event = Event()
        self._thread: Thread | None = None

        # Callbacks
        self.on_change: Callable[[ReloadEvent], None] | None = None

    def add(self, path: str | Path) -> None:
        """Add a file to watch."""
        path = Path(path)
        if not path.exists():
            return

        file_hash = self._get_file_hash(path)
        self._files[str(path)] = WatchedFile(
            path=path,
            last_hash=file_hash,
            last_modified=path.stat().st_mtime,
        )

    def remove(self, path: str | Path) -> None:
        """Remove a file from watching."""
        path_str = str(Path(path))
        if path_str in self._files:
            del self._files[path_str]

    def add_directory(self, directory: str | Path, pattern: str = "*.retro") -> None:
        """Add all matching files in a directory."""
        dir_path = Path(directory)
        for file_path in dir_path.glob(pattern):
            self.add(file_path)

    def start(self) -> None:
        """Start watching for changes."""
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._thread = Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop watching for changes."""
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _watch_loop(self) -> None:
        """Main watch loop running in background thread."""
        while self._running and not self._stop_event.is_set():
            self._check_files()
            self._stop_event.wait(self._poll_interval)

    def _check_files(self) -> None:
        """Check all watched files for changes."""
        for path_str, watched in list(self._files.items()):
            try:
                if not watched.path.exists():
                    # File deleted
                    self._fire_event(watched.path, "deleted")
                    del self._files[path_str]
                    continue

                current_mtime = watched.path.stat().st_mtime
                if current_mtime > watched.last_modified:
                    # File modified - verify with hash
                    current_hash = self._get_file_hash(watched.path)
                    if current_hash != watched.last_hash:
                        watched.last_hash = current_hash
                        watched.last_modified = current_mtime
                        self._fire_event(watched.path, "modified")

            except (OSError, PermissionError, FileNotFoundError):
                pass  # Ignore file access errors

    def _fire_event(self, path: Path, event_type: str) -> None:
        """Fire a change event."""
        if self.on_change:
            event = ReloadEvent(
                path=path,
                event_type=event_type,
                timestamp=time.time(),
            )
            self.on_change(event)

    def _get_file_hash(self, path: Path) -> str:
        """Get hash of file contents."""
        try:
            content = path.read_bytes()
            return hashlib.md5(content).hexdigest()
        except (OSError, PermissionError, FileNotFoundError):
            return ""


class HotReloader:
    """Hot reload manager for RetroScript.

    Usage:
        reloader = HotReloader()
        reloader.watch("main.retro")
        reloader.on_reload = lambda path: print(f"Reloaded: {path}")
        reloader.start()
    """

    def __init__(self) -> None:
        self._watcher = FileWatcher()
        self._watcher.on_change = self._handle_change
        self._state: dict[str, Any] = {}  # Preserved state between reloads
        self._reload_count = 0

        # Callbacks
        self.on_reload: Callable[[Path], None] | None = None
        self.on_error: Callable[[Path, Exception], None] | None = None
        self.before_reload: Callable[[Path], dict[str, Any] | None] | None = None
        self.after_reload: Callable[[Path, dict[str, Any] | None], None] | None = None

    def watch(self, path: str | Path) -> None:
        """Add a file to watch for changes."""
        self._watcher.add(path)

    def watch_directory(self, directory: str | Path, pattern: str = "*.retro") -> None:
        """Watch all matching files in a directory."""
        self._watcher.add_directory(directory, pattern)

    def start(self) -> None:
        """Start hot reload watching."""
        self._watcher.start()

    def stop(self) -> None:
        """Stop hot reload watching."""
        self._watcher.stop()

    def get_state(self) -> dict[str, Any]:
        """Get preserved state."""
        return self._state.copy()

    def set_state(self, key: str, value: Any) -> None:
        """Set state to preserve across reloads."""
        self._state[key] = value

    def get_reload_count(self) -> int:
        """Get total reload count."""
        return self._reload_count

    def _handle_change(self, event: ReloadEvent) -> None:
        """Handle file change event."""
        if event.event_type != "modified":
            return

        try:
            # Save state before reload
            saved_state = None
            if self.before_reload:
                saved_state = self.before_reload(event.path)

            # Perform reload
            self._reload_count += 1

            # Notify
            if self.on_reload:
                self.on_reload(event.path)

            # Restore state after reload
            if self.after_reload:
                self.after_reload(event.path, saved_state)

        except Exception as e:
            if self.on_error:
                self.on_error(event.path, e)


def watch_and_reload(
    path: str | Path,
    on_reload: Callable[[Path], None],
) -> HotReloader:
    """Convenience function to start watching a file.

    Args:
        path: File to watch
        on_reload: Callback when file changes

    Returns:
        HotReloader instance
    """
    reloader = HotReloader()
    reloader.watch(path)
    reloader.on_reload = on_reload
    reloader.start()
    return reloader
