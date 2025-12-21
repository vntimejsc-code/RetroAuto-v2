"""
RetroAuto v2 - DSL Lexer

Tokenizes DSL source code into a stream of tokens.
Supports:
- Keywords (flow, if, while, etc.)
- Identifiers
- Literals (strings, numbers, durations, booleans)
- Operators and delimiters
- Comments (line and block)
"""

from __future__ import annotations

from core.dsl.tokens import KEYWORDS, Token, TokenType


class LexerError(Exception):
    """Lexer error with position information."""

    def __init__(self, message: str, line: int, column: int) -> None:
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"{message} at line {line}, column {column}")


class Lexer:
    """
    DSL Lexer - converts source code to tokens.

    Usage:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
    """

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []
        self.errors: list[LexerError] = []

    def tokenize(self) -> list[Token]:
        """Tokenize the source code and return list of tokens."""
        self.tokens = []
        self.errors = []
        self.pos = 0
        self.line = 1
        self.column = 1

        while not self._at_end():
            self._scan_token()

        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    def _at_end(self) -> bool:
        """Check if we've reached the end of source."""
        return self.pos >= len(self.source)

    def _peek(self, offset: int = 0) -> str:
        """Look at character at current position + offset."""
        idx = self.pos + offset
        if idx >= len(self.source):
            return "\0"
        return self.source[idx]

    def _advance(self) -> str:
        """Consume and return current character."""
        char = self._peek()
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _match(self, expected: str) -> bool:
        """Consume character if it matches expected."""
        if self._peek() == expected:
            self._advance()
            return True
        return False

    def _add_token(
        self,
        token_type: TokenType,
        value: str,
        start_line: int,
        start_col: int,
    ) -> None:
        """Add a token to the list."""
        self.tokens.append(
            Token(token_type, value, start_line, start_col, self.line, self.column)
        )

    def _skip_whitespace(self) -> None:
        """Skip spaces and tabs (not newlines)."""
        while self._peek() in " \t\r":
            self._advance()

    def _scan_token(self) -> None:
        """Scan and add the next token."""
        self._skip_whitespace()

        if self._at_end():
            return

        start_line = self.line
        start_col = self.column
        char = self._peek()

        # ─────────────────────────────────────────────────────────────
        # Newlines
        # ─────────────────────────────────────────────────────────────
        if char == "\n":
            self._advance()
            # Skip newlines as whitespace (DSL is not newline-sensitive)
            return

        # ─────────────────────────────────────────────────────────────
        # Comments
        # ─────────────────────────────────────────────────────────────
        if char == "/":
            if self._peek(1) == "/":
                self._scan_line_comment(start_line, start_col)
                return
            elif self._peek(1) == "*":
                self._scan_block_comment(start_line, start_col)
                return

        # ─────────────────────────────────────────────────────────────
        # Strings
        # ─────────────────────────────────────────────────────────────
        if char in '"\'':
            self._scan_string(start_line, start_col)
            return

        # ─────────────────────────────────────────────────────────────
        # Numbers and Durations
        # ─────────────────────────────────────────────────────────────
        if char.isdigit():
            self._scan_number(start_line, start_col)
            return

        # ─────────────────────────────────────────────────────────────
        # Identifiers and Keywords
        # ─────────────────────────────────────────────────────────────
        if char.isalpha() or char == "_":
            self._scan_identifier(start_line, start_col)
            return

        # ─────────────────────────────────────────────────────────────
        # Operators and Delimiters
        # ─────────────────────────────────────────────────────────────
        self._scan_operator(start_line, start_col)

    def _scan_line_comment(self, start_line: int, start_col: int) -> None:
        """Scan // line comment."""
        self._advance()  # /
        self._advance()  # /
        start = self.pos
        while not self._at_end() and self._peek() != "\n":
            self._advance()
        value = "//" + self.source[start : self.pos]
        self._add_token(TokenType.LINE_COMMENT, value, start_line, start_col)

    def _scan_block_comment(self, start_line: int, start_col: int) -> None:
        """Scan /* block comment */."""
        self._advance()  # /
        self._advance()  # *
        start = self.pos
        while not self._at_end():
            if self._peek() == "*" and self._peek(1) == "/":
                value = "/*" + self.source[start : self.pos] + "*/"
                self._advance()  # *
                self._advance()  # /
                self._add_token(TokenType.BLOCK_COMMENT, value, start_line, start_col)
                return
            self._advance()
        # Unterminated block comment
        self.errors.append(
            LexerError("Unterminated block comment", start_line, start_col)
        )
        value = "/*" + self.source[start : self.pos]
        self._add_token(TokenType.ERROR, value, start_line, start_col)

    def _scan_string(self, start_line: int, start_col: int) -> None:
        """Scan string literal."""
        quote = self._advance()  # " or '
        chars: list[str] = []

        while not self._at_end() and self._peek() != quote:
            if self._peek() == "\n":
                self.errors.append(
                    LexerError("Unterminated string", start_line, start_col)
                )
                self._add_token(TokenType.ERROR, quote + "".join(chars), start_line, start_col)
                return
            if self._peek() == "\\":
                self._advance()  # backslash
                escape_char = self._advance()
                escape_map = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'"}
                chars.append(escape_map.get(escape_char, escape_char))
            else:
                chars.append(self._advance())

        if self._at_end():
            self.errors.append(
                LexerError("Unterminated string", start_line, start_col)
            )
            self._add_token(TokenType.ERROR, quote + "".join(chars), start_line, start_col)
            return

        self._advance()  # closing quote
        value = "".join(chars)
        self._add_token(TokenType.STRING, value, start_line, start_col)

    def _scan_number(self, start_line: int, start_col: int) -> None:
        """Scan integer, float, or duration literal."""
        start = self.pos

        # Consume digits
        while self._peek().isdigit():
            self._advance()

        # Check for float
        if self._peek() == "." and self._peek(1).isdigit():
            self._advance()  # .
            while self._peek().isdigit():
                self._advance()
            value = self.source[start : self.pos]
            self._add_token(TokenType.FLOAT, value, start_line, start_col)
            return

        # Check for duration suffix
        suffix_start = self.pos
        while self._peek().isalpha():
            self._advance()

        suffix = self.source[suffix_start : self.pos].lower()
        if suffix in ("ms", "s", "m", "h"):
            value = self.source[start : self.pos]
            self._add_token(TokenType.DURATION, value, start_line, start_col)
        else:
            # Backtrack if there was an invalid suffix (treat as identifier later)
            self.pos = suffix_start
            self.column -= len(suffix)
            value = self.source[start : self.pos]
            self._add_token(TokenType.INTEGER, value, start_line, start_col)

    def _scan_identifier(self, start_line: int, start_col: int) -> None:
        """Scan identifier or keyword."""
        start = self.pos

        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        value = self.source[start : self.pos]
        token_type = KEYWORDS.get(value.lower(), TokenType.IDENTIFIER)

        # Keywords should be lowercase
        if token_type != TokenType.IDENTIFIER:
            value = value.lower()

        self._add_token(token_type, value, start_line, start_col)

    def _scan_operator(self, start_line: int, start_col: int) -> None:
        """Scan operator or delimiter."""
        char = self._advance()

        # Two-character operators
        two_char_ops = {
            "==": TokenType.EQ,
            "!=": TokenType.NEQ,
            "<=": TokenType.LTE,
            ">=": TokenType.GTE,
            "&&": TokenType.AND,
            "||": TokenType.OR,
            "->": TokenType.ARROW,
        }

        for op, token_type in two_char_ops.items():
            if char == op[0] and self._peek() == op[1]:
                self._advance()
                self._add_token(token_type, op, start_line, start_col)
                return

        # Single-character operators/delimiters
        single_char_ops = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "%": TokenType.PERCENT,
            "<": TokenType.LT,
            ">": TokenType.GT,
            "!": TokenType.NOT,
            "=": TokenType.ASSIGN,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            ";": TokenType.SEMICOLON,
            ":": TokenType.COLON,
            ",": TokenType.COMMA,
            ".": TokenType.DOT,
        }

        if char in single_char_ops:
            self._add_token(single_char_ops[char], char, start_line, start_col)
        else:
            # Unknown character
            self.errors.append(
                LexerError(f"Unexpected character '{char}'", start_line, start_col)
            )
            self._add_token(TokenType.ERROR, char, start_line, start_col)
