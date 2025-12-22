"""
RetroAuto v2 - Code Snippets Library

Pre-built code templates and patterns for common automation tasks.
Part of RetroScript Phase 6 - Error Handling + Templates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class SnippetCategory(Enum):
    """Categories for code snippets."""

    BASIC = auto()  # Basic patterns
    GAME_BOT = auto()  # Game automation
    SCRAPER = auto()  # Data scraping
    UTILITY = auto()  # Utility functions
    ERROR_HANDLING = auto()  # Error handling patterns
    TESTING = auto()  # Test patterns


@dataclass
class Snippet:
    """A code snippet template."""

    name: str
    description: str
    category: SnippetCategory
    prefix: str  # Trigger prefix (e.g., "repeat")
    body: str  # Template body with ${placeholders}
    placeholders: dict[str, str] = field(default_factory=dict)  # Default values


# ─────────────────────────────────────────────────────────────
# Basic Patterns
# ─────────────────────────────────────────────────────────────

BASIC_SNIPPETS = [
    Snippet(
        name="Flow Definition",
        description="Create a new flow",
        category=SnippetCategory.BASIC,
        prefix="flow",
        body="""flow ${1:name} {
    ${0}
}""",
    ),
    Snippet(
        name="Repeat Loop",
        description="Repeat block N times",
        category=SnippetCategory.BASIC,
        prefix="repeat",
        body="""repeat ${1:3} {
    ${0}
}""",
    ),
    Snippet(
        name="Retry Block",
        description="Retry on error with count",
        category=SnippetCategory.BASIC,
        prefix="retry",
        body="""retry ${1:5} {
    ${0}
}""",
    ),
    Snippet(
        name="If Statement",
        description="Conditional statement",
        category=SnippetCategory.BASIC,
        prefix="if",
        body="""if ${1:condition} {
    ${0}
}""",
    ),
    Snippet(
        name="If-Else Statement",
        description="Conditional with else branch",
        category=SnippetCategory.BASIC,
        prefix="ifelse",
        body="""if ${1:condition} {
    ${2}
} else {
    ${0}
}""",
    ),
    Snippet(
        name="For Loop",
        description="Iterate over range",
        category=SnippetCategory.BASIC,
        prefix="for",
        body="""for ${1:i} in range(${2:10}) {
    ${0}
}""",
    ),
    Snippet(
        name="While Loop",
        description="Loop while condition",
        category=SnippetCategory.BASIC,
        prefix="while",
        body="""while ${1:condition} {
    ${0}
}""",
    ),
    Snippet(
        name="Try-Catch",
        description="Error handling block",
        category=SnippetCategory.BASIC,
        prefix="try",
        body="""try {
    ${1}
} catch ${2:err} {
    log("Error: " + ${2:err})
    ${0}
}""",
    ),
    Snippet(
        name="Import Module",
        description="Import external module",
        category=SnippetCategory.BASIC,
        prefix="import",
        body="""import "${1:path/to/module}" as ${2:alias}""",
    ),
]

# ─────────────────────────────────────────────────────────────
# Game Bot Patterns
# ─────────────────────────────────────────────────────────────

GAME_BOT_SNIPPETS = [
    Snippet(
        name="Click Target",
        description="Find and click target",
        category=SnippetCategory.GAME_BOT,
        prefix="clicktarget",
        body="""$target = find(${1:button_img})
if $target {
    click($target.x, $target.y)
    sleep(${2:500ms})
}""",
    ),
    Snippet(
        name="Combat Loop",
        description="Basic combat automation loop",
        category=SnippetCategory.GAME_BOT,
        prefix="combat",
        body="""# Combat automation loop
repeat ${1:100} {
    $enemy = find(enemy_img)
    if $enemy {
        click($enemy.x, $enemy.y)
        sleep(${2:200ms})

        # Use skills
        press("${3:1}")
        sleep(${4:1s})
    }

    # Random delay for anti-detection
    sleep(${5:500ms})
}""",
    ),
    Snippet(
        name="Resource Gathering",
        description="Gather resources in game",
        category=SnippetCategory.GAME_BOT,
        prefix="gather",
        body="""# Resource gathering loop
flow gather_resources {
    repeat ${1:50} {
        $resource = find(${2:ore_img})
        if $resource {
            click($resource.x, $resource.y)
            sleep(${3:3s})  # Wait for gathering
        } else {
            # Move to next area
            press("w")
            sleep(${4:2s})
        }
    }
}""",
    ),
    Snippet(
        name="Anti-AFK",
        description="Prevent AFK detection",
        category=SnippetCategory.GAME_BOT,
        prefix="antiafk",
        body="""# Anti-AFK movement
flow anti_afk {
    while true {
        # Random movement
        $keys = ["w", "a", "s", "d"]
        $key = $keys[random(0, 3)]
        press($key)
        sleep(${1:100ms})

        # Wait before next action
        sleep(${2:30s})
    }
}""",
    ),
    Snippet(
        name="Inventory Check",
        description="Check and manage inventory",
        category=SnippetCategory.GAME_BOT,
        prefix="inventory",
        body="""# Open and check inventory
press("${1:i}")  # Open inventory
sleep(${2:500ms})

$item = find(${3:target_item})
if $item {
    click($item.x, $item.y)
    ${0}
}

