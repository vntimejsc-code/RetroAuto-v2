"""
RetroAuto v2 - Win95/98 Style

Qt stylesheet generator for classic Windows 95/98 appearance.

Colors and styling based on classic Windows:
- 3D raised/sunken borders
- Navy blue selection
- MS Sans Serif / Tahoma fonts
- No rounded corners, no transparency
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────
# Color Palette (Win95/98)
# ─────────────────────────────────────────────────────────────

COLORS = {
    # Background colors
    "window": "#C0C0C0",  # Window/ButtonFace/Menu background
    "window_dark": "#808080",  # Darker variant
    "window_text": "#000000",  # Text color
    # Selection
    "highlight": "#0078d4",  # Blue selection
    "highlight_text": "#FFFFFF",  # White text on selection
    # Borders (3D effect)
    "shadow_dark": "#3c3c3c",  # Dark border
    "shadow_light": "#555555",  # Light border
    "border": "#555555",  # Normal border
    # Disabled state
    "gray_text": "#808080",  # Disabled text
    # Editor - DARK THEME
    "editor_bg": "#1e1e1e",  # Dark editor background
    "gutter_bg": "#252526",  # Gutter background
    "line_number": "#858585",  # Line number color
    # Syntax highlighting - BRIGHT for dark background
    "keyword": "#569cd6",  # Light blue for keywords
    "string": "#ce9178",  # Orange/tan for strings
    "comment": "#6a9955",  # Green for comments
    "number": "#b5cea8",  # Light green for numbers
    "function": "#dcdcaa",  # Yellow for function names
}


# ─────────────────────────────────────────────────────────────
# Font Settings
# ─────────────────────────────────────────────────────────────

FONTS = {
    "ui": '"MS Sans Serif", "Tahoma", sans-serif',
    "ui_size": "8pt",
    "code": '"Courier New", "Consolas", monospace',
    "code_size": "10pt",
}


# ─────────────────────────────────────────────────────────────
# Stylesheet Generator
# ─────────────────────────────────────────────────────────────


def generate_stylesheet() -> str:
    """Generate complete Qt stylesheet for Win95/98 look."""

    return f"""
/* ═══════════════════════════════════════════════════════════════
   Win95/98 Classic Theme
   ═══════════════════════════════════════════════════════════════ */

/* Global */
* {{
    font-family: {FONTS["ui"]};
    font-size: {FONTS["ui_size"]};
}}

QWidget {{
    background-color: {COLORS["window"]};
    color: {COLORS["window_text"]};
}}

/* ─────────────────────────────────────────────────────────────
   Main Window
   ───────────────────────────────────────────────────────────── */

QMainWindow {{
    background-color: {COLORS["window"]};
}}

QMainWindow::separator {{
    background-color: {COLORS["window"]};
    width: 4px;
    height: 4px;
}}

/* ─────────────────────────────────────────────────────────────
   Menu Bar
   ───────────────────────────────────────────────────────────── */

QMenuBar {{
    background-color: {COLORS["window"]};
    border-bottom: 1px solid {COLORS["shadow_dark"]};
    padding: 2px;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 2px 8px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS["highlight"]};
    color: {COLORS["highlight_text"]};
}}

QMenu {{
    background-color: {COLORS["window"]};
    border: 2px outset {COLORS["shadow_light"]};
}}

QMenu::item {{
    padding: 4px 20px;
}}

QMenu::item:selected {{
    background-color: {COLORS["highlight"]};
    color: {COLORS["highlight_text"]};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS["shadow_dark"]};
    margin: 4px 2px;
}}

/* ─────────────────────────────────────────────────────────────
   Toolbar
   ───────────────────────────────────────────────────────────── */

QToolBar {{
    background-color: {COLORS["window"]};
    border: none;
    padding: 2px;
    spacing: 2px;
}}

QToolBar::separator {{
    width: 8px;
    background-color: transparent;
}}

QToolButton {{
    background-color: {COLORS["window"]};
    border: 2px outset {COLORS["shadow_light"]};
    padding: 4px 8px;
    min-width: 20px;
}}

QToolButton:hover {{
    background-color: #D4D4D4;
}}

QToolButton:pressed {{
    border: 2px inset {COLORS["shadow_light"]};
    background-color: #B0B0B0;
}}

QToolButton:disabled {{
    color: {COLORS["gray_text"]};
}}

/* ─────────────────────────────────────────────────────────────
   Buttons
   ───────────────────────────────────────────────────────────── */

QPushButton {{
    background-color: {COLORS["window"]};
    border: 2px outset {COLORS["shadow_light"]};
    padding: 4px 12px;
    min-width: 60px;
}}

QPushButton:hover {{
    background-color: #D4D4D4;
}}

QPushButton:pressed {{
    border: 2px inset {COLORS["shadow_light"]};
    background-color: #B0B0B0;
}}

QPushButton:disabled {{
    color: {COLORS["gray_text"]};
}}

QPushButton:default {{
    border: 2px outset {COLORS["shadow_light"]};
    border-color: {COLORS["window_text"]};
}}

/* ─────────────────────────────────────────────────────────────
   Group Box
   ───────────────────────────────────────────────────────────── */

QGroupBox {{
    border: 2px groove {COLORS["shadow_light"]};
    margin-top: 8px;
    padding-top: 8px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    background-color: {COLORS["window"]};
}}

/* ─────────────────────────────────────────────────────────────
   Text Input
   ───────────────────────────────────────────────────────────── */

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS["editor_bg"]};
    border: 2px inset {COLORS["shadow_dark"]};
    padding: 2px;
    selection-background-color: {COLORS["highlight"]};
    selection-color: {COLORS["highlight_text"]};
}}

