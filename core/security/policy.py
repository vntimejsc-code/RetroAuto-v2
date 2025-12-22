"""
RetroAuto v2 - Security Sandbox

Defines permissions and security policy for script execution.
Part of RetroScript Phase 15 - Security.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Flag, auto


class Permission(Flag):
    """Security permissions for RetroScript."""

    NONE = 0

    # Filesystem
    FS_READ = auto()
    FS_WRITE = auto()
    FS_DELETE = auto()
    FS_ALL = FS_READ | FS_WRITE | FS_DELETE

    # Network
    NET_HTTP = auto()
    NET_WEBSOCKET = auto()
    NET_ALL = NET_HTTP | NET_WEBSOCKET

    # System
    SHELL_EXEC = auto()  # Run external commands
    ENV_READ = auto()  # Read environment variables

    # Input/Output
    INPUT_CONTROL = auto()  # Mouse/Keyboard simulation
    SCREEN_READ = auto()  # Take screenshots

    # Meta
    UNSAFE = FS_ALL | NET_ALL | SHELL_EXEC | ENV_READ | INPUT_CONTROL | SCREEN_READ


class SecurityViolation(Exception):
    """Raised when a script attempts an unauthorized action."""

    pass


@dataclass
class SecurityPolicy:
    """Policy enforcing permissions for the runtime."""

    permissions: Permission = Permission.NONE
    allowed_domains: set[str] = field(default_factory=set)
    allowed_paths: set[str] = field(default_factory=set)
    max_execution_time_sec: float = 0  # 0 = unlimited
    max_memory_mb: int = 0  # 0 = unlimited

    @classmethod
    def default(cls) -> SecurityPolicy:
        """Default policy (Safe mode)."""
        return cls(permissions=Permission.NONE)

    @classmethod
    def unsafe(cls) -> SecurityPolicy:
        """Unsafe policy (Development mode)."""
        return cls(permissions=Permission.UNSAFE)

    def check(self, permission: Permission) -> None:
        """Check if permission is granted."""
        if not (self.permissions & permission):
            raise SecurityViolation(f"Permission denied: {permission.name}")

    def check_network(self, url: str) -> None:
        """Check if network access to URL is allowed."""
        self.check(Permission.NET_HTTP)
        # In a real implementation, we would check allowed_domains here
        # For now, simplistic check
        pass

    def check_fs(self, path: str, write: bool = False) -> None:
        """Check if filesystem access is allowed."""
        if write:
            self.check(Permission.FS_WRITE)
        else:
            self.check(Permission.FS_READ)
        # Filter by allowed_paths if restricted
