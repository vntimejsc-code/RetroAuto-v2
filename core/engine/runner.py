"""
RetroAuto v2 - Core Runner

Execute flows with Label/Goto support and action dispatch.
"""

import time
from collections.abc import Callable
from typing import Any

from core.engine.context import EngineState, ExecutionContext
from core.graph.walker import GraphWalker
from core.models import (
    Action,
    Click,
    ClickImage,
    ClickRandom,
    ClickUntil,
    Delay,
    DelayRandom,
    Drag,
    Flow,
    Goto,
    Hotkey,
    IfImage,
    IfNotImage,
    IfPixel,
    IfText,
    Label,
    Loop,
    Notify,
    NotifyMethod,
    ReadText,
    RunFlow,
    Scroll,
    TypeText,
    WaitImage,
    WaitPixel,
    WhileImage,
)
from core.vision.hasher import calculate_phash, hamming_distance
from infra import get_logger
from vision import WaitResult
from vision.ocr import TextReader

logger = get_logger("Runner")


from core.watchdog import SystemWatchdog


class Runner:
    """
    Execute automation flows.

    Features:
    - Single-step and full-flow execution
    - Label/Goto flow control
    - IfImage conditional branching
    - Nested flow calls (RunFlow)
    - Stop/Pause support
    - System Watchdog monitoring
    """

    def __init__(
        self,
        ctx: ExecutionContext,
        on_step: Callable[[str, int, Action], None] | None = None,
        on_complete: Callable[[str, bool], None] | None = None,
        on_notify: Callable[[str, str], None] | None = None,
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
        self._on_notify = on_notify
        self._call_stack: list[tuple[str, int]] = []  # For nested RunFlow
        self._ocr = TextReader()
        self._watchdog = SystemWatchdog()

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

        # 🛡️ Pre-flight validation
        validation_errors = self._validate_assets_before_run(flow)
        if validation_errors:
            for error in validation_errors:
                logger.error(f"❌ Pre-flight check failed: {error}")
            # Continue anyway but warn user
            logger.warning(f"⚠️ {len(validation_errors)} validation warnings, proceeding...")

        # Check OCR availability if needed
        if self._flow_needs_ocr(flow) and not self._ocr.is_available():
            logger.warning(
                "⚠️ OCR not available (Tesseract not found). ReadText/IfText actions may fail."
            )

        # Check if flow has a graph representation
        if flow.graph and flow.graph.nodes:
            logger.info("Executing flow using graph mode")
            return self._execute_graph(flow)

        # Legacy mode: execute as linear list
        logger.info("Executing flow using legacy list mode")
        labels = self._build_label_index(flow)
        return self._execute_list(flow, from_step, labels, flow_name)

    def _execute_graph(self, flow: Flow) -> bool:
        """Execute flow using graph walker."""
        try:
            walker = GraphWalker(flow.graph)

            # Create action executor callback that maintains context
            def execute_action(action: Action) -> Any:
                # Check stop/pause before each action
                if not self._ctx.wait_if_paused():
                    raise InterruptedError("Flow stopped by user")

                # Execute the action and return result
                return self._execute_action(action, flow, {})

            # Execute graph
            walker.execute_graph(execute_action)
            return True

        except InterruptedError:
            logger.info("Graph execution stopped by user")
            return False
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            return False

    def _execute_list(
        self, flow: Flow, from_step: int, labels: dict[str, int], flow_name: str = "main"
    ) -> bool:
        """Execute flow using traditional linear list walker (backward compat)."""
        # Build label index for fast Goto
        labels = self._build_label_index(flow)

        pc = from_step  # Program counter
        success = True

        try:
            while pc < len(flow.actions):
                # 1. System Watchdog Check (only if run_options available)
                run_options = getattr(self._ctx, "run_options", {})
                if run_options:
                    watchdog_cfg = run_options.get("watchdog", {})
                    is_healthy, msg = self._watchdog.check_health(watchdog_cfg)
                    if not is_healthy:
                        logger.error(f"🛑 Watchdog Stop: {msg}")
                        # Handle as error to stop script
                        raise RuntimeError(f"System Watchdog failed: {msg}")

                # 2. Check stop/pause
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

    def _validate_assets_before_run(self, flow: Flow) -> list[str]:
        """
        Validate all referenced assets exist before running.

        Returns:
            List of error messages (empty if all valid)
        """
        # Skip validation if context doesn't support get_asset (e.g., tests)
        if not hasattr(self._ctx, "get_asset"):
            return []

        errors = []
        checked = set()

        for action in flow.actions:
            # Check asset_id if action has one
            if hasattr(action, "asset_id") and action.asset_id:
                asset_id = action.asset_id
                if asset_id in checked:
                    continue
                checked.add(asset_id)

                # Try to get asset from context
                try:
                    asset = self._ctx.get_asset(asset_id)
                    if asset is None or getattr(asset, "image", None) is None:
                        errors.append(f"Asset '{asset_id}' not loaded or image is None")
                except Exception as e:
                    errors.append(f"Asset '{asset_id}' error: {e}")

        return errors

    def _flow_needs_ocr(self, flow: Flow) -> bool:
        """Check if flow uses any OCR actions."""
        return any(isinstance(action, (ReadText, IfText)) for action in flow.actions)

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
        if isinstance(action, (Click, ClickImage, ClickRandom, Drag)):
            hash_before = self._capture_hash()

            # Execute
            result = self._dispatch_action(action, flow, labels)

            # Flight Recorder: Check for change
            if hash_before is not None:
                # Wait for reaction (small delay)
                time.sleep(0.1)
                hash_after = self._capture_hash()
                if hash_after is not None:
                    dist = hamming_distance(hash_before, hash_after)
                    if dist <= 1:  # Allow exceedingly minor noise (0 or 1 bit)
                        logger.warning(
                            f"✈️ FlightRecorder: Action '{type(action).__name__}' resulted in NO VISUAL CHANGE (dist={dist}). Possible failure."
                        )
                    else:
                        logger.debug(f"FlightRecorder: Visual change confirmed (dist={dist})")

            return result
        else:
            return self._dispatch_action(action, flow, labels)

    def _dispatch_action(
        self, action: Action, flow: Flow, labels: dict[str, int]
    ) -> bool | int | None:
        """
        Internal dispatch with error handling wrapper.

        All action execution is wrapped for:
        - Execution time logging
        - Graceful error recovery
        - Detailed error context
        """
        action_type = type(action).__name__
        start_time = time.perf_counter()

        try:
            result = self._safe_execute(action, flow, labels)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(f"✅ {action_type} completed in {elapsed_ms}ms")
            return result

        except TimeoutError as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"⏱️ {action_type} TIMEOUT after {elapsed_ms}ms: {e}")
            return None  # Continue to next action

        except FileNotFoundError as e:
            logger.error(f"❌ {action_type} Asset not found: {e}")
            return None  # Continue to next action

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"❌ {action_type} FAILED after {elapsed_ms}ms: {e}")
            # Log full traceback at debug level
            logger.debug(f"Traceback for {action_type}:", exc_info=True)
            return None  # Continue to next action (don't crash flow)

    def _safe_execute(
        self, action: Action, flow: Flow, labels: dict[str, int]
    ) -> bool | int | None:
        """Execute action with specific handlers."""
        if isinstance(action, WaitImage):
            return self._exec_wait_image(action)

        elif isinstance(action, Click):
            return self._exec_click(action)

        elif isinstance(action, ClickRandom):
            return self._exec_click_random(action)

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

        elif isinstance(action, ReadText):
            return self._exec_read_text(action)

        elif isinstance(action, IfText):
            return self._exec_if_text(action, flow, labels)

        elif isinstance(action, ClickImage):
            return self._exec_click_image(action)

        elif isinstance(action, Drag):
            return self._exec_drag(action)

        elif isinstance(action, Notify):
            return self._exec_notify(action)

        elif isinstance(action, Scroll):
            return self._exec_scroll(action)

        elif isinstance(action, DelayRandom):
            return self._exec_delay_random(action)

        elif isinstance(action, Loop):
            return self._exec_loop(action, flow, labels)

        elif isinstance(action, WhileImage):
            return self._exec_while_image(action, flow, labels)

        elif isinstance(action, WaitPixel):
            return self._exec_wait_pixel(action)

        elif isinstance(action, IfPixel):
            return self._exec_if_pixel(action, flow, labels)

        elif isinstance(action, ClickUntil):
            return self._exec_click_until(action)

        elif isinstance(action, IfNotImage):
            return self._exec_if_not_image(action, flow, labels)

        else:
            logger.warning("Unknown action type: %s", type(action).__name__)
            return None

    def _capture_hash(self) -> int | None:
        """Capture screen and calculate hash for Flight Recorder."""
        try:
            # We need to grab screen.
            # self._ctx.capture (ScreenCapture) usually has grab() returning numpy/PIL
            img = self._ctx.capture.grab()
            return calculate_phash(img)
        except Exception as e:
            logger.warning(f"FlightRecorder capture failed: {e}")
            return None

    # ─────────────────────────────────────────────────────────────
    # Action Executors
    # ─────────────────────────────────────────────────────────────

    def _resolve_variables(self, text: str) -> str:
        """Replace $var with values from context."""
        if not text:
            return ""
        result = text
        for name, value in self._ctx.variables.items():
            if name in result:
                result = result.replace(name, str(value))
        return result

    def _exec_notify(self, action: Notify) -> None:
        """Execute Notify action."""
        msg = self._resolve_variables(action.message)
        title = self._resolve_variables(action.title)

        logger.info(f"Notify [{action.method}]: {title} - {msg}")

        if action.method == NotifyMethod.POPUP:
            if self._on_notify:
                self._on_notify(title, msg)

        elif action.method == NotifyMethod.TELEGRAM or action.method == NotifyMethod.DISCORD:
            target = self._resolve_variables(action.target)
            if not target:
                logger.warning("Notification target not specified")
                return

            try:
                import json
                import urllib.request

                if action.method == NotifyMethod.DISCORD:
                    data = json.dumps({"content": f"**{title}**\n{msg}"}).encode("utf-8")
                    req = urllib.request.Request(
                        target,
                        data=data,
                        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                    )
                    urllib.request.urlopen(req)

                elif action.method == NotifyMethod.TELEGRAM:
                    if "|" in target:
                        token, chat_id = target.split("|", 1)
                        import urllib.parse

                        encoded_msg = urllib.parse.quote(f"{title}\n{msg}")
                        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={encoded_msg}"
                        urllib.request.urlopen(url)
                    else:
                        logger.warning("Telegram target format: TOKEN|CHAT_ID")

            except Exception as e:
                logger.error(f"Notification failed: {e}")

    def _exec_read_text(self, action: ReadText) -> None:
        """Execute ReadText action."""
        try:
            # Capture screen (returns PIL Image usually, depends on Capture impl)
            # ctx.capture.grab() -> Image
            screenshot = self._ctx.capture.grab()

            text = self._ocr.read_from_image(
                screenshot,
                roi=action.roi,
                allowlist=action.allowlist,
                scale=action.scale,
                invert=action.invert,
                binarize=action.binarize,
            )

            # Store in variable
            self._ctx.variables[action.variable_name] = text
            logger.info("ReadText: %s = '%s' (ROI: %s)", action.variable_name, text, action.roi)

        except Exception as e:
            logger.error("ReadText failed: %s", e)

    def _exec_if_text(self, action: IfText, flow: Flow, labels: dict[str, int]) -> None:
        """Execute IfText conditional."""
        # Get variable value
        var_val = str(self._ctx.variables.get(action.variable_name, ""))
        target = action.value
        op = action.operator
        result = False

        try:
            if op == "contains":
                result = target in var_val
            elif op == "equals":
                result = var_val == target
            elif op == "starts_with":
                result = var_val.startswith(target)
            elif op == "ends_with":
                result = var_val.endswith(target)
            elif op == "numeric_gt" or op == "numeric_lt":
                # Clean up string for numeric conversion (remove non-digits if needed, or just try)
                # Simple float conversion
                f_val = float(var_val.replace(",", "").strip())
                f_target = float(target)
                result = f_val > f_target if op == "numeric_gt" else f_val < f_target
        except ValueError:
            logger.warning("IfText: Numeric conversion failed for '%s'", var_val)
            result = False

        logger.info("IfText: '%s' %s '%s' -> %s", var_val, op, target, result)

        branch = action.then_actions if result else action.else_actions

        # Execute branch
        for sub_action in branch:
            # Check stop/pause between sub-actions
            if not self._ctx.wait_if_paused():
                return None

            # Recursive execution? No, flat execution context needed for goto/labels usually
            # But action models support nesting. We can execute purely.
            # Note: Goto inside IfText won't work well unless we flatten the flow.
            # For now, we just execute simple actions.
            self._execute_action(sub_action, flow, labels)

    def _exec_click_image(self, action: ClickImage) -> None:
        """Execute ClickImage with wait."""
        result = self._ctx.wait_for_image(
            action.asset_id,
            timeout_ms=action.timeout_ms,
            appear=True,
            smart_wait=action.smart_wait,
        )
        if not result or not result.found:
            raise RuntimeError(f"Image not found: {action.asset_id}")

        # Click with offset
        x = result.location[0] + action.offset_x
        y = result.location[1] + action.offset_y

        logger.info(
            f"ClickImage '{action.asset_id}' at ({x},{y}) button={action.button} clicks={action.clicks}"
        )

        # Perform clicks
        for i in range(action.clicks):
            if i > 0:
                # Wait interval between clicks
                import time

                time.sleep(action.interval_ms / 1000.0)

            self._ctx.mouse.click(x, y, button=action.button)

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
                smart_wait=action.smart_wait,
            )
        else:
            outcome = self._ctx.waiter.wait_vanish(
                action.asset_id,
                timeout_ms=action.timeout_ms,
                poll_ms=action.poll_ms,
                roi_override=action.roi_override,
                smart_wait=action.smart_wait,
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
        """Execute click action."""
        if action.x is not None and action.y is not None:
            x, y = action.x, action.y
        else:
            # Use last match
            x, y = self._ctx.last_match_center()
            if x is None or y is None:
                logger.warning("Click: No coordinates and no match")
                return None

        logger.info(f"Clicking at ({x}, {y}) button={action.button} clicks={action.clicks}")

        # Perform clicks
        for i in range(action.clicks):
            if i > 0:
                # Wait interval between clicks
                import time

                time.sleep(action.interval_ms / 1000.0)

            self._ctx.mouse.click(x, y, button=action.button)
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

    def _exec_if_not_image(
        self,
        action: IfNotImage,
        flow: Flow,
        labels: dict[str, int],
    ) -> bool | int | None:
        """Execute IfNotImage conditional (runs when image NOT found)."""
        match = self._ctx.matcher.find(action.asset_id, action.roi_override)

        if match:
            logger.info("IfNotImage: %s FOUND - skipping actions", action.asset_id)
            return None  # Image found, skip then_actions

        logger.info("IfNotImage: %s NOT FOUND - executing actions", action.asset_id)

        # Execute then_actions since image is NOT found
        for sub_action in action.then_actions:
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

    def _exec_click_random(self, action: ClickRandom) -> None:
        """Execute ClickRandom action."""
        import random

        # Calculate random point within ROI
        # Use normal distribution (gaussian) for more human-like "center-bias"
        # but clamp to ROI bounds

        # Center of ROI
        cx = action.roi.x + action.roi.w / 2
        cy = action.roi.y + action.roi.h / 2

        # Standard deviation = 1/6 of width/height (99% points within ROI)
        sigma_x = action.roi.w / 6
        sigma_y = action.roi.h / 6

        # Box-Muller transform or simple gauss
        x = int(random.gauss(cx, sigma_x))
        y = int(random.gauss(cy, sigma_y))

        # Clamp to bounds
        x = max(action.roi.x, min(action.roi.x + action.roi.w, x))
        y = max(action.roi.y, min(action.roi.y + action.roi.h, y))

        logger.info(
            "ClickRandom: (%d, %d) in ROI(x=%d, y=%d, w=%d, h=%d)",
            x,
            y,
            action.roi.x,
            action.roi.y,
            action.roi.w,
            action.roi.h,
        )

        self._ctx.mouse.click(
            x=x,
            y=y,
            button=action.button,
            clicks=action.clicks,
            interval=action.interval_ms / 1000.0,
        )
        return None

    # ═══════════════════════════════════════════════════════════════
    # NEW EXECUTORS (Added to fix missing actions from user guide)
    # ═══════════════════════════════════════════════════════════════

    def _exec_drag(self, action: Drag) -> None:
        """Execute Drag action."""
        logger.info(
            "Drag: (%d, %d) -> (%d, %d) over %dms",
            action.from_x, action.from_y,
            action.to_x, action.to_y,
            action.duration_ms,
        )
        self._ctx.mouse.drag(
            from_x=action.from_x,
            from_y=action.from_y,
            to_x=action.to_x,
            to_y=action.to_y,
            duration=action.duration_ms / 1000.0,
            button=action.button,
        )
        return None

    def _exec_scroll(self, action: Scroll) -> None:
        """Execute Scroll action."""
        x = action.x if action.x is not None else self._ctx.mouse.position()[0]
        y = action.y if action.y is not None else self._ctx.mouse.position()[1]
        logger.info("Scroll: amount=%d at (%d, %d)", action.amount, x, y)
        self._ctx.mouse.scroll(x=x, y=y, amount=action.amount)
        return None

    def _exec_delay_random(self, action: DelayRandom) -> None:
        """Execute DelayRandom action."""
        import random
        delay_ms = random.randint(action.min_ms, action.max_ms)
        logger.info("DelayRandom: %dms (range %d-%d)", delay_ms, action.min_ms, action.max_ms)

        # Sleep in chunks for stop/pause support
        remaining = delay_ms
        chunk = 100
        while remaining > 0:
            if not self._ctx.wait_if_paused():
                return None
            sleep_time = min(chunk, remaining)
            time.sleep(sleep_time / 1000.0)
            remaining -= sleep_time
        return None

    def _exec_loop(self, action: Loop, flow: Flow, labels: dict[str, int]) -> None:
        """Execute Loop action with nested actions."""
        iterations = action.count if action.count is not None else 100000  # Safety limit
        logger.info("Loop: %s iterations", "∞" if action.count is None else action.count)

        for i in range(iterations):
            if not self._ctx.wait_if_paused():
                return False
            logger.debug("Loop iteration %d/%s", i + 1, action.count or "∞")
            for nested_action in action.actions:
                result = self._dispatch_action(nested_action, flow, labels)
                if result is False:
                    return False
        return None

    def _exec_while_image(self, action: WhileImage, flow: Flow, labels: dict[str, int]) -> None:
        """Execute WhileImage action - repeat while image present/absent."""
        logger.info("WhileImage: %s (while_present=%s)", action.asset_id, action.while_present)

        for i in range(action.max_iterations):
            if not self._ctx.wait_if_paused():
                return False

            # Check if image is present
            found = self._ctx.matcher.find(action.asset_id, roi_override=action.roi_override)
            is_present = found.found if hasattr(found, 'found') else bool(found)

            # Continue loop based on condition
            should_continue = is_present if action.while_present else not is_present
            if not should_continue:
                logger.info("WhileImage: condition no longer met, exiting loop")
                break

            # Execute nested actions
            for nested_action in action.actions:
                result = self._dispatch_action(nested_action, flow, labels)
                if result is False:
                    return False

        return None

    def _exec_wait_pixel(self, action: WaitPixel) -> bool | None:
        """Execute WaitPixel action - wait for pixel color."""
        logger.info(
            "WaitPixel: (%d, %d) color=RGB(%d,%d,%d) appear=%s",
            action.x, action.y,
            action.color.r, action.color.g, action.color.b,
            action.appear,
        )

        start_time = time.time()
        timeout_sec = action.timeout_ms / 1000.0

        while True:
            if not self._ctx.wait_if_paused():
                return False

            # Get pixel color at position
            try:
                img = self._ctx.capture.grab()
                # Access pixel at (x, y) - assumed PIL Image or numpy array
                if hasattr(img, 'getpixel'):
                    r, g, b = img.getpixel((action.x, action.y))[:3]
                else:
                    r, g, b = img[action.y, action.x][:3]

                color_matches = action.color.matches(r, g, b)
                if (action.appear and color_matches) or (not action.appear and not color_matches):
                    logger.info("WaitPixel: condition met")
                    return None
            except Exception as e:
                logger.warning("WaitPixel pixel check failed: %s", e)

            # Check timeout
            if time.time() - start_time > timeout_sec:
                logger.warning("WaitPixel: timeout after %dms", action.timeout_ms)
                return None

            time.sleep(action.poll_ms / 1000.0)

    def _exec_if_pixel(self, action: IfPixel, flow: Flow, labels: dict[str, int]) -> None:
        """Execute IfPixel conditional based on pixel color."""
        # Get pixel color
        try:
            img = self._ctx.capture.grab()
            if hasattr(img, 'getpixel'):
                r, g, b = img.getpixel((action.x, action.y))[:3]
            else:
                r, g, b = img[action.y, action.x][:3]

            color_matches = action.color.matches(r, g, b)
        except Exception as e:
            logger.warning("IfPixel pixel check failed: %s", e)
            color_matches = False

        # Execute appropriate branch
        actions_to_run = action.then_actions if color_matches else action.else_actions
        logger.info("IfPixel: (%d,%d) matched=%s, running %d actions",
                    action.x, action.y, color_matches, len(actions_to_run))

        for nested_action in actions_to_run:
            result = self._dispatch_action(nested_action, flow, labels)
            if result is False:
                return False
        return None

    def _exec_click_until(self, action: ClickUntil) -> bool | None:
        """Execute ClickUntil - click repeatedly until condition met."""
        logger.info(
            "ClickUntil: click=%s until=%s (appear=%s)",
            action.click_asset_id, action.until_asset_id, action.until_appear,
        )

        start_time = time.time()
        timeout_sec = action.timeout_ms / 1000.0
        click_count = 0

        while click_count < action.max_clicks:
            if not self._ctx.wait_if_paused():
                return False

            # Check if target condition is met
            found = self._ctx.matcher.find(action.until_asset_id)
            is_present = found.found if hasattr(found, 'found') else bool(found)
            condition_met = is_present if action.until_appear else not is_present

            if condition_met:
                logger.info("ClickUntil: condition met after %d clicks", click_count)
                return None

            # Find and click the click_asset
            click_result = self._ctx.matcher.find(action.click_asset_id)
            if click_result and (click_result.found if hasattr(click_result, 'found') else bool(click_result)):
                cx, cy = click_result.center if hasattr(click_result, 'center') else (click_result.x, click_result.y)
                self._ctx.mouse.click(x=cx, y=cy, button=action.button)
                click_count += 1
                logger.debug("ClickUntil: clicked %s (%d/%d)", action.click_asset_id, click_count, action.max_clicks)

            # Check timeout
            if time.time() - start_time > timeout_sec:
                logger.warning("ClickUntil: timeout after %dms, %d clicks", action.timeout_ms, click_count)
                return None

            time.sleep(action.click_interval_ms / 1000.0)

        logger.warning("ClickUntil: max clicks reached (%d)", action.max_clicks)
        return None
