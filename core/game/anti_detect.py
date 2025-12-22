"""
RetroAuto v2 - Anti-Detection

Human-like behavior simulation to avoid detection.
Part of RetroScript Phase 20 - Game-Specific Features.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# Try to import pyautogui
try:
    import pyautogui

    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    pyautogui = None


@dataclass
class BehaviorProfile:
    """Profile defining human-like behavior patterns."""

    name: str = "default"

    # Timing
    min_delay: float = 0.05  # Minimum delay between actions
    max_delay: float = 0.3  # Maximum delay
    typing_min: float = 0.03  # Minimum typing interval
    typing_max: float = 0.15  # Maximum typing interval

    # Mouse behavior
    mouse_speed_min: float = 0.1  # Minimum mouse move duration
    mouse_speed_max: float = 0.4  # Maximum mouse move duration
    click_hold_min: float = 0.05  # Minimum click hold time
    click_hold_max: float = 0.15  # Maximum click hold time

    # Randomness
    position_variance: int = 3  # Pixel variance for click position
    occasional_pause_chance: float = 0.02  # Chance of random pause
    occasional_pause_min: float = 0.5  # Min pause duration
    occasional_pause_max: float = 2.0  # Max pause duration

    # Mistakes
    typo_chance: float = 0.0  # Chance of making typo (0 = disabled)
    misclick_chance: float = 0.0  # Chance of misclick (0 = disabled)


# Preset profiles
PROFILES = {
    "fast": BehaviorProfile(
        name="fast",
        min_delay=0.02,
        max_delay=0.1,
        mouse_speed_min=0.05,
        mouse_speed_max=0.15,
    ),
    "normal": BehaviorProfile(
        name="normal",
        min_delay=0.05,
        max_delay=0.3,
        mouse_speed_min=0.1,
        mouse_speed_max=0.4,
    ),
    "careful": BehaviorProfile(
        name="careful",
        min_delay=0.1,
        max_delay=0.5,
        mouse_speed_min=0.2,
        mouse_speed_max=0.6,
        occasional_pause_chance=0.05,
    ),
    "human": BehaviorProfile(
        name="human",
        min_delay=0.08,
        max_delay=0.4,
        typing_min=0.05,
        typing_max=0.2,
        mouse_speed_min=0.15,
        mouse_speed_max=0.5,
        position_variance=5,
        occasional_pause_chance=0.03,
        typo_chance=0.01,
    ),
}


class HumanBehavior:
    """Simulate human-like behavior for automation.

    Usage:
        human = HumanBehavior()
        human.click(100, 200)  # Humanized click
        human.type("Hello")    # Humanized typing
    """

    def __init__(self, profile: str | BehaviorProfile = "normal") -> None:
        if isinstance(profile, str):
            self.profile = PROFILES.get(profile, PROFILES["normal"])
        else:
            self.profile = profile

        self._last_action_time = 0.0

    def set_profile(self, profile: str | BehaviorProfile) -> None:
        """Set behavior profile."""
        if isinstance(profile, str):
            self.profile = PROFILES.get(profile, PROFILES["normal"])
        else:
            self.profile = profile

    def random_delay(self, min_d: float | None = None, max_d: float | None = None) -> None:
        """Wait for a random duration.

        Args:
            min_d: Minimum delay (default from profile)
            max_d: Maximum delay (default from profile)
        """
        min_d = min_d or self.profile.min_delay
        max_d = max_d or self.profile.max_delay
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)

    def maybe_pause(self) -> bool:
        """Occasionally take a random pause.

        Returns:
            True if paused
        """
        if random.random() < self.profile.occasional_pause_chance:
            pause = random.uniform(
                self.profile.occasional_pause_min,
                self.profile.occasional_pause_max,
            )
            time.sleep(pause)
            return True
        return False

    def vary_position(self, x: int, y: int) -> tuple[int, int]:
        """Add small random variance to position.

        Args:
            x: Original X
            y: Original Y

        Returns:
            Varied (x, y)
        """
        variance = self.profile.position_variance
        new_x = x + random.randint(-variance, variance)
        new_y = y + random.randint(-variance, variance)
        return (new_x, new_y)

    def click(
        self,
        x: int,
        y: int,
        button: str = "left",
        vary: bool = True,
    ) -> None:
        """Perform a humanized click.

        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button
            vary: Whether to vary position
        """
        if not HAS_PYAUTOGUI:
            print(f"[HUMAN] click({x}, {y})")
            return

        # Vary position
        if vary:
            x, y = self.vary_position(x, y)

        # Move with human-like speed
        duration = random.uniform(
            self.profile.mouse_speed_min,
            self.profile.mouse_speed_max,
        )
        pyautogui.moveTo(x, y, duration=duration)

        # Random delay before click
        self.random_delay()

        # Click with hold time
        hold_time = random.uniform(
            self.profile.click_hold_min,
            self.profile.click_hold_max,
        )
        pyautogui.mouseDown(button=button)
        time.sleep(hold_time)
        pyautogui.mouseUp(button=button)

        # Maybe pause
        self.maybe_pause()

    def double_click(self, x: int, y: int, vary: bool = True) -> None:
        """Perform humanized double-click."""
        self.click(x, y, vary=vary)
        time.sleep(random.uniform(0.05, 0.15))
        self.click(x, y, vary=False)

    def drag(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        button: str = "left",
    ) -> None:
        """Perform humanized drag."""
        if not HAS_PYAUTOGUI:
            print(f"[HUMAN] drag({x1}, {y1} -> {x2}, {y2})")
            return

        # Move to start
        duration = random.uniform(
            self.profile.mouse_speed_min,
            self.profile.mouse_speed_max,
        )
        pyautogui.moveTo(x1, y1, duration=duration)
        self.random_delay()

        # Drag to end
        drag_duration = random.uniform(
            self.profile.mouse_speed_min * 2,
            self.profile.mouse_speed_max * 2,
        )
        pyautogui.drag(x2 - x1, y2 - y1, duration=drag_duration, button=button)

    def type(self, text: str, with_typos: bool = False) -> None:
        """Type text with humanized timing.

        Args:
            text: Text to type
            with_typos: Enable random typos
        """
        if not HAS_PYAUTOGUI:
            print(f"[HUMAN] type({text})")
            return

        for _i, char in enumerate(text):
            # Maybe make typo
            if with_typos and random.random() < self.profile.typo_chance:
                # Type wrong char then backspace
                wrong = random.choice("abcdefghijklmnopqrstuvwxyz")
                pyautogui.press(wrong)
                time.sleep(random.uniform(0.1, 0.3))
                pyautogui.press("backspace")
                time.sleep(random.uniform(0.1, 0.2))

            # Type the character
            pyautogui.press(char) if len(char) > 1 else pyautogui.write(char)

            # Random typing delay
            delay = random.uniform(
                self.profile.typing_min,
                self.profile.typing_max,
            )
            time.sleep(delay)

            # Occasional longer pause
            if random.random() < 0.05:
                time.sleep(random.uniform(0.2, 0.5))

    def press(self, key: str, hold: bool = False) -> None:
        """Press key with humanized timing.

        Args:
            key: Key to press
            hold: Whether to hold briefly
        """
        if not HAS_PYAUTOGUI:
            print(f"[HUMAN] press({key})")
            return

        self.random_delay()

        if hold:
            hold_time = random.uniform(0.05, 0.2)
            pyautogui.keyDown(key)
            time.sleep(hold_time)
            pyautogui.keyUp(key)
        else:
            pyautogui.press(key)

    def scroll(self, amount: int, x: int | None = None, y: int | None = None) -> None:
        """Scroll with humanized behavior."""
        if not HAS_PYAUTOGUI:
            print(f"[HUMAN] scroll({amount})")
            return

        if x is not None and y is not None:
            self.click(x, y)
            self.random_delay()

        # Scroll in smaller increments
        direction = 1 if amount > 0 else -1
        remaining = abs(amount)

        while remaining > 0:
            step = min(remaining, random.randint(1, 3))
            pyautogui.scroll(step * direction)
            remaining -= step
            self.random_delay(0.02, 0.1)


class AntiDetection:
    """Anti-detection wrapper combining multiple techniques.

    Usage:
        anti = AntiDetection()
        anti.wrap(my_function)()  # Wrap function with delays

        with anti.guard():
            # Actions within guard get random delays
            pass
    """

    def __init__(self, profile: str = "normal") -> None:
        self.human = HumanBehavior(profile)
        self._enabled = True

    def enable(self) -> None:
        """Enable anti-detection."""
        self._enabled = True

    def disable(self) -> None:
        """Disable anti-detection."""
        self._enabled = False

    def wrap(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap a function with anti-detection delays.

        Args:
            func: Function to wrap

        Returns:
            Wrapped function
        """

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if self._enabled:
                self.human.random_delay()
            result = func(*args, **kwargs)
            if self._enabled:
                self.human.maybe_pause()
            return result

        return wrapped

    def guard(self) -> DetectionGuard:
        """Context manager for anti-detection.

        Usage:
            with anti.guard():
                click(100, 200)
                press("a")
        """
        return DetectionGuard(self.human, self._enabled)


class DetectionGuard:
    """Context manager for anti-detection."""

    def __init__(self, human: HumanBehavior, enabled: bool) -> None:
        self._human = human
        self._enabled = enabled

    def __enter__(self) -> DetectionGuard:
        if self._enabled:
            self._human.random_delay()
        return self

    def __exit__(self, *args: Any) -> None:
        if self._enabled:
            self._human.maybe_pause()


# Global instance
_anti: AntiDetection | None = None


def get_anti_detection() -> AntiDetection:
    """Get the default anti-detection instance."""
    global _anti
    if _anti is None:
        _anti = AntiDetection()
    return _anti


def human_click(x: int, y: int, **kwargs: Any) -> None:
    """Perform humanized click."""
    get_anti_detection().human.click(x, y, **kwargs)


def human_type(text: str, **kwargs: Any) -> None:
    """Perform humanized typing."""
    get_anti_detection().human.type(text, **kwargs)


def random_delay(min_d: float = 0.05, max_d: float = 0.3) -> None:
    """Random delay."""
    get_anti_detection().human.random_delay(min_d, max_d)
