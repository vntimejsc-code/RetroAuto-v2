"""
RetroAuto v2 - Script Profiler

Performance timing and bottleneck detection for RetroScript.
Part of RetroScript Phase 8 - Runtime + Distribution.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class TimingEntry:
    """A single timing measurement."""

    name: str
    start_time: float
    end_time: float = 0.0
    children: list["TimingEntry"] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """Get duration in milliseconds."""
        return (self.end_time - self.start_time) * 1000

    @property
    def self_time(self) -> float:
        """Get self-time excluding children."""
        child_time = sum(c.duration for c in self.children)
        return self.duration - child_time


@dataclass
class ProfileStats:
    """Aggregated statistics for a profiled item."""

    name: str
    call_count: int = 0
    total_time: float = 0.0  # ms
    min_time: float = float("inf")
    max_time: float = 0.0
    avg_time: float = 0.0

    def update(self, duration: float) -> None:
        """Update stats with new measurement."""
        self.call_count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.avg_time = self.total_time / self.call_count


class Profiler:
    """Script profiler for performance analysis.

    Usage:
        profiler = Profiler()
        
        with profiler.measure("my_operation"):
            do_something()
        
        # Or manually
        profiler.start("operation")
        do_something()
        profiler.stop("operation")
        
        report = profiler.get_report()
    """

    def __init__(self) -> None:
        self._entries: list[TimingEntry] = []
        self._stack: list[TimingEntry] = []
        self._stats: dict[str, ProfileStats] = defaultdict(lambda: ProfileStats(name=""))
        self._enabled = True
        self._start_time = 0.0

    def enable(self) -> None:
        """Enable profiling."""
        self._enabled = True

    def disable(self) -> None:
        """Disable profiling."""
        self._enabled = False

    def reset(self) -> None:
        """Reset all profiling data."""
        self._entries.clear()
        self._stack.clear()
        self._stats.clear()
        self._start_time = time.perf_counter()

    def start(self, name: str) -> None:
        """Start timing a named section."""
        if not self._enabled:
            return

        entry = TimingEntry(name=name, start_time=time.perf_counter())

        if self._stack:
            self._stack[-1].children.append(entry)
        else:
            self._entries.append(entry)

        self._stack.append(entry)

    def stop(self, name: str | None = None) -> float:
        """Stop timing the current or named section.

        Returns:
            Duration in milliseconds
        """
        if not self._enabled or not self._stack:
            return 0.0

        entry = self._stack.pop()
        entry.end_time = time.perf_counter()

        # Verify name matches if provided
        if name and entry.name != name:
            # Push back and report error
            self._stack.append(entry)
            return 0.0

        # Update stats
        stats = self._stats[entry.name]
        stats.name = entry.name
        stats.update(entry.duration)

        return entry.duration

    def measure(self, name: str) -> "ProfileContext":
        """Context manager for measuring a section.

        Usage:
            with profiler.measure("operation"):
                do_something()
        """
        return ProfileContext(self, name)

    def get_stats(self, name: str) -> ProfileStats | None:
        """Get statistics for a named item."""
        return self._stats.get(name)

    def get_all_stats(self) -> dict[str, ProfileStats]:
        """Get all collected statistics."""
        return dict(self._stats)

    def get_hotspots(self, top_n: int = 10) -> list[ProfileStats]:
        """Get the top N hotspots by total time."""
        sorted_stats = sorted(
            self._stats.values(),
            key=lambda s: s.total_time,
            reverse=True,
        )
        return sorted_stats[:top_n]

    def get_report(self) -> str:
        """Generate a human-readable profile report."""
        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("PROFILE REPORT")
        lines.append("=" * 60)

        if not self._stats:
            lines.append("No profiling data collected.")
            return "\n".join(lines)

        # Summary
        total_time = sum(s.total_time for s in self._stats.values())
        total_calls = sum(s.call_count for s in self._stats.values())
        lines.append(f"Total time: {total_time:.2f}ms")
        lines.append(f"Total calls: {total_calls}")
        lines.append("")

        # Top hotspots
        lines.append("TOP HOTSPOTS:")
        lines.append("-" * 60)
        lines.append(f"{'Name':<30} {'Calls':>8} {'Total':>10} {'Avg':>10}")
        lines.append("-" * 60)

        for stats in self.get_hotspots():
            pct = (stats.total_time / total_time * 100) if total_time else 0
            lines.append(
                f"{stats.name:<30} "
                f"{stats.call_count:>8} "
                f"{stats.total_time:>9.2f}ms "
                f"{stats.avg_time:>9.2f}ms "
                f"({pct:.1f}%)"
            )

        lines.append("=" * 60)
        return "\n".join(lines)

    def get_flame_data(self) -> list[dict[str, Any]]:
        """Get data suitable for flame graph visualization."""
        def entry_to_dict(entry: TimingEntry, depth: int = 0) -> dict[str, Any]:
            return {
                "name": entry.name,
                "duration": entry.duration,
                "self_time": entry.self_time,
                "depth": depth,
                "children": [entry_to_dict(c, depth + 1) for c in entry.children],
            }

        return [entry_to_dict(e) for e in self._entries]


class ProfileContext:
    """Context manager for profiling a code section."""

    def __init__(self, profiler: Profiler, name: str) -> None:
        self._profiler = profiler
        self._name = name

    def __enter__(self) -> "ProfileContext":
        self._profiler.start(self._name)
        return self

    def __exit__(self, *args: Any) -> None:
        self._profiler.stop(self._name)


# ─────────────────────────────────────────────────────────────
# Decorators for function profiling
# ─────────────────────────────────────────────────────────────

_default_profiler = Profiler()


def profile(name: str | None = None) -> Callable:
    """Decorator to profile a function.

    Usage:
        @profile("my_function")
        def my_function():
            ...

        # Or use function name
        @profile()
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        func_name = name or func.__name__

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with _default_profiler.measure(func_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def get_profiler() -> Profiler:
    """Get the default profiler instance."""
    return _default_profiler
