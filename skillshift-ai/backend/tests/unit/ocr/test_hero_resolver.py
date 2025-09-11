"""
Unit tests for Advanced Hero Resolver (OCR Mission 4)

Tests hero resolution accuracy, phash filtering, ORB matching, and histogram fallback.
"""

import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch
import os
import tempfile
import json

from backend.ocr.hero_resolver import AdvancedHeroResolver, HeroMatchResult


class TestAdvancedHeroResolver:
    """Test cases for Advanced Hero Resolver."""
    
    @pytest.fixture
    def hero_resolver(self):
        """Create a hero resolver instance for testing."""
        return AdvancedHeroResolver()
    
    @pytest.fixture
    def mock_hero_crop(self):
        """Create a mock hero crop image."""
        # Create a simple test image
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        img[:, :] = [100, 150, 200]  # Blue-ish color
        return img
    
    @pytest.fixture
    def mock_hero_database(self, tmp_path):
        """Create a mock hero database for testing."""
        hero_data = [
            {
                "name": "kagura",
                "image_path": str(tmp_path / "kagura.png"),
                "role": "mage"
            },
            {
                "name": "lancelot", 
                "image_path": str(tmp_path / "lancelot.png"),
                "role": "assassin"
            },
            {
                "name": "beatrix",
                "image_path": str(tmp_path / "beatrix.png"),
                "role": "marksman"
            }
        ]
        
        # Create mock images
        for hero in hero_data:
            img = np.zeros((64, 64, 3), dtype=np.uint8)
            img[:, :] = [50, 100, 150]  # Different color for each
            cv2.imwrite(hero["image_path"], img)
        
        # Write database file
        db_path = tmp_path / "heroes_cleaned.json"
        with open(db_path, 'w') as f:
            json.dump(hero_data, f)
        
        return str(db_path)
    
    def test_hero_resolver_initialization(self, hero_resolver):
        """Test hero resolver initializes correctly."""
        assert hero_resolver is not None
        assert hasattr(hero_resolver, 'hero_templates')
        assert hasattr(hero_resolver, 'phash_database')
        assert hasattr(hero_resolver, 'orb_database')
        assert hasattr(hero_resolver, 'histogram_database')
    
    def test_phash_computation(self, hero_resolver, mock_hero_crop):
        """Test phash computation."""
        phash = hero_resolver._compute_phash(mock_hero_crop)
        assert isinstance(phash, int)
        assert phash >= 0
    
    def test_histogram_computation(self, hero_resolver, mock_hero_crop):
        """Test histogram computation."""
        hist = hero_resolver._compute_histogram(mock_hero_crop)
        assert isinstance(hist, np.ndarray)
        assert len(hist) > 0
    
    def test_preprocess_hero_crop(self, hero_resolver, mock_hero_crop):
        """Test hero crop preprocessing."""
        processed = hero_resolver._preprocess_hero_crop(mock_hero_crop)
        assert processed.shape == (64, 64, 3)
        assert processed.dtype == np.uint8
    
    def test_phash_filtering(self, hero_resolver, mock_hero_crop):
        """Test phash filtering finds candidates."""
        # Mock some templates in the database
        hero_resolver.hero_templates = {
            'kagura': mock_hero_crop,
            'lancelot': mock_hero_crop + 10,
            'beatrix': mock_hero_crop + 20
        }
        hero_resolver._build_similarity_databases()
        
        candidates = hero_resolver._phash_filter(mock_hero_crop)
        assert isinstance(candidates, list)
        # Should find at least one candidate (exact match)
        assert len(candidates) >= 1
    
    def test_orb_match(self, hero_resolver, mock_hero_crop):
        """Test ORB matching."""
        # Mock templates and database
        hero_resolver.hero_templates = {'kagura': mock_hero_crop}
        hero_resolver._build_similarity_databases()
        
        candidates = ['kagura']
        result = hero_resolver._orb_match(mock_hero_crop, candidates)
        
        assert isinstance(result, HeroMatchResult)
        assert result.hero_name in ['kagura', 'unknown']
        assert 0.0 <= result.confidence <= 1.0
    
    def test_histogram_match(self, hero_resolver, mock_hero_crop):
        """Test histogram matching."""
        # Mock templates and database
        hero_resolver.hero_templates = {'kagura': mock_hero_crop}
        hero_resolver._build_similarity_databases()
        
        candidates = ['kagura']
        result = hero_resolver._histogram_match(mock_hero_crop, candidates)
        
        assert isinstance(result, HeroMatchResult)
        assert result.hero_name in ['kagura', 'unknown']
        assert 0.0 <= result.confidence <= 1.0
    
    def test_resolve_hero_with_valid_crop(self, hero_resolver, mock_hero_crop):
        """Test hero resolution with valid crop."""
        # Mock templates
        hero_resolver.hero_templates = {'kagura': mock_hero_crop}
        hero_resolver._build_similarity_databases()
        
        result = hero_resolver.resolve_hero(mock_hero_crop, "test_player")
        
        assert isinstance(result, HeroMatchResult)
        assert result.hero_name in ['kagura', 'unknown']
        assert 0.0 <= result.confidence <= 1.0
        assert result.method in ['orb', 'histogram', 'combined_orb+histogram', 'phash_filter_failed', 'no_valid_results']
    
    def test_resolve_hero_with_invalid_crop(self, hero_resolver):
        """Test hero resolution with invalid crop."""
        result = hero_resolver.resolve_hero(None, "test_player")
        
        assert isinstance(result, HeroMatchResult)
        assert result.hero_name == "unknown"
        assert result.confidence == 0.0
        assert result.method == "no_image"
    
    def test_resolve_hero_with_empty_crop(self, hero_resolver):
        """Test hero resolution with empty crop."""
        empty_crop = np.array([])
        result = hero_resolver.resolve_hero(empty_crop, "test_player")
        
        assert isinstance(result, HeroMatchResult)
        assert result.hero_name == "unknown"
        assert result.confidence == 0.0
        assert result.method == "no_image"
    
    def test_select_best_result(self, hero_resolver):
        """Test best result selection."""
        results = [
            HeroMatchResult("kagura", 0.8, "orb"),
            HeroMatchResult("lancelot", 0.9, "histogram"),
            HeroMatchResult("unknown", 0.0, "error")
        ]
        
        best = hero_resolver._select_best_result(results)
        
        assert best.hero_name == "lancelot"
        assert best.confidence == 0.9
        assert best.method in ["histogram", "combined_orb+histogram"]  # Updated to handle combined methods
    
    def test_select_best_result_with_unknown_only(self, hero_resolver):
        """Test best result selection with only unknown results."""
        results = [
            HeroMatchResult("unknown", 0.0, "error1"),
            HeroMatchResult("unknown", 0.0, "error2")
        ]
        
        best = hero_resolver._select_best_result(results)
        
        assert best.hero_name == "unknown"
        assert best.confidence == 0.0
        assert best.method == "no_valid_results"
    
    def test_get_hero_confidence_breakdown(self, hero_resolver, mock_hero_crop):
        """Test confidence breakdown generation."""
        # Mock templates
        hero_resolver.hero_templates = {'kagura': mock_hero_crop}
        hero_resolver._build_similarity_databases()
        
        breakdown = hero_resolver.get_hero_confidence_breakdown(mock_hero_crop)
        
        assert isinstance(breakdown, dict)
        assert 'phash_candidates' in breakdown
        assert 'orb_result' in breakdown
        assert 'histogram_result' in breakdown
        assert 'final_result' in breakdown
    
    def test_hero_resolver_with_database(self, mock_hero_database):
        """Test hero resolver with actual database file."""
        resolver = AdvancedHeroResolver(mock_hero_database)
        
        assert len(resolver.hero_templates) > 0
        assert 'kagura' in resolver.hero_templates
        assert 'lancelot' in resolver.hero_templates
        assert 'beatrix' in resolver.hero_templates
    
    def test_fallback_templates_creation(self):
        """Test fallback templates are created when database is not found."""
        resolver = AdvancedHeroResolver("nonexistent_database.json")
        
        # Force creation of fallback templates
        resolver._create_fallback_templates()
        
        assert len(resolver.hero_templates) > 0
        # Should have fallback templates for common heroes
        common_heroes = ['kagura', 'lancelot', 'beatrix', 'hayabusa', 'chou']
        for hero in common_heroes:
            assert hero in resolver.hero_templates


class TestHeroMatchResult:
    """Test cases for HeroMatchResult dataclass."""
    
    def test_hero_match_result_creation(self):
        """Test HeroMatchResult creation."""
        result = HeroMatchResult(
            hero_name="kagura",
            confidence=0.85,
            method="orb",
            phash_distance=5,
            orb_matches=15,
            histogram_similarity=0.8
        )
        
        assert result.hero_name == "kagura"
        assert result.confidence == 0.85
        assert result.method == "orb"
        assert result.phash_distance == 5
        assert result.orb_matches == 15
        assert result.histogram_similarity == 0.8
    
    def test_hero_match_result_minimal(self):
        """Test HeroMatchResult with minimal parameters."""
        result = HeroMatchResult(
            hero_name="unknown",
            confidence=0.0,
            method="error"
        )
        
        assert result.hero_name == "unknown"
        assert result.confidence == 0.0
        assert result.method == "error"
        assert result.phash_distance is None
        assert result.orb_matches is None
        assert result.histogram_similarity is None


if __name__ == "__main__":
    pytest.main([__file__])
