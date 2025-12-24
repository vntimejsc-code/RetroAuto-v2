"""
RetroAuto v2 - IDE Controller

Central controller that wires:
- Code Editor ↔ Document ↔ IR
- GUI Panels ↔ Document ↔ IR
- Runner ↔ Document

This keeps the IDE main window clean and handles all coordination.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

from core.dsl.diagnostics import Diagnostic
from core.dsl.document import ScriptDocument
from core.dsl.ir import ActionIR, AssetIR, FlowIR
from core.dsl.parser import Parser
from core.dsl.semantic import analyze


class IDEController(QObject):
    """
    Central controller for MacroIDE 95.

    Signals:
        document_changed: Document was loaded/updated
        code_updated: Code was regenerated from GUI
        ir_updated: IR was updated from code
        errors_found: Parse/semantic errors found
        run_started: Script execution started
        run_stopped: Script execution stopped
    """

    document_changed = Signal()
    code_updated = Signal(str)  # new code
    ir_updated = Signal(str)  # change type
    errors_found = Signal(list)  # list of Diagnostic
    run_started = Signal()
    run_stopped = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._document = ScriptDocument()
        self._is_running = False
        self._setup_callbacks()

    @property
    def document(self) -> ScriptDocument:
        """Get the current document."""
        return self._document

    @property
    def is_running(self) -> bool:
        """Check if script is running."""
        return self._is_running

    def _setup_callbacks(self) -> None:
        """Set up document callbacks."""
        self._document.on_ir_changed(self._on_ir_changed)
        self._document.on_code_changed(self._on_code_changed)
        self._document.on_error(self._on_errors)

    # ─────────────────────────────────────────────────────────────
    # Document Operations
    # ─────────────────────────────────────────────────────────────

    def new_project(self, folder: Path) -> None:
        """Create a new project in folder."""
        # Create directory structure
        (folder / "assets").mkdir(parents=True, exist_ok=True)
        (folder / "scripts").mkdir(exist_ok=True)
        (folder / "flows").mkdir(exist_ok=True)

        # Create main.dsl
        main_path = folder / "scripts" / "main.dsl"
        self._document.new()
        self._document.save_as(main_path)

        self.document_changed.emit()

    def open_file(self, path: Path) -> bool:
        """Open a DSL file."""
        success = self._document.load_from_file(path)
        if success:
            self.document_changed.emit()
            # Run validation
            self.validate()
        return success

    def save(self) -> bool:
        """Save the current document."""
        return self._document.save()

    def save_as(self, path: Path) -> bool:
        """Save to a new file."""
        return self._document.save_as(path)

    # ─────────────────────────────────────────────────────────────
    # Code ↔ IR Sync
    # ─────────────────────────────────────────────────────────────

    def update_code(self, new_code: str) -> None:
        """
        Update document from code editor.

        Called when user types in the editor.
        """
        self._document.update_from_code(new_code, source="editor")

    def update_from_gui(self, path: str, value: Any) -> None:
        """
        Update document from GUI change.

        Called when user changes properties in inspector.
        """
        self._document.update_from_gui(path, value)

    def _on_code_changed(self, source: str) -> None:
        """Handle code change from document."""
        if source != "editor":
            # Code was regenerated from GUI, update editor
            self.code_updated.emit(self._document.code)

    def _on_ir_changed(self, change_type: str) -> None:
        """Handle IR change from document."""
        self.ir_updated.emit(change_type)

    def _on_errors(self, errors: list[str]) -> None:
        """Handle parse errors from document."""
        # Convert to diagnostics
        diagnostics = [
            Diagnostic(
                code="E1000",
                severity="error",
                message=e,
                span=None,  # TODO: Extract span
            )
            for e in errors
        ]
        self.errors_found.emit(diagnostics)

    # ─────────────────────────────────────────────────────────────
    # Validation
    # ─────────────────────────────────────────────────────────────

    def validate(self) -> list[Diagnostic]:
        """
        Validate the current document.

        Returns list of diagnostics.
        """
        code = self._document.code
        parser = Parser(code)
        program = parser.parse()

        # Collect all diagnostics
        diagnostics: list[Diagnostic] = list(parser.errors)

        if not parser.errors:
            # Run semantic analysis
            asset_ids = [a.id for a in self._document.ir.assets]
            semantic_errors = analyze(program, known_assets=asset_ids)
            diagnostics.extend(semantic_errors)

        self.errors_found.emit(diagnostics)
        return diagnostics

    # ─────────────────────────────────────────────────────────────
    # Flow Operations (from GUI)
    # ─────────────────────────────────────────────────────────────

    def add_flow(self, name: str) -> FlowIR | None:
        """Add a new flow."""
        if self._document.ir.get_flow(name):
            return None  # Already exists
        return self._document.add_flow(name)

    def remove_flow(self, name: str) -> None:
        """Remove a flow."""
        self._document.remove_flow(name)

    def add_action(self, flow_name: str, action_type: str, params: dict) -> None:
        """Add an action to a flow."""
        action = ActionIR(action_type=action_type, params=params)
        self._document.add_action_to_flow(flow_name, action)

    # ─────────────────────────────────────────────────────────────
    # Asset Operations
    # ─────────────────────────────────────────────────────────────

    def add_asset(self, asset_id: str, path: str, threshold: float = 0.8) -> None:
        """Add a new asset."""
        asset = AssetIR(id=asset_id, path=path, threshold=threshold)
        self._document.add_asset(asset)

    def remove_asset(self, asset_id: str) -> None:
        """Remove an asset."""
        self._document.remove_asset(asset_id)

    def update_asset(self, asset_id: str, **kwargs: Any) -> None:
        """Update asset properties."""
        asset = self._document.ir.get_asset(asset_id)
        if asset:
            for key, value in kwargs.items():
                if hasattr(asset, key):
                    setattr(asset, key, value)
            self._document._notify_ir_changed("asset_updated")

    # ─────────────────────────────────────────────────────────────
    # Run Operations
    # ─────────────────────────────────────────────────────────────

    def start_run(self) -> bool:
        """
        Start script execution using EngineWorker (QThread).

        Returns True if started successfully.
        """
        if self._is_running:
            return False

        # Validate first
        errors = self.validate()
        if any(d.severity.value == "error" for d in errors):
            return False

        from core.dsl.adapter import ir_to_script

        try:
            script = ir_to_script(self._document.ir)

            # Use EngineWorker (QThread) instead of threading.Thread
            from app.ui.engine_worker import EngineWorker

            self._engine_worker = EngineWorker()
            self._engine_worker.step_started.connect(self._on_step_started)
            self._engine_worker.flow_completed.connect(self._on_flow_completed)
            self._engine_worker.error_occurred.connect(self._on_error)
            self._engine_worker.finished.connect(self._on_run_finished)

            # Set script and start
            self._engine_worker._script = script
            self._engine_worker._setup_context()
            self._engine_worker.start()

            self._is_running = True
            self.run_started.emit()
            return True

        except Exception as e:
            from infra import get_logger
            logger = get_logger("IDEController")
            logger.exception("Failed to start script: %s", e)
            self.errors_found.emit([str(e)])
            return False

    def _on_step_started(self, flow: str, index: int, action_type: str) -> None:
        """Handle step started from engine."""
        from infra import get_logger
        logger = get_logger("IDEController")
        logger.info("[%s] Step %d: %s", flow, index, action_type)

    def _on_flow_completed(self, flow: str, success: bool) -> None:
        """Handle flow completion from engine."""
        from infra import get_logger
        logger = get_logger("IDEController")
        if success:
            logger.info("Flow '%s' completed successfully", flow)
        else:
            logger.warning("Flow '%s' stopped", flow)

    def _on_error(self, message: str) -> None:
        """Handle error from engine."""
        self.errors_found.emit([message])

    def _on_run_finished(self) -> None:
        """Handle engine worker finished."""
        self._is_running = False
        self._engine_worker = None
        self.run_stopped.emit()

    def stop_run(self) -> None:
        """Stop script execution."""
        if self._is_running and hasattr(self, '_engine_worker') and self._engine_worker:
            from core.engine.context import EngineState
            if self._engine_worker.context:
                self._engine_worker.context.set_state(EngineState.STOPPING)
            self._engine_worker.wait(timeout=2000)
        self._is_running = False
        self.run_stopped.emit()

    def pause_run(self) -> None:
        """Toggle pause on script execution."""
        if not self._is_running:
            return

        if hasattr(self, '_engine_worker') and self._engine_worker:
            from core.engine.context import EngineState
            ctx = self._engine_worker.context
            if ctx:
                if ctx.state == EngineState.RUNNING:
                    ctx.set_state(EngineState.PAUSED)
                    from infra import get_logger
                    get_logger("IDEController").info("Script paused")
                elif ctx.state == EngineState.PAUSED:
                    ctx.set_state(EngineState.RUNNING)
                    from infra import get_logger
                    get_logger("IDEController").info("Script resumed")

    # ─────────────────────────────────────────────────────────────
    # Formatting
    # ─────────────────────────────────────────────────────────────

    def format_code(self) -> str:
        """
        Format the current code.

        Returns the formatted code.
        """
        from core.dsl.formatter import format_code

        formatted = format_code(self._document.code)
        self._document.update_from_code(formatted, source="format")
        return formatted
