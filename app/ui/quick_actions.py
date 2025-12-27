"""
RetroAuto v2 - Quick Actions Toolbar

Floating toolbar with essential quick actions always visible.
Run/Pause/Stop controls with visual state indicators.

Features:
- Always-visible execution controls
- Visual state indicators (running/paused/stopped)
- Keyboard shortcuts displayed
- Optional floating mode
"""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QSizePolicy,
)


class ExecutionState(Enum):
    """Script execution states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


# ═══════════════════════════════════════════════════════════════════════════
# QUICK ACTION BUTTON
# ═══════════════════════════════════════════════════════════════════════════

class QuickActionButton(QPushButton):
    """Styled button for quick actions."""
    
    def __init__(
        self, 
        icon: str, 
        label: str, 
        shortcut: str = "", 
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._icon = icon
        self._label = label
        self._shortcut = shortcut
        self._init_ui()
    
    def _init_ui(self) -> None:
        self.setText(f"{self._icon} {self._label}")
        self.setToolTip(f"{self._label} ({self._shortcut})" if self._shortcut else self._label)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(80)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        
        # Default style
        self.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #5a5a5a;
            }
        """)
    
    def set_active(self, active: bool) -> None:
        """Set button active state with visual indicator."""
        if active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1a8cff;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
            """)
        else:
            self._init_ui()


class RunButton(QuickActionButton):
    """Run button with state-aware styling."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("▶", "Run", "F5", parent)
        self._apply_run_style()
    
    def _apply_run_style(self) -> None:
        self.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34c759;
            }
            QPushButton:pressed {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #5a5a5a;
            }
        """)


class StopButton(QuickActionButton):
    """Stop button with state-aware styling."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("⏹", "Stop", "Shift+F5", parent)
        self._apply_stop_style()
    
    def _apply_stop_style(self) -> None:
        self.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff4757;
            }
            QPushButton:pressed {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #5a5a5a;
            }
        """)


# ═══════════════════════════════════════════════════════════════════════════
# QUICK ACTIONS TOOLBAR
# ═══════════════════════════════════════════════════════════════════════════

class QuickActionsToolbar(QFrame):
    """
    Quick actions toolbar with execution controls.
    
    Signals:
        run_requested: Run button clicked
        pause_requested: Pause button clicked
        stop_requested: Stop button clicked
        capture_requested: Capture button clicked
    """
    
    # Signals
    run_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()
    capture_requested = Signal()
    save_requested = Signal()
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state = ExecutionState.IDLE
        self._init_ui()
    
    def _init_ui(self) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("QuickActionsToolbar")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Execution controls group
        exec_frame = QFrame()
        exec_layout = QHBoxLayout(exec_frame)
        exec_layout.setContentsMargins(0, 0, 0, 0)
        exec_layout.setSpacing(6)
        
        # Run button
        self.run_btn = RunButton()
        self.run_btn.clicked.connect(self.run_requested.emit)
        exec_layout.addWidget(self.run_btn)
        
        # Pause button
        self.pause_btn = QuickActionButton("⏸", "Pause", "F6")
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        self.pause_btn.setEnabled(False)
        exec_layout.addWidget(self.pause_btn)
        
        # Stop button
        self.stop_btn = StopButton()
        self.stop_btn.clicked.connect(self.stop_requested.emit)
        self.stop_btn.setEnabled(False)
        exec_layout.addWidget(self.stop_btn)
        
        layout.addWidget(exec_frame)
        
        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("background-color: #3c3c3c;")
        sep1.setFixedWidth(2)
        layout.addWidget(sep1)
        
        # Capture button
        self.capture_btn = QuickActionButton("📷", "Capture", "F3")
        self.capture_btn.clicked.connect(self.capture_requested.emit)
        layout.addWidget(self.capture_btn)
        
        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("background-color: #3c3c3c;")
        sep2.setFixedWidth(2)
        layout.addWidget(sep2)
        
        # Save button
        self.save_btn = QuickActionButton("💾", "Save", "Ctrl+S")
        self.save_btn.clicked.connect(self.save_requested.emit)
        layout.addWidget(self.save_btn)
        
        # Status indicator
        layout.addStretch()
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #28a745;
                font-weight: bold;
                padding: 4px 8px;
                background-color: rgba(40, 167, 69, 0.1);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Apply toolbar style
        self.setStyleSheet("""
            #QuickActionsToolbar {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
            }
        """)
    
    def _on_pause_clicked(self) -> None:
        """Handle pause/resume toggle."""
        if self._state == ExecutionState.RUNNING:
            self.pause_requested.emit()
        elif self._state == ExecutionState.PAUSED:
            self.run_requested.emit()
    
    def set_state(self, state: ExecutionState) -> None:
        """Update toolbar state and button availability."""
        self._state = state
        
        if state == ExecutionState.IDLE:
            self.run_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.pause_btn.setText("⏸ Pause")
            self._set_status("Ready", "#28a745")
            
        elif state == ExecutionState.RUNNING:
            self.run_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.pause_btn.setText("⏸ Pause")
            self._set_status("Running...", "#0078d4")
            
        elif state == ExecutionState.PAUSED:
            self.run_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.pause_btn.setText("▶ Resume")
            self.pause_btn.set_active(True)
            self._set_status("Paused", "#ff9800")
            
        elif state == ExecutionState.ERROR:
            self.run_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.pause_btn.setText("⏸ Pause")
            self._set_status("Error", "#dc3545")
    
    def _set_status(self, text: str, color: str) -> None:
        """Update status label."""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-weight: bold;
                padding: 4px 8px;
                background-color: rgba({self._hex_to_rgb(color)}, 0.1);
                border-radius: 4px;
            }}
        """)
    
    def _hex_to_rgb(self, hex_color: str) -> str:
        """Convert hex color to RGB string."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"
    
    def set_running(self) -> None:
        """Convenience: Set running state."""
        self.set_state(ExecutionState.RUNNING)
    
    def set_paused(self) -> None:
        """Convenience: Set paused state."""
        self.set_state(ExecutionState.PAUSED)
    
    def set_idle(self) -> None:
        """Convenience: Set idle state."""
        self.set_state(ExecutionState.IDLE)
    
    def set_error(self) -> None:
        """Convenience: Set error state."""
        self.set_state(ExecutionState.ERROR)
