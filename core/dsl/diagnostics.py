"""
RetroAuto v2 - DSL Diagnostics

Error types and diagnostic messages for the DSL.
Follows error code convention:
- E100x: Parse errors
- E110x: Semantic errors
- R200x: Runtime errors
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.dsl.ast import Span


class Severity(Enum):
    """Diagnostic severity level."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


@dataclass
class QuickFix:
    """Quick fix suggestion for a diagnostic."""

    title: str
    replacement: str | None = None  # Text to insert/replace
    insert_at: Span | None = None  # Where to insert
    action: str | None = None  # Special action like "capture_asset"


@dataclass
class Diagnostic:
    """A diagnostic message (error, warning, etc.)."""

    code: str
    severity: Severity
    message: str
    span: Span
    hint: str | None = None
    quick_fixes: list[QuickFix] | None = None

    def __str__(self) -> str:
        prefix = f"[{self.code}]" if self.code else ""
        location = f"at {self.span}"
        hint_str = f"\n  Hint: {self.hint}" if self.hint else ""
        return f"{prefix} {self.severity.value}: {self.message} {location}{hint_str}"


# ─────────────────────────────────────────────────────────────
# Error Code Constants
# ─────────────────────────────────────────────────────────────

# Parse Errors (E100x)
E1001_UNEXPECTED_TOKEN = "E1001"
E1002_EXPECTED_TOKEN = "E1002"
E1003_UNTERMINATED_STRING = "E1003"
E1004_UNTERMINATED_COMMENT = "E1004"
E1005_INVALID_NUMBER = "E1005"
E1006_EXPECTED_EXPRESSION = "E1006"
E1007_EXPECTED_STATEMENT = "E1007"
E1008_EXPECTED_BLOCK = "E1008"
E1009_INVALID_ASSIGNMENT = "E1009"

# Semantic Errors (E110x)
E1101_UNKNOWN_ASSET = "E1101"
E1102_UNKNOWN_FLOW = "E1102"
E1103_UNKNOWN_LABEL = "E1103"
E1104_DUPLICATE_LABEL = "E1104"
E1105_DUPLICATE_FLOW = "E1105"
E1106_UNKNOWN_VARIABLE = "E1106"
E1107_TYPE_MISMATCH = "E1107"
E1108_INVALID_ARGUMENT = "E1108"
E1109_MISSING_ARGUMENT = "E1109"

# Runtime Errors (R200x)
R2001_TIMEOUT = "R2001"
R2002_IMAGE_NOT_FOUND = "R2002"
R2003_FLOW_NOT_FOUND = "R2003"
R2004_INTERRUPT_ERROR = "R2004"
R2005_ASSERTION_FAILED = "R2005"


# ─────────────────────────────────────────────────────────────
# Diagnostic Builders
# ─────────────────────────────────────────────────────────────


def unexpected_token(token_value: str, span: Span) -> Diagnostic:
    """Create unexpected token error."""
    return Diagnostic(
        code=E1001_UNEXPECTED_TOKEN,
        severity=Severity.ERROR,
        message=f"Unexpected token '{token_value}'",
        span=span,
        hint="Check for typos or missing semicolons",
    )


def expected_token(expected: str, got: str, span: Span) -> Diagnostic:
    """Create expected token error."""
    return Diagnostic(
        code=E1002_EXPECTED_TOKEN,
        severity=Severity.ERROR,
        message=f"Expected '{expected}', got '{got}'",
        span=span,
    )


def unknown_asset(asset_id: str, span: Span) -> Diagnostic:
    """Create unknown asset error with quick fix."""
    return Diagnostic(
        code=E1101_UNKNOWN_ASSET,
        severity=Severity.ERROR,
        message=f"Unknown asset '{asset_id}'",
        span=span,
        hint=f"Asset '{asset_id}' is not defined. Capture it first.",
        quick_fixes=[
            QuickFix(
                title=f"Capture new asset '{asset_id}'",
                action="capture_asset",
            ),
        ],
    )


def unknown_flow(flow_name: str, span: Span) -> Diagnostic:
    """Create unknown flow error."""
    return Diagnostic(
        code=E1102_UNKNOWN_FLOW,
        severity=Severity.ERROR,
        message=f"Unknown flow '{flow_name}'",
        span=span,
        hint="Define the flow or check the name spelling",
    )


def unknown_label(label_name: str, span: Span) -> Diagnostic:
    """Create unknown label error."""
    return Diagnostic(
        code=E1103_UNKNOWN_LABEL,
        severity=Severity.ERROR,
        message=f"Unknown label '{label_name}'",
        span=span,
        hint="Define the label before using goto",
    )


def duplicate_label(label_name: str, span: Span, original_span: Span) -> Diagnostic:
    """Create duplicate label error."""
    return Diagnostic(
        code=E1104_DUPLICATE_LABEL,
        severity=Severity.ERROR,
        message=f"Duplicate label '{label_name}'",
        span=span,
        hint=f"Label was first defined at line {original_span.start_line}",
    )


def duplicate_flow(flow_name: str, span: Span, original_span: Span) -> Diagnostic:
    """Create duplicate flow error."""
    return Diagnostic(
        code=E1105_DUPLICATE_FLOW,
        severity=Severity.ERROR,
        message=f"Duplicate flow '{flow_name}'",
        span=span,
        hint=f"Flow was first defined at line {original_span.start_line}",
    )


def type_mismatch(expected: str, got: str, span: Span) -> Diagnostic:
    """Create type mismatch error."""
    return Diagnostic(
        code=E1107_TYPE_MISMATCH,
        severity=Severity.ERROR,
        message=f"Type mismatch: expected {expected}, got {got}",
        span=span,
    )


def invalid_argument(func_name: str, arg_name: str, reason: str, span: Span) -> Diagnostic:
    """Create invalid argument error."""
    return Diagnostic(
        code=E1108_INVALID_ARGUMENT,
        severity=Severity.ERROR,
        message=f"Invalid argument '{arg_name}' for {func_name}: {reason}",
        span=span,
    )


def missing_argument(func_name: str, arg_name: str, span: Span) -> Diagnostic:
    """Create missing argument error."""
    return Diagnostic(
        code=E1109_MISSING_ARGUMENT,
        severity=Severity.ERROR,
        message=f"Missing required argument '{arg_name}' for {func_name}",
        span=span,
    )
