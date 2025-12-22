"""
RetroAuto v2 - Dependency Resolver

Semantic version checking and dependency resolution.
Part of RetroScript Phase 13 - Package Management.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Version:
    """Semantic version (Major.Minor.Patch)."""

    major: int
    minor: int
    patch: int
    pre_release: str = ""
    build: str = ""

    def __str__(self) -> str:
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            s += f"-{self.pre_release}"
        if self.build:
            s += f"+{self.build}"
        return s

    def __lt__(self, other: Version) -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        return False  # Simplified pre-release comparison

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return False
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.pre_release == other.pre_release
        )

    @classmethod
    def parse(cls, version_str: str) -> Version:
        """Parse semantic version string."""
        # Simple regex for SemVer
        match = re.match(
            r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-.]+))?(?:\+([0-9A-Za-z-.]+))?$",
            version_str.strip(),
        )
        if not match:
            raise ValueError(f"Invalid version: {version_str}")

        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            pre_release=match.group(4) or "",
            build=match.group(5) or "",
        )


class VersionReq:
    """Version requirement (e.g. ^1.2.0, >=1.0, *)."""

    def __init__(self, req_str: str) -> None:
        self.req_str = req_str
        self.kind = "exact"
        self.version: Version | None = None

        self._parse()

    def _parse(self) -> None:
        s = self.req_str.strip()
        if s == "*":
            self.kind = "any"
            return

        if s.startswith("^"):
            self.kind = "caret"
            self.version = Version.parse(s[1:])
        elif s.startswith("~"):
            self.kind = "tilde"
            self.version = Version.parse(s[1:])
        elif s.startswith(">="):
            self.kind = "gte"
            self.version = Version.parse(s[2:])
        elif s.startswith(">"):
            self.kind = "gt"
            self.version = Version.parse(s[1:])
        elif s.startswith("<="):
            self.kind = "lte"
            self.version = Version.parse(s[2:])
        elif s.startswith("<"):
            self.kind = "lt"
            self.version = Version.parse(s[1:])
        else:
            self.kind = "exact"
            self.version = Version.parse(s)

    def matches(self, version: Version) -> bool:
        """Check if version matches requirement."""
        if self.kind == "any":
            return True

        if not self.version:
            return False

        v = self.version

        if self.kind == "exact":
            return version == v

        elif self.kind == "caret":
            # ^1.2.3 := >=1.2.3 <2.0.0
            if v.major != 0:
                return (version.major == v.major) and (version >= v)
            elif v.minor != 0:
                # ^0.2.3 := >=0.2.3 <0.3.0
                return (version.major == 0) and (version.minor == v.minor) and (version >= v)
            else:
                # ^0.0.3 := 0.0.3
                return version == v

        elif self.kind == "tilde":
            # ~1.2.3 := >=1.2.3 <1.3.0
            return version.major == v.major and version.minor == v.minor and version >= v

        elif self.kind == "gte":
            return version >= v

        elif self.kind == "gt":
            # Since we implemented only <, create proper > logic
            return not (version < v) and version != v

        elif self.kind == "lte":
            return version < v or version == v

        elif self.kind == "lt":
            return version < v

        return False


class DependencyResolver:
    """Dependency resolution logic."""

    def resolve(self, dependencies: dict[str, str]) -> dict[str, Version]:
        """Resolve dependencies (simplified).

        In a real implementation, this would build a graph and handle transitive dependencies.
        For now, we just validate versions.
        """
        resolved = {}

        for name, req_str in dependencies.items():
            # Mock resolution: just pick the required version if exact/caret
            # In real system: query registry, find best match
            req = VersionReq(req_str)
            if req.version:
                resolved[name] = req.version
            else:
                # Fallback for * or unknown
                resolved[name] = Version(0, 0, 0)

        return resolved


# Convenience
def check_version(req: str, version: str) -> bool:
    """Check if version string matches requirement."""
    try:
        r = VersionReq(req)
        v = Version.parse(version)
        return r.matches(v)
    except ValueError:
        return False
