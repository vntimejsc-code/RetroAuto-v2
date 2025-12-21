"""
RetroAuto v2 - Pixel Detection

Fast color-based pixel detection for game automation.
Part of RetroScript Phase 20 - Game-Specific Features.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Try to import optional dependencies
try:
    import mss
    import numpy as np
    HAS_MSS = True
except ImportError:
    HAS_MSS = False
    mss = None
    np = None

try:
    from PIL import ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    ImageGrab = None


@dataclass
class Color:
    """RGB color with optional tolerance."""

    r: int
    g: int
    b: int
    tolerance: int = 10

    def matches(self, other: "Color") -> bool:
        """Check if colors match within tolerance."""
        return (
            abs(self.r - other.r) <= self.tolerance and
            abs(self.g - other.g) <= self.tolerance and
            abs(self.b - other.b) <= self.tolerance
        )

    @classmethod
    def from_hex(cls, hex_color: str, tolerance: int = 10) -> "Color":
        """Create color from hex string like '#FF0000'."""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return cls(r, g, b, tolerance)

    @classmethod
    def from_tuple(cls, rgb: tuple[int, int, int], tolerance: int = 10) -> "Color":
        """Create color from (r, g, b) tuple."""
        return cls(rgb[0], rgb[1], rgb[2], tolerance)

    def to_hex(self) -> str:
        """Convert to hex string."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_tuple(self) -> tuple[int, int, int]:
        """Convert to (r, g, b) tuple."""
        return (self.r, self.g, self.b)


@dataclass
class PixelResult:
    """Result of a pixel check."""

    x: int
    y: int
    color: Color
    matched: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "r": self.color.r,
            "g": self.color.g,
            "b": self.color.b,
            "hex": self.color.to_hex(),
            "matched": self.matched,
        }


class PixelChecker:
    """Fast pixel-based detection for games.

    Usage:
        checker = PixelChecker()
        
        # Get pixel color
        color = checker.get_pixel(100, 200)
        
        # Check if pixel matches color
        if checker.check_pixel(100, 200, Color(255, 0, 0)):
            print("Red pixel found!")
        
        # Find pixel with color
        result = checker.find_pixel(Color(255, 0, 0), region=(0, 0, 500, 500))
    """

    def __init__(self) -> None:
        self._screen_cache: Any = None
        self._cache_time: float = 0

    def get_pixel(self, x: int, y: int) -> Color:
        """Get the color of a pixel at position.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Color at position
        """
        screen = self._capture_screen()
        if screen is None:
            return Color(0, 0, 0)

        # Get pixel value
        try:
            if HAS_MSS and isinstance(screen, np.ndarray):
                # BGR format from mss
                b, g, r = screen[y, x, :3]
                return Color(int(r), int(g), int(b))
            else:
                # PIL format
                r, g, b = screen.getpixel((x, y))[:3]
                return Color(r, g, b)
        except (IndexError, Exception):
            return Color(0, 0, 0)

    def check_pixel(
        self,
        x: int,
        y: int,
        expected: Color | tuple[int, int, int] | str,
        tolerance: int | None = None,
    ) -> bool:
        """Check if pixel matches expected color.

        Args:
            x: X coordinate
            y: Y coordinate
            expected: Expected color
            tolerance: Override color tolerance

        Returns:
            True if pixel matches
        """
        # Convert expected to Color
        if isinstance(expected, str):
            expected = Color.from_hex(expected, tolerance or 10)
        elif isinstance(expected, tuple):
            expected = Color.from_tuple(expected, tolerance or 10)
        elif tolerance is not None:
            expected = Color(expected.r, expected.g, expected.b, tolerance)

        actual = self.get_pixel(x, y)
        return expected.matches(actual)

    def check_pixels(
        self,
        checks: list[tuple[int, int, Color | str]],
        all_match: bool = True,
    ) -> bool:
        """Check multiple pixels at once.

        Args:
            checks: List of (x, y, color) tuples
            all_match: If True, all must match; if False, any match is enough

        Returns:
            True if condition is met
        """
        results = []

        for x, y, expected in checks:
            if isinstance(expected, str):
                expected = Color.from_hex(expected)
            elif isinstance(expected, tuple):
                expected = Color.from_tuple(expected)

            results.append(self.check_pixel(x, y, expected))

        if all_match:
            return all(results)
        else:
            return any(results)

    def find_pixel(
        self,
        target: Color | str,
        region: tuple[int, int, int, int] | None = None,
        step: int = 1,
    ) -> PixelResult | None:
        """Find first pixel matching target color.

        Args:
            target: Target color to find
            region: (x, y, width, height) search region
            step: Pixel step for faster search

        Returns:
            PixelResult if found, None otherwise
        """
        if isinstance(target, str):
            target = Color.from_hex(target)

        screen = self._capture_screen(region)
        if screen is None:
            return None

        # Region offset
        offset_x = region[0] if region else 0
        offset_y = region[1] if region else 0

        # Search for pixel
        try:
            if HAS_MSS and isinstance(screen, np.ndarray):
                h, w = screen.shape[:2]
                for y in range(0, h, step):
                    for x in range(0, w, step):
                        b, g, r = screen[y, x, :3]
                        color = Color(int(r), int(g), int(b))
                        if target.matches(color):
                            return PixelResult(
                                x=x + offset_x,
                                y=y + offset_y,
                                color=color,
                            )
        except Exception:
            pass

        return None

    def find_all_pixels(
        self,
        target: Color | str,
        region: tuple[int, int, int, int] | None = None,
        max_results: int = 100,
        step: int = 1,
    ) -> list[PixelResult]:
        """Find all pixels matching target color.

        Args:
            target: Target color to find
            region: Search region
            max_results: Maximum results to return
            step: Search step

        Returns:
            List of PixelResults
        """
        if isinstance(target, str):
            target = Color.from_hex(target)

        results: list[PixelResult] = []
        screen = self._capture_screen(region)
        if screen is None:
            return results

        offset_x = region[0] if region else 0
        offset_y = region[1] if region else 0

        try:
            if HAS_MSS and isinstance(screen, np.ndarray):
                h, w = screen.shape[:2]
                for y in range(0, h, step):
                    for x in range(0, w, step):
                        if len(results) >= max_results:
                            break
                        b, g, r = screen[y, x, :3]
                        color = Color(int(r), int(g), int(b))
                        if target.matches(color):
                            results.append(PixelResult(
                                x=x + offset_x,
                                y=y + offset_y,
                                color=color,
                            ))
        except Exception:
            pass

        return results

    def wait_for_pixel(
        self,
        x: int,
        y: int,
        expected: Color | str,
        timeout: float = 10.0,
        interval: float = 0.1,
    ) -> bool:
        """Wait for pixel to match expected color.

        Args:
            x: X coordinate
            y: Y coordinate
            expected: Expected color
            timeout: Maximum wait time
            interval: Check interval

        Returns:
            True if pixel matched within timeout
        """
        import time

        if isinstance(expected, str):
            expected = Color.from_hex(expected)

        start = time.time()
        while time.time() - start < timeout:
            if self.check_pixel(x, y, expected):
                return True
            time.sleep(interval)

        return False

    def _capture_screen(
        self,
        region: tuple[int, int, int, int] | None = None,
    ) -> Any:
        """Capture screen or region."""
        if HAS_MSS:
            with mss.mss() as sct:
                if region:
                    x, y, w, h = region
                    monitor = {"left": x, "top": y, "width": w, "height": h}
                else:
                    monitor = sct.monitors[1]

                screenshot = sct.grab(monitor)
                return np.array(screenshot)

        elif HAS_PIL:
            if region:
                x, y, w, h = region
                return ImageGrab.grab(bbox=(x, y, x + w, y + h))
            return ImageGrab.grab()

        return None


# Global instance
_checker: PixelChecker | None = None


def get_checker() -> PixelChecker:
    """Get the default pixel checker."""
    global _checker
    if _checker is None:
        _checker = PixelChecker()
    return _checker


# Convenience functions
def get_pixel(x: int, y: int) -> Color:
    """Get pixel color at position."""
    return get_checker().get_pixel(x, y)


def check_pixel(x: int, y: int, color: Color | str) -> bool:
    """Check if pixel matches color."""
    return get_checker().check_pixel(x, y, color)


def find_pixel(color: Color | str, region: tuple | None = None) -> PixelResult | None:
    """Find first pixel matching color."""
    return get_checker().find_pixel(color, region)
