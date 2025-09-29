"""
Core Search Engine Implementation
"""
import asyncio
import time
import uuid
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from datetime import datetime
import logging

from app.models import SearchRequest, SearchResponse, SearchResult, SearchType, ContentType
from app.database import db_manager
from app.vector_store import vector_store
from app.embeddings import cached_embedding_service
from app.config import settings

logger = logging.getLogger(__name__)


class SearchEngine:
    """Core search engine implementation"""
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = settings.cache_ttl
        self.max_concurrent_searches = settings.max_concurrent_searches
        self._semaphore = asyncio.Semaphore(self.max_concurrent_searches)
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Perform search based on request"""
        start_time = time.time()
        search_id = str(uuid.uuid4())
        
        try:
            # Acquire semaphore for concurrency control
            async with self._semaphore:
                # Check cache first
                if request.use_cache:
                    cached_result = self._get_cached_result(request)
                    if cached_result:
                        cached_result.cached = True
                        return cached_result
                
                # Perform search based on type
                if request.search_type == SearchType.SEMANTIC:
                    results = await self._semantic_search(request)
                elif request.search_type == SearchType.KEYWORD:
                    results = await self._keyword_search(request)
                elif request.search_type == SearchType.HYBRID:
                    results = await self._hybrid_search(request)
                elif request.search_type == SearchType.FILTERED:
                    results = await self._filtered_search(request)
                else:
                    raise ValueError(f"Unsupported search type: {request.search_type}")
                
                # Create response
                execution_time_ms = (time.time() - start_time) * 1000
                response = SearchResponse(
                    query=request.query,
                    search_type=request.search_type,
                    total_results=len(results),
                    results=results,
                    execution_time_ms=execution_time_ms,
                    cached=False,
                    search_id=search_id
                )
                
                # Cache result
                if request.use_cache:
                    self._cache_result(request, response)
                
                # Log search
                await db_manager.log_search(
                    query=request.query,
                    search_type=request.search_type.value,
                    results_count=len(results),
                    execution_time_ms=execution_time_ms,
                    cached=False
                )
                
                return response
                
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Log failed search
            await db_manager.log_search(
                query=request.query,
                search_type=request.search_type.value,
                results_count=0,
                execution_time_ms=execution_time_ms,
                cached=False
            )
            
            raise Exception(f"Search failed: {str(e)}")
    
    async def _semantic_search(self, request: SearchRequest) -> List[SearchResult]:
        """Perform semantic search using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = await cached_embedding_service.generate_embedding(
                request.query, 
                use_cache=request.use_cache
            )
            
            # Search vector store
            vector_results = await vector_store.search_similar(
                query_embedding=query_embedding,
                limit=request.limit,
                filters=self._build_vector_filters(request)
            )
            
            # Get content details from database
            results = []
            for vector_result in vector_results:
                content_id = vector_result["id"]
                content_data = await db_manager.get_content(content_id)
                
                if content_data:
                    # Apply content type filter
                    if request.content_types:
                        content_type = ContentType(content_data["content_type"])
                        if content_type not in request.content_types:
                            continue
                    
                    result = SearchResult(
                        id=content_data["id"],
                        content=content_data["content"],
                        content_type=ContentType(content_data["content_type"]),
                        score=vector_result["score"],
                        metadata=content_data["metadata"] if request.include_metadata else None,
                        created_at=content_data["created_at"],
                        updated_at=content_data["updated_at"]
                    )
                    results.append(result)
            
            return results[:request.limit]
            
        except Exception as e:
            logger.error(f"Semantic search error: {str(e)}")
            return []
    
    async def _keyword_search(self, request: SearchRequest) -> List[SearchResult]:
        """Perform keyword search using full-text search"""
        try:
            # Search database
            db_results = await db_manager.search_content(
                query=request.query,
                content_types=[ct.value for ct in request.content_types] if request.content_types else None,
                limit=request.limit,
                offset=request.offset
            )
            
            # Convert to SearchResult objects
            results = []
            for db_result in db_results:
                result = SearchResult(
                    id=db_result["id"],
                    content=db_result["content"],
                    content_type=ContentType(db_result["content_type"]),
                    score=db_result["score"],
                    metadata=db_result["metadata"] if request.include_metadata else None,
                    created_at=db_result["created_at"],
                    updated_at=db_result["updated_at"]
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Keyword search error: {str(e)}")
            return []
    
    async def _hybrid_search(self, request: SearchRequest) -> List[SearchResult]:
        """Perform hybrid search combining semantic and keyword search"""
        try:
            # Run both searches concurrently
            semantic_task = self._semantic_search(request)
            keyword_task = self._keyword_search(request)
            
            semantic_results, keyword_results = await asyncio.gather(
                semantic_task, keyword_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(semantic_results, Exception):
                logger.error(f"Semantic search failed: {semantic_results}")
                semantic_results = []
            
            if isinstance(keyword_results, Exception):
                logger.error(f"Keyword search failed: {keyword_results}")
                keyword_results = []
            
            # Combine and rank results
            combined_results = self._combine_search_results(
                semantic_results, keyword_results, request.limit
            )
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Hybrid search error: {str(e)}")
            return []
    
    async def _filtered_search(self, request: SearchRequest) -> List[SearchResult]:
        """Perform filtered search with custom filters"""
        try:
            # Start with semantic search
            results = await self._semantic_search(request)
            
            # Apply custom filters
            if request.filters:
                results = self._apply_custom_filters(results, request.filters)
            
            return results[:request.limit]
            
        except Exception as e:
            logger.error(f"Filtered search error: {str(e)}")
            return []
    
    def _combine_search_results(self, semantic_results: List[SearchResult], 
                              keyword_results: List[SearchResult], 
                              limit: int) -> List[SearchResult]:
        """Combine and rank search results"""
        # Create a dictionary to track combined scores
        combined_scores = {}
        
        # Add semantic results with weight 0.7
        for result in semantic_results:
            combined_scores[result.id] = {
                "result": result,
                "semantic_score": result.score,
                "keyword_score": 0.0,
                "combined_score": result.score * 0.7
            }
        
        # Add keyword results with weight 0.3
        for result in keyword_results:
            if result.id in combined_scores:
                # Update existing result
                combined_scores[result.id]["keyword_score"] = result.score
                combined_scores[result.id]["combined_score"] += result.score * 0.3
            else:
                # Add new result
                combined_scores[result.id] = {
                    "result": result,
                    "semantic_score": 0.0,
                    "keyword_score": result.score,
                    "combined_score": result.score * 0.3
                }
        
        # Sort by combined score and return top results
        sorted_results = sorted(
            combined_scores.values(),
            key=lambda x: x["combined_score"],
            reverse=True
        )
        
        # Update scores in results
        final_results = []
        for item in sorted_results[:limit]:
            result = item["result"]
            result.score = item["combined_score"]
            final_results.append(result)
        
        return final_results
    
    def _apply_custom_filters(self, results: List[SearchResult], 
                            filters: Dict[str, Any]) -> List[SearchResult]:
        """Apply custom filters to search results"""
        filtered_results = []
        
        for result in results:
            include_result = True
            
            for filter_key, filter_value in filters.items():
                if filter_key == "created_after":
                    if result.created_at < datetime.fromisoformat(filter_value):
                        include_result = False
                        break
                elif filter_key == "created_before":
                    if result.created_at > datetime.fromisoformat(filter_value):
                        include_result = False
                        break
                elif filter_key == "min_score":
                    if result.score < float(filter_value):
                        include_result = False
                        break
                elif result.content_metadata and filter_key in result.content_metadata:
                    if result.content_metadata[filter_key] != filter_value:
                        include_result = False
                        break
            
            if include_result:
                filtered_results.append(result)
        
        return filtered_results
    
    def _build_vector_filters(self, request: SearchRequest) -> Optional[Dict[str, Any]]:
        """Build filters for vector search"""
        filters = {}
        
        if request.content_types:
            filters["content_type"] = [ct.value for ct in request.content_types]
        
        if request.filters:
            # Add custom filters that are compatible with vector search
            for key, value in request.filters.items():
                if key in ["content_type", "source", "category"]:
                    filters[key] = value
        
        return filters if filters else None
    
    def _get_cached_result(self, request: SearchRequest) -> Optional[SearchResponse]:
        """Get cached search result"""
        cache_key = self._generate_cache_key(request)
        
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            # Check if cache entry is still valid
            if time.time() - cached_item["timestamp"] < self.cache_ttl:
                return cached_item["response"]
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
        
        return None
    
    def _cache_result(self, request: SearchRequest, response: SearchResponse):
        """Cache search result"""
        cache_key = self._generate_cache_key(request)
        
        self.cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        
        # Simple cache size management
        if len(self.cache) > settings.result_cache_size:
            # Remove oldest entries
            oldest_keys = sorted(
                self.cache.keys(),
                key=lambda k: self.cache[k]["timestamp"]
            )[:len(self.cache) - settings.result_cache_size]
            
            for key in oldest_keys:
                del self.cache[key]
    
    def _generate_cache_key(self, request: SearchRequest) -> str:
        """Generate cache key for request"""
        # Create a hashable representation of the request
        key_parts = [
            request.query,
            request.search_type.value,
            request.limit,
            request.offset,
            str(sorted(request.content_types)) if request.content_types else None,
            str(sorted(request.filters.items())) if request.filters else None,
            request.include_metadata
        ]
        
        return str(hash(tuple(key_parts)))
    
    async def get_search_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        try:
            # Get database stats
            db_stats = await db_manager.get_search_stats()
            
            # Get vector store info
            vector_info = await vector_store.get_collection_info()
            
            # Get cache info
            cache_info = cached_embedding_service.get_cache_info()
            
            return {
                "total_searches": db_stats["total_searches"],
                "average_search_time_ms": db_stats["average_execution_time_ms"],
                "cache_hit_rate": db_stats["cache_hit_rate"],
                "vector_store_points": vector_info.get("points_count", 0),
                "embedding_cache_size": cache_info["cache_size"],
                "result_cache_size": len(self.cache)
            }
            
        except Exception as e:
            logger.error(f"Error getting search stats: {str(e)}")
            return {}
    
    def clear_cache(self):
        """Clear all caches"""
        self.cache.clear()
        cached_embedding_service.clear_cache()


# Global search engine instance
search_engine = SearchEngine()