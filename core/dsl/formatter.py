"""
RetroAuto v2 - DSL Formatter

Pretty printer for DSL code.
Rules:
- 2-space indent
- K&R braces (opening { on same line)
- Keywords lowercase
- Strings always "double quotes"
- Deterministic, idempotent output
- Preserve comments
"""

from __future__ import annotations

from core.dsl.ast import (
    ArrayExpr,
    AssignStmt,
    ASTNode,
    BinaryExpr,
    BlockStmt,
    BreakStmt,
    CallExpr,
    ConstStmt,
    ContinueStmt,
    ExprStmt,
    FlowDecl,
    ForStmt,
    GotoStmt,
    HotkeysDecl,
    Identifier,
    IfStmt,
    InterruptDecl,
    LabelStmt,
    LetStmt,
    Literal,
    Program,
    ReturnStmt,
    TryStmt,
    UnaryExpr,
    WhileStmt,
)


class Formatter:
    """
    DSL code formatter.

    Usage:
        formatter = Formatter()
        formatted_code = formatter.format(program)
    """

    INDENT = "  "  # 2 spaces

    def __init__(self) -> None:
        self.indent_level = 0
        self.output: list[str] = []

    def format(self, program: Program) -> str:
        """Format entire program."""
        self.indent_level = 0
        self.output = []

        # Hotkeys
        if program.hotkeys:
            self._format_hotkeys(program.hotkeys)
            self._newline()

        # Constants
        for const in program.constants:
            self._format_const(const)
            self._newline()

        if program.constants:
            self._newline()

        # Flows
        for i, flow in enumerate(program.flows):
            if i > 0:
                self._newline()
            self._format_flow(flow)

        # Interrupts
        for interrupt in program.interrupts:
            self._newline()
            self._format_interrupt(interrupt)

        return "".join(self.output).rstrip() + "\n"

    # ─────────────────────────────────────────────────────────────
    # Output Helpers
    # ─────────────────────────────────────────────────────────────

    def _write(self, text: str) -> None:
        """Write text to output."""
        self.output.append(text)

    def _indent(self) -> None:
        """Write current indentation."""
        self._write(self.INDENT * self.indent_level)

    def _newline(self) -> None:
        """Write newline."""
        self._write("\n")

    def _write_line(self, text: str) -> None:
        """Write indented line."""
        self._indent()
        self._write(text)
        self._newline()

    def _write_comments(self, node: ASTNode) -> None:
        """Write leading comments for a node."""
        for comment in node.leading_comments:
            self._write_line(comment)

    def _write_trailing_comment(self, node: ASTNode) -> None:
        """Write trailing comment for a node."""
        if node.trailing_comment:
            self._write(f"  {node.trailing_comment}")

    # ─────────────────────────────────────────────────────────────
    # Top-level Formatting
    # ─────────────────────────────────────────────────────────────

    def _format_hotkeys(self, hotkeys: HotkeysDecl) -> None:
        """Format hotkeys block."""
        self._write_comments(hotkeys)
        self._write_line("hotkeys {")
        self.indent_level += 1

        for key, value in sorted(hotkeys.bindings.items()):
            self._indent()
            self._write(f'{key} = "{value}"')
            self._newline()

        self.indent_level -= 1
        self._write_line("}")

    def _format_flow(self, flow: FlowDecl) -> None:
        """Format flow declaration."""
        self._write_comments(flow)
        self._indent()
        self._write(f"flow {flow.name} ")
        self._format_block(flow.body, newline_after=True)

    def _format_interrupt(self, interrupt: InterruptDecl) -> None:
        """Format interrupt declaration."""
        self._write_comments(interrupt)
        self._write_line("interrupt {")
        self.indent_level += 1

        self._write_line(f"priority {interrupt.priority}")
        self._write_line(f'when image "{interrupt.when_asset}"')
        self._format_block(interrupt.body, newline_after=True)

        self.indent_level -= 1
        self._write_line("}")

    def _format_const(self, const: ConstStmt) -> None:
        """Format const declaration."""
        self._write_comments(const)
        self._indent()
        self._write(f"const {const.name} = ")
        self._format_expr(const.initializer)
        self._write(";")
        self._write_trailing_comment(const)
        self._newline()

    # ─────────────────────────────────────────────────────────────
    # Statement Formatting
    # ─────────────────────────────────────────────────────────────

    def _format_block(self, block: BlockStmt, newline_after: bool = False) -> None:
        """Format block { ... }."""
        self._write("{")
        self._newline()
        self.indent_level += 1

        for stmt in block.statements:
            self._format_statement(stmt)

        self.indent_level -= 1
        self._indent()
        self._write("}")
        if newline_after:
            self._newline()

    def _format_statement(self, stmt: ASTNode) -> None:
        """Format a single statement."""
        self._write_comments(stmt)

        if isinstance(stmt, LabelStmt):
            self._format_label(stmt)
        elif isinstance(stmt, GotoStmt):
            self._format_goto(stmt)
        elif isinstance(stmt, IfStmt):
            self._format_if(stmt)
        elif isinstance(stmt, WhileStmt):
            self._format_while(stmt)
        elif isinstance(stmt, ForStmt):
            self._format_for(stmt)
        elif isinstance(stmt, LetStmt):
            self._format_let(stmt)
        elif isinstance(stmt, AssignStmt):
            self._format_assign(stmt)
        elif isinstance(stmt, BreakStmt):
            self._write_line("break;")
        elif isinstance(stmt, ContinueStmt):
            self._write_line("continue;")
        elif isinstance(stmt, ReturnStmt):
            self._format_return(stmt)
        elif isinstance(stmt, TryStmt):
            self._format_try(stmt)
        elif isinstance(stmt, ExprStmt):
            self._format_expr_stmt(stmt)
        else:
            # Fallback for unknown statements
            self._write_line(f"// Unknown statement: {type(stmt).__name__}")

    def _format_label(self, stmt: LabelStmt) -> None:
        """Format label statement."""
        self._write_line(f"label {stmt.name}:")

    def _format_goto(self, stmt: GotoStmt) -> None:
        """Format goto statement."""
        self._indent()
        self._write(f"goto {stmt.target};")
        self._write_trailing_comment(stmt)
        self._newline()

    def _format_if(self, stmt: IfStmt) -> None:
        """Format if statement."""
        self._indent()
        self._write("if ")
        self._format_expr(stmt.condition)
        self._write(" ")
        self._format_block(stmt.then_branch)

        for elif_cond, elif_body in stmt.elif_branches:
            self._write(" elif ")
            self._format_expr(elif_cond)
            self._write(" ")
            self._format_block(elif_body)

        if stmt.else_branch:
            self._write(" else ")
            self._format_block(stmt.else_branch)

        self._newline()

    def _format_while(self, stmt: WhileStmt) -> None:
        """Format while statement."""
        self._indent()
        self._write("while ")
        self._format_expr(stmt.condition)
        self._write(" ")
        self._format_block(stmt.body)
        self._newline()

    def _format_for(self, stmt: ForStmt) -> None:
        """Format for statement."""
        self._indent()
        self._write(f"for {stmt.variable} in ")
        self._format_expr(stmt.iterable)
        self._write(" ")
        self._format_block(stmt.body)
        self._newline()

    def _format_let(self, stmt: LetStmt) -> None:
        """Format let statement."""
        self._indent()
        self._write(f"let {stmt.name}")
        if stmt.initializer:
            self._write(" = ")
            self._format_expr(stmt.initializer)
        self._write(";")
        self._write_trailing_comment(stmt)
        self._newline()

    def _format_assign(self, stmt: AssignStmt) -> None:
        """Format assignment statement."""
        self._indent()
        self._format_expr(stmt.target)
        self._write(" = ")
        self._format_expr(stmt.value)
        self._write(";")
        self._write_trailing_comment(stmt)
        self._newline()

    def _format_return(self, stmt: ReturnStmt) -> None:
        """Format return statement."""
        self._indent()
        if stmt.value:
            self._write("return ")
            self._format_expr(stmt.value)
            self._write(";")
        else:
            self._write("return;")
        self._write_trailing_comment(stmt)
        self._newline()

    def _format_try(self, stmt: TryStmt) -> None:
        """Format try-catch statement."""
        self._indent()
        self._write("try ")
        self._format_block(stmt.try_block)

        if stmt.catch_block:
            self._write(" catch")
            if stmt.catch_var:
                self._write(f" {stmt.catch_var}")
            self._write(" ")
            self._format_block(stmt.catch_block)

        self._newline()

    def _format_expr_stmt(self, stmt: ExprStmt) -> None:
        """Format expression statement."""
        self._indent()
        self._format_expr(stmt.expr)
        self._write(";")
        self._write_trailing_comment(stmt)
        self._newline()

    # ─────────────────────────────────────────────────────────────
    # Expression Formatting
    # ─────────────────────────────────────────────────────────────

    def _format_expr(self, expr: ASTNode) -> None:
        """Format an expression."""
        if isinstance(expr, Literal):
            self._format_literal(expr)
        elif isinstance(expr, Identifier):
            self._write(expr.name)
        elif isinstance(expr, BinaryExpr):
            self._format_binary(expr)
        elif isinstance(expr, UnaryExpr):
            self._format_unary(expr)
        elif isinstance(expr, CallExpr):
            self._format_call(expr)
        elif isinstance(expr, ArrayExpr):
            self._format_array(expr)
        else:
            self._write(f"/* unknown expr: {type(expr).__name__} */")

    def _format_literal(self, lit: Literal) -> None:
        """Format literal value."""
        if lit.literal_type == "string":
            # Always use double quotes
            escaped = str(lit.value).replace("\\", "\\\\").replace('"', '\\"')
            self._write(f'"{escaped}"')
        elif lit.literal_type == "bool":
            self._write("true" if lit.value else "false")
        elif lit.literal_type == "null":
            self._write("null")
        elif lit.literal_type == "duration":
            self._write(str(lit.value))
        else:
            self._write(str(lit.value))

    def _format_binary(self, expr: BinaryExpr) -> None:
        """Format binary expression."""
        needs_parens = isinstance(expr.left, BinaryExpr)
        if needs_parens:
            self._write("(")
        self._format_expr(expr.left)
        if needs_parens:
            self._write(")")

        self._write(f" {expr.operator} ")

        needs_parens = isinstance(expr.right, BinaryExpr)
        if needs_parens:
            self._write("(")
        self._format_expr(expr.right)
        if needs_parens:
            self._write(")")

    def _format_unary(self, expr: UnaryExpr) -> None:
        """Format unary expression."""
        self._write(expr.operator)
        self._format_expr(expr.operand)

    def _format_call(self, expr: CallExpr) -> None:
        """Format function call."""
        # Special case: block end keywords should be formatted as keywords, not function calls
        keyword_map = {
            "end_if": "endif",
            "end_loop": "endloop",
            "end_while": "endwhile",
        }
        if expr.callee in keyword_map:
            self._write(keyword_map[expr.callee])
            return

        self._write(f"{expr.callee}(")

        # Format positional arguments
        parts: list[str] = []
        for arg in expr.args:
            self.output.append("")
            start = len(self.output) - 1
            self._format_expr(arg)
            parts.append("".join(self.output[start:]))
            self.output = self.output[:start]

        # Format keyword arguments
        for key, value in sorted(expr.kwargs.items()):
            self.output.append("")
            start = len(self.output) - 1
            self._format_expr(value)
            val_str = "".join(self.output[start:])
            self.output = self.output[:start]
            parts.append(f"{key}={val_str}")

        self._write(", ".join(parts))
        self._write(")")

    def _format_array(self, expr: ArrayExpr) -> None:
        """Format array literal."""
        self._write("[")
        for i, elem in enumerate(expr.elements):
            if i > 0:
                self._write(", ")
            self._format_expr(elem)
        self._write("]")


def format_code(source: str) -> str:
    """
    Format DSL source code.

    This is idempotent: format(format(code)) == format(code)
    """
    from core.dsl.parser import Parser

    parser = Parser(source)
    program = parser.parse()

    if parser.errors:
        # Return original if there are parse errors
        return source

    formatter = Formatter()
    return formatter.format(program)
