"""
Tests for core/dsl/ir.py - Intermediate Representation
"""

from core.dsl.ir import (
    ActionIR,
    AssetIR,
    FlowIR,
    HotkeysIR,
    InterruptIR,
    IRMapper,
    ScriptIR,
    ir_to_code,
    parse_to_ir,
)


class TestAssetIR:
    """Tests for AssetIR dataclass."""

    def test_asset_creation(self):
        asset = AssetIR(id="btn_ok", path="btn_ok.png")
        assert asset.id == "btn_ok"
        assert asset.path == "btn_ok.png"

    def test_asset_defaults(self):
        asset = AssetIR(id="test", path="test.png")
        assert asset.threshold == 0.8
        assert asset.roi is None

    def test_asset_with_roi(self):
        asset = AssetIR(id="test", path="test.png", roi={"x": 10, "y": 20, "w": 100, "h": 200})
        assert asset.roi["x"] == 10


class TestActionIR:
    """Tests for ActionIR dataclass."""

    def test_action_creation(self):
        action = ActionIR(action_type="Click", params={"x": 100, "y": 200})
        assert action.action_type == "Click"
        assert action.params["x"] == 100

    def test_action_defaults(self):
        action = ActionIR(action_type="Delay")
        assert action.params == {}
        assert action.span_line is None

    def test_action_with_line(self):
        action = ActionIR(action_type="Click", params={}, span_line=42)
        assert action.span_line == 42


class TestFlowIR:
    """Tests for FlowIR dataclass."""

    def test_flow_creation(self):
        flow = FlowIR(name="main")
        assert flow.name == "main"
        assert flow.actions == []

    def test_flow_with_actions(self):
        actions = [
            ActionIR(action_type="Click", params={"x": 100, "y": 100}),
            ActionIR(action_type="Delay", params={"ms": 500}),
        ]
        flow = FlowIR(name="main", actions=actions)
        assert len(flow.actions) == 2


class TestInterruptIR:
    """Tests for InterruptIR dataclass."""

    def test_interrupt_creation(self):
        interrupt = InterruptIR(priority=10, when_asset="error_popup")
        assert interrupt.priority == 10
        assert interrupt.when_asset == "error_popup"

    def test_interrupt_with_actions(self):
        interrupt = InterruptIR(
            priority=5, when_asset="popup", actions=[ActionIR(action_type="Click", params={})]
        )
        assert len(interrupt.actions) == 1


class TestHotkeysIR:
    """Tests for HotkeysIR dataclass."""

    def test_hotkeys_defaults(self):
        hotkeys = HotkeysIR()
        assert hotkeys.start == "F5"
        assert hotkeys.stop == "F6"
        assert hotkeys.pause == "F7"

    def test_hotkeys_custom(self):
        hotkeys = HotkeysIR(start="F1", stop="F2", pause="F3")
        assert hotkeys.start == "F1"


class TestScriptIR:
    """Tests for ScriptIR dataclass."""

    def test_script_defaults(self):
        script = ScriptIR()
        assert script.name == "Untitled"
        assert script.version == "1.0"
        assert script.assets == []
        assert script.flows == []

    def test_script_custom(self):
        script = ScriptIR(name="MyScript", version="2.0")
        assert script.name == "MyScript"
        assert script.version == "2.0"

    def test_add_asset(self):
        script = ScriptIR()
        asset = AssetIR(id="btn", path="btn.png")
        script.add_asset(asset)
        assert script.get_asset("btn") is not None

    def test_remove_asset(self):
        script = ScriptIR()
        asset = AssetIR(id="btn", path="btn.png")
        script.add_asset(asset)
        script.remove_asset("btn")
        assert script.get_asset("btn") is None

    def test_add_flow(self):
        script = ScriptIR()
        flow = FlowIR(name="main")
        script.add_flow(flow)
        assert script.get_flow("main") is not None

    def test_remove_flow(self):
        script = ScriptIR()
        flow = FlowIR(name="main")
        script.add_flow(flow)
        script.remove_flow("main")
        assert script.get_flow("main") is None

    def test_listener(self):
        script = ScriptIR()
        changes = []

        def listener(change_type):
            changes.append(change_type)

        script.add_listener(listener)
        script.notify_change("test_change")

        assert "test_change" in changes

    def test_remove_listener(self):
        script = ScriptIR()
        changes = []

        def listener(change_type):
            changes.append(change_type)

        script.add_listener(listener)
        script.remove_listener(listener)
        script.notify_change("test")

        assert len(changes) == 0


class TestParseToIR:
    """Tests for parse_to_ir function."""

    def test_parse_simple_flow(self):
        source = """
flow main {
    click(100, 200);
}
"""
        ir, errors = parse_to_ir(source)
        assert ir is not None
        assert len(errors) == 0

    def test_parse_invalid_syntax(self):
        source = "flow { }"  # Missing flow name
        ir, errors = parse_to_ir(source)
        assert len(errors) > 0


class TestIRToCode:
    """Tests for ir_to_code function."""

    def test_empty_script_to_code(self):
        script = ScriptIR()
        code = ir_to_code(script)
        assert isinstance(code, str)

    def test_script_with_flow_to_code(self):
        script = ScriptIR()
        flow = FlowIR(
            name="main",
            actions=[
                ActionIR(action_type="click", params={"x": 100, "y": 200}),
            ],
        )
        script.add_flow(flow)

        code = ir_to_code(script)
        assert "flow main" in code or "main" in code


class TestIRMapper:
    """Tests for IRMapper class."""

    def test_ir_to_code(self):
        script = ScriptIR()
        code = IRMapper.ir_to_code(script)
        assert isinstance(code, str)
