"""
RetroAuto v2 - Script Document

Manages the document state for a script:
- Holds the IR (source of truth)
- Syncs code ↔ IR ↔ GUI
- Handles dirty state and undo/redo
- Graceful error handling with recovery hints
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any

from core.dsl.ir import (
    ActionIR,
    AssetIR,
    FlowIR,
    ScriptIR,
    ir_to_code,
    parse_to_ir,
)
from core.dsl.parser import Parser
from core.dsl.semantic import analyze


class DocumentState(Enum):
    """Document validation state."""

    VALID = auto()  # Code parsed successfully
    ERROR = auto()  # Parse failed, showing errors
    PARTIAL = auto()  # User is typing, incomplete code
    RECOVERING = auto()  # Attempting auto-fix


@dataclass
class ParseError:
    """Enriched parse error with recovery hints."""

    message: str
    line: int = 0
    column: int = 0
    severity: str = "error"  # error, warning, hint
    recovery_hint: str = ""
    quick_fix: str | None = None  # Suggested fix


# Common error recovery patterns
ERROR_RECOVERY_PATTERNS = {
    r"Expected ';'": ("Thêm ';' ở cuối dòng", ";"),
    r"Expected '\}'": ("Thiếu '}' đóng block", "}"),
    r"Expected '\)'": ("Thiếu ')' đóng ngoặc", ")"),
    r"Unknown asset '(\w+)'": ("Asset không tồn tại. Tạo mới?", None),
    r"Unknown label '(\w+)'": ("Label không tìm thấy trong flow", None),
}


class ScriptDocument:
    """
    Document model for a script file.

    Coordinates sync between:
    - Code (DSL text)
    - IR (intermediate representation)
    - GUI (panels and inspectors)

    Features:
    - Graceful degradation on errors
    - Typing detection to avoid error spam
    - Recovery hints and quick fixes

    Usage:
        doc = ScriptDocument()
        doc.load_from_file(path)
        doc.update_from_code(new_code)
        doc.update_from_gui("flows[0].actions[0].params.x", 100)
    """

    def __init__(self) -> None:
        self._ir = ScriptIR()
        self._code = ""
        self._file_path: Path | None = None
        self._is_dirty = False

        # Error handling state
        self._state = DocumentState.VALID
        self._last_valid_ir: ScriptIR | None = None
        self._parse_errors: list[ParseError] = []
        self._last_code_length = 0
        self._typing_direction = 0  # +1 = adding, -1 = deleting

        # Callbacks
        self._on_ir_changed: list[Callable[[str], None]] = []
        self._on_code_changed: list[Callable[[str], None]] = []
        self._on_error: list[Callable[[list[str]], None]] = []
        self._on_state_changed: list[Callable[[DocumentState], None]] = []

        # Sync mode
        self._sync_enabled = True

    @property
    def ir(self) -> ScriptIR:
        """Get the current IR."""
        return self._ir

    @property
    def code(self) -> str:
        """Get the current code."""
        return self._code

    @property
    def file_path(self) -> Path | None:
        """Get the file path."""
        return self._file_path

    @property
    def is_dirty(self) -> bool:
        """Check if document has unsaved changes."""
        return self._is_dirty

    @property
    def is_valid(self) -> bool:
        """Check if the code is valid (parseable)."""
        return self._ir.is_valid

    # ─────────────────────────────────────────────────────────────
    # Callbacks
    # ─────────────────────────────────────────────────────────────

    def on_ir_changed(self, callback: Callable[[str], None]) -> None:
        """Register callback for IR changes."""
        self._on_ir_changed.append(callback)

    def on_code_changed(self, callback: Callable[[str], None]) -> None:
        """Register callback for code changes."""
        self._on_code_changed.append(callback)

    def on_error(self, callback: Callable[[list[str]], None]) -> None:
        """Register callback for parse errors."""
        self._on_error.append(callback)

    def _notify_ir_changed(self, change_type: str) -> None:
        """Notify IR change listeners."""
        for cb in self._on_ir_changed:
            cb(change_type)

    def _notify_code_changed(self, source: str) -> None:
        """Notify code change listeners."""
        for cb in self._on_code_changed:
            cb(source)

    def _notify_errors(self, errors: list[str]) -> None:
        """Notify error listeners."""
        for cb in self._on_error:
            cb(errors)

    # ─────────────────────────────────────────────────────────────
    # File Operations
    # ─────────────────────────────────────────────────────────────

    def new(self) -> None:
        """Create a new empty document."""
        self._ir = ScriptIR()
        self._ir.flows.append(FlowIR(name="main"))
        self._code = ir_to_code(self._ir)
        self._file_path = None
        self._is_dirty = False
        self._notify_ir_changed("new")
        self._notify_code_changed("new")

    def load_from_file(self, path: Path) -> bool:
        """
        Load document from file.

        Returns True if successful.
        """
        try:
            content = path.read_text(encoding="utf-8")
            self._file_path = path
            self.update_from_code(content, source="file")
            self._is_dirty = False
            return True
        except Exception as e:
            self._notify_errors([f"Failed to load file: {e}"])
            return False

    def save(self) -> bool:
        """
        Save document to file.

        Returns True if successful.
        """
        if not self._file_path:
            return False

        try:
            self._file_path.write_text(self._code, encoding="utf-8")
            self._is_dirty = False
            return True
        except Exception as e:
            self._notify_errors([f"Failed to save file: {e}"])
            return False

    def save_as(self, path: Path) -> bool:
        """Save document to a new file."""
        self._file_path = path
        return self.save()

    # ─────────────────────────────────────────────────────────────
    # Code → IR Sync
    # ─────────────────────────────────────────────────────────────

    def update_from_code(self, new_code: str, source: str = "editor") -> None:
        """
        Update IR from new code.

        Called when the user edits code in the editor.
        Implements graceful degradation on errors.
        """
        if not self._sync_enabled:
            return

        # Track typing direction for partial detection
        code_len_diff = len(new_code) - self._last_code_length
        self._typing_direction = 1 if code_len_diff > 0 else -1 if code_len_diff < 0 else 0
        self._last_code_length = len(new_code)

        self._code = new_code
        self._is_dirty = True

        # Check if user is actively typing (partial code)
        if self._is_typing_in_progress(new_code):
            self._state = DocumentState.PARTIAL
            # Don't parse incomplete code - avoid error spam
            return

        # Parse to IR
        ir, errors = parse_to_ir(new_code)

        if errors:
            # Enrich errors with recovery hints
            enriched_errors = self._enrich_errors(errors)
            self._parse_errors = enriched_errors

            # Keep last valid IR for graceful degradation
            if self._ir.is_valid and self._last_valid_ir is None:
                self._last_valid_ir = self._ir

            # Mark current IR as invalid but don't replace
            self._ir.is_valid = False
            self._ir.parse_errors = [e.message for e in enriched_errors]
            self._state = DocumentState.ERROR

            # Notify with enriched error messages
            self._notify_errors(
                [
                    f"Line {e.line}: {e.message}"
                    + (f" (Hint: {e.recovery_hint})" if e.recovery_hint else "")
                    for e in enriched_errors
                ]
            )
            self._notify_state_changed()
        else:
            # Parse successful - run semantic analysis
            semantic_errors = self._run_semantic_analysis(ir)

            if semantic_errors:
                # Semantic errors are warnings - still update IR
                self._parse_errors = semantic_errors
                for e in semantic_errors:
                    e.severity = "warning"
                self._notify_errors([e.message for e in semantic_errors])

            # Update IR
            self._last_valid_ir = ir  # Save as last valid
            self._ir = ir
            self._ir.is_valid = True
            self._ir.parse_errors = []
            self._parse_errors = []
            self._state = DocumentState.VALID

            self._notify_state_changed()
            self._notify_ir_changed(f"code_{source}")

    def _is_typing_in_progress(self, code: str) -> bool:
        """
        Detect if user is in the middle of typing.

        Returns True if code appears incomplete.
        """
        code = code.rstrip()
        if not code:
            return False

        # Indicators of incomplete code
        incomplete_patterns = [
            code.endswith("("),  # click(
            code.endswith(","),  # click(100,
            code.endswith("{"),  # flow main {
            code.endswith("="),  # asset x =
            code.endswith('"') and code.count('"') % 2 == 1,  # Unclosed string
        ]

        # Also check for recently added text (user is typing)
        if self._typing_direction > 0:  # noqa: SIM102
            # Adding text - check last char is identifier char
            if code and code[-1].isalnum():
                # Might be typing a word
                return True

        return any(incomplete_patterns)

    def _enrich_errors(self, errors: list[str]) -> list[ParseError]:
        """
        Enrich raw error messages with recovery hints and quick fixes.
        """
        enriched = []

        for error in errors:
            # Extract line number if present
            line = 0
            match = re.search(r"line\s*(\d+)", error, re.IGNORECASE)
            if match:
                line = int(match.group(1))

            # Find matching recovery pattern
            hint = ""
            quick_fix = None

            for pattern, (recovery_hint, fix) in ERROR_RECOVERY_PATTERNS.items():
                if re.search(pattern, error, re.IGNORECASE):
                    hint = recovery_hint
                    quick_fix = fix
                    break

            enriched.append(
                ParseError(
                    message=error,
                    line=line,
                    recovery_hint=hint,
                    quick_fix=quick_fix,
                )
            )

        return enriched

    def _run_semantic_analysis(self, ir: ScriptIR) -> list[ParseError]:
        """Run semantic analysis and return errors as ParseError list."""
        errors = []

        # Check asset references
        asset_ids = {a.id for a in ir.assets}
        flow_names = {f.name for f in ir.flows}

        for flow in ir.flows:
            for _i, action in enumerate(flow.actions):
                # Check wait_image/if_image asset references
                if action.action_type in ("wait_image", "if_image", "while_image"):
                    asset_ref = action.params.get("arg0", "")
                    if asset_ref and asset_ref not in asset_ids:
                        errors.append(
                            ParseError(
                                message=f"Unknown asset '{asset_ref}' in {flow.name}",
                                line=action.span_line or 0,
                                severity="warning",
                                recovery_hint=f"Asset '{asset_ref}' không tồn tại. Tạo mới?",
                            )
                        )

                # Check run_flow references
                if action.action_type == "run_flow":
                    flow_ref = action.params.get("arg0", "")
                    if flow_ref and flow_ref not in flow_names:
                        errors.append(
                            ParseError(
                                message=f"Unknown flow '{flow_ref}'",
                                line=action.span_line or 0,
                                severity="warning",
                                recovery_hint=f"Flow '{flow_ref}' không tìm thấy",
                            )
                        )

        return errors

    def _notify_state_changed(self) -> None:
        """Notify state change listeners."""
        for cb in self._on_state_changed:
            cb(self._state)

    def on_state_changed(self, callback: Callable[[DocumentState], None]) -> None:
        """Register callback for state changes."""
        self._on_state_changed.append(callback)

    @property
    def state(self) -> DocumentState:
        """Get current document state."""
        return self._state

    @property
    def parse_errors(self) -> list[ParseError]:
        """Get current parse errors."""
        return self._parse_errors

    @property
    def last_valid_ir(self) -> ScriptIR | None:
        """Get the last successfully parsed IR."""
        return self._last_valid_ir

    # ─────────────────────────────────────────────────────────────
    # GUI → IR → Code Sync
    # ─────────────────────────────────────────────────────────────

    def update_from_gui(self, path: str, value: Any) -> None:
        """
        Update IR from GUI change, then regenerate code.

        Path format: "flows[0].name" or "assets[0].threshold"
        """
        if not self._sync_enabled:
            return

        # Parse path and update IR
        self._update_ir_field(path, value)
        self._is_dirty = True

        # Regenerate code from IR
        self._regenerate_code()

    def _update_ir_field(self, path: str, value: Any) -> None:
        """Update a field in the IR by path."""
        parts = self._parse_path(path)
        obj: Any = self._ir

        for _i, part in enumerate(parts[:-1]):
            obj = obj[part] if isinstance(part, int) else getattr(obj, part)

        final_part = parts[-1]
        if isinstance(final_part, int):
            obj[final_part] = value
        else:
            setattr(obj, final_part, value)

    def _parse_path(self, path: str) -> list[str | int]:
        """Parse a path like 'flows[0].name' into parts."""
        import re

        parts: list[str | int] = []

        for segment in re.split(r"\.", path):
            match = re.match(r"(\w+)\[(\d+)\]", segment)
            if match:
                parts.append(match.group(1))
                parts.append(int(match.group(2)))
            else:
                parts.append(segment)

        return parts

    def _regenerate_code(self) -> None:
        """Regenerate code from current IR."""
        if not self._ir.is_valid:
            return

        # Temporarily disable sync to avoid feedback loop
        self._sync_enabled = False
        try:
            self._code = ir_to_code(self._ir)
            self._notify_code_changed("gui")
        finally:
            self._sync_enabled = True

    # ─────────────────────────────────────────────────────────────
    # IR Operations
    # ─────────────────────────────────────────────────────────────

    def add_flow(self, name: str) -> FlowIR:
        """Add a new flow."""
        flow = FlowIR(name=name)
        self._ir.flows.append(flow)
        self._is_dirty = True
        self._regenerate_code()
        self._notify_ir_changed("flow_added")
        return flow

    def remove_flow(self, name: str) -> None:
        """Remove a flow by name."""
        self._ir.flows = [f for f in self._ir.flows if f.name != name]
        self._is_dirty = True
        self._regenerate_code()
        self._notify_ir_changed("flow_removed")

    def add_action_to_flow(self, flow_name: str, action: ActionIR) -> None:
        """Add an action to a flow."""
        flow = self._ir.get_flow(flow_name)
        if flow:
            flow.actions.append(action)
            self._is_dirty = True
            self._regenerate_code()
            self._notify_ir_changed("action_added")

    def add_asset(self, asset: AssetIR) -> None:
        """Add a new asset."""
        self._ir.assets.append(asset)
        self._is_dirty = True
        self._notify_ir_changed("asset_added")

    def remove_asset(self, asset_id: str) -> None:
        """Remove an asset by ID."""
        self._ir.assets = [a for a in self._ir.assets if a.id != asset_id]
        self._is_dirty = True
        self._notify_ir_changed("asset_removed")

    # ─────────────────────────────────────────────────────────────
    # Validation
    # ─────────────────────────────────────────────────────────────

    def validate(self) -> list[str]:
        """
        Validate the current document.

        Returns list of error messages.
        """
        if not self._ir.is_valid:
            return self._ir.parse_errors

        # Parse and run semantic analysis
        parser = Parser(self._code)
        program = parser.parse()

        if parser.errors:
            return [str(e) for e in parser.errors]

        # Semantic analysis
        asset_ids = [a.id for a in self._ir.assets]
        diagnostics = analyze(program, known_assets=asset_ids)

        return [str(d) for d in diagnostics]
