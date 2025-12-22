"""
Tests for core/dsl/debugger.py - Debugger and BreakpointManager
"""

from core.dsl.debugger import (
    Breakpoint,
    BreakpointManager,
    Debugger,
    DebugState,
    StackFrame,
    StepMode,
    Variable,
)


class TestBreakpointDataclass:
    """Tests for Breakpoint dataclass."""

    def test_breakpoint_creation(self):
        bp = Breakpoint(id=1, file="test.dsl", line=10)
        assert bp.id == 1
        assert bp.file == "test.dsl"
        assert bp.line == 10
        assert bp.enabled is True

    def test_breakpoint_disabled(self):
        bp = Breakpoint(id=1, file="test.dsl", line=5, enabled=False)
        assert bp.enabled is False

    def test_breakpoint_with_condition(self):
        bp = Breakpoint(id=1, file="test.dsl", line=10, condition="x > 5")
        assert bp.condition == "x > 5"

    def test_breakpoint_hit_count(self):
        bp = Breakpoint(id=1, file="test.dsl", line=10, hit_count=5)
        assert bp.hit_count == 5


class TestStackFrame:
    """Tests for StackFrame dataclass."""

    def test_stack_frame_creation(self):
        frame = StackFrame(id=1, name="main", file="test.dsl", line=15)
        assert frame.id == 1
        assert frame.name == "main"
        assert frame.file == "test.dsl"
        assert frame.line == 15

    def test_stack_frame_with_locals(self):
        frame = StackFrame(id=1, name="main", file="test.dsl", line=15, locals={"x": 10, "y": 20})
        assert frame.locals["x"] == 10
        assert frame.locals["y"] == 20


class TestVariable:
    """Tests for Variable dataclass."""

    def test_variable_creation(self):
        var = Variable(name="counter", value=10, type="int")
        assert var.name == "counter"
        assert var.value == 10
        assert var.type == "int"

    def test_variable_expandable(self):
        var = Variable(name="obj", value={}, type="dict", expandable=True)
        assert var.expandable is True


class TestDebugState:
    """Tests for DebugState enum."""

    def test_debug_states_exist(self):
        assert DebugState.IDLE is not None
        assert DebugState.RUNNING is not None
        assert DebugState.PAUSED is not None
        assert DebugState.STEPPING is not None


class TestStepMode:
    """Tests for StepMode enum."""

    def test_step_modes_exist(self):
        assert StepMode.OVER is not None
        assert StepMode.INTO is not None
        assert StepMode.OUT is not None


class TestBreakpointManager:
    """Tests for BreakpointManager."""

    def test_manager_creation(self):
        manager = BreakpointManager()
        assert manager is not None

    def test_add_breakpoint(self):
        manager = BreakpointManager()
        bp = manager.add("test.dsl", 10)
        assert bp is not None
        assert bp.line == 10

    def test_remove_breakpoint(self):
        manager = BreakpointManager()
        bp = manager.add("test.dsl", 10)
        manager.remove(bp.id)
        assert manager.get(bp.id) is None

    def test_toggle_breakpoint(self):
        manager = BreakpointManager()
        bp = manager.add("test.dsl", 10)
        assert bp.enabled is True
        manager.toggle(bp.id)
        # After toggle, should be disabled
        bp2 = manager.get(bp.id)
        assert bp2 is not None and bp2.enabled is False

    def test_get_all(self):
        manager = BreakpointManager()
        manager.add("test.dsl", 10)
        manager.add("test.dsl", 20)
        all_bps = manager.get_all()
        assert len(all_bps) == 2

    def test_clear(self):
        manager = BreakpointManager()
        manager.add("test.dsl", 10)
        manager.add("test.dsl", 20)
        manager.clear()
        assert len(manager.get_all()) == 0

    def test_has_breakpoint(self):
        manager = BreakpointManager()
        manager.add("test.dsl", 10)
        assert manager.has_breakpoint("test.dsl", 10) is True
        assert manager.has_breakpoint("test.dsl", 20) is False

    def test_get_at(self):
        manager = BreakpointManager()
        manager.add("test.dsl", 10)
        bp = manager.get_at("test.dsl", 10)
        assert bp is not None
        assert bp.line == 10


class TestDebugger:
    """Tests for Debugger."""

    def test_debugger_creation(self):
        debugger = Debugger()
        assert debugger is not None
        assert debugger.state == DebugState.IDLE

    def test_debugger_breakpoints_access(self):
        debugger = Debugger()
        assert debugger.breakpoints is not None

    def test_debugger_start(self):
        debugger = Debugger()
        debugger.start()
        assert debugger.state == DebugState.RUNNING

    def test_debugger_stop(self):
        debugger = Debugger()
        debugger.start()
        debugger.stop()
        assert debugger.state == DebugState.IDLE

    def test_debugger_pause(self):
        debugger = Debugger()
        debugger.start()
        debugger.pause()
        assert debugger.state == DebugState.PAUSED

    def test_debugger_continue(self):
        debugger = Debugger()
        debugger.start()
        debugger.pause()
        debugger.continue_execution()
        assert debugger.state == DebugState.RUNNING

    def test_debugger_step_over(self):
        debugger = Debugger()
        debugger.start()
        debugger.pause()
        debugger.step_over()
        assert debugger.state == DebugState.STEPPING

    def test_debugger_step_into(self):
        debugger = Debugger()
        debugger.start()
        debugger.pause()
        debugger.step_into()
        assert debugger.state == DebugState.STEPPING

    def test_debugger_step_out(self):
        debugger = Debugger()
        debugger.start()
        debugger.pause()
        debugger.step_out()
        assert debugger.state == DebugState.STEPPING

    def test_debugger_is_paused(self):
        debugger = Debugger()
        assert debugger.is_paused is False
        debugger.start()
        debugger.pause()
        assert debugger.is_paused is True

    def test_debugger_call_stack(self):
        debugger = Debugger()
        stack = debugger.call_stack
        assert isinstance(stack, list)

    def test_debugger_callbacks(self):
        debugger = Debugger()
        called = []

        debugger.on_paused(lambda f, line_num: called.append("paused"))
        debugger.on_resumed(lambda: called.append("resumed"))
        debugger.on_stopped(lambda: called.append("stopped"))

        # Just verify no exceptions
        assert debugger is not None

    def test_debugger_get_variables(self):
        debugger = Debugger()
        vars = debugger.get_variables()
        assert isinstance(vars, list)

    def test_debugger_evaluate(self):
        debugger = Debugger()
        result = debugger.evaluate("1 + 1")
        # Returns tuple (value, error)
        assert isinstance(result, tuple)
