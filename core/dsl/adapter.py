"""
RetroAuto v2 - DSL Runner Adapter

Adapts DSL IR to the existing YAML-based runner.
Converts ActionIR to Action models for execution.
"""

from __future__ import annotations

from core.dsl.ir import ActionIR, FlowIR, InterruptIR, ScriptIR
from core.models import (
    Action,
    AssetImage,
    Click,
    Delay,
    Flow,
    Goto,
    Hotkey,
    InterruptRule,
    Label,
    RunFlow,
    Script,
    ScriptHotkeys,
    TypeText,
    WaitImage,
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
            main_flow="main"
            if any(f.name == "main" for f in flows)
            else (flows[0].name if flows else "main"),
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
