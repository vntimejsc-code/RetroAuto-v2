"""
RetroAuto v2 - Visual Flow Editor

Node-based visual scripting editor using Qt Graphics Framework.
Inspired by Unreal Blueprints and node-based editors.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsView,
    QStyleOptionGraphicsItem,
    QWidget,
)

from infra import get_logger

logger = get_logger("FlowEditor")


# ─────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────


@dataclass
class Pin:
    """A connection point on a node."""
    
    name: str
    pin_type: str  # "exec_in", "exec_out", "data_in", "data_out"
    data_type: str = "any"  # "exec", "bool", "string", "asset", etc.
    value: Any = None


@dataclass
class NodeData:
    """Data model for a visual node."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    node_type: str = "Action"
    title: str = "Node"
    x: float = 0.0
    y: float = 0.0
    inputs: list[Pin] = field(default_factory=list)
    outputs: list[Pin] = field(default_factory=list)
    properties: dict = field(default_factory=dict)


@dataclass
class ConnectionData:
    """Data model for a wire connection."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    from_node: str = ""
    from_pin: str = ""
    to_node: str = ""
    to_pin: str = ""


# ─────────────────────────────────────────────────────────────
# Node Colors by Category
# ─────────────────────────────────────────────────────────────

NODE_COLORS = {
    "Start": "#4CAF50",      # Green
    "Click": "#2196F3",      # Blue
    "Wait": "#03A9F4",       # Light Blue
    "If": "#FF9800",         # Orange
    "Loop": "#9C27B0",       # Purple
    "End": "#F44336",        # Red
    "Default": "#607D8B",    # Gray
}


# ─────────────────────────────────────────────────────────────
# Socket (Pin) Item
# ─────────────────────────────────────────────────────────────


class SocketItem(QGraphicsItem):
    """A connection socket/pin on a node."""
    
    RADIUS = 6
    
    def __init__(
        self, 
        pin: Pin, 
        is_output: bool,
        parent: "NodeItem"
    ) -> None:
        super().__init__(parent)
        self.pin = pin
        self.is_output = is_output
        self.setAcceptHoverEvents(True)
        self._hovered = False
        
        # Color based on pin type
        if pin.pin_type.startswith("exec"):
            self._color = QColor("#FFFFFF")
        else:
            self._color = QColor("#00BFFF")
    
    def boundingRect(self) -> QRectF:
        return QRectF(
            -self.RADIUS - 2, 
            -self.RADIUS - 2,
            (self.RADIUS + 2) * 2,
            (self.RADIUS + 2) * 2
        )
    
    def paint(
        self, 
        painter: QPainter, 
        option: QStyleOptionGraphicsItem, 
        widget: QWidget | None = None
    ) -> None:
        # Draw socket
        if self.pin.pin_type.startswith("exec"):
            # Triangle for exec
            path = QPainterPath()
            if self.is_output:
                path.moveTo(-self.RADIUS, -self.RADIUS)
                path.lineTo(self.RADIUS, 0)
                path.lineTo(-self.RADIUS, self.RADIUS)
            else:
                path.moveTo(self.RADIUS, -self.RADIUS)
                path.lineTo(-self.RADIUS, 0)
                path.lineTo(self.RADIUS, self.RADIUS)
            path.closeSubpath()
            
            painter.setPen(QPen(Qt.GlobalColor.white, 1))
            painter.setBrush(QBrush(self._color if self._hovered else QColor("#808080")))
            painter.drawPath(path)
        else:
            # Circle for data
            painter.setPen(QPen(Qt.GlobalColor.white, 1))
            painter.setBrush(QBrush(self._color if self._hovered else QColor("#404040")))
            painter.drawEllipse(QPointF(0, 0), self.RADIUS, self.RADIUS)
        
        # Draw label
        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.white)
        
        if self.is_output:
            painter.drawText(
                QRectF(-80, -10, 70, 20),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                self.pin.name
            )
        else:
            painter.drawText(
                QRectF(12, -10, 70, 20),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                self.pin.name
            )
    
    def hoverEnterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        
    def hoverLeaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
    
    def get_center_scene_pos(self) -> QPointF:
        """Get socket center in scene coordinates."""
        return self.scenePos()
    
    def mousePressEvent(self, event) -> None:
        """Start dragging a connection from this socket."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_output:
            scene = self.scene()
            if scene and hasattr(scene, "start_connection"):
                scene.start_connection(self)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        """End dragging a connection."""
        if event.button() == Qt.MouseButton.LeftButton:
            scene = self.scene()
            if scene and hasattr(scene, "end_connection"):
                scene.end_connection(self)
            event.accept()
        else:
            super().mouseReleaseEvent(event)


