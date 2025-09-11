"""
Test configuration and fixtures for MLBB Coach AI backend tests.

This module provides common test fixtures and configuration for testing
the MLBB Coach AI backend functionality, including screenshot processing,
OCR analysis, and hero detection.
"""

import pytest
from pathlib import Path
from typing import Dict, Any, Tuple
from PIL import Image
import cv2
import numpy as np

# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"

# Test constants
DEFAULT_CONFIDENCE_THRESHOLD = 0.85
DEFAULT_COMPLETENESS_THRESHOLD = 0.85
DEFAULT_MVP_SCORE = 10.5


@pytest.fixture
def kda_screenshot_path() -> Path:
    """Path to KDA view test screenshot."""
    return FIXTURES_DIR / "IMG_1767.PNG"


@pytest.fixture
def damage_screenshot_path() -> Path:
    """Path to Damage view test screenshot."""
    return FIXTURES_DIR / "IMG_1768.PNG"


@pytest.fixture
def kda_screenshot_image(kda_screenshot_path: Path) -> Image.Image:
    """Load KDA screenshot as PIL Image."""
    if not kda_screenshot_path.exists():
        pytest.skip(f"Test fixture not found: {kda_screenshot_path}")
    return Image.open(kda_screenshot_path)


@pytest.fixture
def damage_screenshot_image(damage_screenshot_path: Path) -> Image.Image:
    """Load Damage screenshot as PIL Image."""
    if not damage_screenshot_path.exists():
        pytest.skip(f"Test fixture not found: {damage_screenshot_path}")
    return Image.open(damage_screenshot_path)


@pytest.fixture
def kda_screenshot_cv2(kda_screenshot_path: Path) -> np.ndarray:
    """Load KDA screenshot as OpenCV image."""
    if not kda_screenshot_path.exists():
        pytest.skip(f"Test fixture not found: {kda_screenshot_path}")
    return cv2.imread(str(kda_screenshot_path))


@pytest.fixture
def damage_screenshot_cv2(damage_screenshot_path: Path) -> np.ndarray:
    """Load Damage screenshot as OpenCV image."""
    if not damage_screenshot_path.exists():
        pytest.skip(f"Test fixture not found: {damage_screenshot_path}")
    return cv2.imread(str(damage_screenshot_path))


@pytest.fixture
def expected_ocr_result() -> Dict[str, Any]:
    """Expected OCR extraction result for test validation."""
    return {
        "ign": "Diary of dolls",
        "hero": "kagura",
        "role": "mage",
        "kda": {"k": 9, "d": 2, "a": 12},
        "mvp_score": DEFAULT_MVP_SCORE,
        "player_located": True,
        "overall_confidence": DEFAULT_CONFIDENCE_THRESHOLD,
        "data_completeness": DEFAULT_COMPLETENESS_THRESHOLD
    }


@pytest.fixture
def ocr_config() -> Dict[str, float]:
    """Default OCR configuration for testing."""
    return {
        "exact_match_threshold": 1.0,
        "fuzzy_match_threshold": 0.88,
        "visual_anchor_threshold": 0.7,
        "template_confidence_threshold": 0.8,
        "minimum_confidence": 0.5,
        "minimum_completeness": 0.6
    }


@pytest.fixture
def sample_match_data() -> Dict[str, Any]:
    """Sample match data for testing analysis functions."""
    return {
        "hero": "kagura",
        "role": "mage",
        "kda": "9/2/12",
        "gold": 12374,
        "gpm": 583,
        "hero_damage": 107100,
        "turret_damage": 2854,
        "damage_taken": 54444,
        "teamfight_participation": 70,
        "match_duration": 21.2,
        "confidence_score": 0.85,
        "is_mvp": True
    }


@pytest.fixture
def minimal_match_data() -> Dict[str, Any]:
    """Minimal match data for testing with missing values."""
    return {
        "hero": "unknown",
        "role": "unknown",
        "kda": "0/0/0",
        "gold": 0,
        "gpm": 0,
        "confidence_score": 0.3
    }


@pytest.fixture
def test_image_dimensions() -> Tuple[int, int, int]:
    """Standard test image dimensions (height, width, channels)."""
    return (1080, 1920, 3)


@pytest.fixture
def mock_hero_database() -> Dict[str, Dict[str, Any]]:
    """Mock hero database for testing."""
    return {
        "kagura": {
            "name": "Kagura",
            "role": "mage",
            "sub_role": "burst",
            "specialty": "magic_damage",
            "difficulty": 8
        },
        "tigreal": {
            "name": "Tigreal",
            "role": "tank",
            "sub_role": "initiator",
            "specialty": "crowd_control",
            "difficulty": 4
        }
    }
