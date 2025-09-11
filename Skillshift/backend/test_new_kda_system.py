#!/usr/bin/env python3
"""
Test the new comprehensive KDA detection system
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_new_system():
    """Test the new KDA detection system"""
    
    # Load test image
    img_path = "backend/tests/fixtures/IMG_1767.png"
    print(f"🔍 Testing new KDA system with: {img_path}")
    
    image = cv2.imread(img_path)
    if image is None:
        print(f"❌ Failed to load image: {img_path}")
        return
    
    print(f"✅ Image loaded: {image.shape}")
    
    target_ign = "Diary of dolls"
    print(f"\n🎯 Target IGN: '{target_ign}'")
    
    try:
        # Test 1: Row detection with fuzzy matching
        print(f"\n📍 Step 1: Testing row detection")
        from ocr.detectors import detect_player_row_fuzzy
        
        row_index = detect_player_row_fuzzy(image, target_ign)
        print(f"Detected row index: {row_index}")
        
        if row_index == -1:
            print(f"❌ IGN '{target_ign}' not found with sufficient confidence")
            return
        
        print(f"✅ Found '{target_ign}' at row {row_index}")
        
        # Test 2: KDA extraction using slash-guided detection
        print(f"\n🔍 Step 2: Testing KDA extraction")
        from ocr.kda_cell_reader_v2 import read_kda_for_row
        
        kda_result = read_kda_for_row(image, row_index)
        print(f"KDA result: {kda_result}")
        
        if kda_result:
            k = kda_result.get("k")
            d = kda_result.get("d")
            a = kda_result.get("a")
            print(f"✅ Extracted KDA: K={k}, D={d}, A={a}")
            
            # Check if we got the expected 9/2/12
            if k == 9 and d == 2 and a == 12:
                print(f"🎉 SUCCESS: Got expected values 9/2/12!")
            else:
                print(f"⚠️  Different values than expected (9/2/12)")
        else:
            print(f"❌ KDA extraction failed")
        
        # Test 3: Full parser integration
        print(f"\n🔄 Step 3: Testing full parser")
        from ocr.parsers_kda import parse_kda_view_v2
        
        result = parse_kda_view_v2(image, target_ign)
        print(f"Parser result:")
        print(f"  KDA: {result.kda}")
        print(f"  MVP Score: {result.mvp_score}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Warnings: {result.warnings}")
        
        if result.kda and result.kda.get("k") == 9 and result.kda.get("d") == 2 and result.kda.get("a") == 12:
            print(f"🎉 FULL SUCCESS: Parser extracted expected 9/2/12!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_system()