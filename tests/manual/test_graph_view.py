"""
Test script for FlowGraphView.
Verifies zoom, pan, and grid rendering.
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from app.ui.graph_view import FlowGraphView


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flow Graph View Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Info label
        info = QLabel("Controls: Scroll = Zoom | Middle Mouse = Pan")
        layout.addWidget(info)
        
        # Zoom level label
        self.zoom_label = QLabel("Zoom: 100%")
        layout.addWidget(self.zoom_label)
        
        # Graph view
        self.graph = FlowGraphView()
        self.graph.zoom_changed.connect(self._on_zoom)
        layout.addWidget(self.graph)
        
    def _on_zoom(self, level: float):
        self.zoom_label.setText(f"Zoom: {level * 100:.0f}%")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Apply dark theme if available
    theme_path = project_root / "app" / "resources" / "dark_theme.qss"
    if theme_path.exists():
        app.setStyleSheet(theme_path.read_text(encoding="utf-8"))
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())
