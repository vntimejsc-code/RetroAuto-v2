"""
RetroAuto v2 - Assets Panel

Manages image templates for automation.
"""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.models import AssetImage
from infra import get_logger

logger = get_logger("AssetsPanel")


class AssetsPanel(QWidget):
    """
    Panel for managing image assets.

    Features:
    - List of assets with thumbnails
    - Add button (import image / capture)
    - Drag & drop support
    - Edit threshold + ROI
    - Test find button
    """

    asset_selected = Signal(str)  # asset_id
    assets_changed = Signal()  # when list changes

    def __init__(self) -> None:
        super().__init__()
        self._assets: list[AssetImage] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Group box
        group = QGroupBox("Assets")
        group_layout = QVBoxLayout(group)

        # Asset list
        self.asset_list = QListWidget()
        self.asset_list.setDragEnabled(True)
        self.asset_list.currentItemChanged.connect(self._on_selection_changed)
        group_layout.addWidget(self.asset_list)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("+ Add")
        self.btn_add.clicked.connect(self._on_add)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_delete.setEnabled(False)

        self.btn_test = QPushButton("Test Find")
        self.btn_test.clicked.connect(self._on_test)
        self.btn_test.setEnabled(False)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_test)
        group_layout.addLayout(btn_layout)

        layout.addWidget(group)

        # Enable drag & drop
        self.setAcceptDrops(True)

    def load_assets(self, assets: list[AssetImage]) -> None:
        """Load assets from script."""
        self._assets = list(assets)
        self.asset_list.clear()

        for asset in self._assets:
            item = QListWidgetItem(f"🖼️ {asset.id}")
            item.setData(256, asset.id)  # Qt.UserRole
            item.setToolTip(f"Path: {asset.path}\nThreshold: {asset.threshold}")
            self.asset_list.addItem(item)

    def get_assets(self) -> list[AssetImage]:
        """Get current assets list."""
        return list(self._assets)

    def add_asset(self, asset: AssetImage) -> None:
        """Add a new asset."""
        self._assets.append(asset)
        item = QListWidgetItem(f"🖼️ {asset.id}")
        item.setData(256, asset.id)
        item.setToolTip(f"Path: {asset.path}\nThreshold: {asset.threshold}")
        self.asset_list.addItem(item)
        self.assets_changed.emit()

    def _on_selection_changed(
        self, current: QListWidgetItem | None, _: QListWidgetItem | None
    ) -> None:
        has_selection = current is not None
        self.btn_delete.setEnabled(has_selection)
        self.btn_test.setEnabled(has_selection)

        if current:
            asset_id = current.data(256)
            self.asset_selected.emit(asset_id)

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
        """Import image as new asset."""
        # Generate unique ID from filename
        asset_id = path.stem
        counter = 1
        while any(a.id == asset_id for a in self._assets):
            asset_id = f"{path.stem}_{counter}"
            counter += 1

        asset = AssetImage(
            id=asset_id,
            path=path.name,  # Will need to copy to project
            threshold=0.8,
        )
        self.add_asset(asset)
        logger.info("Imported asset: %s from %s", asset_id, path)

    def _on_delete(self) -> None:
        """Delete selected asset."""
        current = self.asset_list.currentItem()
        if current:
            asset_id = current.data(256)
            row = self.asset_list.row(current)
            self.asset_list.takeItem(row)

            # Remove from internal list
            self._assets = [a for a in self._assets if a.id != asset_id]
            self.assets_changed.emit()
            logger.info("Deleted asset: %s", asset_id)

    def _on_test(self) -> None:
        """Test find selected asset on screen."""
        current = self.asset_list.currentItem()
        if current:
            asset_id = current.data(256)
            logger.info("Test find asset: %s", asset_id)
            # TODO: Implement test find with matcher

    def dragEnterEvent(self, event) -> None:  # type: ignore
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # type: ignore
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"):
                self._import_image(path)
