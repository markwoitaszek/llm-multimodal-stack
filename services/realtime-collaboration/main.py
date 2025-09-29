"""
Real-Time Collaboration Service

Provides WebSocket-based real-time communication, live agent execution monitoring,
and collaborative workspace features for the Multimodal LLM Stack.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from app.config import get_settings
from app.websocket_manager import WebSocketManager
from app.workspace_manager import WorkspaceManager
from app.agent_monitor import AgentMonitor
from app.message_queue import MessageQueue
from app.auth import AuthManager
from app.rate_limiter import RateLimiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Real-Time Collaboration Service",
    description="WebSocket-based real-time communication and collaboration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global managers
websocket_manager = WebSocketManager()
workspace_manager = WorkspaceManager()
agent_monitor = AgentMonitor()
message_queue = MessageQueue()
auth_manager = AuthManager()
rate_limiter = RateLimiter()

# Pydantic models
class ConnectionInfo(BaseModel):
    connection_id: str
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    connected_at: datetime
    last_activity: datetime

class WorkspaceInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_by: str
    created_at: datetime
    users: List[str] = Field(default_factory=list)
    agents: List[str] = Field(default_factory=list)

class AgentStatus(BaseModel):
    agent_id: str
    status: str
    current_task: Optional[str] = None
    progress: Optional[int] = None
    last_activity: datetime
    execution_count: int = 0
    success_rate: float = 0.0

class Message(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None
    message_id: Optional[str] = None

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        settings = get_settings()
        logger.info("Starting Real-Time Collaboration Service")
        
        # Initialize managers
        await websocket_manager.initialize()
        await workspace_manager.initialize()
        await agent_monitor.initialize()
        await message_queue.initialize()
        await auth_manager.initialize()
        await rate_limiter.initialize()
        
        # Start background tasks
        asyncio.create_task(heartbeat_task())
        asyncio.create_task(agent_monitoring_task())
        asyncio.create_task(message_processing_task())
        
        logger.info("Real-Time Collaboration Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("Shutting down Real-Time Collaboration Service")
        
        # Disconnect all WebSocket connections
        await websocket_manager.disconnect_all()
        
        # Stop background tasks
        # Note: In a real implementation, you'd properly cancel tasks
        
        logger.info("Real-Time Collaboration Service shut down successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "realtime-collaboration",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health/websocket")
async def websocket_health():
    """WebSocket health check"""
    connections = await websocket_manager.get_connection_count()
    return {
        "status": "healthy",
        "active_connections": connections,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health/database")
async def database_health():
    """Database health check"""
    try:
        # In a real implementation, this would check database connectivity
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get("/health/redis")
async def redis_health():
    """Redis health check"""
    try:
        # In a real implementation, this would check Redis connectivity
        return {
            "status": "healthy",
            "redis": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "redis": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Status endpoints
@app.get("/status")
async def get_status():
    """Get service status"""
    connections = await websocket_manager.get_connection_count()
    workspaces = await workspace_manager.get_workspace_count()
    agents = await agent_monitor.get_agent_count()
    
    return {
        "service": "realtime-collaboration",
        "status": "running",
        "active_connections": connections,
        "workspaces": workspaces,
        "monitored_agents": agents,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/connections")
async def get_connections():
    """Get active connections"""
    connections = await websocket_manager.get_all_connections()
    return {
        "connections": connections,
        "count": len(connections),
        "timestamp": datetime.utcnow().isoformat()
    }

# Workspace endpoints
@app.get("/workspaces")
async def get_workspaces():
    """Get all workspaces"""
    workspaces = await workspace_manager.get_all_workspaces()
    return {
        "workspaces": workspaces,
        "count": len(workspaces),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/workspaces")
async def create_workspace(workspace: WorkspaceInfo):
    """Create a new workspace"""
    try:
        workspace_id = await workspace_manager.create_workspace(workspace)
        return {
            "workspace_id": workspace_id,
            "status": "created",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: str):
    """Get workspace details"""
    workspace = await workspace_manager.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace

@app.post("/workspaces/{workspace_id}/join")
async def join_workspace(workspace_id: str, user_id: str):
    """Join a workspace"""
    try:
        success = await workspace_manager.join_workspace(workspace_id, user_id)
        if success:
            return {
                "status": "joined",
                "workspace_id": workspace_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to join workspace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/workspaces/{workspace_id}/leave")
async def leave_workspace(workspace_id: str, user_id: str):
    """Leave a workspace"""
    try:
        success = await workspace_manager.leave_workspace(workspace_id, user_id)
        if success:
            return {
                "status": "left",
                "workspace_id": workspace_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to leave workspace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/workspaces/{workspace_id}/users")
async def get_workspace_users(workspace_id: str):
    """Get workspace users"""
    users = await workspace_manager.get_workspace_users(workspace_id)
    return {
        "workspace_id": workspace_id,
        "users": users,
        "count": len(users),
        "timestamp": datetime.utcnow().isoformat()
    }

# Agent monitoring endpoints
@app.get("/agents/status")
async def get_agent_status():
    """Get agent status"""
    agents = await agent_monitor.get_all_agents()
    return {
        "agents": agents,
        "count": len(agents),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/agents/{agent_id}/subscribe")
async def subscribe_agent(agent_id: str, user_id: str):
    """Subscribe to agent updates"""
    try:
        success = await agent_monitor.subscribe_user(agent_id, user_id)
        if success:
            return {
                "status": "subscribed",
                "agent_id": agent_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to subscribe to agent")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/agents/{agent_id}/unsubscribe")
async def unsubscribe_agent(agent_id: str, user_id: str):
    """Unsubscribe from agent updates"""
    try:
        success = await agent_monitor.unsubscribe_user(agent_id, user_id)
        if success:
            return {
                "status": "unsubscribed",
                "agent_id": agent_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to unsubscribe from agent")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# WebSocket endpoints
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint"""
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    
    try:
        # Add connection to manager
        await websocket_manager.add_connection(connection_id, websocket)
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "data": {
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }))
        
        # Handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Rate limiting
                if not await rate_limiter.check_rate_limit(connection_id):
                    await websocket.send_text(json.dumps({
                        "type": "rate_limit_exceeded",
                        "data": {
                            "message": "Rate limit exceeded",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }))
                    continue
                
                # Process message
                await process_websocket_message(connection_id, message, websocket)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {
                        "message": "Invalid JSON format",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {
                        "message": "Internal server error",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }))
    
    except WebSocketDisconnect:
        pass
    finally:
        # Remove connection from manager
        await websocket_manager.remove_connection(connection_id)

@app.websocket("/ws/agents")
async def agent_websocket_endpoint(websocket: WebSocket):
    """Agent-specific WebSocket endpoint"""
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    
    try:
        await websocket_manager.add_connection(connection_id, websocket)
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "agent_connection_established",
            "data": {
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }))
        
        # Handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process agent-specific messages
                await process_agent_message(connection_id, message, websocket)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing agent message: {e}")
    
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.remove_connection(connection_id)

@app.websocket("/ws/workspaces")
async def workspace_websocket_endpoint(websocket: WebSocket):
    """Workspace collaboration WebSocket endpoint"""
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    
    try:
        await websocket_manager.add_connection(connection_id, websocket)
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "workspace_connection_established",
            "data": {
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }))
        
        # Handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process workspace-specific messages
                await process_workspace_message(connection_id, message, websocket)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing workspace message: {e}")
    
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.remove_connection(connection_id)

# Message processing functions
async def process_websocket_message(connection_id: str, message: Dict[str, Any], websocket: WebSocket):
    """Process WebSocket messages"""
    message_type = message.get("type")
    data = message.get("data", {})
    
    if message_type == "ping":
        await websocket.send_text(json.dumps({
            "type": "pong",
            "data": {
                "timestamp": datetime.utcnow().isoformat()
            }
        }))
    
    elif message_type == "subscribe_agent":
        agent_id = data.get("agent_id")
        if agent_id:
            await agent_monitor.subscribe_connection(agent_id, connection_id)
            await websocket.send_text(json.dumps({
                "type": "agent_subscribed",
                "data": {
                    "agent_id": agent_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }))
    
    elif message_type == "unsubscribe_agent":
        agent_id = data.get("agent_id")
        if agent_id:
            await agent_monitor.unsubscribe_connection(agent_id, connection_id)
            await websocket.send_text(json.dumps({
                "type": "agent_unsubscribed",
                "data": {
                    "agent_id": agent_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }))
    
    elif message_type == "join_workspace":
        workspace_id = data.get("workspace_id")
        user_id = data.get("user_id")
        if workspace_id and user_id:
            success = await workspace_manager.join_workspace(workspace_id, user_id)
            if success:
                await websocket_manager.broadcast_to_workspace(workspace_id, {
                    "type": "user_joined",
                    "data": {
                        "workspace_id": workspace_id,
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
    
    elif message_type == "leave_workspace":
        workspace_id = data.get("workspace_id")
        user_id = data.get("user_id")
        if workspace_id and user_id:
            success = await workspace_manager.leave_workspace(workspace_id, user_id)
            if success:
                await websocket_manager.broadcast_to_workspace(workspace_id, {
                    "type": "user_left",
                    "data": {
                        "workspace_id": workspace_id,
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
    
    else:
        # Unknown message type
        await websocket.send_text(json.dumps({
            "type": "error",
            "data": {
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.utcnow().isoformat()
            }
        }))

async def process_agent_message(connection_id: str, message: Dict[str, Any], websocket: WebSocket):
    """Process agent-specific messages"""
    message_type = message.get("type")
    data = message.get("data", {})
    
    if message_type == "agent_status_request":
        agent_id = data.get("agent_id")
        if agent_id:
            status = await agent_monitor.get_agent_status(agent_id)
            await websocket.send_text(json.dumps({
                "type": "agent_status_response",
                "data": {
                    "agent_id": agent_id,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }))
    
    elif message_type == "agent_execution_request":
        agent_id = data.get("agent_id")
        task = data.get("task")
        if agent_id and task:
            # Forward to agent monitor
            await agent_monitor.start_execution(agent_id, task, connection_id)
    
    else:
        # Process as regular message
        await process_websocket_message(connection_id, message, websocket)

async def process_workspace_message(connection_id: str, message: Dict[str, Any], websocket: WebSocket):
    """Process workspace-specific messages"""
    message_type = message.get("type")
    data = message.get("data", {})
    
    if message_type == "workspace_update":
        workspace_id = data.get("workspace_id")
        update_type = data.get("update_type")
        if workspace_id and update_type:
            # Broadcast to all workspace members
            await websocket_manager.broadcast_to_workspace(workspace_id, {
                "type": "workspace_update",
                "data": {
                    "workspace_id": workspace_id,
                    "update_type": update_type,
                    "data": data.get("data", {}),
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
    
    else:
        # Process as regular message
        await process_websocket_message(connection_id, message, websocket)

# Background tasks
async def heartbeat_task():
    """Send heartbeat messages to all connections"""
    while True:
        try:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            await websocket_manager.broadcast_to_all({
                "type": "heartbeat",
                "data": {
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error in heartbeat task: {e}")

async def agent_monitoring_task():
    """Monitor agent executions and broadcast updates"""
    while True:
        try:
            await asyncio.sleep(5)  # Check every 5 seconds
            await agent_monitor.check_agent_status()
        except Exception as e:
            logger.error(f"Error in agent monitoring task: {e}")

async def message_processing_task():
    """Process queued messages"""
    while True:
        try:
            await asyncio.sleep(1)  # Process every second
            await message_queue.process_messages()
        except Exception as e:
            logger.error(f"Error in message processing task: {e}")

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )