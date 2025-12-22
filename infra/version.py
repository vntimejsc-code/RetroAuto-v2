"""
RetroAuto v2 - Version Management

Automatic versioning with changelog and git integration.
"""

import subprocess
from datetime import datetime
from pathlib import Path

# Current version - update this when releasing
__version__ = "2.0.0"
__build__ = "20251222.013"

VERSION_FILE = Path(__file__).parent.parent / "VERSION"
CHANGELOG_FILE = Path(__file__).parent.parent / "CHANGELOG.md"


def get_version() -> str:
    """Get current version string."""
    return f"{__version__}+{__build__}"


def bump_build() -> str:
    """
    Auto-increment build number and update version.py file.

    Build format: YYYYMMDD.NNN (date + daily increment)
    Returns:
        New build string
    """
    from datetime import datetime

    today = datetime.now().strftime("%Y%m%d")
    current_date = __build__.split(".")[0]

    # Same day - increment counter, new day - reset to 1
    counter = int(__build__.split(".")[1]) + 1 if today == current_date else 1

    new_build = f"{today}.{counter:03d}"

    # Update this file
    version_file = Path(__file__)
    content = version_file.read_text(encoding="utf-8")
    content = content.replace(f'__build__ = "{__build__}"', f'__build__ = "{new_build}"')
    version_file.write_text(content, encoding="utf-8")

    print(f"📦 Build updated: {__build__} -> {new_build}")
    return new_build


def get_version_tuple() -> tuple[int, int, int]:
    """Get version as tuple (major, minor, patch)."""
    parts = __version__.split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def bump_version(part: str = "patch") -> str:
    """
    Bump version number.

    Args:
        part: "major", "minor", or "patch"

    Returns:
        New version string
    """
    major, minor, patch = get_version_tuple()

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    return f"{major}.{minor}.{patch}"


def git_commit(message: str, auto_add: bool = True) -> bool:
    """
    Create git commit with message.

    Args:
        message: Commit message
        auto_add: Auto-add all changes

    Returns:
        True if successful
    """
    try:
        cwd = Path(__file__).parent.parent

        if auto_add:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=cwd,
                check=True,
                capture_output=True,
            )

        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=cwd,
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def git_tag(tag: str, message: str = "") -> bool:
    """Create git tag."""
    try:
        cwd = Path(__file__).parent.parent
        cmd = ["git", "tag", "-a", tag, "-m", message or tag]
        subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def add_changelog_entry(
    version: str,
    changes: list[str],
    category: str = "Changed",
) -> None:
    """
    Add entry to CHANGELOG.md.

    Args:
        version: Version string
        changes: List of change descriptions
        category: "Added", "Changed", "Fixed", "Removed"
    """
    date = datetime.now().strftime("%Y-%m-%d")

    entry = f"\n## [{version}] - {date}\n\n"
    entry += f"### {category}\n\n"
    for change in changes:
        entry += f"- {change}\n"

    if CHANGELOG_FILE.exists():
        content = CHANGELOG_FILE.read_text(encoding="utf-8")
        # Insert after header
        if "# Changelog" in content:
            parts = content.split("# Changelog", 1)
            new_content = parts[0] + "# Changelog\n" + entry + parts[1].lstrip("\n")
        else:
            new_content = "# Changelog\n" + entry + "\n" + content
    else:
        new_content = "# Changelog\n\nAll notable changes to RetroAuto v2.\n" + entry

    CHANGELOG_FILE.write_text(new_content, encoding="utf-8")


def release(
    changes: list[str],
    bump: str = "patch",
    category: str = "Changed",
) -> str:
    """
    Create a new release with version bump, changelog, and git commit/tag.

    Args:
        changes: List of change descriptions
        bump: Version bump type ("major", "minor", "patch")
        category: Changelog category

    Returns:
        New version string
    """
    new_version = bump_version(bump)

    # Update changelog
    add_changelog_entry(new_version, changes, category)

    # Commit
    commit_msg = f"Release v{new_version}\n\n"
    for change in changes:
        commit_msg += f"- {change}\n"

    git_commit(commit_msg)

    # Tag
    git_tag(f"v{new_version}", f"Version {new_version}")

    return new_version


def quick_save(description: str) -> bool:
    """
    Quick save changes with auto-commit.

    Args:
        description: Short description of changes

    Returns:
        True if successful
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    message = f"[{timestamp}] {description}"
    return git_commit(message)
