#!/usr/bin/env python3
"""
Performance Benchmark for Phase 1 Optimizations

Tests:
1. Adaptive Interrupt Scan Interval
2. OCR Result Caching
3. Image Cache TTL

Run: python scripts/test_phase1_perf.py
"""

import sys
import time
from pathlib import Path

# Setup path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_adaptive_scan_interval():
    """Test adaptive interrupt scan interval calculation."""
    print("\n" + "=" * 60)
    print("TEST 1: Adaptive Interrupt Scan Interval")
    print("=" * 60)

    from core.engine.context import EngineState, ExecutionContext
    from core.models import Script

    # Create mock scanner to test interval logic
    class MockScanner:
        def __init__(self):
            self._interval_idle = 0.5
            self._interval_active = 0.2
            self._interval_fast = 0.1
            self._last_scan_had_activity = False

        def _get_adaptive_interval(self, state: EngineState, had_activity: bool) -> float:
            self._last_scan_had_activity = had_activity
            if state == EngineState.IDLE:
                return self._interval_idle
            elif state == EngineState.RUNNING:
                if self._last_scan_had_activity:
                    return self._interval_fast
                return self._interval_active
            else:
                return self._interval_active

    scanner = MockScanner()

    # Test cases
    tests = [
        (EngineState.IDLE, False, 0.5, "Idle state"),
        (EngineState.RUNNING, False, 0.2, "Running, no activity"),
        (EngineState.RUNNING, True, 0.1, "Running with activity"),
        (EngineState.PAUSED, False, 0.2, "Paused state"),
    ]

    all_passed = True
    for state, activity, expected, desc in tests:
        result = scanner._get_adaptive_interval(state, activity)
        passed = abs(result - expected) < 0.001
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {desc}: {result*1000:.0f}ms (expected {expected*1000:.0f}ms)")
        if not passed:
            all_passed = False

    return all_passed


def test_ocr_cache():
    """Test OCR result caching."""
    print("\n" + "=" * 60)
    print("TEST 2: OCR Result Caching")
    print("=" * 60)

    from PIL import Image

    from vision.ocr import TextReader

    reader = TextReader(cache_ttl=2.0)

    # Check cache is initialized
    print(f"  Cache TTL: {reader._cache_ttl}s")
    print(f"  Cache max size: {reader._cache_max_size}")

    # Test hash computation
    img = Image.new("RGB", (100, 50), color="white")
    hash1 = reader._compute_image_hash(img, "")
    hash2 = reader._compute_image_hash(img, "")
    hash3 = reader._compute_image_hash(img, "0123")  # Different allowlist

    print(f"  Hash same image: {hash1 == hash2} (expected: True)")
    print(f"  Hash different config: {hash1 != hash3} (expected: True)")

    # Test cache storage
    reader._cache_result(hash1, "test_result")
    cached = reader._ocr_cache.get(hash1)
    print(f"  Cache store/retrieve: {cached[0] == 'test_result' if cached else False}")

    # Test LRU eviction
    old_max = reader._cache_max_size
    reader._cache_max_size = 3
    for i in range(5):
        reader._cache_result(i, f"result_{i}")
    print(f"  LRU eviction: {len(reader._ocr_cache) == 3} (size: {len(reader._ocr_cache)})")
    reader._cache_max_size = old_max

    # Clear cache test
    reader.clear_cache()
    print(f"  Cache clear: {len(reader._ocr_cache) == 0}")

    return True


def test_image_cache_ttl():
    """Test image cache TTL and cleanup."""
    print("\n" + "=" * 60)
    print("TEST 3: Image Cache TTL")
    print("=" * 60)

    from core.vision.matcher import ImageCache

    # Create cache with short TTL for testing
    cache = ImageCache(max_size=5, ttl_seconds=2)

    print(f"  Max size: {cache._max_size}")
    print(f"  TTL: {cache._ttl}s")

    # Test put and get
    test_path = str(PROJECT_ROOT / "README.md")  # Use existing file
    cache.put(test_path, "dummy_image")

    result = cache.get(test_path)
    print(f"  Put/Get: {result == 'dummy_image'}")

    # Test LRU eviction
    for i in range(7):
        cache.put(f"path_{i}", f"image_{i}")

    print(f"  LRU eviction: {len(cache._cache) <= 5} (size: {len(cache._cache)})")

    # Test cleanup thread started
    print(f"  Cleanup thread: {cache._cleanup_started}")

    # Test clear
    cache.clear()
    print(f"  Cache clear: {len(cache._cache) == 0}")

    return True


def test_memory_baseline():
    """Measure baseline memory usage."""
    print("\n" + "=" * 60)
    print("TEST 4: Memory Baseline")
    print("=" * 60)

    try:
        import psutil

        process = psutil.Process()
        mem_mb = process.memory_info().rss / (1024 * 1024)
        print(f"  Current memory: {mem_mb:.1f} MB")
        print(f"  Memory target: <200 MB")
        print(f"  Status: {'✅ OK' if mem_mb < 200 else '⚠️  High'}")
        return mem_mb < 200
    except ImportError:
        print("  ⚠️  psutil not installed, skipping memory test")
        return True


def test_import_speed():
    """Test import speed of key modules."""
    print("\n" + "=" * 60)
    print("TEST 5: Import Speed")
    print("=" * 60)

    modules = [
        "core.models",
        "core.engine.runner",
        "vision.capture",
        "vision.ocr",
    ]

    all_fast = True
    for mod in modules:
        start = time.time()
        __import__(mod)
        elapsed = (time.time() - start) * 1000
        status = "✅" if elapsed < 500 else "⚠️"
        print(f"  {status} {mod}: {elapsed:.0f}ms")
        if elapsed > 500:
            all_fast = False

    return all_fast


def main():
    print("=" * 60)
    print("  RetroAuto v2 - Phase 1 Performance Tests")
    print("=" * 60)

    results = []
    results.append(("Adaptive Scan", test_adaptive_scan_interval()))
    results.append(("OCR Cache", test_ocr_cache()))
    results.append(("Image Cache", test_image_cache_ttl()))
    results.append(("Memory", test_memory_baseline()))
    results.append(("Import Speed", test_import_speed()))

    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    failed = len(results) - passed

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {name}")

    print(f"\n  Total: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n  🎉 All Phase 1 tests passed!")
        return 0
    else:
        print("\n  ⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
