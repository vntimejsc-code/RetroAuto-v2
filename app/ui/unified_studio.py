"""
RetroAuto v2 - Unified Studio

Single unified window combining Visual and Code modes.
Replaces the separate MainWindow and IDEMainWindow.

Features:
- Mode tabs (Visual/Code/Debug)
- Shared sidebar panels
- Quick Actions toolbar
- Single entry point
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.ui.mode_tab_bar import ModeTabBar, StudioMode
from app.ui.quick_actions import QuickActionsToolbar
from app.ui.theme_engine import get_theme_manager
from app.ui.progressive_disclosure import get_disclosure_manager

# Import existing panels
from app.ui.project_explorer import ProjectExplorer
from app.ui.assets_panel import AssetsPanel
from app.ui.output_panel import OutputPanel
from app.ui.properties_panel import PropertiesPanel
from app.ui.code_editor import DSLCodeEditor
from app.ui.intellisense import IntelliSenseManager
from app.ui.command_palette import CommandPalette
from app.ui.flow_editor import FlowEditorWidget

from core.dsl.document import ScriptDocument


class UnifiedStudio(QMainWindow):
    """
    Unified Studio - Single window for all RetroAuto modes.
    
    Combines Visual scripting and Code editing in a tabbed interface
    with shared panels and consistent experience.
    """
    
    # Signals
    mode_changed = Signal(str)
    
    def __init__(self) -> None:
        super().__init__()
        
        # State
        self._current_file: Path | None = None
        self._is_modified = False
        self._document = ScriptDocument()
        self._settings = QSettings("RetroAuto", "UnifiedStudio")
        
        # Initialize
        self._init_ui()
        self._init_menu()
        self._init_shortcuts()
        self._init_theme()
        self._restore_state()
        
        self.setWindowTitle("RetroAuto Studio")
        self.setMinimumSize(1200, 800)
    
    def _init_ui(self) -> None:
        """Initialize the unified studio layout."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Mode Tab Bar
        self.mode_bar = ModeTabBar()
        self.mode_bar.mode_changed.connect(self._on_mode_changed)
        main_layout.addWidget(self.mode_bar)
        
        # Quick Actions Toolbar
        self.quick_actions = QuickActionsToolbar()
        self.quick_actions.run_requested.connect(self._run_script)
        self.quick_actions.pause_requested.connect(self._pause_script)
        self.quick_actions.stop_requested.connect(self._stop_script)
        self.quick_actions.save_requested.connect(self._save_file)
        main_layout.addWidget(self.quick_actions)
        
        # Main content area with splitters
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(4)
        
        # Create main horizontal splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left sidebar (shared across modes)
        self.sidebar = self._create_sidebar()
        self.main_splitter.addWidget(self.sidebar)
        
        # Center content (mode-specific, using QStackedWidget)
        self.mode_stack = QStackedWidget()
        self._create_mode_widgets()
        self.main_splitter.addWidget(self.mode_stack)
        
        # Right panel (shared) - Properties + Live Preview tabs
        self.right_tabs = QTabWidget()
        self.right_tabs.setTabPosition(QTabWidget.TabPosition.South)
        
        # Properties Inspector
        self.inspector = PropertiesPanel()
        self.right_tabs.addTab(self.inspector, "🔧 Properties")
        
        # Live Preview
        from app.ui.live_preview import LivePreviewPanel
        self.live_preview = LivePreviewPanel()
        self.live_preview.action_clicked.connect(self._on_preview_action_clicked)
        self.right_tabs.addTab(self.live_preview, "🔍 Preview")
        
        self.main_splitter.addWidget(self.right_tabs)
        
        # Set splitter proportions (1:4:1)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 4)
        self.main_splitter.setStretchFactor(2, 1)
        self.main_splitter.setSizes([200, 700, 200])
        
        # Vertical splitter (content | output)
        vsplitter = QSplitter(Qt.Orientation.Vertical)
        vsplitter.addWidget(self.main_splitter)
        
        # Output panel (shared)
        self.output = OutputPanel()
        vsplitter.addWidget(self.output)
        vsplitter.setStretchFactor(0, 4)
        vsplitter.setStretchFactor(1, 1)
        vsplitter.setSizes([600, 150])
        
        content_layout.addWidget(vsplitter)
        main_layout.addWidget(content)
        
        # Status bar
        self._init_status_bar()
        
        # Command Palette
        self._init_command_palette()
    
    def _create_sidebar(self) -> QTabWidget:
        """Create shared sidebar with Explorer and Assets tabs."""
        sidebar = QTabWidget()
        sidebar.setTabPosition(QTabWidget.TabPosition.South)
        sidebar.setMinimumWidth(180)
        sidebar.setMaximumWidth(350)
        
        # Project Explorer
        self.explorer = ProjectExplorer()
        self.explorer.file_opened.connect(self._on_file_opened)
        sidebar.addTab(self.explorer, "📂 Explorer")
        
        # Assets Panel
        self.assets_panel = AssetsPanel()
        sidebar.addTab(self.assets_panel, "🖼️ Assets")
        
        return sidebar
    
    def _create_mode_widgets(self) -> None:
        """Create widgets for each mode."""
        # Visual Mode - Flow Editor placeholder
        self.visual_widget = self._create_visual_mode()
        self.mode_stack.addWidget(self.visual_widget)
        
        # Code Mode - DSL Code Editor
        self.code_widget = self._create_code_mode()
        self.mode_stack.addWidget(self.code_widget)
        
        # Debug Mode - Debug View placeholder
        self.debug_widget = self._create_debug_mode()
        self.mode_stack.addWidget(self.debug_widget)
    
    def _create_visual_mode(self) -> QWidget:
        """Create Visual mode content widget with Flow Editor."""
        # Integrate FlowEditorWidget for visual scripting
        self.flow_editor = FlowEditorWidget()
        return self.flow_editor
    
    def _create_code_mode(self) -> QWidget:
        """Create Code mode content widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Code Editor
        self.code_editor = DSLCodeEditor()
        self.code_editor.textChanged.connect(self._on_code_changed)
        
        # FindBar (hidden by default)
        from app.ui.find_bar import FindBar
        self.find_bar = FindBar(self.code_editor)
        layout.addWidget(self.find_bar)
        
        layout.addWidget(self.code_editor)
        
        # Initialize IntelliSense
        self._intellisense = IntelliSenseManager(self.code_editor)
        
        return widget
    
    def _create_debug_mode(self) -> QWidget:
        """Create Debug mode content widget with debug panels."""
        from app.ui.debug_mode import DebugModeWidget
        self.debug_mode_widget = DebugModeWidget()
        return self.debug_mode_widget
    
    def _init_status_bar(self) -> None:
        """Initialize status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Mode indicator
        self.mode_label = QLabel("Mode: Visual")
        self.status_bar.addWidget(self.mode_label)
        
        # Cursor position
        self.cursor_label = QLabel("Ln 1, Col 1")
        self.status_bar.addPermanentWidget(self.cursor_label)
        
        # Status message
        self.status_bar.showMessage("Ready")
    
    def _init_menu(self) -> None:
        """Initialize menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        visual_action = QAction("🎨 &Visual Mode", self)
        visual_action.setShortcut(QKeySequence("Ctrl+1"))
        visual_action.triggered.connect(lambda: self.mode_bar.set_visual_mode())
        view_menu.addAction(visual_action)
        
        code_action = QAction("📝 &Code Mode", self)
        code_action.setShortcut(QKeySequence("Ctrl+2"))
        code_action.triggered.connect(lambda: self.mode_bar.set_code_mode())
        view_menu.addAction(code_action)
        
        debug_action = QAction("🔧 &Debug Mode", self)
        debug_action.setShortcut(QKeySequence("Ctrl+3"))
        debug_action.triggered.connect(lambda: self.mode_bar.set_debug_mode())
        view_menu.addAction(debug_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _init_shortcuts(self) -> None:
        """Initialize keyboard shortcuts."""
        # Command Palette
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        shortcut.activated.connect(self._show_command_palette)
        
        # Mode shortcuts
        QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(
            lambda: self.mode_bar.set_visual_mode()
        )
        QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(
            lambda: self.mode_bar.set_code_mode()
        )
        QShortcut(QKeySequence("Ctrl+3"), self).activated.connect(
            lambda: self.mode_bar.set_debug_mode()
        )
        
        # Run shortcuts
        QShortcut(QKeySequence("F5"), self).activated.connect(self._run_script)
        QShortcut(QKeySequence("Shift+F5"), self).activated.connect(self._stop_script)
        
        # Shortcuts overlay (Ctrl+?)
        from app.ui.shortcuts_overlay import register_shortcuts_overlay
        self._shortcuts_overlay = register_shortcuts_overlay(self)
        
        # Find shortcuts (Ctrl+F, F3)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self._show_find_bar)
        QShortcut(QKeySequence("F3"), self).activated.connect(self._find_next)
        QShortcut(QKeySequence("Shift+F3"), self).activated.connect(self._find_previous)
    
    def _init_command_palette(self) -> None:
        """Initialize Command Palette."""
        self._command_palette = CommandPalette(self)
        
        # Wire up handlers
        self._command_palette.set_command_handler("file.new", self._new_file)
        self._command_palette.set_command_handler("file.open", self._open_file)
        self._command_palette.set_command_handler("file.save", self._save_file)
        self._command_palette.set_command_handler("run.start", self._run_script)
        self._command_palette.set_command_handler("run.stop", self._stop_script)
    
    def _init_theme(self) -> None:
        """Apply saved theme."""
        get_theme_manager().apply_theme()
    
    def _restore_state(self) -> None:
        """Restore window state from settings."""
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self._settings.value("windowState")
        if state:
            self.restoreState(state)
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close."""
        if self._is_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Save changes before closing?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self._save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        
        # Save state
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("windowState", self.saveState())
        
        event.accept()
    
    # ─────────────────────────────────────────────────────────────
    # Mode Operations
    # ─────────────────────────────────────────────────────────────
    
    def _on_mode_changed(self, mode: str) -> None:
        """Handle mode change from tab bar."""
        if mode == "visual":
            self.mode_stack.setCurrentIndex(0)
            self.mode_label.setText("Mode: Visual")
        elif mode == "code":
            self.mode_stack.setCurrentIndex(1)
            self.mode_label.setText("Mode: Code")
        elif mode == "debug":
            self.mode_stack.setCurrentIndex(2)
            self.mode_label.setText("Mode: Debug")
        
        self.mode_changed.emit(mode)
        self.status_bar.showMessage(f"Switched to {mode.title()} mode", 2000)
    
    # ─────────────────────────────────────────────────────────────
    # File Operations
    # ─────────────────────────────────────────────────────────────
    
    def _new_file(self) -> None:
        """Create new file."""
        if self._is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes", "Save changes?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self._save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        self.code_editor.set_code("")
        self._current_file = None
        self._is_modified = False
        self._update_title()
    
    def _open_file(self) -> None:
        """Open file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Script",
            str(Path.home()),
            "DSL Scripts (*.dsl);;All Files (*.*)"
        )
        if file_path:
            self._load_file(Path(file_path))
    
    def _on_file_opened(self, file_path: str, file_type: str) -> None:
        """Handle file opened from explorer."""
        self._load_file(Path(file_path))
    
    def _load_file(self, path: Path) -> None:
        """Load file content."""
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8")
                self.code_editor.set_code(content)
                self._current_file = path
                self._is_modified = False
                self._update_title()
                self.output.log_info(f"Opened: {path.name}")
                
                # Switch to code mode when opening a file
                self.mode_bar.set_code_mode()
            except Exception as e:
                self.output.log_error(f"Error opening file: {e}")
    
    def _save_file(self) -> None:
        """Save current file."""
        if not self._current_file:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Script",
                str(Path.home()),
                "DSL Scripts (*.dsl);;All Files (*.*)"
            )
            if not file_path:
                return
            self._current_file = Path(file_path)
        
        try:
            content = self.code_editor.get_code()
            self._current_file.write_text(content, encoding="utf-8")
            self._is_modified = False
            self._update_title()
            self.output.log_info(f"Saved: {self._current_file.name}")
            self.status_bar.showMessage("File saved", 3000)
        except Exception as e:
            self.output.log_error(f"Error saving: {e}")
    
    def _on_code_changed(self) -> None:
        """Handle code changes."""
        if not self._is_modified:
            self._is_modified = True
            self._update_title()
        
        # Update live preview
        if hasattr(self, 'live_preview'):
            self.live_preview.set_code(self.code_editor.get_code())
    
    def _on_preview_action_clicked(self, line_number: int) -> None:
        """Handle click on action in live preview - go to line."""
        # Switch to code mode and go to line
        self.mode_bar.set_code_mode()
        cursor = self.code_editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        for _ in range(line_number - 1):
            cursor.movePosition(cursor.MoveOperation.Down)
        self.code_editor.setTextCursor(cursor)
        self.code_editor.centerCursor()
        self.code_editor.setFocus()
    
    def _update_title(self) -> None:
        """Update window title."""
        title = "RetroAuto Studio"
        if self._current_file:
            title = f"{self._current_file.name} - {title}"
        if self._is_modified:
            title = f"● {title}"
        self.setWindowTitle(title)
    
    # ─────────────────────────────────────────────────────────────
    # Script Operations
    # ─────────────────────────────────────────────────────────────
    
    def _run_script(self) -> None:
        """Run the current script."""
        self.output.log_info("Running script...")
        self.quick_actions.set_running()
        self.status_bar.showMessage("Running...")
        # TODO: Integrate with EngineWorker
    
    def _pause_script(self) -> None:
        """Pause/resume script."""
        self.output.log_info("Script paused")
        self.quick_actions.set_paused()
    
    def _stop_script(self) -> None:
        """Stop script."""
        self.output.log_warning("Script stopped")
        self.quick_actions.set_idle()
        self.status_bar.showMessage("Stopped")
    
    # ─────────────────────────────────────────────────────────────
    # UI Operations
    # ─────────────────────────────────────────────────────────────
    
    def _show_command_palette(self) -> None:
        """Show command palette."""
        self._command_palette.show_palette()
    
    def _show_find_bar(self) -> None:
        """Show find bar in code mode."""
        self.mode_bar.set_code_mode()
        if hasattr(self, 'find_bar'):
            self.find_bar.show_bar()
    
    def _find_next(self) -> None:
        """Find next match."""
        if hasattr(self, 'find_bar') and self.find_bar.isVisible():
            self.find_bar.find_next()
    
    def _find_previous(self) -> None:
        """Find previous match."""
        if hasattr(self, 'find_bar') and self.find_bar.isVisible():
            self.find_bar.find_previous()
    
    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About RetroAuto Studio",
            "RetroAuto Studio v2.23\n\n"
            "Unified scripting environment for desktop automation.\n\n"
            "© 2024 RetroAuto Team"
        )


def run_studio() -> None:
    """Entry point for Unified Studio."""
    import sys
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Apply theme
    get_theme_manager().apply_theme()
    
    studio = UnifiedStudio()
    studio.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_studio()
