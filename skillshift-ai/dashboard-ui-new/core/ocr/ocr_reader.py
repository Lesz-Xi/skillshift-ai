"""
Singleton OCR Reader for Mission 3
Implements thread-safe singleton with warmup for optimal performance.
"""
import os
import logging
import threading
import time
from typing import Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

# Global reader instance
_READER = None
_READER_LOCK = threading.Lock()
_READER_STATS = {
    'initialization_time': 0.0,
    'access_count': 0,
    'warmup_complete': False,
    'last_access': 0.0
}


def get_reader():
    """
    Get singleton EasyOCR reader instance with lazy initialization and warmup.
    
    Returns:
        EasyOCR reader instance
    """
    global _READER, _READER_STATS
    
    if _READER is None:
        with _READER_LOCK:
            if _READER is None:
                _initialize_reader()
    
    # Update access statistics
    _READER_STATS['access_count'] += 1
    _READER_STATS['last_access'] = time.time()
    
    return _READER


def _initialize_reader():
    """Initialize the OCR reader with performance optimizations."""
    global _READER, _READER_STATS
    
    try:
        start_time = time.time()
        logger.info("🔄 Initializing EasyOCR reader (one-time setup)...")
        
        # Determine optimal configuration
        use_gpu = _should_use_gpu()
        logger.info(f"Using {'GPU' if use_gpu else 'CPU'} for OCR processing")
        
        # Initialize EasyOCR with optimized settings
        import easyocr
        _READER = easyocr.Reader(
            ['en'],
            gpu=use_gpu,
            verbose=False,  # Reduce logging overhead
            model_storage_directory=None,  # Use default caching
            download_enabled=True,
            detector=True,
            recognizer=True,
        )
        
        # Record initialization time
        _READER_STATS['initialization_time'] = time.time() - start_time
        logger.info(f"✅ OCR reader initialized in {_READER_STATS['initialization_time']:.3f}s")
        
        # Perform warmup
        _warmup_reader()
        
    except Exception as e:
        logger.error(f"Failed to initialize OCR reader: {e}")
        raise


def _should_use_gpu() -> bool:
    """
    Determine if GPU should be used for OCR processing.
    
    Returns:
        True if GPU should be used, False otherwise
    """
    try:
        # Check environment variable first
        gpu_env = os.getenv("OCR_GPU", "").lower()
        if gpu_env in ["1", "true", "yes"]:
            return True
        elif gpu_env in ["0", "false", "no"]:
            return False
        
        # Check for MPS (Apple Silicon) support
        if _has_mps_support():
            logger.info("MPS (Apple Silicon) support detected")
            return True
        
        # Check for CUDA support
        if _has_cuda_support():
            logger.info("CUDA support detected")
            return True
        
        # Default to CPU for stability
        logger.info("Using CPU for OCR processing (default)")
        return False
        
    except Exception as e:
        logger.warning(f"GPU detection failed, using CPU: {e}")
        return False


def _has_mps_support() -> bool:
    """Check if MPS (Apple Silicon) is available."""
    try:
        import torch
        return torch.backends.mps.is_available()
    except ImportError:
        return False
    except Exception:
        return False


