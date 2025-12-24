"""
RetroAuto v2 - Keyboard Controller

Keyboard control using pywin32 with paste mode for Vietnamese support.
"""

import time

import win32api
import win32clipboard
import win32con

from infra import get_logger

logger = get_logger("Keyboard")

# Virtual key code mappings
VK_CODES: dict[str, int] = {
    # Function keys
    "F1": win32con.VK_F1,
    "F2": win32con.VK_F2,
    "F3": win32con.VK_F3,
    "F4": win32con.VK_F4,
    "F5": win32con.VK_F5,
    "F6": win32con.VK_F6,
    "F7": win32con.VK_F7,
    "F8": win32con.VK_F8,
    "F9": win32con.VK_F9,
    "F10": win32con.VK_F10,
    "F11": win32con.VK_F11,
    "F12": win32con.VK_F12,
    # Modifiers
    "CTRL": win32con.VK_CONTROL,
    "CONTROL": win32con.VK_CONTROL,
    "ALT": win32con.VK_MENU,
    "SHIFT": win32con.VK_SHIFT,
    "WIN": win32con.VK_LWIN,
    "LWIN": win32con.VK_LWIN,
    "RWIN": win32con.VK_RWIN,
    # Special keys
    "ENTER": win32con.VK_RETURN,
    "RETURN": win32con.VK_RETURN,
    "TAB": win32con.VK_TAB,
    "ESC": win32con.VK_ESCAPE,
    "ESCAPE": win32con.VK_ESCAPE,
    "SPACE": win32con.VK_SPACE,
    "BACKSPACE": win32con.VK_BACK,
    "BACK": win32con.VK_BACK,
    "DELETE": win32con.VK_DELETE,
    "DEL": win32con.VK_DELETE,
    "INSERT": win32con.VK_INSERT,
    "INS": win32con.VK_INSERT,
    "HOME": win32con.VK_HOME,
    "END": win32con.VK_END,
    "PAGEUP": win32con.VK_PRIOR,
    "PGUP": win32con.VK_PRIOR,
    "PAGEDOWN": win32con.VK_NEXT,
    "PGDN": win32con.VK_NEXT,
    # Arrow keys
    "UP": win32con.VK_UP,
    "DOWN": win32con.VK_DOWN,
    "LEFT": win32con.VK_LEFT,
    "RIGHT": win32con.VK_RIGHT,
    # Numbers
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
    # Letters
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

# Extended key codes that require special flag
EXTENDED_KEYS = {
    win32con.VK_UP,
    win32con.VK_DOWN,
    win32con.VK_LEFT,
    win32con.VK_RIGHT,
    win32con.VK_HOME,
    win32con.VK_END,
    win32con.VK_PRIOR,
    win32con.VK_NEXT,
    win32con.VK_INSERT,
    win32con.VK_DELETE,
}


def _key_down(vk_code: int) -> None:
    """Send key down event."""
    flags = 0
    if vk_code in EXTENDED_KEYS:
        flags |= win32con.KEYEVENTF_EXTENDEDKEY
    win32api.keybd_event(vk_code, 0, flags, 0)


def _key_up(vk_code: int) -> None:
    """Send key up event."""
    flags = win32con.KEYEVENTF_KEYUP
    if vk_code in EXTENDED_KEYS:
        flags |= win32con.KEYEVENTF_EXTENDEDKEY
    win32api.keybd_event(vk_code, 0, flags, 0)


class KeyboardController:
    """
    Keyboard control using Windows API.

    Features:
    - Hotkey combinations (e.g., CTRL+S)
    - Type text with paste mode (for Vietnamese)
    - Single key press/release
    """

    def __init__(self, key_delay_ms: int = 10) -> None:
        """
        Initialize keyboard controller.

        Args:
            key_delay_ms: Delay between key events
        """
        self._key_delay_ms = key_delay_ms

    def press_key(self, key: str) -> None:
        """
        Press and release a single key.

        Args:
            key: Key name (e.g., "A", "ENTER", "F5")
        """
        key_upper = key.upper()
        if key_upper not in VK_CODES:
            raise ValueError(f"Unknown key: {key}")

        vk_code = VK_CODES[key_upper]
        _key_down(vk_code)
        time.sleep(self._key_delay_ms / 1000.0)
        _key_up(vk_code)
        logger.debug("Pressed key: %s", key)

    def hotkey(self, keys: list[str]) -> None:
        """
        Press hotkey combination.

        Args:
            keys: List of keys to press together (e.g., ["CTRL", "S"])
        """
        if not keys:
            return

        vk_codes = []
        for key in keys:
            key_upper = key.upper()
            if key_upper not in VK_CODES:
                raise ValueError(f"Unknown key: {key}")
            vk_codes.append(VK_CODES[key_upper])

        # Press all keys down
        for vk in vk_codes:
            _key_down(vk)
            time.sleep(self._key_delay_ms / 1000.0)

        # Release in reverse order
        for vk in reversed(vk_codes):
            _key_up(vk)
            time.sleep(self._key_delay_ms / 1000.0)

        logger.debug("Hotkey: %s", "+".join(keys))

    def type_text(
        self,
        text: str,
        paste_mode: bool = True,
        enter: bool = False,
    ) -> None:
        """
        Type text.

        Args:
            text: Text to type
            paste_mode: Use clipboard paste (recommended for Vietnamese)
            enter: Press Enter after text
        """
        if not text:
            if enter:
                self.press_key("ENTER")
            return

        if paste_mode:
            self._paste_text(text)
        else:
            self._type_direct(text)

        if enter:
            time.sleep(0.05)
            self.press_key("ENTER")

        logger.debug(
            "Typed text: %s... (paste=%s)", text[:20] if len(text) > 20 else text, paste_mode
        )

    def _paste_text(self, text: str) -> None:
        """Type using clipboard paste (CTRL+V)."""
        # Save current clipboard
        try:
            win32clipboard.OpenClipboard()
            try:
                old_data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            except (TypeError, OSError):
                # Clipboard empty or wrong format
                old_data = None
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)
            win32clipboard.CloseClipboard()
        except Exception as e:
            logger.warning("Clipboard error: %s", e)
            # Fallback to direct typing
            self._type_direct(text)
            return

        # Paste
        time.sleep(0.01)
        self.hotkey(["CTRL", "V"])
        time.sleep(0.05)

        # Restore clipboard
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            if old_data:
                win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, old_data)
            win32clipboard.CloseClipboard()
        except (OSError, TypeError) as e:
            # Clipboard restore failed - non-critical, log and continue
            logger.debug("Clipboard restore failed: %s", e)

    def _type_direct(self, text: str) -> None:
        """Type directly using SendInput (for ASCII only)."""
        for char in text:
            if char.upper() in VK_CODES:
                # Simple letter/number
                vk = VK_CODES[char.upper()]
                need_shift = char.isupper() or char in '!@#$%^&*()_+{}|:"<>?'

                if need_shift:
                    _key_down(VK_CODES["SHIFT"])

                _key_down(vk)
                time.sleep(0.01)
                _key_up(vk)

                if need_shift:
                    _key_up(VK_CODES["SHIFT"])

                time.sleep(self._key_delay_ms / 1000.0)
            elif char == " ":
                self.press_key("SPACE")
            elif char == "\n":
                self.press_key("ENTER")
            elif char == "\t":
                self.press_key("TAB")
            else:
                # Use Unicode input for special characters
                logger.warning("Cannot type character: %r (use paste_mode=True)", char)

    def hold(self, key: str) -> None:
        """
        Hold a key down.

        Args:
            key: Key to hold
        """
        key_upper = key.upper()
        if key_upper not in VK_CODES:
            raise ValueError(f"Unknown key: {key}")
        _key_down(VK_CODES[key_upper])

    def release(self, key: str) -> None:
        """
        Release a held key.

        Args:
            key: Key to release
        """
        key_upper = key.upper()
        if key_upper not in VK_CODES:
            raise ValueError(f"Unknown key: {key}")
        _key_up(VK_CODES[key_upper])
