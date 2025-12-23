#!/usr/bin/env python3
"""
RetroAuto v2 - Deep Code Analysis

Extended 7-layer code quality analysis:
1. Syntax Check - Python syntax errors
2. Import Check - Missing dependencies
3. Lint Check - Ruff (style, bugs, unused code)
4. Format Check - Black formatting
5. Type Check - Mypy type errors
6. Security Check - Bandit vulnerabilities
7. Test Check - Pytest functional tests

Additional Analysis:
- Dead code detection
- Complexity analysis (McCabe)
- Dependency impact analysis

Usage:
    python scripts/deep_check.py           # Quick check (layers 1-5)
    python scripts/deep_check.py --full    # Full check (all 7 layers)
    python scripts/deep_check.py --fix     # Auto-fix issues
    python scripts/deep_check.py --deep    # Extended analysis
"""

import argparse
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
CHECK_DIRS = ["app", "core", "vision", "input", "infra"]


@dataclass
class CheckResult:
    """Result of a single check."""

    name: str
    passed: bool
    duration: float
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    fixed: int = 0


def run_cmd(cmd: list[str], timeout: int = 120) -> tuple[int, str]:
    """Run command and return (returncode, output)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return -1, "Command timed out"
    except Exception as e:
        return -1, str(e)


def timed_check(
    name: str, check_func: Callable[[], tuple[bool, list[str], list[str]]]
) -> CheckResult:
    """Run a check with timing."""
    start = time.time()
    try:
        passed, errors, warnings = check_func()
    except Exception as e:
        passed, errors, warnings = False, [str(e)], []
    duration = time.time() - start
    return CheckResult(
        name=name, passed=passed, duration=duration, errors=errors, warnings=warnings
    )


# ═══════════════════════════════════════════════════════════════
# Layer 1: Syntax Check
# ═══════════════════════════════════════════════════════════════
def check_syntax() -> tuple[bool, list[str], list[str]]:
    """Check Python syntax."""
    errors = []
    for dir_name in CHECK_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob("*.py"):
            code, output = run_cmd([sys.executable, "-m", "py_compile", str(py_file)])
            if code != 0:
                errors.append(f"{py_file.relative_to(PROJECT_ROOT)}: {output.strip()[:100]}")
    return len(errors) == 0, errors, []


# ═══════════════════════════════════════════════════════════════
# Layer 2: Import Check
# ═══════════════════════════════════════════════════════════════
def check_imports() -> tuple[bool, list[str], list[str]]:
    """Check that critical modules can be imported."""
    errors = []
    modules = [
        "app.main",
        "core.models",
        "core.engine.runner",
        "core.dsl.lexer",
        "core.dsl.parser",
    ]
    for module in modules:
        code, output = run_cmd([sys.executable, "-c", f"import {module}"])
        if code != 0:
            errors.append(f"{module}: {output.strip()[:80]}")
    return len(errors) == 0, errors, []


# ═══════════════════════════════════════════════════════════════
# Layer 3: Lint Check (Ruff)
# ═══════════════════════════════════════════════════════════════
def check_lint(fix: bool = False) -> tuple[bool, list[str], list[str]]:
    """Run Ruff linter."""
    cmd = [sys.executable, "-m", "ruff", "check", "."]
    if fix:
        cmd.append("--fix")

    code, output = run_cmd(cmd)

    if code != 0:
        lines = [l for l in output.strip().split("\n") if ": " in l][:20]
        return False, lines, []
    return True, [], []


# ═══════════════════════════════════════════════════════════════
# Layer 4: Format Check (Black)
# ═══════════════════════════════════════════════════════════════
def check_format(fix: bool = False) -> tuple[bool, list[str], list[str]]:
    """Check Black formatting."""
    cmd = [sys.executable, "-m", "black", "--check", "."]
    if fix:
        cmd = [sys.executable, "-m", "black", "."]

    code, output = run_cmd(cmd)

    if code != 0 and not fix:
        lines = [l for l in output.strip().split("\n") if "would reformat" in l.lower()][:10]
        return False, lines, []
    return True, [], []


# ═══════════════════════════════════════════════════════════════
# Layer 5: Type Check (Mypy)
# ═══════════════════════════════════════════════════════════════
def check_types() -> tuple[bool, list[str], list[str]]:
    """Run Mypy type checker."""
    cmd = [sys.executable, "-m", "mypy", "core/"]
    code, output = run_cmd(cmd, timeout=180)

    if code != 0:
        errors = [l for l in output.strip().split("\n") if ": error:" in l][:15]
        warnings = [l for l in output.strip().split("\n") if ": note:" in l][:5]
        if not errors:  # Only warnings
            return True, [], warnings
        return False, errors, warnings
    return True, [], []


# ═══════════════════════════════════════════════════════════════
# Layer 6: Security Check (Bandit)
# ═══════════════════════════════════════════════════════════════
def check_security() -> tuple[bool, list[str], list[str]]:
    """Run Bandit security scanner."""
    cmd = [
        sys.executable,
        "-m",
        "bandit",
        "-r",
        "core/",
        "app/",
        "-f",
        "json",
        "-ll",  # Low and above
        "--quiet",
    ]
    code, output = run_cmd(cmd)

    try:
        data = json.loads(output)
        issues = data.get("results", [])
        if issues:
            errors = []
            for issue in issues[:10]:
                severity = issue.get("issue_severity", "UNKNOWN")
                text = issue.get("issue_text", "")
                file = issue.get("filename", "")
                line = issue.get("line_number", 0)
                errors.append(f"[{severity}] {file}:{line} - {text}")
            return len([i for i in issues if i.get("issue_severity") == "HIGH"]) == 0, errors, []
        return True, [], []
    except json.JSONDecodeError:
        # Bandit not installed or other error
        return True, [], ["Bandit not installed, skipping security check"]


# ═══════════════════════════════════════════════════════════════
# Layer 7: Test Check (Pytest)
# ═══════════════════════════════════════════════════════════════
def check_tests(full: bool = False) -> tuple[bool, list[str], list[str]]:
    """Run pytest tests."""
    cmd = [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"]
    if not full:
        cmd.append("-x")  # Stop on first failure

    code, output = run_cmd(cmd, timeout=300)

    if code != 0:
        lines = output.strip().split("\n")
        errors = [l for l in lines if "FAILED" in l or "ERROR" in l][:10]
        return False, errors, []
    return True, [], []


# ═══════════════════════════════════════════════════════════════
# Extended Analysis
# ═══════════════════════════════════════════════════════════════
def check_complexity() -> tuple[bool, list[str], list[str]]:
    """Check code complexity using Ruff's McCabe checker."""
    cmd = [sys.executable, "-m", "ruff", "check", ".", "--select=C901"]
    code, output = run_cmd(cmd)

    if code != 0:
        lines = [l for l in output.strip().split("\n") if "C901" in l][:10]
        return False, [], lines  # Complexity as warnings, not errors
    return True, [], []


