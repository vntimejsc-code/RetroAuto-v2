"""
RetroAuto v2 - Core Data Models

Pydantic v2 models with discriminated unions for type-safe actions.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

# ─────────────────────────────────────────────────────────────
# Basic Types
# ─────────────────────────────────────────────────────────────


class ROI(BaseModel):
    """Region of Interest for image matching."""

    x: int = Field(ge=0, description="X coordinate")
    y: int = Field(ge=0, description="Y coordinate")
    w: int = Field(gt=0, description="Width")
    h: int = Field(gt=0, description="Height")

    @property
    def center(self) -> tuple[int, int]:
        """Return center point of ROI."""
        return (self.x + self.w // 2, self.y + self.h // 2)

    def contains(self, x: int, y: int) -> bool:
        """Check if point is inside ROI."""
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h


class MatchMethod(str, Enum):
    """OpenCV template matching methods."""

    TM_CCOEFF_NORMED = "TM_CCOEFF_NORMED"
    TM_CCORR_NORMED = "TM_CCORR_NORMED"
    TM_SQDIFF_NORMED = "TM_SQDIFF_NORMED"


class AssetImage(BaseModel):
    """Image template for matching."""

    id: str = Field(description="Unique asset identifier")
    path: str = Field(description="Relative path to image file")
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    method: MatchMethod = Field(default=MatchMethod.TM_CCOEFF_NORMED)
    grayscale: bool = Field(default=True, description="Use grayscale matching")
    roi: ROI | None = Field(default=None, description="Default search region")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Ensure path uses forward slashes."""
        return v.replace("\\", "/")


