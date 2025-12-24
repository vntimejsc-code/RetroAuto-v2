"""
RetroAuto v2 - Image Recognition

Template matching and image detection for automation.
Part of RetroScript Phase 10 - Image Recognition.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any

# Try to import optional dependencies
try:
    import cv2
    import numpy as np

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    cv2 = None
    np = None

try:
    import mss

    HAS_MSS = True
except ImportError:
    HAS_MSS = False
    mss = None


class MatchMethod(Enum):
    """Template matching methods."""

    CCOEFF = auto()  # cv2.TM_CCOEFF_NORMED
    CCORR = auto()  # cv2.TM_CCORR_NORMED
    SQDIFF = auto()  # cv2.TM_SQDIFF_NORMED


class ResultType(Enum):
    """Types of match results."""

    FOUND = "Found"
    NOT_FOUND = "NotFound"
    TIMEOUT = "Timeout"
    ERROR = "Error"


@dataclass
class MatchResult:
    """Result of an image match operation."""

    result_type: ResultType
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    score: float = 0.0
    scale: float = 1.0
    error_message: str | None = None

    @property
    def found(self) -> bool:
        """Check if match was found."""
        return self.result_type == ResultType.FOUND

    @property
    def center(self) -> tuple[int, int]:
        """Get center point of match."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for script access."""
        return {
            "type": self.result_type.value,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "score": self.score,
            "scale": self.scale,
            "found": self.found,
            "center_x": self.center[0],
            "center_y": self.center[1],
        }

    @classmethod
    def found_at(
        cls,
        x: int,
        y: int,
        width: int = 0,
        height: int = 0,
        score: float = 1.0,
        scale: float = 1.0,
    ) -> MatchResult:
        """Create a Found result."""
        return cls(
            result_type=ResultType.FOUND,
            x=x,
            y=y,
            width=width,
            height=height,
            score=score,
            scale=scale,
        )

    @classmethod
    def not_found(cls) -> MatchResult:
        """Create a NotFound result."""
        return cls(result_type=ResultType.NOT_FOUND)

    @classmethod
    def timeout(cls) -> MatchResult:
        """Create a Timeout result."""
        return cls(result_type=ResultType.TIMEOUT)

    @classmethod
    def error(cls, message: str) -> MatchResult:
        """Create an Error result."""
        return cls(result_type=ResultType.ERROR, error_message=message)


@dataclass
class ROI:
    """Region of Interest for searching."""

    x: int
    y: int
    width: int
    height: int

    def contains(self, x: int, y: int) -> bool:
        """Check if point is in ROI."""
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def to_tuple(self) -> tuple[int, int, int, int]:
        """Convert to tuple (x, y, w, h)."""
        return (self.x, self.y, self.width, self.height)


class ImageCache:
    """LRU cache for loaded images with TTL expiry for 24/7 operation."""

    def __init__(self, max_size: int = 50, ttl_seconds: int = 300) -> None:
        # path -> (image, mtime, last_access_time)
        self._cache: dict[str, tuple[Any, float, float]] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds  # Expire entries not accessed for this long

        # Start background cleanup thread
        self._cleanup_started = False

    def _start_cleanup_thread(self) -> None:
        """Start background cleanup thread (lazy init)."""
        if self._cleanup_started:
            return
        self._cleanup_started = True

        import threading
        def cleanup_loop():
            import time
            while True:
                time.sleep(60)  # Cleanup every 60s
                self._cleanup_expired()

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()

    def _cleanup_expired(self) -> None:
        """Remove entries that haven't been accessed recently."""
        import time
        now = time.time()
        expired_keys = [
            path for path, (_, _, last_access) in self._cache.items()
            if now - last_access > self._ttl
        ]
        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            from infra import get_logger
            get_logger("ImageCache").debug(
                "Cleaned up %d expired cache entries", len(expired_keys)
            )

    def get(self, path: str) -> Any | None:
        """Get image from cache if still valid."""
        if path not in self._cache:
            return None

        image, cached_mtime, _ = self._cache[path]

        # Check if file was modified
        try:
            current_mtime = Path(path).stat().st_mtime
            if current_mtime > cached_mtime:
                # File changed, invalidate
                del self._cache[path]
                return None
        except OSError:
            return None

        # Update last access time
        import time
        self._cache[path] = (image, cached_mtime, time.time())

        return image

    def put(self, path: str, image: Any) -> None:
        """Add image to cache."""
        # Start cleanup thread on first put
        self._start_cleanup_thread()

        if len(self._cache) >= self._max_size:
            # Remove least recently accessed
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k][2])
            del self._cache[oldest]

        try:
            mtime = Path(path).stat().st_mtime
        except OSError:
            mtime = 0.0

        import time
        self._cache[path] = (image, mtime, time.time())

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()


