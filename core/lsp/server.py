"""
RetroAuto v2 - Language Server Protocol

LSP implementation for RetroScript IDE integration.
Part of RetroScript Phase 12 - LSP.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

# ─────────────────────────────────────────────────────────────
# LSP Protocol Types
# ─────────────────────────────────────────────────────────────


class MessageType(IntEnum):
    """LSP message types."""

    ERROR = 1
    WARNING = 2
    INFO = 3
    LOG = 4


class DiagnosticSeverity(IntEnum):
    """LSP diagnostic severity."""

    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


class CompletionItemKind(IntEnum):
    """LSP completion item kinds."""

    TEXT = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    FIELD = 5
    VARIABLE = 6
    CLASS = 7
    INTERFACE = 8
    MODULE = 9
    PROPERTY = 10
    KEYWORD = 14
    SNIPPET = 15


@dataclass
class Position:
    """LSP position (0-indexed)."""

    line: int
    character: int

    def to_dict(self) -> dict[str, int]:
        return {"line": self.line, "character": self.character}


@dataclass
class Range:
    """LSP range."""

    start: Position
    end: Position

    def to_dict(self) -> dict[str, Any]:
        return {"start": self.start.to_dict(), "end": self.end.to_dict()}


@dataclass
class Location:
    """LSP location."""

    uri: str
    range: Range

    def to_dict(self) -> dict[str, Any]:
        return {"uri": self.uri, "range": self.range.to_dict()}


@dataclass
class Diagnostic:
    """LSP diagnostic."""

    range: Range
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    source: str = "retroscript"

    def to_dict(self) -> dict[str, Any]:
        return {
            "range": self.range.to_dict(),
            "message": self.message,
            "severity": self.severity.value,
            "source": self.source,
        }


@dataclass
class CompletionItem:
    """LSP completion item."""

    label: str
    kind: CompletionItemKind = CompletionItemKind.TEXT
    detail: str = ""
    documentation: str = ""
    insert_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"label": self.label, "kind": self.kind.value}
        if self.detail:
            result["detail"] = self.detail
        if self.documentation:
            result["documentation"] = self.documentation
        if self.insert_text:
            result["insertText"] = self.insert_text
        return result


@dataclass
class Hover:
    """LSP hover result."""

    contents: str
    range: Range | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"contents": {"kind": "markdown", "value": self.contents}}
        if self.range:
            result["range"] = self.range.to_dict()
        return result


# ─────────────────────────────────────────────────────────────
# Document Management
# ─────────────────────────────────────────────────────────────


@dataclass
class TextDocument:
    """A text document being edited."""

    uri: str
    text: str
    version: int = 0
    language_id: str = "retroscript"

    def get_line(self, line: int) -> str:
        """Get a specific line."""
        lines = self.text.split("\n")
        if 0 <= line < len(lines):
            return lines[line]
        return ""

    def get_word_at(self, position: Position) -> str:
        """Get word at position."""
        line = self.get_line(position.line)
        if not line:
            return ""

        # Find word boundaries
        start = position.character
        end = position.character

        while start > 0 and re.match(r"[\w$@]", line[start - 1]):
            start -= 1

        while end < len(line) and re.match(r"[\w$@]", line[end]):
            end += 1

        return line[start:end]


class DocumentStore:
    """Store for open documents."""

    def __init__(self) -> None:
        self._documents: dict[str, TextDocument] = {}

    def open(self, uri: str, text: str, version: int = 0) -> TextDocument:
        """Open a document."""
        doc = TextDocument(uri=uri, text=text, version=version)
        self._documents[uri] = doc
        return doc

    def update(self, uri: str, text: str, version: int) -> TextDocument | None:
        """Update a document."""
        if uri in self._documents:
            self._documents[uri].text = text
            self._documents[uri].version = version
            return self._documents[uri]
        return None

    def close(self, uri: str) -> None:
        """Close a document."""
        self._documents.pop(uri, None)

    def get(self, uri: str) -> TextDocument | None:
        """Get a document."""
        return self._documents.get(uri)


# ─────────────────────────────────────────────────────────────
# Language Server
# ─────────────────────────────────────────────────────────────


class RetroScriptLanguageServer:
    """Language Server for RetroScript.

    Usage:
        server = RetroScriptLanguageServer()
        server.run()  # Reads from stdin, writes to stdout
    """

    def __init__(self) -> None:
        self.documents = DocumentStore()
        self._initialized = False
        self._shutdown = False

        # Symbol cache
        self._flows: dict[str, Location] = {}
        self._variables: dict[str, Location] = {}

    def run(self) -> None:
        """Run the language server (stdio mode)."""
        while not self._shutdown:
            try:
                message = self._read_message()
                if message:
                    response = self._handle_message(message)
                    if response:
                        self._write_message(response)
            except Exception as e:
                self._log(f"Error: {e}")
                break

    def _read_message(self) -> dict[str, Any] | None:
        """Read a JSON-RPC message from stdin."""
        # Read headers
        headers: dict[str, str] = {}
        while True:
            line = sys.stdin.readline()
            if not line or line == "\r\n" or line == "\n":
                break
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

        # Read content
        length = int(headers.get("Content-Length", 0))
        if length:
            content = sys.stdin.read(length)
            return json.loads(content)

        return None

    def _write_message(self, message: dict[str, Any]) -> None:
        """Write a JSON-RPC message to stdout."""
        content = json.dumps(message)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        sys.stdout.write(header + content)
        sys.stdout.flush()

    def _handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """Handle incoming message."""
        method = message.get("method", "")
        params = message.get("params", {})
        msg_id = message.get("id")

        # Dispatch to handlers
        handlers: dict[str, Callable[..., Any]] = {
            "initialize": self._handle_initialize,
            "initialized": lambda _: None,
            "shutdown": self._handle_shutdown,
            "exit": self._handle_exit,
            "textDocument/didOpen": self._handle_did_open,
            "textDocument/didChange": self._handle_did_change,
            "textDocument/didClose": self._handle_did_close,
            "textDocument/hover": self._handle_hover,
            "textDocument/completion": self._handle_completion,
            "textDocument/definition": self._handle_definition,
            "textDocument/references": self._handle_references,
            "textDocument/formatting": self._handle_formatting,
        }

        handler = handlers.get(method)
        if handler:
            result = handler(params)
            if msg_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": result,
                }
        elif msg_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        return None

    def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle initialize request."""
        self._initialized = True
        return {
            "capabilities": {
                "textDocumentSync": 1,  # Full sync
                "completionProvider": {"triggerCharacters": [".", "$", "@"]},
                "hoverProvider": True,
                "definitionProvider": True,
                "referencesProvider": True,
                "documentFormattingProvider": True,
            }
        }

    def _handle_shutdown(self, params: dict[str, Any]) -> None:
        """Handle shutdown request."""
        self._shutdown = True
        return None

    def _handle_exit(self, params: dict[str, Any]) -> None:
        """Handle exit notification."""
        sys.exit(0)

    def _handle_did_open(self, params: dict[str, Any]) -> None:
        """Handle textDocument/didOpen."""
        doc = params.get("textDocument", {})
        uri = doc.get("uri", "")
        text = doc.get("text", "")
        version = doc.get("version", 0)

        self.documents.open(uri, text, version)
        self._analyze_document(uri)

    def _handle_did_change(self, params: dict[str, Any]) -> None:
        """Handle textDocument/didChange."""
        doc = params.get("textDocument", {})
        uri = doc.get("uri", "")
        version = doc.get("version", 0)

        changes = params.get("contentChanges", [])
        if changes:
            text = changes[-1].get("text", "")
            self.documents.update(uri, text, version)
            self._analyze_document(uri)

    def _handle_did_close(self, params: dict[str, Any]) -> None:
        """Handle textDocument/didClose."""
        doc = params.get("textDocument", {})
        uri = doc.get("uri", "")
        self.documents.close(uri)

    def _handle_hover(self, params: dict[str, Any]) -> dict[str, Any] | None:
        """Handle textDocument/hover."""
        uri = params.get("textDocument", {}).get("uri", "")
        pos = params.get("position", {})
        position = Position(pos.get("line", 0), pos.get("character", 0))

        doc = self.documents.get(uri)
        if not doc:
            return None

        word = doc.get_word_at(position)
        if not word:
            return None

        # Check for hover info
        hover_info = self._get_hover_info(word)
        if hover_info:
            return Hover(contents=hover_info).to_dict()

        return None

    def _handle_completion(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Handle textDocument/completion."""
        uri = params.get("textDocument", {}).get("uri", "")
        pos = params.get("position", {})
        position = Position(pos.get("line", 0), pos.get("character", 0))

        doc = self.documents.get(uri)
        if not doc:
            return []

        line = doc.get_line(position.line)
        prefix = line[: position.character].split()[-1] if line else ""

        return self._get_completions(prefix)

    def _handle_definition(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Handle textDocument/definition."""
        uri = params.get("textDocument", {}).get("uri", "")
        pos = params.get("position", {})
        position = Position(pos.get("line", 0), pos.get("character", 0))

        doc = self.documents.get(uri)
        if not doc:
            return []

        word = doc.get_word_at(position)
        if not word:
            return []

        # Look up definition
        if word in self._flows:
            return [self._flows[word].to_dict()]

        return []

    def _handle_references(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Handle textDocument/references."""
        uri = params.get("textDocument", {}).get("uri", "")
        pos = params.get("position", {})
        position = Position(pos.get("line", 0), pos.get("character", 0))

        doc = self.documents.get(uri)
        if not doc:
            return []

        word = doc.get_word_at(position)
        if not word:
            return []

        return self._find_references(uri, word)

    def _handle_formatting(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Handle textDocument/formatting."""
        uri = params.get("textDocument", {}).get("uri", "")
        doc = self.documents.get(uri)
        if not doc:
            return []

        # Use the formatter
        try:
            from app.ide.formatter import CodeFormatter

            formatter = CodeFormatter()
            formatted = formatter.format(doc.text)

            lines = doc.text.count("\n")
            return [
                {
                    "range": Range(
                        Position(0, 0),
                        Position(lines, len(doc.get_line(lines))),
                    ).to_dict(),
                    "newText": formatted,
                }
            ]
        except (ImportError, AttributeError, ValueError):
            # Formatter not available or failed
            return []

    def _analyze_document(self, uri: str) -> None:
        """Analyze document for symbols and diagnostics."""
        doc = self.documents.get(uri)
        if not doc:
            return

        # Find flow definitions
        for i, line in enumerate(doc.text.split("\n")):
            match = re.match(r"flow\s+(\w+)", line)
            if match:
                name = match.group(1)
                self._flows[name] = Location(
                    uri=uri,
                    range=Range(Position(i, 0), Position(i, len(line))),
                )

    def _get_hover_info(self, word: str) -> str | None:
        """Get hover information for a word."""
        # Built-in functions
        builtins = {
            "find": "```retroscript\nfind(target, options?)\n```\nFind an image on screen.",
            "click": "```retroscript\nclick(x, y)\n```\nClick at the specified position.",
            "wait": "```retroscript\nwait(duration)\n```\nWait for the specified duration.",
            "log": "```retroscript\nlog(message)\n```\nLog a message to console.",
            "sleep": "```retroscript\nsleep(ms)\n```\nSleep for milliseconds.",
        }

        if word in builtins:
            return builtins[word]

        # Keywords
        keywords = {
            "flow": "Define a new flow (function)",
            "let": "Declare a variable",
            "if": "Conditional statement",
            "while": "While loop",
            "for": "For loop",
            "return": "Return from flow",
        }

        if word in keywords:
            return f"**{word}** - {keywords[word]}"

        # Check if it's a known flow
        if word in self._flows:
            return f"**flow {word}**"

        return None

    def _get_completions(self, prefix: str) -> list[dict[str, Any]]:
        """Get completion items."""
        items: list[CompletionItem] = []

        # Keywords
        keywords = ["flow", "let", "if", "else", "while", "for", "return", "try", "catch"]
        for kw in keywords:
            if kw.startswith(prefix):
                items.append(CompletionItem(kw, CompletionItemKind.KEYWORD))

        # Built-ins
        builtins = ["find", "click", "wait", "log", "sleep", "type", "press"]
        for bi in builtins:
            if bi.startswith(prefix):
                items.append(CompletionItem(bi, CompletionItemKind.FUNCTION))

        # Flows
        for name in self._flows:
            if name.startswith(prefix):
                items.append(CompletionItem(name, CompletionItemKind.METHOD))

        return [item.to_dict() for item in items]

    def _find_references(self, uri: str, word: str) -> list[dict[str, Any]]:
        """Find all references to a symbol."""
        references: list[Location] = []

        for doc_uri, doc in self.documents._documents.items():
            for i, line in enumerate(doc.text.split("\n")):
                for match in re.finditer(rf"\b{re.escape(word)}\b", line):
                    references.append(
                        Location(
                            uri=doc_uri,
                            range=Range(
                                Position(i, match.start()),
                                Position(i, match.end()),
                            ),
                        )
                    )

        return [ref.to_dict() for ref in references]

    def _log(self, message: str) -> None:
        """Log a message."""
        sys.stderr.write(f"[LSP] {message}\n")
        sys.stderr.flush()

    def _publish_diagnostics(self, uri: str, diagnostics: list[Diagnostic]) -> None:
        """Publish diagnostics to client."""
        self._write_message(
            {
                "jsonrpc": "2.0",
                "method": "textDocument/publishDiagnostics",
                "params": {
                    "uri": uri,
                    "diagnostics": [d.to_dict() for d in diagnostics],
                },
            }
        )


def main() -> None:
    """Entry point for language server."""
    server = RetroScriptLanguageServer()
    server.run()


if __name__ == "__main__":
    main()
