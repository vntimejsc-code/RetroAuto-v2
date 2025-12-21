"""
RetroAuto v2 - DSL Semantic Analyzer

Validates AST semantically:
- Resolves asset references
- Resolves flow references
- Validates label/goto pairs
- Type checks built-in function arguments
- Produces diagnostics with quick-fix hints
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.dsl.ast import (
    ASTNode,
    ArrayExpr,
    AssignStmt,
    BinaryExpr,
    BlockStmt,
    CallExpr,
    ConstStmt,
    ExprStmt,
    FlowDecl,
    ForStmt,
    GotoStmt,
    Identifier,
    IfStmt,
    InterruptDecl,
    LabelStmt,
    LetStmt,
    Literal,
    Program,
    ReturnStmt,
    Span,
    TryStmt,
    UnaryExpr,
    WhileStmt,
)
from core.dsl.diagnostics import (
    Diagnostic,
    Severity,
    duplicate_flow,
    duplicate_label,
    invalid_argument,
    missing_argument,
    unknown_asset,
    unknown_flow,
    unknown_label,
)


@dataclass
class FunctionSignature:
    """Signature of a built-in function."""

    name: str
    required_args: list[str]
    optional_args: dict[str, str]  # name -> type
    return_type: str


# Built-in function signatures
BUILTIN_FUNCTIONS: dict[str, FunctionSignature] = {
    # Vision
    "wait_image": FunctionSignature(
        name="wait_image",
        required_args=["asset"],
        optional_args={
            "appear": "bool",
            "timeout": "duration",
            "poll": "duration",
            "roi": "roi",
            "threshold": "float",
        },
        return_type="match",
    ),
    "find_image": FunctionSignature(
        name="find_image",
        required_args=["asset"],
        optional_args={
            "roi": "roi",
            "threshold": "float",
        },
        return_type="match",
    ),
    "image_exists": FunctionSignature(
        name="image_exists",
        required_args=["asset"],
        optional_args={
            "roi": "roi",
            "threshold": "float",
        },
        return_type="bool",
    ),
    "wait_any": FunctionSignature(
        name="wait_any",
        required_args=["assets"],
        optional_args={
            "timeout": "duration",
            "poll": "duration",
        },
        return_type="tuple",
    ),
    # Input
    "click": FunctionSignature(
        name="click",
        required_args=["x", "y"],
        optional_args={
            "button": "string",
            "clicks": "int",
            "interval": "duration",
        },
        return_type="void",
    ),
    "move": FunctionSignature(
        name="move",
        required_args=["x", "y"],
        optional_args={},
        return_type="void",
    ),
    "hotkey": FunctionSignature(
        name="hotkey",
        required_args=[],  # Variadic
        optional_args={},
        return_type="void",
    ),
    "type_text": FunctionSignature(
        name="type_text",
        required_args=["text"],
        optional_args={
            "paste": "bool",
            "enter": "bool",
        },
        return_type="void",
    ),
    "sleep": FunctionSignature(
        name="sleep",
        required_args=["duration"],
        optional_args={},
        return_type="void",
    ),
    # Control
    "run_flow": FunctionSignature(
        name="run_flow",
        required_args=["flow_name"],
        optional_args={},
        return_type="void",
    ),
    "log": FunctionSignature(
        name="log",
        required_args=["message"],
        optional_args={
            "level": "string",
        },
        return_type="void",
    ),
    "assert": FunctionSignature(
        name="assert",
        required_args=["condition"],
        optional_args={
            "message": "string",
        },
        return_type="void",
    ),
    # Utility
    "range": FunctionSignature(
        name="range",
        required_args=["end"],
        optional_args={
            "start": "int",
            "step": "int",
        },
        return_type="iterable",
    ),
}


@dataclass
class Scope:
    """Variable scope for semantic analysis."""

    variables: dict[str, ASTNode] = field(default_factory=dict)
    parent: Scope | None = None

    def lookup(self, name: str) -> ASTNode | None:
        """Look up variable in scope chain."""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def define(self, name: str, node: ASTNode) -> None:
        """Define variable in current scope."""
        self.variables[name] = node


@dataclass
class SymbolTable:
    """Symbol table for the entire program."""

    assets: dict[str, Span] = field(default_factory=dict)
    flows: dict[str, FlowDecl] = field(default_factory=dict)
    labels: dict[str, dict[str, LabelStmt]] = field(default_factory=dict)  # flow -> {label -> stmt}
    constants: dict[str, ConstStmt] = field(default_factory=dict)


class SemanticAnalyzer:
    """
    Semantic analyzer for DSL programs.

    Usage:
        analyzer = SemanticAnalyzer(known_assets=["btn_ok", "popup"])
        diagnostics = analyzer.analyze(program)
    """

    def __init__(self, known_assets: list[str] | None = None) -> None:
        self.known_assets = set(known_assets or [])
        self.symbols = SymbolTable()
        self.diagnostics: list[Diagnostic] = []
        self.current_flow: str = ""
        self.scope: Scope = Scope()

    def analyze(self, program: Program) -> list[Diagnostic]:
        """Analyze program and return diagnostics."""
        self.diagnostics = []
        self.symbols = SymbolTable()

        # First pass: collect all declarations
        self._collect_declarations(program)

        # Second pass: validate references
        self._validate_program(program)

        return self.diagnostics

    # ─────────────────────────────────────────────────────────────
    # First Pass: Declaration Collection
    # ─────────────────────────────────────────────────────────────

    def _collect_declarations(self, program: Program) -> None:
        """Collect all top-level declarations."""
        # Collect constants
        for const in program.constants:
            if const.name in self.symbols.constants:
                # Duplicate constant (warning)
                pass
            self.symbols.constants[const.name] = const

        # Collect flows
        for flow in program.flows:
            if flow.name in self.symbols.flows:
                original = self.symbols.flows[flow.name]
                self.diagnostics.append(
                    duplicate_flow(flow.name, flow.span, original.span)
                )
            else:
                self.symbols.flows[flow.name] = flow

            # Collect labels within flow
            self.symbols.labels[flow.name] = {}
            self._collect_labels(flow.name, flow.body)

        # Collect interrupt assets
        for interrupt in program.interrupts:
            if interrupt.when_asset and interrupt.when_asset not in self.known_assets:
                self.diagnostics.append(
                    unknown_asset(interrupt.when_asset, interrupt.span)
                )

    def _collect_labels(self, flow_name: str, block: BlockStmt) -> None:
        """Collect labels in a block."""
        for stmt in block.statements:
            if isinstance(stmt, LabelStmt):
                labels = self.symbols.labels[flow_name]
                if stmt.name in labels:
                    original = labels[stmt.name]
                    self.diagnostics.append(
                        duplicate_label(stmt.name, stmt.span, original.span)
                    )
                else:
                    labels[stmt.name] = stmt

            # Recurse into nested blocks
            if isinstance(stmt, IfStmt):
                self._collect_labels(flow_name, stmt.then_branch)
                for _, elif_body in stmt.elif_branches:
                    self._collect_labels(flow_name, elif_body)
                if stmt.else_branch:
                    self._collect_labels(flow_name, stmt.else_branch)
            elif isinstance(stmt, WhileStmt):
                self._collect_labels(flow_name, stmt.body)
            elif isinstance(stmt, ForStmt):
                self._collect_labels(flow_name, stmt.body)
            elif isinstance(stmt, TryStmt):
                self._collect_labels(flow_name, stmt.try_block)
                if stmt.catch_block:
                    self._collect_labels(flow_name, stmt.catch_block)

    # ─────────────────────────────────────────────────────────────
    # Second Pass: Validation
    # ─────────────────────────────────────────────────────────────

    def _validate_program(self, program: Program) -> None:
        """Validate all references in program."""
        for flow in program.flows:
            self.current_flow = flow.name
            self.scope = Scope()
            self._validate_block(flow.body)

        for interrupt in program.interrupts:
            self.current_flow = "__interrupt__"
            self.scope = Scope()
            self._validate_block(interrupt.body)

    def _validate_block(self, block: BlockStmt) -> None:
        """Validate statements in a block."""
        for stmt in block.statements:
            self._validate_statement(stmt)

    def _validate_statement(self, stmt: ASTNode) -> None:
        """Validate a single statement."""
        if isinstance(stmt, GotoStmt):
            self._validate_goto(stmt)
        elif isinstance(stmt, IfStmt):
            self._validate_expression(stmt.condition)
            self._validate_block(stmt.then_branch)
            for elif_cond, elif_body in stmt.elif_branches:
                self._validate_expression(elif_cond)
                self._validate_block(elif_body)
            if stmt.else_branch:
                self._validate_block(stmt.else_branch)
        elif isinstance(stmt, WhileStmt):
            self._validate_expression(stmt.condition)
            self._validate_block(stmt.body)
        elif isinstance(stmt, ForStmt):
            self._validate_expression(stmt.iterable)
            # Add loop variable to scope
            old_scope = self.scope
            self.scope = Scope(parent=old_scope)
            self.scope.define(stmt.variable, stmt)
            self._validate_block(stmt.body)
            self.scope = old_scope
        elif isinstance(stmt, LetStmt):
            if stmt.initializer:
                self._validate_expression(stmt.initializer)
            self.scope.define(stmt.name, stmt)
        elif isinstance(stmt, AssignStmt):
            self._validate_expression(stmt.target)
            self._validate_expression(stmt.value)
        elif isinstance(stmt, ReturnStmt):
            if stmt.value:
                self._validate_expression(stmt.value)
        elif isinstance(stmt, TryStmt):
            self._validate_block(stmt.try_block)
            if stmt.catch_block:
                old_scope = self.scope
                self.scope = Scope(parent=old_scope)
                if stmt.catch_var:
                    self.scope.define(stmt.catch_var, stmt)
                self._validate_block(stmt.catch_block)
                self.scope = old_scope
        elif isinstance(stmt, ExprStmt):
            self._validate_expression(stmt.expr)

    def _validate_goto(self, stmt: GotoStmt) -> None:
        """Validate goto target exists."""
        if self.current_flow not in self.symbols.labels:
            return
        labels = self.symbols.labels[self.current_flow]
        if stmt.target not in labels:
            self.diagnostics.append(
                unknown_label(stmt.target, stmt.span)
            )

    def _validate_expression(self, expr: ASTNode) -> None:
        """Validate an expression."""
        if isinstance(expr, CallExpr):
            self._validate_call(expr)
        elif isinstance(expr, BinaryExpr):
            self._validate_expression(expr.left)
            self._validate_expression(expr.right)
        elif isinstance(expr, UnaryExpr):
            self._validate_expression(expr.operand)
        elif isinstance(expr, ArrayExpr):
            for elem in expr.elements:
                self._validate_expression(elem)
        elif isinstance(expr, Identifier):
            # Check if variable exists
            if not self.scope.lookup(expr.name):
                # Could be a constant
                if expr.name not in self.symbols.constants:
                    # Unknown variable - could add warning here
                    pass

    def _validate_call(self, call: CallExpr) -> None:
        """Validate function call."""
        # Check if it's a built-in
        sig = BUILTIN_FUNCTIONS.get(call.callee)

        if call.callee == "run_flow":
            # Validate flow reference
            if call.args:
                flow_arg = call.args[0]
                if isinstance(flow_arg, Literal) and flow_arg.literal_type == "string":
                    flow_name = flow_arg.value
                    if flow_name not in self.symbols.flows:
                        self.diagnostics.append(
                            unknown_flow(flow_name, call.span)
                        )

        elif call.callee in ("wait_image", "find_image", "image_exists"):
            # Validate asset reference
            if call.args:
                asset_arg = call.args[0]
                if isinstance(asset_arg, Literal) and asset_arg.literal_type == "string":
                    asset_id = asset_arg.value
                    if asset_id not in self.known_assets:
                        self.diagnostics.append(
                            unknown_asset(asset_id, call.span)
                        )

        elif call.callee == "wait_any":
            # Validate asset list
            if call.args:
                list_arg = call.args[0]
                if isinstance(list_arg, ArrayExpr):
                    for elem in list_arg.elements:
                        if isinstance(elem, Literal) and elem.literal_type == "string":
                            if elem.value not in self.known_assets:
                                self.diagnostics.append(
                                    unknown_asset(elem.value, elem.span)
                                )

        # Validate argument count for known functions
        if sig:
            min_args = len(sig.required_args)
            if len(call.args) < min_args:
                # Check if missing args are provided as kwargs
                missing = []
                for i, arg_name in enumerate(sig.required_args):
                    if i >= len(call.args) and arg_name not in call.kwargs:
                        missing.append(arg_name)
                for arg_name in missing:
                    self.diagnostics.append(
                        missing_argument(call.callee, arg_name, call.span)
                    )

        # Validate all argument expressions
        for arg in call.args:
            self._validate_expression(arg)
        for arg in call.kwargs.values():
            self._validate_expression(arg)


def analyze(program: Program, known_assets: list[str] | None = None) -> list[Diagnostic]:
    """
    Analyze program and return diagnostics.

    Args:
        program: Parsed AST
        known_assets: List of known asset IDs for validation

    Returns:
        List of diagnostics (errors, warnings)
    """
    analyzer = SemanticAnalyzer(known_assets)
    return analyzer.analyze(program)
