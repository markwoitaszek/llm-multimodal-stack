"""
FastAPI routes for the search engine service
"""
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Path, Request, Depends
from fastapi.responses import JSONResponse

from .config import settings
from .models import (
    SearchRequest, SemanticSearchRequest, HybridSearchRequest, AutocompleteRequest,
    SearchResponse, AutocompleteResponse, SearchSuggestion, FacetedSearchResponse,
    HealthCheck, ErrorResponse, SearchType, ContentType
)
from .search_engine import search_engine
from .cache import cache_manager
from .database import db_manager
from .vector_store import vector_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get session ID
async def get_session_id(request: Request) -> str:
    """Get or create session ID from request"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

@router.post("/api/v1/search/semantic", response_model=SearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    session_id: str = Depends(get_session_id)
):
    """Perform semantic search using vector similarity"""
    try:
        # Validate request
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Create search session
        await db_manager.create_search_session(session_id)
        await db_manager.update_search_session(session_id, request.query)
        
        # Perform search
        response = await search_engine.semantic_search(request, session_id)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/search/hybrid", response_model=SearchResponse)
async def hybrid_search(
    request: HybridSearchRequest,
    session_id: str = Depends(get_session_id)
):
    """Perform hybrid search combining semantic and keyword search"""
    try:
        # Validate request
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Create search session
        await db_manager.create_search_session(session_id)
        await db_manager.update_search_session(session_id, request.query)
        
        # Perform search
        response = await search_engine.hybrid_search(request, session_id)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/search/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_search(request: AutocompleteRequest):
    """Generate autocomplete suggestions for partial query"""
    try:
        start_time = datetime.utcnow()
        
        # Validate request
        if len(request.query.strip()) < 2:
            return AutocompleteResponse(
                query=request.query,
                suggestions=[],
                total_count=0,
                processing_time_ms=0
            )
        
        # Get suggestions
        suggestions = await search_engine.autocomplete_search(
            request.query.strip(),
            request.limit
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return AutocompleteResponse(
            query=request.query,
            suggestions=suggestions,
            total_count=len(suggestions),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Autocomplete search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/search/suggestions", response_model=List[SearchSuggestion])
async def get_search_suggestions(
    query: str = Query(..., description="Search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of suggestions")
):
    """Get search suggestions for a query"""
    try:
        # Validate request
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Get suggestions
        suggestions = await search_engine.get_search_suggestions(query.strip(), limit)
        
        return suggestions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get search suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/search/filters", response_model=FacetedSearchResponse)
async def faceted_search(
    request: SearchRequest,
    session_id: str = Depends(get_session_id)
):
    """Perform faceted search with filter options"""
    try:
        # Validate request
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Perform semantic search first
        semantic_request = SemanticSearchRequest(
            query=request.query,
            content_types=request.content_types,
            limit=request.limit,
            filters=request.filters
        )
        
        search_response = await search_engine.semantic_search(semantic_request, session_id)
        
        # Generate facets (simplified implementation)
        facets = await _generate_facets(search_response.results)
        
        return FacetedSearchResponse(
            query=request.query,
            results=search_response.results,
            total_count=search_response.total_count,
            facets=facets,
            processing_time_ms=search_response.processing_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Faceted search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _generate_facets(results: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Generate facets from search results"""
    facets = {}
    
    # Content type facet
    content_types = {}
    for result in results:
        content_type = result.content_type.value
        content_types[content_type] = content_types.get(content_type, 0) + 1
    
    facets['content_type'] = [
        {'field': 'content_type', 'value': ct, 'count': count, 'label': ct.title()}
        for ct, count in content_types.items()
    ]
    
    # Date facet (simplified)
    if results:
        facets['date_range'] = [
            {'field': 'date_range', 'value': 'last_week', 'count': len(results), 'label': 'Last Week'},
            {'field': 'date_range', 'value': 'last_month', 'count': len(results), 'label': 'Last Month'},
            {'field': 'date_range', 'value': 'last_year', 'count': len(results), 'label': 'Last Year'}
        ]
    
    return facets

