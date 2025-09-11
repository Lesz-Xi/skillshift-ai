#!/usr/bin/env python3
"""
MVP Pipeline 95% Target Test - Final Validation

Tests the fully optimized MVP pipeline with all enhancements:
1. Enhanced IGN detection with multiple strategies
2. Comprehensive fallback positioning algorithms 
3. Confidence boosting mechanisms
4. Intelligent retry logic with quality hints
5. Improved heuristic player name detection

Target: Achieve 95%+ integrated pipeline reliability
"""

import os
import sys
import time
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.enhanced_data_collector import EnhancedDataCollector


class MVP95TargetTester:
    """Test MVP pipeline for 95% target achievement."""
    
    def __init__(self):
        self.enhanced_collector = EnhancedDataCollector()
        
    def test_95_percent_target(self) -> dict:
        """Test the MVP pipeline for 95% reliability target."""
        
        print("🎯 MVP PIPELINE 95% TARGET TEST")
        print("=" * 60)
        print("🚀 Testing fully optimized pipeline with all enhancements")
        print("🔧 Enhanced IGN detection + Fallback strategies + Confidence boosting")
        print()
        
        # Extended test set for more comprehensive validation
        test_images = [
            "yolo_dataset/images/test/edb4fa11-6_ranked_matches_good_performance_match06_win_kda.PNG",
            "yolo_dataset/images/test/ef18ecbc-2_ranked_matches_good_performance_match02_win_kda.PNG",
            "yolo_dataset/images/test/ea01384d-1_ranked_matches_average_performance_match01_win_kda.PNG",
            "yolo_dataset/images/test/ranked_poor_kda_059.jpg",
            # Add more test images if available
            "yolo_dataset/images/test/fff98301-4_ranked_matches_average_performance_match04_win_kda.PNG",
            "yolo_dataset/images/test/fc2a5f56-3_ranked_matches_average_performance_match03_win_damage.PNG"
        ]
        
        successful_detections = 0
        total_tests = 0
        detailed_results = []
        
        for image_path in test_images:
            if not os.path.exists(image_path):
                print(f"⚠️ Skipping {image_path} - not found")
                continue
            
            total_tests += 1
            print(f"\n📸 TEST {total_tests}: {os.path.basename(image_path)}")
            print("-" * 50)
            
            start_time = time.time()
            
            try:
                # Test the integrated pipeline
                result = self.enhanced_collector.analyze_screenshot_with_session(
                    image_path=image_path,
                    ign="Lesz XVII",
                    session_id=None,
                    hero_override=None
                )
                
                processing_time = time.time() - start_time
                
                if result and result.get("data"):
                    data = result["data"]
                    
                    # Check trophy detection results
                    mvp_detected = data.get("mvp_detected", False)
                    medal_type = data.get("medal_type", None)
                    trophy_confidence = data.get("trophy_confidence", 0.0)
                    performance_label = data.get("performance_label", "Unknown")
                    contextual_rating = data.get("contextual_performance_rating", "Unknown")
                    
                    # Determine if detection was successful
                    detection_success = (
                        (mvp_detected or medal_type is not None) and 
                        trophy_confidence > 0.3
                    )
                    
                    if detection_success:
                        successful_detections += 1
                        status = "✅ SUCCESS"
                    else:
                        status = "❌ FAILED"
                    
                    trophy_type = "mvp_crown" if mvp_detected else medal_type
                    
                    print(f"   Result: {status}")
                    print(f"   Trophy Type: {trophy_type}")
                    print(f"   MVP Detected: {mvp_detected}")
                    print(f"   Medal Type: {medal_type}")
                    print(f"   Trophy Confidence: {trophy_confidence:.3f}")
                    print(f"   Performance Label: {performance_label}")
                    print(f"   Contextual Rating: {contextual_rating}")
                    print(f"   Processing Time: {processing_time:.2f}s")
                    print(f"   Overall Confidence: {result.get('overall_confidence', 0.0):.3f}")
                    
                    # Show warnings if any
                    warnings = result.get("warnings", [])
                    if warnings:
                        print(f"   Warnings: {len(warnings)}")
                        for warning in warnings[:2]:  # Show first 2 warnings
                            print(f"      - {warning}")
                    
                    detailed_results.append({
                        "image": os.path.basename(image_path),
                        "success": detection_success,
                        "trophy_type": trophy_type,
                        "trophy_confidence": trophy_confidence,
                        "performance_label": performance_label,
                        "processing_time": processing_time,
                        "overall_confidence": result.get("overall_confidence", 0.0),
                        "warnings_count": len(warnings)
                    })
                    
                else:
                    print(f"   ❌ FAILED: No data returned")
                    print(f"   Processing Time: {processing_time:.2f}s")
                    
                    detailed_results.append({
                        "image": os.path.basename(image_path),
                        "success": False,
                        "trophy_type": "none",
                        "trophy_confidence": 0.0,
                        "performance_label": "Unknown",
                        "processing_time": processing_time,
                        "overall_confidence": 0.0,
                        "warnings_count": 0
                    })
                    
            except Exception as e:
                processing_time = time.time() - start_time
                print(f"   ❌ ERROR: {e}")
                print(f"   Processing Time: {processing_time:.2f}s")
                
                detailed_results.append({
                    "image": os.path.basename(image_path),
                    "success": False,
                    "trophy_type": "error",
                    "trophy_confidence": 0.0,
                    "performance_label": "Error",
                    "processing_time": processing_time,
                    "overall_confidence": 0.0,
                    "error": str(e)
                })
        
        # Calculate final metrics
        success_rate = (successful_detections / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 FINAL 95% TARGET RESULTS")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Successful Detections: {successful_detections}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Detailed breakdown
        print(f"\nDetailed Results:")
        for i, result in enumerate(detailed_results, 1):
            status = "✅" if result['success'] else "❌"
            print(f"  {status} Test {i}: {result['trophy_type']} (conf: {result['trophy_confidence']:.3f}) "
                  f"- {result['performance_label']} - {result['processing_time']:.1f}s")
        
        # Success evaluation against 95% target
        print(f"\n🏆 95% TARGET EVALUATION:")
        if success_rate >= 95:
            print("🎉 EXCELLENT: 95% target ACHIEVED!")
            print("✅ MVP Pipeline ready for production deployment")
            success_level = "target_achieved"
        elif success_rate >= 80:
            print("🟡 VERY GOOD: Close to 95% target")
            print("🔧 Minor optimization could reach 95%")
            success_level = "close_to_target"
        elif success_rate >= 75:
            print("🟠 GOOD: Significant improvement")
            print("🔧 Additional optimization needed for 95% target")
            success_level = "good_progress"
        else:
            print("🔴 NEEDS WORK: Below 75% baseline")
            success_level = "needs_work"
        
        # Performance analysis
        if detailed_results:
            avg_processing_time = sum(r['processing_time'] for r in detailed_results) / len(detailed_results)
            avg_confidence = sum(r['trophy_confidence'] for r in detailed_results if r['success']) / max(1, successful_detections)
            
            print(f"\n📊 Performance Analysis:")
            print(f"   Average Processing Time: {avg_processing_time:.2f}s")
            print(f"   Average Trophy Confidence: {avg_confidence:.3f}")
            print(f"   Success Rate vs Baseline (50%): +{success_rate - 50:.1f}%")
        
        return {
            "total_tests": total_tests,
            "successful_detections": successful_detections,
            "success_rate": success_rate,
            "success_level": success_level,
            "detailed_results": detailed_results,
            "target_achieved": success_rate >= 95
        }


def main():
    """Run the 95% target test."""
    
    print("🚀 MVP PIPELINE 95% TARGET VALIDATION")
    print("=" * 50)
    print("🎯 Goal: Achieve 95%+ integrated pipeline reliability")
    print("🔧 All optimizations applied")
    print()
    
    tester = MVP95TargetTester()
    
    try:
        results = tester.test_95_percent_target()
        
        # Save results
        report_path = Path("temp/mvp_pipeline_95_target_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved: {report_path}")
        
        # Final summary
        success_rate = results['success_rate']
        target_achieved = results['target_achieved']
        
        print(f"\n🎉 FINAL SUMMARY")
        print(f"📊 Pipeline Reliability: {success_rate:.1f}%")
        print(f"🎯 95% Target: {'✅ ACHIEVED' if target_achieved else '🔧 NOT YET REACHED'}")
        
        if target_achieved:
            print("\n🏆 CRITICAL MILESTONE ACHIEVED!")
            print("✅ MVP Pipeline optimized to 95%+ reliability")
            print("🚀 Ready for production deployment")
        elif success_rate >= 80:
            print(f"\n🟡 VERY CLOSE to 95% target ({95 - success_rate:.1f}% gap)")
            print("🔧 Minor fine-tuning recommended")
        else:
            print(f"\n🔧 Additional optimization needed ({95 - success_rate:.1f}% gap to target)")
        
        return target_achieved
        
    except Exception as e:
        print(f"❌ 95% target test failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    print(f"\n🎯 MVP Pipeline 95% Target: {'ACHIEVED' if success else 'IN PROGRESS'}")
