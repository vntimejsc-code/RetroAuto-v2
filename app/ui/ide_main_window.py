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

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.ui.code_editor import DSLCodeEditor
from app.ui.inspector_panel import InspectorPanel
from app.ui.output_panel import OutputPanel
from app.ui.project_explorer import ProjectExplorer
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

    def __init__(self) -> None:
        super().__init__()
        self._current_file: Path | None = None
        self._is_modified = False
        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_status_bar()
        self._connect_signals()
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
        self.explorer = ProjectExplorer()
        hsplitter.addWidget(self.explorer)

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
        editor_layout.addWidget(self.editor)

        hsplitter.addWidget(editor_container)

        # Inspector
        self.inspector = InspectorPanel()
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

    def _connect_signals(self) -> None:
        """Connect signals from child widgets."""
        # Explorer
        self.explorer.file_opened.connect(self._open_file)

        # Editor
        self.editor.content_changed.connect(self._on_content_changed)
        self.editor.cursor_position_changed.connect(self._on_cursor_moved)

        # Output
        self.output.diagnostic_clicked.connect(self._goto_diagnostic)

    def _restore_state(self) -> None:
        """Restore window state from settings."""
        settings = QSettings("RetroAuto", "MacroIDE95")

        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        last_project = settings.value("last_project")
        if last_project and Path(last_project).exists():
            self.explorer.load_project(Path(last_project))

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
                    '''// main.dsl - RetroScript 9.0
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
''',
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
            content = self.editor.get_code()
            self._current_file.write_text(content, encoding="utf-8")
            self._is_modified = False
            self._update_title()
            self.status_bar.showMessage("Saved", 3000)
            self.output.log_success(f"Saved: {self._current_file.name}")
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

    # ─────────────────────────────────────────────────────────────
    # Run Operations
    # ─────────────────────────────────────────────────────────────

    def _run_script(self) -> None:
        """Run the current script."""
        self.output.log_info("Running script...")
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        # TODO: Implement actual script execution
        self.status_bar.showMessage("Running...")

    def _stop_script(self) -> None:
        """Stop the running script."""
        self.output.log_warning("Script stopped")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_bar.showMessage("Stopped")

    # ─────────────────────────────────────────────────────────────
    # UI Updates
    # ─────────────────────────────────────────────────────────────

    def _on_content_changed(self) -> None:
        """Handle content change in editor."""
        if not self._is_modified:
            self._is_modified = True
            self._update_title()

    def _on_cursor_moved(self, line: int, col: int) -> None:
        """Handle cursor movement."""
        self.cursor_label.setText(f"Ln {line}, Col {col}")

    def _update_title(self) -> None:
        """Update window title."""
        name = self._current_file.name if self._current_file else "Untitled"
        modified = " *" if self._is_modified else ""
        self.setWindowTitle(f"MacroIDE 95 - {name}{modified}")

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
