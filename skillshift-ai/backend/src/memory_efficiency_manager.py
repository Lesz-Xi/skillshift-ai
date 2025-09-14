"""
Mission 6: I/O & Memory Efficiency Optimization System
Implements M6-20A, M6-20B, M6-20C - async I/O, buffer pools, and singleton models
"""

import asyncio
import mmap
import os
import weakref
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from functools import lru_cache
from typing import (
    Any, AsyncGenerator, Callable, Dict, Generator, List, 
    Optional, Tuple, TypeVar, Union, Set
)
import numpy as np
import cv2
import torch
from pathlib import Path
import io
from PIL import Image
import psutil
import time
from enum import Enum


T = TypeVar('T')


class MemoryPriority(Enum):
    """Memory allocation priority levels"""
    CRITICAL = 0    # Cannot fail
    HIGH = 1        # Important but can wait
    MEDIUM = 2      # Normal priority
    LOW = 3         # Can be evicted
    TEMPORARY = 4   # Short-lived, immediate cleanup


@dataclass
class BufferStats:
    """Buffer pool statistics"""
    total_allocated: int = 0
    total_freed: int = 0
    current_usage: int = 0
    peak_usage: int = 0
    hit_rate: float = 0.0
    miss_count: int = 0
    eviction_count: int = 0
    
    def update_hit_rate(self, hits: int, total: int) -> None:
        """Update hit rate based on usage patterns"""
        if total > 0:
            self.hit_rate = hits / total


@dataclass
class MemoryPoolConfig:
    """Configuration for memory pools"""
    max_total_memory: int = 1024 * 1024 * 500  # 500MB default
    max_buffer_size: int = 1024 * 1024 * 50   # 50MB max per buffer
    cleanup_threshold: float = 0.8           # Clean at 80% usage
    eviction_threshold: float = 0.9          # Force eviction at 90%
    gc_interval: float = 30.0                 # GC every 30 seconds


