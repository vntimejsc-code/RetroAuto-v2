"""
RetroAuto v2 - Intermediate Representation (IR)

The IR serves as the canonical representation for round-trip sync:
- DSL Code ↔ IR ↔ GUI

When code changes, it's parsed to IR.
When GUI changes, IR is updated and code is regenerated.

This ensures both views stay synchronized.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from core.dsl.ast import Program, FlowDecl, InterruptDecl
from core.dsl.parser import Parser
from core.dsl.formatter import format_code


@dataclass
class AssetIR:
    """Asset representation in IR."""
    
    id: str
    path: str
    threshold: float = 0.8
    roi: dict[str, int] | None = None  # {x, y, width, height}


@dataclass
class ActionIR:
    """Generic action representation in IR."""
    
    action_type: str
    params: dict[str, Any] = field(default_factory=dict)
    span_line: int | None = None  # For source mapping


@dataclass
class FlowIR:
    """Flow representation in IR."""
    
    name: str
    actions: list[ActionIR] = field(default_factory=list)


@dataclass
class InterruptIR:
    """Interrupt representation in IR."""
    
    priority: int
    when_asset: str
    actions: list[ActionIR] = field(default_factory=list)


@dataclass
class HotkeysIR:
    """Hotkeys configuration in IR."""
    
    start: str = "F5"
    stop: str = "F6"
    pause: str = "F7"


@dataclass
class ScriptIR:
    """
    Complete script representation in IR.
    
    This is the single source of truth that both the
    code editor and GUI views sync to.
    """
    
    name: str = "Untitled"
    version: str = "1.0"
    author: str = ""
    
    hotkeys: HotkeysIR = field(default_factory=HotkeysIR)
    assets: list[AssetIR] = field(default_factory=list)
    flows: list[FlowIR] = field(default_factory=list)
    interrupts: list[InterruptIR] = field(default_factory=list)
    
    # Sync state
    is_valid: bool = True
    parse_errors: list[str] = field(default_factory=list)
    
    # Change listeners
    _listeners: list[Callable[[str], None]] = field(default_factory=list, repr=False)
    
    def add_listener(self, callback: Callable[[str], None]) -> None:
        """Add a listener for IR changes."""
        self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[str], None]) -> None:
        """Remove a change listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def notify_change(self, change_type: str) -> None:
        """Notify all listeners of a change."""
        for listener in self._listeners:
            listener(change_type)
    
    # Asset operations
    def get_asset(self, asset_id: str) -> AssetIR | None:
        """Get asset by ID."""
        return next((a for a in self.assets if a.id == asset_id), None)
    
    def add_asset(self, asset: AssetIR) -> None:
        """Add a new asset."""
        self.assets.append(asset)
        self.notify_change("asset_added")
    
    def remove_asset(self, asset_id: str) -> None:
        """Remove an asset by ID."""
        self.assets = [a for a in self.assets if a.id != asset_id]
        self.notify_change("asset_removed")
    
    # Flow operations
    def get_flow(self, name: str) -> FlowIR | None:
        """Get flow by name."""
        return next((f for f in self.flows if f.name == name), None)
    
    def add_flow(self, flow: FlowIR) -> None:
        """Add a new flow."""
        self.flows.append(flow)
        self.notify_change("flow_added")
    
    def remove_flow(self, name: str) -> None:
        """Remove a flow by name."""
        self.flows = [f for f in self.flows if f.name != name]
        self.notify_change("flow_removed")


