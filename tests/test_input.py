"""
Tests for input/mouse.py and input/keyboard.py
"""

from input.keyboard import KeyboardController
from input.mouse import MouseController


class TestMouseController:
    """Tests for MouseController."""

    def test_mouse_instance(self):
        mouse = MouseController()
        assert mouse is not None

    def test_get_position(self):
        mouse = MouseController()
        pos = mouse.get_position()

        assert isinstance(pos, tuple)
        assert len(pos) == 2
        assert isinstance(pos[0], int)
        assert isinstance(pos[1], int)


class TestKeyboardController:
    """Tests for KeyboardController."""

    def test_keyboard_instance(self):
        kb = KeyboardController()
        assert kb is not None
