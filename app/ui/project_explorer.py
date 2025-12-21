"""
RetroAuto v2 - Project Explorer

Win95-style file/folder tree for project navigation.
Features:
- Folder-based project structure
- Asset/Script/Flow icons
- Double-click to open
- Context menu for operations
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QInputDialog,
    QMenu,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ProjectExplorer(QWidget):
    """
    Project explorer panel with Win95 tree view.

    Signals:
        file_opened: Emitted when a file is double-clicked (path, type)
        file_created: Emitted when a new file is created (path, type)
        file_deleted: Emitted when a file is deleted (path)
    """

    file_opened = Signal(str, str)  # path, type (script, asset, flow)
    file_created = Signal(str, str)
    file_deleted = Signal(str)

    def __init__(self, parent=None) -> None:  # type: ignore
        super().__init__(parent)
        self._init_ui()
        self._project_path: Path | None = None

    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        layout.addWidget(self.tree)

        # Style
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #FFFFFF;
                border: 2px inset #808080;
            }
            QTreeWidget::item {
                padding: 2px;
                min-height: 18px;
            }
            QTreeWidget::item:selected {
                background-color: #000080;
                color: #FFFFFF;
            }
        """)

    # ─────────────────────────────────────────────────────────────
    # Project Loading
    # ─────────────────────────────────────────────────────────────

    def load_project(self, project_path: Path) -> None:
        """Load a project folder into the explorer."""
        self._project_path = project_path
        self.tree.clear()

        if not project_path.exists():
            return

        # Root item (project folder)
        root = QTreeWidgetItem([project_path.name])
        root.setData(0, Qt.ItemDataRole.UserRole, {"path": str(project_path), "type": "folder"})
        self.tree.addTopLevelItem(root)

        # Standard folders
        self._add_folder_items(root, project_path)

        root.setExpanded(True)

    def _add_folder_items(self, parent: QTreeWidgetItem, folder_path: Path) -> None:
        """Recursively add folder contents."""
        try:
            items = sorted(folder_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return

        for path in items:
            if path.name.startswith("."):
                continue  # Skip hidden files

            if path.is_dir():
                item = self._create_folder_item(path)
                parent.addChild(item)
                self._add_folder_items(item, path)
            else:
                item = self._create_file_item(path)
                if item:
                    parent.addChild(item)

    def _create_folder_item(self, path: Path) -> QTreeWidgetItem:
        """Create a tree item for a folder."""
        item = QTreeWidgetItem([path.name])
        item.setData(0, Qt.ItemDataRole.UserRole, {"path": str(path), "type": "folder"})

        # Folder type for styling
        folder_name = path.name.lower()
        if folder_name == "assets":
            item.setText(0, "📁 Assets")
        elif folder_name == "scripts":
            item.setText(0, "📁 Scripts")
        elif folder_name == "flows":
            item.setText(0, "📁 Flows")
        else:
            item.setText(0, f"📁 {path.name}")

        return item

    def _create_file_item(self, path: Path) -> QTreeWidgetItem | None:
        """Create a tree item for a file."""
        suffix = path.suffix.lower()

        if suffix == ".dsl":
            item = QTreeWidgetItem([f"📄 {path.name}"])
            item.setData(0, Qt.ItemDataRole.UserRole, {"path": str(path), "type": "script"})
        elif suffix in (".yaml", ".yml"):
            item = QTreeWidgetItem([f"📋 {path.name}"])
            item.setData(0, Qt.ItemDataRole.UserRole, {"path": str(path), "type": "yaml"})
        elif suffix in (".png", ".jpg", ".jpeg", ".bmp"):
            item = QTreeWidgetItem([f"🖼️ {path.name}"])
            item.setData(0, Qt.ItemDataRole.UserRole, {"path": str(path), "type": "asset"})
        else:
            item = QTreeWidgetItem([f"📄 {path.name}"])
            item.setData(0, Qt.ItemDataRole.UserRole, {"path": str(path), "type": "file"})

        return item

    def refresh(self) -> None:
        """Refresh the project tree."""
        if self._project_path:
            self.load_project(self._project_path)

    # ─────────────────────────────────────────────────────────────
    # Event Handlers
    # ─────────────────────────────────────────────────────────────

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on item."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data["type"] != "folder":
            self.file_opened.emit(data["path"], data["type"])

    def _show_context_menu(self, pos) -> None:  # type: ignore
        """Show context menu for selected item."""
        item = self.tree.itemAt(pos)

        menu = QMenu(self)

        if item:
            data = item.data(0, Qt.ItemDataRole.UserRole)

            if data["type"] == "folder":
                new_script = menu.addAction("New Script (.dsl)")
                new_script.triggered.connect(lambda: self._create_new_file(data["path"], "script"))

                new_yaml = menu.addAction("New YAML (.yaml)")
                new_yaml.triggered.connect(lambda: self._create_new_file(data["path"], "yaml"))

                menu.addSeparator()

            if data["type"] != "folder":
                delete_action = menu.addAction("Delete")
                delete_action.triggered.connect(lambda: self._delete_file(data["path"]))

                menu.addSeparator()

        refresh_action = menu.addAction("Refresh")
        refresh_action.triggered.connect(self.refresh)

        menu.exec(self.tree.mapToGlobal(pos))

    def _create_new_file(self, folder_path: str, file_type: str) -> None:
        """Create a new file in the folder."""
        ext = ".dsl" if file_type == "script" else ".yaml"
        name, ok = QInputDialog.getText(
            self, f"New {file_type.title()}", f"File name (without {ext}):"
        )

        if ok and name:
            path = Path(folder_path) / f"{name}{ext}"
            if path.exists():
                QMessageBox.warning(self, "Error", f"File '{path.name}' already exists.")
                return

            # Create file with template
            if file_type == "script":
                content = (
                    f"// {name}.dsl\n\nflow main {{\n  // TODO: Add your automation here\n}}\n"
                )
            else:
                content = f"# {name}.yaml\n\nname: {name}\nflows: []\n"

            path.write_text(content, encoding="utf-8")
            self.refresh()
            self.file_created.emit(str(path), file_type)

    def _delete_file(self, file_path: str) -> None:
        """Delete a file after confirmation."""
        path = Path(file_path)

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete '{path.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                path.unlink()
                self.refresh()
                self.file_deleted.emit(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete file: {e}")