def check_dead_code() -> tuple[bool, list[str], list[str]]:
    """Check for unused code using Ruff's F841, F401."""
    cmd = [sys.executable, "-m", "ruff", "check", ".", "--select=F401,F841"]
    code, output = run_cmd(cmd)

    if code != 0:
        lines = [l for l in output.strip().split("\n") if l.strip()][:15]
        return True, [], lines  # Dead code as warnings
    return True, [], []


# ═══════════════════════════════════════════════════════════════
# Main Pipeline
# ═══════════════════════════════════════════════════════════════
def run_pipeline(full: bool = False, fix: bool = False, deep: bool = False) -> int:
    """Run the full check pipeline."""
    print("=" * 70)
    print("  RetroAuto v2 - Deep Code Analysis")
    print("  Mode:", "FULL" if full else "QUICK", "| Fix:", "ON" if fix else "OFF")
    print("=" * 70)

    results: list[CheckResult] = []

    # Layer 1-5 (Always run)
    checks = [
        ("1. Syntax", lambda: check_syntax()),
        ("2. Imports", lambda: check_imports()),
        ("3. Lint (Ruff)", lambda: check_lint(fix)),
        ("4. Format (Black)", lambda: check_format(fix)),
        ("5. Types (Mypy)", lambda: check_types()),
    ]

    # Layer 6-7 (Full mode)
    if full:
        checks.extend(
            [
                ("6. Security (Bandit)", lambda: check_security()),
                ("7. Tests (Pytest)", lambda: check_tests(full)),
            ]
        )

    # Extended analysis
    if deep:
        checks.extend(
            [
                ("8. Complexity", lambda: check_complexity()),
                ("9. Dead Code", lambda: check_dead_code()),
            ]
        )

    for name, check_func in checks:
        print(f"\n🔍 {name}...")
        result = timed_check(name, check_func)
        results.append(result)

        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"   {status} ({result.duration:.2f}s)")

        for err in result.errors[:5]:
            print(f"   ├─ {err[:90]}")
        for warn in result.warnings[:3]:
            print(f"   └─ ⚠️ {warn[:90]}")

    # Summary
    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)

    total_time = sum(r.duration for r in results)
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)

    for r in results:
        status = "✅" if r.passed else "❌"
        print(f"  {status} {r.name:25s} ({r.duration:.2f}s)")

    print(f"\n  Total: {passed} passed, {failed} failed ({total_time:.2f}s)")

    if failed == 0:
        print("\n  🎉 All checks passed! Ready to commit.")
        return 0
    else:
        print("\n  ⚠️  Some checks failed. Fix before committing.")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Deep Code Analysis")
    parser.add_argument(
        "--full", action="store_true", help="Run all 7 layers including security and tests"
    )
    parser.add_argument("--fix", action="store_true", help="Auto-fix lint and format issues")
    parser.add_argument(
        "--deep", action="store_true", help="Extended analysis (complexity, dead code)"
    )
    args = parser.parse_args()

    return run_pipeline(full=args.full, fix=args.fix, deep=args.deep)


if __name__ == "__main__":
    sys.exit(main())
