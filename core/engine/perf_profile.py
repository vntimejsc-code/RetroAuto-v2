"""
RetroAuto v2 - Performance Profiles

Resource presets for different machine capabilities.
Phase 3.2 Performance Optimization.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from infra import get_logger

logger = get_logger("PerfProfile")


class ProfileLevel(Enum):
    """Performance profile levels."""

    LOW = auto()  # Low-spec machines (2-4GB RAM, older CPUs)
    MEDIUM = auto()  # Standard machines (8GB RAM)
    HIGH = auto()  # High-spec machines (16GB+ RAM, modern CPUs)
    ULTRA = auto()  # Maximum performance (GPU, multi-core)


@dataclass
class PerformanceProfile:
    """Performance settings for a specific profile level."""

    # Interrupt Scanner
    scan_interval_idle_ms: int
    scan_interval_active_ms: int
    scan_interval_fast_ms: int

    # Image Cache
    template_cache_size: int
    template_cache_ttl_seconds: int

    # OCR Cache
    ocr_cache_size: int
    ocr_cache_ttl_seconds: float

    # Memory Manager
    memory_threshold_mb: int
    memory_check_interval_seconds: int

    # Parallel Processing
    max_workers: int

    # Vision
    default_poll_ms: int
    adaptive_threshold: bool


# Predefined profiles
PROFILES: dict[ProfileLevel, PerformanceProfile] = {
    ProfileLevel.LOW: PerformanceProfile(
        scan_interval_idle_ms=1000,
        scan_interval_active_ms=500,
        scan_interval_fast_ms=200,
        template_cache_size=20,
        template_cache_ttl_seconds=600,
        ocr_cache_size=20,
        ocr_cache_ttl_seconds=3.0,
        memory_threshold_mb=150,
        memory_check_interval_seconds=120,
        max_workers=2,
        default_poll_ms=200,
        adaptive_threshold=True,
    ),
    ProfileLevel.MEDIUM: PerformanceProfile(
        scan_interval_idle_ms=500,
        scan_interval_active_ms=200,
        scan_interval_fast_ms=100,
        template_cache_size=50,
        template_cache_ttl_seconds=300,
        ocr_cache_size=50,
        ocr_cache_ttl_seconds=2.0,
        memory_threshold_mb=300,
        memory_check_interval_seconds=60,
        max_workers=4,
        default_poll_ms=100,
        adaptive_threshold=True,
    ),
    ProfileLevel.HIGH: PerformanceProfile(
        scan_interval_idle_ms=300,
        scan_interval_active_ms=100,
        scan_interval_fast_ms=50,
        template_cache_size=100,
        template_cache_ttl_seconds=180,
        ocr_cache_size=100,
        ocr_cache_ttl_seconds=1.0,
        memory_threshold_mb=500,
        memory_check_interval_seconds=30,
        max_workers=6,
        default_poll_ms=50,
        adaptive_threshold=True,
    ),
    ProfileLevel.ULTRA: PerformanceProfile(
        scan_interval_idle_ms=200,
        scan_interval_active_ms=50,
        scan_interval_fast_ms=25,
        template_cache_size=200,
        template_cache_ttl_seconds=120,
        ocr_cache_size=200,
        ocr_cache_ttl_seconds=0.5,
        memory_threshold_mb=1000,
        memory_check_interval_seconds=15,
        max_workers=8,
        default_poll_ms=25,
        adaptive_threshold=True,
    ),
}


class ProfileManager:
    """Manages performance profiles and auto-detection."""

    _instance: "ProfileManager | None" = None
    _lock = None
    _initialized: bool = False  # Class-level type hint for mypy

    def __new__(cls) -> "ProfileManager":
        if cls._instance is None:
            import threading
            cls._lock = threading.Lock()
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._current_level = ProfileLevel.MEDIUM
        self._current_profile = PROFILES[ProfileLevel.MEDIUM]
        self._initialized = True

    @property
    def profile(self) -> PerformanceProfile:
        """Get current performance profile."""
        return self._current_profile

    @property
    def level(self) -> ProfileLevel:
        """Get current profile level."""
        return self._current_level

    def set_level(self, level: ProfileLevel) -> None:
        """Set performance profile level."""
        self._current_level = level
        self._current_profile = PROFILES[level]
        logger.info("Performance profile set to: %s", level.name)

    def auto_detect(self) -> ProfileLevel:
        """Auto-detect appropriate profile based on system specs."""
        try:
            import psutil

            # Get system info
            ram_gb = psutil.virtual_memory().total / (1024**3)
            cpu_count = psutil.cpu_count(logical=False) or 2

            logger.info("System: %.1fGB RAM, %d CPU cores", ram_gb, cpu_count)

            # Determine profile
            if ram_gb < 4 or cpu_count < 2:
                level = ProfileLevel.LOW
            elif ram_gb < 8 or cpu_count < 4:
                level = ProfileLevel.MEDIUM
            elif ram_gb < 16 or cpu_count < 6:
                level = ProfileLevel.HIGH
            else:
                level = ProfileLevel.ULTRA

            self.set_level(level)
            return level

        except ImportError:
            logger.warning("psutil not available, using MEDIUM profile")
            return ProfileLevel.MEDIUM

    def get_setting(self, key: str) -> Any:
        """Get a specific setting from current profile."""
        return getattr(self._current_profile, key, None)


# Singleton accessor
_profile_manager: ProfileManager | None = None


def get_profile_manager() -> ProfileManager:
    """Get singleton ProfileManager instance."""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager


def get_profile() -> PerformanceProfile:
    """Get current performance profile."""
    return get_profile_manager().profile
