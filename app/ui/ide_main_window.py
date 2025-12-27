"""
RetroAuto v2 - MacroIDE 95 Main Window

The main IDE window with Win95/98 styling.
Layout:
  ┌─────────────────────────────────────────────────────────┐
  │ Menu Bar                                                │
  ├─────────────────────────────────────────────────────────┤
  │ Toolbar                                                 │
  ├─────────┬───────────────────────────────┬───────────────┤
  │ Explorer│         Code Editor           │   Inspector   │
  │         │                               │               │
  ├─────────┴───────────────────────────────┴───────────────┤
  │ Output Panel (Output | Problems)                        │
  ├─────────────────────────────────────────────────────────┤
  │ Status Bar: Ln X, Col Y | Ready                         │
  └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.ui.code_editor import DSLCodeEditor
from app.ui.interrupts_panel import InterruptsPanel
from app.ui.output_panel import OutputPanel
from app.ui.project_explorer import ProjectExplorer
from app.ui.properties_panel import PropertiesPanel
from app.ui.theme_engine import get_theme_manager, get_available_themes, ThemeType
from app.ui.progressive_disclosure import get_disclosure_manager, UserLevel
from core.dsl.formatter import format_code
from core.dsl.parser import Parser
from core.dsl.semantic import analyze


class IDEMainWindow(QMainWindow):
    """
    MacroIDE 95 - Main IDE Window.

    Features:
    - Project explorer with folder navigation
    - DSL code editor with syntax highlighting
    - Property inspector
    - Output/Problems panels
    - Win95/98 classic styling
    """

    # Signals
    code_saved = Signal(str)  # Emits the saved code content

    def __init__(self) -> None:
        super().__init__()
        self._current_file: Path | None = None
        self._is_modified = False
        self._script = None  # Current loaded script
        self._intellisense = None  # Will be initialized after editor
        self._command_palette = None  # Command Palette
        self._init_ui()
        self._init_intellisense()
        self._init_command_palette()
        self._init_menu()
        self._init_toolbar()
        self._init_status_bar()
        self._init_shortcuts()  # Keyboard shortcuts
        self._connect_signals()
        self._init_theme()  # Apply saved theme
        self._restore_state()

    def _init_ui(self) -> None:
        """Initialize the main UI layout."""
        self.setWindowTitle("MacroIDE 95 - RetroAuto")
        self.setMinimumSize(1024, 768)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Main vertical splitter (editor area | output)
        vsplitter = QSplitter(Qt.Orientation.Vertical)

        # Top horizontal splitter (explorer | editor | inspector)
        hsplitter = QSplitter(Qt.Orientation.Horizontal)

        # Project Explorer (already has header)
        # Left Panel (Explorer | Assets | Interrupts)
        self.left_tabs = QTabWidget()
        self.left_tabs.setTabPosition(QTabWidget.TabPosition.South)

        # Explorer Tab
        self.explorer = ProjectExplorer()
        self.left_tabs.addTab(self.explorer, "📂 Explorer")

        # Assets Tab (Placeholder for now, or move AssetsPanel here later if desired)
        # For now, just keep Explorer and Interrupts

        # Interrupts Tab
        self.interrupts_panel = InterruptsPanel()
        self.left_tabs.addTab(self.interrupts_panel, "⚡ Interrupts")

        hsplitter.addWidget(self.left_tabs)

        # Code Editor with header
        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)

        editor_header = QLabel("Code Editor")
        editor_header.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                padding: 4px;
                background-color: #0078d4;
                color: #FFFFFF;
            }
        """
        )
        editor_layout.addWidget(editor_header)

        self.editor = DSLCodeEditor()
        # Connect asset provider for Asset Peek
        self.editor.set_asset_provider(self._get_asset_path)
        editor_layout.addWidget(self.editor)

        hsplitter.addWidget(editor_container)

        # Inspector
        self.inspector = PropertiesPanel()
        hsplitter.addWidget(self.inspector)

        # Set proportions (1:3:1)
        hsplitter.setStretchFactor(0, 1)
        hsplitter.setStretchFactor(1, 3)
        hsplitter.setStretchFactor(2, 1)
        hsplitter.setSizes([200, 600, 200])

        vsplitter.addWidget(hsplitter)

        # Output panel
        self.output = OutputPanel()
        vsplitter.addWidget(self.output)

        # Set proportions (3:1)
        vsplitter.setStretchFactor(0, 3)
        vsplitter.setStretchFactor(1, 1)
        vsplitter.setSizes([500, 200])

        main_layout.addWidget(vsplitter)

    def _init_intellisense(self) -> None:
        """Initialize IntelliSense for code editor."""
        from app.ui.intellisense import IntelliSenseManager

        self._intellisense = IntelliSenseManager(self.editor)

    def _init_command_palette(self) -> None:
        """Initialize Command Palette (Ctrl+Shift+P)."""
        from app.ui.command_palette import CommandPalette

        self._command_palette = CommandPalette(self)

        # Wire up command handlers
        self._command_palette.set_command_handler("file.new", self._new_project)
        self._command_palette.set_command_handler("file.open", self._open_single_file)
        self._command_palette.set_command_handler("file.save", self._save_file)
        self._command_palette.set_command_handler("file.saveAs", self._save_file_as)
        self._command_palette.set_command_handler("edit.find", self._show_find_bar)
        self._command_palette.set_command_handler("edit.goToLine", self._goto_line_dialog)
        self._command_palette.set_command_handler("edit.format", self._format_document)
        self._command_palette.set_command_handler("run.start", self._run_script)
        self._command_palette.set_command_handler("run.stop", self._stop_script)
        self._command_palette.set_command_handler("build.check", self._check_syntax)

    def _init_menu(self) -> None:
        """Initialize menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New Project", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)

        open_project_action = QAction("Open &Project...", self)
        open_project_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_project_action.triggered.connect(self._open_project)
        file_menu.addAction(open_project_action)

        open_file_action = QAction("&Open File...", self)
        open_file_action.setShortcut(QKeySequence.StandardKey.Open)
        open_file_action.triggered.connect(self._open_single_file)
        file_menu.addAction(open_file_action)

        file_menu.addSeparator()

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        format_action = QAction("&Format Document", self)
        format_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        format_action.triggered.connect(self._format_document)
        edit_menu.addAction(format_action)

        # Run menu
        run_menu = menubar.addMenu("&Run")

        run_action = QAction("▶ &Run", self)
        run_action.setShortcut(QKeySequence("F5"))
        run_action.triggered.connect(self._run_script)
        run_menu.addAction(run_action)

        stop_action = QAction("■ &Stop", self)
        stop_action.setShortcut(QKeySequence("F6"))
        stop_action.triggered.connect(self._stop_script)
        run_menu.addAction(stop_action)

        run_menu.addSeparator()

        check_action = QAction("✓ &Check Syntax", self)
        check_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        check_action.triggered.connect(self._check_syntax)
        run_menu.addAction(check_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        flow_editor_action = QAction("🎨 &Flow Editor", self)
        flow_editor_action.setShortcut(QKeySequence("Ctrl+Shift+V"))
        flow_editor_action.triggered.connect(self._show_flow_editor)
        view_menu.addAction(flow_editor_action)

        view_menu.addSeparator()

        # Theme submenu
        theme_menu = view_menu.addMenu("🎨 &Theme")
        for theme_value, theme_name in get_available_themes():
            action = QAction(theme_name, self)
            action.setCheckable(True)
            if get_theme_manager().current_theme.value == theme_value:
                action.setChecked(True)
            action.triggered.connect(lambda checked, t=theme_value: self._switch_theme(t))
            theme_menu.addAction(action)

        view_menu.addSeparator()

        # Expert Mode toggle
        self._expert_mode_action = QAction("⚙️ &Expert Mode", self)
        self._expert_mode_action.setCheckable(True)
        self._expert_mode_action.setChecked(get_disclosure_manager().is_expert)
        self._expert_mode_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self._expert_mode_action.triggered.connect(self._toggle_expert_mode)
        view_menu.addAction(self._expert_mode_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About MacroIDE 95", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_toolbar(self) -> None:
        """Initialize toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # New
        new_btn = QAction("📄 New", self)
        new_btn.setToolTip("New Project (Ctrl+N)")
        new_btn.triggered.connect(self._new_project)
        toolbar.addAction(new_btn)

        # Open Folder
        open_folder_btn = QAction("📂 Folder", self)
        open_folder_btn.setToolTip("Open Project Folder (Ctrl+Shift+O)")
        open_folder_btn.triggered.connect(self._open_project)
        toolbar.addAction(open_folder_btn)

        # Open File
        open_file_btn = QAction("📄 File", self)
        open_file_btn.setToolTip("Open File (Ctrl+O)")
        open_file_btn.triggered.connect(self._open_single_file)
        toolbar.addAction(open_file_btn)

        # Save
        save_btn = QAction("💾 Save", self)
        save_btn.setToolTip("Save (Ctrl+S)")
        save_btn.triggered.connect(self._save_file)
        toolbar.addAction(save_btn)

        toolbar.addSeparator()

        # Run
        self.run_btn = QAction("▶ Run", self)
        self.run_btn.setToolTip("Run Script (F5)")
        self.run_btn.triggered.connect(self._run_script)
        toolbar.addAction(self.run_btn)

        # Stop
        self.stop_btn = QAction("■ Stop", self)
        self.stop_btn.setToolTip("Stop Script (F6)")
        self.stop_btn.setEnabled(False)
        self.stop_btn.triggered.connect(self._stop_script)
        toolbar.addAction(self.stop_btn)

        toolbar.addSeparator()

        # Check
        check_btn = QAction("✓ Check", self)
        check_btn.setToolTip("Check Syntax (Ctrl+Shift+C)")
        check_btn.triggered.connect(self._check_syntax)
        toolbar.addAction(check_btn)

        # Format
        format_btn = QAction("📋 Format", self)
        format_btn.setToolTip("Format Code (Ctrl+Shift+F)")
        format_btn.triggered.connect(self._format_document)
        toolbar.addAction(format_btn)

    def _init_status_bar(self) -> None:
        """Initialize status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Cursor position
        self.cursor_label = QLabel("Ln 1, Col 1")
        self.cursor_label.setMinimumWidth(100)
        self.status_bar.addPermanentWidget(self.cursor_label)

        # Status message
        self.status_bar.showMessage("Ready")

    def _init_shortcuts(self) -> None:
        """Initialize keyboard shortcuts."""
        # Run Script - Ctrl+R (alternative to F5)
        run_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        run_shortcut.activated.connect(self._run_script)

        # Stop Script - Ctrl+. (Escape-like stop)
        stop_shortcut = QShortcut(QKeySequence("Ctrl+."), self)
        stop_shortcut.activated.connect(self._stop_script)

        # Toggle Breakpoint - F9
        breakpoint_shortcut = QShortcut(QKeySequence("F9"), self)
        breakpoint_shortcut.activated.connect(self._toggle_breakpoint)

        # Trigger IntelliSense - Ctrl+Space
        autocomplete_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        autocomplete_shortcut.activated.connect(self._trigger_autocomplete)

        # Quick check - Ctrl+Shift+B (build/check)
        check_shortcut = QShortcut(QKeySequence("Ctrl+Shift+B"), self)
        check_shortcut.activated.connect(self._check_syntax)

        # Go To Line - Ctrl+G
        goto_line_shortcut = QShortcut(QKeySequence("Ctrl+G"), self)
        goto_line_shortcut.activated.connect(self._goto_line_dialog)

        # Find - Ctrl+F
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self._show_find_bar)

        # Command Palette - Ctrl+Shift+P
        palette_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        palette_shortcut.activated.connect(self._show_command_palette)

    def _show_command_palette(self) -> None:
        """Show Command Palette (Ctrl+Shift+P)."""
        if self._command_palette:
            self._command_palette.show_palette()

    def _toggle_breakpoint(self) -> None:
        """Toggle breakpoint on current line."""
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        # TODO: Implement breakpoint toggle in debugger
        self.output.log_info(f"Toggle breakpoint at line {line}")

    def _trigger_autocomplete(self) -> None:
        """Trigger autocomplete popup."""
        if self._intellisense:
            self._intellisense.show_completions()
        else:
            self.output.log_warning("IntelliSense not available")

    def _connect_signals(self) -> None:
        """Connect signals from child widgets."""
        # Explorer
        self.explorer.file_opened.connect(self._open_file)

        # Structure Panel
        # Structure Panel
        from app.ui.structure_panel import StructurePanel

        self.structure_panel = StructurePanel()
        self.structure_panel.navigate_requested.connect(self._navigate_to_line)

        # Structure Dock
        structure_dock = QDockWidget("Structure", self)
        structure_dock.setObjectName("StructureDock")
        structure_dock.setWidget(self.structure_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, structure_dock)

        # Try to tabify with Explorer if exists
        explorer_dock = self.findChild(QDockWidget, "ExplorerDock")
        if explorer_dock:
            self.tabifyDockWidget(explorer_dock, structure_dock)

        # Editor
        self.editor.content_changed.connect(self._on_code_changed)
        self.editor.cursor_position_changed.connect(self._on_cursor_moved)

        # Output
        self.output.diagnostic_clicked.connect(self._goto_diagnostic)

        # Interrupts Panel
        self.interrupts_panel.rule_selected.connect(self._on_rule_selected)
        self.interrupts_panel.rule_changed.connect(self._on_rules_changed)

        # Inspector (PropertiesPanel doesn't need signal connection in IDE)

    def _restore_state(self) -> None:
        """Restore window state from settings."""
        settings = QSettings("RetroAuto", "MacroIDE95")

        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        last_project = settings.value("last_project")
        if last_project and Path(last_project).exists():
            self.explorer.load_project(Path(last_project))

        # Restore interrupts if script loaded
        if self._script:
            self.interrupts_panel.set_rules(self._script.interrupts)

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
        settings = QSettings("RetroAuto", "MacroIDE95")
        settings.setValue("geometry", self.saveGeometry())

        event.accept()

    # ─────────────────────────────────────────────────────────────
    # File Operations
    # ─────────────────────────────────────────────────────────────

    def _new_project(self) -> None:
        """Create a new project."""
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            path = Path(folder)
            # Create standard structure
            (path / "assets").mkdir(exist_ok=True)
            (path / "scripts").mkdir(exist_ok=True)
            (path / "flows").mkdir(exist_ok=True)

            # Create main.dsl with new RetroScript syntax
            main_dsl = path / "scripts" / "main.dsl"
            if not main_dsl.exists():
                main_dsl.write_text(
                    """// main.dsl - RetroScript 9.0
