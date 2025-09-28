"""
API routes for the retrieval proxy service
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from .config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    modalities: Optional[List[str]] = Field(default=None, description="Content types to search: text, image, video")
    limit: Optional[int] = Field(default=10, description="Maximum number of results")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")
    score_threshold: Optional[float] = Field(default=None, description="Minimum similarity score")

class SearchResponse(BaseModel):
    session_id: str
    query: str
    modalities: List[str]
    results_count: int
    results: List[Dict[str, Any]]
    context_bundle: Dict[str, Any]
    metadata: Dict[str, Any]

class ContextBundleRequest(BaseModel):
    session_id: str
    format: Optional[str] = Field(default="markdown", description="Output format: markdown, json, plain")

@router.post("/search", response_model=SearchResponse)
async def search_multimodal(request: SearchRequest, req: Request):
    """Perform unified multimodal search with caching"""
    try:
        cache_manager = req.app.state.cache_manager
        retrieval_engine = req.app.state.retrieval_engine
        
        # Check cache first
        cached_results = await cache_manager.get_search_results(
            query=request.query,
            file_type=request.modalities[0] if request.modalities else None,
            limit=request.limit
        )
        
        if cached_results:
            logger.info(f"Returning cached search results for: {request.query}")
            return SearchResponse(**cached_results["results"])
        
        # Perform search if not cached
        result = await retrieval_engine.search(
            query=request.query,
            modalities=request.modalities,
            limit=request.limit,
            filters=request.filters,
            score_threshold=request.score_threshold
        )
        
        # Cache the results
        await cache_manager.set_search_results(
            query=request.query,
            results=result,
            file_type=request.modalities[0] if request.modalities else None,
            limit=request.limit
        )
        
        return SearchResponse(**result)
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/sessions")
async def get_search_sessions(
    limit: int = Query(default=20, description="Number of sessions to retrieve"),
    req: Request = None
):
    """Get recent search sessions"""
    try:
        db_manager = req.app.state.db_manager
        sessions = await db_manager.get_search_sessions(limit=limit)
        
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get search sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context/{session_id}")
async def get_context_bundle(
    session_id: str = Path(..., description="Search session ID"),
    format: str = Query(default="markdown", description="Output format"),
    req: Request = None
):
    """Get context bundle for a search session"""
    try:
        db_manager = req.app.state.db_manager
        
        # Get session from database
        async with db_manager.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT context_bundle, query, created_at
                FROM search_sessions
                WHERE id = $1
            """, session_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Session not found")
        
        context_bundle = row['context_bundle']
        
        if format == "json":
            return context_bundle
        elif format == "plain":
            return {"context": context_bundle.get("unified_context", "")}
        else:  # markdown (default)
            return {"context": context_bundle.get("unified_context", "")}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get context bundle: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/artifacts/image/{document_id}")
async def get_image_artifact(
    document_id: str = Path(..., description="Document ID"),
    req: Request = None
):
    """Get image artifact by document ID"""
    try:
        db_manager = req.app.state.db_manager
        
        # Get image info from database
        async with db_manager.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT i.image_path, i.format, d.filename
                FROM images i
                JOIN documents d ON i.document_id = d.id
                WHERE i.document_id = $1
                LIMIT 1
            """, document_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Image not found")
        
        # In a real implementation, you would stream the image from MinIO
        # For now, return metadata
        return {
            "document_id": document_id,
            "image_path": row['image_path'],
            "format": row['format'],
            "filename": row['filename'],
            "view_url": f"/api/v1/artifacts/image/{document_id}",
            "download_url": f"/api/v1/artifacts/download/{document_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get image artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/artifacts/video/{document_id}")
async def get_video_artifact(
    document_id: str = Path(..., description="Document ID"),
    req: Request = None
):
    """Get video artifact by document ID"""
    try:
        db_manager = req.app.state.db_manager
        
        # Get video info from database
        async with db_manager.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT v.video_path, v.duration_seconds, v.format, d.filename
                FROM videos v
                JOIN documents d ON v.document_id = d.id
                WHERE v.document_id = $1
                LIMIT 1
            """, document_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Video not found")
        
        # In a real implementation, you would stream the video from MinIO
        # For now, return metadata
        return {
            "document_id": document_id,
            "video_path": row['video_path'],
            "duration": row['duration_seconds'],
            "format": row['format'],
            "filename": row['filename'],
            "view_url": f"/api/v1/artifacts/video/{document_id}",
            "download_url": f"/api/v1/artifacts/download/{document_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/artifacts/keyframe/{keyframe_id}")
