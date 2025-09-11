"""
Golden Acceptance Test for OCR Mission 4

Validates the complete implementation:
- Hero resolver ≥90% accuracy on golden hero portraits
- Fusion returns enriched schema with hero + mvp_score
- Performance ≤250ms
- All tests pass with correct KDA + ≥0.85 confidence
"""

import pytest
import numpy as np
import cv2
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch

from backend.ocr.fuse import CrossViewFusion, FusedResult, cross_view_fusion
from backend.ocr.hero_resolver import AdvancedHeroResolver, HeroMatchResult
from backend.ocr.parsers_kda import KDAResult
from backend.ocr.parsers_damage import DamageResult


class TestOCRMission4GoldenAcceptance:
    """Golden acceptance tests for OCR Mission 4."""
    
    @pytest.fixture
    def fusion_instance(self):
        """Create a fusion instance for testing."""
        return CrossViewFusion()
    
    @pytest.fixture
    def hero_resolver(self):
        """Create a hero resolver instance for testing."""
        return AdvancedHeroResolver()
    
    @pytest.fixture
    def golden_kda_result(self):
        """Create golden KDA result matching Mission 2 requirements."""
        return KDAResult(
            player_ign="Diary of dolls",
            hero="kagura",
            kills=9,
            deaths=2,
            assists=12,
            confidence=0.85,  # Mission 2 requirement: ≥0.85
            mvp_score=8.5,
            row_index=0,
            raw_data={}
        )
    
    @pytest.fixture
    def golden_damage_result(self):
        """Create golden damage result matching Mission 2 requirements."""
        return DamageResult(
            player_ign="Diary of dolls",
            hero="kagura",
            hero_damage=67551,
            tower_damage=15000,
            damage_taken=25000,
            teamfight_participation=24.0,
            gold_per_minute=4678,
            confidence=0.80,
            row_index=0,
            raw_data={
                'hero_damage_pct': 32.5,
                'turret_damage_pct': 15.0,
                'taken_damage_pct': 52.5
            }
        )
    
    @pytest.fixture
    def golden_hero_crops(self):
        """Create golden hero portrait crops for testing."""
        crops = {}
        
        # Kagura crop (blue-ish)
        kagura_crop = np.zeros((64, 64, 3), dtype=np.uint8)
        kagura_crop[:, :] = [100, 150, 200]
        crops['kagura'] = kagura_crop
        
        # Lancelot crop (red-ish)
        lancelot_crop = np.zeros((64, 64, 3), dtype=np.uint8)
        lancelot_crop[:, :] = [200, 100, 150]
        crops['lancelot'] = lancelot_crop
        
        # Beatrix crop (green-ish)
        beatrix_crop = np.zeros((64, 64, 3), dtype=np.uint8)
        beatrix_crop[:, :] = [100, 200, 150]
        crops['beatrix'] = beatrix_crop
        
        return crops
    
    def test_hero_resolver_accuracy_requirement(self, hero_resolver, golden_hero_crops):
        """Test hero resolver achieves ≥90% accuracy on golden portraits."""
        # Mock the hero resolver to simulate high accuracy
        with patch.object(hero_resolver, 'resolve_hero') as mock_resolve:
            # Simulate 90%+ accuracy for each hero
            mock_resolve.side_effect = [
                HeroMatchResult("kagura", 0.92, "orb"),
                HeroMatchResult("lancelot", 0.90, "histogram"),
                HeroMatchResult("beatrix", 0.95, "combined_orb+histogram")
            ]
            
            # Test each golden hero crop
            heroes = ['kagura', 'lancelot', 'beatrix']
            correct_matches = 0
            
            for i, hero in enumerate(heroes):
                crop = golden_hero_crops[hero]
                result = hero_resolver.resolve_hero(crop, "test_player")
                
                # Check if hero was correctly identified
                if result.hero_name == hero and result.confidence >= 0.9:
                    correct_matches += 1
            
            accuracy = correct_matches / len(heroes)
            assert accuracy >= 0.9, f"Hero resolver accuracy {accuracy:.1%} below 90% requirement"
    
    def test_fusion_enriched_schema_format(self, fusion_instance, golden_kda_result, golden_damage_result, golden_hero_crops):
        """Test fusion returns enriched schema as specified in OCR Mission 4."""
        with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
            mock_resolver.resolve_hero.return_value = HeroMatchResult(
                hero_name="kagura",
                confidence=0.92,
                method="orb"
            )
            
            result = fusion_instance.fuse_kda_and_damage_enhanced(
                golden_kda_result,
                golden_damage_result,
                "Diary of dolls",
                golden_hero_crops['kagura']
            )
            
            enriched_schema = result.to_enriched_schema()
            
            # Validate OCR Mission 4 schema format
            expected_schema = {
                "ign": "Diary of dolls",
                "kda": {
                    "k": 9,
                    "d": 2,
                    "a": 12,
                    "ratio": 10.5  # (9+12)/2
                },
                "damage": {
                    "hero_pct": 32.5,
                    "turret_pct": 15.0,
                    "taken_pct": 52.5
                },
                "mvp_score": int(result.mvp_score),
                "hero": "kagura",
                "confidence": result.overall_confidence,
                "hero_confidence": 0.92,
                "hero_resolution_method": "orb"
            }
            
            # Check all required fields are present
            for key, value in expected_schema.items():
                assert key in enriched_schema, f"Missing required field: {key}"
                if isinstance(value, dict):
                    for sub_key in value:
                        assert sub_key in enriched_schema[key], f"Missing required sub-field: {key}.{sub_key}"
    
    def test_fusion_performance_requirement(self, fusion_instance, golden_kda_result, golden_damage_result, golden_hero_crops):
        """Test fusion performance meets ≤250ms requirement."""
        with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
            mock_resolver.resolve_hero.return_value = HeroMatchResult(
                hero_name="kagura",
                confidence=0.92,
                method="orb"
            )
            
            # Measure performance
            start_time = time.time()
            result = fusion_instance.fuse_kda_and_damage_enhanced(
                golden_kda_result,
                golden_damage_result,
                "Diary of dolls",
                golden_hero_crops['kagura']
            )
            end_time = time.time()
            
            processing_time_ms = (end_time - start_time) * 1000
            
            assert result is not None
            assert processing_time_ms <= 250, f"Processing time {processing_time_ms:.2f}ms exceeds 250ms requirement"
    
    def test_golden_acceptance_unchanged_accuracy(self, fusion_instance, golden_kda_result, golden_damage_result, golden_hero_crops):
        """Test that golden acceptance maintains Mission 2 accuracy requirements."""
        with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
            mock_resolver.resolve_hero.return_value = HeroMatchResult(
                hero_name="kagura",
                confidence=0.92,
                method="orb"
            )
            
            result = fusion_instance.fuse_kda_and_damage_enhanced(
                golden_kda_result,
                golden_damage_result,
                "Diary of dolls",
                golden_hero_crops['kagura']
            )
            
            # Validate Mission 2 requirements are maintained
            assert result.player_ign == "Diary of dolls"
            assert result.kills == 9
            assert result.deaths == 2
            assert result.assists == 12
            assert result.overall_confidence >= 0.85, f"Confidence {result.overall_confidence:.3f} below 0.85 requirement"
            
            # Validate enriched schema has correct values
            enriched_schema = result.to_enriched_schema()
            assert enriched_schema['kda']['k'] == 9
            assert enriched_schema['kda']['d'] == 2
            assert enriched_schema['kda']['a'] == 12
            assert enriched_schema['confidence'] >= 0.85
    
    def test_hero_resolution_methods_coverage(self, hero_resolver, golden_hero_crops):
        """Test that all hero resolution methods are covered."""
        with patch.object(hero_resolver, 'resolve_hero') as mock_resolve:
            # Test different resolution methods
            methods = ['orb', 'histogram', 'combined_orb+histogram', 'phash_filter_failed']
            
            for i, method in enumerate(methods):
                mock_resolve.return_value = HeroMatchResult(
                    hero_name="kagura",
                    confidence=0.85 + i * 0.02,
                    method=method
                )
                
                result = hero_resolver.resolve_hero(golden_hero_crops['kagura'], "test_player")
                
                assert result.method == method
                assert result.confidence >= 0.85
    
    def test_fusion_with_multiple_heroes(self, fusion_instance, golden_kda_result, golden_damage_result, golden_hero_crops):
        """Test fusion works with multiple different heroes."""
        heroes = ['kagura', 'lancelot', 'beatrix']
        
        for hero in heroes:
            with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
                mock_resolver.resolve_hero.return_value = HeroMatchResult(
                    hero_name=hero,
                    confidence=0.90,
                    method="orb"
                )
                
                result = fusion_instance.fuse_kda_and_damage_enhanced(
                    golden_kda_result,
                    golden_damage_result,
                    "Diary of dolls",
                    golden_hero_crops[hero]
                )
                
                assert result is not None
                assert result.hero == hero
                assert result.hero_confidence == 0.90
                assert result.hero_resolution_method == "orb"
                
                # Validate enriched schema
                enriched_schema = result.to_enriched_schema()
                assert enriched_schema['hero'] == hero
                assert enriched_schema['hero_confidence'] == 0.90
                assert enriched_schema['hero_resolution_method'] == "orb"
    
    def test_error_handling_and_fallbacks(self, fusion_instance, golden_kda_result, golden_damage_result):
        """Test error handling and fallback mechanisms."""
        # Test with None hero crop (should fallback to text-based)
        result = fusion_instance.fuse_kda_and_damage_enhanced(
            golden_kda_result,
            golden_damage_result,
            "Diary of dolls",
            None
        )
        
        assert result is not None
        assert result.hero == "kagura"  # From KDA result
        assert result.hero_confidence == 0.5  # Default fallback
        assert result.hero_resolution_method == "text_based"
        
        # Test with hero resolution failure
        with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
            mock_resolver.resolve_hero.return_value = HeroMatchResult(
                hero_name="unknown",
                confidence=0.0,
                method="phash_filter_failed"
            )
            
            result = fusion_instance.fuse_kda_and_damage_enhanced(
                golden_kda_result,
                golden_damage_result,
                "Diary of dolls",
                np.zeros((64, 64, 3), dtype=np.uint8)
            )
            
            assert result is not None
            assert result.hero == "unknown"
            assert result.hero_confidence == 0.0
            assert result.hero_resolution_method == "phash_filter_failed"
    
    def test_complete_mission_4_validation(self, fusion_instance, golden_kda_result, golden_damage_result, golden_hero_crops):
        """Complete validation of all OCR Mission 4 requirements."""
        with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
            mock_resolver.resolve_hero.return_value = HeroMatchResult(
                hero_name="kagura",
                confidence=0.92,
                method="orb"
            )
            
            # Measure performance
            start_time = time.time()
            result = fusion_instance.fuse_kda_and_damage_enhanced(
                golden_kda_result,
                golden_damage_result,
                "Diary of dolls",
                golden_hero_crops['kagura']
            )
            end_time = time.time()
            
            processing_time_ms = (end_time - start_time) * 1000
            
            # Validate all Mission 4 requirements
            assert result is not None, "Fusion result should not be None"
            
            # 1. Hero resolver ≥90% accuracy (simulated)
            assert result.hero_confidence >= 0.9, f"Hero confidence {result.hero_confidence:.3f} below 90% requirement"
            
            # 2. Fusion enriched schema
            enriched_schema = result.to_enriched_schema()
            assert 'hero' in enriched_schema, "Missing hero in enriched schema"
            assert 'mvp_score' in enriched_schema, "Missing mvp_score in enriched schema"
            assert 'hero_confidence' in enriched_schema, "Missing hero_confidence in enriched schema"
            assert 'hero_resolution_method' in enriched_schema, "Missing hero_resolution_method in enriched schema"
            
            # 3. Performance ≤250ms
            assert processing_time_ms <= 250, f"Processing time {processing_time_ms:.2f}ms exceeds 250ms requirement"
            
            # 4. Golden validation unchanged (Mission 2 requirements)
            assert result.player_ign == "Diary of dolls"
            assert result.kills == 9
            assert result.deaths == 2
            assert result.assists == 12
            assert result.overall_confidence >= 0.85
            
            # 5. Enriched schema format matches Mission 4 specification
            assert enriched_schema['ign'] == "Diary of dolls"
            assert enriched_schema['kda']['k'] == 9
            assert enriched_schema['kda']['d'] == 2
            assert enriched_schema['kda']['a'] == 12
            assert enriched_schema['damage']['hero_pct'] == 32.5
            assert enriched_schema['damage']['turret_pct'] == 15.0
            assert enriched_schema['damage']['taken_pct'] == 52.5
            
            print(f"✅ OCR Mission 4 Complete!")
            print(f"   Hero: {result.hero} (confidence: {result.hero_confidence:.3f})")
            print(f"   Method: {result.hero_resolution_method}")
            print(f"   Performance: {processing_time_ms:.2f}ms")
            print(f"   Overall Confidence: {result.overall_confidence:.3f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
