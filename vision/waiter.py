"""
RetroAuto v2 - Image Waiter

Wait for image to appear or disappear with polling and timeout.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from core.models import ROI, Match
from infra import get_logger
from vision.matcher import Matcher

logger = get_logger("Waiter")


class WaitResult(Enum):
    """Result of wait operation."""

    SUCCESS = "success"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class WaitOutcome:
    """Outcome of a wait operation."""

    result: WaitResult
    match: Match | None = None
    elapsed_ms: int = 0

    @property
    def found(self) -> bool:
        """Check if wait was successful."""
        return self.result == WaitResult.SUCCESS


class ImageWaiter:
    """
    Wait for image conditions with polling.

    Features:
    - Wait for appear/vanish
    - Configurable poll interval
    - Timeout handling
    - Cancel support
    - Exponential backoff during idle
    """

    def __init__(
        self,
        matcher: Matcher,
        default_poll_ms: int = 100,
        default_timeout_ms: int = 10000,
        backoff_max_ms: int = 500,
    ) -> None:
        self._matcher = matcher
        self._default_poll_ms = default_poll_ms
        self._default_timeout_ms = default_timeout_ms
        self._backoff_max_ms = backoff_max_ms
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel ongoing wait."""
        self._cancelled = True

    def reset(self) -> None:
        """Reset cancel flag."""
        self._cancelled = False

    def wait_appear(
        self,
        asset_id: str,
        timeout_ms: int | None = None,
        poll_ms: int | None = None,
        roi_override: ROI | None = None,
        on_poll: Callable[[int], None] | None = None,
        smart_wait: bool = True,
    ) -> WaitOutcome:
        """
        Wait for image to appear on screen.

        Args:
            asset_id: Asset to wait for
            timeout_ms: Maximum wait time (None = use default)
            poll_ms: Polling interval (None = use default)
            roi_override: Override default ROI
            on_poll: Callback on each poll (elapsed_ms)

        Returns:
            WaitOutcome with result and match if found
        """
        return self._wait(
            asset_id=asset_id,
            appear=True,
            timeout_ms=timeout_ms or self._default_timeout_ms,
            poll_ms=poll_ms or self._default_poll_ms,
            roi_override=roi_override,
            on_poll=on_poll,
            smart_wait=smart_wait,
        )

    def wait_vanish(
        self,
        asset_id: str,
        timeout_ms: int | None = None,
        poll_ms: int | None = None,
        roi_override: ROI | None = None,
        on_poll: Callable[[int], None] | None = None,
        smart_wait: bool = True,
    ) -> WaitOutcome:
        """
        Wait for image to disappear from screen.

        Args:
            asset_id: Asset to wait for disappearance
            timeout_ms: Maximum wait time
            poll_ms: Polling interval
            roi_override: Override default ROI
            on_poll: Callback on each poll

        Returns:
            WaitOutcome (match is None on success since image vanished)
        """
        return self._wait(
            asset_id=asset_id,
            appear=False,
            timeout_ms=timeout_ms or self._default_timeout_ms,
            poll_ms=poll_ms or self._default_poll_ms,
            roi_override=roi_override,
            on_poll=on_poll,
            smart_wait=smart_wait,
        )

    def _wait(
        self,
        asset_id: str,
        appear: bool,
        timeout_ms: int,
        poll_ms: int,
        roi_override: ROI | None,
        on_poll: Callable[[int], None] | None,
        smart_wait: bool,
    ) -> WaitOutcome:
        """Internal wait implementation with exponential backoff."""
        self._cancelled = False
        start_time = time.perf_counter()
        current_poll_ms = poll_ms
        consecutive_misses = 0

        action = "appear" if appear else "vanish"
        logger.info("Waiting for %s to %s (timeout=%dms)", asset_id, action, timeout_ms)

        while True:
            # Check cancellation
            if self._cancelled:
                elapsed = int((time.perf_counter() - start_time) * 1000)
                logger.info("Wait cancelled after %dms", elapsed)
                return WaitOutcome(result=WaitResult.CANCELLED, elapsed_ms=elapsed)

            # Check timeout
            elapsed = int((time.perf_counter() - start_time) * 1000)
            if elapsed >= timeout_ms:
                logger.warning("Wait timeout after %dms", elapsed)
                return WaitOutcome(result=WaitResult.TIMEOUT, elapsed_ms=elapsed)

            # Callback
            if on_poll:
                on_poll(elapsed)

            # Check image
            match = self._matcher.find(asset_id, roi_override, adaptive=smart_wait)

            if appear:
                # Waiting for image to appear
                if match is not None:
                    logger.info(
                        "Found %s after %dms (conf=%.2f)", asset_id, elapsed, match.confidence
                    )
                    return WaitOutcome(result=WaitResult.SUCCESS, match=match, elapsed_ms=elapsed)
                consecutive_misses += 1
            else:
                # Waiting for image to vanish
                if match is None:
                    logger.info("%s vanished after %dms", asset_id, elapsed)
                    return WaitOutcome(result=WaitResult.SUCCESS, elapsed_ms=elapsed)
                consecutive_misses = 0  # Reset - still visible

            # Exponential backoff during idle
            if consecutive_misses > 5:
                current_poll_ms = min(current_poll_ms * 1.5, self._backoff_max_ms)
            else:
                current_poll_ms = poll_ms

            # Sleep
            sleep_ms = min(current_poll_ms, timeout_ms - elapsed)
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)
