#!/usr/bin/env python3
"""
RetroAuto v2 - Changelog Generator

Generates CHANGELOG.md from git commits since last release.

Features:
- Groups commits by type (Added, Changed, Fixed)
- Extracts version bumps
- Maintains history between runs

Usage:
    python scripts/generate_changelog.py           # Generate/update changelog
    python scripts/generate_changelog.py --since 2.0.0  # Since specific version
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CHANGELOG_PATH = PROJECT_ROOT / "docs" / "CHANGELOG.md"


def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
    match = re.search(r'version = "(\d+\.\d+\.\d+)"', content)
    return match.group(1) if match else "0.0.0"


def get_git_commits(since_tag: str | None = None, limit: int = 50) -> list[dict]:
    """Get git commits with parsed info."""
    cmd = ["git", "log", f"-{limit}", "--pretty=format:%H|%s|%ai"]
    if since_tag:
        cmd.insert(2, f"{since_tag}..HEAD")
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        return []
    
    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            commits.append({
                "hash": parts[0][:7],
                "message": parts[1],
                "date": parts[2][:10],
            })
    return commits


def categorize_commit(message: str) -> str | None:
    """Categorize commit message into changelog sections."""
    msg_lower = message.lower()
    
    # Feature patterns
    if any(p in msg_lower for p in ["feat:", "feature:", "add:", "added", "new:", "implement"]):
        return "Added"
    
    # Fix patterns
    if any(p in msg_lower for p in ["fix:", "fixed", "bug:", "bugfix", "hotfix"]):
        return "Fixed"
    
    # Change patterns
    if any(p in msg_lower for p in ["change:", "update:", "refactor:", "improve", "config:"]):
        return "Changed"
    
    # Remove patterns
    if any(p in msg_lower for p in ["remove:", "delete:", "deprecate"]):
        return "Removed"
    
    # Auto-commits
    if msg_lower.startswith("auto:"):
        return "Changed"
    
    # Skip docs, chore, etc.
    if any(p in msg_lower for p in ["docs:", "chore:", "test:", "ci:", "merge"]):
        return None
    
    return "Changed"  # Default


def clean_commit_message(message: str) -> str:
    """Clean up commit message for changelog."""
    # Remove prefixes
    prefixes = ["feat:", "fix:", "chore:", "docs:", "refactor:", "auto:", "config:"]
    for prefix in prefixes:
        if message.lower().startswith(prefix):
            message = message[len(prefix):].strip()
            break
    
    # Capitalize first letter
    if message:
        message = message[0].upper() + message[1:]
    
    return message


def generate_changelog_section(version: str, commits: list[dict]) -> str:
    """Generate a changelog section for a version."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    lines = [
        f"## [{version}] - {today}",
        "",
    ]
    
    # Group by category
    categories: dict[str, list[str]] = {}
    for commit in commits:
        cat = categorize_commit(commit["message"])
        if cat:
            clean_msg = clean_commit_message(commit["message"])
            categories.setdefault(cat, []).append(f"- {clean_msg}")
    
    # Output in order
    for cat in ["Added", "Changed", "Fixed", "Removed"]:
        if cat in categories:
            lines.append(f"### {cat}")
            lines.extend(categories[cat])
            lines.append("")
    
    return "\n".join(lines)


def update_changelog(new_section: str) -> bool:
    """Update CHANGELOG.md with new section."""
    if CHANGELOG_PATH.exists():
        content = CHANGELOG_PATH.read_text(encoding="utf-8")
        # Check if this version already exists
        version = re.search(r'\[(\d+\.\d+\.\d+)\]', new_section)
        if version and f"[{version.group(1)}]" in content:
            # Update existing section (find and replace)
            print(f"   ℹ️  Version {version.group(1)} already in changelog")
            return False
        
        # Insert after header
        if "# Changelog" in content:
            parts = content.split("\n## ", 1)
            if len(parts) == 2:
                new_content = f"{parts[0]}\n{new_section}\n## {parts[1]}"
            else:
                new_content = f"{content}\n\n{new_section}"
        else:
            new_content = f"# Changelog\n\n{new_section}\n\n{content}"
    else:
        new_content = f"# Changelog\n\nAll notable changes to RetroAuto v2.\n\n{new_section}"
    
    CHANGELOG_PATH.write_text(new_content, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate changelog")
    parser.add_argument("--since", type=str, help="Generate since specific tag/version")
    parser.add_argument("--limit", type=int, default=30, help="Max commits to process")
    args = parser.parse_args()
    
    print("=" * 60)
    print("  RetroAuto v2 - Changelog Generator")
    print("=" * 60)
    
    version = get_current_version()
    print(f"\n📦 Current version: {version}")
    
    print("\n📜 Fetching git commits...")
    commits = get_git_commits(since_tag=args.since, limit=args.limit)
    print(f"   Found {len(commits)} commits")
    
    if not commits:
        print("   ℹ️  No new commits to add")
        return 0
    
    print("\n📝 Generating changelog section...")
    section = generate_changelog_section(version, commits)
    
    print("\n💾 Updating CHANGELOG.md...")
    if update_changelog(section):
        print("   ✅ Changelog updated!")
    else:
        print("   ℹ️  No changes made")
    
    print(f"\n📄 Changelog saved to: {CHANGELOG_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
