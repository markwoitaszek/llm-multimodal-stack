#!/usr/bin/env python3
"""
Comprehensive Test Suite for Phase 3 Analytics & Insights Dashboard
Part of Issue #9: Analytics & Insights Dashboard

This test suite validates:
- Analytics data collection and processing
- Performance metrics tracking
- Insights generation
- Dashboard functionality
- Real-time updates and WebSocket communication
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta
import uuid

# Import the modules to test
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "analytics"))

from analytics_engine import AnalyticsCollector, AnalyticsEvent, PerformanceMetrics, UserSession, ServiceMetrics, AnalyticsInsights
from insights_dashboard import DashboardServer, DashboardConfig, WidgetConfig

class TestAnalyticsEvent:
    """Test analytics event functionality"""
    
    def test_analytics_event_creation(self):
        """Test creating analytics events"""
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type="api_request",
            timestamp=datetime.now().isoformat(),
            user_id="user123",
            session_id="session456",
            service="litellm",
            endpoint="/v1/chat/completions",
            method="POST",
            status_code=200,
            response_time_ms=150.0,
            request_size_bytes=1024,
            response_size_bytes=2048
        )
        
        assert event.event_type == "api_request"
        assert event.user_id == "user123"
        assert event.service == "litellm"
        assert event.status_code == 200
        assert event.response_time_ms == 150.0
    
    def test_analytics_event_serialization(self):
        """Test analytics event serialization"""
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type="test_event",
            timestamp=datetime.now().isoformat(),
            service="test_service"
        )
        
        # Test conversion to dict
        event_dict = asdict(event)
        assert event_dict["event_type"] == "test_event"
        assert event_dict["service"] == "test_service"
        
        # Test JSON serialization
        event_json = json.dumps(event_dict)
        parsed_event = json.loads(event_json)
        assert parsed_event["event_type"] == "test_event"

class TestPerformanceMetrics:
    """Test performance metrics functionality"""
    
    def test_performance_metrics_creation(self):
        """Test creating performance metrics"""
        metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=45.5,
            memory_percent=67.8,
            memory_used_mb=1024.0,
            memory_available_mb=2048.0,
            disk_usage_percent=23.4,
            disk_free_gb=500.0,
            network_sent_mb=10.5,
            network_recv_mb=15.2,
            active_connections=25
        )
        
        assert metrics.cpu_percent == 45.5
        assert metrics.memory_percent == 67.8
        assert metrics.memory_used_mb == 1024.0
        assert metrics.active_connections == 25
    
    def test_performance_metrics_serialization(self):
        """Test performance metrics serialization"""
        metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_used_mb=1000.0,
            memory_available_mb=2000.0,
            disk_usage_percent=30.0,
            disk_free_gb=400.0,
            network_sent_mb=5.0,
            network_recv_mb=10.0,
            active_connections=20
        )
        
        metrics_dict = asdict(metrics)
        assert metrics_dict["cpu_percent"] == 50.0
        assert metrics_dict["memory_percent"] == 60.0

class TestAnalyticsCollector:
    """Test analytics collector functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        self.collector = AnalyticsCollector(self.data_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    async def test_analytics_collector_initialization(self):
        """Test analytics collector initialization"""
        assert self.collector.data_dir == self.data_dir
        assert self.collector.max_events_in_memory == 10000
        assert self.collector.batch_size == 1000
        assert len(self.collector.events) == 0
        assert len(self.collector.sessions) == 0
    
    async def test_record_event(self):
        """Test recording analytics events"""
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type="test_event",
            timestamp=datetime.now().isoformat(),
            service="test_service",
            user_id="user123",
            session_id="session456"
        )
        
        await self.collector.record_event(event)
        
        assert len(self.collector.events) == 1
        assert self.collector.events[0].event_id == event.event_id
        assert "session456" in self.collector.sessions
    
    async def test_session_tracking(self):
        """Test user session tracking"""
        # Create multiple events for the same session
        session_id = "test_session"
        user_id = "test_user"
        
        for i in range(5):
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                event_type="api_request",
                timestamp=datetime.now().isoformat(),
                user_id=user_id,
                session_id=session_id,
                service="litellm",
                response_time_ms=100.0 + i * 10
            )
            await self.collector.record_event(event)
        
        # Check session data
        assert session_id in self.collector.sessions
        session = self.collector.sessions[session_id]
        assert session.user_id == user_id
        assert session.total_requests == 5
        assert session.total_response_time_ms == 550.0  # 100+110+120+130+140
        assert "litellm" in session.services_used
    
    async def test_service_metrics_tracking(self):
        """Test service metrics tracking"""
        service = "test_service"
        
        # Create events for the service
        for i in range(10):
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                event_type="api_request",
                timestamp=datetime.now().isoformat(),
                service=service,
                status_code=200 if i < 8 else 500,  # 80% success rate
                response_time_ms=100.0 + i * 5,
                request_size_bytes=1024,
                response_size_bytes=2048
            )
            await self.collector.record_event(event)
        
        # Check service metrics
        assert service in self.collector.service_metrics
        metrics = self.collector.service_metrics[service]
        assert metrics.total_requests == 10
        assert metrics.successful_requests == 8
        assert metrics.failed_requests == 2
        assert metrics.error_rate == 0.2  # 20% error rate
        assert metrics.average_response_time_ms > 100.0
    
    async def test_analytics_summary(self):
        """Test analytics summary generation"""
        # Create test events
        for i in range(20):
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                event_type="api_request",
                timestamp=datetime.now().isoformat(),
                user_id=f"user_{i % 5}",  # 5 unique users
                service="litellm",
                status_code=200 if i < 18 else 500,  # 90% success rate
                response_time_ms=150.0
            )
            await self.collector.record_event(event)
        
        # Get summary
        summary = await self.collector.get_analytics_summary(hours=1)
        
        assert summary["total_events"] == 20
        assert summary["unique_users"] == 5
        assert "litellm" in summary["service_metrics"]
        assert summary["service_metrics"]["litellm"]["requests"] == 20
        assert summary["service_metrics"]["litellm"]["errors"] == 2