// Press F5 to run, F6 to stop

@config
  timeout = 30s
  loop_limit = 1000
  click_delay = 50..100ms
  on_error = pause

@hotkeys
  start = "F5"
  stop = "F6"

@main:
  log "Script started..."

  // Example: Wait for a button and click it
  $target = find(login_btn, timeout: 10s)
  match $target:
    Found(pos, score):
      log "Found button at {pos} (score: {score}%)"
      click pos
    NotFound:
      log.warn "Button not found, skipping..."

  // Loop example
  repeat 5:
    $item = find(item_icon)
    if $item.found:
      click $item.pos
      sleep 500ms
  end

  log "Script completed!"

@interrupts:
  // Handle common popups
  close_popup -> press Escape
  error_dialog -> click ok_btn
""",
                    encoding="utf-8",
                )

            self.explorer.load_project(path)
            self._open_file(str(main_dsl), "script")
            self.output.log_success(f"Created new project: {path.name}")

    def _open_project(self) -> None:
        """Open an existing project folder."""
        folder = QFileDialog.getExistingDirectory(self, "Open Project Folder")
        if folder:
            path = Path(folder)
            self.explorer.load_project(path)

            # Save as last project
            settings = QSettings("RetroAuto", "MacroIDE95")
            settings.setValue("last_project", str(path))

            self.output.log_info(f"Opened project: {path.name}")

    def _open_single_file(self) -> None:
        """Open a file directly (DSL, YAML, JSON, TXT)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "DSL Scripts (*.dsl);;"
            "YAML Files (*.yaml *.yml);;"
            "JSON Files (*.json);;"
            "Text Files (*.txt);;"
            "All Files (*)",
        )
        if file_path:
            # Determine file type from extension
            ext = Path(file_path).suffix.lower()
            if ext == ".dsl":
                file_type = "script"
            elif ext in (".yaml", ".yml"):
                file_type = "yaml"
            elif ext == ".json":
                file_type = "json"
            else:
                file_type = "text"
            self._open_file(file_path, file_type)

    def _open_file(self, file_path: str, file_type: str) -> None:
        """Open a file in the editor."""
        if self._is_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Save changes before opening another file?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self._save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        path = Path(file_path)
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8")
                self.editor.set_code(content)
                self._current_file = path
                self._is_modified = False
                self._update_title()
                self.output.log_info(f"Opened: {path.name}")

                # Check syntax on open
                self._check_syntax()
            except Exception as e:
                self.output.log_error(f"Error opening file: {e}")

    def _save_file(self) -> None:
        """Save the current file."""
        if not self._current_file:
            self._save_file_as()
            return

        try:
            # Ensure parent directory exists
            self._current_file.parent.mkdir(parents=True, exist_ok=True)

            content = self.editor.get_code()
            self._current_file.write_text(content, encoding="utf-8")
            self._is_modified = False
            self._update_title()
            self.status_bar.showMessage("Saved", 3000)
            self.output.log_success(f"Saved: {self._current_file.name}")

            # Emit signal for sync with MainWindow
            self.code_saved.emit(content)
        except Exception as e:
            self.output.log_error(f"Error saving: {e}")

    def _save_file_as(self) -> None:
        """Save as new file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save As",
            str(self._current_file or ""),
            "DSL Files (*.dsl);;All Files (*)",
        )
        if file_path:
            self._current_file = Path(file_path)
            self._save_file()

    # ─────────────────────────────────────────────────────────────
    # Code Operations
    # ─────────────────────────────────────────────────────────────

    def _format_document(self) -> None:
        """Format the current document."""
        code = self.editor.get_code()
        formatted = format_code(code)
        if formatted != code:
            cursor_pos = self.editor.get_cursor_position()
            self.editor.set_code(formatted)
            self.editor.goto_line(*cursor_pos)
            self.output.log_info("Document formatted")
        else:
            self.output.log_info("Document already formatted")

    def _check_syntax(self) -> None:
        """Check syntax and update problems panel."""
        code = self.editor.get_code()
        parser = Parser(code)
        program = parser.parse()

        # Get parse errors
        diagnostics = list(parser.errors)

        # Add semantic errors
        if not parser.errors:
            # TODO: Get known assets from project
            semantic_errors = analyze(program, known_assets=[])
            diagnostics.extend(semantic_errors)

        file_name = self._current_file.name if self._current_file else "untitled"
        self.output.set_diagnostics(diagnostics, file_name)

        if diagnostics:
            errors = sum(1 for d in diagnostics if d.severity.value == "error")
            warnings = len(diagnostics) - errors
            self.output.log_warning(f"Found {errors} error(s), {warnings} warning(s)")
        else:
            self.output.log_success("No problems found")

    def _goto_diagnostic(self, file_path: str, line: int, col: int) -> None:
        """Go to diagnostic location in editor."""
        self.editor.goto_line(line, col)
        self.editor.setFocus()

    def _goto_line_dialog(self) -> None:
        """Show Go To Line dialog (Ctrl+G)."""
        from app.ui.editor_dialogs import GoToLineDialog

        max_line = self.editor.blockCount()
        line = GoToLineDialog.get_line(self, max_line)
        if line is not None:
            self.editor.goto_line(line)
            self.editor.setFocus()

    def _show_find_bar(self) -> None:
        """Show find bar (Ctrl+F)."""
        # Get selected text for initial search
        cursor = self.editor.textCursor()
        selected = cursor.selectedText() if cursor.hasSelection() else ""

        # TODO: Integrate FindBar into editor widget
        # For now, use simple input dialog
        from PySide6.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(self, "Find", "Search for:", text=selected)
        if ok and text:
            self._find_and_highlight(text)

    def _find_and_highlight(self, text: str) -> None:
        """Find and highlight text in editor."""
        from PySide6.QtGui import QTextDocument

        # Find first occurrence
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)

        found = self.editor.find(text)
        if found:
            self.output.log_info(f"Found: '{text}'")
        else:
            self.output.log_warning(f"Not found: '{text}'")

    # ─────────────────────────────────────────────────────────────
    # Run Operations
    # ─────────────────────────────────────────────────────────────

    def _run_script(self) -> None:
        """Run the current script using EngineWorker."""
        self.output.log_info("Running script...")
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_bar.showMessage("Running...")

        # Parse current code to Script
        from core.dsl.adapter import ir_to_script
        from core.dsl.document import ScriptDocument

        try:
            # Create document from current code
            doc = ScriptDocument()
            doc.update_from_code(self.editor.get_code(), source="run")

            # Check for parse errors
            if doc.errors:
                self.output.log_error(f"Parse errors: {doc.errors}")
                self._stop_script()
                return

            if not doc.ir.is_valid:
                self.output.log_error("Invalid IR - cannot run")
                self._stop_script()
                return

            # Convert IR to Script
            script = ir_to_script(doc.ir)

            # Create and start engine worker
            from app.ui.engine_worker import EngineWorker

            self._engine = EngineWorker()
            self._engine.step_started.connect(self._on_step_started)
            self._engine.step_completed.connect(self._on_step_completed)
            self._engine.flow_completed.connect(self._on_flow_completed)
            self._engine.error_occurred.connect(self._on_engine_error)
            self._engine.finished.connect(self._on_engine_finished)

            # Set the script and start
            self._engine._script = script
            self._engine._setup_context()
            self._engine.start()
            self.output.log_info("Engine started")

        except Exception as e:
            self.output.log_error(f"Failed to start: {e}")
            self._stop_script()

    def _stop_script(self) -> None:
        """Stop the running script."""
        if hasattr(self, '_engine') and self._engine:
            if self._engine.context:
                from core.engine.context import EngineState
                self._engine.context.set_state(EngineState.STOPPING)
            self._engine.wait(timeout=2000)  # Wait up to 2 seconds
            self._engine = None

        self.output.log_warning("Script stopped")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_bar.showMessage("Stopped")

    def _on_step_started(self, flow: str, index: int, action_type: str) -> None:
        """Handle step started signal from engine."""
        self.output.log_info(f"[{flow}] Step {index}: {action_type}")

    def _on_step_completed(self, flow: str, index: int, elapsed_ms: int) -> None:
        """Handle step completed signal from engine."""
        self.output.log_debug(f"[{flow}] Step {index} done in {elapsed_ms}ms")

    def _on_flow_completed(self, flow: str, success: bool) -> None:
        """Handle flow completed signal from engine."""
        if success:
            self.output.log_info(f"✅ Flow '{flow}' completed")
        else:
            self.output.log_warning(f"⚠️ Flow '{flow}' stopped")

    def _on_engine_error(self, message: str) -> None:
        """Handle error signal from engine."""
        self.output.log_error(f"❌ {message}")

    def _on_engine_finished(self) -> None:
        """Handle engine thread finished."""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_bar.showMessage("Ready")

    def _show_flow_editor(self) -> None:
        """Show the visual flow editor in a new window."""
        from PySide6.QtWidgets import QMainWindow

        from app.ui.flow_editor import FlowEditorWidget
        from core.dsl.document import ScriptDocument

        # Parse current code to IR
        code = self.editor.get_code()
        doc = ScriptDocument()
        doc.update_from_code(code)

        if not doc.ir.is_valid:
            QMessageBox.warning(
                self,
                "Parse Error",
                "Cannot open Flow Editor because the code contains syntax errors.\nPlease fix the errors and try again.",
            )
            return

        # Convert IR to Actions
        try:
            # Flatten all flows into a single list for now (or handle multiple flows)
            # FlowEditor usually expects a list of actions for a single flow.
            # Let's use the 'main' flow or the first flow.
            target_flow = doc.ir.get_flow("main") or (doc.ir.flows[0] if doc.ir.flows else None)

            if not target_flow:
                current_actions = []
            else:
                # We need a converter from IR to Actions (GUI objects)
                # core.dsl.adapter.ir_to_action ? No, adapter is for single action
                # Let's grab the adapter
                from core.dsl.adapter import ir_to_action

                current_actions = [ir_to_action(a) for a in target_flow.actions]

        except Exception as e:
            QMessageBox.critical(
                self, "Conversion Error", f"Failed to convert code to actions: {e}"
            )
            return

        # Create flow editor window
        self._flow_window = QMainWindow(self)
        self._flow_window.setWindowTitle("🎨 Visual Flow Editor - RetroAuto")
        self._flow_window.setMinimumSize(800, 600)

        flow_widget = FlowEditorWidget(actions=current_actions)
        flow_widget.actions_exported.connect(self._on_flow_actions_exported)

        self._flow_window.setCentralWidget(flow_widget)

        self._flow_window.show()
        self.output.log_info("Opened Visual Flow Editor")

    def _on_flow_actions_exported(self, actions: list) -> None:
        """Handle actions exported from flow editor."""
        from core.dsl.adapter import action_to_ir
        from core.dsl.document import ScriptDocument
        from core.dsl.ir import FlowIR, ir_to_code

        try:
            # Convert UI Actions back to IR
            action_irs = []
            for action in actions:
                ir = action_to_ir(action)
                if ir:
                    action_irs.append(ir)

            # Reconstruct Code
            # We preserve existing IR structure (assets, config)
            # regenerate with new main flow

            current_code = self.editor.get_code()
            doc = ScriptDocument()
            doc.update_from_code(current_code)

            # Find main flow to replace
            # If doc was invalid, maybe we overwrite? But safer to rely on valid doc.
            if not doc.ir.is_valid:
                # If code was invalid, we might lose data.
                # But we checked validity on open.
                pass

            main_flow = doc.ir.get_flow("main")
            if not main_flow:
                main_flow = FlowIR(name="main")
                doc.ir.flows.append(main_flow)

            main_flow.actions = action_irs

            # Generate new code
            new_code = ir_to_code(doc.ir)

            # Update Editor
            self.editor.set_code(new_code)

            self.output.log_success(f"Synced {len(actions)} actions from Flow Editor")
            self.status_bar.showMessage("Synced actions from Flow Editor")

        except Exception as e:
            self.output.log_error(f"Failed to sync actions: {e}")
            QMessageBox.critical(self, "Sync Error", f"Failed to sync actions: {e}")

    # ─────────────────────────────────────────────────────────────
    # UI Updates
    # ─────────────────────────────────────────────────────────────

    def _on_code_changed(self) -> None:
        """Handle code changes."""
        if not self._is_modified:
            self._is_modified = True
            self._update_title()
        # Update structure panel
        self.structure_panel.refresh(self.editor.get_code())

    def _navigate_to_line(self, line: int) -> None:
        """Scroll editor to specific line."""
        self.editor.goto_line(line)
        self.editor.setFocus()

    def _on_content_changed(self) -> None:
        """Handle content change in editor."""
        # This method is now effectively replaced by _on_code_changed
        # Keeping it for now, but its signal connection should be updated.
        # The instruction implies _on_content_changed is renamed/replaced by _on_code_changed
        # and the logic for _is_modified and _update_title is moved into _on_code_changed.
        # The original _on_content_changed signal connection is updated in _connect_signals.
        pass  # The logic is now in _on_code_changed

    def _on_cursor_moved(self, line: int, col: int) -> None:
        """Handle cursor movement."""
        self.cursor_label.setText(f"Ln {line}, Col {col}")

    def _update_title(self) -> None:
        """Update window title with full script path."""
        if self._current_file:
            file_path = Path(self._current_file)
            file_name = file_path.name
            parent_dir = file_path.parent
            display = f"{file_name} - {parent_dir}"
        else:
            display = "Untitled"

        modified = " *" if self._is_modified else ""
        self.setWindowTitle(f"RetroAuto v2 - {display}{modified}")

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About MacroIDE 95",
            "MacroIDE 95\nVersion 1.0\n\n"
            "A Windows automation IDE with\n"
            "classic Win95/98 styling.\n\n"
            "© 2024 RetroAuto",
        )

    def _on_rule_selected(self, data: dict) -> None:
        """Handle interrupt rule selection."""
        # data = {"index": int, "rule": InterruptRule}
        self.inspector.load_action(
            {"action": data["rule"], "type": "interrupt", "index": data["index"]}
        )

    def _on_rules_changed(self, rules: list) -> None:
        """Handle interrupt rules update."""
        if self._script:
            self._script.interrupts = rules
            self._mark_modified()

    def _get_asset_path(self, asset_id: str) -> Path | None:
        """Get path to asset image file."""
        if not self._current_file:
            return None

        # Assuming standard structure: project/assets/asset_id.png
        # Assets are in "assets" sibling folder of "scripts" folder?
        # Standard: project_root/assets/
        # Current file: project_root/scripts/main.dsl

        project_root = self._current_file.parent.parent
        assets_dir = project_root / "assets"

        if not assets_dir.exists():
            return None

        # Try common extensions
        for ext in [".png", ".jpg", ".jpeg", ".bmp"]:
            path = assets_dir / f"{asset_id}{ext}"
            if path.exists():
                return path

        return None

    # ─────────────────────────────────────────────────────────────
    # Theme Operations
    # ─────────────────────────────────────────────────────────────

    def _init_theme(self) -> None:
        """Apply saved theme on startup."""
        get_theme_manager().apply_theme()

    def _switch_theme(self, theme_value: str) -> None:
        """Switch to specified theme."""
        try:
            theme = ThemeType(theme_value)
            get_theme_manager().set_theme(theme)
            self.status_bar.showMessage(
                f"Theme changed to {get_theme_manager().current_theme_name}", 3000
            )
        except ValueError:
            pass

    # ─────────────────────────────────────────────────────────────
    # Progressive Disclosure Operations
    # ─────────────────────────────────────────────────────────────

    def _toggle_expert_mode(self) -> None:
        """Toggle between Beginner and Expert modes."""
        manager = get_disclosure_manager()
        is_expert = manager.toggle_expert_mode()
        
        # Update menu action state
        self._expert_mode_action.setChecked(is_expert)
        
        # Update panel visibility
        self._apply_panel_visibility()
        
        # Show status message
        mode_name = "Expert" if is_expert else "Beginner"
        self.status_bar.showMessage(
            f"Switched to {mode_name} mode - "
            f"{'All panels visible' if is_expert else 'Simplified view'}",
            3000
        )
    
    def _apply_panel_visibility(self) -> None:
        """Apply panel visibility based on current user level."""
        manager = get_disclosure_manager()
        is_expert = manager.is_expert
        
        # Toggle advanced panels visibility
        # Inspector (Properties Panel)
        if hasattr(self, 'inspector'):
            self.inspector.setVisible(is_expert)
        
        # Interrupts Panel (in left_tabs)
        if hasattr(self, 'interrupts_panel'):
            # Show/hide the tab instead of the widget
            idx = self.left_tabs.indexOf(self.interrupts_panel)
            if idx >= 0:
                self.left_tabs.setTabVisible(idx, is_expert)
        
        # Structure Panel (if exists as dock)
        if hasattr(self, 'structure_dock'):
            self.structure_dock.setVisible(is_expert)


