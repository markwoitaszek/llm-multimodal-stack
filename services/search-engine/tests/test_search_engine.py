"""
Search Engine Core Logic Tests
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

from app.models import SearchRequest, SearchType, ContentType, SearchResult
from app.search_engine import SearchEngine
from app.database import db_manager
from app.vector_store import vector_store
from app.embeddings import cached_embedding_service


class TestSearchEngine:
    """Test Search Engine core functionality"""
    
    @pytest.fixture
    def search_engine_instance(self):
        """Create search engine instance for testing"""
        return SearchEngine()
    
    @pytest.fixture
    def mock_search_request(self):
        """Mock search request"""
        return SearchRequest(
            query="test search query",
            search_type=SearchType.HYBRID,
            limit=10,
            content_types=[ContentType.TEXT]
        )
    
    @pytest.fixture
    def mock_search_results(self):
        """Mock search results"""
        return [
            SearchResult(
                id="test_1",
                content="Test content 1",
                content_type=ContentType.TEXT,
                score=0.95,
                metadata={"source": "test"},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            SearchResult(
                id="test_2",
                content="Test content 2",
                content_type=ContentType.TEXT,
                score=0.87,
                metadata={"source": "test"},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
    
    @pytest.mark.asyncio
    async def test_search_semantic(self, search_engine_instance, mock_search_request):
        """Test semantic search"""
        # Mock dependencies
        with patch.object(cached_embedding_service, 'generate_embedding') as mock_embedding, \
             patch.object(vector_store, 'search_similar') as mock_vector_search, \
             patch.object(db_manager, 'get_content') as mock_get_content, \
             patch.object(db_manager, 'log_search') as mock_log:
            
            # Setup mocks
            mock_embedding.return_value = [0.1] * 384
            mock_vector_search.return_value = [
                {"id": "test_1", "score": 0.95, "metadata": {"content_type": "text"}}
            ]
            mock_get_content.return_value = {
                "id": "test_1",
                "content": "Test content",
                "content_type": "text",
                "metadata": {"source": "test"},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            mock_log.return_value = True
            
            # Set search type to semantic
            mock_search_request.search_type = SearchType.SEMANTIC
            
            # Execute search
            result = await search_engine_instance.search(mock_search_request)
            
            # Verify results
            assert result.query == "test search query"
            assert result.search_type == SearchType.SEMANTIC
            assert len(result.results) == 1
            assert result.results[0].id == "test_1"
            assert result.results[0].score == 0.95
            
            # Verify mocks were called
            mock_embedding.assert_called_once()
            mock_vector_search.assert_called_once()
            mock_get_content.assert_called_once()
            mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_keyword(self, search_engine_instance, mock_search_request):
        """Test keyword search"""
        with patch.object(db_manager, 'search_content') as mock_search_content, \
             patch.object(db_manager, 'log_search') as mock_log:
            
            # Setup mocks
            mock_search_content.return_value = [
                {
                    "id": "test_1",
                    "content": "Test content",
                    "content_type": "text",
                    "metadata": {"source": "test"},
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "score": 0.85
                }
            ]
            mock_log.return_value = True
            
            # Set search type to keyword
            mock_search_request.search_type = SearchType.KEYWORD
            
            # Execute search
            result = await search_engine_instance.search(mock_search_request)
            
            # Verify results
            assert result.search_type == SearchType.KEYWORD
            assert len(result.results) == 1
            assert result.results[0].id == "test_1"
            assert result.results[0].score == 0.85
            
            # Verify mocks were called
            mock_search_content.assert_called_once()
            mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_hybrid(self, search_engine_instance, mock_search_request):
        """Test hybrid search"""
        with patch.object(search_engine_instance, '_semantic_search') as mock_semantic, \
             patch.object(search_engine_instance, '_keyword_search') as mock_keyword, \
             patch.object(db_manager, 'log_search') as mock_log:
            
            # Setup mocks
            semantic_results = [
                SearchResult(
                    id="semantic_1",
                    content="Semantic result",
                    content_type=ContentType.TEXT,
                    score=0.9,
                    metadata={"source": "semantic"},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            ]
            
            keyword_results = [
                SearchResult(
                    id="keyword_1",
                    content="Keyword result",
                    content_type=ContentType.TEXT,
                    score=0.8,
                    metadata={"source": "keyword"},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            ]
            
            mock_semantic.return_value = semantic_results
            mock_keyword.return_value = keyword_results
            mock_log.return_value = True
            
            # Set search type to hybrid
            mock_search_request.search_type = SearchType.HYBRID
            
            # Execute search
            result = await search_engine_instance.search(mock_search_request)
            
            # Verify results
            assert result.search_type == SearchType.HYBRID
            assert len(result.results) == 2  # Combined results
            
            # Verify mocks were called
            mock_semantic.assert_called_once()
            mock_keyword.assert_called_once()
            mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_filtered(self, search_engine_instance, mock_search_request):
        """Test filtered search"""
        with patch.object(search_engine_instance, '_semantic_search') as mock_semantic, \
             patch.object(search_engine_instance, '_apply_custom_filters') as mock_filters, \
             patch.object(db_manager, 'log_search') as mock_log:
            
            # Setup mocks
            semantic_results = [
                SearchResult(
                    id="test_1",
                    content="Test content",
                    content_type=ContentType.TEXT,
                    score=0.9,
                    metadata={"source": "test"},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            ]
            
            filtered_results = [
                SearchResult(
                    id="test_1",
                    content="Test content",
                    content_type=ContentType.TEXT,
                    score=0.9,
                    metadata={"source": "test"},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            ]
            
            mock_semantic.return_value = semantic_results
            mock_filters.return_value = filtered_results
            mock_log.return_value = True
            
            # Set search type to filtered and add filters
            mock_search_request.search_type = SearchType.FILTERED
            mock_search_request.filters = {"min_score": 0.5}
            
            # Execute search
            result = await search_engine_instance.search(mock_search_request)
            
            # Verify results
            assert result.search_type == SearchType.FILTERED
            assert len(result.results) == 1
            
            # Verify mocks were called
            mock_semantic.assert_called_once()
            mock_filters.assert_called_once()
            mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_with_cache(self, search_engine_instance, mock_search_request):
        """Test search with caching"""
        # First search - should not be cached
        with patch.object(search_engine_instance, '_semantic_search') as mock_semantic, \
             patch.object(db_manager, 'log_search') as mock_log:
            
            mock_semantic.return_value = []
            mock_log.return_value = True
            
            result1 = await search_engine_instance.search(mock_search_request)
            assert result1.cached is False
            mock_semantic.assert_called_once()
        
        # Second search with same parameters - should be cached
        with patch.object(search_engine_instance, '_semantic_search') as mock_semantic:
            mock_semantic.return_value = []
            
            result2 = await search_engine_instance.search(mock_search_request)
            assert result2.cached is True
            mock_semantic.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, search_engine_instance, mock_search_request):
        """Test search error handling"""
        with patch.object(search_engine_instance, '_semantic_search', 
                         side_effect=Exception("Search error")), \
             patch.object(db_manager, 'log_search') as mock_log:
            
            mock_log.return_value = True
            
            with pytest.raises(Exception, match="Search failed"):
                await search_engine_instance.search(mock_search_request)
            
            # Verify error was logged
            mock_log.assert_called_once()
    
    def test_combine_search_results(self, search_engine_instance):
        """Test combining search results"""
        semantic_results = [
            SearchResult(
                id="shared",
                content="Shared content",
                content_type=ContentType.TEXT,
                score=0.9,
                metadata={"source": "semantic"},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            SearchResult(
                id="semantic_only",
                content="Semantic only content",
                content_type=ContentType.TEXT,
                score=0.8,
                metadata={"source": "semantic"},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        keyword_results = [
            SearchResult(
                id="shared",
                content="Shared content",
                content_type=ContentType.TEXT,
                score=0.7,
                metadata={"source": "keyword"},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            SearchResult(
                id="keyword_only",
                content="Keyword only content",
                content_type=ContentType.TEXT,
                score=0.6,
                metadata={"source": "keyword"},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        combined = search_engine_instance._combine_search_results(
            semantic_results, keyword_results, 10
        )
        
        # Should have 3 unique results
        assert len(combined) == 3
        
        # Shared result should have combined score
        shared_result = next(r for r in combined if r.id == "shared")
        expected_score = 0.9 * 0.7 + 0.7 * 0.3  # Weighted combination
        assert abs(shared_result.score - expected_score) < 0.01
        
        # Results should be sorted by combined score
        assert combined[0].score >= combined[1].score >= combined[2].score
    
    def test_apply_custom_filters(self, search_engine_instance):
        """Test applying custom filters"""
        results = [
            SearchResult(
                id="test_1",
                content="Test content 1",
                content_type=ContentType.TEXT,
                score=0.9,
                metadata={"category": "important"},
                created_at=datetime(2023, 1, 1),
                updated_at=datetime.utcnow()
            ),
            SearchResult(
                id="test_2",
                content="Test content 2",
                content_type=ContentType.TEXT,
                score=0.5,
                metadata={"category": "normal"},
                created_at=datetime(2023, 6, 1),
                updated_at=datetime.utcnow()
            )
        ]
        
        filters = {
            "min_score": 0.7,
            "category": "important"
        }
        
        filtered = search_engine_instance._apply_custom_filters(results, filters)
        
        # Should only include high-scoring important content
        assert len(filtered) == 1
        assert filtered[0].id == "test_1"
    
    def test_build_vector_filters(self, search_engine_instance):
        """Test building vector filters"""
        request = SearchRequest(
            query="test",
            content_types=[ContentType.TEXT, ContentType.IMAGE],
            filters={"source": "test", "category": "sample"}
        )
        
        filters = search_engine_instance._build_vector_filters(request)
        
        assert filters is not None
        assert "content_type" in filters
        assert set(filters["content_type"]) == {"text", "image"}
        assert filters["source"] == "test"
        assert filters["category"] == "sample"
    
    @pytest.mark.asyncio
    async def test_get_search_stats(self, search_engine_instance):
        """Test getting search statistics"""
        with patch.object(db_manager, 'get_search_stats') as mock_db_stats, \
             patch.object(vector_store, 'get_collection_info') as mock_vector_info, \
             patch.object(cached_embedding_service, 'get_cache_info') as mock_cache_info:
            
            # Setup mocks
            mock_db_stats.return_value = {
                "total_searches": 100,
                "average_execution_time_ms": 50.0,
                "cache_hit_rate": 0.8
            }
            
            mock_vector_info.return_value = {
                "points_count": 1000,
                "status": "green"
            }
            
            mock_cache_info.return_value = {
                "cache_size": 50
            }
            
            stats = await search_engine_instance.get_search_stats()
            
            assert stats["total_searches"] == 100
            assert stats["average_search_time_ms"] == 50.0
            assert stats["cache_hit_rate"] == 0.8
            assert stats["vector_store_points"] == 1000
            assert stats["embedding_cache_size"] == 50
    
    def test_clear_cache(self, search_engine_instance):
        """Test clearing cache"""
        # Add some items to cache
        search_engine_instance.cache["test_key"] = {
            "response": "test_response",
            "timestamp": 1234567890
        }
        
        assert len(search_engine_instance.cache) == 1
        
        # Clear cache
        search_engine_instance.clear_cache()
        
        assert len(search_engine_instance.cache) == 0


class TestSearchEngineConcurrency:
    """Test search engine concurrency and performance"""
    
    @pytest.mark.asyncio
    async def test_concurrent_searches(self):
        """Test multiple concurrent searches"""
        search_engine = SearchEngine()
        
        # Create multiple search requests
        requests = [
            SearchRequest(
                query=f"concurrent test {i}",
                search_type=SearchType.SEMANTIC,
                limit=5
            )
            for i in range(10)
        ]
        
        # Mock the search method to avoid actual dependencies
        with patch.object(search_engine, '_semantic_search') as mock_search:
            mock_search.return_value = []
            
            # Execute searches concurrently
            tasks = [search_engine.search(request) for request in requests]
            results = await asyncio.gather(*tasks)
            
            # All searches should complete
            assert len(results) == 10
            for result in results:
                assert result.query.startswith("concurrent test")
    
    @pytest.mark.asyncio
    async def test_semaphore_limit(self):
        """Test semaphore limits concurrent searches"""
        search_engine = SearchEngine()
        
        # Create more requests than the semaphore limit
        requests = [
            SearchRequest(
                query=f"semaphore test {i}",
                search_type=SearchType.SEMANTIC,
                limit=5
            )
            for i in range(20)  # More than max_concurrent_searches
        ]
        
        with patch.object(search_engine, '_semantic_search') as mock_search:
            mock_search.return_value = []
            
            # Execute searches
            tasks = [search_engine.search(request) for request in requests]
            results = await asyncio.gather(*tasks)
            
            # All should complete despite semaphore limit
            assert len(results) == 20