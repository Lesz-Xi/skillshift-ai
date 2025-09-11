#!/usr/bin/env python3
"""
Debug Medal Detection Only - Focus on Medal Classification
"""

import os
import sys
import cv2
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.trophy_medal_detector_v3 import advanced_trophy_medal_detector

def test_medal_detection_only():
    """Test only medal detection, bypassing MVP detection."""
    
    image_path = "yolo_dataset/images/test/ranked_poor_kda_059.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        return
    
    print(f"🔍 MEDAL-ONLY DETECTION TEST")
    print(f"Image: {image_path}")
    print("=" * 50)
    
    detector = advanced_trophy_medal_detector
    
    # Load image
    image = cv2.imread(image_path)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    
    # Test medal detection directly
    debug_info = {
        "color_analysis_results": [], 
        "shape_analysis_results": [],
        "ensemble_votes": {},
        "method_confidences": {},
        "processing_stages": []
    }
    visualization_data = {"color_masks": {}}
    
    print("🥇 Testing Medal Detection Directly...")
    
    medal_result = detector._detect_medal_v3(
        image, hsv_image, lab_image, 
        player_row_y=500.0,
        player_name_x=None,
        debug_info=debug_info,
        visualization_data=visualization_data,
        quality_hint="poor"  # Use poor quality hint to favor medal detection
    )
    
    print(f"\nResult:")
    print(f"  Trophy Type: {medal_result.trophy_type.value}")
    print(f"  Confidence: {medal_result.confidence:.3f}")
    print(f"  Method: {medal_result.detection_method.value}")
    
    print(f"\nColor Analysis:")
    print(f"  Color Space: {medal_result.color_analysis.color_space}")
    print(f"  Detected Color: {medal_result.color_analysis.detected_color}")
    print(f"  Color Confidence: {medal_result.color_analysis.confidence:.3f}")
    print(f"  Pixel Count: {medal_result.color_analysis.pixel_count}")
    
    print(f"\nShape Analysis:")
    print(f"  Circularity: {medal_result.shape_analysis.circularity:.3f}")
    print(f"  Aspect Ratio: {medal_result.shape_analysis.aspect_ratio:.3f}")
    print(f"  Solidity: {medal_result.shape_analysis.solidity:.3f}")
    print(f"  Shape Confidence: {medal_result.shape_analysis.shape_confidence:.3f}")
    
    print(f"\nEnsemble Votes:")
    for vote_name, vote_value in medal_result.ensemble_votes.items():
        if vote_value > 0.1:  # Only show significant votes
            print(f"  {vote_name}: {vote_value:.3f}")
    
    print(f"\nMethod Confidences:")
    for method, confidence in medal_result.method_confidences.items():
        print(f"  {method}: {confidence:.3f}")
    
    # Show color analysis details
    print(f"\nDetailed Color Analysis:")
    for i, result in enumerate(debug_info["color_analysis_results"]):
        if result["mask_pixels"] > 0:
            print(f"  {i}: {result['method']} {result['medal_color']} range {result['range_index']} "
                  f"-> {result['mask_pixels']} pixels, {result['contours_found']} contours")

if __name__ == "__main__":
    test_medal_detection_only()
