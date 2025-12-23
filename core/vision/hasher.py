"""
Image Hashing Module
Part of "Titan Light" Phase 3 (Flight Recorder).

Provides methods to calculate perceptual hashes (aHash/pHash) of images
to detect if the screen content has changed effectively.
"""

import cv2
import numpy as np
from PIL import Image


def calculate_phash(image: Image.Image | np.ndarray) -> int:
    """
    Calculate Perceptual Hash (pHash) of an image.
    Robust against minor changes (noise, slight color shifts).

    Args:
        image: PIL Image or numpy array (BGR/RGB)

    Returns:
        64-bit integer hash
    """
    # Convert PIL to numpy if needed
    if isinstance(image, Image.Image):
        image = np.array(image)
        # Convert RGB to BGR for cv2 consistency if needed,
        # but for grayscale conversion it largely doesn't matter
        # as long as we use the right conversion code.
        # PIL is RGB.
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    elif isinstance(image, np.ndarray):
        if len(image.shape) == 3:
            # Assuming BGR from cv2 standard or screen capture
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 1. Resize to 32x32
    img_resized = cv2.resize(image, (32, 32), interpolation=cv2.INTER_AREA)

    # 2. Compute DCT
    float_img = np.float32(img_resized)
    dct = cv2.dct(float_img)

    # 3. Take top-left 8x8 (low frequencies)
    # Skipping DC component (0,0) usually recommended for robustness against brightness
    dct_low_freq = dct[0:8, 0:8]

    # 4. Compute average (excluding DC)
    avg = (np.sum(dct_low_freq) - dct_low_freq[0, 0]) / 63

    # 5. Compute hash
    hash_val = 0
    idx = 0
    for i in range(8):
        for j in range(8):
            val = 1 if dct_low_freq[i, j] > avg else 0
            hash_val |= val << idx
            idx += 1

    return hash_val


def hamming_distance(hash1: int, hash2: int) -> int:
    """
    Calculate Hamming distance between two 64-bit hashes.
    Unchanged screen ~ distance 0-2
    Significant change > 5
    """
    x = hash1 ^ hash2
    return bin(x).count("1")
