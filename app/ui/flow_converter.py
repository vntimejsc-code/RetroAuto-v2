"""
RetroAuto v2 - Flow Graph Converter

Converts between Actions list and Visual Graph representation.
Enables bidirectional sync between ActionsPanel and FlowEditor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.models import (
    Action,
    Click,
    ClickImage,
    ClickRandom,
    ClickUntil,
    Delay,
    DelayRandom,
    Else,
    EndIf,
    EndLoop,
    EndWhile,
    Goto,
    Hotkey,
    IfImage,
    IfPixel,
    IfText,
    Label,
    Loop,
    Notify,
    ReadText,
    RunFlow,
    Scroll,
    TypeText,
    WaitImage,
    WaitPixel,
    WhileImage,
)
from infra import get_logger

if TYPE_CHECKING:
    from app.ui.flow_editor import ConnectionData, NodeData

logger = get_logger("FlowConverter")


# ─────────────────────────────────────────────────────────────
# Action to Node Type Mapping
# ─────────────────────────────────────────────────────────────

ACTION_TO_NODE_TYPE = {
    "Click": "Click",
    "ClickImage": "Click",
    "ClickRandom": "Click",
    "ClickUntil": "Click",
    "WaitImage": "Wait",
    "WaitPixel": "Wait",
    "Delay": "Wait",
    "DelayRandom": "Wait",
    "IfImage": "If",
    "IfPixel": "If",
    "IfText": "If",
    "Loop": "Loop",
    "WhileImage": "Loop",
    "Hotkey": "Default",
    "TypeText": "Default",
    "ReadText": "Default",
    "RunFlow": "Default",
    "Goto": "Default",
    "Label": "Default",
    "Notify": "Default",
    "Scroll": "Default",
    "Else": "Default",
    "EndIf": "End",
    "EndLoop": "End",
    "EndWhile": "End",
}

ACTION_ICONS = {
    "Click": "🖱️",
    "ClickImage": "🎯",
    "ClickRandom": "🎲",
    "ClickUntil": "🔄",
    "WaitImage": "👁️",
    "WaitPixel": "⏳",
    "Delay": "⏱️",
    "DelayRandom": "⏳",
    "IfImage": "❓",
    "IfPixel": "❓",
    "IfText": "❓",
    "Loop": "🔁",
    "WhileImage": "🔄",
    "EndIf": "📍",
    "EndLoop": "📍",
    "EndWhile": "📍",
    "Hotkey": "⌨️",
    "TypeText": "📝",
    "ReadText": "📖",
    "RunFlow": "▶️",
    "Goto": "↗️",
    "Label": "🏷️",
    "Notify": "🔔",
    "Scroll": "📜",
    "Else": "🔀",
}


class FlowConverter:
    """
    Converts between Actions list and Visual Graph.

    Actions → Graph: Creates nodes with auto-layout
    Graph → Actions: Traverses connection graph to create linear list
    """

    NODE_WIDTH = 160
    NODE_HEIGHT = 80
    H_SPACING = 80  # Horizontal spacing
    V_SPACING = 40  # Vertical spacing

    def __init__(self) -> None:
        self._node_counter = 0

    # ─────────────────────────────────────────────────────────────
    # Actions → Graph
    # ─────────────────────────────────────────────────────────────

    def actions_to_graph(
        self, actions: list[Action]
    ) -> tuple[list[NodeData], list[ConnectionData]]:
        """
        Convert a list of actions to visual graph nodes.

        Returns:
            Tuple of (nodes, connections)
        """
        from app.ui.flow_editor import ConnectionData, NodeData, Pin

        nodes: list[NodeData] = []
        connections: list[ConnectionData] = []

        if not actions:
            return nodes, connections

        # Add Start node
        start_node = NodeData(
            id="start",
            node_type="Start",
            title="🚀 Start",
            x=50,
            y=100,
            outputs=[Pin("Exec", "exec_out", "exec")],
        )
        nodes.append(start_node)

        # Convert each action to a node
        x_pos = 50 + self.NODE_WIDTH + self.H_SPACING
        y_pos = 100
        prev_node_id = "start"

        for i, action in enumerate(actions):
            action_type = type(action).__name__
            node_type = ACTION_TO_NODE_TYPE.get(action_type, "Default")
            icon = ACTION_ICONS.get(action_type, "📦")

            # Create node
            node = NodeData(
                id=f"action_{i}",
                node_type=node_type,
                title=f"{icon} {action_type}",
                x=x_pos,
                y=y_pos,
                inputs=[Pin("Exec", "exec_in", "exec")],
                outputs=[Pin("Done", "exec_out", "exec")],
                properties=self._action_to_properties(action),
            )

            # Add data pins based on action type
            self._add_action_pins(node, action)

            nodes.append(node)

            # Create connection from previous node
            connections.append(
                ConnectionData(
                    from_node=prev_node_id,
                    from_pin="Exec" if prev_node_id == "start" else "Done",
                    to_node=node.id,
                    to_pin="Exec",
                )
            )

            prev_node_id = node.id

            # Auto-layout: wrap after every 4 nodes
            if (i + 1) % 4 == 0:
                x_pos = 50 + self.NODE_WIDTH + self.H_SPACING
                y_pos += self.NODE_HEIGHT + self.V_SPACING
            else:
                x_pos += self.NODE_WIDTH + self.H_SPACING

        # Add End node
        end_node = NodeData(
            id="end",
            node_type="End",
            title="🏁 End",
            x=x_pos,
            y=y_pos,
            inputs=[Pin("Exec", "exec_in", "exec")],
        )
        nodes.append(end_node)

        # Connect last action to End
        connections.append(
            ConnectionData(from_node=prev_node_id, from_pin="Done", to_node="end", to_pin="Exec")
        )

        logger.info(f"Converted {len(actions)} actions to {len(nodes)} nodes")
        return nodes, connections

    def _action_to_properties(self, action: Action) -> dict:
        """Extract action properties as dict."""
        try:
            return action.model_dump(exclude={"action"})
        except Exception:
            return {}

    def _add_action_pins(self, node: NodeData, action: Action) -> None:
        """Add data pins based on action type."""
        from app.ui.flow_editor import Pin

        action_type = type(action).__name__

        if action_type in ("ClickImage", "WaitImage", "IfImage"):
            node.inputs.append(Pin("Asset", "data_in", "asset"))

        if action_type in ("IfImage", "IfPixel", "IfText"):
            # Replace single output with True/False
            node.outputs = [
                Pin("True", "exec_out", "exec"),
                Pin("False", "exec_out", "exec"),
            ]

        if action_type == "Loop":
            node.inputs.append(Pin("Count", "data_in", "int"))

    # ─────────────────────────────────────────────────────────────
    # Graph → Actions
    # ─────────────────────────────────────────────────────────────

    def graph_to_actions(
        self, nodes: list[NodeData], connections: list[ConnectionData]
    ) -> list[Action]:
        """
        Convert visual graph back to actions list.

        Traverses the graph starting from 'start' node following connections.
        """
        if not nodes:
            return []

        # Build connection map: node_id -> next_node_id
        conn_map: dict[str, str] = {}
        for conn in connections:
            key = f"{conn.from_node}:{conn.from_pin}"
            conn_map[key] = conn.to_node

        # Build node map
        node_map = {node.id: node for node in nodes}

        actions: list[Action] = []

        # Start from 'start' node or first node
        current_id = "start"
        if current_id not in node_map:
            current_id = nodes[0].id if nodes else None

        visited = set()

        while current_id and current_id not in visited:
            visited.add(current_id)

            node = node_map.get(current_id)
            if not node:
                break

            # Skip Start/End nodes
            if node.node_type not in ("Start", "End"):
                action = self._node_to_action(node)
                if action:
                    actions.append(action)

            # Find next node
            next_id = None
            for pin in node.outputs:
                key = f"{current_id}:{pin.name}"
                if key in conn_map:
                    next_id = conn_map[key]
                    break

            current_id = next_id

        logger.info(f"Converted {len(nodes)} nodes to {len(actions)} actions")
        return actions

    def _node_to_action(self, node: NodeData) -> Action | None:
        """Convert a single node back to an action."""
        props = node.properties or {}

        # Extract action type from title (remove icon)
        title_parts = node.title.split(" ", 1)
        action_type = title_parts[1] if len(title_parts) > 1 else node.node_type

        # Map back to action classes
        action_classes = {
            "Click": Click,
            "ClickImage": ClickImage,
            "ClickRandom": ClickRandom,
            "ClickUntil": ClickUntil,
            "WaitImage": WaitImage,
            "WaitPixel": WaitPixel,
            "Delay": Delay,
            "DelayRandom": DelayRandom,
            "IfImage": IfImage,
            "IfPixel": IfPixel,
            "IfText": IfText,
            "Loop": Loop,
            "WhileImage": WhileImage,
            "Hotkey": Hotkey,
            "TypeText": TypeText,
            "ReadText": ReadText,
            "RunFlow": RunFlow,
            "Goto": Goto,
            "Label": Label,
            "Notify": Notify,
            "Scroll": Scroll,
            "Else": Else,
            "EndIf": EndIf,
            "EndLoop": EndLoop,
            "EndWhile": EndWhile,
        }

        action_class = action_classes.get(action_type)
        if not action_class:
            logger.warning(f"Unknown action type: {action_type}")
            return None

        try:
            return action_class(**props)
        except Exception as e:
            logger.warning(f"Failed to create {action_type}: {e}")
            # Try with defaults
            try:
                return action_class()
            except Exception:
                return None


# Global converter instance
flow_converter = FlowConverter()
