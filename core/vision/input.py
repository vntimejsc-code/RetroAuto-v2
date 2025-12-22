"""
RetroAuto v2 - Input Automation

Mouse and keyboard automation for RetroScript.
Part of RetroScript Phase 10 - Image Recognition.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Try to import optional dependencies
try:
    import pyautogui

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    pyautogui = None


class MouseButton(Enum):
    """Mouse button types."""

    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


@dataclass
class Point:
    """A 2D point."""

    x: int
    y: int

    def offset(self, dx: int, dy: int) -> Point:
        """Return new point with offset."""
        return Point(self.x + dx, self.y + dy)


class MouseController:
    """Mouse automation controller.

    Usage:
        mouse = MouseController()
        mouse.click(100, 200)
        mouse.moveto(300, 400)
    """

    def __init__(self, humanize: bool = True) -> None:
        self.humanize = humanize  # Add human-like delays
        self._position = Point(0, 0)

        if not HAS_PYAUTOGUI:
            print("[WARN] PyAutoGUI not installed. Using stub mode.")

    def click(
        self,
        x: int | None = None,
        y: int | None = None,
        button: str | MouseButton = MouseButton.LEFT,
        clicks: int = 1,
        interval: float = 0.1,
    ) -> None:
        """Click at position.

        Args:
            x: X coordinate (None = current position)
            y: Y coordinate (None = current position)
            button: Mouse button
            clicks: Number of clicks
            interval: Interval between clicks
        """
        if isinstance(button, MouseButton):
            button = button.value

        if not HAS_PYAUTOGUI:
            print(f"[STUB] click({x}, {y}, button={button}, clicks={clicks})")
            return

        if x is not None and y is not None:
            if self.humanize:
                self._move_humanized(x, y)
            else:
                pyautogui.moveTo(x, y)

        pyautogui.click(button=button, clicks=clicks, interval=interval)
        self._update_position()

    def moveto(self, x: int, y: int, duration: float = 0.0) -> None:
        """Move mouse to position.

        Args:
            x: Target X
            y: Target Y
            duration: Movement duration
        """
        if not HAS_PYAUTOGUI:
            print(f"[STUB] moveto({x}, {y})")
            return

        if self.humanize and duration == 0:
            self._move_humanized(x, y)
        else:
            pyautogui.moveTo(x, y, duration=duration)

        self._update_position()

    def move(self, dx: int, dy: int, duration: float = 0.0) -> None:
        """Move mouse relative to current position."""
        if not HAS_PYAUTOGUI:
            print(f"[STUB] move({dx}, {dy})")
            return

        pyautogui.move(dx, dy, duration=duration)
        self._update_position()

    def drag(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        button: str = "left",
        duration: float = 0.5,
    ) -> None:
        """Drag from one point to another."""
        if not HAS_PYAUTOGUI:
            print(f"[STUB] drag({x1}, {y1}, {x2}, {y2})")
            return

        pyautogui.moveTo(x1, y1)
        pyautogui.drag(x2 - x1, y2 - y1, duration=duration, button=button)
        self._update_position()

    def scroll(self, amount: int, x: int | None = None, y: int | None = None) -> None:
        """Scroll the mouse wheel.

        Args:
            amount: Scroll amount (positive = up, negative = down)
            x: X position (optional)
            y: Y position (optional)
        """
        if not HAS_PYAUTOGUI:
            print(f"[STUB] scroll({amount})")
            return

        if x is not None and y is not None:
            pyautogui.moveTo(x, y)

        pyautogui.scroll(amount)

    def position(self) -> Point:
        """Get current mouse position."""
        if not HAS_PYAUTOGUI:
            return self._position

        pos = pyautogui.position()
        self._position = Point(pos.x, pos.y)
        return self._position

    def _move_humanized(self, x: int, y: int) -> None:
        """Move with human-like motion."""
        # Get current position
        current = self.position()

        # Calculate distance
        dx = x - current.x
        dy = y - current.y
        distance = (dx**2 + dy**2) ** 0.5

        # Duration based on distance
        duration = min(0.5, max(0.1, distance / 2000))

        # Add slight curve
        pyautogui.moveTo(
            x + random.randint(-2, 2),
            y + random.randint(-2, 2),
            duration=duration,
        )
        pyautogui.moveTo(x, y, duration=0.05)

    def _update_position(self) -> None:
        """Update cached position."""
        if HAS_PYAUTOGUI:
            pos = pyautogui.position()
            self._position = Point(pos.x, pos.y)


class KeyboardController:
    """Keyboard automation controller.

    Usage:
        kb = KeyboardController()
        kb.type("Hello, world!")
        kb.press("enter")
        kb.hotkey("ctrl", "c")
    """

    def __init__(self, type_delay: float = 0.05) -> None:
        self.type_delay = type_delay

        if not HAS_PYAUTOGUI:
            print("[WARN] PyAutoGUI not installed. Using stub mode.")

    def type(self, text: str, interval: float | None = None) -> None:
        """Type text with optional interval between keys.

        Args:
            text: Text to type
            interval: Delay between keystrokes
        """
        if not HAS_PYAUTOGUI:
            print(f"[STUB] type({text})")
            return

        interval = interval or self.type_delay
        pyautogui.write(text, interval=interval)

    def press(self, key: str, presses: int = 1, interval: float = 0.1) -> None:
        """Press a key.

        Args:
            key: Key name (e.g., 'enter', 'tab', 'a')
            presses: Number of times to press
            interval: Interval between presses
        """
        if not HAS_PYAUTOGUI:
            print(f"[STUB] press({key})")
            return

        pyautogui.press(key, presses=presses, interval=interval)

    def hotkey(self, *keys: str) -> None:
        """Press a key combination.

        Args:
            keys: Keys to press together (e.g., 'ctrl', 'c')
        """
        if not HAS_PYAUTOGUI:
            print(f"[STUB] hotkey({keys})")
            return

        pyautogui.hotkey(*keys)

    def keydown(self, key: str) -> None:
        """Hold a key down."""
        if not HAS_PYAUTOGUI:
            print(f"[STUB] keydown({key})")
            return

        pyautogui.keyDown(key)

    def keyup(self, key: str) -> None:
        """Release a held key."""
        if not HAS_PYAUTOGUI:
            print(f"[STUB] keyup({key})")
            return

        pyautogui.keyUp(key)

    def hold(self, key: str, duration: float = 0.5) -> None:
        """Hold a key for a duration.

        Args:
            key: Key to hold
            duration: Hold duration in seconds
        """
        if not HAS_PYAUTOGUI:
            print(f"[STUB] hold({key}, {duration})")
            return

        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)


class InputController:
    """Combined mouse and keyboard controller.

    Usage:
        input = InputController()
        input.click(100, 200)
        input.type("Hello")
        input.hotkey("ctrl", "s")
    """

    def __init__(self, humanize: bool = True, type_delay: float = 0.05) -> None:
        self.mouse = MouseController(humanize=humanize)
        self.keyboard = KeyboardController(type_delay=type_delay)

    # Mouse methods
    def click(self, x: int | None = None, y: int | None = None, **kwargs: Any) -> None:
        """Click at position."""
        self.mouse.click(x, y, **kwargs)

    def moveto(self, x: int, y: int, **kwargs: Any) -> None:
        """Move mouse to position."""
        self.mouse.moveto(x, y, **kwargs)

    def drag(self, x1: int, y1: int, x2: int, y2: int, **kwargs: Any) -> None:
        """Drag from one point to another."""
        self.mouse.drag(x1, y1, x2, y2, **kwargs)

    def scroll(self, amount: int, **kwargs: Any) -> None:
        """Scroll mouse wheel."""
        self.mouse.scroll(amount, **kwargs)

    # Keyboard methods
    def type(self, text: str, **kwargs: Any) -> None:
        """Type text."""
        self.keyboard.type(text, **kwargs)

    def press(self, key: str, **kwargs: Any) -> None:
        """Press a key."""
        self.keyboard.press(key, **kwargs)

    def hotkey(self, *keys: str) -> None:
        """Press key combination."""
        self.keyboard.hotkey(*keys)

    def position(self) -> Point:
        """Get mouse position."""
        return self.mouse.position()


# Global controller instance
_default_controller: InputController | None = None


def get_controller() -> InputController:
    """Get the default input controller."""
    global _default_controller
    if _default_controller is None:
        _default_controller = InputController()
    return _default_controller


# Convenience functions
def click(x: int | None = None, y: int | None = None, **kwargs: Any) -> None:
    """Click at position."""
    get_controller().click(x, y, **kwargs)


def moveto(x: int, y: int, **kwargs: Any) -> None:
    """Move mouse to position."""
    get_controller().moveto(x, y, **kwargs)


def type_text(text: str, **kwargs: Any) -> None:
    """Type text."""
    get_controller().type(text, **kwargs)


def press(key: str, **kwargs: Any) -> None:
    """Press a key."""
    get_controller().press(key, **kwargs)


def hotkey(*keys: str) -> None:
    """Press key combination."""
    get_controller().hotkey(*keys)
