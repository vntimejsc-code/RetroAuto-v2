"""
RetroAuto v2 - Package Manager

Main interface for managing RetroScript packages.
Part of RetroScript Phase 13 - Package Management.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .manifest import Manifest, Dependency, create_default
from .resolver import DependencyResolver, VersionReq


class PackageManager:
    """RetroScript Package Manager (`retro` package tools)."""

    def __init__(self, root_dir: str | Path = ".") -> None:
        self.root_dir = Path(root_dir).resolve()
        self.packages_dir = self.root_dir / "packages"
        self.manifest_path = self.root_dir / "retro.toml"
        
        self.resolver = DependencyResolver()

    def init(self, name: str) -> None:
        """Initialize a new package."""
        if self.manifest_path.exists():
            print(f"Package already exists at {self.root_dir}")
            return
        
        manifest = create_default(name)
        manifest.save(self.manifest_path)
        print(f"Initialized package '{name}' in {self.root_dir}")
        self._create_structure()

    def install(self) -> None:
        """Install all dependencies from manifest."""
        if not self.manifest_path.exists():
            print("No retro.toml found.")
            return

        manifest = Manifest.load(self.manifest_path)
        print(f"Installing dependencies for {manifest.package.name}...")

        self.packages_dir.mkdir(exist_ok=True)
        
        # Install dependencies
        self._install_list(manifest.dependencies)
        self._install_list(manifest.dev_dependencies, dev=True)
        
        print("Done.")

    def add(self, name: str, version: str = "*", dev: bool = False, git: str = "") -> None:
        """Add a dependency."""
        if not self.manifest_path.exists():
            print("No retro.toml found.")
            return

        manifest = Manifest.load(self.manifest_path)
        manifest.add_dependency(name, version, dev, git)
        manifest.save(self.manifest_path)
        
        print(f"Added {name} ({version})")
        self.install()

    def remove(self, name: str) -> None:
        """Remove a dependency."""
        if not self.manifest_path.exists():
            return

        manifest = Manifest.load(self.manifest_path)
        
        if name in manifest.dependencies:
            del manifest.dependencies[name]
            print(f"Removed {name}")
        elif name in manifest.dev_dependencies:
            del manifest.dev_dependencies[name]
            print(f"Removed {name} (dev)")
        else:
            print(f"Package {name} not found.")
            return
            
        manifest.save(self.manifest_path)
        self._remove_package_dir(name)

    def _install_list(self, dependencies: dict[str, Dependency], dev: bool = False) -> None:
        """Install a list of dependencies."""
        for name, dep in dependencies.items():
            print(f"  - {name} ({dep.version_req})...")
            
            if dep.source == "git":
                self._install_git(name, dep.path, dep.git_ref)
            elif dep.source == "local":
                self._install_local(name, dep.path)
            else:
                self._install_registry(name, dep.version_req)

    def _install_git(self, name: str, url: str, ref: str) -> None:
        """Install from Git."""
        target_dir = self.packages_dir / name
        
        if target_dir.exists():
            # In a real PM, we'd check if it's correct/update it
            return

        try:
            cmd = ["git", "clone", "--depth", "1", url, str(target_dir)]
            if ref:
                cmd = ["git", "clone", "--branch", ref, "--depth", "1", url, str(target_dir)]
                
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone {name}: {e}")

    def _install_local(self, name: str, path: str) -> None:
        """Install local path (symlink)."""
        target_dir = self.packages_dir / name
        src_path = Path(path).resolve()
        
        if not src_path.exists():
            print(f"Local path not found: {src_path}")
            return
            
        if target_dir.exists() or target_dir.is_symlink():
            if target_dir.resolve() == src_path:
                return
            if target_dir.is_symlink():
                target_dir.unlink()
            else:
                shutil.rmtree(target_dir)

        try:
            target_dir.symlink_to(src_path)
        except OSError as e:
            print(f"Failed to link {name}: {e}")

    def _install_registry(self, name: str, version_req: str) -> None:
        """Install from registry (Mock)."""
        # For now, just create a placeholder
        target_dir = self.packages_dir / name
        if target_dir.exists():
            return
        
        target_dir.mkdir(parents=True)
        manifest = create_default(name)
        manifest.package.description = "Installed from registry (mock)"
        manifest.save(target_dir / "retro.toml")

    def _remove_package_dir(self, name: str) -> None:
        """Remove package directory."""
        target_dir = self.packages_dir / name
        if target_dir.exists() or target_dir.is_symlink():
            if target_dir.is_symlink():
                target_dir.unlink()
            else:
                shutil.rmtree(target_dir)

    def _create_structure(self) -> None:
        """Create package structure."""
        (self.root_dir / "src").mkdir(exist_ok=True)
        (self.root_dir / "tests").mkdir(exist_ok=True)
        
        main_file = self.root_dir / "src/main.retro"
        if not main_file.exists():
            with open(main_file, "w") as f:
                f.write('flow main() {\n    log("Hello, RetroScript!");\n}\n')


# Global instance
_manager: PackageManager | None = None

def get_manager() -> PackageManager:
    global _manager
    if _manager is None:
        _manager = PackageManager()
    return _manager
