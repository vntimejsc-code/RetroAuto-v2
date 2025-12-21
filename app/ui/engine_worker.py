"""
RetroAuto v2 - Engine Worker Thread

QThread wrapper for running engine in background.
"""

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.engine import EngineState, ExecutionContext, InterruptManager, Runner
from core.models import Script
from core.script.io import create_empty_script, load_script, save_script
from core.templates import TemplateStore
from infra import get_logger

logger = get_logger("EngineWorker")


class EngineWorker(QThread):
    """
    Background thread for engine execution.

    Emits signals for UI updates (thread-safe).
    """

    # Signals for UI updates
    step_started = Signal(str, int, str)  # flow, index, action_type
    step_completed = Signal(str, int, int)  # flow, index, elapsed_ms
    flow_completed = Signal(str, bool)  # flow, success
    state_changed = Signal(str)  # state name
    error_occurred = Signal(str)  # error message

    def __init__(self) -> None:
        super().__init__()
        self._ctx: ExecutionContext | None = None
        self._runner: Runner | None = None
        self._interrupt_mgr: InterruptManager | None = None
        self._script: Script | None = None
        self._templates: TemplateStore | None = None
        self._project_path: Path | None = None

    @property
    def is_loaded(self) -> bool:
        """Check if script is loaded."""
        return self._script is not None

    @property
    def script(self) -> Script | None:
        """Get current script."""
        return self._script

    @property
    def context(self) -> ExecutionContext | None:
        """Get execution context."""
        return self._ctx

    def new_script(self, name: str = "Untitled") -> None:
        """Create a new empty script."""
        self._script = create_empty_script(name)
        self._project_path = None
        self._setup_context()
        logger.info("Created new script: %s", name)

    def load_project(self, path: Path) -> None:
        """
        Load script from YAML file.

        Args:
            path: Path to script.yaml
        """
        try:
            self._script = load_script(path)
            self._project_path = path.parent
            self._setup_context()
            logger.info("Loaded project: %s", path)
        except Exception as e:
            logger.exception("Failed to load project: %s", e)
            self.error_occurred.emit(f"Failed to load: {e}")

    def save_project(self, path: Path | None = None) -> bool:
        """
        Save script to YAML file.

        Args:
            path: Target path (None = use current)

        Returns:
            True if saved successfully
        """
        if self._script is None:
            return False

        target = path or (self._project_path / "script.yaml" if self._project_path else None)
        if target is None:
            logger.warning("No save path specified")
            return False

        try:
            save_script(self._script, target)
            self._project_path = target.parent
            return True
        except Exception as e:
            logger.exception("Failed to save: %s", e)
            self.error_occurred.emit(f"Failed to save: {e}")
            return False

    def _setup_context(self) -> None:
        """Set up execution context and runner."""
        if self._script is None:
            return

        self._templates = TemplateStore(self._project_path or Path("."))

        # Preload templates if we have a project path
        if self._project_path and self._script.assets:
            errors = self._templates.preload(self._script.assets)
            if errors:
                logger.warning("Template preload errors: %s", errors)

        self._ctx = ExecutionContext(
            script=self._script,
            templates=self._templates,
        )

        self._runner = Runner(
            self._ctx,
            on_step=self._on_step,
            on_complete=self._on_flow_complete,
        )

        self._interrupt_mgr = InterruptManager(self._ctx)
        self._interrupt_mgr.set_runner(self._runner)

    def _on_step(self, flow: str, idx: int, action) -> None:  # type: ignore
        """Callback when step starts."""
        action_type = type(action).__name__
        self.step_started.emit(flow, idx, action_type)

    def _on_flow_complete(self, flow: str, success: bool) -> None:
        """Callback when flow completes."""
        self.flow_completed.emit(flow, success)

    def run(self) -> None:
        """Execute the main flow (called by QThread.start)."""
        if not self._runner or not self._script:
            self.error_occurred.emit("No script loaded")
            return

        try:
            # Start interrupt watching
            if self._interrupt_mgr:
                self._interrupt_mgr.start_watching()

            self.state_changed.emit("running")

            # Run main flow
            success = self._runner.run_flow(self._script.main_flow)

            self.state_changed.emit("idle")

            if success:
                logger.info("Script completed successfully")
            else:
                logger.warning("Script stopped or failed")
        except Exception as e:
            logger.exception("Engine error: %s", e)
            self.error_occurred.emit(str(e))
            self.state_changed.emit("error")
        finally:
            if self._interrupt_mgr:
                self._interrupt_mgr.stop_watching()

    def start_from(self, flow: str, step: int) -> None:
        """Start execution from specific step."""
        if not self._runner:
            return
        # Override run to use specific starting point
        self._run_flow = flow
        self._run_step = step
        self.start()

    def pause(self) -> None:
        """Request pause."""
        if self._ctx:
            self._ctx.request_pause()
            self.state_changed.emit("paused")

    def resume(self) -> None:
        """Resume from pause."""
        if self._ctx:
            self._ctx.request_resume()
            self.state_changed.emit("running")

    def stop(self) -> None:
        """Request stop."""
        if self._ctx:
            self._ctx.request_stop()
            self.state_changed.emit("stopping")

    def run_single_step(self, flow: str, step: int) -> bool:
        """Execute single step (blocking)."""
        if not self._runner:
            return False
        return self._runner.run_step(flow, step)

    def get_state(self) -> str:
        """Get current engine state."""
        if self._ctx:
            return self._ctx.state.value
        return "idle"
