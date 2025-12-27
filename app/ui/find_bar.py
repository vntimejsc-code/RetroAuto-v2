"""
RetroAuto v2 - Find Bar

In-editor find and replace bar with keyboard navigation.

Features:
- Find with highlight all matches
- Find next/previous (F3/Shift+F3)
- Optional replace mode
- Match count display
"""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QCheckBox,
    QFrame,
    QPlainTextEdit,
)


class FindBar(QFrame):
    """
    Find/Replace bar that attaches to a text editor.
    
    Signals:
        closed: Emitted when find bar is closed
    """
    
    closed = Signal()
    
    def __init__(self, editor: QPlainTextEdit, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editor = editor
        self._matches: List[int] = []  # List of match positions
        self._current_match = -1
        self._init_ui()
    
    def _init_ui(self) -> None:
        self.setFixedHeight(40)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Find icon
        find_icon = QLabel("🔍")
        layout.addWidget(find_icon)
        
        # Find input
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find...")
        self.find_input.textChanged.connect(self._on_find_changed)
        self.find_input.returnPressed.connect(self.find_next)
        self.find_input.setMinimumWidth(200)
        layout.addWidget(self.find_input)
        
        # Match count
        self.match_label = QLabel("")
        self.match_label.setStyleSheet("color: #808080; font-size: 11px;")
        self.match_label.setMinimumWidth(60)
        layout.addWidget(self.match_label)
        
        # Case sensitive checkbox
        self.case_check = QCheckBox("Aa")
        self.case_check.setToolTip("Case sensitive")
        self.case_check.toggled.connect(self._on_find_changed)
        layout.addWidget(self.case_check)
        
        # Navigation buttons
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setToolTip("Previous (Shift+F3)")
        self.prev_btn.setFixedWidth(32)
        self.prev_btn.clicked.connect(self.find_previous)
        layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("▶")
        self.next_btn.setToolTip("Next (F3)")
        self.next_btn.setFixedWidth(32)
        self.next_btn.clicked.connect(self.find_next)
        layout.addWidget(self.next_btn)
        
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setToolTip("Close (Esc)")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.close_bar)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #808080;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        layout.addWidget(close_btn)
        
        # Style
        self.setStyleSheet("""
            FindBar {
                background-color: #252526;
                border-bottom: 1px solid #3c3c3c;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #555555;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                border: none;
                padding: 4px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QCheckBox {
                color: #cccccc;
            }
        """)
        
        self.hide()
    
    def show_bar(self) -> None:
        """Show the find bar and focus input."""
        self.show()
        self.find_input.setFocus()
        self.find_input.selectAll()
        
        # If text is selected, use it as search term
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            self.find_input.setText(cursor.selectedText())
    
    def close_bar(self) -> None:
        """Close the find bar and clear highlights."""
        self._clear_highlights()
        self.hide()
        self._editor.setFocus()
        self.closed.emit()
    
    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close_bar()
        elif event.key() == Qt.Key.Key_F3:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.find_previous()
            else:
                self.find_next()
        else:
            super().keyPressEvent(event)
    
    def _on_find_changed(self) -> None:
        """Handle search text changes."""
        search_text = self.find_input.text()
        if not search_text:
            self._clear_highlights()
            self.match_label.setText("")
            return
        
        self._find_all(search_text)
    
    def _find_all(self, text: str) -> None:
        """Find all matches and highlight them."""
        self._clear_highlights()
        self._matches.clear()
        self._current_match = -1
        
        if not text:
            return
        
        document = self._editor.document()
        cursor = QTextCursor(document)
        
        # Find flags
        flags = QTextCursor.FindFlag(0)
        if self.case_check.isChecked():
            flags |= QTextCursor.FindFlag.FindCaseSensitively
        
        # Find all matches
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#515c6a"))
        
        while True:
            cursor = document.find(text, cursor, flags)
            if cursor.isNull():
                break
            
            self._matches.append(cursor.position() - len(text))
            
            # Apply highlight
            cursor.mergeCharFormat(highlight_format)
        
        # Update count
        count = len(self._matches)
        if count == 0:
            self.match_label.setText("No results")
            self.find_input.setStyleSheet("""
                QLineEdit {
                    background-color: #5c3c3c;
                    color: #cccccc;
                    border: 1px solid #ff6b6b;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
            """)
        else:
            self.find_input.setStyleSheet("""
                QLineEdit {
                    background-color: #3c3c3c;
                    color: #cccccc;
                    border: 1px solid #555555;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
            """)
            self.find_next()  # Go to first match
    
    def find_next(self) -> None:
        """Go to next match."""
        if not self._matches:
            return
        
        self._current_match = (self._current_match + 1) % len(self._matches)
        self._go_to_match()
    
    def find_previous(self) -> None:
        """Go to previous match."""
        if not self._matches:
            return
        
        self._current_match = (self._current_match - 1) % len(self._matches)
        self._go_to_match()
    
    def _go_to_match(self) -> None:
        """Navigate to current match."""
        if self._current_match < 0 or self._current_match >= len(self._matches):
            return
        
        position = self._matches[self._current_match]
        cursor = self._editor.textCursor()
        cursor.setPosition(position)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor,
            len(self.find_input.text())
        )
        
        self._editor.setTextCursor(cursor)
        self._editor.centerCursor()
        
        # Update label
        self.match_label.setText(f"{self._current_match + 1}/{len(self._matches)}")
    
    def _clear_highlights(self) -> None:
        """Clear all search highlights."""
        cursor = self._editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        
        # Reset to default format
        format = QTextCharFormat()
        cursor.setCharFormat(format)
        
        # Restore cursor
        cursor.clearSelection()
        self._editor.setTextCursor(cursor)
