"""
Test suite for text normalizers and cleaners - T012
Tests for text normalization, digit cleaning, and IGN fuzzy matching
"""

import pytest
from typing import Tuple, Optional


class TestDigitNormalization:
    """Test digit cleaning and normalization"""
    
    def test_clean_digits_basic(self):
        """Test basic digit cleaning"""
        from backend.ocr.normalizers import clean_digits
        
        # Basic digit cleaning
        assert clean_digits("9/2/12") == "9/2/12"
        assert clean_digits("9,234") == "9234"  # Remove commas
        assert clean_digits("12.5") == "125"    # Remove periods  
        assert clean_digits("O12") == "012"     # O -> 0
        assert clean_digits("l23") == "123"     # l -> 1
        
    def test_clean_digits_complex(self):
        """Test complex OCR noise cleaning"""
        from backend.ocr.normalizers import clean_digits
        
        # Complex OCR errors
        assert clean_digits("9,234.5") == "92345"
        assert clean_digits("O/l/lO") == "0/1/10"
        assert clean_digits("12O74") == "12074"
        
    def test_norm_percent_basic(self):
        """Test percentage normalization"""
        from backend.ocr.normalizers import norm_percent
        
        assert norm_percent("25.4%") == 25.4
        assert norm_percent("18%") == 18.0
        assert norm_percent("100") == 100.0  # Missing %
        assert norm_percent("12.34") == 12.34
        
    def test_norm_percent_with_ocr_errors(self):
        """Test percentage with OCR errors"""
        from backend.ocr.normalizers import norm_percent
        
        assert norm_percent("25.4%") == 25.4
        assert norm_percent("l8.7%") == 18.7  # l -> 1
        assert norm_percent("2O.5") == 20.5   # O -> 0
        
    def test_norm_ratio_basic(self):
        """Test KDA ratio normalization"""
        from backend.ocr.normalizers import norm_ratio
        
        result = norm_ratio(9, 2, 12)
        expected = (9 + 12) / max(1, 2)  # (K+A)/max(1,D)
        assert abs(result - expected) < 0.01
        
        # Edge cases
        assert norm_ratio(5, 0, 3) == 8.0  # 0 deaths -> max(1,0) = 1
        assert norm_ratio(0, 5, 0) == 0.0  # 0 kills and assists


class TestIGNFuzzyMatching:
    """Test IGN fuzzy matching and normalization"""
    
    def test_norm_ign_exact_match(self):
        """Test exact IGN matching"""
        from backend.ocr.normalizers import norm_ign
        
        target = "Diary of dolls"
        candidates = ["Diary of dolls", "Other Player", "Test User"]
        
        best_match, score = norm_ign(candidates, target)
        assert best_match == "Diary of dolls"
        assert score == 1.0  # Perfect match
        
    def test_norm_ign_fuzzy_match(self):
        """Test fuzzy IGN matching with OCR errors"""
        from backend.ocr.normalizers import norm_ign
        
        target = "Diary of dolls"
        candidates = [
            "Diary of d0lls",  # OCR: 0 for o
            "Diary ol dolls",  # OCR: ol for of  
            "HVP Diary of d",  # Partial match
            "Other Player"
        ]
        
        best_match, score = norm_ign(candidates, target)
        
        # Should find best fuzzy match
        assert best_match in ["Diary of d0lls", "Diary ol dolls", "HVP Diary of d"]
        assert score >= 0.70  # Above fuzzy threshold
        
    def test_norm_ign_no_match(self):
        """Test IGN matching when no good match exists"""
        from backend.ocr.normalizers import norm_ign
        
        target = "Diary of dolls"
        candidates = ["Random1", "Player123", "XxXGamerXxX"]
        
        best_match, score = norm_ign(candidates, target)
        
        # Should return None or best attempt with low score
        assert score < 0.50  # Below acceptable threshold
        
    def test_norm_ign_partial_prefix(self):
        """Test partial IGN matching (prefix/suffix cases)"""
        from backend.ocr.normalizers import norm_ign
        
        target = "Diary of dolls"
        candidates = [
            "HVP Diary of d",      # Prefix + partial
            "Diary of dolls MVP",  # Suffix added
            "...Diary of dolls",   # Prefix dots
        ]
        
        best_match, score = norm_ign(candidates, target)
        
        # Should find reasonable partial match
        assert score >= 0.60  # Reasonable threshold for partials


