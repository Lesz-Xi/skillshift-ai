#!/usr/bin/env python3
"""
Intelligent Cache System - Task 5 Component
===========================================

Advanced caching system with prediction, cache warming, and analytics
for optimal performance in MLBB Coach AI processing pipeline.

Features:
- Predictive caching based on usage patterns
- Cache warming for popular heroes and scenarios
- Multi-level caching (Memory + Redis)
- Usage pattern analysis and optimization
- Cache analytics and performance monitoring
- Intelligent cache eviction and cleanup
"""

import logging
import time
import asyncio
import threading
import hashlib
import pickle
import json
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque, Counter
from datetime import datetime, timedelta
import weakref
import gc
import os

import numpy as np
import redis
import psutil
from functools import wraps

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache levels for multi-tier caching."""
    L1_MEMORY = "l1_memory"      # Fastest, smallest
    L2_REDIS = "l2_redis"        # Fast, medium size
    L3_DISK = "l3_disk"          # Slower, largest
    PREDICTIVE = "predictive"    # Predictive pre-loading


class CachePriority(Enum):
    """Cache priority levels."""
    CRITICAL = 5    # Never evict
    HIGH = 4        # Evict last
    NORMAL = 3      # Standard eviction
    LOW = 2         # Evict early
    TEMPORARY = 1   # Evict first


@dataclass
class CacheEntry:
    """Enhanced cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    priority: CachePriority
    size_bytes: int
    ttl: float
    tags: List[str] = field(default_factory=list)
    prediction_score: float = 0.0
    source: str = "manual"  # manual, predicted, warmed


@dataclass
class CachePattern:
    """Usage pattern for predictive caching."""
    pattern_id: str
    access_sequence: List[str]
    frequency: int
    time_pattern: Dict[int, int]  # hour -> access count
    user_pattern: Dict[str, int]  # user -> access count
    prediction_accuracy: float = 0.0


