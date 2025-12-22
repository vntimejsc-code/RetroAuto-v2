"""
RetroAuto v2 - ROI Editor

Visual editor for adjusting Region of Interest on a screenshot.
"""

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from core.models import ROI
from infra import get_logger

logger = get_logger("ROIEditor")


class ROICanvas(QWidget):
    """
    Canvas for displaying image and editing ROI.

    Features:
    - Display screenshot/template
    - Draggable ROI rectangle
    - Resize handles on corners
    """

    roi_changed = Signal(QRect)

    HANDLE_SIZE = 8

    def __init__(self) -> None:
        super().__init__()
        self._pixmap: QPixmap | None = None
        self._roi: QRect = QRect(0, 0, 100, 100)
        self._dragging = False
        self._resizing = False
        self._resize_handle: str = ""
        self._drag_offset = QPoint()

        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)

    def set_image(self, pixmap: QPixmap) -> None:
        """Set the background image."""
        self._pixmap = pixmap
        self.setFixedSize(pixmap.size())
        self.update()

    def set_roi(self, roi: ROI | None) -> None:
        """Set the ROI rectangle."""
        if roi:
            self._roi = QRect(roi.x, roi.y, roi.w, roi.h)
        else:
            # Default to center of image
            if self._pixmap:
                w, h = self._pixmap.width(), self._pixmap.height()
                self._roi = QRect(w // 4, h // 4, w // 2, h // 2)
        self.update()

    def get_roi(self) -> ROI:
        """Get current ROI."""
        return ROI(
            x=max(0, self._roi.x()),
            y=max(0, self._roi.y()),
            w=max(1, self._roi.width()),
            h=max(1, self._roi.height()),
        )

    def paintEvent(self, event) -> None:  # type: ignore
        """Draw image and ROI overlay."""
        painter = QPainter(self)

        # Draw image
        if self._pixmap:
            painter.drawPixmap(0, 0, self._pixmap)

        # Darken outside ROI
        dark = QColor(0, 0, 0, 100)
        roi = self._roi

        # Top
        painter.fillRect(0, 0, self.width(), roi.top(), dark)
        # Bottom
        painter.fillRect(0, roi.bottom(), self.width(), self.height() - roi.bottom(), dark)
        # Left
        painter.fillRect(0, roi.top(), roi.left(), roi.height(), dark)
        # Right
        painter.fillRect(roi.right(), roi.top(), self.width() - roi.right(), roi.height(), dark)

        # Draw ROI border
        pen = QPen(QColor(0, 200, 0), 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawRect(roi)

        # Draw resize handles
        handles = self._get_handles()
        painter.setBrush(QColor(0, 200, 0))
        for _name, rect in handles.items():
            painter.drawRect(rect)

        # Size label
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.drawText(
            roi.bottomRight() + QPoint(-60, 15),
            f"{roi.width()} x {roi.height()}",
        )

    def _get_handles(self) -> dict[str, QRect]:
        """Get resize handle rectangles."""
        s = self.HANDLE_SIZE
        r = self._roi
        return {
            "tl": QRect(r.left() - s // 2, r.top() - s // 2, s, s),
            "tr": QRect(r.right() - s // 2, r.top() - s // 2, s, s),
            "bl": QRect(r.left() - s // 2, r.bottom() - s // 2, s, s),
            "br": QRect(r.right() - s // 2, r.bottom() - s // 2, s, s),
        }

    def _get_handle_at(self, pos: QPoint) -> str:
        """Check if position is on a handle."""
        for name, rect in self._get_handles().items():
            if rect.contains(pos):
                return name
        return ""

    def mousePressEvent(self, event) -> None:  # type: ignore
        """Handle mouse press."""
        if event.button() != Qt.MouseButton.LeftButton:
            return

        pos = event.pos()

        # Check handles first
        handle = self._get_handle_at(pos)
        if handle:
            self._resizing = True
            self._resize_handle = handle
            return

        # Check if inside ROI for dragging
        if self._roi.contains(pos):
            self._dragging = True
            self._drag_offset = pos - self._roi.topLeft()

    def mouseMoveEvent(self, event) -> None:  # type: ignore
        """Handle mouse move."""
        pos = event.pos()

        # Update cursor based on position
        handle = self._get_handle_at(pos)
        if handle in ("tl", "br"):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif handle in ("tr", "bl"):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif self._roi.contains(pos):
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        # Handle resize
        if self._resizing:
            self._do_resize(pos)
            self.update()
            return

        # Handle drag
        if self._dragging:
            new_pos = pos - self._drag_offset
            self._roi.moveTo(new_pos)
            self._clamp_roi()
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore
        """Handle mouse release."""
        if self._dragging or self._resizing:
            self._dragging = False
            self._resizing = False
            self._resize_handle = ""
            self.roi_changed.emit(self._roi)

    def _do_resize(self, pos: QPoint) -> None:
        """Resize ROI based on handle drag."""
        r = self._roi

        if self._resize_handle == "tl":
            r.setTopLeft(pos)
        elif self._resize_handle == "tr":
            r.setTopRight(pos)
        elif self._resize_handle == "bl":
            r.setBottomLeft(pos)
        elif self._resize_handle == "br":
            r.setBottomRight(pos)

        # Normalize and enforce minimum size
        self._roi = r.normalized()
        if self._roi.width() < 10:
            self._roi.setWidth(10)
        if self._roi.height() < 10:
            self._roi.setHeight(10)

        self._clamp_roi()

    def _clamp_roi(self) -> None:
        """Clamp ROI to image bounds."""
        if not self._pixmap:
            return

        # Clamp to image bounds
        if self._roi.left() < 0:
            self._roi.moveLeft(0)
        if self._roi.top() < 0:
            self._roi.moveTop(0)
        if self._roi.right() > self._pixmap.width():
            self._roi.moveRight(self._pixmap.width())
        if self._roi.bottom() > self._pixmap.height():
            self._roi.moveBottom(self._pixmap.height())


class ROIEditorDialog(QDialog):
    """
    Dialog for editing ROI on a screenshot.
    """

    def __init__(self, pixmap: QPixmap, roi: ROI | None = None, parent=None) -> None:  # type: ignore
        super().__init__(parent)
        self.setWindowTitle("Edit ROI")
        self.setModal(True)

        self._init_ui(pixmap, roi)

    def _init_ui(self, pixmap: QPixmap, roi: ROI | None) -> None:
        layout = QVBoxLayout(self)

        # Instructions
        label = QLabel("Drag to move, drag corners to resize")
        layout.addWidget(label)

        # Canvas
        self.canvas = ROICanvas()
        self.canvas.set_image(pixmap)
        self.canvas.set_roi(roi)
        layout.addWidget(self.canvas)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_roi(self) -> ROI:
        """Get the edited ROI."""
        return self.canvas.get_roi()
