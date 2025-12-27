"""
RetroAuto v2 - Live Preview Panel

Shows real-time preview of DSL code as visual action cards.
Syncs with code editor changes.

Features:
- Parse DSL and show action cards
- Visual representation of clicks, waits, conditionals
- Sync on code change with debounce
- Error highlighting
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import re

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLabel,
    QFrame,
    QPushButton,
)


@dataclass
class ActionPreview:
    """Preview data for a single action."""
    action_type: str
    icon: str
    description: str
    line_number: int
    params: dict = None


# Action type to icon/color mapping
ACTION_STYLES = {
    "click": {"icon": "🎯", "color": "#2196F3", "label": "Click"},
    "click_image": {"icon": "🖼️", "color": "#4CAF50", "label": "Click Image"},
    "wait": {"icon": "⏱️", "color": "#FF9800", "label": "Wait"},
    "type": {"icon": "⌨️", "color": "#9C27B0", "label": "Type"},
    "key": {"icon": "🔑", "color": "#673AB7", "label": "Key Press"},
    "if": {"icon": "❓", "color": "#FF5722", "label": "If"},
    "else": {"icon": "↩️", "color": "#607D8B", "label": "Else"},
    "loop": {"icon": "🔄", "color": "#00BCD4", "label": "Loop"},
    "flow": {"icon": "🚀", "color": "#4CAF50", "label": "Flow"},
    "call": {"icon": "📞", "color": "#03A9F4", "label": "Call"},
    "set": {"icon": "📝", "color": "#795548", "label": "Set Variable"},
    "return": {"icon": "↪️", "color": "#F44336", "label": "Return"},
    "break": {"icon": "⏹️", "color": "#E91E63", "label": "Break"},
    "continue": {"icon": "⏭️", "color": "#3F51B5", "label": "Continue"},
}


class ActionCard(QFrame):
    """Visual card representing a single action."""
    
    clicked = Signal(int)  # line number
    
    def __init__(
        self, 
        preview: ActionPreview,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._preview = preview
        self._init_ui()
    
    def _init_ui(self) -> None:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Line number
        line_label = QLabel(f"L{self._preview.line_number}")
        line_label.setStyleSheet("""
            color: #808080;
            font-size: 10px;
            font-family: 'Consolas', monospace;
        """)
        line_label.setFixedWidth(30)
        layout.addWidget(line_label)
        
        # Icon
        icon_label = QLabel(self._preview.icon)
        icon_label.setStyleSheet("font-size: 20px;")
        icon_label.setFixedWidth(30)
        layout.addWidget(icon_label)
        
        # Description
        desc_label = QLabel(self._preview.description)
        desc_label.setStyleSheet("""
            color: #cccccc;
            font-size: 12px;
        """)
        layout.addWidget(desc_label, 1)
        
        # Style
        style = ACTION_STYLES.get(self._preview.action_type, {"color": "#607D8B"})
        color = style["color"]
        
        self.setStyleSheet(f"""
            ActionCard {{
                background-color: #2d2d30;
                border-left: 3px solid {color};
                border-radius: 4px;
            }}
            ActionCard:hover {{
                background-color: #3c3c3c;
            }}
        """)
    
    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._preview.line_number)
        super().mousePressEvent(event)


class LivePreviewPanel(QWidget):
    """
    Live preview panel showing DSL code as visual action cards.
    
    Updates automatically when code changes (with debounce).
    
    Signals:
        action_clicked(int): Emitted when action card is clicked (line number)
    """
    
    action_clicked = Signal(int)
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._code = ""
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._update_preview)
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        title = QLabel("🔍 Live Preview")
        title.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #cccccc;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("↻")
        refresh_btn.setToolTip("Refresh preview")
        refresh_btn.setFixedSize(24, 24)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #808080;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #cccccc;
            }
        """)
        refresh_btn.clicked.connect(self._update_preview)
        header_layout.addWidget(refresh_btn)
        
        header.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border-bottom: 1px solid #3c3c3c;
            }
        """)
        layout.addWidget(header)
        
        # Scroll area for action cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
        """)
        
        self._cards_widget = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(8, 8, 8, 8)
        self._cards_layout.setSpacing(4)
        self._cards_layout.addStretch()
        
        scroll.setWidget(self._cards_widget)
        layout.addWidget(scroll)
        
        # Initial empty state
        self._show_empty_state()
    
    def _show_empty_state(self) -> None:
        """Show placeholder when no code."""
        self._clear_cards()
        
        empty_label = QLabel("No actions to preview\n\nType DSL code to see live preview")
        empty_label.setStyleSheet("""
            color: #606060;
            font-size: 12px;
        """)
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cards_layout.insertWidget(0, empty_label)
    
    def _clear_cards(self) -> None:
        """Clear all action cards."""
        while self._cards_layout.count() > 1:  # Keep the stretch
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def set_code(self, code: str) -> None:
        """Set code and trigger preview update (debounced)."""
        self._code = code
        self._debounce_timer.start(300)  # 300ms debounce
    
    def _update_preview(self) -> None:
        """Parse code and update preview cards."""
        self._clear_cards()
        
        if not self._code.strip():
            self._show_empty_state()
            return
        
        previews = self._parse_code(self._code)
        
        if not previews:
            self._show_empty_state()
            return
        
        for preview in previews:
            card = ActionCard(preview)
            card.clicked.connect(self.action_clicked.emit)
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)
    
    def _parse_code(self, code: str) -> List[ActionPreview]:
        """Parse DSL code and extract action previews."""
        previews = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('#') or line_stripped.startswith('//'):
                continue
            
            preview = self._parse_line(line_stripped, i)
            if preview:
                previews.append(preview)
        
        return previews
    
    def _parse_line(self, line: str, line_num: int) -> Optional[ActionPreview]:
        """Parse a single line and create preview."""
        # Flow declaration
        if line.startswith('flow '):
            name = line.replace('flow ', '').replace('{', '').strip()
            return ActionPreview("flow", "🚀", f"Flow: {name}", line_num)
        
        # Click action
        if 'click(' in line or 'click_image(' in line:
            if 'click_image(' in line:
                match = re.search(r'click_image\(["\']?(\w+)', line)
                target = match.group(1) if match else "image"
                return ActionPreview("click_image", "🖼️", f"Click image: {target}", line_num)
            else:
                match = re.search(r'click\((\d+),\s*(\d+)\)', line)
                if match:
                    x, y = match.groups()
                    return ActionPreview("click", "🎯", f"Click at ({x}, {y})", line_num)
                return ActionPreview("click", "🎯", "Click", line_num)
        
        # Wait action
        if 'wait(' in line:
            match = re.search(r'wait\((\d+)\)', line)
            if match:
                ms = match.group(1)
                return ActionPreview("wait", "⏱️", f"Wait {ms}ms", line_num)
            match = re.search(r'wait\((\d+)s\)', line)
            if match:
                s = match.group(1)
                return ActionPreview("wait", "⏱️", f"Wait {s}s", line_num)
            return ActionPreview("wait", "⏱️", "Wait", line_num)
        
        # Type action
        if 'type(' in line:
            match = re.search(r'type\(["\'](.+?)["\']\)', line)
            if match:
                text = match.group(1)
                if len(text) > 20:
                    text = text[:20] + "..."
                return ActionPreview("type", "⌨️", f'Type: "{text}"', line_num)
            return ActionPreview("type", "⌨️", "Type text", line_num)
        
        # Key press
        if 'key(' in line or 'hotkey(' in line:
            match = re.search(r'(?:key|hotkey)\(["\'](.+?)["\']\)', line)
            if match:
                key = match.group(1)
                return ActionPreview("key", "🔑", f"Press: {key}", line_num)
            return ActionPreview("key", "🔑", "Key press", line_num)
        
        # If statement
        if line.startswith('if ') or line.startswith('if('):
            condition = line.replace('if ', '').replace('{', '').strip()
            if len(condition) > 30:
                condition = condition[:30] + "..."
            return ActionPreview("if", "❓", f"If: {condition}", line_num)
        
        # Else statement
        if line.startswith('else'):
            return ActionPreview("else", "↩️", "Else branch", line_num)
        
        # Loop
        if line.startswith('loop ') or line.startswith('while ') or line.startswith('for '):
            return ActionPreview("loop", "🔄", f"Loop: {line.split('{')[0].strip()}", line_num)
        
        # Call
        if line.startswith('call ') or line.startswith('goto '):
            target = line.replace('call ', '').replace('goto ', '').strip()
            return ActionPreview("call", "📞", f"Call: {target}", line_num)
        
        # Set variable
        if '=' in line and not line.startswith('if') and not '==' in line:
            parts = line.split('=')
            if len(parts) == 2:
                var = parts[0].strip()
                return ActionPreview("set", "📝", f"Set: {var}", line_num)
        
        return None


class LivePreviewDock(QWidget):
    """Dockable live preview panel with toggle."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview = LivePreviewPanel()
        layout.addWidget(self.preview)
    
    def set_code(self, code: str) -> None:
        """Update preview with code."""
        self.preview.set_code(code)
