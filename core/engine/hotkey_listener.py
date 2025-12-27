"""
RetroAuto v2 - Hotkey Listener

Global keyboard shortcut listener for triggering Flows.
Uses pynput for cross-process key detection.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass

from infra import get_logger

logger = get_logger("HotkeyListener")

# Try to import pynput
try:
    from pynput import keyboard

    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False
    keyboard = None


@dataclass
class HotkeyBinding:
    """A hotkey-to-action binding."""

    hotkey: str  # e.g., "f4", "ctrl+f4", "ctrl+shift+a"
    callback: Callable[[], None]
    enabled: bool = True


class HotkeyListener:
    """
    Global hotkey listener using pynput.

    Usage:
        listener = HotkeyListener()
        listener.register("f4", lambda: print("F4 pressed!"))
        listener.register("ctrl+f4", lambda: print("Ctrl+F4 pressed!"))
        listener.start()
        # ... later
        listener.stop()

    Note:
        - Keys are case-insensitive: "F4" == "f4"
        - Modifiers: ctrl, alt, shift, cmd (or win)
        - Special keys: f1-f12, space, enter, tab, etc.
    """

    _instance: HotkeyListener | None = None
    _lock = threading.Lock()
    _initialized: bool = False  # Type annotation for mypy

    def __new__(cls) -> HotkeyListener:
        """Singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self._bindings: dict[str, HotkeyBinding] = {}
        self._listener: keyboard.GlobalHotKeys | None = None
        self._running = False
        self._current_modifiers: set[str] = set()

    # ─────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────

    def register(self, hotkey: str, callback: Callable[[], None]) -> None:
        """
        Register a hotkey binding.

        Args:
            hotkey: Key combination (e.g., "f4", "ctrl+shift+a")
            callback: Function to call when hotkey is pressed
        """
        normalized = self._normalize_hotkey(hotkey)
        self._bindings[normalized] = HotkeyBinding(
            hotkey=normalized,
            callback=callback,
            enabled=True,
        )
        logger.info(f"Registered hotkey: {normalized}")

        # Restart listener if running to pick up new binding
        if self._running:
            self._restart_listener()

    def unregister(self, hotkey: str) -> bool:
        """Unregister a hotkey binding."""
        normalized = self._normalize_hotkey(hotkey)
        if normalized in self._bindings:
            del self._bindings[normalized]
            logger.info(f"Unregistered hotkey: {normalized}")
            if self._running:
                self._restart_listener()
            return True
        return False

    def set_enabled(self, hotkey: str, enabled: bool) -> None:
        """Enable or disable a hotkey without removing it."""
        normalized = self._normalize_hotkey(hotkey)
        if normalized in self._bindings:
            self._bindings[normalized].enabled = enabled

    def start(self) -> bool:
        """Start listening for hotkeys."""
        if not HAS_PYNPUT:
            logger.error("pynput not installed. Run: pip install pynput")
            return False

        if self._running:
            return True

        if not self._bindings:
            logger.warning("No hotkeys registered, nothing to listen for")
            return False

        self._create_listener()
        self._running = True
        logger.info(f"HotkeyListener started with {len(self._bindings)} bindings")
        return True

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._running = False
        logger.info("HotkeyListener stopped")

    def is_running(self) -> bool:
        """Check if listener is active."""
        return self._running

    def get_bindings(self) -> list[str]:
        """Get list of registered hotkeys."""
        return list(self._bindings.keys())

    # ─────────────────────────────────────────────────────────────
    # Internal Methods
    # ─────────────────────────────────────────────────────────────

    def _normalize_hotkey(self, hotkey: str) -> str:
        """
        Normalize hotkey string to pynput format.
        "Ctrl+Shift+C" -> "<ctrl>+<shift>+c"
        "Ctrl+F4" -> "<ctrl>+<f4>"
        """
        # Special keys that need angle brackets
        special_keys = {
            "ctrl", "control", "alt", "shift", "cmd", "win", "windows",
            "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
            "space", "enter", "return", "tab", "escape", "esc",
            "backspace", "delete", "insert", "home", "end", "pageup", "pagedown",
            "up", "down", "left", "right", "caps_lock", "num_lock", "scroll_lock",
        }

        parts = hotkey.lower().replace(" ", "").split("+")
        normalized_parts = []

        for part in parts:
            # Map common aliases
            if part in ("control",):
                part = "ctrl"
            if part in ("win", "windows"):
                part = "cmd"

            # Only wrap special keys in angle brackets
            # Regular character keys like 'a', 'c', '1' stay as-is
            if part in special_keys:
                if not part.startswith("<"):
                    part = f"<{part}>"
            normalized_parts.append(part)

        return "+".join(normalized_parts)

    def _create_listener(self) -> None:
        """Create pynput GlobalHotKeys listener."""
        hotkey_map = {}

        for normalized, binding in self._bindings.items():
            if binding.enabled:
                # Create a closure to capture the binding
                def make_callback(b: HotkeyBinding) -> Callable[[], None]:
                    def cb() -> None:
                        logger.info(f">>> Global hotkey triggered: {b.hotkey} <<<")
                        try:
                            b.callback()
                        except Exception as e:
                            logger.error(f"Hotkey callback error: {e}")

                    return cb

                hotkey_map[normalized] = make_callback(binding)

        # Log registered hotkeys for debugging
        logger.info(f"Creating GlobalHotKeys with bindings: {list(hotkey_map.keys())}")
        self._listener = keyboard.GlobalHotKeys(hotkey_map)
        self._listener.daemon = True  # Ensure daemon thread
        self._listener.start()

    def _restart_listener(self) -> None:
        """Restart the listener to pick up new bindings."""
        self.stop()
        self.start()


# ─────────────────────────────────────────────────────────────
# Convenience Functions
# ─────────────────────────────────────────────────────────────


def get_hotkey_listener() -> HotkeyListener:
    """Get the global HotkeyListener instance."""
    return HotkeyListener()


# Simple test
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)

    listener = get_hotkey_listener()
    listener.register("f4", lambda: print(">>> F4 pressed! <<<"))
    listener.register("ctrl+f4", lambda: print(">>> Ctrl+F4 pressed! <<<"))
    listener.start()

    print("Listening for F4 and Ctrl+F4... Press Ctrl+C to exit.")
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop()
        print("Stopped.")
