"""
RetroAuto v2 - Analytics & Metrics

Metrics collection, logging, and monitoring for RetroScript.
Part of RetroScript Phase 17 - Analytics & Monitoring.
"""

from __future__ import annotations

import json
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from threading import Lock
from typing import Any, Callable


# ─────────────────────────────────────────────────────────────
# Metric Types
# ─────────────────────────────────────────────────────────────

class MetricType(Enum):
    """Types of metrics."""
    COUNTER = auto()
    GAUGE = auto()
    TIMER = auto()
    HISTOGRAM = auto()


@dataclass
class Counter:
    """A counter metric (always increases)."""
    name: str
    value: int = 0
    labels: dict[str, str] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def inc(self, amount: int = 1) -> None:
        """Increment counter."""
        with self._lock:
            self.value += amount

    def get(self) -> int:
        """Get current value."""
        return self.value

    def reset(self) -> None:
        """Reset counter."""
        with self._lock:
            self.value = 0


@dataclass
class Gauge:
    """A gauge metric (can go up or down)."""
    name: str
    value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def set(self, value: float) -> None:
        """Set gauge value."""
        with self._lock:
            self.value = value

    def inc(self, amount: float = 1.0) -> None:
        """Increment gauge."""
        with self._lock:
            self.value += amount

    def dec(self, amount: float = 1.0) -> None:
        """Decrement gauge."""
        with self._lock:
            self.value -= amount

    def get(self) -> float:
        """Get current value."""
        return self.value


@dataclass
class Timer:
    """A timer metric for measuring durations."""
    name: str
    values: list[float] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock, repr=False)
    _start_time: float | None = field(default=None, repr=False)

    def start(self) -> None:
        """Start the timer."""
        self._start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop timer and record duration."""
        if self._start_time is None:
            return 0.0

        duration = time.perf_counter() - self._start_time
        with self._lock:
            self.values.append(duration)
        self._start_time = None
        return duration

    def record(self, duration: float) -> None:
        """Record a duration directly."""
        with self._lock:
            self.values.append(duration)

    def get_stats(self) -> dict[str, float]:
        """Get timer statistics."""
        if not self.values:
            return {"count": 0, "mean": 0, "min": 0, "max": 0, "p50": 0, "p95": 0}

        sorted_values = sorted(self.values)
        return {
            "count": len(self.values),
            "mean": statistics.mean(self.values),
            "min": min(self.values),
            "max": max(self.values),
            "p50": sorted_values[len(sorted_values) // 2],
            "p95": sorted_values[int(len(sorted_values) * 0.95)] if len(sorted_values) >= 20 else sorted_values[-1],
        }


class TimerContext:
    """Context manager for timing."""

    def __init__(self, timer: Timer) -> None:
        self._timer = timer

    def __enter__(self) -> "TimerContext":
        self._timer.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self._timer.stop()


# ─────────────────────────────────────────────────────────────
# Metrics Registry
# ─────────────────────────────────────────────────────────────

class MetricsRegistry:
    """Registry for all metrics.

    Usage:
        metrics = MetricsRegistry()
        
        # Counter
        metrics.counter("requests_total").inc()
        
        # Gauge
        metrics.gauge("active_scripts").set(5)
        
        # Timer
        with metrics.timer("request_duration").time():
            do_something()
    """

    def __init__(self) -> None:
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._timers: dict[str, Timer] = {}
        self._lock = Lock()

    def counter(self, name: str, **labels: str) -> Counter:
        """Get or create a counter."""
        key = self._make_key(name, labels)
        if key not in self._counters:
            with self._lock:
                if key not in self._counters:
                    self._counters[key] = Counter(name=name, labels=labels)
        return self._counters[key]

    def gauge(self, name: str, **labels: str) -> Gauge:
        """Get or create a gauge."""
        key = self._make_key(name, labels)
        if key not in self._gauges:
            with self._lock:
                if key not in self._gauges:
                    self._gauges[key] = Gauge(name=name, labels=labels)
        return self._gauges[key]

    def timer(self, name: str, **labels: str) -> Timer:
        """Get or create a timer."""
        key = self._make_key(name, labels)
        if key not in self._timers:
            with self._lock:
                if key not in self._timers:
                    self._timers[key] = Timer(name=name, labels=labels)
        return self._timers[key]

    def time(self, name: str, **labels: str) -> TimerContext:
        """Context manager for timing."""
        return TimerContext(self.timer(name, **labels))

    def _make_key(self, name: str, labels: dict[str, str]) -> str:
        """Create a unique key for a metric."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_all(self) -> dict[str, Any]:
        """Get all metrics as dictionary."""
        result: dict[str, Any] = {}

        for key, counter in self._counters.items():
            result[key] = {"type": "counter", "value": counter.get()}

        for key, gauge in self._gauges.items():
            result[key] = {"type": "gauge", "value": gauge.get()}

        for key, timer in self._timers.items():
            result[key] = {"type": "timer", **timer.get_stats()}

        return result

    def reset_all(self) -> None:
        """Reset all metrics."""
        for counter in self._counters.values():
            counter.reset()
        for gauge in self._gauges.values():
            gauge.set(0.0)
        for timer in self._timers.values():
            timer.values.clear()