QLineEdit:disabled, QTextEdit:disabled {{
    background-color: {COLORS["window"]};
    color: {COLORS["gray_text"]};
}}

/* ─────────────────────────────────────────────────────────────
   Combo Box
   ───────────────────────────────────────────────────────────── */

QComboBox {{
    background-color: {COLORS["editor_bg"]};
    border: 2px inset {COLORS["shadow_dark"]};
    padding: 2px 4px;
    min-height: 18px;
}}

QComboBox::drop-down {{
    border: none;
    width: 16px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {COLORS["window_text"]};
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["editor_bg"]};
    border: 1px solid {COLORS["shadow_dark"]};
    selection-background-color: {COLORS["highlight"]};
    selection-color: {COLORS["highlight_text"]};
}}

/* ─────────────────────────────────────────────────────────────
   Spin Box
   ───────────────────────────────────────────────────────────── */

QSpinBox {{
    background-color: {COLORS["editor_bg"]};
    border: 2px inset {COLORS["shadow_dark"]};
    padding: 2px;
}}

/* ─────────────────────────────────────────────────────────────
   Check Box
   ───────────────────────────────────────────────────────────── */

QCheckBox {{
    spacing: 4px;
}}

QCheckBox::indicator {{
    width: 13px;
    height: 13px;
    border: 2px inset {COLORS["shadow_dark"]};
    background-color: {COLORS["editor_bg"]};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS["editor_bg"]};
    image: none;
}}

QCheckBox::indicator:checked::after {{
    content: "✓";
}}

/* ─────────────────────────────────────────────────────────────
   List Widget / Tree Widget
   ───────────────────────────────────────────────────────────── */

QListWidget, QTreeWidget, QListView, QTreeView {{
    background-color: {COLORS["editor_bg"]};
    border: 2px inset {COLORS["shadow_dark"]};
    selection-background-color: {COLORS["highlight"]};
    selection-color: {COLORS["highlight_text"]};
}}

QListWidget::item, QTreeWidget::item {{
    padding: 2px;
    min-height: 18px;
}}

QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {COLORS["highlight"]};
    color: {COLORS["highlight_text"]};
}}

QHeaderView::section {{
    background-color: {COLORS["window"]};
    border: 1px solid {COLORS["shadow_dark"]};
    border-bottom: 1px solid {COLORS["shadow_dark"]};
    padding: 2px 4px;
}}

/* ─────────────────────────────────────────────────────────────
   Tab Widget
   ───────────────────────────────────────────────────────────── */

QTabWidget::pane {{
    border: 2px inset {COLORS["shadow_dark"]};
    background-color: {COLORS["window"]};
}}

QTabBar::tab {{
    background-color: {COLORS["window"]};
    border: 2px outset {COLORS["shadow_light"]};
    border-bottom: none;
    padding: 4px 12px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS["window"]};
    border-bottom: 2px solid {COLORS["window"]};
    margin-bottom: -2px;
}}

QTabBar::tab:!selected {{
    background-color: {COLORS["window_dark"]};
    margin-top: 2px;
}}

/* ─────────────────────────────────────────────────────────────
   Scroll Bar
   ───────────────────────────────────────────────────────────── */

QScrollBar:vertical {{
    background-color: {COLORS["window"]};
    width: 16px;
    border: 1px solid {COLORS["shadow_dark"]};
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS["window"]};
    border: 2px outset {COLORS["shadow_light"]};
    min-height: 20px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    background-color: {COLORS["window"]};
    border: 2px outset {COLORS["shadow_light"]};
    height: 16px;
}}

QScrollBar:horizontal {{
    background-color: {COLORS["window"]};
    height: 16px;
    border: 1px solid {COLORS["shadow_dark"]};
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS["window"]};
    border: 2px outset {COLORS["shadow_light"]};
    min-width: 20px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    background-color: {COLORS["window"]};
    border: 2px outset {COLORS["shadow_light"]};
    width: 16px;
}}

/* ─────────────────────────────────────────────────────────────
   Splitter
   ───────────────────────────────────────────────────────────── */

QSplitter::handle {{
    background-color: {COLORS["window"]};
}}

QSplitter::handle:horizontal {{
    width: 4px;
}}

QSplitter::handle:vertical {{
    height: 4px;
}}

/* ─────────────────────────────────────────────────────────────
   Status Bar
   ───────────────────────────────────────────────────────────── */

QStatusBar {{
    background-color: {COLORS["window"]};
    border-top: 1px solid {COLORS["shadow_dark"]};
}}

QStatusBar::item {{
    border: none;
}}

/* ─────────────────────────────────────────────────────────────
   Dialog
   ───────────────────────────────────────────────────────────── */

QDialog {{
    background-color: {COLORS["window"]};
}}

QDialogButtonBox {{
    button-layout: 0;
}}

/* ─────────────────────────────────────────────────────────────
   Progress Bar
   ───────────────────────────────────────────────────────────── */

QProgressBar {{
    background-color: {COLORS["editor_bg"]};
    border: 2px inset {COLORS["shadow_dark"]};
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS["highlight"]};
}}

/* ─────────────────────────────────────────────────────────────
   Tooltip
   ───────────────────────────────────────────────────────────── */

QToolTip {{
    background-color: #FFFFE1;
    color: {COLORS["window_text"]};
    border: 1px solid {COLORS["window_text"]};
    padding: 2px;
}}
"""


def apply_win95_style(app) -> None:  # type: ignore
    """Apply Win95/98 style to a QApplication."""
    stylesheet = generate_stylesheet()
    app.setStyleSheet(stylesheet)
