import unittest

from core.dsl.parser import Parser
from core.engine.interpreter import Interpreter
from core.security.policy import SecurityViolation


class TestSecuritySandbox(unittest.TestCase):

    def test_default_unsafe(self):
        """Default policy should allow actions."""
        code = 'flow main { type("hello"); }'
        interp = Interpreter()
        # Should not raise exception
        try:
            interp.execute(Parser(code).parse())
        except SecurityViolation:
            self.fail("Default policy should be UNSAFE (allow everything)")

    def test_permission_denied(self):
        """Restricted policy should block unauthorized actions."""
        # Policy only allows FS_READ, but code tries INPUT_CONTROL (type)
        code = """
        @permissions { "FS_READ" }
        flow main {
            type("should fail");
        }
        """
        interp = Interpreter()
        program = Parser(code).parse()
        print(f"DEBUG: Parsed permissions: {program.permissions}")
        if not program.permissions:
            print(f"DEBUG: Parser errors: {Parser(code).errors}")

        with self.assertRaises(SecurityViolation):
            interp.execute(program)

    def test_permission_granted(self):
        """Policy with correct permission should succeed."""
        code = """
        @permissions { "INPUT_CONTROL" }
        flow main {
            type("should pass");
        }
        """
        interp = Interpreter()
        try:
            interp.execute(Parser(code).parse())
        except SecurityViolation as e:
            self.fail(f"Should allow action with correct permission: {e}")


if __name__ == "__main__":
    unittest.main()
