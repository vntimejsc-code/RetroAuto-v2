"""
RetroAuto v2 - Mode Tab Bar

Custom tab bar for switching between Visual/Code/Debug modes
in the Unified Studio window.

Features:
- Large mode buttons with icons
- Active state indicator
- Smooth transitions
- Keyboard shortcuts
"""

from __future__ import annotations

from enum import Enum
from typing import Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QButtonGroup,
    QSizePolicy,
    QFrame,
)


class StudioMode(Enum):
    """Available studio modes."""
    VISUAL = "visual"
    CODE = "code"
    DEBUG = "debug"


# Mode configuration
MODE_CONFIG: Dict[StudioMode, Dict] = {
    StudioMode.VISUAL: {
        "icon": "🎨",
        "label": "Visual",
        "shortcut": "Ctrl+1",
        "tooltip": "Visual scripting mode - drag and drop actions",
    },
    StudioMode.CODE: {
        "icon": "📝",
        "label": "Code",
        "shortcut": "Ctrl+2",
        "tooltip": "Code editor mode - write DSL code directly",
    },
    StudioMode.DEBUG: {
        "icon": "🔧",
        "label": "Debug",
        "shortcut": "Ctrl+3",
        "tooltip": "Debug mode - step through execution",
    },
}


class ModeButton(QPushButton):
    """Styled button for mode selection."""
    
    def __init__(
        self, 
        mode: StudioMode,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._mode = mode
        self._config = MODE_CONFIG[mode]
        self._is_active = False
        self._init_ui()
    
    def _init_ui(self) -> None:
        self.setText(f"{self._config['icon']} {self._config['label']}")
        self.setToolTip(f"{self._config['tooltip']} ({self._config['shortcut']})")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setMinimumWidth(100)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self._apply_inactive_style()
    
    def _apply_inactive_style(self) -> None:
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #808080;
                border: none;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 500;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #cccccc;
            }
            QPushButton:checked {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
            }
        """)
    
    @property
    def mode(self) -> StudioMode:
        return self._mode


class ModeTabBar(QFrame):
    """
    Mode tab bar for switching between Visual/Code/Debug modes.
    
    Signals:
        mode_changed(str): Emitted when mode changes, passes mode value
    """
    
    mode_changed = Signal(str)  # Emits mode.value string
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_mode = StudioMode.VISUAL
        self._buttons: Dict[StudioMode, ModeButton] = {}
        self._init_ui()
    
    def _init_ui(self) -> None:
        self.setObjectName("ModeTabBar")
        self.setFixedHeight(48)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(4)
        
        # Create button group for exclusive selection
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        
        # Create mode buttons
        for mode in StudioMode:
            btn = ModeButton(mode, self)
            btn.clicked.connect(lambda checked, m=mode: self._on_mode_clicked(m))
            self._buttons[mode] = btn
            self._button_group.addButton(btn)
            layout.addWidget(btn)
        
        # Set initial mode
        self._buttons[StudioMode.VISUAL].setChecked(True)
        
        # Add stretch to keep buttons left-aligned
        layout.addStretch()
        
        # Apply container style
        self.setStyleSheet("""
            #ModeTabBar {
                background-color: #2d2d30;
                border-bottom: 1px solid #3c3c3c;
            }
        """)
    
    def _on_mode_clicked(self, mode: StudioMode) -> None:
        """Handle mode button click."""
        if mode != self._current_mode:
            self._current_mode = mode
            self.mode_changed.emit(mode.value)
    
    @property
    def current_mode(self) -> StudioMode:
        """Get current mode."""
        return self._current_mode
    
    def set_mode(self, mode: StudioMode | str) -> None:
        """Set current mode programmatically."""
        if isinstance(mode, str):
            try:
                mode = StudioMode(mode)
            except ValueError:
                return
        
        if mode in self._buttons:
            self._buttons[mode].setChecked(True)
            self._current_mode = mode
            self.mode_changed.emit(mode.value)
    
    def set_visual_mode(self) -> None:
        """Switch to Visual mode."""
        self.set_mode(StudioMode.VISUAL)
    
    def set_code_mode(self) -> None:
        """Switch to Code mode."""
        self.set_mode(StudioMode.CODE)
    
    def set_debug_mode(self) -> None:
        """Switch to Debug mode."""
        self.set_mode(StudioMode.DEBUG)
