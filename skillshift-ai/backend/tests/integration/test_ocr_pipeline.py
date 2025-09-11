"""
Integration tests for row-agnostic OCR pipeline.

Tests the complete OCR pipeline from image input to parsed data output,
validating that row-agnostic detection works correctly.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.ocr.detectors import row_agnostic_detector
from backend.ocr.parsers_kda import kda_parser
from backend.ocr.parsers_damage import damage_parser
from backend.ocr.fuse import CrossViewFusion


class TestOCRIntegration:
    """Integration tests for OCR pipeline."""
    
    @pytest.fixture
    def test_images(self):
        """Get test image paths."""
        trial_image_dir = project_root.parent / "Trial-Image"
        return {
            "kda_image": str(trial_image_dir / "IMG_1767.PNG"),
            "damage_image": str(trial_image_dir / "IMG_1768.PNG")
        }
    
    @pytest.fixture
    def fusion_instance(self):
        """Get CrossViewFusion instance."""
        return CrossViewFusion()
    
    def test_table_detection_integration(self, test_images):
        """Test table detection works with real images."""
        kda_image = test_images["kda_image"]
        
        # Test table detection
        table_region = row_agnostic_detector.detect_table_regions(kda_image)
        
        assert table_region is not None, "Table region should be detected"
        assert table_region.confidence > 0.0, "Table region should have confidence > 0"
        assert table_region.rows_count > 0, "Should detect at least one row"
        assert len(table_region.panel_bbox) == 4, "Panel bbox should have 4 coordinates"
        
        # Validate normalized coordinates
        top, left, width, height = table_region.panel_bbox
        assert 0.0 <= top <= 1.0, "Top ratio should be between 0 and 1"
        assert 0.0 <= left <= 1.0, "Left ratio should be between 0 and 1"
        assert 0.0 <= width <= 1.0, "Width ratio should be between 0 and 1"
        assert 0.0 <= height <= 1.0, "Height ratio should be between 0 and 1"
    
    def test_row_crop_generation_integration(self, test_images):
        """Test row crop generation works with real images."""
        kda_image = test_images["kda_image"]
        
        # Detect table first
        table_region = row_agnostic_detector.detect_table_regions(kda_image)
        assert table_region is not None, "Table region should be detected"
        
        # Generate row crops
        row_crops = row_agnostic_detector.generate_row_crops(
            table_region, kda_image, "Diary of dolls"
        )
        
        assert len(row_crops) > 0, "Should generate at least one row crop"
        assert len(row_crops) <= table_region.rows_count, "Should not exceed expected row count"
        
        # Validate row crop structure
        for i, row_crop in enumerate(row_crops):
            assert row_crop.row_index == i, f"Row index should match position {i}"
            assert len(row_crop.bbox_ratio) == 4, "Bbox ratio should have 4 coordinates"
            assert len(row_crop.absolute_bbox) == 4, "Absolute bbox should have 4 coordinates"
    
    def test_kda_parsing_integration(self, test_images):
        """Test KDA parsing with real image."""
        kda_image = test_images["kda_image"]
        target_ign = "Diary of dolls"
        
        # Parse KDA
        kda_result = kda_parser.parse_kda_from_screenshot(kda_image, target_ign)
        
        if kda_result is not None:
            assert kda_result.player_ign == target_ign, "Should match target IGN"
            assert kda_result.confidence > 0.0, "Should have confidence > 0"
            assert kda_result.kills >= 0, "Kills should be non-negative"
            assert kda_result.deaths >= 0, "Deaths should be non-negative"
            assert kda_result.assists >= 0, "Assists should be non-negative"
            assert kda_result.mvp_score >= 0.0, "MVP score should be non-negative"
    
    def test_damage_parsing_integration(self, test_images):
        """Test damage parsing with real image."""
        damage_image = test_images["damage_image"]
        target_ign = "Diary of dolls"
        
        # Parse damage
        damage_result = damage_parser.parse_damage_from_screenshot(damage_image, target_ign)
        
        if damage_result is not None:
            assert damage_result.player_ign == target_ign, "Should match target IGN"
            assert damage_result.confidence > 0.0, "Should have confidence > 0"
            assert damage_result.hero_damage >= 0, "Hero damage should be non-negative"
            assert damage_result.tower_damage >= 0, "Tower damage should be non-negative"
            assert damage_result.damage_taken >= 0, "Damage taken should be non-negative"
    
    def test_cross_view_fusion_integration(self, test_images, fusion_instance):
        """Test cross-view fusion with real images."""
        kda_image = test_images["kda_image"]
        damage_image = test_images["damage_image"]
        target_ign = "Diary of dolls"
        
        # Parse both views
        kda_result = kda_parser.parse_kda_from_screenshot(kda_image, target_ign)
        damage_result = damage_parser.parse_damage_from_screenshot(damage_image, target_ign)
        
        # Fuse results
        fused_result = fusion_instance.fuse_kda_and_damage(kda_result, damage_result)
        
        if fused_result is not None:
            assert fused_result.player_ign == target_ign, "Should match target IGN"
            assert fused_result.overall_confidence > 0.0, "Should have overall confidence > 0"
            assert fused_result.data_completeness > 0.0, "Should have data completeness > 0"
            assert fused_result.fusion_method in ["kda_only", "damage_only", "both_views"], "Should have valid fusion method"
    
    def test_end_to_end_pipeline(self, test_images, fusion_instance):
        """Test complete end-to-end pipeline."""
        kda_image = test_images["kda_image"]
        damage_image = test_images["damage_image"]
        target_ign = "Diary of dolls"
        
        # Run complete pipeline
        fused_result = fusion_instance.parse_screenshot_pair(
            kda_image, damage_image, target_ign
        )
        
        if fused_result is not None:
            # Validate basic structure
            assert fused_result.player_ign == target_ign
            assert fused_result.overall_confidence > 0.0
            assert fused_result.data_completeness > 0.0
            
            # Log results for manual verification
            print(f"\n🎯 End-to-End Pipeline Results:")
            print(f"   Player IGN: {fused_result.player_ign}")
            print(f"   Hero: {fused_result.hero}")
            print(f"   KDA: {fused_result.kills}/{fused_result.deaths}/{fused_result.assists}")
            print(f"   MVP Score: {fused_result.mvp_score}")
            print(f"   Hero Damage: {fused_result.hero_damage}")
            print(f"   Overall Confidence: {fused_result.overall_confidence:.3f}")
            print(f"   Data Completeness: {fused_result.data_completeness:.3f}")
            print(f"   Fusion Method: {fused_result.fusion_method}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