class TestAnalyticsInsights:
    """Test analytics insights generation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        self.collector = AnalyticsCollector(self.data_dir)
        self.insights = AnalyticsInsights(self.collector)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    async def test_insights_generation(self):
        """Test insights generation"""
        # Create test events with high error rate
        for i in range(20):
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                event_type="api_request",
                timestamp=datetime.now().isoformat(),
                service="test_service",
                status_code=500 if i < 10 else 200,  # 50% error rate
                response_time_ms=2000.0  # Slow response time
            )
            await self.collector.record_event(event)
        
        # Generate insights
        insights = await self.insights.generate_insights()
        
        assert len(insights) > 0
        
        # Check for high error rate insight
        error_insights = [i for i in insights if "error rate" in i.title.lower()]
        assert len(error_insights) > 0
        
        # Check for slow response time insight
        performance_insights = [i for i in insights if "response time" in i.title.lower()]
        assert len(performance_insights) > 0
    
    async def test_performance_insights(self):
        """Test performance-based insights"""
        # Simulate high CPU usage
        metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=85.0,  # High CPU
            memory_percent=90.0,  # High memory
            memory_used_mb=8000.0,
            memory_available_mb=1000.0,
            disk_usage_percent=95.0,  # High disk usage
            disk_free_gb=50.0,
            network_sent_mb=100.0,
            network_recv_mb=150.0,
            active_connections=100
        )
        
        # Add to collector's performance history
        self.collector.performance_history.append(metrics)
        
        # Generate insights
        insights = await self.insights.generate_insights()
        
        # Check for performance insights
        cpu_insights = [i for i in insights if "cpu" in i.title.lower()]
        memory_insights = [i for i in insights if "memory" in i.title.lower()]
        disk_insights = [i for i in insights if "disk" in i.title.lower()]
        
        assert len(cpu_insights) > 0
        assert len(memory_insights) > 0
        assert len(disk_insights) > 0
        
        # Check insight severity
        critical_insights = [i for i in insights if i.severity == "critical"]
        assert len(critical_insights) > 0
    
    async def test_usage_pattern_insights(self):
        """Test usage pattern insights"""
        # Create high usage scenario
        for i in range(1000):  # High number of events
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                event_type="api_request",
                timestamp=datetime.now().isoformat(),
                service="litellm"
            )
            await self.collector.record_event(event)
        
        # Generate insights
        insights = await self.insights.generate_insights()
        
        # Check for high usage insight
        usage_insights = [i for i in insights if "high usage" in i.title.lower()]
        assert len(usage_insights) > 0
        
        # Check insight type
        usage_insight = usage_insights[0]
        assert usage_insight.insight_type == "usage"
        assert usage_insight.severity == "info"

class TestDashboardServer:
    """Test dashboard server functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        self.server = DashboardServer(self.data_dir, port=8082)  # Use different port for testing
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_dashboard_server_initialization(self):
        """Test dashboard server initialization"""
        assert self.server.data_dir == self.data_dir
        assert self.server.port == 8082
        assert self.server.collector is not None
        assert self.server.insights is not None
        assert len(self.server.active_connections) == 0
    
    def test_default_dashboard_config(self):
        """Test default dashboard configuration"""
        config = self.server.default_dashboard
        
        assert config.name == "Default Dashboard"
        assert config.refresh_interval == 30
        assert config.auto_refresh == True
        assert len(config.widgets) == 5
        
        # Check widget types
        widget_types = [widget["type"] for widget in config.widgets]
        assert "metric_cards" in widget_types
        assert "line_chart" in widget_types
        assert "bar_chart" in widget_types
        assert "insights" in widget_types
        assert "event_log" in widget_types
    
    async def test_dashboard_initialization(self):
        """Test dashboard server initialization"""
        await self.server.initialize()
        
        # Check that background tasks are started
        assert self.server.collector is not None
        assert self.server.insights is not None
    
    def test_api_models(self):
        """Test API model validation"""
        from insights_dashboard import DashboardConfig, WidgetConfig, TimeRange
        
        # Test DashboardConfig
        config = DashboardConfig(
            name="Test Dashboard",
            widgets=[
                {
                    "id": "test_widget",
                    "type": "metric_cards",
                    "title": "Test Widget"
                }
            ],
            refresh_interval=60,
            auto_refresh=False
        )
        
        assert config.name == "Test Dashboard"
        assert config.refresh_interval == 60
        assert config.auto_refresh == False
        
        # Test WidgetConfig
        widget = WidgetConfig(
            widget_type="line_chart",
            title="Test Chart",
            data_source="performance",
            config={"metric": "cpu_percent"}
        )
        
        assert widget.widget_type == "line_chart"
        assert widget.title == "Test Chart"
        assert widget.data_source == "performance"
        assert widget.config["metric"] == "cpu_percent"
        
        # Test TimeRange
        time_range = TimeRange(
            start_time="2024-01-01T00:00:00",
            end_time="2024-01-02T00:00:00",
            granularity="hour"
        )
        
        assert time_range.start_time == "2024-01-01T00:00:00"
        assert time_range.granularity == "hour"

