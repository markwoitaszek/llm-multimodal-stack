#!/usr/bin/env python3
"""
Multimodal Worker Service
Handles image embeddings, captioning, video transcription, and keyframe extraction
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import ModelManager
from app.database import DatabaseManager
from app.storage import StorageManager
from app.processors import (
    ImageProcessor,
    VideoProcessor,
    TextProcessor,
)
from app.api import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global managers
model_manager = None
db_manager = None
storage_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global model_manager, db_manager, storage_manager
    
    logger.info("Starting Multimodal Worker Service...")
    
    try:
        # Initialize managers
        model_manager = ModelManager()
        db_manager = DatabaseManager()
        storage_manager = StorageManager()
        
        # Load models
        await model_manager.load_models()
        logger.info("Models loaded successfully")
        
        # Initialize database connection
        await db_manager.initialize()
        logger.info("Database connection established")
        
        # Initialize storage
        await storage_manager.initialize()
        logger.info("Storage initialized")
        
        # Store managers in app state
        app.state.model_manager = model_manager
        app.state.db_manager = db_manager
        app.state.storage_manager = storage_manager
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    finally:
        logger.info("Shutting down Multimodal Worker Service...")
        if model_manager:
            await model_manager.cleanup()
        if db_manager:
            await db_manager.close()
        if storage_manager:
            await storage_manager.close()

# Create FastAPI app
app = FastAPI(
    title="Multimodal Worker Service",
    description="Image, video, and text processing service with embeddings and captioning",
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
        "service": "multimodal-worker",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Multimodal Worker Service",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )

