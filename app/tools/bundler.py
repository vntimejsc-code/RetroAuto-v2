"""
RetroAuto v2 - Script Bundler

Package scripts for distribution with dependencies.
Part of RetroScript Phase 8 - Runtime + Distribution.
"""

from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class BundleManifest:
    """Manifest for a bundled script package."""

    name: str
    version: str
    entry_point: str
    created_at: str = ""
    author: str = ""
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    assets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "entry_point": self.entry_point,
            "created_at": self.created_at,
            "author": self.author,
            "description": self.description,
            "dependencies": self.dependencies,
            "files": self.files,
            "assets": self.assets,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BundleManifest:
        """Create from dictionary."""
        return cls(
            name=data.get("name", "unknown"),
            version=data.get("version", "1.0.0"),
            entry_point=data.get("entry_point", "main.retro"),
            created_at=data.get("created_at", ""),
            author=data.get("author", ""),
            description=data.get("description", ""),
            dependencies=data.get("dependencies", []),
            files=data.get("files", []),
            assets=data.get("assets", []),
        )


@dataclass
class BundleOptions:
    """Options for bundling scripts."""

    include_assets: bool = True
    include_libs: bool = True
    compress: bool = True
    minify: bool = False  # Future: minify code
    output_format: str = "zip"  # zip, folder


class Bundler:
    """Bundle RetroScript projects for distribution.

    Usage:
        bundler = Bundler()
        bundler.bundle("/path/to/project", "/path/to/output.zip")
    """

    def __init__(self, options: BundleOptions | None = None) -> None:
        self.options = options or BundleOptions()

    def bundle(
        self,
        project_dir: str | Path,
        output_path: str | Path | None = None,
    ) -> Path:
        """Bundle a project.

        Args:
            project_dir: Path to project directory
            output_path: Output file/directory path

        Returns:
            Path to created bundle
        """
        project_dir = Path(project_dir)
        if not project_dir.exists():
            raise BundleError(f"Project directory not found: {project_dir}")

        # Read project config
        config = self._read_config(project_dir)

        # Create manifest
        manifest = BundleManifest(
            name=config.get("name", project_dir.name),
            version=config.get("version", "1.0.0"),
            entry_point=config.get("entry_point", "main.retro"),
            created_at=datetime.now().isoformat(),
            author=config.get("author", ""),
            description=config.get("description", ""),
        )

        # Collect files
        files_to_bundle: list[tuple[Path, str]] = []

        # Main entry point
        entry_path = project_dir / manifest.entry_point
        if entry_path.exists():
            files_to_bundle.append((entry_path, manifest.entry_point))
            manifest.files.append(manifest.entry_point)

        # Collect .retro files
        for retro_file in project_dir.glob("**/*.retro"):
            if retro_file != entry_path:
                rel_path = retro_file.relative_to(project_dir)
                files_to_bundle.append((retro_file, str(rel_path)))
                manifest.files.append(str(rel_path))

        # Collect lib files
        if self.options.include_libs:
            lib_dir = project_dir / "lib"
            if lib_dir.exists():
                for lib_file in lib_dir.glob("**/*.retro"):
                    rel_path = lib_file.relative_to(project_dir)
                    files_to_bundle.append((lib_file, str(rel_path)))
                    manifest.files.append(str(rel_path))
                    manifest.dependencies.append(str(rel_path))

        # Collect assets
        if self.options.include_assets:
            assets_dir = project_dir / "assets"
            if assets_dir.exists():
                for asset in assets_dir.glob("**/*"):
                    if asset.is_file():
                        rel_path = asset.relative_to(project_dir)
                        files_to_bundle.append((asset, str(rel_path)))
                        manifest.assets.append(str(rel_path))

        # Determine output path
        if not output_path:
            output_path = project_dir.parent / f"{manifest.name}-{manifest.version}.retrobundle"
        else:
            output_path = Path(output_path)

        # Create bundle
        if self.options.output_format == "folder":
            return self._bundle_to_folder(output_path, files_to_bundle, manifest)
        else:
            return self._bundle_to_zip(output_path, files_to_bundle, manifest)

    def _read_config(self, project_dir: Path) -> dict[str, Any]:
        """Read project configuration."""
        config_path = project_dir / "retro.toml"
        if not config_path.exists():
            return {}

        # Simple TOML-like parsing
        config: dict[str, Any] = {}
        current_section = config

        for line in config_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("[") and line.endswith("]"):
                section_name = line[1:-1]
                config[section_name] = {}
                current_section = config[section_name]
            elif "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"')
                current_section[key] = value

        # Flatten for simple access
        if "project" in config:
            config.update(config["project"])
        if "script" in config:
            config.update(config["script"])

        return config

    def _bundle_to_zip(
        self,
        output_path: Path,
        files: list[tuple[Path, str]],
        manifest: BundleManifest,
    ) -> Path:
        """Create ZIP bundle."""
        output_path = output_path.with_suffix(".retrobundle")

        compression = zipfile.ZIP_DEFLATED if self.options.compress else zipfile.ZIP_STORED

        with zipfile.ZipFile(output_path, "w", compression) as zf:
            # Add manifest
            manifest_json = json.dumps(manifest.to_dict(), indent=2)
            zf.writestr("manifest.json", manifest_json)

            # Add files
            for file_path, archive_name in files:
                zf.write(file_path, archive_name)

        return output_path

    def _bundle_to_folder(
        self,
        output_path: Path,
        files: list[tuple[Path, str]],
        manifest: BundleManifest,
    ) -> Path:
        """Create folder bundle."""
        output_path.mkdir(parents=True, exist_ok=True)

        # Write manifest
        manifest_path = output_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")

        # Copy files
        for file_path, rel_name in files:
            dest = output_path / rel_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest)

        return output_path

    def unbundle(
        self,
        bundle_path: str | Path,
        output_dir: str | Path | None = None,
    ) -> Path:
        """Extract a bundle.

        Args:
            bundle_path: Path to bundle file
            output_dir: Output directory

        Returns:
            Path to extracted directory
        """
        bundle_path = Path(bundle_path)
        if not bundle_path.exists():
            raise BundleError(f"Bundle not found: {bundle_path}")

        # Determine output directory
        output_dir = bundle_path.parent / bundle_path.stem if not output_dir else Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Extract
        with zipfile.ZipFile(bundle_path, "r") as zf:
            zf.extractall(output_dir)

        return output_dir

    def get_manifest(self, bundle_path: str | Path) -> BundleManifest:
        """Read manifest from a bundle.

        Args:
            bundle_path: Path to bundle file

        Returns:
            Bundle manifest
        """
        bundle_path = Path(bundle_path)

        with zipfile.ZipFile(bundle_path, "r") as zf:
            manifest_data = json.loads(zf.read("manifest.json"))
            return BundleManifest.from_dict(manifest_data)


class BundleError(Exception):
    """Error during bundling operations."""

    pass


def bundle_project(project_dir: str | Path, output: str | Path | None = None) -> str:
    """Convenience function to bundle a project.

    Returns:
        Path to created bundle
    """
    bundler = Bundler()
    result = bundler.bundle(project_dir, output)
    return str(result)
