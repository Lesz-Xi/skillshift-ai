"""
Unit tests for enhanced OCR parsers (OCR-Mission-2.md requirements).

Tests the enhanced KDA and Damage parsers with:
- parse_from_rows methods implementation
- OCR noise handling and normalization
- ROI-specific OCR with digits-only allowlist
- Bulletproof IGN matching ("Diary of dolls" and variations)
- Enhanced confidence scoring and MVP computation
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from typing import List, Dict, Any
from dataclasses import dataclass

# Import the enhanced parsers
from backend.ocr.parsers_kda import KDAResult, RowAgnosticKDAParser
from backend.ocr.parsers_damage import DamageResult, RowAgnosticDamageParser
from backend.ocr.fuse import FusedResult, CrossViewFusion, cross_view_fusion


@dataclass
class MockRowCrop:
    """Mock RowCrop for testing."""
    row_index: int
    bbox_ratio: tuple
    absolute_bbox: tuple
    contains_target_ign: bool = False
    confidence: float = 0.0


class TestEnhancedKDAParser:
    """Test enhanced KDA parser functionality."""
    
    def setup_method(self):
        self.parser = RowAgnosticKDAParser()
        
    def test_noise_pattern_normalization(self):
        """Test OCR noise pattern normalization."""
        # Test basic noise patterns
        assert self.parser._normalize_text_for_matching("D1ary 0f dolls") == "diary of dolls"
        assert self.parser._normalize_text_for_matching("D1ary of d0lls") == "diary of dolls"
        assert self.parser._normalize_text_for_matching("DIARY OF DOLLS") == "diary of dolls"
        
    def test_advanced_noise_patterns(self):
        """Test advanced OCR noise pattern handling."""
        # Test character substitutions
        text = "D1ary 0f d0lls with S0me n01se"
        normalized = self.parser._normalize_text_for_matching(text)
        assert "diary of dolls" in normalized
        
        # Test common OCR confusions
        assert self.parser._normalize_text_for_matching("rn") == "m"
        assert self.parser._normalize_text_for_matching("vv") == "w"
        assert self.parser._normalize_text_for_matching("ii") == "n"
        assert self.parser._normalize_text_for_matching("ll") == "u"
        
    def test_kda_pattern_matching_variations(self):
        """Test KDA pattern matching with noise tolerance."""
        test_cases = [
            ("12/3/5", True),      # Standard format
            ("12|3|5", True),      # OCR noise: | instead of /
            ("12\\3\\5", True),    # OCR noise: \ instead of /
            ("12 / 3 / 5", True),  # Spaced format
            ("invalid", False),    # Invalid format
            ("12/3", False),       # Incomplete format
        ]
        
        for text, should_match in test_cases:
            # Test with enhanced extraction
            ocr_results = [(None, text, 0.8)]
            result = self.parser._extract_kda_from_ocr_enhanced(ocr_results, "testuser")
            
            if should_match:
                assert result is not None, f"Should match KDA pattern: {text}"
                assert result['kills'] == 12 and result['deaths'] == 3 and result['assists'] == 5
            else:
                assert result is None, f"Should not match KDA pattern: {text}"
    
    def test_ign_matching_golden_variations(self):
        """Test IGN matching with golden test variations."""
        target_ign = "Diary of dolls"
        
        golden_variations = [
            "Diary of dolls",      # Perfect match
            "DIARY OF DOLLS",      # Case variation
            "diary of dolls",      # Lowercase
            "D1ary of dolls",      # OCR noise (1 vs i)
            "Diary 0f dolls",      # OCR noise (0 vs o)
            "Diary  of  dolls",    # Spacing variation
            "D1ary 0f d0lls",      # Multiple OCR errors
        ]
        
        for variation in golden_variations:
            normalized_target = self.parser._normalize_text_for_matching(target_ign)
            normalized_variation = self.parser._normalize_text_for_matching(variation)
            
            # Should find the IGN in the variation
            assert normalized_target in normalized_variation or normalized_variation in normalized_target, \
                f"Failed to match IGN variation: '{variation}'"
    
    def test_enhanced_confidence_calculation(self):
        """Test enhanced confidence calculation with multiple factors."""
        # Mock OCR results with good quality
        good_ocr_results = [
            (None, "Diary of dolls", 0.9),
            (None, "12/3/5", 0.95),
            (None, "Kagura", 0.8)
        ]
        
        normalized_text = "diary of dolls 12/3/5 kagura"
        confidence = self.parser._calculate_confidence_enhanced(
            good_ocr_results, "Diary of dolls", normalized_text
        )
        
        # Should have high confidence due to:
        # - High OCR quality (0.88 avg)
        # - IGN match bonus (0.2)
        # - KDA pattern bonus (0.15)
        # - Completeness bonus (0.1)
        assert confidence >= 0.8, f"Expected high confidence, got {confidence}"
        
        # Test with poor quality OCR
        poor_ocr_results = [
            (None, "unclear text", 0.3),
            (None, "noise", 0.2)
        ]
        
        poor_confidence = self.parser._calculate_confidence_enhanced(
            poor_ocr_results, "Diary of dolls", "unclear noise"
        )
        
        assert poor_confidence < 0.5, f"Expected low confidence, got {poor_confidence}"

    def test_parse_from_rows_integration(self):
        """Test parse_from_rows method integration."""
        # Mock image and rows
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_rows = [
            MockRowCrop(
                row_index=0,
                bbox_ratio=(0.1, 0.1, 0.8, 0.2),
                absolute_bbox=(10, 10, 80, 20),
                contains_target_ign=True,
                confidence=0.9
            )
        ]
        
        # Test parse_from_rows method exists and is callable
        assert hasattr(self.parser, 'parse_from_rows')
        assert callable(getattr(self.parser, 'parse_from_rows'))
        
        # Mock the OCR extraction to return valid KDA data
        with patch.object(self.parser, '_row_contains_ign', return_value=True), \
             patch.object(self.parser, '_parse_kda_from_row_crop') as mock_extract:
            mock_extract.return_value = KDAResult(
                player_ign="Diary of dolls",
                hero="Kagura",
                kills=12,
                deaths=3,
                assists=5,
                mvp_score=8.5,
                confidence=0.9,
                row_index=0,
                raw_data={}
            )
            
            result = self.parser.parse_from_rows(mock_image, mock_rows, "Diary of dolls")
            
            assert result is not None
            assert isinstance(result, KDAResult)
            assert result.player_ign == "Diary of dolls"
            assert result.kills == 12
            assert result.deaths == 3
            assert result.assists == 5
            assert result.confidence > 0.8


class TestEnhancedDamageParser:
    """Test enhanced Damage parser functionality."""
    
    def setup_method(self):
        self.parser = RowAgnosticDamageParser()
    
    def test_damage_value_extraction(self):
        """Test damage value extraction with various formats."""
        test_cases = [
            ("45,230", 45230),      # Comma-formatted
            ("45230", 45230),       # Plain number
            ("45,230 damage", 45230),  # With text
            ("invalid", None),      # Invalid format
        ]
        
        for text, expected in test_cases:
            ocr_results = [(None, text, 0.8)]
            values = self.parser._extract_damage_values_enhanced(ocr_results)
            
            if expected is not None:
                assert expected in values, f"Should extract damage value {expected} from '{text}'"
            else:
                assert len(values) == 0, f"Should not extract damage values from '{text}'"
    
    def test_percentage_extraction(self):
        """Test percentage extraction with OCR-Mission-2.md % tolerance."""
        test_cases = [
            ("45.2%", 45.2),
            ("45%", 45.0),
            ("no percentage", 0.0),
        ]
        
        for text, expected in test_cases:
            ocr_results = [(None, text, 0.8)]
            percentage = self.parser._extract_percentage_by_position(ocr_results, 0)
            
            assert percentage == expected, f"Expected {expected}% from '{text}', got {percentage}"
    
    def test_enhanced_damage_extraction(self):
        """Test enhanced damage extraction with noise handling."""
        # Mock OCR results with damage data
        ocr_results = [
            (None, "D1ary 0f dolls", 0.85),  # IGN with OCR noise
            (None, "45,230", 0.9),          # Hero damage
            (None, "12,500", 0.85),         # Tower damage  
            (None, "38,750", 0.8),          # Damage taken
            (None, "67.5%", 0.9),           # Percentage
            (None, "420", 0.8),             # GPM
        ]
        
        result = self.parser._extract_damage_from_ocr_enhanced(ocr_results, "Diary of dolls")
        
        assert result is not None
        assert result['hero_damage'] > 0
        assert result['confidence'] >= 0.7
        assert 'normalized_text' in result

    def test_parse_from_rows_integration(self):
        """Test parse_from_rows method integration."""
        # Mock image and rows
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_rows = [
            MockRowCrop(
                row_index=0,
                bbox_ratio=(0.1, 0.1, 0.8, 0.2),
                absolute_bbox=(10, 10, 80, 20),
                contains_target_ign=True,
                confidence=0.9
            )
        ]
        
        # Test parse_from_rows method exists and is callable
        assert hasattr(self.parser, 'parse_from_rows')
        assert callable(getattr(self.parser, 'parse_from_rows'))
        
        # Mock the OCR extraction to return valid damage data
        with patch.object(self.parser, '_row_contains_ign', return_value=True), \
             patch.object(self.parser, '_parse_damage_from_row_crop') as mock_extract:
            mock_extract.return_value = DamageResult(
                player_ign="Diary of dolls",
                hero="Kagura",
                hero_damage=45230,
                tower_damage=12500,
                damage_taken=38750,
                teamfight_participation=85.0,
                gold_per_minute=420,
                confidence=0.9,
                row_index=0,
                raw_data={}
            )
            
            result = self.parser.parse_from_rows(mock_image, mock_rows, "Diary of dolls")
            
            assert result is not None
            assert isinstance(result, DamageResult)
            assert result.player_ign == "Diary of dolls"
            assert result.hero_damage > 0
            assert result.confidence > 0.7


class TestEnhancedCrossViewFusion:
    """Test enhanced cross-view fusion with MVP computation."""
    
    def setup_method(self):
        self.fusion = CrossViewFusion()
    
    def test_mvp_score_computation(self):
        """Test MVP score computation with weighted factors."""
        # Mock good performance data
        kda_data = {
            'kills': 12,
            'deaths': 3,
            'assists': 8,
            'mvp_score': 0.0  # Will be computed
        }
        
        damage_data = {
            'hero_damage': 45230,
            'teamfight_participation': 75.0,
            'gold_per_minute': 520
        }
        
        mvp_score = self.fusion._calculate_mvp_score_enhanced(kda_data, damage_data)
        
        # Should be in valid MVP range
        assert 5.0 <= mvp_score <= 15.0, f"MVP score {mvp_score} out of range"
        
        # Good performance should have high MVP score
        assert mvp_score >= 10.0, f"Expected high MVP score for good performance, got {mvp_score}"
    
    def test_enhanced_fusion_with_enriched_schema(self):
        """Test enhanced fusion with enriched schema output."""
        # Mock KDA result
        kda_result = KDAResult(
            player_ign="Diary of dolls",
            hero="Kagura",
            kills=12,
            deaths=3,
            assists=8,
            mvp_score=9.2,
            confidence=0.9,
            row_index=0,
            raw_data={}
        )
        
        # Mock Damage result with percentage data
        damage_result = DamageResult(
            player_ign="Diary of dolls", 
            hero="Kagura",
            hero_damage=45230,
            tower_damage=12500,
            damage_taken=38750,
            teamfight_participation=75.0,
            gold_per_minute=520,
            confidence=0.85,
            row_index=0,
            raw_data={
                'hero_damage_pct': 32.5,
                'turret_damage_pct': 45.2,
                'taken_damage_pct': 28.1
            }
        )
        
        result = self.fusion.fuse_kda_and_damage_enhanced(
            kda_result, damage_result, "Diary of dolls"
        )
        
        assert result is not None
        assert isinstance(result, FusedResult)
        
        # Test enriched schema
        enriched = result.to_enriched_schema()
        
        # Should have all required fields
        assert 'kda' in enriched
        assert 'damage' in enriched
        assert 'mvp_score' in enriched
        assert 'confidence' in enriched
        
        # KDA section should have ratio
        assert 'ratio' in enriched['kda']
        assert enriched['kda']['ratio'] > 0
        
        # Damage section should have percentages
        assert 'hero_damage_pct' in enriched['damage']
        assert 'turret_damage_pct' in enriched['damage']
        assert 'taken_damage_pct' in enriched['damage']
        
        # Should meet confidence target
        assert enriched['confidence'] >= 0.8, f"Confidence {enriched['confidence']} below target"
    
    def test_confidence_weighting(self):
        """Test confidence weighting meets OCR-Mission-2.md ≥0.85 target."""
        # Create high-confidence results
        high_kda = KDAResult(
            player_ign="Diary of dolls", hero="Kagura", kills=10, deaths=2, assists=12,
            mvp_score=11.5, confidence=0.92, row_index=0, raw_data={}
        )
        
        high_damage = DamageResult(
            player_ign="Diary of dolls", hero="Kagura", hero_damage=52000, 
            tower_damage=15000, damage_taken=35000, teamfight_participation=80.0,
            gold_per_minute=580, confidence=0.88, row_index=0, raw_data={}
        )
        
        result = self.fusion.fuse_kda_and_damage_enhanced(high_kda, high_damage, "Diary of dolls")
        
        # Should meet mission target confidence
        assert result.overall_confidence >= 0.85, \
            f"Failed to meet ≥0.85 confidence target: {result.overall_confidence}"
    
    def test_standalone_cross_view_fusion_function(self):
        """Test standalone cross_view_fusion function compatibility."""
        # Mock minimal results
        kda_result = KDAResult(
            player_ign="test", hero="test", kills=5, deaths=2, assists=3,
            mvp_score=8.0, confidence=0.8, row_index=0, raw_data={}
        )
        
        damage_result = DamageResult(
            player_ign="test", hero="test", hero_damage=25000,
            tower_damage=5000, damage_taken=20000, teamfight_participation=60.0,
            gold_per_minute=400, confidence=0.75, row_index=0, raw_data={}
        )
        
        # Test standalone function (expected by performance tests)
        result = cross_view_fusion(kda_result, damage_result)
        
        assert result is not None
        assert isinstance(result, FusedResult)
        assert hasattr(result, 'to_enriched_schema')


class TestParserAccuracyRequirements:
    """Test parser accuracy requirements (≥90% on test fixtures)."""
    
    def test_golden_ign_variations_accuracy(self):
        """Test ≥90% accuracy on golden IGN variations."""
        parser = RowAgnosticKDAParser()
        target_ign = "Diary of dolls"
        
        # Golden variations (should have 100% success rate)
        golden_variations = [
            "Diary of dolls",      # Perfect match
            "DIARY OF DOLLS",      # Case variation
            "diary of dolls",      # Lowercase
            "D1ary of dolls",      # OCR noise (1 vs i)
            "Diary 0f dolls",      # OCR noise (0 vs o)
            "Diary  of  dolls"     # Spacing variation
        ]
        
        success_count = 0
        for variation in golden_variations:
            normalized_target = parser._normalize_text_for_matching(target_ign)
            normalized_variation = parser._normalize_text_for_matching(variation)
            
            if normalized_target in normalized_variation:
                success_count += 1
        
        accuracy = (success_count / len(golden_variations)) * 100
        assert accuracy >= 90.0, f"Golden IGN accuracy {accuracy}% below 90% requirement"
        
        # Should achieve 100% on golden variations
        assert accuracy == 100.0, f"Expected 100% accuracy on golden variations, got {accuracy}%"
    
    def test_comprehensive_ign_variations_accuracy(self):
        """Test ≥90% accuracy on comprehensive IGN test suite."""
        parser = RowAgnosticKDAParser()
        target_ign = "Diary of dolls"
        
        # Comprehensive variations (should have ≥91.7% success rate per Mission 1)
        comprehensive_variations = [
            # Golden variations (should all pass)
            "Diary of dolls", "DIARY OF DOLLS", "diary of dolls",
            "D1ary of dolls", "Diary 0f dolls", "Diary  of  dolls",
            
            # Additional challenging variations
            "D1ary 0f d0lls",      # Multiple OCR errors
            "diary-of-dolls",      # Hyphenated
            "Diary_of_dolls",      # Underscore
            "DiaryOfDolls",        # No spaces
            "D!ary of do11s",      # More OCR noise
            "Dlary of dolls",      # l vs i confusion
        ]
        
        success_count = 0
        for variation in comprehensive_variations:
            normalized_target = parser._normalize_text_for_matching(target_ign)
            normalized_variation = parser._normalize_text_for_matching(variation)
            
            # Use fuzzy matching for comprehensive test
            if (normalized_target in normalized_variation or 
                normalized_variation in normalized_target or
                self._calculate_similarity(normalized_target, normalized_variation) > 0.8):
                success_count += 1
        
        accuracy = (success_count / len(comprehensive_variations)) * 100
        assert accuracy >= 90.0, f"Comprehensive IGN accuracy {accuracy}% below 90% requirement"
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity for fuzzy matching."""
        if not s1 or not s2:
            return 0.0
        
        # If one string contains the other, high similarity
        if s1 in s2 or s2 in s1:
            return 0.9
        
        # Simple Levenshtein-based similarity
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0
        
        # Count matching characters in same positions
        matches = sum(c1 == c2 for c1, c2 in zip(s1, s2))
        position_similarity = matches / max_len
        
        # Also check for common substrings
        common_chars = set(s1) & set(s2)
        char_similarity = len(common_chars) / max(len(set(s1)), len(set(s2)))
        
        # Return the higher of the two similarities
        return max(position_similarity, char_similarity)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])