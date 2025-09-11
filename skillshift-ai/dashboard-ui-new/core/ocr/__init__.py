"""
OCR Module for Mission 3
High-performance OCR system with <500ms processing time.
"""
from .optimized_roi_processor import OptimizedROIProcessor, FastTableDetector
from .ocr_cache import OCRCache, PerformanceOptimizedCache, get_global_cache
from .ocr_reader import get_reader, get_optimized_reader, get_reader_stats
from .fast_table_detector import FastTableDetector, ProjectionBasedDetector
from .early_exit_fusion import EarlyExitFusion
from .config import OCRConfiguration, get_global_config, load_config_from_file

__all__ = [
    'OptimizedROIProcessor',
    'FastTableDetector', 
    'ProjectionBasedDetector',
    'OCRCache',
    'PerformanceOptimizedCache',
    'get_global_cache',
    'get_reader',
    'get_optimized_reader',
    'get_reader_stats',
    'EarlyExitFusion',
    'OCRConfiguration',
    'get_global_config',
    'load_config_from_file'
]