class AsyncImageLoader:
    """Async image loader with memory-mapped files and lazy loading"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._memory_cache = {}
        self._cache_lock = threading.RLock()
        self.stats = {
            'async_loads': 0,
            'cache_hits': 0,
            'memory_mapped_loads': 0,
            'total_bytes_loaded': 0
        }
    
    async def load_image_async(
        self, 
        image_path: Union[str, Path],
        target_size: Optional[Tuple[int, int]] = None,
        use_memory_map: bool = True,
        force_rgb: bool = True
    ) -> np.ndarray:
        """
        Load image asynchronously with memory mapping optimization
        
        Args:
            image_path: Path to image file
            target_size: Optional target size for resizing
            use_memory_map: Use memory mapping for large files
            force_rgb: Convert to RGB format
            
        Returns:
            Loaded image as numpy array
        """
        path = Path(image_path)
        
        # Check cache first
        cache_key = (str(path), target_size, force_rgb)
        with self._cache_lock:
            if cache_key in self._memory_cache:
                self.stats['cache_hits'] += 1
                return self._memory_cache[cache_key]
        
        # Determine if we should use memory mapping
        file_size = path.stat().st_size if path.exists() else 0
        should_memory_map = use_memory_map and file_size > 1024 * 1024  # > 1MB
        
        # Load in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        if should_memory_map:
            image = await loop.run_in_executor(
                self.executor, 
                self._load_with_memory_map, 
                str(path), target_size, force_rgb
            )
            self.stats['memory_mapped_loads'] += 1
        else:
            image = await loop.run_in_executor(
                self.executor,
                self._load_standard,
                str(path), target_size, force_rgb
            )
        
        # Cache result if reasonable size
        image_size = image.nbytes
        if image_size < 10 * 1024 * 1024:  # < 10MB
            with self._cache_lock:
                self._memory_cache[cache_key] = image
                # Limit cache size
                if len(self._memory_cache) > 20:
                    oldest_key = next(iter(self._memory_cache))
                    del self._memory_cache[oldest_key]
        
        self.stats['async_loads'] += 1
        self.stats['total_bytes_loaded'] += image_size
        
        return image
    
    def _load_with_memory_map(
        self, 
        path: str, 
        target_size: Optional[Tuple[int, int]], 
        force_rgb: bool
    ) -> np.ndarray:
        """Load image using memory mapping for zero-copy I/O"""
        try:
            with open(path, 'rb') as f:
                # Create memory map
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    # Load with PIL using memory map
                    with Image.open(io.BytesIO(mm)) as img:
                        if target_size:
                            img = img.resize(target_size, Image.Resampling.LANCZOS)
                        if force_rgb and img.mode != 'RGB':
                            img = img.convert('RGB')
                        return np.array(img)
        except Exception as e:
            # Fallback to standard loading
            return self._load_standard(path, target_size, force_rgb)
    
    def _load_standard(
        self, 
        path: str, 
        target_size: Optional[Tuple[int, int]], 
        force_rgb: bool
    ) -> np.ndarray:
        """Standard image loading with OpenCV"""
        image = cv2.imread(path)
        if image is None:
            raise ValueError(f"Could not load image: {path}")
        
        if target_size:
            image = cv2.resize(image, target_size)
        
        if force_rgb and len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        return image
    
    def get_stats(self) -> Dict[str, Any]:
        """Get loading statistics"""
        return self.stats.copy()
    
    def clear_cache(self) -> None:
        """Clear memory cache"""
        with self._cache_lock:
            self._memory_cache.clear()


class MemoryBuffer:
    """Generic memory buffer with size tracking"""
    
    def __init__(self, size: int, priority: MemoryPriority = MemoryPriority.MEDIUM):
        self.size = size
        self.priority = priority
        self.data = np.empty(size, dtype=np.uint8)
        self.last_used = time.time()
        self.ref_count = 0
    
    def acquire(self) -> np.ndarray:
        """Acquire buffer for use"""
        self.ref_count += 1
        self.last_used = time.time()
        return self.data
    
    def release(self) -> None:
        """Release buffer reference"""
        self.ref_count = max(0, self.ref_count - 1)
    
    def is_free(self) -> bool:
        """Check if buffer is available for reuse"""
        return self.ref_count == 0


class BufferPool:
    """Buffer pool for memory-efficient reuse of image processing buffers with advanced GC"""
    
    def __init__(self, config: MemoryPoolConfig):
        self.config = config
        self.pools: Dict[int, List[MemoryBuffer]] = {}
        self.active_buffers: Dict[int, Set[MemoryBuffer]] = {}
        self.stats = BufferStats()
        self._lock = threading.RLock()
        self._gc_thread = None
        self._adaptive_gc_thread = None
        self._stop_gc = threading.Event()
        self._stop_adaptive_gc = threading.Event()
        
        # Advanced GC tracking
        self._allocation_history = []
        self._memory_pressure_history = []
        self._gc_stats = {
            'aggressive_gc_count': 0,
            'adaptive_gc_count': 0,
            'emergency_gc_count': 0,
            'total_gc_time': 0.0,
            'memory_recovered_gb': 0.0
        }
        
        # Memory pressure monitoring
        self._memory_pressure_threshold = 0.85
        self._emergency_threshold = 0.95
        
        # Start background garbage collection
        self._start_gc_thread()
        self._start_adaptive_gc_thread()
    
    def get_buffer(self, size: int, priority: MemoryPriority = MemoryPriority.MEDIUM) -> MemoryBuffer:
        """Get a buffer of specified size from pool"""
        with self._lock:
            # Round size to nearest power of 2 for better reuse
            pool_size = self._round_to_power_of_2(size)
            
            # Check if we have available buffer
            if pool_size in self.pools:
                for buffer in self.pools[pool_size]:
                    if buffer.is_free() and buffer.priority.value <= priority.value:
                        return buffer
            
            # Create new buffer if we have space
            if self._can_allocate(size):
                buffer = MemoryBuffer(pool_size, priority)
                
                # Add to pool
                if pool_size not in self.pools:
                    self.pools[pool_size] = []
                self.pools[pool_size].append(buffer)
                
                # Update stats
                self.stats.total_allocated += pool_size
                self.stats.current_usage += pool_size
                self.stats.peak_usage = max(self.stats.peak_usage, self.stats.current_usage)
                
                return buffer
            
            # Try to evict and create new buffer
            if self._evict_for_space(size):
                return self.get_buffer(size, priority)
            
            # Fallback: create temporary buffer that won't be pooled
            return MemoryBuffer(size, MemoryPriority.TEMPORARY)
    
    @asynccontextmanager
    async def get_buffer_async(self, size: int, priority: MemoryPriority = MemoryPriority.MEDIUM):
        """Async context manager for buffer usage"""
        buffer = self.get_buffer(size, priority)
        try:
            data = buffer.acquire()
            yield data
        finally:
            buffer.release()
    
    @contextmanager
    def get_buffer_sync(self, size: int, priority: MemoryPriority = MemoryPriority.MEDIUM):
        """Sync context manager for buffer usage"""
        buffer = self.get_buffer(size, priority)
        try:
            data = buffer.acquire()
            yield data
        finally:
            buffer.release()
    
    def _round_to_power_of_2(self, size: int) -> int:
        """Round size to nearest power of 2 for efficient pooling"""
        return 1 << (size - 1).bit_length()
    
    def _can_allocate(self, size: int) -> bool:
        """Check if we can allocate more memory"""
        return (self.stats.current_usage + size) <= self.config.max_total_memory
    
    def _evict_for_space(self, needed_size: int) -> bool:
        """Evict buffers to make space for new allocation"""
        total_freed = 0
        buffers_to_remove = []
        
        # Collect candidates for eviction (lowest priority first)
        candidates = []
        for pool_size, buffers in self.pools.items():
            for buffer in buffers:
                if buffer.is_free():
                    candidates.append((buffer.priority.value, buffer))
        
        # Sort by priority (lower value = higher priority)
        candidates.sort(key=lambda x: x[0])
        
        # Evict until we have enough space or run out of candidates
        for priority, buffer in candidates:
            if self.stats.current_usage - buffer.size + needed_size <= self.config.max_total_memory:
                total_freed += buffer.size
                buffers_to_remove.append(buffer)
                self.stats.eviction_count += 1
                
                if self.stats.current_usage - total_freed + needed_size <= self.config.max_total_memory:
                    break
        
        # Remove evicted buffers
        for buffer in buffers_to_remove:
            self._remove_buffer(buffer)
        
        return total_freed > 0
    
    def _remove_buffer(self, buffer: MemoryBuffer) -> None:
        """Remove buffer from pool"""
        pool_size = buffer.size
        if pool_size in self.pools and buffer in self.pools[pool_size]:
            self.pools[pool_size].remove(buffer)
            self.stats.current_usage -= buffer.size
            self.stats.total_freed += buffer.size
            
            # Remove empty pool
            if not self.pools[pool_size]:
                del self.pools[pool_size]
    
    def _start_gc_thread(self) -> None:
        """Start background garbage collection thread"""
        def gc_worker():
            while not self._stop_gc.wait(self.config.gc_interval):
                self._cleanup_idle_buffers()
        
        self._gc_thread = threading.Thread(target=gc_worker, daemon=True)
        self._gc_thread.start()
    
    def _cleanup_idle_buffers(self) -> None:
        """Clean up idle buffers based on usage patterns"""
        current_time = time.time()
        buffers_to_remove = []
        
        for pool_size, buffers in self.pools.items():
            for buffer in buffers:
                # Remove if idle for more than 5 minutes and low priority
                if (buffer.is_free() and 
                    buffer.priority.value >= MemoryPriority.LOW.value and
                    current_time - buffer.last_used > 300):
                    buffers_to_remove.append(buffer)
        
        for buffer in buffers_to_remove:
            self._remove_buffer(buffer)
    
    def _start_adaptive_gc_thread(self) -> None:
        """Start adaptive garbage collection thread"""
        def adaptive_gc_worker():
            while not self._stop_adaptive_gc.wait(10.0):  # Check every 10 seconds
                self._adaptive_garbage_collection()
        
        self._adaptive_gc_thread = threading.Thread(target=adaptive_gc_worker, daemon=True)
        self._adaptive_gc_thread.start()
    
    def _adaptive_garbage_collection(self) -> None:
        """Adaptive garbage collection based on memory pressure and usage patterns"""
        start_time = time.time()
        
        with self._lock:
            # Calculate current memory pressure
            current_usage_percent = self.stats.current_usage / self.config.max_total_memory
            
            # Track memory pressure history
            self._memory_pressure_history.append({
                'timestamp': time.time(),
                'usage_percent': current_usage_percent,
                'buffer_count': sum(len(buffers) for buffers in self.pools.values())
            })
            
            # Keep only recent history (last 100 entries)
            if len(self._memory_pressure_history) > 100:
                self._memory_pressure_history = self._memory_pressure_history[-100:]
            
            # Determine GC strategy based on pressure
            if current_usage_percent >= self._emergency_threshold:
                # Emergency GC: Aggressive cleanup
                self._emergency_garbage_collection()
                gc_type = 'emergency'
            elif current_usage_percent >= self._memory_pressure_threshold:
                # High pressure: Aggressive cleanup
                self._aggressive_garbage_collection()
                gc_type = 'aggressive'
            elif self._should_adaptive_clean():
                # Normal pressure: Adaptive cleanup based on patterns
                self._pattern_based_cleanup()
                gc_type = 'adaptive'
            else:
                # Low pressure: Standard cleanup only
                return
        
        # Update GC statistics
        gc_time = time.time() - start_time
        self._gc_stats['total_gc_time'] += gc_time
        
        if gc_type == 'aggressive':
            self._gc_stats['aggressive_gc_count'] += 1
        elif gc_type == 'adaptive':
            self._gc_stats['adaptive_gc_count'] += 1
        elif gc_type == 'emergency':
            self._gc_stats['emergency_gc_count'] += 1
    
    def _emergency_garbage_collection(self) -> None:
        """Emergency garbage collection for critical memory situations"""
        logger.warning("🚨 Emergency garbage collection triggered")
        
        memory_before = self.stats.current_usage
        buffers_removed = 0
        
        # Remove ALL free buffers regardless of priority
        buffers_to_remove = []
        for pool_size, buffers in self.pools.items():
            for buffer in buffers:
                if buffer.is_free():
                    buffers_to_remove.append(buffer)
        
        for buffer in buffers_to_remove:
            self._remove_buffer(buffer)
            buffers_removed += 1
        
        # Force Python garbage collection
        import gc
        collected = gc.collect()
        
        memory_after = self.stats.current_usage
        memory_recovered = (memory_before - memory_after) / (1024 * 1024 * 1024)  # GB
        
        self._gc_stats['memory_recovered_gb'] += memory_recovered
        
        logger.warning(
            f"🚨 Emergency GC complete: removed {buffers_removed} buffers, "
            f"recovered {memory_recovered:.2f}GB, collected {collected} Python objects"
        )
    
    def _aggressive_garbage_collection(self) -> None:
        """Aggressive garbage collection for high memory pressure"""
        logger.info("⚡ Aggressive garbage collection triggered")
        
        memory_before = self.stats.current_usage
        buffers_removed = 0
        
        # Remove free buffers with MEDIUM priority or higher
        buffers_to_remove = []
        for pool_size, buffers in self.pools.items():
            for buffer in buffers:
                if buffer.is_free() and buffer.priority.value >= MemoryPriority.MEDIUM.value:
                    buffers_to_remove.append(buffer)
        
        # Also remove old TEMPORARY buffers
        current_time = time.time()
        for pool_size, buffers in self.pools.items():
            for buffer in buffers:
                if (buffer.is_free() and 
                    buffer.priority == MemoryPriority.TEMPORARY and
                    current_time - buffer.last_used > 60):  # 1 minute
                    buffers_to_remove.append(buffer)
        
        for buffer in buffers_to_remove:
            self._remove_buffer(buffer)
            buffers_removed += 1
        
        memory_after = self.stats.current_usage
        memory_recovered = (memory_before - memory_after) / (1024 * 1024 * 1024)  # GB
        
        self._gc_stats['memory_recovered_gb'] += memory_recovered
        
        logger.info(
            f"⚡ Aggressive GC complete: removed {buffers_removed} buffers, "
            f"recovered {memory_recovered:.2f}GB"
        )
    
    def _pattern_based_cleanup(self) -> None:
        """Pattern-based cleanup using historical usage data"""
        logger.debug("🧠 Pattern-based garbage collection")
        
        if len(self._memory_pressure_history) < 10:
            return  # Not enough history
        
        # Analyze usage patterns
        recent_pressure = self._memory_pressure_history[-10:]  # Last 10 measurements
        
        # Calculate trends
        pressure_trend = self._calculate_pressure_trend(recent_pressure)
        buffer_usage_trend = self._calculate_buffer_usage_trend(recent_pressure)
        
        # Clean based on predicted needs
        if pressure_trend > 0.1:  # Rising pressure
            # Remove underutilized buffer sizes
            self._clean_underutilized_pools()
        elif buffer_usage_trend < -0.1:  # Decreasing buffer usage
            # Consolidate similar-sized buffers
            self._consolidate_buffer_pools()
    
    def _calculate_pressure_trend(self, history: List[Dict]) -> float:
        """Calculate memory pressure trend from history"""
        if len(history) < 2:
            return 0.0
        
        pressures = [entry['usage_percent'] for entry in history]
        
        # Simple linear trend (positive = increasing pressure)
        return (pressures[-1] - pressures[0]) / len(pressures)
    
    def _calculate_buffer_usage_trend(self, history: List[Dict]) -> float:
        """Calculate buffer usage trend from history"""
        if len(history) < 2:
            return 0.0
        
        buffer_counts = [entry['buffer_count'] for entry in history]
        
        # Simple linear trend (negative = decreasing usage)
        return (buffer_counts[-1] - buffer_counts[0]) / len(buffer_counts)
    
    def _clean_underutilized_pools(self) -> None:
        """Clean buffer pools that are underutilized"""
        current_time = time.time()
        pools_to_clean = []
        
        for pool_size, buffers in self.pools.items():
            # Check if pool is underutilized
            free_buffers = sum(1 for b in buffers if b.is_free())
            if free_buffers > len(buffers) * 0.7:  # >70% free
                # Check if recently used
                recently_used = any(
                    current_time - b.last_used < 300 for b in buffers
                )
                if not recently_used:
                    pools_to_clean.append(pool_size)
        
        # Remove underutilized pools
        for pool_size in pools_to_clean:
            buffers = self.pools.get(pool_size, [])
            buffers_to_remove = [b for b in buffers if b.is_free()]
            
            for buffer in buffers_to_remove:
                self._remove_buffer(buffer)
            
            logger.debug(f"🧹 Cleaned underutilized pool size {pool_size}: "
                        f"removed {len(buffers_to_remove)} buffers")
    
    def _consolidate_buffer_pools(self) -> None:
        """Consolidate similar-sized buffer pools"""
        pool_sizes = sorted(self.pools.keys())
        
        # Group similar sizes (within 10%)
        consolidated_groups = []
        current_group = [pool_sizes[0]]
        
        for size in pool_sizes[1:]:
            if size <= current_group[-1] * 1.1:  # Within 10%
                current_group.append(size)
            else:
                if len(current_group) > 1:
                    consolidated_groups.append(current_group)
                current_group = [size]
        
        if len(current_group) > 1:
            consolidated_groups.append(current_group)
        
        # Consolidate each group
        for group in consolidated_groups:
            target_size = max(group)  # Use largest size in group
            
            for size in group:
                if size != target_size and size in self.pools:
                    # Move buffers to target pool or remove
                    buffers = self.pools[size]
                    free_buffers = [b for b in buffers if b.is_free()]
                    
                    for buffer in free_buffers:
                        self._remove_buffer(buffer)  # Remove smaller buffer
                    
                    logger.debug(f"🔄 Consolidated pool size {size} into {target_size}")
    
    def _should_adaptive_clean(self) -> bool:
        """Determine if adaptive cleanup should be performed"""
        # Check if we have enough history
        if len(self._memory_pressure_history) < 5:
            return False
        
        # Check for memory pressure patterns
        recent_history = self._memory_pressure_history[-5:]
        avg_pressure = sum(entry['usage_percent'] for entry in recent_history) / len(recent_history)
        
        # Clean if average pressure is above 60%
        return avg_pressure > 0.6
    
    def get_gc_stats(self) -> Dict[str, Any]:
        """Get detailed garbage collection statistics"""
        with self._lock:
            return {
                **self._gc_stats.copy(),
                'current_memory_pressure': self.stats.current_usage / self.config.max_total_memory,
                'memory_pressure_threshold': self._memory_pressure_threshold,
                'emergency_threshold': self._emergency_threshold,
                'active_pools': len(self.pools),
                'total_buffers': sum(len(buffers) for buffers in self.pools.values()),
                'free_buffers': sum(
                    sum(1 for b in buffers if b.is_free()) 
                    for buffers in self.pools.values()
                ),
                'recent_pressure_history': self._memory_pressure_history[-10:] if self._memory_pressure_history else []
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            return {
                'total_allocated': self.stats.total_allocated,
                'total_freed': self.stats.total_freed,
                'current_usage': self.stats.current_usage,
                'peak_usage': self.stats.peak_usage,
                'hit_rate': self.stats.hit_rate,
                'pools': {size: len(buffers) for size, buffers in self.pools.items()},
                'max_memory': self.config.max_total_memory,
                'usage_percent': (self.stats.current_usage / self.config.max_total_memory) * 100
            }
    
    def shutdown(self) -> None:
        """Shutdown buffer pool and cleanup"""
        self._stop_gc.set()
        self._stop_adaptive_gc.set()
        
        if self._gc_thread:
            self._gc_thread.join(timeout=5)
        
        if self._adaptive_gc_thread:
            self._adaptive_gc_thread.join(timeout=5)
        
        with self._lock:
            self.pools.clear()
            
        logger.info("Buffer pool shutdown complete")


class SingletonModelManager:
    """Singleton manager for ML models to prevent redundant loading"""
    
    _instances: Dict[str, 'SingletonModelManager'] = {}
    _lock = threading.RLock()
    
    def __new__(cls, model_type: str):
        with cls._lock:
            if model_type not in cls._instances:
                cls._instances[model_type] = super().__new__(cls)
            return cls._instances[model_type]
    
    def __init__(self, model_type: str):
        if not hasattr(self, '_initialized'):
            self.model_type = model_type
            self._model = None
            self._model_lock = threading.RLock()
            self._load_count = 0
            self._initialized = True
    
    def get_model(self, loader_func: Callable[[], Any]) -> Any:
        """Get singleton model instance"""
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    self._model = loader_func()
                    self._load_count += 1
        return self._model
    
    def get_load_count(self) -> int:
        """Get number of times model was loaded"""
        return self._load_count
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._model is not None
    
    def unload(self) -> None:
        """Unload model to free memory"""
        with self._model_lock:
            if self._model is not None:
                if hasattr(self._model, 'cpu'):
                    self._model.cpu()
                if hasattr(self._model, 'to'):
                    self._model.to('cpu')
                del self._model
                self._model = None
                torch.cuda.empty_cache() if torch.cuda.is_available() else None


class MemoryEfficientImageProcessor:
    """Combines async I/O, buffer pools, and singleton models for efficient processing"""
    
    def __init__(self, config: Optional[MemoryPoolConfig] = None):
        self.config = config or MemoryPoolConfig()
        self.image_loader = AsyncImageLoader()
        self.buffer_pool = BufferPool(self.config)
        self.model_managers = {
            'yolo': SingletonModelManager('yolo'),
            'ocr': SingletonModelManager('ocr')
        }
        self.processing_stats = {
            'total_processed': 0,
            'memory_saved': 0,
            'async_time_saved': 0.0
        }
    
    async def process_image_pipeline(
        self,
        image_path: Union[str, Path],
        processing_steps: List[Callable[[np.ndarray], Any]],
        target_size: Optional[Tuple[int, int]] = None
    ) -> List[Any]:
        """
        Process image through pipeline with memory efficiency
        
        Args:
            image_path: Path to image file
            processing_steps: List of processing functions
            target_size: Optional target size for image
            
        Returns:
            List of processing results
        """
        start_time = time.time()
        
        # Load image asynchronously
        image = await self.image_loader.load_image_async(
            image_path, target_size=target_size
        )
        
        results = []
        for step_func in processing_steps:
            # Get buffer for intermediate processing
            async with self.buffer_pool.get_buffer_async(image.nbytes) as buffer:
                # Copy image to buffer for processing
                np.copyto(buffer, image.ravel())
                reshaped_buffer = buffer.reshape(image.shape)
                
                # Process step
                result = step_func(reshaped_buffer)
                results.append(result)
        
        # Update stats
        processing_time = time.time() - start_time
        self.processing_stats['total_processed'] += 1
        self.processing_stats['async_time_saved'] += max(0, processing_time - 0.1)  # Assume 100ms sync baseline
        
        return results
    
    def get_yolo_model(self, loader_func: Callable[[], Any]) -> Any:
        """Get singleton YOLO model"""
        return self.model_managers['yolo'].get_model(loader_func)
    
    def get_ocr_reader(self, loader_func: Callable[[], Any]) -> Any:
        """Get singleton OCR reader"""
        return self.model_managers['ocr'].get_model(loader_func)
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        return {
            'image_loader': self.image_loader.get_stats(),
            'buffer_pool': self.buffer_pool.get_stats(),
            'processing': self.processing_stats.copy(),
            'models': {
                name: {
                    'loaded': manager.is_loaded(),
                    'load_count': manager.get_load_count()
                }
                for name, manager in self.model_managers.items()
            },
            'system_memory': {
                'available': psutil.virtual_memory().available,
                'total': psutil.virtual_memory().total,
                'percent_used': psutil.virtual_memory().percent
            }
        }
    
    def shutdown(self) -> None:
        """Shutdown and cleanup resources"""
        self.image_loader.clear_cache()
        self.buffer_pool.shutdown()
        
        for manager in self.model_managers.values():
            manager.unload()


# Global instance for application-wide use
_memory_processor: Optional[MemoryEfficientImageProcessor] = None
_processor_lock = threading.RLock()


def get_memory_processor(config: Optional[MemoryPoolConfig] = None) -> MemoryEfficientImageProcessor:
    """Get global memory processor instance"""
    global _memory_processor
    with _processor_lock:
        if _memory_processor is None:
            _memory_processor = MemoryEfficientImageProcessor(config)
        return _memory_processor


def shutdown_memory_processor() -> None:
    """Shutdown global memory processor"""
    global _memory_processor
    with _processor_lock:
        if _memory_processor is not None:
            _memory_processor.shutdown()
            _memory_processor = None