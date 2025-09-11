#!/usr/bin/env python3
"""
Visual debugging for KDA crop positioning
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from ocr.detectors import detect_table_regions

def debug_crop_visual():
    """Visual debugging to see crop positioning"""
    
    # Load test image
    img_path = "backend/tests/fixtures/IMG_1767.png"
    print(f"Loading image: {img_path}")
    
    image = cv2.imread(img_path)
    if image is None:
        print(f"❌ Failed to load image: {img_path}")
        return
    
    print(f"✅ Image loaded: {image.shape}")
    
    target_ign = "Diary of dolls"
    print(f"\n🔍 Analyzing IGN detection for: '{target_ign}'")
    
    # Get table regions with IGN detection
    regions = detect_table_regions(image, target_ign=target_ign)
    print(f"Regions detected: {len(regions.get('rows', []))} rows")
    
    if 'ign_detection' in regions:
        ign_info = regions['ign_detection']
        print(f"IGN Detection: {ign_info}")
        
        if ign_info.get('found'):
            row_index = ign_info['row_index']
            ign_bbox = ign_info['ign_bbox']
            print(f"✅ IGN found in row {row_index} at bbox {ign_bbox}")
            
            # Get the row image
            if row_index < len(regions['rows']):
                row_info = regions['rows'][row_index]
                row_y1, row_y2 = row_info['y1'], row_info['y2']
                row_img = image[row_y1:row_y2]
                
                print(f"Row image shape: {row_img.shape}")
                
                # Calculate dynamic KDA bbox
                nx1, ny1, nx2, ny2 = ign_bbox
                h, w = row_img.shape[:2]
                
                # Tunables (current defaults)
                PAD_Y = 6
                BOX_W = int(0.18 * w)  # width ~18% row width
                BOX_H = max(ny2 - ny1 + 2*PAD_Y, int(0.28 * h))
                
                # KDA box to the RIGHT of the name
                kda_x1 = min(w-1, nx2 + 4)  # start a few px after name
                kda_x2 = min(w, kda_x1 + BOX_W)
                kda_y1 = max(0, ny1 - PAD_Y)
                kda_y2 = min(h, kda_y1 + BOX_H)
                
                kda_bbox = (kda_x1, kda_y1, kda_x2, kda_y2)
                
                print(f"Dynamic KDA bbox: {kda_bbox}")
                print(f"IGN bbox: {ign_bbox}")
                print(f"Row dimensions: {w}x{h}")
                
                # Create debug visualization
                debug_dir = Path("debug_output")
                debug_dir.mkdir(exist_ok=True)
                
                # Create visualization with boxes
                row_debug = row_img.copy()
                
                # Draw IGN bbox in green
                cv2.rectangle(row_debug, (nx1, ny1), (nx2, ny2), (0, 255, 0), 2)
                cv2.putText(row_debug, "IGN", (nx1, ny1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Draw KDA bbox in red
                cv2.rectangle(row_debug, (kda_x1, kda_y1), (kda_x2, kda_y2), (0, 0, 255), 2)
                cv2.putText(row_debug, "KDA", (kda_x1, kda_y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                
                # Save row with boxes
                cv2.imwrite(str(debug_dir / "row_with_boxes.png"), row_debug)
                
                # Extract and save the KDA crop
                kda_crop = row_img[kda_y1:kda_y2, kda_x1:kda_x2]
                cv2.imwrite(str(debug_dir / "kda_crop.png"), kda_crop)
                
                # Also save the IGN crop for comparison
                ign_crop = row_img[ny1:ny2, nx1:nx2]
                cv2.imwrite(str(debug_dir / "ign_crop.png"), ign_crop)
                
                print(f"✅ Debug images saved to {debug_dir}/")
                print(f"  - row_with_boxes.png: Row with bounding boxes")
                print(f"  - kda_crop.png: KDA crop ({kda_crop.shape})")
                print(f"  - ign_crop.png: IGN crop ({ign_crop.shape})")
                
                # Also test OCR on the KDA crop to see what text is detected
                try:
                    import easyocr
                    ocr_reader = easyocr.Reader(['en'])
                    
                    print(f"\n🔍 OCR analysis of KDA crop:")
                    ocr_results = ocr_reader.readtext(kda_crop, detail=1)
                    for i, (bbox, text, conf) in enumerate(ocr_results):
                        print(f"  {i+1}. Text: '{text}' | Confidence: {conf:.3f} | Bbox: {bbox}")
                        
                except Exception as e:
                    print(f"OCR test failed: {e}")
        else:
            print(f"❌ IGN '{target_ign}' not found")
    else:
        print(f"❌ No IGN detection information")

if __name__ == "__main__":
    debug_crop_visual()