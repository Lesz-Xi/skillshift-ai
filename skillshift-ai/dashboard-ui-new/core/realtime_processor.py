#!/usr/bin/env python3
"""
Real-Time Analysis Pipeline - Task 8: Real-Time Analysis Pipeline
================================================================

This module implements real-time analysis capabilities for MLBB Coach AI:
- WebSocket infrastructure for real-time analysis streaming
- Live performance monitoring with <500ms latency
- Stream processing for frame-by-frame analysis
- Real-time event detection and coaching
- Live feedback system with instant coaching loops

Features:
- Real-time screenshot processing pipeline
- Stream analysis with frame buffering
- Live coaching feedback with <500ms target latency
- Real-time performance monitoring
- Instant event detection (kills, deaths, objectives)
- Live tactical suggestions during gameplay
- Real-time team composition analysis
- Continuous performance tracking
"""

import asyncio
import time
import logging
import json
import threading
import queue
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Union, AsyncIterator
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import deque, defaultdict
import uuid
import weakref
from pathlib import Path
import base64
import io
from PIL import Image

# Import existing core systems
try:
    from .ai_coach_v2 import AdvancedAICoachingIntelligence
    from .performance_optimizer_v2 import AdvancedPerformanceOptimizer
    from .enhanced_data_collector import enhanced_data_collector
    from .enhanced_ocr_processor import EnhancedOCRProcessor
    from .quality_assessor import IntelligentQualityAssessmentEngine
    from .events.websocket_manager import WebSocketManager
    from .events.event_bus import get_event_bus, publish_event
    from .events.event_types import Event, EventType, ProgressEvent, PerformanceEvent
    CORE_IMPORTS_AVAILABLE = True
except ImportError as e:
    CORE_IMPORTS_AVAILABLE = False
    logging.warning(f"Core imports not available: {e}")

logger = logging.getLogger(__name__)


class StreamState(Enum):
    """Real-time stream states"""
    INACTIVE = "inactive"
    CONNECTING = "connecting"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    STOPPING = "stopping"


class AnalysisMode(Enum):
    """Real-time analysis modes"""
    LIVE_GAMEPLAY = "live_gameplay"
    POST_MATCH = "post_match"
    REPLAY_ANALYSIS = "replay_analysis"
    TRAINING_MODE = "training_mode"


class EventPriority(Enum):
    """Event priority levels for real-time processing"""
    CRITICAL = 1    # Deaths, major objectives
    HIGH = 2        # Kills, assists, key abilities
    MEDIUM = 3      # Item purchases, positioning
    LOW = 4         # General stats, minor events


@dataclass
class StreamFrame:
    """Real-time frame data structure"""
    frame_id: str
    timestamp: datetime
    frame_data: np.ndarray
    frame_base64: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_start: Optional[float] = None
    processing_end: Optional[float] = None
    analysis_results: Optional[Dict[str, Any]] = None
    
    def get_processing_time_ms(self) -> Optional[float]:
        """Get processing time in milliseconds"""
        if self.processing_start and self.processing_end:
            return (self.processing_end - self.processing_start) * 1000
        return None


@dataclass
class RealTimeEvent:
    """Real-time game event detected from stream"""
    event_id: str
    event_type: str
    timestamp: datetime
    priority: EventPriority
    player_ign: Optional[str] = None
    hero: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    coaching_suggestion: Optional[str] = None
    
    def to_websocket_message(self) -> Dict[str, Any]:
        """Convert to WebSocket message format"""
        return {
            "type": "realtime_event",
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "player_ign": self.player_ign,
            "hero": self.hero,
            "details": self.details,
            "confidence": self.confidence,
            "coaching_suggestion": self.coaching_suggestion
        }


