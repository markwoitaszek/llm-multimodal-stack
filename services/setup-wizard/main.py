#!/usr/bin/env python3
"""
Setup Wizard Service
Provides interactive setup wizard and tutorials for the Multimodal LLM Stack
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Setup Wizard Service...")
    
    try:
        logger.info("Setup Wizard Service initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    finally:
        logger.info("Shutting down Setup Wizard Service...")


# Create FastAPI app
app = FastAPI(
    title="Setup Wizard Service",
    description="Interactive setup wizard and tutorials for Multimodal LLM Stack",
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

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Setup Wizard",
        "version": "1.0.0",
        "description": "Interactive setup wizard and tutorials for Multimodal LLM Stack"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
