"""
RetroAuto v2 - Command Palette

Quick access to all IDE commands via fuzzy search (Ctrl+Shift+P).

Phase: IDE Next
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


@dataclass
class Command:
    """A command in the palette."""

    id: str
    name: str
    shortcut: str = ""
    category: str = "General"
    handler: Callable[[], None] | None = None


class CommandPalette(QDialog):
    """
    Command Palette dialog (Ctrl+Shift+P).

    VS Code-style fuzzy command search with keyboard navigation.

    Usage:
        palette = CommandPalette(parent)
        palette.add_command(Command("file.save", "Save File", "Ctrl+S", "File", save_fn))
        palette.show_palette()
    """

    command_selected = Signal(str)  # Command ID

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._commands: list[Command] = []
        self._filtered: list[Command] = []

        self._init_ui()
        self._register_default_commands()

    def _init_ui(self) -> None:
        self.setWindowTitle("Command Palette")
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(500, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(">")
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.returnPressed.connect(self._on_select)
        layout.addWidget(self.search_input)

        # Command list
        self.command_list = QListWidget()
        self.command_list.itemDoubleClicked.connect(self._on_item_clicked)
        layout.addWidget(self.command_list)

        # Style
        self.setStyleSheet("""
            CommandPalette {
                background-color: #252526;
                border: 1px solid #3c3c3c;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: none;
                padding: 12px;
                font-size: 14px;
            }
            QListWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
        """)

    def _register_default_commands(self) -> None:
        """Register built-in IDE commands."""
        # These will be connected by IDEMainWindow
        default_commands = [
            Command("file.new", "New File", "Ctrl+N", "File"),
            Command("file.open", "Open File", "Ctrl+O", "File"),
            Command("file.save", "Save File", "Ctrl+S", "File"),
            Command("file.saveAs", "Save As...", "Ctrl+Shift+S", "File"),
            Command("edit.find", "Find", "Ctrl+F", "Edit"),
            Command("edit.goToLine", "Go to Line...", "Ctrl+G", "Edit"),
            Command("edit.format", "Format Document", "Ctrl+Shift+F", "Edit"),
            Command("run.start", "Run Script", "F5", "Run"),
            Command("run.stop", "Stop Script", "Shift+F5", "Run"),
            Command("debug.toggleBreakpoint", "Toggle Breakpoint", "F9", "Debug"),
            Command("view.problems", "Show Problems", "", "View"),
            Command("view.output", "Show Output", "", "View"),
            Command("build.check", "Check Syntax", "Ctrl+Shift+B", "Build"),
        ]
        for cmd in default_commands:
            self._commands.append(cmd)

    def add_command(self, command: Command) -> None:
        """Add a command to the palette."""
        self._commands.append(command)

    def set_command_handler(self, command_id: str, handler: Callable[[], None]) -> None:
        """Set handler for a command."""
        for cmd in self._commands:
            if cmd.id == command_id:
                cmd.handler = handler
                break

    def show_palette(self) -> None:
        """Show the command palette."""
        self.search_input.clear()
        self._refresh_list()
        self.show()
        self.search_input.setFocus()

        # Center on parent
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + 100
            self.move(x, y)

    def _on_search(self, text: str) -> None:
        """Filter commands based on search text."""
        self._refresh_list(text.strip().lower())

    def _refresh_list(self, filter_text: str = "") -> None:
        """Refresh the command list."""
        self.command_list.clear()
        self._filtered = []

        for cmd in self._commands:
            # Fuzzy match: check if all chars appear in order
            if filter_text:
                name_lower = cmd.name.lower()
                if not self._fuzzy_match(filter_text, name_lower):
                    continue

            self._filtered.append(cmd)

            item = QListWidgetItem()
            # Format: "Command Name    Shortcut"
            display = cmd.name
            if cmd.shortcut:
                display += f"  [{cmd.shortcut}]"
            item.setText(display)
            item.setData(Qt.ItemDataRole.UserRole, cmd.id)
            self.command_list.addItem(item)

        # Select first item
        if self.command_list.count() > 0:
            self.command_list.setCurrentRow(0)

    def _fuzzy_match(self, pattern: str, text: str) -> bool:
        """Simple fuzzy matching."""
        idx = 0
        for char in pattern:
            idx = text.find(char, idx)
            if idx == -1:
                return False
            idx += 1
        return True

    def _on_select(self) -> None:
        """Handle Enter key - execute selected command."""
        item = self.command_list.currentItem()
        if item:
            self._execute_command(item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on command."""
        self._execute_command(item)

    def _execute_command(self, item: QListWidgetItem) -> None:
        """Execute the selected command."""
        cmd_id = item.data(Qt.ItemDataRole.UserRole)
        self.hide()

        # Find and execute handler
        for cmd in self._commands:
            if cmd.id == cmd_id and cmd.handler:
                cmd.handler()
                break

        self.command_selected.emit(cmd_id)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard navigation."""
        key = event.key()

        if key == Qt.Key.Key_Escape:
            self.hide()
        elif key == Qt.Key.Key_Down:
            current = self.command_list.currentRow()
            if current < self.command_list.count() - 1:
                self.command_list.setCurrentRow(current + 1)
        elif key == Qt.Key.Key_Up:
            current = self.command_list.currentRow()
            if current > 0:
                self.command_list.setCurrentRow(current - 1)
        else:
            super().keyPressEvent(event)
