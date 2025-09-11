#!/usr/bin/env python3
"""
Quick Test Runner for Medal Detection v3 - CRITICAL VALIDATION

This script provides a simple way to test the new Advanced Trophy Medal Detector v3
and validate the CRITICAL BLOCKER fix for medal recognition (37.5% → 90%+ accuracy).

Usage:
    python run_medal_detection_v3_test.py --quick
    python run_medal_detection_v3_test.py --comprehensive
"""

import os
import sys
import time
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.trophy_medal_detector_v3 import advanced_trophy_medal_detector
    from test_medal_detection_v3 import MedalDetectionV3Tester
    V3_AVAILABLE = True
except ImportError as e:
    print(f"❌ V3 Detector not available: {e}")
    V3_AVAILABLE = False


def quick_test():
    """Run a quick test of the v3 detector."""
    
    print("⚡ QUICK TEST - Medal Detection v3")
    print("=" * 50)
    print("🎯 Testing CRITICAL BLOCKER fix: 37.5% → 90%+ accuracy")
    print()
    
    if not V3_AVAILABLE:
        print("❌ V3 Detector not available - check imports")
        return False
    
    # Test with available images from yolo_dataset
    test_image_paths = [
        "yolo_dataset/images/test/ranked_poor_kda_059.jpg",
        "yolo_dataset/images/test/ea01384d-1_ranked_matches_average_performance_match01_win_kda.PNG",
        "yolo_dataset/images/test/edb4fa11-6_ranked_matches_good_performance_match06_win_kda.PNG",
        "yolo_dataset/images/test/ef18ecbc-2_ranked_matches_good_performance_match02_win_kda.PNG"
    ]
    
    detector = advanced_trophy_medal_detector
    successful_tests = 0
    total_tests = 0
    
    for image_path in test_image_paths:
        if not os.path.exists(image_path):
            print(f"⚠️ Test image not found: {image_path}")
            continue
        
        total_tests += 1
        print(f"\n📸 Testing: {os.path.basename(image_path)}")
        
        # Determine expected result based on filename patterns
        if "poor" in image_path.lower():
            expected = "bronze"
        elif "average" in image_path.lower():
            expected = "silver"
        elif "good" in image_path.lower():
            expected = "gold"
        elif "excellent" in image_path.lower() or "mvp" in image_path.lower():
            expected = "mvp"
        else:
            # For other files, try to infer from performance level in path
            if "good_performance" in image_path.lower():
                expected = "gold"
            elif "average_performance" in image_path.lower():
                expected = "silver"
            elif "poor_performance" in image_path.lower():
                expected = "bronze"
            elif "excellent_performance" in image_path.lower():
                expected = "mvp"
            else:
                expected = "unknown"
        
        print(f"   Expected: {expected}")
        
        try:
            # Test detection
            start_time = time.time()
            result = detector.detect_trophy_in_player_row(
                image_path=image_path,
                player_row_y=500.0,  # Middle position
                debug_mode=True,
                quality_hint="average"
            )
            processing_time = time.time() - start_time
            
            detected = result.trophy_type.value
            confidence = result.confidence
            method = result.detection_method.value
            
            print(f"   Detected: {detected}")
            print(f"   Confidence: {confidence:.3f}")
            print(f"   Method: {method}")
            print(f"   Time: {processing_time:.2f}s")
            
            # Check if detection is reasonable
            is_success = confidence > 0.5 and detected != "none"
            
            # Check if detection matches expectation (flexible matching)
            trophy_mappings = {
                "mvp": ["mvp_crown"],
                "gold": ["gold_medal"],
                "silver": ["silver_medal"],
                "bronze": ["bronze_medal"]
            }
            
            expected_types = trophy_mappings.get(expected, [expected])
            is_correct = detected in expected_types
            
            if is_success and is_correct:
                successful_tests += 1
                print(f"   ✅ SUCCESS: Correct detection")
            elif is_success:
                print(f"   🟡 DETECTED: But unexpected type")
            else:
                print(f"   ❌ FAILED: No reliable detection")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    # Summary
    accuracy = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"\n📊 QUICK TEST RESULTS:")
    print(f"   Tests Run: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 75:
        print(f"   ✅ PROMISING: Significant improvement over baseline (37.5%)")
    else:
        print(f"   🔧 NEEDS WORK: Additional optimization required")
    
    # Get detector performance stats
    stats = detector.get_performance_stats()
    print(f"\n📈 DETECTOR PERFORMANCE:")
    print(f"   Total Detections: {stats['total_detections']}")
    print(f"   Success Rate: {stats['success_rate']}")
    print(f"   Avg Processing Time: {stats['average_processing_time']}")
    
    return accuracy >= 75


def comprehensive_test():
    """Run comprehensive validation test."""
    
    print("🚀 COMPREHENSIVE TEST - Medal Detection v3")
    print("=" * 60)
    print("🎯 Full validation of CRITICAL BLOCKER fix")
    print()
    
    if not V3_AVAILABLE:
        print("❌ V3 Detector not available - check imports")
        return False
    
    try:
        tester = MedalDetectionV3Tester()
        report = tester.run_comprehensive_validation()
        
        accuracy = report['test_summary']['overall_accuracy']
        success_level = report['test_summary']['success_level']
        
        print(f"\n🎉 COMPREHENSIVE TEST COMPLETED")
        print(f"📊 Final Accuracy: {accuracy:.1f}%")
        print(f"🏆 Success Level: {success_level.upper()}")
        
        if accuracy >= 90:
            print("✅ CRITICAL BLOCKER RESOLVED!")
            print("🚀 Ready for production deployment")
            return True
        elif accuracy >= 75:
            print("🟡 Significant improvement achieved")
            print("🔧 Minor optimization recommended")
            return True
        else:
            print("🔴 Additional development needed")
            return False
            
    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        return False


def main():
    """Main test runner."""
    
    parser = argparse.ArgumentParser(
        description='Medal Detection v3 Test Runner'
    )
    parser.add_argument(
        '--quick', action='store_true',
        help='Run quick validation test'
    )
    parser.add_argument(
        '--comprehensive', action='store_true',
        help='Run comprehensive validation test'
    )
    parser.add_argument(
        '--stats', action='store_true',
        help='Show detector performance statistics'
    )
    
    args = parser.parse_args()
    
    print("🏆 MEDAL DETECTION V3 - TEST RUNNER")
    print("=" * 50)
    print("🔧 Features: LAB Color Space, Shape Analysis, Ensemble Voting")
    print("🎯 Target: Fix CRITICAL BLOCKER (37.5% → 90%+ accuracy)")
    print()
    
    if args.stats and V3_AVAILABLE:
        print("📊 DETECTOR PERFORMANCE STATISTICS:")
        stats = advanced_trophy_medal_detector.get_performance_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        return
    
    if args.quick:
        success = quick_test()
        print(f"\n🎯 Quick test {'PASSED' if success else 'NEEDS WORK'}")
    elif args.comprehensive:
        success = comprehensive_test()
        print(f"\n🎯 Comprehensive test {'PASSED' if success else 'NEEDS WORK'}")
    else:
        # Run quick test by default
        print("🔧 Running quick test (use --comprehensive for full validation)")
        success = quick_test()
        
        if success:
            print("\n💡 Recommendation: Run comprehensive test with:")
            print("   python run_medal_detection_v3_test.py --comprehensive")
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Review debug images in temp/debug_v3/")
    print(f"   2. Check analysis reports for parameter tuning")
    print(f"   3. {'Proceed to MVP Pipeline fix' if success else 'Optimize medal detection further'}")


if __name__ == "__main__":
    main()
