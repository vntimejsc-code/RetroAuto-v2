"""
RetroAuto v2 - Editor Dialogs

Go To Line and Find/Replace dialogs for the code editor.

Phase: IDE MVP
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class GoToLineDialog(QDialog):
    """
    Go To Line dialog (Ctrl+G).

    Allows user to jump to a specific line number.
    """

    def __init__(self, parent: QWidget | None = None, max_line: int = 1) -> None:
        super().__init__(parent)
        self.setWindowTitle("Go to Line")
        self.setModal(True)
        self.setFixedSize(280, 100)

        self._max_line = max_line
        self._line_number = 1

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Input row
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Line number (1-{}):".format(self._max_line)))

        self.spin = QSpinBox()
        self.spin.setMinimum(1)
        self.spin.setMaximum(self._max_line)
        self.spin.setValue(1)
        self.spin.selectAll()
        input_layout.addWidget(self.spin)

        layout.addLayout(input_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        go_btn = QPushButton("Go")
        go_btn.setDefault(True)
        go_btn.clicked.connect(self._on_go)
        btn_layout.addWidget(go_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _on_go(self) -> None:
        self._line_number = self.spin.value()
        self.accept()

    def get_line_number(self) -> int:
        return self._line_number

    @staticmethod
    def get_line(parent: QWidget | None, max_line: int) -> int | None:
        """Static method to show dialog and return line number or None."""
        dialog = GoToLineDialog(parent, max_line)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_line_number()
        return None


class FindBar(QWidget):
    """
    Find bar for code editor (Ctrl+F).

    Inline search bar with next/previous navigation.
    """

    find_requested = Signal(str, bool, bool)  # text, case_sensitive, whole_word
    find_next = Signal()
    find_previous = Signal()
    close_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()
        self.hide()  # Hidden by default

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find...")
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.returnPressed.connect(self._on_find_next)
        layout.addWidget(self.search_input)

        # Options
        self.case_check = QCheckBox("Aa")
        self.case_check.setToolTip("Match Case")
        self.case_check.stateChanged.connect(self._on_options_changed)
        layout.addWidget(self.case_check)

        self.word_check = QCheckBox("W")
        self.word_check.setToolTip("Whole Word")
        self.word_check.stateChanged.connect(self._on_options_changed)
        layout.addWidget(self.word_check)

        # Navigation buttons
        prev_btn = QPushButton("<")
        prev_btn.setFixedWidth(30)
        prev_btn.setToolTip("Previous (Shift+F3)")
        prev_btn.clicked.connect(self._on_find_previous)
        layout.addWidget(prev_btn)

        next_btn = QPushButton(">")
        next_btn.setFixedWidth(30)
        next_btn.setToolTip("Next (F3)")
        next_btn.clicked.connect(self._on_find_next)
        layout.addWidget(next_btn)

        # Match count label
        self.count_label = QLabel("")
        self.count_label.setMinimumWidth(60)
        layout.addWidget(self.count_label)

        layout.addStretch()

        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedWidth(24)
        close_btn.setToolTip("Close (Esc)")
        close_btn.clicked.connect(self._on_close)
        layout.addWidget(close_btn)

        # Style
        self.setStyleSheet("""
            FindBar {
                background-color: #252526;
                border-bottom: 1px solid #3c3c3c;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #555;
                padding: 4px;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #555;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QCheckBox {
                color: #d4d4d4;
            }
            QLabel {
                color: #888;
            }
        """)

    def show_find(self, selected_text: str = "") -> None:
        """Show the find bar with optional initial text."""
        if selected_text:
            self.search_input.setText(selected_text)
        self.show()
        self.search_input.setFocus()
        self.search_input.selectAll()

    def update_count(self, current: int, total: int) -> None:
        """Update match count display."""
        if total > 0:
            self.count_label.setText(f"{current}/{total}")
        else:
            self.count_label.setText("No results")

    def _on_text_changed(self) -> None:
        text = self.search_input.text()
        if text:
            self.find_requested.emit(
                text,
                self.case_check.isChecked(),
                self.word_check.isChecked(),
            )

    def _on_options_changed(self) -> None:
        self._on_text_changed()

    def _on_find_next(self) -> None:
        self.find_next.emit()

    def _on_find_previous(self) -> None:
        self.find_previous.emit()

    def _on_close(self) -> None:
        self.hide()
        self.close_requested.emit()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._on_close()
        else:
            super().keyPressEvent(event)
