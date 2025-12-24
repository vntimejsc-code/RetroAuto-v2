"""
RetroAuto v2 - Main Window (Win95/98 Style)

3-column layout: Assets | Actions | Properties
Bottom: Log panel
Full engine integration with QThread.
"""

import contextlib
import json
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.ui.assets_panel import AssetsPanel
from app.ui.capture_tool import CaptureTool
from app.ui.coordinates_panel import CoordinatesPanel
from app.ui.engine_worker import EngineWorker
from app.ui.hybrid_panel import HybridActionsPanel
from app.ui.log_panel import LogPanel
from app.ui.properties_panel import PropertiesPanel
from core.dsl.document import ScriptDocument
from core.dsl.sync_manager import SyncManager
from core.engine.hotkey_listener import get_hotkey_listener
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
        # Engine worker (QThread)
        self.engine = EngineWorker()
        self._project_path: Path | None = None

        # Auto-detect project in CWD
        cwd = Path.cwd()
        if (cwd / "script.yaml").exists():
            self._project_path = cwd
            logger.info(f"Auto-detected project at {cwd}")

        self._draft_path = Path.home() / ".retroauto" / "draft.json"

        # ScriptDocument and SyncManager for GUI-IDE sync
        self._script_doc = ScriptDocument()
        self._sync_manager = SyncManager(self._script_doc)

        self._init_ui()
        self._connect_engine_signals()
        self._connect_sync_signals()

        # Create new empty script on start
        self.engine.new_script()
        self._update_title()

        # Load draft if exists
        self._load_draft()

        # Set assets directory for preview functionality
        if self._project_path:
            self.assets_panel.set_assets_dir(self._project_path / "assets")

        # Auto-save timer (every 30 seconds)
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self._save_draft)
        self._auto_save_timer.start(30000)  # 30 seconds

        # Global hotkey for capture (works even when app is minimized)
        # Note: pynput callbacks run on a different thread, so we use QTimer.singleShot
        # to marshal the call to the Qt main thread
        self._hotkey_listener = get_hotkey_listener()
        self._hotkey_listener.register("ctrl+shift+c", self._on_capture_hotkey)
        self._hotkey_listener.start()

        logger.info("MainWindow initialized")

    def _on_capture_hotkey(self) -> None:
        """Handle global capture hotkey - marshals to Qt main thread."""
        # QTimer.singleShot(0) schedules the call on the Qt event loop (main thread)
        QTimer.singleShot(0, self._on_capture)

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
        self.actions_panel = HybridActionsPanel()
        self.properties_panel = PropertiesPanel()
        self.coordinates_panel = CoordinatesPanel()

        hsplitter.addWidget(self.assets_panel)
        hsplitter.addWidget(self.actions_panel)
        hsplitter.addWidget(self.properties_panel)
        hsplitter.addWidget(self.coordinates_panel)
        hsplitter.setStretchFactor(0, 1)  # Assets: 1
        hsplitter.setStretchFactor(1, 2)  # Actions: 2
        hsplitter.setStretchFactor(2, 1)  # Properties: 1
        hsplitter.setStretchFactor(3, 1)  # Coordinates: 1

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

        # Variable Watch Dock
        from PySide6.QtWidgets import QDockWidget

        from app.ui.variable_watch import VariableWatchDock

        self.watch_dock = QDockWidget("Variables", self)
        self.watch_dock.setWidget(VariableWatchDock())
        self.watch_dock.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.watch_dock)

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
        self.action_capture.setShortcut("Ctrl+Shift+C")
        self.action_capture.setToolTip("Capture screen region (Ctrl+Shift+C)")
        toolbar.addSeparator()

        # IDE
        self.action_open_ide = toolbar.addAction("🖥️ Open IDE", self._on_open_ide)

        # View Menu
        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu("View")
        self.action_view_flow = view_menu.addAction("🎨 Visual Flow Editor", self._show_flow_editor)

    def _connect_panel_signals(self) -> None:
        """Connect panel signals."""
        # When action selected in actions panel, show properties
        self.actions_panel.action_selected.connect(self.properties_panel.load_action)

        # When properties changed, update action
        self.properties_panel.properties_changed.connect(self.actions_panel.update_action)

        # When coordinate click added to script
        self.coordinates_panel.add_to_script.connect(self._on_add_click_to_script)

        # When assets change, sync to script for persistence
        self.assets_panel.assets_changed.connect(self._on_assets_changed)

        # Run step from actions panel
        # self.actions_panel.run_step_requested.connect(self._on_run_step)

        # Open Flow Editor
        self.actions_panel.flow_editor_requested.connect(self._show_flow_editor)

    def _connect_engine_signals(self) -> None:
        """Connect engine worker signals."""
        self.engine.state_changed.connect(self._on_state_changed)
        self.engine.step_started.connect(self._on_step_started)
        self.engine.flow_completed.connect(self._on_flow_completed)
        self.engine.error_occurred.connect(self._on_error)
        self.engine.notification_received.connect(self._on_notification)

    def _on_notification(self, title: str, message: str) -> None:
        """Handle notification from engine."""
        QMessageBox.information(self, title, message)

    def _connect_sync_signals(self) -> None:
        """Connect SyncManager signals for GUI-IDE synchronization."""
        # When IR changes from code editor, refresh Actions panel
        self._sync_manager.ir_changed.connect(self._on_ir_changed_from_code)

        # When code regenerated from GUI changes, update IDE if open
        self._sync_manager.code_regenerated.connect(self._on_code_regenerated)

        # Note: action_changed signal will be connected when we need
        # full bidirectional sync (actions_panel -> IR -> code)
        # For now, focus on code -> IR -> GUI direction

        logger.info("Sync signals connected")

    def _on_ir_changed_from_code(self, change_type: str) -> None:
        """Handle IR changes from code editor."""
        logger.info("IR changed signal received: %s", change_type)
        if change_type.startswith("code_"):
            # Refresh actions panel from IR
            actions = self._sync_manager.get_flow_actions("main")
            logger.info("Got %d actions from IR for panel refresh", len(actions) if actions else 0)
            if actions:
                self.actions_panel.load_actions(actions)
                logger.info("Actions panel updated with %d actions", len(actions))
            else:
                logger.warning("No actions returned from IR - panel not updated")

    def _on_code_regenerated(self, new_code: str) -> None:
        """Handle code regenerated from GUI changes."""
        # Update IDE window if open
        if hasattr(self, "_ide_window") and self._ide_window:
            self._ide_window.set_code(new_code)
        logger.debug("Code regenerated from GUI changes")

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

    def _update_title(self) -> None:
        """Update window title with project path and script name."""
        if self._project_path:
            script_file = self._project_path / "script.yaml"
            if script_file.exists():
                title = f"RetroAuto v2 - script.yaml - {self._project_path}"
            else:
                title = f"RetroAuto v2 - Untitled - {self._project_path}"
        else:
            title = "RetroAuto v2 - Untitled"

        self.setWindowTitle(title)

    def _on_capture(self) -> None:
        """Open capture tool."""
        logger.info("Opening capture tool...")

        # Determine assets directory
        assets_dir = self._project_path / "assets" if self._project_path else Path(".")

        # Get existing asset IDs from the assets panel to avoid duplicates
        existing_asset_ids = {asset.id for asset in self.assets_panel.get_assets()}

        # Create capture tool with existing asset info
        self._capture_tool = CaptureTool(assets_dir, existing_asset_ids)
        self._capture_tool.capture(self._on_capture_complete, parent_window=self)

    def _on_capture_complete(self, asset, roi) -> None:  # type: ignore
        """Handle capture completion."""
        logger.info(
            "Captured asset: %s with ROI (%d, %d, %d, %d)", asset.id, roi.x, roi.y, roi.w, roi.h
        )

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

    def _on_add_click_to_script(self, x: int, y: int, button: str, clicks: int) -> None:
        """Add a click action from coordinates panel to script."""
        from core.models import Click

        click_action = Click(x=x, y=y, button=button, clicks=clicks)
        self.actions_panel._actions.append(click_action)
        self.actions_panel._refresh_list()

        logger.info(f"Added Click({x}, {y}, {button}, {clicks}) to script")
        self.status_bar.showMessage(f"Added: Click({x}, {y}) - {button}")

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

    # ─────────────────────────────────────────────────────────────
    # Visual Flow Editor Integration
    # ─────────────────────────────────────────────────────────────

    def _show_flow_editor(self) -> None:
        """Show the visual flow editor in a new window."""
        from PySide6.QtWidgets import QMainWindow

        from app.ui.flow_editor import FlowEditorWidget

        # Create flow editor window
        self._flow_window = QMainWindow(self)
        self._flow_window.setWindowTitle("🎨 Visual Flow Editor - RetroAuto")
        self._flow_window.setMinimumSize(800, 600)

        # Get current actions
        current_actions = self.actions_panel.get_actions()

        # Initialize with current actions
        flow_widget = FlowEditorWidget(actions=current_actions)

        # Connect export signal to sync back
        flow_widget.actions_exported.connect(self._on_flow_actions_exported)

        self._flow_window.setCentralWidget(flow_widget)
        self._flow_window.show()

        logger.info("Opened Visual Flow Editor window")

    def _on_flow_actions_exported(self, actions: list) -> None:
        """Handle actions exported from flow editor."""
        self.actions_panel.load_actions(actions)
        self.status_bar.showMessage(f"Synced {len(actions)} actions from Flow Editor")
        logger.info(f"Updated Actions Panel with {len(actions)} actions from Flow Editor")

    def _on_open_ide(self) -> None:
        """Open the DSL IDE window with current script code."""
        from app.ui.ide_main_window import IDEMainWindow
        from core.dsl.adapter import action_to_ir
        from core.dsl.ir import FlowIR, ScriptIR, ir_to_code

        # Generate DSL code from current actions
        actions = self.actions_panel.get_actions()

        # Build IR from actions
        ir = ScriptIR()
        main_flow = FlowIR(name="main")
        for action in actions:
            action_ir = action_to_ir(action)
            main_flow.actions.append(action_ir)
        ir.flows.append(main_flow)

        # Generate code
        code = ir_to_code(ir)

        # Create and show IDE window
        self._ide_window = IDEMainWindow()

        # Set file path if project exists
        if self._project_path:
            self._ide_window._current_file = self._project_path / "scripts" / "main.dsl"

        # Apply dark theme matching Main Window
        dark_stylesheet = self._get_ide_dark_stylesheet()
        self._ide_window.setStyleSheet(dark_stylesheet)

        # Set the generated code in editor
        if hasattr(self._ide_window, "editor") and self._ide_window.editor:
            self._ide_window.editor.setPlainText(code)
            # Reset modified flag since this is initial content, not user edit
            self._ide_window._is_modified = False
            self._ide_window._update_title()

        # Connect IDE save signal to sync back to actions panel
        self._ide_window.code_saved.connect(self._on_ide_code_saved)

        self._ide_window.show()
        logger.info("Opened IDE window with %d actions", len(actions))

    def _on_ide_code_saved(self, code: str) -> None:
        """Handle code saved from IDE - sync back to actions panel immediately."""
        self._sync_manager.on_code_saved(code)
        logger.info("IDE code synced to actions panel")

    def _get_ide_dark_stylesheet(self) -> str:
        """Get dark theme stylesheet for IDE Editor matching Main Window."""
        return """
        /* Dark Theme for IDE Editor - Matches Main Window */
        QMainWindow, QWidget {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }

        QMenuBar {
            background-color: #2d2d2d;
            color: #e0e0e0;
            border-bottom: 1px solid #3c3c3c;
        }
        QMenuBar::item:selected {
            background-color: #404040;
        }
        QMenu {
            background-color: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #3c3c3c;
        }
        QMenu::item:selected {
            background-color: #0078d4;
        }

        QToolBar {
            background-color: #2d2d2d;
            border: none;
            spacing: 4px;
            padding: 2px;
        }
        QToolButton {
            background-color: #2d2d2d;
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            padding: 4px 8px;
            color: #e0e0e0;
        }
        QToolButton:hover {
            background-color: #404040;
        }
        QToolButton:pressed {
            background-color: #0078d4;
        }

        QPlainTextEdit, QTextEdit {
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #3c3c3c;
            selection-background-color: #264f78;
            selection-color: #ffffff;
        }

        QTreeWidget, QListWidget {
            background-color: #252526;
            color: #e0e0e0;
            border: 1px solid #3c3c3c;
        }
        QTreeWidget::item:selected, QListWidget::item:selected {
            background-color: #0078d4;
        }

        QTabWidget::pane {
            background-color: #1e1e1e;
            border: 1px solid #3c3c3c;
        }
        QTabBar::tab {
            background-color: #2d2d2d;
            color: #e0e0e0;
            padding: 6px 12px;
            border: 1px solid #3c3c3c;
        }
        QTabBar::tab:selected {
            background-color: #1e1e1e;
            border-bottom: none;
        }

        QSplitter::handle {
            background-color: #3c3c3c;
        }

        QStatusBar {
            background-color: #007acc;
            color: white;
        }

        QLabel {
            color: #e0e0e0;
        }

        QGroupBox {
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            margin-top: 8px;
            color: #e0e0e0;
        }
        QGroupBox::title {
            color: #e0e0e0;
        }

        QScrollBar:vertical {
            background: #1e1e1e;
            width: 12px;
        }
        QScrollBar::handle:vertical {
            background: #5a5a5a;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #808080;
        }

        QPushButton {
            background-color: #0078d4;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #1084d8;
        }
        QPushButton:pressed {
            background-color: #006cc1;
        }
        QPushButton:disabled {
            background-color: #3c3c3c;
            color: #808080;
        }
        """

    def _save_draft(self) -> None:
        """Auto-save actions draft to file."""
        try:
            # Ensure directory exists
            self._draft_path.parent.mkdir(parents=True, exist_ok=True)

            # Serialize actions + assets
            actions = self.actions_panel.get_actions()
            assets = self.assets_panel.get_assets()
            draft_data = {
                "version": 1,
                "actions": [action.model_dump() for action in actions],
                "assets": [asset.model_dump() for asset in assets],
                "coordinates": self.coordinates_panel.get_coordinates(),
            }

            with open(self._draft_path, "w", encoding="utf-8") as f:
                json.dump(draft_data, f, indent=2, default=str)

            logger.debug(f"Auto-saved draft: {len(actions)} actions")
        except Exception as e:
            logger.warning(f"Failed to save draft: {e}")

    def _load_draft(self) -> None:
        """Load actions draft from file on startup."""
        try:
            if not self._draft_path.exists():
                return

            with open(self._draft_path, encoding="utf-8") as f:
                draft_data = json.load(f)

            if draft_data.get("version") != 1:
                return

            # Load actions
            from core.models import (
                Click,
                Delay,
                Goto,
                Hotkey,
                IfImage,
                Label,
                RunFlow,
                TypeText,
                WaitImage,
            )

            action_map = {
                "Click": Click,
                "WaitImage": WaitImage,
                "IfImage": IfImage,
                "Hotkey": Hotkey,
                "TypeText": TypeText,
                "Label": Label,
                "Goto": Goto,
                "RunFlow": RunFlow,
                "Delay": Delay,
            }

            actions = []
            for action_data in draft_data.get("actions", []):
                action_type = action_data.get("action")
                if action_type in action_map:
                    with contextlib.suppress(Exception):
                        actions.append(action_map[action_type](**action_data))

            if actions:
                self.actions_panel._actions = actions
                self.actions_panel._refresh_list()
                logger.info(f"Loaded draft: {len(actions)} actions")

            # Load assets
            from core.models import AssetImage

            assets = []
            for asset_data in draft_data.get("assets", []):
                with contextlib.suppress(Exception):
                    assets.append(AssetImage(**asset_data))

            if assets:
                self.assets_panel.load_assets(assets)
                logger.info(f"Loaded draft: {len(assets)} assets")

            if actions or assets:
                self.status_bar.showMessage(
                    f"Loaded draft: {len(actions)} actions, {len(assets)} assets"
                )

        except Exception as e:
            logger.warning(f"Failed to load draft: {e}")

    def closeEvent(self, event) -> None:  # type: ignore
        """Handle window close."""
        # Save draft before closing
        self._save_draft()

        # Stop global hotkey listener
        if hasattr(self, "_hotkey_listener") and self._hotkey_listener:
            self._hotkey_listener.stop()
            logger.info("Hotkey listener stopped")

        if self.engine.isRunning():
            self.engine.stop()
            if not self.engine.wait(2000):
                logger.warning("Engine did not stop gracefully, forcing termination")
                self.engine.terminate()
                self.engine.wait()
        event.accept()

    def _on_assets_changed(self) -> None:
        """Sync assets from UI to script when they change."""
        if self.engine.script:
            # Get current assets from panel
            self.engine.script.assets = self.assets_panel.get_assets()
            logger.info("Assets synced to script (%d assets)", len(self.engine.script.assets))
