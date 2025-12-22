"""
RetroAuto v2 - Flow Graph View (Visual Scripting Canvas)

Phase 1: Foundation Layer
- QGraphicsView with zoom/pan
- Grid background
- Infinite canvas
"""

from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QWheelEvent, QMouseEvent
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene

from infra import get_logger

logger = get_logger("FlowGraph")


class FlowGraphScene(QGraphicsScene):
    """
    Graphics scene for the flow graph.
    Manages all nodes and connections.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set scene rect to very large area for infinite canvas
        self.setSceneRect(-10000, -10000, 20000, 20000)
        
    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Draw grid background."""
        painter.fillRect(rect, QColor(30, 30, 30))  # Dark background
        
        # Grid settings
        grid_size = 20
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        
        # Draw grid dots
        pen = QPen(QColor(50, 50, 50))
        pen.setWidth(1)
        painter.setPen(pen)
        
        x = left
        while x < rect.right():
            y = top
            while y < rect.bottom():
                painter.drawPoint(x, y)
                y += grid_size
            x += grid_size


class FlowGraphView(QGraphicsView):
    """
    Main view for the flow graph canvas.
    
    Features:
    - Zoom with mouse wheel
    - Pan with middle mouse button or drag
    - Infinite canvas
    - Grid background
    """
    
    # Signals
    zoom_changed = Signal(float)  # Emits zoom level (1.0 = 100%)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create scene
        self.scene = FlowGraphScene(self)
        self.setScene(self.scene)
        
        # View settings
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Zoom settings
        self._zoom = 1.0
        self._zoom_min = 0.1
        self._zoom_max = 3.0
        self._zoom_step = 1.15
        
        # Pan settings
        self._is_panning = False
        self._pan_start = QPointF()
        
        # Initial view position (center)
        self.centerOn(0, 0)
        
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle zoom with mouse wheel."""
        # Get delta
        delta = event.angleDelta().y()
        
        if delta > 0:
            # Zoom in
            zoom_factor = self._zoom_step
        else:
            # Zoom out
            zoom_factor = 1.0 / self._zoom_step
        
        # Calculate new zoom
        new_zoom = self._zoom * zoom_factor
        
        # Clamp zoom
        if new_zoom < self._zoom_min:
            zoom_factor = self._zoom_min / self._zoom
        elif new_zoom > self._zoom_max:
            zoom_factor = self._zoom_max / self._zoom
        
        # Apply zoom
        self.scale(zoom_factor, zoom_factor)
        self._zoom *= zoom_factor
        
        # Emit signal
        self.zoom_changed.emit(self._zoom)
        
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for panning."""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Start panning
            self._is_panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for panning."""
        if self._is_panning:
            # Pan the view
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            
            # Translate view
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Stop panning
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def reset_zoom(self) -> None:
        """Reset zoom to 100%."""
        factor = 1.0 / self._zoom
        self.scale(factor, factor)
        self._zoom = 1.0
        self.zoom_changed.emit(self._zoom)
    
    def zoom_to_fit(self) -> None:
        """Zoom to fit all items in view."""
        items_rect = self.scene.itemsBoundingRect()
        if not items_rect.isEmpty():
            self.fitInView(items_rect, Qt.AspectRatioMode.KeepAspectRatio)
            # Update zoom level
            self._zoom = self.transform().m11()
            self.zoom_changed.emit(self._zoom)
