"""
RetroAuto v2 - Actions Panel

Manages the list of actions in a flow.
"""

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QKeySequence, QPainter, QPen, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from core.models import (
    Action,
    Click,
    ClickImage,
    Delay,
    DelayRandom,
    Drag,
    Else,
    EndIf,
    Goto,
    Hotkey,
    IfImage,
    IfPixel,
    Label,
    Loop,
    PixelColor,
    RunFlow,
    Scroll,
    TypeText,
    WaitImage,
    WaitPixel,
    WhileImage,
)
from infra import get_logger

logger = get_logger("ActionsPanel")

# Action types available (ordered by frequency)
ACTION_TYPES = [
    ("ClickImage", "🎯 Click Image"),
    ("WaitImage", "👁️ Wait Image"),
    ("Click", "🖱️ Click"),
    ("IfImage", "❓ If Image"),
    ("Else", "↩️ Else"),
    ("EndIf", "🔚 EndIf"),
    ("Delay", "⏱️ Delay"),
    ("DelayRandom", "🎲 Random Delay"),
    ("Hotkey", "⌨️ Hotkey"),
    ("TypeText", "📝 Type Text"),
    ("Loop", "🔁 Loop"),
    ("Label", "🏷️ Label"),
    ("Goto", "↩️ Goto"),
    ("RunFlow", "▶️ Run Flow"),
    ("WaitPixel", "🎨 Wait Pixel"),
    ("IfPixel", "🎯 If Pixel"),
    ("Drag", "↔️ Drag"),
    ("Scroll", "📜 Scroll"),
    ("WhileImage", "🔄 While Image"),
]

ACTION_DEFAULTS = {
    "ClickImage": lambda: ClickImage(asset_id=""),
    "WaitImage": lambda: WaitImage(asset_id=""),
    "WaitPixel": lambda: WaitPixel(x=0, y=0, color=PixelColor(r=255, g=0, b=0)),
    "Click": lambda: Click(),
    "IfImage": lambda: IfImage(asset_id=""),
    "Else": lambda: Else(),
    "EndIf": lambda: EndIf(),
    "IfPixel": lambda: IfPixel(x=0, y=0, color=PixelColor(r=255, g=0, b=0)),
    "Hotkey": lambda: Hotkey(keys=[]),
    "TypeText": lambda: TypeText(text=""),
    "Label": lambda: Label(name=""),
    "Goto": lambda: Goto(label=""),
    "RunFlow": lambda: RunFlow(flow_name=""),
    "Delay": lambda: Delay(ms=1000),
    "DelayRandom": lambda: DelayRandom(),
    "Drag": lambda: Drag(from_x=0, from_y=0, to_x=100, to_y=100),
    "Scroll": lambda: Scroll(),
    "Loop": lambda: Loop(),
    "WhileImage": lambda: WhileImage(asset_id=""),
}

# Custom MIME type for asset drag
ASSET_MIME_TYPE = "application/x-retroauto-asset"


