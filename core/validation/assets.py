"""
Asset validation utilities.

Validates that all assets referenced by a script exist before execution.
"""

from pathlib import Path

from core.models import Action, Flow, Script
from infra import get_logger

logger = get_logger("AssetValidator")


def get_referenced_assets(flow: Flow) -> set[str]:
    """Extract all asset IDs referenced by a flow."""
    assets = set()

    def scan_actions(actions: list[Action]):
        for action in actions:
            # Check if action has asset_id field
            if hasattr(action, "asset_id") and action.asset_id:
                assets.add(action.asset_id)

            # Recursively scan nested actions
            if hasattr(action, "then_actions"):
                scan_actions(action.then_actions)
            if hasattr(action, "else_actions"):
                scan_actions(action.else_actions)
            if hasattr(action, "do_actions") and action.do_actions:
                scan_actions(action.do_actions)

    scan_actions(flow.actions)
    return assets


def validate_assets(script: Script, assets_dir: Path) -> tuple[bool, list[str]]:
    """
    Validate all assets referenced by script exist.

    Returns:
        (all_valid, missing_assets)
    """
    missing = []

    # Collect all referenced assets
    all_assets = set()
    for flow in script.flows:
        all_assets.update(get_referenced_assets(flow))

    # Also check interrupt rules
    for rule in script.interrupts:
        if rule.when_image:
            all_assets.add(rule.when_image)
        if rule.do_actions:
            # Scan actions in interrupt
            for action in rule.do_actions:
                if hasattr(action, "asset_id") and action.asset_id:
                    all_assets.add(action.asset_id)

    # Check each asset exists
    for asset_id in all_assets:
        asset_path = assets_dir / f"{asset_id}.png"
        if not asset_path.exists():
            missing.append(asset_id)
            logger.warning(f"Missing asset: {asset_id} (expected: {asset_path})")

    if missing:
        logger.error(f"Found {len(missing)} missing assets: {', '.join(missing)}")
        return False, missing

    logger.info(f"All {len(all_assets)} assets validated successfully")
    return True, []
