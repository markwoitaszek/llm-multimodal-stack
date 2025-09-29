#!/usr/bin/env python3
"""
Analytics Engine for Multimodal LLM Stack
Part of Issue #9: Analytics & Insights Dashboard

This module provides comprehensive analytics capabilities including:
- Real-time data collection and processing
- Performance metrics tracking
- User behavior analytics
- System health monitoring
- Data aggregation and insights generation
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from collections import defaultdict, Counter
import logging
import aiofiles
from pathlib import Path
import psutil
import sqlite3
import aiosqlite

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnalyticsEvent:
    """Represents a single analytics event"""
    event_id: str
    event_type: str
    timestamp: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    service: str = "all"
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    request_size_bytes: Optional[int] = None
    response_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    service_status: Dict[str, str] = field(default_factory=dict)

@dataclass
class UserSession:
    """User session tracking"""
    session_id: str
    user_id: Optional[str]
    start_time: str
    last_activity: str
    total_requests: int = 0
    total_response_time_ms: float = 0.0
    services_used: List[str] = field(default_factory=list)
    endpoints_accessed: List[str] = field(default_factory=list)
    errors_encountered: int = 0

@dataclass
class ServiceMetrics:
    """Service-specific metrics"""
    service_name: str
    timestamp: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    total_data_transferred_mb: float
    unique_users: int
    error_rate: float

@dataclass
class AnalyticsInsight:
    """Generated analytics insight"""
    insight_id: str
    insight_type: str
    title: str
    description: str
    severity: str  # 'info', 'warning', 'critical'
    confidence: float  # 0.0 to 1.0
    timestamp: str
    data: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

class AnalyticsCollector:
    """Collects and processes analytics data"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # In-memory storage for real-time data
        self.events: List[AnalyticsEvent] = []
        self.sessions: Dict[str, UserSession] = {}
        self.service_metrics: Dict[str, ServiceMetrics] = {}
        
        # Configuration
        self.max_events_in_memory = 10000
        self.batch_size = 1000
        self.flush_interval = 30  # seconds
        
        # Performance tracking
        self.performance_history: List[PerformanceMetrics] = []
        self.max_performance_history = 1440  # 24 hours at 1-minute intervals
        
        # Initialize database
        self.db_path = self.data_dir / "analytics.db"
        asyncio.create_task(self._initialize_database())
    
    async def _initialize_database(self):
        """Initialize SQLite database for analytics storage"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Events table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        event_id TEXT PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        user_id TEXT,
                        session_id TEXT,
                        service TEXT NOT NULL,
                        endpoint TEXT,
                        method TEXT,
                        status_code INTEGER,
                        response_time_ms REAL,
                        request_size_bytes INTEGER,
                        response_size_bytes INTEGER,
                        error_message TEXT,
                        metadata TEXT
                    )
                """)
                
                # Sessions table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        start_time TEXT NOT NULL,
                        last_activity TEXT NOT NULL,
                        total_requests INTEGER DEFAULT 0,
                        total_response_time_ms REAL DEFAULT 0.0,
                        services_used TEXT,
                        endpoints_accessed TEXT,
                        errors_encountered INTEGER DEFAULT 0
                    )
                """)
                
                # Performance metrics table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        cpu_percent REAL NOT NULL,
                        memory_percent REAL NOT NULL,
                        memory_used_mb REAL NOT NULL,
                        memory_available_mb REAL NOT NULL,
                        disk_usage_percent REAL NOT NULL,
                        disk_free_gb REAL NOT NULL,
                        network_sent_mb REAL NOT NULL,
                        network_recv_mb REAL NOT NULL,
                        active_connections INTEGER NOT NULL,
                        service_status TEXT
                    )
                """)
                
                # Service metrics table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS service_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_name TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        total_requests INTEGER NOT NULL,
                        successful_requests INTEGER NOT NULL,
                        failed_requests INTEGER NOT NULL,
                        average_response_time_ms REAL NOT NULL,
                        p95_response_time_ms REAL NOT NULL,
                        p99_response_time_ms REAL NOT NULL,
                        total_data_transferred_mb REAL NOT NULL,
                        unique_users INTEGER NOT NULL,
                        error_rate REAL NOT NULL
                    )
                """)
                
                # Create indexes for better performance
                await db.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_events_service ON events(service)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_service_metrics_timestamp ON service_metrics(timestamp)")
                
                await db.commit()
                logger.info("Analytics database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing analytics database: {e}")
    
    async def record_event(self, event: AnalyticsEvent):
        """Record an analytics event"""
        try:
            # Add to in-memory storage
            self.events.append(event)
            
            # Update session if applicable
            if event.session_id:
                await self._update_session(event)
            
            # Update service metrics
            await self._update_service_metrics(event)
            
            # Flush to database if batch size reached
            if len(self.events) >= self.batch_size:
                await self._flush_events_to_db()
            
            logger.debug(f"Recorded event: {event.event_type} for service {event.service}")
            
        except Exception as e:
            logger.error(f"Error recording event: {e}")
    
    async def _update_session(self, event: AnalyticsEvent):
        """Update user session with event data"""
        session_id = event.session_id
        
        if session_id not in self.sessions:
            self.sessions[session_id] = UserSession(
                session_id=session_id,
                user_id=event.user_id,
                start_time=event.timestamp,
                last_activity=event.timestamp
            )
        
        session = self.sessions[session_id]
        session.last_activity = event.timestamp
        session.total_requests += 1
        
        if event.response_time_ms:
            session.total_response_time_ms += event.response_time_ms
        
        if event.service not in session.services_used:
            session.services_used.append(event.service)
        
        if event.endpoint and event.endpoint not in session.endpoints_accessed:
            session.endpoints_accessed.append(event.endpoint)
        
        if event.status_code and event.status_code >= 400:
            session.errors_encountered += 1
    
    async def _update_service_metrics(self, event: AnalyticsEvent):
        """Update service-specific metrics"""
        service = event.service
        
        if service not in self.service_metrics:
            self.service_metrics[service] = ServiceMetrics(
                service_name=service,
                timestamp=event.timestamp,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                average_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                total_data_transferred_mb=0.0,
                unique_users=0,
                error_rate=0.0
            )
        
        metrics = self.service_metrics[service]
        metrics.timestamp = event.timestamp
        metrics.total_requests += 1
        
        if event.status_code:
            if 200 <= event.status_code < 400:
                metrics.successful_requests += 1
            else:
                metrics.failed_requests += 1
        
        if event.response_time_ms:
            # Update average response time
            total_time = metrics.average_response_time_ms * (metrics.total_requests - 1) + event.response_time_ms
            metrics.average_response_time_ms = total_time / metrics.total_requests
        
        if event.request_size_bytes and event.response_size_bytes:
            data_mb = (event.request_size_bytes + event.response_size_bytes) / (1024 * 1024)
            metrics.total_data_transferred_mb += data_mb
        
        # Calculate error rate
        if metrics.total_requests > 0:
            metrics.error_rate = metrics.failed_requests / metrics.total_requests
    
    async def _flush_events_to_db(self):
        """Flush events to database"""
        if not self.events:
            return
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Insert events
                for event in self.events:
                    await db.execute("""
                        INSERT OR REPLACE INTO events 
                        (event_id, event_type, timestamp, user_id, session_id, service, 
                         endpoint, method, status_code, response_time_ms, request_size_bytes, 
                         response_size_bytes, error_message, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event.event_id, event.event_type, event.timestamp, event.user_id,
                        event.session_id, event.service, event.endpoint, event.method,
                        event.status_code, event.response_time_ms, event.request_size_bytes,
                        event.response_size_bytes, event.error_message, json.dumps(event.metadata)
                    ))
                
                # Insert/update sessions
                for session in self.sessions.values():
                    await db.execute("""
                        INSERT OR REPLACE INTO sessions 
                        (session_id, user_id, start_time, last_activity, total_requests,
                         total_response_time_ms, services_used, endpoints_accessed, errors_encountered)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session.session_id, session.user_id, session.start_time,
                        session.last_activity, session.total_requests, session.total_response_time_ms,
                        json.dumps(session.services_used), json.dumps(session.endpoints_accessed),
                        session.errors_encountered
                    ))
                
                # Insert service metrics
                for metrics in self.service_metrics.values():
                    await db.execute("""
                        INSERT INTO service_metrics 
                        (service_name, timestamp, total_requests, successful_requests, failed_requests,
                         average_response_time_ms, p95_response_time_ms, p99_response_time_ms,
                         total_data_transferred_mb, unique_users, error_rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        metrics.service_name, metrics.timestamp, metrics.total_requests,
                        metrics.successful_requests, metrics.failed_requests, metrics.average_response_time_ms,
                        metrics.p95_response_time_ms, metrics.p99_response_time_ms,
                        metrics.total_data_transferred_mb, metrics.unique_users, metrics.error_rate
                    ))
                
                await db.commit()
                
                # Clear in-memory data
                self.events.clear()
                self.sessions.clear()
                self.service_metrics.clear()
                
                logger.info(f"Flushed analytics data to database")
                
        except Exception as e:
            logger.error(f"Error flushing events to database: {e}")
    
    async def collect_performance_metrics(self):
        """Collect system performance metrics"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Get active connections (simplified)
            connections = len(psutil.net_connections())
            
            # Create performance metrics
            metrics = PerformanceMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=disk.percent,
                disk_free_gb=disk.free / (1024 * 1024 * 1024),
                network_sent_mb=network.bytes_sent / (1024 * 1024),
                network_recv_mb=network.bytes_recv / (1024 * 1024),
                active_connections=connections,
                service_status={}  # Will be populated by service health checks
            )
            
            # Add to history
            self.performance_history.append(metrics)
            
            # Keep only recent history
            if len(self.performance_history) > self.max_performance_history:
                self.performance_history = self.performance_history[-self.max_performance_history:]
            
            # Store in database
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO performance_metrics 
                    (timestamp, cpu_percent, memory_percent, memory_used_mb, memory_available_mb,
                     disk_usage_percent, disk_free_gb, network_sent_mb, network_recv_mb,
                     active_connections, service_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.timestamp, metrics.cpu_percent, metrics.memory_percent,
                    metrics.memory_used_mb, metrics.memory_available_mb, metrics.disk_usage_percent,
                    metrics.disk_free_gb, metrics.network_sent_mb, metrics.network_recv_mb,
                    metrics.active_connections, json.dumps(metrics.service_status)
                ))
                await db.commit()
            
            logger.debug(f"Collected performance metrics: CPU {cpu_percent}%, Memory {memory.percent}%")
            
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
    
    async def get_analytics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get analytics summary for the specified time period"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            async with aiosqlite.connect(self.db_path) as db:
                # Get event counts by type
                event_counts = {}
                async for row in db.execute("""
                    SELECT event_type, COUNT(*) as count 
                    FROM events 
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY event_type
                """, (start_time.isoformat(), end_time.isoformat())):
                    event_counts[row[0]] = row[1]
                
                # Get service metrics
                service_metrics = {}
                async for row in db.execute("""
                    SELECT service, COUNT(*) as requests, 
                           AVG(response_time_ms) as avg_response_time,
                           COUNT(CASE WHEN status_code >= 400 THEN 1 END) as errors
                    FROM events 
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY service
                """, (start_time.isoformat(), end_time.isoformat())):
                    service_metrics[row[0]] = {
                        "requests": row[1],
                        "avg_response_time_ms": row[2] or 0,
                        "errors": row[3]
                    }
                
                # Get unique users
                unique_users = 0
                async for row in db.execute("""
                    SELECT COUNT(DISTINCT user_id) 
                    FROM events 
                    WHERE timestamp >= ? AND timestamp <= ? AND user_id IS NOT NULL
                """, (start_time.isoformat(), end_time.isoformat())):
                    unique_users = row[0]
                
                # Get performance metrics
                performance_data = []
                async for row in db.execute("""
                    SELECT timestamp, cpu_percent, memory_percent, disk_usage_percent
                    FROM performance_metrics 
                    WHERE timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp
                """, (start_time.isoformat(), end_time.isoformat())):
                    performance_data.append({
                        "timestamp": row[0],
                        "cpu_percent": row[1],
                        "memory_percent": row[2],
                        "disk_usage_percent": row[3]
                    })
                
                return {
                    "time_period_hours": hours,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "event_counts": event_counts,
                    "service_metrics": service_metrics,
                    "unique_users": unique_users,
                    "performance_data": performance_data,
                    "total_events": sum(event_counts.values()),
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return {"error": str(e)}
    
    async def start_performance_monitoring(self):
        """Start continuous performance monitoring"""
        while True:
            try:
                await self.collect_performance_metrics()
                await asyncio.sleep(60)  # Collect every minute
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(60)
    
    async def start_data_flushing(self):
        """Start periodic data flushing to database"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_events_to_db()
            except Exception as e:
                logger.error(f"Error in data flushing: {e}")

