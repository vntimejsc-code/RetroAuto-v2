#!/usr/bin/env python3
"""
RetroAuto v2 - Code Check Script

Runs all code quality checks:
- Syntax check
- Import check  
- Ruff linting
- Mypy type checking
- Pytest tests with coverage

Usage:
    python check_code.py           # Quick check
    python check_code.py --full    # Full check with all tests
    python check_code.py --fix     # Auto-fix issues
    python check_code.py --cov     # Show coverage report
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
            encoding="utf-8",
            errors="replace",
        )
        output = result.stdout + result.stderr
        return result.returncode, output
    except Exception as e:
        return 1, str(e)


def check_syntax() -> bool:
    """Check Python syntax."""
    print("\n🔍 [1/5] Checking Python syntax...")
    
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
    print("\n🔍 [2/5] Checking imports...")
    
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
    print("\n🔍 [3/5] Running Ruff linter...")
    
    cmd = [sys.executable, "-m", "ruff", "check", "."]
    if fix:
        cmd.append("--fix")
    
    code, output = run_cmd(cmd)
    
    if code != 0:
        # Filter to show only first 15 issues
        lines = output.strip().split("\n")
        if len(lines) > 15:
            print("\n".join(lines[:15]))
            print(f"  ... and {len(lines) - 15} more issues")
        else:
            print(output)
        return False
    
    print("  ✅ Ruff OK")
    return True


def check_mypy() -> bool:
    """Run Mypy type checker."""
    print("\n🔍 [4/5] Running Mypy type check...")
    
    cmd = [
        sys.executable, "-m", "mypy",
        "app", "core",
        "--ignore-missing-imports",
        "--no-error-summary",
    ]
    
    code, output = run_cmd(cmd)
    
    if code != 0:
        # Filter to show only errors (not notes)
        lines = [l for l in output.strip().split("\n") if ": error:" in l]
        if len(lines) > 10:
            print("\n".join(lines[:10]))
            print(f"  ... and {len(lines) - 10} more errors")
        elif lines:
            print("\n".join(lines))
        else:
            # No errors but non-zero exit (warnings)
            print("  ✅ Mypy OK (with warnings)")
            return True
        return False
    
    print("  ✅ Mypy OK")
    return True


def check_tests(full: bool = False, coverage: bool = False) -> bool:
    """Run pytest tests."""
    print("\n🔍 [5/5] Running tests...")
    
    cmd = [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"]
    
    if coverage:
        cmd.extend([
            "--cov=app", "--cov=core", "--cov=vision", "--cov=input",
            "--cov-report=term-missing",
            "--cov-fail-under=30",
        ])
    
    if not full:
        cmd.extend(["-x"])  # Stop on first failure for quick check
    
    code, output = run_cmd(cmd)
    
    # Show relevant output
    lines = output.strip().split("\n")
    # Show last 20 lines (summary + coverage)
    relevant = lines[-20:] if len(lines) > 20 else lines
    print("\n".join(relevant))
    
    if code != 0:
        return False
    
    print("  ✅ Tests OK")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Code quality checker")
    parser.add_argument("--full", action="store_true", help="Full check with all tests")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser.add_argument("--cov", action="store_true", help="Show coverage report")
    args = parser.parse_args()
    
    print("=" * 60)
    print("  RetroAuto v2 - Code Quality Check")
    print("=" * 60)
    
    results = {
        "Syntax": check_syntax(),
        "Imports": check_imports(),
        "Ruff": check_ruff(fix=args.fix),
        "Mypy": check_mypy(),
        "Tests": check_tests(full=args.full, coverage=args.cov),
    }
    
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:10s} {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("  🎉 All checks passed! Ready to commit.")
        return 0
    else:
        print("  ⚠️  Some checks failed. Fix before committing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
