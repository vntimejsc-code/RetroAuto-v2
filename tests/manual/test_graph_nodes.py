"""
Test script for Node Rendering.
Creates sample nodes to verify visual appearance.
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from app.ui.graph_view import FlowGraphView
from app.ui.graph_node import NodeItem
from core.models import ClickImage, WaitImage, Delay, IfImage, Hotkey, ReadText, Loop


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Node Rendering Test")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Controls
        controls = QHBoxLayout()
        
        info = QLabel("Controls: Scroll=Zoom | MidMouse=Pan | LeftClick=Select | DRAG FROM RIGHT SOCKET TO LEFT SOCKET TO WIRE")
        controls.addWidget(info)
        
        self.zoom_label = QLabel("Zoom: 100%")
        controls.addWidget(self.zoom_label)
        
        # Add node button
        add_btn = QPushButton("Add Sample Nodes")
        add_btn.clicked.connect(self._add_sample_nodes)
        controls.addWidget(add_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear)
        controls.addWidget(clear_btn)
        
        layout.addLayout(controls)
        
        # Graph view
        self.graph = FlowGraphView()
        self.graph.zoom_changed.connect(self._on_zoom)
        layout.addWidget(self.graph)
        
        # Add initial samples
        self._add_sample_nodes()
        
    def _on_zoom(self, level: float):
        self.zoom_label.setText(f"Zoom: {level * 100:.0f}%")
    
    def _add_sample_nodes(self):
        """Add sample nodes to demonstrate different action types."""
        # Create sample actions
        samples = [
            (ClickImage(asset_id="button_ok"), -300, -100),
            (WaitImage(asset_id="loading"), -300, 50),
            (IfImage(asset_id="error"), 0, -100),
            (ReadText(variable_name="$hp", roi={"x": 0, "y": 0, "w": 100, "h": 30}), 0, 50),
            (Delay(ms=1000), 300, -100),
            (Hotkey(keys=["CTRL", "C"]), 300, 50),
            (Loop(iterations=5), 0, 200),
        ]
        
        for action, x, y in samples:
            node = NodeItem(action, x, y)
            self.graph.scene.addItem(node)
    
    def _clear(self):
        """Clear all nodes."""
        self.graph.scene.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Apply dark theme
    theme_path = project_root / "app" / "resources" / "dark_theme.qss"
    if theme_path.exists():
        app.setStyleSheet(theme_path.read_text(encoding="utf-8"))
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())
