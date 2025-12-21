"""
RetroAuto v2 - Script Recorder

Record mouse and keyboard actions to create automation scripts.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

from infra import get_logger

if TYPE_CHECKING:
    from core.models import Action

logger = get_logger("Recorder")


class RecordState(Enum):
    """Recorder state."""
    IDLE = auto()
    RECORDING = auto()
    PAUSED = auto()


@dataclass
class RecordedEvent:
    """A recorded mouse/keyboard event."""
    
    event_type: str  # click, double_click, right_click, key, hotkey, type
    timestamp: float
    
    # Mouse data
    x: int | None = None
    y: int | None = None
    button: str | None = None
    
    # Keyboard data
    key: str | None = None
    keys: list[str] = field(default_factory=list)
    text: str | None = None
    
    # Computed delay from previous event
    delay_ms: int = 0


class ActionRecorder:
    """
    Record user actions and convert to script actions.
    
    Features:
    - Record mouse clicks (left, right, double)
    - Record keyboard input (keys, hotkeys, text)
    - Calculate delays between actions
    - Convert to script actions
    - Filter noise (accidental clicks, etc.)
    
    Usage:
        recorder = ActionRecorder()
        recorder.on_event(callback)  # Receive events
        
        recorder.start()
        # ... user performs actions ...
        recorder.stop()
        
        actions = recorder.to_actions()
    """

    def __init__(
        self,
        min_delay_ms: int = 50,
        max_delay_ms: int = 5000,
        merge_clicks: bool = True,
    ) -> None:
        """
        Initialize recorder.
        
        Args:
            min_delay_ms: Minimum delay to record (filter fast clicks)
            max_delay_ms: Cap delays at this value
            merge_clicks: Merge sequential clicks at same position
        """
        self._min_delay = min_delay_ms
        self._max_delay = max_delay_ms
        self._merge_clicks = merge_clicks
        
        self._state = RecordState.IDLE
        self._events: list[RecordedEvent] = []
        self._start_time: float = 0
        self._last_event_time: float = 0
        
        self._callbacks: list[Callable[[RecordedEvent], None]] = []
        
        # pynput listeners (lazy import)
        self._mouse_listener = None
        self._keyboard_listener = None
        
        # For text accumulation
        self._text_buffer: list[str] = []
        self._text_start_time: float = 0
        
        # Lock for thread safety
        self._lock = threading.Lock()

    @property
    def state(self) -> RecordState:
        """Get current state."""
        return self._state

    @property
    def events(self) -> list[RecordedEvent]:
        """Get recorded events."""
        return self._events.copy()

    def on_event(self, callback: Callable[[RecordedEvent], None]) -> None:
        """Register callback for recorded events."""
        self._callbacks.append(callback)

    def start(self) -> None:
        """Start recording."""
        if self._state == RecordState.RECORDING:
            logger.warning("Already recording")
            return

        self._events.clear()
        self._start_time = time.time()
        self._last_event_time = self._start_time
        self._state = RecordState.RECORDING

        self._start_listeners()
        logger.info("Recording started")

    def stop(self) -> list[RecordedEvent]:
        """Stop recording and return events."""
        self._stop_listeners()
        self._flush_text_buffer()
        self._state = RecordState.IDLE
        logger.info("Recording stopped, %d events captured", len(self._events))
        return self._events.copy()

    def pause(self) -> None:
        """Pause recording."""
        if self._state == RecordState.RECORDING:
            self._state = RecordState.PAUSED
            logger.info("Recording paused")

    def resume(self) -> None:
        """Resume recording."""
        if self._state == RecordState.PAUSED:
            self._state = RecordState.RECORDING
            self._last_event_time = time.time()
            logger.info("Recording resumed")

    def clear(self) -> None:
        """Clear recorded events."""
        with self._lock:
            self._events.clear()

    def _start_listeners(self) -> None:
        """Start mouse and keyboard listeners."""
        try:
            from pynput import mouse, keyboard
            
            self._mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click,
            )
            self._mouse_listener.start()
            
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release,
            )
            self._keyboard_listener.start()
            
        except ImportError:
            logger.error("pynput not installed. Run: pip install pynput")
            raise

    def _stop_listeners(self) -> None:
        """Stop listeners."""
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
            
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

    def _record_event(self, event: RecordedEvent) -> None:
        """Record an event."""
        if self._state != RecordState.RECORDING:
            return

        with self._lock:
            # Calculate delay from last event
            now = time.time()
            delay_ms = int((now - self._last_event_time) * 1000)
            
            # Apply delay limits
            if delay_ms < self._min_delay:
                delay_ms = 0
            elif delay_ms > self._max_delay:
                delay_ms = self._max_delay
            
            event.delay_ms = delay_ms
            event.timestamp = now
            
            self._events.append(event)
            self._last_event_time = now

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error("Callback error: %s", e)

    def _on_mouse_click(self, x: int, y: int, button: Any, pressed: bool) -> None:
        """Handle mouse click."""
        if not pressed:  # Only record press, not release
            return

        # Flush any pending text
        self._flush_text_buffer()

        button_name = str(button).split(".")[-1]  # 'Button.left' -> 'left'
        
        event = RecordedEvent(
            event_type="click",
            timestamp=time.time(),
            x=x,
            y=y,
            button=button_name,
        )
        
        self._record_event(event)

    def _on_key_press(self, key: Any) -> None:
        """Handle key press."""
        try:
            # Check if it's a character key
            if hasattr(key, "char") and key.char:
                # Accumulate text
                self._text_buffer.append(key.char)
                if not self._text_start_time:
                    self._text_start_time = time.time()
            else:
                # Special key - flush text buffer first
                self._flush_text_buffer()
                
                key_name = str(key).replace("Key.", "").upper()
                
                # Check for hotkey (Ctrl/Alt/Shift + key)
                # This is simplified - full implementation would track modifiers
                event = RecordedEvent(
                    event_type="key",
                    timestamp=time.time(),
                    key=key_name,
                )
                self._record_event(event)
                
        except Exception as e:
            logger.debug("Key event error: %s", e)

    def _on_key_release(self, key: Any) -> None:
        """Handle key release (for detecting typing end)."""
        pass  # Text is flushed on special keys or after timeout

    def _flush_text_buffer(self) -> None:
        """Flush accumulated text to an event."""
        if not self._text_buffer:
            return

        text = "".join(self._text_buffer)
        self._text_buffer.clear()

        if len(text) >= 2:  # Only record if meaningful text
            event = RecordedEvent(
                event_type="type",
                timestamp=self._text_start_time or time.time(),
                text=text,
            )
            self._record_event(event)

        self._text_start_time = 0

    def to_actions(self) -> list["Action"]:
        """
        Convert recorded events to script actions.
        
        Returns:
            List of Action objects
        """
        from core.models import Click, Delay, Hotkey, TypeText

        actions: list[Action] = []

        for event in self._events:
            # Add delay if significant
            if event.delay_ms >= 100:
                actions.append(Delay(ms=event.delay_ms))

            if event.event_type == "click":
                clicks = 1
                button = event.button or "left"
                
                # Check for double-click (next event same position)
                # This is simplified - production would check timing
                
                actions.append(Click(
                    x=event.x,
                    y=event.y,
                    button=button,
                    clicks=clicks,
                ))
                
            elif event.event_type == "key":
                actions.append(Hotkey(keys=[event.key or ""]))
                
            elif event.event_type == "type":
                actions.append(TypeText(text=event.text or ""))

        return actions

    def export_to_dsl(self) -> str:
        """
        Export recorded events as DSL code.
        
        Returns:
            DSL code string
        """
        lines = ["flow recorded {"]
        
        for event in self._events:
            if event.delay_ms >= 100:
                lines.append(f"    delay({event.delay_ms});")

            if event.event_type == "click":
                button = event.button or "left"
                if button == "left":
                    lines.append(f"    click({event.x}, {event.y});")
                elif button == "right":
                    lines.append(f"    right_click({event.x}, {event.y});")
                    
            elif event.event_type == "key":
                lines.append(f'    hotkey("{event.key}");')
                
            elif event.event_type == "type":
                lines.append(f'    type_text("{event.text}");')

        lines.append("}")
        return "\n".join(lines)
