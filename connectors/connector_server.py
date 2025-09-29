#!/usr/bin/env python3
"""
Connector Management Server
Part of Issue #10: API Connector Ecosystem

This module provides a FastAPI server for managing connectors including:
- Connector lifecycle management
- Configuration management
- Health monitoring
- Request proxying
- Analytics and metrics
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import JSONResponse, HTMLResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError as e:
    logger.error(f"Missing dependencies: {e}")
    logger.info("Install with: pip install fastapi uvicorn")
    raise

from connector_framework import (
    ConnectorRegistry, ConnectorManager, ConnectorConfig, ConnectorResponse,
    AuthenticationType, DataFormat, ConnectorStatus, ConnectorError
)
from prebuilt_connectors import create_connector
from connector_builder import ConnectorBuilder

# Pydantic models for API
class ConnectorCreateRequest(BaseModel):
    name: str
    description: str
    connector_type: str
    base_url: str
    authentication_type: str = "api_key"
    auth_config: Dict[str, Any] = {}
    headers: Dict[str, str] = {}
    timeout: int = 30
    retry_attempts: int = 3
    custom_config: Dict[str, Any] = {}

class ConnectorUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_url: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None
    retry_attempts: Optional[int] = None
    custom_config: Optional[Dict[str, Any]] = None

class ConnectorRequest(BaseModel):
    endpoint_name: str
    params: Optional[Dict[str, Any]] = None
    data: Optional[Any] = None
    headers: Optional[Dict[str, str]] = None
    transform_mapping: Optional[Dict[str, str]] = None

class ConnectorResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    metadata: Dict[str, Any] = {}

class ConnectorHealthResponse(BaseModel):
    connector_id: str
    status: str
    metrics: Dict[str, Any]
    endpoints: List[str]
    last_check: str

class ConnectorServer:
    """FastAPI server for connector management"""
    
    def __init__(self, port: int = 8082):
        self.port = port
        self.registry = ConnectorRegistry()
        self.manager = ConnectorManager(self.registry)
        self.builder = ConnectorBuilder()
        self.active_connections: List[WebSocket] = []
        
        # Register pre-built connector types
        self._register_connector_types()
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Connector Management Server",
            description="API for managing and using connectors",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Define routes
        self._setup_routes()
    
    def _register_connector_types(self):
        """Register pre-built connector types"""
        from prebuilt_connectors import (
            OpenAIConnector, GoogleCloudConnector, SlackConnector,
            GitHubConnector, SalesforceConnector, AWSConnector, CustomRESTConnector
        )
        
        self.registry.register_connector_type("openai", OpenAIConnector)
        self.registry.register_connector_type("google_cloud", GoogleCloudConnector)
        self.registry.register_connector_type("slack", SlackConnector)
        self.registry.register_connector_type("github", GitHubConnector)
        self.registry.register_connector_type("salesforce", SalesforceConnector)
        self.registry.register_connector_type("aws", AWSConnector)
        self.registry.register_connector_type("custom_rest", CustomRESTConnector)
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "Connector Management Server",
                "version": "1.0.0",
                "available_connector_types": list(self.registry.connector_types.keys()),
                "active_connectors": len(self.registry.connectors)
            }
        
        @self.app.get("/api/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        # Connector management endpoints
        @self.app.get("/api/connectors")
        async def list_connectors():
            """List all connectors"""
            connectors = self.registry.list_connectors()
            return {"connectors": connectors}
        
        @self.app.post("/api/connectors")
        async def create_connector(request: ConnectorCreateRequest):
            """Create a new connector"""
            try:
                # Generate connector ID
                connector_id = f"{request.name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
                
                # Create configuration
                config = ConnectorConfig(
                    connector_id=connector_id,
                    name=request.name,
                    description=request.description,
                    version="1.0.0",
                    base_url=request.base_url,
                    authentication_type=AuthenticationType(request.authentication_type),
                    auth_config=request.auth_config,
                    headers=request.headers,
                    timeout=request.timeout,
                    retry_attempts=request.retry_attempts,
                    data_format=DataFormat.JSON,
                    custom_config=request.custom_config
                )
                
                # Create connector
                connector = self.registry.create_connector(config, request.connector_type)
                
                return {
                    "connector_id": connector_id,
                    "name": request.name,
                    "status": "created",
                    "message": "Connector created successfully"
                }
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/connectors/{connector_id}")
        async def get_connector(connector_id: str):
            """Get connector details"""
            connector = self.registry.get_connector(connector_id)
            if not connector:
                raise HTTPException(status_code=404, detail="Connector not found")
            
            return {
                "connector_id": connector_id,
                "name": connector.config.name,
                "description": connector.config.description,
                "status": connector.get_status().value,
                "endpoints": list(connector.get_endpoints().keys()),
                "metrics": connector.get_metrics()
            }
        
        @self.app.put("/api/connectors/{connector_id}")
        async def update_connector(connector_id: str, request: ConnectorUpdateRequest):
            """Update connector configuration"""
            connector = self.registry.get_connector(connector_id)
            if not connector:
                raise HTTPException(status_code=404, detail="Connector not found")
            
            try:
                # Update configuration
                if request.name:
                    connector.config.name = request.name
                if request.description:
                    connector.config.description = request.description
                if request.base_url:
                    connector.config.base_url = request.base_url
                if request.auth_config:
                    connector.config.auth_config.update(request.auth_config)
                if request.headers:
                    connector.config.headers.update(request.headers)
                if request.timeout:
                    connector.config.timeout = request.timeout
                if request.retry_attempts:
                    connector.config.retry_attempts = request.retry_attempts
                if request.custom_config:
                    connector.config.custom_config.update(request.custom_config)
                
                return {
                    "connector_id": connector_id,
                    "status": "updated",
                    "message": "Connector updated successfully"
                }
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.delete("/api/connectors/{connector_id}")
        async def delete_connector(connector_id: str):
            """Delete a connector"""
            connector = self.registry.get_connector(connector_id)
            if not connector:
                raise HTTPException(status_code=404, detail="Connector not found")
            
            try:
                # Stop connector if running
                if connector.get_status() == ConnectorStatus.ACTIVE:
                    await connector.stop()
                
                # Remove from registry
                del self.registry.connectors[connector_id]
                del self.registry.configs[connector_id]
                
                return {
                    "connector_id": connector_id,
                    "status": "deleted",
                    "message": "Connector deleted successfully"
                }
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # Connector lifecycle endpoints
        @self.app.post("/api/connectors/{connector_id}/start")
        async def start_connector(connector_id: str):
            """Start a connector"""
            try:
                await self.manager.registry.start_connector(connector_id)
                return {
                    "connector_id": connector_id,
                    "status": "started",
                    "message": "Connector started successfully"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/connectors/{connector_id}/stop")
        async def stop_connector(connector_id: str):
            """Stop a connector"""
            try:
                await self.manager.registry.stop_connector(connector_id)
                return {
                    "connector_id": connector_id,
                    "status": "stopped",
                    "message": "Connector stopped successfully"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/connectors/{connector_id}/test")
        async def test_connector(connector_id: str):
            """Test a connector"""
            connector = self.registry.get_connector(connector_id)
            if not connector:
                raise HTTPException(status_code=404, detail="Connector not found")
            
            try:
                # Test connection
                is_connected = await connector.test_connection()
                
                return {
                    "connector_id": connector_id,
                    "test_result": "success" if is_connected else "failed",
                    "message": "Connection test completed"
                }
                
            except Exception as e:
                return {
                    "connector_id": connector_id,
                    "test_result": "failed",
                    "error": str(e)
                }
        
        # Request execution endpoints
        @self.app.post("/api/connectors/{connector_id}/request")
        async def execute_request(connector_id: str, request: ConnectorRequest):
            """Execute a request through a connector"""
            try:
                response = await self.manager.execute_connector_request(
                    connector_id=connector_id,
                    endpoint_name=request.endpoint_name,
                    params=request.params,
                    data=request.data,
                    transform_mapping=request.transform_mapping
                )
                
                return {
                    "success": response.success,
                    "data": response.data,
                    "error": response.error,
                    "status_code": response.status_code,
                    "metadata": response.metadata
                }
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # Health monitoring endpoints
        @self.app.get("/api/connectors/{connector_id}/health")
        async def get_connector_health(connector_id: str):
            """Get connector health information"""
            health = self.manager.get_connector_health(connector_id)
            if health["status"] == "not_found":
                raise HTTPException(status_code=404, detail="Connector not found")
            
            return health
        
        @self.app.get("/api/connectors/health")
        async def get_all_connector_health():
            """Get health information for all connectors"""
            return self.manager.get_all_connector_health()
        
        # Connector builder endpoints
        @self.app.post("/api/connectors/build")
        async def build_connector(
            name: str,
            description: str,
            base_url: str,
            authentication_type: str = "api_key",
            endpoints: str = "[]"
        ):
            """Build a custom connector"""
            try:
                # Parse endpoints
                endpoints_list = json.loads(endpoints)
                
                # Build connector
                result = self.builder.build_complete_connector(
                    name=name,
                    description=description,
                    base_url=base_url,
                    authentication_type=authentication_type,
                    endpoints=endpoints_list,
                    test_connector=True
                )
                
                return {
                    "status": "built",
                    "spec_file": str(result["spec_file"]),
                    "code_file": str(result["code_file"]),
                    "doc_file": str(result["doc_file"]),
                    "test_results": result.get("test_results", {})
                }
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
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
                    elif message.get("type") == "get_connectors":
                        connectors = self.registry.list_connectors()
                        await websocket.send_text(json.dumps({
                            "type": "connectors",
                            "data": connectors
                        }))
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
    
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
    
    async def start_periodic_health_checks(self):
        """Start periodic health checks for all connectors"""
        while True:
            try:
                # Check health of all connectors
                health_data = self.manager.get_all_connector_health()
                
                # Broadcast health update
                await self.broadcast_update("health_update", health_data)
                
                # Wait for next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in periodic health checks: {e}")
                await asyncio.sleep(30)
    
    async def initialize(self):
        """Initialize the connector server"""
        try:
            # Start background tasks
            asyncio.create_task(self.start_periodic_health_checks())
            
            logger.info("Connector management server initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing connector server: {e}")
            raise
    
    async def start(self):
        """Start the connector server"""
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
    """Main function to run the connector server"""
    server = ConnectorServer(port=8082)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Connector server stopped by user")
    except Exception as e:
        logger.error(f"Error running connector server: {e}")

if __name__ == "__main__":
    asyncio.run(main())