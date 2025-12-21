"""
RetroAuto v2 - Configuration management.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application-wide configuration."""

    # Paths
    log_dir: Path = Field(default_factory=lambda: Path.home() / ".retroauto" / "logs")
    projects_dir: Path = Field(default_factory=lambda: Path.home() / ".retroauto" / "projects")

    # Vision defaults
    default_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    default_poll_ms: int = Field(default=100, ge=10)
    default_timeout_ms: int = Field(default=10000, ge=0)
    grayscale_matching: bool = True

    # Input defaults
    paste_mode: bool = True  # Use clipboard for Vietnamese support
    click_interval_ms: int = Field(default=80, ge=0)

    # Engine defaults
    interrupt_poll_ms: int = Field(default=200, ge=50)
    backoff_max_ms: int = Field(default=1000, ge=100)

    # Hotkeys
    hotkey_start: str = "F5"
    hotkey_stop: str = "F6"
    hotkey_pause: str = "F7"

    model_config = {"validate_assignment": True}


class ProjectConfig(BaseModel):
    """Per-project configuration stored in script.yaml."""

    name: str = "Untitled"
    version: str = "1.0"
    author: str = ""
    description: str = ""

    # Override app defaults
    overrides: dict[str, Any] = Field(default_factory=dict)


# Global config instance
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get global app config (lazy initialized)."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def set_config(config: AppConfig) -> None:
    """Set global app config."""
    global _config
    _config = config
