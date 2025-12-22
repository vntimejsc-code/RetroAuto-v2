"""
RetroAuto v2 - Assets Panel

Manages image templates for automation.
Enhanced UX: drag-drop feedback, inline editing, context menu, smart naming.
"""

from pathlib import Path
import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.models import AssetImage
from infra import get_logger

logger = get_logger("AssetsPanel")


# Smart naming categories
NAMING_CATEGORIES = {
    "btn": "Button",
    "dlg": "Dialog/Popup",
    "icon": "Icon",
    "txt": "Text field",
    "img": "Image",
    "menu": "Menu item",
    "tab": "Tab",
    "chk": "Checkbox",
    "lbl": "Label",
}


class AssetsPanel(QWidget):
    """
    Panel for managing image assets.

    Features:
    - List of assets with thumbnails
    - Add button (import image / capture)
    - Drag & drop with visual feedback
    - Inline ID editing (double-click)
    - Context menu with quick actions
    - Smart naming suggestions
    """

    asset_selected = Signal(str)  # asset_id
    assets_changed = Signal()  # when list changes
    insert_action_requested = Signal(str, str)  # asset_id, action_type

    def __init__(self) -> None:
        super().__init__()
        self._assets: list[AssetImage] = []
        self._default_style = ""
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Group box
        self.group = QGroupBox("Assets")
        group_layout = QVBoxLayout(self.group)

        # Drop hint label (shown when empty)
        self.drop_hint = QLabel("📁 Kéo thả ảnh vào đây\nhoặc bấm '+ Add'")
        self.drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_hint.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 11px;
                padding: 20px;
                border: 2px dashed #555555;
                border-radius: 8px;
                background-color: #2a2a2a;
            }
        """)
        group_layout.addWidget(self.drop_hint)

        # Asset list
        self.asset_list = QListWidget()
        self.asset_list.setDragEnabled(True)
        self.asset_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.asset_list.currentItemChanged.connect(self._on_selection_changed)
        self.asset_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.asset_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.asset_list.customContextMenuRequested.connect(self._show_context_menu)
        group_layout.addWidget(self.asset_list)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("+ Add")
        self.btn_add.setToolTip("Import images (or drag & drop)")
        self.btn_add.clicked.connect(self._on_add)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_delete.setEnabled(False)

        self.btn_test = QPushButton("Test Find")
        self.btn_test.setToolTip("Test find this asset on screen")
        self.btn_test.clicked.connect(self._on_test)
        self.btn_test.setEnabled(False)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_test)
        group_layout.addLayout(btn_layout)

        layout.addWidget(self.group)

        # Enable drag & drop
        self.setAcceptDrops(True)
        self._default_style = self.group.styleSheet()
        self._update_visibility()

    def _update_visibility(self) -> None:
        """Show/hide drop hint based on asset count."""
        has_assets = len(self._assets) > 0
        self.drop_hint.setVisible(not has_assets)
        self.asset_list.setVisible(has_assets)

    def load_assets(self, assets: list[AssetImage]) -> None:
        """Load assets from script."""
        self._assets = list(assets)
        self.asset_list.clear()

        for asset in self._assets:
            self._add_list_item(asset)

        self._update_visibility()

    def _add_list_item(self, asset: AssetImage) -> None:
        """Add item to list widget."""
        item = QListWidgetItem(f"🖼️ {asset.id}")
        item.setData(Qt.ItemDataRole.UserRole, asset.id)
        item.setToolTip(
            f"ID: {asset.id}\n"
            f"Path: {asset.path}\n"
            f"Threshold: {asset.threshold}\n"
            f"─────────────────\n"
            f"Double-click to rename\n"
            f"Right-click for options"
        )
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.asset_list.addItem(item)

    def get_assets(self) -> list[AssetImage]:
        """Get current assets list."""
        return list(self._assets)

    def add_asset(self, asset: AssetImage) -> None:
        """Add a new asset."""
        self._assets.append(asset)
        self._add_list_item(asset)
        self._update_visibility()
        self.assets_changed.emit()

    def _on_selection_changed(
        self, current: QListWidgetItem | None, _: QListWidgetItem | None
    ) -> None:
        has_selection = current is not None
        self.btn_delete.setEnabled(has_selection)
        self.btn_test.setEnabled(has_selection)

        if current:
            asset_id = current.data(Qt.ItemDataRole.UserRole)
            self.asset_selected.emit(asset_id)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click to rename asset."""
        old_id = item.data(Qt.ItemDataRole.UserRole)
        self._rename_asset(old_id)

    def _on_add(self) -> None:
        """Add new asset via file dialog."""
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)",
        )

        for path in paths:
            self._import_image(Path(path))

    def _import_image(self, path: Path) -> None:
        """Import image as new asset with smart naming."""
        # Generate smart ID from filename
        asset_id = self._generate_smart_id(path.stem)

        asset = AssetImage(
            id=asset_id,
            path=path.name,
            threshold=0.8,
        )
        self.add_asset(asset)
        logger.info("Imported asset: %s from %s", asset_id, path)

    def _generate_smart_id(self, name: str) -> str:
        """Generate a smart, unique ID from filename."""
        # Clean the name: lowercase, replace spaces with underscore
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", name.lower())
        clean_name = re.sub(r"_+", "_", clean_name).strip("_")

        # If name is just numbers, prefix with 'img_'
        if clean_name.isdigit() or not clean_name:
            clean_name = f"img_{clean_name or 'new'}"

        # Ensure unique
        base_name = clean_name
        counter = 1
        while any(a.id == clean_name for a in self._assets):
            clean_name = f"{base_name}_{counter}"
            counter += 1

        return clean_name

    def _on_delete(self) -> None:
        """Delete selected asset."""
        current = self.asset_list.currentItem()
        if current:
            asset_id = current.data(Qt.ItemDataRole.UserRole)
            row = self.asset_list.row(current)
            self.asset_list.takeItem(row)

            self._assets = [a for a in self._assets if a.id != asset_id]
            self._update_visibility()
            self.assets_changed.emit()
            logger.info("Deleted asset: %s", asset_id)

    def _on_test(self) -> None:
        """Test find selected asset on screen."""
        current = self.asset_list.currentItem()
        if current:
            asset_id = current.data(Qt.ItemDataRole.UserRole)
            logger.info("Test find asset: %s", asset_id)
            # TODO: Implement test find with matcher

    # ─────────────────────────────────────────────────────────────
    # Context Menu
    # ─────────────────────────────────────────────────────────────

    def _show_context_menu(self, pos) -> None:  # type: ignore
        """Show context menu with quick actions."""
        item = self.asset_list.itemAt(pos)
        if not item:
            return

        asset_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        # Rename
        rename_action = QAction("📝 Rename", self)
        rename_action.triggered.connect(lambda: self._rename_asset(asset_id))
        menu.addAction(rename_action)

        # Copy ID
        copy_action = QAction("📋 Copy ID", self)
        copy_action.triggered.connect(lambda: self._copy_id(asset_id))
        menu.addAction(copy_action)

        # Test Find
        test_action = QAction("🔍 Test Find", self)
        test_action.triggered.connect(self._on_test)
        menu.addAction(test_action)

        menu.addSeparator()

        # Insert to Actions
        insert_menu = menu.addMenu("⬇️ Insert to Actions")

        wait_action = QAction("WaitImage", self)
        wait_action.triggered.connect(
            lambda: self.insert_action_requested.emit(asset_id, "WaitImage")
        )
        insert_menu.addAction(wait_action)

        if_action = QAction("IfImage", self)
        if_action.triggered.connect(
            lambda: self.insert_action_requested.emit(asset_id, "IfImage")
        )
        insert_menu.addAction(if_action)

        menu.addSeparator()

        # Delete
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(self._on_delete)
        menu.addAction(delete_action)

        menu.exec(self.asset_list.mapToGlobal(pos))

    def _rename_asset(self, old_id: str) -> None:
        """Rename an asset with validation."""
        new_id, ok = QInputDialog.getText(
            self,
            "Rename Asset",
            f"New ID for '{old_id}':\n\n"
            "Naming convention: category_element\n"
            "Examples: btn_login, dlg_error, icon_ok",
            text=old_id,
        )

        if not ok or not new_id or new_id == old_id:
            return

        # Validate: only allow a-z, 0-9, _
        clean_id = re.sub(r"[^a-z0-9_]", "_", new_id.lower())
        clean_id = re.sub(r"_+", "_", clean_id).strip("_")

        if not clean_id:
            QMessageBox.warning(self, "Invalid ID", "ID cannot be empty.")
            return

        # Check duplicate
        if any(a.id == clean_id for a in self._assets if a.id != old_id):
            QMessageBox.warning(
                self, "Duplicate ID", f"ID '{clean_id}' already exists."
            )
            return

        # Update in assets list
        for asset in self._assets:
            if asset.id == old_id:
                # Create new asset with updated ID
                idx = self._assets.index(asset)
                self._assets[idx] = AssetImage(
                    id=clean_id,
                    path=asset.path,
                    threshold=asset.threshold,
                    roi=asset.roi,
                )
                break

        # Update list item
        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == old_id:
                item.setText(f"🖼️ {clean_id}")
                item.setData(Qt.ItemDataRole.UserRole, clean_id)
                break

        self.assets_changed.emit()
        logger.info("Renamed asset: %s -> %s", old_id, clean_id)

    def _copy_id(self, asset_id: str) -> None:
        """Copy asset ID to clipboard."""
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(asset_id)
            logger.info("Copied asset ID to clipboard: %s", asset_id)

    # ─────────────────────────────────────────────────────────────
    # Drag & Drop with Visual Feedback
    # ─────────────────────────────────────────────────────────────

    def dragEnterEvent(self, event) -> None:  # type: ignore
        """Handle drag enter with visual feedback."""
        if event.mimeData().hasUrls():
            # Check if any URL is an image
            for url in event.mimeData().urls():
                path = Path(url.toLocalFile())
                if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"):
                    self.group.setStyleSheet("""
                        QGroupBox {
                            border: 2px dashed #0078d4;
                            border-radius: 8px;
                            background-color: rgba(0, 120, 212, 0.1);
                        }
                        QGroupBox::title {
                            color: #0078d4;
                        }
                    """)
                    event.acceptProposedAction()
                    return

    def dragLeaveEvent(self, event) -> None:  # type: ignore
        """Reset style when drag leaves."""
        self.group.setStyleSheet(self._default_style)

    def dropEvent(self, event) -> None:  # type: ignore
        """Handle drop with import."""
        self.group.setStyleSheet(self._default_style)

        imported_count = 0
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"):
                self._import_image(path)
                imported_count += 1

        if imported_count > 0:
            logger.info("Imported %d assets via drag & drop", imported_count)
