"""
RetroAuto v2 - Module Loader

Handles import resolution, caching, and circular dependency detection.
Part of RetroScript Phase 3 - Package Manager + Ecosystem.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.dsl.ast import Program


@dataclass
class LoadedModule:
    """Represents a loaded module."""

    path: str  # Absolute path to module
    alias: str | None  # Import alias
    ast: Program | None = None  # Parsed AST
    exports: dict[str, any] = field(default_factory=dict)  # Exported symbols


class ModuleLoader:
    """Module loader with caching and circular dependency detection.

    Usage:
        loader = ModuleLoader(base_path="/path/to/scripts")
        module = loader.load("lib/combat")
        # Access module.ast or module.exports
    """

    def __init__(self, base_path: str | Path | None = None) -> None:
        """Initialize module loader.

        Args:
            base_path: Base directory for resolving imports
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self._cache: dict[str, LoadedModule] = {}
        self._loading: set[str] = set()  # For circular dependency detection
        self._search_paths: list[Path] = [
            self.base_path,
            self.base_path / "lib",
            self.base_path / "modules",
        ]

    def add_search_path(self, path: str | Path) -> None:
        """Add a path to search for modules."""
        self._search_paths.append(Path(path))

    def resolve_path(self, import_path: str) -> Path | None:
        """Resolve import path to absolute file path.

        Args:
            import_path: Import path from the source (e.g., "lib/combat")

        Returns:
            Absolute path to the module file, or None if not found
        """
        # Try with .retro extension first
        for search_path in self._search_paths:
            # Try exact path with extension
            candidate = search_path / f"{import_path}.retro"
            if candidate.exists():
                return candidate

            # Try without extension (for directories with index.retro)
            candidate_index = search_path / import_path / "index.retro"
            if candidate_index.exists():
                return candidate_index

            # Try as absolute/relative path
            candidate_direct = Path(import_path)
            if candidate_direct.exists():
                return candidate_direct

        return None

    def load(self, import_path: str, alias: str | None = None) -> LoadedModule | None:
        """Load a module by import path.

        Args:
            import_path: Path from import statement
            alias: Optional alias for the module

        Returns:
            LoadedModule if successful, None if not found

        Raises:
            ModuleError: If circular dependency detected
        """
        # Resolve to absolute path
        resolved = self.resolve_path(import_path)
        if not resolved:
            return None

        abs_path = str(resolved.resolve())

        # Check cache
        if abs_path in self._cache:
            return self._cache[abs_path]

        # Detect circular dependency
        if abs_path in self._loading:
            raise ModuleError(f"Circular dependency detected: {import_path}")

        self._loading.add(abs_path)

        try:
            # Read and parse module
            source = resolved.read_text(encoding="utf-8")

            # Import parser here to avoid circular import
            from core.dsl.parser import Parser

            parser = Parser(source)
            ast = parser.parse()

            # Create module
            module = LoadedModule(
                path=abs_path,
                alias=alias or import_path.split("/")[-1],
                ast=ast,
            )

            # Cache it
            self._cache[abs_path] = module

            # Process nested imports
            for import_stmt in ast.imports:
                nested = self.load(import_stmt.path, import_stmt.alias)
                if nested:
                    module.exports[nested.alias] = nested

            return module

        finally:
            self._loading.discard(abs_path)

    def get_cached(self, path: str) -> LoadedModule | None:
        """Get a cached module by path."""
        return self._cache.get(path)

    def clear_cache(self) -> None:
        """Clear all cached modules."""
        self._cache.clear()


class ModuleError(Exception):
    """Error during module loading."""

    pass
