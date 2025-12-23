"""
RetroAuto v2 - DSL Runner Adapter

Adapts DSL IR to the existing YAML-based runner.
Converts ActionIR to Action models for execution.
Also provides bidirectional Action ↔ ActionIR conversion for GUI sync.
"""

from __future__ import annotations

from core.dsl.ir import ActionIR, FlowIR, InterruptIR, ScriptIR
from core.models import (
    Action,
    AssetImage,
    Click,
    ClickImage,
    ClickRandom,
    Delay,
    DelayRandom,
    Drag,
    Else,
    EndIf,
    EndLoop,
    EndWhile,
    Flow,
    Goto,
    Hotkey,
    IfImage,
    IfPixel,
    IfText,
    InterruptRule,
    Label,
    Loop,
    Notify,
    NotifyMethod,
    PixelColor,
    ReadText,
    RunFlow,
    Script,
    ScriptHotkeys,
    Scroll,
    TypeText,
    WaitImage,
    WaitPixel,
    WhileImage,
)


class DSLToYAMLAdapter:
    """
    Converts DSL IR to YAML Script model.

    This allows using the existing Runner with DSL-based scripts.
    """

    @staticmethod
    def convert(ir: ScriptIR) -> Script:
        """Convert ScriptIR to Script model."""
        # Hotkeys
        hotkeys = ScriptHotkeys(
            start=ir.hotkeys.start,
            stop=ir.hotkeys.stop,
            pause=ir.hotkeys.pause,
        )

        # Assets
        assets = [
            AssetImage(
                id=a.id,
                path=a.path,
                threshold=a.threshold,
            )
            for a in ir.assets
        ]

        # Flows
        flows = [DSLToYAMLAdapter._convert_flow(f) for f in ir.flows]

        # Interrupts
        interrupts = [DSLToYAMLAdapter._convert_interrupt(i) for i in ir.interrupts]

        return Script(
            name=ir.name,
            version=ir.version,
            author=ir.author,
            hotkeys=hotkeys,
            assets=assets,
            flows=flows,
            interrupts=interrupts,
            main_flow=(
                "main"
                if any(f.name == "main" for f in flows)
                else (flows[0].name if flows else "main")
            ),
        )

    @staticmethod
    def _convert_flow(flow_ir: FlowIR) -> Flow:
        """Convert FlowIR to Flow model."""
        actions = [
            DSLToYAMLAdapter._convert_action(a)
            for a in flow_ir.actions
            if DSLToYAMLAdapter._convert_action(a) is not None
        ]

        return Flow(name=flow_ir.name, actions=actions)

    @staticmethod
    def _convert_interrupt(interrupt: InterruptIR) -> InterruptRule:
        """Convert InterruptIR to InterruptRule model."""
        actions = [
            DSLToYAMLAdapter._convert_action(a)
            for a in interrupt.actions
            if DSLToYAMLAdapter._convert_action(a) is not None
        ]

        return InterruptRule(
            priority=interrupt.priority,
            when_image=interrupt.when_asset,
            do_actions=actions,
        )

    @staticmethod
    def _convert_action(action: ActionIR) -> Action | None:
        """Convert ActionIR to Action model."""
        params = action.params
        action_type = action.action_type

        if action_type == "wait_image":
            return WaitImage(
                asset_id=params.get("arg0", ""),
                timeout_ms=params.get("timeout", 5000),
                appear=params.get("appear", True),
            )

        if action_type == "click":
            x = params.get("arg0", params.get("x", 0))
            y = params.get("arg1", params.get("y", 0))
            return Click(x=x, y=y, button=params.get("button", "left"))

        if action_type == "sleep":
            # Handle duration (could be int ms or "5s" style)
            duration = params.get("arg0", params.get("duration", 1000))
            if isinstance(duration, str):
                duration = DSLToYAMLAdapter._parse_duration(duration)
            return Delay(ms=duration)

        if action_type == "hotkey":
            keys_arg = params.get("arg0", "")
            if isinstance(keys_arg, str):
                keys = keys_arg.split("+")
            else:
                keys = list(keys_arg) if keys_arg else []
            return Hotkey(keys=keys)

        if action_type == "type_text":
            return TypeText(
                text=params.get("arg0", params.get("text", "")),
                paste_mode=params.get("paste", False),
                enter=params.get("enter", False),
            )

        if action_type == "label":
            return Label(name=params.get("name", ""))

        if action_type == "goto":
            return Goto(label=params.get("target", ""))

        if action_type == "run_flow":
            return RunFlow(flow_name=params.get("arg0", params.get("flow_name", "")))

        if action_type == "log":
            # Log is not an action in YAML - ignore or convert to delay
            return None

        # Unknown action types
        return None

    @staticmethod
    def _parse_duration(duration_str: str) -> int:
        """Parse duration string like '5s' or '100ms' to milliseconds."""
        duration_str = duration_str.lower().strip()

        if duration_str.endswith("ms"):
            return int(duration_str[:-2])
        elif duration_str.endswith("s"):
            return int(float(duration_str[:-1]) * 1000)
        elif duration_str.endswith("m"):
            return int(float(duration_str[:-1]) * 60 * 1000)
        elif duration_str.endswith("h"):
            return int(float(duration_str[:-1]) * 60 * 60 * 1000)
        else:
            # Assume milliseconds
            return int(duration_str)


