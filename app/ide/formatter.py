"""
RetroAuto v2 - Code Formatter

Code formatting for RetroScript with configurable style options.
Part of RetroScript Phase 5 - Advanced IDE Features.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.dsl.ast import Program


@dataclass
class FormatOptions:
    """Code formatting options."""

    indent_size: int = 4
    use_tabs: bool = False
    max_line_length: int = 100
    space_before_colon: bool = False
    space_after_colon: bool = True
    blank_lines_between_flows: int = 2
    trailing_newline: bool = True


class Formatter:
    """Code formatter for RetroScript.

    Provides:
    - Indentation normalization
    - Statement spacing
    - Block formatting
    - Configurable style

    Usage:
        formatter = Formatter()
        formatted = formatter.format(code)
    """

    def __init__(self, options: FormatOptions | None = None) -> None:
        self.options = options or FormatOptions()

    def format(self, source: str) -> str:
        """Format RetroScript source code.

        Args:
            source: The source code to format

        Returns:
            Formatted source code
        """
        lines = source.split("\n")
        result: list[str] = []
        indent_level = 0
        in_multiline_comment = False
        last_line_blank = False
        last_was_block_end = False

        for line in lines:
            stripped = line.strip()

            # Handle empty lines
            if not stripped:
                if not last_line_blank and result:
                    result.append("")
                    last_line_blank = True
                continue

            last_line_blank = False

            # Handle multiline comments
            if "/*" in stripped and "*/" not in stripped:
                in_multiline_comment = True
            if "*/" in stripped:
                in_multiline_comment = False

            # Check for block end
            is_block_end = stripped.startswith("}") or stripped == "end"

            # Decrease indent before closing braces
            if is_block_end and indent_level > 0:
                indent_level -= 1

            # Format the line
            formatted_line = self._format_line(stripped, indent_level)
            
            # Add blank line before flow if needed
            if stripped.startswith("flow ") and result and not last_was_block_end:
                for _ in range(self.options.blank_lines_between_flows):
                    if result and result[-1] != "":
                        result.append("")

            result.append(formatted_line)

            # Increase indent after opening braces/colons
            if stripped.endswith("{") or (stripped.endswith(":") and not stripped.startswith("#")):
                indent_level += 1

            last_was_block_end = is_block_end

        # Trailing newline
        if self.options.trailing_newline and result and result[-1] != "":
            result.append("")

        return "\n".join(result)

    def _format_line(self, line: str, indent_level: int) -> str:
        """Format a single line with proper indentation."""
        # Create indent
        if self.options.use_tabs:
            indent = "\t" * indent_level
        else:
            indent = " " * (self.options.indent_size * indent_level)

        # Format the content
        formatted = self._format_content(line)

        return indent + formatted

    def _format_content(self, content: str) -> str:
        """Format the content of a line (operators, spacing)."""
        result = content

        # Format colon spacing
        if ":" in result and not result.startswith("#") and not result.startswith("//"):
            parts = result.split(":")
            if len(parts) == 2 and not parts[1].startswith("/"):  # Not a URL
                before = parts[0].rstrip() if not self.options.space_before_colon else parts[0].rstrip() + " "
                after = " " + parts[1].strip() if self.options.space_after_colon else parts[1].strip()
                if parts[1].strip():  # Only if there's content after
                    result = before + ":" + after
                else:
                    result = before + ":"

        # Normalize operator spacing
        operators = ["==", "!=", "<=", ">=", "&&", "||", "->", "→"]
        for op in operators:
            if op in result:
                result = result.replace(f" {op}", op)
                result = result.replace(f"{op} ", op)
                result = result.replace(op, f" {op} ")

        # Clean up multiple spaces
        while "  " in result:
            result = result.replace("  ", " ")

        return result.strip()

    def format_selection(self, source: str, start_line: int, end_line: int) -> str:
        """Format only a selection of lines.

        Preserves structure outside the selection.
        """
        lines = source.split("\n")
        
        # Calculate base indent from first selected line
        if start_line < len(lines):
            first_line = lines[start_line]
            base_indent = len(first_line) - len(first_line.lstrip())
        else:
            base_indent = 0

        # Format selected lines
        selected = "\n".join(lines[start_line:end_line + 1])
        formatted_selected = self.format(selected)
        formatted_lines = formatted_selected.split("\n")

        # Re-apply base indent
        reindented = []
        for line in formatted_lines:
            if line.strip():
                reindented.append(" " * base_indent + line)
            else:
                reindented.append("")

        # Combine with rest
        result = lines[:start_line] + reindented + lines[end_line + 1:]
        return "\n".join(result)

    def get_indent(self, line: str) -> int:
        """Get the indentation level of a line."""
        stripped = line.lstrip()
        indent_chars = len(line) - len(stripped)

        if self.options.use_tabs:
            return indent_chars  # Each tab is one level
        else:
            return indent_chars // self.options.indent_size


# Convenience function
def format_code(source: str, options: FormatOptions | None = None) -> str:
    """Format RetroScript code with optional style settings."""
    return Formatter(options).format(source)
