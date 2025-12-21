"""
Tests for DSL Parser.
"""


from core.dsl.ast import (
    BinaryExpr,
    CallExpr,
    ExprStmt,
    ForStmt,
    GotoStmt,
    IfStmt,
    LabelStmt,
    LetStmt,
    WhileStmt,
)
from core.dsl.parser import Parser


class TestParserBasics:
    """Test basic parser functionality."""

    def test_empty_source(self) -> None:
        """Empty source produces empty program."""
        parser = Parser("")
        program = parser.parse()
        assert len(program.flows) == 0
        assert len(program.interrupts) == 0
        assert len(parser.errors) == 0

    def test_simple_flow(self) -> None:
        """Simple flow declaration."""
        parser = Parser("flow main {}")
        program = parser.parse()
        assert len(program.flows) == 1
        assert program.flows[0].name == "main"
        assert len(parser.errors) == 0


class TestParserFlows:
    """Test flow parsing."""

    def test_flow_with_statements(self) -> None:
        """Flow with multiple statements."""
        source = """
        flow main {
            wait_image("btn");
            click(100, 200);
            sleep(500ms);
        }
        """
        parser = Parser(source)
        program = parser.parse()
        assert len(program.flows) == 1
        flow = program.flows[0]
        assert len(flow.body.statements) == 3

    def test_multiple_flows(self) -> None:
        """Multiple flow declarations."""
        source = """
        flow main {
            run_flow("helper");
        }
        flow helper {
            log("helping");
        }
        """
        parser = Parser(source)
        program = parser.parse()
        assert len(program.flows) == 2
        assert program.flows[0].name == "main"
        assert program.flows[1].name == "helper"


class TestParserStatements:
    """Test statement parsing."""

    def test_label_goto(self) -> None:
        """Label and goto statements."""
        source = """
        flow main {
            label start:
            sleep(1s);
            goto start;
        }
        """
        parser = Parser(source)
        program = parser.parse()
        flow = program.flows[0]
        assert isinstance(flow.body.statements[0], LabelStmt)
        assert flow.body.statements[0].name == "start"
        assert isinstance(flow.body.statements[2], GotoStmt)
        assert flow.body.statements[2].target == "start"

    def test_if_statement(self) -> None:
        """If statement."""
        source = """
        flow main {
            if image_exists("btn") {
                click(100, 200);
            }
        }
        """
        parser = Parser(source)
        program = parser.parse()
        flow = program.flows[0]
        assert isinstance(flow.body.statements[0], IfStmt)

    def test_if_elif_else(self) -> None:
        """If with elif and else."""
        source = """
        flow main {
            if x == 1 {
                log("one");
            } elif x == 2 {
                log("two");
            } else {
                log("other");
            }
        }
        """
        parser = Parser(source)
        program = parser.parse()
        if_stmt = program.flows[0].body.statements[0]
        assert isinstance(if_stmt, IfStmt)
        assert len(if_stmt.elif_branches) == 1
        assert if_stmt.else_branch is not None

    def test_while_loop(self) -> None:
        """While loop."""
        source = """
        flow main {
            while running {
                sleep(100ms);
            }
        }
        """
        parser = Parser(source)
        program = parser.parse()
        stmt = program.flows[0].body.statements[0]
        assert isinstance(stmt, WhileStmt)

    def test_for_loop(self) -> None:
        """For loop."""
        source = """
        flow main {
            for i in range(10) {
                log(i);
            }
        }
        """
        parser = Parser(source)
        program = parser.parse()
        stmt = program.flows[0].body.statements[0]
        assert isinstance(stmt, ForStmt)
        assert stmt.variable == "i"

    def test_let_statement(self) -> None:
        """Let variable declaration."""
        source = """
        flow main {
            let x = 5;
            let y;
        }
        """
        parser = Parser(source)
        program = parser.parse()
        stmt1 = program.flows[0].body.statements[0]
        stmt2 = program.flows[0].body.statements[1]
        assert isinstance(stmt1, LetStmt)
        assert stmt1.name == "x"
        assert stmt1.initializer is not None
        assert isinstance(stmt2, LetStmt)
        assert stmt2.initializer is None


