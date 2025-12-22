"""
RetroAuto v2 - Project Scaffolding

Create new RetroScript project structures with templates.
Part of RetroScript Phase 7 - Tools + Productivity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


class ProjectTemplate(Enum):
    """Available project templates."""

    BASIC = auto()  # Simple single-file project
    GAME_BOT = auto()  # Game automation project
    SCRAPER = auto()  # Data scraping project
    TESTING = auto()  # Testing-focused project


@dataclass
class ProjectConfig:
    """Project configuration (retro.toml)."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    entry_point: str = "main.retro"
    assets_dir: str = "assets"
    timeout: str = "30s"
    permissions: list[str] = field(default_factory=list)
    dependencies: dict[str, str] = field(default_factory=dict)


class ProjectScaffold:
    """Create new RetroScript project structures.

    Usage:
        scaffold = ProjectScaffold()
        scaffold.create("my_project", ProjectTemplate.GAME_BOT)
    """

    def __init__(self, base_path: str | Path | None = None) -> None:
        self.base_path = Path(base_path) if base_path else Path.cwd()

    def create(
        self,
        name: str,
        template: ProjectTemplate = ProjectTemplate.BASIC,
        config: ProjectConfig | None = None,
    ) -> Path:
        """Create a new project.

        Args:
            name: Project name (and directory name)
            template: Project template to use
            config: Optional project configuration

        Returns:
            Path to created project directory
        """
        project_dir = self.base_path / name

        # Create directory structure
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "assets").mkdir(exist_ok=True)
        (project_dir / "lib").mkdir(exist_ok=True)
        (project_dir / "tests").mkdir(exist_ok=True)

        # Create config
        cfg = config or ProjectConfig(name=name)
        self._write_config(project_dir / "retro.toml", cfg)

        # Create template files
        self._create_template_files(project_dir, template, cfg)

        # Create README
        self._write_readme(project_dir, cfg)

        # Create .gitignore
        self._write_gitignore(project_dir)

        return project_dir

    def _write_config(self, path: Path, config: ProjectConfig) -> None:
        """Write retro.toml configuration file."""
        lines = [
            "[project]",
            f'name = "{config.name}"',
            f'version = "{config.version}"',
            f'description = "{config.description}"',
            f'author = "{config.author}"',
            "",
            "[script]",
            f'entry_point = "{config.entry_point}"',
            f'assets_dir = "{config.assets_dir}"',
            f'timeout = "{config.timeout}"',
            "",
            "[permissions]",
        ]

        for perm in config.permissions or ["mouse", "keyboard", "screen"]:
            lines.append(f"{perm} = true")

        lines.append("")
        lines.append("[dependencies]")
        for dep, ver in config.dependencies.items():
            lines.append(f'{dep} = "{ver}"')

        path.write_text("\n".join(lines), encoding="utf-8")

    def _create_template_files(
        self,
        project_dir: Path,
        template: ProjectTemplate,
        config: ProjectConfig,
    ) -> None:
        """Create template-specific files."""
        main_file = project_dir / config.entry_point

        if template == ProjectTemplate.BASIC:
            main_file.write_text(self._get_basic_template(config.name), encoding="utf-8")

        elif template == ProjectTemplate.GAME_BOT:
            main_file.write_text(self._get_game_bot_template(config.name), encoding="utf-8")
            # Create utility lib
            lib_file = project_dir / "lib" / "utils.retro"
            lib_file.write_text(self._get_utils_template(), encoding="utf-8")

        elif template == ProjectTemplate.SCRAPER:
            main_file.write_text(self._get_scraper_template(config.name), encoding="utf-8")

        elif template == ProjectTemplate.TESTING:
            main_file.write_text(self._get_testing_template(config.name), encoding="utf-8")
            # Create example test
            test_file = project_dir / "tests" / "test_main.retro"
            test_file.write_text(self._get_test_template(), encoding="utf-8")

    def _write_readme(self, project_dir: Path, config: ProjectConfig) -> None:
        """Write README.md file."""
        content = f"""# {config.name}

{config.description or 'A RetroScript automation project.'}

## Quick Start

1. Open this project in RetroAuto
2. Add your image assets to the `assets/` folder
3. Edit `{config.entry_point}` to customize the script
4. Run with F5 or the Run button

## Project Structure

```
{config.name}/
├── {config.entry_point}    # Main script
├── assets/                  # Image assets
├── lib/                     # Utility modules
├── tests/                   # Test scripts
├── retro.toml              # Project config
└── README.md               # This file
```

## Configuration

See `retro.toml` for project settings.

## License

MIT
"""
        (project_dir / "README.md").write_text(content, encoding="utf-8")

    def _write_gitignore(self, project_dir: Path) -> None:
        """Write .gitignore file."""
        content = """# RetroScript
*.log
*.tmp
__pycache__/
.cache/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
"""
        (project_dir / ".gitignore").write_text(content, encoding="utf-8")

    def _get_basic_template(self, name: str) -> str:
        """Get basic project template."""
        return f"""# {name} - Main Script
# Created with RetroAuto

@config {{
    timeout = 30s
}}

flow main {{
    log("Starting {name}...")

    # Your automation code here
    $target = find(button_img)
    if $target {{
        click($target.x, $target.y)
    }}

    log("Done!")
}}
"""

    def _get_game_bot_template(self, name: str) -> str:
        """Get game bot project template."""
        return f"""# {name} - Game Bot
# Created with RetroAuto

import "lib/utils" as utils

@config {{
    timeout = 60s
}}

@permissions {{
    mouse = true
    keyboard = true
    screen = true
}}

# Constants
const RETRY_COUNT = 5
const COMBAT_DELAY = 500ms

# Main entry point
flow main {{
    log("Starting {name}...")

    repeat 100 {{
        run(combat_loop)
        run(check_health)
        utils.random_pause()
    }}
}}

# Combat automation
flow combat_loop {{
    $enemy = find(enemy_img)
    if $enemy {{
        click($enemy.x, $enemy.y)
        sleep(COMBAT_DELAY)

        # Use skills
        press("1")
        sleep(200ms)
    }}
}}

# Health check
flow check_health {{
    $health_low = find(health_low_img)
    if $health_low {{
        log("Health low, using potion")
        press("h")
        sleep(1s)
    }}
}}
"""

    def _get_scraper_template(self, name: str) -> str:
        """Get scraper project template."""
        return f"""# {name} - Data Scraper
# Created with RetroAuto

@config {{
    timeout = 120s
}}

flow main {{
    log("Starting {name} scraper...")

    # Navigate to target
    $nav = find(nav_button)
    if $nav {{
        click($nav.x, $nav.y)
        sleep(2s)
    }}

    # Collect data
    repeat 10 {{
        run(collect_item)
        run(next_page)
    }}

    log("Scraping complete!")
}}

flow collect_item {{
    $item = find(item_img)
    if $item {{
        click($item.x, $item.y)
        sleep(500ms)
        # Copy data
        hotkey("ctrl+c")
    }}
}}

flow next_page {{
    $next = find(next_page_img)
    if $next {{
        click($next.x, $next.y)
        sleep(1s)
    }}
}}
"""

    def _get_testing_template(self, name: str) -> str:
        """Get testing project template."""
        return f"""# {name} - With Tests
# Created with RetroAuto

@config {{
    timeout = 30s
}}

flow main {{
    log("Running {name}...")
    $result = run(do_action)
    log("Result: " + $result)
}}

# Main action to test
flow do_action {{
    $target = find(button_img)
    if $target {{
        click($target.x, $target.y)
        return "success"
    }}
    return "not_found"
}}
"""

    def _get_test_template(self) -> str:
        """Get test file template."""
        return """# Test suite for main script

@test "do_action finds button" {
    mock find(button_img) -> Found(100, 200)
    $result = run(do_action)
    assert $result == "success"
}

@test "do_action handles missing button" {
    mock find(button_img) -> NotFound
    $result = run(do_action)
    assert $result == "not_found"
}
"""

    def _get_utils_template(self) -> str:
        """Get utility library template."""
        return """# Utility functions

# Random pause for anti-detection
flow random_pause {
    $delay = 500 + random(0, 1000)
    sleep($delay ms)
}

# Safe click with retry
flow safe_click($target) {
    retry 3 {
        $found = find($target)
        if $found {
            click($found.x, $found.y)
            return true
        }
    }
    return false
}

# Wait for any of multiple targets
flow wait_any_of($targets) {
    retry 30 {
        for $t in $targets {
            $found = find($t)
            if $found {
                return $found
            }
        }
        sleep(100ms)
    }
    return null
}
"""


def create_project(
    name: str,
    template: str = "basic",
    path: str | None = None,
) -> str:
    """Convenience function to create a new project.

    Args:
        name: Project name
        template: Template name (basic, game_bot, scraper, testing)
        path: Base path for project

    Returns:
        Path to created project
    """
    template_map = {
        "basic": ProjectTemplate.BASIC,
        "game_bot": ProjectTemplate.GAME_BOT,
        "scraper": ProjectTemplate.SCRAPER,
        "testing": ProjectTemplate.TESTING,
    }

    scaffold = ProjectScaffold(path)
    project_path = scaffold.create(name, template_map.get(template, ProjectTemplate.BASIC))
    return str(project_path)
