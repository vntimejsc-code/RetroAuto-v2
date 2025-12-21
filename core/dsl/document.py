"""
RetroAuto v2 - Script Document

Manages the document state for a script:
- Holds the IR (source of truth)
- Syncs code ↔ IR ↔ GUI
- Handles dirty state and undo/redo
"""

from __future__ import annotations

from collections.abc import Callable
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


class ScriptDocument:
    """
    Document model for a script file.

    Coordinates sync between:
    - Code (DSL text)
    - IR (intermediate representation)
    - GUI (panels and inspectors)

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

        # Callbacks
        self._on_ir_changed: list[Callable[[str], None]] = []
        self._on_code_changed: list[Callable[[str], None]] = []
        self._on_error: list[Callable[[list[str]], None]] = []

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
        """
        if not self._sync_enabled:
            return

        self._code = new_code
        self._is_dirty = True

        # Parse to IR
        ir, errors = parse_to_ir(new_code)

        if errors:
            # Keep old IR, but mark as invalid
            self._ir.is_valid = False
            self._ir.parse_errors = errors
            self._notify_errors(errors)
        else:
            # Update IR
            old_ir = self._ir
            self._ir = ir
            self._ir.is_valid = True
            self._ir.parse_errors = []
            self._notify_ir_changed(f"code_{source}")

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

        for i, part in enumerate(parts[:-1]):
            if isinstance(part, int):
                obj = obj[part]
            else:
                obj = getattr(obj, part)

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
