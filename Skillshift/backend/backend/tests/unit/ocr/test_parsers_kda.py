"""
Test suite for KDA view parsing functionality.
These tests MUST FAIL initially (TDD requirement).

Target: Extract hero=Kagura, KDA=9/2/12, MVP=10.5 from KDA view screenshots
"""
import pytest
from unittest.mock import patch

# This import will fail initially - that's expected in TDD
# We'll create the parsers_kda module in T022
try:
    from backend.ocr.parsers_kda import (
        parse_kda_view,
        extract_hero_info,
        extract_kda_stats,
        extract_economy_stats,
        extract_mvp_score,
        extract_match_duration,
        normalize_kda_text,
        KDAParseResult
    )
except ImportError:
    # Expected during TDD phase - tests written before implementation
    KDAParseResult = None


class TestKDAParseResult:
    """Test the KDAParseResult data structure"""

    def test_kda_parse_result_creation(self):
        """Test creating KDAParseResult with all fields"""
        # This will fail - KDAParseResult doesn't exist yet
        assert KDAParseResult is not None, "KDAParseResult not implemented"

        result = KDAParseResult(
            hero="kagura",
            role="mage",
            kda={"k": 9, "d": 2, "a": 12},
            gpm=425.5,
            gold=8500,
            mvp_score=10.5,
            match_duration_min=21.2,
            confidence=0.9,
            warnings=[],
            raw_text="sample text"
        )

        assert result.hero == "kagura"
        assert result.kda["k"] == 9
        assert result.mvp_score == 10.5
        assert result.confidence == 0.9


class TestTextNormalization:
    """Test OCR text cleaning and normalization"""

    def test_normalize_kda_text(self):
        """Test cleaning common OCR errors in KDA text"""
        # This will fail - normalize_kda_text doesn't exist yet
        assert normalize_kda_text is not None, \
            "normalize_kda_text not implemented"

        # Common OCR errors
        dirty_text = "Diary 0f d011s  Level: l5  Kagura  9/2/l2  Gold: 8,500"
        clean_text = normalize_kda_text(dirty_text)

        # Should fix common OCR mistakes
        assert "0f" not in clean_text  # 'of' correction
        assert "d011s" not in clean_text  # 'dolls' correction
        assert "l5" not in clean_text  # '15' correction
        assert "l2" not in clean_text  # '12' correction
        # comma handling
        assert "8,500" in clean_text or "8500" in clean_text

    def test_normalize_removes_extra_whitespace(self):
        """Test removal of extra whitespace and formatting"""
        dirty_text = "  Kagura    9 / 2 / 12   Gold:  8,500  "
        clean_text = normalize_kda_text(dirty_text)

        # Should clean up spacing
        assert "  " not in clean_text  # no double spaces
        assert clean_text.strip() == clean_text  # no leading/trailing spaces
        assert "9/2/12" in clean_text or "9 / 2 / 12" in clean_text


class TestHeroExtraction:
    """Test hero name and role extraction"""

    def test_extract_kagura_hero_info(self):
        """Test extraction of Kagura hero information"""
        # This will fail - extract_hero_info doesn't exist yet
        assert extract_hero_info is not None, \
            "extract_hero_info not implemented"

        # Sample OCR text containing hero info
        ocr_text = """
        Player Name: Diary of dolls
        Level: 15
        Hero: Kagura
        Role: Mage
        KDA: 9/2/12
        MVP: 10.5
        """

        hero_info = extract_hero_info(ocr_text, player_row_index=1)

        # normalized to lowercase
        assert hero_info["hero"] == "kagura"
        assert hero_info["role"] == "mage"
        assert hero_info["confidence"] >= 0.8

    def test_extract_hero_with_variations(self):
        """Test hero extraction with OCR variations"""
        # Test common OCR variations of hero names
        test_cases = [
            ("Kagura", "kagura"),
            ("KAGURA", "kagura"),
            ("Kagúra", "kagura"),  # accent marks
            ("Kagura.", "kagura"),  # punctuation
        ]

        for ocr_hero, expected in test_cases:
            ocr_text = f"Hero: {ocr_hero}\nRole: Mage"
            hero_info = extract_hero_info(ocr_text, player_row_index=0)
            assert hero_info["hero"] == expected

    def test_extract_hero_not_found(self):
        """Test hero extraction when hero info is missing"""
        ocr_text = "Some random text without hero information"
        hero_info = extract_hero_info(ocr_text, player_row_index=0)

        assert hero_info["hero"] is None
        assert hero_info["role"] is None
        assert hero_info["confidence"] < 0.5


class TestKDAExtraction:
    """Test KDA statistics extraction"""

    def test_extract_kda_9_2_12(self):
        """Test extraction of target KDA: 9/2/12"""
        # This will fail - extract_kda_stats doesn't exist yet
        assert extract_kda_stats is not None, \
            "extract_kda_stats not implemented"

        # Target case: 9/2/12 for Diary of dolls
        ocr_text = """
        Diary of dolls  Level 15  Kagura  9/2/12  Gold: 8500
        """

        kda_stats = extract_kda_stats(ocr_text, player_row_index=0)

        assert kda_stats["k"] == 9
        assert kda_stats["d"] == 2
        assert kda_stats["a"] == 12
        # (9+12)/2
        assert kda_stats["ratio"] == pytest.approx(10.5, rel=0.1)
        assert kda_stats["confidence"] >= 0.9

    def test_extract_kda_various_formats(self):
        """Test KDA extraction with different formatting"""
        test_cases = [
            ("9/2/12", {"k": 9, "d": 2, "a": 12}),
            ("9 / 2 / 12", {"k": 9, "d": 2, "a": 12}),
            ("9-2-12", {"k": 9, "d": 2, "a": 12}),
            ("K:9 D:2 A:12", {"k": 9, "d": 2, "a": 12}),
            ("9|2|12", {"k": 9, "d": 2, "a": 12}),
        ]

        for kda_text, expected in test_cases:
            ocr_text = f"Player: TestUser {kda_text} Gold: 1000"
            kda_stats = extract_kda_stats(ocr_text, player_row_index=0)

            assert kda_stats["k"] == expected["k"]
            assert kda_stats["d"] == expected["d"]
            assert kda_stats["a"] == expected["a"]

    def test_extract_kda_with_ocr_errors(self):
        """Test KDA extraction with common OCR errors"""
        # Common OCR errors: 'O' -> '0', 'I' -> '1', 'l' -> '1'
        ocr_text = "Player: TestUser 9/2/l2 Gold: 1000"  # 'l2' should be '12'
        kda_stats = extract_kda_stats(ocr_text, player_row_index=0)

        assert kda_stats["k"] == 9
        assert kda_stats["d"] == 2
        assert kda_stats["a"] == 12  # Should correct 'l2' to '12'

    def test_extract_kda_not_found(self):
        """Test KDA extraction when no KDA pattern is found"""
        ocr_text = "Player: TestUser Gold: 1000"  # No KDA
        kda_stats = extract_kda_stats(ocr_text, player_row_index=0)

        assert kda_stats["k"] is None
        assert kda_stats["d"] is None
        assert kda_stats["a"] is None
        assert kda_stats["confidence"] < 0.3


class TestEconomyExtraction:
    """Test gold and GPM extraction"""

    def test_extract_economy_stats(self):
        """Test extraction of gold and GPM values"""
        # This will fail - extract_economy_stats doesn't exist yet
        assert extract_economy_stats is not None, \
            "extract_economy_stats not implemented"

        ocr_text = """
        Diary of dolls  Kagura  9/2/12
        Gold: 8,500  GPM: 425.5
        """

        economy = extract_economy_stats(ocr_text, player_row_index=0)

        assert economy["gold"] == 8500
        assert economy["gpm"] == pytest.approx(425.5, rel=0.01)
        assert economy["confidence"] >= 0.8

    def test_extract_gold_various_formats(self):
        """Test gold extraction with different number formats"""
        test_cases = [
            ("Gold: 8,500", 8500),
            ("Gold: 8.5K", 8500),
            ("Gold: 8500", 8500),
            ("8,500 Gold", 8500),
            ("Gold 8500", 8500),
        ]

        for gold_text, expected in test_cases:
            ocr_text = f"Player: TestUser {gold_text}"
            economy = extract_economy_stats(ocr_text, player_row_index=0)
            assert economy["gold"] == expected

    def test_extract_gpm_calculation(self):
        """Test GPM calculation when only gold and duration available"""
        ocr_text = "Gold: 8500"
        match_duration_min = 20.0  # 20 minutes

        economy = extract_economy_stats(
            ocr_text, player_row_index=0, duration_min=match_duration_min)

        expected_gpm = 8500 / 20.0  # 425.0
        assert economy["gpm"] == pytest.approx(expected_gpm, rel=0.01)


class TestMVPExtraction:
    """Test MVP score extraction"""

    def test_extract_mvp_score_10_5(self):
        """Test extraction of target MVP score: 10.5"""
        # This will fail - extract_mvp_score doesn't exist yet
        assert extract_mvp_score is not None, \
            "extract_mvp_score not implemented"

        # Target case: MVP 10.5 for Diary of dolls
        ocr_text = """
        Diary of dolls  Kagura  9/2/12  Gold: 8500
        MVP: 10.5  ⭐⭐⭐
        """

        mvp_score = extract_mvp_score(ocr_text, player_row_index=0)

        assert mvp_score["score"] == pytest.approx(10.5, rel=0.01)
        assert mvp_score["confidence"] >= 0.9
        assert mvp_score["has_crown"] is True  # MVP indicator

    def test_extract_mvp_various_formats(self):
        """Test MVP extraction with different formats"""
        test_cases = [
            ("MVP: 10.5", 10.5),
            ("MVP 10.5", 10.5),
            ("10.5 MVP", 10.5),
            ("Rating: 10.5", 10.5),
            ("Score: 10.5", 10.5),
        ]

        for mvp_text, expected in test_cases:
            ocr_text = f"Player: TestUser {mvp_text}"
            mvp_score = extract_mvp_score(ocr_text, player_row_index=0)
            assert mvp_score["score"] == pytest.approx(expected, rel=0.01)


class TestMatchDurationExtraction:
    """Test match duration extraction"""

    def test_extract_match_duration(self):
        """Test extraction of match duration"""
        # This will fail - extract_match_duration doesn't exist yet
        assert extract_match_duration is not None, \
            "extract_match_duration not implemented"

        # Common duration formats
        test_cases = [
            ("Duration: 21:12", 21.2),  # 21 minutes 12 seconds
            ("Match Time: 20:30", 20.5),  # 20 minutes 30 seconds
            ("21:00", 21.0),  # 21 minutes exactly
            ("Duration 19:45", 19.75),  # 19 minutes 45 seconds
        ]

        for duration_text, expected_min in test_cases:
            ocr_text = f"Game stats {duration_text} Victory"
            duration = extract_match_duration(ocr_text)
            assert duration == pytest.approx(expected_min, abs=0.1)


class TestMainKDAParser:
    """Test the main KDA view parsing function"""

    def test_parse_kda_view_complete(self, kda_screenshot_cv2,
                                     expected_ocr_result):
        """Test complete KDA view parsing for target screenshot"""
        # This will fail - parse_kda_view doesn't exist yet
        assert parse_kda_view is not None, \
            "parse_kda_view not implemented"

        # Mock the player row index (from detectors)
        player_row_index = 1  # Assuming "Diary of dolls" is in row 1

        result = parse_kda_view(
            kda_screenshot_cv2,
            player_row_index=player_row_index,
            target_ign="Diary of dolls"
        )

        # Core acceptance criteria
        assert result.hero == "kagura"
        assert result.role == "mage"
        assert result.kda["k"] == 9
        assert result.kda["d"] == 2
        assert result.kda["a"] == 12
        assert result.mvp_score == pytest.approx(10.5, rel=0.1)
        assert result.confidence >= 0.85
        assert len(result.warnings) == 0  # No warnings for successful parse

    def test_parse_kda_view_missing_data(self, kda_screenshot_cv2):
        """Test KDA parsing with missing data fields"""
        player_row_index = 1

        # Mock scenario where some data is missing
        with patch('backend.ocr.parsers_kda.extract_mvp_score') as mock_mvp:
            mock_mvp.return_value = {
                "score": None, "confidence": 0.2, "has_crown": False}

            result = parse_kda_view(
                kda_screenshot_cv2, player_row_index=player_row_index)

            assert result.mvp_score is None
            assert "MVP score not found" in result.warnings
            # Lower confidence due to missing data
            assert result.confidence < 0.85

    def test_parse_kda_view_low_confidence(self, kda_screenshot_cv2):
        """Test KDA parsing with low confidence data"""
        player_row_index = 1

        result = parse_kda_view(
            kda_screenshot_cv2, player_row_index=player_row_index)

        # If confidence is low, should include warnings
        if result.confidence < 0.85:
            assert len(result.warnings) > 0
            assert any("confidence" in warning.lower()
                       for warning in result.warnings)

    def test_parse_kda_view_no_bogus_defaults(self, kda_screenshot_cv2):
        """Test that parser never returns bogus defaults like 0/1/0"""
        player_row_index = 999  # Invalid row to trigger failures

        result = parse_kda_view(
            kda_screenshot_cv2, player_row_index=player_row_index)

        # Should NOT return the infamous 0/1/0 default
        if result.kda["k"] is not None:
            assert not (result.kda["k"] == 0 and result.kda["d"] == 1
                        and result.kda["a"] == 0)
        else:
            # If KDA is None, that's acceptable - but no bogus defaults
            assert result.kda["k"] is None
            assert result.kda["d"] is None
            assert result.kda["a"] is None
            assert "KDA extraction failed" in result.warnings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

