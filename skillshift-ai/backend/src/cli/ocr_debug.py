#!/usr/bin/env python3
"""
OCR Debug CLI Command

Provides command-line interface for testing OCR functionality
and debugging OCR issues with real screenshots.
"""

import argparse
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.src.services.ocr_debug_service import OCRDebugService
    from backend.src.services.analysis_service import ScreenshotAnalysisService
    from backend.ocr.detectors import row_agnostic_detector
    from backend.ocr.parsers_kda import kda_parser
    from backend.ocr.parsers_damage import damage_parser
    from backend.ocr.fuse import cross_view_fusion
except ImportError as e:
    print(f"❌ Error importing OCR modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def format_kda(kda_dict: Dict[str, Any]) -> str:
    """Format KDA dictionary as string."""
    if not kda_dict:
        return "N/A"
    return f"{kda_dict.get('kills', 0)}/{kda_dict.get('deaths', 0)}/{kda_dict.get('assists', 0)}"


def print_result(title: str, result: Dict[str, Any], show_debug: bool = False):
    """Print formatted result."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")
    
    # Basic info
    print(f"Player Located: {'✅ Yes' if result.get('player_located') else '❌ No'}")
    print(f"Player IGN: {result.get('player_ign', 'N/A')}")
    print(f"KDA: {format_kda(result.get('kda', {}))}")
    print(f"Confidence: {result.get('overall_confidence', 0.0):.2f}")
    
    # Additional info
    if 'rows_count' in result:
        print(f"Rows Detected: {result.get('rows_count', 0)}")
    
    if 'table_bbox' in result and result['table_bbox']:
        bbox = result['table_bbox']
        print(f"Table BBox: {bbox}")
    
    # Debug info
    if show_debug and 'debug' in result:
        debug = result['debug']
        print(f"\n🐛 Debug Information:")
        if 'ratios' in debug:
            ratios = debug['ratios']
            print(f"  Row Top Ratio: {ratios.get('row_top', 'N/A')}")
            print(f"  Row Height Ratio: {ratios.get('row_height', 'N/A')}")
        if 'anchors_detected' in debug:
            anchors = debug['anchors_detected']
            print(f"  Anchors Found: {anchors if anchors else 'None'}")


def test_ocr_debug(image_path: str, target_ign: str, debug_mode: bool = False, 
                  with_damage: bool = False) -> Dict[str, Any]:
    """Test OCR debug service."""
    print(f"🚀 Testing OCR Debug Service")
    print(f"   Image: {image_path}")
    print(f"   Target IGN: {target_ign}")
    print(f"   Debug Mode: {debug_mode}")
    print(f"   With Damage: {with_damage}")
    
    service = OCRDebugService()
    
    start_time = time.time()
    try:
        result = service.debug(
            image_path=image_path,
            target_ign=target_ign,
            debug_mode=debug_mode,
            extract_options={"with_damage": with_damage} if with_damage else None
        )
        processing_time = time.time() - start_time
        
        print(f"⏱️  Processing Time: {processing_time:.2f}s")
        print_result("OCR Debug Result", result, debug_mode)
        
        return result
        
    except Exception as e:
        print(f"❌ OCR Debug failed: {e}")
        return {"error": str(e)}


def test_analysis_service(image_path: str, ign: str, debug_mode: bool = False,
                         with_damage: bool = False) -> Dict[str, Any]:
    """Test analysis service."""
    print(f"🚀 Testing Analysis Service")
    print(f"   Image: {image_path}")
    print(f"   IGN: {ign}")
    print(f"   Debug Mode: {debug_mode}")
    print(f"   With Damage: {with_damage}")
    
    service = ScreenshotAnalysisService()
    
    start_time = time.time()
    try:
        result = service.analyze(
            image_path=image_path,
            ign=ign,
            debug_mode=debug_mode,
            row_agnostic_mode=True,
            extract_options={"with_damage": with_damage} if with_damage else None
        )
        processing_time = time.time() - start_time
        
        print(f"⏱️  Processing Time: {processing_time:.2f}s")
        print_result("Analysis Service Result", result, debug_mode)
        
        return result
        
    except Exception as e:
        print(f"❌ Analysis Service failed: {e}")
        return {"error": str(e)}


def test_detector(image_path: str, target_ign: str) -> Dict[str, Any]:
    """Test detector directly."""
    print(f"🚀 Testing Detector Directly")
    print(f"   Image: {image_path}")
    print(f"   Target IGN: {target_ign}")
    
    start_time = time.time()
    try:
        # Test table detection
        table_region = row_agnostic_detector.detect_table_regions(image_path)
        if not table_region:
            print("❌ Could not detect table regions")
            return {"error": "No table regions detected"}
        
        print(f"✅ Table regions detected")
        print(f"   Confidence: {table_region.confidence:.2f}")
        print(f"   Rows Count: {table_region.rows_count}")
        print(f"   Anchors Found: {table_region.anchors_found}")
        
        # Test row generation
        row_crops = row_agnostic_detector.generate_row_crops(table_region, image_path, target_ign)
        if not row_crops:
            print("❌ Could not generate row crops")
            return {"error": "No row crops generated"}
        
        print(f"✅ Row crops generated: {len(row_crops)} rows")
        
        # Test target row finding
        target_row = row_agnostic_detector.find_target_row(row_crops, target_ign)
        if target_row:
            print(f"✅ Target row found for IGN: {target_ign}")
            print(f"   Row Index: {target_row.row_index}")
            print(f"   Confidence: {target_row.confidence:.2f}")
        else:
            print(f"⚠️  Target row not found for IGN: {target_ign}")
        
        processing_time = time.time() - start_time
        print(f"⏱️  Processing Time: {processing_time:.2f}s")
        
        return {
            "table_region": {
                "confidence": table_region.confidence,
                "rows_count": table_region.rows_count,
                "anchors_found": table_region.anchors_found
            },
            "row_crops_count": len(row_crops),
            "target_row_found": target_row is not None,
            "processing_time": processing_time
        }
        
    except Exception as e:
        print(f"❌ Detector test failed: {e}")
        return {"error": str(e)}


def test_parsers(image_path: str, target_ign: str) -> Dict[str, Any]:
    """Test parsers directly."""
    print(f"🚀 Testing Parsers Directly")
    print(f"   Image: {image_path}")
    print(f"   Target IGN: {target_ign}")
    
    start_time = time.time()
    results = {}
    
    try:
        # Test KDA parser
        print("\n📊 Testing KDA Parser...")
        kda_result = kda_parser.parse_kda_from_screenshot(image_path, target_ign)
        if kda_result:
            print(f"✅ KDA parsed successfully")
            print(f"   Hero: {kda_result.hero}")
            print(f"   KDA: {kda_result.kills}/{kda_result.deaths}/{kda_result.assists}")
            print(f"   MVP Score: {kda_result.mvp_score}")
            print(f"   Confidence: {kda_result.confidence:.2f}")
            results["kda"] = {
                "hero": kda_result.hero,
                "kills": kda_result.kills,
                "deaths": kda_result.deaths,
                "assists": kda_result.assists,
                "mvp_score": kda_result.mvp_score,
                "confidence": kda_result.confidence
            }
        else:
            print("❌ KDA parsing failed")
            results["kda"] = None
        
        # Test Damage parser
        print("\n💥 Testing Damage Parser...")
        damage_result = damage_parser.parse_damage_from_screenshot(image_path, target_ign)
        if damage_result:
            print(f"✅ Damage parsed successfully")
            print(f"   Hero Damage: {damage_result.hero_damage}")
            print(f"   Tower Damage: {damage_result.tower_damage}")
            print(f"   Damage Taken: {damage_result.damage_taken}")
            print(f"   Teamfight Participation: {damage_result.teamfight_participation:.1f}%")
            print(f"   Confidence: {damage_result.confidence:.2f}")
            results["damage"] = {
                "hero_damage": damage_result.hero_damage,
                "tower_damage": damage_result.tower_damage,
                "damage_taken": damage_result.damage_taken,
                "teamfight_participation": damage_result.teamfight_participation,
                "confidence": damage_result.confidence
            }
        else:
            print("❌ Damage parsing failed")
            results["damage"] = None
        
        # Test fusion
        print("\n🔄 Testing Cross-View Fusion...")
        fusion_result = cross_view_fusion.fuse_kda_and_damage(kda_result, damage_result)
        if fusion_result:
            print(f"✅ Fusion successful")
            print(f"   Player IGN: {fusion_result.player_ign}")
            print(f"   Hero: {fusion_result.hero}")
            print(f"   Overall Confidence: {fusion_result.overall_confidence:.2f}")
            print(f"   Data Completeness: {fusion_result.data_completeness:.2f}")
            print(f"   Fusion Method: {fusion_result.fusion_method}")
            results["fusion"] = {
                "player_ign": fusion_result.player_ign,
                "hero": fusion_result.hero,
                "overall_confidence": fusion_result.overall_confidence,
                "data_completeness": fusion_result.data_completeness,
                "fusion_method": fusion_result.fusion_method
            }
        else:
            print("❌ Fusion failed")
            results["fusion"] = None
        
        processing_time = time.time() - start_time
        print(f"⏱️  Total Processing Time: {processing_time:.2f}s")
        results["processing_time"] = processing_time
        
        return results
        
    except Exception as e:
        print(f"❌ Parser test failed: {e}")
        return {"error": str(e)}


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="OCR Debug CLI - Test and debug OCR functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test OCR debug service
  python -m backend.src.cli.ocr_debug --image path/to/screenshot.png --ign "Player Name"
  
  # Test with debug mode and damage parsing
  python -m backend.src.cli.ocr_debug --image path/to/screenshot.png --ign "Player Name" --debug --damage
  
  # Test all components
  python -m backend.src.cli.ocr_debug --image path/to/screenshot.png --ign "Player Name" --all
  
  # Test detector only
  python -m backend.src.cli.ocr_debug --image path/to/screenshot.png --ign "Player Name" --detector
        """
    )
    
    parser.add_argument(
        "--image", "-i",
        required=True,
        help="Path to screenshot image"
    )
    
    parser.add_argument(
        "--ign", "-n",
        required=True,
        help="Target player IGN to look for"
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug mode for detailed output"
    )
    
    parser.add_argument(
        "--damage", "-dm",
        action="store_true",
        help="Include damage parsing (slower but more complete)"
    )
    
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Test all components (detector, parsers, services)"
    )
    
    parser.add_argument(
        "--detector", "-dt",
        action="store_true",
        help="Test detector only"
    )
    
    parser.add_argument(
        "--parsers", "-p",
        action="store_true",
        help="Test parsers only"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file for JSON results"
    )
    
    args = parser.parse_args()
    
    # Validate image path
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"❌ Image file not found: {image_path}")
        sys.exit(1)
    
    print(f"🔧 OCR Debug CLI")
    print(f"   Image: {image_path}")
    print(f"   Target IGN: {args.ign}")
    print(f"   Debug Mode: {args.debug}")
    print(f"   With Damage: {args.damage}")
    
    results = {}
    
    try:
        if args.all or args.detector:
            print(f"\n{'='*80}")
            print(f"🔍 TESTING DETECTOR")
            print(f"{'='*80}")
            results["detector"] = test_detector(str(image_path), args.ign)
        
        if args.all or args.parsers:
            print(f"\n{'='*80}")
            print(f"🔍 TESTING PARSERS")
            print(f"{'='*80}")
            results["parsers"] = test_parsers(str(image_path), args.ign)
        
        if args.all or (not args.detector and not args.parsers):
            print(f"\n{'='*80}")
            print(f"🔍 TESTING SERVICES")
            print(f"{'='*80}")
            results["ocr_debug"] = test_ocr_debug(
                str(image_path), args.ign, args.debug, args.damage
            )
            results["analysis"] = test_analysis_service(
                str(image_path), args.ign, args.debug, args.damage
            )
        
        # Output results
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {output_path}")
        
        print(f"\n{'='*80}")
        print(f"✅ OCR Debug CLI completed successfully!")
        print(f"{'='*80}")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
