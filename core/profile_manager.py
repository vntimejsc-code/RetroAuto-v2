"""
RetroAuto v2 - Game Profile Manager

Manage profiles with preset settings for different games/applications.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from infra import get_logger

logger = get_logger("ProfileManager")


@dataclass
class GameProfile:
    """
    Profile preset for a specific game/application.
    
    Contains default settings like:
    - Window title pattern
    - Default ROI
    - Threshold adjustments
    - Hotkey mappings
    - Custom variables
    """

    name: str
    description: str = ""
    
    # Target application
    window_title: str = ""
    process_name: str = ""
    
    # Vision settings
    default_threshold: float = 0.8
    grayscale: bool = True
    default_roi: dict[str, int] | None = None  # x, y, w, h
    
    # Timing settings
    default_delay_ms: int = 100
    click_delay_ms: int = 50
    
    # Hotkey overrides
    hotkey_start: str = "F5"
    hotkey_stop: str = "F6"
    hotkey_pause: str = "F7"
    
    # Screen resolution (for coordinate scaling)
    target_width: int = 1920
    target_height: int = 1080
    
    # Custom variables for scripts
    variables: dict[str, Any] = field(default_factory=dict)
    
    # Script-specific settings
    scripts: list[str] = field(default_factory=list)  # Associated script paths


class ProfileManager:
    """
    Manage game profiles.
    
    Profiles are stored as JSON files in profiles directory.
    
    Usage:
        manager = ProfileManager(Path("./profiles"))
        
        # Create profile
        profile = manager.create("MU Online", window_title="MU Legend")
        profile.default_threshold = 0.85
        manager.save(profile)
        
        # Load profile
        profile = manager.load("MU Online")
        
        # Apply to script
        manager.apply_to_script(profile, script)
    """

    def __init__(self, profiles_dir: Path) -> None:
        """
        Initialize profile manager.
        
        Args:
            profiles_dir: Directory to store profile files
        """
        self._dir = profiles_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._profiles: dict[str, GameProfile] = {}
        self._load_all()

    def _profile_path(self, name: str) -> Path:
        """Get path for profile file."""
        safe_name = "".join(c if c.isalnum() or c in "_ -" else "_" for c in name)
        return self._dir / f"{safe_name}.json"

    def _load_all(self) -> None:
        """Load all profiles from directory."""
        for path in self._dir.glob("*.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                    profile = GameProfile(**data)
                    self._profiles[profile.name] = profile
            except Exception as e:
                logger.warning("Failed to load profile %s: %s", path, e)

    @property
    def profiles(self) -> list[GameProfile]:
        """Get all profiles."""
        return list(self._profiles.values())

    def get(self, name: str) -> GameProfile | None:
        """Get profile by name."""
        return self._profiles.get(name)

    def create(
        self,
        name: str,
        description: str = "",
        window_title: str = "",
        **kwargs: Any,
    ) -> GameProfile:
        """
        Create new profile.
        
        Args:
            name: Profile name
            description: Profile description
            window_title: Target window title pattern
            **kwargs: Additional profile settings
            
        Returns:
            New GameProfile
        """
        profile = GameProfile(
            name=name,
            description=description,
            window_title=window_title,
            **kwargs,
        )
        self._profiles[name] = profile
        self.save(profile)
        return profile

    def save(self, profile: GameProfile) -> bool:
        """
        Save profile to disk.
        
        Args:
            profile: Profile to save
            
        Returns:
            True if saved successfully
        """
        try:
            path = self._profile_path(profile.name)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(asdict(profile), f, indent=2, ensure_ascii=False)
            self._profiles[profile.name] = profile
            logger.info("Saved profile: %s", profile.name)
            return True
        except Exception as e:
            logger.error("Failed to save profile %s: %s", profile.name, e)
            return False

    def delete(self, name: str) -> bool:
        """
        Delete profile.
        
        Args:
            name: Profile name
            
        Returns:
            True if deleted
        """
        if name not in self._profiles:
            return False

        try:
            path = self._profile_path(name)
            if path.exists():
                path.unlink()
            del self._profiles[name]
            logger.info("Deleted profile: %s", name)
            return True
        except Exception as e:
            logger.error("Failed to delete profile %s: %s", name, e)
            return False

    def duplicate(self, name: str, new_name: str) -> GameProfile | None:
        """
        Duplicate existing profile.
        
        Args:
            name: Source profile name
            new_name: New profile name
            
        Returns:
            New profile or None if source not found
        """
        source = self.get(name)
        if source is None:
            return None

        data = asdict(source)
        data["name"] = new_name
        profile = GameProfile(**data)
        self._profiles[new_name] = profile
        self.save(profile)
        return profile

    def apply_to_script(self, profile: GameProfile, script: Any) -> None:
        """
        Apply profile settings to a script.
        
        Args:
            profile: Profile to apply
            script: Script to modify
        """
        # Apply hotkeys
        if hasattr(script, "hotkeys"):
            script.hotkeys.start = profile.hotkey_start
            script.hotkeys.stop = profile.hotkey_stop
            script.hotkeys.pause = profile.hotkey_pause

        # Apply default threshold to assets
        if hasattr(script, "assets"):
            for asset in script.assets:
                if asset.threshold == 0.8:  # Only if using default
                    asset.threshold = profile.default_threshold
                if profile.grayscale != asset.grayscale:
                    asset.grayscale = profile.grayscale

        logger.info("Applied profile '%s' to script", profile.name)

    def list_profiles(self) -> list[str]:
        """Get list of profile names."""
        return list(self._profiles.keys())


# Preset profiles for common games
PRESET_PROFILES: list[dict[str, Any]] = [
    {
        "name": "MU Online",
        "description": "Settings for MU Online games",
        "window_title": "MU",
        "default_threshold": 0.85,
        "grayscale": True,
        "default_delay_ms": 150,
    },
    {
        "name": "Lineage 2",
        "description": "Settings for Lineage 2",
        "window_title": "Lineage",
        "default_threshold": 0.80,
        "grayscale": False,  # Color important for HP/MP bars
        "default_delay_ms": 100,
    },
    {
        "name": "Web Browser",
        "description": "Settings for web automation",
        "window_title": "Chrome",
        "default_threshold": 0.90,
        "grayscale": False,
        "default_delay_ms": 200,
    },
    {
        "name": "Mobile Emulator",
        "description": "Settings for Android emulators",
        "window_title": "BlueStacks",
        "default_threshold": 0.85,
        "grayscale": True,
        "target_width": 1280,
        "target_height": 720,
    },
]


def create_preset_profiles(manager: ProfileManager) -> None:
    """Create preset profiles if they don't exist."""
    for preset in PRESET_PROFILES:
        if manager.get(preset["name"]) is None:
            manager.create(**preset)
