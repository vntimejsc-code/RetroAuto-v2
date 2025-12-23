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
    QLineEdit,
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
    ClickUntil,
    ClickRandom,
    ROI,
    Delay,
    DelayRandom,
    Drag,
    Else,
    EndIf,
    EndLoop,
    EndWhile,
    Goto,
    Hotkey,
    IfImage,
    IfPixel,
    IfText,
    Label,
    Loop,
    PixelColor,
    ReadText,
    RunFlow,
    Scroll,
    TypeText,
    WaitImage,
    WaitPixel,
    WhileImage,
    Notify,
)
from infra import get_logger

logger = get_logger("ActionsPanel")

# Categorized action types for better discoverability
ACTION_CATEGORIES = {
    "🎯 Clicks & Mouse": [
        ("ClickImage", "🎯 Click Image"),
        ("ClickUntil", "🔄 Click Until"),
        ("ClickRandom", "🎲 Click Random"),
        ("Click", "🖱️ Click"),
        ("Drag", "↔️ Drag"),
        ("Scroll", "📜 Scroll"),
    ],
    "👁️ Vision & Wait": [
        ("WaitImage", "👁️ Wait Image"),
        ("IfImage", "❓ If Image"),
        ("WhileImage", "🔄 While Image"),
        ("WaitPixel", "🎨 Wait Pixel"),
        ("IfPixel", "🎯 If Pixel"),
        ("ReadText", "🧠 Read Text"),
    ],
    "⌨️ Keyboard & Input": [
        ("Hotkey", "⌨️ Hotkey"),
        ("TypeText", "📝 Type Text"),
    ],
    "⏱️ Timing & Delays": [
        ("Delay", "⏱️ Delay"),
        ("DelayRandom", "🎲 Random Delay"),
    ],
    "🔄 Flow Control": [
        ("IfText", "📝 If Text"),
        ("Loop", "🔁 Loop"),
        ("Label", "🏷️ Label"),
        ("Goto", "↩️ Goto"),
        ("RunFlow", "▶️ Run Flow"),
    ],
    "📡 Remote & Notify": [
        ("Notify", "📢 Notify"),
    ],
    "📐 Structure Markers": [
        ("Else", "↩️ Else"),
        ("EndIf", "🔚 EndIf"),
        ("EndLoop", "🔚 EndLoop"),
        ("EndWhile", "🔚 EndWhile"),
    ],
}

# Smart templates for common patterns
ACTION_TEMPLATES = {
    "🎯 Wait & Click": [
        ("WaitImage", {"asset_id": "[target]", "appear": True}),
        ("ClickImage", {"asset_id": "[target]"}),
    ],
    "🔄 Loop Until Found": [
        ("Loop", {"iterations": 100}),
        ("WaitImage", {"asset_id": "[target]", "timeout_ms": 500}),
        ("ClickImage", {"asset_id": "[target]"}),
        ("EndLoop", {}),
    ],
    "❓ Check & React": [
        ("IfImage", {"asset_id": "[condition]"}),
        ("ClickImage", {"asset_id": "[action_true]"}),
        ("Else", {}),
        ("ClickImage", {"asset_id": "[action_false]"}),
        ("EndIf", {}),
    ],
    "📝 Read & Check Value": [
        ("ReadText", {"variable_name": "$value", "roi": {"x": 0, "y": 0, "w": 100, "h": 30}}),
        ("IfText", {"variable_name": "$value", "operator": "numeric_lt", "value": "50"}),
        ("ClickImage", {"asset_id": "[action]"}),
        ("EndIf", {}),
    ],
    "⏱️ Timed Sequence": [
        ("ClickImage", {"asset_id": "[step1]"}),
        ("Delay", {"ms": 1000}),
        ("ClickImage", {"asset_id": "[step2]"}),
        ("Delay", {"ms": 1000}),
        ("ClickImage", {"asset_id": "[step3]"}),
    ],
    "🎮 Farming Loop": [
        ("Loop", {"iterations": 999}),
        ("WaitImage", {"asset_id": "[enemy]", "timeout_ms": 5000}),
        ("ClickImage", {"asset_id": "[attack]"}),
        ("Delay", {"ms": 3000}),
        ("EndLoop", {}),
    ],
    "💊 Auto Heal": [
        ("ReadText", {"variable_name": "$hp", "roi": {"x": 10, "y": 10, "w": 100, "h": 30}}),
        ("IfText", {"variable_name": "$hp", "operator": "numeric_lt", "value": "30"}),
        ("ClickImage", {"asset_id": "[potion]"}),
        ("Delay", {"ms": 500}),
        ("EndIf", {}),
    ],
    "⚔️ Skill Combo": [
        ("ClickImage", {"asset_id": "[skill1]"}),
        ("Delay", {"ms": 500}),
        ("ClickImage", {"asset_id": "[skill2]"}),
        ("Delay", {"ms": 500}),
        ("ClickImage", {"asset_id": "[skill3]"}),
        ("Delay", {"ms": 500}),
    ],
}

