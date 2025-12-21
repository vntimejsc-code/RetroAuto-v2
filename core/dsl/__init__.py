"""
RetroAuto v2 - DSL Package

Custom Domain Specific Language for automation scripts.
Supports:
- Lexer: Tokenization with comments, strings, durations
- Parser: Recursive descent with error recovery
- AST: Node classes with span tracking
- Formatter: Pretty printing with K&R style
- Semantic: Validation with quick-fix hints
"""

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
    Span,
    TryStmt,
    UnaryExpr,
    WhileStmt,
)
from core.dsl.diagnostics import Diagnostic, QuickFix, Severity
from core.dsl.formatter import Formatter, format_code
from core.dsl.lexer import Lexer, LexerError
from core.dsl.parser import ParseError, Parser
from core.dsl.semantic import SemanticAnalyzer, analyze
from core.dsl.tokens import KEYWORDS, Token, TokenType

__all__ = [
    # Tokens
    "Token",
    "TokenType",
    "KEYWORDS",
    # Lexer
    "Lexer",
    "LexerError",
    # Parser
    "Parser",
    "ParseError",
    # AST
    "ASTNode",
    "Span",
    "Program",
    "FlowDecl",
    "InterruptDecl",
    "HotkeysDecl",
    "LabelStmt",
    "GotoStmt",
    "IfStmt",
    "WhileStmt",
    "ForStmt",
    "TryStmt",
    "CallExpr",
    "Literal",
    "Identifier",
    "BinaryExpr",
    "UnaryExpr",
    "ArrayExpr",
    "BlockStmt",
    "ExprStmt",
    "LetStmt",
    "ConstStmt",
    "AssignStmt",
    "ReturnStmt",
    "BreakStmt",
    "ContinueStmt",
    # Formatter
    "Formatter",
    "format_code",
    # Semantic
    "SemanticAnalyzer",
    "analyze",
    # Diagnostics
    "Diagnostic",
    "Severity",
    "QuickFix",
]
