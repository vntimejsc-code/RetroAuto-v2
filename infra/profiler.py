"""
RetroAuto v2 - Performance Profiler

CPU profiling utilities for optimization.
"""

import cProfile
import pstats
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from io import StringIO
from typing import Generator

from infra.logging import get_logger

logger = get_logger("Profiler")


@dataclass
class TimingStats:
    """Statistics for a timed operation."""

    name: str
    count: int = 0
    total_ms: float = 0.0
    min_ms: float = float("inf")
    max_ms: float = 0.0

    @property
    def avg_ms(self) -> float:
        return self.total_ms / self.count if self.count > 0 else 0.0

    def record(self, ms: float) -> None:
        self.count += 1
        self.total_ms += ms
        self.min_ms = min(self.min_ms, ms)
        self.max_ms = max(self.max_ms, ms)

    def __str__(self) -> str:
        return (
            f"{self.name}: count={self.count}, "
            f"avg={self.avg_ms:.2f}ms, "
            f"min={self.min_ms:.2f}ms, "
            f"max={self.max_ms:.2f}ms"
        )


class PerformanceProfiler:
    """
    Simple performance profiler for tracking operation timings.

    Usage:
        profiler = PerformanceProfiler()

        with profiler.track("template_match"):
            # ... do work ...

        profiler.report()
    """

    def __init__(self) -> None:
        self._stats: dict[str, TimingStats] = {}
        self._enabled = True

    def enable(self) -> None:
        """Enable profiling."""
        self._enabled = True

    def disable(self) -> None:
        """Disable profiling."""
        self._enabled = False

    @contextmanager
    def track(self, name: str) -> Generator[None, None, None]:
        """
        Track execution time of a code block.

        Args:
            name: Operation name for grouping
        """
        if not self._enabled:
            yield
            return

        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000

            if name not in self._stats:
                self._stats[name] = TimingStats(name)
            self._stats[name].record(elapsed_ms)

    def get_stats(self, name: str) -> TimingStats | None:
        """Get stats for a specific operation."""
        return self._stats.get(name)

    def reset(self) -> None:
        """Reset all statistics."""
        self._stats.clear()

    def report(self) -> str:
        """Generate text report of all timings."""
        if not self._stats:
            return "No profiling data collected."

        lines = ["Performance Report", "=" * 50]
        for name in sorted(self._stats.keys()):
            lines.append(str(self._stats[name]))
        return "\n".join(lines)

    def log_report(self) -> None:
        """Log the performance report."""
        logger.info("\n%s", self.report())


def run_cprofile(func, *args, **kwargs):  # type: ignore
    """
    Run function with cProfile and return stats.

    Args:
        func: Function to profile
        *args, **kwargs: Arguments to pass to function

    Returns:
        (result, stats_string)
    """
    profiler = cProfile.Profile()
    profiler.enable()

    try:
        result = func(*args, **kwargs)
    finally:
        profiler.disable()

    # Get stats as string
    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")
    stats.print_stats(30)

    return result, stream.getvalue()


# Global profiler instance
_profiler: PerformanceProfiler | None = None


def get_profiler() -> PerformanceProfiler:
    """Get global profiler instance."""
    global _profiler
    if _profiler is None:
        _profiler = PerformanceProfiler()
    return _profiler
