"""
RetroAuto v2 - Plugin System

Plugin infrastructure for extending RetroScript functionality.
Part of RetroScript Phase 4 - Visual IDE + Plugins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class PluginEvent(Enum):
    """Events that plugins can hook into."""

    # Lifecycle events
    ON_LOAD = auto()  # Plugin loaded
    ON_UNLOAD = auto()  # Plugin unloaded

    # Script events
    BEFORE_PARSE = auto()  # Before parsing script
    AFTER_PARSE = auto()  # After parsing script
    BEFORE_RUN = auto()  # Before running script
    AFTER_RUN = auto()  # After running script

    # Execution events
    ON_STEP = auto()  # Each step execution
    ON_ERROR = auto()  # Error occurred
    ON_SUCCESS = auto()  # Script completed successfully

    # IDE events
    ON_FILE_OPEN = auto()  # File opened in IDE
    ON_FILE_SAVE = auto()  # File saved in IDE
    ON_CURSOR_CHANGE = auto()  # Cursor position changed


@dataclass
class PluginInfo:
    """Plugin metadata."""

    name: str
    version: str
    author: str = "Unknown"
    description: str = ""
    dependencies: list[str] = field(default_factory=list)


class Plugin(ABC):
    """Base class for all plugins.

    To create a plugin:
    1. Subclass this class
    2. Implement get_info() and on_load()
    3. Register hooks in on_load()

    Example:
        class MyPlugin(Plugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name="my-plugin",
                    version="1.0.0",
                    description="My awesome plugin"
                )

            def on_load(self, registry: PluginRegistry) -> None:
                registry.add_hook(PluginEvent.BEFORE_RUN, self.before_run)

            def before_run(self, script: Program) -> None:
                print(f"Running script with {len(script.flows)} flows")
    """

    @abstractmethod
    def get_info(self) -> PluginInfo:
        """Return plugin metadata."""
        ...

    @abstractmethod
    def on_load(self, registry: PluginRegistry) -> None:
        """Called when plugin is loaded. Register hooks here."""
        ...

    def on_unload(self) -> None:  # noqa: B027
        """Called when plugin is unloaded. Clean up resources here.

        Override this method in subclasses to perform cleanup.
        """
        ...


class PluginRegistry:
    """Registry for managing plugins and their hooks.

    Usage:
        registry = PluginRegistry()
        registry.load_plugin(MyPlugin())
        registry.trigger(PluginEvent.BEFORE_RUN, script=program)
    """

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._hooks: dict[PluginEvent, list[Callable[..., Any]]] = {
            event: [] for event in PluginEvent
        }

    def load_plugin(self, plugin: Plugin) -> bool:
        """Load a plugin.

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            info = plugin.get_info()

            # Check if already loaded
            if info.name in self._plugins:
                return False

            # Check dependencies
            for dep in info.dependencies:
                if dep not in self._plugins:
                    raise PluginError(f"Missing dependency: {dep}")

            # Store plugin
            self._plugins[info.name] = plugin

            # Let plugin register hooks
            plugin.on_load(self)

            # Trigger load event
            self.trigger(PluginEvent.ON_LOAD, plugin=plugin)

            return True

        except Exception as e:
            raise PluginError(f"Failed to load plugin: {e}") from e

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin by name.

        Returns:
            True if unloaded successfully, False otherwise
        """
        if name not in self._plugins:
            return False

        plugin = self._plugins[name]

        # Trigger unload event first
        self.trigger(PluginEvent.ON_UNLOAD, plugin=plugin)

        # Call cleanup
        plugin.on_unload()

        # Remove from registry
        del self._plugins[name]

        return True

    def add_hook(self, event: PluginEvent, callback: Callable[..., Any]) -> None:
        """Register a hook for an event."""
        self._hooks[event].append(callback)

    def remove_hook(self, event: PluginEvent, callback: Callable[..., Any]) -> None:
        """Remove a hook from an event."""
        if callback in self._hooks[event]:
            self._hooks[event].remove(callback)

    def trigger(self, event: PluginEvent, **kwargs: Any) -> list[Any]:
        """Trigger an event and call all registered hooks.

        Returns:
            List of return values from all hooks
        """
        results = []
        for hook in self._hooks[event]:
            try:
                result = hook(**kwargs)
                results.append(result)
            except Exception as e:
                # Log but don't crash on hook errors
                print(f"Hook error: {e}")
        return results

    def get_plugin(self, name: str) -> Plugin | None:
        """Get a loaded plugin by name."""
        return self._plugins.get(name)

    def list_plugins(self) -> list[PluginInfo]:
        """List all loaded plugins."""
        return [p.get_info() for p in self._plugins.values()]


class PluginError(Exception):
    """Error during plugin operations."""

    pass
