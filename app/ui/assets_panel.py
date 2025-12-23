"""
RetroAuto v2 - Assets Panel

Manages image templates for automation.
Enhanced UX: drag-drop feedback, inline editing, context menu, smart naming.
"""

import re
from pathlib import Path

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QAction, QDrag
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)


class RenameDelegate(QStyledItemDelegate):
    """Custom delegate to ensure rename editor has enough width."""

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index) -> None:
        """Update editor geometry to use full available width."""
        rect = option.rect
        # Expand width to show full text relative to font size
        font_metrics = editor.fontMetrics()
        # Add buffer for padding and emoji
        text_width = font_metrics.horizontalAdvance(index.data()) + 40

        # Use wider of item width or text width
        width = max(rect.width(), text_width)

        # Constrain to parent widget width so it doesn't go off screen
        if editor.parentWidget():
            parent_width = editor.parentWidget().width()
            width = min(width, parent_width - rect.x())

        editor.setGeometry(rect.x(), rect.y(), width, rect.height())


from core.models import AssetImage
from infra import get_logger

logger = get_logger("AssetsPanel")

# Custom MIME type for drag to Actions panel
ASSET_MIME_TYPE = "application/x-retroauto-asset"


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


class AssetListWidget(QListWidget):
    """Custom list widget that sends asset_id via MIME when dragging to Actions."""

    def __init__(self, parent=None) -> None:  # type: ignore
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)

    def startDrag(self, supportedActions) -> None:  # type: ignore
        """Start drag with custom MIME type containing asset_id."""
        item = self.currentItem()
        if not item:
            return

        asset_id = item.data(Qt.ItemDataRole.UserRole)
        if not asset_id:
            return

        # Create drag with custom MIME data
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData(ASSET_MIME_TYPE, asset_id.encode("utf-8"))
        mime_data.setText(f"Asset: {asset_id}")  # For visual feedback
        drag.setMimeData(mime_data)

        # Execute drag
        drag.exec(Qt.DropAction.CopyAction)


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
        self.drop_hint.setStyleSheet(
            """
            QLabel {
                color: #808080;
                font-size: 11px;
                padding: 20px;
                border: 2px dashed #555555;
                border-radius: 8px;
                background-color: #2a2a2a;
            }
        """
        )
        group_layout.addWidget(self.drop_hint)

        # Asset list with custom drag support
        self.asset_list = AssetListWidget()
        self.asset_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.asset_list.currentItemChanged.connect(self._on_selection_changed)
        self.asset_list.itemDoubleClicked.connect(self._on_asset_double_clicked)
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

        # F2 shortcut for inline rename
        from PySide6.QtGui import QKeySequence, QShortcut

        self.rename_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F2), self.asset_list)
        self.rename_shortcut.activated.connect(self._start_inline_rename)

        # Handle inline editing
        self.asset_list.setItemDelegate(RenameDelegate(self.asset_list))
        self.asset_list.itemChanged.connect(self._on_item_edited)

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

    def get_assets(self) -> list[AssetImage]:
        """Get current assets list for syncing to script."""
        return list(self._assets)

    def _add_list_item(self, asset: AssetImage) -> None:
        """Add item to list widget."""
        item = QListWidgetItem(f"🖼️ {asset.id}")
        item.setData(Qt.ItemDataRole.UserRole, asset.id)
        item.setToolTip(
            f"ID: {asset.id}\n"
            f"Path: {asset.path}\n"
            f"Threshold: {asset.threshold}\n"
            f"─────────────────\n"
            f"Double-click: Preview\n"
            f"F2: Rename\n"
            f"Right-click: Options"
        )
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.asset_list.addItem(item)

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
        # Step 1: Try clean filename
        base_id = self._clean_name(path.stem)

        if not self._id_exists(base_id):
            # Unique - use as is
            asset_id = base_id
        else:
            # Step 2: Try with folder prefix (e.g., folder_filename)
            folder_name = self._clean_name(path.parent.name)
            prefixed_id = f"{folder_name}_{base_id}" if folder_name else base_id

            if not self._id_exists(prefixed_id):
                asset_id = prefixed_id
            else:
                # Step 3: Show dialog to let user rename
                asset_id = self._prompt_for_unique_id(base_id, prefixed_id, path)
                if not asset_id:
                    # User cancelled
                    return

        asset = AssetImage(
            id=asset_id,
            path=path.name,
            threshold=0.8,
        )
        self.add_asset(asset)
        logger.info("Imported asset: %s from %s", asset_id, path)

    def _clean_name(self, name: str) -> str:
        """Clean a name to valid ID format (lowercase, alphanumeric + underscore)."""
        clean = re.sub(r"[^a-zA-Z0-9_]", "_", name.lower())
        clean = re.sub(r"_+", "_", clean).strip("_")
        if clean.isdigit() or not clean:
            clean = f"img_{clean or 'new'}"
        return clean

    def _id_exists(self, asset_id: str) -> bool:
        """Check if asset ID already exists."""
        return any(a.id == asset_id for a in self._assets)

    def _prompt_for_unique_id(self, base_id: str, prefixed_id: str, path: Path) -> str | None:
        """Show dialog to get unique ID from user when auto-naming fails."""
        # Suggest a numbered version as fallback
        counter = 1
        suggested = prefixed_id
        while self._id_exists(suggested):
            suggested = f"{prefixed_id}_{counter}"
            counter += 1

        new_id, ok = QInputDialog.getText(
            self,
            "Tên ảnh bị trùng",
            f"Ảnh '{base_id}' đã tồn tại.\n" f"Folder: {path.parent.name}\n\n" f"Nhập ID mới:",
            text=suggested,
        )

        if not ok or not new_id:
            return None

        # Clean and validate
        clean_id = self._clean_name(new_id)
        if not clean_id:
            QMessageBox.warning(self, "ID không hợp lệ", "ID không được để trống.")
            return None

        if self._id_exists(clean_id):
            QMessageBox.warning(
                self, "ID bị trùng", f"ID '{clean_id}' đã tồn tại. Vui lòng chọn tên khác."
            )
            return None

        return clean_id

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

        # Delete
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(self._on_delete)
        menu.addAction(delete_action)

        menu.exec(self.asset_list.mapToGlobal(pos))

    def _on_asset_double_clicked(self, item: QListWidgetItem) -> None:
        """Show image preview when double-clicking asset."""
        asset_id = item.data(Qt.ItemDataRole.UserRole)
        asset = next((a for a in self._assets if a.id == asset_id), None)

        if asset and asset.path:
            # Show image preview in dialog
            from PySide6.QtWidgets import QDialog, QVBoxLayout

            from app.ui.image_preview import ImagePreview

            dialog = QDialog(self)
            dialog.setWindowTitle(f"Preview: {asset_id}")
            dialog.resize(800, 600)

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)

            preview = ImagePreview()
            preview.load_image(asset.path)
            layout.addWidget(preview)

            dialog.exec()

    def _rename_asset(self, old_id: str) -> None:
        """Rename an asset with improved dialog."""
        # Create custom dialog for better UX
        from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Rename Asset")
        dialog.setMinimumWidth(450)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        # Current ID and instructions
        info = QLabel(
            f"<b>Current ID:</b> {old_id}<br><br>"
            "<b>Naming Convention:</b> category_element<br>"
            "Examples: btn_login, icon_close, dlg_confirm"
        )
        layout.addWidget(info)

        # Input field
        layout.addWidget(QLabel("<b>New ID:</b>"))
        input_field = QLineEdit(old_id)
        input_field.setMinimumHeight(32)
        input_field.setStyleSheet("QLineEdit { font-size: 13px; padding: 4px; }")
        input_field.selectAll()
        layout.addWidget(input_field)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        new_id = input_field.text().strip()
        if not new_id or new_id == old_id:
            return

        # Validate: only allow a-z, 0-9, _
        clean_id = re.sub(r"[^a-z0-9_]", "_", new_id.lower())
        clean_id = re.sub(r"_+", "_", clean_id).strip("_")

        if not clean_id:
            QMessageBox.warning(self, "Invalid ID", "ID cannot be empty.")
            return

        # Check duplicate
        if any(a.id == clean_id for a in self._assets if a.id != old_id):
            QMessageBox.warning(self, "Duplicate ID", f"ID '{clean_id}' already exists.")
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

    def _start_inline_rename(self) -> None:
        """Start inline editing on selected item (F2)."""
        current_item = self.asset_list.currentItem()
        if current_item:
            self.asset_list.editItem(current_item)

    def _on_item_edited(self, item: QListWidgetItem) -> None:
        """Handle inline editing completion."""
        # Get new text without emoji
        new_text = item.text().replace("🖼️ ", "").strip()
        old_id = item.data(Qt.ItemDataRole.UserRole)

        if not new_text or new_text == old_id:
            # Restore original
            item.setText(f"🖼️ {old_id}")
            return

        # Validate
        import re

        clean_id = re.sub(r"[^a-z0-9_]", "_", new_text.lower())
        clean_id = re.sub(r"_+", "_", clean_id).strip("_")

        if not clean_id or any(a.id == clean_id for a in self._assets if a.id != old_id):
            # Invalid - restore
            item.setText(f"🖼️ {old_id}")
            if not clean_id:
                QMessageBox.warning(self, "Invalid ID", "ID cannot be empty.")
            else:
                QMessageBox.warning(self, "Duplicate ID", f"'{clean_id}' exists.")
            return

        # Update asset
        for asset in self._assets:
            if asset.id == old_id:
                asset.id = clean_id
                break

        # Update item
        item.setText(f"🖼️ {clean_id}")
        item.setData(Qt.ItemDataRole.UserRole, clean_id)

        self.assets_changed.emit()
        logger.info(f"Inline renamed: {old_id} → {clean_id}")

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
                    self.group.setStyleSheet(
                        """
                        QGroupBox {
                            border: 2px dashed #0078d4;
                            border-radius: 8px;
                            background-color: rgba(0, 120, 212, 0.1);
                        }
                        QGroupBox::title {
                            color: #0078d4;
                        }
                    """
                    )
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
