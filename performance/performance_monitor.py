"""
Advanced Performance Monitoring System for LLM Multimodal Stack
"""
import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import json
import threading
from contextlib import asynccontextmanager
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class PerformanceStats:
    """Performance statistics for a metric"""
    name: str
    count: int
    mean: float
    median: float
    p95: float
    p99: float
    min: float
    max: float
    std: float
    last_value: float
    last_updated: datetime

@dataclass
class SystemMetrics:
    """System-level performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    timestamp: datetime

class PerformanceMonitor:
    """Advanced performance monitoring system"""
    
    def __init__(self, max_metrics: int = 10000, collection_interval: float = 1.0):
        self.max_metrics = max_metrics
        self.collection_interval = collection_interval
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics))
        self.system_metrics: deque = deque(maxlen=1000)
        self.alerts: List[Dict[str, Any]] = []
        self.running = False
        self._lock = threading.Lock()
        self._system_monitor_task: Optional[asyncio.Task] = None
        
        # Performance thresholds
        self.thresholds = {
            "api_response_time_ms": 1000,
            "model_inference_time_ms": 5000,
            "database_query_time_ms": 100,
            "vector_search_time_ms": 200,
            "file_upload_time_ms": 2000,
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_io_mb_per_sec": 100.0,
            "network_mb_per_sec": 50.0
        }
        
        # Alert callbacks
        self.alert_callbacks: List[Callable] = []
    
    async def start(self):
        """Start the performance monitor"""
        if self.running:
            return
        
        self.running = True
        self._system_monitor_task = asyncio.create_task(self._system_monitor_loop())
        logger.info("Performance monitor started")
    
    async def stop(self):
        """Stop the performance monitor"""
        self.running = False
        if self._system_monitor_task:
            self._system_monitor_task.cancel()
            try:
                await self._system_monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitor stopped")
    
    async def _system_monitor_loop(self):
        """System monitoring loop"""
        last_disk_io = psutil.disk_io_counters()
        last_network_io = psutil.net_io_counters()
        
        while self.running:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                
                # Calculate disk I/O rates
                current_disk_io = psutil.disk_io_counters()
                disk_read_mb = (current_disk_io.read_bytes - last_disk_io.read_bytes) / (1024 * 1024)
                disk_write_mb = (current_disk_io.write_bytes - last_disk_io.write_bytes) / (1024 * 1024)
                last_disk_io = current_disk_io
                
                # Calculate network I/O rates
                current_network_io = psutil.net_io_counters()
                network_sent_mb = (current_network_io.bytes_sent - last_network_io.bytes_sent) / (1024 * 1024)
                network_recv_mb = (current_network_io.bytes_recv - last_network_io.bytes_recv) / (1024 * 1024)
                last_network_io = current_network_io
                
                system_metric = SystemMetrics(
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / (1024 * 1024),
                    disk_io_read_mb=disk_read_mb,
                    disk_io_write_mb=disk_write_mb,
                    network_sent_mb=network_sent_mb,
                    network_recv_mb=network_recv_mb,
                    timestamp=datetime.utcnow()
                )
                
                with self._lock:
                    self.system_metrics.append(system_metric)
                
                # Check system thresholds
                await self._check_system_thresholds(system_metric)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in system monitor loop: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _check_system_thresholds(self, metric: SystemMetrics):
        """Check system metrics against thresholds"""
        alerts = []
        
        if metric.cpu_percent > self.thresholds["cpu_percent"]:
            alerts.append({
                "type": "cpu_high",
                "value": metric.cpu_percent,
                "threshold": self.thresholds["cpu_percent"],
                "timestamp": metric.timestamp
            })
        
        if metric.memory_percent > self.thresholds["memory_percent"]:
            alerts.append({
                "type": "memory_high",
                "value": metric.memory_percent,
                "threshold": self.thresholds["memory_percent"],
                "timestamp": metric.timestamp
            })
        
        disk_io_total = metric.disk_io_read_mb + metric.disk_io_write_mb
        if disk_io_total > self.thresholds["disk_io_mb_per_sec"]:
            alerts.append({
                "type": "disk_io_high",
                "value": disk_io_total,
                "threshold": self.thresholds["disk_io_mb_per_sec"],
                "timestamp": metric.timestamp
            })
        
        network_total = metric.network_sent_mb + metric.network_recv_mb
        if network_total > self.thresholds["network_mb_per_sec"]:
            alerts.append({
                "type": "network_high",
                "value": network_total,
                "threshold": self.thresholds["network_mb_per_sec"],
                "timestamp": metric.timestamp
            })
        
        for alert in alerts:
            await self._trigger_alert(alert)
    
    async def _trigger_alert(self, alert: Dict[str, Any]):
        """Trigger performance alert"""
        with self._lock:
            self.alerts.append(alert)
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def record_metric(self, name: str, value: float, metadata: Dict[str, Any] = None, tags: Dict[str, str] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            tags=tags or {}
        )
        
        with self._lock:
            self.metrics[name].append(metric)
        
        # Check threshold
        threshold_key = f"{name}_ms" if not name.endswith("_ms") else name
        if threshold_key in self.thresholds:
            threshold = self.thresholds[threshold_key]
            if value > threshold:
                asyncio.create_task(self._trigger_alert({
                    "type": "metric_threshold_exceeded",
                    "metric": name,
                    "value": value,
                    "threshold": threshold,
                    "timestamp": metric.timestamp
                }))
    
    @asynccontextmanager
    async def measure_time(self, metric_name: str, metadata: Dict[str, Any] = None, tags: Dict[str, str] = None):
        """Context manager for measuring execution time"""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_metric(metric_name, duration_ms, metadata, tags)
    
    def get_metric_stats(self, name: str, window_minutes: int = 5) -> Optional[PerformanceStats]:
        """Get performance statistics for a metric"""
        with self._lock:
            if name not in self.metrics:
                return None
            
            cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
            recent_metrics = [m for m in self.metrics[name] if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return None
            
            values = [m.value for m in recent_metrics]
            
            return PerformanceStats(
                name=name,
                count=len(values),
                mean=statistics.mean(values),
                median=statistics.median(values),
                p95=np.percentile(values, 95),
                p99=np.percentile(values, 99),
                min=min(values),
                max=max(values),
                std=statistics.stdev(values) if len(values) > 1 else 0.0,
                last_value=values[-1],
                last_updated=recent_metrics[-1].timestamp
            )
    
    def get_system_stats(self, window_minutes: int = 5) -> Optional[Dict[str, Any]]:
        """Get system performance statistics"""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
            recent_metrics = [m for m in self.system_metrics if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return None
            
            return {
                "cpu_percent": {
                    "mean": statistics.mean([m.cpu_percent for m in recent_metrics]),
                    "max": max([m.cpu_percent for m in recent_metrics]),
                    "current": recent_metrics[-1].cpu_percent
                },
                "memory_percent": {
                    "mean": statistics.mean([m.memory_percent for m in recent_metrics]),
                    "max": max([m.memory_percent for m in recent_metrics]),
                    "current": recent_metrics[-1].memory_percent
                },
                "memory_used_mb": {
                    "mean": statistics.mean([m.memory_used_mb for m in recent_metrics]),
                    "max": max([m.memory_used_mb for m in recent_metrics]),
                    "current": recent_metrics[-1].memory_used_mb
                }
            }
    
    def get_all_metric_names(self) -> List[str]:
        """Get all metric names"""
        with self._lock:
            return list(self.metrics.keys())
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            return [alert for alert in self.alerts if alert["timestamp"] >= cutoff_time]
    
    def add_alert_callback(self, callback: Callable):
        """Add alert callback"""
        self.alert_callbacks.append(callback)
    
    def set_threshold(self, metric: str, threshold: float):
        """Set performance threshold"""
        self.thresholds[metric] = threshold
    
    def get_thresholds(self) -> Dict[str, float]:
        """Get all thresholds"""
        return self.thresholds.copy()
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        with self._lock:
            if format == "json":
                data = {
                    "metrics": {},
                    "system_metrics": [],
                    "alerts": self.alerts[-100:],  # Last 100 alerts
                    "exported_at": datetime.utcnow().isoformat()
                }
                
                for name, metrics in self.metrics.items():
                    data["metrics"][name] = [
                        {
                            "value": m.value,
                            "timestamp": m.timestamp.isoformat(),
                            "metadata": m.metadata,
                            "tags": m.tags
                        }
                        for m in list(metrics)[-100:]  # Last 100 metrics
                    ]
                
                for metric in list(self.system_metrics)[-100:]:  # Last 100 system metrics
                    data["system_metrics"].append({
                        "cpu_percent": metric.cpu_percent,
                        "memory_percent": metric.memory_percent,
                        "memory_used_mb": metric.memory_used_mb,
                        "disk_io_read_mb": metric.disk_io_read_mb,
                        "disk_io_write_mb": metric.disk_io_write_mb,
                        "network_sent_mb": metric.network_sent_mb,
                        "network_recv_mb": metric.network_recv_mb,
                        "timestamp": metric.timestamp.isoformat()
                    })
                
                return json.dumps(data, indent=2)
            
            return ""

# Global performance monitor instance
performance_monitor = PerformanceMonitor()