def _has_cuda_support() -> bool:
    """Check if CUDA is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False
    except Exception:
        return False


def _warmup_reader():
    """Warm up the OCR reader with a test image."""
    global _READER, _READER_STATS
    
    try:
        logger.info("🔥 Warming up OCR reader...")
        warmup_start = time.time()
        
        # Create a simple test image for warmup
        test_image = np.zeros((64, 64, 3), dtype=np.uint8)
        
        # Add some text-like patterns
        test_image[20:40, 10:50] = 255  # White rectangle
        
        # Perform warmup OCR
        _READER.readtext(test_image, detail=0, paragraph=False)
        
        warmup_time = time.time() - warmup_start
        _READER_STATS['warmup_complete'] = True
        
        logger.info(f"✅ OCR reader warmup complete in {warmup_time:.3f}s")
        
    except Exception as e:
        logger.warning(f"OCR warmup failed: {e}")
        _READER_STATS['warmup_complete'] = False


def get_reader_stats() -> Dict[str, Any]:
    """
    Get OCR reader statistics.
    
    Returns:
        Dictionary with reader statistics
    """
    global _READER_STATS
    
    return {
        'initialized': _READER is not None,
        'initialization_time': _READER_STATS['initialization_time'],
        'access_count': _READER_STATS['access_count'],
        'warmup_complete': _READER_STATS['warmup_complete'],
        'last_access': _READER_STATS['last_access'],
        'uptime_seconds': time.time() - _READER_STATS['last_access'] if _READER_STATS['last_access'] > 0 else 0
    }


def reset_reader():
    """Reset the OCR reader (for testing or error recovery)."""
    global _READER, _READER_STATS
    
    with _READER_LOCK:
        _READER = None
        _READER_STATS = {
            'initialization_time': 0.0,
            'access_count': 0,
            'warmup_complete': False,
            'last_access': 0.0
        }
        logger.info("OCR reader reset")


class OptimizedOCRReader:
    """
    Optimized OCR reader wrapper with additional performance features.
    """
    
    def __init__(self):
        self._reader = None
        self._cache = None
        self._performance_metrics = {
            'total_requests': 0,
            'avg_processing_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def get_reader(self):
        """Get the underlying EasyOCR reader."""
        if self._reader is None:
            self._reader = get_reader()
        return self._reader
    
    def readtext_optimized(self, image, allowlist: str = "0123456789/%,.", **kwargs):
        """
        Optimized text reading with performance monitoring.
        
        Args:
            image: Image to process
            allowlist: Characters to allow in OCR
            **kwargs: Additional arguments for readtext
            
        Returns:
            OCR results
        """
        try:
            start_time = time.time()
            
            # Get reader
            reader = self.get_reader()
            
            # Set default parameters for performance
            default_params = {
                'detail': 0,
                'paragraph': False,
                'allowlist': allowlist,
                'width_ths': 0.7,
                'height_ths': 0.7
            }
            
            # Merge with provided kwargs
            params = {**default_params, **kwargs}
            
            # Perform OCR
            results = reader.readtext(image, **params)
            
            # Update performance metrics
            processing_time = time.time() - start_time
            self._update_metrics(processing_time)
            
            return results
            
        except Exception as e:
            logger.error(f"Optimized OCR failed: {e}")
            return []
    
    def _update_metrics(self, processing_time: float):
        """Update performance metrics."""
        self._performance_metrics['total_requests'] += 1
        
        # Update average processing time
        total = self._performance_metrics['total_requests']
        current_avg = self._performance_metrics['avg_processing_time']
        self._performance_metrics['avg_processing_time'] = (
            (current_avg * (total - 1) + processing_time) / total
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            **self._performance_metrics,
            'reader_stats': get_reader_stats()
        }
    
    def batch_process(self, images, allowlist: str = "0123456789/%,."):
        """
        Process multiple images in batch.
        
        Args:
            images: List of images to process
            allowlist: Characters to allow in OCR
            
        Returns:
            List of OCR results
        """
        try:
            reader = self.get_reader()
            results = []
            
            for image in images:
                result = self.readtext_optimized(image, allowlist)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return [[] for _ in images]


# Global optimized reader instance
_optimized_reader = None
_optimized_reader_lock = threading.Lock()


def get_optimized_reader() -> OptimizedOCRReader:
    """Get global optimized OCR reader instance."""
    global _optimized_reader
    
    if _optimized_reader is None:
        with _optimized_reader_lock:
            if _optimized_reader is None:
                _optimized_reader = OptimizedOCRReader()
    
    return _optimized_reader


def reset_optimized_reader():
    """Reset optimized reader instance."""
    global _optimized_reader
    
    with _optimized_reader_lock:
        _optimized_reader = None
