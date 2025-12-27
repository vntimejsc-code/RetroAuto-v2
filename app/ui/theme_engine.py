"""
RetroAuto v2 - Theme Engine

Multi-theme support with modern and retro options.
Hot-reload capable, system preference detection.

Themes:
- modern_dark: VS Code-inspired dark theme
- modern_light: Clean light theme  
- retro95: Classic Windows 95/98 nostalgia
"""

from __future__ import annotations

from enum import Enum
from typing import Dict
from PySide6.QtCore import QSettings
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication


class ThemeType(Enum):
    """Available theme types."""
    MODERN_DARK = "modern_dark"
    MODERN_LIGHT = "modern_light"
    RETRO_95 = "retro95"
    SYSTEM = "system"  # Auto-detect


# ═══════════════════════════════════════════════════════════════════════════
# COLOR PALETTES
# ═══════════════════════════════════════════════════════════════════════════

THEMES: Dict[str, Dict[str, str]] = {
    "modern_dark": {
        # Backgrounds
        "window": "#1e1e1e",
        "window_alt": "#252526",
        "panel": "#2d2d30",
        "editor": "#1e1e1e",
        "gutter": "#252526",
        "toolbar": "#3c3c3c",
        "menu": "#2d2d30",
        
        # Text
        "text": "#cccccc",
        "text_muted": "#808080",
        "text_disabled": "#5a5a5a",
        
        # Accent
        "accent": "#0078d4",
        "accent_hover": "#1a8cff",
        "accent_text": "#ffffff",
        
        # Borders
        "border": "#3c3c3c",
        "border_light": "#454545",
        "border_focus": "#0078d4",
        
        # Syntax (VSCode Dark+ inspired)
        "keyword": "#569cd6",
        "string": "#ce9178",
        "comment": "#6a9955",
        "number": "#b5cea8",
        "function": "#dcdcaa",
        "variable": "#9cdcfe",
        "type": "#4ec9b0",
        "operator": "#d4d4d4",
        
        # Status
        "success": "#4caf50",
        "warning": "#ff9800",
        "error": "#f44336",
        "info": "#2196f3",
        
        # Selection
        "selection": "#264f78",
        "selection_text": "#ffffff",
        "highlight_line": "#2a2d2e",
    },
    
    "modern_light": {
        # Backgrounds
        "window": "#f3f3f3",
        "window_alt": "#ffffff",
        "panel": "#f8f8f8",
        "editor": "#ffffff",
        "gutter": "#f0f0f0",
        "toolbar": "#e8e8e8",
        "menu": "#f8f8f8",
        
        # Text
        "text": "#1e1e1e",
        "text_muted": "#6e6e6e",
        "text_disabled": "#a0a0a0",
        
        # Accent
        "accent": "#0078d4",
        "accent_hover": "#106ebe",
        "accent_text": "#ffffff",
        
        # Borders
        "border": "#d4d4d4",
        "border_light": "#e5e5e5",
        "border_focus": "#0078d4",
        
        # Syntax (Light theme)
        "keyword": "#0000ff",
        "string": "#a31515",
        "comment": "#008000",
        "number": "#098658",
        "function": "#795e26",
        "variable": "#001080",
        "type": "#267f99",
        "operator": "#000000",
        
        # Status
        "success": "#4caf50",
        "warning": "#ff9800",
        "error": "#f44336",
        "info": "#2196f3",
        
        # Selection
        "selection": "#add6ff",
        "selection_text": "#000000",
        "highlight_line": "#f5f5f5",
    },
    
    "retro95": {
        # Classic Win95/98 colors
        "window": "#c0c0c0",
        "window_alt": "#ffffff",
        "panel": "#c0c0c0",
        "editor": "#1e1e1e",
        "gutter": "#252526",
        "toolbar": "#c0c0c0",
        "menu": "#c0c0c0",
        
        # Text
        "text": "#000000",
        "text_muted": "#808080",
        "text_disabled": "#808080",
        
        # Accent
        "accent": "#000080",
        "accent_hover": "#0000a0",
        "accent_text": "#ffffff",
        
        # Borders (3D effect)
        "border": "#808080",
        "border_light": "#ffffff",
        "border_dark": "#404040",
        "border_focus": "#000080",
        
        # Syntax
        "keyword": "#569cd6",
        "string": "#ce9178",
        "comment": "#6a9955",
        "number": "#b5cea8",
        "function": "#dcdcaa",
        "variable": "#9cdcfe",
        "type": "#4ec9b0",
        "operator": "#d4d4d4",
        
        # Status
        "success": "#008000",
        "warning": "#ff8c00",
        "error": "#ff0000",
        "info": "#0000ff",
        
        # Selection
        "selection": "#000080",
        "selection_text": "#ffffff",
        "highlight_line": "#2a2d2e",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# FONT SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

FONTS = {
    "modern": {
        "ui": '"Segoe UI", "Roboto", sans-serif',
        "ui_size": "9pt",
        "code": '"Cascadia Code", "Fira Code", "Consolas", monospace',
        "code_size": "10pt",
    },
    "retro": {
        "ui": '"MS Sans Serif", "Tahoma", sans-serif',
        "ui_size": "8pt",
        "code": '"Courier New", "Consolas", monospace',
        "code_size": "10pt",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# STYLESHEET GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

def generate_stylesheet(theme_name: str = "modern_dark") -> str:
    """Generate Qt stylesheet for the specified theme."""
    
    if theme_name not in THEMES:
        theme_name = "modern_dark"
    
    c = THEMES[theme_name]
    is_retro = theme_name == "retro95"
    f = FONTS["retro"] if is_retro else FONTS["modern"]
    
    # Border style differs between modern (flat) and retro (3D)
    if is_retro:
        border_style = f"2px outset {c.get('border_light', c['border'])}"
        border_pressed = f"2px inset {c.get('border_dark', c['border'])}"
        input_border = f"2px inset {c.get('border_dark', c['border'])}"
    else:
        border_style = f"1px solid {c['border']}"
        border_pressed = f"1px solid {c['accent']}"
        input_border = f"1px solid {c['border']}"

    return f"""
/* ═══════════════════════════════════════════════════════════════
   Theme: {theme_name}
   Generated by RetroAuto Theme Engine
   ═══════════════════════════════════════════════════════════════ */

/* Global */
* {{
    font-family: {f["ui"]};
    font-size: {f["ui_size"]};
}}

QWidget {{
    background-color: {c["window"]};
    color: {c["text"]};
}}

/* ─────────────────────────────────────────────────────────────
   Main Window
   ───────────────────────────────────────────────────────────── */

QMainWindow {{
    background-color: {c["window"]};
}}

QMainWindow::separator {{
    background-color: {c["border"]};
    width: 4px;
    height: 4px;
}}

QMainWindow::separator:hover {{
    background-color: {c["accent"]};
}}

/* ─────────────────────────────────────────────────────────────
   Menu Bar
   ───────────────────────────────────────────────────────────── */

QMenuBar {{
    background-color: {c["menu"]};
    border-bottom: 1px solid {c["border"]};
    padding: 2px;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 4px 8px;
    border-radius: {"0" if is_retro else "4px"};
}}

QMenuBar::item:selected {{
    background-color: {c["accent"]};
    color: {c["accent_text"]};
}}

QMenu {{
    background-color: {c["menu"]};
    border: 1px solid {c["border"]};
    border-radius: {"0" if is_retro else "4px"};
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px;
    border-radius: {"0" if is_retro else "4px"};
}}

QMenu::item:selected {{
    background-color: {c["accent"]};
    color: {c["accent_text"]};
}}

QMenu::separator {{
    height: 1px;
    background-color: {c["border"]};
    margin: 4px 8px;
}}

/* ─────────────────────────────────────────────────────────────
   Toolbar
   ───────────────────────────────────────────────────────────── */

QToolBar {{
    background-color: {c["toolbar"]};
    border: none;
    padding: 4px;
    spacing: 4px;
}}

QToolButton {{
    background-color: transparent;
    border: {border_style if is_retro else "none"};
    padding: 6px 10px;
    border-radius: {"0" if is_retro else "4px"};
}}

QToolButton:hover {{
    background-color: {c["accent"]};
    color: {c["accent_text"]};
}}

QToolButton:pressed {{
    border: {border_pressed};
    background-color: {c["accent_hover"]};
}}

/* ─────────────────────────────────────────────────────────────
   Buttons
   ───────────────────────────────────────────────────────────── */

QPushButton {{
    background-color: {c["panel"]};
    border: {border_style};
    padding: 6px 16px;
    min-width: 60px;
    border-radius: {"0" if is_retro else "4px"};
}}

QPushButton:hover {{
    background-color: {c["accent"]};
    color: {c["accent_text"]};
    border-color: {c["accent"]};
}}

QPushButton:pressed {{
    border: {border_pressed};
    background-color: {c["accent_hover"]};
}}

QPushButton:disabled {{
    color: {c["text_disabled"]};
    background-color: {c["window"]};
}}

/* ─────────────────────────────────────────────────────────────
   Text Input
   ───────────────────────────────────────────────────────────── */

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {c["editor"]};
    color: {c["text"]};
    border: {input_border};
    padding: 4px;
    border-radius: {"0" if is_retro else "4px"};
    selection-background-color: {c["selection"]};
    selection-color: {c["selection_text"]};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {c["border_focus"]};
}}

/* ─────────────────────────────────────────────────────────────
   Lists and Trees
   ───────────────────────────────────────────────────────────── */

QListWidget, QTreeWidget, QListView, QTreeView {{
    background-color: {c["editor"]};
    border: {input_border};
    border-radius: {"0" if is_retro else "4px"};
    outline: none;
}}

QListWidget::item, QTreeWidget::item {{
    padding: 4px;
    border-radius: {"0" if is_retro else "2px"};
}}

QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {c["selection"]};
    color: {c["selection_text"]};
}}

QListWidget::item:hover, QTreeWidget::item:hover {{
    background-color: {c["highlight_line"]};
}}

QHeaderView::section {{
    background-color: {c["toolbar"]};
    border: 1px solid {c["border"]};
    padding: 4px 8px;
}}

/* ─────────────────────────────────────────────────────────────
   Tab Widget
   ───────────────────────────────────────────────────────────── */

QTabWidget::pane {{
    border: 1px solid {c["border"]};
    background-color: {c["panel"]};
    border-radius: {"0" if is_retro else "4px"};
}}

QTabBar::tab {{
    background-color: {c["window"]};
    border: 1px solid {c["border"]};
    border-bottom: none;
    padding: 6px 16px;
    margin-right: 2px;
    border-top-left-radius: {"0" if is_retro else "4px"};
    border-top-right-radius: {"0" if is_retro else "4px"};
}}

QTabBar::tab:selected {{
    background-color: {c["panel"]};
    border-bottom: 2px solid {c["accent"]};
}}

QTabBar::tab:hover:!selected {{
    background-color: {c["highlight_line"]};
}}

/* ─────────────────────────────────────────────────────────────
   Scroll Bar
   ───────────────────────────────────────────────────────────── */

QScrollBar:vertical {{
    background-color: {c["window"]};
    width: {"16px" if is_retro else "12px"};
    border: {"1px solid " + c["border"] if is_retro else "none"};
}}

QScrollBar::handle:vertical {{
    background-color: {c["toolbar"] if is_retro else c["border_light"]};
    border: {border_style if is_retro else "none"};
    min-height: 20px;
    border-radius: {"0" if is_retro else "6px"};
    margin: {"0" if is_retro else "2px"};
}}

QScrollBar::handle:vertical:hover {{
    background-color: {c["accent"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: {"16px" if is_retro else "0"};
    background-color: {c["window"] if is_retro else "transparent"};
    border: {border_style if is_retro else "none"};
}}

QScrollBar:horizontal {{
    background-color: {c["window"]};
    height: {"16px" if is_retro else "12px"};
    border: {"1px solid " + c["border"] if is_retro else "none"};
}}

QScrollBar::handle:horizontal {{
    background-color: {c["toolbar"] if is_retro else c["border_light"]};
    border: {border_style if is_retro else "none"};
    min-width: 20px;
    border-radius: {"0" if is_retro else "6px"};
    margin: {"0" if is_retro else "2px"};
}}

/* ─────────────────────────────────────────────────────────────
   Dock Widget
   ───────────────────────────────────────────────────────────── */

QDockWidget {{
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

QDockWidget::title {{
    background-color: {c["toolbar"]};
    padding: 6px;
    border-bottom: 1px solid {c["border"]};
}}

QDockWidget::close-button, QDockWidget::float-button {{
    border: none;
    background: transparent;
    padding: 2px;
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background-color: {c["accent"]};
}}

/* ─────────────────────────────────────────────────────────────
   Status Bar
   ───────────────────────────────────────────────────────────── */

QStatusBar {{
    background-color: {c["toolbar"]};
    border-top: 1px solid {c["border"]};
}}

QStatusBar::item {{
    border: none;
}}

/* ─────────────────────────────────────────────────────────────
   Tooltip
   ───────────────────────────────────────────────────────────── */

QToolTip {{
    background-color: {c["panel"]};
    color: {c["text"]};
    border: 1px solid {c["border"]};
    padding: 4px 8px;
    border-radius: {"0" if is_retro else "4px"};
}}

/* ─────────────────────────────────────────────────────────────
   ComboBox
   ───────────────────────────────────────────────────────────── */

QComboBox {{
    background-color: {c["editor"]};
    border: {input_border};
    padding: 4px 8px;
    border-radius: {"0" if is_retro else "4px"};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {c["text"]};
}}

QComboBox QAbstractItemView {{
    background-color: {c["editor"]};
    border: 1px solid {c["border"]};
    selection-background-color: {c["selection"]};
}}

/* ─────────────────────────────────────────────────────────────
   Progress Bar
   ───────────────────────────────────────────────────────────── */

QProgressBar {{
    background-color: {c["editor"]};
    border: {input_border};
    border-radius: {"0" if is_retro else "4px"};
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {c["accent"]};
    border-radius: {"0" if is_retro else "2px"};
}}

/* ─────────────────────────────────────────────────────────────
   SpinBox
   ───────────────────────────────────────────────────────────── */

QSpinBox, QDoubleSpinBox {{
    background-color: {c["editor"]};
    border: {input_border};
    padding: 4px;
    border-radius: {"0" if is_retro else "4px"};
}}

/* ─────────────────────────────────────────────────────────────
   Checkbox & Radio
   ───────────────────────────────────────────────────────────── */

QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: {input_border};
    background-color: {c["editor"]};
    border-radius: {"0" if is_retro else "3px"};
}}

QCheckBox::indicator:checked {{
    background-color: {c["accent"]};
    border-color: {c["accent"]};
}}

QRadioButton::indicator {{
    border-radius: 8px;
}}

QRadioButton::indicator:checked {{
    background-color: {c["accent"]};
    border-color: {c["accent"]};
}}

/* ─────────────────────────────────────────────────────────────
   Group Box
   ───────────────────────────────────────────────────────────── */

QGroupBox {{
    border: {"2px groove " + c.get("border_light", c["border"]) if is_retro else "1px solid " + c["border"]};
    margin-top: 12px;
    padding-top: 8px;
    border-radius: {"0" if is_retro else "4px"};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: {c["window"]};
}}

/* ─────────────────────────────────────────────────────────────
   Splitter
   ───────────────────────────────────────────────────────────── */

QSplitter::handle {{
    background-color: {c["border"]};
}}

QSplitter::handle:hover {{
    background-color: {c["accent"]};
}}

QSplitter::handle:horizontal {{
    width: 4px;
}}

QSplitter::handle:vertical {{
    height: 4px;
}}
"""


# ═══════════════════════════════════════════════════════════════════════════
# THEME MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class ThemeManager:
    """Manages theme switching and persistence."""
    
    SETTINGS_KEY = "appearance/theme"
    
    def __init__(self):
        self._current_theme = ThemeType.MODERN_DARK
        self._settings = QSettings("RetroAuto", "RetroAuto")
        self._load_saved_theme()
    
    def _load_saved_theme(self) -> None:
        """Load saved theme from settings."""
        saved = self._settings.value(self.SETTINGS_KEY, "modern_dark")
        try:
            self._current_theme = ThemeType(saved)
        except ValueError:
            self._current_theme = ThemeType.MODERN_DARK
    
    @property
    def current_theme(self) -> ThemeType:
        """Get current theme."""
        return self._current_theme
    
    @property
    def current_theme_name(self) -> str:
        """Get current theme name for display."""
        names = {
            ThemeType.MODERN_DARK: "Modern Dark",
            ThemeType.MODERN_LIGHT: "Modern Light",
            ThemeType.RETRO_95: "Retro 95",
            ThemeType.SYSTEM: "System",
        }
        return names.get(self._current_theme, "Modern Dark")
    
    def set_theme(self, theme: ThemeType) -> None:
        """Set and apply theme."""
        self._current_theme = theme
        self._settings.setValue(self.SETTINGS_KEY, theme.value)
        self.apply_theme()
    
    def apply_theme(self) -> None:
        """Apply current theme to application."""
        app = QApplication.instance()
        if not app:
            return
        
        theme_name = self._current_theme.value
        
        # Handle system theme
        if theme_name == "system":
            # Detect system preference (simplified)
            palette = app.palette()
            is_dark = palette.color(QPalette.ColorRole.Window).lightness() < 128
            theme_name = "modern_dark" if is_dark else "modern_light"
        
        stylesheet = generate_stylesheet(theme_name)
        app.setStyleSheet(stylesheet)
    
    def get_colors(self) -> Dict[str, str]:
        """Get color palette for current theme."""
        theme_name = self._current_theme.value
        if theme_name == "system":
            theme_name = "modern_dark"  # Default
        return THEMES.get(theme_name, THEMES["modern_dark"])
    
    def get_syntax_colors(self) -> Dict[str, str]:
        """Get syntax highlighting colors."""
        colors = self.get_colors()
        return {
            "keyword": colors.get("keyword", "#569cd6"),
            "string": colors.get("string", "#ce9178"),
            "comment": colors.get("comment", "#6a9955"),
            "number": colors.get("number", "#b5cea8"),
            "function": colors.get("function", "#dcdcaa"),
            "variable": colors.get("variable", "#9cdcfe"),
            "type": colors.get("type", "#4ec9b0"),
            "operator": colors.get("operator", "#d4d4d4"),
        }


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

# Global theme manager instance
_theme_manager: ThemeManager | None = None


def get_theme_manager() -> ThemeManager:
    """Get global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def apply_theme(app: QApplication, theme: ThemeType | str = ThemeType.MODERN_DARK) -> None:
    """Apply theme to application."""
    manager = get_theme_manager()
    if isinstance(theme, str):
        try:
            theme = ThemeType(theme)
        except ValueError:
            theme = ThemeType.MODERN_DARK
    manager.set_theme(theme)


def get_available_themes() -> list[tuple[str, str]]:
    """Get list of available themes (value, display_name)."""
    return [
        (ThemeType.MODERN_DARK.value, "Modern Dark"),
        (ThemeType.MODERN_LIGHT.value, "Modern Light"),
        (ThemeType.RETRO_95.value, "Retro 95 (Classic)"),
        (ThemeType.SYSTEM.value, "System (Auto)"),
    ]
