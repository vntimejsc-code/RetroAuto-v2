"""
RetroAuto v2 - Coordinates Panel

Panel to capture and manage mouse coordinates.
Features:
- F4 to capture current mouse position
- Right-click context menu for click actions
- Multi-selection with Ctrl+A, Shift+Arrow, Delete
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from input.mouse import MouseController


@dataclass
class Coordinate:
    """A saved coordinate."""

    index: int
    x: int
    y: int


class CoordinatesPanel(QWidget):
    """
    Panel for capturing and managing mouse coordinates.

    Features:
    - F4: Capture current mouse position
    - Right-click: Send click or add to script
    - Ctrl+A: Select all
    - Shift+Up/Down: Extend selection
    - Delete: Remove selected

    Signals:
        coordinate_added: Emitted when coordinate is captured (x, y)
        add_to_script: Emitted to add click action to script (x, y, button, clicks)
    """

    coordinate_added = Signal(int, int)
    add_to_script = Signal(int, int, str, int)  # x, y, button, clicks

    def __init__(self, parent=None) -> None:  # type: ignore
        super().__init__(parent)
        self._coordinates: list[Coordinate] = []
        self._next_index = 1
        self._mouse = MouseController()
        self._init_ui()
        self._setup_shortcuts()

    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Group box
        group = QGroupBox("📍 Coordinates (F4)")
        group_layout = QVBoxLayout(group)

        # List widget matching Actions panel style
        self.coord_list = QListWidget()
        self.coord_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.coord_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.coord_list.customContextMenuRequested.connect(self._show_context_menu)
        self.coord_list.setStyleSheet(
            """
            QListWidget {
                background-color: #2B2B2B;
                border: 2px inset #808080;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 9pt;
                color: #E0E0E0;
            }
            QListWidget::item {
                padding: 2px 4px;
                border-bottom: 1px solid #3C3C3C;
            }
            QListWidget::item:selected {
                background-color: #264F78;
                color: #FFFFFF;
            }
            QListWidget::item:hover {
                background-color: #3C3C3C;
            }
        """
        )
        group_layout.addWidget(self.coord_list)

        # Buttons
        btn_layout = QHBoxLayout()

        self.capture_btn = QPushButton("📍 F4")
        self.capture_btn.setToolTip("Capture mouse position (F4)")
        self.capture_btn.clicked.connect(self._on_capture)
        btn_layout.addWidget(self.capture_btn)

        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setToolTip("Delete selected (Del)")
        self.delete_btn.clicked.connect(self._on_delete_selected)
        btn_layout.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._on_clear_all)
        btn_layout.addWidget(self.clear_btn)

        group_layout.addLayout(btn_layout)

        # Current position label
        self.pos_label = QLabel("🖱️ (0, 0)")
        self.pos_label.setStyleSheet("color: #404040; font-size: 9pt;")
        group_layout.addWidget(self.pos_label)

        layout.addWidget(group)

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        # F4 to capture
        self.f4_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F4), self)
        self.f4_shortcut.activated.connect(self._on_capture)

        # Ctrl+Space to capture (alternative)
        self.ctrl_space_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        self.ctrl_space_shortcut.activated.connect(self._on_capture)

        # Delete key
        self.del_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.coord_list)
        self.del_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.del_shortcut.activated.connect(self._on_delete_selected)

        # Ctrl+A to select all
        self.select_all_shortcut = QShortcut(QKeySequence.StandardKey.SelectAll, self.coord_list)
        self.select_all_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.select_all_shortcut.activated.connect(self.coord_list.selectAll)

    def _on_capture(self) -> None:
        """Capture current mouse position."""
        pos = QCursor.pos()
        x, y = pos.x(), pos.y()

        coord = Coordinate(index=self._next_index, x=x, y=y)
        self._coordinates.append(coord)
        self._next_index += 1

        # Add to list with color
        item = QListWidgetItem(f"#{coord.index:02d}  ({x:4d}, {y:4d})")
        item.setData(Qt.ItemDataRole.UserRole, coord)
        item.setBackground(QBrush(QColor("#FFFFEE")))
        self.coord_list.addItem(item)

        # Update label
        self.pos_label.setText(f"🖱️ ({x}, {y}) ✓")

        # Emit signal
        self.coordinate_added.emit(x, y)

    def _show_context_menu(self, pos: QPoint) -> None:
        """Show context menu for click actions."""
        selected = self.coord_list.selectedItems()
        if not selected:
            return

        count = len(selected)
        menu = QMenu(self)

        # Add to Script - works for multiple selected items
        label = f"📝 Add {count} to Script" if count > 1 else "📝 Add to Script"
        script_menu = menu.addMenu(label)

        add_left = script_menu.addAction("Left Click")
        add_left.triggered.connect(lambda: self._add_selected_to_script("left", 1))

        add_right = script_menu.addAction("Right Click")
        add_right.triggered.connect(lambda: self._add_selected_to_script("right", 1))

        add_double = script_menu.addAction("Double Click")
        add_double.triggered.connect(lambda: self._add_selected_to_script("left", 2))

        add_middle = script_menu.addAction("Middle Click")
        add_middle.triggered.connect(lambda: self._add_selected_to_script("middle", 1))

        menu.addSeparator()

        # Delete action
        delete_label = f"🗑️ Delete ({count})" if count > 1 else "🗑️ Delete"
        delete_action = menu.addAction(delete_label)
        delete_action.triggered.connect(self._on_delete_selected)

        menu.exec(self.coord_list.mapToGlobal(pos))

    def _add_selected_to_script(self, button: str, clicks: int) -> None:
        """Add all selected coordinates to script."""
        selected = self.coord_list.selectedItems()
        for item in selected:
            coord: Coordinate = item.data(Qt.ItemDataRole.UserRole)
            self.add_to_script.emit(coord.x, coord.y, button, clicks)

    def _add_to_script(self, item: QListWidgetItem, button: str, clicks: int) -> None:
        """Add click action to script."""
        coord: Coordinate = item.data(Qt.ItemDataRole.UserRole)
        self.add_to_script.emit(coord.x, coord.y, button, clicks)

    def _send_click(self, item: QListWidgetItem, button: str) -> None:
        """Send a click to the coordinate."""
        coord: Coordinate = item.data(Qt.ItemDataRole.UserRole)

        if button == "left":
            self._mouse.click(coord.x, coord.y, "left", 1)
        elif button == "right":
            self._mouse.click(coord.x, coord.y, "right", 1)
        elif button == "double":
            self._mouse.click(coord.x, coord.y, "left", 2)
        elif button == "middle":
            self._mouse.click(coord.x, coord.y, "middle", 1)

    def _on_delete_selected(self) -> None:
        """Delete selected coordinates."""
        selected = self.coord_list.selectedItems()
        for item in selected:
            coord: Coordinate = item.data(Qt.ItemDataRole.UserRole)
            if coord in self._coordinates:
                self._coordinates.remove(coord)
            row = self.coord_list.row(item)
            self.coord_list.takeItem(row)

    def _on_clear_all(self) -> None:
        """Clear all coordinates."""
        self._coordinates.clear()
        self.coord_list.clear()
        self._next_index = 1

    def get_coordinates(self) -> list[tuple[int, int]]:
        """Get all coordinates as (x, y) tuples."""
        return [(c.x, c.y) for c in self._coordinates]

    def update_mouse_position(self) -> None:
        """Update the current mouse position label."""
        pos = QCursor.pos()
        self.pos_label.setText(f"🖱️ ({pos.x()}, {pos.y()})")