# Build flattened lookup for backward compatibility
ACTION_TYPES = []
for category_name, actions in ACTION_CATEGORIES.items():
    ACTION_TYPES.extend(actions)

# Action factory functions
ACTION_DEFAULTS = {
    "ClickImage": lambda: ClickImage(asset_id=""),
    "ClickUntil": lambda: ClickUntil(click_asset_id="", until_asset_id=""),
    "WaitImage": lambda: WaitImage(asset_id=""),
    "WaitPixel": lambda: WaitPixel(x=0, y=0, color=PixelColor(r=255, g=0, b=0)),
    "Click": lambda: Click(),
    "IfImage": lambda: IfImage(asset_id=""),
    "IfText": lambda: IfText(variable_name="$var", value="0"),
    "Else": lambda: Else(),
    "EndIf": lambda: EndIf(),
    "Loop": lambda: Loop(),
    "EndLoop": lambda: EndLoop(),
    "WhileImage": lambda: WhileImage(asset_id=""),
    "EndWhile": lambda: EndWhile(),
    "IfPixel": lambda: IfPixel(x=0, y=0, color=PixelColor(r=255, g=0, b=0)),
    "Hotkey": lambda: Hotkey(keys=[]),
    "TypeText": lambda: TypeText(text=""),
    "Label": lambda: Label(name=""),
    "Goto": lambda: Goto(label=""),
    "RunFlow": lambda: RunFlow(flow_name=""),
    "Delay": lambda: Delay(ms=1000),
    "DelayRandom": lambda: DelayRandom(),
    "ReadText": lambda: ReadText(variable_name="$var", roi=ROI(x=0, y=0, w=100, h=30)),
    "Drag": lambda: Drag(from_x=0, from_y=0, to_x=100, to_y=100),
    "Scroll": lambda: Scroll(),
    "ClickRandom": lambda: ClickRandom(roi=ROI(x=0, y=0, w=100, h=100)),
    "Notify": lambda: Notify(message="Notification"),
}

# Color scheme by action category
ACTION_COLORS = {
    "click": QColor("#4CAF50"),      # Green - click actions
    "wait": QColor("#2196F3"),       # Blue - wait/check actions
    "control": QColor("#FF9800"),    # Orange - control flow
    "input": QColor("#9C27B0"),      # Purple - input actions
    "timing": QColor("#607D8B"),     # Gray-blue - timing
    "marker": QColor("#888888"),     # Gray - block markers
}

ACTION_CATEGORY = {
    "ClickImage": "click", "Click": "click", "ClickUntil": "click",
    "WaitImage": "wait", "WaitPixel": "wait",
    "IfImage": "control", "Else": "control", "EndIf": "marker", "IfText": "control",
    "Loop": "control", "EndLoop": "marker",
    "WhileImage": "control", "EndWhile": "marker",
    "Goto": "control", "Label": "control", "RunFlow": "control",
    "Hotkey": "input", "TypeText": "input", "ReadText": "input",
    "Delay": "timing", "DelayRandom": "timing",
    "IfPixel": "control", "Drag": "click", "Scroll": "click",
}


