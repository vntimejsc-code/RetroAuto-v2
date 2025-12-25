#!/usr/bin/env python
"""
RetroAuto v2 - CLI Headless Runner

Run automation scripts without GUI.

Usage:
    python -m scripts.retro_cli run script.yaml
    python -m scripts.retro_cli run script.yaml --flow main
    python -m scripts.retro_cli history --last 10
    python -m scripts.retro_cli stats
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.engine.context import EngineState, ExecutionContext
from core.engine.runner import Runner
from core.models import Script
from core.orchestration.history import RunHistory, get_run_history
from core.script.io import load_script
from core.templates import TemplateStore
from infra import get_logger, setup_logging

logger = get_logger("CLI")


def run_script(
    script_path: Path,
    flow_name: str | None = None,
    verbose: bool = False,
) -> bool:
    """
    Run a script headlessly.

    Args:
        script_path: Path to script.yaml
        flow_name: Optional flow to run (default: main_flow from script)
        verbose: Enable verbose logging

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        setup_logging(level="DEBUG")
    else:
        setup_logging(level="INFO")

    # Load script
    logger.info("Loading script: %s", script_path)
    try:
        script: Script = load_script(script_path)
    except Exception as e:
        logger.error("Failed to load script: %s", e)
        return False

    # Setup context
    project_dir = script_path.parent
    templates = TemplateStore(project_dir)

    if script.assets:
        errors = templates.preload(script.assets)
        if errors:
            logger.warning("Template errors: %s", errors)

    ctx = ExecutionContext(
        script=script,
        templates=templates,
    )
    ctx.set_state(EngineState.RUNNING)

    # Track in history
    history = get_run_history()
    total_steps = sum(len(f.actions) for f in script.flows)
    run_id = history.start_run(
        script_path=str(script_path),
        script_name=script.name,
        total_steps=total_steps,
    )

    # Callbacks
    steps_done = 0

    def on_step(flow: str, idx: int, action) -> None:
        nonlocal steps_done
        steps_done += 1
        action_type = type(action).__name__
        logger.info("[%d/%d] %s.%d: %s", steps_done, total_steps, flow, idx, action_type)
        history.update_step(run_id, steps_done, total_steps)

    def on_complete(flow: str, success: bool) -> None:
        status = "success" if success else "failed"
        logger.info("Flow '%s' completed: %s", flow, status)

    # Create runner
    runner = Runner(
        ctx,
        on_step=on_step,
        on_complete=on_complete,
    )

    # Run
    target_flow = flow_name or script.main_flow
    logger.info("Running flow: %s", target_flow)

    start_time = time.perf_counter()
    try:
        success = runner.run_flow(target_flow)
        elapsed = time.perf_counter() - start_time

        if success:
            logger.info("✅ Script completed in %.1fs", elapsed)
            history.end_run(run_id, "success")
        else:
            logger.warning("⚠️ Script stopped or failed after %.1fs", elapsed)
            history.end_run(run_id, "stopped")

        return success

    except Exception as e:
        elapsed = time.perf_counter() - start_time
        logger.exception("❌ Script error after %.1fs: %s", elapsed, e)
        history.end_run(run_id, "failed", str(e))
        return False


def show_history(limit: int = 10, status: str | None = None) -> None:
    """Show run history."""
    history = get_run_history()
    runs = history.get_runs(limit=limit, status=status)

    if not runs:
        print("No runs found.")
        return

    print(f"\n{'ID':<10} {'Script':<25} {'Status':<10} {'Steps':<10} {'Time':<20}")
    print("-" * 75)

    for run in runs:
        steps = f"{run.steps_completed}/{run.total_steps}"
        time_str = run.started_at.strftime("%Y-%m-%d %H:%M")
        print(f"{run.run_id:<10} {run.script_name[:24]:<25} {run.status:<10} {steps:<10} {time_str:<20}")

    print()


def show_stats() -> None:
    """Show run statistics."""
    history = get_run_history()
    stats = history.get_stats()

    print("\n📊 Run Statistics")
    print("-" * 30)
    print(f"Total runs:    {stats['total_runs']}")
    print(f"Successful:    {stats['successful']}")
    print(f"Failed:        {stats['failed']}")
    print(f"Success rate:  {stats['success_rate']:.1f}%")
    print()


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="retro",
        description="RetroAuto CLI - Run automation scripts headlessly",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run command
    run_parser = subparsers.add_parser("run", help="Run a script")
    run_parser.add_argument("script", type=Path, help="Path to script.yaml")
    run_parser.add_argument("--flow", type=str, help="Flow to run (default: main)")
    run_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # history command
    history_parser = subparsers.add_parser("history", help="Show run history")
    history_parser.add_argument("--last", type=int, default=10, help="Number of runs to show")
    history_parser.add_argument("--status", type=str, help="Filter by status")

    # stats command
    subparsers.add_parser("stats", help="Show run statistics")

    args = parser.parse_args()

    if args.command == "run":
        success = run_script(args.script, args.flow, args.verbose)
        return 0 if success else 1

    elif args.command == "history":
        show_history(args.last, args.status)
        return 0

    elif args.command == "stats":
        show_stats()
        return 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