class ImageMatcher:
    """Template matching engine for image detection.

    Usage:
        matcher = ImageMatcher()
        result = matcher.find("button.png")
        if result.found:
            print(f"Found at {result.x}, {result.y}")
    """

    def __init__(
        self,
        assets_dir: str | Path = "assets",
        confidence: float = 0.8,
        method: MatchMethod = MatchMethod.CCOEFF,
    ) -> None:
        self.assets_dir = Path(assets_dir)
        self.confidence = confidence
        self.method = method
        self._cache = ImageCache()
        self._screen_capture: Any = None

        if not HAS_CV2:
            print("[WARN] OpenCV not installed. Using stub mode.")

    def find(
        self,
        template: str | Path,
        roi: ROI | tuple[int, int, int, int] | None = None,
        confidence: float | None = None,
        grayscale: bool = True,
        adaptive: bool = True,
    ) -> MatchResult:
        """Find template on screen.

        Args:
            template: Path to template image
            roi: Region of interest to search in
            confidence: Override default confidence
            grayscale: Convert to grayscale for matching

        Returns:
            MatchResult with position if found
        """
        if not HAS_CV2:
            return self._stub_find(str(template))

        confidence = confidence or self.confidence

        # Load template
        template_img = self._load_image(template)
        if template_img is None:
            return MatchResult.error(f"Template not found: {template}")

        # Capture screen
        screen = self._capture_screen(roi)
        if screen is None:
            return MatchResult.error("Failed to capture screen")

        if grayscale and len(template_img.shape) == 3:
            template_img = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
        if grayscale and len(screen.shape) == 3:
            screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

        # Perform template matching
        result = self._match(screen, template_img, confidence)

        # Adaptive Fallback
        if not result.found and adaptive and confidence > 0.6:
            # Try reducing confidence in steps
            for fallback_conf in [
                c * 0.05 for c in range(int(confidence * 20) - 1, 11, -1)
            ]:  # e.g., 0.75, 0.70... 0.60
                fallback_result = self._match(screen, template_img, fallback_conf)
                if fallback_result.found:
                    result = fallback_result
                    result.error_message = f"Matched with degraded confidence: {fallback_conf:.2f}"
                    break

        # Adjust coordinates for ROI
        if result.found and roi:
            if isinstance(roi, tuple):
                roi = ROI(*roi)
            result.x += roi.x
            result.y += roi.y

        return result

    def find_all(
        self,
        template: str | Path,
        roi: ROI | tuple[int, int, int, int] | None = None,
        confidence: float | None = None,
        max_results: int = 10,
    ) -> list[MatchResult]:
        """Find all occurrences of template.

        Args:
            template: Path to template image
            roi: Region of interest
            confidence: Minimum confidence
            max_results: Maximum number of results

        Returns:
            List of MatchResults
        """
        if not HAS_CV2:
            return [self._stub_find(str(template))]

        confidence = confidence or self.confidence
        results: list[MatchResult] = []

        template_img = self._load_image(template)
        if template_img is None:
            return [MatchResult.error(f"Template not found: {template}")]

        screen = self._capture_screen(roi)
        if screen is None:
            return [MatchResult.error("Failed to capture screen")]

        # Convert to grayscale
        if len(template_img.shape) == 3:
            template_img = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
        if len(screen.shape) == 3:
            screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

        # Match
        match_result = cv2.matchTemplate(
            screen,
            template_img,
            self._get_cv2_method(),
        )

        h, w = template_img.shape[:2]

        # Find all locations above threshold
        if self.method == MatchMethod.SQDIFF:
            locations = np.where(match_result <= 1 - confidence)
        else:
            locations = np.where(match_result >= confidence)

        for pt in zip(*locations[::-1], strict=False):
            if len(results) >= max_results:
                break

            x, y = int(pt[0]), int(pt[1])
            score = float(match_result[y, x])

            if self.method == MatchMethod.SQDIFF:
                score = 1 - score

            # Adjust for ROI
            if roi:
                if isinstance(roi, tuple):
                    roi = ROI(*roi)
                x += roi.x
                y += roi.y

            results.append(MatchResult.found_at(x, y, w, h, score))

        if not results:
            results.append(MatchResult.not_found())

        return results

    def find_multiscale(
        self,
        template: str | Path,
        scales: list[float] | None = None,
        roi: ROI | None = None,
        confidence: float | None = None,
    ) -> MatchResult:
        """Find template at multiple scales.

        Args:
            template: Path to template
            scales: List of scales to try (default: 0.5 to 1.5)
            roi: Region of interest
            confidence: Minimum confidence

        Returns:
            Best MatchResult across scales
        """
        if not HAS_CV2:
            return self._stub_find(str(template))

        scales = scales or [0.5, 0.75, 1.0, 1.25, 1.5]
        confidence = confidence or self.confidence

        template_img = self._load_image(template)
        if template_img is None:
            return MatchResult.error(f"Template not found: {template}")

        screen = self._capture_screen(roi)
        if screen is None:
            return MatchResult.error("Failed to capture screen")

        best_result = MatchResult.not_found()

        for scale in scales:
            # Resize template
            scaled = cv2.resize(
                template_img,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_AREA,
            )

            # Skip if scaled template is larger than screen
            if scaled.shape[0] > screen.shape[0] or scaled.shape[1] > screen.shape[1]:
                continue

            result = self._match(screen, scaled, confidence)
            result.scale = scale

            if result.found and result.score > best_result.score:
                best_result = result

        # Adjust for ROI
        if best_result.found and roi:
            best_result.x += roi.x
            best_result.y += roi.y

        return best_result

    def wait(
        self,
        template: str | Path,
        timeout: float = 10.0,
        interval: float = 0.5,
        **kwargs: Any,
    ) -> MatchResult:
        """Wait for template to appear.

        Args:
            template: Path to template
            timeout: Maximum wait time in seconds
            interval: Check interval in seconds
            **kwargs: Additional args for find()

        Returns:
            MatchResult (FOUND, NOT_FOUND, or TIMEOUT)
        """
        start = time.time()

        while time.time() - start < timeout:
            result = self.find(template, **kwargs)
            if result.found:
                return result
            time.sleep(interval)

        return MatchResult.timeout()

    def _load_image(self, path: str | Path) -> Any | None:
        """Load image from file with caching."""
        path = Path(path)

        # Try relative to assets_dir
        if not path.is_absolute():
            path = self.assets_dir / path

        path_str = str(path)

        # Check cache
        cached = self._cache.get(path_str)
        if cached is not None:
            return cached

        # Load from disk
        if not path.exists():
            return None

        img = cv2.imread(path_str)
        if img is not None:
            self._cache.put(path_str, img)

        return img

    def _capture_screen(self, roi: ROI | tuple | None = None) -> Any | None:
        """Capture screen or region."""
        if not HAS_MSS:
            # Fallback: try PIL
            try:
                from PIL import ImageGrab

                screen = ImageGrab.grab()
                screen = np.array(screen)
                screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

                if roi:
                    if isinstance(roi, tuple):
                        roi = ROI(*roi)
                    screen = screen[
                        roi.y : roi.y + roi.height,
                        roi.x : roi.x + roi.width,
                    ]

                return screen
            except (OSError, AttributeError, ValueError):
                # PIL capture failed
                return None

        with mss.mss() as sct:
            if roi:
                if isinstance(roi, tuple):
                    roi = ROI(*roi)
                monitor = {
                    "left": roi.x,
                    "top": roi.y,
                    "width": roi.width,
                    "height": roi.height,
                }
            else:
                monitor = sct.monitors[1]  # Primary monitor

            screenshot = sct.grab(monitor)
            return np.array(screenshot)[:, :, :3]  # Remove alpha

    def _match(
        self,
        screen: Any,
        template: Any,
        confidence: float,
    ) -> MatchResult:
        """Perform template matching."""
        # Ensure same number of channels
        if len(template.shape) != len(screen.shape):
            if len(template.shape) == 3:
                template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            if len(screen.shape) == 3:
                screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(screen, template, self._get_cv2_method())

        if self.method == MatchMethod.SQDIFF:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            score = 1 - min_val
            loc = min_loc
        else:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            score = max_val
            loc = max_loc

        h, w = template.shape[:2]

        if score >= confidence:
            return MatchResult.found_at(loc[0], loc[1], w, h, score)
        else:
            return MatchResult.not_found()

    def _get_cv2_method(self) -> int:
        """Get OpenCV method constant."""
        methods = {
            MatchMethod.CCOEFF: cv2.TM_CCOEFF_NORMED,
            MatchMethod.CCORR: cv2.TM_CCORR_NORMED,
            MatchMethod.SQDIFF: cv2.TM_SQDIFF_NORMED,
        }
        return methods.get(self.method, cv2.TM_CCOEFF_NORMED)

    # ═══════════════════════════════════════════════════════════════
    # Phase 3: Multi-threaded Matching
    # ═══════════════════════════════════════════════════════════════

    def find_any(
        self,
        templates: list[str | Path],
        roi: ROI | tuple[int, int, int, int] | None = None,
        confidence: float | None = None,
        max_workers: int = 4,
    ) -> tuple[MatchResult, str | None]:
        """Find any of multiple templates in parallel.

        Returns as soon as first match is found.
        Uses ThreadPoolExecutor for parallel execution.

        Args:
            templates: List of template paths to search
            roi: Region of interest
            confidence: Minimum confidence
            max_workers: Maximum parallel threads

        Returns:
            Tuple of (MatchResult, matched_template_name) or (NotFound, None)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def search_template(template: str | Path) -> tuple[MatchResult, str]:
            result = self.find(template, roi=roi, confidence=confidence)
            return result, str(template)

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(search_template, t): t for t in templates}

            for future in as_completed(futures):
                try:
                    result, template_name = future.result()
                    if result.found:
                        # Cancel remaining futures
                        for f in futures:
                            f.cancel()
                        return result, template_name
                except (TimeoutError, RuntimeError, OSError):
                    pass  # Thread execution error

        return MatchResult.not_found(), None

    def find_first(
        self,
        templates: list[str | Path],
        roi: ROI | tuple[int, int, int, int] | None = None,
        confidence: float | None = None,
    ) -> tuple[MatchResult, str | None]:
        """Find first matching template (sequential, priority order).

        Searches templates in order and returns on first match.
        Use when template priority matters.

        Args:
            templates: List of template paths in priority order
            roi: Region of interest
            confidence: Minimum confidence

        Returns:
            Tuple of (MatchResult, matched_template_name) or (NotFound, None)
        """
        for template in templates:
            result = self.find(template, roi=roi, confidence=confidence)
            if result.found:
                return result, str(template)
        return MatchResult.not_found(), None

    def find_all_templates(
        self,
        templates: list[str | Path],
        roi: ROI | tuple[int, int, int, int] | None = None,
        confidence: float | None = None,
        max_workers: int = 4,
    ) -> dict[str, MatchResult]:
        """Find all templates in parallel.

        Searches all templates and returns results for each.

        Args:
            templates: List of template paths
            roi: Region of interest
            confidence: Minimum confidence
            max_workers: Maximum parallel threads

        Returns:
            Dict mapping template name to MatchResult
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results: dict[str, MatchResult] = {}

        def search_template(template: str | Path) -> tuple[str, MatchResult]:
            result = self.find(template, roi=roi, confidence=confidence)
            return str(template), result

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(search_template, t) for t in templates]
            for future in as_completed(futures):
                try:
                    template_name, result = future.result()
                    results[template_name] = result
                except Exception as e:
                    pass

        return results

    def _stub_find(self, template: str) -> MatchResult:
        """Stub find for when OpenCV is not available."""
        print(f"[STUB] find({template})")
        return MatchResult.found_at(100, 100, 50, 50, 0.95)


# Global matcher instance
_default_matcher: ImageMatcher | None = None


def get_matcher() -> ImageMatcher:
    """Get the default image matcher."""
    global _default_matcher
    if _default_matcher is None:
        _default_matcher = ImageMatcher()
    return _default_matcher


def find(template: str, **kwargs: Any) -> MatchResult:
    """Convenience function to find image."""
    return get_matcher().find(template, **kwargs)


def wait(template: str, timeout: float = 10.0, **kwargs: Any) -> MatchResult:
    """Convenience function to wait for image."""
    return get_matcher().wait(template, timeout, **kwargs)
