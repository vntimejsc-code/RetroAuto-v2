"""
Deep Verification for Global Interrupts (Concurrency & Priority)
"""

import sys
import time
import unittest
from unittest.mock import MagicMock, call

# Ensure core can be imported
sys.path.append("c:/Auto/Newauto")

from core.engine.context import EngineState, ExecutionContext
from core.engine.interrupts import InterruptWatcher
from core.models import InterruptRule


class TestInterruptsDeep(unittest.TestCase):
    def setUp(self):
        self.ctx = MagicMock(spec=ExecutionContext)
        self.ctx.state = EngineState.RUNNING
        self.ctx.wait_if_paused.return_value = True
        self.ctx.is_running = True
        self.ctx.should_stop = False

        # Mock script with interrupts list
        self.ctx.script = MagicMock()
        self.ctx.script.interrupts = []

        self.runner = MagicMock()
        self.watcher = InterruptWatcher(self.ctx, self.runner, poll_ms=10)  # Fast poll for tests

    def tearDown(self):
        if self.watcher:
            self.watcher.stop()

    def test_interrupt_trigger(self):
        """Verify interrupt triggers when image appears."""
        # Rule: If 'low_hp' appears, run 'HealFlow'
        rule = InterruptRule(when_image="low_hp", priority=10, run_flow="HealFlow")
        self.ctx.script.interrupts = [rule]

        # Mock matcher: Initially nothing, then 'low_hp' appears
        def side_effect_find(asset_id, roi=None):
            if asset_id == "low_hp":
                return MagicMock(confidence=0.99)
            return None

        self.ctx.matcher.find.side_effect = side_effect_find

        self.watcher.start()
        time.sleep(0.1)  # Give thread time to tick

        # Verify run_flow called
        self.runner.run_flow.assert_called_with("HealFlow")

        # Verify pause requested
        self.ctx.request_pause.assert_called()
        self.ctx.request_resume.assert_called()

    def test_interrupt_priority(self):
        """Verify higher priority interrupt preempts lower."""
        # Rules: Critical (P10) and Buff (P1)
        r_crit = InterruptRule(when_image="crit", priority=10, run_flow="Critical")
        r_buff = InterruptRule(when_image="buff", priority=1, run_flow="Buff")
        self.ctx.script.interrupts = [r_crit, r_buff]

        # Both appear at same time
        def side_effect_find(asset_id, roi=None):
            return MagicMock(confidence=0.9)

        self.ctx.matcher.find.side_effect = side_effect_find

        self.watcher.start()
        time.sleep(0.1)

        # Should execute Critical (P10)
        self.runner.run_flow.assert_any_call("Critical")

        # Since watcher loops, it might execute Buff next if critical is done/cooldown?
        # But we verify critical was called FIRST or at least called.
        # Actually since logic breaks after first trigger, only P10 should fire in the first tick.
        # P1 might fire in next tick if P10 enters cooldown.

        # Let's check call args list to ensure Critical was first *if* both fired
        calls = self.runner.run_flow.call_args_list
        if not calls:
            self.fail("No flow run")

        self.assertEqual(calls[0], call("Critical"), "Highest priority did not run first")

    def test_cooldown_logic(self):
        """Verify interrupt does not spam (1s cooldown)."""
        rule = InterruptRule(when_image="spam", priority=5, run_flow="AntiSpam")
        self.ctx.script.interrupts = [rule]

        self.ctx.matcher.find.return_value = MagicMock(confidence=1.0)

        self.watcher.start()
        time.sleep(0.3)

        # Should have run once (maybe twice if 0.1s slept > poll 10ms + execution)
        # But cooldown is 1.0s. So strictly ONCE.
        self.assertEqual(
            self.runner.run_flow.call_count, 1, "Cooldown failed, triggered multiple times"
        )

        # Wait for cooldown expire (>1s)
        time.sleep(1.1)

        # Should trigger again
        # The watcher thread is still running
        count = self.runner.run_flow.call_count
        self.assertGreater(count, 1, "Did not re-trigger after cooldown")


if __name__ == "__main__":
    unittest.main()
