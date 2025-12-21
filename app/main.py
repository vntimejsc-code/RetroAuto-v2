"""
RetroAuto v2 - Windows Automation Tool

Entry point for the application.
"""

import sys
from pathlib import Path

# Add project root to path for direct execution
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from PySide6.QtWidgets import QApplication, QStyleFactory

from app.ui.main_window import MainWindow
from infra import setup_logging


def main() -> int:
    """Application entry point."""
    # Setup logging first
    logger = setup_logging()
    logger.info("RetroAuto v2 starting...")

    # Create Qt application
    app = QApplication(sys.argv)

    # Apply Windows 95/98 style
    app.setStyle(QStyleFactory.create("Windows"))

    # Create and show main window
    window = MainWindow()
    window.show()

    logger.info("Main window displayed")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
