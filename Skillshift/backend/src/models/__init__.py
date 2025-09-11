"""
OCR Models Package
"""

from .ocr import (
    OCRExtractionResult,
    PlayerDetectionResult,
    RegionDetectionResult,
    CrossViewFusionResult,
    OCRConfiguration,
    OCRProcessingStats,
    OCRDebugInfo,
)

__all__ = [
    "OCRExtractionResult",
    "PlayerDetectionResult", 
    "RegionDetectionResult",
    "CrossViewFusionResult",
    "OCRConfiguration",
    "OCRProcessingStats",
    "OCRDebugInfo",
]