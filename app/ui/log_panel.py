"""
RetroAuto v2 - Log Panel

Displays application logs with filtering.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from infra import log_emitter


class LogPanel(QWidget):
    """
    Panel for displaying logs.

    Features:
    - Append text with level coloring
    - Filter by log level
    - Clear button
    """

    COLORS = {
        "DEBUG": "#808080",
        "INFO": "#000000",
        "WARNING": "#FF8C00",
        "ERROR": "#FF0000",
        "CRITICAL": "#FF0000",
    }

    def __init__(self) -> None:
        super().__init__()
        self._filter_level = "DEBUG"
        self._init_ui()
        self._connect_log_emitter()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Group box
        group = QGroupBox("Log")
        group_layout = QVBoxLayout(group)

        # Toolbar
        toolbar = QHBoxLayout()

        # Level filter
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.filter_combo.setCurrentText("DEBUG")
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.filter_combo)

        toolbar.addStretch()

        # Clear button
        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self._on_clear)
        toolbar.addWidget(btn_clear)

        group_layout.addLayout(toolbar)

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(self.log_text.document().defaultFont())
        group_layout.addWidget(self.log_text)

        layout.addWidget(group)

    def _connect_log_emitter(self) -> None:
        """Connect to global log emitter."""
        log_emitter.add_callback(self._on_log)

    def _on_log(self, level: str, timestamp: str, message: str) -> None:
        """Handle incoming log message."""
        # Filter by level
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if levels.index(level) < levels.index(self._filter_level):
            return

        color = self.COLORS.get(level, "#000000")
        html = f'<span style="color:{color}">[{timestamp}] {level}: {message}</span>'
        self.log_text.append(html)

        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_filter_changed(self, level: str) -> None:
        """Change log filter level."""
        self._filter_level = level

    def _on_clear(self) -> None:
        """Clear log text."""
        self.log_text.clear()

    def append(self, text: str) -> None:
        """Append plain text to log."""
        self.log_text.append(text)
