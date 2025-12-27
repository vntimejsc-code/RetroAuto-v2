"""
RetroAuto v2 - Event Recorder

Record mouse and keyboard events for macro creation.

Phase: Mid-term improvement
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable

from infra import get_logger

logger = get_logger("Recorder")


class EventType(Enum):
    """Types of recorded events."""

    CLICK = auto()
    DOUBLE_CLICK = auto()
    RIGHT_CLICK = auto()
    MOUSE_MOVE = auto()
    MOUSE_SCROLL = auto()
    KEY_PRESS = auto()
    KEY_RELEASE = auto()
    HOTKEY = auto()
    SCREENSHOT = auto()  # Keyframe screenshot


@dataclass
class RecorderEvent:
    """A single recorded event."""

    timestamp: float
    event_type: EventType
    x: int = 0
    y: int = 0
    data: dict[str, Any] = field(default_factory=dict)
    screenshot_path: str | None = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type.name,
            "x": self.x,
            "y": self.y,
            "data": self.data,
            "screenshot_path": self.screenshot_path,
        }


@dataclass
class ActionChunk:
    """A group of events that form a logical action."""

    chunk_id: str
    action_type: str  # "click", "type", "hotkey", "drag"
    description: str
    events: list[RecorderEvent] = field(default_factory=list)
    suggested_name: str = ""
    params: dict[str, Any] = field(default_factory=dict)


class RecorderState(Enum):
    """Recorder state."""

    IDLE = auto()
    RECORDING = auto()
    PAUSED = auto()
    STOPPED = auto()


class EventRecorder:
    """
    Record mouse and keyboard events.

    Features:
    - Mouse: clicks, double-clicks, right-clicks, scrolls
    - Keyboard: key presses, hotkey combinations
    - Screenshots: keyframe captures
    - Segmentation: group events into logical actions

    Usage:
        recorder = EventRecorder()
        recorder.start()
        # ... user performs actions ...
        recorder.stop()
        events = recorder.get_events()
        chunks = recorder.segment_events()
    """

    def __init__(
        self,
        capture_screenshots: bool = True,
        screenshot_dir: Path | None = None,
        min_move_distance: int = 50,  # Ignore small mouse movements
    ) -> None:
        self._events: list[RecorderEvent] = []
        self._state = RecorderState.IDLE
        self._start_time: float = 0
        self._capture_screenshots = capture_screenshots
        self._screenshot_dir = screenshot_dir or Path.cwd() / "recordings"
        self._min_move_distance = min_move_distance

        # Listeners (typed as Any to avoid pynput type issues)
        self._mouse_listener: Any = None
        self._keyboard_listener: Any = None
        self._lock = threading.Lock()

        # Last positions for movement filtering
        self._last_x = 0
        self._last_y = 0

        # Key tracking for hotkeys
        self._pressed_keys: set[str] = set()

        # Callbacks
        self._on_event: Callable[[RecorderEvent], None] | None = None

    @property
    def state(self) -> RecorderState:
        return self._state

    @property
    def is_recording(self) -> bool:
        return self._state == RecorderState.RECORDING

    def on_event(self, callback: Callable[[RecorderEvent], None]) -> None:
        """Register callback for each recorded event."""
        self._on_event = callback

    def start(self) -> None:
        """Start recording events."""
        if self._state == RecorderState.RECORDING:
            logger.warning("Already recording")
            return

        self._events.clear()
        self._start_time = time.time()
        self._state = RecorderState.RECORDING

        # Ensure screenshot directory exists
        if self._capture_screenshots:
            self._screenshot_dir.mkdir(parents=True, exist_ok=True)

        # Start listeners
        self._start_listeners()
        logger.info("Recording started")

    def stop(self) -> list[RecorderEvent]:
        """Stop recording and return events."""
        if self._state != RecorderState.RECORDING:
            return self._events

        self._state = RecorderState.STOPPED
        self._stop_listeners()

        logger.info("Recording stopped: %d events captured", len(self._events))
        return self._events

    def pause(self) -> None:
        """Pause recording."""
        if self._state == RecorderState.RECORDING:
            self._state = RecorderState.PAUSED
            logger.info("Recording paused")

    def resume(self) -> None:
        """Resume recording."""
        if self._state == RecorderState.PAUSED:
            self._state = RecorderState.RECORDING
            logger.info("Recording resumed")

    def get_events(self) -> list[RecorderEvent]:
        """Get all recorded events."""
        return self._events.copy()

    def _start_listeners(self) -> None:
        """Start mouse and keyboard listeners."""
        try:
            from pynput import mouse, keyboard

            self._mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll,
            )
            self._mouse_listener.start()

            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release,
            )
            self._keyboard_listener.start()

        except ImportError:
            logger.warning("pynput not installed. Recording without input hooks.")
            logger.warning("Install with: pip install pynput")

    def _stop_listeners(self) -> None:
        """Stop all listeners."""
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None

        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

    def _add_event(self, event: RecorderEvent) -> None:
        """Add event to list (thread-safe)."""
        with self._lock:
            self._events.append(event)

        if self._on_event:
            self._on_event(event)

    def _capture_screenshot(self) -> str | None:
        """Capture screenshot and return path."""
        if not self._capture_screenshots:
            return None

        try:
            import mss

            timestamp = int(time.time() * 1000)
            filename = f"screenshot_{timestamp}.png"
            filepath = self._screenshot_dir / filename

            with mss.mss() as sct:
                sct.shot(output=str(filepath))

            return str(filepath)
        except Exception as e:
            logger.warning("Screenshot failed: %s", e)
            return None

    def _on_mouse_click(self, x: int, y: int, button, pressed: bool) -> None:
        """Handle mouse click events."""
        if self._state != RecorderState.RECORDING or not pressed:
            return

        # Determine event type
        button_name = str(button).split(".")[-1]
        if button_name == "left":
            event_type = EventType.CLICK
        elif button_name == "right":
            event_type = EventType.RIGHT_CLICK
        else:
            event_type = EventType.CLICK

        # Capture screenshot on click
        screenshot = self._capture_screenshot()

        event = RecorderEvent(
            timestamp=time.time() - self._start_time,
            event_type=event_type,
            x=x,
            y=y,
            data={"button": button_name},
            screenshot_path=screenshot,
        )
        self._add_event(event)
        logger.debug("Click: (%d, %d) %s", x, y, button_name)

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """Handle mouse scroll events."""
        if self._state != RecorderState.RECORDING:
            return

        event = RecorderEvent(
            timestamp=time.time() - self._start_time,
            event_type=EventType.MOUSE_SCROLL,
            x=x,
            y=y,
            data={"dx": dx, "dy": dy},
        )
        self._add_event(event)

    def _on_key_press(self, key) -> None:
        """Handle key press events."""
        if self._state != RecorderState.RECORDING:
            return

        try:
            key_str = key.char if hasattr(key, "char") and key.char else str(key).split(".")[-1]
        except AttributeError:
            key_str = str(key)

        self._pressed_keys.add(key_str)

        event = RecorderEvent(
            timestamp=time.time() - self._start_time,
            event_type=EventType.KEY_PRESS,
            data={"key": key_str, "modifiers": list(self._pressed_keys)},
        )
        self._add_event(event)

    def _on_key_release(self, key) -> None:
        """Handle key release events."""
        if self._state != RecorderState.RECORDING:
            return

        try:
            key_str = key.char if hasattr(key, "char") and key.char else str(key).split(".")[-1]
        except AttributeError:
            key_str = str(key)

        self._pressed_keys.discard(key_str)

        event = RecorderEvent(
            timestamp=time.time() - self._start_time,
            event_type=EventType.KEY_RELEASE,
            data={"key": key_str},
        )
        self._add_event(event)

    def segment_events(self) -> list[ActionChunk]:
        """
        Segment events into logical action chunks.

        Groups events by:
        - Time gaps (>500ms = new chunk + delay action)
        - Event type transitions
        - Window changes

        Returns:
            List of ActionChunks with suggested names
        """
        if not self._events:
            return []

        chunks: list[ActionChunk] = []
        current_events: list[RecorderEvent] = []
        chunk_id = 0

        for i, event in enumerate(self._events):
            # Check for time gap
            if current_events:
                # Gap between end of last chunk and start of this new event
                last_event_time = current_events[-1].timestamp
                current_event_time = event.timestamp
                time_gap = current_event_time - last_event_time

                if time_gap > 0.5:  # 500ms gap = new chunk
                    # 1. Flush current chunk
                    chunks.append(self._create_chunk(chunk_id, current_events))
                    chunk_id += 1
                    current_events = []

                    # 2. Insert Delay chunk
                    # Round to nearest 100ms to look cleaner
                    delay_ms = int(round(time_gap * 1000 / 100) * 100)
                    chunks.append(
                        ActionChunk(
                            chunk_id=f"chunk_{chunk_id}",
                            action_type="delay",
                            description=f"Wait {delay_ms}ms",
                            events=[],  # No events for synthetic delay
                            suggested_name=f"delay_{chunk_id}",
                            params={"ms": delay_ms},
                        )
                    )
                    chunk_id += 1

            current_events.append(event)

        # Final chunk
        if current_events:
            chunks.append(self._create_chunk(chunk_id, current_events))

        logger.info("Segmented %d events into %d chunks", len(self._events), len(chunks))
        return chunks

    def _create_chunk(self, chunk_id: int, events: list[RecorderEvent]) -> ActionChunk:
        """Create an ActionChunk from a group of events."""
        # Determine action type based on events
        event_types = {e.event_type for e in events}
        
        # Initialize with proper type annotation
        action_type: str = "unknown"
        description: str = "Unknown action"
        suggested_name: str = f"action_{chunk_id}"
        params: dict[str, Any] = {}

        if EventType.CLICK in event_types or EventType.RIGHT_CLICK in event_types:
            action_type = "click"
            click_event = next(e for e in events if e.event_type in (EventType.CLICK, EventType.RIGHT_CLICK))
            description = f"Click at ({click_event.x}, {click_event.y})"
            suggested_name = f"click_{chunk_id}"
            params = {"x": click_event.x, "y": click_event.y}

        elif EventType.KEY_PRESS in event_types:
            action_type = "type"
            keys = [e.data.get("key", "") for e in events if e.event_type == EventType.KEY_PRESS]
            text = "".join(k for k in keys if len(k) == 1)
            description = f"Type: {text[:20]}..." if len(text) > 20 else f"Type: {text}"
            suggested_name = f"type_{chunk_id}"
            params = {"text": text}

        elif EventType.MOUSE_SCROLL in event_types:
            action_type = "scroll"
            description = "Scroll"
            suggested_name = f"scroll_{chunk_id}"
            params = {}

        return ActionChunk(
            chunk_id=f"chunk_{chunk_id}",
            action_type=action_type,
            description=description,
            events=events,
            suggested_name=suggested_name,
            params=params,
        )

    def export_script(self, chunks: list[ActionChunk]) -> str:
        """
        Export chunks as RetroScript DSL.

        Args:
            chunks: Segmented action chunks

        Returns:
            Generated DSL code
        """
        lines = ["# Auto-generated from recording", f"# Date: {datetime.now().isoformat()}", ""]

        for chunk in chunks:
            if chunk.action_type == "click":
                x = chunk.params.get("x", 0)
                y = chunk.params.get("y", 0)
                lines.append(f"Click x={x} y={y}")

            elif chunk.action_type == "type":
                text = chunk.params.get("text", "")
                lines.append(f'TypeText "{text}"')

            elif chunk.action_type == "scroll":
                lines.append("# Scroll action (manual review needed)")

            lines.append("")

        return "\n".join(lines)
