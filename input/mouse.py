"""
RetroAuto v2 - Mouse Controller

Smooth mouse control using pywin32 for Windows.
"""

import time

import win32api
import win32con

from infra import get_logger

logger = get_logger("Mouse")


class MouseController:
    """
    Mouse control using Windows API.

    Features:
    - Move to coordinates
    - Click (left/right/middle)
    - Double-click
    - Smooth movement (optional)
    """

    # Mouse button mappings
    BUTTONS = {
        "left": (win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP),
        "right": (win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP),
        "middle": (win32con.MOUSEEVENTF_MIDDLEDOWN, win32con.MOUSEEVENTF_MIDDLEUP),
    }

    def __init__(self, click_delay_ms: int = 80) -> None:
        """
        Initialize mouse controller.

        Args:
            click_delay_ms: Delay between clicks for multi-click
        """
        self._click_delay_ms = click_delay_ms

    @staticmethod
    def get_position() -> tuple[int, int]:
        """Get current cursor position."""
        return win32api.GetCursorPos()

    def move_to(self, x: int, y: int) -> None:
        """
        Move cursor to absolute coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        win32api.SetCursorPos((x, y))
        logger.debug("Mouse moved to (%d, %d)", x, y)

    def move_relative(self, dx: int, dy: int) -> None:
        """Move cursor relative to current position."""
        x, y = self.get_position()
        self.move_to(x + dx, y + dy)

    def click(
        self,
        x: int | None = None,
        y: int | None = None,
        button: str = "left",
        clicks: int = 1,
        interval_ms: int | None = None,
    ) -> None:
        """
        Click at position.

        Args:
            x: X coordinate (None = current position)
            y: Y coordinate (None = current position)
            button: "left", "right", or "middle"
            clicks: Number of clicks
            interval_ms: Interval between clicks (None = use default)
        """
        if button not in self.BUTTONS:
            raise ValueError(f"Invalid button: {button}. Use 'left', 'right', or 'middle'")

        # Move if coordinates provided
        if x is not None and y is not None:
            self.move_to(x, y)

        down_flag, up_flag = self.BUTTONS[button]
        interval = (interval_ms if interval_ms is not None else self._click_delay_ms) / 1000.0

        for i in range(clicks):
            win32api.mouse_event(down_flag, 0, 0, 0, 0)
            time.sleep(0.01)  # Brief delay between down/up
            win32api.mouse_event(up_flag, 0, 0, 0, 0)

            if i < clicks - 1:
                time.sleep(interval)

        pos = self.get_position()
        logger.debug("Clicked %s x%d at (%d, %d)", button, clicks, pos[0], pos[1])

    def double_click(
        self,
        x: int | None = None,
        y: int | None = None,
        button: str = "left",
    ) -> None:
        """Double-click at position."""
        self.click(x, y, button, clicks=2, interval_ms=50)

    def right_click(
        self,
        x: int | None = None,
        y: int | None = None,
    ) -> None:
        """Right-click at position."""
        self.click(x, y, button="right")

    def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        button: str = "left",
        duration_ms: int = 100,
    ) -> None:
        """
        Drag from start to end position.

        Args:
            start_x, start_y: Start position
            end_x, end_y: End position
            button: Button to hold during drag
            duration_ms: Duration of drag movement
        """
        if button not in self.BUTTONS:
            raise ValueError(f"Invalid button: {button}")

        down_flag, up_flag = self.BUTTONS[button]

        # Move to start
        self.move_to(start_x, start_y)
        time.sleep(0.01)

        # Press down
        win32api.mouse_event(down_flag, 0, 0, 0, 0)

        # Move to end (simple linear interpolation)
        steps = max(1, duration_ms // 10)
        for i in range(1, steps + 1):
            progress = i / steps
            x = int(start_x + (end_x - start_x) * progress)
            y = int(start_y + (end_y - start_y) * progress)
            self.move_to(x, y)
            time.sleep(0.01)

        # Release
        win32api.mouse_event(up_flag, 0, 0, 0, 0)
        logger.debug("Dragged from (%d, %d) to (%d, %d)", start_x, start_y, end_x, end_y)

    def scroll(self, delta: int, x: int | None = None, y: int | None = None) -> None:
        """
        Scroll the mouse wheel.

        Args:
            delta: Scroll amount (positive = up, negative = down)
            x, y: Position to scroll at (None = current)
        """
        if x is not None and y is not None:
            self.move_to(x, y)

        # WHEEL_DELTA is 120
        wheel_delta = delta * 120
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, wheel_delta, 0)
        logger.debug("Scrolled %d at cursor position", delta)
