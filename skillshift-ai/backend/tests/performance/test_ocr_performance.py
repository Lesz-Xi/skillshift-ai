"""
Performance tests for OCR pipeline with CI guardrails (OCR-Mission-1.md).

Tests OCR processing against configurable performance budgets with 
ratcheting schedule: 2000ms → 1500ms → 1000ms → 500ms.

Environment Variables:
- OCR_BUDGET_MS: Performance budget in milliseconds (default: 2000)
- ENFORCE_OCR_BUDGET: Enable/disable budget enforcement (default: 1)
- FAST_TEST: Enable fast test mode for optimal performance (default: True)

Usage Examples:
- OCR_BUDGET_MS=1500 pytest backend/tests/performance/test_ocr_performance.py
- ENFORCE_OCR_BUDGET=0 pytest backend/tests/performance/test_ocr_performance.py
"""

import pytest
import time
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Performance budget with environment variable support (OCR-Mission-1.md)
# Ratcheting schedule: 2000ms → 1500ms → 1000ms → 500ms
PERFORMANCE_BUDGET_MS = int(os.getenv("OCR_BUDGET_MS", "2000"))
FAST_TEST_MODE = True

# CI Performance validation enabled
ENFORCE_PERFORMANCE_BUDGET = os.getenv("ENFORCE_OCR_BUDGET", "1") == "1"


class TestOCRPerformance:
    """Performance tests for OCR pipeline."""
    
    @pytest.fixture
    def test_images(self):
        """Get test image paths."""
        # Use the trial images if available
        trial_dir = project_root.parent / "Trial-Image"
        if trial_dir.exists():
            images = list(trial_dir.glob("*.PNG")) + list(trial_dir.glob("*.png"))
            if len(images) >= 2:
                return {
                    "kda_image": str(images[0]),
                    "damage_image": str(images[1])
                }
        
        # Fallback to any available test images
        test_dir = project_root / "test_screenshots"
        if test_dir.exists():
            images = list(test_dir.glob("*.PNG")) + list(test_dir.glob("*.png"))
            if len(images) >= 2:
                return {
                    "kda_image": str(images[0]),
                    "damage_image": str(images[1])
                }
        
        pytest.skip("No test images available for performance testing")
    
    @pytest.fixture
    def ocr_service(self):
        """Create OCR debug service instance."""
        try:
            from backend.src.services.ocr_debug_service import OCRDebugService
            return OCRDebugService()
        except ImportError:
            pytest.skip("OCR debug service not available")
    
    @pytest.fixture
    def analysis_service(self):
        """Create analysis service instance."""
        try:
            from backend.src.services.analysis_service import ScreenshotAnalysisService
            return ScreenshotAnalysisService()
        except ImportError:
            pytest.skip("Analysis service not available")
    
    def test_ocr_debug_performance(self, ocr_service, test_images):
        """Test OCR debug service performance."""
        print(f"\n🚀 Testing OCR debug performance with FAST_TEST={FAST_TEST_MODE}")
        
        start_time = time.time()
        
        try:
            result = ocr_service.debug(
                image_path=test_images["kda_image"],
                target_ign="Diary of dolls",
                debug_mode=True,
                extract_options={"with_damage": True} if FAST_TEST_MODE else None
            )
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            print(f"⏱️  OCR debug processing time: {processing_time_ms:.2f}ms")
            print(f"📊 Result keys: {list(result.keys())}")
            
            # Performance budget validation with CI guardrails
            if ENFORCE_PERFORMANCE_BUDGET:
                assert processing_time_ms <= PERFORMANCE_BUDGET_MS, (
                    f"OCR debug processing took {processing_time_ms:.2f}ms, "
                    f"exceeds performance budget of {PERFORMANCE_BUDGET_MS}ms "
                    f"(set via OCR_BUDGET_MS environment variable)"
                )
                print(f"✅ Performance budget met: {processing_time_ms:.2f}ms <= {PERFORMANCE_BUDGET_MS}ms")
            else:
                print(f"ℹ️  Performance budget check disabled (ENFORCE_OCR_BUDGET=0)")
                print(f"   Current time: {processing_time_ms:.2f}ms, Budget: {PERFORMANCE_BUDGET_MS}ms")
            
            # Basic result validation
            assert "player_located" in result
            assert "overall_confidence" in result
            assert "kda" in result
            
            print("✅ OCR debug performance test passed")
            
        except Exception as e:
            print(f"❌ OCR debug performance test failed: {e}")
            # Don't fail the test if it's due to missing dependencies
            if "No module named" in str(e) or "ImportError" in str(e):
                pytest.skip(f"Missing dependencies: {e}")
            raise
    
    def test_analysis_service_performance(self, analysis_service, test_images):
        """Test analysis service performance."""
        print(f"\n🚀 Testing analysis service performance with FAST_TEST={FAST_TEST_MODE}")
        
        start_time = time.time()
        
        try:
            result = analysis_service.analyze(
                image_path=test_images["kda_image"],
                ign="Diary of dolls",
                debug_mode=True,
                row_agnostic_mode=True,
                extract_options={"with_damage": True} if FAST_TEST_MODE else None
            )
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            print(f"⏱️  Analysis service processing time: {processing_time_ms:.2f}ms")
            print(f"📊 Result keys: {list(result.keys())}")
            
            # Performance budget validation with CI guardrails
            if ENFORCE_PERFORMANCE_BUDGET:
                assert processing_time_ms <= PERFORMANCE_BUDGET_MS, (
                    f"Analysis service processing took {processing_time_ms:.2f}ms, "
                    f"exceeds performance budget of {PERFORMANCE_BUDGET_MS}ms "
                    f"(set via OCR_BUDGET_MS environment variable)"
                )
                print(f"✅ Performance budget met: {processing_time_ms:.2f}ms <= {PERFORMANCE_BUDGET_MS}ms")
            else:
                print(f"ℹ️  Performance budget check disabled (ENFORCE_OCR_BUDGET=0)")
                print(f"   Current time: {processing_time_ms:.2f}ms, Budget: {PERFORMANCE_BUDGET_MS}ms")
            
            # Basic result validation
            assert "player_located" in result
            assert "overall_confidence" in result
            assert "kda" in result
            assert "ign" in result
            
            print("✅ Analysis service performance test passed")
            
        except Exception as e:
            print(f"❌ Analysis service performance test failed: {e}")
            # Don't fail the test if it's due to missing dependencies
            if "No module named" in str(e) or "ImportError" in str(e):
                pytest.skip(f"Missing dependencies: {e}")
            raise
    
    def test_cross_view_fusion_performance(self, test_images):
        """Test cross-view fusion performance (KDA + Damage)."""
        print(f"\n🚀 Testing cross-view fusion performance with FAST_TEST={FAST_TEST_MODE}")
        
        try:
            from backend.src.services.ocr_debug_service import OCRDebugService
            from backend.ocr.detectors import row_agnostic_detector
            from backend.ocr.parsers_kda import kda_parser
            from backend.ocr.parsers_damage import damage_parser
            from backend.ocr.fuse import cross_view_fusion
            import cv2
            import numpy as np
            
            start_time = time.time()
            
            # Load both images
            kda_img = cv2.imread(test_images["kda_image"])
            dmg_img = cv2.imread(test_images["damage_image"])
            
            if kda_img is None or dmg_img is None:
                pytest.skip("Could not load test images")
            
            # Detect table and rows once
            table = row_agnostic_detector.detect(kda_img)
            rows = row_agnostic_detector.rows(kda_img, table)
            
            # Parse both views
            kda = kda_parser.parse_from_rows(kda_img, rows)
            dmg = damage_parser.parse_from_rows(dmg_img, rows)
            
            # Cross-view fusion
            fusion = cross_view_fusion(kda, dmg)
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            print(f"⏱️  Cross-view fusion processing time: {processing_time_ms:.2f}ms")
            print(f"📊 Fusion result keys: {list(fusion.__dict__.keys()) if hasattr(fusion, '__dict__') else 'N/A'}")
            
            # Performance budget validation with CI guardrails
            if ENFORCE_PERFORMANCE_BUDGET:
                assert processing_time_ms <= PERFORMANCE_BUDGET_MS, (
                    f"Cross-view fusion processing took {processing_time_ms:.2f}ms, "
                    f"exceeds performance budget of {PERFORMANCE_BUDGET_MS}ms "
                    f"(set via OCR_BUDGET_MS environment variable)"
                )
                print(f"✅ Performance budget met: {processing_time_ms:.2f}ms <= {PERFORMANCE_BUDGET_MS}ms")
            else:
                print(f"ℹ️  Performance budget check disabled (ENFORCE_OCR_BUDGET=0)")
                print(f"   Current time: {processing_time_ms:.2f}ms, Budget: {PERFORMANCE_BUDGET_MS}ms")
            
            # Basic result validation
            assert hasattr(fusion, 'player_located')
            assert hasattr(fusion, 'overall_confidence')
            assert hasattr(fusion, 'kda')
            
            print("✅ Cross-view fusion performance test passed")
            
        except Exception as e:
            print(f"❌ Cross-view fusion performance test failed: {e}")
            # Don't fail the test if it's due to missing dependencies
            if "No module named" in str(e) or "ImportError" in str(e):
                pytest.skip(f"Missing dependencies: {e}")
            raise
    
    def test_api_endpoint_performance(self, test_images):
        """Test API endpoint performance."""
        print(f"\n🚀 Testing API endpoint performance with FAST_TEST={FAST_TEST_MODE}")
        
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            from backend.src.api.v2.ocr import router as ocr_router
            from backend.src.api.v2.analysis import router as analysis_router
            
            app = FastAPI()
            app.include_router(ocr_router)
            app.include_router(analysis_router)
            
            client = TestClient(app)
            
            # Test OCR debug endpoint
            start_time = time.time()
            response = client.post("/ocr/debug", json={
                "image_path": test_images["kda_image"],
                "target_ign": "Diary of dolls",
                "debug_mode": True,
                "extract_options": {"with_damage": True} if FAST_TEST_MODE else None
            })
            debug_time_ms = (time.time() - start_time) * 1000
            
            print(f"⏱️  OCR debug API time: {debug_time_ms:.2f}ms")
            print(f"📊 Response status: {response.status_code}")
            
            # Test analysis endpoint
            start_time = time.time()
            response = client.post("/analysis/screenshot", json={
                "image_path": test_images["kda_image"],
                "ign": "Diary of dolls",
                "debug_mode": True,
                "row_agnostic_mode": True,
                "extract_options": {"with_damage": True} if FAST_TEST_MODE else None
            })
            analysis_time_ms = (time.time() - start_time) * 1000
            
            print(f"⏱️  Analysis API time: {analysis_time_ms:.2f}ms")
            print(f"📊 Response status: {response.status_code}")
            
            # Performance budget validation with CI guardrails
            if ENFORCE_PERFORMANCE_BUDGET:
                assert debug_time_ms <= PERFORMANCE_BUDGET_MS, (
                    f"OCR debug API took {debug_time_ms:.2f}ms, "
                    f"exceeds performance budget of {PERFORMANCE_BUDGET_MS}ms "
                    f"(set via OCR_BUDGET_MS environment variable)"
                )
                
                assert analysis_time_ms <= PERFORMANCE_BUDGET_MS, (
                    f"Analysis API took {analysis_time_ms:.2f}ms, "
                    f"exceeds performance budget of {PERFORMANCE_BUDGET_MS}ms "
                    f"(set via OCR_BUDGET_MS environment variable)"
                )
                print(f"✅ Both API endpoints met budget: debug={debug_time_ms:.2f}ms, analysis={analysis_time_ms:.2f}ms <= {PERFORMANCE_BUDGET_MS}ms")
            else:
                print(f"ℹ️  Performance budget check disabled (ENFORCE_OCR_BUDGET=0)")
                print(f"   OCR debug API time: {debug_time_ms:.2f}ms, Budget: {PERFORMANCE_BUDGET_MS}ms")
                print(f"   Analysis API time: {analysis_time_ms:.2f}ms, Budget: {PERFORMANCE_BUDGET_MS}ms")
            
            print("✅ API endpoint performance test passed")
            
        except Exception as e:
            print(f"❌ API endpoint performance test failed: {e}")
            # Don't fail the test if it's due to missing dependencies
            if "No module named" in str(e) or "ImportError" in str(e):
                pytest.skip(f"Missing dependencies: {e}")
            raise


if __name__ == "__main__":
    # Run performance tests directly
    pytest.main([__file__, "-v", "-s"])
