"""
RetroAuto v2 - Graph Conversion Utilities

Phase 4: Data Model Migration
- Convert list <-> graph
- Auto-layout for list-to-graph conversion
- UUID generation
"""

import uuid
from core.models import Flow, FlowGraph, GraphNode, GraphConnection, Action

from infra import get_logger

logger = get_logger("GraphConverter")


def list_to_graph(actions: list[Action]) -> FlowGraph:
    """
    Convert a linear action list to a graph structure.
    
    Uses auto-layout to position nodes in a vertical flow.
    """
    nodes = []
    connections = []
    
    # Auto-layout settings
    start_x = 0
    start_y = 0
    spacing_y = 100
    
    node_ids = []
    
    # Create nodes
    for i, action in enumerate(actions):
        node_id = str(uuid.uuid4())
        node = GraphNode(
            id=node_id,
            action=action,
            x=start_x,
            y=start_y + (i * spacing_y)
        )
        nodes.append(node)
        node_ids.append(node_id)
    
    # Create linear connections (each node to next)
    for i in range(len(node_ids) - 1):
        connection = GraphConnection(
            from_node=node_ids[i],
            from_socket="exec_out",
            to_node=node_ids[i + 1],
            to_socket="exec_in"
        )
        connections.append(connection)
    
    return FlowGraph(nodes=nodes, connections=connections)


def graph_to_list(graph: FlowGraph) -> list[Action]:
    """
    Convert a graph to a linear action list.
    
    Performs topological sort to determine execution order.
    For simple linear graphs, this is straightforward.
    For complex graphs with branches, uses depth-first traversal.
    """
    if not graph.nodes:
        return []
    
    # Build adjacency map
    node_map = {node.id: node for node in graph.nodes}
    outgoing = {node.id: [] for node in graph.nodes}
    
    for conn in graph.connections:
        if conn.from_socket == "exec_out":  # Only follow exec flow
            outgoing[conn.from_node].append(conn.to_node)
    
    # Find start node (node with no incoming exec connections)
    incoming_counts = {node.id: 0 for node in graph.nodes}
    for conn in graph.connections:
        if conn.from_socket == "exec_out":
            incoming_counts[conn.to_node] += 1
    
    start_nodes = [nid for nid, count in incoming_counts.items() if count == 0]
    
    if not start_nodes:
        # Fallback: use first node by position
        logger.warning("No clear start node found, using topmost node")
        start_nodes = [min(graph.nodes, key=lambda n: n.y).id]
    
    # DFS traversal
    visited = set()
    result = []
    
    def visit(node_id: str):
        if node_id in visited:
            return
        visited.add(node_id)
        
        # Add this node's action
        if node_id in node_map:
            result.append(node_map[node_id].action)
        
        # Visit children
        for child_id in outgoing.get(node_id, []):
            visit(child_id)
    
    # Start from each start node
    for start_id in start_nodes:
        visit(start_id)
    
    return result


def auto_layout_graph(graph: FlowGraph, algorithm: str = "vertical") -> FlowGraph:
    """
    Auto-arrange nodes in the graph.
    
    Algorithms:
    - vertical: Simple top-to-bottom flow
    - hierarchical: Layered layout (future)
    """
    if algorithm == "vertical":
        # Simple vertical layout
        spacing = 100
        for i, node in enumerate(graph.nodes):
            node.x = 0
            node.y = i * spacing
    
    return graph


def generate_node_id() -> str:
    """Generate a unique node ID."""
    return str(uuid.uuid4())
