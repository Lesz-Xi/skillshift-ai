#!/usr/bin/env python3
"""
Create a simple slash template for KDA detection
"""

import cv2
import numpy as np

def create_slash_template():
    """Create a 16x16 white slash on black background"""
    # Create 16x16 black image
    template = np.zeros((16, 16), dtype=np.uint8)
    
    # Draw a diagonal line (slash) from top-right to bottom-left
    # Line thickness of 2 pixels, white color (255)
    cv2.line(template, (12, 2), (4, 14), 255, 2)
    
    # Save the template
    cv2.imwrite("backend/ocr/assets/templates/slash16.png", template)
    print("✅ Created slash template: backend/ocr/assets/templates/slash16.png")
    
    # Also create a version for visual inspection
    visual = cv2.resize(template, (64, 64), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite("backend/ocr/assets/templates/slash16_visual.png", visual)
    print("✅ Created visual version: backend/ocr/assets/templates/slash16_visual.png")

if __name__ == "__main__":
    create_slash_template()