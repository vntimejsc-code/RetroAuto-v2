"""
RetroAuto v2 - Properties Panel

Dynamic form for editing action properties.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.models import (
    Click,
    ClickImage,
    ClickUntil,
    ClickRandom,  # Add import
    Delay,
    Goto,
    Hotkey,
    IfImage,
    IfText,
    InterruptRule,  # Add import
    Label,
    ROI,
    ReadText,
    RunFlow,
    TypeText,
    WaitImage,
    Notify,
    NotifyMethod,
)

from infra import get_logger

logger = get_logger("PropertiesPanel")


class PropertiesPanel(QWidget):
    """
    Panel for editing action properties.

    Dynamically generates form fields based on action type.
    """

    properties_changed = Signal(dict)  # Updated action data

    def __init__(self) -> None:
        super().__init__()
        self._current_data: dict | None = None
        self._fields: dict = {}
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Group box
        self.group = QGroupBox("Properties")
        self.form_layout = QFormLayout(self.group)

        # Placeholder
        self.placeholder = QLabel("Select an action to edit")
        self.form_layout.addRow(self.placeholder)

        layout.addWidget(self.group)
        layout.addStretch()

    def load_action(self, data: dict) -> None:
        """Load action data into form."""
        self._current_data = data.copy()
        self._rebuild_form()

    def _rebuild_form(self) -> None:
        """Rebuild form fields based on action type."""
        # Clear existing
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._fields.clear()

        if not self._current_data:
            self.placeholder = QLabel("Select an action to edit")
            self.form_layout.addRow(self.placeholder)
            return

        action = self._current_data.get("action")
        if not action:
            return

        action_type = type(action).__name__

        # Title
        self.form_layout.addRow(QLabel(f"<b>{action_type}</b>"))

        # Build fields based on type
        if isinstance(action, ClickImage):
            self._add_text_field("asset_id", action.asset_id)
            self._add_combo_field("button", action.button, ["left", "right", "middle"])
            self._add_spin_field("clicks", action.clicks, 1, 3)
            self._add_spin_field("interval_ms", action.interval_ms, 0, 1000)
            self._add_spin_field("timeout_ms", action.timeout_ms, 0, 60000)
            # Advanced options (collapsible)
            self._add_collapsible_section("▸ Advanced", [
                ("offset_x", action.offset_x, -500, 500),
                ("offset_y", action.offset_y, -500, 500),
            ])

        elif isinstance(action, ClickUntil):
            self._add_text_field("click_asset_id", action.click_asset_id)
            self._add_text_field("until_asset_id", action.until_asset_id)
            self._add_bool_field("until_appear", action.until_appear)
            self._add_combo_field("button", action.button, ["left", "right", "middle"])
            self._add_spin_field("click_interval_ms", action.click_interval_ms, 100, 10000)
            self._add_spin_field("timeout_ms", action.timeout_ms, 0, 300000)
            self._add_spin_field("max_clicks", action.max_clicks, 1, 1000)

        elif isinstance(action, WaitImage):
            self._add_text_field("asset_id", action.asset_id)
            self._add_bool_field("appear", action.appear)
            self._add_spin_field("timeout_ms", action.timeout_ms, 0, 300000)
            self._add_spin_field("poll_ms", action.poll_ms, 10, 5000)

        elif isinstance(action, Click):
            self._add_spin_field("x", action.x or 0, 0, 9999)
            self._add_spin_field("y", action.y or 0, 0, 9999)
            self._add_combo_field("button", action.button, ["left", "right", "middle"])
            self._add_spin_field("clicks", action.clicks, 1, 3)
            self._add_spin_field("interval_ms", action.interval_ms, 0, 1000)
            self._add_bool_field("use_match", action.use_match)

        elif isinstance(action, IfImage):
            self._add_text_field("asset_id", action.asset_id)
            self._add_label("(then/else actions edited separately)")

        elif isinstance(action, IfText):
            self._add_text_field("variable_name", action.variable_name)
            self._add_combo_field("operator", action.operator, [
                "contains", "equals", "starts_with", "ends_with", "numeric_lt", "numeric_gt"
            ])
            self._add_text_field("value", action.value)
            self._add_label("(then/else actions edited separately)")

        elif isinstance(action, Hotkey):
            keys_str = "+".join(action.keys) if action.keys else ""
            self._add_text_field("keys", keys_str)
            self._add_label("(e.g., CTRL+S, ALT+F4)")

        elif isinstance(action, TypeText):
            self._add_text_field("text", action.text)
            self._add_bool_field("paste_mode", action.paste_mode)
            self._add_bool_field("enter", action.enter)

        elif isinstance(action, Label):
            self._add_text_field("name", action.name)

        elif isinstance(action, Goto):
            self._add_text_field("label", action.label)

        elif isinstance(action, RunFlow):
            self._add_text_field("flow_name", action.flow_name)

        elif isinstance(action, ReadText):
            self._add_text_field("variable_name", action.variable_name)
            r = action.roi
            self._add_spin_field("roi_x", r.x, 0, 9999)
            self._add_spin_field("roi_y", r.y, 0, 9999)
            self._add_spin_field("roi_w", r.w, 1, 9999)
            self._add_spin_field("roi_h", r.h, 1, 9999)
            self._add_text_field("allowlist", action.allowlist)
            self._add_double_spin_field("scale", action.scale, 0.1, 10.0)
            self._add_bool_field("invert", action.invert)
            self._add_bool_field("binarize", action.binarize)

        elif isinstance(action, InterruptRule):
            self._add_text_field("when_image", action.when_image)
            self._add_spin_field("priority", action.priority, 0, 100)
            self._add_text_field("run_flow", action.run_flow or "")

        elif isinstance(action, ClickRandom):
            r = action.roi
            self._add_spin_field("roi_x", r.x, 0, 9999)
            self._add_spin_field("roi_y", r.y, 0, 9999)
            self._add_spin_field("roi_w", r.w, 1, 9999)
            self._add_spin_field("roi_h", r.h, 1, 9999)
            self._add_spin_field("clicks", action.clicks, 1, 10)
            self._add_spin_field("interval_ms", action.interval_ms, 0, 5000)
            self._add_combo_field("button", action.button, ["left", "right", "middle"])

        elif isinstance(action, Delay):
            self._add_spin_field("ms", action.ms, 0, 300000)

        elif isinstance(action, Notify):
            self._add_text_field("message", action.message)
            self._add_combo_field("method", action.method.value, [m.value for m in NotifyMethod])
            self._add_text_field("title", action.title)
            self._add_text_field("target", action.target)

        # Comment field (common to all)
        self._add_text_field("comment", action.comment)

        # Apply button
        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self._on_apply)
        self.form_layout.addRow(btn_apply)

    def _add_text_field(self, name: str, value: str) -> None:
        field = QLineEdit(str(value))
        self._fields[name] = field
        self.form_layout.addRow(name.replace("_", " ").title() + ":", field)

    def _add_spin_field(self, name: str, value: int, min_val: int, max_val: int) -> None:
        field = QSpinBox()
        field.setRange(min_val, max_val)
        field.setValue(value)
        self._fields[name] = field
        self.form_layout.addRow(name.replace("_", " ").title() + ":", field)

    def _add_double_spin_field(self, name: str, value: float, min_val: float, max_val: float) -> None:
        field = QDoubleSpinBox()
        field.setRange(min_val, max_val)
        field.setValue(value)
        field.setSingleStep(0.1)
        self._fields[name] = field
        self.form_layout.addRow(name.replace("_", " ").title() + ":", field)

    def _add_combo_field(self, name: str, value: str, options: list[str]) -> None:
        field = QComboBox()
        field.addItems(options)
        if value in options:
            field.setCurrentText(value)
        self._fields[name] = field
        self.form_layout.addRow(name.replace("_", " ").title() + ":", field)

    def _add_bool_field(self, name: str, value: bool) -> None:
        field = QCheckBox()
        field.setChecked(value)
        self._fields[name] = field
        self.form_layout.addRow(name.replace("_", " ").title() + ":", field)

    def _add_label(self, text: str) -> None:
        label = QLabel(text)
        label.setStyleSheet("color: gray; font-style: italic;")
        self.form_layout.addRow(label)

    def _add_collapsible_section(
        self, title: str, fields: list[tuple[str, int, int, int]]
    ) -> None:
        """Add collapsible section with spin fields (hidden by default)."""
        # Toggle checkbox
        toggle = QCheckBox(title)
        toggle.setStyleSheet("color: #888; font-weight: bold;")
        self.form_layout.addRow(toggle)

        # Create hidden fields
        field_widgets = []
        for name, value, min_val, max_val in fields:
            field = QSpinBox()
            field.setRange(min_val, max_val)
            field.setValue(value)
            field.setVisible(False)
            self._fields[name] = field
            label = QLabel(name.replace("_", " ").title() + ":")
            label.setVisible(False)
            label.setStyleSheet("padding-left: 16px;")
            self.form_layout.addRow(label, field)
            field_widgets.append((label, field))

        # Toggle visibility
        def on_toggle(checked: bool) -> None:
            toggle.setText("▾ Advanced" if checked else "▸ Advanced")
            for label, field in field_widgets:
                label.setVisible(checked)
                field.setVisible(checked)

        toggle.toggled.connect(on_toggle)

    def _on_apply(self) -> None:
        """Apply changes to action."""
        if not self._current_data:
            return

        action = self._current_data.get("action")
        if not action:
            return

        # Build updated action based on type
        try:
            updated = self._build_updated_action(action)
            if updated:
                self._current_data["action"] = updated
                self.properties_changed.emit(self._current_data)
                logger.info("Applied changes to %s", type(action).__name__)
        except Exception as e:
            logger.error("Failed to apply: %s", e)

    def _build_updated_action(self, action):  # type: ignore
        """Build updated action from form fields."""
        if isinstance(action, ClickImage):
            return ClickImage(
                asset_id=self._fields["asset_id"].text(),
                button=self._fields["button"].currentText(),
                clicks=self._fields["clicks"].value(),
                timeout_ms=self._fields["timeout_ms"].value(),
                offset_x=self._fields["offset_x"].value(),
                offset_y=self._fields["offset_y"].value(),
                comment=self._fields["comment"].text(),
            )

        elif isinstance(action, ClickUntil):
            return ClickUntil(
                click_asset_id=self._fields["click_asset_id"].text(),
                until_asset_id=self._fields["until_asset_id"].text(),
                until_appear=self._fields["until_appear"].isChecked(),
                button=self._fields["button"].currentText(),
                click_interval_ms=self._fields["click_interval_ms"].value(),
                timeout_ms=self._fields["timeout_ms"].value(),
                max_clicks=self._fields["max_clicks"].value(),
                comment=self._fields["comment"].text(),
            )

        elif isinstance(action, WaitImage):
            return WaitImage(
                asset_id=self._fields["asset_id"].text(),
                appear=self._fields["appear"].isChecked(),
                timeout_ms=self._fields["timeout_ms"].value(),
                poll_ms=self._fields["poll_ms"].value(),
                comment=self._fields["comment"].text(),
            )

        elif isinstance(action, Click):
            return Click(
                x=self._fields["x"].value() or None,
                y=self._fields["y"].value() or None,
                button=self._fields["button"].currentText(),
                clicks=self._fields["clicks"].value(),
                use_match=self._fields["use_match"].isChecked(),
                comment=self._fields["comment"].text(),
            )

        elif isinstance(action, IfImage):
            return IfImage(
                asset_id=self._fields["asset_id"].text(),
                then_actions=action.then_actions,
                else_actions=action.else_actions,
                comment=self._fields["comment"].text(),
            )

        elif isinstance(action, IfText):
            return IfText(
                variable_name=self._fields["variable_name"].text(),
                operator=self._fields["operator"].currentText(),
                value=self._fields["value"].text(),
                then_actions=action.then_actions,
                else_actions=action.else_actions,
                comment=self._fields["comment"].text(),
            )

        elif isinstance(action, Hotkey):
            keys_str = self._fields["keys"].text()
            keys = [k.strip().upper() for k in keys_str.split("+") if k.strip()]
            return Hotkey(
                keys=keys,
                comment=self._fields["comment"].text(),
            )

        elif isinstance(action, TypeText):
            return TypeText(
                text=self._fields["text"].text(),
                paste_mode=self._fields["paste_mode"].isChecked(),
                enter=self._fields["enter"].isChecked(),
                comment=self._fields["comment"].text(),
            )

        elif isinstance(action, Label):
            return Label(
                name=self._fields["name"].text(),
                comment=self._fields["comment"].text(),
            )

        elif isinstance(action, Goto):
            return Goto(
                label=self._fields["label"].text(),
                comment=self._fields["comment"].text(),
            )

        elif isinstance(action, RunFlow):
            return RunFlow(
                flow_name=self._fields["flow_name"].text(),
                comment=self._fields["comment"].text(),
            )

        elif isinstance(action, ReadText):
            return ReadText(
                variable_name=self._fields["variable_name"].text(),
                roi=ROI(
                    x=self._fields["roi_x"].value(),
                    y=self._fields["roi_y"].value(),
                    w=self._fields["roi_w"].value(),
                    h=self._fields["roi_h"].value()
                ),
                allowlist=self._fields["allowlist"].text(),
                scale=self._fields["scale"].value(),
                invert=self._fields["invert"].isChecked(),
                binarize=self._fields["binarize"].isChecked(),
                comment=self._fields["comment"].text(),
            )

        elif isinstance(action, InterruptRule):
            return InterruptRule(
                when_image=self._fields["when_image"].text(),
                priority=self._fields["priority"].value(),
                run_flow=self._fields["run_flow"].text() or None,
                do_actions=action.do_actions  # Preserve existing
            )

        elif isinstance(action, ClickRandom):
            return ClickRandom(
                roi=ROI(
                    x=self._fields["roi_x"].value(),
                    y=self._fields["roi_y"].value(),
                    w=self._fields["roi_w"].value(),
                    h=self._fields["roi_h"].value()
                ),
                clicks=self._fields["clicks"].value(),
                interval_ms=self._fields["interval_ms"].value(),
                button=self._fields["button"].currentText(),
                comment=self._fields["comment"].text(),
            )

            return Delay(
                ms=self._fields["ms"].value(),
                comment=self._fields["comment"].text(),
            )

        elif isinstance(action, Notify):
            return Notify(
                message=self._fields["message"].text(),
                method=NotifyMethod(self._fields["method"].currentText()),
                title=self._fields["title"].text(),
                target=self._fields["target"].text(),
                comment=self._fields["comment"].text(),
            )

        return None
