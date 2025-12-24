"""
RetroAuto v2 - Custom Exception Hierarchy

Structured error classes for better debugging and error handling.
Phase 1.2: Error Handling Cleanup
"""

from typing import Any


class RetroAutoError(Exception):
    """Base exception for all RetroAuto errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


# ─────────────────────────────────────────────────────────────
# Script Execution Errors
# ─────────────────────────────────────────────────────────────


class ScriptError(RetroAutoError):
    """Error during script execution."""

    pass


class ActionExecutionError(ScriptError):
    """Error executing a specific action."""

    def __init__(
        self, action_type: str, message: str, step_index: int | None = None
    ) -> None:
        self.action_type = action_type
        self.step_index = step_index
        super().__init__(
            f"Action '{action_type}' failed at step {step_index}: {message}",
            {"action_type": action_type, "step_index": step_index},
        )


class FlowNotFoundError(ScriptError):
    """Referenced flow does not exist."""

    def __init__(self, flow_name: str) -> None:
        self.flow_name = flow_name
        super().__init__(f"Flow not found: {flow_name}", {"flow_name": flow_name})


class LabelNotFoundError(ScriptError):
    """Referenced label does not exist."""

    def __init__(self, label_name: str, flow_name: str) -> None:
        self.label_name = label_name
        self.flow_name = flow_name
        super().__init__(
            f"Label '{label_name}' not found in flow '{flow_name}'",
            {"label_name": label_name, "flow_name": flow_name},
        )


# ─────────────────────────────────────────────────────────────
# Asset Errors
# ─────────────────────────────────────────────────────────────


class AssetError(RetroAutoError):
    """Error related to assets."""

    pass


class AssetNotFoundError(AssetError):
    """Referenced asset does not exist."""

    def __init__(self, asset_id: str) -> None:
        self.asset_id = asset_id
        super().__init__(f"Asset not found: {asset_id}", {"asset_id": asset_id})


class AssetLoadError(AssetError):
    """Failed to load asset image."""

    def __init__(self, asset_id: str, path: str, reason: str) -> None:
        self.asset_id = asset_id
        self.path = path
        super().__init__(
            f"Failed to load asset '{asset_id}' from '{path}': {reason}",
            {"asset_id": asset_id, "path": path, "reason": reason},
        )


# ─────────────────────────────────────────────────────────────
# Vision Errors
# ─────────────────────────────────────────────────────────────


class VisionError(RetroAutoError):
    """Error in vision/image processing."""

    pass


class MatchTimeoutError(VisionError):
    """Image matching timed out."""

    def __init__(self, asset_id: str, timeout_ms: int) -> None:
        self.asset_id = asset_id
        self.timeout_ms = timeout_ms
        super().__init__(
            f"Match timeout after {timeout_ms}ms for asset '{asset_id}'",
            {"asset_id": asset_id, "timeout_ms": timeout_ms},
        )


class ScreenCaptureError(VisionError):
    """Failed to capture screen."""

    pass


class OCRError(VisionError):
    """OCR text recognition failed."""

    def __init__(self, message: str, roi: dict | None = None) -> None:
        super().__init__(message, {"roi": roi})


# ─────────────────────────────────────────────────────────────
# DSL/Parser Errors
# ─────────────────────────────────────────────────────────────


class DSLError(RetroAutoError):
    """Error in DSL processing."""

    pass


class ParseError(DSLError):
    """DSL parsing failed."""

    def __init__(self, message: str, line: int | None = None, col: int | None = None) -> None:
        self.line = line
        self.col = col
        location = f" at line {line}" if line else ""
        if col:
            location += f", column {col}"
        super().__init__(f"Parse error{location}: {message}", {"line": line, "col": col})


class SemanticError(DSLError):
    """Semantic analysis error."""

    pass


class IRConversionError(DSLError):
    """Failed to convert IR to Script."""

    pass


# ─────────────────────────────────────────────────────────────
# Configuration Errors
# ─────────────────────────────────────────────────────────────


class ConfigurationError(RetroAutoError):
    """Configuration or settings error."""

    pass


class InvalidConfigError(ConfigurationError):
    """Invalid configuration value."""

    def __init__(self, key: str, value: Any, expected: str) -> None:
        self.key = key
        self.value = value
        super().__init__(
            f"Invalid config '{key}': got {value!r}, expected {expected}",
            {"key": key, "value": value, "expected": expected},
        )


# ─────────────────────────────────────────────────────────────
# Network Errors
# ─────────────────────────────────────────────────────────────


class NetworkError(RetroAutoError):
    """Network-related error."""

    pass


class ConnectionError(NetworkError):
    """Failed to establish connection."""

    pass


class TimeoutError(NetworkError):
    """Network operation timed out."""

    pass


# ─────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────


def wrap_exception(
    original: Exception, wrapper_class: type[RetroAutoError], message: str | None = None
) -> RetroAutoError:
    """Wrap a generic exception in a RetroAutoError subclass."""
    msg = message or str(original)
    error = wrapper_class(msg, {"original_type": type(original).__name__})
    error.__cause__ = original
    return error
