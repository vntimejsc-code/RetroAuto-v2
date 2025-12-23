"""
RetroAuto v2 - Template Matcher

OpenCV template matching with ROI optimization.
"""

import cv2
import numpy as np

from core.models import ROI, AssetImage, Match, MatchMethod
from core.templates import TemplateStore
from infra import get_logger
from vision.capture import ScreenCapture, get_capture

logger = get_logger("Matcher")

# OpenCV method mapping
CV_METHODS = {
    MatchMethod.TM_CCOEFF_NORMED: cv2.TM_CCOEFF_NORMED,
    MatchMethod.TM_CCORR_NORMED: cv2.TM_CCORR_NORMED,
    MatchMethod.TM_SQDIFF_NORMED: cv2.TM_SQDIFF_NORMED,
}


class Matcher:
    """
    Template matcher using OpenCV.

    Features:
    - ROI-first matching (faster)
    - Grayscale optimization
    - Multiple match methods
    - Confidence thresholding
    """

    def __init__(
        self,
        templates: TemplateStore,
        capture: ScreenCapture | None = None,
    ) -> None:
        self._templates = templates
        self._capture = capture or get_capture()

    def find(
        self,
        asset_id: str,
        roi_override: ROI | None = None,
        adaptive: bool = False,
    ) -> Match | None:
        """
        Find asset on screen.

        Args:
            asset_id: Asset ID from template store
            roi_override: Override asset's default ROI
            adaptive: Allow adaptive thresholding (lower confidence)

        Returns:
            Match if found with confidence >= threshold (or adaptive floor), else None
        """
        # Get template
        tmpl_data = self._templates.get(asset_id)
        if tmpl_data is None:
            logger.warning("Asset not found in store: %s", asset_id)
            return None

        asset: AssetImage = tmpl_data["asset"]
        tmpl_img: np.ndarray = tmpl_data["gray"] if asset.grayscale else tmpl_data["color"]
        tmpl_h, tmpl_w = tmpl_data["shape"]

        # Determine ROI
        roi = roi_override or asset.roi

        # Capture screen
        if roi:
            screen = self._capture.capture_roi(roi, grayscale=asset.grayscale)
            offset_x, offset_y = roi.x, roi.y
        else:
            screen = self._capture.capture_full(grayscale=asset.grayscale)
            offset_x, offset_y = 0, 0

        # Match
        result = cv2.matchTemplate(screen, tmpl_img, CV_METHODS[asset.method])

        # Get best match
        if asset.method == MatchMethod.TM_SQDIFF_NORMED:
            # For SQDIFF, lower is better
            min_val, _, min_loc, _ = cv2.minMaxLoc(result)
            confidence = 1.0 - min_val
            loc = min_loc
        else:
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            confidence = max_val
            loc = max_loc

        # Check threshold
        if confidence < asset.threshold:
            bypass = False
            if adaptive and confidence >= 0.6:
                logger.warning(
                    "Adaptive Match: %s found with %.2f (threshold logic bypassed from %.2f)", 
                    asset_id, confidence, asset.threshold
                )
                bypass = True
            
            if not bypass:
                logger.debug(
                    "Match below threshold: %s (%.2f < %.2f)", asset_id, confidence, asset.threshold
                )
                return None

        # Create match with absolute coordinates
        match = Match(
            x=loc[0] + offset_x,
            y=loc[1] + offset_y,
            w=tmpl_w,
            h=tmpl_h,
            confidence=confidence,
        )

        logger.debug("Found %s at (%d, %d) conf=%.2f", asset_id, match.x, match.y, confidence)
        return match

    def find_all(
        self,
        asset_id: str,
        roi_override: ROI | None = None,
        max_matches: int = 10,
    ) -> list[Match]:
        """
        Find all occurrences of asset on screen.

        Args:
            asset_id: Asset ID
            roi_override: Override default ROI
            max_matches: Maximum matches to return

        Returns:
            List of matches sorted by confidence
        """
        tmpl_data = self._templates.get(asset_id)
        if tmpl_data is None:
            return []

        asset: AssetImage = tmpl_data["asset"]
        tmpl_img: np.ndarray = tmpl_data["gray"] if asset.grayscale else tmpl_data["color"]
        tmpl_h, tmpl_w = tmpl_data["shape"]

        roi = roi_override or asset.roi

        if roi:
            screen = self._capture.capture_roi(roi, grayscale=asset.grayscale)
            offset_x, offset_y = roi.x, roi.y
        else:
            screen = self._capture.capture_full(grayscale=asset.grayscale)
            offset_x, offset_y = 0, 0

        result = cv2.matchTemplate(screen, tmpl_img, CV_METHODS[asset.method])

        # Find all locations above threshold
        if asset.method == MatchMethod.TM_SQDIFF_NORMED:
            locations = np.where(result <= (1.0 - asset.threshold))
            confidences = 1.0 - result[locations]
        else:
            locations = np.where(result >= asset.threshold)
            confidences = result[locations]

        matches = []
        for i, (y, x) in enumerate(zip(locations[0], locations[1], strict=False)):
            if len(matches) >= max_matches:
                break
            matches.append(
                Match(
                    x=int(x) + offset_x,
                    y=int(y) + offset_y,
                    w=tmpl_w,
                    h=tmpl_h,
                    confidence=float(confidences[i]),
                )
            )

        # Sort by confidence descending
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches

    def exists(
        self,
        asset_id: str,
        roi_override: ROI | None = None,
    ) -> bool:
        """Quick check if asset exists on screen."""
        return self.find(asset_id, roi_override) is not None
