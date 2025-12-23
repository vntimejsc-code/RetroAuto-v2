"""
MacroIDE 95 - Entry Point

Launches the MacroIDE 95 application with Win95/98 styling.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.ui.ide_main_window import IDEMainWindow
from app.ui.win95_style import apply_win95_style


def main() -> int:
    """Main entry point."""
    # Initialize stability features first
    from infra.crash_handler import CrashHandler
    CrashHandler.install()

    # Start memory manager for 24/7 operation
    from core.engine.memory_manager import get_memory_manager
    memory_mgr = get_memory_manager()
    memory_mgr.start()

    app = QApplication(sys.argv)

    # Apply Win95/98 styling
    apply_win95_style(app)

    # Create and show main window
    window = IDEMainWindow()
    window.show()

    result = app.exec()

    # Cleanup
    memory_mgr.stop()

    return result


if __name__ == "__main__":
    sys.exit(main())

