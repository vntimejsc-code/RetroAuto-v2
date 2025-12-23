"""
RetroAuto v2 - DSL Code Editor

Custom QPlainTextEdit-based code editor for the DSL.
Features:
- Line numbers (Win95/98 style)
- Syntax highlighting
- Current line highlighting
- Auto-indent
- Tab to spaces conversion
- Breakpoint markers
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QTextCursor,
    QTextFormat,
)
from PySide6.QtWidgets import QCompleter, QPlainTextEdit, QToolTip, QWidget

from app.ui.minimap import Minimap

from app.ui.syntax_highlighter import DSLHighlighter
from app.ui.win95_style import COLORS

# ─────────────────────────────────────────────────────────────
# Line Number Area (with breakpoint gutter)
# ─────────────────────────────────────────────────────────────


class LineNumberArea(QWidget):
    """Line number gutter with breakpoint support."""

    BREAKPOINT_MARGIN = 16  # Width for breakpoint markers

    def __init__(self, editor: DSLCodeEditor) -> None:
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:  # type: ignore
        """Paint line numbers and breakpoints."""
        self.editor.line_number_area_paint_event(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle click to toggle breakpoint."""
        if event.button() == Qt.MouseButton.LeftButton:  # noqa: SIM102
            # Check if click is in breakpoint margin
            if event.position().x() < self.BREAKPOINT_MARGIN:
                # Find which line was clicked
                block = self.editor.firstVisibleBlock()
                top = int(
                    self.editor.blockBoundingGeometry(block)
                    .translated(self.editor.contentOffset())
                    .top()
                )

                while block.isValid():
                    if block.isVisible():
                        block_top = top
                        block_bottom = top + int(self.editor.blockBoundingRect(block).height())

                        if block_top <= event.position().y() < block_bottom:
                            line = block.blockNumber() + 1
                            self.editor.toggle_breakpoint(line)
                            self.update()
                            return

                    top += int(self.editor.blockBoundingRect(block).height())
                    block = block.next()


# ─────────────────────────────────────────────────────────────
# Code Editor
# ─────────────────────────────────────────────────────────────


class DSLCodeEditor(QPlainTextEdit):
    """
    DSL code editor with Win95/98 styling.

    Features:
    - Line numbers with classic styling
    - Syntax highlighting for DSL
    - Current line highlight
    - Smart indentation
    - Tab to 2-space conversion
    - Breakpoint markers
    - Debug line highlighting

    Signals:
        content_changed: Emitted when content changes
        cursor_position_changed: Emitted with (line, col)
        breakpoint_toggled: Emitted when breakpoint is toggled (line, enabled)
    """

    content_changed = Signal()
    cursor_position_changed = Signal(int, int)
    breakpoint_toggled = Signal(int, bool)  # line, is_set

    TAB_SIZE = 2  # 2-space indent per DSL spec

    def __init__(self, parent=None) -> None:  # type: ignore
        super().__init__(parent)
        self._breakpoints: set[int] = set()  # Set of line numbers with breakpoints
        self._debug_line: int | None = None  # Current debug execution line
        self._init_style()
        self._init_line_numbers()
        self._init_highlighter()
        self._init_highlighter()
        self._connect_signals()

        self.setMouseTracking(True)
        self._asset_provider = None  # Callable[[str], Path | None]

        # Minimap (Overlay)
        self.minimap = Minimap(self)
        self.minimap.show()

    def set_asset_provider(self, provider) -> None:
        """Set callback to lookup asset path from ID."""
        self._asset_provider = provider

    def _init_style(self) -> None:
        """Set up editor styling."""
        # Font
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)

        # Tab width
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * self.TAB_SIZE)

        # Colors - Dark theme
        self.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background-color: {COLORS["editor_bg"]};
                color: #d4d4d4;
                border: 1px solid {COLORS["shadow_dark"]};
                selection-background-color: {COLORS["highlight"]};
                selection-color: {COLORS["highlight_text"]};
            }}
        """
        )

        # Current line highlight color - dark theme
        self.current_line_color = QColor("#2d2d2d")  # Subtle dark highlight
        self.debug_line_color = QColor("#3a3a00")  # Dark yellow for debug

    def _init_line_numbers(self) -> None:
        """Set up line number gutter."""
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_area_width()

    def _init_highlighter(self) -> None:
        """Set up syntax highlighter."""
        self.highlighter = DSLHighlighter(self.document())

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.textChanged.connect(self._on_text_changed)
        self.cursorPositionChanged.connect(self._on_cursor_moved)

    # ─────────────────────────────────────────────────────────────
    # Line Numbers
    # ─────────────────────────────────────────────────────────────

    def line_number_area_width(self) -> int:
        """Calculate width needed for line numbers."""
        digits = len(str(max(1, self.blockCount())))
        digits = max(digits, 3)  # Minimum 3 digits
        space = 8 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def _update_line_number_area_width(self) -> None:
        """Update viewport margins for line numbers."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        """Update line number area on scroll."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()

    def resizeEvent(self, event) -> None:  # type: ignore
        """Handle resize to adjust line number area."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event) -> None:  # type: ignore
        """Paint the line number gutter with breakpoint markers."""
        painter = QPainter(self.line_number_area)

        # Background (Win95 gray)
        painter.fillRect(event.rect(), QColor(COLORS["gutter_bg"]))

        # Border line
        painter.setPen(QColor(COLORS["border"]))
        painter.drawLine(
            self.line_number_area.width() - 1,
            event.rect().top(),
            self.line_number_area.width() - 1,
            event.rect().bottom(),
        )

        # Draw line numbers and breakpoints
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                line = block_number + 1

                # Draw breakpoint marker (red circle)
                if line in self._breakpoints:
                    circle_y = top + (self.fontMetrics().height() - 12) // 2
                    painter.setBrush(QBrush(QColor("#CC0000")))  # Dark red
                    painter.setPen(QColor("#800000"))
                    painter.drawEllipse(2, circle_y, 12, 12)

                # Draw debug arrow (yellow arrow on current debug line)
                if self._debug_line == line:
                    arrow_y = top + (self.fontMetrics().height() - 8) // 2
                    painter.setBrush(QBrush(QColor("#FFFF00")))  # Yellow
                    painter.setPen(QColor("#808000"))
                    # Draw simple arrow
                    painter.drawRect(2, arrow_y + 2, 8, 4)
                    painter.drawLine(10, arrow_y, 14, arrow_y + 4)
                    painter.drawLine(10, arrow_y + 8, 14, arrow_y + 4)

                # Draw line number
                painter.setPen(QColor(COLORS["line_number"]))
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(line),
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    # ─────────────────────────────────────────────────────────────
    # Current Line Highlight
    # ─────────────────────────────────────────────────────────────

    def _highlight_current_line(self) -> None:
        """Highlight the current line."""
        extra_selections: list[QTextEdit.ExtraSelection] = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(self.current_line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    # ─────────────────────────────────────────────────────────────
    # Mouse Events (Asset Peek)
    # ─────────────────────────────────────────────────────────────

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for Asset Peek tooltip."""
        super().mouseMoveEvent(event)

        if not self._asset_provider:
            return

        # Get cursor under mouse
        cursor = self.cursorForPosition(event.position().toPoint())

        # Select word under cursor
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText().strip("\"'")

        if not word:
            return

        # Check if it looks like an asset ID (alphanumeric + underscore)
        if not word.replace("_", "").isalnum():
            return

        # Try to resolve asset
        image_path = self._asset_provider(word)
        if image_path and image_path.exists():
            # Show tooltip with image
            # Convert path to string using forward slashes for HTML compatibility
            html_path = str(image_path).replace("\\", "/")

            tooltip_html = f"""
            <div style='background-color: #2d2d2d; color: #fff; padding: 4px; border: 1px solid #0078d4;'>
                <div style='font-weight: bold; margin-bottom: 4px;'>📷 {word}</div>
                <img src='file:///{html_path}' width='200' />
            </div>
            """

            QToolTip.showText(event.globalPosition().toPoint(), tooltip_html, self)
        else:
            QToolTip.hideText()

    # ─────────────────────────────────────────────────────────────
    # Key Events (Auto-indent, Tab handling)
    # ─────────────────────────────────────────────────────────────

        # Minimap (Overlay)
        self.minimap = Minimap(self)
        self.minimap.show()

    def resizeEvent(self, event) -> None:
        """Handle resize to update minimap position."""
        super().resizeEvent(event)
        if hasattr(self, "minimap"):
            cr = self.contentsRect()
            w = self.minimap.WIDTH
            self.minimap.setGeometry(
                QRect(cr.right() - w, cr.top(), w, cr.height())
            )
            # Adjust viewport margins so text doesn't go under minimap
            self.setViewportMargins(0, 0, w, 0)
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key events for editor behavior."""
        # Tab -> spaces
        if event.key() == Qt.Key.Key_Tab:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._unindent()
            else:
                self._insert_spaces()
            return

        # Enter -> auto-indent
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._insert_newline_with_indent()
            return

        # Backspace -> smart unindent
        if event.key() == Qt.Key.Key_Backspace and self._smart_backspace():
            return

        super().keyPressEvent(event)

    def _insert_spaces(self) -> None:
        """Insert spaces instead of tab."""
        cursor = self.textCursor()
        cursor.insertText(" " * self.TAB_SIZE)

    def _unindent(self) -> None:
        """Remove one level of indentation."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
        line = cursor.selectedText()

        # Remove leading spaces
        if line.startswith(" " * self.TAB_SIZE):
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(
                QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, self.TAB_SIZE
            )
            cursor.removeSelectedText()
        elif line.startswith("\t"):
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
            cursor.removeSelectedText()

    def _insert_newline_with_indent(self) -> None:
        """Insert newline and match previous line's indentation."""
        cursor = self.textCursor()

        # Get current line's indentation
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
        current_line = cursor.selectedText()

        # Calculate indent
        indent = ""
        for char in current_line:
            if char == " ":
                indent += " "
            elif char == "\t":
                indent += " " * self.TAB_SIZE
            else:
                break

        # Check if we should increase indent (line ends with {)
        stripped = current_line.rstrip()
        if stripped.endswith("{"):
            indent += " " * self.TAB_SIZE

        # Insert newline with indent
        cursor = self.textCursor()
        cursor.insertText("\n" + indent)

    def _smart_backspace(self) -> bool:
        """Smart backspace to remove indent levels."""
        cursor = self.textCursor()

        # Only at start of non-empty indent
        if cursor.positionInBlock() == 0:
            return False

        # Get text before cursor on current line
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor,
            self.textCursor().positionInBlock(),
        )
        before = cursor.selectedText()

        # If only spaces before cursor, remove indent level
        if before and before.strip() == "":
            spaces_to_remove = len(before) % self.TAB_SIZE
            if spaces_to_remove == 0:
                spaces_to_remove = self.TAB_SIZE

            cursor = self.textCursor()
            for _ in range(spaces_to_remove):
                cursor.deletePreviousChar()
            return True

        return False

    # ─────────────────────────────────────────────────────────────
    # Signal Handlers
    # ─────────────────────────────────────────────────────────────

    def _on_text_changed(self) -> None:
        """Handle text change."""
        self.content_changed.emit()
        self._highlight_current_line()

    def _on_cursor_moved(self) -> None:
        """Handle cursor position change."""
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.cursor_position_changed.emit(line, col)
        self._highlight_current_line()

    # ─────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────

    def get_code(self) -> str:
        """Get editor content."""
        return self.toPlainText()

    def set_code(self, code: str) -> None:
        """Set editor content."""
        self.setPlainText(code)

    def goto_line(self, line: int, col: int = 1) -> None:
        """Move cursor to specific line and column."""
        block = self.document().findBlockByLineNumber(line - 1)
        if block.isValid():
            cursor = self.textCursor()
            cursor.setPosition(block.position() + min(col - 1, block.length() - 1))
            self.setTextCursor(cursor)
            self.centerCursor()

    def get_cursor_position(self) -> tuple[int, int]:
        """Get current (line, column) position."""
        cursor = self.textCursor()
        return (cursor.blockNumber() + 1, cursor.columnNumber() + 1)

    # ─────────────────────────────────────────────────────────────
    # Breakpoint API
    # ─────────────────────────────────────────────────────────────

    def toggle_breakpoint(self, line: int) -> None:
        """Toggle breakpoint at line."""
        if line in self._breakpoints:
            self._breakpoints.remove(line)
            self.breakpoint_toggled.emit(line, False)
        else:
            self._breakpoints.add(line)
            self.breakpoint_toggled.emit(line, True)
        self.line_number_area.update()

    def set_breakpoint(self, line: int) -> None:
        """Set a breakpoint at line."""
        if line not in self._breakpoints:
            self._breakpoints.add(line)
            self.breakpoint_toggled.emit(line, True)
            self.line_number_area.update()

    def clear_breakpoint(self, line: int) -> None:
        """Clear breakpoint at line."""
        if line in self._breakpoints:
            self._breakpoints.remove(line)
            self.breakpoint_toggled.emit(line, False)
            self.line_number_area.update()

    def clear_all_breakpoints(self) -> None:
        """Clear all breakpoints."""
        for line in list(self._breakpoints):
            self.breakpoint_toggled.emit(line, False)
        self._breakpoints.clear()
        self.line_number_area.update()

    def get_breakpoints(self) -> set[int]:
        """Get set of lines with breakpoints."""
        return self._breakpoints.copy()

    def has_breakpoint(self, line: int) -> bool:
        """Check if line has a breakpoint."""
        return line in self._breakpoints

    # ─────────────────────────────────────────────────────────────
    # Debug Line API
    # ─────────────────────────────────────────────────────────────

    def set_debug_line(self, line: int | None) -> None:
        """Set the current debug execution line (highlighted yellow)."""
        self._debug_line = line
        self._highlight_current_line()
        if line:
            self.goto_line(line)

    def clear_debug_line(self) -> None:
        """Clear debug line highlighting."""
        self._debug_line = None
        self._highlight_current_line()
