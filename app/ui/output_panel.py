"""
RetroAuto v2 - Output Panel

Win95-style output/log panel with tabs for:
- Output (execution logs)
- Problems (diagnostics)
- Console (future REPL)
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.dsl.diagnostics import Diagnostic, Severity


class OutputPanel(QWidget):
    """
    Output panel with Win95 tab styling.

    Tabs:
    - Output: Execution logs with color-coded levels
    - Problems: DSL diagnostics (errors, warnings)

    Signals:
        diagnostic_clicked: Emitted when a problem is double-clicked
    """

    diagnostic_clicked = Signal(str, int, int)  # file, line, col

    def __init__(self, parent=None) -> None:  # type: ignore
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Output tab
        self.output_widget = self._create_output_tab()
        self.tabs.addTab(self.output_widget, "Output")

        # Problems tab
        self.problems_widget = self._create_problems_tab()
        self.tabs.addTab(self.problems_widget, "Problems")

        # Apply styling
        self._apply_style()

    def _create_output_tab(self) -> QWidget:
        """Create the output log tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["All", "Info", "Warning", "Error"])
        self.log_level_combo.currentTextChanged.connect(self._filter_logs)
        toolbar.addWidget(self.log_level_combo)

        toolbar.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_output)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # Log output
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier New", 9))
        self.log_output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #FFFFFF;
                border: 2px inset #808080;
            }
        """)
        layout.addWidget(self.log_output)

        return widget

    def _create_problems_tab(self) -> QWidget:
        """Create the problems/diagnostics tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Problems tree
        self.problems_tree = QTreeWidget()
        self.problems_tree.setHeaderLabels(["", "Message", "Location"])
        self.problems_tree.setColumnWidth(0, 30)
        self.problems_tree.setColumnWidth(1, 400)
        self.problems_tree.itemDoubleClicked.connect(self._on_problem_clicked)
        self.problems_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #FFFFFF;
                border: 2px inset #808080;
            }
            QTreeWidget::item:selected {
                background-color: #000080;
                color: #FFFFFF;
            }
        """)
        layout.addWidget(self.problems_tree)

        return widget

    def _apply_style(self) -> None:
        """Apply Win95 tab styling."""
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px inset #808080;
                background-color: #C0C0C0;
            }
            QTabBar::tab {
                background-color: #C0C0C0;
                border: 2px outset #FFFFFF;
                border-bottom: none;
                padding: 4px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #C0C0C0;
                border-bottom: 2px solid #C0C0C0;
                margin-bottom: -2px;
            }
            QTabBar::tab:!selected {
                background-color: #808080;
                margin-top: 2px;
            }
        """)

    # ─────────────────────────────────────────────────────────────
    # Output Logging
    # ─────────────────────────────────────────────────────────────

    def log(self, message: str, level: str = "info") -> None:
        """Add a log message to output."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color based on level
        color_map = {
            "debug": "#808080",
            "info": "#000000",
            "warning": "#808000",
            "error": "#FF0000",
            "success": "#008000",
        }
        color = color_map.get(level.lower(), "#000000")

        # Add formatted message
        prefix = f"[{level.upper():7}]"
        html = f'<span style="color:{color}">{timestamp} {prefix} {message}</span>'
        self.log_output.appendHtml(html)

    def log_info(self, message: str) -> None:
        """Log info message."""
        self.log(message, "info")

    def log_warning(self, message: str) -> None:
        """Log warning message."""
        self.log(message, "warning")

    def log_error(self, message: str) -> None:
        """Log error message."""
        self.log(message, "error")

    def log_success(self, message: str) -> None:
        """Log success message."""
        self.log(message, "success")

    def _clear_output(self) -> None:
        """Clear the output log."""
        self.log_output.clear()

    def _filter_logs(self, level: str) -> None:
        """Filter logs by level (future implementation)."""
        # For now, just a placeholder
        pass

    # ─────────────────────────────────────────────────────────────
    # Problems/Diagnostics
    # ─────────────────────────────────────────────────────────────

    def set_diagnostics(self, diagnostics: list[Diagnostic], file_path: str = "") -> None:
        """Update the problems list with diagnostics."""
        self.problems_tree.clear()

        for diag in diagnostics:
            icon = "❌" if diag.severity == Severity.ERROR else "⚠️"
            location = f"{file_path}:{diag.span.start_line}:{diag.span.start_col}"

            item = QTreeWidgetItem([icon, diag.message, location])
            item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                {
                    "file": file_path,
                    "line": diag.span.start_line,
                    "col": diag.span.start_col,
                    "diagnostic": diag,
                },
            )

            # Color based on severity
            if diag.severity == Severity.ERROR:
                item.setForeground(1, QColor("#CC0000"))
            elif diag.severity == Severity.WARNING:
                item.setForeground(1, QColor("#806600"))

            self.problems_tree.addTopLevelItem(item)

        # Update tab title with count
        error_count = sum(1 for d in diagnostics if d.severity == Severity.ERROR)
        warning_count = sum(1 for d in diagnostics if d.severity == Severity.WARNING)

        if error_count or warning_count:
            self.tabs.setTabText(1, f"Problems ({error_count}E, {warning_count}W)")
        else:
            self.tabs.setTabText(1, "Problems")

    def clear_diagnostics(self) -> None:
        """Clear all diagnostics."""
        self.problems_tree.clear()
        self.tabs.setTabText(1, "Problems")

    def _on_problem_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on a problem."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            self.diagnostic_clicked.emit(data["file"], data["line"], data["col"])
