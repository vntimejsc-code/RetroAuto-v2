"""
OCR Module for Text Recognition.
Wraps pytesseract/Tesseract-OCR.
"""
import logging
import os

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

    def read_from_file(self, image_path: str, roi: ROI | None = None, allowlist: str = "") -> str:
        """Read text from an image file."""
        if not self.available:
            logger.error("OCR not available (pytesseract missing)")
            return ""

        try:
            img = Image.open(image_path)
            # Convert ROI object to dictionary for the new read_from_image signature
            roi_dict = {"x": roi.x, "y": roi.y, "w": roi.w, "h": roi.h} if roi else None
            return self.read_from_image(img, allowlist=allowlist, roi=roi_dict)
        except Exception as e:
            logger.error(f"OCR File Error: {e}")
            return ""

    def read_from_image(
        self, image: Image.Image, allowlist: str | None = None, roi: dict | None = None
    ) -> str:
        """
        Extract text from image with robust error handling.

        Args:
            image: PIL Image to read from
            allowlist: Characters to allow (e.g., "0123456789" for numbers only)
            roi: Region of interest {"x": int, "y": int, "w": int, "h": int}

        Returns:
            Extracted text, or empty string on failure
        """
        if not self.available:
            logger.warning("OCR not available - cannot read text")
            return ""

        try:
            # Validate image
            if image is None or image.size[0] == 0 or image.size[1] == 0:
                logger.error("Invalid image: None or zero size")
                return ""

            # Apply ROI if specified
            if roi:
                # Validate ROI bounds
                img_width, img_height = image.size
                x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]

                if x < 0 or y < 0 or w <= 0 or h <= 0:
                    logger.error(f"Invalid ROI coordinates: {roi}")
                    return ""

                if x + w > img_width or y + h > img_height:
                    logger.warning(
                        f"ROI {roi} exceeds image bounds ({img_width}x{img_height}), "
                        f"clamping to valid region"
                    )
                    # Clamp to valid region
                    w = min(w, img_width - x)
                    h = min(h, img_height - y)

                # Crop to ROI
                try:
                    image = image.crop((x, y, x + w, y + h))
                except Exception as e:
                    logger.error(f"Failed to crop ROI {roi}: {e}")
                    return ""

            # Convert to grayscale for better OCR
            try:
                if image.mode != "L":
                    image = image.convert("L")
            except Exception as e:
                logger.warning(f"Failed to convert to grayscale: {e}, using original")

            # Build config
            config = "--psm 6"  # Assume uniform block of text
            if allowlist:
                # Tesseract 4/5 uses multiple engines, some allowlist features behave differently
                # But generally -c tessedit_char_whitelist=... works
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
            return ""