@dataclass
class StreamConfig:
    """Configuration for real-time stream processing"""
    target_fps: int = 2  # Process 2 frames per second for real-time
    max_latency_ms: int = 500  # Target <500ms latency
    buffer_size: int = 30  # Keep last 30 frames
    quality_threshold: float = 0.7  # Minimum quality for processing
    analysis_mode: AnalysisMode = AnalysisMode.LIVE_GAMEPLAY
    enable_coaching: bool = True
    enable_event_detection: bool = True
    coaching_frequency: int = 5  # Coaching every 5 seconds
    
    # Performance settings
    max_concurrent_analysis: int = 2
    enable_gpu_acceleration: bool = True
    enable_caching: bool = True
    
    # Event detection settings
    detect_kills: bool = True
    detect_deaths: bool = True
    detect_objectives: bool = True
    detect_items: bool = True
    detect_positioning: bool = True


class FrameBuffer:
    """Circular buffer for managing real-time frames"""
    
    def __init__(self, max_size: int = 30):
        self.max_size = max_size
        self.frames: deque = deque(maxlen=max_size)
        self.lock = threading.Lock()
        
    def add_frame(self, frame: StreamFrame):
        """Add frame to buffer"""
        with self.lock:
            self.frames.append(frame)
    
    def get_latest_frame(self) -> Optional[StreamFrame]:
        """Get the most recent frame"""
        with self.lock:
            return self.frames[-1] if self.frames else None
    
    def get_frame_sequence(self, count: int = 5) -> List[StreamFrame]:
        """Get last N frames for temporal analysis"""
        with self.lock:
            return list(self.frames)[-count:] if len(self.frames) >= count else list(self.frames)
    
    def clear(self):
        """Clear all frames"""
        with self.lock:
            self.frames.clear()


class RealTimeEventDetector:
    """Detects game events from real-time frames"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.previous_stats = {}
        self.event_history = deque(maxlen=100)
        
    async def detect_events(
        self, 
        frame: StreamFrame, 
        analysis_results: Dict[str, Any]
    ) -> List[RealTimeEvent]:
        """Detect events from current frame and analysis"""
        events = []
        
        try:
            # Extract current stats
            current_stats = self._extract_stats(analysis_results)
            
            if self.config.detect_kills:
                kill_events = await self._detect_kills(current_stats)
                events.extend(kill_events)
            
            if self.config.detect_deaths:
                death_events = await self._detect_deaths(current_stats)
                events.extend(death_events)
            
            if self.config.detect_objectives:
                objective_events = await self._detect_objectives(current_stats)
                events.extend(objective_events)
            
            if self.config.detect_items:
                item_events = await self._detect_item_purchases(current_stats)
                events.extend(item_events)
            
            # Store current stats for next comparison
            self.previous_stats = current_stats
            
            # Add events to history
            for event in events:
                self.event_history.append(event)
            
        except Exception as e:
            logger.error(f"Error detecting events: {e}")
        
        return events
    
    def _extract_stats(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant stats from analysis results"""
        stats = {}
        
        if "match_data" in analysis_results:
            match_data = analysis_results["match_data"]
            
            # Extract KDA
            if "kda" in match_data:
                kda = match_data["kda"]
                stats["kills"] = kda.get("kills", 0)
                stats["deaths"] = kda.get("deaths", 0)
                stats["assists"] = kda.get("assists", 0)
            
            # Extract other stats
            stats["gold"] = match_data.get("gold", 0)
            stats["damage"] = match_data.get("damage", 0)
            stats["hero"] = match_data.get("hero", "unknown")
        
        return stats
    
    async def _detect_kills(self, current_stats: Dict[str, Any]) -> List[RealTimeEvent]:
        """Detect kill events"""
        events = []
        
        current_kills = current_stats.get("kills", 0)
        previous_kills = self.previous_stats.get("kills", 0)
        
        if current_kills > previous_kills:
            kill_count = current_kills - previous_kills
            
            event = RealTimeEvent(
                event_id=str(uuid.uuid4()),
                event_type="kill",
                timestamp=datetime.now(),
                priority=EventPriority.HIGH,
                hero=current_stats.get("hero"),
                details={"kill_count": kill_count, "total_kills": current_kills},
                confidence=0.9,
                coaching_suggestion="Great job! Keep up the aggressive play and look for more picks."
            )
            events.append(event)
        
        return events
    
    async def _detect_deaths(self, current_stats: Dict[str, Any]) -> List[RealTimeEvent]:
        """Detect death events"""
        events = []
        
        current_deaths = current_stats.get("deaths", 0)
        previous_deaths = self.previous_stats.get("deaths", 0)
        
        if current_deaths > previous_deaths:
            event = RealTimeEvent(
                event_id=str(uuid.uuid4()),
                event_type="death",
                timestamp=datetime.now(),
                priority=EventPriority.CRITICAL,
                hero=current_stats.get("hero"),
                details={"total_deaths": current_deaths},
                confidence=0.9,
                coaching_suggestion="Focus on positioning and map awareness. Consider playing more defensively."
            )
            events.append(event)
        
        return events
    
    async def _detect_objectives(self, current_stats: Dict[str, Any]) -> List[RealTimeEvent]:
        """Detect objective-related events"""
        events = []
        # Implementation for objective detection (turrets, lord, turtle, etc.)
        return events
    
    async def _detect_item_purchases(self, current_stats: Dict[str, Any]) -> List[RealTimeEvent]:
        """Detect item purchase events"""
        events = []
        
        current_gold = current_stats.get("gold", 0)
        previous_gold = self.previous_stats.get("gold", 0)
        
        # Significant gold decrease might indicate item purchase
        if previous_gold > 0 and current_gold < previous_gold - 500:
            gold_spent = previous_gold - current_gold
            
            event = RealTimeEvent(
                event_id=str(uuid.uuid4()),
                event_type="item_purchase",
                timestamp=datetime.now(),
                priority=EventPriority.MEDIUM,
                hero=current_stats.get("hero"),
                details={"gold_spent": gold_spent, "remaining_gold": current_gold},
                confidence=0.7,
                coaching_suggestion="Good item timing! Consider your next item based on the game situation."
            )
            events.append(event)
        
        return events


class RealTimeCoachingEngine:
    """Provides real-time coaching feedback"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.last_coaching_time = 0
        self.coaching_history = deque(maxlen=50)
        
        # Initialize AI coach if available
        self.ai_coach = None
        if CORE_IMPORTS_AVAILABLE:
            try:
                self.ai_coach = AdvancedAICoachingIntelligence()
            except Exception as e:
                logger.warning(f"Could not initialize AI coach: {e}")
    
    async def generate_live_coaching(
        self,
        frame: StreamFrame,
        analysis_results: Dict[str, Any],
        events: List[RealTimeEvent]
    ) -> Optional[Dict[str, Any]]:
        """Generate live coaching feedback"""
        
        # Check coaching frequency
        current_time = time.time()
        if current_time - self.last_coaching_time < self.config.coaching_frequency:
            return None
        
        try:
            coaching_data = {
                "timestamp": datetime.now().isoformat(),
                "type": "live_coaching",
                "suggestions": [],
                "priority": "medium"
            }
            
            # Generate event-based coaching
            if events:
                event_coaching = await self._generate_event_coaching(events)
                coaching_data["suggestions"].extend(event_coaching)
            
            # Generate general coaching
            general_coaching = await self._generate_general_coaching(analysis_results)
            coaching_data["suggestions"].extend(general_coaching)
            
            # Prioritize suggestions
            if coaching_data["suggestions"]:
                coaching_data["priority"] = "high" if any(
                    event.priority in [EventPriority.CRITICAL, EventPriority.HIGH] 
                    for event in events
                ) else "medium"
            
            self.last_coaching_time = current_time
            self.coaching_history.append(coaching_data)
            
            return coaching_data
            
        except Exception as e:
            logger.error(f"Error generating live coaching: {e}")
            return None
    
    async def _generate_event_coaching(self, events: List[RealTimeEvent]) -> List[str]:
        """Generate coaching based on recent events"""
        suggestions = []
        
        for event in events:
            if event.coaching_suggestion:
                suggestions.append(event.coaching_suggestion)
        
        return suggestions
    
    async def _generate_general_coaching(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate general coaching suggestions"""
        suggestions = []
        
        try:
            if "match_data" in analysis_results:
                match_data = analysis_results["match_data"]
                
                # Gold efficiency coaching
                gold = match_data.get("gold", 0)
                if gold > 2000:
                    suggestions.append("You have good gold income! Consider investing in key items.")
                
                # KDA-based coaching
                if "kda" in match_data:
                    kda = match_data["kda"]
                    deaths = kda.get("deaths", 0)
                    if deaths > 3:
                        suggestions.append("Focus on positioning and map awareness to reduce deaths.")
                
        except Exception as e:
            logger.error(f"Error in general coaching: {e}")
        
        return suggestions


