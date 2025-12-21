"""
RetroAuto v2 - Global hotkey management using Windows RegisterHotKey.
"""

import ctypes
import threading
from collections.abc import Callable
from ctypes import wintypes

from infra.logging import get_logger

logger = get_logger("Hotkeys")

# Windows constants
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

# Virtual key codes
VK_CODES: dict[str, int] = {
    "F1": 0x70,
    "F2": 0x71,
    "F3": 0x72,
    "F4": 0x73,
    "F5": 0x74,
    "F6": 0x75,
    "F7": 0x76,
    "F8": 0x77,
    "F9": 0x78,
    "F10": 0x79,
    "F11": 0x7A,
    "F12": 0x7B,
    "ESC": 0x1B,
    "SPACE": 0x20,
    "RETURN": 0x0D,
    "TAB": 0x09,
    "BACK": 0x08,
    "DELETE": 0x2E,
    "INSERT": 0x2D,
    "HOME": 0x24,
    "END": 0x23,
    "PAGEUP": 0x21,
    "PAGEDOWN": 0x22,
    "LEFT": 0x25,
    "UP": 0x26,
    "RIGHT": 0x27,
    "DOWN": 0x28,
    "0": 0x30,
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
    "5": 0x35,
    "6": 0x36,
    "7": 0x37,
    "8": 0x38,
    "9": 0x39,
    "A": 0x41,
    "B": 0x42,
    "C": 0x43,
    "D": 0x44,
    "E": 0x45,
    "F": 0x46,
    "G": 0x47,
    "H": 0x48,
    "I": 0x49,
    "J": 0x4A,
    "K": 0x4B,
    "L": 0x4C,
    "M": 0x4D,
    "N": 0x4E,
    "O": 0x4F,
    "P": 0x50,
    "Q": 0x51,
    "R": 0x52,
    "S": 0x53,
    "T": 0x54,
    "U": 0x55,
    "V": 0x56,
    "W": 0x57,
    "X": 0x58,
    "Y": 0x59,
    "Z": 0x5A,
}


def parse_hotkey(hotkey_str: str) -> tuple[int, int]:
    """
    Parse hotkey string like 'CTRL+SHIFT+F5' into (modifiers, vk_code).

    Returns:
        (modifiers, virtual_key_code)
    """
    parts = [p.strip().upper() for p in hotkey_str.split("+")]
    modifiers = 0
    vk_code = 0

    for part in parts:
        if part in ("CTRL", "CONTROL"):
            modifiers |= MOD_CONTROL
        elif part in ("ALT",):
            modifiers |= MOD_ALT
        elif part in ("SHIFT",):
            modifiers |= MOD_SHIFT
        elif part in ("WIN", "WINDOWS"):
            modifiers |= MOD_WIN
        elif part in VK_CODES:
            vk_code = VK_CODES[part]
        else:
            raise ValueError(f"Unknown key: {part}")

    if vk_code == 0:
        raise ValueError(f"No main key in hotkey: {hotkey_str}")

    return modifiers | MOD_NOREPEAT, vk_code


class HotkeyManager:
    """
    Manages global hotkeys using Windows RegisterHotKey.

    Thread-safe: runs message loop in background thread.
    """

    def __init__(self) -> None:
        self._hotkeys: dict[int, Callable[[], None]] = {}
        self._next_id = 1
        self._thread: threading.Thread | None = None
        self._running = False
        self._hwnd: int = 0

    def register(self, hotkey: str, callback: Callable[[], None]) -> int:
        """
        Register a global hotkey.

        Args:
            hotkey: Hotkey string like 'CTRL+SHIFT+S' or 'F5'
            callback: Function to call when hotkey pressed

        Returns:
            Hotkey ID for unregistering
        """
        modifiers, vk_code = parse_hotkey(hotkey)
        hotkey_id = self._next_id
        self._next_id += 1

        if not ctypes.windll.user32.RegisterHotKey(None, hotkey_id, modifiers, vk_code):
            error = ctypes.get_last_error()
            raise OSError(f"Failed to register hotkey {hotkey}: error {error}")

        self._hotkeys[hotkey_id] = callback
        logger.info("Registered hotkey: %s (id=%d)", hotkey, hotkey_id)
        return hotkey_id

    def unregister(self, hotkey_id: int) -> None:
        """Unregister a hotkey by ID."""
        if hotkey_id in self._hotkeys:
            ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
            del self._hotkeys[hotkey_id]
            logger.info("Unregistered hotkey id=%d", hotkey_id)

    def unregister_all(self) -> None:
        """Unregister all hotkeys."""
        for hotkey_id in list(self._hotkeys.keys()):
            self.unregister(hotkey_id)

    def start(self) -> None:
        """Start the hotkey listener thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()
        logger.info("Hotkey manager started")

    def stop(self) -> None:
        """Stop the hotkey listener."""
        self._running = False
        self.unregister_all()
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        logger.info("Hotkey manager stopped")

    def _message_loop(self) -> None:
        """Windows message loop for hotkey events."""
        msg = wintypes.MSG()
        while self._running:
            if ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                if msg.message == WM_HOTKEY:
                    hotkey_id = msg.wParam
                    if hotkey_id in self._hotkeys:
                        try:
                            self._hotkeys[hotkey_id]()
                        except Exception as e:
                            logger.error("Hotkey callback error: %s", e)
            else:
                # Avoid busy-wait
                ctypes.windll.kernel32.Sleep(10)
