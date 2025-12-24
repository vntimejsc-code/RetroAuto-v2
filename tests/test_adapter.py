"""
Tests for DSL Adapter (IR <-> Action conversion).
"""

import pytest

from core.dsl.ir import ActionIR
from core.dsl.adapter import (
    ir_to_action,
    ir_to_actions,
    DSLToYAMLAdapter,
)
from core.models import (
    Click,
    Delay,
    DelayRandom,
    Hotkey,
    Label,
    Loop,
    Goto,
    TypeText,
    WaitImage,
    EndIf,
    EndLoop,
    Else,
)


class TestIRToAction:
    """Test IR to Action conversion."""

    def test_ir_to_click(self) -> None:
        """Convert click ActionIR to Click model."""
        ir = ActionIR(action_type="click", params={"arg0": 100, "arg1": 200})
        action = ir_to_action(ir)
        
        assert action is not None
        assert isinstance(action, Click)
        assert action.x == 100
        assert action.y == 200

    def test_ir_to_delay(self) -> None:
        """Convert sleep ActionIR to Delay model."""
        ir = ActionIR(action_type="sleep", params={"arg0": 500})
        action = ir_to_action(ir)
        
        assert action is not None
        assert isinstance(action, Delay)
        assert action.ms == 500

    def test_ir_to_delay_random(self) -> None:
        """Convert delay_random ActionIR to DelayRandom model."""
        ir = ActionIR(action_type="delay_random", params={"arg0": 100, "arg1": 500})
        action = ir_to_action(ir)
        
        assert action is not None
        assert isinstance(action, DelayRandom)
        assert action.min_ms == 100
        assert action.max_ms == 500

    def test_ir_to_wait_image(self) -> None:
        """Convert wait_image ActionIR to WaitImage model."""
        ir = ActionIR(action_type="wait_image", params={"arg0": "dialog", "timeout": 5000})
        action = ir_to_action(ir)
        
        assert action is not None
        assert isinstance(action, WaitImage)
        assert action.asset_id == "dialog"
        assert action.timeout_ms == 5000

    def test_ir_to_loop(self) -> None:
        """Convert loop ActionIR to Loop model."""
        ir = ActionIR(action_type="loop", params={"count": 5})
        action = ir_to_action(ir)
        
        assert action is not None
        assert isinstance(action, Loop)
        assert action.count == 5

    def test_ir_to_label(self) -> None:
        """Convert label ActionIR to Label model."""
        ir = ActionIR(action_type="label", params={"name": "start_point"})
        action = ir_to_action(ir)
        
        assert action is not None
        assert isinstance(action, Label)
        assert action.name == "start_point"

    def test_ir_to_goto(self) -> None:
        """Convert goto ActionIR to Goto model."""
        ir = ActionIR(action_type="goto", params={"label": "start_point"})
        action = ir_to_action(ir)
        
        assert action is not None
        assert isinstance(action, Goto)
        assert action.label == "start_point"

    def test_ir_to_type_text(self) -> None:
        """Convert type ActionIR to TypeText model."""
        ir = ActionIR(action_type="type", params={"arg0": "Hello World", "enter": True})
        action = ir_to_action(ir)
        
        assert action is not None
        assert isinstance(action, TypeText)
        assert action.text == "Hello World"
        assert action.enter is True

    def test_ir_to_hotkey(self) -> None:
        """Convert hotkey ActionIR to Hotkey model."""
        ir = ActionIR(action_type="hotkey", params={"keys": ["ctrl", "s"]})
        action = ir_to_action(ir)
        
        assert action is not None
        assert isinstance(action, Hotkey)
        assert action.keys == ["ctrl", "s"]

    def test_ir_to_end_if(self) -> None:
        """Convert end_if ActionIR to EndIf model."""
        ir = ActionIR(action_type="end_if", params={})
        action = ir_to_action(ir)
        
        assert action is not None
        assert isinstance(action, EndIf)

    def test_ir_to_end_loop(self) -> None:
        """Convert end_loop ActionIR to EndLoop model."""
        ir = ActionIR(action_type="end_loop", params={})
        action = ir_to_action(ir)
        
        assert action is not None
        assert isinstance(action, EndLoop)

    def test_ir_to_else(self) -> None:
        """Convert else ActionIR to Else model."""
        ir = ActionIR(action_type="else", params={})
        action = ir_to_action(ir)
        
        assert action is not None
        assert isinstance(action, Else)

    def test_unknown_action_returns_none(self) -> None:
        """Unknown action type returns None."""
        ir = ActionIR(action_type="unknown_action_xyz", params={})
        action = ir_to_action(ir)
        
        assert action is None


class TestIRToActions:
    """Test batch conversion of IR to Actions."""

    def test_empty_list(self) -> None:
        """Empty IR list produces empty action list."""
        actions = ir_to_actions([])
        assert actions == []

    def test_multiple_actions(self) -> None:
        """Multiple IRs convert to multiple actions."""
        irs = [
            ActionIR(action_type="click", params={"arg0": 10, "arg1": 20}),
            ActionIR(action_type="sleep", params={"arg0": 100}),
            ActionIR(action_type="click", params={"arg0": 30, "arg1": 40}),
        ]
        actions = ir_to_actions(irs)
        
        assert len(actions) == 3
        assert isinstance(actions[0], Click)
        assert isinstance(actions[1], Delay)
        assert isinstance(actions[2], Click)

    def test_skips_invalid_actions(self) -> None:
        """Invalid actions are skipped, not added to list."""
        irs = [
            ActionIR(action_type="click", params={"arg0": 10, "arg1": 20}),
            ActionIR(action_type="invalid_action_xyz", params={}),
            ActionIR(action_type="sleep", params={"arg0": 100}),
        ]
        actions = ir_to_actions(irs)
        
        # Invalid action skipped
        assert len(actions) == 2
        assert isinstance(actions[0], Click)
        assert isinstance(actions[1], Delay)


class TestDSLAdapter:
    """Test the DSL to YAML adapter class."""

    def test_parse_duration_seconds(self) -> None:
        """Parse duration with 's' suffix."""
        adapter = DSLToYAMLAdapter()
        ms = adapter._parse_duration("5s")
        assert ms == 5000

    def test_parse_duration_milliseconds(self) -> None:
        """Parse duration with 'ms' suffix."""
        adapter = DSLToYAMLAdapter()
        ms = adapter._parse_duration("500ms")
        assert ms == 500

    def test_parse_duration_numeric(self) -> None:
        """Parse numeric duration (assumed ms)."""
        adapter = DSLToYAMLAdapter()
        ms = adapter._parse_duration("250")
        assert ms == 250
