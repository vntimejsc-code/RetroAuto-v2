"""
RetroAuto v2 - Auto-Completion Provider

Provides intelligent code completion for RetroScript.
Part of RetroScript Phase 5 - Advanced IDE Features.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.dsl.ast import Program


class CompletionKind(Enum):
    """Types of completion items."""

    KEYWORD = auto()
    BUILTIN = auto()
    VARIABLE = auto()
    FLOW = auto()
    IMPORT = auto()
    SNIPPET = auto()


@dataclass
class CompletionItem:
    """A single completion suggestion."""

    label: str  # Display text
    kind: CompletionKind
    detail: str = ""  # Description
    insert_text: str | None = None  # Text to insert (if different from label)
    snippet: str | None = None  # Snippet with placeholders


# ─────────────────────────────────────────────────────────────
# RetroScript Keywords and Builtins
# ─────────────────────────────────────────────────────────────

KEYWORDS = [
    # Core
    CompletionItem("flow", CompletionKind.KEYWORD, "Define a flow", "flow ${1:name} {\n\t$0\n}"),
    CompletionItem("hotkeys", CompletionKind.KEYWORD, "Define hotkeys"),
    CompletionItem("interrupt", CompletionKind.KEYWORD, "Define interrupt handler"),
    CompletionItem("const", CompletionKind.KEYWORD, "Constant declaration", "const ${1:NAME} = $0"),
    CompletionItem("let", CompletionKind.KEYWORD, "Variable declaration", "let ${1:name} = $0"),
    # Control flow
    CompletionItem("if", CompletionKind.KEYWORD, "Conditional", "if ${1:condition} {\n\t$0\n}"),
    CompletionItem("elif", CompletionKind.KEYWORD, "Else if"),
    CompletionItem("else", CompletionKind.KEYWORD, "Else branch"),
    CompletionItem("while", CompletionKind.KEYWORD, "While loop", "while ${1:condition} {\n\t$0\n}"),
    CompletionItem("for", CompletionKind.KEYWORD, "For loop", "for ${1:i} in ${2:range(10)} {\n\t$0\n}"),
    # RetroScript Phase 1
    CompletionItem("repeat", CompletionKind.KEYWORD, "Repeat N times", "repeat ${1:3} {\n\t$0\n}"),
    CompletionItem("retry", CompletionKind.KEYWORD, "Retry on error", "retry ${1:5} {\n\t$0\n}"),
    CompletionItem("match", CompletionKind.KEYWORD, "Pattern matching", "match ${1:$result}: {\n\t$0\n}"),
    CompletionItem("and", CompletionKind.KEYWORD, "Logical AND"),
    CompletionItem("or", CompletionKind.KEYWORD, "Logical OR"),
    CompletionItem("not", CompletionKind.KEYWORD, "Logical NOT"),
    CompletionItem("end", CompletionKind.KEYWORD, "End block"),
    # Phase 2
    CompletionItem("test", CompletionKind.KEYWORD, "Test block"),
    CompletionItem("mock", CompletionKind.KEYWORD, "Mock function"),
    CompletionItem("assert", CompletionKind.KEYWORD, "Assertion"),
    # Phase 3
    CompletionItem("import", CompletionKind.KEYWORD, "Import module", "import \"${1:path}\" as ${2:alias}"),
    CompletionItem("as", CompletionKind.KEYWORD, "Alias"),
    # Control
    CompletionItem("break", CompletionKind.KEYWORD, "Break loop"),
    CompletionItem("continue", CompletionKind.KEYWORD, "Continue loop"),
    CompletionItem("return", CompletionKind.KEYWORD, "Return from flow"),
    CompletionItem("goto", CompletionKind.KEYWORD, "Jump to label"),
    CompletionItem("label", CompletionKind.KEYWORD, "Define label"),
    # Literals
    CompletionItem("true", CompletionKind.KEYWORD, "Boolean true"),
    CompletionItem("false", CompletionKind.KEYWORD, "Boolean false"),
    CompletionItem("null", CompletionKind.KEYWORD, "Null value"),
]

BUILTINS = [
    # Image functions
    CompletionItem("find", CompletionKind.BUILTIN, "Find image on screen", "find(${1:image})"),
    CompletionItem("wait", CompletionKind.BUILTIN, "Wait for image", "wait(${1:image}, timeout=${2:10s})"),
    CompletionItem("wait_image", CompletionKind.BUILTIN, "Wait for image (legacy)"),
    CompletionItem("find_image", CompletionKind.BUILTIN, "Find image (legacy)"),
    CompletionItem("image_exists", CompletionKind.BUILTIN, "Check if image exists"),
    CompletionItem("wait_any", CompletionKind.BUILTIN, "Wait for any of multiple images"),
    # Mouse actions
    CompletionItem("click", CompletionKind.BUILTIN, "Click at position", "click(${1:x}, ${2:y})"),
    CompletionItem("move", CompletionKind.BUILTIN, "Move mouse", "move(${1:x}, ${2:y})"),
    CompletionItem("drag", CompletionKind.BUILTIN, "Drag from to", "drag(${1:x1}, ${2:y1}, ${3:x2}, ${4:y2})"),
    CompletionItem("scroll", CompletionKind.BUILTIN, "Scroll wheel", "scroll(${1:amount})"),
    # Keyboard actions
    CompletionItem("type", CompletionKind.BUILTIN, "Type text", "type(\"${1:text}\")"),
    CompletionItem("press", CompletionKind.BUILTIN, "Press key", "press(\"${1:key}\")"),
    CompletionItem("hotkey", CompletionKind.BUILTIN, "Key combination", "hotkey(\"${1:ctrl+c}\")"),
    # Utility
    CompletionItem("sleep", CompletionKind.BUILTIN, "Pause execution", "sleep(${1:1s})"),
    CompletionItem("log", CompletionKind.BUILTIN, "Log message", "log(\"${1:message}\")"),
    CompletionItem("run", CompletionKind.BUILTIN, "Run another flow", "run(${1:flow_name})"),
    CompletionItem("range", CompletionKind.BUILTIN, "Generate range", "range(${1:10})"),
]

DECORATORS = [
    CompletionItem("@test", CompletionKind.SNIPPET, "Test block", "@test \"${1:name}\" {\n\t$0\n}"),
    CompletionItem("@config", CompletionKind.SNIPPET, "Configuration", "@config {\n\t$0\n}"),
    CompletionItem("@permissions", CompletionKind.SNIPPET, "Permissions", "@permissions {\n\t$0\n}"),
    CompletionItem("@meta", CompletionKind.SNIPPET, "Metadata", "@meta {\n\t$0\n}"),
]


class CompletionProvider:
    """Provides auto-completion suggestions for RetroScript.

    Usage:
        provider = CompletionProvider()
        completions = provider.get_completions(code, cursor_position)
    """

    def __init__(self) -> None:
        self._all_items = KEYWORDS + BUILTINS + DECORATORS
        self._variables: set[str] = set()
        self._flows: set[str] = set()
        self._imports: dict[str, str] = {}  # alias -> path

    def update_context(self, program: Program | None) -> None:
        """Update completion context from parsed program."""
        if not program:
            return

        self._variables.clear()
        self._flows.clear()
        self._imports.clear()

        # Extract flows
        for flow in program.flows:
            self._flows.add(flow.name)

        # Extract imports
        for imp in program.imports:
            alias = imp.alias or imp.path.split("/")[-1]
            self._imports[alias] = imp.path

    def get_completions(
        self,
        prefix: str = "",
        include_variables: bool = True,
        include_flows: bool = True,
    ) -> list[CompletionItem]:
        """Get completion suggestions filtered by prefix.

        Args:
            prefix: Text to filter by (e.g., "re" -> "repeat", "retry")
            include_variables: Include $variables
            include_flows: Include flow names

        Returns:
            List of matching completion items
        """
        results: list[CompletionItem] = []
        prefix_lower = prefix.lower()

        # Filter static items
        for item in self._all_items:
            if item.label.lower().startswith(prefix_lower):
                results.append(item)

        # Add variables
        if include_variables and prefix.startswith("$"):
            var_prefix = prefix[1:].lower()
            for var in self._variables:
                if var.lower().startswith(var_prefix):
                    results.append(CompletionItem(
                        f"${var}",
                        CompletionKind.VARIABLE,
                        "Variable",
                    ))

        # Add flows
        if include_flows:
            for flow in self._flows:
                if flow.lower().startswith(prefix_lower):
                    results.append(CompletionItem(
                        flow,
                        CompletionKind.FLOW,
                        "Flow",
                    ))

        # Add imports
        for alias in self._imports:
            if alias.lower().startswith(prefix_lower):
                results.append(CompletionItem(
                    alias,
                    CompletionKind.IMPORT,
                    f"import \"{self._imports[alias]}\"",
                ))

        return results

    def add_variable(self, name: str) -> None:
        """Track a variable for completion."""
        # Remove $ prefix if present
        if name.startswith("$"):
            name = name[1:]
        self._variables.add(name)

    def get_decorator_completions(self) -> list[CompletionItem]:
        """Get decorator-specific completions."""
        return DECORATORS.copy()

    def get_keyword_completions(self) -> list[CompletionItem]:
        """Get all keyword completions."""
        return KEYWORDS.copy()

    def get_builtin_completions(self) -> list[CompletionItem]:
        """Get all builtin function completions."""
        return BUILTINS.copy()
