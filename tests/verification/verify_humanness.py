"""
Deep Verification for Human Mouse Movement
"""

import math
import statistics
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure core can be imported
sys.path.append("c:/Auto/Newauto")

from core.models import ROI, ClickRandom
from core.vision.input import MouseController


class TestHumanMouseMovement(unittest.TestCase):
    def setUp(self):
        # Force HAS_PYAUTOGUI to True so logic runs
        import core.vision.input

        core.vision.input.HAS_PYAUTOGUI = True
        # Ensure pyautogui exists in module so patch works (if it failed import)
        if not hasattr(core.vision.input, "pyautogui"):
            core.vision.input.pyautogui = MagicMock()

        self.mouse = MouseController()
        # Mock pyautogui.position to return (0,0) initially
        self.mock_pos = MagicMock(return_value=MagicMock(x=0, y=0))

    @patch("core.vision.input.pyautogui")
    @patch("core.vision.input.time")
    def test_bezier_curve_shape(self, mock_time, mock_pyautogui):
        """Verify the path is curved, not straight."""
        # Fix position mock
        mock_point = MagicMock()
        mock_point.x = 0
        mock_point.y = 0
        mock_pyautogui.position.return_value = mock_point

        self.mouse._position = MagicMock(x=0, y=0)
        recorded_points = []

        # Mock time to increment to avoid infinite loops or stuck logic
        # Increase range to support long loops
        mock_time.time.side_effect = [i * 0.001 for i in range(50000)]

        def side_effect_moveTo(x, y, duration=0.0, _pause=False):
            recorded_points.append((x, y))

        mock_pyautogui.moveTo.side_effect = side_effect_moveTo

        # Move from 0,0 to 1000, 1000 using absolute move
        self.mouse.moveto(1000, 1000)

        # Filter out start and potential jitter points
        if len(recorded_points) < 5:
            self.fail(f"Path too short: {len(recorded_points)}")

        path = recorded_points[:-2]

        # Calculate linearity error
        max_deviation = 0
        for x, y in path:
            # Distance from point to line: |Ax + By + C| / sqrt(A^2 + B^2)
            # Line: -x + y = 0 -> | -x + y | / sqrt(2)
            deviation = abs(-x + y) / math.sqrt(2)
            max_deviation = max(max_deviation, deviation)

        print(f"Max deviation from straight line: {max_deviation:.2f} px")
        self.assertGreater(max_deviation, 1.0, "Movement is too robotic (straight line)")

    @patch("core.vision.input.pyautogui")
    @patch("core.vision.input.time")
    def test_speed_variance(self, mock_time, mock_pyautogui):
        """Verify speed (distance per step) is not constant."""
        # Fix position mock
        mock_point = MagicMock()
        mock_point.x = 0
        mock_point.y = 0
        mock_pyautogui.position.return_value = mock_point

        self.mouse._position = MagicMock(x=0, y=0)
        recorded_points = []

        mock_time.time.side_effect = [i * 0.001 for i in range(10000)]

        def side_effect_moveTo(x, y, duration=0.0, _pause=False):
            recorded_points.append((x, y))

        mock_pyautogui.moveTo.side_effect = side_effect_moveTo

        self.mouse.moveto(1000, 1000)

        if len(recorded_points) < 10:
            self.fail("Path too short")

        # Calculate segment lengths
        lengths = []
        prev = (0, 0)
        for p in recorded_points[:-2]:  # Ignore last jitter
            dist = math.sqrt((p[0] - prev[0]) ** 2 + (p[1] - prev[1]) ** 2)
            lengths.append(dist)
            prev = p

        # If speed varies, segments should vary
        stdev = statistics.stdev(lengths)
        print(f"Segment length stdev: {stdev:.2f}")
        # With Bezier easing, we expect significant variance
        self.assertGreater(stdev, 1.0, "Speed appears constant (equidistant points)")

    @patch("core.vision.input.pyautogui")
    @patch("core.vision.input.time")
    def test_random_distribution(self, mock_time, mock_pyautogui):
        """Verify random clicks check ROI distribution."""
        from core.engine.runner import Runner

        # Mock dependencies
        ctx = MagicMock()
        ctx.mouse = self.mouse
        runner = Runner(ctx)

        # Run 1000 clicks
        roi = ROI(x=0, y=0, w=100, h=100)
        action = ClickRandom(roi=roi, clicks=1, interval_ms=0)

        clicks = []

        def side_effect_click(x, y, *args, **kwargs):
            clicks.append((x, y))

        self.mouse.click = MagicMock(side_effect=side_effect_click)

        for _ in range(1000):
            runner._exec_click_random(action)

        xs = [c[0] for c in clicks]
        ys = [c[1] for c in clicks]

        mean_x = statistics.mean(xs)
        mean_y = statistics.mean(ys)
        stdev_x = statistics.stdev(xs)

        print(f"Distribution: Mean=({mean_x:.1f}, {mean_y:.1f}), StdDev={stdev_x:.1f}")

        # Target mean is 50, 50
        self.assertTrue(45 < mean_x < 55, "Distribution not centered X")
        self.assertTrue(45 < mean_y < 55, "Distribution not centered Y")

        # Target sigma was width/6 = 100/6 = 16.6
        self.assertTrue(14 < stdev_x < 19, "Distribution spread incorrect")

        # Check clamping
        min_x, max_x = min(xs), max(xs)
        self.assertGreaterEqual(min_x, 0)
        self.assertLessEqual(max_x, 100)


if __name__ == "__main__":
    unittest.main()
