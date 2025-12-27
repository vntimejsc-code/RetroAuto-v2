"""
RetroAuto v2 - Enhanced Command Palette

Quick access to all IDE commands via fuzzy search (Ctrl+Shift+P).

Features:
- Fuzzy search across all commands
- Recent files section
- Category-grouped commands
- Keyboard shortcuts displayed
- Settings and theme commands

Phase: IDE Next (Enhanced)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QKeyEvent, QFont
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)


@dataclass
class Command:
    """A command in the palette."""

    id: str
    name: str
    shortcut: str = ""
    category: str = "General"
    icon: str = ""  # Emoji icon
    handler: Callable[[], None] | None = None
    keywords: list[str] = field(default_factory=list)  # Additional search keywords


@dataclass  
class RecentFile:
    """A recently opened file."""
    path: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def display_name(self) -> str:
        return Path(self.path).name
    
    @property
    def relative_time(self) -> str:
        delta = datetime.now() - self.timestamp
        if delta.seconds < 60:
            return "just now"
        elif delta.seconds < 3600:
            return f"{delta.seconds // 60}m ago"
        elif delta.seconds < 86400:
            return f"{delta.seconds // 3600}h ago"
        else:
            return f"{delta.days}d ago"


class EnhancedCommandPalette(QDialog):
    """
    Enhanced Command Palette dialog (Ctrl+Shift+P).

    VS Code-style fuzzy command search with:
    - Recent files section
    - Category grouping
    - Score-based ranking
    - Rich display with icons and shortcuts

    Usage:
        palette = EnhancedCommandPalette(parent)
        palette.add_command(Command("file.save", "Save File", "Ctrl+S", "File", "💾"))
        palette.show_palette()
    """

    command_selected = Signal(str)  # Command ID
    file_selected = Signal(str)  # File path

    MAX_RECENT_FILES = 10
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._commands: list[Command] = []
        self._recent_files: list[RecentFile] = []
        self._filtered: list[Command] = []
        self._settings = QSettings("RetroAuto", "RetroAuto")

        self._load_recent_files()
        self._init_ui()
        self._register_default_commands()

    def _init_ui(self) -> None:
        self.setWindowTitle("Command Palette")
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with search input
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        self.mode_label = QLabel("🔍")
        header_layout.addWidget(self.mode_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search commands, files, or settings...")
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.returnPressed.connect(self._on_select)
        header_layout.addWidget(self.search_input)
        
        layout.addWidget(header)

        # Command list
        self.command_list = QListWidget()
        self.command_list.itemDoubleClicked.connect(self._on_item_clicked)
        self.command_list.setAlternatingRowColors(True)
        layout.addWidget(self.command_list)
        
        # Footer hint
        self.footer = QLabel("↑↓ Navigate • Enter Select • Esc Close • > Commands • @ Settings • : Files")
        self.footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.footer)

        # Style
        self.setStyleSheet("""
            EnhancedCommandPalette {
                background-color: #1e1e1e;
                border: 1px solid #454545;
                border-radius: 8px;
            }
            QLineEdit {
                background-color: transparent;
                color: #d4d4d4;
                border: none;
                padding: 8px;
                font-size: 14px;
            }
            QListWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 16px;
                border-bottom: 1px solid #2d2d30;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
            QListWidget::item:alternate {
                background-color: #252526;
            }
            QLabel {
                color: #808080;
                padding: 8px;
                font-size: 11px;
            }
        """)

    def _register_default_commands(self) -> None:
        """Register built-in IDE commands."""
        default_commands = [
            # File commands
            Command("file.new", "New File", "Ctrl+N", "File", "📄"),
            Command("file.open", "Open File", "Ctrl+O", "File", "📂"),
            Command("file.save", "Save File", "Ctrl+S", "File", "💾"),
            Command("file.saveAs", "Save As...", "Ctrl+Shift+S", "File", "💾"),
            Command("file.close", "Close File", "Ctrl+W", "File", "❌"),
            
            # Edit commands
            Command("edit.find", "Find", "Ctrl+F", "Edit", "🔍"),
            Command("edit.replace", "Find and Replace", "Ctrl+H", "Edit", "🔄"),
            Command("edit.goToLine", "Go to Line...", "Ctrl+G", "Edit", "📍"),
            Command("edit.format", "Format Document", "Ctrl+Shift+F", "Edit", "✨"),
            Command("edit.undo", "Undo", "Ctrl+Z", "Edit", "↩️"),
            Command("edit.redo", "Redo", "Ctrl+Y", "Edit", "↪️"),
            
            # Run commands
            Command("run.start", "Run Script", "F5", "Run", "▶️"),
            Command("run.stop", "Stop Script", "Shift+F5", "Run", "⏹️"),
            Command("run.debug", "Debug Script", "F9", "Run", "🐛"),
            
            # View commands
            Command("view.flowEditor", "Open Flow Editor", "Ctrl+Shift+V", "View", "🎨"),
            Command("view.problems", "Show Problems", "", "View", "⚠️"),
            Command("view.output", "Show Output", "", "View", "📋"),
            Command("view.commandPalette", "Command Palette", "Ctrl+Shift+P", "View", "🔮"),
            
            # Settings commands  
            Command("settings.theme.dark", "Theme: Modern Dark", "", "Settings", "🌙", keywords=["dark", "theme", "appearance"]),
            Command("settings.theme.light", "Theme: Modern Light", "", "Settings", "☀️", keywords=["light", "theme", "appearance"]),
            Command("settings.theme.retro", "Theme: Retro 95", "", "Settings", "🖥️", keywords=["retro", "win95", "classic"]),
            Command("settings.expertMode", "Toggle Expert Mode", "Ctrl+Shift+E", "Settings", "⚙️", keywords=["expert", "advanced", "beginner"]),
            
            # Debug commands
            Command("debug.toggleBreakpoint", "Toggle Breakpoint", "F9", "Debug", "🔴"),
            Command("debug.stepOver", "Step Over", "F10", "Debug", "⏭️"),
            Command("debug.stepInto", "Step Into", "F11", "Debug", "⬇️"),
            
            # Build commands
            Command("build.check", "Check Syntax", "Ctrl+Shift+C", "Build", "✓"),
            Command("build.run", "Build and Run", "Ctrl+F5", "Build", "🔨"),
            
            # Help commands
            Command("help.docs", "Documentation", "F1", "Help", "📖"),
            Command("help.shortcuts", "Keyboard Shortcuts", "Ctrl+K Ctrl+S", "Help", "⌨️"),
            Command("help.about", "About RetroAuto", "", "Help", "ℹ️"),
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

    def add_recent_file(self, file_path: str) -> None:
        """Add a file to recent files list."""
        # Remove if already exists
        self._recent_files = [f for f in self._recent_files if f.path != file_path]
        # Add to front
        self._recent_files.insert(0, RecentFile(path=file_path))
        # Trim to max
        self._recent_files = self._recent_files[:self.MAX_RECENT_FILES]
        # Save
        self._save_recent_files()

    def _load_recent_files(self) -> None:
        """Load recent files from settings."""
        paths = self._settings.value("recentFiles", [])
        if isinstance(paths, list):
            self._recent_files = [RecentFile(path=p) for p in paths if Path(p).exists()]

    def _save_recent_files(self) -> None:
        """Save recent files to settings."""
        paths = [f.path for f in self._recent_files]
        self._settings.setValue("recentFiles", paths)

    def show_palette(self, mode: str = "") -> None:
        """Show the command palette.
        
        Args:
            mode: Optional initial mode - ">" for commands, "@" for settings, ":" for files
        """
        self.search_input.clear()
        if mode:
            self.search_input.setText(mode)
        self._refresh_list()
        self.show()
        self.search_input.setFocus()

        # Center on parent
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + 80
            self.move(x, y)

    def _on_search(self, text: str) -> None:
        """Filter commands based on search text."""
        self._refresh_list(text.strip())

    def _refresh_list(self, filter_text: str = "") -> None:
        """Refresh the command list with smart filtering."""
        self.command_list.clear()
        self._filtered = []
        
        # Parse mode prefix
        mode = ""
        search_text = filter_text.lower()
        
        if filter_text.startswith(">"):
            mode = "commands"
            search_text = filter_text[1:].strip().lower()
            self.mode_label.setText("⌘")
        elif filter_text.startswith("@"):
            mode = "settings"
            search_text = filter_text[1:].strip().lower()
            self.mode_label.setText("⚙️")
        elif filter_text.startswith(":"):
            mode = "files"
            search_text = filter_text[1:].strip().lower()
            self.mode_label.setText("📁")
        else:
            self.mode_label.setText("🔍")
        
        # Show recent files if no filter and not in command mode
        if not filter_text and mode != "commands":
            self._add_section_header("Recent Files")
            for recent in self._recent_files[:5]:
                item = QListWidgetItem()
                item.setText(f"📄 {recent.display_name}  •  {recent.relative_time}")
                item.setData(Qt.ItemDataRole.UserRole, ("file", recent.path))
                self.command_list.addItem(item)
            
            self._add_section_header("Commands")
        
        # Filter commands
        scored_commands = []
        for cmd in self._commands:
            # Filter by mode
            if mode == "settings" and cmd.category != "Settings":
                continue
            if mode == "files":
                continue  # Only show files
                
            # Calculate match score
            score = self._calculate_score(search_text, cmd)
            if score > 0 or not search_text:
                scored_commands.append((score, cmd))
        
        # Sort by score (descending)
        scored_commands.sort(key=lambda x: x[0], reverse=True)
        
        # Show files if in file mode
        if mode == "files":
            for recent in self._recent_files:
                if search_text in recent.display_name.lower():
                    item = QListWidgetItem()
                    item.setText(f"📄 {recent.display_name}")
                    item.setData(Qt.ItemDataRole.UserRole, ("file", recent.path))
                    self.command_list.addItem(item)
            return
        
        # Group by category if no search
        if not search_text and mode != "settings":
            current_category = ""
            for _, cmd in scored_commands:
                if cmd.category != current_category:
                    current_category = cmd.category
                    self._add_section_header(current_category)
                self._add_command_item(cmd)
        else:
            for _, cmd in scored_commands:
                self._add_command_item(cmd)

        # Select first item
        if self.command_list.count() > 0:
            # Find first non-header item
            for i in range(self.command_list.count()):
                item = self.command_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole):
                    self.command_list.setCurrentRow(i)
                    break

    def _add_section_header(self, text: str) -> None:
        """Add a section header to the list."""
        item = QListWidgetItem()
        item.setText(text)
        item.setFlags(Qt.ItemFlag.NoItemFlags)  # Not selectable
        font = item.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() - 1)
        item.setFont(font)
        item.setForeground(Qt.GlobalColor.gray)
        self.command_list.addItem(item)

    def _add_command_item(self, cmd: Command) -> None:
        """Add a command item to the list."""
        self._filtered.append(cmd)
        
        item = QListWidgetItem()
        # Format: "Icon Name    [Shortcut]"
        display = f"{cmd.icon} {cmd.name}" if cmd.icon else cmd.name
        if cmd.shortcut:
            display += f"  [{cmd.shortcut}]"
        item.setText(display)
        item.setData(Qt.ItemDataRole.UserRole, ("command", cmd.id))
        self.command_list.addItem(item)

    def _calculate_score(self, pattern: str, cmd: Command) -> int:
        """Calculate match score with fuzzy matching."""
        if not pattern:
            return 100  # All commands match with no filter
        
        score = 0
        name_lower = cmd.name.lower()
        
        # Exact match in name
        if pattern in name_lower:
            score += 100
            # Bonus for match at start
            if name_lower.startswith(pattern):
                score += 50
        
        # Match in keywords
        for keyword in cmd.keywords:
            if pattern in keyword.lower():
                score += 30
        
        # Fuzzy match
        if self._fuzzy_match(pattern, name_lower):
            score += 20
        
        # Category match
        if pattern in cmd.category.lower():
            score += 10
            
        return score

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
        if item and item.data(Qt.ItemDataRole.UserRole):
            self._execute_item(item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on item."""
        if item.data(Qt.ItemDataRole.UserRole):
            self._execute_item(item)

    def _execute_item(self, item: QListWidgetItem) -> None:
        """Execute the selected item."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        item_type, item_id = data
        self.hide()

        if item_type == "file":
            self.file_selected.emit(item_id)
        elif item_type == "command":
            # Find and execute handler
            for cmd in self._commands:
                if cmd.id == item_id and cmd.handler:
                    cmd.handler()
                    break
            self.command_selected.emit(item_id)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard navigation."""
        key = event.key()

        if key == Qt.Key.Key_Escape:
            self.hide()
        elif key == Qt.Key.Key_Down:
            self._navigate_next()
        elif key == Qt.Key.Key_Up:
            self._navigate_prev()
        else:
            super().keyPressEvent(event)

    def _navigate_next(self) -> None:
        """Navigate to next selectable item."""
        current = self.command_list.currentRow()
        for i in range(current + 1, self.command_list.count()):
            item = self.command_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsSelectable:
                self.command_list.setCurrentRow(i)
                break

    def _navigate_prev(self) -> None:
        """Navigate to previous selectable item."""
        current = self.command_list.currentRow()
        for i in range(current - 1, -1, -1):
            item = self.command_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsSelectable:
                self.command_list.setCurrentRow(i)
                break


# Backwards compatibility alias
CommandPalette = EnhancedCommandPalette