class ActionItemDelegate(QStyledItemDelegate):
    """Custom delegate to draw tree lines and expand indicators."""

    def __init__(self, parent=None):  # type: ignore
        super().__init__(parent)
        self.line_color = QColor("#555555")
        self.indent_width = 20

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:  # type: ignore
        """Draw item with visual tree lines."""
        painter.save()

        # Get item data
        depth = index.data(257) or 0  # Qt.UserRole + 1
        is_block_start = index.data(258) or False  # Qt.UserRole + 2
        category = index.data(259) or "timing"  # Qt.UserRole + 3
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""

        # Draw selection background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            text_color = option.palette.highlightedText().color()
        else:
            text_color = ACTION_COLORS.get(category, QColor("#CCCCCC"))

        # Calculate tree line area
        tree_width = depth * self.indent_width
        text_x = option.rect.x() + tree_width + 4
        y_center = option.rect.y() + option.rect.height() // 2

        # Draw tree lines
        pen = QPen(self.line_color, 1)
        painter.setPen(pen)

        for i in range(depth):
            x = option.rect.x() + (i * self.indent_width) + self.indent_width // 2
            # Vertical line
            painter.drawLine(x, option.rect.y(), x, option.rect.y() + option.rect.height())
            # Horizontal connector for last level
            if i == depth - 1:
                painter.drawLine(x, y_center, x + self.indent_width // 2, y_center)

        # Draw expand indicator for block starters
        if is_block_start:
            indicator = "▾ "
            painter.setPen(QColor("#888888"))
            painter.drawText(text_x, option.rect.y(), 20, option.rect.height(),
                           Qt.AlignmentFlag.AlignVCenter, indicator)
            text_x += 14

        # Draw text
        painter.setPen(text_color)
        text_rect = option.rect.adjusted(text_x - option.rect.x(), 0, 0, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, text)

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index) -> "QSize":  # type: ignore
        """Return size with space for tree lines."""
        from PySide6.QtCore import QSize
        size = super().sizeHint(option, index)
        depth = index.data(257) or 0
        return QSize(size.width() + depth * self.indent_width, max(size.height(), 22))


# Custom MIME type for asset drag
ASSET_MIME_TYPE = "application/x-retroauto-asset"


