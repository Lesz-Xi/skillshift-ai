#!/usr/bin/env python3
"""
Debug individual KDA crop images
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def debug_individual_crops():
    """Debug individual crop images for K, D, A"""
    
    # Load test image
    img_path = "backend/tests/fixtures/IMG_1767.png"
    print(f"🔍 Debugging individual crops with: {img_path}")
    
    image = cv2.imread(img_path)
    if image is None:
        print(f"❌ Failed to load image: {img_path}")
        return
    
    print(f"✅ Image loaded: {image.shape}")
    
    # We know "Diary of dolls" is at row 4
    row_index = 4
    
    try:
        # Calculate the KDA band
        from ocr.detectors import detect_blue_panel
        from ocr.utils_geometry import row_bbox, BBox
        import yaml
        
        with open("backend/ocr/config_ocr.yaml", "r") as f:
            CFG = yaml.safe_load(f)
        
        panel = detect_blue_panel(image)
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
        
        print(f"Band image shape: {band_img.shape}")
        
        # Simulate slash detection results (we know from previous runs)
        # Slashes at (269, 15) and (401, 56)
        s1x, s1y = 269, 15
        s2x, s2y = 401, 56
        
        print(f"Using known slash positions: ({s1x}, {s1y}) and ({s2x}, {s2y})")
        
        # Test different crop positions around these slashes
        debug_dir = Path("debug_output")
        debug_dir.mkdir(exist_ok=True)
        
        crop_w = CFG["kda_region"]["digit_crop_w_px"]
        crop_h = CFG["kda_region"]["digit_crop_h_px"]
        
        def make_crop(center_x, center_y, label):
            H, W = gray.shape
            x1 = max(0, center_x - crop_w // 2)
            x2 = min(W, center_x + crop_w // 2)
            y1 = max(0, center_y - crop_h // 2)
            y2 = min(H, center_y + crop_h // 2)
            crop = gray[y1:y2, x1:x2]
            
            # Save crop image
            cv2.imwrite(str(debug_dir / f"crop_{label}_x{center_x}.png"), crop)
            
            # Test OCR on this crop
            try:
                import easyocr
                reader = easyocr.Reader(['en'], gpu=False)
                results = reader.readtext(crop, detail=0, allowlist="0123456789")
                text = "".join([t for t in results if t.strip()])
                value = int(text) if text.isdigit() and 0 <= int(text) <= 50 else None
                print(f"  Crop {label} at x={center_x}: shape={crop.shape}, OCR='{text}', value={value}")
                return value
            except Exception as e:
                print(f"  Crop {label} at x={center_x}: shape={crop.shape}, OCR failed: {e}")
                return None
        
        print(f"\n🔍 Testing different K positions (looking for '9'):")
        for offset in [10, 20, 30, 40]:
            k_center_x = s1x - offset
            make_crop(k_center_x, s1y, f"K_minus{offset}")
        
        print(f"\n🔍 Testing different D positions (looking for '2'):")
        for offset in [10, 20, 30]:
            d_center_x = s1x + offset
            make_crop(d_center_x, s1y, f"D_plus{offset}")
        
        print(f"\n🔍 Testing different A positions (looking for '12'):")
        for offset in [10, 20, 30, 40]:
            a_center_x = s2x + offset
            make_crop(a_center_x, s2y, f"A_plus{offset}")
        
        # Also test some positions between slashes
        print(f"\n🔍 Testing positions between slashes:")
        mid_x = (s1x + s2x) // 2
        for offset in [-20, -10, 0, 10, 20]:
            test_x = mid_x + offset
            make_crop(test_x, (s1y + s2y) // 2, f"MID_{offset:+d}")
        
        print(f"\n💾 All crop images saved to {debug_dir}/")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_individual_crops()