# ─────────────────────────────────────────────────────────────
# Script Metrics
# ─────────────────────────────────────────────────────────────

class ScriptMetrics:
    """Pre-defined metrics for script execution.

    Usage:
        sm = ScriptMetrics()
        sm.script_started("my_script")
        # ... execute ...
        sm.script_completed("my_script", success=True, duration=1.5)
    """

    def __init__(self, registry: MetricsRegistry | None = None) -> None:
        self.registry = registry or MetricsRegistry()

        # Pre-defined counters
        self._scripts_started = self.registry.counter("scripts_started_total")
        self._scripts_completed = self.registry.counter("scripts_completed_total")
        self._scripts_failed = self.registry.counter("scripts_failed_total")
        self._actions_executed = self.registry.counter("actions_executed_total")
        self._finds_total = self.registry.counter("finds_total")
        self._finds_success = self.registry.counter("finds_success_total")
        self._clicks_total = self.registry.counter("clicks_total")

        # Gauges
        self._active_scripts = self.registry.gauge("active_scripts")

        # Timers
        self._script_duration = self.registry.timer("script_duration_seconds")
        self._action_duration = self.registry.timer("action_duration_seconds")
        self._find_duration = self.registry.timer("find_duration_seconds")

    def script_started(self, name: str) -> None:
        """Record script start."""
        self._scripts_started.inc()
        self._active_scripts.inc()

    def script_completed(self, name: str, success: bool, duration: float) -> None:
        """Record script completion."""
        self._scripts_completed.inc()
        self._active_scripts.dec()
        self._script_duration.record(duration)

        if not success:
            self._scripts_failed.inc()

    def action_executed(self, action: str, duration: float) -> None:
        """Record action execution."""
        self._actions_executed.inc()
        self._action_duration.record(duration)

    def find_executed(self, success: bool, duration: float) -> None:
        """Record find operation."""
        self._finds_total.inc()
        self._find_duration.record(duration)
        if success:
            self._finds_success.inc()

    def click_executed(self) -> None:
        """Record click action."""
        self._clicks_total.inc()

    def get_success_rate(self) -> float:
        """Get overall script success rate."""
        total = self._scripts_completed.get()
        if total == 0:
            return 1.0
        failed = self._scripts_failed.get()
        return (total - failed) / total

    def get_find_success_rate(self) -> float:
        """Get find success rate."""
        total = self._finds_total.get()
        if total == 0:
            return 1.0
        return self._finds_success.get() / total

    def get_summary(self) -> dict[str, Any]:
        """Get metrics summary."""
        return {
            "scripts": {
                "started": self._scripts_started.get(),
                "completed": self._scripts_completed.get(),
                "failed": self._scripts_failed.get(),
                "active": int(self._active_scripts.get()),
                "success_rate": self.get_success_rate(),
            },
            "actions": {
                "total": self._actions_executed.get(),
                "clicks": self._clicks_total.get(),
            },
            "finds": {
                "total": self._finds_total.get(),
                "success": self._finds_success.get(),
                "success_rate": self.get_find_success_rate(),
            },
            "timing": {
                "script": self._script_duration.get_stats(),
                "action": self._action_duration.get_stats(),
                "find": self._find_duration.get_stats(),
            },
        }


# ─────────────────────────────────────────────────────────────
# Structured Logger
# ─────────────────────────────────────────────────────────────

