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

from PySide6.QtWidgets import QApplication, QStyleFactory  # noqa: E402

from app.ui.main_window import MainWindow  # noqa: E402
from infra import setup_logging  # noqa: E402
from infra.crash_handler import CrashHandler  # noqa: E402


def main() -> int:
    """Application entry point."""
    # Setup logging first
    logger = setup_logging()

    # Install Global Crash Handler
    CrashHandler.install()

    # Register cleanup handler for global hotkey listener
    import atexit
    def cleanup_hotkey_listener() -> None:
        """Ensure hotkey listener is stopped on exit."""
        try:
            from core.engine.hotkey_listener import get_hotkey_listener
            listener = get_hotkey_listener()
            if listener.is_running():
                listener.stop()
                logger.info("Hotkey listener cleaned up on exit")
        except Exception:
            pass  # Ignore errors during cleanup

    atexit.register(cleanup_hotkey_listener)

    logger.info("RetroAuto v2 starting...")

    # Check OCR availability
    try:
        from vision.ocr import TextReader

        reader = TextReader()
        if not reader.available:
            logger.warning("OCR (Tesseract) not available - ReadText actions will be disabled")
            logger.info(
                "To enable OCR, install Tesseract: https://github.com/tesseract-ocr/tesseract"
            )
        else:
            logger.info("OCR initialized successfully")
    except Exception as e:
        logger.warning(f"OCR initialization failed: {e}")

    # Create Qt application
    app = QApplication(sys.argv)

    # Apply Windows 95/98 style (Fusion for better QSS support, or keep Windows)
    app.setStyle(QStyleFactory.create("Fusion"))

    # Load Dark Theme
    theme_path = _project_root / "app" / "resources" / "dark_theme.qss"
    if theme_path.exists():
        app.setStyleSheet(theme_path.read_text(encoding="utf-8"))
        logger.info("Dark theme loaded")
    else:
        logger.warning(f"Theme file not found: {theme_path}")

    # Create and show main window
    window = MainWindow()
    window.show()

    logger.info("Main window displayed")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
