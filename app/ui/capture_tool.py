"""
RetroAuto v2 - Screen Capture Tool

Full-screen overlay for region selection.
"""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from core.models import ROI, AssetImage
from infra import get_logger

logger = get_logger("CaptureTool")


class CaptureOverlay(QWidget):
    """
    Full-screen overlay for selecting a region.

    Features:
    - Covers entire screen
    - Rubber-band rectangle selection
    - ESC to cancel
    - Preview of selection
    """

    region_selected = Signal(QRect, QPixmap)  # Selected region and cropped image
    cancelled = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._start_pos: QPoint | None = None
        self._current_pos: QPoint | None = None
        self._screenshot: QPixmap | None = None
        self._selection: QRect | None = None
        self._parent_window: QWidget | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize overlay window."""
        # Frameless, fullscreen, on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Get screen geometry
        screen = QGuiApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            self.setGeometry(geometry)

    def start_capture(self, parent_window: QWidget | None = None) -> None:
        """Start the capture process."""
        self._parent_window = parent_window

        # Hide parent window before capturing screen
        if parent_window:
            parent_window.hide()
            QGuiApplication.processEvents()  # Ensure window is fully hidden
            # Small delay to ensure window is hidden
            import time
            time.sleep(0.15)

        # Take screenshot first
        screen = QGuiApplication.primaryScreen()
        if screen:
            self._screenshot = screen.grabWindow(0)
            self.setGeometry(screen.geometry())

        self._start_pos = None
        self._current_pos = None
        self._selection = None
        self.showFullScreen()
        self.activateWindow()
        logger.info("Capture overlay started")

    def paintEvent(self, event) -> None:  # type: ignore
        """Draw the overlay with selection rectangle."""
        painter = QPainter(self)

        # Draw screenshot as background
        if self._screenshot:
            painter.drawPixmap(0, 0, self._screenshot)

        # Darken non-selected area
        if self._start_pos and self._current_pos:
            rect = self._get_selection_rect()

            # Draw dark overlay
            dark = QColor(0, 0, 0, 128)
            painter.fillRect(self.rect(), dark)

            # Clear selection area (show original screenshot)
            if self._screenshot:
                painter.drawPixmap(rect, self._screenshot, rect)

            # Draw selection border
            pen = QPen(QColor(0, 255, 0), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)

            # Draw size label
            painter.setPen(QPen(Qt.GlobalColor.white))
            size_text = f"{rect.width()} x {rect.height()}"
            painter.drawText(rect.bottomRight() + QPoint(-80, 20), size_text)
        else:
            # Just show dimmed screenshot
            dark = QColor(0, 0, 0, 64)
            painter.fillRect(self.rect(), dark)

            # Instructions
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Click and drag to select region\nESC to cancel",
            )

    def _get_selection_rect(self) -> QRect:
        """Get normalized selection rectangle."""
        if not self._start_pos or not self._current_pos:
            return QRect()

        return QRect(self._start_pos, self._current_pos).normalized()

    def mousePressEvent(self, event) -> None:  # type: ignore
        """Start selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.pos()
            self._current_pos = event.pos()
            self.update()

    def mouseMoveEvent(self, event) -> None:  # type: ignore
        """Update selection."""
        if self._start_pos:
            self._current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore
        """Complete selection."""
        if event.button() == Qt.MouseButton.LeftButton and self._start_pos:
            self._current_pos = event.pos()
            rect = self._get_selection_rect()

            # Minimum size check
            if rect.width() > 5 and rect.height() > 5:
                self._selection = rect
                self._finish_capture()
            else:
                # Too small, reset
                self._start_pos = None
                self._current_pos = None
                self.update()

    def keyPressEvent(self, event) -> None:  # type: ignore
        """Handle keyboard input."""
        if event.key() == Qt.Key.Key_Escape:
            self._restore_parent_window()
            self.hide()
            self.cancelled.emit()
            logger.info("Capture cancelled")

    def _finish_capture(self) -> None:
        """Complete capture and emit result."""
        if not self._selection or not self._screenshot:
            return

        # Crop selection from screenshot
        cropped = self._screenshot.copy(self._selection)

        self._restore_parent_window()
        self.hide()
        self.region_selected.emit(self._selection, cropped)
        logger.info(
            "Region captured: %dx%d at (%d, %d)",
            self._selection.width(),
            self._selection.height(),
            self._selection.x(),
            self._selection.y(),
        )

    def _restore_parent_window(self) -> None:
        """Restore the parent window after capture."""
        if self._parent_window:
            self._parent_window.show()
            self._parent_window.activateWindow()


class CaptureTool:
    """
    High-level capture tool for creating assets.

    Usage:
        tool = CaptureTool(assets_dir)
        tool.capture()  # Shows overlay
        # On selection, creates asset and saves image
    """

    def __init__(
        self,
        assets_dir: Path | None = None,
        existing_asset_ids: set[str] | None = None,
    ) -> None:
        self._assets_dir = assets_dir or Path(".")
        self._overlay = CaptureOverlay()

        # Existing asset IDs from the script (in-memory, may not be on disk)
        self._existing_asset_ids = existing_asset_ids or set()

        # Connect signals
        self._overlay.region_selected.connect(self._on_region_selected)
        self._overlay.cancelled.connect(self._on_cancelled)

        self._callback: Callable | None = None

    def capture(self, callback: Callable | None = None, parent_window: QWidget | None = None) -> None:
        """
        Start capture process.

        Args:
            callback: Function(asset: AssetImage, roi: ROI) called on success
            parent_window: Main window to hide during capture (optional)
        """
        self._callback = callback
        self._overlay.start_capture(parent_window)

    def _on_region_selected(self, rect: QRect, pixmap: QPixmap) -> None:
        """Handle successful region selection."""
        # Get existing asset names to avoid duplicates
        existing_names = self._get_existing_asset_names()

        # Generate unique filename that doesn't conflict with existing assets
        counter = 1
        while True:
            filename = f"capture_{counter}.png"
            asset_id = f"capture_{counter}"  # ID without extension
            path = self._assets_dir / filename

            # Check both: file doesn't exist AND name not in existing assets
            if not path.exists() and asset_id not in existing_names:
                break
            counter += 1

        # Save image
        self._assets_dir.mkdir(parents=True, exist_ok=True)
        pixmap.save(str(path), "PNG")
        logger.info("Saved capture: %s", path)

        # Create asset
        asset = AssetImage(
            id=asset_id,
            path=filename,
            threshold=0.8,
        )

        # Create ROI from selection
        roi = ROI(
            x=rect.x(),
            y=rect.y(),
            w=rect.width(),
            h=rect.height(),
        )

        # Callback
        if self._callback:
            self._callback(asset, roi)

    def _on_cancelled(self) -> None:
        """Handle cancellation."""
        logger.info("Capture cancelled by user")

    def _get_existing_asset_names(self) -> set[str]:
        """Get set of existing asset IDs/names in assets directory.

        Returns:
            Set of asset names (without extension) to avoid duplicates.
        """
        # Start with in-memory asset IDs from the script
        existing = set(self._existing_asset_ids)

        try:
            if self._assets_dir.exists():
                # Also add all image files on disk
                for ext in ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif"]:
                    for path in self._assets_dir.glob(ext):
                        existing.add(path.stem)  # Name without extension
        except Exception as e:
            logger.warning("Error scanning assets: %s", e)
        return existing

