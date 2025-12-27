"""
RetroAuto v2 - Sync Manager

Coordinates bidirectional synchronization between GUI panels and ScriptDocument.
Handles debouncing, conflict prevention, and cursor preservation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Signal

from core.dsl.adapter import action_to_ir, ir_to_actions
from core.dsl.document import ScriptDocument
from core.models import Action
from infra import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger("SyncManager")


class SyncManager(QObject):
    """
    Manages sync between GUI and ScriptDocument.

    Features:
    - Debounced code → IR sync (500ms delay)
    - Immediate GUI → IR → code sync
    - Prevents feedback loops
    - Cursor position preservation

    Usage:
        doc = ScriptDocument()
        sync = SyncManager(doc)

        # Connect ActionsPanel
        actions_panel.action_changed.connect(sync.on_action_changed)
        sync.ir_changed.connect(actions_panel.refresh_from_ir)

        # Connect CodeEditor
        code_editor.textChanged.connect(sync.on_code_changed)
        sync.code_regenerated.connect(code_editor.set_code)
    """

    # Signals
    ir_changed = Signal(str)  # change_type
    code_regenerated = Signal(str)  # new code
    errors_occurred = Signal(list)  # error messages

    def __init__(self, document: ScriptDocument) -> None:
        super().__init__()
        self._doc = document
        self._sync_lock = False

        # Debounce timer for code → IR sync
        self._code_debounce = QTimer()
        self._code_debounce.setSingleShot(True)
        self._code_debounce.timeout.connect(self._do_code_to_ir)
        self._pending_code: str = ""

        # Connect to document callbacks
        self._doc.on_ir_changed(self._on_doc_ir_changed)
        self._doc.on_code_changed(self._on_doc_code_changed)
        self._doc.on_error(self._on_doc_error)

        logger.info("SyncManager initialized")

    @property
    def document(self) -> ScriptDocument:
        """Get the managed document."""
        return self._doc

    # ─────────────────────────────────────────────────────────────
    # Code Editor → IR (debounced)
    # ─────────────────────────────────────────────────────────────

    def on_code_changed(self, new_code: str) -> None:
        """
        Handle code changes from the editor.

        Debounces by 500ms to avoid parsing on every keystroke.
        """
        if self._sync_lock:
            return

        self._pending_code = new_code
        self._code_debounce.start(500)  # 500ms debounce

    def on_code_saved(self, code: str) -> None:
        """
        Handle code save from IDE - sync immediately without debounce.

        Use this when user explicitly saves, not on every keystroke.
        """
        if self._sync_lock:
            logger.warning("on_code_saved: sync_lock is active, skipping")
            return

        # Cancel any pending debounced sync
        self._code_debounce.stop()

        logger.info("on_code_saved: Starting immediate sync (code length: %d)", len(code))

        # Sync immediately
        self._sync_lock = True
        try:
            self._doc.update_from_code(code, source="editor")
            logger.info(
                "on_code_saved: update_from_code completed, IR valid: %s", self._doc.ir.is_valid
            )
            logger.info("on_code_saved: IR has %d flows", len(self._doc.ir.flows))
            if self._doc.ir.flows:
                logger.info(
                    "on_code_saved: main flow has %d actions", len(self._doc.ir.flows[0].actions)
                )
        finally:
            self._sync_lock = False

    def _do_code_to_ir(self) -> None:
        """Execute the debounced code → IR sync."""
        if self._sync_lock:
            return

        self._sync_lock = True
        try:
            self._doc.update_from_code(self._pending_code, source="editor")
        finally:
            self._sync_lock = False

    # ─────────────────────────────────────────────────────────────
    # GUI → IR → Code (immediate)
    # ─────────────────────────────────────────────────────────────

    def on_action_changed(
        self,
        flow_name: str,
        action_index: int,
        action: Action,
    ) -> None:
        """
        Handle action changed in GUI.

        Immediately updates IR and regenerates code.
        """
        if self._sync_lock:
            return

        self._sync_lock = True
        try:
            action_ir = action_to_ir(action)
            flow = self._doc.ir.get_flow(flow_name)

            if flow and 0 <= action_index < len(flow.actions):
                flow.actions[action_index] = action_ir
                self._doc._is_dirty = True
                self._doc._regenerate_code()
                self._doc._notify_ir_changed("gui_action_changed")
        finally:
            self._sync_lock = False

    def on_action_added(
        self,
        flow_name: str,
        action: Action,
        at_index: int = -1,
    ) -> None:
        """Handle action added in GUI."""
        if self._sync_lock:
            return

        self._sync_lock = True
        try:
            action_ir = action_to_ir(action)
            flow = self._doc.ir.get_flow(flow_name)

            if flow:
                if at_index < 0 or at_index >= len(flow.actions):
                    flow.actions.append(action_ir)
                else:
                    flow.actions.insert(at_index, action_ir)
                self._doc._is_dirty = True
                self._doc._regenerate_code()
                self._doc._notify_ir_changed("gui_action_added")
        finally:
            self._sync_lock = False

    def on_action_removed(self, flow_name: str, action_index: int) -> None:
        """Handle action removed in GUI."""
        if self._sync_lock:
            return

        self._sync_lock = True
        try:
            flow = self._doc.ir.get_flow(flow_name)

            if flow and 0 <= action_index < len(flow.actions):
                del flow.actions[action_index]
                self._doc._is_dirty = True
                self._doc._regenerate_code()
                self._doc._notify_ir_changed("gui_action_removed")
        finally:
            self._sync_lock = False

    def on_actions_reordered(
        self,
        flow_name: str,
        from_index: int,
        to_index: int,
    ) -> None:
        """Handle action reordered in GUI."""
        if self._sync_lock:
            return

        self._sync_lock = True
        try:
            flow = self._doc.ir.get_flow(flow_name)

            if flow:
                action = flow.actions.pop(from_index)
                flow.actions.insert(to_index, action)
                self._doc._is_dirty = True
                self._doc._regenerate_code()
                self._doc._notify_ir_changed("gui_action_reordered")
        finally:
            self._sync_lock = False

    # ─────────────────────────────────────────────────────────────
    # IR → GUI Helpers
    # ─────────────────────────────────────────────────────────────

    def get_flow_actions(self, flow_name: str) -> list[Action]:
        """Get all actions for a flow as Action models.

        Uses ir_to_actions() which automatically adds EndIf/EndLoop/EndWhile
        markers for proper GUI flat list display.
        """
        flow = self._doc.ir.get_flow(flow_name)
        if not flow:
            return []

        # Use ir_to_actions which adds auto-EndIf markers
        return ir_to_actions(flow.actions)

    def get_flow_names(self) -> list[str]:
        """Get all flow names."""
        return [f.name for f in self._doc.ir.flows]

    # ─────────────────────────────────────────────────────────────
    # Document Callback Handlers
    # ─────────────────────────────────────────────────────────────

    def _on_doc_ir_changed(self, change_type: str) -> None:
        """Forward IR changes to listeners."""
        if change_type.startswith("code_"):
            # IR changed from code edit - GUI should refresh
            self.ir_changed.emit(change_type)

    def _on_doc_code_changed(self, source: str) -> None:
        """Forward code changes to listeners."""
        if source == "gui":
            # Code regenerated from GUI change - editor should update
            self.code_regenerated.emit(self._doc.code)

    def _on_doc_error(self, errors: list[str]) -> None:
        """Forward errors to listeners."""
        self.errors_occurred.emit(errors)

    # ─────────────────────────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────────────────────────

    def force_sync_from_ir(self) -> None:
        """Force regenerate code from current IR."""
        self._doc._regenerate_code()

    def cancel_pending_sync(self) -> None:
        """Cancel any pending debounced sync."""
        self._code_debounce.stop()
        self._pending_code = ""