# ─────────────────────────────────────────────────────────────
# Node Item
# ─────────────────────────────────────────────────────────────


class NodeItem(QGraphicsItem):
    """A visual node in the flow editor."""
    
    WIDTH = 160
    HEADER_HEIGHT = 28
    PIN_SPACING = 24
    CORNER_RADIUS = 8
    
    def __init__(self, data: NodeData, parent=None) -> None:
        super().__init__(parent)
        self.data = data
        self.input_sockets: list[SocketItem] = []
        self.output_sockets: list[SocketItem] = []
        
        # Flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Set position
        self.setPos(data.x, data.y)
        
        # Calculate height
        max_pins = max(len(data.inputs), len(data.outputs), 1)
        self._height = self.HEADER_HEIGHT + max_pins * self.PIN_SPACING + 8
        
        # Get color
        category = data.node_type.split("_")[0] if "_" in data.node_type else data.node_type
        self._header_color = QColor(NODE_COLORS.get(category, NODE_COLORS["Default"]))
        
        # Create sockets
        self._create_sockets()
    
    def _create_sockets(self) -> None:
        """Create socket items for inputs and outputs."""
        # Input sockets (left side)
        for i, pin in enumerate(self.data.inputs):
            socket = SocketItem(pin, is_output=False, parent=self)
            socket.setPos(0, self.HEADER_HEIGHT + 12 + i * self.PIN_SPACING)
            self.input_sockets.append(socket)
        
        # Output sockets (right side)
        for i, pin in enumerate(self.data.outputs):
            socket = SocketItem(pin, is_output=True, parent=self)
            socket.setPos(self.WIDTH, self.HEADER_HEIGHT + 12 + i * self.PIN_SPACING)
            self.output_sockets.append(socket)
    
    def boundingRect(self) -> QRectF:
        return QRectF(-2, -2, self.WIDTH + 4, self._height + 4)
    
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None
    ) -> None:
        # Body
        body_rect = QRectF(0, 0, self.WIDTH, self._height)
        
        # Shadow
        shadow_rect = body_rect.translated(3, 3)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 80))
        painter.drawRoundedRect(shadow_rect, self.CORNER_RADIUS, self.CORNER_RADIUS)
        
        # Main body
        painter.setBrush(QColor("#2d2d2d"))
        if self.isSelected():
            painter.setPen(QPen(QColor("#00aaff"), 2))
        else:
            painter.setPen(QPen(QColor("#555555"), 1))
        painter.drawRoundedRect(body_rect, self.CORNER_RADIUS, self.CORNER_RADIUS)
        
        # Header
        header_rect = QRectF(0, 0, self.WIDTH, self.HEADER_HEIGHT)
        path = QPainterPath()
        path.addRoundedRect(header_rect, self.CORNER_RADIUS, self.CORNER_RADIUS)
        # Clip bottom corners
        path.addRect(QRectF(0, self.HEADER_HEIGHT - self.CORNER_RADIUS, 
                           self.WIDTH, self.CORNER_RADIUS))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._header_color)
        painter.drawPath(path.simplified())
        
        # Title
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(
            header_rect.adjusted(8, 0, -8, 0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self.data.title
        )
    
    def itemChange(self, change, value):
        """Track position changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update data
            pos = self.pos()
            self.data.x = pos.x()
            self.data.y = pos.y()
            # Notify connections to update
            scene = self.scene()
            if scene and hasattr(scene, "update_connections"):
                scene.update_connections(self)
        return super().itemChange(change, value)


# ─────────────────────────────────────────────────────────────
# Connection Item (Wire)
# ─────────────────────────────────────────────────────────────


class ConnectionItem(QGraphicsPathItem):
    """A wire connecting two sockets."""
    
    def __init__(
        self,
        data: ConnectionData,
        start_socket: SocketItem | None = None,
        end_socket: SocketItem | None = None,
        parent=None
    ) -> None:
        super().__init__(parent)
        self.data = data
        self.start_socket = start_socket
        self.end_socket = end_socket
        
        # Styling
        self._pen = QPen(QColor("#cccccc"), 2)
        self._pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(self._pen)
        
        self.setZValue(-1)  # Behind nodes
        self.update_path()
    
    def update_path(self) -> None:
        """Update the bezier curve path."""
        if not self.start_socket or not self.end_socket:
            return
        
        start = self.start_socket.get_center_scene_pos()
        end = self.end_socket.get_center_scene_pos()
        
        # Bezier control points
        dx = abs(end.x() - start.x()) * 0.5
        
        path = QPainterPath(start)
        path.cubicTo(
            QPointF(start.x() + dx, start.y()),
            QPointF(end.x() - dx, end.y()),
            end
        )
        
        self.setPath(path)


# ─────────────────────────────────────────────────────────────
# Flow Scene
# ─────────────────────────────────────────────────────────────


class FlowScene(QGraphicsScene):
    """Scene containing the node graph."""
    
    node_selected = Signal(NodeData)
    node_added = Signal(NodeData)
    connection_made = Signal(ConnectionData)
    
    GRID_SIZE = 20
    GRID_COLOR_SMALL = QColor("#353535")
    GRID_COLOR_LARGE = QColor("#454545")
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.nodes: dict[str, NodeItem] = {}
        self.connections: list[ConnectionItem] = []
        
        # Large scene rect
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self.setBackgroundBrush(QColor("#1e1e1e"))
    
    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Draw grid background."""
        super().drawBackground(painter, rect)
        
        left = int(rect.left()) - (int(rect.left()) % self.GRID_SIZE)
        top = int(rect.top()) - (int(rect.top()) % self.GRID_SIZE)
        
        # Small grid
        lines_small = []
        x = left
        while x < rect.right():
            if x % (self.GRID_SIZE * 5) != 0:
                lines_small.append((x, rect.top(), x, rect.bottom()))
            x += self.GRID_SIZE
        
        y = top
        while y < rect.bottom():
            if y % (self.GRID_SIZE * 5) != 0:
                lines_small.append((rect.left(), y, rect.right(), y))
            y += self.GRID_SIZE
        
        painter.setPen(QPen(self.GRID_COLOR_SMALL, 0.5))
        for line in lines_small:
            painter.drawLine(int(line[0]), int(line[1]), int(line[2]), int(line[3]))
        
        # Large grid
        lines_large = []
        x = left
        while x < rect.right():
            if x % (self.GRID_SIZE * 5) == 0:
                lines_large.append((x, rect.top(), x, rect.bottom()))
            x += self.GRID_SIZE
        
        y = top
        while y < rect.bottom():
            if y % (self.GRID_SIZE * 5) == 0:
                lines_large.append((rect.left(), y, rect.right(), y))
            y += self.GRID_SIZE
        
        painter.setPen(QPen(self.GRID_COLOR_LARGE, 1))
        for line in lines_large:
            painter.drawLine(int(line[0]), int(line[1]), int(line[2]), int(line[3]))
    
    def add_node(self, data: NodeData) -> NodeItem:
        """Add a node to the scene."""
        node = NodeItem(data)
        self.addItem(node)
        self.nodes[data.id] = node
        logger.info(f"Added node: {data.title} ({data.id})")
        return node
    
    def remove_node(self, node_id: str) -> None:
        """Remove a node from the scene."""
        if node_id in self.nodes:
            node = self.nodes.pop(node_id)
            self.removeItem(node)
    
    def update_connections(self, node: NodeItem) -> None:
        """Update all connections involving this node."""
        for conn in self.connections:
            if conn.start_socket and conn.start_socket.parentItem() == node:
                conn.update_path()
            if conn.end_socket and conn.end_socket.parentItem() == node:
                conn.update_path()
    
    def start_connection(self, socket: SocketItem) -> None:
        """Start dragging a new connection from a socket."""
        self._dragging_connection = True
        self._drag_start_socket = socket
        
        # Create temporary connection for preview
        self._temp_connection = ConnectionItem(
            ConnectionData(),
            start_socket=socket,
            end_socket=None
        )
        self.addItem(self._temp_connection)
        logger.info(f"Started connection from {socket.pin.name}")
    
    def end_connection(self, socket: SocketItem) -> None:
        """Complete connection to a socket."""
        if not hasattr(self, "_dragging_connection") or not self._dragging_connection:
            return
        
        self._dragging_connection = False
        
        # Remove temp connection
        if hasattr(self, "_temp_connection") and self._temp_connection:
            self.removeItem(self._temp_connection)
            self._temp_connection = None
        
        # Validate connection
        start_socket = self._drag_start_socket
        if not start_socket or socket == start_socket:
            return
        
        # Check compatible: output -> input
        if start_socket.is_output and not socket.is_output:
            self.add_connection(start_socket, socket)
        elif not start_socket.is_output and socket.is_output:
            self.add_connection(socket, start_socket)
    
    def add_connection(
        self, 
        from_socket: SocketItem, 
        to_socket: SocketItem
    ) -> ConnectionItem | None:
        """Create a connection between two sockets."""
        # Get parent nodes
        from_node = from_socket.parentItem()
        to_node = to_socket.parentItem()
        
        if not isinstance(from_node, NodeItem) or not isinstance(to_node, NodeItem):
            return None
        
        # Create connection data
        data = ConnectionData(
            from_node=from_node.data.id,
            from_pin=from_socket.pin.name,
            to_node=to_node.data.id,
            to_pin=to_socket.pin.name
        )
        
        # Create connection item
        conn = ConnectionItem(data, from_socket, to_socket)
        self.addItem(conn)
        self.connections.append(conn)
        
        logger.info(f"Connected {from_node.data.title}.{from_socket.pin.name} -> {to_node.data.title}.{to_socket.pin.name}")
        return conn
    
    def cancel_connection(self) -> None:
        """Cancel the in-progress connection drag."""
        if hasattr(self, "_temp_connection") and self._temp_connection:
            self.removeItem(self._temp_connection)
            self._temp_connection = None
        self._dragging_connection = False


# ─────────────────────────────────────────────────────────────
# Flow View
# ─────────────────────────────────────────────────────────────


class FlowView(QGraphicsView):
    """View widget for the flow editor with pan and zoom."""
    
    def __init__(self, scene: FlowScene, parent=None) -> None:
        super().__init__(scene, parent)
        self.flow_scene = scene
        
        # Settings
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        # Zoom
        self._zoom = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 3.0
        
        # Pan
        self._panning = False
        self._pan_start = QPointF()
        
        # Style
        self.setStyleSheet("""
            QGraphicsView {
                border: 1px solid #3c3c3c;
                background-color: #1e1e1e;
            }
        """)
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Zoom with mouse wheel."""
        factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        new_zoom = self._zoom * factor
        
        if self._min_zoom <= new_zoom <= self._max_zoom:
            self._zoom = new_zoom
            self.scale(factor, factor)
    
    def mousePressEvent(self, event) -> None:
        """Handle pan start."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle panning."""
        if self._panning:
            delta = self._pan_start - event.position()
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                int(self.horizontalScrollBar().value() + delta.x())
            )
            self.verticalScrollBar().setValue(
                int(self.verticalScrollBar().value() + delta.y())
            )
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle pan end."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)
    
    def fit_in_view_all(self) -> None:
        """Fit all nodes in view."""
        items_rect = self.scene().itemsBoundingRect()
        if not items_rect.isEmpty():
            self.fitInView(items_rect.adjusted(-50, -50, 50, 50), 
                          Qt.AspectRatioMode.KeepAspectRatio)


