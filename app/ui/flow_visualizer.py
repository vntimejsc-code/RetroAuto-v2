"""
RetroAuto v2 - Flow Visualizer

Visual diagram display for RetroScript flows.
Part of RetroScript Phase 14 - Visual Editor Components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import QPointF, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QVBoxLayout,
    QWidget,
)


@dataclass
class FlowNode:
    """A node in the flow diagram."""

    id: str
    label: str
    node_type: str = "default"  # default, start, end, condition, action
    x: float = 0
    y: float = 0
    width: float = 120
    height: float = 40
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowConnection:
    """A connection between nodes."""

    from_node: str
    to_node: str
    label: str = ""
    connection_type: str = "default"  # default, true, false


class NodeItem(QGraphicsRectItem):
    """Visual representation of a flow node."""

    def __init__(self, node: FlowNode, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.node = node

        # Setup rect
        self.setRect(0, 0, node.width, node.height)
        self.setPos(node.x, node.y)

        # Make interactive
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setAcceptHoverEvents(True)

        # Style based on type
        self._setup_style()

        # Add label
        self._label = QGraphicsSimpleTextItem(node.label, self)
        self._label.setFont(QFont("Segoe UI", 10))
        self._center_label()

    def _setup_style(self) -> None:
        """Setup visual style based on node type."""
        colors = {
            "default": ("#2d3748", "#4a5568"),
            "start": ("#22543d", "#38a169"),
            "end": ("#742a2a", "#e53e3e"),
            "condition": ("#744210", "#dd6b20"),
            "action": ("#2c5282", "#4299e1"),
            "loop": ("#553c9a", "#805ad5"),
        }

        fill, border = colors.get(self.node.node_type, colors["default"])

        self.setBrush(QBrush(QColor(fill)))
        self.setPen(QPen(QColor(border), 2))

    def _center_label(self) -> None:
        """Center the label in the node."""
        rect = self._label.boundingRect()
        x = (self.node.width - rect.width()) / 2
        y = (self.node.height - rect.height()) / 2
        self._label.setPos(x, y)
        self._label.setBrush(QColor("#ffffff"))

    def hoverEnterEvent(self, event) -> None:
        """Handle hover enter."""
        self.setPen(QPen(QColor("#63b3ed"), 3))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """Handle hover leave."""
        self._setup_style()
        super().hoverLeaveEvent(event)


class ConnectionItem(QGraphicsPathItem):
    """Visual representation of a connection."""

    def __init__(
        self,
        from_item: NodeItem,
        to_item: NodeItem,
        connection: FlowConnection,
        parent: QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self.from_item = from_item
        self.to_item = to_item
        self.connection = connection

        # Style
        color = "#718096"
        if connection.connection_type == "true":
            color = "#38a169"
        elif connection.connection_type == "false":
            color = "#e53e3e"

        self.setPen(QPen(QColor(color), 2))

        # Create path
        self._update_path()

    def _update_path(self) -> None:
        """Update the connection path."""
        # Get node centers
        from_rect = self.from_item.sceneBoundingRect()
        to_rect = self.to_item.sceneBoundingRect()

        # Start from bottom of from_node
        start = QPointF(
            from_rect.center().x(),
            from_rect.bottom(),
        )

        # End at top of to_node
        end = QPointF(
            to_rect.center().x(),
            to_rect.top(),
        )

        # Create curved path
        path = QPainterPath()
        path.moveTo(start)

        # Control points for bezier curve
        mid_y = (start.y() + end.y()) / 2
        ctrl1 = QPointF(start.x(), mid_y)
        ctrl2 = QPointF(end.x(), mid_y)

        path.cubicTo(ctrl1, ctrl2, end)

        self.setPath(path)

        # Add arrow head
        self._add_arrow(end)

    def _add_arrow(self, tip: QPointF) -> None:
        """Add arrow head at the tip."""
        # Arrow is drawn as part of the scene separately
        pass


class FlowDiagram(QGraphicsView):
    """Flow diagram viewer.

    Usage:
        diagram = FlowDiagram()
        diagram.add_node(FlowNode("start", "Start", "start"))
        diagram.add_node(FlowNode("action1", "Click Button", "action"))
        diagram.connect("start", "action1")
    """

    node_selected = Signal(str)  # node id
    node_double_clicked = Signal(str)  # node id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Create scene
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Settings
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setBackgroundBrush(QColor("#1a202c"))

        # Node storage
        self._nodes: dict[str, NodeItem] = {}
        self._connections: list[ConnectionItem] = []

    def add_node(self, node: FlowNode) -> NodeItem:
        """Add a node to the diagram."""
        item = NodeItem(node)
        self._scene.addItem(item)
        self._nodes[node.id] = item
        return item

    def remove_node(self, node_id: str) -> None:
        """Remove a node from the diagram."""
        if node_id in self._nodes:
            item = self._nodes.pop(node_id)
            self._scene.removeItem(item)

    def connect(
        self,
        from_id: str,
        to_id: str,
        label: str = "",
        connection_type: str = "default",
    ) -> ConnectionItem | None:
        """Connect two nodes."""
        if from_id not in self._nodes or to_id not in self._nodes:
            return None

        connection = FlowConnection(from_id, to_id, label, connection_type)
        item = ConnectionItem(
            self._nodes[from_id],
            self._nodes[to_id],
            connection,
        )
        self._scene.addItem(item)
        self._connections.append(item)
        return item

    def clear(self) -> None:
        """Clear all nodes and connections."""
        self._scene.clear()
        self._nodes.clear()
        self._connections.clear()

    def auto_layout(self) -> None:
        """Auto-layout nodes in a tree structure."""
        if not self._nodes:
            return

        # Simple vertical layout
        x = 50
        y = 50
        spacing_y = 80

        for _node_id, item in self._nodes.items():
            item.setPos(x, y)
            y += spacing_y

        # Update connections
        for conn in self._connections:
            conn._update_path()

    def from_ast(self, flows: list[Any]) -> None:
        """Build diagram from AST flows.

        Args:
            flows: List of FlowDecl AST nodes
        """
        self.clear()
        y = 50

        for flow in flows:
            # Add flow start node
            start_node = FlowNode(
                id=f"{flow.name}_start",
                label=f"flow {flow.name}",
                node_type="start",
                x=50,
                y=y,
            )
            self.add_node(start_node)
            y += 80

            # Add end node
            end_node = FlowNode(
                id=f"{flow.name}_end",
                label="end",
                node_type="end",
                x=50,
                y=y,
            )
            self.add_node(end_node)

            # Connect
            self.connect(start_node.id, end_node.id)
            y += 100

    def wheelEvent(self, event) -> None:
        """Handle zoom with mouse wheel."""
        factor = 1.15

        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1 / factor, 1 / factor)


class FlowVisualizer(QWidget):
    """Complete flow visualizer widget.

    Usage:
        viz = FlowVisualizer()
        viz.load_from_source(source_code)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.diagram = FlowDiagram()
        layout.addWidget(self.diagram)

    def load_from_source(self, source: str) -> None:
        """Load diagram from RetroScript source."""
        try:
            from core.dsl.parser import Parser

            parser = Parser(source)
            program = parser.parse()

            if program.flows:
                self.diagram.from_ast(program.flows)

        except Exception as e:
            print(f"Error parsing source: {e}")

    def add_sample(self) -> None:
        """Add a sample diagram for testing."""
        self.diagram.add_node(FlowNode("start", "Start", "start", 100, 50))
        self.diagram.add_node(FlowNode("find", "find(button)", "action", 100, 150))
        self.diagram.add_node(FlowNode("check", "if found?", "condition", 100, 250))
        self.diagram.add_node(FlowNode("click", "click(x, y)", "action", 50, 350))
        self.diagram.add_node(FlowNode("wait", "sleep(1s)", "action", 200, 350))
        self.diagram.add_node(FlowNode("end", "End", "end", 100, 450))

        self.diagram.connect("start", "find")
        self.diagram.connect("find", "check")
        self.diagram.connect("check", "click", "yes", "true")
        self.diagram.connect("check", "wait", "no", "false")
        self.diagram.connect("click", "end")
        self.diagram.connect("wait", "end")
