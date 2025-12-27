"""
RetroAuto v2 - Keyboard Shortcuts Overlay

Shows all available keyboard shortcuts in a modal overlay.
Triggered by Ctrl+? (Ctrl+Shift+/)

Features:
- Categorized shortcuts list
- Search/filter
- Click to execute
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QFrame,
    QWidget,
    QPushButton,
)


@dataclass
class ShortcutInfo:
    """Information about a keyboard shortcut."""
    key: str
    description: str
    category: str
    action: Optional[Callable] = None


# All keyboard shortcuts organized by category
SHORTCUTS: List[ShortcutInfo] = [
    # File operations
    ShortcutInfo("Ctrl+N", "New file", "File"),
    ShortcutInfo("Ctrl+O", "Open file", "File"),
    ShortcutInfo("Ctrl+S", "Save file", "File"),
    ShortcutInfo("Ctrl+Shift+S", "Save as", "File"),
    ShortcutInfo("Ctrl+W", "Close file", "File"),
    
    # Edit operations
    ShortcutInfo("Ctrl+Z", "Undo", "Edit"),
    ShortcutInfo("Ctrl+Y", "Redo", "Edit"),
    ShortcutInfo("Ctrl+X", "Cut", "Edit"),
    ShortcutInfo("Ctrl+C", "Copy", "Edit"),
    ShortcutInfo("Ctrl+V", "Paste", "Edit"),
    ShortcutInfo("Ctrl+A", "Select all", "Edit"),
    ShortcutInfo("Ctrl+F", "Find", "Edit"),
    ShortcutInfo("Ctrl+H", "Replace", "Edit"),
    ShortcutInfo("Ctrl+G", "Go to line", "Edit"),
    
    # View operations
    ShortcutInfo("Ctrl+1", "Visual mode", "View"),
    ShortcutInfo("Ctrl+2", "Code mode", "View"),
    ShortcutInfo("Ctrl+3", "Debug mode", "View"),
    ShortcutInfo("Ctrl+Shift+E", "Toggle expert mode", "View"),
    ShortcutInfo("Ctrl+Shift+P", "Command palette", "View"),
    ShortcutInfo("Ctrl+?", "Show shortcuts", "View"),
    ShortcutInfo("F11", "Toggle fullscreen", "View"),
    
    # Run operations
    ShortcutInfo("F5", "Run script", "Run"),
    ShortcutInfo("Shift+F5", "Stop script", "Run"),
    ShortcutInfo("F6", "Pause/resume", "Run"),
    ShortcutInfo("F10", "Step over", "Run"),
    ShortcutInfo("F11", "Step into", "Run"),
    ShortcutInfo("Shift+F11", "Step out", "Run"),
    ShortcutInfo("F9", "Toggle breakpoint", "Run"),
    
    # Code operations
    ShortcutInfo("Ctrl+Space", "Trigger autocomplete", "Code"),
    ShortcutInfo("Ctrl+Shift+I", "Format document", "Code"),
    ShortcutInfo("Ctrl+/", "Toggle comment", "Code"),
    ShortcutInfo("Tab", "Indent", "Code"),
    ShortcutInfo("Shift+Tab", "Outdent", "Code"),
    
    # Navigation
    ShortcutInfo("Ctrl+P", "Quick open file", "Navigation"),
    ShortcutInfo("Ctrl+Tab", "Switch between files", "Navigation"),
    ShortcutInfo("Ctrl+Click", "Go to definition", "Navigation"),
    ShortcutInfo("Alt+Left", "Go back", "Navigation"),
    ShortcutInfo("Alt+Right", "Go forward", "Navigation"),
]


class ShortcutItem(QFrame):
    """Single shortcut item in the list."""
    
    clicked = Signal(str)  # key sequence
    
    def __init__(
        self, 
        info: ShortcutInfo,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._info = info
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Key sequence
        key_label = QLabel(self._info.key)
        key_label.setStyleSheet("""
            background-color: #3c3c3c;
            color: #ffffff;
            padding: 4px 8px;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
            font-size: 11px;
            font-weight: bold;
        """)
        key_label.setFixedWidth(120)
        layout.addWidget(key_label)
        
        # Description
        desc_label = QLabel(self._info.description)
        desc_label.setStyleSheet("""
            color: #cccccc;
            font-size: 12px;
        """)
        layout.addWidget(desc_label, 1)
        
        self.setStyleSheet("""
            ShortcutItem {
                background-color: transparent;
            }
            ShortcutItem:hover {
                background-color: #2d2d30;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._info.key)
        super().mousePressEvent(event)


class ShortcutsOverlay(QDialog):
    """
    Modal overlay showing all keyboard shortcuts.
    
    Features:
    - Categorized list
    - Search filter
    - Click to dismiss
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self) -> None:
        self.setWindowTitle("Keyboard Shortcuts")
        self.setFixedSize(500, 600)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        title = QLabel("⌨️ Keyboard Shortcuts")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #808080;
                font-size: 20px;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        header.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border-bottom: 1px solid #3c3c3c;
            }
        """)
        layout.addWidget(header)
        
        # Search box
        search_container = QFrame()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(16, 8, 16, 8)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search shortcuts...")
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: #cccccc;
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
            }
        """)
        search_layout.addWidget(self.search_input)
        
        search_container.setStyleSheet("background-color: #252526;")
        layout.addWidget(search_container)
        
        # Shortcuts list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
        """)
        
        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(8, 8, 8, 8)
        self._list_layout.setSpacing(0)
        
        self._populate_shortcuts()
        
        scroll.setWidget(self._list_widget)
        layout.addWidget(scroll)
        
        # Footer hint
        footer = QLabel("Press Esc or click outside to close")
        footer.setStyleSheet("""
            color: #606060;
            font-size: 11px;
            padding: 8px;
            background-color: #252526;
        """)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
        
        # Dialog style
        self.setStyleSheet("""
            ShortcutsOverlay {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
            }
        """)
    
    def _populate_shortcuts(self, filter_text: str = "") -> None:
        """Populate shortcuts list, optionally filtered."""
        # Clear existing
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Group by category
        categories: Dict[str, List[ShortcutInfo]] = {}
        for shortcut in SHORTCUTS:
            if filter_text:
                if filter_text.lower() not in shortcut.key.lower() and \
                   filter_text.lower() not in shortcut.description.lower():
                    continue
            
            if shortcut.category not in categories:
                categories[shortcut.category] = []
            categories[shortcut.category].append(shortcut)
        
        # Add categorized items
        for category, shortcuts in categories.items():
            # Category header
            cat_label = QLabel(category)
            cat_label.setStyleSheet("""
                color: #808080;
                font-size: 11px;
                font-weight: bold;
                padding: 12px 12px 4px 12px;
            """)
            self._list_layout.addWidget(cat_label)
            
            # Shortcuts in category
            for shortcut in shortcuts:
                item = ShortcutItem(shortcut)
                item.clicked.connect(self.close)
                self._list_layout.addWidget(item)
        
        # Stretch at end
        self._list_layout.addStretch()
    
    def _on_search(self, text: str) -> None:
        """Filter shortcuts based on search text."""
        self._populate_shortcuts(text)
    
    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


def register_shortcuts_overlay(window: QWidget) -> ShortcutsOverlay:
    """
    Register Ctrl+? shortcut to show shortcuts overlay.
    
    Returns:
        The overlay instance
    """
    overlay = ShortcutsOverlay(window)
    
    # Ctrl+? (Ctrl+Shift+/)
    shortcut = QShortcut(QKeySequence("Ctrl+?"), window)
    shortcut.activated.connect(overlay.exec)
    
    return overlay