press("${1:i}")  # Close inventory""",
    ),
]

# ─────────────────────────────────────────────────────────────
# Error Handling Patterns
# ─────────────────────────────────────────────────────────────

ERROR_HANDLING_SNIPPETS = [
    Snippet(
        name="Retry with Fallback",
        description="Retry with fallback action",
        category=SnippetCategory.ERROR_HANDLING,
        prefix="retryfallback",
        body="""retry ${1:3} {
    ${2:primary_action}
} else {
    log("Retry failed, using fallback")
    ${0:fallback_action}
}""",
    ),
    Snippet(
        name="Safe Click",
        description="Click with existence check",
        category=SnippetCategory.ERROR_HANDLING,
        prefix="safeclick",
        body="""$target = find(${1:button})
if $target {
    click($target.x, $target.y)
} else {
    log("Target not found: ${1:button}")
    ${0}
}""",
    ),
    Snippet(
        name="Wait with Timeout",
        description="Wait for target with timeout",
        category=SnippetCategory.ERROR_HANDLING,
        prefix="waittimeout",
        body="""$result = wait(${1:target}, timeout=${2:10s})
match $result:
    Found: ${3:success_action}
    Timeout: ${0:timeout_action}""",
    ),
]

# ─────────────────────────────────────────────────────────────
# Testing Patterns
# ─────────────────────────────────────────────────────────────

TESTING_SNIPPETS = [
    Snippet(
        name="Test Block",
        description="Create a test block",
        category=SnippetCategory.TESTING,
        prefix="test",
        body="""@test "${1:test name}" {
    ${0}
    assert ${2:condition}
}""",
    ),
    Snippet(
        name="Mock Function",
        description="Mock a function for testing",
        category=SnippetCategory.TESTING,
        prefix="mock",
        body="""@test "${1:test name}" {
    mock find(${2:target}) -> Found(${3:100}, ${4:200})
    ${0}
}""",
    ),
]

# ─────────────────────────────────────────────────────────────
# Utility Patterns
# ─────────────────────────────────────────────────────────────

UTILITY_SNIPPETS = [
    Snippet(
        name="Random Delay",
        description="Sleep for random duration",
        category=SnippetCategory.UTILITY,
        prefix="randomsleep",
        body="""sleep(${1:500ms} + random(0, ${2:500})ms)""",
    ),
    Snippet(
        name="Log with Timestamp",
        description="Log message with timestamp",
        category=SnippetCategory.UTILITY,
        prefix="logts",
        body="""log("[" + timestamp() + "] ${1:message}")""",
    ),
    Snippet(
        name="Screen Region",
        description="Search in specific region",
        category=SnippetCategory.UTILITY,
        prefix="region",
        body="""$result = find(${1:target}, roi=(${2:x}, ${3:y}, ${4:width}, ${5:height}))""",
    ),
]


class SnippetLibrary:
    """Library of code snippets for RetroScript.

    Usage:
        library = SnippetLibrary()
        snippets = library.search("combat")
        snippet = library.get_by_prefix("repeat")
    """

    def __init__(self) -> None:
        self._snippets: list[Snippet] = []
        self._by_prefix: dict[str, Snippet] = {}
        self._load_default_snippets()

    def _load_default_snippets(self) -> None:
        """Load all default snippets."""
        all_snippets = (
            BASIC_SNIPPETS
            + GAME_BOT_SNIPPETS
            + ERROR_HANDLING_SNIPPETS
            + TESTING_SNIPPETS
            + UTILITY_SNIPPETS
        )
        for snippet in all_snippets:
            self.add(snippet)

    def add(self, snippet: Snippet) -> None:
        """Add a snippet to the library."""
        self._snippets.append(snippet)
        self._by_prefix[snippet.prefix] = snippet

    def get_by_prefix(self, prefix: str) -> Snippet | None:
        """Get snippet by trigger prefix."""
        return self._by_prefix.get(prefix)

    def search(self, query: str) -> list[Snippet]:
        """Search snippets by name, description, or prefix."""
        query_lower = query.lower()
        results = []
        for snippet in self._snippets:
            if (
                query_lower in snippet.name.lower()
                or query_lower in snippet.description.lower()
                or query_lower in snippet.prefix.lower()
            ):
                results.append(snippet)
        return results

    def get_by_category(self, category: SnippetCategory) -> list[Snippet]:
        """Get all snippets in a category."""
        return [s for s in self._snippets if s.category == category]

    def get_all(self) -> list[Snippet]:
        """Get all snippets."""
        return self._snippets.copy()

    def expand(self, prefix: str, values: dict[str, str] | None = None) -> str | None:
        """Expand a snippet with given placeholder values.

        Args:
            prefix: Snippet trigger prefix
            values: Dict of placeholder index to value (e.g., {"1": "my_value"})

        Returns:
            Expanded snippet body or None if not found
        """
        snippet = self.get_by_prefix(prefix)
        if not snippet:
            return None

        result = snippet.body
        if values:
            for key, value in values.items():
                result = result.replace(f"${{{key}}}", value)
                result = result.replace(f"${key}", value)

        # Remove remaining placeholders
        import re

        result = re.sub(r"\$\{?\d+:?[^}]*\}?", "", result)

        return result
