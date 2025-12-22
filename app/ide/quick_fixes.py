"""
RetroAuto v2 - Error Quick-Fixes

Provides intelligent error detection and fix suggestions.
Part of RetroScript Phase 6 - Error Handling + Templates.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from difflib import get_close_matches
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.dsl.diagnostics import Diagnostic


@dataclass
class QuickFix:
    """A suggested fix for an error."""

    title: str  # Display title
    description: str  # Detailed description
    replacement: str  # Text to replace with
    start_line: int
    end_line: int
    start_col: int = 0
    end_col: int = -1  # -1 means end of line


@dataclass
class ErrorPattern:
    """Pattern for detecting common errors."""

    code: str  # Error code to match
    pattern: str | None  # Regex pattern for message
    fixer: Callable[[str, int, int], list[QuickFix]]  # Fix generator


# ─────────────────────────────────────────────────────────────
# RetroScript Keywords for typo detection
# ─────────────────────────────────────────────────────────────

KEYWORDS = [
    "flow",
    "interrupt",
    "hotkeys",
    "const",
    "let",
    "if",
    "elif",
    "else",
    "while",
    "for",
    "in",
    "try",
    "catch",
    "break",
    "continue",
    "return",
    "repeat",
    "retry",
    "match",
    "and",
    "or",
    "not",
    "end",
    "import",
    "as",
    "test",
    "mock",
    "assert",
    "config",
    "permissions",
    "meta",
    "true",
    "false",
    "null",
]

BUILTINS = [
    "find",
    "wait",
    "click",
    "type",
    "press",
    "sleep",
    "scroll",
    "drag",
    "run",
    "log",
    "range",
    "wait_image",
    "find_image",
    "image_exists",
    "move",
    "hotkey",
    "type_text",
]


class QuickFixProvider:
    """Provides quick fixes for common RetroScript errors.

    Usage:
        provider = QuickFixProvider()
        fixes = provider.get_fixes(diagnostic, source_line)
    """

    def __init__(self) -> None:
        self._patterns: list[ErrorPattern] = []
        self._init_patterns()

    def _init_patterns(self) -> None:
        """Initialize error patterns."""
        # Undefined variable/function
        self._patterns.append(
            ErrorPattern(
                code="E1001",
                pattern=r"Unexpected token '(\w+)'",
                fixer=self._fix_typo,
            )
        )

        # Missing semicolon
        self._patterns.append(
            ErrorPattern(
                code="E1002",
                pattern=r"Expected ';'",
                fixer=self._fix_missing_semicolon,
            )
        )

        # Missing brace
        self._patterns.append(
            ErrorPattern(
                code="E1003",
                pattern=r"Expected '\}'",
                fixer=self._fix_missing_brace,
            )
        )

        # Missing colon
        self._patterns.append(
            ErrorPattern(
                code="E1004",
                pattern=r"Expected ':'",
                fixer=self._fix_missing_colon,
            )
        )

    def get_fixes(
        self,
        diagnostic: Diagnostic,
        source_line: str,
    ) -> list[QuickFix]:
        """Get quick fixes for a diagnostic.

        Args:
            diagnostic: The error diagnostic
            source_line: The source line with the error

        Returns:
            List of applicable quick fixes
        """
        fixes: list[QuickFix] = []

        for pattern in self._patterns:
            if pattern.code and diagnostic.code != pattern.code:
                continue

            if pattern.pattern:
                match = re.search(pattern.pattern, diagnostic.message)
                if not match:
                    continue

            try:
                pattern_fixes = pattern.fixer(
                    source_line,
                    diagnostic.span.start_line,
                    diagnostic.span.start_col,
                )
                fixes.extend(pattern_fixes)
            except Exception:
                pass  # Silently ignore fixer errors

        return fixes

    def _fix_typo(
        self,
        source_line: str,
        line: int,
        col: int,
    ) -> list[QuickFix]:
        """Suggest fixes for potential typos."""
        fixes: list[QuickFix] = []

        # Extract word at error position
        words = re.findall(r"\b\w+\b", source_line)
        if not words:
            return fixes

        # Find word at position
        pos = 0
        typo_word = None
        typo_start = 0
        for word in words:
            start = source_line.find(word, pos)
            end = start + len(word)
            if start <= col < end:
                typo_word = word
                typo_start = start
                break
            pos = end

        if not typo_word:
            return fixes

        # Find similar keywords
        all_words = KEYWORDS + BUILTINS
        matches = get_close_matches(typo_word.lower(), all_words, n=3, cutoff=0.6)

        for match in matches:
            fixes.append(
                QuickFix(
                    title=f"Change to '{match}'",
                    description=f"Did you mean '{match}'?",
                    replacement=match,
                    start_line=line,
                    end_line=line,
                    start_col=typo_start,
                    end_col=typo_start + len(typo_word),
                )
            )

        return fixes

    def _fix_missing_semicolon(
        self,
        source_line: str,
        line: int,
        col: int,
    ) -> list[QuickFix]:
        """Suggest adding missing semicolon."""
        return [
            QuickFix(
                title="Add semicolon",
                description="Add ';' at end of statement",
                replacement=source_line.rstrip() + ";",
                start_line=line,
                end_line=line,
            )
        ]

    def _fix_missing_brace(
        self,
        source_line: str,
        line: int,
        col: int,
    ) -> list[QuickFix]:
        """Suggest adding missing closing brace."""
        # Count opening braces in line
        opens = source_line.count("{")
        closes = source_line.count("}")

        if opens > closes:
            return [
                QuickFix(
                    title="Add closing brace",
                    description="Add '}' to close block",
                    replacement=source_line.rstrip() + "\n}",
                    start_line=line,
                    end_line=line,
                )
            ]
        return []

    def _fix_missing_colon(
        self,
        source_line: str,
        line: int,
        col: int,
    ) -> list[QuickFix]:
        """Suggest adding missing colon for RetroScript blocks."""
        # Check if line ends with block keyword
        stripped = source_line.rstrip()
        block_keywords = ["repeat", "retry", "match", "if", "elif", "else", "while", "for"]

        for kw in block_keywords:
            if (
                stripped.startswith(kw)
                and not stripped.endswith(":")
                and not stripped.endswith("{")
            ):
                return [
                    QuickFix(
                        title="Add colon",
                        description="Add ':' after block keyword",
                        replacement=stripped + ":",
                        start_line=line,
                        end_line=line,
                    )
                ]
        return []


class LiveValidator:
    """Real-time validation for RetroScript code.

    Usage:
        validator = LiveValidator()
        errors = validator.validate(source)
    """

    def __init__(self) -> None:
        self._defined_variables: set[str] = set()
        self._defined_flows: set[str] = set()

    def validate(self, source: str) -> list[ValidationError]:
        """Validate source code and return errors.

        Args:
            source: RetroScript source code

        Returns:
            List of validation errors
        """
        errors: list[ValidationError] = []
        lines = source.split("\n")

        self._defined_variables.clear()
        self._defined_flows.clear()

        # First pass: collect definitions
        for _, line in enumerate(lines, 1):
            self._collect_definitions(line)

        # Second pass: validate usage
        for i, line in enumerate(lines, 1):
            line_errors = self._validate_line(line, i)
            errors.extend(line_errors)

        return errors

    def _collect_definitions(self, line: str) -> None:
        """Collect variable and flow definitions from a line."""
        stripped = line.strip()

        # Flow definitions
        if stripped.startswith("flow "):
            match = re.match(r"flow\s+(\w+)", stripped)
            if match:
                self._defined_flows.add(match.group(1))

        # Variable assignments
        var_match = re.match(r"\$(\w+)\s*=", stripped)
        if var_match:
            self._defined_variables.add(var_match.group(1))

        # let declarations
        let_match = re.match(r"let\s+(\w+)", stripped)
        if let_match:
            self._defined_variables.add(let_match.group(1))

    def _validate_line(self, line: str, line_num: int) -> list[ValidationError]:
        """Validate a single line."""
        errors: list[ValidationError] = []
        stripped = line.strip()

        # Skip comments
        if stripped.startswith("//") or stripped.startswith("#"):
            return errors

        # Check for undefined variables
        var_uses = re.findall(r"\$(\w+)", stripped)
        for var in var_uses:
            # Skip if it's an assignment
            if re.match(rf"\${var}\s*=", stripped):
                continue
            if var not in self._defined_variables:
                errors.append(
                    ValidationError(
                        message=f"Undefined variable: ${var}",
                        line=line_num,
                        severity="warning",
                        suggestion=f"Did you mean to define it? Use: ${var} = value",
                    )
                )

        # Check for unclosed braces
        if stripped.count("{") > stripped.count("}") and not stripped.endswith("{"):
            errors.append(
                ValidationError(
                    message="Possible unclosed brace",
                    line=line_num,
                    severity="warning",
                )
            )

        # Check for typos in keywords
        words = re.findall(r"\b([a-z_]+)\b", stripped.lower())
        all_keywords = set(KEYWORDS + BUILTINS)
        for word in words:
            if len(word) > 3 and word not in all_keywords:
                matches = get_close_matches(word, list(all_keywords), n=1, cutoff=0.85)
                if matches and matches[0] != word:
                    errors.append(
                        ValidationError(
                            message=f"Possible typo: '{word}'. Did you mean '{matches[0]}'?",
                            line=line_num,
                            severity="hint",
                        )
                    )

        return errors


@dataclass
class ValidationError:
    """A validation error or warning."""

    message: str
    line: int
    severity: str = "error"  # error, warning, hint
    suggestion: str | None = None
