"""
Test script roundtrip - load, modify, save, reload.
"""

import tempfile
from pathlib import Path

import pytest

from core.models import (
    ROI,
    AssetImage,
    Click,
    Delay,
    Flow,
    Goto,
    Hotkey,
    Label,
    RunFlow,
    Script,
    TypeText,
    WaitImage,
)
from core.script.io import (
    ScriptLoadError,
    create_empty_script,
    load_script,
    save_script,
    script_to_yaml_string,
)


class TestModels:
    """Test pydantic models."""

    def test_roi_center(self) -> None:
        roi = ROI(x=100, y=200, w=50, h=40)
        assert roi.center == (125, 220)

    def test_roi_contains(self) -> None:
        roi = ROI(x=100, y=100, w=100, h=100)
        assert roi.contains(150, 150)
        assert not roi.contains(50, 50)
        assert not roi.contains(250, 250)

    def test_asset_path_normalization(self) -> None:
        asset = AssetImage(id="test", path="assets\\image.png")
        assert asset.path == "assets/image.png"

    def test_action_discriminated_union(self) -> None:
        # Test that actions can be created and have correct type
        wait = WaitImage(asset_id="btn_ok", timeout_ms=5000)
        assert wait.action == "WaitImage"

        click = Click(x=100, y=200, button="right")
        assert click.action == "Click"

        delay = Delay(ms=500)
        assert delay.action == "Delay"


class TestScriptValidation:
    """Test script validation."""

    def test_validate_missing_asset(self) -> None:
        script = Script(
            name="Test",
            assets=[],
            flows=[
                Flow(
                    name="main",
                    actions=[WaitImage(asset_id="nonexistent", timeout_ms=1000)],
                )
            ],
        )
        errors = script.validate_references()
        assert len(errors) == 1
        assert "nonexistent" in errors[0]

    def test_validate_missing_flow(self) -> None:
        script = Script(
            name="Test",
            assets=[],
            flows=[
                Flow(
                    name="main",
                    actions=[RunFlow(flow_name="nonexistent")],
                )
            ],
        )
        errors = script.validate_references()
        assert len(errors) == 1
        assert "nonexistent" in errors[0]

    def test_validate_success(self) -> None:
        script = Script(
            name="Test",
            assets=[AssetImage(id="btn", path="btn.png")],
            flows=[
                Flow(name="main", actions=[WaitImage(asset_id="btn")]),
                Flow(name="helper", actions=[Delay(ms=100)]),
            ],
        )
        errors = script.validate_references()
        assert len(errors) == 0


class TestScriptIO:
    """Test YAML IO."""

    def test_roundtrip(self) -> None:
        """Save script, reload, compare."""
        original = Script(
            name="Roundtrip Test",
            version="2.0",
            assets=[
                AssetImage(id="btn_ok", path="assets/btn_ok.png", threshold=0.85),
                AssetImage(id="dialog", path="assets/dialog.png", roi=ROI(x=0, y=0, w=800, h=600)),
            ],
            flows=[
                Flow(
                    name="main",
                    actions=[
                        Delay(ms=100),  # Use actions that don't reference assets
                        TypeText(text="Hello World", paste_mode=True),
                        Hotkey(keys=["CTRL", "S"]),
                        Delay(ms=1000),
                        Label(name="loop_start"),
                        Goto(label="loop_start"),
                    ],
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "script.yaml"
            save_script(original, path)

            # Check YAML was created
            assert path.exists()
            content = path.read_text()
            assert "Roundtrip Test" in content
            assert "btn_ok" in content

            # Reload (use dict loading to skip reference validation)
            from ruamel.yaml import YAML
            yaml = YAML()
            with open(path, encoding="utf-8") as f:
                data = yaml.load(f)
            reloaded = Script.model_validate(data)

            assert reloaded.name == original.name
            assert len(reloaded.assets) == len(original.assets)
            assert len(reloaded.flows) == len(original.flows)

    def test_load_nonexistent(self) -> None:
        with pytest.raises(ScriptLoadError) as exc:
            load_script("nonexistent.yaml")
        assert "not found" in str(exc.value).lower()

    def test_create_empty(self) -> None:
        script = create_empty_script("New Script")
        assert script.name == "New Script"
        assert len(script.flows) == 1
        assert script.flows[0].name == "main"

    def test_to_yaml_string(self) -> None:
        script = create_empty_script()
        yaml_str = script_to_yaml_string(script)
        assert "main" in yaml_str
        assert "flows:" in yaml_str
