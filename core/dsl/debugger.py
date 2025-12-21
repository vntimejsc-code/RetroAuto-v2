"""
RetroAuto v2 - Debugger Protocol

Debug adapter for DSL scripts:
- Breakpoint management
- Step execution (step over, step into, step out)
- Variable inspection
- Call stack tracking
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable
from threading import Lock


class DebugState(Enum):
    """Debugger state."""
    
    IDLE = auto()        # Not debugging
    RUNNING = auto()     # Running normally
    PAUSED = auto()      # Paused at breakpoint
    STEPPING = auto()    # Single-stepping


class StepMode(Enum):
    """Step execution mode."""
    
    OVER = auto()    # Step over (next line)
    INTO = auto()    # Step into function call
    OUT = auto()     # Step out of current function


@dataclass
class Breakpoint:
    """A breakpoint in the script."""
    
    id: int
    file: str
    line: int
    enabled: bool = True
    condition: str | None = None  # Optional conditional expression
    hit_count: int = 0


@dataclass 
class StackFrame:
    """A frame in the call stack."""
    
    id: int
    name: str  # Flow name or "main"
    file: str
    line: int
    column: int = 1
    locals: dict[str, Any] = field(default_factory=dict)


@dataclass
class Variable:
    """A variable for inspection."""
    
    name: str
    value: Any
    type: str
    expandable: bool = False
    children: list["Variable"] = field(default_factory=list)


class BreakpointManager:
    """
    Manages breakpoints for the debugger.
    
    Thread-safe breakpoint storage and lookup.
    """
    
    def __init__(self) -> None:
        self._breakpoints: dict[int, Breakpoint] = {}
        self._next_id = 1
        self._lock = Lock()
        self._by_location: dict[tuple[str, int], int] = {}  # (file, line) -> id
    
    def add(self, file: str, line: int, condition: str | None = None) -> Breakpoint:
        """Add a new breakpoint."""
        with self._lock:
            # Check if already exists
            key = (file, line)
            if key in self._by_location:
                return self._breakpoints[self._by_location[key]]
            
            bp = Breakpoint(
                id=self._next_id,
                file=file,
                line=line,
                condition=condition,
            )
            self._breakpoints[self._next_id] = bp
            self._by_location[key] = self._next_id
            self._next_id += 1
            return bp
    
    def remove(self, bp_id: int) -> bool:
        """Remove a breakpoint by ID."""
        with self._lock:
            if bp_id not in self._breakpoints:
                return False
            bp = self._breakpoints[bp_id]
            del self._by_location[(bp.file, bp.line)]
            del self._breakpoints[bp_id]
            return True
    
    def toggle(self, bp_id: int) -> bool:
        """Toggle breakpoint enabled state."""
        with self._lock:
            if bp_id in self._breakpoints:
                self._breakpoints[bp_id].enabled = not self._breakpoints[bp_id].enabled
                return True
            return False
    
    def get(self, bp_id: int) -> Breakpoint | None:
        """Get breakpoint by ID."""
        return self._breakpoints.get(bp_id)
    
    def get_at(self, file: str, line: int) -> Breakpoint | None:
        """Get breakpoint at file:line."""
        key = (file, line)
        if key in self._by_location:
            return self._breakpoints[self._by_location[key]]
        return None
    
    def get_all(self) -> list[Breakpoint]:
        """Get all breakpoints."""
        return list(self._breakpoints.values())
    
    def clear(self) -> None:
        """Remove all breakpoints."""
        with self._lock:
            self._breakpoints.clear()
            self._by_location.clear()
    
    def has_breakpoint(self, file: str, line: int) -> bool:
        """Check if there's an enabled breakpoint at location."""
        bp = self.get_at(file, line)
        return bp is not None and bp.enabled