class AnalyticsInsights:
    """Generates insights from analytics data"""
    
    def __init__(self, collector: AnalyticsCollector):
        self.collector = collector
    
    async def generate_insights(self) -> List[AnalyticsInsight]:
        """Generate insights from analytics data"""
        insights = []
        
        try:
            # Get recent analytics data
            summary = await self.collector.get_analytics_summary(hours=1)
            
            if "error" in summary:
                return insights
            
            # Performance insights
            performance_insights = await self._analyze_performance(summary)
            insights.extend(performance_insights)
            
            # Service health insights
            service_insights = await self._analyze_service_health(summary)
            insights.extend(service_insights)
            
            # Usage pattern insights
            usage_insights = await self._analyze_usage_patterns(summary)
            insights.extend(usage_insights)
            
            # Error analysis insights
            error_insights = await self._analyze_errors(summary)
            insights.extend(error_insights)
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
        
        return insights
    
    async def _analyze_performance(self, summary: Dict[str, Any]) -> List[AnalyticsInsight]:
        """Analyze performance metrics for insights"""
        insights = []
        
        try:
            performance_data = summary.get("performance_data", [])
            if not performance_data:
                return insights
            
            # Get latest performance metrics
            latest = performance_data[-1]
            
            # High CPU usage
            if latest["cpu_percent"] > 80:
                insights.append(AnalyticsInsight(
                    insight_id=str(uuid.uuid4()),
                    insight_type="performance",
                    title="High CPU Usage Detected",
                    description=f"CPU usage is at {latest['cpu_percent']:.1f}%, which may impact system performance.",
                    severity="warning" if latest["cpu_percent"] < 90 else "critical",
                    confidence=0.9,
                    timestamp=datetime.now().isoformat(),
                    data={"cpu_percent": latest["cpu_percent"]},
                    recommendations=[
                        "Monitor system load and consider scaling",
                        "Check for resource-intensive processes",
                        "Review recent deployments for performance impact"
                    ]
                ))
            
            # High memory usage
            if latest["memory_percent"] > 85:
                insights.append(AnalyticsInsight(
                    insight_id=str(uuid.uuid4()),
                    insight_type="performance",
                    title="High Memory Usage Detected",
                    description=f"Memory usage is at {latest['memory_percent']:.1f}%, which may cause performance issues.",
                    severity="warning" if latest["memory_percent"] < 95 else "critical",
                    confidence=0.9,
                    timestamp=datetime.now().isoformat(),
                    data={"memory_percent": latest["memory_percent"]},
                    recommendations=[
                        "Monitor memory usage trends",
                        "Consider memory optimization",
                        "Check for memory leaks in applications"
                    ]
                ))
            
            # High disk usage
            if latest["disk_usage_percent"] > 90:
                insights.append(AnalyticsInsight(
                    insight_id=str(uuid.uuid4()),
                    insight_type="performance",
                    title="High Disk Usage Detected",
                    description=f"Disk usage is at {latest['disk_usage_percent']:.1f}%, which may cause storage issues.",
                    severity="critical",
                    confidence=0.95,
                    timestamp=datetime.now().isoformat(),
                    data={"disk_usage_percent": latest["disk_usage_percent"]},
                    recommendations=[
                        "Clean up unnecessary files",
                        "Archive old data",
                        "Consider expanding storage capacity"
                    ]
                ))
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
        
        return insights
    
    async def _analyze_service_health(self, summary: Dict[str, Any]) -> List[AnalyticsInsight]:
        """Analyze service health for insights"""
        insights = []
        
        try:
            service_metrics = summary.get("service_metrics", {})
            
            for service, metrics in service_metrics.items():
                # High error rate
                if metrics["requests"] > 0:
                    error_rate = metrics["errors"] / metrics["requests"]
                    if error_rate > 0.05:  # 5% error rate
                        insights.append(AnalyticsInsight(
                            insight_id=str(uuid.uuid4()),
                            insight_type="service_health",
                            title=f"High Error Rate in {service}",
                            description=f"Service {service} has an error rate of {error_rate:.1%} ({metrics['errors']} errors out of {metrics['requests']} requests).",
                            severity="warning" if error_rate < 0.1 else "critical",
                            confidence=0.8,
                            timestamp=datetime.now().isoformat(),
                            data={"service": service, "error_rate": error_rate, "errors": metrics["errors"], "requests": metrics["requests"]},
                            recommendations=[
                                f"Investigate error patterns in {service}",
                                "Check service logs for error details",
                                "Review recent changes to the service"
                            ]
                        ))
                
                # Slow response times
                if metrics["avg_response_time_ms"] > 1000:  # 1 second
                    insights.append(AnalyticsInsight(
                        insight_id=str(uuid.uuid4()),
                        insight_type="performance",
                        title=f"Slow Response Times in {service}",
                        description=f"Service {service} has an average response time of {metrics['avg_response_time_ms']:.0f}ms, which may impact user experience.",
                        severity="warning" if metrics["avg_response_time_ms"] < 2000 else "critical",
                        confidence=0.7,
                        timestamp=datetime.now().isoformat(),
                        data={"service": service, "avg_response_time_ms": metrics["avg_response_time_ms"]},
                        recommendations=[
                            f"Optimize {service} performance",
                            "Check database query performance",
                            "Review service dependencies"
                        ]
                    ))
            
        except Exception as e:
            logger.error(f"Error analyzing service health: {e}")
        
        return insights
    
    async def _analyze_usage_patterns(self, summary: Dict[str, Any]) -> List[AnalyticsInsight]:
        """Analyze usage patterns for insights"""
        insights = []
        
        try:
            total_events = summary.get("total_events", 0)
            unique_users = summary.get("unique_users", 0)
            
            # High usage
            if total_events > 1000:  # More than 1000 events in the last hour
                insights.append(AnalyticsInsight(
                    insight_id=str(uuid.uuid4()),
                    insight_type="usage",
                    title="High System Usage",
                    description=f"System has processed {total_events} events in the last hour, indicating high usage.",
                    severity="info",
                    confidence=0.8,
                    timestamp=datetime.now().isoformat(),
                    data={"total_events": total_events, "unique_users": unique_users},
                    recommendations=[
                        "Monitor system performance during peak usage",
                        "Consider scaling resources if needed",
                        "Review usage patterns for optimization opportunities"
                    ]
                ))
            
            # Low usage
            elif total_events < 10:  # Less than 10 events in the last hour
                insights.append(AnalyticsInsight(
                    insight_id=str(uuid.uuid4()),
                    insight_type="usage",
                    title="Low System Usage",
                    description=f"System has processed only {total_events} events in the last hour, indicating low usage.",
                    severity="info",
                    confidence=0.7,
                    timestamp=datetime.now().isoformat(),
                    data={"total_events": total_events, "unique_users": unique_users},
                    recommendations=[
                        "Check if this is expected during this time period",
                        "Verify system health and connectivity",
                        "Consider if there are any issues preventing usage"
                    ]
                ))
            
        except Exception as e:
            logger.error(f"Error analyzing usage patterns: {e}")
        
        return insights
    
    async def _analyze_errors(self, summary: Dict[str, Any]) -> List[AnalyticsInsight]:
        """Analyze error patterns for insights"""
        insights = []
        
        try:
            event_counts = summary.get("event_counts", {})
            error_events = sum(count for event_type, count in event_counts.items() if "error" in event_type.lower())
            total_events = sum(event_counts.values())
            
            if total_events > 0:
                error_rate = error_events / total_events
                
                if error_rate > 0.1:  # 10% error rate
                    insights.append(AnalyticsInsight(
                        insight_id=str(uuid.uuid4()),
                        insight_type="error_analysis",
                        title="High Error Rate Detected",
                        description=f"System has an error rate of {error_rate:.1%} ({error_events} errors out of {total_events} total events).",
                        severity="critical",
                        confidence=0.9,
                        timestamp=datetime.now().isoformat(),
                        data={"error_rate": error_rate, "error_events": error_events, "total_events": total_events},
                        recommendations=[
                            "Investigate error patterns and root causes",
                            "Check system logs for error details",
                            "Review recent changes that might have introduced errors",
                            "Consider rolling back recent deployments if necessary"
                        ]
                    ))
            
        except Exception as e:
            logger.error(f"Error analyzing errors: {e}")
        
        return insights

