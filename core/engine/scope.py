"""
RetroAuto v2 - Scope Manager

Variable scoping and lookup for RetroScript execution.
Part of RetroScript Phase 9 - Script Execution Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Scope:
    """A single scope level."""

    name: str  # Scope name (e.g., "global", "flow:main")
    variables: dict[str, Any] = field(default_factory=dict)
    parent: "Scope | None" = None
    is_flow: bool = False  # True if this is a flow scope

    def get(self, name: str) -> tuple[Any, bool]:
        """Get variable value.

        Returns:
            Tuple of (value, found)
        """
        if name in self.variables:
            return self.variables[name], True
        if self.parent:
            return self.parent.get(name)
        return None, False

    def set(self, name: str, value: Any) -> None:
        """Set variable in this scope."""
        self.variables[name] = value

    def update(self, name: str, value: Any) -> bool:
        """Update existing variable, searching up the scope chain.

        Returns:
            True if variable was found and updated
        """
        if name in self.variables:
            self.variables[name] = value
            return True
        if self.parent:
            return self.parent.update(name, value)
        return False

    def has(self, name: str) -> bool:
        """Check if variable exists in scope chain."""
        if name in self.variables:
            return True
        if self.parent:
            return self.parent.has(name)
        return False


class ScopeManager:
    """Manages variable scopes for script execution.

    Usage:
        scope = ScopeManager()
        scope.define("x", 10)
        scope.push("flow:main")
        scope.define("local_var", 20)
        print(scope.get("x"))  # 10 (from global)
        scope.pop()
    """

    def __init__(self) -> None:
        self._global = Scope(name="global")
        self._stack: list[Scope] = [self._global]

    @property
    def current(self) -> Scope:
        """Get current scope."""
        return self._stack[-1]

    @property
    def global_scope(self) -> Scope:
        """Get global scope."""
        return self._global

    def push(self, name: str, is_flow: bool = False) -> Scope:
        """Push a new scope onto the stack.

        Args:
            name: Scope name
            is_flow: Whether this is a flow scope

        Returns:
            The new scope
        """
        new_scope = Scope(
            name=name,
            parent=self.current,
            is_flow=is_flow,
        )
        self._stack.append(new_scope)
        return new_scope

    def pop(self) -> Scope | None:
        """Pop the current scope.

        Returns:
            The popped scope, or None if at global
        """
        if len(self._stack) > 1:
            return self._stack.pop()
        return None

    def define(self, name: str, value: Any) -> None:
        """Define a new variable in current scope."""
        self.current.set(name, value)

    def assign(self, name: str, value: Any) -> bool:
        """Assign to existing variable, or create in current scope.

        Returns:
            True if existing variable was updated
        """
        # Try to update existing
        if self.current.update(name, value):
            return True
        # Create new in current scope
        self.current.set(name, value)
        return False

    def get(self, name: str) -> Any:
        """Get variable value.

        Raises:
            NameError: If variable not found
        """
        value, found = self.current.get(name)
        if not found:
            raise NameError(f"Undefined variable: {name}")
        return value

    def get_or_default(self, name: str, default: Any = None) -> Any:
        """Get variable value or default."""
        value, found = self.current.get(name)
        return value if found else default

    def has(self, name: str) -> bool:
        """Check if variable exists."""
        return self.current.has(name)

    def set_global(self, name: str, value: Any) -> None:
        """Set variable in global scope."""
        self._global.set(name, value)

    def get_global(self, name: str) -> Any:
        """Get variable from global scope."""
        value, found = self._global.get(name)
        if not found:
            raise NameError(f"Undefined global: {name}")
        return value

    def depth(self) -> int:
        """Get current scope depth."""
        return len(self._stack)

    def get_all_locals(self) -> dict[str, Any]:
        """Get all local variables in current scope."""
        return self.current.variables.copy()

    def get_all_globals(self) -> dict[str, Any]:
        """Get all global variables."""
        return self._global.variables.copy()

    def clear_locals(self) -> None:
        """Clear current scope variables."""
        self.current.variables.clear()

    def reset(self) -> None:
        """Reset to initial state."""
        self._global = Scope(name="global")
        self._stack = [self._global]


class ExecutionContext:
    """Execution context combining scope and control state.

    Provides:
    - Variable scope management
    - Control flow flags (break, continue, return)
    - Flow call stack
    """

    def __init__(self) -> None:
        self.scope = ScopeManager()
        self._return_value: Any = None
        self._should_return = False
        self._should_break = False
        self._should_continue = False
        self._call_stack: list[str] = []

    def enter_flow(self, name: str) -> None:
        """Enter a new flow context."""
        self.scope.push(f"flow:{name}", is_flow=True)
        self._call_stack.append(name)

    def exit_flow(self) -> None:
        """Exit current flow context."""
        self.scope.pop()
        if self._call_stack:
            self._call_stack.pop()
        self._should_return = False

    def set_return(self, value: Any = None) -> None:
        """Set return value and flag."""
        self._return_value = value
        self._should_return = True

    def get_return(self) -> Any:
        """Get and clear return value."""
        value = self._return_value
        self._return_value = None
        return value

    def should_return(self) -> bool:
        """Check if should return from current flow."""
        return self._should_return

    def set_break(self) -> None:
        """Set break flag for loop."""
        self._should_break = True

    def clear_break(self) -> bool:
        """Clear and return break flag."""
        was_break = self._should_break
        self._should_break = False
        return was_break

    def should_break(self) -> bool:
        """Check if should break from loop."""
        return self._should_break

    def set_continue(self) -> None:
        """Set continue flag for loop."""
        self._should_continue = True

    def clear_continue(self) -> bool:
        """Clear and return continue flag."""
        was_continue = self._should_continue
        self._should_continue = False
        return was_continue

    def should_continue(self) -> bool:
        """Check if should continue loop."""
        return self._should_continue

    def get_call_stack(self) -> list[str]:
        """Get current call stack."""
        return self._call_stack.copy()

    def current_flow(self) -> str | None:
        """Get current flow name."""
        return self._call_stack[-1] if self._call_stack else None
