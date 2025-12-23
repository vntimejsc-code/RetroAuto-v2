"""
RetroAuto v2 - Structure Panel (The Navigator)

Displays the outline of the script structure (Flows, Labels) for quick navigation.
"""

from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class StructurePanel(QWidget):
    """
    Panel showing script structure (Outline).
    """

    # Signal: Line number to scroll to (1-based)
    navigate_requested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter structure...")
        self.search_box.textChanged.connect(self._filter_items)
        layout.addWidget(self.search_box)

        # Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        # Style
        self.tree.setStyleSheet(
            """
            QTreeWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
            }
            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
            }
        """
        )

        layout.addWidget(self.tree)

    def refresh(self, code: str) -> None:
        """Parse code and update tree."""
        self.tree.clear()

        # Regex for structure items
        # @flow name:
        # #label

        lines = code.splitlines()

        root_flow = QTreeWidgetItem(self.tree)
        root_flow.setText(0, "Flows")
        root_flow.setExpanded(True)
        # Icon?

        current_flow_item = None

        for i, line in enumerate(lines):
            line = line.strip()
            line_num = i + 1

            if line.startswith("@"):
                # Flow definition: @flow_name:
                match = re.match(r"@(\w+):?", line)
                if match:
                    name = match.group(1)
                    item = QTreeWidgetItem(root_flow)
                    item.setText(0, f"@{name}")
                    item.setData(0, Qt.ItemDataRole.UserRole, line_num)
                    # item.setIcon(0, QIcon("...")) # TODO: Add icons
                    current_flow_item = item
                    root_flow.addChild(item)

            elif line.startswith("#"):
                # Label: #label_name
                # Attach to current flow or root if no flow
                parent = current_flow_item or root_flow
                item = QTreeWidgetItem(parent)
                item.setText(0, line)  # Keep the #
                item.setData(0, Qt.ItemDataRole.UserRole, line_num)
                # Indent labels visually strictly or just tree hierarchy?
                # Tree hierarchy is good.

        # If we have assets, maybe list them too?
        # For now, just flows and labels as requested.

    def _filter_items(self, text: str) -> None:
        """Filter tree items."""
        # TODO: Implement filtering logic
        pass

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle navigation."""
        line_num = item.data(0, Qt.ItemDataRole.UserRole)
        if line_num:
            self.navigate_requested.emit(line_num)
