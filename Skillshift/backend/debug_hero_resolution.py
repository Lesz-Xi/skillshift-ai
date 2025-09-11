#!/usr/bin/env python3
"""Debug script for hero resolution"""

import sys
import os
sys.path.append('backend')

from backend.ocr.templates_index import get_all_templates
from backend.ocr.hero_resolver import resolve_hero_from_portrait
import cv2
import numpy as np

def debug_hero_resolution():
    """Debug hero resolution process"""
    print("=== Debug Hero Resolution ===")
    
    # Check templates
    templates = get_all_templates()
    print(f"Loaded {len(templates)} templates:")
    for slug, template in templates.items():
        print(f"  {slug}: phash={template['phash'][:8]}...")
    
    # Load test image
    test_image_path = "tests/fixtures/IMG_1767.PNG"
    if os.path.exists(test_image_path):
        image = cv2.imread(test_image_path)
        print(f"Loaded test image: {image.shape}")
        
        # Test avatar bbox (simplified)
        h, w = image.shape[:2]
        avatar_bbox = (int(0.02*w), int(0.10*h), int(0.10*w), int(0.80*h))
        print(f"Avatar bbox: {avatar_bbox}")
        
        # Test hero resolution
        hero_slug, confidence, debug_info = resolve_hero_from_portrait(
            image, avatar_bbox, templates
        )
        
        print(f"Hero resolution result:")
        print(f"  Hero: {hero_slug}")
        print(f"  Confidence: {confidence}")
        print(f"  Debug info: {debug_info}")
    else:
        print(f"Test image not found: {test_image_path}")

if __name__ == "__main__":
    debug_hero_resolution()
