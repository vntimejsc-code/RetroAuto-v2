"""
Test graph data model and conversion.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import yaml

from core.graph import graph_to_list, list_to_graph
from core.models import ClickImage, Delay, Flow, WaitImage


def _create_test_flow() -> Flow:
    """Helper to create a test flow with graph."""
    flow = Flow(name="test_flow")
    flow.actions = [
        Delay(ms=1000),
        ClickImage(asset_id="button"),
        WaitImage(asset_id="loading"),
    ]
    flow.graph = list_to_graph(flow.actions)
    return flow


def test_model_creation():
    """Test creating graph models."""
    flow = _create_test_flow()

    assert len(flow.graph.nodes) == 3
    assert len(flow.graph.connections) == 2


def test_serialization():
    """Test YAML serialization."""
    flow = _create_test_flow()

    # Serialize to dict
    data = flow.model_dump()

    # Convert to YAML
    yaml_str = yaml.dump(data, sort_keys=False, allow_unicode=True)

    # Deserialize back
    loaded_data = yaml.safe_load(yaml_str)
    loaded_flow = Flow(**loaded_data)

    assert loaded_flow.name == flow.name
    assert len(loaded_flow.graph.nodes) == len(flow.graph.nodes)


def test_graph_to_list():
    """Test graph -> list conversion."""
    flow = _create_test_flow()

    # Convert graph back to list
    actions = graph_to_list(flow.graph)

    assert len(actions) == 3
    assert actions[0].action == "Delay"
    assert actions[1].action == "ClickImage"
    assert actions[2].action == "WaitImage"


def test_backward_compat():
    """Test backward compatibility (flow without graph)."""
    # Legacy format (no graph)
    legacy_flow = Flow(name="legacy")
    legacy_flow.actions = [Delay(ms=500), ClickImage(asset_id="ok")]

    # Should work fine without graph
    yaml_str = yaml.dump(legacy_flow.model_dump(), sort_keys=False)
    loaded = Flow(**yaml.safe_load(yaml_str))

    assert loaded.graph is None
    assert len(loaded.actions) == 2


if __name__ == "__main__":
    print("=" * 60)
    print("Graph Data Model Tests")
    print("=" * 60)

    test_model_creation()
    print("  ✓ Model creation passed")

    test_serialization()
    print("  ✓ Serialization passed")

    test_graph_to_list()
    print("  ✓ Graph-to-list conversion passed")

    test_backward_compat()
    print("  ✓ Backward compatibility passed")

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