# ─────────────────────────────────────────────────────────────
# Flow Editor Widget (Main Panel)
# ─────────────────────────────────────────────────────────────


class FlowEditorWidget(QWidget):
    """Main widget containing the flow editor."""
    
    # Signal to export actions
    actions_exported = Signal(list)  # list[Action]
    
    def __init__(self, parent=None, actions: list = None) -> None:
        super().__init__(parent)
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel
        
        self._initial_actions = actions or []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(4, 4, 4, 4)
        
        add_btn = QPushButton("+ Add Node")
        add_btn.clicked.connect(self._on_add_node)
        toolbar.addWidget(add_btn)
        
        fit_btn = QPushButton("📐 Fit All")
        fit_btn.clicked.connect(self._on_fit_all)
        toolbar.addWidget(fit_btn)
        
        toolbar.addWidget(QLabel(" | "))
        
        import_btn = QPushButton("📥 Import Actions")
        import_btn.clicked.connect(self._on_import_actions)
        toolbar.addWidget(import_btn)
        
        export_btn = QPushButton("📤 Export Actions")
        export_btn.clicked.connect(self._on_export_actions)
        toolbar.addWidget(export_btn)
        
        toolbar.addStretch()
        
        zoom_label = QLabel("🔍 Zoom: 100%")
        self._zoom_label = zoom_label
        toolbar.addWidget(zoom_label)
        
        layout.addLayout(toolbar)
        
        # Flow editor
        self.scene = FlowScene()
        self.view = FlowView(self.scene)
        layout.addWidget(self.view)
        
        # Load initial actions or demo
        if self._initial_actions:
            self.import_actions(self._initial_actions)
        else:
            self._add_demo_nodes()
    
    def _add_demo_nodes(self) -> None:
        """Add demo nodes to show the editor."""
        # Start node
        start = NodeData(
            node_type="Start",
            title="🚀 Start",
            x=100, y=100,
            outputs=[Pin("Exec", "exec_out", "exec")]
        )
        self.scene.add_node(start)
        
        # Click node
        click = NodeData(
            node_type="Click",
            title="🎯 Click Image",
            x=350, y=100,
            inputs=[
                Pin("Exec", "exec_in", "exec"),
                Pin("Asset", "data_in", "asset"),
            ],
            outputs=[
                Pin("Done", "exec_out", "exec"),
                Pin("Found", "data_out", "bool"),
            ]
        )
        self.scene.add_node(click)
        
        # If node
        if_node = NodeData(
            node_type="If",
            title="❓ If Found",
            x=600, y=100,
            inputs=[
                Pin("Exec", "exec_in", "exec"),
                Pin("Condition", "data_in", "bool"),
            ],
            outputs=[
                Pin("True", "exec_out", "exec"),
                Pin("False", "exec_out", "exec"),
            ]
        )
        self.scene.add_node(if_node)
    
    def _on_add_node(self) -> None:
        """Add a new node at center."""
        center = self.view.mapToScene(self.view.viewport().rect().center())
        node = NodeData(
            node_type="Default",
            title="New Node",
            x=center.x(),
            y=center.y(),
            inputs=[Pin("In", "exec_in", "exec")],
            outputs=[Pin("Out", "exec_out", "exec")]
        )
        self.scene.add_node(node)
    
    def _on_fit_all(self) -> None:
        """Fit all nodes in view."""
        self.view.fit_in_view_all()
    
    def _on_import_actions(self) -> None:
        """Import actions from MainWindow's actions panel."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, 
            "Import Actions",
            "Use import_actions(actions_list) method to import actions programmatically.\n\n"
            "Or connect this Flow Editor to the main window to sync with ActionsPanel."
        )
    
    def _on_export_actions(self) -> None:
        """Export graph back to actions."""
        actions = self.export_actions()
        self.actions_exported.emit(actions)
        
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Export Actions",
            f"Exported {len(actions)} actions.\n\n"
            "Connect to actions_exported signal to receive the actions list."
        )
    
    def import_actions(self, actions: list) -> None:
        """
        Import actions into the flow editor.
        
        Clears current graph and creates nodes from actions.
        """
        from app.ui.flow_converter import flow_converter
        
        # Clear current scene
        for node_id in list(self.scene.nodes.keys()):
            self.scene.remove_node(node_id)
        for conn in list(self.scene.connections):
            self.scene.removeItem(conn)
        self.scene.connections.clear()
        
        # Convert actions to graph
        nodes, connections = flow_converter.actions_to_graph(actions)
        
        # Add nodes
        for node_data in nodes:
            self.scene.add_node(node_data)
        
        # Add connections
        for conn_data in connections:
            from_node = self.scene.nodes.get(conn_data.from_node)
            to_node = self.scene.nodes.get(conn_data.to_node)
            
            if from_node and to_node:
                # Find matching sockets
                from_socket = None
                for sock in from_node.output_sockets:
                    if sock.pin.name == conn_data.from_pin:
                        from_socket = sock
                        break
                # Fallback to first output
                if not from_socket and from_node.output_sockets:
                    from_socket = from_node.output_sockets[0]
                
                to_socket = None
                for sock in to_node.input_sockets:
                    if sock.pin.name == conn_data.to_pin:
                        to_socket = sock
                        break
                # Fallback to first input
                if not to_socket and to_node.input_sockets:
                    to_socket = to_node.input_sockets[0]
                
                if from_socket and to_socket:
                    self.scene.add_connection(from_socket, to_socket)
        
        # Fit view
        self.view.fit_in_view_all()
        logger.info(f"Imported {len(actions)} actions as {len(nodes)} nodes")
    
    def export_actions(self) -> list:
        """
        Export the current graph back to an actions list.
        
        Returns:
            List of Action objects
        """
        from app.ui.flow_converter import flow_converter
        
        # Collect node data
        nodes = [node.data for node in self.scene.nodes.values()]
        
        # Collect connection data  
        connections = [conn.data for conn in self.scene.connections]
        
        # Convert to actions
        actions = flow_converter.graph_to_actions(nodes, connections)
        logger.info(f"Exported {len(nodes)} nodes as {len(actions)} actions")
        return actions
