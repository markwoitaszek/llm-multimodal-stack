"""
Protocol Integration Service - Main application entry point
Provides universal IDE compatibility through multiple protocol implementations
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
from fastapi.graphql import GraphQLApp
from strawberry.fastapi import GraphQLRouter

from app.config import settings
from app.lsp_server import LSPServer
from app.mcp_server import MCPServer
from app.custom_protocols import CustomProtocolHandler
from app.protocol_translator import ProtocolTranslator
from app.plugin_manager import PluginManager
from app.websocket_manager import WebSocketManager
from app.graphql_schema import schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
lsp_server: LSPServer = None
mcp_server: MCPServer = None
custom_protocol_handler: CustomProtocolHandler = None
protocol_translator: ProtocolTranslator = None
plugin_manager: PluginManager = None
websocket_manager: WebSocketManager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global lsp_server, mcp_server, custom_protocol_handler, protocol_translator, plugin_manager, websocket_manager
    
    logger.info("Starting Protocol Integration Service...")
    
    try:
        # Initialize components
        websocket_manager = WebSocketManager()
        plugin_manager = PluginManager()
        protocol_translator = ProtocolTranslator()
        custom_protocol_handler = CustomProtocolHandler(protocol_translator)
        mcp_server = MCPServer()
        lsp_server = LSPServer()
        
        # Start background tasks
        await plugin_manager.initialize()
        await protocol_translator.initialize()
        await custom_protocol_handler.initialize()
        await mcp_server.initialize()
        await lsp_server.initialize()
        
        logger.info("Protocol Integration Service started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start Protocol Integration Service: {e}")
        raise
    finally:
        logger.info("Shutting down Protocol Integration Service...")
        if websocket_manager:
            await websocket_manager.disconnect_all()

# Create FastAPI application
app = FastAPI(
    title="Protocol Integration Service",
    description="Universal IDE compatibility through multiple protocol implementations",
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
        "service": "protocol-integration",
        "version": "1.0.0",
        "protocols": {
            "lsp": lsp_server is not None,
            "mcp": mcp_server is not None,
            "custom": custom_protocol_handler is not None,
            "websocket": websocket_manager is not None
        }
    }

# LSP endpoints
@app.post("/lsp")
async def lsp_endpoint(request: Dict[str, Any]):
    """Main LSP endpoint for all LSP requests"""
    if not lsp_server:
        return JSONResponse(
            status_code=503,
            content={"error": "LSP server not initialized"}
        )
    
    try:
        response = await lsp_server.handle_request(request)
        return response
    except Exception as e:
        logger.error(f"LSP request failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# MCP endpoints
@app.get("/mcp/tools")
async def list_mcp_tools():
    """List available MCP tools"""
    if not mcp_server:
        return JSONResponse(
            status_code=503,
            content={"error": "MCP server not initialized"}
        )
    
    try:
        tools = await mcp_server.list_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Failed to list MCP tools: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/mcp/tools/execute")
async def execute_mcp_tool(request: Dict[str, Any]):
    """Execute an MCP tool"""
    if not mcp_server:
        return JSONResponse(
            status_code=503,
            content={"error": "MCP server not initialized"}
        )
    
    try:
        result = await mcp_server.execute_tool(
            request.get("tool"),
            request.get("parameters", {})
        )
        return {"result": result}
    except Exception as e:
        logger.error(f"Failed to execute MCP tool: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/mcp/resources")
async def list_mcp_resources():
    """List available MCP resources"""
    if not mcp_server:
        return JSONResponse(
            status_code=503,
            content={"error": "MCP server not initialized"}
        )
    
    try:
        resources = await mcp_server.list_resources()
        return {"resources": resources}
    except Exception as e:
        logger.error(f"Failed to list MCP resources: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/mcp/resources/{resource_id}")
async def read_mcp_resource(resource_id: str):
    """Read an MCP resource"""
    if not mcp_server:
        return JSONResponse(
            status_code=503,
            content={"error": "MCP server not initialized"}
        )
    
    try:
        resource = await mcp_server.read_resource(resource_id)
        return {"resource": resource}
    except Exception as e:
        logger.error(f"Failed to read MCP resource: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Custom protocol endpoints
@app.post("/custom/{protocol_name}")
async def custom_protocol_endpoint(protocol_name: str, request: Dict[str, Any]):
    """Handle custom protocol requests"""
    if not custom_protocol_handler:
        return JSONResponse(
            status_code=503,
            content={"error": "Custom protocol handler not initialized"}
        )
    
    try:
        result = await custom_protocol_handler.handle_request(protocol_name, request)
        return {"result": result}
    except Exception as e:
        logger.error(f"Custom protocol request failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Protocol translation endpoints
@app.post("/translate/{from_protocol}/{to_protocol}")
async def translate_protocol(from_protocol: str, to_protocol: str, request: Dict[str, Any]):
    """Translate between protocols"""
    if not protocol_translator:
        return JSONResponse(
            status_code=503,
            content={"error": "Protocol translator not initialized"}
        )
    
    try:
        result = await protocol_translator.translate(from_protocol, to_protocol, request)
        return {"result": result}
    except Exception as e:
        logger.error(f"Protocol translation failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Plugin management endpoints
@app.get("/plugins")
async def list_plugins():
    """List available plugins"""
    if not plugin_manager:
        return JSONResponse(
            status_code=503,
            content={"error": "Plugin manager not initialized"}
        )
    
    try:
        plugins = await plugin_manager.list_plugins()
        return {"plugins": plugins}
    except Exception as e:
        logger.error(f"Failed to list plugins: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/plugins/{plugin_name}/enable")
async def enable_plugin(plugin_name: str):
    """Enable a plugin"""
    if not plugin_manager:
        return JSONResponse(
            status_code=503,
            content={"error": "Plugin manager not initialized"}
        )
    
    try:
        await plugin_manager.enable_plugin(plugin_name)
        return {"status": "enabled", "plugin": plugin_name}
    except Exception as e:
        logger.error(f"Failed to enable plugin: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/plugins/{plugin_name}/disable")
async def disable_plugin(plugin_name: str):
    """Disable a plugin"""
    if not plugin_manager:
        return JSONResponse(
            status_code=503,
            content={"error": "Plugin manager not initialized"}
        )
    
    try:
        await plugin_manager.disable_plugin(plugin_name)
        return {"status": "disabled", "plugin": plugin_name}
    except Exception as e:
        logger.error(f"Failed to disable plugin: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time protocol communication"""
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

# GraphQL endpoint
app.add_route("/graphql", GraphQLRouter(schema))

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.PROTOCOL_INTEGRATION_HOST,
        port=settings.PROTOCOL_INTEGRATION_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )