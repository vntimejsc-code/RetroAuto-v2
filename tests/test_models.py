"""
Tests for core/models.py - Action models
"""

import pytest
from core.models import (
    ROI,
    AssetImage,
    Match,
    WaitImage,
    Click,
    IfImage,
    Hotkey,
    TypeText,
    Label,
    Goto,
    RunFlow,
    Delay,
    Flow,
    InterruptRule,
    MatchMethod,
)


class TestROI:
    """Tests for ROI model."""
    
    def test_roi_creation(self):
        roi = ROI(x=10, y=20, w=100, h=200)
        assert roi.x == 10
        assert roi.y == 20
        assert roi.w == 100
        assert roi.h == 200


class TestAssetImage:
    """Tests for AssetImage model."""
    
    def test_asset_creation(self):
        asset = AssetImage(
            id="btn_ok",
            path="assets/btn_ok.png",
            threshold=0.8
        )
        assert asset.id == "btn_ok"
        assert asset.path == "assets/btn_ok.png"
        assert asset.threshold == 0.8
    
    def test_asset_defaults(self):
        asset = AssetImage(id="test", path="test.png")
        assert asset.threshold == 0.8  # Default
        assert asset.grayscale is True
        assert asset.roi is None


class TestMatch:
    """Tests for Match model."""
    
    def test_match_creation(self):
        match = Match(
            asset_id="btn_ok",
            x=100,
            y=200,
            w=50,
            h=30,
            confidence=0.95
        )
        assert match.center == (125, 215)
    
    def test_match_center_calculation(self):
        match = Match(
            asset_id="test",
            x=0,
            y=0,
            w=100,
            h=100,
            confidence=0.9
        )
        assert match.center == (50, 50)


class TestActions:
    """Tests for Action models."""
    
    def test_wait_image(self):
        action = WaitImage(
            asset_id="btn_ok",
            appear=True,
            timeout_ms=5000
        )
        assert action.action == "WaitImage"
        assert action.asset_id == "btn_ok"
        assert action.appear is True
        assert action.timeout_ms == 5000
    
    def test_click(self):
        action = Click(x=100, y=200, button="left", clicks=1)
        assert action.action == "Click"
        assert action.x == 100
        assert action.y == 200
        assert action.button == "left"
    
    def test_click_at_match(self):
        action = Click(use_match=True)
        assert action.use_match is True
        assert action.x is None
    
    def test_double_click(self):
        action = Click(x=100, y=200, clicks=2)
        assert action.clicks == 2
    
    def test_right_click(self):
        action = Click(x=100, y=200, button="right")
        assert action.button == "right"
    
    def test_if_image(self):
        then_actions = [Click(x=10, y=10)]
        else_actions = [Delay(ms=1000)]
        action = IfImage(
            asset_id="btn",
            then_actions=then_actions,
            else_actions=else_actions
        )
        assert action.action == "IfImage"
        assert len(action.then_actions) == 1
        assert len(action.else_actions) == 1
    
    def test_hotkey(self):
        action = Hotkey(keys=["CTRL", "S"])
        assert action.action == "Hotkey"
        assert action.keys == ["CTRL", "S"]
    
    def test_type_text(self):
        action = TypeText(text="Hello World")
        assert action.action == "TypeText"
        assert action.text == "Hello World"
    
    def test_label(self):
        action = Label(name="start")
        assert action.action == "Label"
        assert action.name == "start"
    
    def test_goto(self):
        action = Goto(label="start")
        assert action.action == "Goto"
        assert action.label == "start"
    
    def test_run_flow(self):
        action = RunFlow(flow_name="login")
        assert action.action == "RunFlow"
        assert action.flow_name == "login"
    
    def test_delay(self):
        action = Delay(ms=1000)
        assert action.action == "Delay"
        assert action.ms == 1000


class TestFlow:
    """Tests for Flow model."""
    
    def test_flow_creation(self):
        flow = Flow(
            name="main",
            actions=[
                WaitImage(asset_id="btn"),
                Click(x=100, y=100)
            ]
        )
        assert flow.name == "main"
        assert len(flow.actions) == 2
    
    def test_empty_flow(self):
        flow = Flow(name="empty")
        assert flow.actions == []


class TestMatchMethod:
    """Tests for MatchMethod enum."""
    
    def test_match_methods_exist(self):
        assert hasattr(MatchMethod, "TM_CCOEFF_NORMED")
        assert hasattr(MatchMethod, "TM_SQDIFF_NORMED")
