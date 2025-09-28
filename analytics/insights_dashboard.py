#!/usr/bin/env python3
"""
Analytics & Insights Dashboard
Part of Issue #9: Analytics & Insights Dashboard

This module provides a comprehensive web-based dashboard for analytics and insights including:
- Real-time metrics visualization
- Interactive charts and graphs
- Performance monitoring
- User analytics
- System health monitoring
- Customizable dashboards
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from pydantic import BaseModel
    import uvicorn
except ImportError as e:
    logger.error(f"Missing dependencies: {e}")
    logger.info("Install with: pip install fastapi uvicorn jinja2")
    raise

from analytics_engine import AnalyticsCollector, AnalyticsInsights, AnalyticsEvent, PerformanceMetrics

# Pydantic models for API
class DashboardConfig(BaseModel):
    name: str
    widgets: List[Dict[str, Any]]
    refresh_interval: int = 30
    auto_refresh: bool = True

class WidgetConfig(BaseModel):
    widget_type: str
    title: str
    data_source: str
    config: Dict[str, Any] = {}

class TimeRange(BaseModel):
    start_time: str
    end_time: str
    granularity: str = "hour"  # minute, hour, day

class DashboardServer:
    """FastAPI server for analytics dashboard"""
    
    def __init__(self, data_dir: Path, port: int = 8081):
        self.data_dir = Path(data_dir)
        self.port = port
        
        # Initialize analytics components
        self.collector = AnalyticsCollector(data_dir)
        self.insights = AnalyticsInsights(self.collector)
        
        # WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Dashboard configurations
        self.dashboard_configs: Dict[str, DashboardConfig] = {}
        self.default_dashboard = self._create_default_dashboard()
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Analytics & Insights Dashboard",
            description="Real-time analytics and insights dashboard for Multimodal LLM Stack",
            version="1.0.0"
        )
        
        # Setup templates
        self.templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
        
        # Define routes
        self._setup_routes()
    
    def _create_default_dashboard(self) -> DashboardConfig:
        """Create default dashboard configuration"""
        return DashboardConfig(
            name="Default Dashboard",
            widgets=[
                {
                    "id": "overview_metrics",
                    "type": "metric_cards",
                    "title": "Overview Metrics",
                    "position": {"x": 0, "y": 0, "w": 12, "h": 2},
                    "config": {
                        "metrics": ["total_requests", "unique_users", "error_rate", "avg_response_time"]
                    }
                },
                {
                    "id": "performance_chart",
                    "type": "line_chart",
                    "title": "System Performance",
                    "position": {"x": 0, "y": 2, "w": 8, "h": 4},
                    "config": {
                        "metrics": ["cpu_percent", "memory_percent", "disk_usage_percent"],
                        "time_range": "24h"
                    }
                },
                {
                    "id": "service_metrics",
                    "type": "bar_chart",
                    "title": "Service Metrics",
                    "position": {"x": 8, "y": 2, "w": 4, "h": 4},
                    "config": {
                        "metric": "requests",
                        "group_by": "service"
                    }
                },
                {
                    "id": "insights_panel",
                    "type": "insights",
                    "title": "Insights & Alerts",
                    "position": {"x": 0, "y": 6, "w": 6, "h": 4},
                    "config": {
                        "max_insights": 10,
                        "severity_filter": ["critical", "warning", "info"]
                    }
                },
                {
                    "id": "recent_events",
                    "type": "event_log",
                    "title": "Recent Events",
                    "position": {"x": 6, "y": 6, "w": 6, "h": 4},
                    "config": {
                        "max_events": 50,
                        "event_types": ["api_request", "error", "performance"]
                    }
                }
            ],
            refresh_interval=30,
            auto_refresh=True
        )
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        # Static files
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        # Dashboard routes
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "dashboard_config": self.default_dashboard
            })
        
        @self.app.get("/api/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/api/dashboard/config")
        async def get_dashboard_config():
            return {"dashboard": self.default_dashboard}
        
        @self.app.post("/api/dashboard/config")
        async def update_dashboard_config(config: DashboardConfig):
            self.default_dashboard = config
            return {"status": "updated", "config": config}
        
        @self.app.get("/api/metrics/overview")
        async def get_overview_metrics():
            try:
                summary = await self.collector.get_analytics_summary(hours=24)
                return {
                    "total_requests": summary.get("total_events", 0),
                    "unique_users": summary.get("unique_users", 0),
                    "error_rate": self._calculate_error_rate(summary),
                    "avg_response_time": self._calculate_avg_response_time(summary),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting overview metrics: {e}")
                return {"error": str(e)}
        
        @self.app.get("/api/metrics/performance")
        async def get_performance_metrics(hours: int = 24):
            try:
                summary = await self.collector.get_analytics_summary(hours=hours)
                performance_data = summary.get("performance_data", [])
                
                # Format data for charts
                chart_data = {
                    "labels": [],
                    "datasets": [
                        {"label": "CPU %", "data": [], "borderColor": "#3b82f6"},
                        {"label": "Memory %", "data": [], "borderColor": "#ef4444"},
                        {"label": "Disk %", "data": [], "borderColor": "#10b981"}
                    ]
                }
                
                for point in performance_data:
                    chart_data["labels"].append(point["timestamp"])
                    chart_data["datasets"][0]["data"].append(point["cpu_percent"])
                    chart_data["datasets"][1]["data"].append(point["memory_percent"])
                    chart_data["datasets"][2]["data"].append(point["disk_usage_percent"])
                
                return chart_data
            except Exception as e:
                logger.error(f"Error getting performance metrics: {e}")
                return {"error": str(e)}
        
        @self.app.get("/api/metrics/services")
        async def get_service_metrics():
            try:
                summary = await self.collector.get_analytics_summary(hours=24)
                service_metrics = summary.get("service_metrics", {})
                
                # Format data for charts
                chart_data = {
                    "labels": list(service_metrics.keys()),
                    "datasets": [
                        {
                            "label": "Requests",
                            "data": [metrics["requests"] for metrics in service_metrics.values()],
                            "backgroundColor": ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6"]
                        }
                    ]
                }
                
                return chart_data
            except Exception as e:
                logger.error(f"Error getting service metrics: {e}")
                return {"error": str(e)}
        
        @self.app.get("/api/insights")
        async def get_insights():
            try:
                insights = await self.insights.generate_insights()
                return {
                    "insights": [
                        {
                            "id": insight.insight_id,
                            "type": insight.insight_type,
                            "title": insight.title,
                            "description": insight.description,
                            "severity": insight.severity,
                            "confidence": insight.confidence,
                            "timestamp": insight.timestamp,
                            "data": insight.data,
                            "recommendations": insight.recommendations
                        }
                        for insight in insights
                    ],
                    "generated_at": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting insights: {e}")
                return {"error": str(e)}
        
        @self.app.get("/api/events/recent")
        async def get_recent_events(limit: int = 50):
            try:
                # This would typically query the database for recent events
                # For now, return mock data
                events = []
                for i in range(min(limit, 10)):
                    events.append({
                        "id": str(uuid.uuid4()),
                        "type": "api_request",
                        "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
                        "service": "litellm",
                        "endpoint": "/v1/chat/completions",
                        "status_code": 200,
                        "response_time_ms": 150.0 + (i * 10)
                    })
                
                return {"events": events}
            except Exception as e:
                logger.error(f"Error getting recent events: {e}")
                return {"error": str(e)}
        
        @self.app.get("/api/analytics/summary")
        async def get_analytics_summary(hours: int = 24):
            try:
                summary = await self.collector.get_analytics_summary(hours=hours)
                return summary
            except Exception as e:
                logger.error(f"Error getting analytics summary: {e}")
                return {"error": str(e)}
        
        # WebSocket endpoint for real-time updates
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive and handle messages
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    elif message.get("type") == "subscribe":
                        # Handle subscription to specific metrics
                        subscription = message.get("subscription", {})
                        await self._handle_subscription(websocket, subscription)
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
    
    async def _handle_subscription(self, websocket: WebSocket, subscription: Dict[str, Any]):
        """Handle WebSocket subscription to metrics"""
        try:
            metric_type = subscription.get("metric_type")
            
            if metric_type == "overview":
                data = await self._get_overview_metrics()
                await websocket.send_text(json.dumps({
                    "type": "overview_metrics",
                    "data": data
                }))
            elif metric_type == "performance":
                data = await self._get_performance_metrics()
                await websocket.send_text(json.dumps({
                    "type": "performance_metrics",
                    "data": data
                }))
            elif metric_type == "insights":
                data = await self._get_insights()
                await websocket.send_text(json.dumps({
                    "type": "insights",
                    "data": data
                }))
                
        except Exception as e:
            logger.error(f"Error handling subscription: {e}")
    
    async def _get_overview_metrics(self) -> Dict[str, Any]:
        """Get overview metrics for real-time updates"""
        try:
            summary = await self.collector.get_analytics_summary(hours=1)
            return {
                "total_requests": summary.get("total_events", 0),
                "unique_users": summary.get("unique_users", 0),
                "error_rate": self._calculate_error_rate(summary),
                "avg_response_time": self._calculate_avg_response_time(summary),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting overview metrics: {e}")
            return {"error": str(e)}
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for real-time updates"""
        try:
            summary = await self.collector.get_analytics_summary(hours=1)
            performance_data = summary.get("performance_data", [])
            
            if performance_data:
                latest = performance_data[-1]
                return {
                    "cpu_percent": latest["cpu_percent"],
                    "memory_percent": latest["memory_percent"],
                    "disk_usage_percent": latest["disk_usage_percent"],
                    "timestamp": latest["timestamp"]
                }
            
            return {"error": "No performance data available"}
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}
    
    async def _get_insights(self) -> Dict[str, Any]:
        """Get insights for real-time updates"""
        try:
            insights = await self.insights.generate_insights()
            return {
                "insights": [
                    {
                        "id": insight.insight_id,
                        "type": insight.insight_type,
                        "title": insight.title,
                        "description": insight.description,
                        "severity": insight.severity,
                        "confidence": insight.confidence,
                        "timestamp": insight.timestamp
                    }
                    for insight in insights
                ],
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting insights: {e}")
            return {"error": str(e)}
    
    def _calculate_error_rate(self, summary: Dict[str, Any]) -> float:
        """Calculate overall error rate from summary"""
        try:
            service_metrics = summary.get("service_metrics", {})
            total_requests = sum(metrics["requests"] for metrics in service_metrics.values())
            total_errors = sum(metrics["errors"] for metrics in service_metrics.values())
            
            if total_requests > 0:
                return total_errors / total_requests
            return 0.0
        except Exception:
            return 0.0
    
    def _calculate_avg_response_time(self, summary: Dict[str, Any]) -> float:
        """Calculate average response time from summary"""
        try:
            service_metrics = summary.get("service_metrics", {})
            response_times = [metrics["avg_response_time_ms"] for metrics in service_metrics.values() if metrics["avg_response_time_ms"] > 0]
            
            if response_times:
                return sum(response_times) / len(response_times)
            return 0.0
        except Exception:
            return 0.0
    
    async def broadcast_update(self, update_type: str, data: Dict[str, Any]):
        """Broadcast update to all connected WebSocket clients"""
        if not self.active_connections:
            return
        
        message = json.dumps({
            "type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
        disconnected = []
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.active_connections.remove(websocket)
    
    async def start_periodic_updates(self):
        """Start periodic updates for real-time dashboard"""
        while True:
            try:
                # Get latest metrics
                overview = await self._get_overview_metrics()
                performance = await self._get_performance_metrics()
                insights = await self._get_insights()
                
                # Broadcast updates
                await self.broadcast_update("overview_metrics", overview)
                await self.broadcast_update("performance_metrics", performance)
                await self.broadcast_update("insights", insights)
                
                # Wait for next update
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in periodic updates: {e}")
                await asyncio.sleep(30)
    
    async def initialize(self):
        """Initialize the dashboard server"""
        try:
            # Start background tasks
            asyncio.create_task(self.collector.start_performance_monitoring())
            asyncio.create_task(self.collector.start_data_flushing())
            asyncio.create_task(self.start_periodic_updates())
            
            logger.info("Analytics dashboard server initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing dashboard server: {e}")
            raise
    
    async def start(self):
        """Start the dashboard server"""
        await self.initialize()
        
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info",
            reload=False
        )
        
        server = uvicorn.Server(config)
        await server.serve()

async def main():
    """Main function to run the analytics dashboard"""
    data_dir = Path(__file__).parent / "data"
    server = DashboardServer(data_dir, port=8081)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Analytics dashboard server stopped by user")
    except Exception as e:
        logger.error(f"Error running analytics dashboard server: {e}")

if __name__ == "__main__":
    asyncio.run(main())