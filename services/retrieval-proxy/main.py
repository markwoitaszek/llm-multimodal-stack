#!/usr/bin/env python3
"""
Retrieval Proxy Service
Provides unified search across text, image, and video content with context bundling
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import DatabaseManager
from app.vector_store import VectorStoreManager
from app.retrieval import RetrievalEngine
from app.api import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global managers
db_manager = None
vector_manager = None
retrieval_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global db_manager, vector_manager, retrieval_engine
    
    logger.info("Starting Retrieval Proxy Service...")
    
    try:
        # Initialize managers
        db_manager = DatabaseManager()
        vector_manager = VectorStoreManager()
        
        # Initialize connections
        await db_manager.initialize()
        await vector_manager.initialize()
        
        # Initialize retrieval engine
        retrieval_engine = RetrievalEngine(db_manager, vector_manager)
        
        # Store managers in app state
        app.state.db_manager = db_manager
        app.state.vector_manager = vector_manager
        app.state.retrieval_engine = retrieval_engine
        
        logger.info("Retrieval Proxy Service initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    finally:
        logger.info("Shutting down Retrieval Proxy Service...")
        if db_manager:
            await db_manager.close()
        if vector_manager:
            await vector_manager.close()

# Create FastAPI app
app = FastAPI(
    title="Retrieval Proxy Service",
    description="Unified search and context bundling for multimodal content",
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
        "service": "retrieval-proxy",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Retrieval Proxy Service",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )

