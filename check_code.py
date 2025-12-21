#!/usr/bin/env python3
"""
RetroAuto v2 - Code Check Script

Runs all code quality checks:
- Syntax check
- Import check  
- Ruff linting
- Pytest tests

Usage:
    python check_code.py           # Quick check
    python check_code.py --full    # Full check with all tests
    python check_code.py --fix     # Auto-fix issues
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Directories to check
CHECK_DIRS = ["app", "core", "vision", "input", "infra"]
PROJECT_ROOT = Path(__file__).parent


def run_cmd(cmd: list[str], check: bool = True) -> tuple[int, str]:
    """Run command and return (returncode, output)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        output = result.stdout + result.stderr
        return result.returncode, output
    except Exception as e:
        return 1, str(e)


def check_syntax() -> bool:
    """Check Python syntax."""
    print("\n🔍 Checking Python syntax...")
    
    errors = []
    for dir_name in CHECK_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            continue
            
        for py_file in dir_path.rglob("*.py"):
            code, output = run_cmd([sys.executable, "-m", "py_compile", str(py_file)])
            if code != 0:
                errors.append(f"  ❌ {py_file.relative_to(PROJECT_ROOT)}")
    
    if errors:
        print("\n".join(errors))
        return False
    
    print("  ✅ Syntax OK")
    return True


def check_imports() -> bool:
    """Check that all modules can be imported."""
    print("\n🔍 Checking imports...")
    
    errors = []
    modules = [
        "app.main",
        "app.ui.main_window",
        "core.models",
        "core.engine.runner",
        "vision.capture",
        "input.mouse",
    ]
    
    for module in modules:
        code, output = run_cmd([sys.executable, "-c", f"import {module}"])
        if code != 0:
            errors.append(f"  ❌ {module}: {output.strip()[:100]}")
    
    if errors:
        print("\n".join(errors))
        return False
    
    print("  ✅ Imports OK")
    return True


def check_ruff(fix: bool = False) -> bool:
    """Run Ruff linter."""
    print("\n🔍 Running Ruff linter...")
    
    cmd = [sys.executable, "-m", "ruff", "check", "."]
    if fix:
        cmd.append("--fix")
    
    code, output = run_cmd(cmd)
    
    if code != 0:
        # Filter to show only first 20 issues
        lines = output.strip().split("\n")
        if len(lines) > 20:
            print("\n".join(lines[:20]))
            print(f"  ... and {len(lines) - 20} more issues")
        else:
            print(output)
        return False
    
    print("  ✅ Ruff OK")
    return True


def check_tests(full: bool = False) -> bool:
    """Run pytest tests."""
    print("\n🔍 Running tests...")
    
    cmd = [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"]
    if not full:
        cmd.extend(["-x"])  # Stop on first failure for quick check
    
    code, output = run_cmd(cmd)
    
    # Always show test output
    print(output)
    
    if code != 0:
        return False
    
    print("  ✅ Tests OK")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Code quality checker")
    parser.add_argument("--full", action="store_true", help="Full check with all tests")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    args = parser.parse_args()
    
    print("=" * 50)
    print("RetroAuto v2 - Code Check")
    print("=" * 50)
    
    results = {
        "Syntax": check_syntax(),
        "Imports": check_imports(),
        "Ruff": check_ruff(fix=args.fix),
        "Tests": check_tests(full=args.full),
    }
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All checks passed!")
        return 0
    else:
        print("⚠️ Some checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
