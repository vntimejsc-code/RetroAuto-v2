"""
RetroAuto v2 - Script Recorder

Record mouse/keyboard events and generate RetroScript code.
Part of RetroScript Phase 7 - Tools + Productivity.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto


class EventType(Enum):
    """Types of recorded events."""

    MOUSE_CLICK = auto()
    MOUSE_MOVE = auto()
    MOUSE_DRAG = auto()
    MOUSE_SCROLL = auto()
    KEY_PRESS = auto()
    KEY_RELEASE = auto()
    KEY_TYPE = auto()  # Text input
    DELAY = auto()


@dataclass
class RecordedEvent:
    """A single recorded event."""

    event_type: EventType
    timestamp: float  # Seconds since recording start
    x: int = 0
    y: int = 0
    button: str = ""  # left, right, middle
    key: str = ""  # Key name
    text: str = ""  # Typed text
    scroll_delta: int = 0


@dataclass
class RecorderOptions:
    """Options for script recording."""

    record_mouse_moves: bool = False  # Record all mouse movements
    record_delays: bool = True  # Include sleep() between actions
    min_delay: float = 0.1  # Minimum delay to record (seconds)
    max_delay: float = 5.0  # Maximum delay to cap at
    merge_clicks: bool = True  # Merge rapid clicks
    merge_typing: bool = True  # Merge key presses into type()
    include_comments: bool = True  # Add descriptive comments
    indent_size: int = 4


class ScriptRecorder:
    """Records user actions and generates RetroScript code.

    Usage:
        recorder = ScriptRecorder()
        recorder.start()
        # User performs actions...
        recorder.stop()
        code = recorder.generate()
    """

    def __init__(self, options: RecorderOptions | None = None) -> None:
        self.options = options or RecorderOptions()
        self._events: list[RecordedEvent] = []
        self._recording = False
        self._start_time = 0.0

        # Callbacks
        self.on_event: Callable[[RecordedEvent], None] | None = None

    def start(self) -> None:
        """Start recording events."""
        self._events.clear()
        self._recording = True
        self._start_time = time.time()

    def stop(self) -> None:
        """Stop recording events."""
        self._recording = False

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording

    def record_click(self, x: int, y: int, button: str = "left") -> None:
        """Record a mouse click event."""
        if not self._recording:
            return
        self._add_event(
            RecordedEvent(
                event_type=EventType.MOUSE_CLICK,
                timestamp=self._get_timestamp(),
                x=x,
                y=y,
                button=button,
            )
        )

    def record_move(self, x: int, y: int) -> None:
        """Record a mouse move event."""
        if not self._recording or not self.options.record_mouse_moves:
            return
        self._add_event(
            RecordedEvent(
                event_type=EventType.MOUSE_MOVE,
                timestamp=self._get_timestamp(),
                x=x,
                y=y,
            )
        )

    def record_drag(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Record a drag event."""
        if not self._recording:
            return
        # Store start in x,y and end in button as "x2,y2"
        self._add_event(
            RecordedEvent(
                event_type=EventType.MOUSE_DRAG,
                timestamp=self._get_timestamp(),
                x=x1,
                y=y1,
                button=f"{x2},{y2}",
            )
        )

    def record_scroll(self, x: int, y: int, delta: int) -> None:
        """Record a scroll event."""
        if not self._recording:
            return
        self._add_event(
            RecordedEvent(
                event_type=EventType.MOUSE_SCROLL,
                timestamp=self._get_timestamp(),
                x=x,
                y=y,
                scroll_delta=delta,
            )
        )

    def record_key(self, key: str) -> None:
        """Record a key press event."""
        if not self._recording:
            return
        self._add_event(
            RecordedEvent(
                event_type=EventType.KEY_PRESS,
                timestamp=self._get_timestamp(),
                key=key,
            )
        )

    def record_text(self, text: str) -> None:
        """Record typed text."""
        if not self._recording:
            return
        self._add_event(
            RecordedEvent(
                event_type=EventType.KEY_TYPE,
                timestamp=self._get_timestamp(),
                text=text,
            )
        )

    def _add_event(self, event: RecordedEvent) -> None:
        """Add event and trigger callback."""
        self._events.append(event)
        if self.on_event:
            self.on_event(event)

    def _get_timestamp(self) -> float:
        """Get timestamp relative to recording start."""
        return time.time() - self._start_time

    def get_events(self) -> list[RecordedEvent]:
        """Get all recorded events."""
        return self._events.copy()

    def clear(self) -> None:
        """Clear all recorded events."""
        self._events.clear()

    def generate(self, flow_name: str = "recorded_script") -> str:
        """Generate RetroScript code from recorded events.

        Args:
            flow_name: Name for the generated flow

        Returns:
            RetroScript source code
        """
        if not self._events:
            return f"flow {flow_name} {{\n    # No events recorded\n}}"

        lines: list[str] = []
        indent = " " * self.options.indent_size

        # Header
        if self.options.include_comments:
            lines.append(f"# Recorded script - {len(self._events)} events")
            lines.append(f"# Duration: {self._events[-1].timestamp:.1f}s")
            lines.append("")

        lines.append(f"flow {flow_name} {{")

        # Process events
        processed = self._process_events()
        last_time = 0.0

        for event in processed:
            # Add delay if needed
            if self.options.record_delays:
                delay = event.timestamp - last_time
                if delay >= self.options.min_delay:
                    delay = min(delay, self.options.max_delay)
                    lines.append(f"{indent}sleep({self._format_duration(delay)})")
                last_time = event.timestamp

            # Generate event code
            code = self._generate_event_code(event)
            if code:
                lines.append(f"{indent}{code}")

        lines.append("}")
        return "\n".join(lines)

    def _process_events(self) -> list[RecordedEvent]:
        """Process events: merge typing, merge clicks, etc."""
        if not self._events:
            return []

        result: list[RecordedEvent] = []
        i = 0

        while i < len(self._events):
            event = self._events[i]

            # Merge consecutive key presses into text
            if self.options.merge_typing and event.event_type == EventType.KEY_PRESS:
                text = ""
                start_time = event.timestamp
                while i < len(self._events) and self._events[i].event_type == EventType.KEY_PRESS:
                    key = self._events[i].key
                    if len(key) == 1:  # Single character
                        text += key
                    else:
                        break  # Special key ends merge
                    i += 1
                if text:
                    result.append(
                        RecordedEvent(
                            event_type=EventType.KEY_TYPE,
                            timestamp=start_time,
                            text=text,
                        )
                    )
                    continue

            result.append(event)
            i += 1

        return result

    def _generate_event_code(self, event: RecordedEvent) -> str:
        """Generate RetroScript code for a single event."""
        if event.event_type == EventType.MOUSE_CLICK:
            if event.button == "left":
                return f"click({event.x}, {event.y})"
            else:
                return f'click({event.x}, {event.y}, button="{event.button}")'

        elif event.event_type == EventType.MOUSE_MOVE:
            return f"move({event.x}, {event.y})"

        elif event.event_type == EventType.MOUSE_DRAG:
            x2, y2 = event.button.split(",")
            return f"drag({event.x}, {event.y}, {x2}, {y2})"

        elif event.event_type == EventType.MOUSE_SCROLL:
            return f"scroll({event.scroll_delta})"

        elif event.event_type == EventType.KEY_PRESS:
            return f'press("{event.key}")'

        elif event.event_type == EventType.KEY_TYPE:
            # Escape quotes in text
            text = event.text.replace('"', '\\"')
            return f'type("{text}")'

        return ""

    def _format_duration(self, seconds: float) -> str:
        """Format duration as RetroScript time literal."""
        if seconds < 1:
            return f"{int(seconds * 1000)}ms"
        elif seconds == int(seconds):
            return f"{int(seconds)}s"
        else:
            return f"{seconds:.1f}s"


def record_and_generate(duration: float = 10.0, flow_name: str = "recorded") -> str:
    """Convenience function to record for a duration and generate code.

    Note: This is a placeholder. Actual recording requires
    platform-specific event hooks (pynput, pyautogui, etc.)
    """
    recorder = ScriptRecorder()
    recorder.start()
    # In real implementation, would hook into system events
    time.sleep(min(duration, 0.1))  # Placeholder
    recorder.stop()
    return recorder.generate(flow_name)
