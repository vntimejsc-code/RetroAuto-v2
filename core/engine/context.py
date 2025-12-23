"""
RetroAuto v2 - Engine Execution Context

Shared state and resources for action execution.
"""

from dataclasses import dataclass, field
from enum import Enum
from threading import Event, Lock
from typing import Any

from core.models import Match, Script
from core.security.policy import SecurityPolicy
from core.templates import TemplateStore
from infra import get_logger
from input import KeyboardController, MouseController
from vision import ImageWaiter, Matcher, ScreenCapture, WaitOutcome

logger = get_logger("Context")


class EngineState(Enum):
    """Engine execution state."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"


@dataclass
class ExecutionContext:
    """
    Shared context for action execution.

    Provides access to all services and shared state.
    Thread-safe for state changes.
    """

    # Script and templates
    script: Script
    templates: TemplateStore

    # Security
    policy: SecurityPolicy = field(default_factory=SecurityPolicy.unsafe)

    # Services
    capture: ScreenCapture = field(default_factory=ScreenCapture)
    matcher: Matcher | None = None
    waiter: ImageWaiter | None = None
    mouse: MouseController = field(default_factory=MouseController)
    keyboard: KeyboardController = field(default_factory=KeyboardController)

    # Execution state
    state: EngineState = EngineState.IDLE
    current_flow: str = ""
    current_step: int = 0

    # Last match result (for Click with use_match=True)
    last_match: Match | None = None

    # Variables for custom logic
    variables: dict[str, Any] = field(default_factory=dict)

    # Thread synchronization
    _lock: Lock = field(default_factory=Lock)
    _pause_event: Event = field(default_factory=Event)
    _stop_event: Event = field(default_factory=Event)

    def __post_init__(self) -> None:
        """Initialize derived services."""
        if self.matcher is None:
            self.matcher = Matcher(self.templates, self.capture)
        if self.waiter is None:
            self.waiter = ImageWaiter(self.matcher)
        self._pause_event.set()  # Not paused initially

    @property
    def is_running(self) -> bool:
        """Check if engine is running."""
        return self.state == EngineState.RUNNING

    @property
    def is_paused(self) -> bool:
        """Check if engine is paused."""
        return self.state == EngineState.PAUSED

    @property
    def should_stop(self) -> bool:
        """Check if stop was requested."""
        return self._stop_event.is_set()

    def set_state(self, state: EngineState) -> None:
        """Thread-safe state change."""
        with self._lock:
            old_state = self.state
            self.state = state
            logger.info("Engine state: %s -> %s", old_state.value, state.value)

    def request_pause(self) -> None:
        """Request pause (blocks execution at next checkpoint)."""
        self._pause_event.clear()
        self.set_state(EngineState.PAUSED)

    def request_resume(self) -> None:
        """Resume from pause."""
        self._pause_event.set()
        self.set_state(EngineState.RUNNING)

    def request_stop(self) -> None:
        """Request stop (sets flag, also unblocks pause)."""
        self._stop_event.set()
        self._pause_event.set()  # Unblock if paused
        self.set_state(EngineState.STOPPING)

    def reset(self) -> None:
        """Reset state for new execution."""
        self._stop_event.clear()
        self._pause_event.set()
        self.current_flow = ""
        self.current_step = 0
        self.last_match = None
        self.set_state(EngineState.IDLE)

    def wait_if_paused(self) -> bool:
        """
        Wait if paused. Returns False if stop requested.

        Call this at checkpoints in action execution.
        """
        self._pause_event.wait()
        return not self.should_stop

    def update_step(self, flow: str, step: int) -> None:
        """Update current position (thread-safe)."""
        with self._lock:
            self.current_flow = flow
            self.current_step = step

    def wait_for_image(
        self,
        asset_id: str,
        timeout_ms: int = 10000,
        appear: bool = True,
        smart_wait: bool = True,
    ) -> WaitOutcome | None:
        """Wait for image using configured waiter."""
        if not self.waiter:
            return None
        
        if appear:
            return self.waiter.wait_appear(
                asset_id, timeout_ms=timeout_ms, smart_wait=smart_wait
            )
        else:
            return self.waiter.wait_vanish(
                asset_id, timeout_ms=timeout_ms, smart_wait=smart_wait
            )
