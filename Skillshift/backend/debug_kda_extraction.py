#!/usr/bin/env python3
"""
Debug KDA extraction step by step
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def debug_kda_extraction():
    """Debug the KDA extraction step by step"""
    
    # Load test image
    img_path = "backend/tests/fixtures/IMG_1767.png"
    print(f"🔍 Debugging KDA extraction with: {img_path}")
    
    image = cv2.imread(img_path)
    if image is None:
        print(f"❌ Failed to load image: {img_path}")
        return
    
    print(f"✅ Image loaded: {image.shape}")
    
    # We know "Diary of dolls" is at row 4
    row_index = 4
    print(f"\n🎯 Testing KDA extraction for row {row_index}")
    
    try:
        # Step 1: Test geometry calculation
        from ocr.detectors import detect_blue_panel
        from ocr.utils_geometry import row_bbox, BBox
        import yaml
        
        with open("backend/ocr/config_ocr.yaml", "r") as f:
            CFG = yaml.safe_load(f)
        
        panel = detect_blue_panel(image)
        print(f"Blue panel: {panel}")
        
        # Calculate row bbox
        rbox = row_bbox(
            panel, 
            row_index, 
            CFG["table"]["rows"],
            CFG["table"]["row_top_offset_pct"],
            CFG["table"]["row_bottom_offset_pct"]
        )
        print(f"Row bbox: {rbox}")
        
        # Calculate post-name band (where KDA should be)
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
        print(f"KDA band bbox: {band_bbox}")
        
        # Extract the band image
        band_img = image[band_bbox.y:band_bbox.y+band_bbox.h, band_bbox.x:band_bbox.x+band_bbox.w]
        print(f"Band image shape: {band_img.shape}")
        
        # Save debug images
        debug_dir = Path("debug_output")
        debug_dir.mkdir(exist_ok=True)
        
        # Save row image with boxes
        row_img = image[rbox.y:rbox.y+rbox.h, rbox.x:rbox.x+rbox.w]
        row_debug = row_img.copy()
        
        # Draw band bbox (relative to row)
        rel_band_x = band_bbox.x - rbox.x
        rel_band_y = band_bbox.y - rbox.y
        cv2.rectangle(row_debug, (rel_band_x, rel_band_y), 
                     (rel_band_x + band_bbox.w, rel_band_y + band_bbox.h), (0, 0, 255), 2)
        cv2.putText(row_debug, "KDA BAND", (rel_band_x, rel_band_y-5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        cv2.imwrite(str(debug_dir / "row_4_with_kda_band.png"), row_debug)
        cv2.imwrite(str(debug_dir / "kda_band.png"), band_img)
        
        print(f"✅ Debug images saved")
        
        # Step 2: Test slash detection
        print(f"\n🔍 Testing slash detection")
        
        if band_img.size > 0:
            gray = cv2.cvtColor(band_img, cv2.COLOR_BGR2GRAY)
            print(f"Gray band shape: {gray.shape}")
            
            # Test template matching
            slash_template_path = Path("backend/ocr/assets/templates/slash16.png")
            if slash_template_path.exists():
                slash_tpl = cv2.imread(str(slash_template_path), cv2.IMREAD_GRAYSCALE)
                print(f"Slash template shape: {slash_tpl.shape}")
                
                # Template matching
                res = cv2.matchTemplate(gray, slash_tpl, cv2.TM_CCOEFF_NORMED)
                threshold = CFG["matching"]["slash_match_threshold"]
                
                ys, xs = np.where(res >= threshold)
                matches = [(int(y), int(x), float(res[y, x])) for y, x in zip(ys, xs)]
                
                print(f"Found {len(matches)} slash matches above threshold {threshold}")
                for i, (y, x, conf) in enumerate(matches):
                    print(f"  Match {i}: ({x}, {y}) confidence: {conf:.3f}")
                
                # Save result visualization
                result_vis = gray.copy()
                result_vis = cv2.cvtColor(result_vis, cv2.COLOR_GRAY2BGR)
                
                for y, x, conf in matches:
                    cv2.rectangle(result_vis, (x, y), (x+slash_tpl.shape[1], y+slash_tpl.shape[0]), (0, 255, 0), 1)
                    cv2.putText(result_vis, f"{conf:.2f}", (x, y-2), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                
                cv2.imwrite(str(debug_dir / "slash_detection.png"), result_vis)
                print(f"✅ Slash detection visualization saved")
                
            else:
                print(f"❌ Slash template not found at {slash_template_path}")
        
        # Step 3: Test full KDA extraction
        print(f"\n🧪 Testing full KDA extraction")
        from ocr.kda_cell_reader_v2 import read_kda_for_row
        
        kda_result = read_kda_for_row(image, row_index)
        print(f"KDA extraction result: {kda_result}")
        
        print(f"\n💾 All debug images saved to {debug_dir}/")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_kda_extraction()