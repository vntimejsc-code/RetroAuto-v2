"""
RetroAuto v2 - Core Runner

Execute flows with Label/Goto support and action dispatch.
"""

import time
from collections.abc import Callable

from core.engine.context import EngineState, ExecutionContext
from core.models import (
    Action,
    Click,
    Delay,
    Flow,
    Goto,
    Hotkey,
    IfImage,
    Label,
    RunFlow,
    TypeText,
    WaitImage,
)
from infra import get_logger
from vision import WaitResult

logger = get_logger("Runner")


class Runner:
    """
    Execute automation flows.

    Features:
    - Single-step and full-flow execution
    - Label/Goto flow control
    - IfImage conditional branching
    - Nested flow calls (RunFlow)
    - Stop/Pause support
    """

    def __init__(
        self,
        ctx: ExecutionContext,
        on_step: Callable[[str, int, Action], None] | None = None,
        on_complete: Callable[[str, bool], None] | None = None,
    ) -> None:
        """
        Initialize runner.

        Args:
            ctx: Execution context with all services
            on_step: Callback when step starts (flow, index, action)
            on_complete: Callback when flow completes (flow, success)
        """
        self._ctx = ctx
        self._on_step = on_step
        self._on_complete = on_complete
        self._call_stack: list[tuple[str, int]] = []  # For nested RunFlow

    def run_flow(self, flow_name: str, from_step: int = 0) -> bool:
        """
        Execute a flow.

        Args:
            flow_name: Name of flow to execute
            from_step: Start from this step index

        Returns:
            True if completed successfully, False if stopped/error
        """
        flow = self._ctx.script.get_flow(flow_name)
        if flow is None:
            logger.error("Flow not found: %s", flow_name)
            return False

        self._ctx.set_state(EngineState.RUNNING)
        logger.info("Starting flow: %s (from step %d)", flow_name, from_step)

        # Build label index for fast Goto
        labels = self._build_label_index(flow)

        pc = from_step  # Program counter
        success = True

        try:
            while pc < len(flow.actions):
                # Check stop/pause
                if not self._ctx.wait_if_paused():
                    logger.info("Flow stopped by user")
                    success = False
                    break

                action = flow.actions[pc]
                self._ctx.update_step(flow_name, pc)

                # Callback
                if self._on_step:
                    self._on_step(flow_name, pc, action)

                # Execute action
                start_time = time.perf_counter()
                result = self._execute_action(action, flow, labels)
                elapsed = int((time.perf_counter() - start_time) * 1000)

                logger.debug("Step %d completed in %dms", pc, elapsed)

                # Handle Goto
                if isinstance(result, int):
                    pc = result
                elif result is False:
                    success = False
                    break
                else:
                    pc += 1

        except Exception as e:
            logger.exception("Error in flow %s step %d: %s", flow_name, pc, e)
            success = False

        # Callback
        if self._on_complete:
            self._on_complete(flow_name, success)

        if success:
            self._ctx.set_state(EngineState.IDLE)
        return success

    def run_step(self, flow_name: str, step_index: int) -> bool:
        """Execute single step."""
        flow = self._ctx.script.get_flow(flow_name)
        if flow is None or step_index >= len(flow.actions):
            return False

        action = flow.actions[step_index]
        labels = self._build_label_index(flow)

        try:
            result = self._execute_action(action, flow, labels)
            return result is not False
        except Exception as e:
            logger.exception("Error executing step: %s", e)
            return False

    def _build_label_index(self, flow: Flow) -> dict[str, int]:
        """Build index of label names to step indices."""
        labels = {}
        for i, action in enumerate(flow.actions):
            if isinstance(action, Label):
                labels[action.name] = i
        return labels

    def _execute_action(
        self,
        action: Action,
        flow: Flow,
        labels: dict[str, int],
    ) -> bool | int | None:
        """
        Execute single action.

        Returns:
            - None: Continue to next step
            - int: Jump to this step index (Goto)
            - False: Stop execution
        """
        if isinstance(action, WaitImage):
            return self._exec_wait_image(action)

        elif isinstance(action, Click):
            return self._exec_click(action)

        elif isinstance(action, IfImage):
            return self._exec_if_image(action, flow, labels)

        elif isinstance(action, Hotkey):
            return self._exec_hotkey(action)

        elif isinstance(action, TypeText):
            return self._exec_type_text(action)

        elif isinstance(action, Label):
            # Labels are no-ops at runtime
            return None

        elif isinstance(action, Goto):
            return self._exec_goto(action, labels)

        elif isinstance(action, RunFlow):
            return self._exec_run_flow(action)

        elif isinstance(action, Delay):
            return self._exec_delay(action)

        else:
            logger.warning("Unknown action type: %s", type(action).__name__)
            return None

    # ─────────────────────────────────────────────────────────────
    # Action Executors
    # ─────────────────────────────────────────────────────────────

    def _exec_wait_image(self, action: WaitImage) -> bool | None:
        """Execute WaitImage action."""
        logger.info(
            "WaitImage: %s (appear=%s, timeout=%dms)",
            action.asset_id,
            action.appear,
            action.timeout_ms,
        )

        if action.appear:
            outcome = self._ctx.waiter.wait_appear(
                action.asset_id,
                timeout_ms=action.timeout_ms,
                poll_ms=action.poll_ms,
                roi_override=action.roi_override,
            )
        else:
            outcome = self._ctx.waiter.wait_vanish(
                action.asset_id,
                timeout_ms=action.timeout_ms,
                poll_ms=action.poll_ms,
                roi_override=action.roi_override,
            )

        if outcome.result == WaitResult.SUCCESS:
            if outcome.match:
                self._ctx.last_match = outcome.match
            return None
        elif outcome.result == WaitResult.TIMEOUT:
            logger.warning("WaitImage timeout: %s", action.asset_id)
            return False
        else:
            return False  # Cancelled

    def _exec_click(self, action: Click) -> None:
        """Execute Click action."""
        if action.use_match and self._ctx.last_match:
            x, y = self._ctx.last_match.center
        elif action.x is not None and action.y is not None:
            x, y = action.x, action.y
        else:
            logger.warning("Click: No coordinates and no match")
            return None

        logger.info("Click: (%d, %d) button=%s clicks=%d", x, y, action.button, action.clicks)
        self._ctx.mouse.click(x, y, action.button, action.clicks, action.interval_ms)
        return None

    def _exec_if_image(
        self,
        action: IfImage,
        flow: Flow,
        labels: dict[str, int],
    ) -> bool | int | None:
        """Execute IfImage conditional."""
        match = self._ctx.matcher.find(action.asset_id, action.roi_override)

        if match:
            logger.info("IfImage: %s FOUND (conf=%.2f)", action.asset_id, match.confidence)
            self._ctx.last_match = match
            branch = action.then_actions
        else:
            logger.info("IfImage: %s NOT FOUND", action.asset_id)
            branch = action.else_actions

        # Execute branch actions inline
        for sub_action in branch:
            if not self._ctx.wait_if_paused():
                return False
            result = self._execute_action(sub_action, flow, labels)
            if result is False:
                return False
            if isinstance(result, int):
                return result  # Propagate Goto

        return None

    def _exec_hotkey(self, action: Hotkey) -> None:
        """Execute Hotkey action."""
        logger.info("Hotkey: %s", "+".join(action.keys))
        self._ctx.keyboard.hotkey(action.keys)
        return None

    def _exec_type_text(self, action: TypeText) -> None:
        """Execute TypeText action."""
        logger.info(
            "TypeText: '%s...' (paste=%s)",
            action.text[:20] if len(action.text) > 20 else action.text,
            action.paste_mode,
        )
        self._ctx.keyboard.type_text(action.text, action.paste_mode, action.enter)
        return None

    def _exec_goto(self, action: Goto, labels: dict[str, int]) -> int | None:
        """Execute Goto action."""
        if action.label not in labels:
            logger.error("Goto: Label not found: %s", action.label)
            return None

        target = labels[action.label]
        logger.info("Goto: %s (step %d)", action.label, target)
        return target

    def _exec_run_flow(self, action: RunFlow) -> bool | None:
        """Execute RunFlow action (nested flow call)."""
        logger.info("RunFlow: %s", action.flow_name)

        # Check recursion limit
        if len(self._call_stack) > 10:
            logger.error("RunFlow: Maximum recursion depth exceeded")
            return False

        # Push current position
        self._call_stack.append((self._ctx.current_flow, self._ctx.current_step))

        # Execute nested flow
        success = self.run_flow(action.flow_name)

        # Pop call stack
        if self._call_stack:
            self._call_stack.pop()

        return None if success else False

    def _exec_delay(self, action: Delay) -> None:
        """Execute Delay action."""
        logger.info("Delay: %dms", action.ms)

        # Sleep in small chunks to allow stop/pause
        remaining = action.ms
        chunk = 100  # 100ms chunks

        while remaining > 0:
            if not self._ctx.wait_if_paused():
                return None
            sleep_time = min(chunk, remaining)
            time.sleep(sleep_time / 1000.0)
            remaining -= sleep_time

        return None
