"""
RetroAuto v2 - Graph Connections

Phase 3: Connection System
- ConnectionItem: Bezier curve wires between nodes
- Drag-and-drop wiring
- Dynamic updates when nodes move
"""

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem

from infra import get_logger

logger = get_logger("GraphConnection")


class ConnectionItem(QGraphicsPathItem):
    """
    Connection wire between two sockets.

    Uses Cubic Bezier curves for smooth S-shaped wires.
    """

    def __init__(self, start_socket=None, end_socket=None):
        super().__init__()

        self.start_socket = start_socket
        self.end_socket = end_socket

        # Visual settings
        self.setZValue(-1)  # Draw behind nodes
        self._update_pen()

        # Enable selection
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        # Update path
        self.update_path()

    def _update_pen(self):
        """Update pen based on selection state."""
        if self.isSelected():
            pen = QPen(QColor(255, 255, 100), 3)
        else:
            # White wire for exec connections
            pen = QPen(QColor(255, 255, 255, 200), 2.5)

        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)

    def update_path(self):
        """Update the Bezier curve path between sockets."""
        if not self.start_socket or not self.end_socket:
            return

        # Get socket positions in scene coordinates
        start_pos = self.start_socket.scenePos()
        end_pos = self.end_socket.scenePos()

        self._draw_bezier(start_pos, end_pos)

    def update_path_to_point(self, end_point: QPointF):
        """Update path to a specific point (for dragging)."""
        if not self.start_socket:
            return

        start_pos = self.start_socket.scenePos()
        self._draw_bezier(start_pos, end_point)

    def _draw_bezier(self, start: QPointF, end: QPointF):
        """Draw Bezier curve from start to end point."""
        path = QPainterPath()
        path.moveTo(start)

        # Calculate control points for S-curve
        dx = end.x() - start.x()

        # Horizontal offset for control points (creates the S shape)
        offset = abs(dx) * 0.5
        if offset < 100:
            offset = 100
        if offset > 300:
            offset = 300

        # Control points
        cp1 = QPointF(start.x() + offset, start.y())
        cp2 = QPointF(end.x() - offset, end.y())

        # Draw cubic Bezier
        path.cubicTo(cp1, cp2, end)

        self.setPath(path)

    def itemChange(self, change, value):
        """Handle selection changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self._update_pen()
        return super().itemChange(change, value)

    def paint(self, painter: QPainter, option, widget=None):
        """Custom paint to add selection highlight."""
        self._update_pen()
        super().paint(painter, option, widget)


class DragConnection(ConnectionItem):
    """
    Temporary connection item used during drag-and-drop wiring.
    Follows mouse cursor until dropped on a valid socket.
    """

    def __init__(self, start_socket):
        super().__init__(start_socket, None)

        # Different visual for drag connection
        pen = QPen(QColor(255, 255, 255, 150), 2.5)
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
