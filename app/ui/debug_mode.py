"""
RetroAuto v2 - Debug Mode Widget

Debug mode content for UnifiedStudio with:
- Execution controls (Step Over, Step Into, Continue)
- Breakpoints list
- Variable watch panel
- Call stack view
"""

from __future__ import annotations


from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QPushButton,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QHeaderView,
    QFrame,
)


class DebugToolbar(QFrame):
    """Debug execution control toolbar."""
    
    # Signals
    continue_requested = Signal()
    step_over_requested = Signal()
    step_into_requested = Signal()
    step_out_requested = Signal()
    restart_requested = Signal()
    stop_requested = Signal()
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Continue
        self.continue_btn = QPushButton("▶ Continue")
        self.continue_btn.setToolTip("Continue execution (F5)")
        self.continue_btn.clicked.connect(self.continue_requested.emit)
        layout.addWidget(self.continue_btn)
        
        # Step Over
        self.step_over_btn = QPushButton("⏭ Step Over")
        self.step_over_btn.setToolTip("Step over current line (F10)")
        self.step_over_btn.clicked.connect(self.step_over_requested.emit)
        layout.addWidget(self.step_over_btn)
        
        # Step Into
        self.step_into_btn = QPushButton("⬇ Step Into")
        self.step_into_btn.setToolTip("Step into function (F11)")
        self.step_into_btn.clicked.connect(self.step_into_requested.emit)
        layout.addWidget(self.step_into_btn)
        
        # Step Out
        self.step_out_btn = QPushButton("⬆ Step Out")
        self.step_out_btn.setToolTip("Step out of function (Shift+F11)")
        self.step_out_btn.clicked.connect(self.step_out_requested.emit)
        layout.addWidget(self.step_out_btn)
        
        layout.addStretch()
        
        # Restart
        self.restart_btn = QPushButton("🔄 Restart")
        self.restart_btn.setToolTip("Restart debugging (Ctrl+Shift+F5)")
        self.restart_btn.clicked.connect(self.restart_requested.emit)
        layout.addWidget(self.restart_btn)
        
        # Stop
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setToolTip("Stop debugging (Shift+F5)")
        self.stop_btn.clicked.connect(self.stop_requested.emit)
        layout.addWidget(self.stop_btn)
        
        self._apply_style()
    
    def _apply_style(self) -> None:
        self.setStyleSheet("""
            DebugToolbar {
                background-color: #252526;
                border-bottom: 1px solid #3c3c3c;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
            QPushButton:disabled {
                color: #5a5a5a;
            }
        """)
    
    def set_running(self, running: bool) -> None:
        """Enable/disable controls based on running state."""
        self.continue_btn.setEnabled(not running)
        self.step_over_btn.setEnabled(not running)
        self.step_into_btn.setEnabled(not running)
        self.step_out_btn.setEnabled(not running)


class BreakpointsPanel(QGroupBox):
    """Panel showing all breakpoints."""
    
    breakpoint_clicked = Signal(str, int)  # file, line
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("🔴 Breakpoints", parent)
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 4)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Location", "Enabled"])
        self.tree.setColumnCount(2)
        self.tree.setRootIsDecorated(False)
        self.tree.itemDoubleClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)
        
        # Demo breakpoints
        self._add_demo_breakpoints()
    
    def _add_demo_breakpoints(self) -> None:
        """Add sample breakpoints for demo."""
        samples = [
            ("main.dsl:12", True),
            ("main.dsl:25", True),
            ("utils.dsl:8", False),
        ]
        for loc, enabled in samples:
            item = QTreeWidgetItem([loc, "✓" if enabled else "○"])
            self.tree.addTopLevelItem(item)
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        loc = item.text(0)
        if ":" in loc:
            file_name, line = loc.rsplit(":", 1)
            self.breakpoint_clicked.emit(file_name, int(line))
    
    def add_breakpoint(self, file_name: str, line: int) -> None:
        """Add a breakpoint to the list."""
        item = QTreeWidgetItem([f"{file_name}:{line}", "✓"])
        self.tree.addTopLevelItem(item)
    
    def clear(self) -> None:
        """Clear all breakpoints."""
        self.tree.clear()


