"""
RetroAuto v2 - Debug Panel

Win95-style debug panel showing:
- Call Stack
- Variables/Watch
- Breakpoints list
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
    QSplitter,
)

from core.dsl.debugger import Debugger, StackFrame, Variable, Breakpoint


class DebugPanel(QWidget):
    """
    Debug panel with Win95 styling.
    
    Tabs:
    - Call Stack: Current execution stack
    - Variables: Local and watch variables
    - Breakpoints: List of all breakpoints
    
    Signals:
        frame_selected: Stack frame was selected (frame_id)
        breakpoint_toggled: Breakpoint enable toggled (bp_id)
        breakpoint_removed: Breakpoint was removed (bp_id)
        goto_source: Navigate to source location (file, line)
    """
    
    frame_selected = Signal(int)
    breakpoint_toggled = Signal(int)
    breakpoint_removed = Signal(int)
    goto_source = Signal(str, int)
    
    def __init__(self, debugger: Debugger | None = None, parent=None) -> None:  # type: ignore
        super().__init__(parent)
        self._debugger = debugger or Debugger()
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Debug toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(4, 4, 4, 4)
        toolbar.setSpacing(4)
        
        self.continue_btn = QPushButton("▶ Continue")
        self.continue_btn.clicked.connect(self._on_continue)
        toolbar.addWidget(self.continue_btn)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self._on_pause)
        toolbar.addWidget(self.pause_btn)
        
        self.step_over_btn = QPushButton("⤵ Step Over")
        self.step_over_btn.clicked.connect(self._on_step_over)
        toolbar.addWidget(self.step_over_btn)
        
        self.step_into_btn = QPushButton("↴ Step Into")
        self.step_into_btn.clicked.connect(self._on_step_into)
        toolbar.addWidget(self.step_into_btn)
        
        self.step_out_btn = QPushButton("↱ Step Out")
        self.step_out_btn.clicked.connect(self._on_step_out)
        toolbar.addWidget(self.step_out_btn)
        
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.clicked.connect(self._on_stop)
        toolbar.addWidget(self.stop_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Call Stack tab
        self.stack_widget = self._create_stack_tab()
        self.tabs.addTab(self.stack_widget, "Call Stack")
        
        # Variables tab
        self.variables_widget = self._create_variables_tab()
        self.tabs.addTab(self.variables_widget, "Variables")
        
        # Breakpoints tab
        self.breakpoints_widget = self._create_breakpoints_tab()
        self.tabs.addTab(self.breakpoints_widget, "Breakpoints")
        
        self._apply_style()
        self._update_button_states()
    
    def _create_stack_tab(self) -> QWidget:
        """Create the call stack tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        self.stack_list = QListWidget()
        self.stack_list.itemDoubleClicked.connect(self._on_stack_item_clicked)
        self.stack_list.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                border: 2px inset #808080;
            }
            QListWidget::item:selected {
                background-color: #000080;
                color: #FFFFFF;
            }
        """)
        layout.addWidget(self.stack_list)
        
        return widget
    
    def _create_variables_tab(self) -> QWidget:
        """Create the variables/watch tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Variables tree
        self.variables_tree = QTreeWidget()
        self.variables_tree.setHeaderLabels(["Name", "Value", "Type"])
        self.variables_tree.setColumnWidth(0, 150)
        self.variables_tree.setColumnWidth(1, 200)
        self.variables_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #FFFFFF;
                border: 2px inset #808080;
            }
            QTreeWidget::item:selected {
                background-color: #000080;
                color: #FFFFFF;
            }
        """)
        layout.addWidget(self.variables_tree)
        
        # Watch expression input
        watch_layout = QHBoxLayout()
        self.watch_input = QLineEdit()
        self.watch_input.setPlaceholderText("Enter expression to watch...")
        self.watch_input.returnPressed.connect(self._on_add_watch)
        watch_layout.addWidget(self.watch_input)
        
        add_watch_btn = QPushButton("Add")
        add_watch_btn.clicked.connect(self._on_add_watch)
        watch_layout.addWidget(add_watch_btn)
        
        layout.addLayout(watch_layout)
        
        return widget
    
    def _create_breakpoints_tab(self) -> QWidget:
        """Create the breakpoints tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        self.breakpoints_list = QListWidget()
        self.breakpoints_list.itemDoubleClicked.connect(self._on_breakpoint_clicked)
        self.breakpoints_list.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                border: 2px inset #808080;
            }
            QListWidget::item:selected {
                background-color: #000080;
                color: #FFFFFF;
            }
        """)
        layout.addWidget(self.breakpoints_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        toggle_btn = QPushButton("Toggle")
        toggle_btn.clicked.connect(self._on_toggle_breakpoint)
        btn_layout.addWidget(toggle_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._on_remove_breakpoint)
        btn_layout.addWidget(remove_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._on_clear_breakpoints)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
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
    
    def _update_button_states(self) -> None:
        """Update button enabled states based on debugger state."""
        is_paused = self._debugger.is_paused
        is_running = self._debugger.state.name == "RUNNING"
        
        self.continue_btn.setEnabled(is_paused)
        self.pause_btn.setEnabled(is_running)
        self.step_over_btn.setEnabled(is_paused)
        self.step_into_btn.setEnabled(is_paused)
        self.step_out_btn.setEnabled(is_paused)
        self.stop_btn.setEnabled(is_paused or is_running)
    
    # ─────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────
    
    def set_debugger(self, debugger: Debugger) -> None:
        """Set the debugger instance."""
        self._debugger = debugger
        self._update_button_states()
    
    def update_call_stack(self, frames: list[StackFrame]) -> None:
        """Update the call stack display."""
        self.stack_list.clear()
        
        for frame in reversed(frames):  # Show top frame first
            text = f"{frame.name} at line {frame.line}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, frame.id)
            self.stack_list.addItem(item)
    
    def update_variables(self, variables: list[Variable]) -> None:
        """Update the variables display."""
        self.variables_tree.clear()
        
        for var in variables:
            item = QTreeWidgetItem([var.name, str(var.value), var.type])
            if var.expandable:
                item.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
                )
            self.variables_tree.addTopLevelItem(item)
    
    def update_breakpoints(self, breakpoints: list[Breakpoint]) -> None:
        """Update the breakpoints list."""
        self.breakpoints_list.clear()
        
        for bp in breakpoints:
            text = f"{'●' if bp.enabled else '○'} {bp.file}:{bp.line}"
            if bp.condition:
                text += f" [{bp.condition}]"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, bp.id)
            if not bp.enabled:
                item.setForeground(QColor("#808080"))
            self.breakpoints_list.addItem(item)
    
    def on_paused(self, reason: str, line: int) -> None:
        """Called when debugger pauses."""
        self._update_button_states()
        self.update_call_stack(self._debugger.call_stack)
        self.update_variables(self._debugger.get_variables())
        self.update_breakpoints(self._debugger.breakpoints.get_all())
    
    def on_resumed(self) -> None:
        """Called when debugger resumes."""
        self._update_button_states()
    
    def on_stopped(self) -> None:
        """Called when debugger stops."""
        self._update_button_states()
        self.stack_list.clear()
        self.variables_tree.clear()
    
    # ─────────────────────────────────────────────────────────────
    # Event Handlers
    # ─────────────────────────────────────────────────────────────
    
    def _on_continue(self) -> None:
        """Handle continue button."""
        self._debugger.continue_execution()
    
    def _on_pause(self) -> None:
        """Handle pause button."""
        self._debugger.pause()
    
    def _on_step_over(self) -> None:
        """Handle step over button."""
        self._debugger.step_over()
    
    def _on_step_into(self) -> None:
        """Handle step into button."""
        self._debugger.step_into()
    
    def _on_step_out(self) -> None:
        """Handle step out button."""
        self._debugger.step_out()
    
    def _on_stop(self) -> None:
        """Handle stop button."""
        self._debugger.stop()
    
    def _on_stack_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle stack frame selection."""
        frame_id = item.data(Qt.ItemDataRole.UserRole)
        self.frame_selected.emit(frame_id)
        self.update_variables(self._debugger.get_variables(frame_id))
    
    def _on_add_watch(self) -> None:
        """Handle add watch expression."""
        expr = self.watch_input.text().strip()
        if expr:
            value, error = self._debugger.evaluate(expr)
            if error:
                item = QTreeWidgetItem([expr, f"Error: {error}", ""])
                item.setForeground(1, QColor("#FF0000"))
            else:
                item = QTreeWidgetItem([expr, str(value), type(value).__name__])
            self.variables_tree.addTopLevelItem(item)
            self.watch_input.clear()
    
    def _on_breakpoint_clicked(self, item: QListWidgetItem) -> None:
        """Handle breakpoint double-click."""
        bp_id = item.data(Qt.ItemDataRole.UserRole)
        bp = self._debugger.breakpoints.get(bp_id)
        if bp:
            self.goto_source.emit(bp.file, bp.line)
    
    def _on_toggle_breakpoint(self) -> None:
        """Toggle selected breakpoint."""
        item = self.breakpoints_list.currentItem()
        if item:
            bp_id = item.data(Qt.ItemDataRole.UserRole)
            self._debugger.breakpoints.toggle(bp_id)
            self.breakpoint_toggled.emit(bp_id)
            self.update_breakpoints(self._debugger.breakpoints.get_all())
    
    def _on_remove_breakpoint(self) -> None:
        """Remove selected breakpoint."""
        item = self.breakpoints_list.currentItem()
        if item:
            bp_id = item.data(Qt.ItemDataRole.UserRole)
            self._debugger.breakpoints.remove(bp_id)
            self.breakpoint_removed.emit(bp_id)
            self.update_breakpoints(self._debugger.breakpoints.get_all())
    
    def _on_clear_breakpoints(self) -> None:
        """Clear all breakpoints."""
        self._debugger.breakpoints.clear()
        self.update_breakpoints([])
