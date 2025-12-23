"""
RetroAuto v2 - Hybrid Actions Panel

Shows GUI actions alongside their DSL code representation.
Bridges the gap between low-code and high-tech users.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.ui.actions_panel import ActionsPanel
from core.dsl.adapter import action_to_ir
from core.dsl.ir import IRMapper
from core.models import Action
from infra import get_logger

logger = get_logger("HybridPanel")


class CodePreview(QPlainTextEdit):
    """Read-only code preview with syntax highlighting style."""

    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))
        self.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                padding: 8px;
            }
        """
        )
        self.setPlaceholderText("// Code preview will appear here...")


class HybridActionsPanel(QWidget):
    """
    Hybrid panel showing Actions GUI + Code side-by-side.

    Layout:
    ┌─────────────────────────────────────────────────┐
    │ [GUI Mode] [Code Mode] [Hybrid Mode*]           │
    ├──────────────────────┬──────────────────────────┤
    │  Actions Panel       │  Code Preview            │
    │  (Drag-drop GUI)     │  (Read-only DSL)         │
    │                      │                          │
    └──────────────────────┴──────────────────────────┘
    """

    # Forward signals from ActionsPanel
    action_selected = Signal(dict)
    action_changed = Signal()
    run_step_requested = Signal(int)
    flow_editor_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._view_mode = "hybrid"  # "gui", "code", "hybrid"
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # View mode toggle buttons
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(2)

        self.btn_gui = QPushButton("📋 GUI")
        self.btn_gui.setCheckable(True)
        self.btn_gui.clicked.connect(lambda: self._set_view_mode("gui"))

        self.btn_code = QPushButton("📝 Code")
        self.btn_code.setCheckable(True)
        self.btn_code.clicked.connect(lambda: self._set_view_mode("code"))

        self.btn_hybrid = QPushButton("🔀 Hybrid")
        self.btn_hybrid.setCheckable(True)
        self.btn_hybrid.setChecked(True)
        self.btn_hybrid.clicked.connect(lambda: self._set_view_mode("hybrid"))

        btn_bar.addWidget(self.btn_gui)
        btn_bar.addWidget(self.btn_code)
        btn_bar.addWidget(self.btn_hybrid)

        btn_bar.addStretch()

        # Link to Visual Flow Editor
        self.btn_flow = QPushButton("🎨 Flow Editor")
        self.btn_flow.clicked.connect(self.flow_editor_requested.emit)
        btn_bar.addWidget(self.btn_flow)

        layout.addLayout(btn_bar)

        # Splitter for side-by-side view
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Actions Panel (GUI)
        self.actions_panel = ActionsPanel()
        self.splitter.addWidget(self.actions_panel)

        # Right: Code Preview
        self.code_preview = CodePreview()
        self.splitter.addWidget(self.code_preview)

        # Default split 60/40
        self.splitter.setStretchFactor(0, 6)
        self.splitter.setStretchFactor(1, 4)

        layout.addWidget(self.splitter)

    def _connect_signals(self) -> None:
        # Forward ActionsPanel signals
        self.actions_panel.action_selected.connect(self.action_selected.emit)
        self.actions_panel.action_changed.connect(self._on_actions_changed)
        self.actions_panel.run_step_requested.connect(self.run_step_requested.emit)

        # Update code preview when selection changes
        self.actions_panel.action_selected.connect(self._highlight_selected_code)

    def _set_view_mode(self, mode: str) -> None:
        """Switch between GUI, Code, and Hybrid view modes."""
        self._view_mode = mode

        # Update button states
        self.btn_gui.setChecked(mode == "gui")
        self.btn_code.setChecked(mode == "code")
        self.btn_hybrid.setChecked(mode == "hybrid")

        # Update visibility
        if mode == "gui":
            self.actions_panel.show()
            self.code_preview.hide()
        elif mode == "code":
            self.actions_panel.hide()
            self.code_preview.show()
        else:  # hybrid
            self.actions_panel.show()
            self.code_preview.show()

        logger.info(f"View mode changed to: {mode}")

    def _on_actions_changed(self) -> None:
        """Regenerate code preview when actions change."""
        self._update_code_preview()
        self.action_changed.emit()

    def _update_code_preview(self) -> None:
        """Generate DSL code from current actions."""
        actions = self.actions_panel.get_actions()

        lines = ["// Auto-generated from Actions Panel", ""]

        for action in actions:
            try:
                action_ir = action_to_ir(action)
                code = IRMapper._action_to_code(action_ir)
                lines.append(f"  {code}")
            except Exception as e:
                lines.append(f"  // Error: {e}")

        self.code_preview.setPlainText("\n".join(lines))

    def _highlight_selected_code(self, data: dict) -> None:
        """Highlight the code line corresponding to selected action."""
        idx = data.get("index", -1)
        if idx >= 0:
            # Move cursor to that line (line = idx + 2 for header)
            cursor = self.code_preview.textCursor()
            block = self.code_preview.document().findBlockByLineNumber(idx + 2)
            if block.isValid():
                cursor.setPosition(block.position())
                self.code_preview.setTextCursor(cursor)
                self.code_preview.centerCursor()

    # ─────────────────────────────────────────────────────────────
    # Proxy methods to ActionsPanel for compatibility
    # ─────────────────────────────────────────────────────────────

    def load_actions(self, actions: list[Action]) -> None:
        """Load actions into the panel."""
        self.actions_panel.load_actions(actions)
        self._update_code_preview()

    def get_actions(self) -> list[Action]:
        """Get current actions list."""
        return self.actions_panel.get_actions()

    def update_action(self, data: dict) -> None:
        """Update action from properties panel."""
        self.actions_panel.update_action(data)
        self._update_code_preview()

    def highlight_step(self, idx: int) -> None:
        """Highlight currently executing step."""
        self.actions_panel.highlight_step(idx)

    def insert_action_for_asset(self, asset_id: str, action_type: str) -> None:
        """Insert action for asset."""
        self.actions_panel.insert_action_for_asset(asset_id, action_type)
        self._update_code_preview()

    @property
    def _actions(self) -> list[Action]:
        """Proxy to internal ActionsPanel._actions for compatibility."""
        return self.actions_panel._actions

    @_actions.setter
    def _actions(self, value: list[Action]) -> None:
        """Set actions and update code preview."""
        self.actions_panel._actions = value

    def _refresh_list(self) -> None:
        """Proxy to internal ActionsPanel._refresh_list."""
        self.actions_panel._refresh_list()
        self._update_code_preview()

    @property
    def action_list(self):
        """Proxy to action_list widget for compatibility."""
        return self.actions_panel.action_list
