"""
Optimized Analysis Engine for Mission 3
Main integration module that combines all optimizations for <500ms performance.
"""
import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from .config import get_global_config
from .early_exit_fusion import EarlyExitFusion
from .optimized_roi_processor import OptimizedROIProcessor
from .fast_table_detector import FastTableDetector
from .ocr_cache import get_global_cache
from .ocr_reader import get_optimized_reader

logger = logging.getLogger(__name__)


class OptimizedAnalysisEngine:
    """
    Main analysis engine that integrates all Mission 3 optimizations.
    
    Features:
    - ROI-only OCR with digits allowlist
    - Intelligent caching system
    - Early-exit fusion logic
    - Fast table detection
    - Performance monitoring
    - Hardware-optimized processing
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize optimized analysis engine.
        
        Args:
            config: Optional configuration overrides
        """
        # Load configuration
        self.config = get_global_config()
        if config:
            for key, value in config.items():
                self.config.set(key, value)
        
        # Initialize components
        self.roi_processor = OptimizedROIProcessor(
            max_side=self.config.get('roi.max_side', 512),
            min_side=self.config.get('roi.min_side', 64)
        )
        
        self.table_detector = FastTableDetector(
            downscale_size=self.config.get('table_detection.downscale_size', 1280)
        )
        
        self.early_exit_fusion = EarlyExitFusion(
            confidence_threshold=self.config.get('fusion.early_exit_threshold', 0.9),
            max_iterations=self.config.get('fusion.max_iterations', 5),
            enable_performance_monitoring=self.config.get('fusion.enable_performance_monitoring', True)
        )
        
        self.cache = get_global_cache()
        self.reader = get_optimized_reader()
        
        # Performance tracking
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_processing_time': 0.0,
            'early_exit_rate': 0.0,
            'cache_hit_rate': 0.0
        }
        
        logger.info("Optimized Analysis Engine initialized")
    
    def analyze_screenshot(self, 
                          image_path: str, 
                          ign: str,
                          enable_early_exit: bool = True) -> Dict[str, Any]:
        """
        Analyze screenshot with all Mission 3 optimizations.
        
        Args:
            image_path: Path to screenshot
            ign: Player's in-game name
            enable_early_exit: Whether to use early-exit optimization
            
        Returns:
            Analysis result with performance metrics
        """
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        try:
            logger.info(f"Starting analysis for {ign} (request: {request_id})")
            
            # Phase 1: Fast table detection
            table_start = time.time()
            table_result = self.table_detector.detect_table_structure(image_path)
            table_time = (time.time() - table_start) * 1000
            
            if table_result['confidence'] < self.config.get('table_detection.confidence_threshold', 0.3):
                logger.warning("Low table detection confidence, using fallback")
                return self._fallback_analysis(image_path, ign, start_time)
            
            # Phase 2: Early-exit analysis
            if enable_early_exit:
                analysis_result = self.early_exit_fusion.analyze_with_early_exit(
                    image_path, ign, 
                    confidence_threshold=self.config.get('fusion.early_exit_threshold', 0.9)
                )
            else:
                analysis_result = self._full_analysis(image_path, ign, table_result)
            
            # Phase 3: Performance monitoring
            total_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(start_time, True, analysis_result.get('early_exit_used', False))
            
            # Build final result
            result = self._build_final_result(
                analysis_result, 
                table_result, 
                total_time, 
                table_time,
                request_id
            )
            
            logger.info(f"Analysis completed in {total_time:.1f}ms (request: {request_id})")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {ign} (request: {request_id}): {e}")
            self._update_performance_metrics(start_time, False, False)
            return self._error_result(str(e), start_time, request_id)
    
    def _full_analysis(self, image_path: str, ign: str, table_result: Dict[str, Any]) -> Dict[str, Any]:
        """Perform full analysis without early-exit optimization."""
        try:
            # Use existing enhanced data collector for full processing
            from ..enhanced_data_collector import EnhancedDataCollector
            
            collector = EnhancedDataCollector()
            result = collector.analyze_screenshot_with_session(
                image_path=image_path,
                ign=ign
            )
            
            return {
                'found': result.get('confidence', 0.0) > 0.5,
                'confidence': result.get('confidence', 0.0),
                'data': result.get('data', {}),
                'early_exit_used': False
            }
            
        except Exception as e:
            logger.error(f"Full analysis failed: {e}")
            return {
                'found': False,
                'confidence': 0.0,
                'data': {},
                'early_exit_used': False
            }
    
    def _fallback_analysis(self, image_path: str, ign: str, start_time: float) -> Dict[str, Any]:
        """Fallback analysis when main processing fails."""
        try:
            from ..data_collector import DataCollector
            
            collector = DataCollector()
            result = collector.from_screenshot_enhanced(ign, image_path)
            
            total_time = (time.time() - start_time) * 1000
            
            return {
                'data': result.get('data', {}),
                'confidence': 0.5,
                'processing_time_ms': total_time,
                'mvp_score': 0.0,
                'early_exit_used': False,
                'table_detection': {'confidence': 0.0, 'rows_count': 0},
                'warnings': ['Fallback analysis used'],
                'performance': {
                    'total_time_ms': total_time,
                    'table_detection_ms': 0.0,
                    'analysis_ms': total_time,
                    'cache_hits': 0,
                    'early_exit': False
                }
            }
            
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            return self._error_result(f"Fallback analysis failed: {e}", start_time, "fallback")
    
    def _build_final_result(self, 
                           analysis_result: Dict[str, Any], 
                           table_result: Dict[str, Any], 
                           total_time: float,
                           table_time: float,
                           request_id: str) -> Dict[str, Any]:
        """Build final result with all performance metrics."""
        try:
            # Get cache statistics
            cache_stats = self.cache.get_stats()
            
            # Build performance metrics
            performance = {
                'total_time_ms': total_time,
                'table_detection_ms': table_time,
                'analysis_ms': total_time - table_time,
                'cache_hits': cache_stats.get('hits', 0),
                'cache_misses': cache_stats.get('misses', 0),
                'cache_hit_rate': cache_stats.get('hit_rate_percent', 0.0),
                'early_exit': analysis_result.get('early_exit_used', False),
                'request_id': request_id
            }
            
            # Build final result
            result = {
                'data': analysis_result.get('data', {}),
                'confidence': analysis_result.get('confidence', 0.0),
                'processing_time_ms': total_time,
                'mvp_score': analysis_result.get('mvp_score', 0.0),
                'early_exit_used': analysis_result.get('early_exit_used', False),
                'table_detection': {
                    'confidence': table_result.get('confidence', 0.0),
                    'rows_count': table_result.get('rows_count', 0),
                    'columns_count': table_result.get('columns_count', 0)
                },
                'warnings': analysis_result.get('warnings', []),
                'performance': performance
            }
            
            # Add warnings for performance issues
            if total_time > self.config.get('performance.budget_ms', 500):
                result['warnings'].append(f"Processing time exceeded budget: {total_time:.1f}ms")
            
            if result['confidence'] < 0.85:
                result['warnings'].append(f"Low confidence: {result['confidence']:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Result building failed: {e}")
            return self._error_result(f"Result building failed: {e}", time.time(), request_id)
    
    def _error_result(self, error_message: str, start_time: float, request_id: str) -> Dict[str, Any]:
        """Build error result."""
        total_time = (time.time() - start_time) * 1000
        
        return {
            'data': {},
            'confidence': 0.0,
            'processing_time_ms': total_time,
            'mvp_score': 0.0,
            'early_exit_used': False,
            'table_detection': {'confidence': 0.0, 'rows_count': 0},
            'warnings': [f"Analysis failed: {error_message}"],
            'performance': {
                'total_time_ms': total_time,
                'table_detection_ms': 0.0,
                'analysis_ms': total_time,
                'cache_hits': 0,
                'early_exit': False,
                'request_id': request_id
            },
            'error': error_message
        }
    
    def _update_performance_metrics(self, start_time: float, success: bool, early_exit: bool):
        """Update performance metrics."""
        try:
            processing_time = (time.time() - start_time) * 1000
            
            self.performance_metrics['total_requests'] += 1
            
            if success:
                self.performance_metrics['successful_requests'] += 1
            else:
                self.performance_metrics['failed_requests'] += 1
            
            # Update average processing time
            total = self.performance_metrics['total_requests']
            current_avg = self.performance_metrics['avg_processing_time']
            self.performance_metrics['avg_processing_time'] = (
                (current_avg * (total - 1) + processing_time) / total
            )
            
            # Update early exit rate
            if early_exit:
                early_exits = self.performance_metrics.get('early_exits', 0) + 1
                self.performance_metrics['early_exits'] = early_exits
                self.performance_metrics['early_exit_rate'] = early_exits / total
            
            # Update cache hit rate
            cache_stats = self.cache.get_stats()
            self.performance_metrics['cache_hit_rate'] = cache_stats.get('hit_rate_percent', 0.0)
            
        except Exception as e:
            logger.warning(f"Performance metrics update failed: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        try:
            cache_stats = self.cache.get_stats()
            reader_stats = self.reader.get_performance_metrics()
            
            return {
                'engine_metrics': self.performance_metrics.copy(),
                'cache_metrics': cache_stats,
                'reader_metrics': reader_stats,
                'configuration': {
                    'budget_ms': self.config.get('performance.budget_ms'),
                    'early_exit_enabled': self.config.get('performance.enable_early_exit'),
                    'caching_enabled': self.config.get('performance.enable_caching'),
                    'hardware_backend': self.config.get_hardware_config()['gpu_backend']
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}
    
    def reset_metrics(self):
        """Reset all performance metrics."""
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_processing_time': 0.0,
            'early_exit_rate': 0.0,
            'cache_hit_rate': 0.0
        }
        
        # Reset component metrics
        self.cache.clear_cache()
        self.early_exit_fusion.reset_metrics()
        
        logger.info("Performance metrics reset")
    
    def warmup(self, test_images: Optional[List[str]] = None):
        """Warm up the analysis engine with test images."""
        try:
            logger.info("Warming up analysis engine...")
            
            # Warm up OCR reader
            self.reader.get_reader()
            
            # Warm up cache with test images
            if test_images:
                import numpy as np
                test_arrays = []
                for img_path in test_images:
                    try:
                        import cv2
                        img = cv2.imread(img_path)
                        if img is not None:
                            test_arrays.append(img)
                    except Exception as e:
                        logger.warning(f"Failed to load test image {img_path}: {e}")
                
                if test_arrays:
                    self.cache.warmup_cache(test_arrays)
            
            logger.info("Analysis engine warmup complete")
            
        except Exception as e:
            logger.warning(f"Engine warmup failed: {e}")


# Global engine instance
_global_engine = None


def get_global_engine() -> OptimizedAnalysisEngine:
    """Get global optimized analysis engine instance."""
    global _global_engine
    
    if _global_engine is None:
        _global_engine = OptimizedAnalysisEngine()
    
    return _global_engine


def reset_global_engine():
    """Reset global engine instance."""
    global _global_engine
    _global_engine = None
