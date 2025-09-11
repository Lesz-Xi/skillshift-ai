#!/usr/bin/env python3
"""
T010: Damage Parser Test Suite - OCR Damage View Parsing Tests
Tests extraction from IMG_1768 (Damage view) for "Diary of dolls" → hero=Kagura

Target Requirements:
- Extract hero damage percentage from damage view
- Extract teamfight participation data  
- Cross-reference with "Diary of dolls" IGN
- Achieve ≥0.7 confidence for damage metrics
- Handle "No numeric data found" errors gracefully

TDD Status: MUST FAIL before implementation exists
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import Optional, Dict, Any

# Import functions that don't exist yet (TDD - must fail)
from ocr.parsers_damage import (
    parse_damage_view,
    extract_hero_damage_percentage,
    extract_teamfight_participation,
    DamageViewResult
)


class TestDamageViewParsing:
    """Core damage view OCR parsing functionality"""
    
    def test_parse_damage_view_complete(self, damage_screenshot_cv2):
        """T010-1: Complete damage view parsing for Diary of dolls → Kagura"""
        target_ign = "Diary of dolls"
        result = parse_damage_view(damage_screenshot_cv2, player_row_index=1, target_ign=target_ign)
        
        # Core requirements - damage view specific data
        assert result.hero_damage_pct is not None, "Hero damage percentage not extracted"
        assert isinstance(result.hero_damage_pct, (int, float)), "Invalid damage percentage type"
        assert 0 <= result.hero_damage_pct <= 100, "Damage percentage out of valid range"
        assert result.confidence >= 0.7, f"Confidence {result.confidence} below 0.7 threshold"
        
        # Player identification validation
        assert result.player_ign == target_ign, f"Player IGN mismatch: {result.player_ign}"
        
    def test_parse_damage_view_high_confidence(self, damage_screenshot_cv2):
        """T010-2: Damage parsing achieves high confidence scores"""
        result = parse_damage_view(damage_screenshot_cv2, player_row_index=1, target_ign="Diary of dolls")
        
        assert result.confidence >= 0.8, "High confidence damage extraction failed"
        assert result.hero_damage_pct is not None, "No damage data extracted despite high confidence"


class TestHeroDamageExtraction:
    """Hero damage percentage extraction from damage view"""
    
    def test_extract_hero_damage_percentage_success(self, damage_screenshot_cv2):
        """T010-3: Extract hero damage percentage successfully"""
        damage_pct = extract_hero_damage_percentage(
            damage_screenshot_cv2, 
            player_row_index=1,
            target_ign="Diary of dolls"
        )
        
        assert damage_pct is not None, "Failed to extract hero damage percentage"
        assert isinstance(damage_pct, (int, float)), "Invalid damage percentage data type"
        assert 0 <= damage_pct <= 100, "Damage percentage outside valid range (0-100%)"
        
    def test_extract_teamfight_participation(self, damage_screenshot_cv2):
        """T010-4: Extract teamfight participation data"""
        participation = extract_teamfight_participation(
            damage_screenshot_cv2,
            player_row_index=1,
            target_ign="Diary of dolls"  
        )
        
        # Teamfight data can be optional but should be valid when present
        if participation is not None:
            assert isinstance(participation, (int, float)), "Invalid teamfight participation type"
            assert 0 <= participation <= 100, "Teamfight participation outside valid range"


class TestDamageViewErrorHandling:
    """Error handling and edge cases for damage view parsing"""
    
    def test_damage_view_no_numeric_data_handling(self, damage_screenshot_cv2):
        """T010-5: Handle 'No numeric data found' gracefully"""
        # Test with invalid player row to trigger fallback behavior  
        result = parse_damage_view(damage_screenshot_cv2, player_row_index=999, target_ign="Invalid Player")
        
        # Should not return bogus defaults, should indicate missing data explicitly
        if result.hero_damage_pct is None:
            assert result.confidence < 0.5, "High confidence reported for missing data"
            assert "numeric data" not in str(result.error_message).lower() or \
                   result.error_message is None, "Avoid 'No numeric data found' generic errors"
        
    def test_damage_view_invalid_input_handling(self):
        """T010-6: Handle invalid/corrupted image input"""
        invalid_image = np.zeros((10, 10, 3), dtype=np.uint8)  # Tiny black image
        
        result = parse_damage_view(invalid_image, player_row_index=0, target_ign="Test Player")
        
        # Should handle gracefully without crashes
        assert isinstance(result, DamageViewResult), "Should return valid result object for invalid input"
        assert result.confidence < 0.3, "Should report low confidence for invalid input"


# Fixtures and test data setup
@pytest.fixture
def damage_screenshot_cv2(damage_screenshot_image):
    """Convert damage screenshot to OpenCV format for processing"""
    import cv2
    # Convert PIL Image to OpenCV format
    img_array = np.array(damage_screenshot_image)
    return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)


@pytest.fixture  
def expected_damage_result():
    """Expected damage view parsing results for IMG_1768"""
    return {
        "player_ign": "Diary of dolls",
        "hero": "kagura",
        "hero_damage_pct": None,  # To be determined from actual screenshot
        "teamfight_participation": None,  # Optional data
        "confidence": 0.7,  # Minimum threshold
        "data_source": "damage_view"
    }