class ActionListWidget(QListWidget):
    """
    Custom list widget with external drop support from Assets panel.
    - Drop ON an item: update that action's asset_id (if applicable)
    - Drop BETWEEN items: shows blue indicator line (insert position)
    """

    asset_dropped_on_item = Signal(str, int)  # asset_id, item_index (update existing)
    asset_dropped_insert = Signal(str, int)  # asset_id, insert_index (create new)

    def __init__(self, parent=None) -> None:  # type: ignore
        super().__init__(parent)
        self._drop_indicator_index = -1
        self._drop_on_item_index = -1  # -1 = insert mode, >=0 = update mode
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.viewport().setAcceptDrops(True)

    def dragEnterEvent(self, event) -> None:  # type: ignore
        """Accept drag from Assets panel or internal move."""
        mime = event.mimeData()
        if mime.hasFormat(ASSET_MIME_TYPE):
            event.acceptProposedAction()
        elif mime.hasFormat("application/x-qabstractitemmodeldatalist"):
            # Internal move
            super().dragEnterEvent(event)
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # type: ignore
        """Update drop indicator - detect if dropping ON item or BETWEEN items."""
        mime = event.mimeData()
        if mime.hasFormat(ASSET_MIME_TYPE):
            pos = event.position().toPoint()
            item = self.itemAt(pos)

            if item:
                rect = self.visualItemRect(item)
                index = self.row(item)
                # Check if in center 60% of item (update mode) or edge 20% (insert mode)
                item_height = rect.height()
                edge_zone = item_height * 0.2

                if pos.y() < rect.top() + edge_zone:
                    # Top edge - insert before
                    self._drop_on_item_index = -1
                    self._drop_indicator_index = index
                elif pos.y() > rect.bottom() - edge_zone:
                    # Bottom edge - insert after
                    self._drop_on_item_index = -1
                    self._drop_indicator_index = index + 1
                else:
                    # Center - update this item
                    self._drop_on_item_index = index
                    self._drop_indicator_index = -1
            else:
                # Below all items - insert at end
                self._drop_on_item_index = -1
                self._drop_indicator_index = self.count()

            self.viewport().update()
            event.acceptProposedAction()
        else:
            self._drop_indicator_index = -1
            self._drop_on_item_index = -1
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event) -> None:  # type: ignore
        """Clear drop indicators."""
        self._drop_indicator_index = -1
        self._drop_on_item_index = -1
        self.viewport().update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # type: ignore
        """Handle drop from Assets panel."""
        mime = event.mimeData()
        if mime.hasFormat(ASSET_MIME_TYPE):
            asset_id = mime.data(ASSET_MIME_TYPE).data().decode("utf-8")

            if self._drop_on_item_index >= 0:
                # Update existing action
                self.asset_dropped_on_item.emit(asset_id, self._drop_on_item_index)
            else:
                # Insert new action
                insert_index = self._drop_indicator_index
                if insert_index < 0:
                    insert_index = self.count()
                self.asset_dropped_insert.emit(asset_id, insert_index)

            self._drop_indicator_index = -1
            self._drop_on_item_index = -1
            self.viewport().update()
            event.acceptProposedAction()
        else:
            self._drop_indicator_index = -1
            self._drop_on_item_index = -1
            super().dropEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore
        """Paint drop indicator line or item highlight."""
        super().paintEvent(event)

        # Draw item highlight for update mode
        if self._drop_on_item_index >= 0:
            item = self.item(self._drop_on_item_index)
            if item:
                painter = QPainter(self.viewport())
                rect = self.visualItemRect(item)
                # Semi-transparent blue highlight
                painter.fillRect(rect, QColor(0, 120, 212, 60))  # #0078d4 with alpha
                # Blue border
                pen = QPen(QColor("#0078d4"), 2)
                painter.setPen(pen)
                painter.drawRect(rect.adjusted(1, 1, -1, -1))
                painter.end()

        # Draw insert line indicator
        elif self._drop_indicator_index >= 0:
            painter = QPainter(self.viewport())
            pen = QPen(QColor("#0078d4"), 3)  # Blue line, 3px thick
            painter.setPen(pen)

            # Calculate Y position for indicator
            if self._drop_indicator_index < self.count():
                item = self.item(self._drop_indicator_index)
                if item:
                    rect = self.visualItemRect(item)
                    y = rect.top()
                else:
                    y = 0
            else:
                # After last item
                if self.count() > 0:
                    item = self.item(self.count() - 1)
                    if item:
                        rect = self.visualItemRect(item)
                        y = rect.bottom()
                    else:
                        y = 0
                else:
                    y = 0

            # Draw horizontal line across widget
            painter.drawLine(0, y, self.viewport().width(), y)
            painter.end()


