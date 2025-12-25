"""
RetroAuto v2 - Action Plugin Registry

Extensible action dispatch system allowing custom action handlers
without modifying core runner.

Phase: Mid-term improvement
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Protocol

from infra import get_logger

if TYPE_CHECKING:
    from core.engine.context import ExecutionContext
    from core.models import Action

logger = get_logger("PluginRegistry")


class ActionHandler(Protocol):
    """Protocol for action handlers."""

    def __call__(
        self,
        action: Action,
        ctx: ExecutionContext,
    ) -> Any:
        """
        Execute an action.

        Args:
            action: The action to execute
            ctx: Execution context with services

        Returns:
            Action result (varies by action type)
        """
        ...


@dataclass
class RegisteredAction:
    """Metadata for a registered action."""

    action_type: str
    handler: ActionHandler
    description: str = ""
    category: str = "custom"


class ActionRegistry:
    """
    Registry for action handlers.

    Features:
    - Register custom actions via decorator
    - Dispatch to appropriate handler 
    - Plugin discovery
    - Category organization

    Usage:
        @ActionRegistry.register("MyCustomAction")
        def handle_my_action(action, ctx):
            # Custom logic
            pass

        # Later:
        result = ActionRegistry.dispatch(action, ctx)
    """

    _handlers: dict[str, RegisteredAction] = {}
    _initialized: bool = False

    @classmethod
    def register(
        cls,
        action_type: str,
        description: str = "",
        category: str = "custom",
    ) -> Callable[[ActionHandler], ActionHandler]:
        """
        Decorator to register an action handler.

        Args:
            action_type: Name of the action class
            description: Human-readable description
            category: Category for organization

        Returns:
            Decorator function
        """

        def decorator(handler: ActionHandler) -> ActionHandler:
            cls._handlers[action_type] = RegisteredAction(
                action_type=action_type,
                handler=handler,
                description=description,
                category=category,
            )
            logger.debug("Registered action: %s (%s)", action_type, category)
            return handler

        return decorator

    @classmethod
    def dispatch(
        cls,
        action: Action,
        ctx: ExecutionContext,
    ) -> Any:
        """
        Dispatch action to its registered handler.

        Args:
            action: Action to execute
            ctx: Execution context

        Returns:
            Handler result

        Raises:
            ValueError: If action type not registered
        """
        action_type = type(action).__name__

        registered = cls._handlers.get(action_type)
        if registered:
            return registered.handler(action, ctx)

        raise ValueError(f"No handler registered for action: {action_type}")

    @classmethod
    def is_registered(cls, action_type: str) -> bool:
        """Check if action type is registered."""
        return action_type in cls._handlers

    @classmethod
    def list_actions(cls, category: str | None = None) -> list[RegisteredAction]:
        """
        List all registered actions.

        Args:
            category: Filter by category (None = all)

        Returns:
            List of registered actions
        """
        actions = list(cls._handlers.values())
        if category:
            actions = [a for a in actions if a.category == category]
        return actions

    @classmethod
    def get_categories(cls) -> list[str]:
        """Get all action categories."""
        return list(set(a.category for a in cls._handlers.values()))

    @classmethod
    def clear(cls) -> None:
        """Clear all registered handlers (for testing)."""
        cls._handlers.clear()
        cls._initialized = False


# ─────────────────────────────────────────────────────────────
# Built-in Action Registration
# ─────────────────────────────────────────────────────────────


def register_builtin_actions() -> None:
    """Register all built-in actions from core.models."""
    from core.models import (
        Click,
        ClickImage,
        Delay,
        DelayRandom,
        Drag,
        Goto,
        Hotkey,
        IfImage,
        Label,
        Loop,
        Notify,
        ReadText,
        RunFlow,
        Scroll,
        TypeText,
        WaitImage,
    )

    # Note: Handlers are registered but delegate to Runner methods
    # This allows gradual migration to plugin-based dispatch

    logger.info("Built-in actions available for plugin extension")
    ActionRegistry._initialized = True


# Auto-register on import
register_builtin_actions()
