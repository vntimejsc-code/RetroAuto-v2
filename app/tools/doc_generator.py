"""
RetroAuto v2 - Documentation Generator

Generate documentation from RetroScript code and comments.
Part of RetroScript Phase 7 - Tools + Productivity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class FlowDoc:
    """Documentation for a single flow."""

    name: str
    description: str = ""
    params: list[tuple[str, str]] = field(default_factory=list)  # (name, desc)
    returns: str = ""
    examples: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class ModuleDoc:
    """Documentation for a module/file."""

    name: str
    description: str = ""
    flows: list[FlowDoc] = field(default_factory=list)
    constants: list[tuple[str, str, str]] = field(default_factory=list)  # (name, value, desc)
    imports: list[str] = field(default_factory=list)


class DocGenerator:
    """Generate documentation from RetroScript code.

    Usage:
        gen = DocGenerator()
        doc = gen.generate(source)
        markdown = gen.to_markdown(doc)
    """

    def __init__(self) -> None:
        self._doc_comment_pattern = re.compile(r"^\s*#\s*(.*)$")
        self._tag_pattern = re.compile(r"@(\w+)\s*(.*)")

    def generate(self, source: str) -> ModuleDoc:
        """Generate documentation from source code.

        Args:
            source: RetroScript source code

        Returns:
            ModuleDoc with extracted documentation
        """
        lines = source.split("\n")
        doc = ModuleDoc(name="module")

        i = 0
        current_comments: list[str] = []

        while i < len(lines):
            line = lines[i].strip()

            # Collect doc comments
            if line.startswith("#"):
                comment = line[1:].strip()
                current_comments.append(comment)
                i += 1
                continue

            # Flow definition
            if line.startswith("flow "):
                flow_doc = self._parse_flow(line, current_comments)
                doc.flows.append(flow_doc)
                current_comments = []

            # Constant definition
            elif line.startswith("const "):
                const_doc = self._parse_const(line, current_comments)
                if const_doc:
                    doc.constants.append(const_doc)
                current_comments = []

            # Import statement
            elif line.startswith("import "):
                match = re.search(r'import\s+"([^"]+)"', line)
                if match:
                    doc.imports.append(match.group(1))
                current_comments = []

            # Module-level description (first comment block)
            elif not doc.description and current_comments:
                doc.description = "\n".join(current_comments)
                current_comments = []

            else:
                current_comments = []

            i += 1

        return doc

    def _parse_flow(self, line: str, comments: list[str]) -> FlowDoc:
        """Parse a flow definition with its doc comments."""
        # Extract flow name
        match = re.match(r"flow\s+(\w+)", line)
        name = match.group(1) if match else "unknown"

        flow_doc = FlowDoc(name=name)

        # Parse doc comments
        description_lines = []
        for comment in comments:
            # Check for tags
            tag_match = self._tag_pattern.match(comment)
            if tag_match:
                tag, value = tag_match.groups()
                if tag == "param":
                    parts = value.split(" ", 1)
                    param_name = parts[0] if parts else ""
                    param_desc = parts[1] if len(parts) > 1 else ""
                    flow_doc.params.append((param_name, param_desc))
                elif tag == "returns" or tag == "return":
                    flow_doc.returns = value
                elif tag == "example":
                    flow_doc.examples.append(value)
                elif tag == "tag":
                    flow_doc.tags.append(value)
                else:
                    flow_doc.tags.append(f"{tag}: {value}")
            else:
                description_lines.append(comment)

        flow_doc.description = "\n".join(description_lines)
        return flow_doc

    def _parse_const(
        self,
        line: str,
        comments: list[str],
    ) -> tuple[str, str, str] | None:
        """Parse a constant definition."""
        match = re.match(r"const\s+(\w+)\s*=\s*(.+)", line)
        if not match:
            return None

        name = match.group(1)
        value = match.group(2).rstrip(";")
        description = " ".join(comments) if comments else ""

        return (name, value, description)

    def to_markdown(self, doc: ModuleDoc) -> str:
        """Convert ModuleDoc to Markdown format.

        Args:
            doc: The documentation to convert

        Returns:
            Markdown formatted documentation
        """
        lines: list[str] = []

        # Title
        lines.append(f"# {doc.name}")
        lines.append("")

        # Description
        if doc.description:
            lines.append(doc.description)
            lines.append("")

        # Imports
        if doc.imports:
            lines.append("## Imports")
            lines.append("")
            for imp in doc.imports:
                lines.append(f"- `{imp}`")
            lines.append("")

        # Constants
        if doc.constants:
            lines.append("## Constants")
            lines.append("")
            lines.append("| Name | Value | Description |")
            lines.append("|------|-------|-------------|")
            for name, value, desc in doc.constants:
                lines.append(f"| `{name}` | `{value}` | {desc} |")
            lines.append("")

        # Flows
        if doc.flows:
            lines.append("## Flows")
            lines.append("")
            for flow in doc.flows:
                lines.extend(self._flow_to_markdown(flow))
                lines.append("")

        return "\n".join(lines)

    def _flow_to_markdown(self, flow: FlowDoc) -> list[str]:
        """Convert a FlowDoc to Markdown."""
        lines: list[str] = []

        # Heading
        lines.append(f"### `{flow.name}`")
        lines.append("")

        # Description
        if flow.description:
            lines.append(flow.description)
            lines.append("")

        # Parameters
        if flow.params:
            lines.append("**Parameters:**")
            lines.append("")
            for name, desc in flow.params:
                lines.append(f"- `{name}`: {desc}")
            lines.append("")

        # Returns
        if flow.returns:
            lines.append(f"**Returns:** {flow.returns}")
            lines.append("")

        # Examples
        if flow.examples:
            lines.append("**Examples:**")
            lines.append("")
            for example in flow.examples:
                lines.append("```retro")
                lines.append(example)
                lines.append("```")
                lines.append("")

        # Tags
        if flow.tags:
            lines.append(f"**Tags:** {', '.join(flow.tags)}")
            lines.append("")

        return lines

    def generate_index(self, modules: list[ModuleDoc]) -> str:
        """Generate index page for multiple modules.

        Args:
            modules: List of module documentation

        Returns:
            Markdown index page
        """
        lines: list[str] = []

        lines.append("# RetroScript API Documentation")
        lines.append("")
        lines.append("## Modules")
        lines.append("")

        for mod in modules:
            lines.append(f"### [{mod.name}]({mod.name}.md)")
            if mod.description:
                # First line of description
                first_line = mod.description.split("\n")[0]
                lines.append(f"  {first_line}")
            lines.append("")

            # List flows
            if mod.flows:
                lines.append("  **Flows:**")
                for flow in mod.flows:
                    lines.append(f"  - `{flow.name}`")
                lines.append("")

        return "\n".join(lines)


def generate_docs(source: str, module_name: str = "script") -> str:
    """Convenience function to generate documentation.

    Args:
        source: RetroScript source code
        module_name: Name for the module

    Returns:
        Markdown documentation
    """
    gen = DocGenerator()
    doc = gen.generate(source)
    doc.name = module_name
    return gen.to_markdown(doc)
