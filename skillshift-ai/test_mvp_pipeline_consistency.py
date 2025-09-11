#!/usr/bin/env python3
"""
MVP Pipeline Consistency Test - Validate 50% → 95%+ Reliability Fix

This test compares:
1. Direct MVP detection (should be 100% reliable)
2. Integrated pipeline MVP detection (was 50% reliable, now should be 95%+)

Tests the fixes:
- Updated to use trophy_medal_detector_v3
- Enhanced player row positioning with fallbacks
- Quality-aware detection strategy
- Multi-resolution support
"""

import os
import sys
import time
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.enhanced_data_collector import EnhancedDataCollector
from core.trophy_medal_detector_v3 import advanced_trophy_medal_detector


class MVPPipelineConsistencyTester:
    """Test MVP detection consistency between direct and integrated approaches."""
    
    def __init__(self):
        self.enhanced_collector = EnhancedDataCollector()
        self.direct_detector = advanced_trophy_medal_detector
        self.test_results = []
        
    def test_mvp_pipeline_consistency(self) -> Dict[str, Any]:
        """Main test method comparing direct vs integrated MVP detection."""
        
        print("🚀 MVP PIPELINE CONSISTENCY TEST")
        print("=" * 60)
        print("🎯 Target: 50% → 95%+ integrated pipeline reliability")
        print("🔧 Testing: v3 detector integration + positioning fixes")
        print()
        
        # Test images that should contain MVP or high-performance indicators
        test_images = [
            {
                "path": "yolo_dataset/images/test/edb4fa11-6_ranked_matches_good_performance_match06_win_kda.PNG",
                "expected_performance": "good_to_excellent",
                "description": "Good performance match - should detect MVP or gold"
            },
            {
                "path": "yolo_dataset/images/test/ef18ecbc-2_ranked_matches_good_performance_match02_win_kda.PNG", 
                "expected_performance": "good_to_excellent",
                "description": "Good performance match - should detect MVP or gold"
            },
            {
                "path": "yolo_dataset/images/test/ea01384d-1_ranked_matches_average_performance_match01_win_kda.PNG",
                "expected_performance": "average",
                "description": "Average performance match - should detect silver"
            },
            {
                "path": "yolo_dataset/images/test/ranked_poor_kda_059.jpg",
                "expected_performance": "poor",
                "description": "Poor performance match - should detect bronze/silver"
            }
        ]
        
        total_tests = 0
        direct_successes = 0
        integrated_successes = 0
        consistency_matches = 0
        
        for test_case in test_images:
            image_path = test_case["path"]
            
            if not os.path.exists(image_path):
                print(f"⚠️ Skipping {image_path} - not found")
                continue
                
            total_tests += 1
            print(f"\n📸 TESTING: {os.path.basename(image_path)}")
            print(f"Expected: {test_case['expected_performance']}")
            print(f"Description: {test_case['description']}")
            print("-" * 50)
            
            # Test 1: Direct Detection
            direct_result = self._test_direct_detection(image_path)
            
            # Test 2: Integrated Pipeline Detection  
            integrated_result = self._test_integrated_detection(image_path)
            
            # Compare results
            consistency_analysis = self._analyze_consistency(
                direct_result, integrated_result, test_case)
            
            # Count successes
            if direct_result["detection_success"]:
                direct_successes += 1
                
            if integrated_result["detection_success"]:
                integrated_successes += 1
                
            if consistency_analysis["consistent"]:
                consistency_matches += 1
            
            # Display results
            print(f"\n📊 COMPARISON RESULTS:")
            print(f"   Direct Detection: {'✅' if direct_result['detection_success'] else '❌'} "
                  f"{direct_result['trophy_type']} (conf: {direct_result['confidence']:.3f})")
            print(f"   Integrated Pipeline: {'✅' if integrated_result['detection_success'] else '❌'} "
                  f"{integrated_result['trophy_type']} (conf: {integrated_result['confidence']:.3f})")
            print(f"   Consistency: {'✅ CONSISTENT' if consistency_analysis['consistent'] else '❌ INCONSISTENT'}")
            print(f"   Performance Gap: {consistency_analysis['performance_gap']:.1%}")
            
            if consistency_analysis["positioning_diff"]:
                print(f"   Positioning Difference: {consistency_analysis['positioning_diff']:.1f} pixels")
            
            # Store detailed results
            self.test_results.append({
                "image": os.path.basename(image_path),
                "expected": test_case["expected_performance"],
                "direct": direct_result,
                "integrated": integrated_result,
                "consistency": consistency_analysis
            })
        
        # Calculate final metrics
        direct_reliability = (direct_successes / total_tests * 100) if total_tests > 0 else 0
        integrated_reliability = (integrated_successes / total_tests * 100) if total_tests > 0 else 0
        consistency_rate = (consistency_matches / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 PIPELINE CONSISTENCY RESULTS")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Direct Detection Reliability: {direct_reliability:.1f}% ({direct_successes}/{total_tests})")
        print(f"Integrated Pipeline Reliability: {integrated_reliability:.1f}% ({integrated_successes}/{total_tests})")
        print(f"Consistency Rate: {consistency_rate:.1f}% ({consistency_matches}/{total_tests})")
        
        # Success evaluation
        print(f"\n🏆 SUCCESS EVALUATION:")
        if integrated_reliability >= 95:
            print("✅ EXCELLENT: Integrated pipeline meets 95%+ reliability target!")
            print("✅ CRITICAL ISSUE RESOLVED")
            success_level = "excellent"
        elif integrated_reliability >= 80:
            print("🟡 GOOD: Significant improvement achieved")
            print("🔧 Minor optimization recommended")
            success_level = "good"
        elif integrated_reliability >= 60:
            print("🟠 PROGRESS: Improvement over baseline (50%)")
            print("🔧 Additional optimization needed")
            success_level = "progress"
        else:
            print("🔴 NEEDS WORK: Further development required")
            success_level = "needs_work"
        
        # Improvement analysis
        if integrated_reliability > 50:
            improvement = integrated_reliability - 50
            print(f"📈 Improvement: +{improvement:.1f}% over baseline")
        
        return {
            "total_tests": total_tests,
            "direct_reliability": direct_reliability,
            "integrated_reliability": integrated_reliability,
            "consistency_rate": consistency_rate,
            "success_level": success_level,
            "detailed_results": self.test_results
        }
    
    def _test_direct_detection(self, image_path: str) -> Dict[str, Any]:
        """Test direct trophy detection."""
        
        print(f"\n🎯 DIRECT DETECTION:")
        
        start_time = time.time()
        best_result = None
        best_confidence = 0.0
        
        # Test at multiple Y positions (simulating different player rows)
        test_positions = [300, 400, 500, 600, 700]
        
        for y_pos in test_positions:
            try:
                result = self.direct_detector.detect_trophy_in_player_row(
                    image_path=image_path,
                    player_row_y=float(y_pos),
                    player_name_x=None,
                    debug_mode=False,
                    quality_hint="average"
                )
                
                if result.confidence > best_confidence:
                    best_confidence = result.confidence
                    best_result = result
                    
            except Exception as e:
                print(f"   Error at Y={y_pos}: {e}")
        
        processing_time = time.time() - start_time
        
        if best_result and best_result.confidence > 0.3:
            print(f"   Result: {best_result.trophy_type.value}")
            print(f"   Confidence: {best_result.confidence:.3f}")
            print(f"   Method: {best_result.detection_method.value}")
            print(f"   Processing Time: {processing_time:.2f}s")
            
            return {
                "detection_success": True,
                "trophy_type": best_result.trophy_type.value,
                "confidence": best_result.confidence,
                "method": best_result.detection_method.value,
                "processing_time": processing_time,
                "bounding_box": best_result.bounding_box
            }
        else:
            print(f"   No reliable detection found")
            print(f"   Processing Time: {processing_time:.2f}s")
            
            return {
                "detection_success": False,
                "trophy_type": "none",
                "confidence": 0.0,
                "method": "none",
                "processing_time": processing_time,
                "bounding_box": None
            }
    
    def _test_integrated_detection(self, image_path: str) -> Dict[str, Any]:
        """Test integrated pipeline detection."""
        
        print(f"\n🔗 INTEGRATED PIPELINE:")
        
        start_time = time.time()
        
        try:
            # Use the enhanced data collector with session management
            result = self.enhanced_collector.analyze_screenshot_with_session(
                image_path=image_path,
                ign="Lesz XVII",  # Use default IGN
                session_id=None,
                hero_override=None
            )
            
            processing_time = time.time() - start_time
            
            if result and result.get("data"):
                data = result["data"]
                
                # Extract trophy detection results
                mvp_detected = data.get("mvp_detected", False)
                medal_type = data.get("medal_type", None)
                trophy_confidence = data.get("trophy_confidence", 0.0)
                performance_label = data.get("performance_label", "Unknown")
                contextual_rating = data.get("contextual_performance_rating", "Unknown")
                
                # Determine detected trophy type
                if mvp_detected:
                    trophy_type = "mvp_crown"
                elif medal_type:
                    trophy_type = medal_type
                else:
                    trophy_type = "none"
                
                print(f"   Result: {trophy_type}")
                print(f"   MVP Detected: {mvp_detected}")
                print(f"   Medal Type: {medal_type}")
                print(f"   Trophy Confidence: {trophy_confidence:.3f}")
                print(f"   Performance Label: {performance_label}")
                print(f"   Contextual Rating: {contextual_rating}")
                print(f"   Processing Time: {processing_time:.2f}s")
                print(f"   Overall Confidence: {result.get('overall_confidence', 0.0):.3f}")
                
                detection_success = trophy_confidence > 0.3 and trophy_type != "none"
                
                return {
                    "detection_success": detection_success,
                    "trophy_type": trophy_type,
                    "confidence": trophy_confidence,
                    "mvp_detected": mvp_detected,
                    "medal_type": medal_type,
                    "performance_label": performance_label,
                    "contextual_rating": contextual_rating,
                    "processing_time": processing_time,
                    "overall_confidence": result.get("overall_confidence", 0.0),
                    "warnings": result.get("warnings", [])
                }
            else:
                print(f"   Integration failed - no data returned")
                print(f"   Processing Time: {processing_time:.2f}s")
                
                return {
                    "detection_success": False,
                    "trophy_type": "none",
                    "confidence": 0.0,
                    "processing_time": processing_time,
                    "error": "No data returned from integrated pipeline"
                }
                
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"   Integration error: {e}")
            print(f"   Processing Time: {processing_time:.2f}s")
            
            return {
                "detection_success": False,
                "trophy_type": "none", 
                "confidence": 0.0,
                "processing_time": processing_time,
                "error": str(e)
            }
    
    def _analyze_consistency(
        self, 
        direct_result: Dict[str, Any], 
        integrated_result: Dict[str, Any],
        test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze consistency between direct and integrated detection."""
        
        # Check if both methods detected something
        both_detected = (direct_result["detection_success"] and 
                        integrated_result["detection_success"])
        
        # Check if trophy types match
        trophy_types_match = (direct_result["trophy_type"] == 
                             integrated_result["trophy_type"])
        
        # Calculate performance gap
        direct_conf = direct_result["confidence"]
        integrated_conf = integrated_result["confidence"]
        performance_gap = abs(direct_conf - integrated_conf)
        
        # Calculate positioning difference (if available)
        positioning_diff = None
        if (direct_result.get("bounding_box") and 
            integrated_result.get("bounding_box")):
            direct_bbox = direct_result["bounding_box"]
            integrated_bbox = integrated_result["bounding_box"]
            
            # Calculate center points
            direct_center_y = direct_bbox[1] + direct_bbox[3] / 2
            integrated_center_y = integrated_bbox[1] + integrated_bbox[3] / 2
            positioning_diff = abs(direct_center_y - integrated_center_y)
        
        # Determine consistency
        consistent = (both_detected and trophy_types_match and performance_gap < 0.3)
        
        return {
            "consistent": consistent,
            "both_detected": both_detected,
            "trophy_types_match": trophy_types_match,
            "performance_gap": performance_gap,
            "positioning_diff": positioning_diff,
            "direct_confidence": direct_conf,
            "integrated_confidence": integrated_conf,
            "reliability_improvement": integrated_result["detection_success"]
        }


def main():
    """Run MVP pipeline consistency tests."""
    
    print("🔧 MVP PIPELINE CONSISTENCY VALIDATION")
    print("=" * 50)
    print("🎯 Testing fixes for 50% → 95%+ reliability issue")
    print("🔧 Enhancements: v3 detector, fallback positioning, quality hints")
    print()
    
    tester = MVPPipelineConsistencyTester()
    
    try:
        results = tester.test_mvp_pipeline_consistency()
        
        # Display final summary
        print(f"\n🎉 PIPELINE CONSISTENCY TEST COMPLETE")
        print(f"📊 Integrated Pipeline Reliability: {results['integrated_reliability']:.1f}%")
        print(f"📊 Direct Detection Reliability: {results['direct_reliability']:.1f}%") 
        print(f"📊 Consistency Rate: {results['consistency_rate']:.1f}%")
        print(f"🏆 Success Level: {results['success_level'].upper()}")
        
        if results['integrated_reliability'] >= 95:
            print("\n✅ CRITICAL ISSUE RESOLVED!")
            print("🚀 MVP pipeline ready for production")
        elif results['integrated_reliability'] >= 75:
            print("\n🟡 Significant improvement achieved")
            print("🔧 Minor tuning recommended")
        else:
            print("\n🔴 Additional optimization needed")
            print("📋 Review detailed results for improvement areas")
        
        # Save detailed report
        import json
        from pathlib import Path
        
        report_path = Path("temp/mvp_pipeline_consistency_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved: {report_path}")
        
        return results['integrated_reliability'] >= 75
        
    except Exception as e:
        print(f"❌ Pipeline consistency test failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    print(f"\n🎯 MVP Pipeline Consistency: {'RESOLVED' if success else 'NEEDS MORE WORK'}")
