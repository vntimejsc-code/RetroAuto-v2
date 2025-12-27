"""
RetroAuto v2 - Progressive Disclosure Manager

Manages panel visibility based on user expertise level.
Beginner mode shows essential panels only, Expert mode unlocks all.

Features:
- Two modes: Beginner (simplified) and Expert (full)
- Persistent preference via QSettings
- Panel groups: Essential, Advanced, Debug
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List
from PySide6.QtCore import QSettings, QObject, Signal
from PySide6.QtWidgets import QWidget


class UserLevel(Enum):
    """User expertise levels."""
    BEGINNER = "beginner"
    EXPERT = "expert"


# ═══════════════════════════════════════════════════════════════════════════
# PANEL CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════

class PanelCategory(Enum):
    """Panel categories for progressive disclosure."""
    ESSENTIAL = "essential"      # Always visible
    STANDARD = "standard"        # Visible in Beginner+
    ADVANCED = "advanced"        # Expert only
    DEBUG = "debug"              # Expert + Debug mode only


# Default panel visibility configuration
PANEL_CONFIG: Dict[str, Dict] = {
    # Essential panels - always visible
    "editor": {
        "category": PanelCategory.ESSENTIAL,
        "name": "Code Editor",
        "tooltip": "Main code editing area",
    },
    
    # Standard panels - visible in Beginner mode
    "explorer": {
        "category": PanelCategory.STANDARD,
        "name": "Project Explorer",
        "tooltip": "Browse project files",
    },
    "output": {
        "category": PanelCategory.STANDARD,
        "name": "Output",
        "tooltip": "Script output and logs",
    },
    
    # Advanced panels - Expert mode only
    "inspector": {
        "category": PanelCategory.ADVANCED,
        "name": "Inspector",
        "tooltip": "Property inspector for selected items",
    },
    "interrupts": {
        "category": PanelCategory.ADVANCED,
        "name": "Interrupts",
        "tooltip": "Configure interrupt rules",
    },
    "structure": {
        "category": PanelCategory.ADVANCED,
        "name": "Structure",
        "tooltip": "Document outline and navigation",
    },
    "assets": {
        "category": PanelCategory.ADVANCED,
        "name": "Assets",
        "tooltip": "Manage image assets",
    },
    
    # Debug panels - Expert + Debug mode
    "debug": {
        "category": PanelCategory.DEBUG,
        "name": "Debug Panel",
        "tooltip": "Debugging controls and breakpoints",
    },
    "variables": {
        "category": PanelCategory.DEBUG,
        "name": "Variable Watch",
        "tooltip": "Watch variable values during execution",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# PROGRESSIVE DISCLOSURE MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class ProgressiveDisclosureManager(QObject):
    """Manages panel visibility based on user level."""
    
    # Signals
    level_changed = Signal(str)  # Emitted when user level changes
    
    SETTINGS_KEY = "ui/user_level"
    
    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("RetroAuto", "RetroAuto")
        self._current_level = self._load_level()
        self._registered_panels: Dict[str, QWidget] = {}
        self._panel_configs = PANEL_CONFIG.copy()
    
    def _load_level(self) -> UserLevel:
        """Load saved user level."""
        saved = self._settings.value(self.SETTINGS_KEY, "beginner")
        try:
            return UserLevel(saved)
        except ValueError:
            return UserLevel.BEGINNER
    
    @property
    def current_level(self) -> UserLevel:
        """Get current user level."""
        return self._current_level
    
    @property
    def is_expert(self) -> bool:
        """Check if in expert mode."""
        return self._current_level == UserLevel.EXPERT
    
    @property
    def level_display_name(self) -> str:
        """Get display name for current level."""
        names = {
            UserLevel.BEGINNER: "Beginner (Simplified)",
            UserLevel.EXPERT: "Expert (Full)",
        }
        return names.get(self._current_level, "Beginner")
    
    def set_level(self, level: UserLevel) -> None:
        """Set user level and update visibility."""
        self._current_level = level
        self._settings.setValue(self.SETTINGS_KEY, level.value)
        self._apply_visibility()
        self.level_changed.emit(level.value)
    
    def toggle_expert_mode(self) -> bool:
        """Toggle between beginner and expert mode."""
        new_level = UserLevel.BEGINNER if self.is_expert else UserLevel.EXPERT
        self.set_level(new_level)
        return self.is_expert
    
    def register_panel(self, panel_id: str, widget: QWidget) -> None:
        """Register a panel for visibility management."""
        self._registered_panels[panel_id] = widget
    
    def unregister_panel(self, panel_id: str) -> None:
        """Unregister a panel."""
        self._registered_panels.pop(panel_id, None)
    
    def _apply_visibility(self) -> None:
        """Apply visibility rules to all registered panels."""
        for panel_id, widget in self._registered_panels.items():
            visible = self._should_show_panel(panel_id)
            widget.setVisible(visible)
    
    def _should_show_panel(self, panel_id: str) -> bool:
        """Determine if panel should be visible for current level."""
        config = self._panel_configs.get(panel_id)
        if not config:
            return True  # Unknown panels are visible by default
        
        category = config.get("category", PanelCategory.STANDARD)
        
        # Essential panels always visible
        if category == PanelCategory.ESSENTIAL:
            return True
        
        # Standard panels visible for all
        if category == PanelCategory.STANDARD:
            return True
        
        # Advanced and Debug panels only for Expert
        if category in (PanelCategory.ADVANCED, PanelCategory.DEBUG):
            return self.is_expert
        
        return True
    
    def get_visible_panels(self) -> List[str]:
        """Get list of currently visible panel IDs."""
        return [
            panel_id for panel_id in self._panel_configs
            if self._should_show_panel(panel_id)
        ]
    
    def get_hidden_panels(self) -> List[str]:
        """Get list of currently hidden panel IDs."""
        return [
            panel_id for panel_id in self._panel_configs
            if not self._should_show_panel(panel_id)
        ]
    
    def get_panel_info(self, panel_id: str) -> Dict:
        """Get panel configuration info."""
        return self._panel_configs.get(panel_id, {})


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════════════════

_disclosure_manager: ProgressiveDisclosureManager | None = None


def get_disclosure_manager() -> ProgressiveDisclosureManager:
    """Get global progressive disclosure manager instance."""
    global _disclosure_manager
    if _disclosure_manager is None:
        _disclosure_manager = ProgressiveDisclosureManager()
    return _disclosure_manager


def is_expert_mode() -> bool:
    """Quick check if in expert mode."""
    return get_disclosure_manager().is_expert


def toggle_expert_mode() -> bool:
    """Toggle expert mode and return new state."""
    return get_disclosure_manager().toggle_expert_mode()
