"""
RetroAuto v2 - IntelliSense Completer

Provides autocomplete suggestions for DSL code editor.
Features:
- Action function names (click, wait_image, etc.)
- Asset ID completion
- Parameter hints
- Context-aware suggestions
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QStringListModel, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QCompleter, QPlainTextEdit, QToolTip

from infra import get_logger

logger = get_logger("IntelliSense")


# DSL Built-in functions
DSL_FUNCTIONS = [
    "click",
    "click_image",
    "click_random",
    "wait_image",
    "wait_pixel",
    "if_image",
    "if_pixel",
    "if_text",
    "while_image",
    "sleep",
    "delay",
    "delay_random",
    "hotkey",
    "type_text",
    "read_text",
    "label",
    "goto",
    "run_flow",
    "drag",
    "scroll",
    "loop",
    "end_loop",
    "end_if",
    "end_while",
    "notify",
]

# DSL Keywords
DSL_KEYWORDS = [
    "flow",
    "interrupt",
    "hotkeys",
    "when",
    "priority",
    "true",
    "false",
]

# Common snippets
DSL_SNIPPETS = {
    "loop": "loop {\n  \n}",
    "flow": "flow name {\n  \n}",
    "if_image": 'if_image("asset_id") {\n  \n}',
    "while_image": 'while_image("asset_id") {\n  \n}',
}

# DSL Function Signatures
DSL_SIGNATURES = {
    "click": "click(x: int, y: int, button: str = 'left', clicks: int = 1)",
    "click_image": "click_image(asset_id: str, timeout: int = 30, region: tuple = None)",
    "click_random": "click_random(min_x: int, max_x: int, min_y: int, max_y: int)",
    "wait_image": "wait_image(asset_id: str, timeout: int = 30) -> Match",
    "wait_pixel": "wait_pixel(x: int, y: int, color: str, timeout: int = 30)",
    "if_image": "if_image(asset_id: str, region: tuple = None) -> bool",
    "if_pixel": "if_pixel(x: int, y: int, color: str) -> bool",
    "if_text": "if_text(text: str, region: tuple = None) -> bool",
    "while_image": "while_image(asset_id: str, timeout: int = 30)",
    "sleep": "sleep(duration: int_or_str)",
    "delay": "delay(ms: int)",
    "delay_random": "delay_random(min_ms: int, max_ms: int)",
    "hotkey": "hotkey(keys: str)",
    "type_text": "type_text(text: str, interval: float = 0.0)",
    "read_text": "read_text(region: tuple = None, lang: str = 'eng') -> str",
    "run_flow": "run_flow(flow_name: str)",
    "scroll": "scroll(amount: int)",
    "drag": "drag(x1: int, y1: int, x2: int, y2: int, duration: float = 0.5)",
    "notify": "notify(title: str, message: str)",
}


class DSLCompleter(QCompleter):
    """
    Autocomplete for DSL code editor.

    Provides context-aware suggestions for:
    - Function names (click, wait_image, etc.)
    - Asset IDs (from project)
    - Keywords (flow, interrupt, etc.)
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # Combine all completions
        self._base_completions = sorted(set(DSL_FUNCTIONS + DSL_KEYWORDS))
        self._asset_ids: list[str] = []

        # Setup model
        self._model = QStringListModel()
        self._update_model()
        self.setModel(self._model)

        # Completion settings
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setFilterMode(Qt.MatchFlag.MatchContains)

        # Styling
        popup = self.popup()
        popup.setStyleSheet(
            """
            QListView {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #454545;
                selection-background-color: #094771;
                font-family: Consolas;
                font-size: 10pt;
            }
        """
        )

    def _update_model(self) -> None:
        """Update completion model with current data."""
        all_items = sorted(set(self._base_completions + self._asset_ids))
        self._model.setStringList(all_items)

    def set_asset_ids(self, asset_ids: list[str]) -> None:
        """Update available asset IDs for completion."""
        self._asset_ids = [f'"{aid}"' for aid in asset_ids]  # Add quotes
        self._update_model()
        logger.info(f"IntelliSense: Updated {len(asset_ids)} asset IDs")


class IntelliSenseManager:
    """
    Manages IntelliSense for a code editor.

    Handles:
    - Detecting completion context
    - Triggering completion popup
    - Inserting selected completion
    """

    def __init__(self, editor: QPlainTextEdit) -> None:
        self.editor = editor
        self.completer = DSLCompleter()
        self.completer.setWidget(editor)
        self.completer.activated.connect(self._insert_completion)

        # Debounce timer for completion (100ms)
        from PySide6.QtCore import QTimer

        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(100)
        self._debounce_timer.timeout.connect(self._do_completion)

        # Connect to editor events
        editor.textChanged.connect(self._on_text_changed)
        editor.cursorPositionChanged.connect(self._on_cursor_moved)

    def _on_cursor_moved(self) -> None:
        """Check for signature help context."""
        cursor = self.editor.textCursor()
        pos = cursor.position()

        # Look backwards for function call
        # Simple heuristic: find '(' backwards within current line
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
        line_text = cursor.selectedText()

        # Cursor is at end of line_text. Find last '(' before cursor
        # Since we selected from start of line, `line_text` length matches position in line
        # Logic: iterate backwards from current char

        # Get char before cursor
        current_line_idx = pos - self.editor.document().findBlock(pos).position()
        text_before_cursor = line_text[:current_line_idx]

        # Find opening parenthesis of current scope
        open_paren_idx = text_before_cursor.rfind("(")
        close_paren_idx = text_before_cursor.rfind(")")

        # If we are inside parens (last open > last close)
        if open_paren_idx > close_paren_idx:
            # Check what's before the '('
            # e.g. "click(..."
            pre_paren = text_before_cursor[:open_paren_idx].strip()
            # Get last word
            words = pre_paren.split()
            if words:
                func_name = words[-1]
                if func_name in DSL_SIGNATURES:
                    # Show signature
                    signature = DSL_SIGNATURES[func_name]
                    QToolTip.showText(
                        self.editor.cursorRect().bottomRight(),  # Position
                        signature,
                        self.editor,
                        QRect(),  # No specific rect
                    )
                    return

        # If we reached here, no signature found or outside parens
        # We don't hide immediately to allow hovering, but typically we should hide if moved away
        # For now, let's rely on QToolTip auto-hide or explicit hide if strictly outside
        # But QToolTip might flicker if we hide/show constantly.
        # Let's hide if we are clearly not in specific context or if completer is showing
        if self.completer.popup().isVisible():
            return  # Don't interfere with completer

        # Optional: Hide if not identifying a function
        # QToolTip.hideText()

    def _on_text_changed(self) -> None:
        """Trigger debounced completion update."""
        # Restart debounce timer on each keystroke
        self._debounce_timer.start()

    def _do_completion(self) -> None:
        """Perform completion (called after debounce)."""
        cursor = self.editor.textCursor()

        # Get current word being typed
        cursor.movePosition(QTextCursor.MoveOperation.StartOfWord, QTextCursor.MoveMode.KeepAnchor)
        prefix = cursor.selectedText()

        # Show popup if typing at least 2 characters
        if len(prefix) >= 2:
            self.completer.setCompletionPrefix(prefix)

            if self.completer.completionCount() > 0:
                # Position popup below cursor
                rect = self.editor.cursorRect()
                rect.setWidth(250)
                self.completer.complete(rect)
            else:
                self.completer.popup().hide()
        else:
            self.completer.popup().hide()

    def show_completions(self) -> None:
        """Manually trigger completion popup (Ctrl+Space)."""
        self._do_completion()

    def _insert_completion(self, completion: str) -> None:
        """Insert selected completion into editor."""
        cursor = self.editor.textCursor()

        # Remove the typed prefix
        cursor.movePosition(QTextCursor.MoveOperation.StartOfWord, QTextCursor.MoveMode.KeepAnchor)

        # Check if completion is a snippet
        if completion in DSL_SNIPPETS:
            cursor.insertText(DSL_SNIPPETS[completion])
        else:
            cursor.insertText(completion)

            # If it's a function, add parentheses
            if completion in DSL_FUNCTIONS:
                cursor.insertText("(")

        self.editor.setTextCursor(cursor)
        logger.debug(f"IntelliSense: Inserted '{completion}'")

    def set_asset_ids(self, asset_ids: list[str]) -> None:
        """Update available asset IDs."""
        self.completer.set_asset_ids(asset_ids)
