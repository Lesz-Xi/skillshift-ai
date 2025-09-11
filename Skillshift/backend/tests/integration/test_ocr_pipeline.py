"""
T013: OCR Pipeline Integration Test
End-to-end testing of the complete OCR processing pipeline using real screenshots
"""

import pytest
import cv2
import time
from pathlib import Path
from typing import Dict, Any

# Import the OCR modules we've built
from backend.ocr.parsers_kda import parse_kda_view_v2
from backend.ocr.parsers_damage import parse_damage_view
from backend.ocr.fuse import fuse_cross_view_data
from backend.ocr.detectors import detect_player_row_fuzzy
from backend.src.models.ocr import (
    OCRExtractionResult,
    CrossViewFusionResult,
    OCRProcessingStats
)


class TestOCRPipelineIntegration:
    """Integration tests for complete OCR pipeline"""
    
    @pytest.fixture
    def kda_image_path(self):
        """Path to KDA view test image"""
        return "backend/tests/fixtures/IMG_1767.PNG"
    
    @pytest.fixture
    def damage_image_path(self):
        """Path to Damage view test image"""
        return "backend/tests/fixtures/IMG_1768.PNG"
    
    @pytest.fixture
    def target_ign(self):
        """Target player IGN for testing"""
        return "Diary of dolls"
    
    @pytest.fixture
    def expected_results(self):
        """Expected results for validation"""
        return {
            "hero": "kagura",
            "kda": {"k": 9, "d": 2, "a": 12},
            "mvp_score": 10.5,
            "player_located": True,
            "min_confidence": 0.85,
            "min_completeness": 0.85
        }
    
    def test_end_to_end_ocr_pipeline(self, kda_image_path, damage_image_path, target_ign, expected_results):
        """T013-1: Complete end-to-end OCR pipeline test"""
        start_time = time.time()
        
        # Load test images
        kda_image = cv2.imread(kda_image_path)
        damage_image = cv2.imread(damage_image_path)
        
        assert kda_image is not None, f"Failed to load KDA image: {kda_image_path}"
        assert damage_image is not None, f"Failed to load Damage image: {damage_image_path}"
        
        # Step 1: Process KDA view
        print(f"\n🔍 Processing KDA view for '{target_ign}'")
        kda_start = time.time()
        
        kda_result = parse_kda_view_v2(kda_image, target_ign)
        
        kda_time = (time.time() - kda_start) * 1000
        print(f"KDA processing: {kda_time:.1f}ms")
        
        # Validate KDA results
        assert kda_result is not None, "KDA parsing returned None"
        assert hasattr(kda_result, 'kda'), "KDA result missing kda field"
        assert hasattr(kda_result, 'confidence'), "KDA result missing confidence field"
        
        # Step 2: Process Damage view
        print(f"🔍 Processing Damage view for '{target_ign}'")
        damage_start = time.time()
        
        # First detect player row in damage view
        damage_row = detect_player_row_fuzzy(damage_image, target_ign)
        damage_result = None
        
        if damage_row >= 0:
            damage_result = parse_damage_view(damage_image, damage_row, target_ign)
        
        damage_time = (time.time() - damage_start) * 1000
        print(f"Damage processing: {damage_time:.1f}ms")
        
        # Step 3: Fuse results from both views
        print(f"🔄 Fusing cross-view data")
        fusion_start = time.time()
        
        fused_result = fuse_cross_view_data(kda_result, damage_result, target_ign)
        
        fusion_time = (time.time() - fusion_start) * 1000
        print(f"Fusion processing: {fusion_time:.1f}ms")
        
        # Calculate total processing time
        total_time = (time.time() - start_time) * 1000
        print(f"Total processing: {total_time:.1f}ms")
        
        # Step 4: Validate results against expectations
        self._validate_pipeline_results(fused_result, expected_results)
        
        # Step 5: Performance validation
        assert total_time < 5000, f"Total processing time {total_time:.1f}ms exceeds 5s limit"
        print(f"✅ Performance: {total_time:.1f}ms (within limits)")
        
        # Step 6: Print detailed results for verification
        self._print_detailed_results(fused_result, kda_time, damage_time, fusion_time, total_time)
    
    def test_kda_only_pipeline(self, kda_image_path, target_ign, expected_results):
        """T013-2: Pipeline with only KDA view (fallback scenario)"""
        kda_image = cv2.imread(kda_image_path)
        
        # Process only KDA view
        kda_result = parse_kda_view_v2(kda_image, target_ign)
        
        # Fuse with None damage result (single view scenario)
        fused_result = fuse_cross_view_data(kda_result, None, target_ign)
        
        # Should still work but with reduced completeness
        assert fused_result.player_located is True, "Player should be located from KDA view"
        assert fused_result.hero == expected_results["hero"], f"Hero mismatch: {fused_result.hero}"
        assert fused_result.kda is not None, "KDA data should be available"
        assert fused_result.data_completeness < 0.85, "Completeness should be reduced for single view"
        assert "Damage data missing" in fused_result.warnings, "Should warn about missing damage data"
    
    def test_damage_only_pipeline(self, damage_image_path, target_ign):
        """T013-3: Pipeline with only Damage view (fallback scenario)"""
        damage_image = cv2.imread(damage_image_path)
        
        # Detect player and process damage view
        damage_row = detect_player_row_fuzzy(damage_image, target_ign)
        damage_result = None
        
        if damage_row >= 0:
            damage_result = parse_damage_view(damage_image, damage_row, target_ign)
        
        # Fuse with None KDA result (single view scenario)
        fused_result = fuse_cross_view_data(None, damage_result, target_ign)
        
        if damage_result:
            # Should work but with reduced completeness
            assert fused_result.player_located is True, "Player should be located from Damage view"
            assert fused_result.damage_stats is not None, "Damage stats should be available"
            assert fused_result.kda is None, "KDA should be None (not available from damage view)"
            assert fused_result.data_completeness < 0.85, "Completeness should be reduced for single view"
            assert "KDA data missing" in fused_result.warnings, "Should warn about missing KDA data"
    
    def test_pipeline_error_handling(self, target_ign):
        """T013-4: Pipeline error handling with invalid inputs"""
        # Test with None images
        kda_result = parse_kda_view_v2(None, target_ign)
        assert kda_result is not None, "Should handle None image gracefully"
        
        # Test with empty target IGN
        kda_image = cv2.imread("backend/tests/fixtures/IMG_1767.PNG")
        kda_result = parse_kda_view_v2(kda_image, "")
        assert kda_result is not None, "Should handle empty IGN gracefully"
        
        # Test fusion with both None results
        fused_result = fuse_cross_view_data(None, None, target_ign)
        assert fused_result.player_located is False, "Should indicate no player found"
        assert fused_result.overall_confidence < 0.5, "Should have low confidence"
        assert len(fused_result.warnings) > 0, "Should have warnings for no data"
    
    def test_pipeline_performance_benchmarking(self, kda_image_path, damage_image_path, target_ign):
        """T013-5: Performance benchmarking across multiple runs"""
        processing_times = []
        
        # Run multiple iterations for consistent timing
        for i in range(3):
            start_time = time.time()
            
            # Load images
            kda_image = cv2.imread(kda_image_path)
            damage_image = cv2.imread(damage_image_path)
            
            # Process both views
            kda_result = parse_kda_view_v2(kda_image, target_ign)
            damage_row = detect_player_row_fuzzy(damage_image, target_ign)
            damage_result = parse_damage_view(damage_image, damage_row, target_ign) if damage_row >= 0 else None
            
            # Fuse results
            fused_result = fuse_cross_view_data(kda_result, damage_result, target_ign)
            
            processing_time = (time.time() - start_time) * 1000
            processing_times.append(processing_time)
            
            print(f"Run {i+1}: {processing_time:.1f}ms")
        
        # Calculate performance statistics
        avg_time = sum(processing_times) / len(processing_times)
        max_time = max(processing_times)
        min_time = min(processing_times)
        
        print(f"\nPerformance Summary:")
        print(f"Average: {avg_time:.1f}ms")
        print(f"Min: {min_time:.1f}ms")
        print(f"Max: {max_time:.1f}ms")
        
        # Validate performance requirements
        assert avg_time < 3000, f"Average processing time {avg_time:.1f}ms exceeds 3s target"
        assert max_time < 5000, f"Max processing time {max_time:.1f}ms exceeds 5s limit"
        
        print(f"✅ Performance requirements met")
    
    def _validate_pipeline_results(self, result: Any, expected: Dict[str, Any]):
        """Validate pipeline results against expected outcomes"""
        # Player detection
        assert result.player_located == expected["player_located"], \
            f"Player location: expected {expected['player_located']}, got {result.player_located}"
        
        # Hero identification
        if expected.get("hero"):
            assert result.hero == expected["hero"], \
                f"Hero: expected {expected['hero']}, got {result.hero}"
        
        # KDA values
        if expected.get("kda") and result.kda:
            exp_kda = expected["kda"]
            assert result.kda["k"] == exp_kda["k"], f"Kills: expected {exp_kda['k']}, got {result.kda['k']}"
            assert result.kda["d"] == exp_kda["d"], f"Deaths: expected {exp_kda['d']}, got {result.kda['d']}"
            assert result.kda["a"] == exp_kda["a"], f"Assists: expected {exp_kda['a']}, got {result.kda['a']}"
        
        # MVP score (approximate match)
        if expected.get("mvp_score") and result.mvp_score:
            assert abs(result.mvp_score - expected["mvp_score"]) < 1.0, \
                f"MVP Score: expected ~{expected['mvp_score']}, got {result.mvp_score}"
        
        # Quality metrics
        if expected.get("min_confidence"):
            assert result.overall_confidence >= expected["min_confidence"], \
                f"Confidence: expected >={expected['min_confidence']}, got {result.overall_confidence}"
        
        if expected.get("min_completeness"):
            assert result.data_completeness >= expected["min_completeness"], \
                f"Completeness: expected >={expected['min_completeness']}, got {result.data_completeness}"
        
        print("✅ All validation criteria met")
    
    def _print_detailed_results(self, result: Any, kda_time: float, damage_time: float, fusion_time: float, total_time: float):
        """Print detailed results for verification"""
        print("\n📊 Detailed Pipeline Results:")
        print(f"  Player Located: {result.player_located}")
        print(f"  Player IGN: {result.player_ign}")
        print(f"  Hero: {result.hero}")
        
        if result.kda:
            print(f"  KDA: {result.kda['k']}/{result.kda['d']}/{result.kda['a']}")
        
        if result.mvp_score:
            print(f"  MVP Score: {result.mvp_score}")
        
        if result.damage_stats:
            print(f"  Damage Stats: {result.damage_stats}")
        
        print(f"  Overall Confidence: {result.overall_confidence:.3f}")
        print(f"  Data Completeness: {result.data_completeness:.3f}")
        
        if result.warnings:
            print(f"  Warnings: {result.warnings}")
        
        if result.conflicts:
            print(f"  Conflicts: {len(result.conflicts)} detected")
        
        print(f"\n⏱️ Performance Breakdown:")
        print(f"  KDA Processing: {kda_time:.1f}ms")
        print(f"  Damage Processing: {damage_time:.1f}ms")
        print(f"  Fusion Processing: {fusion_time:.1f}ms")
        print(f"  Total Time: {total_time:.1f}ms")