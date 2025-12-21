"""
Test runner with Label/Goto flow control.
"""

import pytest

from core.models import (
    AssetImage,
    Click,
    Delay,
    Flow,
    Goto,
    Hotkey,
    IfImage,
    Label,
    Script,
    TypeText,
)
from core.templates import TemplateStore


class MockMatcher:
    """Mock matcher for testing."""

    def __init__(self) -> None:
        self.find_results: dict[str, bool] = {}

    def find(self, asset_id: str, roi_override=None):  # type: ignore
        from core.models import Match

        if self.find_results.get(asset_id, False):
            return Match(x=100, y=100, w=50, h=50, confidence=0.95)
        return None

    def exists(self, asset_id: str, roi_override=None) -> bool:  # type: ignore
        return self.find_results.get(asset_id, False)


class MockWaiter:
    """Mock waiter for testing."""

    def __init__(self) -> None:
        self.success = True

    def wait_appear(self, asset_id, **kwargs):  # type: ignore
        from core.models import Match
        from vision.waiter import WaitOutcome, WaitResult

        if self.success:
            return WaitOutcome(
                result=WaitResult.SUCCESS,
                match=Match(x=100, y=100, w=50, h=50, confidence=0.95),
                elapsed_ms=100,
            )
        return WaitOutcome(result=WaitResult.TIMEOUT, elapsed_ms=1000)

    def wait_vanish(self, asset_id, **kwargs):  # type: ignore
        from vision.waiter import WaitOutcome, WaitResult

        if self.success:
            return WaitOutcome(result=WaitResult.SUCCESS, elapsed_ms=100)
        return WaitOutcome(result=WaitResult.TIMEOUT, elapsed_ms=1000)


class MockMouse:
    """Mock mouse for testing."""

    def __init__(self) -> None:
        self.clicks: list[tuple] = []

    def click(self, x=None, y=None, button="left", clicks=1, interval_ms=80):  # type: ignore
        self.clicks.append((x, y, button, clicks))


class MockKeyboard:
    """Mock keyboard for testing."""

    def __init__(self) -> None:
        self.hotkeys: list[list[str]] = []
        self.typed: list[str] = []

    def hotkey(self, keys: list[str]) -> None:
        self.hotkeys.append(keys)

    def type_text(self, text: str, paste_mode: bool = True, enter: bool = False) -> None:
        self.typed.append(text)


class TestRunner:
    """Test runner functionality."""

    @pytest.fixture
    def setup_runner(self):  # type: ignore
        """Create runner with mocks."""
        from core.engine.context import ExecutionContext
        from core.engine.runner import Runner

        script = Script(
            name="Test",
            flows=[
                Flow(
                    name="main",
                    actions=[
                        Label(name="start"),
                        Delay(ms=10),
                        Label(name="middle"),
                        Delay(ms=10),
                        Goto(label="end"),
                        Delay(ms=10),  # Should be skipped
                        Label(name="end"),
                        Delay(ms=10),
                    ],
                )
            ],
        )

        templates = TemplateStore()
        ctx = ExecutionContext(script=script, templates=templates)

        # Inject mocks
        ctx.matcher = MockMatcher()
        ctx.waiter = MockWaiter()
        ctx.mouse = MockMouse()
        ctx.keyboard = MockKeyboard()

        runner = Runner(ctx)
        return runner, ctx

    def test_label_goto(self, setup_runner) -> None:  # type: ignore
        """Test Label and Goto flow control."""
        runner, ctx = setup_runner

        # Track steps executed
        steps_executed = []

        def on_step(flow: str, idx: int, action) -> None:  # type: ignore
            steps_executed.append(idx)

        runner._on_step = on_step
        success = runner.run_flow("main")

        assert success
        # Should skip step 5 (Delay after Goto)
        # Steps: 0 (Label), 1 (Delay), 2 (Label), 3 (Delay), 4 (Goto), 6 (Label), 7 (Delay)
        assert 5 not in steps_executed

    def test_if_image_then(self, setup_runner) -> None:  # type: ignore
        """Test IfImage when image is found."""
        runner, ctx = setup_runner

        # Modify script for this test
        ctx.script = Script(
            name="Test",
            assets=[AssetImage(id="btn", path="btn.png")],
            flows=[
                Flow(
                    name="main",
                    actions=[
                        IfImage(
                            asset_id="btn",
                            then_actions=[Delay(ms=10)],
                            else_actions=[Delay(ms=20)],
                        )
                    ],
                )
            ],
        )

        # Mock: image IS found
        ctx.matcher.find_results["btn"] = True

        success = runner.run_flow("main")
        assert success

    def test_if_image_else(self, setup_runner) -> None:  # type: ignore
        """Test IfImage when image is NOT found."""
        runner, ctx = setup_runner

        ctx.script = Script(
            name="Test",
            assets=[AssetImage(id="btn", path="btn.png")],
            flows=[
                Flow(
                    name="main",
                    actions=[
                        IfImage(
                            asset_id="btn",
                            then_actions=[Delay(ms=10)],
                            else_actions=[Delay(ms=20)],
                        )
                    ],
                )
            ],
        )

        # Mock: image NOT found
        ctx.matcher.find_results["btn"] = False

        success = runner.run_flow("main")
        assert success

    def test_click_at_match(self, setup_runner) -> None:  # type: ignore
        """Test Click with use_match=True."""
        runner, ctx = setup_runner

        from core.models import Match

        ctx.last_match = Match(x=200, y=300, w=50, h=50, confidence=0.95)

        ctx.script = Script(
            name="Test",
            flows=[
                Flow(
                    name="main",
                    actions=[Click(use_match=True)],
                )
            ],
        )

        success = runner.run_flow("main")
        assert success
        assert len(ctx.mouse.clicks) == 1
        # Should click at center of match (200 + 25, 300 + 25)
        assert ctx.mouse.clicks[0][0] == 225
        assert ctx.mouse.clicks[0][1] == 325

    def test_hotkey(self, setup_runner) -> None:  # type: ignore
        """Test Hotkey action."""
        runner, ctx = setup_runner

        ctx.script = Script(
            name="Test",
            flows=[
                Flow(
                    name="main",
                    actions=[Hotkey(keys=["CTRL", "S"])],
                )
            ],
        )

        success = runner.run_flow("main")
        assert success
        assert ctx.keyboard.hotkeys == [["CTRL", "S"]]

    def test_type_text(self, setup_runner) -> None:  # type: ignore
        """Test TypeText action."""
        runner, ctx = setup_runner

        ctx.script = Script(
            name="Test",
            flows=[
                Flow(
                    name="main",
                    actions=[TypeText(text="Hello World")],
                )
            ],
        )

        success = runner.run_flow("main")
        assert success
        assert ctx.keyboard.typed == ["Hello World"]