def ir_to_script(ir: ScriptIR) -> Script:
    """Convert DSL IR to YAML Script model."""
    return DSLToYAMLAdapter.convert(ir)


# ─────────────────────────────────────────────────────────────
# Bidirectional Action ↔ ActionIR Converters for GUI Sync
# ─────────────────────────────────────────────────────────────


def action_to_ir(action: Action) -> ActionIR:
    """
    Convert Action model to ActionIR for GUI → IR sync.

    This enables the Actions Panel to update the IR when
    the user modifies actions via the GUI.
    """
    action_type = action.action.lower()  # WaitImage -> wait_image

    # Convert action_type to snake_case
    type_mapping = {
        "WaitImage": "wait_image",
        "WaitPixel": "wait_pixel",
        "Click": "click",
        "ClickImage": "click_image",
        "ClickRandom": "click_random",
        "IfImage": "if_image",
        "IfPixel": "if_pixel",
        "IfText": "if_text",
        "Hotkey": "hotkey",
        "TypeText": "type_text",
        "Label": "label",
        "Goto": "goto",
        "RunFlow": "run_flow",
        "Delay": "sleep",
        "DelayRandom": "delay_random",
        "Drag": "drag",
        "Scroll": "scroll",
        "Loop": "loop",
        "WhileImage": "while_image",
        "ReadText": "read_text",
        "Notify": "notify",
        "EndIf": "end_if",
        "Else": "else",
    }

    action_type = type_mapping.get(action.action, action.action.lower())

    # Build params dict from action fields
    params: dict = {}

    if isinstance(action, WaitImage):
        params["arg0"] = action.asset_id
        params["timeout"] = action.timeout_ms
        params["appear"] = action.appear

    elif isinstance(action, WaitPixel):
        params["x"] = action.x
        params["y"] = action.y
        params["r"] = action.color.r
        params["g"] = action.color.g
        params["b"] = action.color.b
        params["tolerance"] = action.color.tolerance
        params["appear"] = action.appear

    elif isinstance(action, Click):
        params["x"] = action.x
        params["y"] = action.y
        params["button"] = action.button
        params["clicks"] = action.clicks
        params["use_match"] = action.use_match

    elif isinstance(action, IfImage):
        params["arg0"] = action.asset_id
        # Nested actions would need recursive conversion

    elif isinstance(action, IfPixel):
        params["x"] = action.x
        params["y"] = action.y
        params["r"] = action.color.r
        params["g"] = action.color.g
        params["b"] = action.color.b

    elif isinstance(action, Hotkey):
        params["arg0"] = "+".join(action.keys)

    elif isinstance(action, TypeText):
        params["arg0"] = action.text
        params["paste"] = action.paste_mode
        params["enter"] = action.enter

    elif isinstance(action, Label):
        params["name"] = action.name

    elif isinstance(action, Goto):
        params["target"] = action.label

    elif isinstance(action, RunFlow):
        params["arg0"] = action.flow_name

    elif isinstance(action, Delay):
        params["arg0"] = action.ms

    elif isinstance(action, DelayRandom):
        params["min_ms"] = action.min_ms
        params["max_ms"] = action.max_ms

    elif isinstance(action, Drag):
        params["from_x"] = action.from_x
        params["from_y"] = action.from_y
        params["to_x"] = action.to_x
        params["to_y"] = action.to_y
        params["duration_ms"] = action.duration_ms

    elif isinstance(action, Scroll):
        params["x"] = action.x
        params["y"] = action.y
        params["amount"] = action.amount

    elif isinstance(action, Loop):
        params["count"] = action.count
        # Nested actions would need recursive conversion

    elif isinstance(action, WhileImage):
        params["arg0"] = action.asset_id
        params["while_present"] = action.while_present

    elif isinstance(action, ClickImage):
        params["asset_id"] = action.asset_id
        params["button"] = action.button
        params["clicks"] = action.clicks
        params["timeout_ms"] = action.timeout_ms

    elif isinstance(action, ClickRandom):
        params["x1"] = action.x1
        params["y1"] = action.y1
        params["x2"] = action.x2
        params["y2"] = action.y2

    elif isinstance(action, ReadText):
        params["variable_name"] = action.variable_name
        params["roi"] = action.roi
        params["allowlist"] = action.allowlist
        params["scale"] = action.scale
        params["invert"] = action.invert
        params["binarize"] = action.binarize

    elif isinstance(action, IfText):
        params["variable_name"] = action.variable_name
        params["operator"] = action.operator
        params["value"] = action.value

    elif isinstance(action, Notify):
        params["message"] = action.message
        params["method"] = action.method.value if hasattr(action.method, 'value') else str(action.method)
        params["title"] = action.title
        params["target"] = action.target

    # Block markers (no params needed)
    elif isinstance(action, Else):
        pass  # No params
    elif isinstance(action, EndIf):
        pass  # No params
    elif isinstance(action, EndLoop):
        pass  # No params
    elif isinstance(action, EndWhile):
        pass  # No params

    return ActionIR(
        action_type=action_type,
        params=params,
        span_line=None,
    )


