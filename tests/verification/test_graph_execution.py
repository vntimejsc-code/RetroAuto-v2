"""
Test graph execution with GraphWalker.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.models import Flow, Delay, ClickImage, WaitImage
from core.graph import list_to_graph
from core.graph.walker import GraphWalker


def test_graph_walker():
    """Test basic graph execution."""
    print("=" * 60)
    print("Graph Execution Test")
    print("=" * 60)
    
    # Create a simple flow
    flow = Flow(name="test_flow")
    flow.actions = [
        Delay(ms=100),
        ClickImage(asset_id="button1"),
        WaitImage(asset_id="loading"),
        ClickImage(asset_id="button2"),
    ]
    
    # Convert to graph
    flow.graph = list_to_graph(flow.actions)
    
    print(f"\n📊 Graph Info:")
    print(f"  Nodes: {len(flow.graph.nodes)}")
    print(f"  Connections: {len(flow.graph.connections)}")
    
    # Create walker
    walker = GraphWalker(flow.graph)
    
    # Find start node
    start = walker.find_start_node()
    print(f"\n🚀 Start Node: {type(start.action).__name__}")
    
    # Track execution order
    execution_order = []
    
    def mock_executor(action):
        """Mock action executor that just records execution."""
        action_name = type(action).__name__
        execution_order.append(action_name)
        print(f"  ✓ Executed: {action_name}")
        return None  # No branch result
    
    # Execute graph
    print(f"\n⚙️  Executing graph...")
    walker.execute_graph(mock_executor)
    
    # Verify execution order
    print(f"\n📋 Execution Order:")
    for i, name in enumerate(execution_order):
        print(f"  {i+1}. {name}")
    
    expected = ["Delay", "ClickImage", "WaitImage", "ClickImage"]
    assert execution_order == expected, f"Expected {expected}, got {execution_order}"
    
    print(f"\n✅ Test passed! All {len(execution_order)} nodes executed in correct order.")
    print("=" * 60)


if __name__ == "__main__":
    test_graph_walker()
