"""
RetroAuto v2 - Memory Manager

Background memory monitoring and cleanup for 24/7 operation.
Phase 2.2 Performance Optimization.
"""

import gc
import threading
import time
from typing import Callable

from infra import get_logger

logger = get_logger("MemoryManager")


class MemoryManager:
    """
    Background memory monitoring and cleanup for 24/7 operation.

    Features:
    - Periodic memory monitoring
    - Threshold-based garbage collection
    - Cache cleanup coordination
    - Memory usage logging
    """

    _instance: "MemoryManager | None" = None
    _lock = threading.Lock()
    _initialized: bool = False  # Class-level type hint for mypy

    def __new__(cls) -> "MemoryManager":
        """Singleton pattern for single memory manager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        threshold_mb: int = 200,  # Lowered from 300 for 24/7 stability
        check_interval_seconds: int = 30,  # More frequent from 60 for proactive cleanup
    ) -> None:
        if self._initialized:
            return

        self._threshold = threshold_mb * 1024 * 1024  # Convert to bytes
        self._check_interval = check_interval_seconds
        self._running = False
        self._thread: threading.Thread | None = None

        # Callbacks for coordinated cleanup
        self._cleanup_callbacks: list[Callable[[], None]] = []

        # Stats
        self._cleanup_count = 0
        self._peak_memory = 0

        self._initialized = True
        logger.info(
            "MemoryManager initialized (threshold: %dMB, interval: %ds)",
            threshold_mb,
            check_interval_seconds,
        )

    def register_cleanup(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called during cleanup."""
        self._cleanup_callbacks.append(callback)

    def start(self) -> None:
        """Start background monitoring thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("MemoryManager started")

    def stop(self) -> None:
        """Stop background monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("MemoryManager stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                mem_bytes = self._get_memory_usage()
                mem_mb = mem_bytes / (1024 * 1024)

                # Track peak
                if mem_bytes > self._peak_memory:
                    self._peak_memory = mem_bytes

                # Check threshold
                if mem_bytes > self._threshold:
                    logger.warning(
                        "Memory threshold exceeded: %.1fMB > %.1fMB, triggering cleanup",
                        mem_mb,
                        self._threshold / (1024 * 1024),
                    )
                    self._force_cleanup()

            except Exception as e:
                logger.error("MemoryManager error: %s", e)

            time.sleep(self._check_interval)

    def _get_memory_usage(self) -> int:
        """Get current process memory usage in bytes."""
        try:
            import psutil

            return psutil.Process().memory_info().rss
        except ImportError:
            # Fallback: estimate from gc
            import sys

            return sum(sys.getsizeof(obj) for obj in gc.get_objects()[:1000])
        except (OSError, PermissionError) as e:
            logger.debug("Failed to get memory usage: %s", e)
            return 0

    def _force_cleanup(self) -> None:
        """Force garbage collection and notify callbacks."""
        before = self._get_memory_usage()

        # Run registered cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.warning("Cleanup callback error: %s", e)

        # Force garbage collection
        gc.collect()

        after = self._get_memory_usage()
        freed = before - after
        self._cleanup_count += 1

        logger.info(
            "Cleanup #%d: freed %.1fMB (%.1fMB -> %.1fMB)",
            self._cleanup_count,
            freed / (1024 * 1024),
            before / (1024 * 1024),
            after / (1024 * 1024),
        )

    def get_stats(self) -> dict:
        """Get memory statistics."""
        current = self._get_memory_usage()
        return {
            "current_mb": current / (1024 * 1024),
            "peak_mb": self._peak_memory / (1024 * 1024),
            "threshold_mb": self._threshold / (1024 * 1024),
            "cleanup_count": self._cleanup_count,
            "running": self._running,
        }

    def force_gc(self) -> None:
        """Manually trigger garbage collection."""
        self._force_cleanup()


# Singleton accessor
_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """Get singleton MemoryManager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