class VariablesPanel(QGroupBox):
    """Panel showing variable values during debugging."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("📋 Variables", parent)
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 4)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Value", "Type"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # Demo variables
        self._add_demo_variables()
    
    def _add_demo_variables(self) -> None:
        """Add sample variables for demo."""
        samples = [
            ("counter", "5", "int"),
            ("found", "True", "bool"),
            ("target_pos", "(120, 450)", "tuple"),
            ("current_flow", '"main"', "str"),
        ]
        self.table.setRowCount(len(samples))
        for row, (name, value, var_type) in enumerate(samples):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(value))
            self.table.setItem(row, 2, QTableWidgetItem(var_type))
    
    def update_variable(self, name: str, value: str, var_type: str) -> None:
        """Update or add a variable."""
        # Find existing row
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == name:
                self.table.setItem(row, 1, QTableWidgetItem(value))
                self.table.setItem(row, 2, QTableWidgetItem(var_type))
                return
        
        # Add new row
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem(value))
        self.table.setItem(row, 2, QTableWidgetItem(var_type))
    
    def clear(self) -> None:
        """Clear all variables."""
        self.table.setRowCount(0)


class CallStackPanel(QGroupBox):
    """Panel showing the call stack during debugging."""
    
    frame_clicked = Signal(str, int)  # file, line
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("📚 Call Stack", parent)
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 4)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Function", "Location"])
        self.tree.setColumnCount(2)
        self.tree.setRootIsDecorated(False)
        self.tree.itemDoubleClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)
        
        # Demo stack
        self._add_demo_stack()
    
    def _add_demo_stack(self) -> None:
        """Add sample call stack for demo."""
        samples = [
            ("do_click", "main.dsl:25"),
            ("flow_main", "main.dsl:10"),
            ("<module>", "main.dsl:1"),
        ]
        for func, loc in samples:
            item = QTreeWidgetItem([func, loc])
            self.tree.addTopLevelItem(item)
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        loc = item.text(1)
        if ":" in loc:
            file_name, line = loc.rsplit(":", 1)
            self.frame_clicked.emit(file_name, int(line))
    
    def clear(self) -> None:
        """Clear the call stack."""
        self.tree.clear()


class DebugModeWidget(QWidget):
    """
    Debug mode content widget for UnifiedStudio.
    
    Features:
    - Debug toolbar with step controls
    - Breakpoints panel
    - Variable watch panel
    - Call stack panel
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Debug toolbar
        self.toolbar = DebugToolbar()
        layout.addWidget(self.toolbar)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Code view placeholder
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(4, 4, 4, 4)
        
        code_label = QLabel("📝 Code View")
        code_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                background-color: #2d2d30;
                color: #cccccc;
            }
        """)
        left_layout.addWidget(code_label)
        
        code_placeholder = QLabel(
            "Code with current execution line\n\n"
            "→ line 25: click(target_image)\n"
            "   line 26: wait(500)\n"
            "   line 27: if found:\n"
        )
        code_placeholder.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                padding: 12px;
            }
        """)
        code_placeholder.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(code_placeholder, 1)
        
        splitter.addWidget(left_panel)
        
        # Right side: Debug panels
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(4)
        
        # Variables panel
        self.variables_panel = VariablesPanel()
        right_layout.addWidget(self.variables_panel)
        
        # Call stack panel
        self.call_stack_panel = CallStackPanel()
        right_layout.addWidget(self.call_stack_panel)
        
        # Breakpoints panel
        self.breakpoints_panel = BreakpointsPanel()
        right_layout.addWidget(self.breakpoints_panel)
        
        splitter.addWidget(right_panel)
        
        # Set proportions
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([500, 300])
        
        layout.addWidget(splitter)
        
        self._apply_style()
    
    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: #252526;
                color: #cccccc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QTreeWidget, QTableWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-size: 11px;
            }
            QTreeWidget::item, QTableWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected, QTableWidget::item:selected {
                background-color: #094771;
            }
            QHeaderView::section {
                background-color: #2d2d30;
                color: #cccccc;
                padding: 4px;
                border: none;
                border-bottom: 1px solid #3c3c3c;
            }
        """)
