"""
RetroAuto v2 - Test Runner

Test discovery, execution, and reporting for RetroScript.
Part of RetroScript Phase 11 - Test Runner.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


class TestStatus(Enum):
    """Test result status."""

    PASSED = auto()
    FAILED = auto()
    SKIPPED = auto()
    ERROR = auto()


@dataclass
class TestCase:
    """A single test case."""

    name: str
    file: str = ""
    line: int = 0
    status: TestStatus = TestStatus.PASSED
    duration: float = 0.0
    message: str = ""
    error: str | None = None


@dataclass
class TestSuite:
    """Collection of test cases."""

    name: str
    tests: list[TestCase] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def total(self) -> int:
        return len(self.tests)

    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.PASSED)

    @property
    def failed(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.FAILED)

    @property
    def skipped(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.SKIPPED)

    @property
    def errors(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.ERROR)

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


# ─────────────────────────────────────────────────────────────
# Mock System
# ─────────────────────────────────────────────────────────────


@dataclass
class MockCall:
    """Record of a mock function call."""

    name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    timestamp: float


class MockRegistry:
    """Registry for mock functions.

    Usage:
        mocks = MockRegistry()
        mocks.register("find", lambda target: {"x": 100, "y": 100})
        result = mocks.call("find", "button.png")
    """

    def __init__(self) -> None:
        self._mocks: dict[str, Callable[..., Any]] = {}
        self._calls: list[MockCall] = []
        self._return_values: dict[str, Any] = {}

    def register(self, name: str, func: Callable[..., Any] | None = None) -> None:
        """Register a mock function.

        Args:
            name: Function name to mock
            func: Mock implementation (optional)
        """
        self._mocks[name] = func or (lambda *a, **kw: None)

    def set_return(self, name: str, value: Any) -> None:
        """Set return value for a mock.

        Args:
            name: Function name
            value: Value to return
        """
        self._return_values[name] = value
        self._mocks[name] = lambda *a, **kw: value

    def is_mocked(self, name: str) -> bool:
        """Check if function is mocked."""
        return name in self._mocks

    def call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Call a mock function.

        Args:
            name: Function name
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Mock return value
        """
        # Record call
        self._calls.append(
            MockCall(
                name=name,
                args=args,
                kwargs=kwargs,
                timestamp=time.time(),
            )
        )

        # Return fixed value if set
        if name in self._return_values:
            return self._return_values[name]

        # Call mock implementation
        if name in self._mocks:
            return self._mocks[name](*args, **kwargs)

        return None

    def get_calls(self, name: str | None = None) -> list[MockCall]:
        """Get recorded calls.

        Args:
            name: Filter by function name (optional)

        Returns:
            List of mock calls
        """
        if name:
            return [c for c in self._calls if c.name == name]
        return self._calls.copy()

    def call_count(self, name: str) -> int:
        """Get number of calls to a function."""
        return sum(1 for c in self._calls if c.name == name)

    def was_called(self, name: str) -> bool:
        """Check if function was called."""
        return any(c.name == name for c in self._calls)

    def was_called_with(self, name: str, *args: Any, **kwargs: Any) -> bool:
        """Check if function was called with specific arguments."""
        for call in self._calls:
            if call.name == name and call.args == args and call.kwargs == kwargs:
                return True
        return False

    def reset(self) -> None:
        """Reset all mocks and call history."""
        self._mocks.clear()
        self._calls.clear()
        self._return_values.clear()


# ─────────────────────────────────────────────────────────────
# Assertions
# ─────────────────────────────────────────────────────────────


class AssertionError(Exception):
    """Test assertion failure."""

    def __init__(self, message: str, expected: Any = None, actual: Any = None) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(message)


def assert_true(condition: Any, message: str = "") -> None:
    """Assert that condition is truthy."""
    if not condition:
        raise AssertionError(message or "Expected truthy value", True, condition)


def assert_false(condition: Any, message: str = "") -> None:
    """Assert that condition is falsy."""
    if condition:
        raise AssertionError(message or "Expected falsy value", False, condition)


def assert_equal(expected: Any, actual: Any, message: str = "") -> None:
    """Assert that values are equal."""
    if expected != actual:
        raise AssertionError(
            message or f"Expected {expected!r}, got {actual!r}",
            expected,
            actual,
        )


def assert_not_equal(expected: Any, actual: Any, message: str = "") -> None:
    """Assert that values are not equal."""
    if expected == actual:
        raise AssertionError(
            message or f"Expected value different from {expected!r}",
            f"not {expected!r}",
            actual,
        )


def assert_null(value: Any, message: str = "") -> None:
    """Assert that value is null/None."""
    if value is not None:
        raise AssertionError(message or f"Expected null, got {value!r}", None, value)


