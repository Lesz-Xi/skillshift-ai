# /backend/tests/unit/ocr/test_config.py
"""
Unit tests for OCR configuration module.

Tests configuration loading, validation, serialization, and default values.
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from backend.src.models.ocr import OCRConfiguration
from backend.ocr.config import (
    OCRMission5Config,
    get_config,
    is_robust_mode_enabled,
    is_drift_telemetry_enabled,
    get_performance_limits
)


class TestDetectionConfig:
    """Test DetectionConfig dataclass."""
    
    def test_default_values(self):
        """Test that DetectionConfig has correct default values."""
        config = DetectionConfig()
        
        assert config.table_confidence_threshold == 0.7
        assert config.min_table_area == 10000
        assert config.max_table_area == 1000000
        assert config.min_row_height == 30
        assert config.max_row_height == 200
        assert config.row_spacing_tolerance == 5
        assert config.anchor_confidence_threshold == 0.8
        assert config.required_anchors == ["Hero Damage", "Victory", "Defeat", "MVP"]
        assert config.ign_similarity_threshold == 0.85
        assert config.ign_fuzzy_threshold == 80
    
    def test_custom_values(self):
        """Test DetectionConfig with custom values."""
        config = DetectionConfig(
            table_confidence_threshold=0.8,
            min_table_area=5000,
            max_table_area=2000000,
            min_row_height=25,
            max_row_height=250,
            row_spacing_tolerance=10,
            anchor_confidence_threshold=0.9,
            required_anchors=["Custom Anchor"],
            ign_similarity_threshold=0.9,
            ign_fuzzy_threshold=90,
        )
        
        assert config.table_confidence_threshold == 0.8
        assert config.min_table_area == 5000
        assert config.max_table_area == 2000000
        assert config.min_row_height == 25
        assert config.max_row_height == 250
        assert config.row_spacing_tolerance == 10
        assert config.anchor_confidence_threshold == 0.9
        assert config.required_anchors == ["Custom Anchor"]
        assert config.ign_similarity_threshold == 0.9
        assert config.ign_fuzzy_threshold == 90


class TestParsingConfig:
    """Test ParsingConfig dataclass."""
    
    def test_default_values(self):
        """Test that ParsingConfig has correct default values."""
        config = ParsingConfig()
        
        assert config.ocr_confidence_threshold == 0.6
        assert config.ocr_gpu_enabled is True
        assert config.ocr_languages == ["en"]
        assert config.normalize_numbers is True
        assert config.normalize_separators is True
        assert config.fix_common_ocr_errors is True
        assert len(config.kda_patterns) == 3
        assert len(config.damage_patterns) == 2
        assert config.hero_similarity_threshold == 0.8
        assert config.hero_fuzzy_threshold == 85
    
    def test_custom_values(self):
        """Test ParsingConfig with custom values."""
        config = ParsingConfig(
            ocr_confidence_threshold=0.7,
            ocr_gpu_enabled=False,
            ocr_languages=["en", "es"],
            normalize_numbers=False,
            normalize_separators=False,
            fix_common_ocr_errors=False,
            kda_patterns=["custom_pattern"],
            damage_patterns=["custom_damage"],
            hero_similarity_threshold=0.9,
            hero_fuzzy_threshold=95,
        )
        
        assert config.ocr_confidence_threshold == 0.7
        assert config.ocr_gpu_enabled is False
        assert config.ocr_languages == ["en", "es"]
        assert config.normalize_numbers is False
        assert config.normalize_separators is False
        assert config.fix_common_ocr_errors is False
        assert config.kda_patterns == ["custom_pattern"]
        assert config.damage_patterns == ["custom_damage"]
        assert config.hero_similarity_threshold == 0.9
        assert config.hero_fuzzy_threshold == 95


class TestFusionConfig:
    """Test FusionConfig dataclass."""
    
    def test_default_values(self):
        """Test that FusionConfig has correct default values."""
        config = FusionConfig()
        
        assert config.kda_weight == 0.6
        assert config.damage_weight == 0.4
        assert config.prefer_kda_for_stats is True
        assert config.prefer_damage_for_damage is True
        assert config.min_fusion_confidence == 0.7
        assert config.validate_kda_range is True
        assert config.max_kills == 50
        assert config.max_deaths == 20
        assert config.max_assists == 50
    
    def test_custom_values(self):
        """Test FusionConfig with custom values."""
        config = FusionConfig(
            kda_weight=0.7,
            damage_weight=0.3,
            prefer_kda_for_stats=False,
            prefer_damage_for_damage=False,
            min_fusion_confidence=0.8,
            validate_kda_range=False,
            max_kills=100,
            max_deaths=50,
            max_assists=100,
        )
        
        assert config.kda_weight == 0.7
        assert config.damage_weight == 0.3
        assert config.prefer_kda_for_stats is False
        assert config.prefer_damage_for_damage is False
        assert config.min_fusion_confidence == 0.8
        assert config.validate_kda_range is False
        assert config.max_kills == 100
        assert config.max_deaths == 50
        assert config.max_assists == 100


class TestPerformanceConfig:
    """Test PerformanceConfig dataclass."""
    
    def test_default_values(self):
        """Test that PerformanceConfig has correct default values."""
        config = PerformanceConfig()
        
        assert config.detection_timeout_ms == 2000
        assert config.parsing_timeout_ms == 3000
        assert config.fusion_timeout_ms == 1000
        assert config.max_image_size_mb == 50
        assert config.enable_image_compression is True
        assert config.compression_quality == 85
        assert config.enable_result_caching is True
        assert config.cache_ttl_seconds == 3600
        assert config.max_cache_size_mb == 500
    
    def test_custom_values(self):
        """Test PerformanceConfig with custom values."""
        config = PerformanceConfig(
            detection_timeout_ms=5000,
            parsing_timeout_ms=10000,
            fusion_timeout_ms=2000,
            max_image_size_mb=100,
            enable_image_compression=False,
            compression_quality=95,
            enable_result_caching=False,
            cache_ttl_seconds=7200,
            max_cache_size_mb=1000,
        )
        
        assert config.detection_timeout_ms == 5000
        assert config.parsing_timeout_ms == 10000
        assert config.fusion_timeout_ms == 2000
        assert config.max_image_size_mb == 100
        assert config.enable_image_compression is False
        assert config.compression_quality == 95
        assert config.enable_result_caching is False
        assert config.cache_ttl_seconds == 7200
        assert config.max_cache_size_mb == 1000


class TestOCRConfiguration:
    """Test OCRConfiguration main class."""
    
    def test_default_initialization(self):
        """Test OCRConfiguration with default values."""
        config = OCRConfiguration()
        
        assert isinstance(config.detection, DetectionConfig)
        assert isinstance(config.parsing, ParsingConfig)
        assert isinstance(config.fusion, FusionConfig)
        assert isinstance(config.performance, PerformanceConfig)
        assert config.debug_mode is False
        assert config.log_level == "INFO"
        assert config.output_format == "json"
    
    def test_custom_initialization(self):
        """Test OCRConfiguration with custom values."""
        detection = DetectionConfig(table_confidence_threshold=0.9)
        parsing = ParsingConfig(ocr_confidence_threshold=0.8)
        fusion = FusionConfig(kda_weight=0.7)
        performance = PerformanceConfig(detection_timeout_ms=5000)
        
        config = OCRConfiguration(
            detection=detection,
            parsing=parsing,
            fusion=fusion,
            performance=performance,
            debug_mode=True,
            log_level="DEBUG",
            output_format="yaml",
        )
        
        assert config.detection.table_confidence_threshold == 0.9
        assert config.parsing.ocr_confidence_threshold == 0.8
        assert config.fusion.kda_weight == 0.7
        assert config.performance.detection_timeout_ms == 5000
        assert config.debug_mode is True
        assert config.log_level == "DEBUG"
        assert config.output_format == "yaml"
    
    def test_to_dict(self):
        """Test configuration serialization to dictionary."""
        config = OCRConfiguration()
        config_dict = config.to_dict()
        
        assert "detection" in config_dict
        assert "parsing" in config_dict
        assert "fusion" in config_dict
        assert "performance" in config_dict
        assert "global" in config_dict
        
        # Check detection values
        assert config_dict["detection"]["table_confidence_threshold"] == 0.7
        assert config_dict["detection"]["min_table_area"] == 10000
        
        # Check parsing values
        assert config_dict["parsing"]["ocr_confidence_threshold"] == 0.6
        assert config_dict["parsing"]["ocr_gpu_enabled"] is True
        
        # Check fusion values
        assert config_dict["fusion"]["kda_weight"] == 0.6
        assert config_dict["fusion"]["damage_weight"] == 0.4
        
        # Check performance values
        assert config_dict["performance"]["detection_timeout_ms"] == 2000
        assert config_dict["performance"]["parsing_timeout_ms"] == 3000
        
        # Check global values
        assert config_dict["global"]["debug_mode"] is False
        assert config_dict["global"]["log_level"] == "INFO"
        assert config_dict["global"]["output_format"] == "json"
    
    def test_from_dict(self):
        """Test configuration creation from dictionary."""
        config_dict = {
            "detection": {
                "table_confidence_threshold": 0.8,
                "min_table_area": 5000,
                "max_table_area": 2000000,
            },
            "parsing": {
                "ocr_confidence_threshold": 0.7,
                "ocr_gpu_enabled": False,
                "ocr_languages": ["en", "es"],
            },
            "fusion": {
                "kda_weight": 0.7,
                "damage_weight": 0.3,
                "min_fusion_confidence": 0.8,
            },
            "performance": {
                "detection_timeout_ms": 5000,
                "parsing_timeout_ms": 10000,
                "max_image_size_mb": 100,
            },
            "global": {
                "debug_mode": True,
                "log_level": "DEBUG",
                "output_format": "yaml",
            }
        }
        
        config = OCRConfiguration.from_dict(config_dict)
        
        assert config.detection.table_confidence_threshold == 0.8
        assert config.detection.min_table_area == 5000
        assert config.detection.max_table_area == 2000000
        
        assert config.parsing.ocr_confidence_threshold == 0.7
        assert config.parsing.ocr_gpu_enabled is False
        assert config.parsing.ocr_languages == ["en", "es"]
        
        assert config.fusion.kda_weight == 0.7
        assert config.fusion.damage_weight == 0.3
        assert config.fusion.min_fusion_confidence == 0.8
        
        assert config.performance.detection_timeout_ms == 5000
        assert config.performance.parsing_timeout_ms == 10000
        assert config.performance.max_image_size_mb == 100
        
        assert config.debug_mode is True
        assert config.log_level == "DEBUG"
        assert config.output_format == "yaml"
    
    def test_from_dict_partial(self):
        """Test configuration creation from partial dictionary."""
        config_dict = {
            "detection": {
                "table_confidence_threshold": 0.9,
            },
            "global": {
                "debug_mode": True,
            }
        }
        
        config = OCRConfiguration.from_dict(config_dict)
        
        # Custom values
        assert config.detection.table_confidence_threshold == 0.9
        assert config.debug_mode is True
        
        # Default values should be preserved
        assert config.detection.min_table_area == 10000
        assert config.parsing.ocr_confidence_threshold == 0.6
        assert config.fusion.kda_weight == 0.6
        assert config.performance.detection_timeout_ms == 2000
        assert config.log_level == "INFO"
        assert config.output_format == "json"
    
    def test_validation_success(self):
        """Test configuration validation with valid values."""
        config = OCRConfiguration()
        errors = config.validate()
        assert len(errors) == 0
    
    def test_validation_errors(self):
        """Test configuration validation with invalid values."""
        config = OCRConfiguration()
        
        # Invalid confidence thresholds
        config.detection.table_confidence_threshold = 1.5
        config.parsing.ocr_confidence_threshold = -0.1
        config.fusion.kda_weight = 1.5
        config.fusion.damage_weight = 0.8  # Sum > 1.0
        
        # Invalid area values
        config.detection.min_table_area = 10000
        config.detection.max_table_area = 5000  # Less than min
        
        # Invalid row heights
        config.detection.min_row_height = 50
        config.detection.max_row_height = 20  # Less than min
        
        # Invalid timeouts
        config.performance.detection_timeout_ms = 0
        config.performance.parsing_timeout_ms = -1000
        
        # Invalid compression quality
        config.performance.compression_quality = 150
        
        # Invalid languages
        config.parsing.ocr_languages = []
        
        errors = config.validate()
        
        assert len(errors) > 0
        assert any("table_confidence_threshold must be between 0.0 and 1.0" in error for error in errors)
        assert any("ocr_confidence_threshold must be between 0.0 and 1.0" in error for error in errors)
        assert any("kda_weight must be between 0.0 and 1.0" in error for error in errors)
        assert any("kda_weight and damage_weight must sum to 1.0" in error for error in errors)
        assert any("max_table_area must be greater than min_table_area" in error for error in errors)
        assert any("max_row_height must be greater than min_row_height" in error for error in errors)
        assert any("detection_timeout_ms must be positive" in error for error in errors)
        assert any("parsing_timeout_ms must be positive" in error for error in errors)
        assert any("compression_quality must be between 1 and 100" in error for error in errors)
        assert any("ocr_languages cannot be empty" in error for error in errors)
    
    def test_save_and_load_file(self):
        """Test saving and loading configuration to/from file."""
        config = OCRConfiguration()
        config.debug_mode = True
        config.detection.table_confidence_threshold = 0.9
        config.parsing.ocr_confidence_threshold = 0.8
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            # Save configuration
            config.save_to_file(config_path)
            
            # Load configuration
            loaded_config = OCRConfiguration.from_file(config_path)
            
            assert loaded_config.debug_mode is True
            assert loaded_config.detection.table_confidence_threshold == 0.9
            assert loaded_config.parsing.ocr_confidence_threshold == 0.8
            
            # Check that all other values are preserved
            assert loaded_config.detection.min_table_area == 10000
            assert loaded_config.parsing.ocr_gpu_enabled is True
            assert loaded_config.fusion.kda_weight == 0.6
            assert loaded_config.performance.detection_timeout_ms == 2000
            
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_load_nonexistent_file(self):
        """Test loading configuration from nonexistent file."""
        with pytest.raises(FileNotFoundError):
            OCRConfiguration.from_file("nonexistent_config.yaml")


class TestGlobalConfiguration:
    """Test global configuration management functions."""
    
    def test_get_config_default(self):
        """Test getting default configuration."""
        reset_config()
        config = get_config()
        
        assert isinstance(config, OCRConfiguration)
        assert config.debug_mode is False
        assert config.log_level == "INFO"
    
    def test_set_config(self):
        """Test setting custom configuration."""
        custom_config = OCRConfiguration()
        custom_config.debug_mode = True
        custom_config.log_level = "DEBUG"
        
        set_config(custom_config)
        retrieved_config = get_config()
        
        assert retrieved_config is custom_config
        assert retrieved_config.debug_mode is True
        assert retrieved_config.log_level == "DEBUG"
    
    def test_reset_config(self):
        """Test resetting configuration to defaults."""
        custom_config = OCRConfiguration()
        custom_config.debug_mode = True
        set_config(custom_config)
        
        reset_config()
        config = get_config()
        
        assert config is not custom_config
        assert config.debug_mode is False
        assert config.log_level == "INFO"
    
    def test_load_config_from_file(self):
        """Test loading configuration from file and setting as global."""
        config_dict = {
            "detection": {
                "table_confidence_threshold": 0.9,
            },
            "global": {
                "debug_mode": True,
                "log_level": "DEBUG",
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            config_path = f.name
        
        try:
            reset_config()
            config = load_config_from_file(config_path)
            
            assert config.detection.table_confidence_threshold == 0.9
            assert config.debug_mode is True
            assert config.log_level == "DEBUG"
            
            # Verify it's set as global
            global_config = get_config()
            assert global_config is config
            
        finally:
            Path(config_path).unlink(missing_ok=True)


class TestConfigurationIntegration:
    """Test configuration integration with other modules."""
    
    def test_configuration_immutability(self):
        """Test that configuration changes don't affect other instances."""
        config1 = OCRConfiguration()
        config2 = OCRConfiguration()
        
        config1.detection.table_confidence_threshold = 0.9
        config2.detection.table_confidence_threshold = 0.8
        
        assert config1.detection.table_confidence_threshold == 0.9
        assert config2.detection.table_confidence_threshold == 0.8
    
    def test_configuration_serialization_roundtrip(self):
        """Test that configuration can be serialized and deserialized correctly."""
        original_config = OCRConfiguration()
        original_config.debug_mode = True
        original_config.detection.table_confidence_threshold = 0.9
        original_config.parsing.ocr_confidence_threshold = 0.8
        original_config.fusion.kda_weight = 0.7
        original_config.performance.detection_timeout_ms = 5000
        
        # Serialize to dict
        config_dict = original_config.to_dict()
        
        # Deserialize from dict
        restored_config = OCRConfiguration.from_dict(config_dict)
        
        # Verify all values are preserved
        assert restored_config.debug_mode == original_config.debug_mode
        assert restored_config.detection.table_confidence_threshold == original_config.detection.table_confidence_threshold
        assert restored_config.parsing.ocr_confidence_threshold == original_config.parsing.ocr_confidence_threshold
        assert restored_config.fusion.kda_weight == original_config.fusion.kda_weight
        assert restored_config.performance.detection_timeout_ms == original_config.performance.detection_timeout_ms
        
        # Verify all other values are preserved
        assert restored_config.detection.min_table_area == original_config.detection.min_table_area
        assert restored_config.parsing.ocr_gpu_enabled == original_config.parsing.ocr_gpu_enabled
        assert restored_config.fusion.damage_weight == original_config.fusion.damage_weight
        assert restored_config.performance.parsing_timeout_ms == original_config.performance.parsing_timeout_ms