def ir_to_action(ir: ActionIR) -> Action | None:
    """
    Convert ActionIR to Action model for IR → GUI sync.

    This enables the Actions Panel to refresh when
    the IR is updated from code changes.
    """
    params = ir.params
    action_type = ir.action_type.lower()

    try:
        if action_type == "wait_image":
            return WaitImage(
                asset_id=params.get("arg0", ""),
                timeout_ms=params.get("timeout", 10000),
                appear=params.get("appear", True),
            )

        if action_type == "wait_pixel":
            return WaitPixel(
                x=params.get("x", 0),
                y=params.get("y", 0),
                color=PixelColor(
                    r=params.get("r", 255),
                    g=params.get("g", 0),
                    b=params.get("b", 0),
                    tolerance=params.get("tolerance", 10),
                ),
                appear=params.get("appear", True),
            )

        if action_type == "click":
            return Click(
                x=params.get("arg0", params.get("x", 0)),
                y=params.get("arg1", params.get("y", 0)),
                button=params.get("button", "left"),
                clicks=params.get("clicks", 1),
                use_match=params.get("use_match", False),
            )

        if action_type == "if_image":
            return IfImage(
                asset_id=params.get("arg0", ""),
            )

        if action_type == "if_pixel":
            return IfPixel(
                x=params.get("x", 0),
                y=params.get("y", 0),
                color=PixelColor(
                    r=params.get("r", 255),
                    g=params.get("g", 0),
                    b=params.get("b", 0),
                ),
            )

        if action_type == "hotkey":
            keys_str = params.get("arg0", "")
            keys = keys_str.split("+") if keys_str else []
            return Hotkey(keys=keys)

        if action_type in ("type_text", "typetext"):
            return TypeText(
                text=params.get("arg0", params.get("text", "")),
                paste_mode=params.get("paste", True),
                enter=params.get("enter", False),
            )

        if action_type == "label":
            return Label(name=params.get("name", ""))

        if action_type == "goto":
            return Goto(label=params.get("target", ""))

        if action_type in ("run_flow", "runflow"):
            return RunFlow(flow_name=params.get("arg0", ""))

        if action_type in ("sleep", "delay"):
            ms = params.get("arg0", params.get("ms", 1000))
            if isinstance(ms, str):
                ms = DSLToYAMLAdapter._parse_duration(ms)
            return Delay(ms=ms)

        if action_type == "delay_random":
            return DelayRandom(
                min_ms=params.get("min_ms", 500),
                max_ms=params.get("max_ms", 1500),
            )

        if action_type == "drag":
            return Drag(
                from_x=params.get("from_x", 0),
                from_y=params.get("from_y", 0),
                to_x=params.get("to_x", 100),
                to_y=params.get("to_y", 100),
                duration_ms=params.get("duration_ms", 500),
            )

        if action_type == "scroll":
            return Scroll(
                x=params.get("x"),
                y=params.get("y"),
                amount=params.get("amount", 3),
            )

        if action_type == "loop":
            return Loop(
                count=params.get("count"),
            )

        if action_type == "while_image":
            return WhileImage(
                asset_id=params.get("arg0", ""),
                while_present=params.get("while_present", True),
            )

        if action_type == "click_image":
            return ClickImage(
                asset_id=params.get("asset_id", params.get("arg0", "")),
                button=params.get("button", "left"),
                clicks=params.get("clicks", 1),
                timeout_ms=params.get("timeout_ms", 10000),
            )

        if action_type == "click_random":
            return ClickRandom(
                x1=params.get("x1", 0),
                y1=params.get("y1", 0),
                x2=params.get("x2", 100),
                y2=params.get("y2", 100),
            )

        if action_type == "read_text":
            return ReadText(
                variable_name=params.get("variable_name", "text"),
                roi=params.get("roi"),
                allowlist=params.get("allowlist", ""),
                scale=params.get("scale", 1.0),
                invert=params.get("invert", False),
                binarize=params.get("binarize", False),
            )

        if action_type == "if_text":
            return IfText(
                variable_name=params.get("variable_name", ""),
                operator=params.get("operator", "contains"),
                value=params.get("value", ""),
            )

        if action_type == "notify":
            method_str = params.get("method", "popup")
            method = NotifyMethod.POPUP
            if method_str == "telegram":
                method = NotifyMethod.TELEGRAM
            elif method_str == "discord":
                method = NotifyMethod.DISCORD
            return Notify(
                message=params.get("message", params.get("arg0", "")),
                method=method,
                title=params.get("title", "Notification"),
                target=params.get("target", ""),
            )

        # Block markers
        if action_type == "else":
            return Else()
        if action_type in ("end_if", "endif"):
            return EndIf()
        if action_type in ("end_loop", "endloop"):
            return EndLoop()
        if action_type in ("end_while", "endwhile"):
            return EndWhile()

    except Exception:
        pass

    return None
