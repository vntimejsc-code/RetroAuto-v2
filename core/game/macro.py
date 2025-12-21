"""
RetroAuto v2 - Macro System

Record and playback mouse/keyboard macros.
Part of RetroScript Phase 20 - Game-Specific Features.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from threading import Thread, Event
from typing import Any, Callable

# Try to import pynput for recording
try:
    from pynput import mouse, keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False
    mouse = None
    keyboard = None

# Try to import pyautogui for playback
try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    pyautogui = None


class ActionType(Enum):
    """Types of recordable actions."""

    CLICK = auto()
    MOVE = auto()
    SCROLL = auto()
    KEY_PRESS = auto()
    KEY_RELEASE = auto()
    DELAY = auto()


@dataclass
class MacroAction:
    """A single recorded action."""

    action_type: ActionType
    timestamp: float = 0.0
    x: int = 0
    y: int = 0
    button: str = ""
    key: str = ""
    delta: int = 0  # For scroll

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON."""
        return {
            "type": self.action_type.name,
            "timestamp": self.timestamp,
            "x": self.x,
            "y": self.y,
            "button": self.button,
            "key": self.key,
            "delta": self.delta,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MacroAction":
        """Create from dictionary."""
        return cls(
            action_type=ActionType[data["type"]],
            timestamp=data.get("timestamp", 0),
            x=data.get("x", 0),
            y=data.get("y", 0),
            button=data.get("button", ""),
            key=data.get("key", ""),
            delta=data.get("delta", 0),
        )


@dataclass
class Macro:
    """A recorded macro."""

    name: str
    actions: list[MacroAction] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    description: str = ""
    loop_count: int = 1  # Number of times to play

    @property
    def duration(self) -> float:
        """Get total duration of macro."""
        if not self.actions:
            return 0
        return self.actions[-1].timestamp

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON."""
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "loop_count": self.loop_count,
            "actions": [a.to_dict() for a in self.actions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Macro":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            created_at=data.get("created_at", time.time()),
            loop_count=data.get("loop_count", 1),
            actions=[MacroAction.from_dict(a) for a in data.get("actions", [])],
        )


class MacroRecorder:
    """Record mouse and keyboard actions.

    Usage:
        recorder = MacroRecorder()
        recorder.start()
        # ... user performs actions ...
        macro = recorder.stop()
    """

    def __init__(self) -> None:
        self._recording = False
        self._start_time = 0.0
        self._actions: list[MacroAction] = []
        self._mouse_listener = None
        self._keyboard_listener = None
        self._stop_event = Event()

        # Callbacks
        self.on_action: Callable[[MacroAction], None] | None = None

    def start(self) -> None:
        """Start recording."""
        if self._recording or not HAS_PYNPUT:
            return

        self._recording = True
        self._start_time = time.time()
        self._actions.clear()
        self._stop_event.clear()

        # Start mouse listener
        self._mouse_listener = mouse.Listener(
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._mouse_listener.start()

        # Start keyboard listener
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._keyboard_listener.start()

    def stop(self, name: str = "Untitled") -> Macro:
        """Stop recording and return macro.

        Args:
            name: Name for the macro

        Returns:
            Recorded Macro
        """
        self._recording = False
        self._stop_event.set()

        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()

        return Macro(
            name=name,
            actions=self._actions.copy(),
        )

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording

    def _add_action(self, action: MacroAction) -> None:
        """Add an action with timestamp."""
        action.timestamp = time.time() - self._start_time
        self._actions.append(action)

        if self.on_action:
            self.on_action(action)

    def _on_click(self, x: int, y: int, button: Any, pressed: bool) -> None:
        """Handle mouse click."""
        if not self._recording or not pressed:
            return

        self._add_action(MacroAction(
            action_type=ActionType.CLICK,
            x=x,
            y=y,
            button=button.name if hasattr(button, "name") else str(button),
        ))

    def _on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """Handle mouse scroll."""
        if not self._recording:
            return

        self._add_action(MacroAction(
            action_type=ActionType.SCROLL,
            x=x,
            y=y,
            delta=dy,
        ))

    def _on_key_press(self, key: Any) -> None:
        """Handle key press."""
        if not self._recording:
            return

        key_str = str(key).replace("Key.", "").replace("'", "")

        self._add_action(MacroAction(
            action_type=ActionType.KEY_PRESS,
            key=key_str,
        ))

    def _on_key_release(self, key: Any) -> None:
        """Handle key release."""
        # We don't typically record key releases
        pass


class MacroPlayer:
    """Play back recorded macros.

    Usage:
        player = MacroPlayer()
        player.play(macro)
    """

    def __init__(self, speed: float = 1.0) -> None:
        self._speed = speed  # 1.0 = normal, 2.0 = double speed
        self._playing = False
        self._stop_event = Event()

        # Callbacks
        self.on_action: Callable[[MacroAction], None] | None = None
        self.on_complete: Callable[[], None] | None = None

    def set_speed(self, speed: float) -> None:
        """Set playback speed."""
        self._speed = max(0.1, min(10.0, speed))

    def play(self, macro: Macro, loop: int | None = None) -> None:
        """Play a macro.

        Args:
            macro: Macro to play
            loop: Override loop count
        """
        if self._playing or not HAS_PYAUTOGUI:
            return

        self._playing = True
        self._stop_event.clear()

        loops = loop or macro.loop_count

        for i in range(loops):
            if self._stop_event.is_set():
                break

            last_time = 0.0

            for action in macro.actions:
                if self._stop_event.is_set():
                    break

                # Wait for timing
                delay = (action.timestamp - last_time) / self._speed
                if delay > 0:
                    time.sleep(delay)
                last_time = action.timestamp

                # Execute action
                self._execute(action)

                if self.on_action:
                    self.on_action(action)

        self._playing = False

        if self.on_complete:
            self.on_complete()

    def play_async(self, macro: Macro, loop: int | None = None) -> Thread:
        """Play macro in background thread.

        Returns:
            Thread running the playback
        """
        thread = Thread(target=self.play, args=(macro, loop), daemon=True)
        thread.start()
        return thread

    def stop(self) -> None:
        """Stop playback."""
        self._stop_event.set()
        self._playing = False

    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self._playing

    def _execute(self, action: MacroAction) -> None:
        """Execute a single action."""
        if action.action_type == ActionType.CLICK:
            pyautogui.click(action.x, action.y, button=action.button.lower())

        elif action.action_type == ActionType.MOVE:
            pyautogui.moveTo(action.x, action.y)

        elif action.action_type == ActionType.SCROLL:
            pyautogui.scroll(action.delta, action.x, action.y)

        elif action.action_type == ActionType.KEY_PRESS:
            pyautogui.press(action.key)


class MacroManager:
    """Manage macro storage and retrieval.

    Usage:
        manager = MacroManager()
        manager.save(macro)
        loaded = manager.load("my_macro")
    """

    def __init__(self, macros_dir: str | Path = "macros") -> None:
        self.macros_dir = Path(macros_dir)
        self.macros_dir.mkdir(parents=True, exist_ok=True)

    def save(self, macro: Macro) -> Path:
        """Save macro to file.

        Returns:
            Path to saved file
        """
        filename = f"{macro.name}.json"
        filepath = self.macros_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(macro.to_dict(), f, indent=2)

        return filepath

    def load(self, name: str) -> Macro | None:
        """Load macro from file.

        Args:
            name: Macro name (without extension)

        Returns:
            Loaded Macro or None
        """
        filepath = self.macros_dir / f"{name}.json"
        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return Macro.from_dict(data)

    def list_macros(self) -> list[str]:
        """List all saved macro names."""
        return [f.stem for f in self.macros_dir.glob("*.json")]

    def delete(self, name: str) -> bool:
        """Delete a macro.

        Returns:
            True if deleted
        """
        filepath = self.macros_dir / f"{name}.json"
        if filepath.exists():
            filepath.unlink()
            return True
        return False


# Global instances
_recorder: MacroRecorder | None = None
_player: MacroPlayer | None = None
_manager: MacroManager | None = None


def get_recorder() -> MacroRecorder:
    """Get the default macro recorder."""
    global _recorder
    if _recorder is None:
        _recorder = MacroRecorder()
    return _recorder


def get_player() -> MacroPlayer:
    """Get the default macro player."""
    global _player
    if _player is None:
        _player = MacroPlayer()
    return _player


def get_manager() -> MacroManager:
    """Get the default macro manager."""
    global _manager
    if _manager is None:
        _manager = MacroManager()
    return _manager
