"""
RetroAuto v2 - Main Window (Win95/98 Style)

3-column layout: Assets | Actions | Properties
Bottom: Log panel
Full engine integration with QThread.
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.ui.actions_panel import ActionsPanel
from app.ui.assets_panel import AssetsPanel
from app.ui.capture_tool import CaptureTool
from app.ui.engine_worker import EngineWorker
from app.ui.log_panel import LogPanel
from app.ui.properties_panel import PropertiesPanel
from infra import get_logger

logger = get_logger("MainWindow")


class MainWindow(QMainWindow):
    """
    Main application window with Win95/98 style.

    Layout:
    ┌─────────────────────────────────────────────────────┐
    │ Toolbar: Open | Save | Run | Pause | Stop | Capture │
    ├──────────┬───────────────────────┬──────────────────┤
    │  Assets  │    Actions (Flow)     │   Properties     │
    │  Panel   │      - list           │     Panel        │
    │          │      - add/delete     │                  │
    ├──────────┴───────────────────────┴──────────────────┤
    │                    Log Panel                        │
    ├─────────────────────────────────────────────────────┤
    │ Status: Ready | Step: 0/0                           │
    └─────────────────────────────────────────────────────┘
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RetroAuto v2")
        self.resize(1200, 800)

        # Engine worker (QThread)
        self.engine = EngineWorker()
        self._project_path: Path | None = None

        self._init_ui()
        self._connect_engine_signals()

        # Create new empty script on start
        self.engine.new_script()
        self._update_title()

        logger.info("MainWindow initialized")

    def _init_ui(self) -> None:
        """Initialize UI components."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Toolbar
        self._init_toolbar()

        # Main content splitter (vertical: panels | log)
        vsplitter = QSplitter(Qt.Orientation.Vertical)

        # Top: 3-column panels
        hsplitter = QSplitter(Qt.Orientation.Horizontal)

        self.assets_panel = AssetsPanel()
        self.actions_panel = ActionsPanel()
        self.properties_panel = PropertiesPanel()

        hsplitter.addWidget(self.assets_panel)
        hsplitter.addWidget(self.actions_panel)
        hsplitter.addWidget(self.properties_panel)
        hsplitter.setStretchFactor(0, 1)  # Assets: 1
        hsplitter.setStretchFactor(1, 2)  # Actions: 2
        hsplitter.setStretchFactor(2, 1)  # Properties: 1

        # Bottom: Log panel
        self.log_panel = LogPanel()

        vsplitter.addWidget(hsplitter)
        vsplitter.addWidget(self.log_panel)
        vsplitter.setStretchFactor(0, 3)  # Panels: 3
        vsplitter.setStretchFactor(1, 1)  # Log: 1

        main_layout.addWidget(vsplitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Connect panel signals
        self._connect_panel_signals()

    def _init_toolbar(self) -> None:
        """Create toolbar with actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # File actions
        self.action_new = toolbar.addAction("📄 New", self._on_new)
        self.action_open = toolbar.addAction("📂 Open", self._on_open)
        self.action_save = toolbar.addAction("💾 Save", self._on_save)
        toolbar.addSeparator()

        # Run actions
        self.action_run = toolbar.addAction("▶ Run", self._on_run)
        self.action_pause = toolbar.addAction("⏸ Pause", self._on_pause)
        self.action_stop = toolbar.addAction("⏹ Stop", self._on_stop)
        self.action_pause.setEnabled(False)
        self.action_stop.setEnabled(False)
        toolbar.addSeparator()

        # Tools
        self.action_capture = toolbar.addAction("📷 Capture", self._on_capture)
        toolbar.addSeparator()

        # IDE
        self.action_open_ide = toolbar.addAction("🖥️ Open IDE", self._on_open_ide)

    def _connect_panel_signals(self) -> None:
        """Connect panel signals."""
        # When action selected in actions panel, show properties
        self.actions_panel.action_selected.connect(self.properties_panel.load_action)

        # When properties changed, update action
        self.properties_panel.properties_changed.connect(self.actions_panel.update_action)

        # Run step from actions panel
        # self.actions_panel.run_step_requested.connect(self._on_run_step)

    def _connect_engine_signals(self) -> None:
        """Connect engine worker signals."""
        self.engine.state_changed.connect(self._on_state_changed)
        self.engine.step_started.connect(self._on_step_started)
        self.engine.flow_completed.connect(self._on_flow_completed)
        self.engine.error_occurred.connect(self._on_error)

    def _update_title(self) -> None:
        """Update window title with project name."""
        if self.engine.script:
            name = self.engine.script.name
            path = f" - {self._project_path}" if self._project_path else ""
            self.setWindowTitle(f"RetroAuto v2 - {name}{path}")
        else:
            self.setWindowTitle("RetroAuto v2")

    # ─────────────────────────────────────────────────────────────
    # Toolbar handlers
    # ─────────────────────────────────────────────────────────────

    def _on_new(self) -> None:
        """Create new project."""
        # Confirm if unsaved changes
        self.engine.new_script()
        self._project_path = None
        self._update_title()
        self._sync_ui_from_script()
        logger.info("Created new project")

    def _on_open(self) -> None:
        """Open project file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Script",
            "",
            "YAML Files (*.yaml *.yml);;All Files (*)",
        )
        if path:
            self._project_path = Path(path).parent
            self.engine.load_project(Path(path))
            self._update_title()
            self._sync_ui_from_script()
            logger.info("Opened project: %s", path)

    def _on_save(self) -> None:
        """Save project."""
        self._sync_script_from_ui()

        if self._project_path:
            path = self._project_path / "script.yaml"
        else:
            path_str, _ = QFileDialog.getSaveFileName(
                self,
                "Save Script",
                "script.yaml",
                "YAML Files (*.yaml);;All Files (*)",
            )
            if not path_str:
                return
            path = Path(path_str)
            self._project_path = path.parent

        if self.engine.save_project(path):
            self._update_title()
            logger.info("Saved project: %s", path)

    def _on_run(self) -> None:
        """Start script execution."""
        if self.engine.isRunning():
            return

        self._sync_script_from_ui()

        logger.info("Starting script execution...")
        self.action_run.setEnabled(False)
        self.action_pause.setEnabled(True)
        self.action_stop.setEnabled(True)
        self.engine.start()

    def _on_pause(self) -> None:
        """Toggle pause/resume."""
        if self.engine.get_state() == "paused":
            self.engine.resume()
            self.action_pause.setText("⏸ Pause")
        else:
            self.engine.pause()
            self.action_pause.setText("▶ Resume")

    def _on_stop(self) -> None:
        """Stop script execution."""
        logger.info("Stopping script...")
        self.engine.stop()

    def _on_capture(self) -> None:
        """Open capture tool."""
        logger.info("Opening capture tool...")

        # Determine assets directory
        assets_dir = self._project_path / "assets" if self._project_path else Path(".")

        # Create capture tool
        self._capture_tool = CaptureTool(assets_dir)
        self._capture_tool.capture(self._on_capture_complete)

    def _on_capture_complete(self, asset, roi) -> None:  # type: ignore
        """Handle capture completion."""
        logger.info("Captured asset: %s with ROI (%d, %d, %d, %d)", asset.id, roi.x, roi.y, roi.w, roi.h)

        # Add asset with ROI to panel
        asset.roi = roi
        self.assets_panel.add_asset(asset)

    # ─────────────────────────────────────────────────────────────
    # Engine callbacks
    # ─────────────────────────────────────────────────────────────

    def _on_state_changed(self, state: str) -> None:
        """Handle engine state change."""
        self.status_bar.showMessage(f"Status: {state.upper()}")

        if state in ("idle", "error", "stopping"):
            self.action_run.setEnabled(True)
            self.action_pause.setEnabled(False)
            self.action_stop.setEnabled(False)
            self.action_pause.setText("⏸ Pause")

    def _on_step_started(self, flow: str, idx: int, action_type: str) -> None:
        """Handle step start."""
        self.status_bar.showMessage(f"Running: {flow}[{idx}] - {action_type}")
        # Highlight current step in actions panel
        self.actions_panel.highlight_step(idx)

    def _on_flow_completed(self, flow: str, success: bool) -> None:
        """Handle flow completion."""
        if success:
            self.status_bar.showMessage(f"Completed: {flow}")
        else:
            self.status_bar.showMessage(f"Stopped/Failed: {flow}")

    def _on_error(self, message: str) -> None:
        """Handle engine error."""
        QMessageBox.critical(self, "Error", message)

    # ─────────────────────────────────────────────────────────────
    # Sync UI <-> Script
    # ─────────────────────────────────────────────────────────────

    def _sync_ui_from_script(self) -> None:
        """Update UI from current script."""
        script = self.engine.script
        if not script:
            return

        # Update assets panel
        self.assets_panel.load_assets(script.assets)

        # Update actions panel with main flow
        main_flow = script.get_flow(script.main_flow)
        if main_flow:
            self.actions_panel.load_actions(main_flow.actions)

    def _sync_script_from_ui(self) -> None:
        """Update script from UI state."""
        script = self.engine.script
        if not script:
            return

        # Get assets from panel
        script.assets = self.assets_panel.get_assets()

        # Get actions from panel
        main_flow = script.get_flow(script.main_flow)
        if main_flow:
            main_flow.actions = self.actions_panel.get_actions()

    def _on_open_ide(self) -> None:
        """Open the DSL IDE window."""
        from app.ui.ide_main_window import IDEMainWindow
        from app.ui.win95_style import generate_stylesheet
        
        self.ide_window = IDEMainWindow()
        self.ide_window.setStyleSheet(generate_stylesheet())
        self.ide_window.show()
        logger.info("Opened IDE window")

    def closeEvent(self, event) -> None:  # type: ignore
        """Handle window close."""
        if self.engine.isRunning():
            self.engine.stop()
            self.engine.wait(2000)
        event.accept()
