#!/usr/bin/env python3
"""
Simple test for dynamic KDA extraction
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from ocr.parsers_kda import _extract_kda_from_image

def test_simple():
    """Simple focused test"""
    
    # Load test image
    img_path = "backend/tests/fixtures/IMG_1767.png"
    print(f"Loading image: {img_path}")
    
    image = cv2.imread(img_path)
    if image is None:
        print(f"❌ Failed to load image: {img_path}")
        return
    
    print(f"✅ Image loaded: {image.shape}")
    
    # Test the IGN-anchored KDA extraction function directly
    target_ign = "Diary of dolls"
    player_row_index = 2  # Based on previous testing
    
    print(f"\n🎯 Testing _extract_kda_from_image with IGN: '{target_ign}' at row {player_row_index}")
    
    try:
        result = _extract_kda_from_image(image, player_row_index, mvp_score=None, target_ign=target_ign)
        print(f"KDA extraction result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()