class TestAnalyticsIntegration:
    """Test integration between analytics components"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    async def test_full_analytics_workflow(self):
        """Test complete analytics workflow"""
        # Initialize components
        collector = AnalyticsCollector(self.data_dir)
        insights = AnalyticsInsights(collector)
        server = DashboardServer(self.data_dir, port=8083)
        
        # Create test events
        events = []
        for i in range(50):
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                event_type="api_request",
                timestamp=datetime.now().isoformat(),
                user_id=f"user_{i % 10}",  # 10 unique users
                session_id=f"session_{i % 5}",  # 5 sessions
                service="litellm" if i % 2 == 0 else "multimodal-worker",
                endpoint="/v1/chat/completions" if i % 2 == 0 else "/process",
                method="POST",
                status_code=200 if i < 45 else 500,  # 90% success rate
                response_time_ms=100.0 + (i * 2),
                request_size_bytes=1024,
                response_size_bytes=2048
            )
            events.append(event)
            await collector.record_event(event)
        
        # Test analytics summary
        summary = await collector.get_analytics_summary(hours=1)
        assert summary["total_events"] == 50
        assert summary["unique_users"] == 10
        
        # Test insights generation
        insights_list = await insights.generate_insights()
        assert len(insights_list) > 0
        
        # Test dashboard initialization
        await server.initialize()
        assert server.collector is not None
        assert server.insights is not None
        
        # Test WebSocket connections
        assert len(server.active_connections) == 0
    
    async def test_performance_monitoring(self):
        """Test performance monitoring functionality"""
        collector = AnalyticsCollector(self.data_dir)
        
        # Start performance monitoring (simulate)
        await collector.collect_performance_metrics()
        
        # Check that performance data was collected
        assert len(collector.performance_history) > 0
        
        # Check performance metrics structure
        metrics = collector.performance_history[0]
        assert hasattr(metrics, 'cpu_percent')
        assert hasattr(metrics, 'memory_percent')
        assert hasattr(metrics, 'disk_usage_percent')
        assert hasattr(metrics, 'active_connections')
    
    async def test_data_persistence(self):
        """Test data persistence to database"""
        collector = AnalyticsCollector(self.data_dir)
        
        # Create test events
        for i in range(10):
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                event_type="test_event",
                timestamp=datetime.now().isoformat(),
                service="test_service"
            )
            await collector.record_event(event)
        
        # Flush to database
        await collector._flush_events_to_db()
        
        # Check that events were flushed
        assert len(collector.events) == 0
        
        # Check database file exists
        db_path = collector.db_path
        assert db_path.exists()

# Performance Tests
class TestAnalyticsPerformance:
    """Test performance of analytics system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    async def test_high_volume_event_processing(self):
        """Test processing high volume of events"""
        collector = AnalyticsCollector(self.data_dir)
        
        # Create many events
        num_events = 1000
        start_time = datetime.now()
        
        for i in range(num_events):
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                event_type="api_request",
                timestamp=datetime.now().isoformat(),
                service="test_service",
                response_time_ms=100.0
            )
            await collector.record_event(event)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Should process events quickly
        assert processing_time < 5.0  # Less than 5 seconds for 1000 events
        assert len(collector.events) == num_events
    
    async def test_insights_generation_performance(self):
        """Test insights generation performance"""
        collector = AnalyticsCollector(self.data_dir)
        insights = AnalyticsInsights(collector)
        
        # Create test data
        for i in range(100):
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                event_type="api_request",
                timestamp=datetime.now().isoformat(),
                service="test_service",
                status_code=200 if i < 90 else 500
            )
            await collector.record_event(event)
        
        # Test insights generation performance
        start_time = datetime.now()
        insights_list = await insights.generate_insights()
        generation_time = (datetime.now() - start_time).total_seconds()
        
        # Should generate insights quickly
        assert generation_time < 2.0  # Less than 2 seconds
        assert len(insights_list) > 0
    
    async def test_dashboard_initialization_performance(self):
        """Test dashboard initialization performance"""
        start_time = datetime.now()
        
        server = DashboardServer(self.data_dir, port=8084)
        await server.initialize()
        
        initialization_time = (datetime.now() - start_time).total_seconds()
        
        # Should initialize quickly
        assert initialization_time < 3.0  # Less than 3 seconds
        assert server.collector is not None
        assert server.insights is not None

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])