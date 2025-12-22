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
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe")
                ]
                
                # Only set if not already set (default is 'tesseract')
                cmd = pytesseract.pytesseract.tesseract_cmd
                if cmd == 'tesseract':
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
            return self.read_from_image(img, roi, allowlist)
        except Exception as e:
            logger.error(f"OCR File Error: {e}")
            return ""

    def read_from_image(self, img: Image.Image, roi: ROI | None = None, allowlist: str = "") -> str:
        """Read text from a PIL Image object."""
        if not self.available:
            return ""
            
        try:
            # Crop to ROI if specified
            if roi:
                # ROI is x, y, w, h
                # Image.crop takes (left, top, right, bottom)
                box = (roi.x, roi.y, roi.x + roi.w, roi.y + roi.h)
                img = img.crop(box)
            
            # Pre-processing
            # Convert to grayscale
            img = img.convert('L')
            
            # Simple thresholding to binary (can improve simple text)
            # img = img.point(lambda p: 255 if p > 128 else 0)
            
            # Build config
            # --psm 7 is "Treat the image as a single text line" - good for game stats
            # --psm 6 is "Assume a single uniform block of text"
            config_opts = ["--psm 7"] 
            
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
                self.available = False
            return ""
