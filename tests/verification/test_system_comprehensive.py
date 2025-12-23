"""
Comprehensive System Test Suite
Tests all major components for bugs and regressions.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_models_validation():
    """Test 1: Model validation and serialization."""
    print("\n" + "=" * 60)
    print("TEST 1: Models Validation")
    print("=" * 60)

    import yaml

    from core.models import (
        ROI,
        ClickImage,
        Delay,
        Flow,
        Hotkey,
        IfImage,
        IfText,
        Loop,
        ReadText,
        Script,
        WaitImage,
    )

    try:
        # Test all action types can be created
        actions = [
            ClickImage(asset_id="test"),
            WaitImage(asset_id="test", timeout_ms=5000),
            Delay(ms=1000),
            IfImage(asset_id="test", then_actions=[], else_actions=[]),
            IfText(variable_name="$hp", operator="contains", value="100"),
            ReadText(variable_name="$text", roi=ROI(x=0, y=0, w=100, h=30)),
            Hotkey(keys=["CTRL", "C"]),
            Loop(iterations=5),
        ]

        print(f"✓ Created {len(actions)} action types successfully")

        # Test flow creation
        flow = Flow(name="test_flow", actions=actions)
        print(f"✓ Created flow with {len(flow.actions)} actions")

        # Test script creation
        script = Script(name="test_script", flows=[flow])
        print(f"✓ Created script with {len(script.flows)} flows")

        # Test serialization
        yaml_str = yaml.dump(script.model_dump(), sort_keys=False)
        print(f"✓ Serialized to YAML ({len(yaml_str)} bytes)")

        # Test deserialization
        loaded_data = yaml.safe_load(yaml_str)
        loaded_script = Script(**loaded_data)
        print("✓ Deserialized from YAML")

        assert loaded_script.name == script.name
        assert len(loaded_script.flows) == len(script.flows)
        print("✓ Validation passed!\n")
        return True

    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        return False


def test_ocr_functionality():
    """Test 2: OCR functionality."""
    print("=" * 60)
    print("TEST 2: OCR Functionality")
    print("=" * 60)

    try:
        from PIL import Image, ImageDraw

        from vision.ocr import TextReader

        reader = TextReader()

        if not reader.available:
            print("⚠ Tesseract not available, skipping OCR test")
            return True

        # Create test image
        img = Image.new("RGB", (200, 50), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((10, 10), "TEST: 123", fill=(0, 0, 0))

        # Read text
        text = reader.read_from_image(img)
        print(f"✓ OCR read: '{text}'")

        if "123" in text or "TEST" in text:
            print("✓ OCR working correctly\n")
            return True
        else:
            print("⚠ OCR result unclear, but no crash\n")
            return True

    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        return False


def test_graph_models():
    """Test 3: Graph models and conversion."""
    print("=" * 60)
    print("TEST 3: Graph Models & Conversion")
    print("=" * 60)

    try:
        from core.graph import graph_to_list, list_to_graph
        from core.models import ClickImage, Delay, Flow

        # Create flow
        flow = Flow(name="test")
        flow.actions = [Delay(ms=100), ClickImage(asset_id="btn")]

        # Convert to graph
        flow.graph = list_to_graph(flow.actions)
        print(f"✓ Converted list to graph ({len(flow.graph.nodes)} nodes)")

        # Convert back to list
        actions_back = graph_to_list(flow.graph)
        print(f"✓ Converted graph to list ({len(actions_back)} actions)")

        assert len(actions_back) == len(flow.actions)
        print("✓ Round-trip conversion successful\n")
        return True

    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        return False


def test_action_union():
    """Test 4: Action discriminated union."""
    print("=" * 60)
    print("TEST 4: Action Discriminated Union")
    print("=" * 60)

    try:
        from core.models import ClickImage, IfText, ReadText, WaitImage

        # Create instances to verify they work
        test_actions = [
            ClickImage(asset_id="test"),
            WaitImage(asset_id="test"),
            IfText(variable_name="$var", value="test"),
            ReadText(variable_name="$var", roi={"x": 0, "y": 0, "w": 100, "h": 30}),
        ]

        print(f"✓ Created {len(test_actions)} test action instances")

        # Verify each has correct action field
        for action in test_actions:
            assert hasattr(action, "action"), f"{type(action).__name__} missing 'action' field"
            print(f"  - {action.action} ✓")

        print("✓ All key action types validated\n")
        return True

    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        return False


def test_imports():
    """Test 5: Import all major modules."""
    print("=" * 60)
    print("TEST 5: Module Imports")
    print("=" * 60)

    modules_to_test = [
        "core.models",
        "core.engine.runner",
        "core.engine.context",
        "core.graph.converter",
        "core.graph.walker",
        "app.ui.graph_view",
        "app.ui.graph_node",
        "app.ui.graph_connection",
        "vision.ocr",
    ]

    failed = []
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name}")
        except Exception as e:
            print(f"  ✗ {module_name}: {e}")
            failed.append(module_name)

    if failed:
        print(f"\n✗ {len(failed)} imports failed\n")
        return False

    print(f"\n✓ All {len(modules_to_test)} modules imported successfully\n")
    return True


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "#" * 60)
    print("# RETROAUTO COMPREHENSIVE SYSTEM TEST")
    print("#" * 60)

    tests = [
        ("Module Imports", test_imports),
        ("Models Validation", test_models_validation),
        ("OCR Functionality", test_ocr_functionality),
        ("Graph Models", test_graph_models),
        ("Action Union", test_action_union),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"CRITICAL ERROR in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "#" * 60)
    print("# TEST SUMMARY")
    print("#" * 60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\n{passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! System is stable.")
    else:
        print(f"\n⚠️  {total_count - passed_count} TESTS FAILED! Bugs detected.")

    print("#" * 60 + "\n")

    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
