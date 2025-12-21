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
    app = QApplication(sys.argv)
    
    # Apply Win95/98 styling
    apply_win95_style(app)
    
    # Create and show main window
    window = IDEMainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