@router.get("/api/v1/search/analytics")
async def get_search_analytics(
    start_date: Optional[datetime] = Query(default=None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(default=None, description="End date for analytics"),
    user_id: Optional[str] = Query(default=None, description="User ID filter"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of records")
):
    """Get search analytics data"""
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        analytics = await search_engine.get_search_analytics(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            limit=limit
        )
        
        return {
            "analytics": analytics,
            "count": len(analytics),
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get search analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/search/popular")
async def get_popular_queries(
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of popular queries")
):
    """Get popular search queries"""
    try:
        popular_queries = await search_engine.get_popular_queries(limit)
        
        return {
            "popular_queries": popular_queries,
            "count": len(popular_queries)
        }
        
    except Exception as e:
        logger.error(f"Failed to get popular queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/search/sessions/{session_id}")
async def get_search_session(
    session_id: str = Path(..., description="Session ID")
):
    """Get search session information"""
    try:
        session = await db_manager.get_search_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get search session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/search/user-history")
async def get_user_search_history(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of queries")
):
    """Get user search history"""
    try:
        history = await cache_manager.get_user_search_history(user_id, limit)
        
        return {
            "user_id": user_id,
            "search_history": history or [],
            "count": len(history) if history else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get user search history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/search/stats")
async def get_search_stats():
    """Get search engine statistics"""
    try:
        # Get database stats
        db_stats = await db_manager.get_database_stats()
        
        # Get cache stats
        cache_stats = await cache_manager.get_cache_stats()
        
        # Get vector store stats
        vector_stats = await vector_manager.get_all_collections_info()
        
        return {
            "database": db_stats,
            "cache": cache_stats,
            "vector_store": vector_stats,
            "search_engine": {
                "uptime_seconds": search_engine.get_uptime(),
                "embedding_model": "all-MiniLM-L6-v2"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get search stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        # Check all components
        db_healthy = await db_manager.health_check()
        cache_healthy = await cache_manager.health_check()
        vector_healthy = await vector_manager.health_check()
        search_healthy = await search_engine.health_check()
        
        overall_status = "healthy" if all([
            db_healthy, cache_healthy, vector_healthy, search_healthy
        ]) else "unhealthy"
        
        return HealthCheck(
            service="search-engine",
            status=overall_status,
            version="1.0.0",
            components={
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy",
                "vector_store": "healthy" if vector_healthy else "unhealthy",
                "search_engine": "healthy" if search_healthy else "unhealthy"
            },
            uptime_seconds=search_engine.get_uptime()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            service="search-engine",
            status="unhealthy",
            version="1.0.0",
            components={
                "database": "unknown",
                "cache": "unknown",
                "vector_store": "unknown",
                "search_engine": "unknown"
            },
            uptime_seconds=0
        )

# Cache management endpoints
@router.get("/api/v1/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        stats = await cache_manager.get_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/v1/cache/clear")
async def clear_cache():
    """Clear all cache entries"""
    try:
        success = await cache_manager.clear_all_cache()
        if success:
            return {"message": "Cache cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/v1/cache/search/{pattern}")
async def invalidate_search_cache(pattern: str):
    """Invalidate search cache entries matching pattern"""
    try:
        deleted_count = await cache_manager.invalidate_search_cache(pattern)
        return {
            "message": f"Invalidated {deleted_count} cache entries",
            "pattern": pattern
        }
    except Exception as e:
        logger.error(f"Failed to invalidate search cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Vector store management endpoints
@router.get("/api/v1/vector/collections")
async def get_collections():
    """Get vector store collections information"""
    try:
        collections = await vector_manager.get_all_collections_info()
        return {"collections": collections}
    except Exception as e:
        logger.error(f"Failed to get collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/vector/collections/{content_type}")
async def get_collection_info(
    content_type: str = Path(..., description="Content type")
):
    """Get specific collection information"""
    try:
        if content_type not in [ct.value for ct in ContentType]:
            raise HTTPException(status_code=400, detail="Invalid content type")
        
        content_type_enum = ContentType(content_type)
        info = await vector_manager.get_collection_info(content_type_enum)
        
        if not info:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers - Note: APIRouter doesn't support exception handlers
# These should be handled at the FastAPI app level in main.py