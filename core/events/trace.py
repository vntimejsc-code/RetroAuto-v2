"""
RetroAuto v2 - Execution Trace

Span-based execution tracing for debugging and replay.

Phase: Mid-term improvement
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from infra import get_logger

logger = get_logger("Trace")


@dataclass
class TraceSpan:
    """
    A single execution span (action or block).

    Spans form a tree structure where parent spans contain child spans.
    """

    span_id: str
    parent_id: str | None
    action_type: str
    action_params: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: datetime | None = None
    status: str = "running"  # running, success, failed, skipped
    duration_ms: int = 0
    error_message: str | None = None
    healing: dict[str, Any] | None = None  # Self-healing info
    screenshot_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "action_type": self.action_type,
            "action_params": self.action_params,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "healing": self.healing,
            "screenshot_path": self.screenshot_path,
            "metadata": self.metadata,
        }


@dataclass
class ExecutionTrace:
    """
    Complete trace of a script execution.

    Contains all spans from a single run for debugging and replay.
    """

    trace_id: str
    run_id: str
    script_path: str
    script_name: str
    started_at: datetime
    ended_at: datetime | None = None
    status: str = "running"
    spans: list[TraceSpan] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "script_path": self.script_path,
            "script_name": self.script_name,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "spans": [s.to_dict() for s in self.spans],
            "metadata": self.metadata,
        }


class TraceCollector:
    """
    Collect execution traces during script runs.

    Usage:
        collector = TraceCollector("runs/")
        trace = collector.start_trace("abc123", "script.yaml", "My Script")
        
        with collector.span("ClickImage", {"asset_id": "btn"}):
            # action execution
            pass
        
        collector.end_trace("success")
        collector.save()
    """

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self._output_dir = Path(output_dir) if output_dir else Path.cwd() / "traces"
        self._current_trace: ExecutionTrace | None = None
        self._span_stack: list[TraceSpan] = []
        self._enabled = True

    @property
    def is_tracing(self) -> bool:
        return self._current_trace is not None

    @property
    def current_trace(self) -> ExecutionTrace | None:
        return self._current_trace

    def enable(self) -> None:
        """Enable tracing."""
        self._enabled = True

    def disable(self) -> None:
        """Disable tracing (for performance)."""
        self._enabled = False

    def start_trace(
        self,
        run_id: str,
        script_path: str,
        script_name: str,
        metadata: dict | None = None,
    ) -> ExecutionTrace:
        """
        Start a new execution trace.

        Args:
            run_id: Associated run ID from history
            script_path: Path to script
            script_name: Script name
            metadata: Optional metadata

        Returns:
            New ExecutionTrace
        """
        trace_id = str(uuid.uuid4())[:8]

        self._current_trace = ExecutionTrace(
            trace_id=trace_id,
            run_id=run_id,
            script_path=script_path,
            script_name=script_name,
            started_at=datetime.now(),
            metadata=metadata or {},
        )

        logger.info("Trace started: %s", trace_id)
        return self._current_trace

    def end_trace(self, status: str) -> ExecutionTrace | None:
        """
        End current trace.

        Args:
            status: Final status (success, failed, stopped)

        Returns:
            Completed trace
        """
        if not self._current_trace:
            return None

        self._current_trace.ended_at = datetime.now()
        self._current_trace.status = status

        logger.info("Trace ended: %s (status=%s)", self._current_trace.trace_id, status)
        return self._current_trace

    def start_span(
        self,
        action_type: str,
        params: dict | None = None,
        metadata: dict | None = None,
    ) -> TraceSpan | None:
        """
        Start a new span.

        Args:
            action_type: Type of action
            params: Action parameters
            metadata: Optional metadata

        Returns:
            New span
        """
        if not self._enabled or not self._current_trace:
            return None

        span_id = str(uuid.uuid4())[:8]
        parent_id = self._span_stack[-1].span_id if self._span_stack else None

        span = TraceSpan(
            span_id=span_id,
            parent_id=parent_id,
            action_type=action_type,
            action_params=params or {},
            metadata=metadata or {},
        )

        self._span_stack.append(span)
        self._current_trace.spans.append(span)

        logger.debug("Span started: %s (%s)", span_id, action_type)
        return span

    def end_span(
        self,
        status: str = "success",
        error: str | None = None,
        healing: dict | None = None,
        screenshot: str | None = None,
    ) -> TraceSpan | None:
        """
        End current span.

        Args:
            status: Span status
            error: Optional error message
            healing: Self-healing info
            screenshot: Screenshot path

        Returns:
            Completed span
        """
        if not self._span_stack:
            return None

        span = self._span_stack.pop()
        span.ended_at = datetime.now()
        span.status = status
        span.duration_ms = int((span.ended_at - span.started_at).total_seconds() * 1000)
        span.error_message = error
        span.healing = healing
        span.screenshot_path = screenshot

        logger.debug("Span ended: %s (status=%s, %dms)", span.span_id, status, span.duration_ms)
        return span

    def span(self, action_type: str, params: dict | None = None):
        """
        Context manager for spans.

        Usage:
            with collector.span("ClickImage", {"asset_id": "btn"}):
                # action code
                pass
        """
        return SpanContext(self, action_type, params)

    def save(self, filepath: Path | None = None) -> Path | None:
        """
        Save trace to file.

        Args:
            filepath: Optional output path

        Returns:
            Path to saved file
        """
        if not self._current_trace:
            return None

        # Ensure output directory exists
        self._output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        if filepath is None:
            filename = f"trace_{self._current_trace.trace_id}.json"
            filepath = self._output_dir / filename

        # Save as JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._current_trace.to_dict(), f, indent=2)

        logger.info("Trace saved: %s", filepath)
        return filepath

    def load(self, filepath: Path) -> ExecutionTrace | None:
        """Load trace from file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            trace = ExecutionTrace(
                trace_id=data["trace_id"],
                run_id=data["run_id"],
                script_path=data["script_path"],
                script_name=data["script_name"],
                started_at=datetime.fromisoformat(data["started_at"]),
                ended_at=datetime.fromisoformat(data["ended_at"]) if data["ended_at"] else None,
                status=data["status"],
                metadata=data.get("metadata", {}),
            )

            # Load spans
            for span_data in data.get("spans", []):
                span = TraceSpan(
                    span_id=span_data["span_id"],
                    parent_id=span_data["parent_id"],
                    action_type=span_data["action_type"],
                    action_params=span_data.get("action_params", {}),
                    started_at=datetime.fromisoformat(span_data["started_at"]),
                    ended_at=datetime.fromisoformat(span_data["ended_at"]) if span_data["ended_at"] else None,
                    status=span_data["status"],
                    duration_ms=span_data.get("duration_ms", 0),
                    error_message=span_data.get("error_message"),
                    healing=span_data.get("healing"),
                    screenshot_path=span_data.get("screenshot_path"),
                    metadata=span_data.get("metadata", {}),
                )
                trace.spans.append(span)

            return trace

        except Exception as e:
            logger.error("Failed to load trace: %s", e)
            return None


class SpanContext:
    """Context manager for spans."""

    def __init__(self, collector: TraceCollector, action_type: str, params: dict | None):
        self._collector = collector
        self._action_type = action_type
        self._params = params
        self._span: TraceSpan | None = None

    def __enter__(self) -> TraceSpan | None:
        self._span = self._collector.start_span(self._action_type, self._params)
        return self._span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self._collector.end_span(status="failed", error=str(exc_val))
        else:
            self._collector.end_span(status="success")
        return False  # Don't suppress exceptions


# Global collector instance
_default_collector: TraceCollector | None = None


def get_trace_collector(output_dir: Path | str | None = None) -> TraceCollector:
    """Get the default trace collector."""
    global _default_collector
    if _default_collector is None:
        if output_dir is None:
            output_dir = Path.home() / ".retroauto" / "traces"
        _default_collector = TraceCollector(output_dir)
    return _default_collector
