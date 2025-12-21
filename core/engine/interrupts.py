"""
RetroAuto v2 - Interrupt Watcher

Background thread that monitors for interrupt conditions.
"""

import threading
import time
from typing import TYPE_CHECKING

from core.engine.context import EngineState, ExecutionContext
from core.models import InterruptRule
from infra import get_logger

if TYPE_CHECKING:
    from core.engine.runner import Runner

logger = get_logger("Interrupts")


class InterruptWatcher:
    """
    Background thread that watches for interrupt conditions.

    Features:
    - Priority-based checking (higher priority first)
    - Pauses main runner when triggered
    - Executes interrupt actions or flow
    - Thread-safe with locks
    - Exponential backoff during idle
    """

    def __init__(
        self,
        ctx: ExecutionContext,
        runner: "Runner",
        poll_ms: int = 200,
        backoff_max_ms: int = 1000,
    ) -> None:
        """
        Initialize interrupt watcher.

        Args:
            ctx: Execution context
            runner: Runner for executing interrupt actions
            poll_ms: Base polling interval
            backoff_max_ms: Maximum backoff during idle
        """
        self._ctx = ctx
        self._runner = runner
        self._poll_ms = poll_ms
        self._backoff_max_ms = backoff_max_ms

        self._thread: threading.Thread | None = None
        self._running = False
        self._lock = threading.Lock()
        self._triggered_cooldown: dict[str, float] = {}  # Prevent spam

    def start(self) -> None:
        """Start the watcher thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info("InterruptWatcher started")

    def stop(self) -> None:
        """Stop the watcher thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("InterruptWatcher stopped")

    def _watch_loop(self) -> None:
        """Main watch loop."""
        current_poll = self._poll_ms
        consecutive_idle = 0

        while self._running:
            # Only check when engine is running
            if self._ctx.state != EngineState.RUNNING:
                time.sleep(self._poll_ms / 1000.0)
                continue

            # Check interrupts in priority order
            triggered = self._check_interrupts()

            if triggered:
                consecutive_idle = 0
                current_poll = self._poll_ms
            else:
                consecutive_idle += 1
                # Exponential backoff during idle
                if consecutive_idle > 5:
                    current_poll = min(current_poll * 1.2, self._backoff_max_ms)

            time.sleep(current_poll / 1000.0)

    def _check_interrupts(self) -> bool:
        """
        Check all interrupt rules in priority order.

        Returns:
            True if any interrupt was triggered
        """
        rules = self._get_sorted_rules()

        for rule in rules:
            # Check cooldown
            cooldown_key = rule.when_image
            if cooldown_key in self._triggered_cooldown:
                if time.time() - self._triggered_cooldown[cooldown_key] < 1.0:
                    continue  # Skip, still in cooldown

            # Check if image is present
            match = self._ctx.matcher.find(rule.when_image, rule.roi_override)
            if match is None:
                continue

            logger.info(
                "Interrupt triggered: %s (priority=%d, conf=%.2f)",
                rule.when_image,
                rule.priority,
                match.confidence,
            )

            # Update cooldown
            self._triggered_cooldown[cooldown_key] = time.time()

            # Store match for actions
            self._ctx.last_match = match

            # Execute interrupt
            self._execute_interrupt(rule)
            return True

        return False

    def _get_sorted_rules(self) -> list[InterruptRule]:
        """Get interrupt rules sorted by priority (descending)."""
        rules = list(self._ctx.script.interrupts)
        rules.sort(key=lambda r: r.priority, reverse=True)
        return rules

    def _execute_interrupt(self, rule: InterruptRule) -> None:
        """
        Execute interrupt actions.

        The main runner is already paused via shared state.
        """
        with self._lock:
            # Pause main execution while handling interrupt
            was_running = self._ctx.is_running
            if was_running:
                self._ctx.request_pause()

            try:
                if rule.run_flow:
                    # Run a flow
                    logger.info("Interrupt running flow: %s", rule.run_flow)
                    self._runner.run_flow(rule.run_flow)
                elif rule.do_actions:
                    # Execute inline actions
                    logger.info("Interrupt executing %d actions", len(rule.do_actions))
                    for action in rule.do_actions:
                        if self._ctx.should_stop:
                            break
                        self._runner._execute_action(action, None, {})
            except Exception as e:
                logger.exception("Error executing interrupt: %s", e)
            finally:
                # Resume main execution
                if was_running and not self._ctx.should_stop:
                    self._ctx.request_resume()


class InterruptManager:
    """
    High-level manager for interrupt handling.

    Coordinates between runner and watcher.
    """

    def __init__(self, ctx: ExecutionContext) -> None:
        self._ctx = ctx
        self._runner: Runner | None = None
        self._watcher: InterruptWatcher | None = None

    def set_runner(self, runner: "Runner") -> None:
        """Set the runner instance."""
        self._runner = runner

    def start_watching(self) -> None:
        """Start interrupt watching."""
        if self._runner is None:
            logger.warning("Cannot start watching: no runner set")
            return

        if not self._ctx.script.interrupts:
            logger.debug("No interrupt rules defined, skipping watcher")
            return

        self._watcher = InterruptWatcher(self._ctx, self._runner)
        self._watcher.start()

    def stop_watching(self) -> None:
        """Stop interrupt watching."""
        if self._watcher:
            self._watcher.stop()
            self._watcher = None
