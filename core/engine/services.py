"""
RetroAuto v2 - Execution Services (Dependency Injection)

Provides a clean dependency injection pattern for the Runner
and other execution-related components.

Phase 3.1.2: Architecture Refinement
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, Any

if TYPE_CHECKING:
    from core.templates import TemplateStore
    from vision.capture import ScreenCapture
    from vision.matcher import Matcher
    from vision.waiter import ImageWaiter
    from input.mouse import MouseController
    from input.keyboard import KeyboardController


class IScreenCapture(Protocol):
    """Protocol for screen capture service."""
    
    def capture_screen(self) -> Any:
        """Capture full screen."""
        ...
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> Any:
        """Capture specific region."""
        ...


class IMatcher(Protocol):
    """Protocol for image matching service."""
    
    def find(self, asset_id: str, roi: Any | None = None) -> Any:
        """Find asset on screen."""
        ...


class ITemplateStore(Protocol):
    """Protocol for template store service."""
    
    def get(self, asset_id: str) -> Any | None:
        """Get template by ID."""
        ...
    
    def __contains__(self, asset_id: str) -> bool:
        """Check if template exists."""
        ...


class IMouseController(Protocol):
    """Protocol for mouse control service."""
    
    def click(self, x: int, y: int) -> None:
        """Click at position."""
        ...
    
    def move(self, x: int, y: int) -> None:
        """Move mouse to position."""
        ...


class IKeyboardController(Protocol):
    """Protocol for keyboard control service."""
    
    def type_text(self, text: str, paste_mode: bool = True) -> None:
        """Type text."""
        ...
    
    def hotkey(self, keys: list[str]) -> None:
        """Press hotkey combination."""
        ...


@dataclass
class ExecutionServices:
    """
    Container for all services needed by the script runner.
    
    Using dependency injection allows for:
    - Easy testing with mocks
    - Swappable implementations
    - Clear dependencies
    
    Usage:
        # Production
        services = ExecutionServices.create_default()
        runner = Runner(services=services)
        
        # Testing
        mock_services = ExecutionServices(
            matcher=MockMatcher(),
            templates=MockTemplates(),
            ...
        )
        runner = Runner(services=mock_services)
    """
    
    # Vision services
    screen_capture: IScreenCapture | None = None
    matcher: IMatcher | None = None
    templates: ITemplateStore | None = None
    
    # Input services
    mouse: IMouseController | None = None
    keyboard: IKeyboardController | None = None
    
    # Configuration
    enable_logging: bool = True
    enable_screenshots: bool = False
    
    @classmethod
    def create_default(cls) -> ExecutionServices:
        """
        Create ExecutionServices with default implementations.
        
        Returns:
            ExecutionServices with real implementations
        """
        from core.templates import TemplateStore
        from vision.capture import ScreenCapture
        from vision.matcher import Matcher
        from input.mouse import MouseController
        from input.keyboard import KeyboardController
        
        return cls(
            screen_capture=ScreenCapture(),
            matcher=Matcher(),
            templates=TemplateStore(),
            mouse=MouseController(),
            keyboard=KeyboardController(),
        )
    
    @classmethod
    def create_for_testing(cls) -> ExecutionServices:
        """
        Create ExecutionServices with mock/stub implementations.
        
        Returns:
            ExecutionServices for testing (no real I/O)
        """
        return cls(
            screen_capture=None,
            matcher=None,
            templates=None,
            mouse=None,
            keyboard=None,
            enable_logging=False,
        )
    
    def validate(self) -> list[str]:
        """
        Validate that all required services are available.
        
        Returns:
            List of missing service names
        """
        missing = []
        
        if self.matcher is None:
            missing.append("matcher")
        if self.templates is None:
            missing.append("templates")
        if self.mouse is None:
            missing.append("mouse")
        if self.keyboard is None:
            missing.append("keyboard")
        
        return missing


# ─────────────────────────────────────────────────────────────
# Singleton default services (for backward compatibility)
# ─────────────────────────────────────────────────────────────

_default_services: ExecutionServices | None = None


def get_default_services() -> ExecutionServices:
    """Get or create default execution services singleton."""
    global _default_services
    if _default_services is None:
        _default_services = ExecutionServices.create_default()
    return _default_services


def set_default_services(services: ExecutionServices) -> None:
    """Set custom default services (for testing)."""
    global _default_services
    _default_services = services
