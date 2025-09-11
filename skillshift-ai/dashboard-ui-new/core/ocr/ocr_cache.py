"""
OCR Cache System for Mission 3
Implements SHA-1 based caching for OCR results with LRU eviction.
"""
import hashlib
import logging
import threading
import time
from functools import lru_cache
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class OCRCache:
    """
    High-performance OCR cache with SHA-1 based keys and LRU eviction.
    
    Features:
    - SHA-1 based cache keys for image content
    - LRU eviction policy
    - Thread-safe operations
    - Performance monitoring
    - Memory-efficient storage
    """
    
    def __init__(self, max_size: int = 4096):
        """
        Initialize OCR cache.
        
        Args:
            max_size: Maximum number of cached entries
        """
        self.max_size = max_size
        self._stash = {}  # SHA-1 key -> (reader, image_data)
        self._access_times = {}  # SHA-1 key -> last access time
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
    
    def _hash_image(self, image: np.ndarray) -> str:
        """
        Generate SHA-1 hash for image content.
        
        Args:
            image: Image array
            
        Returns:
            SHA-1 hash string
        """
        try:
            # Convert to bytes for hashing
            if image.dtype != np.uint8:
                image = image.astype(np.uint8)
            
            # Use memoryview for efficient hashing
            hash_obj = hashlib.sha1()
            hash_obj.update(memoryview(image).tobytes())
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"Image hashing failed: {e}")
            return str(time.time())  # Fallback to timestamp
    
    def _evict_oldest(self):
        """Evict oldest entries when cache is full."""
        with self._lock:
            if len(self._stash) < self.max_size:
                return
            
            # Find oldest entry
            oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
            
            # Remove oldest entry
            if oldest_key in self._stash:
                del self._stash[oldest_key]
            if oldest_key in self._access_times:
                del self._access_times[oldest_key]
            
            self._stats['evictions'] += 1
            logger.debug(f"Evicted cache entry: {oldest_key[:8]}...")
    
    def _update_access_time(self, key: str):
        """Update access time for cache entry."""
        with self._lock:
            self._access_times[key] = time.time()
    
    def get_reader(self):
        """
        Get OCR reader instance (singleton pattern).
        
        Returns:
            EasyOCR reader instance
        """
        try:
            from .ocr_reader import get_reader
            return get_reader()
        except ImportError:
            # Fallback to direct initialization
            import easyocr
            return easyocr.Reader(['en'], gpu=False)
    
    @lru_cache(maxsize=4096)
    def _cached_readtext(self, key: str, allowlist: str) -> List[str]:
        """
        Cached OCR text extraction.
        
        Args:
            key: SHA-1 cache key
            allowlist: Characters to allow in OCR
            
        Returns:
            List of extracted text strings
        """
        try:
            with self._lock:
                if key not in self._stash:
                    raise KeyError(f"Cache key not found: {key}")
                
                reader, image = self._stash[key]
                
                # Perform OCR with allowlist
                results = reader.readtext(
                    image, 
                    detail=0, 
                    paragraph=False, 
                    allowlist=allowlist
                )
                
                # Update access time
                self._update_access_time(key)
                
                return list(results)
                
        except Exception as e:
            logger.error(f"Cached OCR failed: {e}")
            return []
    
    def cached_readtext(self, reader, image: np.ndarray, allowlist: str = "0123456789/%,.") -> List[str]:
        """
        Perform cached OCR on image with allowlist.
        
        Args:
            reader: EasyOCR reader instance
            image: Image array
            allowlist: Characters to allow in OCR
            
        Returns:
            List of extracted text strings
        """
        try:
            # Generate cache key
            key = self._hash_image(image)
            
            # Check if already cached
            with self._lock:
                if key in self._stash:
                    self._stats['hits'] += 1
                    self._stats['total_requests'] += 1
                    logger.debug(f"Cache hit: {key[:8]}...")
                else:
                    self._stats['misses'] += 1
                    self._stats['total_requests'] += 1
                    logger.debug(f"Cache miss: {key[:8]}...")
                    
                    # Evict if necessary
                    if len(self._stash) >= self.max_size:
                        self._evict_oldest()
                    
                    # Store in cache
                    self._stash[key] = (reader, image.copy())
                    self._update_access_time(key)
            
            # Perform cached OCR
            return self._cached_readtext(key, allowlist)
            
        except Exception as e:
            logger.error(f"Cached OCR failed: {e}")
            # Fallback to direct OCR
            try:
                results = reader.readtext(
                    image, 
                    detail=0, 
                    paragraph=False, 
                    allowlist=allowlist
                )
                return list(results)
            except Exception as fallback_error:
                logger.error(f"Fallback OCR also failed: {fallback_error}")
                return []
    
    def clear_cache(self):
        """Clear all cached entries."""
        with self._lock:
            self._stash.clear()
            self._access_times.clear()
            self._cached_readtext.cache_clear()
            logger.info("OCR cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._stats['total_requests']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'cache_size': len(self._stash),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate_percent': round(hit_rate, 2),
                'evictions': self._stats['evictions'],
                'total_requests': total_requests
            }
    
    def warmup_cache(self, images: List[np.ndarray], allowlist: str = "0123456789/%,."):
        """
        Warm up cache with common images.
        
        Args:
            images: List of images to pre-cache
            allowlist: Characters to allow in OCR
        """
        try:
            reader = self.get_reader()
            
            for i, image in enumerate(images):
                try:
                    self.cached_readtext(reader, image, allowlist)
                    logger.debug(f"Warmed up cache with image {i+1}/{len(images)}")
                except Exception as e:
                    logger.warning(f"Failed to warm up image {i+1}: {e}")
            
            logger.info(f"Cache warmup complete: {len(images)} images processed")
            
        except Exception as e:
            logger.error(f"Cache warmup failed: {e}")


