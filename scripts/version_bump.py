#!/usr/bin/env python3
"""
RetroAuto v2 - Smart Version Manager

Automatically manages version numbers in pyproject.toml.

Version Format: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes (manual)
- MINOR: New features (--minor)
- PATCH: Bug fixes, improvements (--patch, default)

Usage:
    python scripts/version_bump.py           # Bump patch (2.0.0 -> 2.0.1)
    python scripts/version_bump.py --minor   # Bump minor (2.0.0 -> 2.1.0)
    python scripts/version_bump.py --major   # Bump major (2.0.0 -> 3.0.0)
    python scripts/version_bump.py --show    # Show current version
    python scripts/version_bump.py --set 2.1.0  # Set specific version
"""

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
VERSION_PATTERN = re.compile(r'^version = "(\d+)\.(\d+)\.(\d+)"', re.MULTILINE)


def get_current_version() -> tuple[int, int, int]:
    """Get current version from pyproject.toml."""
    content = PYPROJECT_PATH.read_text(encoding="utf-8")
    match = VERSION_PATTERN.search(content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def set_version(major: int, minor: int, patch: int) -> str:
    """Set version in pyproject.toml."""
    content = PYPROJECT_PATH.read_text(encoding="utf-8")
    new_version = f'version = "{major}.{minor}.{patch}"'
    new_content = VERSION_PATTERN.sub(new_version, content)
    PYPROJECT_PATH.write_text(new_content, encoding="utf-8")
    return f"{major}.{minor}.{patch}"


def bump_patch() -> str:
    """Bump patch version: 2.0.0 -> 2.0.1."""
    major, minor, patch = get_current_version()
    return set_version(major, minor, patch + 1)


def bump_minor() -> str:
    """Bump minor version: 2.0.5 -> 2.1.0."""
    major, minor, patch = get_current_version()
    return set_version(major, minor + 1, 0)


def bump_major() -> str:
    """Bump major version: 2.5.3 -> 3.0.0."""
    major, minor, patch = get_current_version()
    return set_version(major + 1, 0, 0)


def get_version_for_commit_message() -> str:
    """Get version string for commit message."""
    major, minor, patch = get_current_version()
    return f"v{major}.{minor}.{patch}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Smart Version Manager")
    parser.add_argument("--patch", action="store_true", help="Bump patch version (default)")
    parser.add_argument("--minor", action="store_true", help="Bump minor version")
    parser.add_argument("--major", action="store_true", help="Bump major version")
    parser.add_argument("--show", action="store_true", help="Show current version")
    parser.add_argument("--set", type=str, help="Set specific version (e.g., 2.1.0)")
    args = parser.parse_args()

    try:
        if args.show:
            major, minor, patch = get_current_version()
            print(f"{major}.{minor}.{patch}")
            return 0

        if args.set:
            parts = args.set.split(".")
            if len(parts) != 3:
                print("Error: Version must be in format X.Y.Z")
                return 1
            new_version = set_version(int(parts[0]), int(parts[1]), int(parts[2]))
            print(f"Version set to: {new_version}")
            return 0

        old_version = ".".join(map(str, get_current_version()))

        if args.major:
            new_version = bump_major()
            bump_type = "MAJOR"
        elif args.minor:
            new_version = bump_minor()
            bump_type = "MINOR"
        else:
            new_version = bump_patch()
            bump_type = "PATCH"

        print(f"📦 Version bumped ({bump_type}): {old_version} → {new_version}")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
