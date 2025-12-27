"""
RetroAuto v2 - UI Animations

Smooth animations and transitions for enhanced UX.

Features:
- Fade in/out effects
- Slide animations
- Pulse/highlight effects
- Loading spinners
"""

from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    Property,
    QParallelAnimationGroup,
    QSequentialAnimationGroup,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QGraphicsOpacityEffect,
    QLabel,
)


# ═══════════════════════════════════════════════════════════════════════════
# FADE ANIMATIONS
# ═══════════════════════════════════════════════════════════════════════════

def fade_in(widget: QWidget, duration: int = 300) -> QPropertyAnimation:
    """
    Fade in a widget from transparent to opaque.
    
    Args:
        widget: Widget to animate
        duration: Animation duration in ms
    
    Returns:
        The animation object (auto-starts)
    """
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    
    animation = QPropertyAnimation(effect, b"opacity")
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
    animation.start()
    
    return animation


def fade_out(widget: QWidget, duration: int = 300, hide_on_finish: bool = True) -> QPropertyAnimation:
    """
    Fade out a widget from opaque to transparent.
    
    Args:
        widget: Widget to animate
        duration: Animation duration in ms
        hide_on_finish: Whether to hide widget when animation finishes
    
    Returns:
        The animation object (auto-starts)
    """
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    
    animation = QPropertyAnimation(effect, b"opacity")
    animation.setDuration(duration)
    animation.setStartValue(1.0)
    animation.setEndValue(0.0)
    animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
    
    if hide_on_finish:
        animation.finished.connect(widget.hide)
    
    animation.start()
    return animation


# ═══════════════════════════════════════════════════════════════════════════
# PULSE ANIMATION
# ═══════════════════════════════════════════════════════════════════════════

def pulse(widget: QWidget, times: int = 2, duration: int = 200) -> QSequentialAnimationGroup:
    """
    Pulse widget opacity to draw attention.
    
    Args:
        widget: Widget to animate
        times: Number of pulses
        duration: Duration per half-pulse in ms
    
    Returns:
        Animation group (auto-starts)
    """
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    
    group = QSequentialAnimationGroup()
    
    for _ in range(times):
        # Fade out
        fade_out_anim = QPropertyAnimation(effect, b"opacity")
        fade_out_anim.setDuration(duration)
        fade_out_anim.setStartValue(1.0)
        fade_out_anim.setEndValue(0.5)
        fade_out_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        group.addAnimation(fade_out_anim)
        
        # Fade in
        fade_in_anim = QPropertyAnimation(effect, b"opacity")
        fade_in_anim.setDuration(duration)
        fade_in_anim.setStartValue(0.5)
        fade_in_anim.setEndValue(1.0)
        fade_in_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        group.addAnimation(fade_in_anim)
    
    group.start()
    return group


# ═══════════════════════════════════════════════════════════════════════════
# LOADING SPINNER
# ═══════════════════════════════════════════════════════════════════════════

class LoadingSpinner(QLabel):
    """Animated loading spinner widget."""
    
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, text: str = "Loading", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._base_text = text
        self._frame_index = 0
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_frame)
        
        self.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 12px;
            }
        """)
        self._update_text()
    
    def _update_frame(self) -> None:
        self._frame_index = (self._frame_index + 1) % len(self.FRAMES)
        self._update_text()
    
    def _update_text(self) -> None:
        frame = self.FRAMES[self._frame_index]
        self.setText(f"{frame} {self._base_text}")
    
    def start(self, interval: int = 80) -> None:
        """Start spinning animation."""
        self._timer.start(interval)
    
    def stop(self) -> None:
        """Stop spinning animation."""
        self._timer.stop()
    
    def set_text(self, text: str) -> None:
        """Update base text."""
        self._base_text = text
        self._update_text()


# ═══════════════════════════════════════════════════════════════════════════
# STATUS NOTIFICATION
# ═══════════════════════════════════════════════════════════════════════════

class StatusNotification(QLabel):
    """
    Animated status notification that fades in and auto-hides.
    
    Usage:
        notification = StatusNotification(parent)
        notification.show_message("File saved!", 3000)
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._auto_hide)
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 120, 212, 0.9);
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        self.hide()
    
    def show_message(
        self, 
        message: str, 
        duration: int = 3000,
        message_type: str = "info"
    ) -> None:
        """
        Show a notification message.
        
        Args:
            message: Message text
            duration: Auto-hide duration in ms (0 = no auto-hide)
            message_type: "info", "success", "warning", "error"
        """
        colors = {
            "info": "rgba(0, 120, 212, 0.9)",
            "success": "rgba(40, 167, 69, 0.9)",
            "warning": "rgba(255, 152, 0, 0.9)",
            "error": "rgba(220, 53, 69, 0.9)",
        }
        
        bg_color = colors.get(message_type, colors["info"])
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }}
        """)
        
        self.setText(message)
        self.adjustSize()
        
        # Center in parent
        if self.parent():
            parent = self.parent()
            x = (parent.width() - self.width()) // 2
            y = 20
            self.move(x, y)
        
        self.show()
        fade_in(self, 200)
        
        if duration > 0:
            self._timer.start(duration)
    
    def _auto_hide(self) -> None:
        """Auto-hide with fade out."""
        fade_out(self, 300)


# ═══════════════════════════════════════════════════════════════════════════
# HIGHLIGHT EFFECT
# ═══════════════════════════════════════════════════════════════════════════

def highlight_widget(widget: QWidget, color: str = "#0078d4", duration: int = 1000) -> None:
    """
    Temporarily highlight a widget with a colored border.
    
    Args:
        widget: Widget to highlight
        color: Highlight color
        duration: How long to show highlight
    """
    original_style = widget.styleSheet()
    
    # Add highlight border
    widget.setStyleSheet(original_style + f"""
        border: 2px solid {color} !important;
        border-radius: 4px;
    """)
    
    # Restore after duration
    def restore():
        widget.setStyleSheet(original_style)
    
    QTimer.singleShot(duration, restore)


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def smooth_show(widget: QWidget) -> None:
    """Show widget with fade in animation."""
    widget.show()
    fade_in(widget, 200)


def smooth_hide(widget: QWidget) -> None:
    """Hide widget with fade out animation."""
    fade_out(widget, 200, hide_on_finish=True)


def attention(widget: QWidget) -> None:
    """Draw attention to widget with pulse."""
    pulse(widget, times=3, duration=150)
