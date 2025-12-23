"""
Global Crash Handler
Pillar 2 of "Titan Light" Robustness Strategy.

Intercepts unhandled exceptions and shows a dialog instead of crashing to desktop.
"""

import platform
import subprocess
import sys
import traceback
from datetime import datetime

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStyle,
    QTextEdit,
    QVBoxLayout,
)

from infra import get_logger

logger = get_logger("CrashHandler")


class CrashDialog(QDialog):
    """
    Dialog shown when the application crashes.
    """

    def __init__(self, exctype, value, tb, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RetroAuto - Critcal Error")
        self.setMinimumSize(600, 400)
        self.setModal(True)

        # Get traceback string
        self.traceback_text = "".join(traceback.format_exception(exctype, value, tb))

        # Determine restart command
        self.restart_cmd = [sys.executable] + sys.argv

        self._init_ui(exctype, value)

    def _init_ui(self, exctype, value):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()

        # Icon (Warning)
        icon_label = QLabel()
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical)
        icon_label.setPixmap(icon.pixmap(48, 48))
        header_layout.addWidget(icon_label)

        # Message
        msg_layout = QVBoxLayout()
        title_label = QLabel("Oops! RetroAuto encountered a problem.")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff5555;")

        desc_label = QLabel(
            "An unhandled exception occurred. You can restart the application or close it.\n"
            f"Error: {exctype.__name__}: {value}"
        )
        desc_label.setWordWrap(True)

        msg_layout.addWidget(title_label)
        msg_layout.addWidget(desc_label)
        header_layout.addLayout(msg_layout)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Stack Trace Area
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Consolas", 9))
        self.text_edit.setPlainText(self.traceback_text)
        self.text_edit.setStyleSheet(
            "background-color: #2b2b2b; color: #f8f8f2; border: 1px solid #444;"
        )
        layout.addWidget(self.text_edit)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_copy = QPushButton("📄 Copy Error")
        btn_copy.clicked.connect(self._copy_error)

        btn_restart = QPushButton("🔄 Restart Application")
        btn_restart.clicked.connect(self._restart_app)
        btn_restart.setStyleSheet("background-color: #50fa7b; color: #000; font-weight: bold;")

        btn_close = QPushButton("❌ Close")
        btn_close.clicked.connect(self.close)

        btn_layout.addWidget(btn_copy)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_restart)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _copy_error(self):
        clipboard = QApplication.clipboard()
        report = (
            f"RetroAuto Crash Report\n"
            f"Date: {datetime.now()}\n"
            f"OS: {platform.system()} {platform.release()}\n"
            f"Python: {platform.python_version()}\n\n"
            f"Traceback:\n{self.traceback_text}"
        )
        clipboard.setText(report)
        self.text_edit.selectAll()

    def _restart_app(self):
        """Restart the application."""
        logger.info("Restarting application...")
        subprocess.Popen(self.restart_cmd)
        QApplication.quit()


class CrashHandler:
    """
    Installs global exception hooks to catch crashes.
    """

    _installed = False
    _is_handling = False

    @classmethod
    def install(cls):
        if cls._installed:
            return

        sys.excepthook = cls._handle_exception
        # Also catch calls that are ignored (like in threads mostly, though Qt handles connection errors differently)
        # sys.unraisablehook = cls._handle_unraisable

        cls._installed = True
        logger.info("Global Crash Handler installed")

    @classmethod
    def _handle_exception(cls, exctype, value, tb):
        """Handle execution exception."""
        # Prevent recursion
        if cls._is_handling:
            sys.__excepthook__(exctype, value, tb)
            return

        cls._is_handling = True
        try:
            # Log it first (safely)
            try:
                logger.critical("Uncaught exception!", exc_info=(exctype, value, tb))
            except Exception:
                print("Failed to log crash (likely stack overflow)", file=sys.stderr)

            # Don't handle KeyboardInterrupt (Ctrl+C)
            if issubclass(exctype, KeyboardInterrupt):
                sys.__excepthook__(exctype, value, tb)
                return

            # Show dialog if QApplication exists
            app = QApplication.instance()
            if app:
                try:
                    dialog = CrashDialog(exctype, value, tb)
                    dialog.exec()
                except Exception as e:
                    # If dialog fails, fallback to stderr
                    print("Error showing CrashDialog:", e, file=sys.stderr)
                    sys.__excepthook__(exctype, value, tb)
            else:
                sys.__excepthook__(exctype, value, tb)
        finally:
            cls._is_handling = False

    # @classmethod
    # def _handle_unraisable(cls, args):
    #     """Handle unraisable exceptions (e.g. in __del__)."""
    #     cls._handle_exception(args.exc_type, args.exc_value, args.exc_traceback)