class UsagePatternAnalyzer:
    """Analyzes usage patterns for predictive caching."""
    
    def __init__(self, history_size: int = 10000):
        """
        Initialize pattern analyzer.
        
        Args:
            history_size: Maximum size of access history
        """
        self.history_size = history_size
        self.access_history = deque(maxlen=history_size)
        self.patterns = {}
        
        # Pattern tracking
        self.hero_patterns = defaultdict(list)
        self.time_patterns = defaultdict(list)
        self.user_patterns = defaultdict(list)
        self.sequence_patterns = defaultdict(int)
        
        # Prediction accuracy tracking
        self.predictions_made = 0
        self.predictions_correct = 0
        
        logger.info("📊 Usage Pattern Analyzer initialized")
    
    def record_access(self, key: str, user_id: str = "anonymous", metadata: Dict[str, Any] = None):
        """Record cache access for pattern analysis."""
        access_record = {
            'key': key,
            'user_id': user_id,
            'timestamp': time.time(),
            'hour': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'metadata': metadata or {}
        }
        
        self.access_history.append(access_record)
        
        # Update pattern tracking
        self._update_patterns(access_record)
    
    def _update_patterns(self, access_record: Dict[str, Any]):
        """Update pattern tracking with new access."""
        key = access_record['key']
        user_id = access_record['user_id']
        hour = access_record['hour']
        
        # Hero patterns
        if 'hero:' in key:
            hero_name = key.split(':')[1] if ':' in key else key
            self.hero_patterns[hero_name].append(access_record)
        
        # Time patterns
        self.time_patterns[hour].append(key)
        
        # User patterns
        self.user_patterns[user_id].append(key)
        
        # Sequence patterns (last 3 accesses)
        if len(self.access_history) >= 3:
            recent_keys = [record['key'] for record in list(self.access_history)[-3:]]
            sequence = '->'.join(recent_keys)
            self.sequence_patterns[sequence] += 1
    
    def predict_next_accesses(self, current_key: str, user_id: str = "anonymous", 
                            max_predictions: int = 5) -> List[Tuple[str, float]]:
        """
        Predict next likely cache accesses.
        
        Args:
            current_key: Currently accessed key
            user_id: User ID for personalized predictions
            max_predictions: Maximum number of predictions
            
        Returns:
            List of (predicted_key, confidence) tuples
        """
        predictions = []
        
        # 1. Hero-based predictions
        if 'hero:' in current_key:
            hero_predictions = self._predict_hero_related(current_key)
            predictions.extend(hero_predictions)
        
        # 2. Time-based predictions
        time_predictions = self._predict_time_based(current_key)
        predictions.extend(time_predictions)
        
        # 3. User-based predictions
        user_predictions = self._predict_user_based(current_key, user_id)
        predictions.extend(user_predictions)
        
        # 4. Sequence-based predictions
        sequence_predictions = self._predict_sequence_based(current_key)
        predictions.extend(sequence_predictions)
        
        # Combine and rank predictions
        prediction_scores = defaultdict(float)
        for key, confidence in predictions:
            prediction_scores[key] += confidence
        
        # Sort by confidence and return top predictions
        sorted_predictions = sorted(prediction_scores.items(), key=lambda x: x[1], reverse=True)
        
        self.predictions_made += len(sorted_predictions[:max_predictions])
        
        return sorted_predictions[:max_predictions]
    
    def _predict_hero_related(self, current_key: str) -> List[Tuple[str, float]]:
        """Predict hero-related accesses."""
        predictions = []
        
        if 'hero:' in current_key:
            hero_name = current_key.split(':')[1] if ':' in current_key else current_key
            
            # Common hero operations
            related_operations = ['stats', 'analysis', 'performance', 'build', 'matchup']
            
            for operation in related_operations:
                predicted_key = f"hero:{hero_name}:{operation}"
                if predicted_key != current_key:
                    # Calculate confidence based on historical access
                    confidence = self._calculate_hero_confidence(hero_name, operation)
                    predictions.append((predicted_key, confidence))
        
        return predictions
    
    def _predict_time_based(self, current_key: str) -> List[Tuple[str, float]]:
        """Predict based on time patterns."""
        predictions = []
        current_hour = datetime.now().hour
        
        if current_hour in self.time_patterns:
            # Get most common keys for this hour
            hour_keys = self.time_patterns[current_hour]
            if len(hour_keys) > 5:
                common_keys = Counter(hour_keys).most_common(3)
                
                for key, frequency in common_keys:
                    if key != current_key:
                        confidence = min(0.8, frequency / len(hour_keys))
                        predictions.append((key, confidence))
        
        return predictions
    
    def _predict_user_based(self, current_key: str, user_id: str) -> List[Tuple[str, float]]:
        """Predict based on user patterns."""
        predictions = []
        
        if user_id in self.user_patterns:
            user_keys = self.user_patterns[user_id]
            if len(user_keys) > 3:
                # Find keys commonly accessed after current_key
                for i, key in enumerate(user_keys[:-1]):
                    if key == current_key:
                        next_key = user_keys[i + 1]
                        if next_key != current_key:
                            confidence = 0.6  # Base confidence for user patterns
                            predictions.append((next_key, confidence))
        
        return predictions
    
    def _predict_sequence_based(self, current_key: str) -> List[Tuple[str, float]]:
        """Predict based on access sequences."""
        predictions = []
        
        # Find sequences that end with current_key
        for sequence, frequency in self.sequence_patterns.items():
            sequence_keys = sequence.split('->')
            if len(sequence_keys) >= 2 and sequence_keys[-2] == current_key:
                next_key = sequence_keys[-1]
                confidence = min(0.7, frequency / max(self.sequence_patterns.values()))
                predictions.append((next_key, confidence))
        
        return predictions
    
    def _calculate_hero_confidence(self, hero_name: str, operation: str) -> float:
        """Calculate confidence for hero-related prediction."""
        if hero_name not in self.hero_patterns:
            return 0.3  # Base confidence
        
        hero_accesses = self.hero_patterns[hero_name]
        operation_accesses = sum(1 for access in hero_accesses 
                               if operation in access['key'])
        
        if len(hero_accesses) > 0:
            confidence = operation_accesses / len(hero_accesses)
            return min(0.9, confidence + 0.2)  # Boost confidence
        
        return 0.3
    
    def validate_prediction(self, predicted_key: str, actually_accessed: bool):
        """Validate prediction accuracy."""
        if actually_accessed:
            self.predictions_correct += 1
        
        # Update prediction accuracy
        if self.predictions_made > 0:
            accuracy = self.predictions_correct / self.predictions_made
            logger.debug(f"📊 Prediction accuracy: {accuracy:.2%}")
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get pattern analysis statistics."""
        return {
            'total_accesses': len(self.access_history),
            'unique_keys': len(set(record['key'] for record in self.access_history)),
            'hero_patterns': len(self.hero_patterns),
            'time_patterns': len(self.time_patterns),
            'user_patterns': len(self.user_patterns),
            'sequence_patterns': len(self.sequence_patterns),
            'prediction_accuracy': (self.predictions_correct / self.predictions_made) 
                                 if self.predictions_made > 0 else 0.0,
            'predictions_made': self.predictions_made,
            'predictions_correct': self.predictions_correct
        }


class CacheWarmingService:
    """Intelligent cache warming service."""
    
    def __init__(self, cache_manager, pattern_analyzer: UsagePatternAnalyzer):
        """
        Initialize cache warming service.
        
        Args:
            cache_manager: Cache manager instance
            pattern_analyzer: Pattern analyzer for predictions
        """
        self.cache_manager = cache_manager
        self.pattern_analyzer = pattern_analyzer
        
        # Warming configuration
        self.warming_enabled = True
        self.warming_interval = 300  # 5 minutes
        self.max_warming_operations = 20
        
        # Popular content tracking
        self.popular_heroes = Counter()
        self.popular_operations = Counter()
        self.warming_queue = asyncio.Queue()
        
        # Warming statistics
        self.warming_stats = {
            'total_warming_operations': 0,
            'successful_warming': 0,
            'failed_warming': 0,
            'cache_hits_from_warming': 0,
            'warming_efficiency': 0.0
        }
        
        logger.info("🔥 Cache Warming Service initialized")
    
    async def start_warming_service(self):
        """Start cache warming background service."""
        logger.info("🔥 Starting cache warming service")
        
        # Start warming worker
        asyncio.create_task(self._warming_worker())
        
        # Start periodic warming
        asyncio.create_task(self._periodic_warming())
    
    async def _warming_worker(self):
        """Background worker for cache warming."""
        while self.warming_enabled:
            try:
                # Wait for warming requests
                warming_request = await asyncio.wait_for(
                    self.warming_queue.get(), 
                    timeout=5.0
                )
                
                # Process warming request
                await self._process_warming_request(warming_request)
                
            except asyncio.TimeoutError:
                # No requests, continue
                continue
            except Exception as e:
                logger.error(f"❌ Cache warming error: {e}")
                await asyncio.sleep(1.0)
    
    async def _periodic_warming(self):
        """Periodic cache warming based on patterns."""
        while self.warming_enabled:
            try:
                await asyncio.sleep(self.warming_interval)
                
                # Analyze current patterns
                await self._analyze_and_warm()
                
            except Exception as e:
                logger.error(f"❌ Periodic warming error: {e}")
    
    async def _analyze_and_warm(self):
        """Analyze patterns and warm cache accordingly."""
        logger.debug("🔍 Analyzing patterns for cache warming")
        
        # Get current time context
        current_hour = datetime.now().hour
        current_day = datetime.now().weekday()
        
        # Predict popular content for current time
        time_predictions = self._predict_popular_for_time(current_hour, current_day)
        
        # Queue warming operations
        for predicted_key, confidence in time_predictions:
            if confidence > 0.5:  # Only warm high-confidence predictions
                await self.warming_queue.put({
                    'key': predicted_key,
                    'confidence': confidence,
                    'source': 'time_pattern',
                    'priority': int(confidence * 5)
                })
        
        # Hero popularity warming
        popular_heroes = self.popular_heroes.most_common(5)
        for hero, frequency in popular_heroes:
            # Warm common hero operations
            for operation in ['stats', 'analysis', 'build']:
                warming_key = f"hero:{hero}:{operation}"
                await self.warming_queue.put({
                    'key': warming_key,
                    'confidence': min(0.8, frequency / 100),
                    'source': 'hero_popularity',
                    'priority': 3
                })
    
    def _predict_popular_for_time(self, hour: int, day: int) -> List[Tuple[str, float]]:
        """Predict popular content for specific time."""
        predictions = []
        
        # Analyze historical data for this time
        time_key = f"{day}_{hour}"
        
        # Get access patterns for this time
        historical_accesses = []
        for record in self.pattern_analyzer.access_history:
            record_time = datetime.fromtimestamp(record['timestamp'])
            if record_time.hour == hour and record_time.weekday() == day:
                historical_accesses.append(record['key'])
        
        if len(historical_accesses) > 5:
            # Find most common accesses for this time
            common_keys = Counter(historical_accesses).most_common(10)
            
            for key, frequency in common_keys:
                confidence = min(0.9, frequency / len(historical_accesses))
                predictions.append((key, confidence))
        
        return predictions
    
    async def _process_warming_request(self, warming_request: Dict[str, Any]):
        """Process a cache warming request."""
        key = warming_request['key']
        confidence = warming_request['confidence']
        
        try:
            # Check if already cached
            if await self.cache_manager.exists(key):
                logger.debug(f"🔥 Key already cached, skipping: {key}")
                return
            
            # Generate content for warming (this would be operation-specific)
            warmed_content = await self._generate_warming_content(key, warming_request)
            
            if warmed_content:
                # Cache the warmed content
                await self.cache_manager.set(
                    key, 
                    warmed_content, 
                    ttl=3600,  # 1 hour for warmed content
                    priority=CachePriority.LOW,  # Lower priority than user requests
                    source="warmed"
                )
                
                self.warming_stats['successful_warming'] += 1
                logger.debug(f"🔥 Cache warmed: {key} (confidence: {confidence:.2f})")
            else:
                self.warming_stats['failed_warming'] += 1
                
        except Exception as e:
            logger.error(f"❌ Cache warming failed for {key}: {e}")
            self.warming_stats['failed_warming'] += 1
        
        self.warming_stats['total_warming_operations'] += 1
    
    async def _generate_warming_content(self, key: str, request: Dict[str, Any]) -> Optional[Any]:
        """Generate content for cache warming."""
        # This would implement actual content generation
        # For now, return mock content based on key type
        
        if 'hero:' in key:
            # Generate hero-related content
            parts = key.split(':')
            hero_name = parts[1] if len(parts) > 1 else 'unknown'
            operation = parts[2] if len(parts) > 2 else 'general'
            
            return {
                'hero': hero_name,
                'operation': operation,
                'warmed_at': time.time(),
                'mock_data': True,
                'warming_source': request.get('source', 'unknown')
            }
        
        elif 'screenshot:' in key:
            # Generate screenshot analysis content
            return {
                'analysis_type': 'screenshot',
                'warmed_at': time.time(),
                'mock_analysis': True,
                'warming_source': request.get('source', 'unknown')
            }
        
        return None
    
    def record_warming_hit(self, key: str):
        """Record when warmed cache content is accessed."""
        self.warming_stats['cache_hits_from_warming'] += 1
        
        # Update warming efficiency
        total_warmed = self.warming_stats['successful_warming']
        hits_from_warming = self.warming_stats['cache_hits_from_warming']
        
        if total_warmed > 0:
            self.warming_stats['warming_efficiency'] = hits_from_warming / total_warmed
    
    def get_warming_stats(self) -> Dict[str, Any]:
        """Get cache warming statistics."""
        return self.warming_stats.copy()


class IntelligentCacheSystem:
    """
    Advanced intelligent caching system with prediction and optimization.
    
    Features:
    - Multi-level caching (L1 Memory, L2 Redis, L3 Disk)
    - Predictive caching based on usage patterns
    - Cache warming for popular content
    - Intelligent eviction policies
    - Performance analytics and optimization
    """
    
    def __init__(self,
                 memory_cache_size: int = 2000,
                 redis_url: str = "redis://localhost:6379",
                 enable_prediction: bool = True,
                 enable_warming: bool = True,
                 enable_disk_cache: bool = False):
        """
        Initialize intelligent cache system.
        
        Args:
            memory_cache_size: L1 memory cache size
            redis_url: Redis connection URL for L2 cache
            enable_prediction: Enable predictive caching
            enable_warming: Enable cache warming
            enable_disk_cache: Enable L3 disk cache
        """
        self.memory_cache_size = memory_cache_size
        self.enable_prediction = enable_prediction
        self.enable_warming = enable_warming
        self.enable_disk_cache = enable_disk_cache
        
        # L1 Memory Cache
        self.l1_cache: Dict[str, CacheEntry] = {}
        self.l1_lock = threading.RLock()
        
        # L2 Redis Cache
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            self.redis_client.ping()  # Test connection
            self.redis_available = True
            logger.info("✅ Redis L2 cache connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis L2 cache not available: {e}")
            self.redis_client = None
            self.redis_available = False
        
        # L3 Disk Cache
        if enable_disk_cache:
            self.disk_cache_dir = Path("cache/disk_cache")
            self.disk_cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"💾 L3 disk cache enabled: {self.disk_cache_dir}")
        else:
            self.disk_cache_dir = None
        
        # Pattern analysis and prediction
        self.pattern_analyzer = UsagePatternAnalyzer() if enable_prediction else None
        
        # Cache warming
        self.warming_service = CacheWarmingService(self, self.pattern_analyzer) if enable_warming else None
        
        # Cache statistics
        self.cache_stats = {
            'l1_hits': 0, 'l1_misses': 0,
            'l2_hits': 0, 'l2_misses': 0,
            'l3_hits': 0, 'l3_misses': 0,
            'predictions': 0, 'prediction_hits': 0,
            'total_operations': 0,
            'evictions': 0,
            'memory_usage_mb': 0
        }
        
        logger.info("🧠 Intelligent Cache System initialized")
        logger.info(f"   - L1 Memory: {memory_cache_size} entries")
        logger.info(f"   - L2 Redis: {self.redis_available}")
        logger.info(f"   - L3 Disk: {enable_disk_cache}")
        logger.info(f"   - Prediction: {enable_prediction}")
        logger.info(f"   - Warming: {enable_warming}")
    
    async def get(self, 
                  key: str, 
                  operation: Optional[Callable] = None,
                  user_id: str = "anonymous",
                  priority: CachePriority = CachePriority.NORMAL,
                  *args, **kwargs) -> Any:
        """
        Intelligent cache get with multi-level lookup and prediction.
        
        Args:
            key: Cache key
            operation: Function to execute on cache miss
            user_id: User ID for pattern analysis
            priority: Cache priority
            *args: Arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Cached or computed value
        """
        start_time = time.time()
        self.cache_stats['total_operations'] += 1
        
        # Record access pattern
        if self.pattern_analyzer:
            self.pattern_analyzer.record_access(key, user_id, kwargs.get('metadata', {}))
        
        # L1 Memory Cache lookup
        l1_result = await self._get_l1(key)
        if l1_result is not None:
            self.cache_stats['l1_hits'] += 1
            
            # Trigger predictive caching
            if self.enable_prediction:
                asyncio.create_task(self._trigger_predictions(key, user_id))
            
            return l1_result
        
        self.cache_stats['l1_misses'] += 1
        
        # L2 Redis Cache lookup
        l2_result = await self._get_l2(key)
        if l2_result is not None:
            self.cache_stats['l2_hits'] += 1
            
            # Promote to L1
            await self._set_l1(key, l2_result, priority)
            
            return l2_result
        
        self.cache_stats['l2_misses'] += 1
        
        # L3 Disk Cache lookup
        if self.enable_disk_cache:
            l3_result = await self._get_l3(key)
            if l3_result is not None:
                self.cache_stats['l3_hits'] += 1
                
                # Promote to L2 and L1
                await self._set_l2(key, l3_result)
                await self._set_l1(key, l3_result, priority)
                
                return l3_result
            
            self.cache_stats['l3_misses'] += 1
        
        # Cache miss - execute operation
        if operation:
            logger.debug(f"💡 Cache miss, executing operation: {key}")
            
            # Execute operation
            result = await self._execute_with_timeout(operation, *args, **kwargs)
            
            # Cache the result at all levels
            await self.set(key, result, priority=priority, user_id=user_id)
            
            # Trigger predictive caching
            if self.enable_prediction:
                asyncio.create_task(self._trigger_predictions(key, user_id))
            
            return result
        
        return None
    
    async def set(self, 
                  key: str, 
                  value: Any,
                  ttl: int = 3600,
                  priority: CachePriority = CachePriority.NORMAL,
                  user_id: str = "anonymous",
                  source: str = "manual") -> bool:
        """
        Set value in intelligent cache system.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            priority: Cache priority
            user_id: User ID for analytics
            source: Source of the cache entry
            
        Returns:
            Success status
        """
        try:
            # Calculate value size
            value_size = len(pickle.dumps(value))
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=1,
                priority=priority,
                size_bytes=value_size,
                ttl=ttl,
                source=source
            )
            
            # Set in L1 (always)
            await self._set_l1(key, value, priority, entry)
            
            # Set in L2 if value is significant
            if self.redis_available and value_size > 1000:  # Cache larger values in Redis
                await self._set_l2(key, value, ttl)
            
            # Set in L3 if enabled and value is very large
            if self.enable_disk_cache and value_size > 100000:  # 100KB threshold
                await self._set_l3(key, value)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache set failed for {key}: {e}")
            return False
    
    async def _get_l1(self, key: str) -> Optional[Any]:
        """Get from L1 memory cache."""
        with self.l1_lock:
            if key in self.l1_cache:
                entry = self.l1_cache[key]
                
                # Check TTL
                if time.time() - entry.created_at > entry.ttl:
                    del self.l1_cache[key]
                    return None
                
                # Update access statistics
                entry.last_accessed = time.time()
                entry.access_count += 1
                
                return entry.value
        
        return None
    
    async def _set_l1(self, key: str, value: Any, priority: CachePriority, entry: CacheEntry = None):
        """Set in L1 memory cache with intelligent eviction."""
        with self.l1_lock:
            # Create entry if not provided
            if entry is None:
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=time.time(),
                    last_accessed=time.time(),
                    access_count=1,
                    priority=priority,
                    size_bytes=len(pickle.dumps(value)),
                    ttl=3600
                )
            
            # Evict if cache is full
            if len(self.l1_cache) >= self.memory_cache_size:
                await self._evict_l1_entries(1)
            
            self.l1_cache[key] = entry
            
            # Update memory usage
            self._update_memory_usage()
    
    async def _evict_l1_entries(self, count: int = 1):
        """Evict entries from L1 cache using intelligent policy."""
        if not self.l1_cache:
            return
        
        # Sort by eviction priority (priority, access_count, last_accessed)
        entries = list(self.l1_cache.items())
        entries.sort(key=lambda x: (
            x[1].priority.value,  # Lower priority first
            -x[1].access_count,   # Less accessed first
            x[1].last_accessed   # Older first
        ))
        
        # Evict entries
        for i in range(min(count, len(entries))):
            key_to_evict = entries[i][0]
            del self.l1_cache[key_to_evict]
            self.cache_stats['evictions'] += 1
            logger.debug(f"🗑️ Evicted from L1: {key_to_evict}")
    
    async def _get_l2(self, key: str) -> Optional[Any]:
        """Get from L2 Redis cache."""
        if not self.redis_available:
            return None
        
        try:
            redis_value = self.redis_client.get(key)
            if redis_value:
                return pickle.loads(redis_value)
        except Exception as e:
            logger.warning(f"⚠️ L2 cache error: {e}")
        
        return None
    
    async def _set_l2(self, key: str, value: Any, ttl: int = 3600):
        """Set in L2 Redis cache."""
        if not self.redis_available:
            return
        
        try:
            serialized_value = pickle.dumps(value)
            self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.warning(f"⚠️ L2 cache set error: {e}")
    
    async def _get_l3(self, key: str) -> Optional[Any]:
        """Get from L3 disk cache."""
        if not self.enable_disk_cache:
            return None
        
        try:
            cache_file = self.disk_cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.pkl"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"⚠️ L3 cache error: {e}")
        
        return None
    
    async def _set_l3(self, key: str, value: Any):
        """Set in L3 disk cache."""
        if not self.enable_disk_cache:
            return
        
        try:
            cache_file = self.disk_cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            logger.warning(f"⚠️ L3 cache set error: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in any cache level."""
        # Check L1
        with self.l1_lock:
            if key in self.l1_cache:
                entry = self.l1_cache[key]
                if time.time() - entry.created_at <= entry.ttl:
                    return True
                else:
                    del self.l1_cache[key]
        
        # Check L2
        if self.redis_available:
            try:
                return self.redis_client.exists(key) > 0
            except:
                pass
        
        # Check L3
        if self.enable_disk_cache:
            cache_file = self.disk_cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.pkl"
            return cache_file.exists()
        
        return False
    
    async def _trigger_predictions(self, key: str, user_id: str):
        """Trigger predictive caching based on current access."""
        if not self.pattern_analyzer:
            return
        
        # Get predictions
        predictions = self.pattern_analyzer.predict_next_accesses(key, user_id, max_predictions=3)
        
        self.cache_stats['predictions'] += len(predictions)
        
        # Queue predictions for warming
        if self.warming_service:
            for predicted_key, confidence in predictions:
                if confidence > 0.4:  # Only warm reasonably confident predictions
                    await self.warming_service.warming_queue.put({
                        'key': predicted_key,
                        'confidence': confidence,
                        'source': 'prediction',
                        'triggered_by': key,
                        'priority': int(confidence * 3)
                    })
    
    async def _execute_with_timeout(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation with timeout."""
        timeout = kwargs.pop('timeout', 10.0)
        try:
            return await asyncio.wait_for(operation(*args, **kwargs), timeout=timeout)
        except asyncio.TimeoutError:
            raise Exception(f"Operation timed out after {timeout}s")
    
    def _update_memory_usage(self):
        """Update memory usage statistics."""
        total_size = sum(entry.size_bytes for entry in self.l1_cache.values())
        self.cache_stats['memory_usage_mb'] = total_size / 1024**2
    
    async def start_services(self):
        """Start cache services."""
        logger.info("🚀 Starting intelligent cache services")
        
        if self.warming_service:
            await self.warming_service.start_warming_service()
            logger.info("✅ Cache warming service started")
        
        # Start periodic cleanup
        asyncio.create_task(self._periodic_cleanup())
        logger.info("✅ Cache cleanup service started")
    
    async def _periodic_cleanup(self):
        """Periodic cache cleanup and optimization."""
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutes
                
                # Clean expired entries
                await self._clean_expired_entries()
                
                # Optimize cache distribution
                await self._optimize_cache_distribution()
                
                # Force garbage collection if memory usage is high
                if self.cache_stats['memory_usage_mb'] > 500:  # 500MB threshold
                    gc.collect()
                
            except Exception as e:
                logger.error(f"❌ Cache cleanup error: {e}")
    
    async def _clean_expired_entries(self):
        """Clean expired cache entries."""
        current_time = time.time()
        expired_keys = []
        
        with self.l1_lock:
            for key, entry in self.l1_cache.items():
                if current_time - entry.created_at > entry.ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.l1_cache[key]
        
        if expired_keys:
            logger.debug(f"🧹 Cleaned {len(expired_keys)} expired L1 entries")
        
        self._update_memory_usage()
    
    async def _optimize_cache_distribution(self):
        """Optimize cache distribution across levels."""
        # Move frequently accessed items to higher cache levels
        # Move rarely accessed items to lower cache levels
        
        with self.l1_lock:
            # Find high-access items that should stay in L1
            high_access_items = [
                (key, entry) for key, entry in self.l1_cache.items()
                if entry.access_count > 5 and entry.priority.value >= 3
            ]
            
            # Find low-access items that can be demoted
            low_access_items = [
                (key, entry) for key, entry in self.l1_cache.items()
                if entry.access_count <= 2 and entry.priority.value <= 2
            ]
            
            # Demote low-access items to L2
            for key, entry in low_access_items[:10]:  # Limit demotion
                if self.redis_available:
                    await self._set_l2(key, entry.value, int(entry.ttl))
                    del self.l1_cache[key]
                    logger.debug(f"📉 Demoted to L2: {key}")
        
        self._update_memory_usage()
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = self.cache_stats.copy()
        
        # Calculate hit ratios
        total_l1 = stats['l1_hits'] + stats['l1_misses']
        total_l2 = stats['l2_hits'] + stats['l2_misses']
        total_l3 = stats['l3_hits'] + stats['l3_misses']
        
        if total_l1 > 0:
            stats['l1_hit_ratio'] = stats['l1_hits'] / total_l1
        if total_l2 > 0:
            stats['l2_hit_ratio'] = stats['l2_hits'] / total_l2
        if total_l3 > 0:
            stats['l3_hit_ratio'] = stats['l3_hits'] / total_l3
        
        # Overall hit ratio
        total_hits = stats['l1_hits'] + stats['l2_hits'] + stats['l3_hits']
        total_requests = stats['total_operations']
        if total_requests > 0:
            stats['overall_hit_ratio'] = total_hits / total_requests
        
        # Add component stats
        if self.pattern_analyzer:
            stats['pattern_analysis'] = self.pattern_analyzer.get_pattern_stats()
        
        if self.warming_service:
            stats['cache_warming'] = self.warming_service.get_warming_stats()
        
        # Cache level information
        stats['cache_levels'] = {
            'l1_size': len(self.l1_cache),
            'l1_max_size': self.memory_cache_size,
            'l2_available': self.redis_available,
            'l3_available': self.enable_disk_cache
        }
        
        return stats


# Global cache system instance
intelligent_cache = IntelligentCacheSystem()


def get_intelligent_cache() -> IntelligentCacheSystem:
    """Get the global intelligent cache instance."""
    return intelligent_cache


# Cache decorators
def intelligent_cache_decorator(ttl: int = 3600, priority: CachePriority = CachePriority.NORMAL):
    """Decorator for intelligent caching."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_intelligent_cache()
            
            # Generate cache key
            key_data = f"{func.__name__}_{str(args)}_{str(sorted(kwargs.items()))}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Get user_id if available
            user_id = kwargs.pop('user_id', 'anonymous')
            
            return await cache.get(
                cache_key, 
                func, 
                user_id=user_id,
                priority=priority,
                *args, 
                **kwargs
            )
        return wrapper
    return decorator


def cache_hero_data(ttl: int = 7200):  # 2 hours for hero data
    """Decorator for caching hero-related data."""
    return intelligent_cache_decorator(ttl=ttl, priority=CachePriority.HIGH)


def cache_analysis_results(ttl: int = 1800):  # 30 minutes for analysis
    """Decorator for caching analysis results."""
    return intelligent_cache_decorator(ttl=ttl, priority=CachePriority.NORMAL)


if __name__ == "__main__":
    # Test intelligent cache system
    async def test_intelligent_cache():
        """Test intelligent cache functionality."""
        logger.info("🧪 Testing Intelligent Cache System")
        
        cache = IntelligentCacheSystem(
            memory_cache_size=100,
            enable_prediction=True,
            enable_warming=True
        )
        
        # Start services
        await cache.start_services()
        
        # Test cache operations
        test_data = {'test': 'data', 'number': 42}
        
        # Set and get
        await cache.set('test_key', test_data)
        result = await cache.get('test_key')
        
        logger.info(f"📊 Cache test: {result == test_data}")
        
        # Test with operation
        async def expensive_operation():
            await asyncio.sleep(0.1)
            return {'computed': True, 'value': 100}
        
        result = await cache.get('computed_key', expensive_operation)
        logger.info(f"📊 Operation cache: {result}")
        
        # Get statistics
        stats = cache.get_comprehensive_stats()
        logger.info(f"📈 Cache stats: {json.dumps(stats, indent=2, default=str)}")
    
    import json
    asyncio.run(test_intelligent_cache())
