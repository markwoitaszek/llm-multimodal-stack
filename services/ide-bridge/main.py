"""
IDE Bridge Service - Main application entry point
Provides LSP, MCP, and WebSocket support for IDE integration
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
from app.lsp_server import LSPServer
from app.mcp_server import MCPServer
from app.websocket_manager import WebSocketManager
from app.agent_integration import AgentIntegration
from app.code_analyzer import CodeAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
lsp_server: LSPServer = None
mcp_server: MCPServer = None
websocket_manager: WebSocketManager = None
agent_integration: AgentIntegration = None
code_analyzer: CodeAnalyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global lsp_server, mcp_server, websocket_manager, agent_integration, code_analyzer
    
    logger.info("Starting IDE Bridge Service...")
    
    try:
        # Initialize components
        code_analyzer = CodeAnalyzer()
        agent_integration = AgentIntegration()
        websocket_manager = WebSocketManager()
        lsp_server = LSPServer(code_analyzer, agent_integration)
        mcp_server = MCPServer(agent_integration)
        
        # Start background tasks
        await code_analyzer.initialize()
        await agent_integration.initialize()
        
        logger.info("IDE Bridge Service started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start IDE Bridge Service: {e}")
        raise
    finally:
        logger.info("Shutting down IDE Bridge Service...")
        if websocket_manager:
            await websocket_manager.disconnect_all()
        if agent_integration:
            await agent_integration.cleanup()

# Create FastAPI application
app = FastAPI(
    title="IDE Bridge Service",
    description="LSP, MCP, and WebSocket support for IDE integration",
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
        "service": "ide-bridge",
        "version": "1.0.0",
        "components": {
            "lsp_server": lsp_server is not None,
            "mcp_server": mcp_server is not None,
            "websocket_manager": websocket_manager is not None,
            "agent_integration": agent_integration is not None,
            "code_analyzer": code_analyzer is not None
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

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
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

# Agent integration endpoints
@app.post("/agents/execute")
async def execute_agent_task(request: Dict[str, Any]):
    """Execute an agent task from IDE"""
    if not agent_integration:
        return JSONResponse(
            status_code=503,
            content={"error": "Agent integration not initialized"}
        )
    
    try:
        result = await agent_integration.execute_task(
            request.get("agent_id"),
            request.get("task"),
            request.get("context", {})
        )
        return {"result": result}
    except Exception as e:
        logger.error(f"Failed to execute agent task: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/agents")
async def list_available_agents():
    """List available agents for IDE integration"""
    if not agent_integration:
        return JSONResponse(
            status_code=503,
            content={"error": "Agent integration not initialized"}
        )
    
    try:
        agents = await agent_integration.list_agents()
        return {"agents": agents}
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Code analysis endpoints
@app.post("/analyze")
async def analyze_code(request: Dict[str, Any]):
    """Analyze code for suggestions and errors"""
    if not code_analyzer:
        return JSONResponse(
            status_code=503,
            content={"error": "Code analyzer not initialized"}
        )
    
    try:
        analysis = await code_analyzer.analyze(
            request.get("code"),
            request.get("language"),
            request.get("file_path")
        )
        return {"analysis": analysis}
    except Exception as e:
        logger.error(f"Failed to analyze code: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.IDE_BRIDGE_HOST,
        port=settings.IDE_BRIDGE_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )