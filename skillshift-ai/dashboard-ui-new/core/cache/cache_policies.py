"""
Cache Invalidation Policies for MLBB Coach AI
Advanced cache invalidation strategies and policies
"""

import asyncio
import logging
from typing import Dict, List, Set, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from .distributed_cache_manager import CachePartition, CacheInvalidationStrategy

logger = logging.getLogger(__name__)


class InvalidationEvent(Enum):
    """Events that can trigger cache invalidation."""
    USER_UPDATE = "user_update"
    MATCH_COMPLETE = "match_complete"
    HERO_BALANCE_UPDATE = "hero_balance_update"
    MODEL_UPDATE = "model_update"
    SYSTEM_UPDATE = "system_update"
    MANUAL_INVALIDATION = "manual_invalidation"


@dataclass
class InvalidationRule:
    """Rule for cache invalidation."""
    event: InvalidationEvent
    partitions: List[CachePartition]
    patterns: List[str]
    delay: int = 0  # Delay before invalidation in seconds
    cascade: bool = False  # Whether to cascade invalidation


class CacheInvalidationManager:
    """Manages cache invalidation policies and strategies."""
    
    def __init__(self, cache_manager):
        """Initialize invalidation manager."""
        self.cache_manager = cache_manager
        
        # Define invalidation rules
        self.rules: Dict[InvalidationEvent, List[InvalidationRule]] = {
            InvalidationEvent.USER_UPDATE: [
                InvalidationRule(
                    event=InvalidationEvent.USER_UPDATE,
                    partitions=[CachePartition.USER_DATA, CachePartition.SESSION_DATA],
                    patterns=["user:*", "session:*"],
                    cascade=True
                )
            ],
            InvalidationEvent.MATCH_COMPLETE: [
                InvalidationRule(
                    event=InvalidationEvent.MATCH_COMPLETE,
                    partitions=[CachePartition.MATCH_DATA, CachePartition.ANALYSIS_RESULTS],
                    patterns=["match:*", "analysis:*"],
                    delay=60  # Allow time for analysis completion
                )
            ],
            InvalidationEvent.HERO_BALANCE_UPDATE: [
                InvalidationRule(
                    event=InvalidationEvent.HERO_BALANCE_UPDATE,
                    partitions=[CachePartition.HERO_DATA, CachePartition.ANALYSIS_RESULTS],
                    patterns=["hero:*", "analysis:*"],
                    cascade=True
                )
            ],
            InvalidationEvent.MODEL_UPDATE: [
                InvalidationRule(
                    event=InvalidationEvent.MODEL_UPDATE,
                    partitions=[CachePartition.ML_MODELS, CachePartition.ANALYSIS_RESULTS],
                    patterns=["model:*", "analysis:*"],
                    cascade=True
                )
            ],
        }
        
        # Event queue for processing
        self.event_queue = asyncio.Queue()
        self.processor_task = None
        
    async def start(self):
        """Start the invalidation manager."""
        self.processor_task = asyncio.create_task(self._process_events())
        logger.info("Cache invalidation manager started")
        
    async def stop(self):
        """Stop the invalidation manager."""
        if self.processor_task:
            self.processor_task.cancel()
        logger.info("Cache invalidation manager stopped")
        
    async def trigger_invalidation(self, event: InvalidationEvent, context: Dict[str, Any] = None):
        """Trigger cache invalidation for an event."""
        await self.event_queue.put((event, context or {}, datetime.now()))
        logger.debug(f"Invalidation event queued: {event.value}")
        
    async def _process_events(self):
        """Process invalidation events."""
        while True:
            try:
                event, context, timestamp = await self.event_queue.get()
                await self._handle_event(event, context, timestamp)
                self.event_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing invalidation event: {e}")
                
    async def _handle_event(self, event: InvalidationEvent, context: Dict[str, Any], timestamp: datetime):
        """Handle a specific invalidation event."""
        rules = self.rules.get(event, [])
        
        for rule in rules:
            try:
                # Apply delay if specified
                if rule.delay > 0:
                    await asyncio.sleep(rule.delay)
                
                # Invalidate by patterns
                total_invalidated = 0
                for partition in rule.partitions:
                    for pattern in rule.patterns:
                        # Apply context to pattern if available
                        formatted_pattern = self._format_pattern(pattern, context)
                        count = await self.cache_manager.invalidate_by_pattern(
                            formatted_pattern, partition
                        )
                        total_invalidated += count
                
                logger.info(f"Invalidated {total_invalidated} entries for event {event.value}")
                
                # Handle cascading invalidation
                if rule.cascade:
                    await self._cascade_invalidation(event, context)
                    
            except Exception as e:
                logger.error(f"Error handling invalidation rule for {event.value}: {e}")
                
    def _format_pattern(self, pattern: str, context: Dict[str, Any]) -> str:
        """Format pattern with context variables."""
        try:
            return pattern.format(**context)
        except (KeyError, ValueError):
            return pattern
            
    async def _cascade_invalidation(self, event: InvalidationEvent, context: Dict[str, Any]):
        """Handle cascading invalidation."""
        # Define cascade relationships
        cascade_map = {
            InvalidationEvent.USER_UPDATE: [InvalidationEvent.MATCH_COMPLETE],
            InvalidationEvent.HERO_BALANCE_UPDATE: [InvalidationEvent.MODEL_UPDATE],
        }
        
        cascade_events = cascade_map.get(event, [])
        for cascade_event in cascade_events:
            await self.trigger_invalidation(cascade_event, context)


class SmartCacheWarmer:
    """Intelligent cache warming based on usage patterns."""
    
    def __init__(self, cache_manager):
        """Initialize cache warmer."""
        self.cache_manager = cache_manager
        self.warming_patterns = {
            CachePartition.HERO_DATA: [
                "hero:popular:*",
                "hero:meta:*",
                "hero:winrates:*"
            ],
            CachePartition.STATIC_ASSETS: [
                "assets:images:heroes:*",
                "assets:icons:*"
            ],
            CachePartition.ANALYSIS_RESULTS: [
                "analysis:templates:*",
                "analysis:thresholds:*"
            ]
        }
        
    async def warm_cache(self, partition: Optional[CachePartition] = None):
        """Warm cache with frequently accessed data."""
        partitions = [partition] if partition else list(self.warming_patterns.keys())
        
        for part in partitions:
            patterns = self.warming_patterns.get(part, [])
            for pattern in patterns:
                try:
                    await self._warm_pattern(pattern, part)
                except Exception as e:
                    logger.error(f"Error warming cache pattern {pattern}: {e}")
                    
    async def _warm_pattern(self, pattern: str, partition: CachePartition):
        """Warm cache for a specific pattern."""
        # This would typically fetch data from the primary data source
        # and populate the cache. Implementation depends on data sources.
        logger.debug(f"Warming cache pattern: {pattern} in partition: {partition.value}")


# Global invalidation manager
_invalidation_manager: Optional[CacheInvalidationManager] = None


async def get_invalidation_manager() -> CacheInvalidationManager:
    """Get global invalidation manager."""
    global _invalidation_manager
    
    if _invalidation_manager is None:
        from .distributed_cache_manager import get_cache_manager
        cache_manager = await get_cache_manager()
        _invalidation_manager = CacheInvalidationManager(cache_manager)
        await _invalidation_manager.start()
    
    return _invalidation_manager


async def invalidate_cache(event: InvalidationEvent, context: Dict[str, Any] = None):
    """Trigger cache invalidation using global manager."""
    manager = await get_invalidation_manager()
    await manager.trigger_invalidation(event, context)
