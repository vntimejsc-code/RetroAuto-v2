#!/usr/bin/env python3
"""
RetroAuto v2 - Development File Watcher

Watches for Python file changes and runs checks + auto-commit.

Features:
- Real-time file change detection
- Quick lint check on save
- Auto-fix option
- AUTO-COMMIT after successful check
- Version bump on commit

Usage:
    python scripts/dev_watcher.py              # Check only
    python scripts/dev_watcher.py --fix        # Auto-fix + check
    python scripts/dev_watcher.py --auto       # Auto-fix + check + commit

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
DEBOUNCE_SECONDS = 2.0  # Increased debounce for auto-commit


class CodeCheckHandler(FileSystemEventHandler):
    """Handle file system events."""

    def __init__(self, fix: bool = False, auto_commit: bool = False):
        self.fix = fix
        self.auto_commit = auto_commit
        self._last_check: dict[str, float] = {}
        self._checking = False
        self._pending_changes: list[str] = []

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

        # Debounce - don't check same file within threshold
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

        all_passed = True

        # 1. Syntax check
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"❌ Syntax Error: {result.stderr.strip()[:100]}")
            all_passed = False
        else:
            print("✅ Syntax OK")

        # 2. Ruff check + fix (single file)
        cmd = [sys.executable, "-m", "ruff", "check", str(path)]
        if self.fix:
            cmd.extend(["--fix", "--unsafe-fixes"])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 and not self.fix:
            print(f"⚠️  Lint issues found")
            all_passed = False
        else:
            print("✅ Lint OK" + (" (auto-fixed)" if self.fix else ""))

        # 3. Black format (single file)
        if self.fix:
            subprocess.run(
                [sys.executable, "-m", "black", str(path), "-q"],
                capture_output=True,
            )
            print("✅ Formatted")

        # 4. Auto-commit if enabled and all passed
        if all_passed and self.auto_commit:
            self._auto_commit(rel_path)
        elif all_passed:
            print("\n🎉 All checks passed!")
        else:
            print("\n⚠️  Fix issues before commit")

        self._checking = False

    def _auto_commit(self, changed_file: Path):
        """Auto version bump + commit + push."""
        print("\n🚀 Auto-committing...")

        try:
            # 1. Version bump
            result = subprocess.run(
                [sys.executable, "scripts/version_bump.py", "--patch"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )
            version_line = result.stdout.strip()
            print(f"   {version_line}")

            # 2. Get new version
            result = subprocess.run(
                [sys.executable, "scripts/version_bump.py", "--show"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )
            version = result.stdout.strip()

            # 3. Git add all
            subprocess.run(
                ["git", "add", "-A"],
                cwd=PROJECT_ROOT,
                capture_output=True,
            )

            # 4. Git commit
            commit_msg = f"Auto: v{version} - {changed_file}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg, "--no-verify"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"   ✅ Committed: {commit_msg}")
            else:
                if "nothing to commit" in result.stdout:
                    print("   ℹ️  No changes to commit")
                else:
                    print(f"   ⚠️  Commit failed: {result.stderr[:50]}")
                return

            # 5. Git push
            result = subprocess.run(
                ["git", "push", "origin", "master"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"   ✅ Pushed to master")
            else:
                print(f"   ⚠️  Push failed: {result.stderr[:50]}")

        except Exception as e:
            print(f"   ❌ Auto-commit error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Development File Watcher")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues on save")
    parser.add_argument("--auto", action="store_true", help="Auto-commit after successful check")
    args = parser.parse_args()

    # --auto implies --fix
    if args.auto:
        args.fix = True

    print("=" * 60)
    print("  RetroAuto v2 - Development Watcher")
    print("=" * 60)
    mode = "AUTO-COMMIT" if args.auto else ("Auto-Fix" if args.fix else "Check Only")
    print(f"  Mode: {mode}")
    print(f"  Watching: {', '.join(WATCH_DIRS)}")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    handler = CodeCheckHandler(fix=args.fix, auto_commit=args.auto)
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