class TestParserExpressions:
    """Test expression parsing."""

    def test_function_call(self) -> None:
        """Function call with args and kwargs."""
        source = """
        flow main {
            wait_image("btn", timeout=5s, appear=true);
        }
        """
        parser = Parser(source)
        program = parser.parse()
        stmt = program.flows[0].body.statements[0]
        assert isinstance(stmt, ExprStmt)
        call = stmt.expr
        assert isinstance(call, CallExpr)
        assert call.callee == "wait_image"
        assert len(call.args) == 1
        assert "timeout" in call.kwargs
        assert "appear" in call.kwargs

    def test_binary_expressions(self) -> None:
        """Binary expressions."""
        source = """
        flow main {
            let x = 1 + 2 * 3;
            let y = a == b && c != d;
        }
        """
        parser = Parser(source)
        program = parser.parse()
        assert len(parser.errors) == 0

        stmt1 = program.flows[0].body.statements[0]
        assert isinstance(stmt1, LetStmt)
        assert isinstance(stmt1.initializer, BinaryExpr)

    def test_comparison_operators(self) -> None:
        """Comparison operators."""
        source = """
        flow main {
            if x < 10 && y >= 5 {
                log("ok");
            }
        }
        """
        parser = Parser(source)
        program = parser.parse()
        assert len(parser.errors) == 0

    def test_array_literal(self) -> None:
        """Array literal."""
        source = """
        flow main {
            wait_any(["btn1", "btn2", "btn3"]);
        }
        """
        parser = Parser(source)
        program = parser.parse()
        assert len(parser.errors) == 0


class TestParserHotkeys:
    """Test hotkeys parsing."""

    def test_hotkeys_block(self) -> None:
        """Hotkeys block."""
        source = """
        hotkeys {
            start = "F5"
            stop = "F6"
            pause = "F7"
        }
        """
        parser = Parser(source)
        program = parser.parse()
        assert program.hotkeys is not None
        assert program.hotkeys.bindings["start"] == "F5"
        assert program.hotkeys.bindings["stop"] == "F6"


class TestParserInterrupts:
    """Test interrupt parsing."""

    def test_interrupt_block(self) -> None:
        """Interrupt declaration."""
        source = """
        interrupt {
            priority 10
            when image "error_popup"
            {
                click(50, 50);
            }
        }
        """
        parser = Parser(source)
        program = parser.parse()
        assert len(program.interrupts) == 1
        interrupt = program.interrupts[0]
        assert interrupt.priority == 10
        assert interrupt.when_asset == "error_popup"


class TestParserErrorRecovery:
    """Test parser error recovery."""

    def test_missing_semicolon(self) -> None:
        """Missing semicolon continues parsing."""
        source = """
        flow main {
            log("first")
            log("second");
        }
        """
        parser = Parser(source)
        program = parser.parse()
        # Should still parse both statements
        assert len(program.flows) == 1

    def test_invalid_token_recovery(self) -> None:
        """Invalid token allows recovery."""
        source = """
        flow main {
            @@invalid@@
            log("recovered");
        }
        """
        parser = Parser(source)
        program = parser.parse()
        # Parser should recover after error
        assert len(program.flows) == 1

    def test_unclosed_brace(self) -> None:
        """Unclosed brace produces error."""
        source = """
        flow main {
            log("test");
        """
        parser = Parser(source)
        program = parser.parse()
        assert len(parser.errors) > 0


class TestParserSpans:
    """Test span tracking."""

    def test_flow_span(self) -> None:
        """Flow has correct span."""
        source = "flow main {}"
        parser = Parser(source)
        program = parser.parse()
        flow = program.flows[0]
        assert flow.span.start_line == 1
        assert flow.span.start_col == 1

    def test_statement_span(self) -> None:
        """Statement has correct span."""
        source = """
flow main {
    log("test");
}"""
        parser = Parser(source)
        program = parser.parse()
        stmt = program.flows[0].body.statements[0]
        assert stmt.span.start_line == 3


class TestParserCompleteScript:
    """Test complete script parsing."""

    def test_full_script(self) -> None:
        """Complete script with all features."""
        source = """
        hotkeys {
            start = "F5"
            stop = "F6"
        }

        const MAX_RETRIES = 5;

        flow main {
            let retries = 0;

            label start:

            if image_exists("ready") {
                click(100, 200);
            } else {
                sleep(1s);
                retries = retries + 1;

                if retries < MAX_RETRIES {
                    goto start;
                }
            }

            run_flow("cleanup");
        }

        flow cleanup {
            log("cleaning up", level="info");
        }

        interrupt {
            priority 10
            when image "error"
            {
                click(50, 50);
            }
        }
        """
        parser = Parser(source)
        program = parser.parse()

        assert len(parser.errors) == 0
        assert program.hotkeys is not None
        assert len(program.constants) == 1
        assert len(program.flows) == 2
        assert len(program.interrupts) == 1
