#!/usr/bin/env python3
"""
Batch Processing Engine - Task 5 Component
==========================================

Advanced batch processing system with async queue management, progress tracking,
and intelligent load balancing for handling 1000+ concurrent users.

Features:
- Multi-priority async queue management
- Dynamic worker scaling based on load
- Progress tracking with real-time updates
- Intelligent batching with size optimization
- Resource-aware processing with throttling
- Comprehensive monitoring and analytics
- Circuit breaker pattern for reliability
"""

import logging
import time
import asyncio
import threading
import queue
import uuid
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json
import weakref
import gc

import psutil
import numpy as np

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Processing priority levels."""
    CRITICAL = 5    # Real-time requirements
    HIGH = 4        # Premium users
    NORMAL = 3      # Standard processing
    LOW = 2         # Background tasks
    BULK = 1        # Batch operations


class ProcessingStatus(Enum):
    """Processing status states."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class BatchRequest:
    """Enhanced batch processing request."""
    request_id: str
    operation: str
    data: Dict[str, Any]
    priority: Priority
    submitted_at: float
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    user_id: str = "anonymous"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.request_id:
            self.request_id = str(uuid.uuid4())


@dataclass
class BatchResult:
    """Batch processing result with comprehensive metrics."""
    request_id: str
    status: ProcessingStatus
    result: Any
    processing_time: float
    queue_wait_time: float
    worker_id: str
    retry_count: int
    memory_used: float  # MB
    cpu_used: float     # Percentage
    batch_size: int
    position_in_batch: int
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before trying to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        # Circuit state
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
        
        logger.debug("⚡ Circuit breaker initialized")
    
    async def execute(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation through circuit breaker."""
        if self.state == "open":
            # Check if we should try to close the circuit
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                logger.info("🔄 Circuit breaker: half-open state")
            else:
                raise Exception("Circuit breaker is open - operation blocked")
        
        try:
            # Execute operation
            result = await operation(*args, **kwargs)
            
            # Success - reset failure count or close circuit
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("✅ Circuit breaker: closed state")
            
            return result
            
        except Exception as e:
            # Failure - increment count and possibly open circuit
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"⚠️ Circuit breaker: opened due to {self.failure_count} failures")
            
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'last_failure_time': self.last_failure_time,
            'recovery_timeout': self.recovery_timeout
        }


class WorkerPool:
    """Dynamic worker pool with intelligent scaling."""
    
    def __init__(self, 
                 min_workers: int = 2,
                 max_workers: int = None,
                 scale_threshold: int = 10,
                 scale_down_delay: float = 300.0):
        """
        Initialize worker pool.
        
        Args:
            min_workers: Minimum number of workers
            max_workers: Maximum number of workers
            scale_threshold: Queue size threshold for scaling up
            scale_down_delay: Delay before scaling down (seconds)
        """
        self.min_workers = min_workers
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) * 2)
        self.scale_threshold = scale_threshold
        self.scale_down_delay = scale_down_delay
        
        # Worker management
        self.workers = {}
        self.worker_stats = defaultdict(dict)
        self.active_workers = 0
        self.last_scale_event = time.time()
        
        # Load balancing
        self.worker_loads = defaultdict(int)
        self.worker_performance = defaultdict(list)
        
        logger.info(f"👥 Worker Pool initialized: {min_workers}-{max_workers} workers")
    
    async def start_workers(self, initial_count: Optional[int] = None):
        """Start initial set of workers."""
        worker_count = initial_count or self.min_workers
        
        logger.info(f"🚀 Starting {worker_count} initial workers")
        
        for i in range(worker_count):
            await self._create_worker(f"worker_{i}")
        
        # Start scaling monitor
        asyncio.create_task(self._scaling_monitor())
    
    async def _create_worker(self, worker_id: str) -> bool:
        """Create a new worker."""
        try:
            worker_task = asyncio.create_task(self._worker_loop(worker_id))
            self.workers[worker_id] = {
                'task': worker_task,
                'created_at': time.time(),
                'requests_processed': 0,
                'avg_processing_time': 0.0,
                'status': 'active'
            }
            
            self.active_workers += 1
            logger.debug(f"👷 Created worker: {worker_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create worker {worker_id}: {e}")
            return False
    
    async def _worker_loop(self, worker_id: str):
        """Main worker processing loop."""
        logger.debug(f"👷 Worker {worker_id} started")
        
        while worker_id in self.workers and self.workers[worker_id]['status'] == 'active':
            try:
                # Get work from batch processor
                # This would integrate with the main batch processor
                await asyncio.sleep(0.1)  # Prevent busy waiting
                
            except Exception as e:
                logger.error(f"❌ Worker {worker_id} error: {e}")
                await asyncio.sleep(1.0)
        
        logger.debug(f"👷 Worker {worker_id} stopped")
    
    async def _scaling_monitor(self):
        """Monitor and adjust worker count based on load."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Get current load metrics
                # This would integrate with queue size monitoring
                current_load = self._estimate_current_load()
                
                # Scale up if needed
                if (current_load > self.scale_threshold and 
                    self.active_workers < self.max_workers):
                    await self._scale_up()
                
                # Scale down if needed
                elif (current_load < self.scale_threshold / 2 and 
                      self.active_workers > self.min_workers and
                      time.time() - self.last_scale_event > self.scale_down_delay):
                    await self._scale_down()
                
            except Exception as e:
                logger.error(f"❌ Scaling monitor error: {e}")
    
    def _estimate_current_load(self) -> int:
        """Estimate current processing load."""
        # This would integrate with actual queue monitoring
        # For now, simulate based on worker performance
        avg_load = sum(self.worker_loads.values()) / max(len(self.worker_loads), 1)
        return int(avg_load)
    
    async def _scale_up(self):
        """Scale up worker count."""
        new_worker_id = f"worker_{int(time.time())}"
        success = await self._create_worker(new_worker_id)
        
        if success:
            self.last_scale_event = time.time()
            logger.info(f"📈 Scaled up: {self.active_workers} workers")
    
    async def _scale_down(self):
        """Scale down worker count."""
        if self.active_workers <= self.min_workers:
            return
        
        # Find least utilized worker
        worker_utilization = {}
        for worker_id, stats in self.workers.items():
            if stats['status'] == 'active':
                worker_utilization[worker_id] = self.worker_loads[worker_id]
        
        if worker_utilization:
            least_utilized = min(worker_utilization, key=worker_utilization.get)
            await self._terminate_worker(least_utilized)
            
            self.last_scale_event = time.time()
            logger.info(f"📉 Scaled down: {self.active_workers} workers")
    
    async def _terminate_worker(self, worker_id: str):
        """Gracefully terminate a worker."""
        if worker_id in self.workers:
            self.workers[worker_id]['status'] = 'terminating'
            self.workers[worker_id]['task'].cancel()
            
            # Wait for graceful shutdown
            try:
                await asyncio.wait_for(self.workers[worker_id]['task'], timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            
            del self.workers[worker_id]
            self.active_workers -= 1
            logger.debug(f"👷 Worker {worker_id} terminated")
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Get worker pool statistics."""
        return {
            'active_workers': self.active_workers,
            'min_workers': self.min_workers,
            'max_workers': self.max_workers,
            'worker_details': {
                worker_id: {
                    'requests_processed': stats['requests_processed'],
                    'avg_processing_time': stats['avg_processing_time'],
                    'status': stats['status'],
                    'uptime': time.time() - stats['created_at']
                }
                for worker_id, stats in self.workers.items()
            },
            'worker_loads': dict(self.worker_loads),
            'last_scale_event': self.last_scale_event
        }


class ProgressTracker:
    """Advanced progress tracking with real-time updates."""
    
    def __init__(self):
        """Initialize progress tracker."""
        self.active_requests = {}
        self.completed_requests = {}
        self.request_lock = threading.RLock()
        
        # Progress callbacks
        self.progress_callbacks = defaultdict(list)
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'completed_requests': 0,
            'failed_requests': 0,
            'avg_completion_time': 0.0,
            'avg_queue_time': 0.0
        }
        
        logger.debug("📊 Progress Tracker initialized")
    
    def start_request(self, request: BatchRequest) -> str:
        """Start tracking a request."""
        with self.request_lock:
            self.active_requests[request.request_id] = {
                'request': request,
                'started_at': time.time(),
                'status': ProcessingStatus.QUEUED,
                'progress': 0.0,
                'stage': 'queued',
                'worker_id': None,
                'estimated_completion': None
            }
            
            self.stats['total_requests'] += 1
        
        return request.request_id
    
    def update_progress(self, 
                       request_id: str, 
                       progress: float, 
                       stage: str = None,
                       worker_id: str = None,
                       estimated_completion: float = None):
        """Update request progress."""
        with self.request_lock:
            if request_id in self.active_requests:
                tracking_data = self.active_requests[request_id]
                tracking_data['progress'] = min(1.0, max(0.0, progress))
                
                if stage:
                    tracking_data['stage'] = stage
                if worker_id:
                    tracking_data['worker_id'] = worker_id
                if estimated_completion:
                    tracking_data['estimated_completion'] = estimated_completion
                
                # Update status based on progress
                if progress >= 1.0:
                    tracking_data['status'] = ProcessingStatus.COMPLETED
                elif progress > 0:
                    tracking_data['status'] = ProcessingStatus.PROCESSING
                
                # Notify callbacks
                self._notify_progress_callbacks(request_id, tracking_data)
    
    def complete_request(self, request_id: str, result: BatchResult):
        """Mark request as completed."""
        with self.request_lock:
            if request_id in self.active_requests:
                tracking_data = self.active_requests[request_id]
                completion_time = time.time() - tracking_data['started_at']
                
                # Move to completed requests
                self.completed_requests[request_id] = {
                    'completed_at': time.time(),
                    'completion_time': completion_time,
                    'status': result.status,
                    'worker_id': result.worker_id,
                    'retry_count': result.retry_count
                }
                
                del self.active_requests[request_id]
                
                # Update statistics
                if result.status == ProcessingStatus.COMPLETED:
                    self.stats['completed_requests'] += 1
                else:
                    self.stats['failed_requests'] += 1
                
                # Update average completion time
                current_avg = self.stats['avg_completion_time']
                self.stats['avg_completion_time'] = (current_avg + completion_time) / 2
                
                # Update average queue time
                queue_time = result.queue_wait_time
                current_queue_avg = self.stats['avg_queue_time']
                self.stats['avg_queue_time'] = (current_queue_avg + queue_time) / 2
    
    def get_request_progress(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get progress for specific request."""
        with self.request_lock:
            if request_id in self.active_requests:
                return self.active_requests[request_id].copy()
            elif request_id in self.completed_requests:
                return self.completed_requests[request_id].copy()
        
        return None
    
    def register_progress_callback(self, request_id: str, callback: Callable):
        """Register callback for progress updates."""
        self.progress_callbacks[request_id].append(callback)
    
    def _notify_progress_callbacks(self, request_id: str, tracking_data: Dict[str, Any]):
        """Notify registered callbacks of progress updates."""
        if request_id in self.progress_callbacks:
            for callback in self.progress_callbacks[request_id]:
                try:
                    asyncio.create_task(callback(request_id, tracking_data))
                except Exception as e:
                    logger.error(f"❌ Progress callback error: {e}")
    
    def get_progress_stats(self) -> Dict[str, Any]:
        """Get progress tracking statistics."""
        with self.request_lock:
            stats = self.stats.copy()
            stats.update({
                'active_requests': len(self.active_requests),
                'completed_requests_stored': len(self.completed_requests),
                'total_tracked': stats['total_requests']
            })
            
            # Calculate success rate
            total_finished = stats['completed_requests'] + stats['failed_requests']
            if total_finished > 0:
                stats['success_rate'] = stats['completed_requests'] / total_finished
            
            return stats


class ResourceMonitor:
    """System resource monitoring and throttling."""
    
    def __init__(self, 
                 cpu_threshold: float = 80.0,
                 memory_threshold: float = 85.0,
                 check_interval: float = 5.0):
        """
        Initialize resource monitor.
        
        Args:
            cpu_threshold: CPU usage threshold for throttling (%)
            memory_threshold: Memory usage threshold for throttling (%)
            check_interval: Resource check interval (seconds)
        """
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.check_interval = check_interval
        
        # Resource history
        self.resource_history = deque(maxlen=100)
        
        # Throttling state
        self.throttling_active = False
        self.throttle_factor = 1.0  # 1.0 = no throttling, 0.5 = 50% throttling
        
        logger.info("📊 Resource Monitor initialized")
        logger.info(f"   - CPU threshold: {cpu_threshold}%")
        logger.info(f"   - Memory threshold: {memory_threshold}%")
    
    async def start_monitoring(self):
        """Start resource monitoring."""
        asyncio.create_task(self._monitoring_loop())
        logger.info("✅ Resource monitoring started")
    
    async def _monitoring_loop(self):
        """Main resource monitoring loop."""
        while True:
            try:
                # Get current resource usage
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent
                
                # Record resource usage
                resource_record = {
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent
                }
                self.resource_history.append(resource_record)
                
                # Check if throttling is needed
                await self._check_throttling(cpu_percent, memory_percent)
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Resource monitoring error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_throttling(self, cpu_percent: float, memory_percent: float):
        """Check if throttling should be applied."""
        should_throttle = (cpu_percent > self.cpu_threshold or 
                          memory_percent > self.memory_threshold)
        
        if should_throttle and not self.throttling_active:
            # Start throttling
            self.throttling_active = True
            self.throttle_factor = 0.7  # Reduce processing by 30%
            logger.warning(f"⚠️ Resource throttling activated (CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%)")
            
        elif not should_throttle and self.throttling_active:
            # Stop throttling
            self.throttling_active = False
            self.throttle_factor = 1.0
            logger.info("✅ Resource throttling deactivated")
        
        # Adjust throttle factor based on severity
        if self.throttling_active:
            severity = max(
                (cpu_percent - self.cpu_threshold) / 20,  # Scale over 20% range
                (memory_percent - self.memory_threshold) / 15  # Scale over 15% range
            )
            self.throttle_factor = max(0.3, 1.0 - severity)  # Minimum 30% capacity
    
    def get_throttle_delay(self) -> float:
        """Get current throttling delay."""
        if self.throttling_active:
            base_delay = 0.1  # 100ms base delay
            return base_delay * (1.0 / self.throttle_factor - 1.0)
        return 0.0
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get resource monitoring statistics."""
        if not self.resource_history:
            return {}
        
        recent_records = list(self.resource_history)[-10:]  # Last 10 records
        
        avg_cpu = np.mean([r['cpu_percent'] for r in recent_records])
        avg_memory = np.mean([r['memory_percent'] for r in recent_records])
        avg_disk = np.mean([r['disk_percent'] for r in recent_records])
        
        return {
            'current_cpu': recent_records[-1]['cpu_percent'],
            'current_memory': recent_records[-1]['memory_percent'],
            'current_disk': recent_records[-1]['disk_percent'],
            'avg_cpu': avg_cpu,
            'avg_memory': avg_memory,
            'avg_disk': avg_disk,
            'throttling_active': self.throttling_active,
            'throttle_factor': self.throttle_factor,
            'resource_history_size': len(self.resource_history)
        }


class BatchProcessor:
    """
    Advanced batch processing engine with comprehensive optimization.
    
    Features:
    - Multi-priority queue management
    - Dynamic worker scaling
    - Progress tracking with real-time updates
    - Resource monitoring and throttling
    - Circuit breaker for fault tolerance
    - Intelligent batching optimization
    """
    
    def __init__(self,
                 max_queue_size: int = 10000,
                 default_batch_size: int = 10,
                 max_workers: int = None,
                 enable_circuit_breaker: bool = True,
                 enable_resource_monitoring: bool = True):
        """
        Initialize batch processor.
        
        Args:
            max_queue_size: Maximum queue size per priority
            default_batch_size: Default batch size for processing
            max_workers: Maximum number of workers
            enable_circuit_breaker: Enable circuit breaker pattern
            enable_resource_monitoring: Enable resource monitoring
        """
        self.max_queue_size = max_queue_size
        self.default_batch_size = default_batch_size
        
        # Priority queues
        self.queues = {
            Priority.CRITICAL: asyncio.Queue(maxsize=max_queue_size),
            Priority.HIGH: asyncio.Queue(maxsize=max_queue_size),
            Priority.NORMAL: asyncio.Queue(maxsize=max_queue_size),
            Priority.LOW: asyncio.Queue(maxsize=max_queue_size),
            Priority.BULK: asyncio.Queue(maxsize=max_queue_size * 2)  # Larger for bulk
        }
        
        # Worker pool
        self.worker_pool = WorkerPool(max_workers=max_workers)
        
        # Progress tracking
        self.progress_tracker = ProgressTracker()
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker() if enable_circuit_breaker else None
        
        # Resource monitoring
        self.resource_monitor = ResourceMonitor() if enable_resource_monitoring else None
        
        # Batch processing statistics
        self.batch_stats = {
            'total_requests': 0,
            'processed_requests': 0,
            'failed_requests': 0,
            'avg_batch_size': 0.0,
            'avg_processing_time': 0.0,
            'throughput_rps': 0.0,
            'queue_sizes': {p.name: 0 for p in Priority},
            'active_batches': 0
        }
        
        # Performance optimization
        self.optimization_enabled = True
        self.adaptive_batching = True
        
        logger.info("⚡ Advanced Batch Processor initialized")
        logger.info(f"   - Queue capacity: {max_queue_size} per priority")
        logger.info(f"   - Default batch size: {default_batch_size}")
        logger.info(f"   - Circuit breaker: {enable_circuit_breaker}")
        logger.info(f"   - Resource monitoring: {enable_resource_monitoring}")
    
    async def submit_request(self, request: BatchRequest) -> str:
        """
        Submit request for batch processing.
        
        Args:
            request: Batch processing request
            
        Returns:
            Request ID for tracking
        """
        try:
            # Add to appropriate priority queue
            queue = self.queues[request.priority]
            await queue.put(request)
            
            # Start progress tracking
            self.progress_tracker.start_request(request)
            
            # Update statistics
            self.batch_stats['total_requests'] += 1
            self.batch_stats['queue_sizes'][request.priority.name] = queue.qsize()
            
            logger.debug(f"📥 Request queued: {request.request_id} (priority: {request.priority.name})")
            return request.request_id
            
        except asyncio.QueueFull:
            raise Exception(f"Queue full for priority {request.priority.name}")
    
    async def start_processing(self):
        """Start batch processing services."""
        logger.info("🚀 Starting batch processing services")
        
        # Start worker pool
        await self.worker_pool.start_workers()
        
        # Start resource monitoring
        if self.resource_monitor:
            await self.resource_monitor.start_monitoring()
        
        # Start batch processing loops
        for priority in Priority:
            asyncio.create_task(self._batch_processing_loop(priority))
        
        # Start statistics updates
        asyncio.create_task(self._update_statistics())
        
        logger.info("✅ Batch processing services started")
    
    async def _batch_processing_loop(self, priority: Priority):
        """Main batch processing loop for specific priority."""
        logger.debug(f"🔄 Batch processing loop started for {priority.name}")
        
        while True:
            try:
                # Get batch of requests
                batch = await self._get_next_batch(priority)
                
                if batch:
                    # Process batch
                    asyncio.create_task(self._process_batch(batch, priority))
                else:
                    # No work, short sleep
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"❌ Batch processing error for {priority.name}: {e}")
                await asyncio.sleep(1.0)
    
    async def _get_next_batch(self, priority: Priority) -> List[BatchRequest]:
        """Get next batch of requests for processing."""
        batch = []
        queue = self.queues[priority]
        
        # Determine optimal batch size
        batch_size = self._calculate_optimal_batch_size(priority)
        
        # Apply resource throttling
        if self.resource_monitor and self.resource_monitor.throttling_active:
            batch_size = max(1, int(batch_size * self.resource_monitor.throttle_factor))
            
            # Add throttling delay
            throttle_delay = self.resource_monitor.get_throttle_delay()
            if throttle_delay > 0:
                await asyncio.sleep(throttle_delay)
        
        # Collect batch
        for _ in range(batch_size):
            try:
                request = queue.get_nowait()
                batch.append(request)
            except asyncio.QueueEmpty:
                break
        
        return batch
    
    def _calculate_optimal_batch_size(self, priority: Priority) -> int:
        """Calculate optimal batch size based on conditions."""
        base_size = self.default_batch_size
        
        # Adjust based on priority
        priority_multipliers = {
            Priority.CRITICAL: 1,      # Process immediately
            Priority.HIGH: 2,          # Small batches for speed
            Priority.NORMAL: 3,        # Standard batching
            Priority.LOW: 5,           # Larger batches for efficiency
            Priority.BULK: 10          # Large batches for bulk operations
        }
        
        optimal_size = base_size * priority_multipliers.get(priority, 1)
        
        # Adjust based on system load
        if self.resource_monitor:
            cpu_percent = psutil.cpu_percent()
            if cpu_percent > 70:
                optimal_size = max(1, optimal_size // 2)  # Reduce batch size under high CPU
        
        return optimal_size
    
    async def _process_batch(self, batch: List[BatchRequest], priority: Priority):
        """Process a batch of requests."""
        if not batch:
            return
        
        batch_id = f"batch_{int(time.time()*1000)}"
        logger.debug(f"🔄 Processing batch {batch_id}: {len(batch)} requests (priority: {priority.name})")
        
        self.batch_stats['active_batches'] += 1
        batch_start_time = time.time()
        
        try:
            # Process requests in parallel within batch
            tasks = []
            for i, request in enumerate(batch):
                # Update progress
                self.progress_tracker.update_progress(
                    request.request_id, 
                    0.1, 
                    stage="batch_processing",
                    worker_id=batch_id
                )
                
                # Create processing task
                task = asyncio.create_task(
                    self._process_single_request(request, i, len(batch), batch_id)
                )
                tasks.append((request.request_id, task))
            
            # Wait for all tasks to complete
            for request_id, task in tasks:
                try:
                    result = await task
                    self.progress_tracker.complete_request(request_id, result)
                    
                    if result.status == ProcessingStatus.COMPLETED:
                        self.batch_stats['processed_requests'] += 1
                    else:
                        self.batch_stats['failed_requests'] += 1
                        
                except Exception as e:
                    logger.error(f"❌ Task failed for {request_id}: {e}")
                    self.batch_stats['failed_requests'] += 1
            
            # Update batch statistics
            batch_time = time.time() - batch_start_time
            current_avg = self.batch_stats['avg_processing_time']
            self.batch_stats['avg_processing_time'] = (current_avg + batch_time) / 2
            
            current_batch_avg = self.batch_stats['avg_batch_size']
            self.batch_stats['avg_batch_size'] = (current_batch_avg + len(batch)) / 2
            
            logger.debug(f"✅ Batch {batch_id} completed: {len(batch)} requests in {batch_time:.2f}s")
            
        finally:
            self.batch_stats['active_batches'] -= 1
    
    async def _process_single_request(self, 
                                    request: BatchRequest, 
                                    position: int, 
                                    batch_size: int,
                                    worker_id: str) -> BatchResult:
        """Process a single request within a batch."""
        start_time = time.time()
        queue_wait_time = start_time - request.submitted_at
        
        # Update progress
        self.progress_tracker.update_progress(
            request.request_id, 
            0.3, 
            stage="processing",
            worker_id=worker_id
        )
        
        try:
            # Execute through circuit breaker if enabled
            if self.circuit_breaker:
                result = await self.circuit_breaker.execute(
                    self._execute_request_operation, 
                    request
                )
            else:
                result = await self._execute_request_operation(request)
            
            processing_time = time.time() - start_time
            
            # Update final progress
            self.progress_tracker.update_progress(request.request_id, 1.0, stage="completed")
            
            return BatchResult(
                request_id=request.request_id,
                status=ProcessingStatus.COMPLETED,
                result=result,
                processing_time=processing_time,
                queue_wait_time=queue_wait_time,
                worker_id=worker_id,
                retry_count=request.retry_count,
                memory_used=psutil.Process().memory_info().rss / 1024**2,  # MB
                cpu_used=psutil.cpu_percent(),
                batch_size=batch_size,
                position_in_batch=position
            )
            
        except Exception as e:
            logger.error(f"❌ Request processing failed: {e}")
            
            return BatchResult(
                request_id=request.request_id,
                status=ProcessingStatus.FAILED,
                result=None,
                processing_time=time.time() - start_time,
                queue_wait_time=queue_wait_time,
                worker_id=worker_id,
                retry_count=request.retry_count,
                memory_used=psutil.Process().memory_info().rss / 1024**2,
                cpu_used=psutil.cpu_percent(),
                batch_size=batch_size,
                position_in_batch=position,
                error=str(e)
            )
    
    async def _execute_request_operation(self, request: BatchRequest) -> Dict[str, Any]:
        """Execute the actual request operation."""
        # This would integrate with the actual processing systems
        # For now, simulate processing based on operation type
        
        operation = request.operation
        data = request.data
        
        if operation == "screenshot_analysis":
            # Simulate screenshot analysis
            processing_time = 0.5 + (request.priority.value * 0.1)
            await asyncio.sleep(processing_time)
            
            return {
                'operation': operation,
                'image_path': data.get('image_path', ''),
                'ign': data.get('ign', ''),
                'analysis_result': 'mock_analysis_complete',
                'processing_time': processing_time,
                'batch_processed': True
            }
        
        elif operation == "hero_analysis":
            # Simulate hero analysis
            await asyncio.sleep(0.3)
            
            return {
                'operation': operation,
                'hero': data.get('hero', 'unknown'),
                'analysis': 'mock_hero_analysis',
                'batch_processed': True
            }
        
        else:
            # Generic operation
            await asyncio.sleep(0.2)
            return {
                'operation': operation,
                'data': data,
                'result': 'mock_generic_result',
                'batch_processed': True
            }
    
    async def _update_statistics(self):
        """Update processing statistics."""
        last_update = time.time()
        last_processed = 0
        
        while True:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds
                
                # Calculate throughput
                current_time = time.time()
                time_delta = current_time - last_update
                processed_delta = self.batch_stats['processed_requests'] - last_processed
                
                if time_delta > 0:
                    self.batch_stats['throughput_rps'] = processed_delta / time_delta
                
                # Update queue sizes
                for priority, queue in self.queues.items():
                    self.batch_stats['queue_sizes'][priority.name] = queue.qsize()
                
                last_update = current_time
                last_processed = self.batch_stats['processed_requests']
                
            except Exception as e:
                logger.error(f"❌ Statistics update error: {e}")
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive batch processing statistics."""
        stats = self.batch_stats.copy()
        
        # Add component stats
        stats['worker_pool'] = self.worker_pool.get_worker_stats()
        stats['progress_tracking'] = self.progress_tracker.get_progress_stats()
        
        if self.resource_monitor:
            stats['resource_monitoring'] = self.resource_monitor.get_resource_stats()
        
        if self.circuit_breaker:
            stats['circuit_breaker'] = self.circuit_breaker.get_status()
        
        # Calculate performance metrics
        total_processed = stats['processed_requests'] + stats['failed_requests']
        if total_processed > 0:
            stats['success_rate'] = stats['processed_requests'] / total_processed
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform batch processor health check."""
        health_status = {
            'status': 'healthy',
            'components': {},
            'performance': {}
        }
        
        # Check queue health
        total_queued = sum(queue.qsize() for queue in self.queues.values())
        queue_utilization = total_queued / (len(self.queues) * self.max_queue_size)
        
        health_status['components']['queues'] = {
            'status': 'healthy' if queue_utilization < 0.8 else 'degraded',
            'utilization': queue_utilization,
            'total_queued': total_queued
        }
        
        # Check worker health
        worker_stats = self.worker_pool.get_worker_stats()
        health_status['components']['workers'] = {
            'status': 'healthy' if worker_stats['active_workers'] > 0 else 'unhealthy',
            'active_workers': worker_stats['active_workers'],
            'max_workers': worker_stats['max_workers']
        }
        
        # Check resource health
        if self.resource_monitor:
            resource_stats = self.resource_monitor.get_resource_stats()
            health_status['components']['resources'] = {
                'status': 'healthy' if not resource_stats['throttling_active'] else 'throttled',
                'cpu_percent': resource_stats['current_cpu'],
                'memory_percent': resource_stats['current_memory']
            }
        
        # Overall health determination
        component_statuses = [comp['status'] for comp in health_status['components'].values()]
        if all(status == 'healthy' for status in component_statuses):
            health_status['status'] = 'healthy'
        elif any(status == 'unhealthy' for status in component_statuses):
            health_status['status'] = 'unhealthy'
        else:
            health_status['status'] = 'degraded'
        
        # Performance metrics
        health_status['performance'] = {
            'throughput_rps': self.batch_stats['throughput_rps'],
            'avg_processing_time': self.batch_stats['avg_processing_time'],
            'success_rate': self.batch_stats.get('success_rate', 0.0),
            'active_batches': self.batch_stats['active_batches']
        }
        
        return health_status


# Global batch processor instance
batch_processor = BatchProcessor()


def get_batch_processor() -> BatchProcessor:
    """Get the global batch processor instance."""
    return batch_processor


# Batch processing decorators
def batch_process(priority: Priority = Priority.NORMAL, timeout: float = 30.0):
    """Decorator for batch processing operations."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            processor = get_batch_processor()
            
            # Create batch request
            request = BatchRequest(
                request_id=str(uuid.uuid4()),
                operation=func.__name__,
                data={'args': args, 'kwargs': kwargs},
                priority=priority,
                submitted_at=time.time(),
                timeout=timeout
            )
            
            # Submit to batch processor
            request_id = await processor.submit_request(request)
            
            # Wait for completion (simplified for demo)
            max_wait = timeout
            poll_interval = 0.1
            waited = 0
            
            while waited < max_wait:
                progress = processor.progress_tracker.get_request_progress(request_id)
                if progress and progress.get('status') == ProcessingStatus.COMPLETED:
                    return progress.get('result', {})
                
                await asyncio.sleep(poll_interval)
                waited += poll_interval
            
            raise Exception(f"Batch processing timeout for {request_id}")
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test batch processing system
    async def test_batch_processing():
        """Test batch processing functionality."""
        logger.info("🧪 Testing Batch Processing Engine")
        
        processor = BatchProcessor(
            max_queue_size=100,
            default_batch_size=5,
            enable_circuit_breaker=True,
            enable_resource_monitoring=True
        )
        
        # Start processing
        await processor.start_processing()
        
        # Submit test requests
        test_requests = []
        for i in range(10):
            request = BatchRequest(
                request_id=f"test_{i}",
                operation="screenshot_analysis",
                data={'image_path': f'test_{i}.png', 'ign': f'Player_{i}'},
                priority=Priority.NORMAL,
                submitted_at=time.time()
            )
            
            request_id = await processor.submit_request(request)
            test_requests.append(request_id)
        
        logger.info(f"📥 Submitted {len(test_requests)} test requests")
        
        # Wait for processing
        await asyncio.sleep(5)
        
        # Check results
        completed = 0
        for request_id in test_requests:
            progress = processor.progress_tracker.get_request_progress(request_id)
            if progress and progress.get('status') == ProcessingStatus.COMPLETED:
                completed += 1
        
        logger.info(f"✅ Completed: {completed}/{len(test_requests)} requests")
        
        # Get statistics
        stats = processor.get_comprehensive_stats()
        logger.info(f"📈 Batch stats: {json.dumps(stats, indent=2, default=str)}")
        
        # Health check
        health = await processor.health_check()
        logger.info(f"🏥 Health status: {health['status']}")
    
    import json
    asyncio.run(test_batch_processing())
