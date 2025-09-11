"""
OCR Mission 5: Unit Tests for Layout Drift Robustness

Tests for grid variance regularizer, percent normalizer, and hero partial-crop handling.
"""

import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch
import tempfile
import os

from backend.ocr.robustness import (
    DetectorDriftGuards, 
    AdaptiveNormalizer, 
    RobustnessConfig,
    DriftTelemetry
)
from backend.ocr.hero_resolver import AdvancedHeroResolver


class TestDetectorDriftGuards:
    """Test detector drift guards functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = RobustnessConfig(
            grid_variance_warn=0.015,
            grid_variance_correct=0.03,
            bbox_expand_pct=0.03,
            min_anchor_consensus=2
        )
        self.drift_guards = DetectorDriftGuards(self.config)
    
    def test_validate_row_grid_normal_variance(self):
        """Test row grid validation with normal variance."""
        # Normal bands with low variance
        bands = [100, 150, 200, 250, 300]
        image_height = 1000
        
        corrected_bands, warnings = self.drift_guards.validate_row_grid(bands, image_height)
        
        # Should not correct normal variance
        assert corrected_bands == bands
        assert len(warnings) == 0
        assert self.drift_guards.telemetry.row_variance < self.config.grid_variance_warn
    
    def test_validate_row_grid_high_variance_warning(self):
        """Test row grid validation with high variance (warning only)."""
        # Bands with high variance but below correction threshold
        bands = [100, 120, 200, 220, 300]  # Uneven spacing
        image_height = 1000
        
        corrected_bands, warnings = self.drift_guards.validate_row_grid(bands, image_height)
        
        # Should warn and may correct if variance is too high
        assert len(warnings) > 0
        assert "variance" in warnings[0].lower()
        assert self.drift_guards.telemetry.row_variance > self.config.grid_variance_warn
        
        # Bands may be corrected if variance exceeds correction threshold
        if self.drift_guards.telemetry.row_variance > self.config.grid_variance_correct:
            assert corrected_bands != bands  # Should be corrected
        else:
            assert corrected_bands == bands  # Should not be corrected
    
    def test_validate_row_grid_high_variance_correction(self):
        """Test row grid validation with very high variance (correction)."""
        # Bands with very high variance
        bands = [100, 110, 200, 210, 300]  # Very uneven spacing
        image_height = 1000
        
        corrected_bands, warnings = self.drift_guards.validate_row_grid(bands, image_height)
        
        # Should correct the bands
        assert corrected_bands != bands
        assert len(corrected_bands) == len(bands)
        assert len(warnings) > 0
        assert "high row variance" in warnings[0].lower()
        assert self.drift_guards.telemetry.row_variance > self.config.grid_variance_correct
    
    def test_regularize_bands(self):
        """Test band regularization functionality."""
        # Uneven bands
        bands = [100, 120, 200, 220, 300]
        
        regularized = self.drift_guards._regularize_bands(bands)
        
        # Should have equal spacing
        assert len(regularized) == len(bands)
        assert regularized[0] == bands[0]  # First band unchanged
        assert regularized[-1] == bands[-1]  # Last band unchanged
        
        # Check spacing is more regular
        spacings = np.diff(regularized)
        variance = np.var(spacings)
        assert variance < 1.0  # Should be very low variance
    
    def test_multi_anchor_consensus(self):
        """Test multi-anchor consensus detection."""
        # Create mock grayscale image
        gray_image = np.zeros((100, 100), dtype=np.uint8)
        
        with patch('backend.ocr.ocr_reader.extract_text_optimized') as mock_extract:
            # Mock OCR results with scoreboard anchors
            mock_extract.return_value = [
                "Victory", "KDA", "Damage", "Gold", "MVP"
            ]
            
            anchors, confidence = self.drift_guards.multi_anchor_consensus(gray_image, 100, 100)
            
            # Should find multiple anchors
            assert len(anchors) >= self.config.min_anchor_consensus
            assert confidence > 0.0
            # Check for anchor categories (format: "category:pattern")
            anchor_categories = [a.split(':')[0] for a in anchors]
            assert "victory" in anchor_categories
            assert "kda" in anchor_categories
    
    def test_expand_bbox_dynamic(self):
        """Test dynamic bbox expansion."""
        # Original bbox (top, left, width, height) as ratios
        bbox = (0.2, 0.1, 0.8, 0.6)
        width, height = 1000, 1000
        
        expanded_bbox = self.drift_guards.expand_bbox_dynamic(bbox, width, height)
        
        # Should expand the bbox
        assert expanded_bbox[0] <= bbox[0]  # Top should move up
        assert expanded_bbox[1] <= bbox[1]  # Left should move left
        assert expanded_bbox[2] >= bbox[2]  # Width should increase
        assert expanded_bbox[3] >= bbox[3]  # Height should increase
        
        # Should stay within bounds
        assert expanded_bbox[0] >= 0.0
        assert expanded_bbox[1] >= 0.0
        assert expanded_bbox[0] + expanded_bbox[3] <= 1.0
        assert expanded_bbox[1] + expanded_bbox[2] <= 1.0


class TestAdaptiveNormalizer:
    """Test adaptive normalizer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = RobustnessConfig(use_sauvola_fallback=True)
        self.normalizer = AdaptiveNormalizer(self.config)
    
    def test_adaptive_binarization_otsu(self):
        """Test adaptive binarization with Otsu."""
        # Create test image with clear foreground/background
        image = np.zeros((100, 100), dtype=np.uint8)
        image[20:80, 20:80] = 255  # White square on black background
        
        binary = self.normalizer.adaptive_binarization(image)
        
        # Should produce binary image
        assert binary.dtype == np.uint8
        assert np.all(np.isin(binary, [0, 255]))
        assert binary.shape == image.shape
    
    def test_adaptive_binarization_sauvola_fallback(self):
        """Test adaptive binarization with Sauvola fallback."""
        # Create image with many midtones (should trigger Sauvola)
        image = np.random.randint(50, 205, (100, 100), dtype=np.uint8)
        
        binary = self.normalizer.adaptive_binarization(image)
        
        # Should produce binary image
        assert binary.dtype == np.uint8
        assert np.all(np.isin(binary, [0, 255]))
        assert binary.shape == image.shape
    
    def test_too_many_midtones_detection(self):
        """Test midtone detection heuristic."""
        # Image with many midtones
        midtone_image = np.random.randint(50, 205, (100, 100), dtype=np.uint8)
        assert self.normalizer._too_many_midtones(midtone_image) == True
        
        # Binary image (no midtones)
        binary_image = np.zeros((100, 100), dtype=np.uint8)
        binary_image[50:, :] = 255
        assert self.normalizer._too_many_midtones(binary_image) == False
    
    def test_sauvola_binarization(self):
        """Test Sauvola binarization implementation."""
        # Create test image
        image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        binary = self.normalizer._sauvola_binarization(image)
        
        # Should produce binary image
        assert binary.dtype == np.uint8
        assert np.all(np.isin(binary, [0, 255]))
        assert binary.shape == image.shape
    
    def test_normalize_percentage_tokens(self):
        """Test percentage token normalization."""
        test_cases = [
            ("45°", "45%"),
            ("45·", "45%"),
            ("45o/o", "45%"),
            ("45O/O", "45%"),
            ("45° 32· 12o/o", "45% 32% 12%"),
            ("normal text", "normal text"),
            ("", "")
        ]
        
        for input_text, expected in test_cases:
            result = self.normalizer.normalize_percentage_tokens(input_text)
            assert result == expected, f"Failed for input: {input_text}"


class TestHeroResolverRobustness:
    """Test hero resolver robustness features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.hero_resolver = AdvancedHeroResolver()
    
    def test_is_partial_crop_detection(self):
        """Test partial crop detection."""
        # Small crop (should be detected as partial)
        small_crop = np.random.randint(0, 255, (20, 20, 3), dtype=np.uint8)
        assert self.hero_resolver._is_partial_crop(small_crop) == True
        
        # Large crop (should not be detected as partial)
        large_crop = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        assert self.hero_resolver._is_partial_crop(large_crop) == False
        
        # Corner crop with high edge variance
        corner_crop = np.zeros((64, 64, 3), dtype=np.uint8)
        corner_crop[:32, :32] = 255  # High contrast corner
        assert self.hero_resolver._is_partial_crop(corner_crop) == True
    
    def test_reflect_pad_crop(self):
        """Test reflection padding for partial crops."""
        # Create test crop
        crop = np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8)
        
        padded = self.hero_resolver._reflect_pad_crop(crop, pad=8)
        
        # Should be larger than original
        assert padded.shape[0] > crop.shape[0]
        assert padded.shape[1] > crop.shape[1]
        assert padded.shape[2] == crop.shape[2]
        
        # Should maintain data type
        assert padded.dtype == crop.dtype
    
    def test_phash_filter_with_config(self):
        """Test phash filtering with configurable threshold."""
        # Create test crop
        crop = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        
        # Mock the phash database
        self.hero_resolver.phash_database = {
            "kagura": 0x1234567890ABCDEF,
            "lancelot": 0xFEDCBA0987654321
        }
        
        # Mock phash computation
        with patch.object(self.hero_resolver, '_compute_phash', return_value=0x1234567890ABCDEF):
            candidates = self.hero_resolver._phash_filter(crop)
            
            # Should find candidates based on threshold
            assert isinstance(candidates, list)
            # Exact match should be found
            assert "kagura" in candidates


class TestRobustnessIntegration:
    """Integration tests for robustness features."""
    
    def test_end_to_end_robustness_pipeline(self):
        """Test end-to-end robustness pipeline."""
        # Create test image
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Test drift guards
        config = RobustnessConfig()
        drift_guards = DetectorDriftGuards(config)
        
        # Test normalizer
        normalizer = AdaptiveNormalizer(config)
        
        # Test hero resolver
        hero_resolver = AdvancedHeroResolver()
        
        # Test synthetic transforms
        from backend.ocr.synthetic_transforms import synthetic_transform_generator
        
        # Generate transforms
        transforms = synthetic_transform_generator.generate_transform_matrix(image, max_transforms=3)
        assert len(transforms) <= 3
        
        # Apply transforms
        for transform in transforms:
            transformed = synthetic_transform_generator.apply_transform(image, transform)
            assert transformed.shape[2] == image.shape[2]  # Same channels
            assert transformed.dtype == image.dtype
    
    def test_telemetry_logging(self):
        """Test drift telemetry logging."""
        from backend.ocr.robustness import drift_telemetry_logger, DriftTelemetry
        
        # Create test telemetry
        telemetry = DriftTelemetry(
            row_variance=0.05,
            anchors_used=["victory", "kda"],
            ign_score=0.9,
            hero_conf=0.85,
            phash_dist=8,
            cache_hits=5,
            stage_ms={"detection": 50.0, "parsing": 30.0},
            drift_warnings=["High variance detected"],
            corrective_actions=["Applied regularization"]
        )
        
        # Test logging (should not raise exceptions)
        with patch('backend.ocr.robustness.logger') as mock_logger:
            drift_telemetry_logger.log_analysis_telemetry(telemetry)
            assert mock_logger.warning.called or mock_logger.info.called


if __name__ == "__main__":
    pytest.main([__file__])
