#!/usr/bin/env python3
"""
AI Agents Service
LangChain-based autonomous agents with multimodal capabilities
"""

import os
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.agent_manager import AgentManager
from app.tools import ToolRegistry
from app.memory import MemoryManager
from app.api import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global managers
agent_manager = None
tool_registry = None
memory_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global agent_manager, tool_registry, memory_manager
    
    logger.info("Starting AI Agents Service...")
    
    try:
        # Initialize managers
        tool_registry = ToolRegistry()
        memory_manager = MemoryManager()
        agent_manager = AgentManager(tool_registry, memory_manager)
        
        # Initialize tools and memory
        await tool_registry.initialize()
        await memory_manager.initialize()
        await agent_manager.initialize()
        
        # Store managers in app state
        app.state.agent_manager = agent_manager
        app.state.tool_registry = tool_registry
        app.state.memory_manager = memory_manager
        
        logger.info("AI Agents Service initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize AI Agents Service: {e}")
        raise
    finally:
        logger.info("Shutting down AI Agents Service...")
        if agent_manager:
            await agent_manager.cleanup()
        if memory_manager:
            await memory_manager.close()

# Create FastAPI app
app = FastAPI(
    title="AI Agents Service",
    description="LangChain-based autonomous agents with multimodal capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-agents",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Agents Service",
        "version": "1.0.0",
        "docs": "/docs",
        "agents": "/api/v1/agents",
        "tools": "/api/v1/tools"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
        log_level="info"
    )
