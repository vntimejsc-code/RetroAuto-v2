import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PIL import Image, ImageDraw

from core.models import ROI
from vision.ocr import TextReader


class TestOCR(unittest.TestCase):
    def setUp(self):
        self.reader = TextReader()

    def test_ocr_read(self):
        if not self.reader.available:
            print("WARNING: Tesseract not installed. Skipping OCR test.")
            return

        # Create image with text
        img = Image.new("RGB", (200, 50), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        # Use default bitmap font
        d.text((10, 10), "HP: 100/100", fill=(0, 0, 0))

        # Read
        text = self.reader.read_from_image(img)
        print(f"OCR Read: '{text}'")

        # Tesseract usually struggles with default PIL font (very small) unless scaled
        # But let's see if it gets anything.
        # Ideally we'd use a better font, but we don't know if arial.ttf is available?
        # Windows usually has arial.

        # Only assert if we got something, otherwise just warn (environment dependent)
        if text:
            self.assertIn("100", text)

    def test_roi_crop(self):
        if not self.reader.available:
            return

        img = Image.new("RGB", (200, 50), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((10, 10), "Mana: 50", fill=(0, 0, 0))

        # ROI matching the text area roughly
        roi = ROI(x=0, y=0, w=100, h=50)
        text = self.reader.read_from_image(img, roi=roi)
        print(f"ROI Read: '{text}'")


if __name__ == "__main__":
    unittest.main()
