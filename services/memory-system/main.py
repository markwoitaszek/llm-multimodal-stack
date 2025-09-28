#!/usr/bin/env python3
"""
Memory System Service
Persistent memory management system for AI agents with conversation history,
context retention, and knowledge base integration.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import DatabaseManager
from app.cache import CacheManager
from app.memory_manager import MemoryManager
from app.conversation import ConversationManager
from app.knowledge_base import KnowledgeManager
from app.api import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global managers
db_manager = None
cache_manager = None
memory_manager = None
conversation_manager = None
knowledge_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global db_manager, cache_manager, memory_manager, conversation_manager, knowledge_manager
    
    logger.info("Starting Memory System Service...")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.initialize()
        logger.info("Database manager initialized")
        
        # Initialize cache manager
        cache_manager = CacheManager()
        await cache_manager.initialize()
        logger.info("Cache manager initialized")
        
        # Initialize specialized managers
        conversation_manager = ConversationManager(db_manager, cache_manager)
        knowledge_manager = KnowledgeManager(db_manager, cache_manager)
        memory_manager = MemoryManager(db_manager, cache_manager)
        
        logger.info("Memory managers initialized")
        
        # Store managers in app state
        app.state.db_manager = db_manager
        app.state.cache_manager = cache_manager
        app.state.memory_manager = memory_manager
        app.state.conversation_manager = conversation_manager
        app.state.knowledge_manager = knowledge_manager
        
        logger.info("Memory System Service started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize Memory System Service: {e}")
        raise
    finally:
        logger.info("Shutting down Memory System Service...")
        if db_manager:
            await db_manager.close()
        if cache_manager:
            await cache_manager.close()
        logger.info("Memory System Service shut down")

# Create FastAPI app
app = FastAPI(
    title="Memory System Service",
    description="Persistent memory management system for AI agents with conversation history, context retention, and knowledge base integration",
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
app.include_router(router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Memory System Service",
        "version": "1.0.0",
        "description": "Persistent memory management for AI agents",
        "docs": "/docs",
        "health": "/health"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )