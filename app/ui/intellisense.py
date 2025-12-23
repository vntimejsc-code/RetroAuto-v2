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

from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtWidgets import QCompleter, QPlainTextEdit
from PySide6.QtGui import QTextCursor

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
        self._base_completions = sorted(
            set(DSL_FUNCTIONS + DSL_KEYWORDS)
        )
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
        popup.setStyleSheet("""
            QListView {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #454545;
                selection-background-color: #094771;
                font-family: Consolas;
                font-size: 10pt;
            }
        """)
        
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
        
        # Connect to editor events
        editor.textChanged.connect(self._on_text_changed)
        
    def _on_text_changed(self) -> None:
        """Check if we should show completion popup."""
        cursor = self.editor.textCursor()
        
        # Get current word being typed
        cursor.movePosition(QTextCursor.MoveOperation.StartOfWord, QTextCursor.MoveMode.KeepAnchor)
        prefix = cursor.selectedText()
        
        # Show popup if typing at least 2 characters
        if len(prefix) >= 2:
            self.completer.setCompletionPrefix(prefix)
            
            if self.completer.completionCount() > 0:
                popup = self.completer.popup()
                
                # Position popup below cursor
                rect = self.editor.cursorRect()
                rect.setWidth(250)
                self.completer.complete(rect)
            else:
                self.completer.popup().hide()
        else:
            self.completer.popup().hide()
            
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
