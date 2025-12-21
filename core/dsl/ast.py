"""
RetroAuto v2 - DSL Abstract Syntax Tree

AST node classes with span tracking for:
- Error reporting
- Debugger integration
- Round-trip code generation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class Span:
    """Source location span for AST nodes."""

    start_line: int
    start_col: int
    end_line: int
    end_col: int

    def __str__(self) -> str:
        if self.start_line == self.end_line:
            return f"{self.start_line}:{self.start_col}-{self.end_col}"
        return f"{self.start_line}:{self.start_col}-{self.end_line}:{self.end_col}"

    @classmethod
    def from_token(cls, token: Any) -> Span:
        """Create span from a token."""
        return cls(token.line, token.column, token.end_line, token.end_column)

    def merge(self, other: Span) -> Span:
        """Merge two spans to cover both ranges."""
        return Span(
            min(self.start_line, other.start_line),
            min(self.start_col, other.start_col) if self.start_line == other.start_line else (
                self.start_col if self.start_line < other.start_line else other.start_col
            ),
            max(self.end_line, other.end_line),
            max(self.end_col, other.end_col) if self.end_line == other.end_line else (
                self.end_col if self.end_line > other.end_line else other.end_col
            ),
        )


def _gen_id() -> str:
    """Generate unique node ID."""
    return str(uuid4())[:8]


# ─────────────────────────────────────────────────────────────
# Base class uses kw_only=True to allow subclass fields without defaults
# ─────────────────────────────────────────────────────────────


@dataclass(kw_only=True)
class ASTNode:
    """Base class for all AST nodes."""

    span: Span
    id: str = field(default_factory=_gen_id)
    leading_comments: list[str] = field(default_factory=list)
    trailing_comment: str | None = None


# ─────────────────────────────────────────────────────────────
# Expressions
# ─────────────────────────────────────────────────────────────


@dataclass(kw_only=True)
class Literal(ASTNode):
    """Literal value: string, number, duration, bool, null."""

    value: Any
    literal_type: str  # "string", "int", "float", "duration", "bool", "null"


@dataclass(kw_only=True)
class Identifier(ASTNode):
    """Variable or function name."""

    name: str


@dataclass(kw_only=True)
class BinaryExpr(ASTNode):
    """Binary operation: a + b, a == b, etc."""

    left: ASTNode
    operator: str  # "+", "-", "==", "!=", "&&", "||", etc.
    right: ASTNode


@dataclass(kw_only=True)
class UnaryExpr(ASTNode):
    """Unary operation: !a, -b."""

    operator: str  # "!", "-"
    operand: ASTNode


@dataclass(kw_only=True)
class CallExpr(ASTNode):
    """Function call: wait_image("btn", timeout=5s)."""

    callee: str
    args: list[ASTNode] = field(default_factory=list)
    kwargs: dict[str, ASTNode] = field(default_factory=dict)


@dataclass(kw_only=True)
class ArrayExpr(ASTNode):
    """Array literal: [a, b, c]."""

    elements: list[ASTNode] = field(default_factory=list)


@dataclass(kw_only=True)
class MemberExpr(ASTNode):
    """Member access: obj.property."""

    object: ASTNode
    property: str


@dataclass(kw_only=True)
class IndexExpr(ASTNode):
    """Index access: arr[0]."""

    object: ASTNode
    index: ASTNode


# ─────────────────────────────────────────────────────────────
# Statements
# ─────────────────────────────────────────────────────────────


@dataclass(kw_only=True)
class ExprStmt(ASTNode):
    """Expression statement: func();."""

    expr: ASTNode


@dataclass(kw_only=True)
class BlockStmt(ASTNode):
    """Block of statements: { ... }."""

    statements: list[ASTNode] = field(default_factory=list)


@dataclass(kw_only=True)
class LetStmt(ASTNode):
    """Variable declaration: let x = 5;."""

    name: str
    initializer: ASTNode | None = None


@dataclass(kw_only=True)
class ConstStmt(ASTNode):
    """Constant declaration: const X = 5;."""

    name: str
    initializer: ASTNode


@dataclass(kw_only=True)
class AssignStmt(ASTNode):
    """Assignment: x = 5;."""

    target: ASTNode  # Identifier or MemberExpr or IndexExpr
    value: ASTNode


@dataclass(kw_only=True)
class IfStmt(ASTNode):
    """If statement with optional elif/else."""

    condition: ASTNode
    then_branch: BlockStmt
    elif_branches: list[tuple[ASTNode, BlockStmt]] = field(default_factory=list)
    else_branch: BlockStmt | None = None


@dataclass(kw_only=True)
class WhileStmt(ASTNode):
    """While loop."""

    condition: ASTNode
    body: BlockStmt


@dataclass(kw_only=True)
class ForStmt(ASTNode):
    """For loop: for i in range(10) { }."""

    variable: str
    iterable: ASTNode
    body: BlockStmt


@dataclass(kw_only=True)
class LabelStmt(ASTNode):
    """Label for goto: label start:."""

    name: str


@dataclass(kw_only=True)
class GotoStmt(ASTNode):
    """Goto statement: goto start;."""

    target: str


@dataclass(kw_only=True)
class BreakStmt(ASTNode):
    """Break statement."""

    pass


@dataclass(kw_only=True)
class ContinueStmt(ASTNode):
    """Continue statement."""

    pass


@dataclass(kw_only=True)
class ReturnStmt(ASTNode):
    """Return statement: return value;."""

    value: ASTNode | None = None


@dataclass(kw_only=True)
class TryStmt(ASTNode):
    """Try-catch statement."""

    try_block: BlockStmt
    catch_var: str | None = None
    catch_block: BlockStmt | None = None


# ─────────────────────────────────────────────────────────────
# Top-level Declarations
# ─────────────────────────────────────────────────────────────


@dataclass(kw_only=True)
class FlowDecl(ASTNode):
    """Flow declaration: flow main { ... }."""

    name: str
    body: BlockStmt


@dataclass(kw_only=True)
class InterruptDecl(ASTNode):
    """Interrupt declaration.

    interrupt {
        priority 10
        when image "error_popup"
        { ... }
    }
    """

    priority: int
    when_asset: str
    body: BlockStmt
    roi: ASTNode | None = None


@dataclass(kw_only=True)
class HotkeysDecl(ASTNode):
    """Hotkeys configuration.

    hotkeys {
        start = "F5"
        stop = "F6"
        pause = "F7"
    }
    """

    bindings: dict[str, str] = field(default_factory=dict)


@dataclass(kw_only=True)
class Program(ASTNode):
    """Root AST node containing all declarations."""

    hotkeys: HotkeysDecl | None = None
    flows: list[FlowDecl] = field(default_factory=list)
    interrupts: list[InterruptDecl] = field(default_factory=list)
    constants: list[ConstStmt] = field(default_factory=list)

    @property
    def main_flow(self) -> FlowDecl | None:
        """Get the main flow."""
        for flow in self.flows:
            if flow.name == "main":
                return flow
        return self.flows[0] if self.flows else None
