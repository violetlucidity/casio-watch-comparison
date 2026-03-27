#!/usr/bin/env python3
"""
Rotate landscape-oriented Pixabay images 90° clockwise and re-standardize.
All Pixabay images are 400x290 (landscape) and need rotation to portrait orientation.
"""

import os
from PIL import Image
import shutil

NOBG_DIR = "images/nobg"
ORIGINALS_DIR = "images/originals"
WATCHES_400_DIR = "images/watches/400"
WATCHES_120_DIR = "images/watches/120"

# All 18 Pixabay-sourced models (confirmed from footer)
PIXABAY_MODELS = [
    "F-91W", "F-93W", "F-200W", "A500", "AE-1200SN",
    "AW90", "AW49", "AQ230", "W-213", "W-215",
    "WS-1000H", "WV-59", "MW-59",
    "PRG-340", "EFR-S108D", "MSG-S600G", "OCW-T200S", "LF-20W"
]

def rotate_image_file(filepath):
    """Rotate PNG 90° clockwise and save in-place."""
    try:
        img = Image.open(filepath)
        # Check if landscape (width > height)
        if img.width > img.height:
            print(f"  {os.path.basename(filepath)}: {img.size} (landscape) → rotating 90° CW")
            rotated = img.rotate(-90, expand=True)  # -90 = clockwise
            rotated.save(filepath)
            return True
        else:
            print(f"  {os.path.basename(filepath)}: {img.size} (already portrait) → skip")
            return False
    except Exception as e:
        print(f"  ERROR rotating {filepath}: {e}")
        return False

print("Rotating Pixabay images from landscape to portrait orientation...\n")

rotated_count = 0
for model in PIXABAY_MODELS:
    nobg_file = os.path.join(NOBG_DIR, f"{model}.png")
    if os.path.exists(nobg_file):
        if rotate_image_file(nobg_file):
            rotated_count += 1
    else:
        print(f"  {model}.png not found in {NOBG_DIR}")

print(f"\nRotated {rotated_count} images.")
print("Next: Run standardize_images_final.py to re-crop and resize.")
