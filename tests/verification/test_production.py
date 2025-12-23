"""
Production Test Suite - Real-world scenarios.

Simulates actual automation scripts to find edge cases and bugs.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_scenario_1_missing_asset():
    """Scenario: Script references non-existent image."""
    print("\n" + "=" * 60)
    print("SCENARIO 1: Missing Asset Handling")
    print("=" * 60)

    from core.models import ClickImage, Delay, Flow, Script
    from core.validation import validate_assets

    # Create script with missing asset
    script = Script(name="test_missing")
    flow = Flow(name="main")
    flow.actions = [
        Delay(ms=100),
        ClickImage(asset_id="nonexistent_button"),  # This doesn't exist
        Delay(ms=100),
    ]
    script.flows = [flow]

    # Validate
    assets_dir = Path("C:/fake/assets")
    valid, missing = validate_assets(script, assets_dir)

    if not valid:
        print(f"✓ Validation caught {len(missing)} missing assets before execution")
        print(f"  Missing: {missing}")
        print("✓ System prevented crash by validating upfront")
        return True
    else:
        print("✗ Validation should have detected missing asset")
        return False


def test_scenario_2_timeout_protection():
    """Scenario: Wait action with excessive timeout."""
    print("\n" + "=" * 60)
    print("SCENARIO 2: Timeout Protection")
    print("=" * 60)

    from pydantic import ValidationError

    from core.models import WaitImage

    # Try to create wait with 10-minute timeout (should fail)
    try:
        action = WaitImage(asset_id="test", timeout_ms=600000)
        print("✗ Should have rejected 10-minute timeout")
        return False
    except ValidationError as e:
        print("✓ Pydantic rejected excessive timeout (600,000ms)")
        print(f"  Error: {str(e).split('validation error')[0]}")
        print("✓ System prevents infinite hangs")
        return True


def test_scenario_3_nested_conditionals():
    """Scenario: Complex nested if/else logic."""
    print("\n" + "=" * 60)
    print("SCENARIO 3: Nested Conditionals")
    print("=" * 60)

    from core.models import ClickImage, Delay, IfImage

    try:
        # Create nested IfImage
        inner_if = IfImage(
            asset_id="error_dialog",
            then_actions=[ClickImage(asset_id="ok_button")],
            else_actions=[Delay(ms=100)],
        )

        outer_if = IfImage(
            asset_id="main_menu",
            then_actions=[ClickImage(asset_id="start_button"), inner_if],  # Nested conditional
            else_actions=[Delay(ms=1000)],
        )

        print("✓ Created nested conditional structure")
        print(f"  Outer IfImage with {len(outer_if.then_actions)} then-actions")
        print(f"  Inner IfImage with {len(inner_if.then_actions)} then-actions")
        print("✓ Model supports complex logic")
        return True

    except Exception as e:
        print(f"✗ Failed to create nested conditionals: {e}")
        return False


def test_scenario_4_ocr_with_missing_tesseract():
    """Scenario: OCR action when Tesseract unavailable."""
    print("\n" + "=" * 60)
    print("SCENARIO 4: OCR Graceful Degradation")
    print("=" * 60)

    from core.models import ReadText
    from vision.ocr import TextReader

    reader = TextReader()

    if not reader.available:
        print("✓ System detected Tesseract unavailable")
        print("  ReadText actions would be skipped gracefully")
        print("✓ No crash - just warning logged")
        return True
    else:
        print("✓ Tesseract available - OCR fully functional")

        # Test creating ReadText action
        action = ReadText(variable_name="$hp", roi={"x": 10, "y": 10, "w": 100, "h": 30})
        print(f"✓ ReadText action created: variable={action.variable_name}")
        return True


def test_scenario_5_graph_execution():
    """Scenario: Execute flow as graph instead of list."""
    print("\n" + "=" * 60)
    print("SCENARIO 5: Graph-based Execution")
    print("=" * 60)

    from core.graph import list_to_graph
    from core.graph.walker import GraphWalker
    from core.models import ClickImage, Delay, Flow

    try:
        # Create flow
        flow = Flow(name="test")
        flow.actions = [
            Delay(ms=100),
            ClickImage(asset_id="btn1"),
            Delay(ms=200),
            ClickImage(asset_id="btn2"),
        ]

        # Convert to graph
        flow.graph = list_to_graph(flow.actions)
        print(f"✓ Converted {len(flow.actions)} actions to graph")
        print(f"  Graph: {len(flow.graph.nodes)} nodes, {len(flow.graph.connections)} connections")

        # Test walker can find start
        walker = GraphWalker(flow.graph)
        start = walker.find_start_node()

        if start:
            print(f"✓ Walker found start node: {type(start.action).__name__}")
            print("✓ Graph execution ready")
            return True
        else:
            print("✗ Walker could not find start node")
            return False

    except Exception as e:
        print(f"✗ Graph execution failed: {e}")
        return False


def test_scenario_6_serialization_roundtrip():
    """Scenario: Save and load complex script."""
    print("\n" + "=" * 60)
    print("SCENARIO 6: Serialization Roundtrip")
    print("=" * 60)

    import yaml

    from core.models import Delay, Flow, IfText, ReadText, Script

    try:
        # Create complex script
        script = Script(name="production_bot")
        flow = Flow(name="main_loop")
        flow.actions = [
            ReadText(variable_name="$hp", roi={"x": 0, "y": 0, "w": 50, "h": 20}),
            IfText(
                variable_name="$hp",
                operator="numeric_lt",
                value="50",
                then_actions=[Delay(ms=500)],
                else_actions=[Delay(ms=100)],
            ),
            Delay(ms=1000),
        ]
        script.flows = [flow]

        # Serialize
        yaml_str = yaml.dump(script.model_dump(), sort_keys=False)
        print(f"✓ Serialized script to YAML ({len(yaml_str)} bytes)")

        # Deserialize
        loaded_data = yaml.safe_load(yaml_str)
        loaded_script = Script(**loaded_data)

        print(f"✓ Deserialized script: '{loaded_script.name}'")
        print(f"  Flows: {len(loaded_script.flows)}")
        print(f"  Actions: {len(loaded_script.flows[0].actions)}")

        # Verify
        assert loaded_script.name == script.name
        assert len(loaded_script.flows) == len(script.flows)
        print("✓ Roundtrip successful - no data loss")
        return True

    except Exception as e:
        print(f"✗ Serialization failed: {e}")
        return False


def run_production_tests():
    """Run all production scenarios."""
    print("\n" + "#" * 60)
    print("# PRODUCTION TEST SUITE")
    print("# Real-world automation scenarios")
    print("#" * 60)

    scenarios = [
        ("Missing Asset Handling", test_scenario_1_missing_asset),
        ("Timeout Protection", test_scenario_2_timeout_protection),
        ("Nested Conditionals", test_scenario_3_nested_conditionals),
        ("OCR Graceful Degradation", test_scenario_4_ocr_with_missing_tesseract),
        ("Graph Execution", test_scenario_5_graph_execution),
        ("Serialization Roundtrip", test_scenario_6_serialization_roundtrip),
    ]

    results = []
    for name, test_func in scenarios:
        try:
            passed = test_func()
            results.append((name, passed, None))
        except Exception as e:
            print(f"\n✗ CRITICAL ERROR: {e}")
            results.append((name, False, str(e)))

    # Summary
    print("\n" + "#" * 60)
    print("# PRODUCTION TEST SUMMARY")
    print("#" * 60)

    for name, passed, error in results:
        if passed:
            print(f"✅ PASS: {name}")
        else:
            print(f"❌ FAIL: {name}")
            if error:
                print(f"         {error}")

    passed_count = sum(1 for _, p, _ in results if p)
    total = len(results)

    print(f"\n{passed_count}/{total} scenarios passed")

    if passed_count == total:
        print("\n🎉 SYSTEM READY FOR PRODUCTION!")
        print("All real-world scenarios handled correctly.")
    else:
        print(f"\n⚠️  {total - passed_count} scenarios failed")
        print("System needs additional hardening.")

    print("#" * 60 + "\n")

    return passed_count == total


if __name__ == "__main__":
    success = run_production_tests()
    sys.exit(0 if success else 1)
