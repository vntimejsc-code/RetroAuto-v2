"""
RetroAuto v2 - Performance Utilities

Utilities for UI performance optimization.
Phase 2.2 Performance Optimization.
"""

from PySide6.QtCore import QTimer

from infra import get_logger

logger = get_logger("PerfUtils")


class DebouncedCallback:
    """
    Debounced callback to prevent rapid-fire UI updates.

    Usage:
        debounced = DebouncedCallback(self._update_ui, delay_ms=50)
        # Call debounced.trigger() instead of _update_ui()
        # Multiple rapid triggers will coalesce into one call
    """

    def __init__(self, callback, delay_ms: int = 50) -> None:
        self._callback = callback
        self._delay_ms = delay_ms
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._execute)
        self._pending_args = None
        self._pending_kwargs = None

    def trigger(self, *args, **kwargs) -> None:
        """Trigger callback (debounced)."""
        self._pending_args = args
        self._pending_kwargs = kwargs
        if not self._timer.isActive():
            self._timer.start(self._delay_ms)

    def _execute(self) -> None:
        """Execute the callback with pending arguments."""
        try:
            self._callback(*self._pending_args, **self._pending_kwargs)
        except Exception as e:
            logger.warning("Debounced callback error: %s", e)

    def cancel(self) -> None:
        """Cancel pending callback."""
        self._timer.stop()
        self._pending_args = None
        self._pending_kwargs = None

    @property
    def is_pending(self) -> bool:
        """Check if callback is pending."""
        return self._timer.isActive()


class ThrottledCallback:
    """
    Throttled callback to limit update frequency.

    Unlike debounce, throttle executes at most once per interval.
    """

    def __init__(self, callback, interval_ms: int = 100) -> None:
        self._callback = callback
        self._interval_ms = interval_ms
        self._last_call = 0
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._execute)
        self._pending_args = None
        self._pending_kwargs = None

    def trigger(self, *args, **kwargs) -> None:
        """Trigger callback (throttled)."""
        import time

        now = time.time() * 1000
        elapsed = now - self._last_call

        if elapsed >= self._interval_ms:
            # Execute immediately
            self._last_call = now
            try:
                self._callback(*args, **kwargs)
            except Exception as e:
                logger.warning("Throttled callback error: %s", e)
        else:
            # Schedule for later
            self._pending_args = args
            self._pending_kwargs = kwargs
            if not self._timer.isActive():
                remaining = self._interval_ms - elapsed
                self._timer.start(int(remaining))

    def _execute(self) -> None:
        """Execute pending callback."""
        import time

        self._last_call = time.time() * 1000
        if self._pending_args is not None:
            try:
                self._callback(*self._pending_args, **self._pending_kwargs)
            except Exception as e:
                logger.warning("Throttled callback error: %s", e)
            self._pending_args = None
            self._pending_kwargs = None
