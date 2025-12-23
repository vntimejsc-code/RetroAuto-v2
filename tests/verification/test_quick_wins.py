"""
Test Quick Wins implementation.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_asset_validation():
    """Test asset validation utility."""
    print("=" * 60)
    print("TEST: Asset Validation")
    print("=" * 60)

    from core.models import ClickImage, Flow, Script, WaitImage
    from core.validation import get_referenced_assets, validate_assets

    # Create test flow with assets
    flow = Flow(name="test")
    flow.actions = [
        ClickImage(asset_id="button_ok"),
        WaitImage(asset_id="loading_screen"),
        ClickImage(asset_id="button_cancel"),
    ]

    # Get referenced assets
    assets = get_referenced_assets(flow)
    print(f"✓ Found {len(assets)} referenced assets: {assets}")
    assert len(assets) == 3

    # Create script
    script = Script(name="test", flows=[flow])

    # Test with non-existent directory
    fake_dir = Path("C:/nonexistent/assets")
    valid, missing = validate_assets(script, fake_dir)

    print(f"✓ Validation detected {len(missing)} missing assets")
    assert not valid
    assert len(missing) == 3

    print("✓ Asset validation working correctly\n")
    return True


def test_timeout_limits():
    """Test timeout validation."""
    print("=" * 60)
    print("TEST: Timeout Limits")
    print("=" * 60)

    from pydantic import ValidationError

    from core.models import WaitImage

    # Test valid timeout
    action1 = WaitImage(asset_id="test", timeout_ms=10000)
    print(f"✓ Valid timeout accepted: {action1.timeout_ms}ms")

    # Test max timeout (5 minutes = 300,000ms)
    action2 = WaitImage(asset_id="test", timeout_ms=300000)
    print(f"✓ Max timeout accepted: {action2.timeout_ms}ms")

    # Test exceeding max (should fail)
    try:
        WaitImage(asset_id="test", timeout_ms=600000)  # 10 minutes
        print("✗ Should have rejected timeout > 5 min")
        return False
    except ValidationError:
        print("✓ Timeout > 5 min correctly rejected")

    print("✓ Timeout limits working\n")
    return True


def test_ocr_availability():
    """Test OCR availability check."""
    print("=" * 60)
    print("TEST: OCR Availability Check")
    print("=" * 60)

    try:
        from vision.ocr import TextReader

        reader = TextReader()
        print(f"OCR Available: {reader.available}")

        if reader.available:
            print("✓ Tesseract detected")
        else:
            print("⚠ Tesseract not available (feature will be disabled)")

        print("✓ OCR check completed without crash\n")
        return True

    except Exception as e:
        print(f"✗ OCR check failed: {e}\n")
        return False


if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("# QUICK WINS VERIFICATION")
    print("#" * 60 + "\n")

    results = []
    results.append(("Asset Validation", test_asset_validation()))
    results.append(("Timeout Limits", test_timeout_limits()))
    results.append(("OCR Availability", test_ocr_availability()))

    print("#" * 60)
    print("# SUMMARY")
    print("#" * 60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    passed_count = sum(1 for _, p in results if p)
    print(f"\n{passed_count}/{len(results)} tests passed")
    print("#" * 60 + "\n")
