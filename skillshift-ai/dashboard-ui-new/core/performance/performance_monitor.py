"""
Advanced Performance Monitoring for MLBB Coach AI
Real-time performance tracking, optimization suggestions, and alerting
"""

import asyncio
import logging
import time
import psutil
import statistics
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IO = "network_io"
    CACHE_HIT_RATE = "cache_hit_rate"
    DATABASE_CONNECTIONS = "db_connections"
    QUEUE_SIZE = "queue_size"


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricValue:
    """Individual metric measurement."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration."""
    warning_threshold: float
    error_threshold: float
    critical_threshold: float
    comparison_operator: str = ">"  # >, <, >=, <=
    time_window: int = 300  # seconds


@dataclass
class Alert:
    """Performance alert."""
    metric_type: MetricType
    level: AlertLevel
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class PerformanceMonitor:
    """Advanced performance monitoring system."""
    
    def __init__(
        self,
        collection_interval: int = 10,
        retention_period: int = 86400,  # 24 hours
        max_samples_per_metric: int = 8640  # 24 hours at 10s intervals
    ):
        """Initialize performance monitor."""
        self.collection_interval = collection_interval
        self.retention_period = retention_period
        self.max_samples_per_metric = max_samples_per_metric
        
        # Metric storage
        self.metrics: Dict[MetricType, deque] = defaultdict(
            lambda: deque(maxlen=self.max_samples_per_metric)
        )
        
        # Custom metric collectors
        self.custom_collectors: Dict[str, Callable] = {}
        
        # Performance thresholds
        self.thresholds: Dict[MetricType, PerformanceThreshold] = {
            MetricType.RESPONSE_TIME: PerformanceThreshold(100, 500, 1000),  # ms
            MetricType.CPU_USAGE: PerformanceThreshold(70, 85, 95),  # %
            MetricType.MEMORY_USAGE: PerformanceThreshold(70, 85, 95),  # %
            MetricType.ERROR_RATE: PerformanceThreshold(1, 5, 10),  # %
            MetricType.CACHE_HIT_RATE: PerformanceThreshold(80, 60, 40, "<"),  # %
            MetricType.DATABASE_CONNECTIONS: PerformanceThreshold(80, 90, 95),  # % of pool
        }
        
        # Alert management
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        # Background tasks
        self.collection_task = None
        self.cleanup_task = None
        
        # Performance statistics
        self.stats = {
            "total_metrics_collected": 0,
            "alerts_generated": 0,
            "uptime_start": datetime.now(),
        }
        
    async def start(self):
        """Start performance monitoring."""
        self.collection_task = asyncio.create_task(self._collect_metrics())
        self.cleanup_task = asyncio.create_task(self._cleanup_old_data())
        
        logger.info("Performance monitoring started")
        
    async def stop(self):
        """Stop performance monitoring."""
        if self.collection_task:
            self.collection_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
            
        logger.info("Performance monitoring stopped")
    
    def add_custom_collector(self, name: str, collector: Callable[[], float]):
        """Add custom metric collector."""
        self.custom_collectors[name] = collector
        logger.info(f"Added custom metric collector: {name}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add alert callback function."""
        self.alert_callbacks.append(callback)
    
    async def record_metric(
        self, 
        metric_type: MetricType, 
        value: float, 
        labels: Dict[str, str] = None
    ):
        """Record a metric value."""
        metric_value = MetricValue(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        
        self.metrics[metric_type].append(metric_value)
        self.stats["total_metrics_collected"] += 1
        
        # Check thresholds
        await self._check_thresholds(metric_type, value)
    
    async def _collect_metrics(self):
        """Background task to collect system metrics."""
        while True:
            try:
                await asyncio.sleep(self.collection_interval)
                
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Collect custom metrics
                await self._collect_custom_metrics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
    
    async def _collect_system_metrics(self):
        """Collect system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            await self.record_metric(MetricType.CPU_USAGE, cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            await self.record_metric(MetricType.MEMORY_USAGE, memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            await self.record_metric(MetricType.DISK_USAGE, disk_percent)
            
            # Network I/O
            net_io = psutil.net_io_counters()
            if hasattr(self, '_last_net_io'):
                bytes_sent = net_io.bytes_sent - self._last_net_io.bytes_sent
                bytes_recv = net_io.bytes_recv - self._last_net_io.bytes_recv
                total_bytes = bytes_sent + bytes_recv
                await self.record_metric(MetricType.NETWORK_IO, total_bytes)
            
            self._last_net_io = net_io
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def _collect_custom_metrics(self):
        """Collect custom metrics."""
        for name, collector in self.custom_collectors.items():
            try:
                value = await collector() if asyncio.iscoroutinefunction(collector) else collector()
                # Custom metrics are stored with the name as a label
                await self.record_metric(MetricType.THROUGHPUT, value, {"custom": name})
            except Exception as e:
                logger.error(f"Error collecting custom metric {name}: {e}")
    
    async def _check_thresholds(self, metric_type: MetricType, value: float):
        """Check if metric value exceeds thresholds."""
        threshold = self.thresholds.get(metric_type)
        if not threshold:
            return
        
        alert_key = f"{metric_type.value}"
        comparison_op = threshold.comparison_operator
        
        # Determine alert level
        alert_level = None
        threshold_value = None
        
        if comparison_op in [">", ">="]:
            if value >= threshold.critical_threshold:
                alert_level = AlertLevel.CRITICAL
                threshold_value = threshold.critical_threshold
            elif value >= threshold.error_threshold:
                alert_level = AlertLevel.ERROR
                threshold_value = threshold.error_threshold
            elif value >= threshold.warning_threshold:
                alert_level = AlertLevel.WARNING
                threshold_value = threshold.warning_threshold
        else:  # "<", "<="
            if value <= threshold.critical_threshold:
                alert_level = AlertLevel.CRITICAL
                threshold_value = threshold.critical_threshold
            elif value <= threshold.error_threshold:
                alert_level = AlertLevel.ERROR
                threshold_value = threshold.error_threshold
            elif value <= threshold.warning_threshold:
                alert_level = AlertLevel.WARNING
                threshold_value = threshold.warning_threshold
        
        if alert_level:
            # Create or update alert
            if alert_key not in self.active_alerts:
                alert = Alert(
                    metric_type=metric_type,
                    level=alert_level,
                    message=f"{metric_type.value} is {value:.2f} (threshold: {threshold_value})",
                    value=value,
                    threshold=threshold_value,
                    timestamp=datetime.now()
                )
                
                self.active_alerts[alert_key] = alert
                self.alert_history.append(alert)
                self.stats["alerts_generated"] += 1
                
                # Trigger callbacks
                for callback in self.alert_callbacks:
                    try:
                        await callback(alert) if asyncio.iscoroutinefunction(callback) else callback(alert)
                    except Exception as e:
                        logger.error(f"Error in alert callback: {e}")
                        
                logger.warning(f"Alert triggered: {alert.message}")
        
        else:
            # Resolve alert if it exists
            if alert_key in self.active_alerts:
                alert = self.active_alerts[alert_key]
                alert.resolved = True
                alert.resolved_at = datetime.now()
                del self.active_alerts[alert_key]
                
                logger.info(f"Alert resolved: {alert.message}")
    
    async def _cleanup_old_data(self):
        """Background task to clean up old metric data."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff_time = datetime.now() - timedelta(seconds=self.retention_period)
                
                # Clean up metrics
                for metric_type, values in self.metrics.items():
                    # Remove old values (deque automatically handles max length)
                    while values and values[0].timestamp < cutoff_time:
                        values.popleft()
                
                # Clean up old alerts from history
                self.alert_history = [
                    alert for alert in self.alert_history 
                    if alert.timestamp > cutoff_time
                ]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error cleaning up old data: {e}")
    
    def get_metric_statistics(
        self, 
        metric_type: MetricType, 
        time_window: int = 300
    ) -> Dict[str, float]:
        """Get statistical summary of a metric over time window."""
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        
        values = [
            mv.value for mv in self.metrics[metric_type]
            if mv.timestamp > cutoff_time
        ]
        
        if not values:
            return {}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "percentile_95": np.percentile(values, 95),
            "percentile_99": np.percentile(values, 99),
        }
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metric values."""
        current_metrics = {}
        
        for metric_type, values in self.metrics.items():
            if values:
                latest = values[-1]
                current_metrics[metric_type.value] = {
                    "value": latest.value,
                    "timestamp": latest.timestamp.isoformat(),
                    "labels": latest.labels
                }
        
        return current_metrics
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "uptime": (datetime.now() - self.stats["uptime_start"]).total_seconds(),
            "current_metrics": self.get_current_metrics(),
            "active_alerts": len(self.active_alerts),
            "total_alerts": len(self.alert_history),
            "statistics": {},
            "recommendations": self._generate_recommendations()
        }
        
        # Add statistics for each metric type
        for metric_type in MetricType:
            if metric_type in self.metrics and self.metrics[metric_type]:
                summary["statistics"][metric_type.value] = self.get_metric_statistics(metric_type)
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # CPU recommendations
        cpu_stats = self.get_metric_statistics(MetricType.CPU_USAGE)
        if cpu_stats and cpu_stats.get("mean", 0) > 80:
            recommendations.append(
                "High CPU usage detected. Consider scaling horizontally or optimizing CPU-intensive operations."
            )
        
        # Memory recommendations
        memory_stats = self.get_metric_statistics(MetricType.MEMORY_USAGE)
        if memory_stats and memory_stats.get("mean", 0) > 80:
            recommendations.append(
                "High memory usage detected. Consider increasing memory allocation or implementing memory optimization."
            )
        
        # Cache recommendations
        cache_stats = self.get_metric_statistics(MetricType.CACHE_HIT_RATE)
        if cache_stats and cache_stats.get("mean", 100) < 70:
            recommendations.append(
                "Low cache hit rate detected. Consider reviewing cache policies and warming strategies."
            )
        
        # Response time recommendations
        response_stats = self.get_metric_statistics(MetricType.RESPONSE_TIME)
        if response_stats and response_stats.get("percentile_95", 0) > 500:
            recommendations.append(
                "High response times detected. Consider optimizing database queries and adding caching."
            )
        
        return recommendations
    
    async def generate_performance_report(self) -> str:
        """Generate detailed performance report."""
        summary = self.get_performance_summary()
        
        report = f"""
# MLBB Coach AI - Performance Report
Generated: {summary['timestamp']}
Uptime: {summary['uptime']:.0f} seconds

## Current Status
- Active Alerts: {summary['active_alerts']}
- Total Alerts (24h): {summary['total_alerts']}
- Metrics Collected: {self.stats['total_metrics_collected']}

## Current Metrics
"""
        
        for metric, data in summary['current_metrics'].items():
            report += f"- {metric.replace('_', ' ').title()}: {data['value']:.2f}\n"
        
        report += "\n## Performance Statistics (Last 5 minutes)\n"
        
        for metric, stats in summary['statistics'].items():
            if stats:
                report += f"\n### {metric.replace('_', ' ').title()}\n"
                report += f"- Mean: {stats.get('mean', 0):.2f}\n"
                report += f"- Max: {stats.get('max', 0):.2f}\n"
                report += f"- 95th Percentile: {stats.get('percentile_95', 0):.2f}\n"
        
        if summary['recommendations']:
            report += "\n## Recommendations\n"
            for i, rec in enumerate(summary['recommendations'], 1):
                report += f"{i}. {rec}\n"
        
        return report


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


async def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
        await _performance_monitor.start()
    
    return _performance_monitor


# Convenience functions
async def record_response_time(endpoint: str, duration_ms: float):
    """Record API response time."""
    monitor = await get_performance_monitor()
    await monitor.record_metric(
        MetricType.RESPONSE_TIME, 
        duration_ms, 
        {"endpoint": endpoint}
    )


async def record_error_rate(service: str, error_rate: float):
    """Record service error rate."""
    monitor = await get_performance_monitor()
    await monitor.record_metric(
        MetricType.ERROR_RATE, 
        error_rate, 
        {"service": service}
    )


async def record_cache_hit_rate(cache_type: str, hit_rate: float):
    """Record cache hit rate."""
    monitor = await get_performance_monitor()
    await monitor.record_metric(
        MetricType.CACHE_HIT_RATE, 
        hit_rate, 
        {"cache_type": cache_type}
    )
