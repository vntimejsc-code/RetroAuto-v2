"""
RetroAuto v2 - DSL Syntax Highlighter

Syntax highlighting for the DSL code editor.
Uses QSyntaxHighlighter with Win95-compatible colors.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

# ─────────────────────────────────────────────────────────────
# Syntax Colors (Win95-compatible, high-contrast)
# ─────────────────────────────────────────────────────────────


class SyntaxColors:
    """Color definitions for syntax highlighting."""

    KEYWORD = QColor("#00007F")  # Dark blue
    STRING = QColor("#7F0000")  # Dark red
    COMMENT = QColor("#007F00")  # Green
    NUMBER = QColor("#7F007F")  # Purple
    DURATION = QColor("#7F007F")  # Purple (same as number)
    FUNCTION = QColor("#000000")  # Black (bold)
    BUILTIN = QColor("#00007F")  # Dark blue (italic)
    OPERATOR = QColor("#000000")  # Black
    ERROR = QColor("#FF0000")  # Red


# ─────────────────────────────────────────────────────────────
# Format Factory
# ─────────────────────────────────────────────────────────────


def make_format(
    color: QColor,
    bold: bool = False,
    italic: bool = False,
) -> QTextCharFormat:
    """Create a QTextCharFormat with given style."""
    fmt = QTextCharFormat()
    fmt.setForeground(color)
    if bold:
        fmt.setFontWeight(QFont.Weight.Bold)
    if italic:
        fmt.setFontItalic(True)
    return fmt


# ─────────────────────────────────────────────────────────────
# Keywords and Builtins
# ─────────────────────────────────────────────────────────────

KEYWORDS = {
    "flow",
    "interrupt",
    "priority",
    "when",
    "image",
    "const",
    "let",
    "if",
    "elif",
    "else",
    "while",
    "for",
    "in",
    "label",
    "goto",
    "try",
    "catch",
    "break",
    "continue",
    "return",
    "hotkeys",
    "true",
    "false",
    "null",
}

BUILTINS = {
    "wait_image",
    "find_image",
    "image_exists",
    "wait_any",
    "click",
    "move",
    "hotkey",
    "type_text",
    "sleep",
    "run_flow",
    "log",
    "assert",
    "range",
}


# ─────────────────────────────────────────────────────────────
# Highlighter
# ─────────────────────────────────────────────────────────────


class DSLHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for DSL code editor.

    Highlights:
    - Keywords (blue, bold)
    - Built-in functions (blue, italic)
    - Strings (dark red)
    - Comments (green)
    - Numbers and durations (purple)
    """

    def __init__(self, parent=None):  # type: ignore
        super().__init__(parent)
        self._init_formats()

    def _init_formats(self) -> None:
        """Initialize text formats for each syntax element."""
        self.formats = {
            "keyword": make_format(SyntaxColors.KEYWORD, bold=True),
            "builtin": make_format(SyntaxColors.BUILTIN, italic=True),
            "string": make_format(SyntaxColors.STRING),
            "comment": make_format(SyntaxColors.COMMENT, italic=True),
            "number": make_format(SyntaxColors.NUMBER),
            "duration": make_format(SyntaxColors.DURATION),
            "error": make_format(SyntaxColors.ERROR),
        }

    def highlightBlock(self, text: str) -> None:
        """Highlight a single block of text."""
        # Handle multiline comments first
        self._highlight_multiline_comments(text)

        # Then do single-line highlighting
        self._highlight_line(text)

    def _highlight_line(self, text: str) -> None:
        """Highlight single line elements."""
        i = 0
        length = len(text)

        while i < length:
            char = text[i]

            # Skip if inside multiline comment
            if self.currentBlockState() == 1:
                if text[i : i + 2] == "*/":
                    self.setFormat(i, 2, self.formats["comment"])
                    self.setCurrentBlockState(0)
                    i += 2
                else:
                    self.setFormat(i, 1, self.formats["comment"])
                    i += 1
                continue

            # Line comment
            if text[i : i + 2] == "//":
                self.setFormat(i, length - i, self.formats["comment"])
                return

            # Block comment start
            if text[i : i + 2] == "/*":
                start = i
                i += 2
                while i < length and text[i : i + 2] != "*/":
                    i += 1
                if i < length:
                    self.setFormat(start, i - start + 2, self.formats["comment"])
                    i += 2
                else:
                    self.setFormat(start, length - start, self.formats["comment"])
                    self.setCurrentBlockState(1)
                continue

            # Strings
            if char in "\"'":
                quote = char
                start = i
                i += 1
                while i < length:
                    if text[i] == "\\":
                        i += 2  # Skip escape
                    elif text[i] == quote:
                        i += 1
                        break
                    else:
                        i += 1
                self.setFormat(start, i - start, self.formats["string"])
                continue

            # Numbers and durations
            if char.isdigit():
                start = i
                while i < length and (text[i].isdigit() or text[i] == "."):
                    i += 1
                # Check for duration suffix
                suffix_start = i
                while i < length and text[i].isalpha():
                    i += 1
                suffix = text[suffix_start:i].lower()
                if suffix in ("ms", "s", "m", "h"):
                    self.setFormat(start, i - start, self.formats["duration"])
                else:
                    i = suffix_start  # Rollback if not duration
                    self.setFormat(start, i - start, self.formats["number"])
                continue

            # Identifiers (keywords/builtins)
            if char.isalpha() or char == "_":
                start = i
                while i < length and (text[i].isalnum() or text[i] == "_"):
                    i += 1
                word = text[start:i].lower()

                if word in KEYWORDS:
                    self.setFormat(start, i - start, self.formats["keyword"])
                elif word in BUILTINS:
                    self.setFormat(start, i - start, self.formats["builtin"])
                continue

            i += 1

    def _highlight_multiline_comments(self, text: str) -> None:
        """Handle multiline comment state from previous block."""
        # Get state from previous block
        prev_state = self.previousBlockState()

        if prev_state == 1:  # Inside multiline comment
            # Look for end
            end_idx = text.find("*/")
            if end_idx >= 0:
                self.setFormat(0, end_idx + 2, self.formats["comment"])
                self.setCurrentBlockState(0)
            else:
                self.setFormat(0, len(text), self.formats["comment"])
                self.setCurrentBlockState(1)
        else:
            self.setCurrentBlockState(0)
