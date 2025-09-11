#!/usr/bin/env python3
"""
Debug script for dynamic KDA extraction
"""

import cv2
import numpy as np
from pathlib import Path
import sys
import os

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from ocr.detectors import detect_table_regions, rel_to_abs
from ocr.kda_cell_reader import KDACellReader
from ocr.parsers_kda import parse_kda_view

def debug_dynamic_kda():
    """Debug the dynamic KDA extraction system"""
    
    # Load test image
    img_path = "backend/tests/fixtures/IMG_1767.png"
    print(f"Loading image: {img_path}")
    
    image = cv2.imread(img_path)
    if image is None:
        print(f"❌ Failed to load image: {img_path}")
        return
    
    print(f"✅ Image loaded: {image.shape}")
    
    # Test dynamic KDA parsing
    target_ign = "Diary of dolls"
    print(f"\n🎯 Testing dynamic KDA parsing for IGN: '{target_ign}'")
    
    try:
        # Run the full parsing pipeline (Row 2 based on previous testing)
        result = parse_kda_view(image, player_row_index=2, target_ign=target_ign)
        print(f"Parse result: {result}")
        
        # Now let's debug step by step
        print(f"\n🔍 Step-by-step debugging:")
        
        # Step 1: Table detection with IGN
        regions = detect_table_regions(image, target_ign=target_ign)
        print(f"Regions detected: {len(regions.get('rows', []))} rows")
        
        if 'ign_detection' in regions:
            ign_info = regions['ign_detection']
            print(f"IGN Detection: {ign_info}")
            
            if ign_info.get('found'):
                row_index = ign_info['row_index']
                ign_bbox = ign_info['ign_bbox']
                print(f"IGN found in row {row_index} at bbox {ign_bbox}")
                
                # Get the row image
                if row_index < len(regions['rows']):
                    row_info = regions['rows'][row_index]
                    row_y1, row_y2 = row_info['y1'], row_info['y2']
                    row_img = image[row_y1:row_y2]
                    
                    print(f"Row image shape: {row_img.shape}")
                    
                    # Calculate dynamic KDA bbox
                    nx1, ny1, nx2, ny2 = ign_bbox
                    h, w = row_img.shape[:2]
                    
                    # Tunables (safe defaults)
                    PAD_Y = 6
                    BOX_W = int(0.18 * w)  # width ~18% row width
                    BOX_H = max(ny2 - ny1 + 2*PAD_Y, int(0.28 * h))
                    
                    # KDA box to the RIGHT of the name
                    kda_x1 = min(w-1, nx2 + 4)  # start a few px after name
                    kda_x2 = min(w, kda_x1 + BOX_W)
                    kda_y1 = max(0, ny1 - PAD_Y)
                    kda_y2 = min(h, kda_y1 + BOX_H)
                    
                    kda_bbox = (kda_x1, kda_y1, kda_x2, kda_y2)
                    name_x2 = nx2
                    
                    print(f"Dynamic KDA bbox: {kda_bbox}")
                    print(f"Name right edge: {name_x2}")
                    
                    # Extract the KDA crop
                    kda_crop = row_img[kda_y1:kda_y2, kda_x1:kda_x2]
                    print(f"KDA crop shape: {kda_crop.shape}")
                    
                    # Save debug images
                    debug_dir = Path("debug_output")
                    debug_dir.mkdir(exist_ok=True)
                    
                    # Save row image with boxes
                    row_debug = row_img.copy()
                    # Draw IGN bbox in green
                    cv2.rectangle(row_debug, (nx1, ny1), (nx2, ny2), (0, 255, 0), 2)
                    # Draw KDA bbox in red
                    cv2.rectangle(row_debug, (kda_x1, kda_y1), (kda_x2, kda_y2), (0, 0, 255), 2)
                    cv2.imwrite(str(debug_dir / "row_with_boxes.png"), row_debug)
                    
                    # Save KDA crop
                    cv2.imwrite(str(debug_dir / "kda_crop.png"), kda_crop)
                    
                    print(f"✅ Debug images saved to {debug_dir}/")
                    
                    # Test KDA extraction on this crop
                    print(f"\n🧪 Testing KDA extraction on crop:")
                    
                    reader = KDACellReader()
                    kda_result, confidence = reader.read_kda_from_cell(
                        row_img, kda_bbox, mvp_score=None, name_x2=name_x2
                    )
                    
                    print(f"KDA extraction result: {kda_result}")
                    print(f"Confidence: {confidence}")
                    
                    # Manual OCR test on the crop
                    print(f"\n🔍 Manual OCR test on KDA crop:")
                    try:
                        import easyocr
                        ocr_reader = easyocr.Reader(['en'])
                        ocr_results = ocr_reader.readtext(kda_crop, detail=1)
                        print(f"Raw OCR results: {ocr_results}")
                        
                        # Also test with different preprocessing
                        gray_crop = cv2.cvtColor(kda_crop, cv2.COLOR_BGR2GRAY)
                        # Threshold
                        _, thresh_crop = cv2.threshold(gray_crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                        cv2.imwrite(str(debug_dir / "kda_crop_thresh.png"), thresh_crop)
                        
                        thresh_rgb = cv2.cvtColor(thresh_crop, cv2.COLOR_GRAY2RGB)
                        thresh_results = ocr_reader.readtext(thresh_rgb, detail=1)
                        print(f"Thresholded OCR results: {thresh_results}")
                        
                    except Exception as e:
                        print(f"OCR test failed: {e}")
                
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_dynamic_kda()