class ActionsPanel(QWidget):
    """
    Panel for managing actions in a flow.

    Features:
    - List of actions with icons
    - Add action menu (WaitImage, Click, etc.)
    - Reorder (up/down)
    - Context menu: Run Step, Run From Here
    - Drop from Assets panel to create WaitImage
    """

    action_selected = Signal(dict)  # action data for properties panel
    action_changed = Signal()  # when list changes
    run_step_requested = Signal(int)  # step index

    def __init__(self) -> None:
        super().__init__()
        self._actions: list[Action] = []
        self._current_highlight: int = -1
        self._clipboard: list[Action] = []  # For copy/paste
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Group box
        group = QGroupBox("Actions")
        group_layout = QVBoxLayout(group)

        # Action list with extended selection and drop support
        self.action_list = ActionListWidget(self)
        self.action_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.action_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.action_list.currentItemChanged.connect(self._on_selection_changed)
        self.action_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.action_list.customContextMenuRequested.connect(self._show_context_menu)
        self.action_list.asset_dropped_on_item.connect(self._on_asset_dropped_on_item)
        self.action_list.asset_dropped_insert.connect(self._on_asset_dropped_insert)
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
        """Setup keyboard shortcuts for gamer-friendly workflow."""
        # Delete key
        self.del_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.action_list)
        self.del_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.del_shortcut.activated.connect(self._on_delete)

        # Ctrl+A to select all
        self.select_all_shortcut = QShortcut(QKeySequence.StandardKey.SelectAll, self.action_list)
        self.select_all_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.select_all_shortcut.activated.connect(self.action_list.selectAll)

        # Ctrl+D to duplicate
        self.dup_shortcut = QShortcut(QKeySequence("Ctrl+D"), self.action_list)
        self.dup_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.dup_shortcut.activated.connect(self._on_duplicate)

        # Ctrl+C to copy
        self.copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self.action_list)
        self.copy_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.copy_shortcut.activated.connect(self._on_copy)

        # Ctrl+V to paste
        self.paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self.action_list)
        self.paste_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.paste_shortcut.activated.connect(self._on_paste)

        # Ctrl+Shift+Up to move up
        self.move_up_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Up"), self.action_list)
        self.move_up_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.move_up_shortcut.activated.connect(self._on_move_up)

        # Ctrl+Shift+Down to move down
        self.move_down_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Down"), self.action_list)
        self.move_down_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.move_down_shortcut.activated.connect(self._on_move_down)

    def load_actions(self, actions: list[Action]) -> None:
        """Load actions from script flow."""
        self._actions = list(actions)
        self._refresh_list()

    def get_actions(self) -> list[Action]:
        """Get current actions list."""
        return list(self._actions)

    def _refresh_list(self) -> None:
        """Refresh list widget from internal actions with visual indentation."""
        self.action_list.clear()

        # Track if we're inside an if block for indentation
        if_depth = 0

        for i, action in enumerate(self._actions):
            action_type = type(action).__name__
            label = next(
                (label_text for t, label_text in ACTION_TYPES if t == action_type), action_type
            )

            # Add details to label
            detail = self._get_action_detail(action)
            if detail:
                label = f"{label}: {detail}"

            # Handle visual indentation for if/else/endif blocks
            prefix = ""
            if action_type == "IfImage":
                if_depth += 1
            elif action_type == "Else":
                # Else is at current depth but marks transition
                label = "┣ Else"
            elif action_type == "EndIf":
                label = "┗ EndIf"
                if_depth = max(0, if_depth - 1)
            elif if_depth > 0:
                # Inside an if block - indent
                prefix = "│  " * (if_depth - 1) + "┣── "

            item = QListWidgetItem(prefix + label)
            item.setData(256, i)  # Qt.UserRole
            self.action_list.addItem(item)

    def _get_action_detail(self, action: Action) -> str:
        """Get short detail string for action."""
        if isinstance(action, ClickImage):
            return action.asset_id or "?"
        elif isinstance(action, WaitImage):
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
        elif isinstance(action, DelayRandom):
            return f"{action.min_ms}-{action.max_ms}ms"
        elif isinstance(action, Drag):
            return f"({action.from_x},{action.from_y})→({action.to_x},{action.to_y})"
        elif isinstance(action, Scroll):
            direction = "↑" if action.amount > 0 else "↓"
            return f"{direction} {abs(action.amount)}"
        elif isinstance(action, Loop):
            count = action.count if action.count else "∞"
            return f"{count}x [{len(action.actions)} actions]"
        elif isinstance(action, WhileImage):
            mode = "present" if action.while_present else "absent"
            return f"{action.asset_id} ({mode})"
        elif isinstance(action, WaitPixel):
            c = action.color
            mode = "appear" if action.appear else "disappear"
            return f"({action.x},{action.y}) RGB({c.r},{c.g},{c.b}) {mode}"
        elif isinstance(action, IfPixel):
            c = action.color
            return f"({action.x},{action.y}) RGB({c.r},{c.g},{c.b})"
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
        """Show enhanced context menu with edit actions."""
        item = self.action_list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        idx = self.action_list.row(item)

        # Run actions
        menu.addAction("▶ Test Step", lambda: self.run_step_requested.emit(idx))
        menu.addSeparator()

        # Edit actions
        menu.addAction("📋 Duplicate        Ctrl+D", self._on_duplicate)
        menu.addAction("📄 Copy              Ctrl+C", self._on_copy)
        if self._clipboard:
            menu.addAction("📥 Paste             Ctrl+V", self._on_paste)
        menu.addSeparator()

        # Insert actions
        insert_menu = menu.addMenu("➕ Insert")
        insert_menu.addAction("⬆️ Insert Above", lambda: self._insert_action_at(idx))
        insert_menu.addAction("⬇️ Insert Below", lambda: self._insert_action_at(idx + 1))
        menu.addSeparator()

        # Move actions
        if idx > 0:
            menu.addAction("⬆️ Move Up        Ctrl+Shift+↑", self._on_move_up)
        if idx < len(self._actions) - 1:
            menu.addAction("⬇️ Move Down    Ctrl+Shift+↓", self._on_move_down)
        menu.addSeparator()

        # Delete
        menu.addAction("🗑️ Delete            Del", self._on_delete)

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

    def _on_asset_dropped_on_item(self, asset_id: str, item_index: int) -> None:
        """Handle asset dropped ON an existing action - update its asset_id."""
        if item_index < 0 or item_index >= len(self._actions):
            return

        action = self._actions[item_index]
        action_type = type(action).__name__

        # Only update actions that have asset_id
        if isinstance(action, WaitImage):
            updated = WaitImage(
                asset_id=asset_id,
                appear=action.appear,
                timeout_ms=action.timeout_ms,
                poll_ms=action.poll_ms,
                roi_override=action.roi_override,
            )
        elif isinstance(action, IfImage):
            updated = IfImage(
                asset_id=asset_id,
                then_actions=action.then_actions,
                else_actions=action.else_actions,
                roi_override=action.roi_override,
            )
        elif isinstance(action, WhileImage):
            updated = WhileImage(
                asset_id=asset_id,
                while_present=action.while_present,
                actions=action.actions,
            )
        else:
            # Action doesn't support asset_id - ignore drop
            logger.warning("Cannot set asset_id on action type: %s", action_type)
            return

        self._actions[item_index] = updated
        self._refresh_list()
        self.action_list.setCurrentRow(item_index)
        self.action_changed.emit()
        logger.info("Updated %s asset_id to: %s", action_type, asset_id)

    def _on_asset_dropped_insert(self, asset_id: str, insert_index: int) -> None:
        """Handle asset dropped BETWEEN actions - insert new WaitImage."""
        action = WaitImage(asset_id=asset_id)

        # Insert at specific position
        if insert_index >= len(self._actions):
            self._actions.append(action)
        else:
            self._actions.insert(insert_index, action)

        self._refresh_list()
        self.action_list.setCurrentRow(insert_index)
        self.action_changed.emit()
        logger.info("Created WaitImage at index %d with asset: %s", insert_index, asset_id)

    def insert_action_for_asset(self, asset_id: str, action_type: str) -> None:
        """Insert action for asset (called from Assets panel context menu)."""
        if action_type == "WaitImage":
            action = WaitImage(asset_id=asset_id)
        elif action_type == "IfImage":
            action = IfImage(asset_id=asset_id)
        else:
            return
        
        self._actions.append(action)
        self._refresh_list()
        self.action_list.setCurrentRow(len(self._actions) - 1)
        self.action_changed.emit()
        logger.info("Created %s for asset: %s", action_type, asset_id)

    def _on_duplicate(self) -> None:
        """Duplicate selected actions."""
        selected = self.action_list.selectedItems()
        if not selected:
            return

        # Get indices sorted
        rows = sorted([self.action_list.row(item) for item in selected])
        insert_pos = rows[-1] + 1

        for row in rows:
            if 0 <= row < len(self._actions):
                # Deep copy using model copy
                action_copy = self._actions[row].model_copy(deep=True)
                self._actions.insert(insert_pos, action_copy)
                insert_pos += 1

        self._refresh_list()
        self.action_changed.emit()
        logger.info("Duplicated %d actions", len(rows))

    def _on_copy(self) -> None:
        """Copy selected actions to clipboard."""
        selected = self.action_list.selectedItems()
        if not selected:
            return

        # Get actions by sorted indices
        rows = sorted([self.action_list.row(item) for item in selected])
        self._clipboard = [
            self._actions[row].model_copy(deep=True)
            for row in rows
            if 0 <= row < len(self._actions)
        ]
        logger.info("Copied %d actions to clipboard", len(self._clipboard))

    def _on_paste(self) -> None:
        """Paste clipboard actions after current selection."""
        if not self._clipboard:
            return

        # Get insert position (after current selection)
        current = self.action_list.currentRow()
        insert_pos = current + 1 if current >= 0 else len(self._actions)

        for action in self._clipboard:
            action_copy = action.model_copy(deep=True)
            self._actions.insert(insert_pos, action_copy)
            insert_pos += 1

        self._refresh_list()
        self.action_changed.emit()
        logger.info("Pasted %d actions", len(self._clipboard))

    def _insert_action_at(self, position: int) -> None:
        """Show add menu and insert action at specific position."""
        menu = QMenu(self)
        for action_type, label in ACTION_TYPES:
            action = menu.addAction(label)
            action.setData(action_type)
            action.triggered.connect(
                lambda checked, t=action_type, p=position: self._add_action_at(t, p)
            )
        # Show menu at current item position
        item = self.action_list.item(position if position < self.action_list.count() else position - 1)
        if item:
            rect = self.action_list.visualItemRect(item)
            global_pos = self.action_list.mapToGlobal(rect.bottomLeft())
            menu.exec(global_pos)

    def _add_action_at(self, action_type: str, position: int) -> None:
        """Add new action at specific position."""
        factory = ACTION_DEFAULTS.get(action_type)
        if factory:
            action = factory()
            if position >= len(self._actions):
                self._actions.append(action)
            else:
                self._actions.insert(position, action)
            self._refresh_list()
            self.action_list.setCurrentRow(position)
            self.action_changed.emit()
            logger.info("Added %s at position %d", action_type, position)

