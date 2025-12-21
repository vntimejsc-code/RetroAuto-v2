"""
RetroAuto v2 - AST Interpreter

Execute RetroScript AST nodes directly.
Part of RetroScript Phase 9 - Script Execution Engine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
    Identifier,
    IfStmt,
    ImportStmt,
    LetStmt,
    Literal,
    Program,
    ReturnStmt,
    TryStmt,
    UnaryExpr,
    WhileStmt,
)
from core.engine.builtins import BuiltinRegistry, get_builtins
from core.engine.scope import ExecutionContext, ScopeManager

if TYPE_CHECKING:
    pass


class InterpreterError(Exception):
    """Error during script interpretation."""

    def __init__(self, message: str, node: ASTNode | None = None) -> None:
        self.node = node
        super().__init__(message)


class Interpreter:
    """AST interpreter for RetroScript.

    Usage:
        interpreter = Interpreter()
        result = interpreter.execute(program)
    """

    def __init__(self, builtins: BuiltinRegistry | None = None) -> None:
        self.builtins = builtins or get_builtins()
        self.context = ExecutionContext()
        self._flows: dict[str, FlowDecl] = {}

    def execute(self, program: Program) -> Any:
        """Execute a program.

        Args:
            program: Parsed program AST

        Returns:
            Result of main flow, if any
        """
        # Register constants
        for const in program.constants:
            value = self._eval(const.initializer)
            self.context.scope.set_global(const.name, value)

        # Register flows
        for flow in program.flows:
            self._flows[flow.name] = flow

        # Execute main flow
        main_flow = program.main_flow
        if main_flow:
            return self._execute_flow(main_flow)

        return None

    def _execute_flow(self, flow: FlowDecl) -> Any:
        """Execute a flow."""
        self.context.enter_flow(flow.name)
        try:
            self._execute_block(flow.body)
            return self.context.get_return()
        finally:
            self.context.exit_flow()

    def _execute_block(self, block: BlockStmt) -> None:
        """Execute a block of statements."""
        for stmt in block.statements:
            self._execute_stmt(stmt)

            # Check for control flow
            if (self.context.should_return() or
                self.context.should_break() or
                self.context.should_continue()):
                break

    def _execute_stmt(self, node: ASTNode) -> None:
        """Execute a statement."""
        if isinstance(node, LetStmt):
            self._execute_let(node)
        elif isinstance(node, AssignStmt):
            self._execute_assign(node)
        elif isinstance(node, IfStmt):
            self._execute_if(node)
        elif isinstance(node, WhileStmt):
            self._execute_while(node)
        elif isinstance(node, ForStmt):
            self._execute_for(node)
        elif isinstance(node, TryStmt):
            self._execute_try(node)
        elif isinstance(node, ReturnStmt):
            self._execute_return(node)
        elif isinstance(node, BreakStmt):
            self.context.set_break()
        elif isinstance(node, ContinueStmt):
            self.context.set_continue()
        elif isinstance(node, BlockStmt):
            self._execute_block(node)
        elif isinstance(node, ExprStmt):
            self._eval(node.expr)
        elif isinstance(node, CallExpr):
            self._eval_call(node)
        else:
            # Unknown/expression statement
            self._eval(node)

    def _execute_let(self, node: LetStmt) -> None:
        """Execute let declaration."""
        value = None
        if node.initializer:
            value = self._eval(node.initializer)
        self.context.scope.define(node.name, value)

    def _execute_assign(self, node: AssignStmt) -> None:
        """Execute assignment."""
        value = self._eval(node.value)

        if isinstance(node.target, Identifier):
            name = node.target.name
            # Handle $variable syntax
            if name.startswith("$"):
                name = name[1:]
            self.context.scope.assign(name, value)
        else:
            raise InterpreterError(f"Invalid assignment target: {node.target}", node)

    def _execute_if(self, node: IfStmt) -> None:
        """Execute if statement."""
        condition = self._eval(node.condition)

        if self._is_truthy(condition):
            self._execute_block(node.then_branch)
        else:
            # Check elif branches
            for elif_cond, elif_block in node.elif_branches:
                if self._is_truthy(self._eval(elif_cond)):
                    self._execute_block(elif_block)
                    return

            # Execute else
            if node.else_branch:
                self._execute_block(node.else_branch)

    def _execute_while(self, node: WhileStmt) -> None:
        """Execute while loop."""
        while self._is_truthy(self._eval(node.condition)):
            self._execute_block(node.body)

            # Handle break/continue
            if self.context.clear_break():
                break
            self.context.clear_continue()

            # Handle return
            if self.context.should_return():
                break

    def _execute_for(self, node: ForStmt) -> None:
        """Execute for loop."""
        iterable = self._eval(node.iterable)

        if not hasattr(iterable, "__iter__"):
            raise InterpreterError(f"Cannot iterate over: {type(iterable)}", node)

        for item in iterable:
            self.context.scope.define(node.variable, item)
            self._execute_block(node.body)

            # Handle break/continue
            if self.context.clear_break():
                break
            self.context.clear_continue()

            # Handle return
            if self.context.should_return():
                break

    def _execute_try(self, node: TryStmt) -> None:
        """Execute try-catch block."""
        try:
            self._execute_block(node.try_block)
        except Exception as e:
            # Set catch variable
            if node.catch_var:
                self.context.scope.define(node.catch_var, str(e))
            self._execute_block(node.catch_block)

    def _execute_return(self, node: ReturnStmt) -> None:
        """Execute return statement."""
        value = None
        if node.value:
            value = self._eval(node.value)
        self.context.set_return(value)

    def _eval(self, node: ASTNode) -> Any:
        """Evaluate an expression."""
        if isinstance(node, Literal):
            return self._eval_literal(node)
        elif isinstance(node, Identifier):
            return self._eval_identifier(node)
        elif isinstance(node, BinaryExpr):
            return self._eval_binary(node)
        elif isinstance(node, UnaryExpr):
            return self._eval_unary(node)
        elif isinstance(node, CallExpr):
            return self._eval_call(node)
        elif isinstance(node, ArrayExpr):
            return self._eval_array(node)
        else:
            raise InterpreterError(f"Unknown expression type: {type(node)}", node)

    def _eval_literal(self, node: Literal) -> Any:
        """Evaluate literal value."""
        if node.literal_type == "null":
            return None
        elif node.literal_type == "bool":
            return node.value in (True, "true", "True")
        elif node.literal_type == "duration":
            # Return duration in milliseconds
            return self._parse_duration_ms(node.value)
        return node.value

    def _eval_identifier(self, node: Identifier) -> Any:
        """Evaluate identifier."""
        name = node.name
        if name.startswith("$"):
            name = name[1:]
        return self.context.scope.get(name)

    def _eval_binary(self, node: BinaryExpr) -> Any:
        """Evaluate binary expression."""
        op = node.operator

        # Short-circuit evaluation for logical operators
        if op in ("and", "&&"):
            left = self._eval(node.left)
            if not self._is_truthy(left):
                return left
            return self._eval(node.right)

        if op in ("or", "||"):
            left = self._eval(node.left)
            if self._is_truthy(left):
                return left
            return self._eval(node.right)

        # Evaluate both sides
        left = self._eval(node.left)
        right = self._eval(node.right)

        # Arithmetic
        if op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right
        elif op == "-":
            return left - right
        elif op == "*":
            return left * right
        elif op == "/":
            if right == 0:
                raise InterpreterError("Division by zero", node)
            return left / right
        elif op == "%":
            return left % right

        # Comparison
        elif op == "==":
            return left == right
        elif op == "!=":
            return left != right
        elif op == "<":
            return left < right
        elif op == "<=":
            return left <= right
        elif op == ">":
            return left > right
        elif op == ">=":
            return left >= right

        else:
            raise InterpreterError(f"Unknown operator: {op}", node)

    def _eval_unary(self, node: UnaryExpr) -> Any:
        """Evaluate unary expression."""
        operand = self._eval(node.operand)

        if node.operator == "-":
            return -operand
        elif node.operator in ("!", "not"):
            return not self._is_truthy(operand)

        raise InterpreterError(f"Unknown unary operator: {node.operator}", node)

    def _eval_call(self, node: CallExpr) -> Any:
        """Evaluate function call."""
        name = node.callee

        # Check if it's a flow call
        if name in self._flows:
            return self._call_flow(name, node.args)

        # Check if it's a built-in
        if self.builtins.has(name):
            args = [self._eval(arg) for arg in node.args]
            kwargs = {k: self._eval(v) for k, v in node.kwargs.items()}
            return self.builtins.call(name, *args, **kwargs)

        # Check special built-in "run"
        if name == "run":
            if node.args:
                flow_name = self._eval(node.args[0])
                if isinstance(flow_name, str) and flow_name in self._flows:
                    return self._call_flow(flow_name, node.args[1:])

        raise InterpreterError(f"Unknown function: {name}", node)

    def _call_flow(self, name: str, args: list[ASTNode]) -> Any:
        """Call a flow by name."""
        flow = self._flows.get(name)
        if not flow:
            raise InterpreterError(f"Unknown flow: {name}")

        return self._execute_flow(flow)

    def _eval_array(self, node: ArrayExpr) -> list[Any]:
        """Evaluate array expression."""
        return [self._eval(elem) for elem in node.elements]

    def _is_truthy(self, value: Any) -> bool:
        """Check if value is truthy."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return True

    def _parse_duration_ms(self, value: Any) -> int:
        """Parse duration to milliseconds."""
        if isinstance(value, (int, float)):
            return int(value)
        s = str(value).strip().lower()
        if s.endswith("ms"):
            return int(s[:-2])
        elif s.endswith("s"):
            return int(float(s[:-1]) * 1000)
        elif s.endswith("m"):
            return int(float(s[:-1]) * 60000)
        elif s.endswith("h"):
            return int(float(s[:-1]) * 3600000)
        return int(value)


def interpret(source: str) -> Any:
    """Convenience function to parse and interpret source code.

    Args:
        source: RetroScript source code

    Returns:
        Result of execution
    """
    from core.dsl.parser import Parser

    parser = Parser(source)
    program = parser.parse()

    if parser.errors:
        raise InterpreterError(f"Parse errors: {parser.errors}")

    interpreter = Interpreter()
    return interpreter.execute(program)
