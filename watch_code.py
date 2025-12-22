#!/usr/bin/env python3
"""
RetroAuto v2 - File Watcher for Real-time Code Checking

Watches for .py file changes and automatically runs code checks.

Usage:
    python watch_code.py           # Watch and run quick checks
    python watch_code.py --full    # Watch and run full checks
    python watch_code.py --fix     # Watch and auto-fix on change
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:
    print("❌ watchdog not installed. Run: pip install watchdog")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent
WATCH_DIRS = ["app", "core", "vision", "input", "infra", "tests"]
DEBOUNCE_SECONDS = 2  # Wait before running check after change


class CodeCheckHandler(FileSystemEventHandler):
    """Handler that runs code checks on Python file changes."""

    def __init__(self, full: bool = False, fix: bool = False):
        super().__init__()
        self.full = full
        self.fix = fix
        self._last_run = 0
        self._pending_check = False

    def on_modified(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Only react to .py files
        if path.suffix != ".py":
            return

        # Skip __pycache__ and other generated files
        if "__pycache__" in str(path):
            return

        # Debounce: don't run check too frequently
        now = time.time()
        if now - self._last_run < DEBOUNCE_SECONDS:
            return

        self._last_run = now
        self._run_check(path)

    def _run_check(self, changed_file: Path):
        """Run code check."""
        rel_path = changed_file.relative_to(PROJECT_ROOT)

        print()
        print("=" * 60)
        print(f"  📝 File changed: {rel_path}")
        print(f"  ⏰ {time.strftime('%H:%M:%S')}")
        print("=" * 60)

        # Build command
        cmd = [sys.executable, "check_code.py"]
        if self.full:
            cmd.append("--full")
        if self.fix:
            cmd.append("--fix")

        # Run check
        try:
            result = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                timeout=120,
            )

            if result.returncode == 0:
                print("\n  🔔 Ready to commit!")
            else:
                print("\n  ⚠️ Fix issues before committing")

        except subprocess.TimeoutExpired:
            print("\n  ⏱️ Check timed out")
        except Exception as e:
            print(f"\n  ❌ Error: {e}")

        print("\n  👀 Watching for changes... (Ctrl+C to stop)")


def main():
    parser = argparse.ArgumentParser(description="Watch files and run code checks")
    parser.add_argument("--full", action="store_true", help="Run full tests")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    args = parser.parse_args()

    print("=" * 60)
    print("  RetroAuto v2 - File Watcher")
    print("=" * 60)
    print()
    print(f"  Watching: {', '.join(WATCH_DIRS)}")
    print(f"  Mode: {'Full' if args.full else 'Quick'}")
    print(f"  Auto-fix: {'Yes' if args.fix else 'No'}")
    print()
    print("  👀 Watching for changes... (Ctrl+C to stop)")
    print()

    # Setup watcher
    event_handler = CodeCheckHandler(full=args.full, fix=args.fix)
    observer = Observer()

    for dir_name in WATCH_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            observer.schedule(event_handler, str(dir_path), recursive=True)

    # Start watching
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n  👋 Stopping watcher...")
        observer.stop()

    observer.join()
    print("  ✅ Watcher stopped")


if __name__ == "__main__":
    main()
