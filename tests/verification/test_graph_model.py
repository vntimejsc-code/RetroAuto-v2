"""
Test graph data model and conversion.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.models import Flow, FlowGraph, Delay, ClickImage, WaitImage
from core.graph import list_to_graph, graph_to_list
import yaml


def test_model_creation():
    """Test creating graph models."""
    print("Test 1: Creating graph models...")
    
    # Create a simple flow with graph
    flow = Flow(name="test_flow")
    flow.actions = [
        Delay(ms=1000),
        ClickImage(asset_id="button"),
        WaitImage(asset_id="loading")
    ]
    
    # Convert to graph
    flow.graph = list_to_graph(flow.actions)
    
    print(f"  Created flow with {len(flow.graph.nodes)} nodes")
    print(f"  Created {len(flow.graph.connections)} connections")
    assert len(flow.graph.nodes) == 3
    assert len(flow.graph.connections) == 2
    print("  ✓ Model creation passed")
    
    return flow


def test_serialization(flow: Flow):
    """Test YAML serialization."""
    print("\nTest 2: YAML serialization...")
    
    # Serialize to dict
    data = flow.model_dump()
    
    # Convert to YAML
    yaml_str = yaml.dump(data, sort_keys=False, allow_unicode=True)
    print(f"  YAML length: {len(yaml_str)} bytes")
    
    # Deserialize back
    loaded_data = yaml.safe_load(yaml_str)
    loaded_flow = Flow(**loaded_data)
    
    assert loaded_flow.name == flow.name
    assert len(loaded_flow.graph.nodes) == len(flow.graph.nodes)
    print("  ✓ Serialization passed")


def test_graph_to_list(flow: Flow):
    """Test graph -> list conversion."""
    print("\nTest 3: Graph to list conversion...")
    
    # Convert graph back to list
    actions = graph_to_list(flow.graph)
    
    print(f"  Converted graph to {len(actions)} actions")
    assert len(actions) == 3
    assert actions[0].action == "Delay"
    assert actions[1].action == "ClickImage"
    assert actions[2].action == "WaitImage"
    print("  ✓ Graph-to-list conversion passed")


def test_backward_compat():
    """Test backward compatibility (flow without graph)."""
    print("\nTest 4: Backward compatibility...")
    
    # Legacy format (no graph)
    legacy_flow = Flow(name="legacy")
    legacy_flow.actions = [
        Delay(ms=500),
        ClickImage(asset_id="ok")
    ]
    
    # Should work fine without graph
    yaml_str = yaml.dump(legacy_flow.model_dump(), sort_keys=False)
    loaded = Flow(**yaml.safe_load(yaml_str))
    
    assert loaded.graph is None
    assert len(loaded.actions) == 2
    print("  ✓ Backward compatibility passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Graph Data Model Tests")
    print("=" * 60)
    
    flow = test_model_creation()
    test_serialization(flow)
    test_graph_to_list(flow)
    test_backward_compat()
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