class TestOCRSlashNormalization:
    """Test slash-based text normalization"""
    
    def test_fix_ocr_slash_noise_basic(self):
        """Test basic slash noise fixing"""
        from backend.ocr.normalizers import fix_ocr_slash_noise
        
        # Basic slash fixes
        assert fix_ocr_slash_noise("9/2/12") == "9/2/12"  # No change
        assert fix_ocr_slash_noise("9l2l12") == "9/2/12"  # l -> /
        assert fix_ocr_slash_noise("9|2|12") == "9/2/12"  # | -> /
        
    def test_fix_ocr_slash_noise_complex(self):
        """Test complex slash pattern fixing"""
        from backend.ocr.normalizers import fix_ocr_slash_noise
        
        # Complex patterns
        assert fix_ocr_slash_noise("9 2 12") == "9/2/12"    # spaces -> /
        assert fix_ocr_slash_noise("9-2-12") == "9/2/12"    # dashes -> /
        assert fix_ocr_slash_noise("9\\2\\12") == "9/2/12"  # backslash -> /
        
    def test_fix_ocr_slash_noise_mixed(self):
        """Test mixed OCR errors in slash patterns"""
        from backend.ocr.normalizers import fix_ocr_slash_noise
        
        # Mixed OCR errors
        assert fix_ocr_slash_noise("Ol2ll2") == "0/2/12"    # O->0, l->1, l->/
        assert fix_ocr_slash_noise("9|2 l2") == "9/2/12"    # Mixed separators


class TestTextNormalizationPipeline:
    """Test complete normalization pipeline"""
    
    def test_normalize_kda_text_complete(self):
        """Test complete KDA text normalization"""
        from backend.ocr.normalizers import normalize_kda_text
        
        # Raw OCR output -> clean KDA
        raw_ocr = "9,2l12"  # Comma + l instead of /
        normalized = normalize_kda_text(raw_ocr)
        
        expected = {"k": 9, "d": 2, "a": 12, "ratio": 10.5}
        assert normalized == expected
        
    def test_normalize_damage_text_complete(self):
        """Test complete damage text normalization"""
        from backend.ocr.normalizers import normalize_damage_text
        
        # Raw percentage with OCR errors
        raw_ocr = "25.4%"
        normalized = normalize_damage_text(raw_ocr)
        
        assert normalized == 25.4
        
    def test_normalize_ign_text_complete(self):
        """Test complete IGN text normalization"""  
        from backend.ocr.normalizers import normalize_ign_text
        
        # OCR output with noise
        raw_ocr_candidates = ["HVP Diary of d", "Other123", "Random"]
        target = "Diary of dolls"
        
        best_ign, confidence = normalize_ign_text(raw_ocr_candidates, target)
        
        assert best_ign == "HVP Diary of d"
        assert confidence >= 0.70


class TestNormalizationEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_input_handling(self):
        """Test handling of empty/None inputs"""
        from backend.ocr.normalizers import clean_digits, norm_percent, norm_ign
        
        # Empty strings
        assert clean_digits("") == ""
        assert clean_digits(None) == ""
        
        # Empty percentage
        assert norm_percent("") == 0.0
        assert norm_percent(None) == 0.0
        
        # Empty IGN candidates
        best, score = norm_ign([], "target")
        assert best is None
        assert score == 0.0
        
    def test_malformed_input_handling(self):
        """Test handling of malformed inputs"""
        from backend.ocr.normalizers import norm_ratio, norm_percent
        
        # Invalid ratio values
        assert norm_ratio(-1, 5, 3) == 0.0  # Negative kills
        assert norm_ratio(5, -1, 3) == 8.0  # Negative deaths (treated as 0)
        
        # Invalid percentage
        assert norm_percent("abc%") == 0.0
        assert norm_percent("25.4.5%") == 0.0  # Multiple decimals
        
    def test_extreme_values_handling(self):
        """Test handling of extreme values"""
        from backend.ocr.normalizers import norm_ratio, norm_percent
        
        # Extreme KDA values
        assert norm_ratio(99, 1, 99) == 198.0  # High ratio
        assert norm_ratio(0, 99, 0) == 0.0     # No kills/assists
        
        # Extreme percentages
        assert norm_percent("999%") == 999.0   # > 100%
        assert norm_percent("0.01%") == 0.01   # Very small