class Match(BaseModel):
    """Result of a successful template match."""

    x: int
    y: int
    w: int
    h: int
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    @property
    def center(self) -> tuple[int, int]:
        """Return center point of match."""
        return (self.x + self.w // 2, self.y + self.h // 2)


# ─────────────────────────────────────────────────────────────
# Actions (Discriminated Union)
# ─────────────────────────────────────────────────────────────


class ActionBase(BaseModel):
    """Base class for all actions."""

    comment: str = Field(default="", description="Optional comment")


class WaitImage(ActionBase):
    """Wait for image to appear or vanish."""

    action: Literal["WaitImage"] = "WaitImage"
    asset_id: str = Field(description="Asset to wait for")
    appear: bool = Field(default=True, description="True=appear, False=vanish")
    timeout_ms: int = Field(default=10000, ge=0)
    poll_ms: int = Field(default=100, ge=10)
    roi_override: ROI | None = Field(default=None)


class Click(ActionBase):
    """Click at coordinates or previous match."""

    action: Literal["Click"] = "Click"
    x: int | None = Field(default=None, description="X coordinate (None=use match)")
    y: int | None = Field(default=None, description="Y coordinate (None=use match)")
    button: Literal["left", "right", "middle"] = Field(default="left")
    clicks: int = Field(default=1, ge=1, le=10)
    interval_ms: int = Field(default=80, ge=0)
    use_match: bool = Field(default=False, description="Click at last match center")


class ClickImage(ActionBase):
    """Wait for image and click on it (combo action)."""

    action: Literal["ClickImage"] = "ClickImage"
    asset_id: str = Field(description="Asset to find and click")
    button: Literal["left", "right", "middle"] = Field(default="left")
    clicks: int = Field(default=1, ge=1, le=10)
    timeout_ms: int = Field(default=10000, ge=0)
    offset_x: int = Field(default=0, description="X offset from center")
    offset_y: int = Field(default=0, description="Y offset from center")


class ClickUntil(ActionBase):
    """Click repeatedly until target image appears/vanishes (farming loop)."""

    action: Literal["ClickUntil"] = "ClickUntil"
    click_asset_id: str = Field(description="Asset to click")
    until_asset_id: str = Field(description="Target asset to check")
    until_appear: bool = Field(default=True, description="True=until appears, False=until vanishes")
    button: Literal["left", "right", "middle"] = Field(default="left")
    click_interval_ms: int = Field(default=1000, ge=100)
    timeout_ms: int = Field(default=30000, ge=0)
    max_clicks: int = Field(default=50, ge=1, description="Safety limit")


class IfImage(ActionBase):
    """Conditional branch based on image presence."""

    action: Literal["IfImage"] = "IfImage"
    asset_id: str = Field(description="Asset to check")
    then_actions: list[Action] = Field(default_factory=list)
    else_actions: list[Action] = Field(default_factory=list)
    roi_override: ROI | None = Field(default=None)


class Else(ActionBase):
    """Marks start of else block in IfImage (for GUI flat list)."""

    action: Literal["Else"] = "Else"


class EndIf(ActionBase):
    """Marks end of IfImage block (for GUI flat list)."""

    action: Literal["EndIf"] = "EndIf"


class Hotkey(ActionBase):
    """Press hotkey combination."""

    action: Literal["Hotkey"] = "Hotkey"
    keys: list[str] = Field(description="Keys to press, e.g. ['CTRL', 'S']")


class TypeText(ActionBase):
    """Type text using keyboard."""

    action: Literal["TypeText"] = "TypeText"
    text: str = Field(description="Text to type")
    paste_mode: bool = Field(default=True, description="Use clipboard paste")
    enter: bool = Field(default=False, description="Press Enter after text")


class Label(ActionBase):
    """Mark a position for Goto."""

    action: Literal["Label"] = "Label"
    name: str = Field(description="Label name")


class Goto(ActionBase):
    """Jump to a label."""

    action: Literal["Goto"] = "Goto"
    label: str = Field(description="Target label name")


class RunFlow(ActionBase):
    """Execute another flow."""

    action: Literal["RunFlow"] = "RunFlow"
    flow_name: str = Field(description="Name of flow to run")


class Delay(ActionBase):
    """Wait for specified duration."""

    action: Literal["Delay"] = "Delay"
    ms: int = Field(default=1000, ge=0, description="Delay in milliseconds")


class DelayRandom(ActionBase):
    """Wait for random duration between min and max."""

    action: Literal["DelayRandom"] = "DelayRandom"
    min_ms: int = Field(default=500, ge=0, description="Minimum delay")
    max_ms: int = Field(default=1500, ge=0, description="Maximum delay")


class Drag(ActionBase):
    """Drag from one position to another."""

    action: Literal["Drag"] = "Drag"
    from_x: int = Field(description="Start X coordinate")
    from_y: int = Field(description="Start Y coordinate")
    to_x: int = Field(description="End X coordinate")
    to_y: int = Field(description="End Y coordinate")
    duration_ms: int = Field(default=500, ge=0, description="Drag duration")
    button: Literal["left", "right", "middle"] = Field(default="left")


class Scroll(ActionBase):
    """Scroll mouse wheel."""

    action: Literal["Scroll"] = "Scroll"
    x: int | None = Field(default=None, description="X position (None=current)")
    y: int | None = Field(default=None, description="Y position (None=current)")
    amount: int = Field(default=3, description="Scroll amount (positive=up, negative=down)")


class Loop(ActionBase):
    """Repeat actions N times or infinitely."""

    action: Literal["Loop"] = "Loop"
    count: int | None = Field(default=None, description="Times to repeat (None=infinite)")
    actions: list[Action] = Field(default_factory=list)


class WhileImage(ActionBase):
    """Repeat actions while image is present/absent."""

    action: Literal["WhileImage"] = "WhileImage"
    asset_id: str = Field(description="Asset to check")
    while_present: bool = Field(default=True, description="True=while exists")
    actions: list[Action] = Field(default_factory=list)
    max_iterations: int = Field(default=100, description="Safety limit")
    roi_override: ROI | None = Field(default=None)


class PixelColor(BaseModel):
    """RGB color for pixel checking."""

    r: int = Field(ge=0, le=255)
    g: int = Field(ge=0, le=255)
    b: int = Field(ge=0, le=255)
    tolerance: int = Field(default=10, ge=0, le=255, description="Color tolerance")

    def matches(self, other_r: int, other_g: int, other_b: int) -> bool:
        """Check if another color matches within tolerance."""
        return (
            abs(self.r - other_r) <= self.tolerance
            and abs(self.g - other_g) <= self.tolerance
            and abs(self.b - other_b) <= self.tolerance
        )


class WaitPixel(ActionBase):
    """Wait for pixel color at position."""

    action: Literal["WaitPixel"] = "WaitPixel"
    x: int = Field(description="X coordinate")
    y: int = Field(description="Y coordinate")
    color: PixelColor = Field(description="Expected color")
    appear: bool = Field(default=True, description="True=wait for color, False=wait until gone")
    timeout_ms: int = Field(default=10000, ge=0)
    poll_ms: int = Field(default=100, ge=10)


class IfPixel(ActionBase):
    """Conditional branch based on pixel color."""

    action: Literal["IfPixel"] = "IfPixel"
    x: int = Field(description="X coordinate")
    y: int = Field(description="Y coordinate")
    color: PixelColor = Field(description="Color to check")
    then_actions: list[Action] = Field(default_factory=list)
    else_actions: list[Action] = Field(default_factory=list)


# Discriminated union type
Action = Annotated[
    WaitImage
    | Click
    | IfImage
    | Hotkey
    | TypeText
    | Label
    | Goto
    | RunFlow
    | Delay
    | DelayRandom
    | Drag
    | Scroll
    | Loop
    | WhileImage
    | WaitPixel
    | IfPixel,
    Field(discriminator="action"),
]


# ─────────────────────────────────────────────────────────────
# Flow & Script
# ─────────────────────────────────────────────────────────────


class Flow(BaseModel):
    """A named sequence of actions."""

    name: str = Field(description="Flow name")
    actions: list[Action] = Field(default_factory=list)


class InterruptRule(BaseModel):
    """Global interrupt that triggers on image detection."""

    priority: int = Field(default=0, description="Higher = checked first")
    when_image: str = Field(description="Asset ID to watch for")
    roi_override: ROI | None = Field(default=None)
    do_actions: list[Action] = Field(default_factory=list)
    run_flow: str | None = Field(default=None, description="Or run this flow")


class ScriptHotkeys(BaseModel):
    """Hotkey bindings for script control."""

    start: str = Field(default="F5")
    stop: str = Field(default="F6")
    pause: str = Field(default="F7")


class Script(BaseModel):
    """Complete automation script."""

    name: str = Field(default="Untitled")
    version: str = Field(default="1.0")
    author: str = Field(default="")
    description: str = Field(default="")

    hotkeys: ScriptHotkeys = Field(default_factory=ScriptHotkeys)
    assets: list[AssetImage] = Field(default_factory=list)
    flows: list[Flow] = Field(default_factory=list)
    interrupts: list[InterruptRule] = Field(default_factory=list)

    # Main flow to run
    main_flow: str = Field(default="main")

    def get_asset(self, asset_id: str) -> AssetImage | None:
        """Get asset by ID."""
        return next((a for a in self.assets if a.id == asset_id), None)

    def get_flow(self, name: str) -> Flow | None:
        """Get flow by name."""
        return next((f for f in self.flows if f.name == name), None)

    def validate_references(self) -> list[str]:
        """Validate all asset/flow references. Returns list of errors."""
        errors: list[str] = []
        asset_ids = {a.id for a in self.assets}
        flow_names = {f.name for f in self.flows}

        def check_actions(actions: list[Action], context: str) -> None:
            for i, action in enumerate(actions):
                loc = f"{context}[{i}]"
                if isinstance(action, (WaitImage, IfImage)) and action.asset_id not in asset_ids:
                    errors.append(f"{loc}: Unknown asset '{action.asset_id}'")
                if isinstance(action, IfImage):
                    check_actions(action.then_actions, f"{loc}.then")
                    check_actions(action.else_actions, f"{loc}.else")
                if isinstance(action, RunFlow) and action.flow_name not in flow_names:
                    errors.append(f"{loc}: Unknown flow '{action.flow_name}'")
                if isinstance(action, Goto):
                    # Label validation would need full flow context
                    pass

        for flow in self.flows:
            check_actions(flow.actions, f"flow[{flow.name}]")

        for i, interrupt in enumerate(self.interrupts):
            if interrupt.when_image not in asset_ids:
                errors.append(f"interrupt[{i}]: Unknown asset '{interrupt.when_image}'")
            if interrupt.run_flow and interrupt.run_flow not in flow_names:
                errors.append(f"interrupt[{i}]: Unknown flow '{interrupt.run_flow}'")
            check_actions(interrupt.do_actions, f"interrupt[{i}].do")

        if self.main_flow not in flow_names and self.flows:
            errors.append(f"main_flow '{self.main_flow}' not found")

        return errors
