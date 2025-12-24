"""
RetroAuto v2 - Template Store

Manages preloaded templates for fast matching.
"""

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from core.models import AssetImage
from infra import get_logger

logger = get_logger("TemplateStore")


class TemplateStore:
    """
    Stores preloaded and cached templates for fast matching.

    Features:
    - Preload all templates on script load
    - Cache grayscale converted versions
    - Memory management
    """

    def __init__(self, base_path: Path | None = None) -> None:
        self._base_path = base_path or Path(".")
        self._templates: dict[str, dict[str, Any]] = {}

    def set_base_path(self, path: Path) -> None:
        """Set base path for relative asset paths."""
        self._base_path = path

    def preload(self, assets: list[AssetImage]) -> list[str]:
        """
        Preload all assets into memory.

        Returns:
            List of errors (empty if all loaded successfully)
        """
        errors: list[str] = []
        self._templates.clear()

        for asset in assets:
            try:
                self._load_asset(asset)
            except Exception as e:
                errors.append(f"{asset.id}: {e}")

        logger.info("Preloaded %d templates (%d errors)", len(self._templates), len(errors))
        return errors

    def _load_asset(self, asset: AssetImage) -> None:
        """Load single asset into cache."""
        asset_path = Path(asset.path)

        # Support both absolute and relative paths
        if asset_path.is_absolute():
            path = asset_path
        else:
            path = self._base_path / asset.path

        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")

        # Load image
        img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Failed to read image: {path}")

        # Convert to grayscale if needed
        if asset.grayscale and len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        self._templates[asset.id] = {
            "asset": asset,
            "color": img,
            "gray": gray,
            "shape": img.shape[:2],  # (h, w)
        }

        logger.debug("Loaded template: %s (%dx%d)", asset.id, img.shape[1], img.shape[0])

    def get(self, asset_id: str) -> dict[str, Any] | None:
        """Get preloaded template."""
        return self._templates.get(asset_id)

    def get_template_image(self, asset_id: str, grayscale: bool = True) -> np.ndarray | None:
        """Get template image array."""
        data = self._templates.get(asset_id)
        if data is None:
            return None
        return data["gray"] if grayscale else data["color"]

    def get_asset(self, asset_id: str) -> AssetImage | None:
        """Get asset metadata."""
        data = self._templates.get(asset_id)
        return data["asset"] if data else None

    def clear(self) -> None:
        """Clear all cached templates."""
        self._templates.clear()
        logger.debug("Template cache cleared")

    def __contains__(self, asset_id: str) -> bool:
        return asset_id in self._templates

    def __len__(self) -> int:
        return len(self._templates)
