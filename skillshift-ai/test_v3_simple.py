#!/usr/bin/env python3
"""
Simple V3 Detector Test - Isolate the Issue
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.trophy_medal_detector_v3 import advanced_trophy_medal_detector

def test_simple():
    """Simple test to understand the issue."""
    
    image_path = "yolo_dataset/images/test/ranked_poor_kda_059.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        return
    
    print(f"🔍 Testing: {image_path}")
    
    # Test with lower threshold
    detector = advanced_trophy_medal_detector
    
    # Manually lower the threshold for testing
    detector.quality_thresholds['average']['min_confidence'] = 0.3
    
    result = detector.detect_trophy_in_player_row(
        image_path=image_path,
        player_row_y=500.0,
        debug_mode=True,
        quality_hint="average"
    )
    
    print(f"Result: {result.trophy_type.value}")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Method: {result.detection_method.value}")
    
    # Show debug details
    print(f"\nDebug Info:")
    print(f"  Ensemble votes: {result.debug_info.get('ensemble_votes', {})}")
    print(f"  Method confidences: {result.method_confidences}")
    
    # Show the best individual scores
    votes = result.debug_info.get('ensemble_votes', {})
    if votes:
        best_vote = max(votes.items(), key=lambda x: x[1])
        print(f"  Best individual vote: {best_vote[0]} = {best_vote[1]:.3f}")

if __name__ == "__main__":
    test_simple()
