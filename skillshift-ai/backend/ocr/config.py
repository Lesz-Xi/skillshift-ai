"""
OCR Mission 5: Configuration Management

Configuration switches for robust mode, variance thresholds, and bbox expansion
with conservative defaults for production deployment.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class OCRMission5Config:
    """
    OCR Mission 5 configuration with conservative defaults.
    
    All robustness features are configurable with safe defaults for production.
    """
    # Robust mode toggle
    robust_mode: bool = True
    
    # Grid variance thresholds
    grid_variance_warn: float = 0.015
    grid_variance_correct: float = 0.03
    
    # Bbox expansion for letterboxing/crop tolerance
    bbox_expand_pct: float = 0.03
    
    # Hero resolver thresholds
    phash_threshold: int = 12
    
    # Adaptive binarization
    use_sauvola_fallback: bool = True
    
    # Drift telemetry
    enable_drift_telemetry: bool = True
    
    # Anchor consensus
    min_anchor_consensus: int = 2
    
    # Performance limits
    max_processing_time_ms: int = 500
    target_processing_time_ms: int = 250
    
    # Debug and logging
    enable_debug_logging: bool = False
    log_drift_warnings: bool = True
    
    # Feature toggles
    enable_adaptive_binarization: bool = True
    enable_percentage_normalization: bool = True
    enable_hero_skin_detection: bool = True
    enable_partial_crop_handling: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'OCRMission5Config':
        """Create config from dictionary."""
        return cls(**config_dict)
    
    def save_to_file(self, file_path: str):
        """Save config to JSON file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.info(f"Config saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving config to {file_path}: {e}")
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'OCRMission5Config':
        """Load config from JSON file."""
        try:
            with open(file_path, 'r') as f:
                config_dict = json.load(f)
            return cls.from_dict(config_dict)
        except Exception as e:
            logger.warning(f"Error loading config from {file_path}: {e}, using defaults")
            return cls()


# Global configuration instance
ocr_config = OCRMission5Config()

# Convenience functions
def get_config() -> OCRMission5Config:
    """Get current OCR Mission 5 configuration."""
    return ocr_config

def is_robust_mode_enabled() -> bool:
    """Check if robust mode is enabled."""
    return get_config().robust_mode

def is_drift_telemetry_enabled() -> bool:
    """Check if drift telemetry is enabled."""
    return get_config().enable_drift_telemetry

def get_performance_limits() -> tuple:
    """Get performance limits (max_ms, target_ms)."""
    config = get_config()
    return config.max_processing_time_ms, config.target_processing_time_ms