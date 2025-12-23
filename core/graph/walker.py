"""
RetroAuto v2 - Graph Execution Walker

Phase 5: Execution Engine
- Traverse graph following exec connections
- Handle branching (IfImage true/false paths)
- Maintain execution order
"""

from collections.abc import Callable
from typing import Any

from core.models import Action, FlowGraph, GraphConnection, GraphNode
from infra import get_logger

logger = get_logger("GraphWalker")


class GraphWalker:
    """
    Walks through a flow graph and executes nodes in order.

    Follows execution flow connections (exec_out -> exec_in).
    Supports branching via conditional nodes.
    """

    def __init__(self, graph: FlowGraph):
        self.graph = graph

        # Build lookup maps
        self.node_map = {node.id: node for node in graph.nodes}

        # Build adjacency map (outgoing connections from each node)
        self.outgoing: dict[str, list[GraphConnection]] = {node.id: [] for node in graph.nodes}
        for conn in graph.connections:
            if conn.from_node in self.outgoing:
                self.outgoing[conn.from_node].append(conn)

        # Track visited nodes (for loop detection)
        self.visited = set()
        self.execution_count = {}  # Track how many times each node executed

    def find_start_node(self) -> GraphNode | None:
        """
        Find the start node (node with no incoming exec connections).
        """
        # Count incoming exec connections
        incoming_counts = {node.id: 0 for node in self.graph.nodes}

        for conn in self.graph.connections:
            if conn.to_socket == "exec_in":  # Only count exec flow
                incoming_counts[conn.to_node] += 1

        # Find nodes with no incoming connections
        start_candidates = [nid for nid, count in incoming_counts.items() if count == 0]

        if not start_candidates:
            logger.warning("No clear start node found in graph")
            return None

        if len(start_candidates) > 1:
            # Multiple start nodes - pick the topmost one
            logger.warning(f"Multiple start nodes found ({len(start_candidates)}), using topmost")
            start_candidates.sort(key=lambda nid: self.node_map[nid].y)

        return self.node_map[start_candidates[0]]

    def get_next_node(self, current_id: str, branch_result: Any = None) -> GraphNode | None:
        """
        Get the next node to execute based on current node's output connections.

        For regular nodes: follows 'exec_out' connection
        For conditional nodes (IfImage, IfText): follows 'true_out' or 'false_out' based on result

        Args:
            current_id: Current node ID
            branch_result: Result of conditional check (True/False) for branching nodes
        """
        connections = self.outgoing.get(current_id, [])

        # Filter to exec flow connections
        exec_connections = [
            c for c in connections if c.from_socket in ("exec_out", "true_out", "false_out")
        ]

        if not exec_connections:
            return None  # End of flow

        # Handle branching
        if branch_result is not None:
            # This is a conditional node
            target_socket = "true_out" if branch_result else "false_out"
            for conn in exec_connections:
                if conn.from_socket == target_socket:
                    return self.node_map.get(conn.to_node)

            logger.warning(f"No {target_socket} connection found for node {current_id}")
            return None

        # Regular flow - just take the first exec connection
        if len(exec_connections) > 1:
            logger.warning(f"Multiple exec outputs from node {current_id}, taking first")

        conn = exec_connections[0]
        return self.node_map.get(conn.to_node)

    def execute_graph(self, action_executor: Callable[[Action], Any], max_iterations: int = 10000):
        """
        Execute the entire graph.

        Args:
            action_executor: Function that executes an action and returns result
            max_iterations: Safety limit to prevent infinite loops
        """
        start_node = self.find_start_node()

        if not start_node:
            logger.error("Cannot execute graph: no start node found")
            return

        current_node = start_node
        iteration_count = 0

        while current_node and iteration_count < max_iterations:
            iteration_count += 1

            # Track execution
            self.execution_count[current_node.id] = self.execution_count.get(current_node.id, 0) + 1

            # Detect infinite loops (node executed too many times)
            if self.execution_count[current_node.id] > 1000:
                logger.error(f"Infinite loop detected at node {current_node.id}")
                break

            logger.debug(f"Executing node {current_node.id}: {type(current_node.action).__name__}")

            # Execute the action
            try:
                result = action_executor(current_node.action)
            except Exception as e:
                logger.error(f"Error executing node {current_node.id}: {e}")
                break

            # Get next node
            current_node = self.get_next_node(current_node.id, branch_result=result)

        if iteration_count >= max_iterations:
            logger.error("Execution stopped: max iterations reached (possible infinite loop)")

        logger.info(f"Graph execution complete. Executed {iteration_count} nodes.")