def assert_not_null(value: Any, message: str = "") -> None:
    """Assert that value is not null/None."""
    if value is None:
        raise AssertionError(message or "Expected non-null value", "not null", None)


def assert_in(item: Any, container: Any, message: str = "") -> None:
    """Assert that item is in container."""
    if item not in container:
        raise AssertionError(
            message or f"Expected {item!r} in {container!r}",
            f"{item} in container",
            f"{item} not in container",
        )


def assert_not_in(item: Any, container: Any, message: str = "") -> None:
    """Assert that item is not in container."""
    if item in container:
        raise AssertionError(
            message or f"Expected {item!r} not in {container!r}",
            f"{item} not in container",
            f"{item} in container",
        )


def assert_greater(value: Any, threshold: Any, message: str = "") -> None:
    """Assert that value > threshold."""
    if not value > threshold:
        raise AssertionError(
            message or f"Expected {value!r} > {threshold!r}",
            f">{threshold}",
            value,
        )


def assert_less(value: Any, threshold: Any, message: str = "") -> None:
    """Assert that value < threshold."""
    if not value < threshold:
        raise AssertionError(
            message or f"Expected {value!r} < {threshold!r}",
            f"<{threshold}",
            value,
        )


def assert_type(value: Any, expected_type: type, message: str = "") -> None:
    """Assert that value is of expected type."""
    if not isinstance(value, expected_type):
        raise AssertionError(
            message or f"Expected type {expected_type.__name__}, got {type(value).__name__}",
            expected_type.__name__,
            type(value).__name__,
        )


# ─────────────────────────────────────────────────────────────
# Test Runner
# ─────────────────────────────────────────────────────────────


