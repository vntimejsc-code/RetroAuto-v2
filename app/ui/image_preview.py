"""
RetroAuto v2 - Image Preview

Asset preview widget with zoom, pan, and match highlighting.
Part of RetroScript Phase 14 - Visual Editor Components.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)


@dataclass
class MatchHighlight:
    """A match result to highlight on the image."""

    x: int
    y: int
    width: int
    height: int
    score: float = 1.0
    label: str = ""


class ImagePreviewWidget(QLabel):
    """Image display widget with zoom and pan support."""

    clicked = Signal(int, int)  # x, y position

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._zoom = 1.0
        self._highlights: list[MatchHighlight] = []
        self._pan_start: QPoint | None = None

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(100, 100)
        self.setStyleSheet("background: #1e1e1e; border: 1px solid #3c3c3c;")

    def set_image(self, image: QPixmap | QImage | str | Path) -> None:
        """Set the image to display.

        Args:
            image: QPixmap, QImage, or path to image file
        """
        if isinstance(image, (str, Path)):
            self._pixmap = QPixmap(str(image))
        elif isinstance(image, QImage):
            self._pixmap = QPixmap.fromImage(image)
        else:
            self._pixmap = image

        self._update_display()

    def set_zoom(self, zoom: float) -> None:
        """Set zoom level (1.0 = 100%)."""
        self._zoom = max(0.1, min(10.0, zoom))
        self._update_display()

    def zoom_in(self) -> None:
        """Zoom in by 25%."""
        self.set_zoom(self._zoom * 1.25)

    def zoom_out(self) -> None:
        """Zoom out by 25%."""
        self.set_zoom(self._zoom * 0.8)

    def zoom_fit(self) -> None:
        """Zoom to fit the widget."""
        if not self._pixmap:
            return

        # Calculate zoom to fit
        w_ratio = self.width() / self._pixmap.width()
        h_ratio = self.height() / self._pixmap.height()
        self._zoom = min(w_ratio, h_ratio, 1.0)
        self._update_display()

    def zoom_reset(self) -> None:
        """Reset zoom to 100%."""
        self.set_zoom(1.0)

    def add_highlight(self, highlight: MatchHighlight) -> None:
        """Add a match highlight."""
        self._highlights.append(highlight)
        self._update_display()

    def clear_highlights(self) -> None:
        """Clear all highlights."""
        self._highlights.clear()
        self._update_display()

    def _update_display(self) -> None:
        """Update the displayed image."""
        if not self._pixmap:
            self.setText("No image")
            return

        # Scale image
        scaled_size = self._pixmap.size() * self._zoom
        scaled = self._pixmap.scaled(
            scaled_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        # Draw highlights
        if self._highlights:
            scaled = self._draw_highlights(scaled)

        self.setPixmap(scaled)

    def _draw_highlights(self, pixmap: QPixmap) -> QPixmap:
        """Draw match highlights on the pixmap."""
        result = QPixmap(pixmap)
        painter = QPainter(result)

        for hl in self._highlights:
            # Scale coordinates
            x = int(hl.x * self._zoom)
            y = int(hl.y * self._zoom)
            w = int(hl.width * self._zoom)
            h = int(hl.height * self._zoom)

            # Color based on score
            if hl.score >= 0.9:
                color = QColor(0, 200, 0, 180)  # Green
            elif hl.score >= 0.7:
                color = QColor(255, 165, 0, 180)  # Orange
            else:
                color = QColor(255, 0, 0, 180)  # Red

            # Draw rectangle
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.drawRect(x, y, w, h)

            # Draw label
            if hl.label:
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(x, y - 4, hl.label)

        painter.end()
        return result

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for panning."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_start = event.position().toPoint()
        elif event.button() == Qt.MouseButton.LeftButton:
            # Calculate click position on original image
            if self._pixmap:
                pos = event.position().toPoint()
                x = int(pos.x() / self._zoom)
                y = int(pos.y() / self._zoom)
                self.clicked.emit(x, y)

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for panning."""
        if self._pan_start:
            delta = event.position().toPoint() - self._pan_start
            # Pan is handled by scroll area
            self._pan_start = event.position().toPoint()

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release."""
        self._pan_start = None


class ImagePreview(QWidget):
    """Complete image preview with controls.

    Usage:
        preview = ImagePreview()
        preview.load_image("assets/button.png")
        preview.add_match(100, 100, 50, 30, 0.95)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_path: str = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()

        open_btn = QPushButton("📂 Open")
        open_btn.clicked.connect(self._on_open)
        toolbar.addWidget(open_btn)

        toolbar.addStretch()

        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setMaximumWidth(30)
        zoom_out_btn.clicked.connect(self._on_zoom_out)
        toolbar.addWidget(zoom_out_btn)

        self._zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self._zoom_slider.setRange(10, 500)
        self._zoom_slider.setValue(100)
        self._zoom_slider.setMaximumWidth(150)
        self._zoom_slider.valueChanged.connect(self._on_zoom_slider)
        toolbar.addWidget(self._zoom_slider)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setMaximumWidth(30)
        zoom_in_btn.clicked.connect(self._on_zoom_in)
        toolbar.addWidget(zoom_in_btn)

        fit_btn = QPushButton("Fit")
        fit_btn.setMaximumWidth(40)
        fit_btn.clicked.connect(self._on_fit)
        toolbar.addWidget(fit_btn)

        layout.addLayout(toolbar)

        # Scroll area for image
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._image_widget = ImagePreviewWidget()
        self._scroll.setWidget(self._image_widget)

        layout.addWidget(self._scroll)

        # Info bar
        self._info_label = QLabel("No image loaded")
        self._info_label.setStyleSheet("color: #888; padding: 4px;")
        layout.addWidget(self._info_label)

        # Style
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 4px 8px;
                background: #2d2d2d;
            }
            QPushButton:hover {
                background: #404040;
            }
        """)

    def load_image(self, path: str | Path) -> None:
        """Load an image from file."""
        path = Path(path)
        if path.exists():
            self._current_path = str(path)
            self._image_widget.set_image(path)
            self._update_info()

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """Set image from pixmap."""
        self._image_widget.set_image(pixmap)
        self._current_path = ""
        self._update_info()

    def add_match(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        score: float = 1.0,
        label: str = "",
    ) -> None:
        """Add a match highlight."""
        self._image_widget.add_highlight(MatchHighlight(x, y, width, height, score, label))

    def clear_matches(self) -> None:
        """Clear all match highlights."""
        self._image_widget.clear_highlights()

    def _update_info(self) -> None:
        """Update the info label."""
        if self._image_widget._pixmap:
            pm = self._image_widget._pixmap
            zoom = int(self._image_widget._zoom * 100)
            self._info_label.setText(
                f"{self._current_path or 'Image'} | "
                f"{pm.width()}x{pm.height()} | "
                f"{zoom}%"
            )
        else:
            self._info_label.setText("No image loaded")

    def _on_open(self) -> None:
        """Open file dialog."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)",
        )
        if path:
            self.load_image(path)

    def _on_zoom_in(self) -> None:
        """Zoom in."""
        self._image_widget.zoom_in()
        self._zoom_slider.setValue(int(self._image_widget._zoom * 100))
        self._update_info()

    def _on_zoom_out(self) -> None:
        """Zoom out."""
        self._image_widget.zoom_out()
        self._zoom_slider.setValue(int(self._image_widget._zoom * 100))
        self._update_info()

    def _on_zoom_slider(self, value: int) -> None:
        """Handle zoom slider change."""
        self._image_widget.set_zoom(value / 100)
        self._update_info()

    def _on_fit(self) -> None:
        """Zoom to fit."""
        self._image_widget.zoom_fit()
        self._zoom_slider.setValue(int(self._image_widget._zoom * 100))
        self._update_info()
