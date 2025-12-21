"""
RetroAuto v2 - Actions Panel

Manages the list of actions in a flow.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.models import (
    Action,
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
from infra import get_logger

logger = get_logger("ActionsPanel")

# Action types available
ACTION_TYPES = [
    ("WaitImage", "⏳ Wait Image"),
    ("Click", "🖱️ Click"),
    ("IfImage", "❓ If Image"),
    ("Hotkey", "⌨️ Hotkey"),
    ("TypeText", "📝 Type Text"),
    ("Label", "🏷️ Label"),
    ("Goto", "➡️ Goto"),
    ("RunFlow", "▶️ Run Flow"),
    ("Delay", "⏱️ Delay"),
]

ACTION_DEFAULTS = {
    "WaitImage": lambda: WaitImage(asset_id=""),
    "Click": lambda: Click(),
    "IfImage": lambda: IfImage(asset_id=""),
    "Hotkey": lambda: Hotkey(keys=[]),
    "TypeText": lambda: TypeText(text=""),
    "Label": lambda: Label(name=""),
    "Goto": lambda: Goto(label=""),
    "RunFlow": lambda: RunFlow(flow_name=""),
    "Delay": lambda: Delay(ms=1000),
}


class ActionsPanel(QWidget):
    """
    Panel for managing actions in a flow.

    Features:
    - List of actions with icons
    - Add action menu (WaitImage, Click, etc.)
    - Reorder (up/down)
    - Context menu: Run Step, Run From Here
    """

    action_selected = Signal(dict)  # action data for properties panel
    action_changed = Signal()  # when list changes
    run_step_requested = Signal(int)  # step index

    def __init__(self) -> None:
        super().__init__()
        self._actions: list[Action] = []
        self._current_highlight: int = -1
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Group box
        group = QGroupBox("Actions")
        group_layout = QVBoxLayout(group)

        # Action list with extended selection
        self.action_list = QListWidget()
        self.action_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.action_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.action_list.currentItemChanged.connect(self._on_selection_changed)
        self.action_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.action_list.customContextMenuRequested.connect(self._show_context_menu)
        group_layout.addWidget(self.action_list)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("+ Add")
        self.btn_add.clicked.connect(self._show_add_menu)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_delete.setEnabled(False)

        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.clicked.connect(self._on_clear_all)

        self.btn_up = QPushButton("▲")
        self.btn_up.setFixedWidth(30)
        self.btn_up.clicked.connect(self._on_move_up)
        self.btn_up.setEnabled(False)

        self.btn_down = QPushButton("▼")
        self.btn_down.setFixedWidth(30)
        self.btn_down.clicked.connect(self._on_move_down)
        self.btn_down.setEnabled(False)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        group_layout.addLayout(btn_layout)

        layout.addWidget(group)

        # Setup keyboard shortcuts
        self._setup_shortcuts()

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        # Delete key
        self.del_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.action_list)
        self.del_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.del_shortcut.activated.connect(self._on_delete)

        # Ctrl+A to select all
        self.select_all_shortcut = QShortcut(QKeySequence.StandardKey.SelectAll, self.action_list)
        self.select_all_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.select_all_shortcut.activated.connect(self.action_list.selectAll)

    def load_actions(self, actions: list[Action]) -> None:
        """Load actions from script flow."""
        self._actions = list(actions)
        self._refresh_list()

    def get_actions(self) -> list[Action]:
        """Get current actions list."""
        return list(self._actions)

    def _refresh_list(self) -> None:
        """Refresh list widget from internal actions."""
        self.action_list.clear()

        for i, action in enumerate(self._actions):
            action_type = type(action).__name__
            label = next((l for t, l in ACTION_TYPES if t == action_type), action_type)

            # Add details to label
            detail = self._get_action_detail(action)
            if detail:
                label = f"{label}: {detail}"

            item = QListWidgetItem(label)
            item.setData(256, i)  # Qt.UserRole
            self.action_list.addItem(item)

    def _get_action_detail(self, action: Action) -> str:
        """Get short detail string for action."""
        if isinstance(action, WaitImage):
            return action.asset_id or "?"
        elif isinstance(action, Click):
            # Show specific click type
            click_type = ""
            if action.clicks == 2:
                click_type = "Double "
            elif action.button == "right":
                click_type = "Right "
            elif action.button == "middle":
                click_type = "Middle "
            else:
                click_type = "Left "

            if action.use_match:
                return f"{click_type}@ match"
            elif action.x is not None:
                return f"{click_type}({action.x}, {action.y})"
            return click_type.strip()
        elif isinstance(action, IfImage):
            return action.asset_id or "?"
        elif isinstance(action, Hotkey):
            return "+".join(action.keys) if action.keys else "?"
        elif isinstance(action, TypeText):
            return action.text[:15] + "..." if len(action.text) > 15 else action.text
        elif isinstance(action, Label):
            return action.name or "?"
        elif isinstance(action, Goto):
            return action.label or "?"
        elif isinstance(action, RunFlow):
            return action.flow_name or "?"
        elif isinstance(action, Delay):
            return f"{action.ms}ms"
        return ""

    def highlight_step(self, idx: int) -> None:
        """Highlight currently executing step."""
        # Clear previous highlight
        if 0 <= self._current_highlight < self.action_list.count():
            item = self.action_list.item(self._current_highlight)
            if item:
                item.setBackground(QColor(255, 255, 255))

        # Set new highlight
        self._current_highlight = idx
        if 0 <= idx < self.action_list.count():
            item = self.action_list.item(idx)
            if item:
                item.setBackground(QColor(255, 255, 200))  # Light yellow
                self.action_list.scrollToItem(item)

    def _on_selection_changed(
        self, current: QListWidgetItem | None, _: QListWidgetItem | None
    ) -> None:
        has_selection = current is not None
        self.btn_delete.setEnabled(has_selection)
        self.btn_up.setEnabled(has_selection and self.action_list.currentRow() > 0)
        self.btn_down.setEnabled(
            has_selection and self.action_list.currentRow() < self.action_list.count() - 1
        )

        if current:
            idx = self.action_list.row(current)
            if idx < len(self._actions):
                action = self._actions[idx]
                # Convert to dict for properties panel
                data = {
                    "index": idx,
                    "type": type(action).__name__,
                    "action": action,
                }
                self.action_selected.emit(data)

    def _show_add_menu(self) -> None:
        """Show menu for adding action types."""
        menu = QMenu(self)
        for action_type, label in ACTION_TYPES:
            action = menu.addAction(label)
            action.setData(action_type)
            action.triggered.connect(lambda checked, t=action_type: self._add_action(t))
        menu.exec(self.btn_add.mapToGlobal(self.btn_add.rect().bottomLeft()))

    def _add_action(self, action_type: str) -> None:
        """Add a new action of given type."""
        factory = ACTION_DEFAULTS.get(action_type)
        if factory:
            action = factory()
            self._actions.append(action)
            self._refresh_list()

            # Select the new action
            self.action_list.setCurrentRow(len(self._actions) - 1)
            self.action_changed.emit()
            logger.info("Added action: %s", action_type)

    def _on_delete(self) -> None:
        """Delete selected actions."""
        selected = self.action_list.selectedItems()
        if not selected:
            return

        # Get indices in reverse order to delete from end
        rows = sorted([self.action_list.row(item) for item in selected], reverse=True)
        for row in rows:
            if 0 <= row < len(self._actions):
                del self._actions[row]

        self._refresh_list()
        self.action_changed.emit()
        logger.info("Deleted %d actions", len(rows))

    def _on_clear_all(self) -> None:
        """Clear all actions."""
        self._actions.clear()
        self._refresh_list()
        self.action_changed.emit()
        logger.info("Cleared all actions")

    def _on_move_up(self) -> None:
        """Move selected action up."""
        row = self.action_list.currentRow()
        if row > 0:
            self._actions[row], self._actions[row - 1] = self._actions[row - 1], self._actions[row]
            self._refresh_list()
            self.action_list.setCurrentRow(row - 1)
            self.action_changed.emit()

    def _on_move_down(self) -> None:
        """Move selected action down."""
        row = self.action_list.currentRow()
        if row < len(self._actions) - 1:
            self._actions[row], self._actions[row + 1] = self._actions[row + 1], self._actions[row]
            self._refresh_list()
            self.action_list.setCurrentRow(row + 1)
            self.action_changed.emit()

    def _show_context_menu(self, pos) -> None:  # type: ignore
        """Show context menu for run actions."""
        item = self.action_list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        idx = self.action_list.row(item)
        menu.addAction("▶ Run Step", lambda: self.run_step_requested.emit(idx))
        menu.addAction("▶▶ Run From Here", lambda: logger.info("Run from %d", idx))
        menu.exec(self.action_list.mapToGlobal(pos))

    def update_action(self, data: dict) -> None:
        """Update action from properties panel."""
        idx = data.get("index", -1)
        action = data.get("action")

        if 0 <= idx < len(self._actions) and action:
            self._actions[idx] = action
            self._refresh_list()
            self.action_list.setCurrentRow(idx)
            logger.debug("Updated action %d", idx)