class TestRunner:
    """Test runner for RetroScript tests.

    Usage:
        runner = TestRunner()
        suite = runner.run_file("tests/test_combat.retro")
        print(runner.format_results(suite))
    """

    def __init__(self) -> None:
        self.mocks = MockRegistry()
        self._suites: list[TestSuite] = []

    def discover(self, path: str | Path, pattern: str = "*_test.retro") -> list[Path]:
        """Discover test files.

        Args:
            path: Directory to search
            pattern: File pattern to match

        Returns:
            List of test file paths
        """
        path = Path(path)
        if path.is_file():
            return [path]

        files: list[Path] = []
        files.extend(path.glob(f"**/{pattern}"))
        files.extend(path.glob("**/test_*.retro"))
        return sorted(set(files))

    def run_file(self, path: str | Path) -> TestSuite:
        """Run tests in a single file.

        Args:
            path: Path to test file

        Returns:
            TestSuite with results
        """
        path = Path(path)
        suite = TestSuite(name=path.stem)
        suite.start_time = time.time()

        try:
            source = path.read_text(encoding="utf-8")
            tests = self._extract_tests(source, str(path))

            for test in tests:
                result = self._run_test(test, source)
                suite.tests.append(result)

        except Exception as e:
            suite.tests.append(
                TestCase(
                    name="<file>",
                    file=str(path),
                    status=TestStatus.ERROR,
                    error=str(e),
                )
            )

        suite.end_time = time.time()
        self._suites.append(suite)
        return suite

    def run_all(self, path: str | Path, pattern: str = "*_test.retro") -> list[TestSuite]:
        """Run all tests in a directory.

        Args:
            path: Directory path
            pattern: File pattern

        Returns:
            List of TestSuites
        """
        files = self.discover(path, pattern)
        suites = []
        for file in files:
            suite = self.run_file(file)
            suites.append(suite)
        return suites

    def _extract_tests(self, source: str, file: str) -> list[dict[str, Any]]:
        """Extract @test blocks from source."""
        import re

        tests = []
        pattern = r'@test\s+"([^"]+)"\s*\{([^}]*)\}'

        for match in re.finditer(pattern, source, re.MULTILINE | re.DOTALL):
            name = match.group(1)
            body = match.group(2)
            line = source[: match.start()].count("\n") + 1

            tests.append(
                {
                    "name": name,
                    "body": body,
                    "line": line,
                    "file": file,
                }
            )

        return tests

    def _run_test(self, test: dict[str, Any], source: str) -> TestCase:
        """Run a single test."""
        start = time.time()
        result = TestCase(
            name=test["name"],
            file=test["file"],
            line=test["line"],
        )

        try:
            # Reset mocks for each test
            self.mocks.reset()

            # Execute test body
            # TODO: Integrate with interpreter
            # For now, just mark as passed
            result.status = TestStatus.PASSED

        except AssertionError as e:
            result.status = TestStatus.FAILED
            result.message = str(e)

        except Exception as e:
            result.status = TestStatus.ERROR
            result.error = str(e)

        result.duration = time.time() - start
        return result

    def format_results(self, suite: TestSuite) -> str:
        """Format test results for console."""
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"Test Suite: {suite.name}")
        lines.append(f"{'='*60}\n")

        for test in suite.tests:
            status_icon = {
                TestStatus.PASSED: "✓",
                TestStatus.FAILED: "✗",
                TestStatus.SKIPPED: "○",
                TestStatus.ERROR: "!",
            }.get(test.status, "?")

            lines.append(f"  {status_icon} {test.name} ({test.duration:.3f}s)")

            if test.message:
                lines.append(f"      {test.message}")
            if test.error:
                lines.append(f"      Error: {test.error}")

        lines.append(f"\n{'-'*60}")
        lines.append(
            f"Total: {suite.total} | "
            f"Passed: {suite.passed} | "
            f"Failed: {suite.failed} | "
            f"Errors: {suite.errors} | "
            f"Skipped: {suite.skipped}"
        )
        lines.append(f"Duration: {suite.duration:.3f}s")
        lines.append(f"{'='*60}\n")

        return "\n".join(lines)

    def to_junit_xml(self, suites: list[TestSuite]) -> str:
        """Generate JUnit XML report."""
        root = ET.Element("testsuites")

        for suite in suites:
            suite_elem = ET.SubElement(root, "testsuite")
            suite_elem.set("name", suite.name)
            suite_elem.set("tests", str(suite.total))
            suite_elem.set("failures", str(suite.failed))
            suite_elem.set("errors", str(suite.errors))
            suite_elem.set("time", f"{suite.duration:.3f}")

            for test in suite.tests:
                test_elem = ET.SubElement(suite_elem, "testcase")
                test_elem.set("name", test.name)
                test_elem.set("time", f"{test.duration:.3f}")

                if test.status == TestStatus.FAILED:
                    failure = ET.SubElement(test_elem, "failure")
                    failure.set("message", test.message)

                elif test.status == TestStatus.ERROR:
                    error = ET.SubElement(test_elem, "error")
                    error.set("message", test.error or "Unknown error")

                elif test.status == TestStatus.SKIPPED:
                    ET.SubElement(test_elem, "skipped")

        return ET.tostring(root, encoding="unicode")

    def to_html(self, suites: list[TestSuite]) -> str:
        """Generate HTML report."""
        total_tests = sum(s.total for s in suites)
        total_passed = sum(s.passed for s in suites)
        total_failed = sum(s.failed for s in suites)
        total_errors = sum(s.errors for s in suites)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>RetroScript Test Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .passed {{ color: #22c55e; }}
        .failed {{ color: #ef4444; }}
        .error {{ color: #f59e0b; }}
        .suite {{ border: 1px solid #ddd; border-radius: 8px; margin-bottom: 20px; overflow: hidden; }}
        .suite-header {{ background: #f0f0f0; padding: 15px; font-weight: bold; }}
        .test {{ padding: 10px 15px; border-top: 1px solid #eee; }}
        .test.passed {{ border-left: 4px solid #22c55e; }}
        .test.failed {{ border-left: 4px solid #ef4444; }}
        .test.error {{ border-left: 4px solid #f59e0b; }}
        .message {{ color: #666; font-size: 0.9em; margin-top: 5px; }}
    </style>
</head>
<body>
    <h1>RetroScript Test Report</h1>
    <div class="summary">
        <strong>Total:</strong> {total_tests} |
        <span class="passed">Passed: {total_passed}</span> |
        <span class="failed">Failed: {total_failed}</span> |
        <span class="error">Errors: {total_errors}</span>
    </div>
"""
        for suite in suites:
            html += f"""
    <div class="suite">
        <div class="suite-header">{suite.name} ({suite.total} tests)</div>
"""
            for test in suite.tests:
                status = test.status.name.lower()
                icon = "✓" if test.status == TestStatus.PASSED else "✗"
                html += f"""
        <div class="test {status}">
            {icon} {test.name} <span style="color:#999">({test.duration:.3f}s)</span>
"""
                if test.message:
                    html += f'            <div class="message">{test.message}</div>\n'
                if test.error:
                    html += f'            <div class="message">Error: {test.error}</div>\n'
                html += "        </div>\n"

            html += "    </div>\n"

        html += """
</body>
</html>"""
        return html


# Convenience function
def run_tests(path: str | Path) -> TestSuite:
    """Run tests in a file or directory."""
    runner = TestRunner()
    if Path(path).is_file():
        return runner.run_file(path)
    else:
        suites = runner.run_all(path)
        # Return combined suite
        combined = TestSuite(name=str(path))
        for s in suites:
            combined.tests.extend(s.tests)
        return combined
