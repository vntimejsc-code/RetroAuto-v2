"""
RetroAuto v2 - DSL Token Types

Defines all token types for the DSL lexer.
"""

from enum import Enum, auto


class TokenType(Enum):
    """Token types for DSL lexer."""

    # ─────────────────────────────────────────────────────────────
    # Literals
    # ─────────────────────────────────────────────────────────────
    INTEGER = auto()  # 123
    FLOAT = auto()  # 1.5
    STRING = auto()  # "hello" or 'hello'
    DURATION = auto()  # 250ms, 2s, 1m
    TRUE = auto()  # true
    FALSE = auto()  # false
    NULL = auto()  # null

    # ─────────────────────────────────────────────────────────────
    # Identifiers
    # ─────────────────────────────────────────────────────────────
    IDENTIFIER = auto()  # variable names, function names

    # ─────────────────────────────────────────────────────────────
    # Keywords
    # ─────────────────────────────────────────────────────────────
    FLOW = auto()  # flow
    INTERRUPT = auto()  # interrupt
    PRIORITY = auto()  # priority
    WHEN = auto()  # when
    IMAGE = auto()  # image
    CONST = auto()  # const
    LET = auto()  # let
    IF = auto()  # if
    ELIF = auto()  # elif
    ELSE = auto()  # else
    WHILE = auto()  # while
    FOR = auto()  # for
    IN = auto()  # in
    RANGE = auto()  # range
    LABEL = auto()  # label
    GOTO = auto()  # goto
    TRY = auto()  # try
    CATCH = auto()  # catch
    BREAK = auto()  # break
    CONTINUE = auto()  # continue
    RETURN = auto()  # return
    HOTKEYS = auto()  # hotkeys

    # ─────────────────────────────────────────────────────────────
    # Operators
    # ─────────────────────────────────────────────────────────────
    PLUS = auto()  # +
    MINUS = auto()  # -
    STAR = auto()  # *
    SLASH = auto()  # /
    PERCENT = auto()  # %
    EQ = auto()  # ==
    NEQ = auto()  # !=
    LT = auto()  # <
    GT = auto()  # >
    LTE = auto()  # <=
    GTE = auto()  # >=
    AND = auto()  # &&
    OR = auto()  # ||
    NOT = auto()  # !
    ASSIGN = auto()  # =

    # ─────────────────────────────────────────────────────────────
    # Delimiters
    # ─────────────────────────────────────────────────────────────
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    LBRACE = auto()  # {
    RBRACE = auto()  # }
    LBRACKET = auto()  # [
    RBRACKET = auto()  # ]
    SEMICOLON = auto()  # ;
    COLON = auto()  # :
    COMMA = auto()  # ,
    DOT = auto()  # .
    ARROW = auto()  # ->

    # ─────────────────────────────────────────────────────────────
    # Comments (preserved for formatter)
    # ─────────────────────────────────────────────────────────────
    LINE_COMMENT = auto()  # // ...
    BLOCK_COMMENT = auto()  # /* ... */

    # ─────────────────────────────────────────────────────────────
    # Special
    # ─────────────────────────────────────────────────────────────
    NEWLINE = auto()  # \n (for error reporting)
    EOF = auto()  # End of file
    ERROR = auto()  # Lexer error token


# Keyword mapping
KEYWORDS: dict[str, TokenType] = {
    "flow": TokenType.FLOW,
    "interrupt": TokenType.INTERRUPT,
    "priority": TokenType.PRIORITY,
    "when": TokenType.WHEN,
    "image": TokenType.IMAGE,
    "const": TokenType.CONST,
    "let": TokenType.LET,
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "label": TokenType.LABEL,
    "goto": TokenType.GOTO,
    "try": TokenType.TRY,
    "catch": TokenType.CATCH,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "return": TokenType.RETURN,
    "hotkeys": TokenType.HOTKEYS,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
}


class Token:
    """A single token from the lexer."""

    __slots__ = ("type", "value", "line", "column", "end_line", "end_column")

    def __init__(
        self,
        token_type: TokenType,
        value: str,
        line: int,
        column: int,
        end_line: int | None = None,
        end_column: int | None = None,
    ) -> None:
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column
        self.end_line = end_line if end_line is not None else line
        self.end_column = end_column if end_column is not None else column + len(value)

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Token):
            return False
        return self.type == other.type and self.value == other.value

    @property
    def span(self) -> tuple[int, int, int, int]:
        """Return (start_line, start_col, end_line, end_col)."""
        return (self.line, self.column, self.end_line, self.end_column)
