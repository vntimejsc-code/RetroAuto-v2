"""
RetroAuto v2 - Template Store

Manages preloaded templates for fast matching.
Phase 3.2.1: Lazy loading with LRU cache for memory efficiency.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Any

import cv2
import numpy as np

from core.models import AssetImage
from infra import get_logger

logger = get_logger("TemplateStore")


@dataclass
class TemplateData:
    """Cached template data."""
    
    asset: AssetImage
    gray: np.ndarray
    color: np.ndarray | None
    shape: tuple[int, int]


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

        # Memory optimization: only store color if explicitly needed (not grayscale)
        # This saves ~40% memory for grayscale templates
        self._templates[asset.id] = {
            "asset": asset,
            "color": None if asset.grayscale else img,  # Don't duplicate color for grayscale
            "gray": gray,
            "shape": img.shape[:2],  # (h, w)
        }

        logger.debug("Loaded template: %s (%dx%d, grayscale=%s)", asset.id, img.shape[1], img.shape[0], asset.grayscale)

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


class LazyTemplateStore:
    """
    Lazy-loading template store with LRU cache.
    
    Loads templates on-demand instead of upfront, with LRU eviction
    to manage memory usage for large asset libraries.
    
    Phase 3.2.1: Performance optimization.
    
    Usage:
        store = LazyTemplateStore(base_path, max_cached=50)
        template = store.get("button_ok")  # Loads on first access
        stats = store.get_cache_stats()  # Monitor cache performance
    """
    
    def __init__(
        self,
        base_path: Path | None = None,
        max_cached: int = 50,
    ) -> None:
        self._base_path = base_path or Path(".")
        self._max_cached = max_cached
        self._assets: dict[str, AssetImage] = {}  # Asset metadata registry
        self._lock = Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        
    def set_base_path(self, path: Path) -> None:
        """Set base path for relative asset paths."""
        self._base_path = path
        
    def register_assets(self, assets: list[AssetImage]) -> None:
        """Register assets without loading them (lazy loading)."""
        for asset in assets:
            self._assets[asset.id] = asset
        logger.info("Registered %d assets for lazy loading", len(assets))
    
    def get(self, asset_id: str) -> TemplateData | None:
        """
        Get template, loading it lazily if not cached.
        
        Args:
            asset_id: Asset ID to load
            
        Returns:
            TemplateData or None if not found
        """
        # Check if asset is registered
        asset = self._assets.get(asset_id)
        if asset is None:
            return None
        
        # Use cached loader
        return self._load_cached(asset_id, asset.path)
    
    @lru_cache(maxsize=50)
    def _load_cached(self, asset_id: str, asset_path: str) -> TemplateData | None:
        """
        Load template with LRU caching.
        
        Uses asset_id + path as cache key for invalidation on path changes.
        """
        asset = self._assets.get(asset_id)
        if asset is None:
            self._misses += 1
            return None
        
        try:
            path = Path(asset_path)
            if not path.is_absolute():
                path = self._base_path / asset_path
            
            if not path.exists():
                logger.warning("Template not found: %s", path)
                self._misses += 1
                return None
            
            # Load image
            img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if img is None:
                logger.warning("Failed to read image: %s", path)
                self._misses += 1
                return None
            
            # Convert to grayscale if needed
            if asset.grayscale and len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            self._hits += 1
            logger.debug("Lazy-loaded template: %s", asset_id)
            
            return TemplateData(
                asset=asset,
                gray=gray,
                color=None if asset.grayscale else img,
                shape=img.shape[:2],
            )
            
        except (OSError, cv2.error) as e:
            logger.error("Error loading template %s: %s", asset_id, e)
            self._misses += 1
            return None
    
    def get_template_image(
        self,
        asset_id: str,
        grayscale: bool = True,
    ) -> np.ndarray | None:
        """Get template image array."""
        data = self.get(asset_id)
        if data is None:
            return None
        return data.gray if grayscale else data.color
    
    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with hits, misses, hit_rate, cache_size
        """
        cache_info = self._load_cached.cache_info()
        total = self._hits + self._misses
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0,
            "cache_size": cache_info.currsize,
            "max_size": cache_info.maxsize,
            "registered_assets": len(self._assets),
        }
    
    def clear_cache(self) -> None:
        """Clear the LRU cache."""
        self._load_cached.cache_clear()
        self._hits = 0
        self._misses = 0
        logger.debug("Lazy template cache cleared")
    
    def __contains__(self, asset_id: str) -> bool:
        return asset_id in self._assets
    
    def __len__(self) -> int:
        return len(self._assets)

