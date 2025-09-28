"""
Core search engine logic for semantic, hybrid, and keyword search
"""
import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import httpx
import numpy as np
from sentence_transformers import SentenceTransformer

from .config import settings
from .models import (
    SearchType, ContentType, SearchRequest, SemanticSearchRequest, 
    HybridSearchRequest, SearchResponse, SearchResult, SearchAnalytics
)
from .vector_store import vector_manager
from .cache import cache_manager
from .query_processor import query_processor
from .database import db_manager

logger = logging.getLogger(__name__)

class SearchEngine:
    """Core search engine implementation"""
    
    def __init__(self):
        self.embedding_model: Optional[SentenceTransformer] = None
        self._start_time = datetime.utcnow()
    
    async def initialize(self):
        """Initialize the search engine"""
        try:
            # Initialize embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Search engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize search engine: {e}")
            raise
    
    async def close(self):
        """Close search engine resources"""
        if self.embedding_model:
            # SentenceTransformer doesn't have explicit cleanup
            self.embedding_model = None
            logger.info("Search engine resources closed")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")
        
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def semantic_search(
        self,
        request: SemanticSearchRequest,
        session_id: Optional[str] = None
    ) -> SearchResponse:
        """Perform semantic search using vector similarity"""
        start_time = time.time()
        
        try:
            # Process query
            processed_query = await query_processor.process_query(
                request.query,
                SearchType.SEMANTIC,
                expand_query=request.expand_query
            )
            
            # Check cache first
            cached_results = await cache_manager.get_search_results(
                query=request.query,
                search_type=SearchType.SEMANTIC.value,
                content_types=[ct.value for ct in request.content_types] if request.content_types else None,
                limit=request.limit,
                filters=request.filters
            )
            
            if cached_results:
                logger.info(f"Returning cached semantic search results for: {request.query}")
                return SearchResponse(**cached_results['results'])
            
            # Generate query embedding
            query_embedding = self._generate_embedding(processed_query['corrected_query'])
            
            # Perform vector search
            search_results = []
            content_types = request.content_types or [ContentType.TEXT, ContentType.IMAGE, ContentType.VIDEO]
            
            for content_type in content_types:
                results = await vector_manager.search_semantic(
                    query_vector=query_embedding,
                    content_type=content_type,
                    limit=request.limit,
                    score_threshold=request.similarity_threshold,
                    filters=request.filters
                )
                search_results.extend(results)
            
            # Sort by score and limit results
            search_results.sort(key=lambda x: x['score'], reverse=True)
            search_results = search_results[:request.limit]
            
            # Convert to SearchResult objects
            results = []
            for result in search_results:
                results.append(SearchResult(
                    id=result['id'],
                    title=result['payload'].get('title', 'Untitled'),
                    content=result['payload'].get('content', ''),
                    content_type=ContentType(result['content_type']),
                    score=result['score'],
                    metadata=result['payload'],
                    url=result['payload'].get('url'),
                    created_at=result['payload'].get('created_at'),
                    updated_at=result['payload'].get('updated_at')
                ))
            
            processing_time = (time.time() - start_time) * 1000
            
            # Create response
            response = SearchResponse(
                query=request.query,
                search_type=SearchType.SEMANTIC,
                results=results,
                total_count=len(results),
                limit=request.limit,
                offset=request.offset,
                processing_time_ms=processing_time,
                suggestions=await query_processor.generate_search_suggestions(request.query),
                filters_applied=request.filters or {},
                metadata={
                    'processed_query': processed_query,
                    'embedding_model': 'all-MiniLM-L6-v2',
                    'similarity_threshold': request.similarity_threshold
                }
            )
            
            # Cache results
            await cache_manager.set_search_results(
                query=request.query,
                search_type=SearchType.SEMANTIC.value,
                results=response.dict(),
                content_types=[ct.value for ct in request.content_types] if request.content_types else None,
                limit=request.limit,
                filters=request.filters
            )
            
            # Log analytics
            await self._log_search_analytics(
                request.query,
                SearchType.SEMANTIC,
                len(results),
                processing_time,
                session_id,
                request.filters
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise
    
    async def hybrid_search(
        self,
        request: HybridSearchRequest,
        session_id: Optional[str] = None
    ) -> SearchResponse:
        """Perform hybrid search combining semantic and keyword search"""
        start_time = time.time()
        
        try:
            # Process query
            processed_query = await query_processor.process_query(
                request.query,
                SearchType.HYBRID
            )
            
            # Check cache first
            cached_results = await cache_manager.get_search_results(
                query=request.query,
                search_type=SearchType.HYBRID.value,
                content_types=[ct.value for ct in request.content_types] if request.content_types else None,
                limit=request.limit,
                filters=request.filters
            )
            
            if cached_results:
                logger.info(f"Returning cached hybrid search results for: {request.query}")
                return SearchResponse(**cached_results['results'])
            
            # Perform semantic search
            semantic_request = SemanticSearchRequest(
                query=request.query,
                content_types=request.content_types,
                limit=request.limit,
                filters=request.filters,
                similarity_threshold=request.similarity_threshold
            )
            semantic_response = await self.semantic_search(semantic_request, session_id)
            
            # Perform keyword search (simplified implementation)
            keyword_results = await self._keyword_search(
                request.query,
                request.content_types or [ContentType.TEXT, ContentType.IMAGE, ContentType.VIDEO],
                request.limit,
                request.filters
            )
            
            # Fuse results using reciprocal rank fusion
            fused_results = self._fuse_results(
                semantic_response.results,
                keyword_results,
                request.semantic_weight,
                request.keyword_weight,
                request.fusion_method
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Create response
            response = SearchResponse(
                query=request.query,
                search_type=SearchType.HYBRID,
                results=fused_results[:request.limit],
                total_count=len(fused_results),
                limit=request.limit,
                offset=request.offset,
                processing_time_ms=processing_time,
                suggestions=await query_processor.generate_search_suggestions(request.query),
                filters_applied=request.filters or {},
                metadata={
                    'processed_query': processed_query,
                    'semantic_weight': request.semantic_weight,
                    'keyword_weight': request.keyword_weight,
                    'fusion_method': request.fusion_method,
                    'semantic_results_count': len(semantic_response.results),
                    'keyword_results_count': len(keyword_results)
                }
            )
            
            # Cache results
            await cache_manager.set_search_results(
                query=request.query,
                search_type=SearchType.HYBRID.value,
                results=response.dict(),
                content_types=[ct.value for ct in request.content_types] if request.content_types else None,
                limit=request.limit,
                filters=request.filters
            )
            
            # Log analytics
            await self._log_search_analytics(
                request.query,
                SearchType.HYBRID,
                len(fused_results),
                processing_time,
                session_id,
                request.filters
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise
    
    async def _keyword_search(
        self,
        query: str,
        content_types: List[ContentType],
        limit: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Perform keyword-based search (simplified implementation)"""
        try:
            # This is a simplified keyword search implementation
            # In a real system, you would use a full-text search engine like Elasticsearch
            
            # For now, we'll use a basic text matching approach
            # This would typically involve querying a full-text search index
            
            results = []
            
            # Simulate keyword search results
            # In practice, this would query a full-text search index
            for content_type in content_types:
                # This is a placeholder - real implementation would search text indices
                # and return actual results based on keyword matching
                pass
            
            return results
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    def _fuse_results(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        semantic_weight: float,
        keyword_weight: float,
        fusion_method: str
    ) -> List[SearchResult]:
        """Fuse semantic and keyword search results"""
        if fusion_method == "rrf":
            return self._reciprocal_rank_fusion(semantic_results, keyword_results)
        elif fusion_method == "weighted":
            return self._weighted_fusion(semantic_results, keyword_results, semantic_weight, keyword_weight)
        else:
            # Default to RRF
            return self._reciprocal_rank_fusion(semantic_results, keyword_results)
    
    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        k: int = 60
    ) -> List[SearchResult]:
        """Reciprocal Rank Fusion algorithm"""
        scores = {}
        
        # Add semantic results
        for rank, result in enumerate(semantic_results):
            score = 1.0 / (k + rank + 1)
            if result.id in scores:
                scores[result.id]['score'] += score
            else:
                scores[result.id] = {'result': result, 'score': score}
        
        # Add keyword results
        for rank, result in enumerate(keyword_results):
            score = 1.0 / (k + rank + 1)
            if result.id in scores:
                scores[result.id]['score'] += score
            else:
                scores[result.id] = {'result': result, 'score': score}
        
        # Sort by combined score
        fused_results = []
        for item in sorted(scores.values(), key=lambda x: x['score'], reverse=True):
            result = item['result']
            result.score = item['score']
            fused_results.append(result)
        
        return fused_results
    
    def _weighted_fusion(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[SearchResult]:
        """Weighted fusion of results"""
        scores = {}
        
        # Normalize semantic scores
        if semantic_results:
            max_semantic_score = max(result.score for result in semantic_results)
            for result in semantic_results:
                normalized_score = result.score / max_semantic_score if max_semantic_score > 0 else 0
                weighted_score = normalized_score * semantic_weight
                scores[result.id] = {'result': result, 'score': weighted_score}
        
        # Normalize keyword scores
        if keyword_results:
            max_keyword_score = max(result.score for result in keyword_results)
            for result in keyword_results:
                normalized_score = result.score / max_keyword_score if max_keyword_score > 0 else 0
                weighted_score = normalized_score * keyword_weight
                if result.id in scores:
                    scores[result.id]['score'] += weighted_score
                else:
                    scores[result.id] = {'result': result, 'score': weighted_score}
        
        # Sort by combined score
        fused_results = []
        for item in sorted(scores.values(), key=lambda x: x['score'], reverse=True):
            result = item['result']
            result.score = item['score']
            fused_results.append(result)
        
        return fused_results
    
    async def autocomplete_search(
        self,
        partial_query: str,
        limit: int = 10
    ) -> List[str]:
        """Generate autocomplete suggestions"""
        try:
            # Check cache first
            cached_suggestions = await cache_manager.get_autocomplete_suggestions(
                partial_query, limit
            )
            
            if cached_suggestions:
                return cached_suggestions
            
            # Generate suggestions
            suggestions = await query_processor.generate_autocomplete_suggestions(
                partial_query, limit
            )
            
            # Cache suggestions
            await cache_manager.set_autocomplete_suggestions(
                partial_query, suggestions, limit
            )
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Autocomplete search failed: {e}")
            return []
    
    async def get_search_suggestions(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get search suggestions for a query"""
        try:
            # Check cache first
            cached_suggestions = await cache_manager.get_search_suggestions(query, limit)
            
            if cached_suggestions:
                return cached_suggestions
            
            # Generate suggestions
            suggestions = await query_processor.generate_search_suggestions(query, limit)
            
            # Convert to dict format for caching
            suggestions_dict = [suggestion.dict() for suggestion in suggestions]
            
            # Cache suggestions
            await cache_manager.set_search_suggestions(query, suggestions_dict, limit)
            
            return suggestions_dict
            
        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []
    
    async def _log_search_analytics(
        self,
        query: str,
        search_type: SearchType,
        results_count: int,
        processing_time_ms: float,
        session_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ):
        """Log search analytics"""
        try:
            analytics = SearchAnalytics(
                query=query,
                search_type=search_type,
                results_count=results_count,
                processing_time_ms=processing_time_ms,
                session_id=session_id,
                filters=filters
            )
            
            await db_manager.log_search_analytics(analytics)
            
        except Exception as e:
            logger.error(f"Failed to log search analytics: {e}")
    
    async def get_search_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get search analytics data"""
        return await db_manager.get_search_analytics(start_date, end_date, user_id, limit)
    
    async def get_popular_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get popular search queries"""
        return await db_manager.get_popular_queries(limit)
    
    async def health_check(self) -> bool:
        """Check search engine health"""
        try:
            # Check embedding model
            if not self.embedding_model:
                return False
            
            # Test embedding generation
            test_embedding = self._generate_embedding("test query")
            if not test_embedding or len(test_embedding) == 0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Search engine health check failed: {e}")
            return False
    
    def get_uptime(self) -> float:
        """Get service uptime in seconds"""
        return (datetime.utcnow() - self._start_time).total_seconds()

# Global search engine instance
search_engine = SearchEngine()