class Debugger:
    """
    DSL Script Debugger.
    
    Provides:
    - Breakpoint-based pausing
    - Step over/into/out execution
    - Variable inspection
    - Call stack tracking
    
    Signals (via callbacks):
        on_paused: Called when execution pauses (reason, line)
        on_resumed: Called when execution resumes
        on_step: Called for each step (flow, line, action)
        on_stopped: Called when debugging ends
    """
    
    def __init__(self) -> None:
        self.breakpoints = BreakpointManager()
        self._state = DebugState.IDLE
        self._step_mode: StepMode | None = None
        self._call_stack: list[StackFrame] = []
        self._variables: dict[str, Any] = {}
        self._lock = Lock()
        self._frame_id = 0
        
        # Callbacks
        self._on_paused: Callable[[str, int], None] | None = None
        self._on_resumed: Callable[[], None] | None = None
        self._on_step: Callable[[str, int, str], None] | None = None
        self._on_stopped: Callable[[], None] | None = None
    
    @property
    def state(self) -> DebugState:
        """Get current debug state."""
        return self._state
    
    @property
    def is_paused(self) -> bool:
        """Check if debugger is paused."""
        return self._state == DebugState.PAUSED
    
    @property
    def call_stack(self) -> list[StackFrame]:
        """Get current call stack."""
        return list(self._call_stack)
    
    # ─────────────────────────────────────────────────────────────
    # Callback Registration
    # ─────────────────────────────────────────────────────────────
    
    def on_paused(self, callback: Callable[[str, int], None]) -> None:
        """Register callback for pause events."""
        self._on_paused = callback
    
    def on_resumed(self, callback: Callable[[], None]) -> None:
        """Register callback for resume events."""
        self._on_resumed = callback
    
    def on_step(self, callback: Callable[[str, int, str], None]) -> None:
        """Register callback for step events."""
        self._on_step = callback
    
    def on_stopped(self, callback: Callable[[], None]) -> None:
        """Register callback for stop events."""
        self._on_stopped = callback
    
    # ─────────────────────────────────────────────────────────────
    # Execution Control
    # ─────────────────────────────────────────────────────────────
    
    def start(self) -> None:
        """Start debugging session."""
        self._state = DebugState.RUNNING
        self._call_stack.clear()
        self._variables.clear()
        self._frame_id = 0
    
    def stop(self) -> None:
        """Stop debugging session."""
        self._state = DebugState.IDLE
        self._call_stack.clear()
        if self._on_stopped:
            self._on_stopped()
    
    def continue_execution(self) -> None:
        """Continue execution after pause."""
        if self._state == DebugState.PAUSED:
            self._state = DebugState.RUNNING
            self._step_mode = None
            if self._on_resumed:
                self._on_resumed()
    
    def pause(self) -> None:
        """Pause execution."""
        if self._state == DebugState.RUNNING:
            self._state = DebugState.PAUSED
            if self._on_paused:
                line = self._call_stack[-1].line if self._call_stack else 0
                self._on_paused("user", line)
    
    def step_over(self) -> None:
        """Step over to next line."""
        self._step_mode = StepMode.OVER
        self._state = DebugState.STEPPING
        if self._on_resumed:
            self._on_resumed()
    
    def step_into(self) -> None:
        """Step into function call."""
        self._step_mode = StepMode.INTO
        self._state = DebugState.STEPPING
        if self._on_resumed:
            self._on_resumed()
    
    def step_out(self) -> None:
        """Step out of current function."""
        self._step_mode = StepMode.OUT
        self._state = DebugState.STEPPING
        if self._on_resumed:
            self._on_resumed()
    
    # ─────────────────────────────────────────────────────────────
    # Execution Hooks (called by runner)
    # ─────────────────────────────────────────────────────────────
    
    def enter_flow(self, flow_name: str, file: str, line: int) -> None:
        """Called when entering a flow."""
        self._frame_id += 1
        frame = StackFrame(
            id=self._frame_id,
            name=flow_name,
            file=file,
            line=line,
        )
        self._call_stack.append(frame)
    
    def exit_flow(self) -> None:
        """Called when exiting a flow."""
        if self._call_stack:
            self._call_stack.pop()
    
    def before_step(self, file: str, line: int, action_type: str) -> bool:
        """
        Called before executing a step.
        
        Returns True if execution should continue, False to pause.
        """
        if self._state == DebugState.IDLE:
            return True
        
        # Update current frame
        if self._call_stack:
            self._call_stack[-1].line = line
        
        # Callback
        if self._on_step:
            flow_name = self._call_stack[-1].name if self._call_stack else "main"
            self._on_step(flow_name, line, action_type)
        
        # Check breakpoint
        if self.breakpoints.has_breakpoint(file, line):
            bp = self.breakpoints.get_at(file, line)
            if bp:
                bp.hit_count += 1
                self._state = DebugState.PAUSED
                if self._on_paused:
                    self._on_paused("breakpoint", line)
                return False
        
        # Check step mode
        if self._state == DebugState.STEPPING:
            if self._step_mode == StepMode.OVER:
                self._state = DebugState.PAUSED
                if self._on_paused:
                    self._on_paused("step", line)
                return False
        
        return True
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable value (for inspection)."""
        self._variables[name] = value
        if self._call_stack:
            self._call_stack[-1].locals[name] = value
    
    # ─────────────────────────────────────────────────────────────
    # Inspection
    # ─────────────────────────────────────────────────────────────
    
    def get_variables(self, frame_id: int | None = None) -> list[Variable]:
        """Get variables for a stack frame."""
        if frame_id is None and self._call_stack:
            frame = self._call_stack[-1]
        elif frame_id:
            frame = next((f for f in self._call_stack if f.id == frame_id), None)
        else:
            frame = None
        
        if not frame:
            return []
        
        return [
            Variable(
                name=name,
                value=value,
                type=type(value).__name__,
                expandable=isinstance(value, (dict, list)),
            )
            for name, value in frame.locals.items()
        ]
    
    def evaluate(self, expression: str) -> tuple[Any, str | None]:
        """
        Evaluate an expression in the current context.
        
        Returns (value, error_message).
        """
        try:
            # Simple evaluation with current variables
            result = eval(expression, {"__builtins__": {}}, self._variables)
            return result, None
        except Exception as e:
            return None, str(e)
