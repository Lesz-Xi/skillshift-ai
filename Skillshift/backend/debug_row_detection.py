#!/usr/bin/env python3
"""
Debug the row detection system
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def debug_row_detection():
    """Debug the row detection step by step"""
    
    # Load test image
    img_path = "backend/tests/fixtures/IMG_1767.png"
    print(f"🔍 Debugging row detection with: {img_path}")
    
    image = cv2.imread(img_path)
    if image is None:
        print(f"❌ Failed to load image: {img_path}")
        return
    
    print(f"✅ Image loaded: {image.shape}")
    
    target_ign = "Diary of dolls"
    print(f"\n🎯 Target IGN: '{target_ign}'")
    
    try:
        # Step 1: Test blue panel detection
        from ocr.detectors import detect_blue_panel
        from ocr.utils_geometry import row_bbox
        
        panel = detect_blue_panel(image)
        print(f"\n📍 Blue panel detected: {panel}")
        
        # Load config for debugging
        import yaml
        with open("backend/ocr/config_ocr.yaml", "r") as f:
            CFG = yaml.safe_load(f)
        
        rows = CFG["table"]["rows"]
        top_off = CFG["table"]["row_top_offset_pct"]
        bot_off = CFG["table"]["row_bottom_offset_pct"]
        name_start_pct = CFG["table"]["name_col_start_pct"]
        name_w_pct = CFG["table"]["name_col_width_pct"]
        sim_thresh = CFG["matching"]["fuzzy_ign_threshold"]
        
        print(f"Configuration:")
        print(f"  Rows: {rows}")
        print(f"  Top offset: {top_off}")
        print(f"  Bottom offset: {bot_off}")
        print(f"  Name start %: {name_start_pct}")
        print(f"  Name width %: {name_w_pct}")
        print(f"  Similarity threshold: {sim_thresh}")
        
        # Step 2: Test each row
        import easyocr
        from difflib import SequenceMatcher
        
        reader = easyocr.Reader(['en'], gpu=False)
        
        def fuzzy_sim(a, b):
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()
        
        print(f"\n🔍 Testing each row:")
        
        debug_dir = Path("debug_output")
        debug_dir.mkdir(exist_ok=True)
        
        best_scores = []
        
        for i in range(rows):
            print(f"\n--- Row {i} ---")
            
            # Calculate row bbox
            rbox = row_bbox(panel, i, rows, top_off, bot_off)
            print(f"Row bbox: {rbox}")
            
            # Calculate name column bbox using new positioning
            from ocr.utils_geometry import BBox
            name_x = rbox.x + int(rbox.w * name_start_pct)
            name_w = int(rbox.w * name_w_pct)
            name_box = BBox(name_x, rbox.y, name_w, rbox.h)
            print(f"Name bbox: {name_box}")
            
            # Extract name crop
            crop = image[name_box.y:name_box.y+name_box.h, name_box.x:name_box.x+name_box.w]
            print(f"Crop shape: {crop.shape}")
            
            # Save crop for visual inspection
            cv2.imwrite(str(debug_dir / f"row_{i}_name_crop.png"), crop)
            
            # OCR the name column
            try:
                ocr_results = reader.readtext(crop, detail=1, paragraph=True)
                text = " ".join([t[1] for t in ocr_results if len(t) >= 2])
                print(f"OCR text: '{text}'")
                
                # Calculate similarity
                sim = fuzzy_sim(text, target_ign)
                print(f"Similarity to '{target_ign}': {sim:.3f}")
                
                best_scores.append((i, sim, text))
                
                if sim >= sim_thresh:
                    print(f"✅ MATCH! Row {i} meets threshold")
                
            except Exception as e:
                print(f"❌ OCR failed: {e}")
                best_scores.append((i, 0.0, ""))
        
        # Summary
        print(f"\n📊 Summary:")
        best_scores.sort(key=lambda x: x[1], reverse=True)
        
        for i, (row, sim, text) in enumerate(best_scores):
            status = "✅" if sim >= sim_thresh else "❌"
            print(f"  {status} Row {row}: {sim:.3f} - '{text}'")
        
        best_row, best_sim, best_text = best_scores[0]
        print(f"\n🏆 Best match: Row {best_row} with similarity {best_sim:.3f}")
        
        if best_sim < sim_thresh:
            print(f"💡 Suggestion: Lower similarity threshold from {sim_thresh:.3f} to {best_sim - 0.05:.3f}")
        
        print(f"\n💾 Debug images saved to {debug_dir}/")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_row_detection()