async def get_keyframe_artifact(
    keyframe_id: str = Path(..., description="Keyframe ID"),
    req: Request = None
):
    """Get keyframe artifact by keyframe ID"""
    try:
        db_manager = req.app.state.db_manager
        
        # Get keyframe info from database
        async with db_manager.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT vk.keyframe_path, vk.timestamp_seconds, v.video_path, d.filename
                FROM video_keyframes vk
                JOIN videos v ON vk.video_id = v.id
                JOIN documents d ON v.document_id = d.id
                WHERE vk.id = $1
            """, keyframe_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Keyframe not found")
        
        # In a real implementation, you would stream the keyframe from MinIO
        # For now, return metadata
        return {
            "keyframe_id": keyframe_id,
            "keyframe_path": row['keyframe_path'],
            "timestamp": row['timestamp_seconds'],
            "video_path": row['video_path'],
            "filename": row['filename'],
            "view_url": f"/api/v1/artifacts/keyframe/{keyframe_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get keyframe artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_system_stats(req: Request):
    """Get system statistics"""
    try:
        db_manager = req.app.state.db_manager
        vector_manager = req.app.state.vector_manager
        
        # Get database stats
        async with db_manager.pool.acquire() as conn:
            db_stats = {}
            
            # Count documents by type
            rows = await conn.fetch("""
                SELECT file_type, COUNT(*) as count
                FROM documents
                GROUP BY file_type
            """)
            db_stats['documents'] = {row['file_type']: row['count'] for row in rows}
            
            # Count total items
            total_docs = await conn.fetchval("SELECT COUNT(*) FROM documents")
            total_chunks = await conn.fetchval("SELECT COUNT(*) FROM text_chunks")
            total_images = await conn.fetchval("SELECT COUNT(*) FROM images")
            total_videos = await conn.fetchval("SELECT COUNT(*) FROM videos")
            total_keyframes = await conn.fetchval("SELECT COUNT(*) FROM video_keyframes")
            
            db_stats['totals'] = {
                'documents': total_docs,
                'text_chunks': total_chunks,
                'images': total_images,
                'videos': total_videos,
                'keyframes': total_keyframes
            }
        
        # Get vector store stats
        vector_stats = vector_manager.get_stats()
        
        return {
            "database": db_stats,
            "vector_store": vector_stats,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_service_status(req: Request):
    """Get service status"""
    try:
        db_manager = req.app.state.db_manager
        vector_manager = req.app.state.vector_manager
        
        # Test database connection
        db_status = "healthy"
        try:
            async with db_manager.pool.acquire() as conn:
                await conn.execute("SELECT 1")
        except:
            db_status = "unhealthy"
        
        # Test vector store connection
        vector_status = "healthy"
        try:
            vector_manager.client.get_collections()
        except:
            vector_status = "unhealthy"
        
        return {
            "service": "retrieval-proxy",
            "status": "healthy" if db_status == "healthy" and vector_status == "healthy" else "degraded",
            "components": {
                "database": db_status,
                "vector_store": vector_status
            },
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        return {
            "service": "retrieval-proxy",
            "status": "unhealthy",
            "error": str(e)
        }

# Cache management endpoints
@router.get("/cache/stats")
async def get_cache_stats(req: Request):
    """Get cache statistics"""
    try:
        cache_manager = req.app.state.cache_manager
        stats = await cache_manager.get_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache/clear")
async def clear_cache(req: Request):
    """Clear all cache entries"""
    try:
        cache_manager = req.app.state.cache_manager
        success = await cache_manager.clear_all_cache()
        if success:
            return {"message": "Cache cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache/search/{pattern}")
async def invalidate_search_cache(pattern: str, req: Request):
    """Invalidate search cache entries matching pattern"""
    try:
        cache_manager = req.app.state.cache_manager
        deleted_count = await cache_manager.invalidate_search_cache(pattern)
        return {
            "message": f"Invalidated {deleted_count} cache entries",
            "pattern": pattern
        }
    except Exception as e:
        logger.error(f"Failed to invalidate search cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