class IRMapper:
    """
    Maps between DSL AST and IR.
    
    Provides bidirectional conversion:
    - AST → IR: For parsing code to IR
    - IR → Code: For generating code from IR
    """
    
    @staticmethod
    def ast_to_ir(program: Program, source: str = "") -> ScriptIR:
        """Convert parsed AST to IR."""
        ir = ScriptIR()
        
        # Hotkeys
        if program.hotkeys:
            ir.hotkeys = HotkeysIR(
                start=program.hotkeys.bindings.get("start", "F5"),
                stop=program.hotkeys.bindings.get("stop", "F6"),
                pause=program.hotkeys.bindings.get("pause", "F7"),
            )
        
        # Flows
        for flow_decl in program.flows:
            flow_ir = IRMapper._flow_to_ir(flow_decl)
            ir.flows.append(flow_ir)
        
        # Interrupts
        for interrupt in program.interrupts:
            interrupt_ir = IRMapper._interrupt_to_ir(interrupt)
            ir.interrupts.append(interrupt_ir)
        
        return ir
    
    @staticmethod
    def _flow_to_ir(flow: FlowDecl) -> FlowIR:
        """Convert flow declaration to IR."""
        flow_ir = FlowIR(name=flow.name)
        
        for stmt in flow.body.statements:
            action = IRMapper._statement_to_action(stmt)
            if action:
                flow_ir.actions.append(action)
        
        return flow_ir
    
    @staticmethod
    def _interrupt_to_ir(interrupt: InterruptDecl) -> InterruptIR:
        """Convert interrupt declaration to IR."""
        interrupt_ir = InterruptIR(
            priority=interrupt.priority,
            when_asset=interrupt.when_asset,
        )
        
        for stmt in interrupt.body.statements:
            action = IRMapper._statement_to_action(stmt)
            if action:
                interrupt_ir.actions.append(action)
        
        return interrupt_ir
    
    @staticmethod
    def _statement_to_action(stmt: Any) -> ActionIR | None:
        """Convert statement to action IR."""
        from core.dsl.ast import (
            ExprStmt, CallExpr, LabelStmt, GotoStmt,
            IfStmt, WhileStmt, ForStmt, LetStmt,
            BreakStmt, ContinueStmt, ReturnStmt,
        )
        
        if isinstance(stmt, ExprStmt) and isinstance(stmt.expr, CallExpr):
            call = stmt.expr
            return ActionIR(
                action_type=call.callee,
                params=IRMapper._extract_call_params(call),
                span_line=stmt.span.start_line,
            )
        
        if isinstance(stmt, LabelStmt):
            return ActionIR(
                action_type="label",
                params={"name": stmt.name},
                span_line=stmt.span.start_line,
            )
        
        if isinstance(stmt, GotoStmt):
            return ActionIR(
                action_type="goto",
                params={"target": stmt.target},
                span_line=stmt.span.start_line,
            )
        
        if isinstance(stmt, IfStmt):
            return ActionIR(
                action_type="if",
                params={"has_else": stmt.else_branch is not None},
                span_line=stmt.span.start_line,
            )
        
        # For complex statements, just track type
        if isinstance(stmt, WhileStmt):
            return ActionIR(action_type="while", span_line=stmt.span.start_line)
        if isinstance(stmt, ForStmt):
            return ActionIR(
                action_type="for",
                params={"variable": stmt.variable},
                span_line=stmt.span.start_line,
            )
        if isinstance(stmt, BreakStmt):
            return ActionIR(action_type="break", span_line=stmt.span.start_line)
        if isinstance(stmt, ContinueStmt):
            return ActionIR(action_type="continue", span_line=stmt.span.start_line)
        if isinstance(stmt, ReturnStmt):
            return ActionIR(action_type="return", span_line=stmt.span.start_line)
        
        return None
    
    @staticmethod
    def _extract_call_params(call: Any) -> dict[str, Any]:
        """Extract parameters from a CallExpr."""
        from core.dsl.ast import Literal, Identifier
        
        params: dict[str, Any] = {}
        
        # Positional args
        for i, arg in enumerate(call.args):
            if isinstance(arg, Literal):
                params[f"arg{i}"] = arg.value
            elif isinstance(arg, Identifier):
                params[f"arg{i}"] = arg.name
        
        # Keyword args
        for key, value in call.kwargs.items():
            if isinstance(value, Literal):
                params[key] = value.value
            elif isinstance(value, Identifier):
                params[key] = value.name
        
        return params
    
    @staticmethod
    def ir_to_code(ir: ScriptIR) -> str:
        """Generate DSL code from IR."""
        lines: list[str] = []
        
        # Hotkeys
        lines.append("hotkeys {")
        lines.append(f'  start = "{ir.hotkeys.start}"')
        lines.append(f'  stop = "{ir.hotkeys.stop}"')
        lines.append(f'  pause = "{ir.hotkeys.pause}"')
        lines.append("}")
        lines.append("")
        
        # Flows
        for flow in ir.flows:
            lines.append(f"flow {flow.name} {{")
            for action in flow.actions:
                code = IRMapper._action_to_code(action)
                lines.append(f"  {code}")
            lines.append("}")
            lines.append("")
        
        # Interrupts
        for interrupt in ir.interrupts:
            lines.append("interrupt {")
            lines.append(f"  priority {interrupt.priority}")
            lines.append(f'  when image "{interrupt.when_asset}"')
            lines.append("  {")
            for action in interrupt.actions:
                code = IRMapper._action_to_code(action)
                lines.append(f"    {code}")
            lines.append("  }")
            lines.append("}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _action_to_code(action: ActionIR) -> str:
        """Convert action IR to code string."""
        if action.action_type == "label":
            return f'label {action.params.get("name", "unnamed")}:'
        
        if action.action_type == "goto":
            return f'goto {action.params.get("target", "unknown")};'
        
        if action.action_type in ("break", "continue", "return"):
            return f"{action.action_type};"
        
        # Function call
        args = []
        kwargs = []
        
        for key, value in action.params.items():
            if key.startswith("arg"):
                if isinstance(value, str):
                    args.append(f'"{value}"')
                else:
                    args.append(str(value))
            else:
                if isinstance(value, str):
                    kwargs.append(f'{key}="{value}"')
                elif isinstance(value, bool):
                    kwargs.append(f'{key}={str(value).lower()}')
                else:
                    kwargs.append(f'{key}={value}')
        
        all_args = ", ".join(args + kwargs)
        return f"{action.action_type}({all_args});"


def parse_to_ir(source: str) -> tuple[ScriptIR, list[str]]:
    """
    Parse DSL source code to IR.
    
    Returns:
        Tuple of (ScriptIR, list of error messages)
    """
    parser = Parser(source)
    program = parser.parse()
    
    errors = [str(e) for e in parser.errors]
    
    if errors:
        # Return empty IR with errors
        ir = ScriptIR(is_valid=False, parse_errors=errors)
        return ir, errors
    
    ir = IRMapper.ast_to_ir(program, source)
    ir.is_valid = True
    return ir, []


def ir_to_code(ir: ScriptIR) -> str:
    """
    Generate DSL code from IR.
    
    The output is formatted per DSL spec.
    """
    raw_code = IRMapper.ir_to_code(ir)
    return format_code(raw_code)