class ActionListWidget(QListWidget):
    """
    Custom list widget with external drop support from Assets panel.
    - Drop ON an item: update that action's asset_id (if applicable)
    - Drop BETWEEN items: shows blue indicator line (insert position)
    """

    asset_dropped_on_item = Signal(str, int)  # asset_id, item_index (update existing)
    asset_dropped_insert = Signal(str, int, str)  # asset_id, insert_index, action_type (create new)
    about_to_reorder = Signal()  # Before internal move
    reordered = Signal()  # After internal move

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
        """Handle drop from Assets panel - show action chooser menu."""
        mime = event.mimeData()
        if mime.hasFormat(ASSET_MIME_TYPE):
            asset_id = mime.data(ASSET_MIME_TYPE).data().decode("utf-8")

            if self._drop_on_item_index >= 0:
                # Update existing action
                self.asset_dropped_on_item.emit(asset_id, self._drop_on_item_index)
            else:
                # Insert new action - show menu to choose type
                insert_index = self._drop_indicator_index
                if insert_index < 0:
                    insert_index = self.count()
                
                # Show menu to choose action type
                from PySide6.QtWidgets import QMenu
                from PySide6.QtGui import QCursor
                
                menu = QMenu(self)
                menu.setStyleSheet("QMenu { font-size: 12px; }")
                
                # Image-related actions
                actions_list = [
                    ("👁️ Wait Image", "WaitImage"),
                    ("🎯 Click Image", "ClickImage"),
                    ("❓ If Image", "IfImage"),
                    ("🔄 While Image", "WhileImage"),
                ]
                
                for label, action_type in actions_list:
                    action = menu.addAction(label)
                    action.triggered.connect(
                        lambda checked=False, aid=asset_id, idx=insert_index, at=action_type:
                            self.asset_dropped_insert.emit(aid, idx, at)
                    )
                
                # Show menu at cursor
                menu.exec(QCursor.pos())

            self._drop_indicator_index = -1
            self._drop_on_item_index = -1
            self.viewport().update()
            event.acceptProposedAction()
        else:
            # Internal move
            self.about_to_reorder.emit()
            self._drop_indicator_index = -1
            self._drop_on_item_index = -1
            super().dropEvent(event)
            self.reordered.emit()

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
        self._undo_stack: list[list[Action]] = []  # Undo history
        self._redo_stack: list[list[Action]] = []  # Redo history
        self._max_undo = 50  # Max undo steps
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Group box
        group = QGroupBox("Actions")
        group_layout = QVBoxLayout(group)

        # Quick Add Bar - 1-click common actions
        quick_bar = QHBoxLayout()
        quick_bar.setSpacing(2)

        # Common action quick buttons
        quick_actions = [
            ("🎯", "ClickImage", "Click Image"),
            ("🖱️", "Click", "Click"),
            ("👁️", "WaitImage", "Wait Image"),
            ("👻", "WaitGone", "Wait Gone"),
            ("⏱️", "Delay", "Delay"),
            ("🔁", "Loop", "Loop"),
        ]

        for icon, action_type, tooltip in quick_actions:
            btn = QPushButton(icon)
            btn.setFixedSize(28, 24)
            btn.setToolTip(f"Add {tooltip}")
            btn.clicked.connect(lambda checked, t=action_type: self._quick_add(t))
            quick_bar.addWidget(btn)

        quick_bar.addStretch()

        # Search input (filter actions)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Filter...")
        self.search_input.setFixedWidth(100)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_changed)
        quick_bar.addWidget(self.search_input)

        # More menu button
        self.btn_more = QPushButton("+ More")
        self.btn_more.clicked.connect(self._show_add_menu)
        quick_bar.addWidget(self.btn_more)

        group_layout.addLayout(quick_bar)

        # Action list with extended selection and drop support
        self.action_list = ActionListWidget(self)
        self.action_list.setItemDelegate(ActionItemDelegate(self.action_list))
        self.action_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.action_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.action_list.currentItemChanged.connect(self._on_selection_changed)
        self.action_list.itemDoubleClicked.connect(self._on_double_click)
        self.action_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.action_list.customContextMenuRequested.connect(self._show_context_menu)
        self.action_list.asset_dropped_on_item.connect(self._on_asset_dropped_on_item)
        self.action_list.asset_dropped_insert.connect(self._on_asset_drop_insert)
        self.action_list.about_to_reorder.connect(self._save_state)
        self.action_list.reordered.connect(self._sync_actions_order)
        group_layout.addWidget(self.action_list)

        # Bottom buttons (Add, Delete, Clear, Move)
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("+ Add")
        self.btn_add.clicked.connect(self._show_add_menu)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_delete.setEnabled(False)

        self.btn_clear = QPushButton("Clear")
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

        # Ctrl+Z to undo
        self.undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self.action_list)
        self.undo_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.undo_shortcut.activated.connect(self._on_undo)

        # Ctrl+Y to redo
        self.redo_shortcut = QShortcut(QKeySequence.StandardKey.Redo, self.action_list)
        self.redo_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.redo_shortcut.activated.connect(self._on_redo)

        # Space to test current step
        self.test_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self.action_list)
        self.test_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.test_shortcut.activated.connect(self._on_test_step)

    def load_actions(self, actions: list[Action]) -> None:
        """Load actions from script flow."""
        self._actions = list(actions)
        self._refresh_list()

    def get_actions(self) -> list[Action]:
        """Get current actions list."""
        return list(self._actions)

    def _refresh_list(self) -> None:
        """Refresh list widget from internal actions with visual indentation and colors."""
        # SAVE current state to restore after refresh
        current_row = self.action_list.currentRow()
        scroll_value = self.action_list.verticalScrollBar().value()
        
        self.action_list.clear()

        # Track block depth for indentation (supports nested blocks)
        block_depth = 0

        for i, action in enumerate(self._actions):
            action_type = type(action).__name__
            label = next(
                (label_text for t, label_text in ACTION_TYPES if t == action_type), action_type
            )

            # Add details to label
            detail = self._get_action_detail(action)
            if detail:
                label = f"{label}: {detail}"

            # Determine depth and flags for this item
            is_block_start = action_type in ("IfImage", "Loop", "WhileImage")
            item_depth = block_depth

            # Block openers increase depth AFTER this item
            if is_block_start:
                block_depth += 1

            # Block closers decrease depth BEFORE this item
            elif action_type in ("EndIf", "EndLoop", "EndWhile"):
                block_depth = max(0, block_depth - 1)
                item_depth = block_depth

            # Get category for color
            category = ACTION_CATEGORY.get(action_type, "timing")

            # Create item with data roles for delegate
            item = QListWidgetItem(label)
            item.setData(256, i)         # Qt.UserRole - index
            item.setData(257, item_depth)  # Qt.UserRole + 1 - depth
            item.setData(258, is_block_start)  # Qt.UserRole + 2 - is_block_start
            item.setData(259, category)   # Qt.UserRole + 3 - category

            self.action_list.addItem(item)
        
        # RESTORE scroll position and selection
        self.action_list.verticalScrollBar().setValue(scroll_value)
        if current_row >= 0 and current_row < self.action_list.count():
            self.action_list.setCurrentRow(current_row)

    def _get_action_detail(self, action: Action) -> str:
        """Get short detail string for action."""
        if isinstance(action, ClickImage):
            return action.asset_id or "?"
        elif isinstance(action, ClickUntil):
            click = action.click_asset_id or "?"
            until = action.until_asset_id or "?"
            return f"{click} → {until}"
        elif isinstance(action, ClickRandom):
            r = action.roi
            return f"ROI({r.x},{r.y}, {r.w}x{r.h})"
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
        elif isinstance(action, ReadText):
            return f"{action.variable_name} = OCR"
        elif isinstance(action, IfText):
            return f"if {action.variable_name} {action.operator} {action.value}"
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
        """Show categorized add action menu with templates."""
        menu = QMenu(self)
        
        # Add Templates submenu first (most common use case)
        templates_menu = menu.addMenu("✨ Templates")
        for template_name in ACTION_TEMPLATES.keys():
            action = templates_menu.addAction(template_name)
            action.triggered.connect(lambda checked=False, t=template_name: self._add_template(t))
        
        menu.addSeparator()
        
        # Add categorized actions
        for category_name, actions in ACTION_CATEGORIES.items():
            category_menu = menu.addMenu(category_name)
            for action_type, label in actions:
                action = category_menu.addAction(label)
                action.triggered.connect(
                    lambda checked=False, t=action_type: self._add_action_type(t)
                )
        
        menu.exec(self.btn_more.mapToGlobal(self.btn_more.rect().bottomLeft()))

    def _add_action(self, action_type: str) -> None:
        """Add a new action of given type."""
        factory = ACTION_DEFAULTS.get(action_type)
        if factory:
            self._save_state()  # Save for undo
            action = factory()
            self._actions.append(action)
            self._refresh_list()

            # Select the new action
            self.action_list.setCurrentRow(len(self._actions) - 1)
            self.action_changed.emit()
            logger.info("Added action: %s", action_type)
    
    def _add_template(self, template_name: str) -> None:
        """Add a template (multiple actions at once) with smart insertion."""
        template = ACTION_TEMPLATES.get(template_name)
        if not template:
            return
        
        self._save_state()
        
        # Smart insertion: insert at current position
        current_row = self.action_list.currentRow()
        if current_row < 0:
            insert_pos = len(self._actions)
        else:
            insert_pos = current_row + 1
        
        # Add all actions from template
        for i, (action_type, params) in enumerate(template):
            action = ACTION_DEFAULTS[action_type]()
            for key, value in params.items():
                if hasattr(action, key):
                    setattr(action, key, value)
            self._actions.insert(insert_pos + i, action)
        
        self._refresh_list()
        
        # Auto-select all inserted actions
        self.action_list.clearSelection()
        for i in range(len(template)):
            item = self.action_list.item(insert_pos + i)
            if item:
                item.setSelected(True)
        
        # Scroll to show first inserted action
        self.action_list.setCurrentRow(insert_pos)
        self.action_list.scrollToItem(self.action_list.item(insert_pos))
        
        self.action_changed.emit()
        logger.info(f"Added template: {template_name} ({len(template)} actions) at position {insert_pos}")
    
    def _add_template(self, template_name: str) -> None:
        """Add a template (multiple actions at once)."""
        template = ACTION_TEMPLATES.get(template_name)
        if not template:
            return
        
        self._save_state()  # Save for undo
        
        # Get insertion index (append at end)
        insert_pos = len(self._actions)
        
        # Add all actions from template
        for action_type, params in template:
            # Create action with default
            action = ACTION_DEFAULTS[action_type]()
            
            # Apply template parameters
            for key, value in params.items():
                if hasattr(action, key):
                    setattr(action, key, value)
            
            self._actions.append(action)
        
        self._refresh_list()
        # Select first action of template
        self.action_list.setCurrentRow(insert_pos)
        self.action_changed.emit()
        
        logger.info(f"Added template: {template_name} ({len(template)} actions)")
    
    def _add_action_type(self, action_type: str) -> None:
        """Add action from categorized menu (alias for _add_action)."""
        self._add_action(action_type)

    def _quick_add(self, action_type: str) -> None:
        """Quick add action after current selection (1-click workflow)."""
        if action_type == "WaitGone":
             self._save_state()
             action = WaitImage(asset_id="", appear=False)
        else:
            factory = ACTION_DEFAULTS.get(action_type)
            if not factory:
                return

            self._save_state()  # Save for undo
            action = factory()

        # Insert after current selection, or at end
        current_row = self.action_list.currentRow()
        if current_row >= 0:
            insert_pos = current_row + 1
        else:
            insert_pos = len(self._actions)

        if insert_pos >= len(self._actions):
            self._actions.append(action)
        else:
            self._actions.insert(insert_pos, action)

        self._refresh_list()
        self.action_list.setCurrentRow(insert_pos)
        self.action_changed.emit()
        logger.info("Quick added: %s at position %d", action_type, insert_pos)

    def _on_delete(self) -> None:
        """Delete selected actions."""
        selected = self.action_list.selectedItems()
        if not selected:
            return

        self._save_state()  # Save for undo
        # Get indices in reverse order to delete from end
        rows = sorted([self.action_list.row(item) for item in selected], reverse=True)
        first_deleted_row = min(rows)  # Remember position for reselection
        
        for row in rows:
            if 0 <= row < len(self._actions):
                del self._actions[row]

        self._refresh_list()
        
        # Smart selection: select item at deleted position (or last if beyond end)
        if self.action_list.count() > 0:
            new_row = min(first_deleted_row, self.action_list.count() - 1)
            self.action_list.setCurrentRow(new_row)
            self.action_list.scrollToItem(self.action_list.item(new_row))
        
        self.action_changed.emit()
        logger.info("Deleted %d actions", len(rows))

    def _on_clear_all(self) -> None:
        """Clear all actions."""
        self._save_state()  # Save for undo
        self._actions.clear()
        self._refresh_list()
        self.action_changed.emit()
        logger.info("Cleared all actions")

    def _on_move_up(self) -> None:
        """Move selected action up."""
        row = self.action_list.currentRow()
        if row > 0:
            self._save_state()
            self._actions[row], self._actions[row - 1] = self._actions[row - 1], self._actions[row]
            self._refresh_list()
            self.action_list.setCurrentRow(row - 1)
            self.action_changed.emit()

    def _on_move_down(self) -> None:
        """Move selected action down."""
        row = self.action_list.currentRow()
        if row < len(self._actions) - 1:
            self._save_state()
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
            self._save_state()
            self._actions[idx] = action
            self._refresh_list()
            self.action_list.setCurrentRow(idx)
            logger.debug("Updated action %d", idx)

    def _on_asset_dropped_on_item(self, asset_id: str, item_index: int) -> None:
        """Handle asset dropped ON an existing action - update its asset_id."""
        if item_index < 0 or item_index >= len(self._actions):
            return

        self._save_state()
        action = self._actions[item_index]
        action_type = type(action).__name__

        # Only update actions that have asset_id
        if isinstance(action, ClickImage):
            updated = ClickImage(
                asset_id=asset_id,
                button=action.button,
                clicks=action.clicks,
                timeout_ms=action.timeout_ms,
                offset_x=action.offset_x,
                offset_y=action.offset_y,
            )
        elif isinstance(action, ClickUntil):
            # For ClickUntil, update the click_asset_id (primary target)
            updated = ClickUntil(
                click_asset_id=asset_id,
                until_asset_id=action.until_asset_id,
                until_appear=action.until_appear,
                button=action.button,
                click_interval_ms=action.click_interval_ms,
                timeout_ms=action.timeout_ms,
                max_clicks=action.max_clicks,
            )
        elif isinstance(action, WaitImage):
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

    def _on_asset_drop_insert(self, asset_id: str, insert_index: int, action_type: str) -> None:
        """Handle asset dropped BETWEEN actions - create chosen action type."""
        self._save_state()
        # Create appropriate action based on type
        if action_type == "WaitImage":
            action = WaitImage(asset_id=asset_id)
        elif action_type == "ClickImage":
            action = ClickImage(asset_id=asset_id)
        elif action_type == "IfImage":
            action = IfImage(asset_id=asset_id)
        elif action_type == "WhileImage":
            action = WhileImage(asset_id=asset_id)
        else:
            action = WaitImage(asset_id=asset_id)  # Fallback

        # Insert at specific position
        if insert_index >= len(self._actions):
            self._actions.append(action)
        else:
            self._actions.insert(insert_index, action)

        self._refresh_list()
        self.action_list.setCurrentRow(insert_index)
        self.action_changed.emit()
        logger.info(f"Created {action_type} at index {insert_index} with asset: {asset_id}")

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

        self._save_state()  # Save for undo
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

        self._save_state()  # Save for undo
        # Get insert position (after current selection)
        current = self.action_list.currentRow()
        insert_pos = current + 1 if current >= 0 else len(self._actions)

        for action in self._clipboard:
            action_copy = action.model_copy(deep=True)
            self._actions.insert(insert_pos, action_copy)
            insert_pos += 1
            self.action_changed.emit()
            logger.info("Pasted %d actions", len(self._clipboard))

    def _show_add_menu(self) -> None:
        """Show categorized add action menu with templates."""
        menu = QMenu(self)

        # Add Templates submenu first
        templates_menu = menu.addMenu("✨ Templates")
        for template_name in ACTION_TEMPLATES.keys():
            action = templates_menu.addAction(template_name)
            action.triggered.connect(lambda checked=False, t=template_name: self._add_template(t))

        menu.addSeparator()

        # Add categorized actions
        for category_name, actions in ACTION_CATEGORIES.items():
            category_menu = menu.addMenu(category_name)
            for action_type, label in actions:
                action = category_menu.addAction(label)
                action.triggered.connect(lambda checked=False, t=action_type: self._add_action(t))

        menu.exec(self.btn_more.mapToGlobal(self.btn_more.rect().bottomLeft()))

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
            self._save_state()  # Save for undo
            action = factory()
            if position >= len(self._actions):
                self._actions.append(action)
            else:
                self._actions.insert(position, action)
            self._refresh_list()
            self.action_list.setCurrentRow(position)
            self.action_changed.emit()
            logger.info("Added %s at position %d", action_type, position)

    def _save_state(self) -> None:
        """Save current state to undo stack."""
        # Deep copy all actions
        state = [action.model_copy(deep=True) for action in self._actions]
        self._undo_stack.append(state)
        # Limit stack size
        if len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)
        # Clear redo stack on new action
        self._redo_stack.clear()

    def _on_undo(self) -> None:
        """Undo last action."""
        if not self._undo_stack:
            logger.debug("Nothing to undo")
            return

        # Save current state to redo stack
        current = [action.model_copy(deep=True) for action in self._actions]
        self._redo_stack.append(current)

        # Restore previous state
        self._actions = self._undo_stack.pop()
        self._refresh_list()
        self.action_changed.emit()
        logger.info("Undo: restored to %d actions", len(self._actions))

    def _on_redo(self) -> None:
        """Redo last undone action."""
        if not self._redo_stack:
            logger.debug("Nothing to redo")
            return

        # Save current state to undo stack
        current = [action.model_copy(deep=True) for action in self._actions]
        self._undo_stack.append(current)

        # Restore next state
        self._actions = self._redo_stack.pop()
        self._refresh_list()
        self.action_changed.emit()
        logger.info("Redo: restored to %d actions", len(self._actions))

    def _on_test_step(self) -> None:
        """Test current step (Space key)."""
        row = self.action_list.currentRow()
        if row >= 0:
            self.run_step_requested.emit(row)
            logger.info("Test step: %d", row)

    def _on_search_changed(self, text: str) -> None:
        """Filter action list by search text."""
        search = text.lower().strip()
        for i in range(self.action_list.count()):
            item = self.action_list.item(i)
            if item:
                # Hide items that don't match search
                visible = not search or search in item.text().lower()
                item.setHidden(not visible)

    def _sync_actions_order(self) -> None:
        """
        Synchronize self._actions list with the visual order in QListWidget after a drag-drop reorder.
        This fixes the bug where drag-drop changed visuals but not the underlying data.
        """
        if self.action_list.count() != len(self._actions):
            logger.error("Sync error: Visua list count %d != Data list count %d", 
                         self.action_list.count(), len(self._actions))
            return # Should not happen unless state is corrupted

        # Create a mapping of original_index -> action
        # We need a copy because we'll be rebuilding self._actions
        # Note: We rely on the UserRole (256) which stores the index AT THE TIME OF LAST REFRESH
        
        # Snapshot of actions before reorder (we already saved state in about_to_reorder, 
        # but we need this reference for reconstruction)
        # However, self._actions HAS NOT CHANGED YET. The visual list HAS changed order.
        # But the UserRole data on items STILL points to the index in the CURRENT self._actions.
        
        new_actions_list = []
        
        for i in range(self.action_list.count()):
            item = self.action_list.item(i)
            original_idx = item.data(256)  # Qt.UserRole
            
            if original_idx is None or original_idx >= len(self._actions):
                logger.error("Sync error: Invalid original index %s", original_idx)
                # Fallback: Just keep original order to prevent data loss? 
                # Or try to continue? Better to abort sync if critical error.
                # But partial sync is bad.
                # For safety, we should probably stick to original list if mapping fails.
                return 

            new_actions_list.append(self._actions[original_idx])
            
        # Update the data model
        self._actions = new_actions_list
        
        # Refresh list to update indices for next time
        self._refresh_list()
        self.action_changed.emit()
        logger.info("Synced action order after drag-drop")

    def _on_double_click(self, item: QListWidgetItem) -> None:
        """Handle double-click for quick inline edit (opens properties panel)."""
        row = self.action_list.row(item)
        if 0 <= row < len(self._actions):
            action = self._actions[row]
            self.action_selected.emit({"index": row, "action": action})
            logger.info("Double-click edit: %s", type(action).__name__)
