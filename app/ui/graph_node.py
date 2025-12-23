"""
RetroAuto v2 - Graph Node Items

Phase 2: Node Rendering
- NodeItem: Visual representation of actions
- SocketItem: Connection points (inputs/outputs)
- Professional Blueprint-style aesthetics
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
)

from app.ui.graph_connection import ConnectionItem, DragConnection
from core.models import Action
from infra import get_logger

logger = get_logger("GraphNode")


# Color scheme for different action types
NODE_COLORS = {
    "ClickImage": QColor(76, 175, 80),  # Green
    "Click": QColor(76, 175, 80),
    "ClickUntil": QColor(76, 175, 80),
    "ClickRandom": QColor(76, 175, 80),
    "WaitImage": QColor(33, 150, 243),  # Blue
    "WaitPixel": QColor(33, 150, 243),
    "IfImage": QColor(255, 152, 0),  # Orange
    "IfText": QColor(255, 152, 0),
    "IfPixel": QColor(255, 152, 0),
    "Loop": QColor(156, 39, 176),  # Purple
    "WhileImage": QColor(156, 39, 176),
    "Delay": QColor(158, 158, 158),  # Gray
    "DelayRandom": QColor(158, 158, 158),
    "Hotkey": QColor(244, 67, 54),  # Red
    "TypeText": QColor(244, 67, 54),
    "ReadText": QColor(244, 67, 54),
    "Label": QColor(96, 125, 139),  # Blue Gray
    "Goto": QColor(96, 125, 139),
    "RunFlow": QColor(96, 125, 139),
}

DEFAULT_NODE_COLOR = QColor(100, 100, 100)


class SocketType:
    """Socket type enum."""

    EXEC = "exec"  # Execution flow (white triangle)
    DATA = "data"  # Data (colored circle)


class SocketItem(QGraphicsEllipseItem):
    """
    Connection socket (input/output point on a node).

    Types:
    - Exec: Execution flow sockets (triangular shape)
    - Data: Data sockets (circular shape)
    """

    def __init__(self, socket_type: str, socket_name: str, is_output: bool, parent=None):
        super().__init__(-6, -6, 12, 12, parent)

        self.socket_type = socket_type
        self.socket_name = socket_name
        self.is_output = is_output

        # Visual settings
        if socket_type == SocketType.EXEC:
            # Exec sockets: white background
            self.setBrush(QBrush(QColor(255, 255, 255, 200)))
            self.setPen(QPen(QColor(200, 200, 200), 2))
        else:
            # Data sockets: colored
            color = QColor(100, 200, 255)  # Default cyan for data
            self.setBrush(QBrush(color))
            self.setPen(QPen(color.darker(120), 2))

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

        # Connections
        self.connections = []  # List of ConnectionItem
        self._drag_connection = None  # Temporary connection during drag

    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        self.setPen(QPen(QColor(255, 255, 100), 3))
        self.setCursor(Qt.CursorShape.CrossCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Remove highlight."""
        if self.socket_type == SocketType.EXEC:
            self.setPen(QPen(QColor(200, 200, 200), 2))
        else:
            self.setPen(QPen(self.brush().color().darker(120), 2))
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Start drag connection."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Only output sockets can initiate connections
            if self.is_output:
                self._drag_connection = DragConnection(self)
                self.scene().addItem(self._drag_connection)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """Update drag connection."""
        if self._drag_connection:
            self._drag_connection.update_path_to_point(event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """Complete or cancel drag connection."""
        if self._drag_connection:
            # Try to find target socket under cursor
            target = self._find_socket_at(event.scenePos())

            if target and self._can_connect_to(target):
                # Create permanent connection
                connection = ConnectionItem(self, target)
                self.scene().addItem(connection)
                connection.update_path()

                # Track connection in both sockets
                self.connections.append(connection)
                target.connections.append(connection)

                logger.info(f"Connected {self.socket_name} -> {target.socket_name}")

            # Remove drag connection
            self.scene().removeItem(self._drag_connection)
            self._drag_connection = None
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def _find_socket_at(self, pos: QPointF):
        """Find socket item at given position."""
        items = self.scene().items(pos)
        for item in items:
            if isinstance(item, SocketItem) and item != self:
                return item
        return None

    def _can_connect_to(self, target) -> bool:
        """Check if can connect to target socket."""
        # Must be different sockets
        if target == self:
            return False

        # Must be input socket (we are output)
        if target.is_output:
            return False

        # Type must match
        if target.socket_type != self.socket_type:
            return False

        # Can't connect to same node
        return target.parentItem() != self.parentItem()

    def update_connections(self):
        """Update all connection paths (called when node moves)."""
        for conn in self.connections:
            conn.update_path()


class NodeItem(QGraphicsItem):
    """
    Visual representation of an action as a node.

    Layout:
    ┌─────────────────────────────┐
    │ [Icon] Action Name        ▶ │ ← Header
    ├─────────────────────────────┤
    │ ◀ Input 1                   │
    │ ◀ Input 2                   │
    ├─────────────────────────────┤
    │                   Output ▶  │
    └─────────────────────────────┘
    """

    def __init__(self, action: Action, x: float = 0, y: float = 0):
        super().__init__()

        self.action = action
        self.action_type = type(action).__name__

        # Visual settings
        self.width = 200
        self.header_height = 30
        self.socket_spacing = 25
        self.padding = 10

        # Color
        self.color = NODE_COLORS.get(self.action_type, DEFAULT_NODE_COLOR)

        # Flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        # Position
        self.setPos(x, y)

        # Create sockets
        self.input_sockets = []
        self.output_sockets = []
        self._create_sockets()

        # Connections (all connections attached to this node)
        self.connections = []

        # Cache
        self._height = None

    def _create_sockets(self):
        """Create input/output sockets based on action type."""
        # Every action has exec in/out
        exec_in = SocketItem(SocketType.EXEC, "exec_in", False, self)
        exec_in.setPos(0, self.header_height / 2)
        self.input_sockets.append(exec_in)

        exec_out = SocketItem(SocketType.EXEC, "exec_out", True, self)
        exec_out.setPos(self.width, self.header_height / 2)
        self.output_sockets.append(exec_out)

        # TODO: Add data sockets based on action type
        # For now, just exec flow

    def boundingRect(self) -> QRectF:
        """Return bounding rectangle."""
        return QRectF(0, 0, self.width, self._get_height())

    def _get_height(self) -> float:
        """Calculate node height."""
        if self._height is None:
            # Header + body + padding
            body_height = max(
                len(self.input_sockets) * self.socket_spacing,
                len(self.output_sockets) * self.socket_spacing,
                50,  # Minimum body height
            )
            self._height = self.header_height + body_height + self.padding
        return self._height

    def paint(self, painter: QPainter, option, widget=None):
        """Paint the node."""
        height = self._get_height()

        # Selection outline
        if self.isSelected():
            painter.setPen(QPen(QColor(255, 255, 100), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(-2, -2, self.width + 4, height + 4, 7, 7)

        # Node body shadow
        shadow_offset = 3
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
        painter.drawRoundedRect(shadow_offset, shadow_offset, self.width, height, 5, 5)

        # Node body background
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.setBrush(QBrush(QColor(45, 45, 45)))
        painter.drawRoundedRect(0, 0, self.width, height, 5, 5)

        # Header background (gradient)
        header_gradient = QLinearGradient(0, 0, 0, self.header_height)
        header_gradient.setColorAt(0, self.color)
        header_gradient.setColorAt(1, self.color.darker(120))

        painter.setBrush(QBrush(header_gradient))
        painter.setPen(Qt.PenStyle.NoPen)

        # Draw header with rounded top corners
        header_path = QPainterPath()
        header_path.moveTo(0, self.header_height)
        header_path.lineTo(0, 5)
        header_path.arcTo(0, 0, 10, 10, 180, -90)
        header_path.lineTo(self.width - 5, 0)
        header_path.arcTo(self.width - 10, 0, 10, 10, 90, -90)
        header_path.lineTo(self.width, self.header_height)
        header_path.closeSubpath()
        painter.drawPath(header_path)

        # Header text
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)

        # Get action display name
        display_name = self._get_display_name()

        # Draw text centered in header
        text_rect = QRectF(self.padding, 0, self.width - 2 * self.padding, self.header_height)
        painter.drawText(
            text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, display_name
        )

        # Body separator line
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawLine(0, self.header_height, self.width, self.header_height)

    def _get_display_name(self) -> str:
        """Get display name for the action."""
        # Map action types to friendly names
        names = {
            "ClickImage": "Click Image",
            "WaitImage": "Wait Image",
            "IfImage": "If Image",
            "IfText": "If Text",
            "ReadText": "Read Text",
            "Delay": "Delay",
            "Hotkey": "Hotkey",
            "TypeText": "Type Text",
            "Loop": "Loop",
            "RunFlow": "Run Flow",
        }
        return names.get(self.action_type, self.action_type)

    def itemChange(self, change, value):
        """Handle item changes (for connection updates)."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update all socket connections
            for socket in self.input_sockets + self.output_sockets:
                socket.update_connections()
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.update()

    def hoverLeaveEvent(self, event):
        """Remove highlight."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)
