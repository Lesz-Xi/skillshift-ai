"""
Integration tests for OCR fusion with hero resolution (OCR Mission 4)

Tests the complete pipeline from hero resolution to enriched schema generation.
"""

import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch
import tempfile
import json

from backend.ocr.fuse import CrossViewFusion, FusedResult, cross_view_fusion
from backend.ocr.hero_resolver import AdvancedHeroResolver, HeroMatchResult
from backend.ocr.parsers_kda import KDAResult
from backend.ocr.parsers_damage import DamageResult


class TestFusionHeroResolutionIntegration:
    """Integration tests for fusion with hero resolution."""
    
    @pytest.fixture
    def fusion_instance(self):
        """Create a fusion instance for testing."""
        return CrossViewFusion()
    
    @pytest.fixture
    def mock_kda_result(self):
        """Create a mock KDA result."""
        return KDAResult(
            player_ign="Diary of dolls",
            hero="kagura",
            kills=9,
            deaths=2,
            assists=12,
            confidence=0.85,
            mvp_score=8.5,
            row_index=0,
            raw_data={}
        )
    
    @pytest.fixture
    def mock_damage_result(self):
        """Create a mock damage result."""
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
    def mock_hero_crop(self):
        """Create a mock hero crop image."""
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        img[:, :] = [100, 150, 200]  # Blue-ish color
        return img
    
    def test_fusion_with_hero_resolution(self, fusion_instance, mock_kda_result, mock_damage_result, mock_hero_crop):
        """Test fusion with hero resolution integration."""
        # Mock the hero resolver
        with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
            mock_resolver.resolve_hero.return_value = HeroMatchResult(
                hero_name="kagura",
                confidence=0.92,
                method="orb",
                phash_distance=3,
                orb_matches=18,
                histogram_similarity=0.88
            )
            
            result = fusion_instance.fuse_kda_and_damage_enhanced(
                mock_kda_result, 
                mock_damage_result, 
                "Diary of dolls",
                mock_hero_crop
            )
            
            assert result is not None
            assert isinstance(result, FusedResult)
            assert result.hero == "kagura"
            assert result.hero_confidence == 0.92
            assert result.hero_resolution_method == "orb"
            assert result.player_ign == "Diary of dolls"
            assert result.kills == 9
            assert result.deaths == 2
            assert result.assists == 12
    
    def test_fusion_without_hero_crop(self, fusion_instance, mock_kda_result, mock_damage_result):
        """Test fusion without hero crop (fallback to text-based)."""
        result = fusion_instance.fuse_kda_and_damage_enhanced(
            mock_kda_result, 
            mock_damage_result, 
            "Diary of dolls",
            None  # No hero crop
        )
        
        assert result is not None
        assert isinstance(result, FusedResult)
        assert result.hero == "kagura"  # From KDA result
        assert result.hero_confidence == 0.5  # Default fallback confidence
        assert result.hero_resolution_method == "text_based"
    
    def test_fusion_with_hero_resolution_failure(self, fusion_instance, mock_kda_result, mock_damage_result, mock_hero_crop):
        """Test fusion when hero resolution fails."""
        # Mock the hero resolver to return unknown
        with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
            mock_resolver.resolve_hero.return_value = HeroMatchResult(
                hero_name="unknown",
                confidence=0.0,
                method="phash_filter_failed"
            )
            
            result = fusion_instance.fuse_kda_and_damage_enhanced(
                mock_kda_result, 
                mock_damage_result, 
                "Diary of dolls",
                mock_hero_crop
            )
            
            assert result is not None
            assert result.hero == "unknown"
            assert result.hero_confidence == 0.0
            assert result.hero_resolution_method == "phash_filter_failed"
    
    def test_enriched_schema_generation(self, fusion_instance, mock_kda_result, mock_damage_result, mock_hero_crop):
        """Test enriched schema generation with hero resolution."""
        with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
            mock_resolver.resolve_hero.return_value = HeroMatchResult(
                hero_name="kagura",
                confidence=0.90,
                method="combined_orb+histogram"
            )
            
            result = fusion_instance.fuse_kda_and_damage_enhanced(
                mock_kda_result, 
                mock_damage_result, 
                "Diary of dolls",
                mock_hero_crop
            )
            
            enriched_schema = result.to_enriched_schema()
            
            # Check OCR Mission 4 schema format
            assert enriched_schema['ign'] == "Diary of dolls"
            assert enriched_schema['hero'] == "kagura"
            assert enriched_schema['hero_confidence'] == 0.90
            assert enriched_schema['hero_resolution_method'] == "combined_orb+histogram"
            assert enriched_schema['mvp_score'] == int(result.mvp_score)
            
            # Check KDA structure
            assert 'kda' in enriched_schema
            assert enriched_schema['kda']['k'] == 9
            assert enriched_schema['kda']['d'] == 2
            assert enriched_schema['kda']['a'] == 12
            assert enriched_schema['kda']['ratio'] == result.kda_ratio
            
            # Check damage structure
            assert 'damage' in enriched_schema
            assert enriched_schema['damage']['hero_pct'] == 32.5
            assert enriched_schema['damage']['turret_pct'] == 15.0
            assert enriched_schema['damage']['taken_pct'] == 52.5
    
    def test_standalone_cross_view_fusion_with_hero(self, mock_kda_result, mock_damage_result, mock_hero_crop):
        """Test standalone cross_view_fusion function with hero resolution."""
        with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
            mock_resolver.resolve_hero.return_value = HeroMatchResult(
                hero_name="lancelot",
                confidence=0.88,
                method="orb"
            )
            
            result = cross_view_fusion(mock_kda_result, mock_damage_result, mock_hero_crop)
            
            assert result is not None
            assert isinstance(result, FusedResult)
            assert result.hero == "lancelot"
            assert result.hero_confidence == 0.88
            assert result.hero_resolution_method == "orb"
    
    def test_standalone_cross_view_fusion_without_hero(self, mock_kda_result, mock_damage_result):
        """Test standalone cross_view_fusion function without hero resolution."""
        result = cross_view_fusion(mock_kda_result, mock_damage_result, None)
        
        assert result is not None
        assert isinstance(result, FusedResult)
        assert result.hero == "kagura"  # From KDA result
        assert result.hero_confidence == 0.5  # Default fallback
        assert result.hero_resolution_method == "text_based"
    
    def test_fusion_performance_with_hero_resolution(self, fusion_instance, mock_kda_result, mock_damage_result, mock_hero_crop):
        """Test that fusion with hero resolution meets performance requirements."""
        import time
        
        with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
            mock_resolver.resolve_hero.return_value = HeroMatchResult(
                hero_name="kagura",
                confidence=0.90,
                method="orb"
            )
            
            start_time = time.time()
            result = fusion_instance.fuse_kda_and_damage_enhanced(
                mock_kda_result, 
                mock_damage_result, 
                "Diary of dolls",
                mock_hero_crop
            )
            end_time = time.time()
            
            processing_time_ms = (end_time - start_time) * 1000
            
            assert result is not None
            # Should be well under 250ms target
            assert processing_time_ms < 250, f"Processing time {processing_time_ms:.2f}ms exceeds 250ms target"
    
    def test_raw_data_includes_hero_resolution_info(self, fusion_instance, mock_kda_result, mock_damage_result, mock_hero_crop):
        """Test that raw_data includes hero resolution information."""
        with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
            mock_resolver.resolve_hero.return_value = HeroMatchResult(
                hero_name="beatrix",
                confidence=0.85,
                method="histogram"
            )
            
            result = fusion_instance.fuse_kda_and_damage_enhanced(
                mock_kda_result, 
                mock_damage_result, 
                "Diary of dolls",
                mock_hero_crop
            )
            
            assert 'hero_resolution' in result.raw_data
            hero_resolution_info = result.raw_data['hero_resolution']
            
            assert hero_resolution_info['hero'] == "beatrix"
            assert hero_resolution_info['confidence'] == 0.85
            assert hero_resolution_info['method'] == "histogram"
    
    def test_fusion_with_missing_kda_result(self, fusion_instance, mock_damage_result, mock_hero_crop):
        """Test fusion with missing KDA result."""
        with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
            mock_resolver.resolve_hero.return_value = HeroMatchResult(
                hero_name="kagura",
                confidence=0.90,
                method="orb"
            )
            
            result = fusion_instance.fuse_kda_and_damage_enhanced(
                None,  # No KDA result
                mock_damage_result, 
                "Diary of dolls",
                mock_hero_crop
            )
            
            assert result is not None
            assert result.hero == "kagura"  # From hero resolution
            assert result.hero_confidence == 0.90
            assert result.kills == 0  # Default values
            assert result.deaths == 0
            assert result.assists == 0
    
    def test_fusion_with_missing_damage_result(self, fusion_instance, mock_kda_result, mock_hero_crop):
        """Test fusion with missing damage result."""
        with patch('backend.ocr.fuse.hero_resolver') as mock_resolver:
            mock_resolver.resolve_hero.return_value = HeroMatchResult(
                hero_name="lancelot",
                confidence=0.88,
                method="combined_orb+histogram"
            )
            
            result = fusion_instance.fuse_kda_and_damage_enhanced(
                mock_kda_result,
                None,  # No damage result
                "Diary of dolls",
                mock_hero_crop
            )
            
            assert result is not None
            assert result.hero == "lancelot"  # From hero resolution
            assert result.hero_confidence == 0.88
            assert result.hero_damage == 0  # Default values
            assert result.tower_damage == 0
            assert result.damage_taken == 0


if __name__ == "__main__":
    pytest.main([__file__])
