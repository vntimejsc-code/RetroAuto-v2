"""
Tests for DSL Lexer.
"""

import pytest

from core.dsl.lexer import Lexer
from core.dsl.tokens import TokenType


class TestLexerBasics:
    """Test basic lexer functionality."""

    def test_empty_source(self) -> None:
        """Empty source produces only EOF."""
        lexer = Lexer("")
        tokens = lexer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_whitespace_only(self) -> None:
        """Whitespace only produces EOF."""
        lexer = Lexer("   \t\n\n  ")
        tokens = lexer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF


class TestLexerKeywords:
    """Test keyword tokenization."""

    def test_all_keywords(self) -> None:
        """All keywords are recognized."""
        source = "flow if elif else while for in label goto break continue return"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        expected = [
            TokenType.FLOW,
            TokenType.IF,
            TokenType.ELIF,
            TokenType.ELSE,
            TokenType.WHILE,
            TokenType.FOR,
            TokenType.IN,
            TokenType.LABEL,
            TokenType.GOTO,
            TokenType.BREAK,
            TokenType.CONTINUE,
            TokenType.RETURN,
            TokenType.EOF,
        ]
        assert [t.type for t in tokens] == expected

    def test_case_insensitive_keywords(self) -> None:
        """Keywords are case-insensitive."""
        lexer = Lexer("FLOW Flow flow")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.FLOW
        assert tokens[1].type == TokenType.FLOW
        assert tokens[2].type == TokenType.FLOW


