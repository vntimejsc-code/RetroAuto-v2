"""
RetroAuto v2 - DSL Autocomplete Provider

Provides intelligent autocompletion for the DSL:
- Built-in functions
- Keywords
- Asset references
- Flow references
- Variables in scope
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class CompletionKind(Enum):
    """Type of completion item."""
    
    KEYWORD = auto()
    FUNCTION = auto()
    ASSET = auto()
    FLOW = auto()
    VARIABLE = auto()
    SNIPPET = auto()


@dataclass
class CompletionItem:
    """A completion suggestion."""
    
    label: str
    kind: CompletionKind
    detail: str = ""
    insert_text: str = ""
    documentation: str = ""
    
    def __post_init__(self) -> None:
        if not self.insert_text:
            self.insert_text = self.label


# ─────────────────────────────────────────────────────────────
# Built-in Completions
# ─────────────────────────────────────────────────────────────

KEYWORDS = [
    CompletionItem("flow", CompletionKind.KEYWORD, "Flow definition"),
    CompletionItem("if", CompletionKind.KEYWORD, "Conditional statement"),
    CompletionItem("elif", CompletionKind.KEYWORD, "Else if clause"),
    CompletionItem("else", CompletionKind.KEYWORD, "Else clause"),
    CompletionItem("while", CompletionKind.KEYWORD, "While loop"),
    CompletionItem("for", CompletionKind.KEYWORD, "For loop"),
    CompletionItem("in", CompletionKind.KEYWORD, "In keyword"),
    CompletionItem("label", CompletionKind.KEYWORD, "Label definition"),
    CompletionItem("goto", CompletionKind.KEYWORD, "Jump to label"),
    CompletionItem("break", CompletionKind.KEYWORD, "Break loop"),
    CompletionItem("continue", CompletionKind.KEYWORD, "Continue loop"),
    CompletionItem("return", CompletionKind.KEYWORD, "Return statement"),
    CompletionItem("hotkeys", CompletionKind.KEYWORD, "Hotkey configuration"),
    CompletionItem("interrupt", CompletionKind.KEYWORD, "Interrupt handler"),
    CompletionItem("true", CompletionKind.KEYWORD, "Boolean true"),
    CompletionItem("false", CompletionKind.KEYWORD, "Boolean false"),
    CompletionItem("null", CompletionKind.KEYWORD, "Null value"),
]

BUILTIN_FUNCTIONS = [
    CompletionItem(
        "wait_image", CompletionKind.FUNCTION,
        "Wait for image to appear/disappear",
        'wait_image("$1", timeout=$2)',
        "Wait for an image asset to appear or disappear on screen."
    ),
    CompletionItem(
        "click", CompletionKind.FUNCTION,
        "Click at position",
        "click($1, $2)",
        "Perform a mouse click at (x, y) coordinates."
    ),
    CompletionItem(
        "click_image", CompletionKind.FUNCTION,
        "Click on image match",
        'click_image("$1")',
        "Find an image and click on its center."
    ),
    CompletionItem(
        "double_click", CompletionKind.FUNCTION,
        "Double click at position",
        "double_click($1, $2)",
        "Perform a double click at (x, y) coordinates."
    ),
    CompletionItem(
        "right_click", CompletionKind.FUNCTION,
        "Right click at position",
        "right_click($1, $2)",
        "Perform a right click at (x, y) coordinates."
    ),
    CompletionItem(
        "drag", CompletionKind.FUNCTION,
        "Drag from one point to another",
        "drag($1, $2, $3, $4)",
        "Drag from (x1, y1) to (x2, y2)."
    ),
    CompletionItem(
        "scroll", CompletionKind.FUNCTION,
        "Scroll mouse wheel",
        "scroll($1)",
        "Scroll the mouse wheel. Positive = up, negative = down."
    ),
    CompletionItem(
        "hotkey", CompletionKind.FUNCTION,
        "Press keyboard shortcut",
        'hotkey("$1")',
        "Press a keyboard shortcut like 'ctrl+c'."
    ),
    CompletionItem(
        "type_text", CompletionKind.FUNCTION,
        "Type text",
        'type_text("$1")',
        "Type text character by character."
    ),
    CompletionItem(
        "paste", CompletionKind.FUNCTION,
        "Paste text via clipboard",
        'paste("$1")',
        "Paste text using the clipboard (faster for long text)."
    ),
    CompletionItem(
        "sleep", CompletionKind.FUNCTION,
        "Wait for duration",
        "sleep($1)",
        "Wait for the specified duration (e.g., 1s, 500ms)."
    ),
    CompletionItem(
        "log", CompletionKind.FUNCTION,
        "Log a message",
        'log("$1")',
        "Print a message to the log output."
    ),
    CompletionItem(
        "run_flow", CompletionKind.FUNCTION,
        "Run another flow",
        'run_flow("$1")',
        "Execute another flow by name."
    ),
    CompletionItem(
        "if_image", CompletionKind.FUNCTION,
        "Check if image exists",
        'if_image("$1")',
        "Returns true if the image is currently on screen."
    ),
    CompletionItem(
        "capture", CompletionKind.FUNCTION,
        "Capture screen region",
        'capture($1, $2, $3, $4, "$5")',
        "Capture a screen region and save to file."
    ),
    CompletionItem(
        "random", CompletionKind.FUNCTION,
        "Random number",
        "random($1, $2)",
        "Generate a random integer between min and max."
    ),
    CompletionItem(
        "range", CompletionKind.FUNCTION,
        "Number range",
        "range($1, $2)",
        "Generate a range of numbers for iteration."
    ),
]

SNIPPETS = [
    CompletionItem(
        "flow_new", CompletionKind.SNIPPET,
        "New flow definition",
        "flow $1 {\n  $0\n}",
        "Create a new flow."
    ),
    CompletionItem(
        "if_block", CompletionKind.SNIPPET,
        "If block",
        "if ($1) {\n  $0\n}",
        "Create an if statement."
    ),
    CompletionItem(
        "if_else", CompletionKind.SNIPPET,
        "If-else block",
        "if ($1) {\n  $2\n} else {\n  $0\n}",
        "Create an if-else statement."
    ),
    CompletionItem(
        "while_loop", CompletionKind.SNIPPET,
        "While loop",
        "while ($1) {\n  $0\n}",
        "Create a while loop."
    ),
    CompletionItem(
        "for_loop", CompletionKind.SNIPPET,
        "For loop",
        "for $1 in range($2, $3) {\n  $0\n}",
        "Create a for loop with range."
    ),
    CompletionItem(
        "label_goto", CompletionKind.SNIPPET,
        "Label and goto",
        "label $1:\n$0\ngoto $1;",
        "Create a label with goto jump."
    ),
    CompletionItem(
        "wait_click", CompletionKind.SNIPPET,
        "Wait and click image",
        'wait_image("$1");\nclick_image("$1");',
        "Wait for image to appear then click it."
    ),
    CompletionItem(
        "interrupt_block", CompletionKind.SNIPPET,
        "Interrupt handler",
        'interrupt {\n  priority $1\n  when image "$2"\n  {\n    $0\n  }\n}',
        "Create an interrupt handler."
    ),
]


class AutocompleteProvider:
    """
    Provides autocompletion suggestions for DSL.
    
    Usage:
        provider = AutocompleteProvider()
        provider.set_context(assets=["btn_ok", "img_error"], flows=["main", "login"])
        items = provider.complete("wait_")
    """
    
    def __init__(self) -> None:
        self._assets: list[str] = []
        self._flows: list[str] = []
        self._variables: list[str] = []
    
    def set_context(
        self,
        assets: list[str] | None = None,
        flows: list[str] | None = None,
        variables: list[str] | None = None,
    ) -> None:
        """Set the context for completions."""
        if assets is not None:
            self._assets = assets
        if flows is not None:
            self._flows = flows
        if variables is not None:
            self._variables = variables
    
    def complete(self, prefix: str, in_string: bool = False) -> list[CompletionItem]:
        """
        Get completions for a prefix.
        
        Args:
            prefix: The text to complete
            in_string: If true, only return asset/flow completions
        
        Returns:
            List of matching completion items
        """
        prefix_lower = prefix.lower()
        results: list[CompletionItem] = []
        
        if in_string:
            # Inside string - suggest assets and flows
            for asset in self._assets:
                if asset.lower().startswith(prefix_lower):
                    results.append(CompletionItem(
                        asset, CompletionKind.ASSET,
                        "Image asset"
                    ))
            for flow in self._flows:
                if flow.lower().startswith(prefix_lower):
                    results.append(CompletionItem(
                        flow, CompletionKind.FLOW,
                        "Flow"
                    ))
        else:
            # Normal code context
            # Keywords
            for kw in KEYWORDS:
                if kw.label.lower().startswith(prefix_lower):
                    results.append(kw)
            
            # Functions
            for fn in BUILTIN_FUNCTIONS:
                if fn.label.lower().startswith(prefix_lower):
                    results.append(fn)
            
            # Variables
            for var in self._variables:
                if var.lower().startswith(prefix_lower):
                    results.append(CompletionItem(
                        var, CompletionKind.VARIABLE,
                        "Variable"
                    ))
            
            # Snippets (only if prefix is short)
            if len(prefix) <= 3:
                for snippet in SNIPPETS:
                    if snippet.label.lower().startswith(prefix_lower):
                        results.append(snippet)
        
        return results
    
    def get_function_signature(self, name: str) -> str | None:
        """Get signature help for a function."""
        for fn in BUILTIN_FUNCTIONS:
            if fn.label == name:
                return fn.insert_text
        return None
    
    def get_all_functions(self) -> list[CompletionItem]:
        """Get all built-in functions."""
        return BUILTIN_FUNCTIONS.copy()
    
    def get_all_keywords(self) -> list[CompletionItem]:
        """Get all keywords."""
        return KEYWORDS.copy()
    
    def get_all_snippets(self) -> list[CompletionItem]:
        """Get all snippets."""
        return SNIPPETS.copy()
