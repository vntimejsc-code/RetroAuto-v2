"""
RetroAuto v2 - Screen Capture

Fast screen capture using mss library.
"""

import numpy as np
from mss import mss
from mss.base import MSSBase

from core.models import ROI
from infra import get_logger

logger = get_logger("Capture")


class ScreenCapture:
    """
    High-performance screen capture using mss.

    Features:
    - Full screen capture
    - ROI-specific capture (faster)
    - Grayscale conversion
    - Monitor selection
    """

    def __init__(self) -> None:
        self._sct: MSSBase | None = None

    def _get_sct(self) -> MSSBase:
        """Get or create mss instance."""
        if self._sct is None:
            self._sct = mss()
        return self._sct

    @property
    def monitors(self) -> list[dict]:
        """Get list of available monitors."""
        return list(self._get_sct().monitors)

    @property
    def screen_size(self) -> tuple[int, int]:
        """Get primary screen size (width, height)."""
        mon = self._get_sct().monitors[1]  # Primary monitor
        return mon["width"], mon["height"]

    def capture_full(self, monitor: int = 1, grayscale: bool = False) -> np.ndarray:
        """
        Capture full screen.

        Args:
            monitor: Monitor index (0=all, 1=primary, 2+=secondary)
            grayscale: Convert to grayscale

        Returns:
            numpy array (H, W, C) or (H, W) if grayscale
        """
        sct = self._get_sct()
        mon = sct.monitors[monitor]
        img = np.array(sct.grab(mon))

        # mss returns BGRA, convert to BGR or Gray
        if grayscale:
            return self._to_grayscale(img)
        return img[:, :, :3]  # Remove alpha channel

    def capture_roi(self, roi: ROI, grayscale: bool = False) -> np.ndarray:
        """
        Capture specific region (faster than full + crop).

        Args:
            roi: Region of interest
            grayscale: Convert to grayscale

        Returns:
            numpy array of the region
        """
        sct = self._get_sct()
        region = {
            "left": roi.x,
            "top": roi.y,
            "width": roi.w,
            "height": roi.h,
        }
        img = np.array(sct.grab(region))

        if grayscale:
            return self._to_grayscale(img)
        return img[:, :, :3]

    def _to_grayscale(self, img: np.ndarray) -> np.ndarray:
        """Convert BGRA/BGR to grayscale using luminance formula."""
        if img.shape[2] == 4:
            # BGRA
            b, g, r = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        else:
            # BGR
            b, g, r = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        # Standard luminance formula
        return (0.299 * r + 0.587 * g + 0.114 * b).astype(np.uint8)

    def close(self) -> None:
        """Release mss resources."""
        if self._sct is not None:
            self._sct.close()
            self._sct = None

    def __enter__(self) -> "ScreenCapture":
        return self

    def __exit__(self, *args) -> None:  # type: ignore
        self.close()


# Singleton instance for convenience
_capture: ScreenCapture | None = None


def get_capture() -> ScreenCapture:
    """Get singleton screen capture instance."""
    global _capture
    if _capture is None:
        _capture = ScreenCapture()
    return _capture