class RealTimeAnalysisProcessor:
    """Main real-time analysis processor"""
    
    def __init__(self, config: StreamConfig = None):
        self.config = config or StreamConfig()
        self.state = StreamState.INACTIVE
        self.frame_buffer = FrameBuffer(self.config.buffer_size)
        self.event_detector = RealTimeEventDetector(self.config)
        self.coaching_engine = RealTimeCoachingEngine(self.config)
        
        # WebSocket and event systems
        try:
            from .events.websocket_manager import WebSocketManager
            self.websocket_manager = WebSocketManager()
        except ImportError:
            self.websocket_manager = None
            logger.warning("WebSocketManager not available")
        
        try:
            self.event_bus = get_event_bus()
        except NameError:
            from .events.event_bus import get_event_bus
            self.event_bus = get_event_bus()
        
        # Processing components
        self.performance_optimizer = None
        self.ocr_processor = None
        self.quality_assessor = None
        
        # Initialize components if available
        if CORE_IMPORTS_AVAILABLE:
            try:
                self.performance_optimizer = AdvancedPerformanceOptimizer()
                self.ocr_processor = EnhancedOCRProcessor()
                self.quality_assessor = IntelligentQualityAssessmentEngine()
            except Exception as e:
                logger.warning(f"Could not initialize components: {e}")
        
        # Processing queues and workers
        self.frame_queue = asyncio.Queue(maxsize=10)
        self.analysis_semaphore = asyncio.Semaphore(self.config.max_concurrent_analysis)
        self.worker_tasks = []
        
        # Metrics
        self.metrics = {
            "frames_processed": 0,
            "events_detected": 0,
            "coaching_messages": 0,
            "average_latency_ms": 0.0,
            "error_count": 0,
            "start_time": None
        }
        
        logger.info("RealTimeAnalysisProcessor initialized")
    
    async def start_stream(
        self, 
        user_id: str = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """Start real-time analysis stream"""
        
        if self.state != StreamState.INACTIVE:
            return {"success": False, "error": "Stream already active"}
        
        try:
            self.state = StreamState.CONNECTING
            
            # Start event bus if not running
            await self.event_bus.start()
            
            # Start worker tasks
            self.worker_tasks = [
                asyncio.create_task(self._frame_processor()),
                asyncio.create_task(self._metrics_reporter())
            ]
            
            self.state = StreamState.ACTIVE
            self.metrics["start_time"] = time.time()
            
            # Notify clients
            await self._broadcast_stream_status("started", user_id, session_id)
            
            logger.info(f"Real-time stream started for user: {user_id}")
            
            return {
                "success": True,
                "stream_id": str(uuid.uuid4()),
                "config": asdict(self.config),
                "state": self.state.value
            }
            
        except Exception as e:
            self.state = StreamState.ERROR
            logger.error(f"Error starting stream: {e}")
            return {"success": False, "error": str(e)}
    
    async def stop_stream(self, user_id: str = None) -> Dict[str, Any]:
        """Stop real-time analysis stream"""
        
        if self.state == StreamState.INACTIVE:
            return {"success": True, "message": "Stream already inactive"}
        
        try:
            self.state = StreamState.STOPPING
            
            # Cancel worker tasks
            for task in self.worker_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            self.worker_tasks.clear()
            
            # Clear buffers
            self.frame_buffer.clear()
            
            self.state = StreamState.INACTIVE
            
            # Notify clients
            await self._broadcast_stream_status("stopped", user_id)
            
            logger.info(f"Real-time stream stopped for user: {user_id}")
            
            return {"success": True, "metrics": self.get_metrics()}
            
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_frame(
        self, 
        frame_data: Union[np.ndarray, bytes, str],
        user_id: str = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """Process a single frame in real-time"""
        
        if self.state != StreamState.ACTIVE:
            return {"success": False, "error": "Stream not active"}
        
        try:
            # Convert frame data to numpy array
            frame_array = await self._convert_frame_data(frame_data)
            
            # Create stream frame
            stream_frame = StreamFrame(
                frame_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                frame_data=frame_array,
                processing_start=time.time()
            )
            
            # Add to buffer
            self.frame_buffer.add_frame(stream_frame)
            
            # Queue for processing
            try:
                await self.frame_queue.put(stream_frame)
            except asyncio.QueueFull:
                logger.warning("Frame queue full, dropping frame")
                return {"success": False, "error": "Processing queue full"}
            
            return {
                "success": True,
                "frame_id": stream_frame.frame_id,
                "queued_at": stream_frame.timestamp.isoformat()
            }
            
        except Exception as e:
            self.metrics["error_count"] += 1
            logger.error(f"Error processing frame: {e}")
            return {"success": False, "error": str(e)}
    
    async def _frame_processor(self):
        """Background worker for processing frames"""
        
        while self.state == StreamState.ACTIVE:
            try:
                # Get frame from queue with timeout
                frame = await asyncio.wait_for(
                    self.frame_queue.get(), 
                    timeout=1.0
                )
                
                # Process frame with semaphore
                async with self.analysis_semaphore:
                    await self._analyze_frame(frame)
                
            except asyncio.TimeoutError:
                continue  # No frames to process
            except Exception as e:
                logger.error(f"Error in frame processor: {e}")
                await asyncio.sleep(0.1)  # Brief pause on error
    
    async def _analyze_frame(self, frame: StreamFrame):
        """Analyze a single frame"""
        
        try:
            # Quality assessment
            if self.quality_assessor:
                quality_result = await self._assess_frame_quality(frame)
                if quality_result["quality_score"] < self.config.quality_threshold:
                    logger.debug(f"Frame {frame.frame_id} quality too low: {quality_result['quality_score']}")
                    return
            
            # Run analysis
            analysis_results = await self._run_frame_analysis(frame)
            frame.analysis_results = analysis_results
            
            # Detect events
            events = await self.event_detector.detect_events(frame, analysis_results)
            
            # Generate coaching
            coaching = None
            if self.config.enable_coaching:
                coaching = await self.coaching_engine.generate_live_coaching(
                    frame, analysis_results, events
                )
            
            # Complete frame processing
            frame.processing_end = time.time()
            processing_time = frame.get_processing_time_ms()
            
            # Update metrics
            self.metrics["frames_processed"] += 1
            self.metrics["events_detected"] += len(events)
            if coaching:
                self.metrics["coaching_messages"] += 1
            
            if processing_time:
                # Update average latency
                current_avg = self.metrics["average_latency_ms"]
                frame_count = self.metrics["frames_processed"]
                self.metrics["average_latency_ms"] = (
                    (current_avg * (frame_count - 1) + processing_time) / frame_count
                )
            
            # Broadcast results
            await self._broadcast_frame_results(frame, events, coaching)
            
            # Check latency target
            if processing_time and processing_time > self.config.max_latency_ms:
                await self._handle_latency_warning(frame, processing_time)
            
        except Exception as e:
            self.metrics["error_count"] += 1
            logger.error(f"Error analyzing frame {frame.frame_id}: {e}")
    
    async def _assess_frame_quality(self, frame: StreamFrame) -> Dict[str, Any]:
        """Assess frame quality"""
        
        if not self.quality_assessor:
            return {"quality_score": 1.0}  # Assume good quality
        
        try:
            # Convert frame to PIL Image for quality assessment
            pil_image = Image.fromarray(cv2.cvtColor(frame.frame_data, cv2.COLOR_BGR2RGB))
            
            # Run quality assessment
            quality_result = await asyncio.to_thread(
                self.quality_assessor.assess_quality,
                pil_image
            )
            
            return quality_result
            
        except Exception as e:
            logger.error(f"Error assessing frame quality: {e}")
            return {"quality_score": 0.5}  # Default medium quality
    
    async def _run_frame_analysis(self, frame: StreamFrame) -> Dict[str, Any]:
        """Run comprehensive frame analysis"""
        
        try:
            # Convert frame to format expected by data collector
            frame_bgr = cv2.cvtColor(frame.frame_data, cv2.COLOR_RGB2BGR)
            
            # Save frame temporarily for analysis
            temp_path = f"/tmp/realtime_frame_{frame.frame_id}.png"
            cv2.imwrite(temp_path, frame_bgr)
            
            # Run analysis using enhanced data collector
            if enhanced_data_collector:
                result = await asyncio.to_thread(
                    enhanced_data_collector.from_screenshot,
                    "RealTimePlayer",  # Placeholder IGN
                    temp_path,
                    hero_override=None
                )
                
                # Clean up temp file
                try:
                    Path(temp_path).unlink()
                except:
                    pass
                
                return result or {}
            
            return {}
            
        except Exception as e:
            logger.error(f"Error running frame analysis: {e}")
            return {}
    
    async def _broadcast_frame_results(
        self, 
        frame: StreamFrame, 
        events: List[RealTimeEvent], 
        coaching: Optional[Dict[str, Any]]
    ):
        """Broadcast frame analysis results"""
        
        try:
            # Prepare message
            message = {
                "type": "frame_analysis",
                "frame_id": frame.frame_id,
                "timestamp": frame.timestamp.isoformat(),
                "processing_time_ms": frame.get_processing_time_ms(),
                "analysis_results": frame.analysis_results,
                "events": [event.to_websocket_message() for event in events],
                "coaching": coaching
            }
            
            # Broadcast via WebSocket
            if self.websocket_manager:
                await self.websocket_manager.broadcast(message)
            
            # Publish events to event bus
            for event in events:
                await publish_event(Event(
                    event_type=EventType.USER_ACTION,
                    data=event.to_websocket_message()
                ))
            
        except Exception as e:
            logger.error(f"Error broadcasting frame results: {e}")
    
    async def _broadcast_stream_status(
        self, 
        status: str, 
        user_id: str = None, 
        session_id: str = None
    ):
        """Broadcast stream status update"""
        
        message = {
            "type": "stream_status",
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "metrics": self.get_metrics()
        }
        
        if self.websocket_manager:
            await self.websocket_manager.broadcast(
                message, 
                user_id=user_id, 
                session_id=session_id
            )
    
    async def _handle_latency_warning(self, frame: StreamFrame, processing_time: float):
        """Handle latency warning"""
        
        warning_message = {
            "type": "latency_warning",
            "frame_id": frame.frame_id,
            "processing_time_ms": processing_time,
            "target_ms": self.config.max_latency_ms,
            "suggestion": "Consider reducing analysis complexity or improving hardware"
        }
        
        if self.websocket_manager:
            await self.websocket_manager.broadcast(warning_message)
        
        # Publish performance event
        await publish_event(PerformanceEvent(
            metric_name="frame_processing_time",
            metric_value=processing_time,
            threshold=self.config.max_latency_ms,
            severity="warning"
        ))
    
    async def _metrics_reporter(self):
        """Background metrics reporting"""
        
        while self.state == StreamState.ACTIVE:
            try:
                await asyncio.sleep(10)  # Report every 10 seconds
                
                metrics = self.get_metrics()
                message = {
                    "type": "metrics_update",
                    "timestamp": datetime.now().isoformat(),
                    "metrics": metrics
                }
                
                if self.websocket_manager:
                    await self.websocket_manager.broadcast(message)
                
            except Exception as e:
                logger.error(f"Error reporting metrics: {e}")
    
    async def _convert_frame_data(self, frame_data: Union[np.ndarray, bytes, str]) -> np.ndarray:
        """Convert various frame data formats to numpy array"""
        
        if isinstance(frame_data, np.ndarray):
            return frame_data
        
        elif isinstance(frame_data, bytes):
            # Decode bytes to image
            nparr = np.frombuffer(frame_data, np.uint8)
            frame_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame_array
        
        elif isinstance(frame_data, str):
            # Assume base64 encoded image
            if frame_data.startswith('data:image'):
                # Remove data URL prefix
                frame_data = frame_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(frame_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame_array
        
        else:
            raise ValueError(f"Unsupported frame data type: {type(frame_data)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current processing metrics"""
        
        runtime = 0
        if self.metrics["start_time"]:
            runtime = time.time() - self.metrics["start_time"]
        
        return {
            "state": self.state.value,
            "runtime_seconds": runtime,
            "frames_processed": self.metrics["frames_processed"],
            "events_detected": self.metrics["events_detected"],
            "coaching_messages": self.metrics["coaching_messages"],
            "average_latency_ms": round(self.metrics["average_latency_ms"], 2),
            "error_count": self.metrics["error_count"],
            "fps": round(self.metrics["frames_processed"] / runtime, 2) if runtime > 0 else 0,
            "queue_size": self.frame_queue.qsize(),
            "buffer_size": len(self.frame_buffer.frames)
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return asdict(self.config)
    
    async def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update stream configuration"""
        
        try:
            # Update configuration
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            # Apply configuration changes
            self.frame_buffer = FrameBuffer(self.config.buffer_size)
            self.analysis_semaphore = asyncio.Semaphore(self.config.max_concurrent_analysis)
            
            return {"success": True, "config": asdict(self.config)}
            
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return {"success": False, "error": str(e)}


# Global real-time processor instance
_global_realtime_processor = None


def get_realtime_processor(config: StreamConfig = None) -> RealTimeAnalysisProcessor:
    """Get global real-time processor instance"""
    global _global_realtime_processor
    
    if _global_realtime_processor is None:
        _global_realtime_processor = RealTimeAnalysisProcessor(config)
    
    return _global_realtime_processor


# Utility functions
async def start_realtime_analysis(
    user_id: str = None,
    session_id: str = None,
    config: StreamConfig = None
) -> Dict[str, Any]:
    """Start real-time analysis for a user"""
    processor = get_realtime_processor(config)
    return await processor.start_stream(user_id, session_id)


async def stop_realtime_analysis(user_id: str = None) -> Dict[str, Any]:
    """Stop real-time analysis for a user"""
    processor = get_realtime_processor()
    return await processor.stop_stream(user_id)


async def process_realtime_frame(
    frame_data: Union[np.ndarray, bytes, str],
    user_id: str = None,
    session_id: str = None
) -> Dict[str, Any]:
    """Process a single frame in real-time"""
    processor = get_realtime_processor()
    return await processor.process_frame(frame_data, user_id, session_id)


if __name__ == "__main__":
    # Test the real-time processor
    async def test_realtime_processor():
        """Test real-time processor functionality"""
        
        config = StreamConfig(
            target_fps=1,
            max_latency_ms=1000,
            enable_coaching=True
        )
        
        processor = RealTimeAnalysisProcessor(config)
        
        # Start stream
        result = await processor.start_stream("test_user")
        print(f"Start result: {result}")
        
        # Simulate frame processing
        test_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        for i in range(5):
            frame_result = await processor.process_frame(test_frame, "test_user")
            print(f"Frame {i} result: {frame_result}")
            await asyncio.sleep(1)
        
        # Get metrics
        metrics = processor.get_metrics()
        print(f"Final metrics: {metrics}")
        
        # Stop stream
        stop_result = await processor.stop_stream("test_user")
        print(f"Stop result: {stop_result}")
    
    # Run test
    asyncio.run(test_realtime_processor())
