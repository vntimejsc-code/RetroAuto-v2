"""
RetroAuto v2 - Variable Watch

Live variable display and monitoring widget.
Part of RetroScript Phase 14 - Visual Editor Components.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


@dataclass
class WatchedVariable:
    """A variable being watched."""

    name: str
    value: Any
    type_name: str
    last_updated: datetime = field(default_factory=datetime.now)
    history: list[tuple[datetime, Any]] = field(default_factory=list)


class VariableWatch(QWidget):
    """Live variable display widget.

    Usage:
        watch = VariableWatch()
        watch.set_variable("$count", 42)
        watch.set_variable("$name", "Player1")
    """

    variable_edited = Signal(str, object)  # name, new_value

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._variables: dict[str, WatchedVariable] = {}
        self._max_history = 50

        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header
        header = QLabel("📊 Variables")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 4px;")
        layout.addWidget(header)

        # Search bar
        search_layout = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Filter variables...")
        self._search_input.textChanged.connect(self._filter_variables)
        search_layout.addWidget(self._search_input)

        clear_btn = QPushButton("Clear")
        clear_btn.setMaximumWidth(60)
        clear_btn.clicked.connect(self.clear)
        search_layout.addWidget(clear_btn)

        layout.addLayout(search_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Name", "Value", "Type"])

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        layout.addWidget(self._table)

        # Style
        self.setStyleSheet(
            """
            QTableWidget {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                background: #1e1e1e;
                gridline-color: #3c3c3c;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
            QTableWidget::item:selected {
                background: #264f78;
            }
            QHeaderView::section {
                background: #2d2d2d;
                border: none;
                padding: 6px;
            }
            QLineEdit {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 4px 8px;
                background: #2d2d2d;
            }
            QPushButton {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 4px 8px;
                background: #2d2d2d;
            }
            QPushButton:hover {
                background: #404040;
            }
        """
        )

    def _setup_timer(self) -> None:
        """Setup refresh timer."""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_display)
        self._timer.start(100)  # 10 FPS

    def set_variable(self, name: str, value: Any) -> None:
        """Set or update a variable."""
        type_name = type(value).__name__ if value is not None else "null"

        if name in self._variables:
            var = self._variables[name]
            # Record history
            var.history.append((var.last_updated, var.value))
            if len(var.history) > self._max_history:
                var.history.pop(0)
            # Update
            var.value = value
            var.type_name = type_name
            var.last_updated = datetime.now()
        else:
            self._variables[name] = WatchedVariable(
                name=name,
                value=value,
                type_name=type_name,
            )

        self._refresh_display()

    def set_variables(self, variables: dict[str, Any]) -> None:
        """Set multiple variables at once."""
        for name, value in variables.items():
            self.set_variable(name, value)

    def get_variable(self, name: str) -> Any:
        """Get a variable value."""
        if name in self._variables:
            return self._variables[name].value
        return None

    def remove_variable(self, name: str) -> None:
        """Remove a variable."""
        if name in self._variables:
            del self._variables[name]
            self._refresh_display()

    def clear(self) -> None:
        """Clear all variables."""
        self._variables.clear()
        self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the table display."""
        filter_text = self._search_input.text().lower()

        # Filter variables
        filtered = [
            var
            for var in self._variables.values()
            if not filter_text or filter_text in var.name.lower()
        ]

        # Update table
        self._table.setRowCount(len(filtered))

        for row, var in enumerate(sorted(filtered, key=lambda v: v.name)):
            # Name
            name_item = QTableWidgetItem(var.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setForeground(QColor("#9cdcfe"))  # Variable color
            self._table.setItem(row, 0, name_item)

            # Value
            value_str = self._format_value(var.value)
            value_item = QTableWidgetItem(value_str)
            value_item.setData(Qt.ItemDataRole.UserRole, var.name)

            # Color based on type
            if var.type_name == "str":
                value_item.setForeground(QColor("#ce9178"))
            elif var.type_name in ("int", "float"):
                value_item.setForeground(QColor("#b5cea8"))
            elif var.type_name == "bool":
                value_item.setForeground(QColor("#569cd6"))
            elif var.type_name == "null":
                value_item.setForeground(QColor("#808080"))

            self._table.setItem(row, 1, value_item)

            # Type
            type_item = QTableWidgetItem(var.type_name)
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            type_item.setForeground(QColor("#4ec9b0"))
            self._table.setItem(row, 2, type_item)

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if value is None:
            return "null"
        if isinstance(value, str):
            if len(value) > 50:
                return f'"{value[:50]}..."'
            return f'"{value}"'
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, (list, tuple)):
            if len(value) > 5:
                return f"[{len(value)} items]"
            return str(value)
        if isinstance(value, dict):
            return f"{{{len(value)} keys}}"
        return str(value)

    def _filter_variables(self, text: str) -> None:
        """Filter displayed variables."""
        self._refresh_display()

    def _on_cell_double_clicked(self, row: int, col: int) -> None:
        """Handle double-click to edit value."""
        if col == 1:  # Value column
            item = self._table.item(row, col)
            if item:
                item.data(Qt.ItemDataRole.UserRole)
                # Enable editing
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self._table.editItem(item)

    def get_history(self, name: str) -> list[tuple[datetime, Any]]:
        """Get value history for a variable."""
        if name in self._variables:
            return self._variables[name].history.copy()
        return []


class VariableWatchDock(QWidget):
    """Dockable variable watch widget with refresh controls.

    Usage:
        dock = VariableWatchDock()
        dock.watch.set_variable("$x", 100)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Controls
        controls = QHBoxLayout()

        self._auto_refresh = QPushButton("⟳ Auto")
        self._auto_refresh.setCheckable(True)
        self._auto_refresh.setChecked(True)
        self._auto_refresh.clicked.connect(self._toggle_auto_refresh)
        controls.addWidget(self._auto_refresh)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._on_refresh)
        controls.addWidget(refresh_btn)

        controls.addStretch()

        layout.addLayout(controls)

        # Watch widget
        self.watch = VariableWatch()
        layout.addWidget(self.watch)

        # External source
        self._source_callback: Callable[[], dict[str, Any]] | None = None

    def set_source(self, callback: Callable[[], dict[str, Any]]) -> None:
        """Set the source for variable data.

        Args:
            callback: Function that returns dict of variables
        """
        self._source_callback = callback

    def _toggle_auto_refresh(self) -> None:
        """Toggle auto-refresh."""
        if self._auto_refresh.isChecked():
            self.watch._timer.start(100)
        else:
            self.watch._timer.stop()

    def _on_refresh(self) -> None:
        """Manual refresh from source."""
        if self._source_callback:
            variables = self._source_callback()
            self.watch.set_variables(variables)