# Import required modules
try:
    import aiofiles
except ImportError:
    logger.warning("aiofiles not available. Install with: pip install aiofiles")
    # Fallback to synchronous file operations
    import aiofiles
    aiofiles.open = open

try:
    import aiosqlite
except ImportError:
    logger.warning("aiosqlite not available. Install with: pip install aiosqlite")
    # Fallback to synchronous sqlite
    import aiosqlite
    aiosqlite.connect = sqlite3.connect

async def main():
    """Main function to demonstrate analytics engine"""
    data_dir = Path(__file__).parent / "data"
    collector = AnalyticsCollector(data_dir)
    insights = AnalyticsInsights(collector)
    
    # Start background tasks
    asyncio.create_task(collector.start_performance_monitoring())
    asyncio.create_task(collector.start_data_flushing())
    
    # Simulate some events
    for i in range(10):
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type="api_request",
            timestamp=datetime.now().isoformat(),
            user_id=f"user_{i % 3}",
            session_id=f"session_{i % 2}",
            service="litellm",
            endpoint="/v1/chat/completions",
            method="POST",
            status_code=200,
            response_time_ms=150.0 + (i * 10),
            request_size_bytes=1024,
            response_size_bytes=2048
        )
        await collector.record_event(event)
    
    # Wait a bit for data to be processed
    await asyncio.sleep(2)
    
    # Get analytics summary
    summary = await collector.get_analytics_summary(hours=1)
    print("Analytics Summary:")
    print(json.dumps(summary, indent=2))
    
    # Generate insights
    insights_list = await insights.generate_insights()
    print(f"\nGenerated {len(insights_list)} insights:")
    for insight in insights_list:
        print(f"- {insight.title}: {insight.description}")

if __name__ == "__main__":
    asyncio.run(main())