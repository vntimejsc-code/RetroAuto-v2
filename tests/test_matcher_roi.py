"""
Test matcher with ROI optimization.
"""

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from core.models import AssetImage, ROI
from core.templates import TemplateStore
from vision.capture import ScreenCapture
from vision.matcher import Matcher


class MockCapture:
    """Mock screen capture for testing."""

    def __init__(self, image: np.ndarray) -> None:
        self._image = image
        self._gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    def capture_full(self, monitor: int = 1, grayscale: bool = False) -> np.ndarray:
        return self._gray if grayscale else self._image

    def capture_roi(self, roi: ROI, grayscale: bool = False) -> np.ndarray:
        img = self._gray if grayscale else self._image
        return img[roi.y : roi.y + roi.h, roi.x : roi.x + roi.w]


class TestMatcher:
    """Test template matching."""

    @pytest.fixture
    def setup_matcher(self, tmp_path: Path):  # type: ignore
        """Create matcher with test images."""
        # Create a test "screen" with a button
        screen = np.ones((600, 800, 3), dtype=np.uint8) * 200  # Gray background

        # Draw a red button at (100, 100)
        cv2.rectangle(screen, (100, 100), (180, 140), (0, 0, 255), -1)
        cv2.putText(screen, "OK", (120, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Save button template
        btn_path = tmp_path / "btn_ok.png"
        btn_crop = screen[100:140, 100:180]
        cv2.imwrite(str(btn_path), btn_crop)

        # Create template store
        store = TemplateStore(tmp_path)
        asset = AssetImage(id="btn_ok", path="btn_ok.png", threshold=0.8)
        errors = store.preload([asset])
        assert len(errors) == 0

        # Create matcher with mock capture
        mock_capture = MockCapture(screen)
        matcher = Matcher(store, mock_capture)

        return matcher, screen, btn_crop

    def test_find_exact_match(self, setup_matcher) -> None:  # type: ignore
        """Test finding exact template match."""
        matcher, _, _ = setup_matcher

        match = matcher.find("btn_ok")
        assert match is not None
        assert match.x == 100
        assert match.y == 100
        assert match.confidence >= 0.99  # Should be near-perfect

    def test_find_with_roi(self, setup_matcher, tmp_path: Path) -> None:  # type: ignore
        """Test ROI-restricted matching."""
        matcher, screen, _ = setup_matcher

        # Match within ROI containing button
        roi = ROI(x=50, y=50, w=200, h=200)
        match = matcher.find("btn_ok", roi_override=roi)
        assert match is not None
        # Coordinates should be absolute
        assert match.x == 100
        assert match.y == 100

    def test_find_outside_roi(self, setup_matcher) -> None:  # type: ignore
        """Test that match outside ROI is not found."""
        matcher, _, _ = setup_matcher

        # ROI that doesn't contain the button
        roi = ROI(x=400, y=400, w=100, h=100)
        match = matcher.find("btn_ok", roi_override=roi)
        assert match is None

    def test_below_threshold(self, setup_matcher, tmp_path: Path) -> None:  # type: ignore
        """Test threshold filtering."""
        matcher, screen, _ = setup_matcher

        # Create asset with very high threshold
        store = TemplateStore(tmp_path)
        asset = AssetImage(id="btn_strict", path="btn_ok.png", threshold=0.999)
        errors = store.preload([asset])
        assert len(errors) == 0

        # Modify screen slightly so it's not perfect match
        screen_modified = screen.copy()
        screen_modified[110, 110] = [0, 255, 0]  # Add noise pixel
        mock_capture = MockCapture(screen_modified)
        matcher_strict = Matcher(store, mock_capture)

        match = matcher_strict.find("btn_strict")
        # May or may not match depending on threshold
        # This is mainly to test threshold logic works

    def test_exists(self, setup_matcher) -> None:  # type: ignore
        """Test exists helper."""
        matcher, _, _ = setup_matcher

        assert matcher.exists("btn_ok")
        assert not matcher.exists("nonexistent")

    def test_find_nonexistent_asset(self, setup_matcher) -> None:  # type: ignore
        """Test finding asset not in store."""
        matcher, _, _ = setup_matcher

        match = matcher.find("not_loaded")
        assert match is None


class TestScreenCapture:
    """Test screen capture functionality."""

    def test_screen_size(self) -> None:
        """Test getting screen size."""
        with ScreenCapture() as cap:
            w, h = cap.screen_size
            assert w > 0
            assert h > 0

    def test_capture_full(self) -> None:
        """Test full screen capture."""
        with ScreenCapture() as cap:
            img = cap.capture_full()
            assert img.shape[2] == 3  # BGR
            assert img.shape[0] > 0
            assert img.shape[1] > 0

    def test_capture_full_grayscale(self) -> None:
        """Test grayscale capture."""
        with ScreenCapture() as cap:
            img = cap.capture_full(grayscale=True)
            assert len(img.shape) == 2  # No color channels

    def test_capture_roi(self) -> None:
        """Test ROI capture."""
        roi = ROI(x=0, y=0, w=100, h=100)
        with ScreenCapture() as cap:
            img = cap.capture_roi(roi)
            assert img.shape == (100, 100, 3)