class TestLexerLiterals:
    """Test literal tokenization."""

    def test_integers(self) -> None:
        """Integer literals."""
        lexer = Lexer("0 42 12345")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.INTEGER
        assert tokens[0].value == "0"
        assert tokens[1].value == "42"
        assert tokens[2].value == "12345"

    def test_floats(self) -> None:
        """Float literals."""
        lexer = Lexer("1.0 3.14159 0.5")
        tokens = lexer.tokenize()
        assert all(t.type == TokenType.FLOAT for t in tokens[:-1])
        assert tokens[0].value == "1.0"
        assert tokens[1].value == "3.14159"

    def test_durations(self) -> None:
        """Duration literals."""
        lexer = Lexer("100ms 5s 2m 1h")
        tokens = lexer.tokenize()
        assert all(t.type == TokenType.DURATION for t in tokens[:-1])
        assert tokens[0].value == "100ms"
        assert tokens[1].value == "5s"
        assert tokens[2].value == "2m"
        assert tokens[3].value == "1h"

    def test_booleans(self) -> None:
        """Boolean literals."""
        lexer = Lexer("true false")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.TRUE
        assert tokens[1].type == TokenType.FALSE

    def test_null(self) -> None:
        """Null literal."""
        lexer = Lexer("null")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NULL

    def test_double_quoted_string(self) -> None:
        """Double-quoted string."""
        lexer = Lexer('"hello world"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello world"

    def test_single_quoted_string(self) -> None:
        """Single-quoted string."""
        lexer = Lexer("'hello'")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello"

    def test_string_escape_sequences(self) -> None:
        """String escape sequences."""
        lexer = Lexer(r'"hello\nworld\ttab"')
        tokens = lexer.tokenize()
        assert tokens[0].value == "hello\nworld\ttab"


class TestLexerOperators:
    """Test operator tokenization."""

    def test_arithmetic_operators(self) -> None:
        """Arithmetic operators."""
        lexer = Lexer("+ - * / %")
        tokens = lexer.tokenize()
        expected = [
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.STAR,
            TokenType.SLASH,
            TokenType.PERCENT,
            TokenType.EOF,
        ]
        assert [t.type for t in tokens] == expected

    def test_comparison_operators(self) -> None:
        """Comparison operators."""
        lexer = Lexer("== != < > <= >=")
        tokens = lexer.tokenize()
        expected = [
            TokenType.EQ,
            TokenType.NEQ,
            TokenType.LT,
            TokenType.GT,
            TokenType.LTE,
            TokenType.GTE,
            TokenType.EOF,
        ]
        assert [t.type for t in tokens] == expected

    def test_logical_operators(self) -> None:
        """Logical operators."""
        lexer = Lexer("&& || !")
        tokens = lexer.tokenize()
        expected = [TokenType.AND, TokenType.OR, TokenType.NOT, TokenType.EOF]
        assert [t.type for t in tokens] == expected


class TestLexerDelimiters:
    """Test delimiter tokenization."""

    def test_all_delimiters(self) -> None:
        """All delimiters."""
        lexer = Lexer("( ) { } [ ] ; : , . ->")
        tokens = lexer.tokenize()
        expected = [
            TokenType.LPAREN,
            TokenType.RPAREN,
            TokenType.LBRACE,
            TokenType.RBRACE,
            TokenType.LBRACKET,
            TokenType.RBRACKET,
            TokenType.SEMICOLON,
            TokenType.COLON,
            TokenType.COMMA,
            TokenType.DOT,
            TokenType.ARROW,
            TokenType.EOF,
        ]
        assert [t.type for t in tokens] == expected


class TestLexerComments:
    """Test comment tokenization."""

    def test_line_comment(self) -> None:
        """Line comment."""
        lexer = Lexer("flow main // this is a comment\n{}")
        tokens = lexer.tokenize()
        assert TokenType.LINE_COMMENT in [t.type for t in tokens]
        assert any("this is a comment" in t.value for t in tokens)

    def test_block_comment(self) -> None:
        """Block comment."""
        lexer = Lexer("flow /* comment */ main {}")
        tokens = lexer.tokenize()
        assert TokenType.BLOCK_COMMENT in [t.type for t in tokens]

    def test_multiline_block_comment(self) -> None:
        """Multiline block comment."""
        source = """flow main {
            /* this is a
               multiline comment */
        }"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert any(t.type == TokenType.BLOCK_COMMENT for t in tokens)


class TestLexerPositions:
    """Test token position tracking."""

    def test_line_numbers(self) -> None:
        """Token line numbers."""
        source = "flow\nmain\n{"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert tokens[0].line == 1
        assert tokens[1].line == 2
        assert tokens[2].line == 3

    def test_column_numbers(self) -> None:
        """Token column numbers."""
        source = "flow main"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert tokens[0].column == 1
        assert tokens[1].column == 6


class TestLexerErrors:
    """Test lexer error handling."""

    def test_unterminated_string(self) -> None:
        """Unterminated string produces error."""
        lexer = Lexer('"unterminated')
        tokens = lexer.tokenize()
        assert len(lexer.errors) > 0
        assert any(t.type == TokenType.ERROR for t in tokens)

    def test_unknown_character(self) -> None:
        """Unknown character produces error."""
        lexer = Lexer("@#$")
        tokens = lexer.tokenize()
        assert len(lexer.errors) > 0


class TestLexerRealCode:
    """Test lexer with real DSL code."""

    def test_simple_flow(self) -> None:
        """Simple flow definition."""
        source = """
        flow main {
            wait_image("button", timeout=5s);
            click(100, 200);
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert len(lexer.errors) == 0

        # Check key tokens
        types = [t.type for t in tokens]
        assert TokenType.FLOW in types
        assert TokenType.LBRACE in types
        assert TokenType.RBRACE in types
        assert TokenType.STRING in types
        assert TokenType.DURATION in types

    def test_complete_script(self) -> None:
        """Complete script with hotkeys, flow, and interrupt."""
        source = """
        hotkeys {
            start = "F5"
            stop = "F6"
        }

        flow main {
            label start:
            wait_image("ready");
            click(100, 200);
            sleep(500ms);
            goto start;
        }

        interrupt {
            priority 10
            when image "error"
            {
                click(50, 50);
            }
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert len(lexer.errors) == 0
