#!/usr/bin/env python3
"""
MCP Server Implementation
Part of Issue #6: MCP Support

This FastAPI server provides comprehensive MCP support including:
- MCP protocol server implementation
- Tool discovery and execution
- Resource management and serving
- Prompt engineering and management
- Completion handling and streaming
- Integration with AI models
- WebSocket and HTTP support
"""

import asyncio
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# Import MCP modules
from mcp_protocol import (
    MCPClient, MCPServer, MCPTool, MCPResource, MCPPrompt, MCPCompletion,
    MCPError, MCPErrorCode, MCPMethod, MCPMessage
)
from mcp_integration import (
    MCPIntegrationManager, MCPToolExecutor, MCPResourceManager,
    IntegrationConfig, ModelConfig, ModelProvider, IntegrationType,
    ExecutionResult
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Server",
    description="Model Context Protocol server for AI model integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global managers
integration_manager: Optional[MCPIntegrationManager] = None
tool_executor: Optional[MCPToolExecutor] = None
resource_manager: Optional[MCPResourceManager] = None
mcp_server: Optional[MCPServer] = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_text(json.dumps(message))
    
    async def broadcast(self, message: dict):
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")

connection_manager = ConnectionManager()

# Pydantic models for API requests/responses
class IntegrationCreateRequest(BaseModel):
    integration_id: str
    name: str
    description: str
    integration_type: str
    model_provider: str
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    metadata: Dict[str, Any] = {}

class ToolExecuteRequest(BaseModel):
    integration_id: str
    tool_name: str
    arguments: Dict[str, Any] = {}

class ResourceReadRequest(BaseModel):
    integration_id: str
    resource_uri: str
    use_cache: bool = True

class PromptGetRequest(BaseModel):
    integration_id: str
    prompt_name: str
    arguments: Dict[str, Any] = {}

class CompletionRequest(BaseModel):
    integration_id: str
    prompt: str
    max_tokens: int = 1000
    stream: bool = False

class ToolChainRequest(BaseModel):
    tool_chain: List[Dict[str, Any]]

class ParallelToolsRequest(BaseModel):
    tool_calls: List[Dict[str, Any]]

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize managers on startup"""
    global integration_manager, tool_executor, resource_manager, mcp_server
    
    data_dir = Path("./mcp_data")
    data_dir.mkdir(exist_ok=True)
    
    # Initialize managers
    integration_manager = MCPIntegrationManager(data_dir)
    tool_executor = MCPToolExecutor(integration_manager)
    resource_manager = MCPResourceManager(integration_manager)
    mcp_server = MCPServer()
    
    # Register some default tools
    def echo_tool(arguments):
        return f"Echo: {arguments.get('message', 'Hello')}"
    
    mcp_server.register_tool(MCPTool(
        name="echo",
        description="Echo a message",
        input_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message to echo"}
            },
            "required": ["message"]
        },
        handler=echo_tool
    ))
    
    # Register some default resources
    def file_resource():
        return "This is a sample file resource"
    
    mcp_server.register_resource(MCPResource(
        uri="file://sample.txt",
        name="Sample File",
        description="A sample file resource",
        mime_type="text/plain",
        handler=file_resource
    ))
    
    # Register some default prompts
    def code_prompt(arguments):
        return f"Write code for: {arguments.get('task', 'Hello World')}"
    
    mcp_server.register_prompt(MCPPrompt(
        name="code_generator",
        description="Generate code for a given task",
        arguments=[
            {"name": "task", "description": "The task to generate code for", "required": True}
        ],
        handler=code_prompt
    ))
    
    logger.info("MCP Server started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if integration_manager:
        await integration_manager.disconnect_all()
    logger.info("MCP Server stopped")

# Dependency functions
def get_integration_manager() -> MCPIntegrationManager:
    if not integration_manager:
        raise HTTPException(status_code=500, detail="Integration manager not initialized")
    return integration_manager

def get_tool_executor() -> MCPToolExecutor:
    if not tool_executor:
        raise HTTPException(status_code=500, detail="Tool executor not initialized")
    return tool_executor

def get_resource_manager() -> MCPResourceManager:
    if not resource_manager:
        raise HTTPException(status_code=500, detail="Resource manager not initialized")
    return resource_manager

def get_mcp_server() -> MCPServer:
    if not mcp_server:
        raise HTTPException(status_code=500, detail="MCP server not initialized")
    return mcp_server

# Integration Management Endpoints
@app.post("/integrations")
async def create_integration(
    request: IntegrationCreateRequest,
    mgr: MCPIntegrationManager = Depends(get_integration_manager)
):
    """Create a new integration"""
    try:
        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            api_key=request.api_key,
            base_url=request.base_url,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        integration = mgr.create_integration(
            request.integration_id,
            request.name,
            request.description,
            IntegrationType(request.integration_type),
            model_config,
            request.metadata
        )
        
        return {"message": "Integration created successfully", "integration_id": integration.integration_id}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/integrations")
async def list_integrations(
    mgr: MCPIntegrationManager = Depends(get_integration_manager)
):
    """List all integrations"""
    try:
        integrations = mgr.list_integrations()
        
        return [
            {
                "integration_id": integration.integration_id,
                "name": integration.name,
                "description": integration.description,
                "integration_type": integration.integration_type.value,
                "model_provider": integration.model_config.provider.value,
                "model_name": integration.model_config.model_name,
                "enabled": integration.enabled,
                "metadata": integration.metadata
            }
            for integration in integrations
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/integrations/{integration_id}")
async def get_integration(
    integration_id: str,
    mgr: MCPIntegrationManager = Depends(get_integration_manager)
):
    """Get integration by ID"""
    try:
        integration = mgr.get_integration(integration_id)
        
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        return {
            "integration_id": integration.integration_id,
            "name": integration.name,
            "description": integration.description,
            "integration_type": integration.integration_type.value,
            "model_provider": integration.model_config.provider.value,
            "model_name": integration.model_config.model_name,
            "enabled": integration.enabled,
            "metadata": integration.metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/integrations/{integration_id}/connect")
async def connect_integration(
    integration_id: str,
    server_url: str,
    mgr: MCPIntegrationManager = Depends(get_integration_manager)
):
    """Connect integration to MCP server"""
    try:
        success = await mgr.connect_to_mcp_server(integration_id, server_url)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to connect to MCP server")
        
        return {"message": "Integration connected successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/integrations/{integration_id}/disconnect")
async def disconnect_integration(
    integration_id: str,
    mgr: MCPIntegrationManager = Depends(get_integration_manager)
):
    """Disconnect integration"""
    try:
        success = await mgr.disconnect_integration(integration_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to disconnect integration")
        
        return {"message": "Integration disconnected successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Tool Management Endpoints
@app.get("/tools")
async def list_tools(
    mgr: MCPIntegrationManager = Depends(get_integration_manager)
):
    """List all available tools"""
    try:
        tools = mgr.list_available_tools()
        
        return [
            {
                "integration_id": tool["integration_id"],
                "name": tool["name"],
                "description": tool["data"].get("description", ""),
                "input_schema": tool["data"].get("inputSchema", {})
            }
            for tool in tools
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tools/execute")
async def execute_tool(
    request: ToolExecuteRequest,
    mgr: MCPIntegrationManager = Depends(get_integration_manager)
):
    """Execute a tool"""
    try:
        result = await mgr.execute_tool(
            request.integration_id,
            request.tool_name,
            request.arguments
        )
        
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "execution_time": result.execution_time,
            "metadata": result.metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tools/chain")
async def execute_tool_chain(
    request: ToolChainRequest,
    executor: MCPToolExecutor = Depends(get_tool_executor)
):
    """Execute a chain of tools"""
    try:
        results = await executor.execute_tool_chain(request.tool_chain)
        
        return [
            {
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "execution_time": result.execution_time,
                "metadata": result.metadata
            }
            for result in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tools/parallel")
async def execute_parallel_tools(
    request: ParallelToolsRequest,
    executor: MCPToolExecutor = Depends(get_tool_executor)
):
    """Execute multiple tools in parallel"""
    try:
        results = await executor.execute_parallel_tools(request.tool_calls)
        
        return [
            {
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "execution_time": result.execution_time,
                "metadata": result.metadata
            }
            for result in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Resource Management Endpoints
@app.get("/resources")
async def list_resources(
    mgr: MCPIntegrationManager = Depends(get_integration_manager)
):
    """List all available resources"""
    try:
        resources = mgr.list_available_resources()
        
        return [
            {
                "integration_id": resource["integration_id"],
                "uri": resource["uri"],
                "name": resource["data"].get("name", ""),
                "description": resource["data"].get("description", ""),
                "mime_type": resource["data"].get("mimeType", "")
            }
            for resource in resources
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/resources/read")
async def read_resource(
    request: ResourceReadRequest,
    mgr: MCPResourceManager = Depends(get_resource_manager)
):
    """Read a resource"""
    try:
        result = await mgr.get_resource(
            request.integration_id,
            request.resource_uri,
            request.use_cache
        )
        
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "execution_time": result.execution_time,
            "metadata": result.metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/resources/{integration_id}/{resource_uri}/subscribe")
async def subscribe_to_resource(
    integration_id: str,
    resource_uri: str,
    mgr: MCPResourceManager = Depends(get_resource_manager)
):
    """Subscribe to resource changes"""
    try:
        success = await mgr.subscribe_to_resource(integration_id, resource_uri)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to subscribe to resource")
        
        return {"message": "Subscribed to resource successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Prompt Management Endpoints
@app.get("/prompts")
async def list_prompts(
    mgr: MCPIntegrationManager = Depends(get_integration_manager)
):
    """List all available prompts"""
    try:
        prompts = mgr.list_available_prompts()
        
        return [
            {
                "integration_id": prompt["integration_id"],
                "name": prompt["name"],
                "description": prompt["data"].get("description", ""),
                "arguments": prompt["data"].get("arguments", [])
            }
            for prompt in prompts
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/prompts/get")
async def get_prompt(
    request: PromptGetRequest,
    mgr: MCPIntegrationManager = Depends(get_integration_manager)
):
    """Get a prompt"""
    try:
        result = await mgr.get_prompt(
            request.integration_id,
            request.prompt_name,
            request.arguments
        )
        
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "execution_time": result.execution_time,
            "metadata": result.metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Completion Endpoints
@app.post("/completions")
async def get_completion(
    request: CompletionRequest,
    mgr: MCPIntegrationManager = Depends(get_integration_manager)
):
    """Get completion"""
    try:
        if request.stream:
            return StreamingResponse(
                mgr.stream_completion(
                    request.integration_id,
                    request.prompt,
                    request.max_tokens
                ),
                media_type="text/plain"
            )
        else:
            result = await mgr.get_completion(
                request.integration_id,
                request.prompt,
                request.max_tokens
            )
            
            return {
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "execution_time": result.execution_time,
                "metadata": result.metadata
            }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# WebSocket Endpoint for MCP Protocol
@app.websocket("/mcp")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for MCP protocol"""
    client_id = str(uuid.uuid4())
    
    try:
        await connection_manager.connect(websocket, client_id)
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle MCP message
            message = MCPMessage(**message_data)
            response = await mcp_server.handle_message(message, client_id)
            
            # Send response
            await websocket.send_text(json.dumps(asdict(response)))
            
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(client_id)

# System Endpoints
@app.get("/summary")
async def get_summary(
    mgr: MCPIntegrationManager = Depends(get_integration_manager)
):
    """Get system summary"""
    try:
        summary = mgr.get_integration_summary()
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "mcp-server"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "MCP Server",
        "version": "1.0.0",
        "description": "Model Context Protocol server for AI model integration",
        "endpoints": {
            "integrations": "/integrations",
            "tools": "/tools",
            "resources": "/resources",
            "prompts": "/prompts",
            "completions": "/completions",
            "websocket": "/mcp",
            "summary": "/summary",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )