"""
n8n Workflow Monitoring Service - Main application entry point
Provides real-time monitoring, analytics, and alerting for n8n workflows
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.workflow_monitor import WorkflowMonitor
from app.agent_analytics import AgentAnalytics
from app.performance_metrics import PerformanceMetrics
from app.alert_manager import AlertManager
from app.websocket_manager import WebSocketManager
from app.dashboard_api import DashboardAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
workflow_monitor: WorkflowMonitor = None
agent_analytics: AgentAnalytics = None
performance_metrics: PerformanceMetrics = None
alert_manager: AlertManager = None
websocket_manager: WebSocketManager = None
dashboard_api: DashboardAPI = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global workflow_monitor, agent_analytics, performance_metrics, alert_manager, websocket_manager, dashboard_api
    
    logger.info("Starting n8n Monitoring Service...")
    
    try:
        # Initialize components
        websocket_manager = WebSocketManager()
        alert_manager = AlertManager()
        performance_metrics = PerformanceMetrics()
        agent_analytics = AgentAnalytics()
        workflow_monitor = WorkflowMonitor(agent_analytics, performance_metrics, alert_manager)
        dashboard_api = DashboardAPI(workflow_monitor, agent_analytics, performance_metrics)
        
        # Start background tasks
        await workflow_monitor.initialize()
        await agent_analytics.initialize()
        await performance_metrics.initialize()
        await alert_manager.initialize()
        
        # Start monitoring tasks
        asyncio.create_task(workflow_monitor.start_monitoring())
        asyncio.create_task(agent_analytics.start_analytics_collection())
        asyncio.create_task(performance_metrics.start_metrics_collection())
        
        logger.info("n8n Monitoring Service started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start n8n Monitoring Service: {e}")
        raise
    finally:
        logger.info("Shutting down n8n Monitoring Service...")
        if workflow_monitor:
            await workflow_monitor.stop_monitoring()
        if websocket_manager:
            await websocket_manager.disconnect_all()

# Create FastAPI application
app = FastAPI(
    title="n8n Workflow Monitoring Service",
    description="Real-time monitoring, analytics, and alerting for n8n workflows",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "n8n-monitoring",
        "version": "1.0.0",
        "components": {
            "workflow_monitor": workflow_monitor is not None,
            "agent_analytics": agent_analytics is not None,
            "performance_metrics": performance_metrics is not None,
            "alert_manager": alert_manager is not None,
            "websocket_manager": websocket_manager is not None,
            "dashboard_api": dashboard_api is not None
        }
    }

# Workflow monitoring endpoints
@app.get("/api/v1/workflows")
async def list_workflows():
    """List all monitored workflows"""
    if not workflow_monitor:
        return JSONResponse(
            status_code=503,
            content={"error": "Workflow monitor not initialized"}
        )
    
    try:
        workflows = await workflow_monitor.list_workflows()
        return {"workflows": workflows}
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/v1/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get workflow status"""
    if not workflow_monitor:
        return JSONResponse(
            status_code=503,
            content={"error": "Workflow monitor not initialized"}
        )
    
    try:
        status = await workflow_monitor.get_workflow_status(workflow_id)
        return {"workflow_id": workflow_id, "status": status}
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/v1/workflows/{workflow_id}/executions")
async def get_workflow_executions(workflow_id: str, limit: int = 50, offset: int = 0):
    """Get workflow execution history"""
    if not workflow_monitor:
        return JSONResponse(
            status_code=503,
            content={"error": "Workflow monitor not initialized"}
        )
    
    try:
        executions = await workflow_monitor.get_workflow_executions(workflow_id, limit, offset)
        return {"workflow_id": workflow_id, "executions": executions}
    except Exception as e:
        logger.error(f"Failed to get workflow executions: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/v1/workflows/{workflow_id}/metrics")
async def get_workflow_metrics(workflow_id: str, period: str = "7d"):
    """Get workflow performance metrics"""
    if not performance_metrics:
        return JSONResponse(
            status_code=503,
            content={"error": "Performance metrics not initialized"}
        )
    
    try:
        metrics = await performance_metrics.get_workflow_metrics(workflow_id, period)
        return {"workflow_id": workflow_id, "period": period, "metrics": metrics}
    except Exception as e:
        logger.error(f"Failed to get workflow metrics: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Agent analytics endpoints
@app.get("/api/v1/agents/analytics")
async def get_agent_analytics(period: str = "30d"):
    """Get agent usage analytics"""
    if not agent_analytics:
        return JSONResponse(
            status_code=503,
            content={"error": "Agent analytics not initialized"}
        )
    
    try:
        analytics = await agent_analytics.get_analytics(period)
        return {"period": period, "analytics": analytics}
    except Exception as e:
        logger.error(f"Failed to get agent analytics: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/v1/agents/{agent_id}/performance")
async def get_agent_performance(agent_id: str, period: str = "7d"):
    """Get agent performance metrics"""
    if not agent_analytics:
        return JSONResponse(
            status_code=503,
            content={"error": "Agent analytics not initialized"}
        )
    
    try:
        performance = await agent_analytics.get_agent_performance(agent_id, period)
        return {"agent_id": agent_id, "period": period, "performance": performance}
    except Exception as e:
        logger.error(f"Failed to get agent performance: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/v1/agents/{agent_id}/workflows")
async def get_agent_workflows(agent_id: str):
    """Get workflows using specific agent"""
    if not agent_analytics:
        return JSONResponse(
            status_code=503,
            content={"error": "Agent analytics not initialized"}
        )
    
    try:
        workflows = await agent_analytics.get_agent_workflows(agent_id)
        return {"agent_id": agent_id, "workflows": workflows}
    except Exception as e:
        logger.error(f"Failed to get agent workflows: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Dashboard endpoints
@app.get("/api/v1/dashboard/overview")
async def get_dashboard_overview():
    """Get dashboard overview data"""
    if not dashboard_api:
        return JSONResponse(
            status_code=503,
            content={"error": "Dashboard API not initialized"}
        )
    
    try:
        overview = await dashboard_api.get_overview()
        return {"overview": overview}
    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/v1/dashboard/metrics")
async def get_dashboard_metrics(period: str = "24h"):
    """Get dashboard metrics"""
    if not dashboard_api:
        return JSONResponse(
            status_code=503,
            content={"error": "Dashboard API not initialized"}
        )
    
    try:
        metrics = await dashboard_api.get_metrics(period)
        return {"period": period, "metrics": metrics}
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Alert endpoints
@app.get("/api/v1/alerts")
async def list_alerts(active_only: bool = True):
    """List alerts"""
    if not alert_manager:
        return JSONResponse(
            status_code=503,
            content={"error": "Alert manager not initialized"}
        )
    
    try:
        alerts = await alert_manager.list_alerts(active_only)
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Failed to list alerts: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    if not alert_manager:
        return JSONResponse(
            status_code=503,
            content={"error": "Alert manager not initialized"}
        )
    
    try:
        await alert_manager.acknowledge_alert(alert_id)
        return {"alert_id": alert_id, "status": "acknowledged"}
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring"""
    if not websocket_manager:
        await websocket.close(code=1011, reason="WebSocket manager not initialized")
        return
    
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Process message
            response = await websocket_manager.process_message(data)
            
            # Send response back
            await websocket.send_text(response)
            
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.N8N_MONITORING_HOST,
        port=settings.N8N_MONITORING_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )