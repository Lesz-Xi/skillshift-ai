#!/usr/bin/env python3
"""
Debug Medal Detection v3 - Diagnostic Test
Helps identify why the v3 detector is not finding any trophies.
"""

import os
import sys
import cv2
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.trophy_medal_detector_v3 import advanced_trophy_medal_detector
    print("✅ V3 Detector imported successfully")
except ImportError as e:
    print(f"❌ Failed to import V3 detector: {e}")
    sys.exit(1)


def debug_single_image(image_path: str):
    """Debug a single image to understand detection issues."""
    
    print(f"\n🔍 DEBUGGING: {os.path.basename(image_path)}")
    print("=" * 60)
    
    # Check if image exists and can be loaded
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return
    
    height, width = image.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")
    
    # Test basic color space conversions
    try:
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        print("✅ Color space conversions successful")
    except Exception as e:
        print(f"❌ Color space conversion failed: {e}")
        return
    
    # Test detection at multiple positions
    test_positions = [200, 300, 400, 500, 600, 700]
    print(f"\n🎯 Testing detection at {len(test_positions)} Y positions:")
    
    for y_pos in test_positions:
        print(f"\n   Testing Y={y_pos}:")
        
        try:
            result = advanced_trophy_medal_detector.detect_trophy_in_player_row(
                image_path=image_path,
                player_row_y=float(y_pos),
                player_name_x=None,
                debug_mode=True,
                quality_hint="average"
            )
            
            print(f"      Trophy: {result.trophy_type.value}")
            print(f"      Confidence: {result.confidence:.3f}")
            print(f"      Method: {result.detection_method.value}")
            print(f"      Processing Time: {result.processing_time:.2f}s")
            
            # Show debug info
            if result.debug_info:
                stages = result.debug_info.get("processing_stages", [])
                print(f"      Processing Stages: {stages}")
                
                search_regions = result.debug_info.get("search_regions", [])
                print(f"      Search Regions: {len(search_regions)}")
                
                color_results = result.debug_info.get("color_analysis_results", [])
                print(f"      Color Analysis Results: {len(color_results)}")
                
                shape_results = result.debug_info.get("shape_analysis_results", [])
                print(f"      Shape Analysis Results: {len(shape_results)}")
                
                ensemble_votes = result.debug_info.get("ensemble_votes", {})
                if ensemble_votes:
                    print(f"      Ensemble Votes: {ensemble_votes}")
                
                if result.debug_info.get("error"):
                    print(f"      ❌ Error: {result.debug_info['error']}")
            
            if result.confidence > 0.1:
                print(f"      ✅ Some detection confidence found")
                break
                
        except Exception as e:
            print(f"      ❌ Exception: {e}")
    
    print(f"\n📊 Overall Analysis:")
    print(f"   Image loadable: ✅")
    print(f"   Color spaces: ✅")
    print(f"   Detection attempts: {len(test_positions)}")


def debug_color_spaces():
    """Debug color space analysis with sample colors."""
    
    print("\n🎨 COLOR SPACE DEBUGGING")
    print("=" * 40)
    
    # Create sample medal colors for testing
    sample_colors_bgr = {
        'gold': (0, 215, 255),      # BGR gold
        'silver': (192, 192, 192),  # BGR silver
        'bronze': (205, 127, 50),   # BGR bronze
    }
    
    detector = advanced_trophy_medal_detector
    
    for color_name, bgr_color in sample_colors_bgr.items():
        print(f"\n🎨 Testing {color_name.upper()} color:")
        
        # Create a small test image with this color
        test_img = np.full((100, 100, 3), bgr_color, dtype=np.uint8)
        
        # Convert to different color spaces
        hsv_img = cv2.cvtColor(test_img, cv2.COLOR_BGR2HSV)
        lab_img = cv2.cvtColor(test_img, cv2.COLOR_BGR2LAB)
        
        # Get color values
        hsv_val = hsv_img[50, 50]  # Center pixel
        lab_val = lab_img[50, 50]  # Center pixel
        
        print(f"   BGR: {bgr_color}")
        print(f"   HSV: {hsv_val}")
        print(f"   LAB: {lab_val}")
        
        # Test against detection ranges
        print(f"   Testing against {color_name} ranges:")
        
        # Test LAB ranges
        lab_matches = 0
        for i, color_range in enumerate(detector.lab_medal_colors[color_name]):
            lower, upper = color_range['lower'], color_range['upper']
            in_range = np.all(lab_val >= lower) and np.all(lab_val <= upper)
            print(f"      LAB range {i}: {'✅ MATCH' if in_range else '❌ NO MATCH'} "
                  f"({lower} <= {lab_val} <= {upper})")
            if in_range:
                lab_matches += 1
        
        # Test HSV ranges
        hsv_matches = 0
        for i, color_range in enumerate(detector.hsv_medal_colors[color_name]):
            lower, upper = color_range['lower'], color_range['upper']
            in_range = np.all(hsv_val >= lower) and np.all(hsv_val <= upper)
            print(f"      HSV range {i}: {'✅ MATCH' if in_range else '❌ NO MATCH'} "
                  f"({lower} <= {hsv_val} <= {upper})")
            if in_range:
                hsv_matches += 1
        
        print(f"   Summary: LAB matches: {lab_matches}, HSV matches: {hsv_matches}")


def main():
    """Main diagnostic function."""
    
    print("🔍 MEDAL DETECTION V3 - DIAGNOSTIC MODE")
    print("=" * 50)
    print("🎯 Debugging why v3 detector finds no trophies")
    print()
    
    # First, test color space analysis
    debug_color_spaces()
    
    # Then test with actual images
    test_images = [
        "yolo_dataset/images/test/ranked_poor_kda_059.jpg",
        "yolo_dataset/images/test/edb4fa11-6_ranked_matches_good_performance_match06_win_kda.PNG"
    ]
    
    for image_path in test_images:
        if os.path.exists(image_path):
            debug_single_image(image_path)
            break  # Just test one image for now
        else:
            print(f"⚠️ Test image not found: {image_path}")
    
    print(f"\n💡 DIAGNOSTIC COMPLETE")
    print(f"📋 Check temp/debug_v3/ for visualization files")
    print(f"🔧 Review color range matches and detection logic")


if __name__ == "__main__":
    main()
