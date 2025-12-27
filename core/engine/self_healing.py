"""
RetroAuto v2 - Self-Healing Automation

Fallback strategies when primary image match fails:
1. Try alternative/fallback assets
2. Lower threshold (fuzzy matching)
3. OCR text search fallback
4. Expand search region

Phase: Mid-term improvement
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

from infra import get_logger

if TYPE_CHECKING:
    from core.models import Match, ROI
    from vision.matcher import Matcher
    from vision.ocr import TextReader

logger = get_logger("SelfHealing")


class HealingMethod(Enum):
    """Method used to find the element."""

    PRIMARY = auto()  # Found with primary asset
    FALLBACK_ASSET = auto()  # Found with fallback asset
    FUZZY_MATCH = auto()  # Found with lower threshold
    OCR_TEXT = auto()  # Found via OCR
    EXPANDED_ROI = auto()  # Found with expanded ROI
    FAILED = auto()  # All methods failed


@dataclass
class HealingStrategy:
    """
    Self-healing strategy configuration.

    Usage:
        strategy = HealingStrategy(
            asset_id="button_ok",
            fallback_assets=["button_ok_hover", "button_ok_disabled"],
            enable_fuzzy=True,
            fuzzy_threshold=0.6,
        )
    """

    asset_id: str

    # Fallback assets to try if primary fails
    fallback_assets: list[str] = field(default_factory=list)

    # Fuzzy matching (lower threshold)
    enable_fuzzy: bool = True
    fuzzy_threshold: float = 0.6  # Minimum acceptable

    # OCR fallback
    enable_ocr: bool = False
    ocr_text: str = ""  # Text to search for

    # ROI expansion
    expand_roi: bool = True
    expand_pixels: int = 50  # Expand each side by this amount


@dataclass
class HealingResult:
    """Result of self-healing attempt."""

    found: bool
    match: Match | None
    method: HealingMethod
    asset_used: str  # Which asset/text was matched
    confidence: float = 0.0
    attempts: int = 1


class SelfHealingMatcher:
    """
    Wrapper around Matcher with fallback strategies.

    Tries multiple methods to find elements, improving
    automation robustness against UI changes.

    Usage:
        healer = SelfHealingMatcher(matcher, ocr_reader)
        result = healer.find_with_healing(strategy)
        if result.found:
            click(result.match.x, result.match.y)
    """

    def __init__(
        self,
        matcher: Matcher,
        ocr_reader: TextReader | None = None,
    ) -> None:
        self._matcher = matcher
        self._ocr = ocr_reader

    def find_with_healing(
        self,
        strategy: HealingStrategy,
        roi: ROI | None = None,
    ) -> HealingResult:
        """
        Find element using self-healing strategies.

        Tries in order:
        1. Primary asset (normal threshold)
        2. Fallback assets
        3. Fuzzy match (lower threshold)
        4. Expanded ROI
        5. OCR text (if enabled)

        Args:
            strategy: Healing configuration
            roi: Optional ROI override

        Returns:
            HealingResult with match info and method used
        """
        attempts = 0

        # 1. Try primary asset
        attempts += 1
        match = self._matcher.find(strategy.asset_id, roi)
        if match:
            logger.debug("Primary match found: %s", strategy.asset_id)
            return HealingResult(
                found=True,
                match=match,
                method=HealingMethod.PRIMARY,
                asset_used=strategy.asset_id,
                confidence=match.confidence,
                attempts=attempts,
            )

        # 2. Try fallback assets
        for fallback_id in strategy.fallback_assets:
            attempts += 1
            match = self._matcher.find(fallback_id, roi)
            if match:
                logger.info("Fallback match found: %s (primary: %s)", fallback_id, strategy.asset_id)
                return HealingResult(
                    found=True,
                    match=match,
                    method=HealingMethod.FALLBACK_ASSET,
                    asset_used=fallback_id,
                    confidence=match.confidence,
                    attempts=attempts,
                )

        # 3. Try fuzzy matching (lower threshold)
        if strategy.enable_fuzzy:
            attempts += 1
            match = self._matcher.find(strategy.asset_id, roi, adaptive=True)
            if match and match.confidence >= strategy.fuzzy_threshold:
                logger.info(
                    "Fuzzy match found: %s (conf=%.2f)",
                    strategy.asset_id,
                    match.confidence,
                )
                return HealingResult(
                    found=True,
                    match=match,
                    method=HealingMethod.FUZZY_MATCH,
                    asset_used=strategy.asset_id,
                    confidence=match.confidence,
                    attempts=attempts,
                )

        # 4. Try expanded ROI
        if strategy.expand_roi and roi:
            attempts += 1
            expanded_roi = self._expand_roi(roi, strategy.expand_pixels)
            match = self._matcher.find(strategy.asset_id, expanded_roi)
            if match:
                logger.info("Expanded ROI match found: %s", strategy.asset_id)
                return HealingResult(
                    found=True,
                    match=match,
                    method=HealingMethod.EXPANDED_ROI,
                    asset_used=strategy.asset_id,
                    confidence=match.confidence,
                    attempts=attempts,
                )

        # 5. Try OCR fallback
        if strategy.enable_ocr and strategy.ocr_text and self._ocr:
            attempts += 1
            ocr_match = self._find_by_ocr(strategy.ocr_text, roi)
            if ocr_match:
                logger.info("OCR match found: '%s'", strategy.ocr_text)
                return HealingResult(
                    found=True,
                    match=ocr_match,
                    method=HealingMethod.OCR_TEXT,
                    asset_used=f"ocr:'{strategy.ocr_text}'",
                    confidence=1.0,  # OCR is binary
                    attempts=attempts,
                )

        # All methods failed
        logger.warning(
            "Self-healing failed for %s after %d attempts",
            strategy.asset_id,
            attempts,
        )
        return HealingResult(
            found=False,
            match=None,
            method=HealingMethod.FAILED,
            asset_used=strategy.asset_id,
            attempts=attempts,
        )

    def _expand_roi(self, roi: ROI, pixels: int) -> ROI:
        """Expand ROI by given pixels on each side."""
        from core.models import ROI as ROIModel

        return ROIModel(
            x=max(0, roi.x - pixels),
            y=max(0, roi.y - pixels),
            w=roi.w + pixels * 2,
            h=roi.h + pixels * 2,
        )

    def _find_by_ocr(self, text: str, roi: ROI | None) -> Match | None:
        """Find text on screen using OCR."""
        if not self._ocr:
            return None

        try:
            # Capture screen
            from vision.capture import get_capture

            capture = get_capture()
            if roi:
                screen = capture.capture_roi(roi)
            else:
                screen = capture.capture_full()

            # Run OCR
            results = self._ocr.read(screen)

            # Find matching text
            for result in results:
                if text.lower() in result.text.lower():
                    from core.models import Match

                    return Match(
                        x=result.x + (roi.x if roi else 0),
                        y=result.y + (roi.y if roi else 0),
                        w=result.w,
                        h=result.h,
                        confidence=result.confidence,
                    )
        except Exception as e:
            logger.warning("OCR fallback failed: %s", e)

        return None
