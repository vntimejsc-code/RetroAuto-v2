"""
RetroAuto v2 - ROI Selector

Screen region selector with overlay and drag selection.
Part of RetroScript Phase 14 - Visual Editor Components.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QPainter, QPen, QPixmap, QScreen
from PySide6.QtWidgets import QApplication, QLabel, QRubberBand, QWidget


@dataclass
class Region:
    """A selected screen region."""

    x: int
    y: int
    width: int
    height: int

    def to_tuple(self) -> tuple[int, int, int, int]:
        """Convert to (x, y, w, h) tuple."""
        return (self.x, self.y, self.width, self.height)

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary."""
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    @property
    def center(self) -> tuple[int, int]:
        """Get center point."""
        return (self.x + self.width // 2, self.y + self.height // 2)


class ROISelector(QWidget):
    """Full-screen overlay for selecting a region of interest.

    Usage:
        def on_selected(region):
            print(f"Selected: {region.x}, {region.y}, {region.width}x{region.height}")

        selector = ROISelector()
        selector.region_selected.connect(on_selected)
        selector.start()
    """

    region_selected = Signal(Region)
    selection_cancelled = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Selection state
        self._origin = QPoint()
        self._rubber_band: QRubberBand | None = None
        self._screenshot: QPixmap | None = None
        self._is_selecting = False

        # Style
        self._overlay_color = QColor(0, 0, 0, 100)
        self._border_color = QColor(0, 150, 255)
        self._info_bg = QColor(0, 0, 0, 180)
        self._info_fg = QColor(255, 255, 255)

    def start(self) -> None:
        """Start the region selection."""
        # Capture screen
        screen = QApplication.primaryScreen()
        if screen:
            self._screenshot = screen.grabWindow(0)
            self.setGeometry(screen.geometry())

        self.showFullScreen()
        self.activateWindow()
        self.raise_()

    def paintEvent(self, event) -> None:
        """Paint the overlay and selection."""
        painter = QPainter(self)

        # Draw screenshot as background
        if self._screenshot:
            painter.drawPixmap(0, 0, self._screenshot)

        # Draw semi-transparent overlay
        painter.fillRect(self.rect(), self._overlay_color)

        # Draw instructions
        painter.setPen(self._info_fg)
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
            "\n\n Click and drag to select region | ESC to cancel",
        )

    def mousePressEvent(self, event) -> None:
        """Handle mouse press - start selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position().toPoint()
            self._is_selecting = True

            if not self._rubber_band:
                self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)

            self._rubber_band.setGeometry(QRect(self._origin, self._origin))
            self._rubber_band.show()

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move - update selection."""
        if self._is_selecting and self._rubber_band:
            rect = QRect(self._origin, event.position().toPoint()).normalized()
            self._rubber_band.setGeometry(rect)

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release - finish selection."""
        if event.button() == Qt.MouseButton.LeftButton and self._is_selecting:
            self._is_selecting = False

            if self._rubber_band:
                rect = self._rubber_band.geometry()
                self._rubber_band.hide()

                # Only emit if selection is meaningful
                if rect.width() > 5 and rect.height() > 5:
                    region = Region(
                        x=rect.x(),
                        y=rect.y(),
                        width=rect.width(),
                        height=rect.height(),
                    )
                    self.region_selected.emit(region)

            self.close()

    def keyPressEvent(self, event) -> None:
        """Handle key press - ESC to cancel."""
        if event.key() == Qt.Key.Key_Escape:
            self.selection_cancelled.emit()
            self.close()


class ROISelectorDialog:
    """Convenience wrapper for ROI selection with callback.

    Usage:
        def handle_region(region):
            print(f"Got region: {region}")

        ROISelectorDialog.select(handle_region)
    """

    _current_selector: ROISelector | None = None

    @classmethod
    def select(
        cls,
        callback: Callable[[Region], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> None:
        """Open ROI selector and call callback with result.

        Args:
            callback: Called with Region when selection is made
            on_cancel: Called when selection is cancelled
        """
        # Ensure Qt app exists
        app = QApplication.instance()
        if not app:
            app = QApplication([])

        cls._current_selector = ROISelector()

        if callback:
            cls._current_selector.region_selected.connect(callback)

        if on_cancel:
            cls._current_selector.selection_cancelled.connect(on_cancel)

        cls._current_selector.start()


class MiniROIPreview(QLabel):
    """Small preview widget showing a captured ROI.

    Usage:
        preview = MiniROIPreview()
        preview.set_region(Region(100, 100, 200, 150))
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(100, 75)
        self.setMaximumSize(300, 225)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #0096ff;
                border-radius: 4px;
                background: #1e1e1e;
            }
        """)
        self._region: Region | None = None

    def set_region(self, region: Region) -> None:
        """Set and display a region."""
        self._region = region
        self._capture_region()

    def _capture_region(self) -> None:
        """Capture and display the region."""
        if not self._region:
            return

        screen = QApplication.primaryScreen()
        if not screen:
            return

        pixmap = screen.grabWindow(
            0,
            self._region.x,
            self._region.y,
            self._region.width,
            self._region.height,
        )

        # Scale to fit
        scaled = pixmap.scaled(
            self.width() - 4,
            self.height() - 4,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.setPixmap(scaled)

    def get_region(self) -> Region | None:
        """Get the current region."""
        return self._region


def select_roi() -> Region | None:
    """Blocking function to select a ROI.

    Returns:
        Selected Region or None if cancelled
    """
    result: list[Region | None] = [None]

    def on_selected(region: Region) -> None:
        result[0] = region

    app = QApplication.instance()
    if not app:
        app = QApplication([])

    selector = ROISelector()
    selector.region_selected.connect(on_selected)
    selector.start()

    # Process events until closed
    while selector.isVisible():
        app.processEvents()

    return result[0]
