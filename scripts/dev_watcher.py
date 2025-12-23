#!/usr/bin/env python3
"""
RetroAuto v2 - Development File Watcher

Watches for Python file changes and runs quick checks automatically.

Features:
- Real-time file change detection
- Quick lint check on save
- Auto-fix option
- Notification on errors

Usage:
    python scripts/dev_watcher.py           # Start watcher
    python scripts/dev_watcher.py --fix     # Auto-fix on save
    python scripts/dev_watcher.py --notify  # Desktop notifications

Press Ctrl+C to stop.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

# Try to import watchdog
try:
    from watchdog.events import FileModifiedEvent, FileSystemEventHandler
    from watchdog.observers import Observer

    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    print("⚠️  watchdog not installed. Run: pip install watchdog")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent
WATCH_DIRS = ["app", "core", "vision", "input", "infra"]
DEBOUNCE_SECONDS = 1.0


class CodeCheckHandler(FileSystemEventHandler):
    """Handle file system events."""

    def __init__(self, fix: bool = False, notify: bool = False):
        self.fix = fix
        self.notify = notify
        self._last_check: dict[str, float] = {}
        self._checking = False

    def on_modified(self, event):
        if self._checking:
            return

        if not isinstance(event, FileModifiedEvent):
            return

        path = Path(event.src_path)

        # Only Python files
        if path.suffix != ".py":
            return

        # Ignore __pycache__
        if "__pycache__" in str(path):
            return

        # Debounce - don't check same file within 1 second
        now = time.time()
        last = self._last_check.get(str(path), 0)
        if now - last < DEBOUNCE_SECONDS:
            return
        self._last_check[str(path)] = now

        self._run_quick_check(path)

    def _run_quick_check(self, path: Path):
        """Run quick check on a single file."""
        self._checking = True
        rel_path = path.relative_to(PROJECT_ROOT)
        print(f"\n{'='*60}")
        print(f"📝 File changed: {rel_path}")
        print(f"{'='*60}")

        errors = []

        # 1. Syntax check
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            errors.append(f"❌ Syntax Error: {result.stderr.strip()[:100]}")
        else:
            print("✅ Syntax OK")

        # 2. Ruff check (single file)
        cmd = [sys.executable, "-m", "ruff", "check", str(path)]
        if self.fix:
            cmd.append("--fix")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            issues = result.stdout.strip().split("\n")[:5]
            for issue in issues:
                if issue.strip():
                    errors.append(f"⚠️  {issue}")
            if self.fix:
                print("🔧 Auto-fixed lint issues")
        else:
            print("✅ Lint OK")

        # 3. Black check (single file)
        if self.fix:
            subprocess.run(
                [sys.executable, "-m", "black", str(path), "-q"],
                capture_output=True,
            )
            print("🔧 Formatted with Black")
        else:
            result = subprocess.run(
                [sys.executable, "-m", "black", "--check", str(path)],
                capture_output=True,
            )
            if result.returncode != 0:
                errors.append("⚠️  Needs formatting (run with --fix)")
            else:
                print("✅ Format OK")

        # Summary
        if errors:
            print("\n" + "\n".join(errors))
            if self.notify:
                self._show_notification("Code Issues", f"{len(errors)} issues in {rel_path}")
        else:
            print("\n🎉 All checks passed!")

        self._checking = False

    def _show_notification(self, title: str, message: str):
        """Show desktop notification (Windows)."""
        try:
            from win11toast import notify

            notify(title, message)
        except ImportError:
            pass  # Notifications not available


def main():
    parser = argparse.ArgumentParser(description="Development File Watcher")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues on save")
    parser.add_argument("--notify", action="store_true", help="Desktop notifications")
    args = parser.parse_args()

    print("=" * 60)
    print("  RetroAuto v2 - Development Watcher")
    print("=" * 60)
    print(f"  Mode: {'Auto-Fix' if args.fix else 'Check Only'}")
    print(f"  Watching: {', '.join(WATCH_DIRS)}")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    handler = CodeCheckHandler(fix=args.fix, notify=args.notify)
    observer = Observer()

    for dir_name in WATCH_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            observer.schedule(handler, str(dir_path), recursive=True)
            print(f"  👁️  Watching: {dir_name}/")

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n\n👋 Watcher stopped.")

    observer.join()


if __name__ == "__main__":
    main()
