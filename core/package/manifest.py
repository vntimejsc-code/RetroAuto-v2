"""
RetroAuto v2 - Package Manifest

Structure and parsing for retro.toml package manifests.
Part of RetroScript Phase 13 - Package Management.
"""

from __future__ import annotations

import tomli
import tomli_w
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class PackageMetadata:
    """Metadata for a RetroScript package."""
    name: str
    version: str
    description: str = ""
    authors: list[str] = field(default_factory=list)
    license: str = "MIT"
    repository: str = ""
    keywords: list[str] = field(default_factory=list)
    entry_point: str = "main.retro"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "authors": self.authors,
            "license": self.license,
            "repository": self.repository,
            "keywords": self.keywords,
            "entry_point": self.entry_point,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PackageMetadata":
        """Create from dictionary."""
        return cls(
            name=data.get("name", "unnamed"),
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
            authors=data.get("authors", []),
            license=data.get("license", "MIT"),
            repository=data.get("repository", ""),
            keywords=data.get("keywords", []),
            entry_point=data.get("entry_point", "main.retro"),
        )


@dataclass
class Dependency:
    """A package dependency."""
    name: str
    version_req: str  # e.g. "^1.0.0", ">=1.2.0"
    source: str = "registry"  # registry, git, local
    path: str = ""  # for local/git dependencies
    git_ref: str = ""  # branch/tag/commit

    def to_dict(self) -> str | dict[str, Any]:
        """Convert to dictionary or string (if simple version)."""
        if self.source == "registry":
            return self.version_req
        
        result = {"version": self.version_req}
        if self.source == "git":
            result["git"] = self.path
            if self.git_ref:
                result["rev"] = self.git_ref
        elif self.source == "local":
            result["path"] = self.path
        
        return result

    @classmethod
    def from_entry(cls, name: str, entry: str | dict[str, Any]) -> "Dependency":
        """Create from TOML entry."""
        if isinstance(entry, str):
            return cls(name=name, version_req=entry)
        
        version = entry.get("version", "*")
        
        if "git" in entry:
            return cls(
                name=name,
                version_req=version,
                source="git",
                path=entry["git"],
                git_ref=entry.get("rev", ""),
            )
        elif "path" in entry:
            return cls(
                name=name,
                version_req=version,
                source="local",
                path=entry["path"],
            )
        
        return cls(name=name, version_req=version)


@dataclass
class Manifest:
    """Complete package manifest (retro.toml)."""
    package: PackageMetadata
    dependencies: dict[str, Dependency]
    dev_dependencies: dict[str, Dependency]

    @classmethod
    def load(cls, path: str | Path) -> "Manifest":
        """Load manifest from file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {path}")

        with open(path, "rb") as f:
            data = tomli.load(f)

        package_data = data.get("package", {})
        deps_data = data.get("dependencies", {})
        dev_deps_data = data.get("dev-dependencies", {})

        return cls(
            package=PackageMetadata.from_dict(package_data),
            dependencies={
                k: Dependency.from_entry(k, v) for k, v in deps_data.items()
            },
            dev_dependencies={
                k: Dependency.from_entry(k, v) for k, v in dev_deps_data.items()
            },
        )

    def save(self, path: str | Path) -> None:
        """Save manifest to file."""
        data = {
            "package": self.package.to_dict(),
            "dependencies": {
                dep.name: dep.to_dict() for dep in self.dependencies.values()
            },
            "dev-dependencies": {
                dep.name: dep.to_dict() for dep in self.dev_dependencies.values()
            },
        }

        with open(path, "wb") as f:
            tomli_w.dump(data, f)
    
    def add_dependency(
        self,
        name: str,
        version: str = "^0.1.0",
        dev: bool = False,
        git: str = "",
        path: str = "",
    ) -> None:
        """Add a dependency."""
        source = "registry"
        src_path = ""
        
        if git:
            source = "git"
            src_path = git
        elif path:
            source = "local"
            src_path = path

        dep = Dependency(
            name=name,
            version_req=version,
            source=source,
            path=src_path,
        )

        target = self.dev_dependencies if dev else self.dependencies
        target[name] = dep


def create_default(name: str) -> Manifest:
    """Create a default manifest."""
    return Manifest(
        package=PackageMetadata(name=name, version="0.1.0"),
        dependencies={},
        dev_dependencies={},
    )
