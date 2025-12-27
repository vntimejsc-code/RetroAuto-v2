"""
RetroAuto v2 - Onboarding Wizard

First-run wizard to guide new users through the app.

Features:
- Welcome screen with mode selection
- "Don't show again" checkbox
- Saves preference to QSettings
- Opens appropriate mode based on selection
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QFrame,
    QWidget,
)


class ModeCard(QFrame):
    """Clickable card for mode selection."""
    
    clicked = Signal(str)  # mode name
    
    def __init__(
        self, 
        mode: str, 
        icon: str, 
        title: str, 
        description: str,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._mode = mode
        self._selected = False
        self._init_ui(icon, title, description)
    
    def _init_ui(self, icon: str, title: str, description: str) -> None:
        self.setFixedSize(180, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #ffffff;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            font-size: 11px;
            color: #808080;
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        self._apply_style(False)
    
    def _apply_style(self, selected: bool) -> None:
        if selected:
            self.setStyleSheet("""
                ModeCard {
                    background-color: #094771;
                    border: 2px solid #0078d4;
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                ModeCard {
                    background-color: #2d2d30;
                    border: 2px solid #3c3c3c;
                    border-radius: 12px;
                }
                ModeCard:hover {
                    border: 2px solid #0078d4;
                }
            """)
    
    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._apply_style(selected)
    
    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._mode)
        super().mousePressEvent(event)


class OnboardingWizard(QDialog):
    """
    First-run onboarding wizard.
    
    Shows on first launch to help users select their preferred mode.
    
    Signals:
        mode_selected(str): Emitted when user selects a mode
    """
    
    mode_selected = Signal(str)
    
    SETTINGS_KEY = "onboarding/shown"
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = QSettings("RetroAuto", "UnifiedStudio")
        self._selected_mode = "visual"
        self._init_ui()
    
    def _init_ui(self) -> None:
        self.setWindowTitle("Welcome to RetroAuto!")
        self.setFixedSize(650, 450)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 24)
        layout.setSpacing(24)
        
        # Header
        header = QLabel("👋 Welcome to RetroAuto Studio!")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #ffffff;
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("What would you like to do?")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #808080;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Mode cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Visual Mode
        self.visual_card = ModeCard(
            "visual",
            "🎨",
            "Visual Scripting",
            "Drag & drop actions to build scripts"
        )
        self.visual_card.clicked.connect(self._on_mode_clicked)
        self.visual_card.set_selected(True)
        cards_layout.addWidget(self.visual_card)
        
        # Code Mode
        self.code_card = ModeCard(
            "code",
            "📝",
            "Code Editor",
            "Write DSL code directly"
        )
        self.code_card.clicked.connect(self._on_mode_clicked)
        cards_layout.addWidget(self.code_card)
        
        # Tutorial Mode
        self.tutorial_card = ModeCard(
            "tutorial",
            "📚",
            "Quick Tutorial",
            "Learn the basics in 5 minutes"
        )
        self.tutorial_card.clicked.connect(self._on_mode_clicked)
        cards_layout.addWidget(self.tutorial_card)
        
        layout.addLayout(cards_layout)
        
        layout.addStretch()
        
        # Bottom section
        bottom_layout = QHBoxLayout()
        
        # Don't show again checkbox
        self.dont_show_checkbox = QCheckBox("Don't show this again")
        self.dont_show_checkbox.setStyleSheet("""
            QCheckBox {
                color: #808080;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        bottom_layout.addWidget(self.dont_show_checkbox)
        
        bottom_layout.addStretch()
        
        # Get Started button
        self.start_btn = QPushButton("Get Started →")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 12px 32px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a8cff;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        self.start_btn.clicked.connect(self._on_start)
        bottom_layout.addWidget(self.start_btn)
        
        layout.addLayout(bottom_layout)
        
        # Dialog style
        self.setStyleSheet("""
            OnboardingWizard {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 16px;
            }
        """)
    
    def _on_mode_clicked(self, mode: str) -> None:
        """Handle mode card selection."""
        self._selected_mode = mode
        
        # Update selection states
        self.visual_card.set_selected(mode == "visual")
        self.code_card.set_selected(mode == "code")
        self.tutorial_card.set_selected(mode == "tutorial")
    
    def _on_start(self) -> None:
        """Handle Get Started button click."""
        # Save preference
        if self.dont_show_checkbox.isChecked():
            self._settings.setValue(self.SETTINGS_KEY, True)
        
        # Emit and close
        self.mode_selected.emit(self._selected_mode)
        self.accept()
    
    @classmethod
    def should_show(cls) -> bool:
        """Check if wizard should be shown (first run)."""
        settings = QSettings("RetroAuto", "UnifiedStudio")
        return not settings.value(cls.SETTINGS_KEY, False, type=bool)
    
    @classmethod
    def reset(cls) -> None:
        """Reset first-run flag (for testing)."""
        settings = QSettings("RetroAuto", "UnifiedStudio")
        settings.remove(cls.SETTINGS_KEY)


def show_onboarding_if_needed(parent: QWidget | None = None) -> str | None:
    """
    Show onboarding wizard if it's the first run.
    
    Returns:
        Selected mode string, or None if wizard was skipped
    """
    if OnboardingWizard.should_show():
        wizard = OnboardingWizard(parent)
        if wizard.exec() == QDialog.DialogCode.Accepted:
            return wizard._selected_mode
    return None
