"""
RetroAuto v2 - Built-in Functions

Standard library functions for RetroScript execution.
Part of RetroScript Phase 9 - Script Execution Engine.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.engine.scope import ExecutionContext


from core.security.policy import Permission


@dataclass
class BuiltinFunction:
    """A built-in function definition."""

    name: str
    func: Callable[..., Any]
    min_args: int = 0
    max_args: int = -1  # -1 = unlimited
    description: str = ""
    permission: Permission = Permission.NONE


class BuiltinRegistry:
    """Registry of built-in functions.

    Usage:
        registry = BuiltinRegistry()
        result = registry.call("log", "Hello, world!")
    """

    def __init__(self) -> None:
        self._functions: dict[str, BuiltinFunction] = {}
        self._context: ExecutionContext | None = None
        self._register_defaults()

    def set_context(self, context: ExecutionContext) -> None:
        """Set execution context for builtins that need it."""
        self._context = context

    def register(
        self,
        name: str,
        func: Callable[..., Any],
        min_args: int = 0,
        max_args: int = -1,
        description: str = "",
        permission: Permission = Permission.NONE,
    ) -> None:
        """Register a built-in function."""
        self._functions[name] = BuiltinFunction(
            name=name,
            func=func,
            min_args=min_args,
            max_args=max_args,
            description=description,
            permission=permission,
        )

    def has(self, name: str) -> bool:
        """Check if function exists."""
        return name in self._functions

    def call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Call a built-in function.

        Raises:
            NameError: If function not found
            TypeError: If wrong number of arguments
            SecurityViolation: If permission denied
        """
        if name not in self._functions:
            raise NameError(f"Unknown function: {name}")

        builtin = self._functions[name]

        # Security Check
        if builtin.permission != Permission.NONE and self._context:
            self._context.policy.check(builtin.permission)

        # Check argument count
        if len(args) < builtin.min_args:
            raise TypeError(
                f"{name}() requires at least {builtin.min_args} arguments, " f"got {len(args)}"
            )
        if builtin.max_args >= 0 and len(args) > builtin.max_args:
            raise TypeError(
                f"{name}() takes at most {builtin.max_args} arguments, " f"got {len(args)}"
            )

        return builtin.func(*args, **kwargs)

    def get_all(self) -> list[BuiltinFunction]:
        """Get all registered functions."""
        return list(self._functions.values())

    def _register_defaults(self) -> None:
        """Register default built-in functions."""
        # ─────────────────────────────────────────────────────
        # Output functions
        # ─────────────────────────────────────────────────────
        self.register("log", self._log, 1, -1, "Log a message")
        self.register("print", self._log, 1, -1, "Print a message")

        # ─────────────────────────────────────────────────────
        # Time functions
        # ─────────────────────────────────────────────────────
        self.register("sleep", self._sleep, 1, 1, "Sleep for duration")
        self.register("timestamp", self._timestamp, 0, 0, "Get current timestamp")
        self.register("time", self._time, 0, 0, "Get current time in seconds")

        # ─────────────────────────────────────────────────────
        # Math functions
        # ─────────────────────────────────────────────────────
        self.register("random", self._random, 0, 2, "Random number")
        self.register("abs", abs, 1, 1, "Absolute value")
        self.register("min", min, 2, -1, "Minimum value")
        self.register("max", max, 2, -1, "Maximum value")
        self.register("round", round, 1, 2, "Round number")
        self.register("floor", self._floor, 1, 1, "Floor value")
        self.register("ceil", self._ceil, 1, 1, "Ceiling value")

        # ─────────────────────────────────────────────────────
        # String functions
        # ─────────────────────────────────────────────────────
        self.register("str", str, 1, 1, "Convert to string")
        self.register("int", self._to_int, 1, 1, "Convert to integer")
        self.register("float", float, 1, 1, "Convert to float")
        self.register("len", len, 1, 1, "Length of string/list")
        self.register("upper", self._upper, 1, 1, "Uppercase string")
        self.register("lower", self._lower, 1, 1, "Lowercase string")
        self.register("trim", self._trim, 1, 1, "Trim whitespace")
        self.register("split", self._split, 1, 2, "Split string")
        self.register("join", self._join, 2, 2, "Join list with separator")
        self.register("contains", self._contains, 2, 2, "Check if contains")
        self.register("replace", self._replace, 3, 3, "Replace in string")

        # ─────────────────────────────────────────────────────
        # List functions
        # ─────────────────────────────────────────────────────
        self.register("range", self._range, 1, 3, "Generate range")
        self.register("list", list, 0, 1, "Create list")
        self.register("append", self._append, 2, 2, "Append to list")
        self.register("pop", self._pop, 1, 2, "Pop from list")
        self.register("first", self._first, 1, 1, "Get first element")
        self.register("last", self._last, 1, 1, "Get last element")

        # ─────────────────────────────────────────────────────
        # Type checking
        # ─────────────────────────────────────────────────────
        self.register("type", self._type, 1, 1, "Get type name")
        self.register("is_null", self._is_null, 1, 1, "Check if null")
        self.register("is_number", self._is_number, 1, 1, "Check if number")
        self.register("is_string", self._is_string, 1, 1, "Check if string")
        self.register("is_list", self._is_list, 1, 1, "Check if list")

        # ─────────────────────────────────────────────────────
        # Automation stubs (to be implemented by engine)
        # ─────────────────────────────────────────────────────
        self.register("find", self._find_stub, 1, 2, "Find image on screen", Permission.SCREEN_READ)
        self.register("wait", self._wait_stub, 1, 2, "Wait for image", Permission.SCREEN_READ)
        self.register(
            "click", self._click_stub, 1, 3, "Click at position", Permission.INPUT_CONTROL
        )
        self.register("move", self._move_stub, 2, 2, "Move mouse", Permission.INPUT_CONTROL)
        self.register("press", self._press_stub, 1, 1, "Press key", Permission.INPUT_CONTROL)
        self.register("type", self._type_text_stub, 1, 1, "Type text", Permission.INPUT_CONTROL)
        self.register("scroll", self._scroll_stub, 1, 1, "Scroll wheel", Permission.INPUT_CONTROL)
        self.register("drag", self._drag_stub, 4, 4, "Drag from to", Permission.INPUT_CONTROL)
        self.register(
            "hotkey", self._hotkey_stub, 1, 1, "Key combination", Permission.INPUT_CONTROL
        )

    # ─────────────────────────────────────────────────────────────
    # Implementation functions
    # ─────────────────────────────────────────────────────────────

    def _log(self, *args: Any) -> None:
        """Log message to console."""
        message = " ".join(str(a) for a in args)
        print(f"[LOG] {message}")

    def _sleep(self, duration: int | float) -> None:
        """Sleep for duration in milliseconds."""
        # Handle duration - could be ms or have suffix
        if isinstance(duration, str):
            duration = self._parse_duration(duration)
        elif isinstance(duration, (int, float)):  # noqa: SIM102
            # Assume milliseconds if small, seconds if < 1
            if duration > 100:  # Likely milliseconds
                duration = duration / 1000
        time.sleep(duration)

    def _timestamp(self) -> str:
        """Get current timestamp."""
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def _time(self) -> float:
        """Get current time in seconds."""
        return time.time()

    def _random(self, *args: Any) -> int | float:
        """Generate random number."""
        if len(args) == 0:
            return random.random()
        elif len(args) == 1:
            return random.randint(0, int(args[0]))
        else:
            return random.randint(int(args[0]), int(args[1]))

    def _floor(self, x: float) -> int:
        """Floor value."""
        import math

        return math.floor(x)

    def _ceil(self, x: float) -> int:
        """Ceiling value."""
        import math

        return math.ceil(x)

    def _to_int(self, x: Any) -> int:
        """Convert to integer."""
        if isinstance(x, str):
            # Handle duration strings
            if x.endswith("ms"):
                return int(x[:-2])
            elif x.endswith("s"):
                return int(x[:-1]) * 1000
        return int(x)

    def _upper(self, s: str) -> str:
        return str(s).upper()

    def _lower(self, s: str) -> str:
        return str(s).lower()

    def _trim(self, s: str) -> str:
        return str(s).strip()

    def _split(self, s: str, sep: str = " ") -> list[str]:
        return str(s).split(sep)

    def _join(self, lst: list, sep: str) -> str:
        return sep.join(str(x) for x in lst)

    def _contains(self, haystack: Any, needle: Any) -> bool:
        return needle in haystack

    def _replace(self, s: str, old: str, new: str) -> str:
        return str(s).replace(old, new)

    def _range(self, *args: Any) -> list[int]:
        """Generate range as list."""
        if len(args) == 1:
            return list(range(int(args[0])))
        elif len(args) == 2:
            return list(range(int(args[0]), int(args[1])))
        else:
            return list(range(int(args[0]), int(args[1]), int(args[2])))

    def _append(self, lst: list, item: Any) -> list:
        """Append to list and return it."""
        lst.append(item)
        return lst

    def _pop(self, lst: list, index: int = -1) -> Any:
        """Pop from list."""
        return lst.pop(index)

    def _first(self, lst: list) -> Any:
        """Get first element."""
        return lst[0] if lst else None

    def _last(self, lst: list) -> Any:
        """Get last element."""
        return lst[-1] if lst else None

    def _type(self, x: Any) -> str:
        """Get type name."""
        if x is None:
            return "null"
        return type(x).__name__

    def _is_null(self, x: Any) -> bool:
        return x is None

    def _is_number(self, x: Any) -> bool:
        return isinstance(x, (int, float))

    def _is_string(self, x: Any) -> bool:
        return isinstance(x, str)

    def _is_list(self, x: Any) -> bool:
        return isinstance(x, list)

    def _parse_duration(self, duration: str) -> float:
        """Parse duration string to seconds."""
        duration = str(duration).strip().lower()
        if duration.endswith("ms"):
            return float(duration[:-2]) / 1000
        elif duration.endswith("s"):
            return float(duration[:-1])
        elif duration.endswith("m"):
            return float(duration[:-1]) * 60
        elif duration.endswith("h"):
            return float(duration[:-1]) * 3600
        return float(duration)

    # ─────────────────────────────────────────────────────────────
    # Automation stubs (replaced by actual engine)
    # ─────────────────────────────────────────────────────────────

    def _find_stub(self, target: str, **kwargs: Any) -> dict[str, Any] | None:
        """Stub for find - returns mock result."""
        print(f"[STUB] find({target})")
        return {"x": 100, "y": 100, "score": 0.95}

    def _wait_stub(self, target: str, timeout: Any = "10s") -> dict[str, Any] | None:
        """Stub for wait."""
        print(f"[STUB] wait({target}, timeout={timeout})")
        return {"x": 100, "y": 100, "score": 0.95}

    def _click_stub(self, x: int, y: int | None = None, button: str = "left") -> None:
        """Stub for click."""
        if y is None and isinstance(x, dict):
            # click($result) where result is {x, y}
            y = x.get("y", 0)
            x = x.get("x", 0)
        print(f"[STUB] click({x}, {y}, button={button})")

    def _move_stub(self, x: int, y: int) -> None:
        """Stub for move."""
        print(f"[STUB] move({x}, {y})")

    def _press_stub(self, key: str) -> None:
        """Stub for press."""
        print(f"[STUB] press({key})")

    def _type_text_stub(self, text: str) -> None:
        """Stub for type."""
        print(f"[STUB] type({text})")

    def _scroll_stub(self, amount: int) -> None:
        """Stub for scroll."""
        print(f"[STUB] scroll({amount})")

    def _drag_stub(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Stub for drag."""
        print(f"[STUB] drag({x1}, {y1}, {x2}, {y2})")

    def _hotkey_stub(self, keys: str) -> None:
        """Stub for hotkey."""
        print(f"[STUB] hotkey({keys})")


# Global registry instance
_default_registry = BuiltinRegistry()


def get_builtins() -> BuiltinRegistry:
    """Get the default builtin registry."""
    return _default_registry
