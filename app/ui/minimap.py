"""
RetroAuto v2 - Code Minimap (The Navigator)

Visual minimap for DSL code editor.
Renders a scaled-down version of the code with syntax coloring.
"""

from __future__ import annotations

import re

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QPlainTextEdit, QWidget

# Minimap Colors
COLORS = {
    "bg": "#1e1e1e",
    "viewport": "#ffffff10",  # Transparent white
    "viewport_border": "#ffffff40",
    "default": "#808080",
    "flow": "#569cd6",  # Blue
    "logic": "#c586c0",  # Purple (Control flow)
    "comment": "#6a9955",  # Green
    "string": "#ce9178",  # Orange
}


class Minimap(QWidget):
    """
    Code Minimap widget.
    
    Displays a high-level view of the code structure.
    Handles scrolling interactions.
    """

    WIDTH = 60
    LINE_HEIGHT = 2  # Pixels per line

    def __init__(self, editor: QPlainTextEdit):
        super().__init__(editor)
        self.editor = editor
        self.setFixedWidth(self.WIDTH)
        self.setMouseTracking(True)
        self.show()

        # Update when editor changes
        self.editor.blockCountChanged.connect(self.update)
        self.editor.updateRequest.connect(self._on_update_request)
        self.editor.verticalScrollBar().valueChanged.connect(self.update)

    def _on_update_request(self, rect: QRect, dy: int):
        """Handle editor update requests."""
        self.update()

    def paintEvent(self, event: QPaintEvent):
        """Paint the minimap."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(COLORS["bg"]))

        # Paint lines
        block = self.editor.document().firstBlock()
        pixel_y = 0
        max_y = self.height()

        while block.isValid():
            if pixel_y > max_y:
                break

            text = block.text().strip()
            if text:
                color = self._get_line_color(text)
                painter.fillRect(
                    2, 
                    pixel_y, 
                    min(len(text) * 2, self.WIDTH - 4), 
                    self.LINE_HEIGHT, 
                    QColor(color)
                )

            block = block.next()
            pixel_y += self.LINE_HEIGHT + 1  # 1px gap

        # Paint Viewport (Visible Area)
        self._paint_viewport(painter)

    def _get_line_color(self, text: str) -> str:
        """Determine color based on content."""
        if text.startswith("//") or text.startswith("#"):
            return COLORS["comment"]
        if text.startswith("@") or text.startswith("flow "):
            return COLORS["flow"]
        if any(text.startswith(k) for k in ("if", "else", "while", "loop", "match")):
            return COLORS["logic"]
        if '"' in text:
            return COLORS["string"]
        return COLORS["default"]

    def _paint_viewport(self, painter: QPainter):
        """Paint the rectangle representing visible area."""
        
        # Calculate viewport position
        # Ratio of visible lines to total lines
        
        total_lines = max(1, self.editor.blockCount())
        lines_visible = self.editor.viewport().height() / self.editor.fontMetrics().height()
        
        # Scaling factor: map editor scroll range to minimap height?
        # Typically minimap shows the WHOLE file scaled down, or a window of it?
        # Let's map 1 code line = LINE_HEIGHT pixels on minimap.
        
        # If file is too long for minimap, we might need a scrollable minimap or scaling.
        # For simple implementation: Fixed scale.
        
        first_visible = self.editor.firstVisibleBlock().blockNumber()
        
        y = first_visible * (self.LINE_HEIGHT + 1)
        h = lines_visible * (self.LINE_HEIGHT + 1)
        
        # Draw viewport rect
        painter.fillRect(0, int(y), self.WIDTH, int(h), QColor(COLORS["viewport"]))
        
        # Draw border
        painter.setPen(QColor(COLORS["viewport_border"]))
        painter.drawRect(0, int(y), self.WIDTH - 1, int(h))

    def mousePressEvent(self, event: QMouseEvent):
        """Scroll to clicked position."""
        self._handle_mouse(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Drag scroll."""
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._handle_mouse(event)

    def _handle_mouse(self, event: QMouseEvent):
        """Map mouse Y to scroll position."""
        y = event.position().y()
        
        # Reverse map: y pixels -> line number
        line = int(y / (self.LINE_HEIGHT + 1))
        
        # Center viewport on click?
        # Or simpler: Jump to that line
        
        viewport_lines = self.editor.viewport().height() / self.editor.fontMetrics().height()
        target_line = int(line - (viewport_lines / 2))
        
        scrollbar = self.editor.verticalScrollBar()
        # Map line to scroll value?
        # QPlainTextEdit scroll is by lines usually, or pixels?
        # Default is usually lines if not smooth scroll?
        # Let's try cursor movement or scrollbar
        
        cursor = self.editor.textCursor()
        block = self.editor.document().findBlockByNumber(max(0, min(line, self.editor.blockCount() - 1)))
        
        # We want to scroll so this block is visible, preferably centered
        # Using scrollbar setValue directly is cleaner if we know the ratio
        
        # But setting cursor is safer for valid range
        # self.editor.setTextCursor(...) scrolls to cursor.
        
        # Let's try direct scrollbar calculation
        # total_pixels in minimap vs scrollbar range
        
        # If using 1-to-1 mapping logic:
        # scroll_val = line_idx
        scrollbar.setValue(target_line)
