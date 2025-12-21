"""
Tests for DSL Formatter.
"""

import pytest

from core.dsl.parser import Parser
from core.dsl.formatter import Formatter, format_code


class TestFormatterIdempotent:
    """Test formatter idempotency: format(format(x)) == format(x)."""

    def test_simple_flow(self) -> None:
        """Simple flow is idempotent."""
        source = """
        flow main { log("test"); }
        """
        result1 = format_code(source)
        result2 = format_code(result1)
        assert result1 == result2

    def test_complex_script(self) -> None:
        """Complex script is idempotent."""
        source = """
        hotkeys {
            start = "F5"
            stop="F6"
        }
        flow main {
            let x=5;
            if x==1{log("one");}else{log("other");}
        }
        """
        result1 = format_code(source)
        result2 = format_code(result1)
        assert result1 == result2

    def test_nested_blocks(self) -> None:
        """Nested blocks are idempotent."""
        source = """
        flow main {
            while true {
                if x {
                    for i in range(10) {
                        log(i);
                    }
                }
            }
        }
        """
        result1 = format_code(source)
        result2 = format_code(result1)
        assert result1 == result2


class TestFormatterIndentation:
    """Test indentation rules."""

    def test_two_space_indent(self) -> None:
        """Uses 2-space indentation."""
        source = "flow main { log('test'); }"
        result = format_code(source)
        lines = result.split("\n")
        # Content line should start with 2 spaces
        content_lines = [l for l in lines if l.strip().startswith("log")]
        assert all(l.startswith("  ") for l in content_lines)

    def test_nested_indent(self) -> None:
        """Nested blocks have correct indentation."""
        source = """
        flow main {
            if true {
                log("nested");
            }
        }
        """
        result = format_code(source)
        lines = result.split("\n")
        log_line = [l for l in lines if "log" in l][0]
        # Should be 4 spaces (2 for flow + 2 for if)
        assert log_line.startswith("    ")


class TestFormatterBraces:
    """Test K&R brace style."""

    def test_opening_brace_same_line(self) -> None:
        """Opening brace on same line as keyword."""
        source = """
        flow main
        {
            log("test");
        }
        """
        result = format_code(source)
        assert "flow main {" in result

    def test_if_brace_same_line(self) -> None:
        """If opening brace on same line."""
        source = """
        flow main {
            if true
            {
                log("test");
            }
        }
        """
        result = format_code(source)
        assert "if true {" in result


class TestFormatterStrings:
    """Test string formatting."""

    def test_double_quotes(self) -> None:
        """Strings use double quotes."""
        source = "flow main { log('single'); }"
        result = format_code(source)
        assert '"single"' in result
        assert "'" not in result.replace("'", "").replace('"', "")

    def test_escape_in_strings(self) -> None:
        """Escapes preserved in strings."""
        source = 'flow main { log("hello\\nworld"); }'
        result = format_code(source)
        assert "\\n" in result or "\n" in result


class TestFormatterKeywords:
    """Test keyword formatting."""

    def test_lowercase_keywords(self) -> None:
        """Keywords are lowercase."""
        source = "FLOW main { IF TRUE { LOG('test'); } }"
        result = format_code(source)
        assert "flow " in result
        assert "if " in result
        assert "true" in result
        assert "FLOW" not in result


class TestFormatterSpacing:
    """Test spacing rules."""

    def test_binary_operator_spacing(self) -> None:
        """Binary operators have spaces."""
        source = "flow main { let x=1+2; }"
        result = format_code(source)
        assert " = " in result
        assert " + " in result

    def test_comma_spacing(self) -> None:
        """Commas followed by space."""
        source = "flow main { click(100,200,button='left'); }"
        result = format_code(source)
        assert ", " in result


class TestFormatterCompleteScript:
    """Test complete script formatting."""

    def test_full_script_format(self) -> None:
        """Complete script formats correctly."""
        source = """
        hotkeys{start="F5"}
        flow main{
            label start:
            wait_image("btn",timeout=5s);
            click(100,200);
            goto start;
        }
        interrupt{priority 10 when image "error"{click(50,50);}}
        """
        result = format_code(source)

        # Check structure
        assert "hotkeys {" in result
        assert "flow main {" in result
        assert "interrupt {" in result
        assert "label start:" in result
        assert 'wait_image("btn"' in result

    def test_preserves_semantics(self) -> None:
        """Formatting preserves semantics."""
        source = """
        flow main {
            let x = 1 + 2 * 3;
            if x == 7 {
                log("correct");
            }
        }
        """
        original_parser = Parser(source)
        original_ast = original_parser.parse()

        formatted = format_code(source)
        formatted_parser = Parser(formatted)
        formatted_ast = formatted_parser.parse()

        # Same structure
        assert len(original_ast.flows) == len(formatted_ast.flows)
        assert len(original_ast.flows[0].body.statements) == len(
            formatted_ast.flows[0].body.statements
        )


class TestFormatterEdgeCases:
    """Test edge cases."""

    def test_empty_flow(self) -> None:
        """Empty flow body."""
        source = "flow main {}"
        result = format_code(source)
        assert "flow main {\n}" in result

    def test_multiple_flows(self) -> None:
        """Multiple flows separated by blank line."""
        source = "flow a {} flow b {}"
        result = format_code(source)
        lines = result.strip().split("\n")
        # Should have blank line between flows
        assert len(lines) >= 4

    def test_parse_error_returns_original(self) -> None:
        """Parse error returns original source."""
        source = "this is not valid DSL @@@"
        result = format_code(source)
        assert result == source
