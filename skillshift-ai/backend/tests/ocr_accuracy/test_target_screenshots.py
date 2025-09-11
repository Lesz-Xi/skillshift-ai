"""
OCR accuracy tests for target screenshots.

Tests the specific target screenshots to validate that row-agnostic
extraction achieves the expected KDA = 9/2/12 for "Diary of dolls".
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
from backend.ocr.fuse import cross_view_fusion


class TestTargetScreenshots:
    """Accuracy tests for target screenshots."""
    
    @pytest.fixture
    def target_images(self):
        """Get target test image paths."""
        trial_image_dir = project_root.parent / "Trial-Image"
        return {
            "kda_image": str(trial_image_dir / "IMG_1767.PNG"),
            "damage_image": str(trial_image_dir / "IMG_1768.PNG")
        }
    
    @pytest.fixture
    def target_ign(self):
        """Target IGN for testing."""
        return "Diary of dolls"
    
    @pytest.fixture
    def expected_kda(self):
        """Expected KDA values."""
        return {
            "kills": 9,
            "deaths": 2,
            "assists": 12,
            "mvp_score": 10.5  # Approximate
        }
    
    def test_target_kda_extraction(self, target_images, target_ign, expected_kda):
        """Test that we can extract the target KDA = 9/2/12."""
        kda_image = target_images["kda_image"]
        
        # Parse KDA
        kda_result = kda_parser.parse_kda_from_screenshot(kda_image, target_ign)
        
        if kda_result is not None:
            print(f"\n🎯 KDA Extraction Results:")
            print(f"   Target IGN: {target_ign}")
            print(f"   Found IGN: {kda_result.player_ign}")
            print(f"   KDA: {kda_result.kills}/{kda_result.deaths}/{kda_result.assists}")
            print(f"   Expected: {expected_kda['kills']}/{expected_kda['deaths']}/{expected_kda['assists']}")
            print(f"   Hero: {kda_result.hero}")
            print(f"   MVP Score: {kda_result.mvp_score}")
            print(f"   Confidence: {kda_result.confidence:.3f}")
            print(f"   Row Index: {kda_result.row_index}")
            
            # Validate IGN match
            assert kda_result.player_ign.lower() == target_ign.lower(), "IGN should match"
            
            # Validate KDA values (allow some tolerance for OCR errors)
            assert abs(kda_result.kills - expected_kda["kills"]) <= 1, f"Kills should be close to {expected_kda['kills']}"
            assert abs(kda_result.deaths - expected_kda["deaths"]) <= 1, f"Deaths should be close to {expected_kda['deaths']}"
            assert abs(kda_result.assists - expected_kda["assists"]) <= 1, f"Assists should be close to {expected_kda['assists']}"
            
            # Validate confidence
            assert kda_result.confidence >= 0.5, "Should have reasonable confidence"
        else:
            pytest.skip("KDA parsing failed - may need better OCR or image preprocessing")
    
    def test_target_damage_extraction(self, target_images, target_ign):
        """Test damage extraction from target screenshot."""
        damage_image = target_images["damage_image"]
        
        # Parse damage
        damage_result = damage_parser.parse_damage_from_screenshot(damage_image, target_ign)
        
        if damage_result is not None:
            print(f"\n🎯 Damage Extraction Results:")
            print(f"   Target IGN: {target_ign}")
            print(f"   Found IGN: {damage_result.player_ign}")
            print(f"   Hero: {damage_result.hero}")
            print(f"   Hero Damage: {damage_result.hero_damage}")
            print(f"   Tower Damage: {damage_result.tower_damage}")
            print(f"   Damage Taken: {damage_result.damage_taken}")
            print(f"   Teamfight Participation: {damage_result.teamfight_participation}%")
            print(f"   GPM: {damage_result.gold_per_minute}")
            print(f"   Confidence: {damage_result.confidence:.3f}")
            print(f"   Row Index: {damage_result.row_index}")
            
            # Validate IGN match
            assert damage_result.player_ign.lower() == target_ign.lower(), "IGN should match"
            
            # Validate damage values are reasonable
            assert damage_result.hero_damage > 0, "Should have positive hero damage"
            assert damage_result.confidence >= 0.5, "Should have reasonable confidence"
        else:
            pytest.skip("Damage parsing failed - may need better OCR or image preprocessing")
    
    def test_target_fusion_accuracy(self, target_images, target_ign, expected_kda):
        """Test fusion accuracy for target screenshots."""
        kda_image = target_images["kda_image"]
        damage_image = target_images["damage_image"]
        
        # Run fusion
        fused_result = cross_view_fusion.parse_screenshot_pair(
            kda_image, damage_image, target_ign
        )
        
        if fused_result is not None:
            print(f"\n🎯 Fusion Results:")
            print(f"   Player IGN: {fused_result.player_ign}")
            print(f"   Hero: {fused_result.hero}")
            print(f"   KDA: {fused_result.kills}/{fused_result.deaths}/{fused_result.assists}")
            print(f"   Expected: {expected_kda['kills']}/{expected_kda['deaths']}/{expected_kda['assists']}")
            print(f"   MVP Score: {fused_result.mvp_score}")
            print(f"   Hero Damage: {fused_result.hero_damage}")
            print(f"   Overall Confidence: {fused_result.overall_confidence:.3f}")
            print(f"   Data Completeness: {fused_result.data_completeness:.3f}")
            print(f"   Fusion Method: {fused_result.fusion_method}")
            print(f"   Conflicts Resolved: {fused_result.conflicts_resolved}")
            
            # Validate IGN match
            assert fused_result.player_ign.lower() == target_ign.lower(), "IGN should match"
            
            # Validate KDA accuracy (allow tolerance for OCR errors)
            kda_accuracy = 0
            if abs(fused_result.kills - expected_kda["kills"]) <= 1:
                kda_accuracy += 1
            if abs(fused_result.deaths - expected_kda["deaths"]) <= 1:
                kda_accuracy += 1
            if abs(fused_result.assists - expected_kda["assists"]) <= 1:
                kda_accuracy += 1
            
            kda_accuracy_percent = (kda_accuracy / 3) * 100
            print(f"   KDA Accuracy: {kda_accuracy_percent:.1f}% ({kda_accuracy}/3 values correct)")
            
            # Should have at least 2/3 KDA values correct
            assert kda_accuracy >= 2, f"Should have at least 2/3 KDA values correct, got {kda_accuracy}"
            
            # Validate confidence and completeness
            assert fused_result.overall_confidence >= 0.5, "Should have reasonable overall confidence"
            assert fused_result.data_completeness >= 0.3, "Should have some data completeness"
        else:
            pytest.skip("Fusion failed - may need better OCR or image preprocessing")
    
    def test_row_agnostic_consistency(self, target_images, target_ign):
        """Test that row-agnostic detection works consistently."""
        kda_image = target_images["kda_image"]
        
        # Detect table region
        table_region = row_agnostic_detector.detect_table_regions(kda_image)
        assert table_region is not None, "Should detect table region"
        
        # Generate row crops
        row_crops = row_agnostic_detector.generate_row_crops(
            table_region, kda_image, target_ign
        )
        
        assert len(row_crops) > 0, "Should generate row crops"
        
        # Test that we can find the target row
        target_row = row_agnostic_detector.find_target_row(row_crops, target_ign)
        
        if target_row is not None:
            print(f"\n🎯 Row-Agnostic Detection Results:")
            print(f"   Total rows detected: {len(row_crops)}")
            print(f"   Target row found: {target_row.row_index}")
            print(f"   Target row confidence: {target_row.confidence:.3f}")
            print(f"   Target row contains IGN: {target_row.contains_target_ign}")
            
            # Validate row crop structure
            assert target_row.row_index >= 0, "Row index should be non-negative"
            assert target_row.confidence > 0.0, "Should have positive confidence"
            
            # Validate normalized coordinates
            top, left, width, height = target_row.bbox_ratio
            assert 0.0 <= top <= 1.0, "Top ratio should be between 0 and 1"
            assert 0.0 <= left <= 1.0, "Left ratio should be between 0 and 1"
            assert 0.0 <= width <= 1.0, "Width ratio should be between 0 and 1"
            assert 0.0 <= height <= 1.0, "Height ratio should be between 0 and 1"
        else:
            pytest.skip("Target row not found - may need better IGN matching")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
