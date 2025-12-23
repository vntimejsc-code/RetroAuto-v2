"""
RetroAuto v2 - Interrupts Panel

Manage global interrupt rules that trigger on specific image events OR hotkeys.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.models import InterruptRule
from infra import get_logger

logger = get_logger("InterruptsPanel")


class InterruptsPanel(QWidget):
    """
    Panel for managing global interrupt rules.
    Supports both Image triggers and Hotkey triggers.
    """

    rule_selected = Signal(dict)  # Emits {"index": int, "rule": InterruptRule}
    rule_changed = Signal(list)  # Emits updated list of rules

    def __init__(self, rules: list[InterruptRule] = None) -> None:
        super().__init__()
        self._rules = rules or []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QLabel("⚡ GLOBAL INTERRUPTS")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-weight: bold; color: #ff5555; padding: 5px;")
        layout.addWidget(header)

        # List
        self.rule_list = QListWidget()
        self.rule_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.rule_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.rule_list.itemClicked.connect(self._on_item_clicked)
        self.rule_list.model().rowsMoved.connect(self._on_reorder)  # type: ignore
        layout.addWidget(self.rule_list)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Add Rule")
        self.btn_add.clicked.connect(self._add_rule)
        self.btn_remove = QPushButton("🗑️ Remove")
        self.btn_remove.clicked.connect(self._remove_rule)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        layout.addLayout(btn_layout)

        self._refresh_list()

    def set_rules(self, rules: list[InterruptRule]) -> None:
        """Update rules list."""
        self._rules = rules
        self._refresh_list()

    def _refresh_list(self) -> None:
        """Refresh logic."""
        self.rule_list.clear()
        for i, rule in enumerate(self._rules):
            item = QListWidgetItem(self._get_rule_label(rule))
            self.rule_list.addItem(item)

    def _get_rule_label(self, rule: InterruptRule) -> str:
        """Format rule display for both Image and Hotkey triggers."""
        # Determine trigger display
        if rule.trigger_type == "hotkey" and rule.when_hotkey:
            trigger = f"⌨️ {rule.when_hotkey.upper()}"
        else:
            trigger = f"🖼️ '{rule.when_image or '?'}'"

        # Determine action display
        action = (
            f"Run Flow: {rule.run_flow}" if rule.run_flow else f"{len(rule.do_actions)} Actions"
        )
        return f"[P{rule.priority}] WHEN {trigger} → {action}"

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        row = self.rule_list.row(item)
        if 0 <= row < len(self._rules):
            self.rule_selected.emit({"index": row, "rule": self._rules[row]})

    def _add_rule(self) -> None:
        new_rule = InterruptRule(when_image="", priority=10)
        self._rules.append(new_rule)
        self._refresh_list()
        self.rule_changed.emit(self._rules)
        # Select new item
        self.rule_list.setCurrentRow(len(self._rules) - 1)
        self.rule_selected.emit({"index": len(self._rules) - 1, "rule": new_rule})

    def _remove_rule(self) -> None:
        row = self.rule_list.currentRow()
        if row >= 0:
            self._rules.pop(row)
            self._refresh_list()
            self.rule_changed.emit(self._rules)

    def _on_reorder(self) -> None:
        # Sync internal list with UI order if needed
        pass

    def update_rule(self, index: int, updated: InterruptRule) -> None:
        """Update a specific rule after editing."""
        if 0 <= index < len(self._rules):
            self._rules[index] = updated
            self._refresh_list()
            self.rule_changed.emit(self._rules)
