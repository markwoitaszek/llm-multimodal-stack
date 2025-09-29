"""
Search Engine API Endpoints
"""
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.models import (
    SearchRequest, SearchResponse, IndexRequest, IndexResponse,
    DeleteRequest, DeleteResponse, HealthResponse, StatsResponse, ErrorResponse
)
from app.search_engine import search_engine
from app.database import db_manager
from app.vector_store import vector_store
from app.embeddings import cached_embedding_service
from app.config import settings

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Search Engine Service",
    description="Advanced search engine with semantic and keyword search capabilities",
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
        
        # Initialize vector store
        await vector_store.initialize()
        logger.info("Vector store initialized")
        
        # Initialize embedding service
        await cached_embedding_service.embedding_service.initialize()
        logger.info("Embedding service initialized")
        
        logger.info("Search Engine Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Search Engine Service: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await db_manager.close()
        await vector_store.close()
        logger.info("Search Engine Service shutdown complete")
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
        ).model_dump()
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database health
        db_healthy = True
        try:
            await db_manager.get_content_count()
        except Exception:
            db_healthy = False
        
        # Check vector store health
        vector_healthy = await vector_store.health_check()
        
        # Check embedding service health
        embedding_healthy = await cached_embedding_service.embedding_service.health_check()
        
        overall_status = "healthy" if all([db_healthy, vector_healthy, embedding_healthy]) else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            dependencies={
                "database": "healthy" if db_healthy else "unhealthy",
                "vector_store": "healthy" if vector_healthy else "unhealthy",
                "embedding_service": "healthy" if embedding_healthy else "unhealthy"
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )


# Search endpoints
@app.post("/api/v1/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Perform search"""
    try:
        result = await search_engine.search(request)
        return result
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@app.post("/api/v1/search/semantic", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """Perform semantic search"""
    try:
        # Override search type to semantic
        request.search_type = "semantic"
        result = await search_engine.search(request)
        return result
        
    except Exception as e:
        logger.error(f"Semantic search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}"
        )


@app.post("/api/v1/search/keyword", response_model=SearchResponse)
async def keyword_search(request: SearchRequest):
    """Perform keyword search"""
    try:
        # Override search type to keyword
        request.search_type = "keyword"
        result = await search_engine.search(request)
        return result
        
    except Exception as e:
        logger.error(f"Keyword search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Keyword search failed: {str(e)}"
        )


@app.post("/api/v1/search/hybrid", response_model=SearchResponse)
async def hybrid_search(request: SearchRequest):
    """Perform hybrid search"""
    try:
        # Override search type to hybrid
        request.search_type = "hybrid"
        result = await search_engine.search(request)
        return result
        
    except Exception as e:
        logger.error(f"Hybrid search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid search failed: {str(e)}"
        )


# Indexing endpoints
@app.post("/api/v1/index", response_model=IndexResponse)
async def index_content(request: IndexRequest, background_tasks: BackgroundTasks):
    """Index content for search"""
    try:
        # Generate embedding if not provided
        embedding = request.embedding
        if not embedding:
            embedding = await cached_embedding_service.generate_embedding(request.content)
        
        # Store in database
        success = await db_manager.create_content(
            content_id=request.content_id,
            content=request.content,
            content_type=request.content_type.value,
            metadata=request.metadata,
            embedding=embedding
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store content in database"
            )
        
        # Store embedding in vector store (background task)
        background_tasks.add_task(
            vector_store.upsert_embedding,
            request.content_id,
            embedding,
            request.metadata
        )
        
        return IndexResponse(
            content_id=request.content_id,
            indexed=True,
            embedding_dimension=len(embedding),
            indexed_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Index content error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}"
        )


@app.get("/api/v1/index/{content_id}")
async def get_indexed_content(content_id: str):
    """Get indexed content by ID"""
    try:
        content = await db_manager.get_content(content_id)
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        return content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get content error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content: {str(e)}"
        )


@app.delete("/api/v1/index/{content_id}", response_model=DeleteResponse)
async def delete_indexed_content(content_id: str, background_tasks: BackgroundTasks):
    """Delete indexed content"""
    try:
        # Delete from database
        db_success = await db_manager.delete_content(content_id)
        
        # Delete from vector store (background task)
        background_tasks.add_task(vector_store.delete_embedding, content_id)
        
        if not db_success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        return DeleteResponse(
            content_id=content_id,
            deleted=True,
            deleted_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete content error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete content: {str(e)}"
        )


# Batch operations
@app.post("/api/v1/index/batch", response_model=List[IndexResponse])
async def batch_index_content(requests: List[IndexRequest], background_tasks: BackgroundTasks):
    """Batch index content"""
    try:
        results = []
        
        for request in requests:
            try:
                # Generate embedding if not provided
                embedding = request.embedding
                if not embedding:
                    embedding = await cached_embedding_service.generate_embedding(request.content)
                
                # Store in database
                success = await db_manager.create_content(
                    content_id=request.content_id,
                    content=request.content,
                    content_type=request.content_type.value,
                    metadata=request.metadata,
                    embedding=embedding
                )
                
                if success:
                    results.append(IndexResponse(
                        content_id=request.content_id,
                        indexed=True,
                        embedding_dimension=len(embedding),
                        indexed_at=datetime.utcnow()
                    ))
                else:
                    results.append(IndexResponse(
                        content_id=request.content_id,
                        indexed=False,
                        indexed_at=datetime.utcnow()
                    ))
                
            except Exception as e:
                logger.error(f"Batch index error for {request.content_id}: {str(e)}")
                results.append(IndexResponse(
                    content_id=request.content_id,
                    indexed=False,
                    indexed_at=datetime.utcnow()
                ))
        
        # Batch store embeddings in vector store (background task)
        embeddings_data = []
        for i, request in enumerate(requests):
            if results[i].indexed and request.embedding:
                embeddings_data.append((request.content_id, request.embedding, request.metadata))
        
        if embeddings_data:
            background_tasks.add_task(
                vector_store.batch_upsert_embeddings,
                embeddings_data
            )
        
        return results
        
    except Exception as e:
        logger.error(f"Batch index content error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch indexing failed: {str(e)}"
        )


# Statistics and monitoring
@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats():
    """Get service statistics"""
    try:
        stats = await search_engine.get_search_stats()
        
        return StatsResponse(
            total_indexed_content=stats.get("total_searches", 0),
            total_searches=stats.get("total_searches", 0),
            cache_hit_rate=stats.get("cache_hit_rate", 0.0),
            average_search_time_ms=stats.get("average_search_time_ms", 0.0),
            active_connections=settings.database_pool_size,
            memory_usage_mb=0.0  # Could be implemented with psutil
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
        search_engine.clear_cache()
        return {"message": "Cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Clear cache error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Search Engine Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }