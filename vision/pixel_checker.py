"""
RetroAuto v2 - Pixel Color Checker

Fast pixel color checking for automation triggers.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass

from infra import get_logger

logger = get_logger("PixelChecker")

# Windows API
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32


@dataclass
class PixelResult:
    """Result of pixel color check."""

    x: int
    y: int
    r: int
    g: int
    b: int


class PixelChecker:
    """
    Fast pixel color checking using Windows API.
    
    Much faster than capturing screen and extracting pixel.
    Uses GetPixel directly from screen DC.
    
    Usage:
        checker = PixelChecker()
        result = checker.get_pixel(100, 200)
        if result.r > 200 and result.g < 50:
            print("Red detected!")
    """

    def __init__(self) -> None:
        """Initialize pixel checker."""
        self._hdc = user32.GetDC(0)  # Screen DC

    def __del__(self) -> None:
        """Clean up DC."""
        if hasattr(self, "_hdc") and self._hdc:
            user32.ReleaseDC(0, self._hdc)

    def get_pixel(self, x: int, y: int) -> PixelResult:
        """
        Get pixel color at coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            PixelResult with RGB values
        """
        color = gdi32.GetPixel(self._hdc, x, y)
        
        # Extract RGB from COLORREF (0x00BBGGRR)
        r = color & 0xFF
        g = (color >> 8) & 0xFF
        b = (color >> 16) & 0xFF
        
        return PixelResult(x=x, y=y, r=r, g=g, b=b)

    def check_color(
        self,
        x: int,
        y: int,
        r: int,
        g: int,
        b: int,
        tolerance: int = 10,
    ) -> bool:
        """
        Check if pixel matches expected color.
        
        Args:
            x, y: Coordinates
            r, g, b: Expected RGB values
            tolerance: Allowed difference per channel
            
        Returns:
            True if color matches within tolerance
        """
        pixel = self.get_pixel(x, y)
        
        return (
            abs(pixel.r - r) <= tolerance
            and abs(pixel.g - g) <= tolerance
            and abs(pixel.b - b) <= tolerance
        )

    def wait_for_color(
        self,
        x: int,
        y: int,
        r: int,
        g: int,
        b: int,
        tolerance: int = 10,
        timeout_ms: int = 10000,
        poll_ms: int = 100,
        appear: bool = True,
    ) -> bool:
        """
        Wait for pixel color to appear or disappear.
        
        Args:
            x, y: Coordinates
            r, g, b: Expected RGB values
            tolerance: Allowed difference
            timeout_ms: Maximum wait time
            poll_ms: Time between checks
            appear: True = wait for color, False = wait until color gone
            
        Returns:
            True if condition met, False if timeout
        """
        import time

        start = time.time()
        timeout_sec = timeout_ms / 1000.0
        poll_sec = poll_ms / 1000.0

        while time.time() - start < timeout_sec:
            matches = self.check_color(x, y, r, g, b, tolerance)
            
            if appear and matches:
                return True
            elif not appear and not matches:
                return True
            
            time.sleep(poll_sec)

        return False

    def find_color_in_region(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        r: int,
        g: int,
        b: int,
        tolerance: int = 10,
        step: int = 5,
    ) -> PixelResult | None:
        """
        Find first occurrence of color in region.
        
        Args:
            x1, y1, x2, y2: Region bounds
            r, g, b: Target color
            tolerance: Color tolerance
            step: Pixel step for faster scanning
            
        Returns:
            PixelResult if found, None otherwise
        """
        for y in range(y1, y2, step):
            for x in range(x1, x2, step):
                if self.check_color(x, y, r, g, b, tolerance):
                    return self.get_pixel(x, y)
        
        return None


# Global instance for convenience
_checker: PixelChecker | None = None


def get_pixel_checker() -> PixelChecker:
    """Get global pixel checker instance."""
    global _checker
    if _checker is None:
        _checker = PixelChecker()
    return _checker
