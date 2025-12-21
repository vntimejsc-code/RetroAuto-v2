"""
Tests for DSL Semantic Analyzer.
"""

import pytest

from core.dsl.parser import Parser
from core.dsl.semantic import SemanticAnalyzer, analyze
from core.dsl.diagnostics import Severity


class TestSemanticAssets:
    """Test asset reference validation."""

    def test_unknown_asset_error(self) -> None:
        """Unknown asset produces error."""
        source = """
        flow main {
            wait_image("unknown_button");
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program, known_assets=[])

        assert len(diagnostics) > 0
        assert any("unknown_button" in d.message for d in diagnostics)
        assert any(d.code == "E1101" for d in diagnostics)

    def test_known_asset_no_error(self) -> None:
        """Known asset produces no error."""
        source = """
        flow main {
            wait_image("btn_ok");
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program, known_assets=["btn_ok"])

        asset_errors = [d for d in diagnostics if d.code == "E1101"]
        assert len(asset_errors) == 0

    def test_wait_any_assets(self) -> None:
        """wait_any validates all assets in array."""
        source = """
        flow main {
            wait_any(["btn1", "btn2", "btn3"]);
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program, known_assets=["btn1"])

        # Should report btn2 and btn3 as unknown
        asset_errors = [d for d in diagnostics if d.code == "E1101"]
        assert len(asset_errors) >= 2

    def test_asset_quick_fix(self) -> None:
        """Unknown asset has quick fix."""
        source = """
        flow main {
            wait_image("new_button");
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program, known_assets=[])

        asset_error = next(d for d in diagnostics if d.code == "E1101")
        assert asset_error.quick_fixes is not None
        assert len(asset_error.quick_fixes) > 0
        assert asset_error.quick_fixes[0].action == "capture_asset"


class TestSemanticFlows:
    """Test flow reference validation."""

    def test_unknown_flow_error(self) -> None:
        """Unknown flow produces error."""
        source = """
        flow main {
            run_flow("nonexistent");
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program)

        assert any(d.code == "E1102" for d in diagnostics)
        assert any("nonexistent" in d.message for d in diagnostics)

    def test_known_flow_no_error(self) -> None:
        """Known flow produces no error."""
        source = """
        flow main {
            run_flow("helper");
        }

        flow helper {
            log("helping");
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program)

        flow_errors = [d for d in diagnostics if d.code == "E1102"]
        assert len(flow_errors) == 0


class TestSemanticLabels:
    """Test label/goto validation."""

    def test_unknown_label_error(self) -> None:
        """Goto unknown label produces error."""
        source = """
        flow main {
            goto nonexistent;
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program)

        assert any(d.code == "E1103" for d in diagnostics)

    def test_known_label_no_error(self) -> None:
        """Goto known label produces no error."""
        source = """
        flow main {
            label start:
            sleep(1s);
            goto start;
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program)

        label_errors = [d for d in diagnostics if d.code == "E1103"]
        assert len(label_errors) == 0

    def test_duplicate_label_error(self) -> None:
        """Duplicate label produces error."""
        source = """
        flow main {
            label start:
            sleep(1s);
            label start:
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program)

        assert any(d.code == "E1104" for d in diagnostics)

    def test_labels_scoped_to_flow(self) -> None:
        """Labels are scoped to their flow."""
        source = """
        flow main {
            goto helper_label;
        }

        flow helper {
            label helper_label:
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program)

        # goto helper_label should fail because it's in different flow
        assert any(d.code == "E1103" for d in diagnostics)


class TestSemanticDuplicates:
    """Test duplicate definition detection."""

    def test_duplicate_flow_error(self) -> None:
        """Duplicate flow produces error."""
        source = """
        flow main {
            log("first");
        }

        flow main {
            log("second");
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program)

        assert any(d.code == "E1105" for d in diagnostics)


class TestSemanticFunctionCalls:
    """Test function call validation."""

    def test_missing_required_argument(self) -> None:
        """Missing required argument produces error."""
        source = """
        flow main {
            click();
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program)

        assert any(d.code == "E1109" for d in diagnostics)

    def test_all_required_args_no_error(self) -> None:
        """All required args produces no error."""
        source = """
        flow main {
            click(100, 200);
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program)

        arg_errors = [d for d in diagnostics if d.code == "E1109"]
        assert len(arg_errors) == 0


class TestSemanticInterrupts:
    """Test interrupt validation."""

    def test_interrupt_unknown_asset(self) -> None:
        """Interrupt with unknown asset produces error."""
        source = """
        interrupt {
            priority 10
            when image "unknown_popup"
            {
                click(50, 50);
            }
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program, known_assets=[])

        assert any(d.code == "E1101" for d in diagnostics)


class TestSemanticCompleteScript:
    """Test complete script validation."""

    def test_valid_script_no_errors(self) -> None:
        """Valid script produces no semantic errors."""
        source = """
        hotkeys {
            start = "F5"
            stop = "F6"
        }

        flow main {
            label start:

            wait_image("btn_ready", timeout=5s);
            click(100, 200);

            if image_exists("btn_done") {
                return;
            }

            sleep(1s);
            goto start;
        }

        interrupt {
            priority 10
            when image "error_popup"
            {
                click(50, 50);
            }
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(
            program,
            known_assets=["btn_ready", "btn_done", "error_popup"]
        )

        errors = [d for d in diagnostics if d.severity == Severity.ERROR]
        assert len(errors) == 0

    def test_multiple_errors(self) -> None:
        """Multiple errors are all reported."""
        source = """
        flow main {
            wait_image("unknown1");
            wait_image("unknown2");
            run_flow("missing_flow");
            goto missing_label;
        }
        """
        parser = Parser(source)
        program = parser.parse()
        diagnostics = analyze(program, known_assets=[])

        # Should have at least 4 errors
        assert len(diagnostics) >= 4
