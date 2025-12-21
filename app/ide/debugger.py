"""
RetroAuto v2 - Visual Debugger

Debugger foundation for RetroScript with breakpoints and step execution.
Part of RetroScript Phase 5 - Advanced IDE Features.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from core.dsl.ast import ASTNode, Program


class DebugState(Enum):
    """Debugger execution state."""

    STOPPED = auto()  # Not running
    RUNNING = auto()  # Running normally
    PAUSED = auto()  # Paused at breakpoint
    STEPPING = auto()  # Single-step mode


class StepMode(Enum):
    """Step execution modes."""

    STEP_IN = auto()  # Step into function calls
    STEP_OVER = auto()  # Step over function calls
    STEP_OUT = auto()  # Step out of current function


@dataclass
class Breakpoint:
    """A debug breakpoint."""

    line: int
    file: str = ""
    condition: str | None = None  # Optional conditional expression
    enabled: bool = True
    hit_count: int = 0


@dataclass
class StackFrame:
    """A call stack frame."""

    name: str  # Flow/function name
    line: int
    file: str = ""
    locals: dict[str, Any] = field(default_factory=dict)


@dataclass
class DebugContext:
    """Current debug context with variables and call stack."""

    variables: dict[str, Any] = field(default_factory=dict)
    stack: list[StackFrame] = field(default_factory=list)
    current_line: int = 0
    current_file: str = ""


class Debugger:
    """Visual debugger for RetroScript.

    Provides:
    - Breakpoint management
    - Step execution (in/over/out)
    - Variable inspection
    - Call stack navigation

    Usage:
        debugger = Debugger()
        debugger.add_breakpoint(10)
        debugger.on_break = lambda ctx: print(f"Hit line {ctx.current_line}")
        debugger.start(program)
    """

    def __init__(self) -> None:
        self._breakpoints: dict[int, Breakpoint] = {}  # line -> breakpoint
        self._state = DebugState.STOPPED
        self._step_mode: StepMode | None = None
        self._context = DebugContext()

        # Callbacks
        self.on_break: Callable[[DebugContext], None] | None = None
        self.on_step: Callable[[DebugContext], None] | None = None
        self.on_variable_change: Callable[[str, Any], None] | None = None

    # ─────────────────────────────────────────────────────────────
    # Breakpoint Management
    # ─────────────────────────────────────────────────────────────

    def add_breakpoint(
        self,
        line: int,
        file: str = "",
        condition: str | None = None,
    ) -> Breakpoint:
        """Add a breakpoint at the specified line."""
        bp = Breakpoint(line=line, file=file, condition=condition)
        self._breakpoints[line] = bp
        return bp

    def remove_breakpoint(self, line: int) -> bool:
        """Remove breakpoint at line. Returns True if removed."""
        if line in self._breakpoints:
            del self._breakpoints[line]
            return True
        return False

    def toggle_breakpoint(self, line: int) -> bool:
        """Toggle breakpoint at line. Returns new state."""
        if line in self._breakpoints:
            self._breakpoints[line].enabled = not self._breakpoints[line].enabled
            return self._breakpoints[line].enabled
        else:
            self.add_breakpoint(line)
            return True

    def get_breakpoints(self) -> list[Breakpoint]:
        """Get all breakpoints."""
        return list(self._breakpoints.values())

    def clear_breakpoints(self) -> None:
        """Remove all breakpoints."""
        self._breakpoints.clear()

    def has_breakpoint(self, line: int, enabled_only: bool = True) -> bool:
        """Check if line has a (enabled) breakpoint."""
        if line not in self._breakpoints:
            return False
        bp = self._breakpoints[line]
        return bp.enabled if enabled_only else True

    # ─────────────────────────────────────────────────────────────
    # Execution Control
    # ─────────────────────────────────────────────────────────────

    def start(self, program: Program | None = None) -> None:
        """Start debugging session."""
        self._state = DebugState.RUNNING
        self._context = DebugContext()
        if program:
            self._context.stack.append(StackFrame(
                name="<main>",
                line=1,
            ))

    def stop(self) -> None:
        """Stop debugging session."""
        self._state = DebugState.STOPPED
        self._step_mode = None

    def pause(self) -> None:
        """Pause execution."""
        self._state = DebugState.PAUSED

    def resume(self) -> None:
        """Resume execution from pause."""
        self._state = DebugState.RUNNING
        self._step_mode = None

    def step_in(self) -> None:
        """Step into next statement."""
        self._state = DebugState.STEPPING
        self._step_mode = StepMode.STEP_IN

    def step_over(self) -> None:
        """Step over to next statement."""
        self._state = DebugState.STEPPING
        self._step_mode = StepMode.STEP_OVER

    def step_out(self) -> None:
        """Step out of current function."""
        self._state = DebugState.STEPPING
        self._step_mode = StepMode.STEP_OUT

    # ─────────────────────────────────────────────────────────────
    # Runtime Hooks (called by engine)
    # ─────────────────────────────────────────────────────────────

    def on_line(self, line: int, node: ASTNode | None = None) -> bool:
        """Called before executing each line.

        Returns:
            True to continue, False to pause
        """
        self._context.current_line = line

        # Check for breakpoint
        if self.has_breakpoint(line):
            bp = self._breakpoints[line]
            bp.hit_count += 1

            # Check condition if any
            if bp.condition:
                try:
                    if not self._evaluate_condition(bp.condition):
                        return True  # Condition not met
                except Exception:
                    pass  # Ignore condition errors

            self._state = DebugState.PAUSED
            if self.on_break:
                self.on_break(self._context)
            return False

        # Check for step mode
        if self._state == DebugState.STEPPING:
            self._state = DebugState.PAUSED
            if self.on_step:
                self.on_step(self._context)
            return False

        return True

    def on_enter_flow(self, name: str, line: int) -> None:
        """Called when entering a flow/function."""
        self._context.stack.append(StackFrame(name=name, line=line))

    def on_exit_flow(self) -> None:
        """Called when exiting a flow/function."""
        if self._context.stack:
            self._context.stack.pop()

    def set_variable(self, name: str, value: Any) -> None:
        """Track variable value."""
        old_value = self._context.variables.get(name)
        self._context.variables[name] = value

        if self.on_variable_change and old_value != value:
            self.on_variable_change(name, value)

    # ─────────────────────────────────────────────────────────────
    # Inspection
    # ─────────────────────────────────────────────────────────────

    def get_variables(self) -> dict[str, Any]:
        """Get all tracked variables."""
        return self._context.variables.copy()

    def get_stack(self) -> list[StackFrame]:
        """Get current call stack."""
        return self._context.stack.copy()

    def get_state(self) -> DebugState:
        """Get current debugger state."""
        return self._state

    def get_context(self) -> DebugContext:
        """Get full debug context."""
        return self._context

    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate a breakpoint condition."""
        # Simple evaluation using current variables
        try:
            return bool(eval(condition, {}, self._context.variables))
        except Exception:
            return False
