"""
RetroAuto v2 - DSL Parser

Recursive descent parser with error recovery.
Produces AST with precise span tracking.
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
    Span,
    TryStmt,
    UnaryExpr,
    WhileStmt,
)
from core.dsl.diagnostics import (
    Diagnostic,
    Severity,
    expected_token,
    unexpected_token,
)
from core.dsl.lexer import Lexer
from core.dsl.tokens import Token, TokenType


class ParseError(Exception):
    """Parse error for internal use."""

    def __init__(self, diagnostic: Diagnostic) -> None:
        self.diagnostic = diagnostic
        super().__init__(diagnostic.message)


class Parser:
    """
    DSL Parser - converts tokens to AST.

    Features:
    - Recursive descent parsing
    - Error recovery (synchronize at statement boundaries)
    - Comment preservation
    - Precise span tracking

    Usage:
        parser = Parser(source_code)
        program = parser.parse()
        if parser.errors:
            print(parser.errors)
    """

    def __init__(self, source: str) -> None:
        self.source = source
        self.tokens: list[Token] = []
        self.pos = 0
        self.errors: list[Diagnostic] = []
        self.comments: list[Token] = []  # Collected comments

    def parse(self) -> Program:
        """Parse source code and return AST."""
        # Tokenize
        lexer = Lexer(self.source)
        all_tokens = lexer.tokenize()

        # Separate comments from tokens
        self.tokens = []
        self.comments = []
        for token in all_tokens:
            if token.type in (TokenType.LINE_COMMENT, TokenType.BLOCK_COMMENT):
                self.comments.append(token)
            else:
                self.tokens.append(token)

        # Add lexer errors
        for err in lexer.errors:
            self.errors.append(
                Diagnostic(
                    code="E1003",
                    severity=Severity.ERROR,
                    message=err.message,
                    span=Span(err.line, err.column, err.line, err.column + 1),
                )
            )

        self.pos = 0

        # Parse program
        return self._parse_program()

    # ─────────────────────────────────────────────────────────────
    # Token Handling
    # ─────────────────────────────────────────────────────────────

    def _at_end(self) -> bool:
        """Check if at end of tokens."""
        return self._peek().type == TokenType.EOF

    def _peek(self, offset: int = 0) -> Token:
        """Look at current token."""
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[idx]

    def _advance(self) -> Token:
        """Consume and return current token."""
        token = self._peek()
        if not self._at_end():
            self.pos += 1
        return token

    def _check(self, *types: TokenType) -> bool:
        """Check if current token is one of the types."""
        return self._peek().type in types

    def _match(self, *types: TokenType) -> Token | None:
        """Consume token if it matches, return it or None."""
        if self._check(*types):
            return self._advance()
        return None

    def _expect(self, token_type: TokenType, message: str = "") -> Token:
        """Consume token or raise error."""
        if self._check(token_type):
            return self._advance()
        current = self._peek()
        expected_name = token_type.name.lower()
        if message:
            msg = message
        else:
            msg = f"Expected {expected_name}"
        raise ParseError(expected_token(expected_name, current.value, Span.from_token(current)))

    def _span_from(self, start_token: Token) -> Span:
        """Create span from start token to current position."""
        end_token = self.tokens[max(0, self.pos - 1)]
        return Span(
            start_token.line,
            start_token.column,
            end_token.end_line,
            end_token.end_column,
        )

    def _synchronize(self) -> None:
        """Recover from parse error by skipping to next statement boundary."""
        self._advance()

        while not self._at_end():
            # Sync at statement boundaries
            if self._peek(-1).type == TokenType.SEMICOLON:
                return

            # Sync at block starts
            if self._check(
                TokenType.FLOW,
                TokenType.INTERRUPT,
                TokenType.HOTKEYS,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.FOR,
                TokenType.LABEL,
                TokenType.RETURN,
                TokenType.BREAK,
                TokenType.CONTINUE,
                TokenType.RBRACE,
            ):
                return

            self._advance()

    # ─────────────────────────────────────────────────────────────
    # Top-level Parsing
    # ─────────────────────────────────────────────────────────────

    def _parse_program(self) -> Program:
        """Parse entire program."""
        start = self._peek()
        hotkeys: HotkeysDecl | None = None
        flows: list[FlowDecl] = []
        interrupts: list[InterruptDecl] = []
        constants: list[ConstStmt] = []

        while not self._at_end():
            try:
                if self._check(TokenType.HOTKEYS):
                    hotkeys = self._parse_hotkeys()
                elif self._check(TokenType.FLOW):
                    flows.append(self._parse_flow())
                elif self._check(TokenType.INTERRUPT):
                    interrupts.append(self._parse_interrupt())
                elif self._check(TokenType.CONST):
                    constants.append(self._parse_const())
                else:
                    # Try to parse as statement for better error
                    token = self._peek()
                    self.errors.append(unexpected_token(token.value, Span.from_token(token)))
                    self._synchronize()
            except ParseError as e:
                self.errors.append(e.diagnostic)
                self._synchronize()

        return Program(
            span=self._span_from(start),
            hotkeys=hotkeys,
            flows=flows,
            interrupts=interrupts,
            constants=constants,
        )

    def _parse_hotkeys(self) -> HotkeysDecl:
        """Parse hotkeys block."""
        start = self._expect(TokenType.HOTKEYS)
        self._expect(TokenType.LBRACE)

        bindings: dict[str, str] = {}

        while not self._check(TokenType.RBRACE) and not self._at_end():
            name_token = self._expect(TokenType.IDENTIFIER)
            self._expect(TokenType.ASSIGN)
            value_token = self._expect(TokenType.STRING)
            bindings[name_token.value] = value_token.value

            # Optional semicolon
            self._match(TokenType.SEMICOLON)

        self._expect(TokenType.RBRACE)

        return HotkeysDecl(
            span=self._span_from(start),
            bindings=bindings,
        )

    def _parse_flow(self) -> FlowDecl:
        """Parse flow declaration."""
        start = self._expect(TokenType.FLOW)
        name_token = self._expect(TokenType.IDENTIFIER)
        body = self._parse_block()

        return FlowDecl(
            span=self._span_from(start),
            name=name_token.value,
            body=body,
        )

    def _parse_interrupt(self) -> InterruptDecl:
        """Parse interrupt declaration."""
        start = self._expect(TokenType.INTERRUPT)
        self._expect(TokenType.LBRACE)

        priority = 0
        when_asset = ""
        roi: ASTNode | None = None

        # Parse priority and when clauses
        while not self._check(TokenType.LBRACE, TokenType.RBRACE) and not self._at_end():
            if self._match(TokenType.PRIORITY):
                priority_token = self._expect(TokenType.INTEGER)
                priority = int(priority_token.value)
            elif self._match(TokenType.WHEN):
                self._expect(TokenType.IMAGE)
                asset_token = self._expect(TokenType.STRING)
                when_asset = asset_token.value
            else:
                break

        # Parse body block
        body = self._parse_block()

        self._expect(TokenType.RBRACE)

        return InterruptDecl(
            span=self._span_from(start),
            priority=priority,
            when_asset=when_asset,
            body=body,
            roi=roi,
        )

    def _parse_const(self) -> ConstStmt:
        """Parse const declaration."""
        start = self._expect(TokenType.CONST)
        name_token = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.ASSIGN)
        value = self._parse_expression()
        self._match(TokenType.SEMICOLON)

        return ConstStmt(
            span=self._span_from(start),
            name=name_token.value,
            initializer=value,
        )

    # ─────────────────────────────────────────────────────────────
    # Statement Parsing
    # ─────────────────────────────────────────────────────────────

    def _parse_block(self) -> BlockStmt:
        """Parse block of statements { ... }."""
        start = self._expect(TokenType.LBRACE)
        statements: list[ASTNode] = []

        while not self._check(TokenType.RBRACE) and not self._at_end():
            try:
                stmt = self._parse_statement()
                if stmt:
                    statements.append(stmt)
            except ParseError as e:
                self.errors.append(e.diagnostic)
                self._synchronize()

        self._expect(TokenType.RBRACE)

        return BlockStmt(
            span=self._span_from(start),
            statements=statements,
        )

    def _parse_statement(self) -> ASTNode | None:
        """Parse a single statement."""
        # Label statement
        if self._check(TokenType.LABEL):
            return self._parse_label()

        # Goto statement
        if self._check(TokenType.GOTO):
            return self._parse_goto()

        # If statement
        if self._check(TokenType.IF):
            return self._parse_if()

        # While statement
        if self._check(TokenType.WHILE):
            return self._parse_while()

        # For statement
        if self._check(TokenType.FOR):
            return self._parse_for()

        # Let statement
        if self._check(TokenType.LET):
            return self._parse_let()

        # Try statement
        if self._check(TokenType.TRY):
            return self._parse_try()

        # Break
        if self._check(TokenType.BREAK):
            start = self._advance()
            self._match(TokenType.SEMICOLON)
            return BreakStmt(span=self._span_from(start))

        # Continue
        if self._check(TokenType.CONTINUE):
            start = self._advance()
            self._match(TokenType.SEMICOLON)
            return ContinueStmt(span=self._span_from(start))

        # Return
        if self._check(TokenType.RETURN):
            return self._parse_return()

        # ─────────────────────────────────────────────────────────────
        # RetroScript: $variable assignment
        # ─────────────────────────────────────────────────────────────
        if self._check(TokenType.VARIABLE):
            return self._parse_variable_assignment()

        # ─────────────────────────────────────────────────────────────
        # RetroScript: repeat N: block
        # ─────────────────────────────────────────────────────────────
        if self._check(TokenType.REPEAT):
            return self._parse_repeat()

        # ─────────────────────────────────────────────────────────────
        # RetroScript: retry N: block
        # ─────────────────────────────────────────────────────────────
        if self._check(TokenType.RETRY):
            return self._parse_retry()

        # ─────────────────────────────────────────────────────────────
        # RetroScript: match $expr: patterns
        # ─────────────────────────────────────────────────────────────
        if self._check(TokenType.MATCH):
            return self._parse_match()

        # Expression statement
        return self._parse_expression_statement()

    def _parse_label(self) -> LabelStmt:
        """Parse label statement: label name:."""
        start = self._expect(TokenType.LABEL)
        name_token = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.COLON)

        return LabelStmt(
            span=self._span_from(start),
            name=name_token.value,
        )

    def _parse_goto(self) -> GotoStmt:
        """Parse goto statement: goto name;."""
        start = self._expect(TokenType.GOTO)
        target_token = self._expect(TokenType.IDENTIFIER)
        self._match(TokenType.SEMICOLON)

        return GotoStmt(
            span=self._span_from(start),
            target=target_token.value,
        )

    def _parse_if(self) -> IfStmt:
        """Parse if statement with elif/else."""
        start = self._expect(TokenType.IF)
        condition = self._parse_expression()
        then_branch = self._parse_block()

        elif_branches: list[tuple[ASTNode, BlockStmt]] = []
        while self._match(TokenType.ELIF):
            elif_cond = self._parse_expression()
            elif_body = self._parse_block()
            elif_branches.append((elif_cond, elif_body))

        else_branch: BlockStmt | None = None
        if self._match(TokenType.ELSE):
            else_branch = self._parse_block()

        return IfStmt(
            span=self._span_from(start),
            condition=condition,
            then_branch=then_branch,
            elif_branches=elif_branches,
            else_branch=else_branch,
        )

    def _parse_while(self) -> WhileStmt:
        """Parse while loop."""
        start = self._expect(TokenType.WHILE)
        condition = self._parse_expression()
        body = self._parse_block()

        return WhileStmt(
            span=self._span_from(start),
            condition=condition,
            body=body,
        )

    def _parse_for(self) -> ForStmt:
        """Parse for loop: for i in range(10) { }."""
        start = self._expect(TokenType.FOR)
        var_token = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.IN)
        iterable = self._parse_expression()
        body = self._parse_block()

        return ForStmt(
            span=self._span_from(start),
            variable=var_token.value,
            iterable=iterable,
            body=body,
        )

    def _parse_let(self) -> LetStmt:
        """Parse let statement: let x = 5;."""
        start = self._expect(TokenType.LET)
        name_token = self._expect(TokenType.IDENTIFIER)

        initializer: ASTNode | None = None
        if self._match(TokenType.ASSIGN):
            initializer = self._parse_expression()

        self._match(TokenType.SEMICOLON)

        return LetStmt(
            span=self._span_from(start),
            name=name_token.value,
            initializer=initializer,
        )

    def _parse_try(self) -> TryStmt:
        """Parse try-catch statement."""
        start = self._expect(TokenType.TRY)
        try_block = self._parse_block()

        catch_var: str | None = None
        catch_block: BlockStmt | None = None

        if self._match(TokenType.CATCH):
            if self._check(TokenType.IDENTIFIER):
                catch_var = self._advance().value
            catch_block = self._parse_block()

        return TryStmt(
            span=self._span_from(start),
            try_block=try_block,
            catch_var=catch_var,
            catch_block=catch_block,
        )

    def _parse_return(self) -> ReturnStmt:
        """Parse return statement."""
        start = self._expect(TokenType.RETURN)

        value: ASTNode | None = None
        if not self._check(TokenType.SEMICOLON, TokenType.RBRACE):
            value = self._parse_expression()

        self._match(TokenType.SEMICOLON)

        return ReturnStmt(
            span=self._span_from(start),
            value=value,
        )

    # ─────────────────────────────────────────────────────────────
    # RetroScript Parsing
    # ─────────────────────────────────────────────────────────────

    def _parse_variable_assignment(self) -> AssignStmt:
        """Parse $variable = expression (RetroScript)."""
        start = self._advance()  # $variable token
        var_name = start.value  # includes $ prefix

        self._expect(TokenType.ASSIGN, "Expected '=' after variable name")
        value = self._parse_expression()

        # Optional semicolon (RetroScript doesn't require it)
        self._match(TokenType.SEMICOLON)

        # Create identifier node for target
        target = Identifier(span=self._span_from(start), name=var_name)

        return AssignStmt(
            span=self._span_from(start),
            target=target,
            value=value,
        )

    def _parse_repeat(self) -> ForStmt:
        """Parse repeat N: block (RetroScript).

        Translates to: for _i in range(N) { block }
        """
        start = self._expect(TokenType.REPEAT)

        # Parse count (optional - if missing, infinite loop)
        count: ASTNode | None = None
        if self._check(TokenType.INTEGER):
            count_token = self._advance()
            count = Literal(
                span=self._span_from(count_token),
                value=int(count_token.value),
                literal_type="integer",
            )

        # Optional 'times' keyword
        self._match(TokenType.TIMES)

        # Expect colon or brace
        if not self._match(TokenType.COLON):
            self._expect(TokenType.LBRACE)
            # Put back for block parsing
            self.pos -= 1

        # Parse block
        body = self._parse_block()

        # Optional 'end' keyword (RetroScript style)
        self._match(TokenType.END)

        # Create synthetic range call
        if count:
            range_call = CallExpr(
                span=self._span_from(start),
                callee="range",
                args=[count],
            )
        else:
            # Infinite loop - use large number with safety limit
            range_call = CallExpr(
                span=self._span_from(start),
                callee="range",
                args=[Literal(span=self._span_from(start), value=1000, literal_type="integer")],
            )

        return ForStmt(
            span=self._span_from(start),
            variable="_i",
            iterable=range_call,
            body=body,
        )

    def _parse_retry(self) -> TryStmt:
        """Parse retry N: block (RetroScript).

        Syntax: retry 3 times: block
        Translates to: try { block } catch err { if _retry < 3 { _retry++; goto retry } }
        """
        start = self._expect(TokenType.RETRY)

        # Parse count
        count = 3  # Default retry count
        if self._check(TokenType.INTEGER):
            count_token = self._advance()
            count = int(count_token.value)

        # Optional 'times' keyword
        self._match(TokenType.TIMES)

        # Expect colon or brace
        if not self._match(TokenType.COLON):
            self._expect(TokenType.LBRACE)
            self.pos -= 1

        # Parse try block
        try_block = self._parse_block()

        # Optional 'end' keyword
        self._match(TokenType.END)

        # Parse optional else block (runs if all retries fail)
        else_block: BlockStmt | None = None
        if self._match(TokenType.ELSE):
            if not self._match(TokenType.COLON):
                self._expect(TokenType.LBRACE)
                self.pos -= 1
            else_block = self._parse_block()
            self._match(TokenType.END)

        # For now, we create a simple TryStmt
        # The engine will handle retry logic based on retry_count metadata
        result = TryStmt(
            span=self._span_from(start),
            try_block=try_block,
            catch_var="_retry_err",
            catch_block=else_block if else_block else BlockStmt(
                span=self._span_from(start),
                statements=[],
            ),
        )

        # Store retry count as attribute (engine uses this)
        result.retry_count = count  # type: ignore
        return result

    def _parse_match(self) -> IfStmt:
        """Parse match statement (RetroScript pattern matching).

        Syntax:
            match $result:
                Found(pos, score): click pos
                NotFound: log "Not found"
                Timeout: retry

        Translates to if-elif chain based on expression value.
        """
        start = self._expect(TokenType.MATCH)

        # Parse the expression to match on
        match_expr = self._parse_expression()

        # Expect colon
        self._expect(TokenType.COLON, "Expected ':' after match expression")

        # Parse match arms - simplified version
        # For now, we treat match as a simple if-statement
        # match $result:
        #   Found: body1
        #   NotFound: body2
        # becomes: if $result == "Found" { body1 } elif $result == "NotFound" { body2 }

        # Expect block or indented patterns
        if self._match(TokenType.LBRACE):
            # Block-style match
            body = self._parse_block_inner()
            self._expect(TokenType.RBRACE)
        else:
            # Simple single-line or indented
            body = self._parse_block()

        # Optional 'end' keyword
        self._match(TokenType.END)

        # For now, create a simplified structure
        # The match expression becomes an if statement checking the expression
        # This is a placeholder - full pattern matching would need more complex AST
        return IfStmt(
            span=self._span_from(start),
            condition=match_expr,
            then_branch=body,
            elif_branches=[],
            else_branch=None,
        )

    def _parse_block_inner(self) -> BlockStmt:
        """Parse block statements without braces (for match arms)."""
        statements: list[ASTNode] = []
        start = self._peek()

        while not self._check(TokenType.RBRACE, TokenType.EOF):
            try:
                stmt = self._parse_statement()
                if stmt:
                    statements.append(stmt)
            except ParseError as e:
                self.errors.append(e.diagnostic)
                self._synchronize()

        return BlockStmt(
            span=self._span_from(start),
            statements=statements,
        )

    def _parse_expression_statement(self) -> ASTNode:
        """Parse expression statement or assignment."""
        start = self._peek()
        expr = self._parse_expression()

        # Check for assignment
        if self._match(TokenType.ASSIGN):
            value = self._parse_expression()
            self._match(TokenType.SEMICOLON)
            return AssignStmt(
                span=self._span_from(start),
                target=expr,
                value=value,
            )

        self._match(TokenType.SEMICOLON)
        from core.dsl.ast import ExprStmt

        return ExprStmt(
            span=self._span_from(start),
            expr=expr,
        )

    # ─────────────────────────────────────────────────────────────
    # Expression Parsing (Precedence Climbing)
    # ─────────────────────────────────────────────────────────────

    def _parse_expression(self) -> ASTNode:
        """Parse expression (entry point)."""
        return self._parse_or()

    def _parse_or(self) -> ASTNode:
        """Parse || or 'or' expression."""
        left = self._parse_and()

        # Support both || and 'or' keyword (RetroScript)
        while self._match(TokenType.OR, TokenType.OR_KW):
            right = self._parse_and()
            left = BinaryExpr(
                span=left.span.merge(right.span),
                left=left,
                operator="or",  # Normalize to 'or'
                right=right,
            )

        return left

    def _parse_and(self) -> ASTNode:
        """Parse && or 'and' expression."""
        left = self._parse_equality()

        # Support both && and 'and' keyword (RetroScript)
        while self._match(TokenType.AND, TokenType.AND_KW):
            right = self._parse_equality()
            left = BinaryExpr(
                span=left.span.merge(right.span),
                left=left,
                operator="and",  # Normalize to 'and'
                right=right,
            )

        return left

    def _parse_equality(self) -> ASTNode:
        """Parse == != expression."""
        left = self._parse_comparison()

        while True:
            if self._match(TokenType.EQ):
                right = self._parse_comparison()
                left = BinaryExpr(
                    span=left.span.merge(right.span),
                    left=left,
                    operator="==",
                    right=right,
                )
            elif self._match(TokenType.NEQ):
                right = self._parse_comparison()
                left = BinaryExpr(
                    span=left.span.merge(right.span),
                    left=left,
                    operator="!=",
                    right=right,
                )
            else:
                break

        return left

    def _parse_comparison(self) -> ASTNode:
        """Parse < > <= >= expression."""
        left = self._parse_additive()

        op_map = {
            TokenType.LT: "<",
            TokenType.GT: ">",
            TokenType.LTE: "<=",
            TokenType.GTE: ">=",
        }

        while True:
            matched = False
            for token_type, op in op_map.items():
                if self._match(token_type):
                    right = self._parse_additive()
                    left = BinaryExpr(
                        span=left.span.merge(right.span),
                        left=left,
                        operator=op,
                        right=right,
                    )
                    matched = True
                    break
            if not matched:
                break

        return left

    def _parse_additive(self) -> ASTNode:
        """Parse + - expression."""
        left = self._parse_multiplicative()

        while True:
            if self._match(TokenType.PLUS):
                right = self._parse_multiplicative()
                left = BinaryExpr(
                    span=left.span.merge(right.span),
                    left=left,
                    operator="+",
                    right=right,
                )
            elif self._match(TokenType.MINUS):
                right = self._parse_multiplicative()
                left = BinaryExpr(
                    span=left.span.merge(right.span),
                    left=left,
                    operator="-",
                    right=right,
                )
            else:
                break

        return left

    def _parse_multiplicative(self) -> ASTNode:
        """Parse * / % expression."""
        left = self._parse_unary()

        while True:
            if self._match(TokenType.STAR):
                right = self._parse_unary()
                left = BinaryExpr(
                    span=left.span.merge(right.span),
                    left=left,
                    operator="*",
                    right=right,
                )
            elif self._match(TokenType.SLASH):
                right = self._parse_unary()
                left = BinaryExpr(
                    span=left.span.merge(right.span),
                    left=left,
                    operator="/",
                    right=right,
                )
            elif self._match(TokenType.PERCENT):
                right = self._parse_unary()
                left = BinaryExpr(
                    span=left.span.merge(right.span),
                    left=left,
                    operator="%",
                    right=right,
                )
            else:
                break

        return left

    def _parse_unary(self) -> ASTNode:
        """Parse ! - unary expression."""
        if self._match(TokenType.NOT):
            start = self.tokens[self.pos - 1]
            operand = self._parse_unary()
            return UnaryExpr(
                span=self._span_from(start),
                operator="!",
                operand=operand,
            )

        if self._match(TokenType.MINUS):
            start = self.tokens[self.pos - 1]
            operand = self._parse_unary()
            return UnaryExpr(
                span=self._span_from(start),
                operator="-",
                operand=operand,
            )

        return self._parse_call()

    def _parse_call(self) -> ASTNode:
        """Parse function call or primary."""
        expr = self._parse_primary()

        while True:
            if self._match(TokenType.LPAREN):
                expr = self._finish_call(expr)
            else:
                break

        return expr

    def _finish_call(self, callee: ASTNode) -> CallExpr:
        """Parse function call arguments."""
        args: list[ASTNode] = []
        kwargs: dict[str, ASTNode] = {}

        if not self._check(TokenType.RPAREN):
            while True:
                # Check for keyword argument
                if self._check(TokenType.IDENTIFIER) and self._peek(1).type == TokenType.ASSIGN:
                    name = self._advance().value
                    self._advance()  # =
                    value = self._parse_expression()
                    kwargs[name] = value
                else:
                    args.append(self._parse_expression())

                if not self._match(TokenType.COMMA):
                    break

        self._expect(TokenType.RPAREN)

        callee_name = callee.name if isinstance(callee, Identifier) else "unknown"

        return CallExpr(
            span=callee.span.merge(Span.from_token(self.tokens[self.pos - 1])),
            callee=callee_name,
            args=args,
            kwargs=kwargs,
        )

    def _parse_primary(self) -> ASTNode:
        """Parse primary expression (literals, identifiers, groups)."""
        token = self._peek()

        # Null
        if self._match(TokenType.NULL):
            return Literal(
                span=Span.from_token(token),
                value=None,
                literal_type="null",
            )

        # Booleans
        if self._match(TokenType.TRUE):
            return Literal(
                span=Span.from_token(token),
                value=True,
                literal_type="bool",
            )

        if self._match(TokenType.FALSE):
            return Literal(
                span=Span.from_token(token),
                value=False,
                literal_type="bool",
            )

        # Numbers
        if self._match(TokenType.INTEGER):
            return Literal(
                span=Span.from_token(token),
                value=int(token.value),
                literal_type="int",
            )

        if self._match(TokenType.FLOAT):
            return Literal(
                span=Span.from_token(token),
                value=float(token.value),
                literal_type="float",
            )

        # Duration
        if self._match(TokenType.DURATION):
            return Literal(
                span=Span.from_token(token),
                value=token.value,
                literal_type="duration",
            )

        # String
        if self._match(TokenType.STRING):
            return Literal(
                span=Span.from_token(token),
                value=token.value,
                literal_type="string",
            )

        # Identifier
        if self._match(TokenType.IDENTIFIER):
            return Identifier(
                span=Span.from_token(token),
                name=token.value,
            )

        # ─────────────────────────────────────────────────────────────
        # RetroScript: Action keywords as callable identifiers
        # These can be used as function calls: find(btn), click(100, 200), etc.
        # ─────────────────────────────────────────────────────────────
        retro_actions = (
            TokenType.FIND,
            TokenType.WAIT,
            TokenType.CLICK,
            TokenType.TYPE_KW,
            TokenType.PRESS,
            TokenType.SLEEP,
            TokenType.SCROLL,
            TokenType.DRAG,
            TokenType.RUN,
        )
        if self._check(*retro_actions):
            token = self._advance()
            return Identifier(
                span=Span.from_token(token),
                name=token.value,
            )

        # RetroScript: $variable as expression
        if self._match(TokenType.VARIABLE):
            return Identifier(
                span=Span.from_token(token),
                name=token.value,
            )

        # Array literal
        if self._match(TokenType.LBRACKET):
            elements: list[ASTNode] = []
            if not self._check(TokenType.RBRACKET):
                while True:
                    elements.append(self._parse_expression())
                    if not self._match(TokenType.COMMA):
                        break
            self._expect(TokenType.RBRACKET)
            return ArrayExpr(
                span=self._span_from(token),
                elements=elements,
            )

        # Grouped expression
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr

        # Error
        raise ParseError(unexpected_token(token.value, Span.from_token(token)))