class LogLevel(Enum):
    """Log levels."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass
class LogEntry:
    """A structured log entry."""
    timestamp: str
    level: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    script: str = ""

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "data": self.data,
            "source": self.source,
            "script": self.script,
        })


class StructuredLogger:
    """JSON-structured logger for RetroScript.

    Usage:
        logger = StructuredLogger()
        logger.info("Script started", script="my_script")
        logger.error("Failed to find image", target="button.png")
    """

    def __init__(
        self,
        name: str = "retroscript",
        level: LogLevel = LogLevel.INFO,
        log_file: str | Path | None = None,
    ) -> None:
        self.name = name
        self.level = level
        self.log_file = Path(log_file) if log_file else None
        self._entries: list[LogEntry] = []
        self._max_entries = 1000
        self._lock = Lock()

        # Callbacks
        self.on_log: Callable[[LogEntry], None] | None = None

    def _log(self, level: LogLevel, message: str, **data: Any) -> LogEntry:
        """Internal log method."""
        if level.value < self.level.value:
            return LogEntry("", "", "")

        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.name,
            message=message,
            data=data,
            source=self.name,
        )

        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self._max_entries:
                self._entries.pop(0)

        # Write to file
        if self.log_file:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry.to_json() + "\n")

        # Callback
        if self.on_log:
            self.on_log(entry)

        return entry

    def debug(self, message: str, **data: Any) -> LogEntry:
        """Log debug message."""
        return self._log(LogLevel.DEBUG, message, **data)

    def info(self, message: str, **data: Any) -> LogEntry:
        """Log info message."""
        return self._log(LogLevel.INFO, message, **data)

    def warning(self, message: str, **data: Any) -> LogEntry:
        """Log warning message."""
        return self._log(LogLevel.WARNING, message, **data)

    def error(self, message: str, **data: Any) -> LogEntry:
        """Log error message."""
        return self._log(LogLevel.ERROR, message, **data)

    def critical(self, message: str, **data: Any) -> LogEntry:
        """Log critical message."""
        return self._log(LogLevel.CRITICAL, message, **data)

    def get_entries(
        self,
        level: LogLevel | None = None,
        limit: int = 100,
    ) -> list[LogEntry]:
        """Get log entries."""
        entries = self._entries[-limit:]
        if level:
            entries = [e for e in entries if e.level == level.name]
        return entries

    def clear(self) -> None:
        """Clear log entries."""
        with self._lock:
            self._entries.clear()


# ─────────────────────────────────────────────────────────────
# Dashboard Stats
# ─────────────────────────────────────────────────────────────

class DashboardStats:
    """Aggregated statistics for dashboard display.

    Usage:
        stats = DashboardStats(metrics, logger)
        summary = stats.get_summary()
    """

    def __init__(
        self,
        metrics: ScriptMetrics | None = None,
        logger: StructuredLogger | None = None,
    ) -> None:
        self.metrics = metrics or ScriptMetrics()
        self.logger = logger or StructuredLogger()
        self._start_time = time.time()

    def get_summary(self) -> dict[str, Any]:
        """Get complete dashboard summary."""
        return {
            "uptime": time.time() - self._start_time,
            "metrics": self.metrics.get_summary(),
            "recent_logs": [
                {"level": e.level, "message": e.message, "time": e.timestamp}
                for e in self.logger.get_entries(limit=10)
            ],
            "errors": [
                {"message": e.message, "data": e.data, "time": e.timestamp}
                for e in self.logger.get_entries(level=LogLevel.ERROR, limit=5)
            ],
        }

    def get_health(self) -> dict[str, Any]:
        """Get health status."""
        success_rate = self.metrics.get_success_rate()
        return {
            "status": "healthy" if success_rate >= 0.9 else "degraded" if success_rate >= 0.7 else "unhealthy",
            "success_rate": success_rate,
            "uptime": time.time() - self._start_time,
        }


# Global instances
_metrics: MetricsRegistry | None = None
_script_metrics: ScriptMetrics | None = None
_logger: StructuredLogger | None = None


def get_metrics() -> MetricsRegistry:
    """Get the default metrics registry."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsRegistry()
    return _metrics


def get_script_metrics() -> ScriptMetrics:
    """Get the default script metrics."""
    global _script_metrics
    if _script_metrics is None:
        _script_metrics = ScriptMetrics(get_metrics())
    return _script_metrics


def get_logger() -> StructuredLogger:
    """Get the default structured logger."""
    global _logger
    if _logger is None:
        _logger = StructuredLogger()
    return _logger
