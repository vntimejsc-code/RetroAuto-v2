"""
RetroAuto v2 - Inspector Panel

Win95-style property inspector for:
- Script properties
- Asset properties
- Action properties
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QScrollArea,
)


class InspectorPanel(QWidget):
    """
    Property inspector panel with Win95 styling.
    
    Displays and edits properties of:
    - Scripts (metadata)
    - Assets (threshold, ROI)
    - Actions (parameters)
    
    Signals:
        property_changed: Emitted when any property changes (key, value)
    """

    property_changed = Signal(str, object)

    def __init__(self, parent=None) -> None:  # type: ignore
        super().__init__(parent)
        self._init_ui()
        self._current_data: dict[str, Any] = {}

    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Title
        self.title_label = QLabel("Inspector")
        self.title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                padding: 4px;
                background-color: #000080;
                color: #FFFFFF;
            }
        """)
        layout.addWidget(self.title_label)

        # Scroll area for properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 2px inset #808080;
                background-color: #C0C0C0;
            }
        """)
        
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.content)
        layout.addWidget(scroll)

        # Empty state
        self._show_empty_state()

    def _show_empty_state(self) -> None:
        """Show empty state message."""
        self._clear_content()
        label = QLabel("No selection")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #808080;")
        self.content_layout.addWidget(label)

    def _clear_content(self) -> None:
        """Clear all content widgets."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ─────────────────────────────────────────────────────────────
    # Script Properties
    # ─────────────────────────────────────────────────────────────

    def show_script_properties(self, data: dict[str, Any]) -> None:
        """Display script metadata properties."""
        self._clear_content()
        self._current_data = data
        self.title_label.setText("📄 Script Properties")

        # Metadata group
        group = QGroupBox("Metadata")
        form = QFormLayout(group)
        
        name_edit = QLineEdit(data.get("name", ""))
        name_edit.textChanged.connect(lambda v: self._emit_change("name", v))
        form.addRow("Name:", name_edit)
        
        version_edit = QLineEdit(data.get("version", "1.0"))
        version_edit.textChanged.connect(lambda v: self._emit_change("version", v))
        form.addRow("Version:", version_edit)
        
        author_edit = QLineEdit(data.get("author", ""))
        author_edit.textChanged.connect(lambda v: self._emit_change("author", v))
        form.addRow("Author:", author_edit)
        
        self.content_layout.addWidget(group)

        # Hotkeys group
        hotkeys_group = QGroupBox("Hotkeys")
        hotkeys_form = QFormLayout(hotkeys_group)
        
        hotkeys = data.get("hotkeys", {})
        
        start_edit = QLineEdit(hotkeys.get("start", "F5"))
        start_edit.textChanged.connect(lambda v: self._emit_change("hotkeys.start", v))
        hotkeys_form.addRow("Start:", start_edit)
        
        stop_edit = QLineEdit(hotkeys.get("stop", "F6"))
        stop_edit.textChanged.connect(lambda v: self._emit_change("hotkeys.stop", v))
        hotkeys_form.addRow("Stop:", stop_edit)
        
        pause_edit = QLineEdit(hotkeys.get("pause", "F7"))
        pause_edit.textChanged.connect(lambda v: self._emit_change("hotkeys.pause", v))
        hotkeys_form.addRow("Pause:", pause_edit)
        
        self.content_layout.addWidget(hotkeys_group)
        self.content_layout.addStretch()

    # ─────────────────────────────────────────────────────────────
    # Asset Properties
    # ─────────────────────────────────────────────────────────────

    def show_asset_properties(self, data: dict[str, Any]) -> None:
        """Display asset properties."""
        self._clear_content()
        self._current_data = data
        self.title_label.setText("🖼️ Asset Properties")

        group = QGroupBox("Image Asset")
        form = QFormLayout(group)
        
        # ID
        id_edit = QLineEdit(data.get("id", ""))
        id_edit.textChanged.connect(lambda v: self._emit_change("id", v))
        form.addRow("ID:", id_edit)
        
        # Path (read-only)
        path_label = QLabel(data.get("path", ""))
        path_label.setStyleSheet("color: #808080;")
        form.addRow("Path:", path_label)
        
        # Threshold
        threshold_spin = QDoubleSpinBox()
        threshold_spin.setRange(0.0, 1.0)
        threshold_spin.setSingleStep(0.05)
        threshold_spin.setValue(data.get("threshold", 0.8))
        threshold_spin.valueChanged.connect(lambda v: self._emit_change("threshold", v))
        form.addRow("Threshold:", threshold_spin)
        
        self.content_layout.addWidget(group)

        # ROI group
        roi = data.get("roi", {})
        if roi:
            roi_group = QGroupBox("Region of Interest")
            roi_form = QFormLayout(roi_group)
            
            x_spin = QSpinBox()
            x_spin.setRange(0, 9999)
            x_spin.setValue(roi.get("x", 0))
            x_spin.valueChanged.connect(lambda v: self._emit_change("roi.x", v))
            roi_form.addRow("X:", x_spin)
            
            y_spin = QSpinBox()
            y_spin.setRange(0, 9999)
            y_spin.setValue(roi.get("y", 0))
            y_spin.valueChanged.connect(lambda v: self._emit_change("roi.y", v))
            roi_form.addRow("Y:", y_spin)
            
            w_spin = QSpinBox()
            w_spin.setRange(0, 9999)
            w_spin.setValue(roi.get("width", 0))
            w_spin.valueChanged.connect(lambda v: self._emit_change("roi.width", v))
            roi_form.addRow("Width:", w_spin)
            
            h_spin = QSpinBox()
            h_spin.setRange(0, 9999)
            h_spin.setValue(roi.get("height", 0))
            h_spin.valueChanged.connect(lambda v: self._emit_change("roi.height", v))
            roi_form.addRow("Height:", h_spin)
            
            self.content_layout.addWidget(roi_group)

        self.content_layout.addStretch()

    # ─────────────────────────────────────────────────────────────
    # Action Properties
    # ─────────────────────────────────────────────────────────────

    def show_action_properties(self, action_type: str, data: dict[str, Any]) -> None:
        """Display action properties based on type."""
        self._clear_content()
        self._current_data = data
        self.title_label.setText(f"⚡ {action_type}")

        group = QGroupBox("Parameters")
        form = QFormLayout(group)

        # Common action fields based on type
        if action_type == "wait_image":
            self._add_asset_field(form, data)
            self._add_timeout_field(form, data)
            self._add_bool_field(form, "appear", data.get("appear", True))
            
        elif action_type == "click":
            self._add_position_fields(form, data)
            self._add_button_field(form, data)
            
        elif action_type == "type_text":
            text_edit = QLineEdit(data.get("text", ""))
            text_edit.textChanged.connect(lambda v: self._emit_change("text", v))
            form.addRow("Text:", text_edit)
            
            self._add_bool_field(form, "paste", data.get("paste", False))
            self._add_bool_field(form, "enter", data.get("enter", False))
            
        elif action_type == "sleep":
            duration_spin = QSpinBox()
            duration_spin.setRange(0, 999999)
            duration_spin.setSuffix(" ms")
            duration_spin.setValue(data.get("duration_ms", 1000))
            duration_spin.valueChanged.connect(lambda v: self._emit_change("duration_ms", v))
            form.addRow("Duration:", duration_spin)
            
        elif action_type == "run_flow":
            flow_edit = QLineEdit(data.get("flow_name", ""))
            flow_edit.textChanged.connect(lambda v: self._emit_change("flow_name", v))
            form.addRow("Flow:", flow_edit)
            
        elif action_type == "goto":
            label_edit = QLineEdit(data.get("target", ""))
            label_edit.textChanged.connect(lambda v: self._emit_change("target", v))
            form.addRow("Label:", label_edit)

        self.content_layout.addWidget(group)
        self.content_layout.addStretch()

    def _add_asset_field(self, form: QFormLayout, data: dict) -> None:
        """Add asset ID field."""
        asset_edit = QLineEdit(data.get("asset_id", ""))
        asset_edit.textChanged.connect(lambda v: self._emit_change("asset_id", v))
        form.addRow("Asset:", asset_edit)

    def _add_timeout_field(self, form: QFormLayout, data: dict) -> None:
        """Add timeout field."""
        timeout_spin = QSpinBox()
        timeout_spin.setRange(0, 999999)
        timeout_spin.setSuffix(" ms")
        timeout_spin.setValue(data.get("timeout_ms", 5000))
        timeout_spin.valueChanged.connect(lambda v: self._emit_change("timeout_ms", v))
        form.addRow("Timeout:", timeout_spin)

    def _add_position_fields(self, form: QFormLayout, data: dict) -> None:
        """Add X/Y position fields."""
        x_spin = QSpinBox()
        x_spin.setRange(0, 9999)
        x_spin.setValue(data.get("x", 0))
        x_spin.valueChanged.connect(lambda v: self._emit_change("x", v))
        form.addRow("X:", x_spin)
        
        y_spin = QSpinBox()
        y_spin.setRange(0, 9999)
        y_spin.setValue(data.get("y", 0))
        y_spin.valueChanged.connect(lambda v: self._emit_change("y", v))
        form.addRow("Y:", y_spin)

    def _add_button_field(self, form: QFormLayout, data: dict) -> None:
        """Add mouse button field."""
        button_combo = QComboBox()
        button_combo.addItems(["left", "right", "middle"])
        button_combo.setCurrentText(data.get("button", "left"))
        button_combo.currentTextChanged.connect(lambda v: self._emit_change("button", v))
        form.addRow("Button:", button_combo)

    def _add_bool_field(self, form: QFormLayout, name: str, value: bool) -> None:
        """Add boolean checkbox field."""
        checkbox = QCheckBox()
        checkbox.setChecked(value)
        checkbox.stateChanged.connect(lambda s: self._emit_change(name, s == Qt.CheckState.Checked.value))
        form.addRow(f"{name.title()}:", checkbox)

    def _emit_change(self, key: str, value: Any) -> None:
        """Emit property change signal."""
        self.property_changed.emit(key, value)

    def clear(self) -> None:
        """Clear the inspector."""
        self._show_empty_state()
        self.title_label.setText("Inspector")