class PerformanceOptimizedCache(OCRCache):
    """
    Performance-optimized OCR cache with additional optimizations.
    """
    
    def __init__(self, max_size: int = 4096, preload_common_patterns: bool = True):
        """
        Initialize performance-optimized cache.
        
        Args:
            max_size: Maximum number of cached entries
            preload_common_patterns: Whether to preload common OCR patterns
        """
        super().__init__(max_size)
        self.preload_common_patterns = preload_common_patterns
        
        if preload_common_patterns:
            self._preload_common_patterns()
    
    def _preload_common_patterns(self):
        """Preload common OCR patterns for faster processing."""
        try:
            # Create common pattern images
            common_patterns = []
            
            # Create images with common MLBB text patterns
            patterns = [
                "Victory", "Defeat", "MVP", "Legendary",
                "9/2/12", "15/3/8", "5/7/4",
                "45,230", "67,551", "23,456",
                "85%", "92%", "78%"
            ]
            
            for pattern in patterns:
                # Create a simple text image (placeholder)
                # In real implementation, this would be actual text rendering
                img = np.zeros((32, len(pattern) * 8, 3), dtype=np.uint8)
                common_patterns.append(img)
            
            # Warm up cache with common patterns
            self.warmup_cache(common_patterns)
            logger.info("Preloaded common OCR patterns")
            
        except Exception as e:
            logger.warning(f"Failed to preload common patterns: {e}")
    
    def batch_process(self, images: List[np.ndarray], allowlist: str = "0123456789/%,.") -> List[List[str]]:
        """
        Process multiple images in batch for optimal performance.
        
        Args:
            images: List of images to process
            allowlist: Characters to allow in OCR
            
        Returns:
            List of OCR results for each image
        """
        try:
            reader = self.get_reader()
            results = []
            
            for image in images:
                result = self.cached_readtext(reader, image, allowlist)
                results.append(result)
            
            logger.debug(f"Batch processed {len(images)} images")
            return results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return [[] for _ in images]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get detailed performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        base_stats = self.get_stats()
        
        # Add performance-specific metrics
        performance_metrics = {
            **base_stats,
            'cache_efficiency': self._calculate_cache_efficiency(),
            'memory_usage_mb': self._estimate_memory_usage(),
            'avg_access_time_ms': self._calculate_avg_access_time()
        }
        
        return performance_metrics
    
    def _calculate_cache_efficiency(self) -> float:
        """Calculate cache efficiency score."""
        with self._lock:
            if self._stats['total_requests'] == 0:
                return 0.0
            
            hit_rate = self._stats['hits'] / self._stats['total_requests']
            size_efficiency = len(self._stash) / self.max_size
            
            # Weighted efficiency score
            return (hit_rate * 0.7 + size_efficiency * 0.3)
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB."""
        with self._lock:
            total_bytes = 0
            for reader, image in self._stash.values():
                total_bytes += image.nbytes
            
            return total_bytes / (1024 * 1024)  # Convert to MB
    
    def _calculate_avg_access_time(self) -> float:
        """Calculate average access time (placeholder)."""
        # This would require timing measurements in real implementation
        return 0.0


# Global cache instance
_global_cache = None
_cache_lock = threading.Lock()


def get_global_cache() -> OCRCache:
    """Get global OCR cache instance (singleton)."""
    global _global_cache
    
    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = PerformanceOptimizedCache()
    
    return _global_cache


def reset_global_cache():
    """Reset global cache instance."""
    global _global_cache
    
    with _cache_lock:
        if _global_cache is not None:
            _global_cache.clear_cache()
        _global_cache = None
