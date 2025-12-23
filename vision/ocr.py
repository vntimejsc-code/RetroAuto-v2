"""
OCR Module for Text Recognition.
Wraps pytesseract/Tesseract-OCR.
"""
import logging
import os

import cv2
import numpy as np
from PIL import Image

# Try to import pytesseract
try:
    import pytesseract

    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

from core.models import ROI

logger = logging.getLogger(__name__)


class TextReader:
    """
    OCR Reader using Tesseract.
    """

    def __init__(self) -> None:
        self.available = HAS_TESSERACT
        if not self.available:
            logger.warning("pytesseract not installed. OCR features will be disabled.")

    def is_available(self) -> bool:
        """
        Check if OCR is available and working.

        Returns:
            True if Tesseract is installed and accessible
        """
        if not self.available:
            return False

        try:
            # Try to get Tesseract version as a quick check
            import pytesseract

            version = pytesseract.get_tesseract_version()
            return version is not None
        except Exception:
            return False

        # Check for Tesseract binary in common Windows paths if not in PATH
        if HAS_TESSERACT:
            try:
                # Simple check if "tesseract" command is available
                # If shutil.which("tesseract") is None, we might need to look for it.
                # For now, we trust the user has Tesseract in PATH or we set a default.

                # Common defaults for Windows
                known_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
                ]

                # Only set if not already set (default is 'tesseract')
                cmd = pytesseract.pytesseract.tesseract_cmd
                if cmd == "tesseract":
                    import shutil

                    if not shutil.which("tesseract"):
                        for p in known_paths:
                            if os.path.exists(p):
                                pytesseract.pytesseract.tesseract_cmd = p
                                logger.info(f"Set Tesseract path to: {p}")
                                break
            except Exception as e:
                logger.warning(f"Error configuring Tesseract: {e}")

    def preprocess_image(
        self, img: Image.Image, scale: float = 1.0, invert: bool = False, binarize: bool = False
    ) -> Image.Image:
        """
        Preprocess image for better OCR.

        Args:
            img: Input PIL Image
            scale: Scaling factor (e.g. 2.0 to double size)
            invert: Invert colors (useful for white text on dark bg)
            binarize: Apply OTSU thresholding

        Returns:
            Processed PIL Image
        """
        try:
            # Convert to numpy for CV2 operations
            # PIL RGB -> CV2 BGR (or Grayscale)
            # Standard conversion:
            open_cv_image = np.array(img)

            # Convert to grayscale if not already
            if len(open_cv_image.shape) == 3:
                open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)

            # Scaling
            if scale != 1.0 and scale > 0:
                width = int(open_cv_image.shape[1] * scale)
                height = int(open_cv_image.shape[0] * scale)
                open_cv_image = cv2.resize(
                    open_cv_image, (width, height), interpolation=cv2.INTER_CUBIC
                )

            # Inversion (White on Black -> Black on White)
            if invert:
                open_cv_image = cv2.bitwise_not(open_cv_image)

            # Binarization (Thresholding)
            if binarize:
                # Otsu's thresholding
                _, open_cv_image = cv2.threshold(
                    open_cv_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )

            # Convert back to PIL
            return Image.fromarray(open_cv_image)

        except Exception as e:
            logger.error(f"Preprocessing Error: {e}")
            return img

    def read_from_file(self, image_path: str, roi: ROI | None = None, allowlist: str = "") -> str:
        """Read text from an image file."""
        if not self.available:
            logger.error("OCR not available (pytesseract missing)")
            return ""

        try:
            img = Image.open(image_path)
            return self.read_from_image(img, roi, allowlist=allowlist)
        except Exception as e:
            logger.error(f"OCR File Error: {e}")
            return ""

    def read_from_image(
        self,
        img: Image.Image,
        roi: ROI | None = None,
        allowlist: str = "",
        scale: float = 1.0,
        invert: bool = False,
        binarize: bool = False,
    ) -> str:
        """
        Read text from a PIL Image object with options.
        """
        if not self.available:
            return ""

        try:
            # Crop to ROI if specified
            if roi:
                # ROI is x, y, w, h
                box = (roi.x, roi.y, roi.x + roi.w, roi.y + roi.h)
                img = img.crop(box)

            # Preprocessing
            img = self.preprocess_image(img, scale, invert, binarize)

            # Build config
            # --psm 7 is "Treat the image as a single text line" - good for game stats
            config_opts = ["--psm 7"]

            if allowlist:
                config_opts.append(f"-c tessedit_char_whitelist={allowlist}")

            config_str = " ".join(config_opts)

            text = pytesseract.image_to_string(img, config=config_str)
            return text.strip()

        except Exception as e:
            logger.error(f"OCR Execution Error: {e}")
            # If tesseract not found, it raises TesseractNotFoundError
            if "tesseract is not installed" in str(e).lower() or "not found" in str(e).lower():
                self.available = False
                logger.critical("Tesseract binary not found! Please install Tesseract-OCR.")
                self.available = False
            return ""
