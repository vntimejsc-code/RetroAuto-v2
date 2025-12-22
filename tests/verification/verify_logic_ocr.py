
import unittest
from unittest.mock import MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.models import IfText, Action, Delay
from core.engine.runner import Runner
from core.engine.context import ExecutionContext

class TestOCRLogic(unittest.TestCase):
    def setUp(self):
        # Mock Context
        self.ctx = MagicMock(spec=ExecutionContext)
        self.ctx.variables = {}
        # Mock wait_if_paused to always return True (not paused)
        self.ctx.wait_if_paused.return_value = True
        
        # Init Runner with mocked context
        self.runner = Runner(self.ctx)
        
        # Mock recursive execution to track calls
        self.runner._execute_action = MagicMock()

    def test_if_text_numeric(self):
        # Scenario: HP = "100"
        self.ctx.variables["$hp"] = "100"
        
        pass_action = Delay(ms=10)
        fail_action = Delay(ms=999)

        # If $hp > 50
        action = IfText(
            variable_name="$hp",
            operator="numeric_gt",
            value="50",
            then_actions=[pass_action], 
            else_actions=[fail_action] 
        )
        
        self.runner._exec_if_text(action, MagicMock(), {})
        
        # Verify THEN branch executed (pass_action)
        self.runner._execute_action.assert_called_with(pass_action, unittest.mock.ANY, unittest.mock.ANY)
        
    def test_if_text_contains(self):
        self.ctx.variables["$chat"] = "Player1: Hello World"
        pass_action = Delay(ms=10)
        
        action = IfText(
            variable_name="$chat",
            operator="contains",
            value="Hello",
            then_actions=[pass_action],
            else_actions=[]
        )
        
        self.runner._exec_if_text(action, MagicMock(), {})
        self.runner._execute_action.assert_called_with(pass_action, unittest.mock.ANY, unittest.mock.ANY)

    def test_if_text_fail(self):
        self.ctx.variables["$hp"] = "10"
        pass_action = Delay(ms=10)
        fail_action = Delay(ms=999)
        
        action = IfText(
            variable_name="$hp",
            operator="numeric_gt",
            value="50",
            then_actions=[pass_action],
            else_actions=[fail_action] 
        )
        
        self.runner._exec_if_text(action, MagicMock(), {})
        # Verify ELSE branch executed (fail_action)
        self.runner._execute_action.assert_called_with(fail_action, unittest.mock.ANY, unittest.mock.ANY)

if __name__ == '__main__':
    unittest.main()
