#!/usr/bin/env python3
"""
Find exact positions of target digits 9, 2, 12
"""

import cv2
import numpy as np
from pathlib import Path
import sys
import easyocr

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def find_target_digits():
    """Find exact positions of 9, 2, 12 in the KDA band"""
    
    # Load test image
    img_path = "backend/tests/fixtures/IMG_1767.png"
    print(f"🎯 Finding target digits 9, 2, 12 in: {img_path}")
    
    image = cv2.imread(img_path)
    if image is None:
        print(f"❌ Failed to load image: {img_path}")
        return
    
    try:
        # Calculate the KDA band (same as before)
        from ocr.detectors import detect_blue_panel
        from ocr.utils_geometry import row_bbox, BBox
        import yaml
        
        with open("backend/ocr/config_ocr.yaml", "r") as f:
            CFG = yaml.safe_load(f)
        
        panel = detect_blue_panel(image)
        row_index = 4
        rbox = row_bbox(
            panel, 
            row_index, 
            CFG["table"]["rows"],
            CFG["table"]["row_top_offset_pct"],
            CFG["table"]["row_bottom_offset_pct"]
        )
        
        # Calculate post-name band
        name_start_pct = CFG["table"]["name_col_start_pct"]
        name_w_pct = CFG["table"]["name_col_width_pct"]
        kda_start_pct = name_start_pct + name_w_pct
        
        band_top_pct = CFG["kda_region"]["band_top_pct_of_row"]
        band_h_pct = CFG["kda_region"]["band_height_pct_of_row"]
        
        band_y = int(rbox.y + band_top_pct * rbox.h)
        band_h = int(band_h_pct * rbox.h)
        band_x = rbox.x + int(kda_start_pct * rbox.w)
        band_w = rbox.w - int(kda_start_pct * rbox.w)
        
        band_bbox = BBox(band_x, band_y, band_w, band_h)
        
        # Extract the band image
        band_img = image[band_bbox.y:band_bbox.y+band_bbox.h, band_bbox.x:band_bbox.x+band_bbox.w]
        gray = cv2.cvtColor(band_img, cv2.COLOR_BGR2GRAY)
        
        print(f"KDA band shape: {band_img.shape}")
        
        # Use OCR to find all text with positions
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(band_img, detail=1)
        
        print(f"\n🔍 All OCR results in KDA band:")
        target_positions = {}
        
        for i, (bbox_coords, text, confidence) in enumerate(results):
            # Calculate bounding box
            x_coords = [point[0] for point in bbox_coords]
            y_coords = [point[1] for point in bbox_coords]
            x1, x2 = int(min(x_coords)), int(max(x_coords))
            y1, y2 = int(min(y_coords)), int(max(y_coords))
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            print(f"  {i}: '{text}' at ({center_x}, {center_y}) bbox=({x1},{y1},{x2},{y2}) conf={confidence:.3f}")
            
            # Look for our target values
            text_clean = text.strip()
            if text_clean == "9":
                target_positions["K"] = (center_x, center_y)
                print(f"    🎯 Found K value '9' at ({center_x}, {center_y})")
            elif text_clean == "2":
                target_positions["D"] = (center_x, center_y)
                print(f"    🎯 Found D value '2' at ({center_x}, {center_y})")
            elif text_clean == "12":
                target_positions["A"] = (center_x, center_y)
                print(f"    🎯 Found A value '12' at ({center_x}, {center_y})")
        
        print(f"\n📍 Target positions found:")
        for kda, pos in target_positions.items():
            print(f"  {kda}: {pos}")
        
        # Create visualization
        debug_dir = Path("debug_output")
        debug_dir.mkdir(exist_ok=True)
        
        vis_img = band_img.copy()
        for kda, (x, y) in target_positions.items():
            cv2.circle(vis_img, (x, y), 5, (0, 255, 0), 2)
            cv2.putText(vis_img, kda, (x-10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        cv2.imwrite(str(debug_dir / "target_positions.png"), vis_img)
        print(f"\n💾 Target positions visualization saved to {debug_dir}/target_positions.png")
        
        # Generate positioning code
        if len(target_positions) >= 2:
            print(f"\n💡 Suggested positioning code:")
            for kda, (x, y) in target_positions.items():
                print(f"    {kda.lower()}_center_x = {x}  # Target: {kda}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_target_digits()