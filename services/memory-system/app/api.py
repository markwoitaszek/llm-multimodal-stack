"""
Memory System API Endpoints
"""
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.models import (
    MemoryRequest, MemoryResponse, RetrieveRequest, RetrieveResponse,
    ConversationRequest, ConversationResponse, ConsolidateRequest, ConsolidateResponse,
    ContextRequest, ContextResponse, UpdateRequest, DeleteRequest, DeleteResponse,
    HealthResponse, StatsResponse, ErrorResponse
)
from app.memory_manager import memory_manager
from app.database import db_manager
from app.embeddings import cached_embedding_service
from app.config import settings

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Memory System Service",
    description="Advanced memory management system with conversation storage and retrieval",
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


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize database
        await db_manager.initialize()
        logger.info("Database initialized")
        
        # Initialize embedding service
        await cached_embedding_service.embedding_service.initialize()
        logger.info("Embedding service initialized")
        
        logger.info("Memory System Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Memory System Service: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await db_manager.close()
        logger.info("Memory System Service shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            timestamp=datetime.utcnow()
        ).dict()
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database health
        db_healthy = True
        try:
            await db_manager.get_memory_count()
        except Exception:
            db_healthy = False
        
        # Check embedding service health
        embedding_healthy = await cached_embedding_service.embedding_service.health_check()
        
        overall_status = "healthy" if all([db_healthy, embedding_healthy]) else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            dependencies={
                "database": "healthy" if db_healthy else "unhealthy",
                "embedding_service": "healthy" if embedding_healthy else "unhealthy"
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )


# Memory endpoints
@app.post("/api/v1/memories", response_model=MemoryResponse)
async def store_memory(request: MemoryRequest):
    """Store a new memory"""
    try:
        result = await memory_manager.store_memory(request)
        return result
        
    except Exception as e:
        logger.error(f"Memory storage error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory storage failed: {str(e)}"
        )


@app.get("/api/v1/memories/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: str):
    """Get memory by ID"""
    try:
        memory = await db_manager.get_memory(memory_id)
        
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        response = MemoryResponse(
            memory_id=memory["id"],
            content=memory["content"],
            memory_type=memory["memory_type"],
            importance=memory["importance"],
            tags=memory["tags"],
            metadata=memory["metadata"],
            created_at=memory["created_at"],
            updated_at=memory["updated_at"]
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get memory error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory: {str(e)}"
        )


@app.put("/api/v1/memories/{memory_id}", response_model=MemoryResponse)
async def update_memory(memory_id: str, request: UpdateRequest):
    """Update existing memory"""
    try:
        result = await memory_manager.update_memory(memory_id, request)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update memory: {str(e)}"
        )


@app.delete("/api/v1/memories/{memory_id}", response_model=DeleteResponse)
async def delete_memory(memory_id: str):
    """Delete memory"""
    try:
        success = await memory_manager.delete_memory(memory_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        return DeleteResponse(
            memory_id=memory_id,
            deleted=True,
            deleted_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory deletion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete memory: {str(e)}"
        )


@app.post("/api/v1/memories/retrieve", response_model=RetrieveResponse)
async def retrieve_memories(request: RetrieveRequest):
    """Retrieve memories based on query"""
    try:
        result = await memory_manager.retrieve_memories(request)
        return result
        
    except Exception as e:
        logger.error(f"Memory retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory retrieval failed: {str(e)}"
        )


# Conversation endpoints
@app.post("/api/v1/conversations", response_model=ConversationResponse)
async def store_conversation(request: ConversationRequest):
    """Store a new conversation"""
    try:
        result = await memory_manager.store_conversation(request)
        return result
        
    except Exception as e:
        logger.error(f"Conversation storage error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation storage failed: {str(e)}"
        )


@app.get("/api/v1/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get conversation by ID"""
    try:
        result = await memory_manager.get_conversation(conversation_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@app.get("/api/v1/conversations/session/{session_id}")
async def get_conversations_by_session(session_id: str, limit: int = 10):
    """Get conversations by session ID"""
    try:
        conversations = await db_manager.get_conversations_by_session(session_id, limit)
        
        return {
            "session_id": session_id,
            "conversations": conversations,
            "total_count": len(conversations)
        }
        
    except Exception as e:
        logger.error(f"Get conversations by session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )


# Context endpoint
@app.post("/api/v1/context", response_model=ContextResponse)
async def get_context(request: ContextRequest):
    """Get context for a query"""
    try:
        result = await memory_manager.get_context(request)
        return result
        
    except Exception as e:
        logger.error(f"Context retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context retrieval failed: {str(e)}"
        )


# Memory consolidation endpoint
@app.post("/api/v1/memories/consolidate", response_model=ConsolidateResponse)
async def consolidate_memories(request: ConsolidateRequest):
    """Consolidate memories"""
    try:
        result = await memory_manager.consolidate_memories(request)
        return result
        
    except Exception as e:
        logger.error(f"Memory consolidation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory consolidation failed: {str(e)}"
        )


# Batch operations
@app.post("/api/v1/memories/batch", response_model=List[MemoryResponse])
async def batch_store_memories(requests: List[MemoryRequest]):
    """Batch store memories"""
    try:
        results = []
        
        for request in requests:
            try:
                result = await memory_manager.store_memory(request)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch memory storage error: {str(e)}")
                # Continue with other memories
                continue
        
        return results
        
    except Exception as e:
        logger.error(f"Batch memory storage error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch memory storage failed: {str(e)}"
        )


# Statistics and monitoring
@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats():
    """Get service statistics"""
    try:
        stats = await memory_manager.get_memory_stats()
        
        return StatsResponse(
            total_memories=stats.get("total_memories", 0),
            total_conversations=stats.get("total_conversations", 0),
            memory_types_distribution=stats.get("memory_types_distribution", {}),
            importance_distribution=stats.get("importance_distribution", {}),
            average_memory_size=stats.get("average_memory_size", 0.0),
            cache_hit_rate=stats.get("cache_hit_rate", 0.0),
            active_sessions=stats.get("active_sessions", 0)
        )
        
    except Exception as e:
        logger.error(f"Get stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


# Cache management
@app.delete("/api/v1/cache")
async def clear_cache():
    """Clear all caches"""
    try:
        memory_manager.clear_cache()
        cached_embedding_service.clear_cache()
        return {"message": "Cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Clear cache error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


# Cleanup endpoint
@app.post("/api/v1/cleanup")
async def cleanup_old_memories(days: int = None):
    """Clean up old memories"""
    try:
        cleaned_count = await db_manager.cleanup_old_memories(days)
        
        return {
            "message": f"Cleaned up {cleaned_count} old memories",
            "cleaned_count": cleaned_count,
            "retention_days": days or settings.memory_retention_days
        }
        
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup old memories: {str(e)}"
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Memory System Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }