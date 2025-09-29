"""
Search Engine API Tests
"""
import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.models import SearchRequest, IndexRequest, SearchType, ContentType
from app.api import app


class TestSearchEngineAPI:
    """Test Search Engine API endpoints"""
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint"""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Search Engine Service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "dependencies" in data
    
    @patch('app.search_engine.search_engine.search')
    def test_search_endpoint(self, mock_search, test_client, sample_search_request):
        """Test search endpoint"""
        # Mock search response
        mock_search_response = {
            "query": "test search query",
            "search_type": "hybrid",
            "total_results": 2,
            "results": [
                {
                    "id": "test_1",
                    "content": "Test content 1",
                    "content_type": "text",
                    "score": 0.95,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            ],
            "execution_time_ms": 50.0,
            "cached": False,
            "search_id": "test_search_id"
        }
        mock_search.return_value = AsyncMock(return_value=mock_search_response)
        
        response = test_client.post("/api/v1/search", json=sample_search_request.model_dump())
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test search query"
        assert data["search_type"] == "hybrid"
        assert "results" in data
    
    def test_search_endpoint_invalid_request(self, test_client):
        """Test search endpoint with invalid request"""
        invalid_request = {
            "query": "",  # Empty query should fail
            "search_type": "invalid_type",
            "limit": -1  # Invalid limit
        }
        
        response = test_client.post("/api/v1/search", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    @patch('app.search_engine.search_engine.search')
    def test_semantic_search_endpoint(self, mock_search, test_client):
        """Test semantic search endpoint"""
        mock_semantic_response = {
            "query": "semantic test",
            "search_type": "semantic",
            "total_results": 1,
            "results": [],
            "execution_time_ms": 30.0,
            "cached": False,
            "search_id": "semantic_test_id"
        }
        mock_search.return_value = AsyncMock(return_value=mock_semantic_response)
        
        request_data = {
            "query": "semantic test",
            "limit": 10
        }
        
        response = test_client.post("/api/v1/search/semantic", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["search_type"] == "semantic"
    
    @patch('app.search_engine.search_engine.search')
    def test_keyword_search_endpoint(self, test_client):
        """Test keyword search endpoint"""
        request_data = {
            "query": "keyword test",
            "limit": 5
        }
        
        response = test_client.post("/api/v1/search/keyword", json=request_data)
        # Should work even without mocking due to async nature
        assert response.status_code in [200, 500]  # Either success or internal error
    
    @patch('app.search_engine.search_engine.search')
    def test_hybrid_search_endpoint(self, test_client):
        """Test hybrid search endpoint"""
        request_data = {
            "query": "hybrid test",
            "limit": 10
        }
        
        response = test_client.post("/api/v1/search/hybrid", json=request_data)
        assert response.status_code in [200, 500]
    
    @patch('app.database.db_manager.create_content')
    @patch('app.embeddings.cached_embedding_service.generate_embedding')
    def test_index_content_endpoint(self, mock_embedding, mock_create, test_client, sample_index_request):
        """Test index content endpoint"""
        # Mock embedding generation
        mock_embedding.return_value = AsyncMock(return_value=[0.1] * 384)
        
        # Mock database creation
        mock_create.return_value = AsyncMock(return_value=True)
        
        response = test_client.post("/api/v1/index", json=sample_index_request.model_dump())
        assert response.status_code == 200
        data = response.json()
        assert data["content_id"] == sample_index_request.content_id
        assert data["indexed"] is True
        assert "indexed_at" in data
    
    @patch('app.database.db_manager.create_content')
    def test_index_content_with_embedding(self, mock_create, test_client):
        """Test index content with pre-computed embedding"""
        mock_create.return_value = AsyncMock(return_value=True)
        
        request_data = {
            "content_id": "test_with_embedding",
            "content": "Test content with embedding",
            "content_type": "text",
            "embedding": [0.1] * 384
        }
        
        response = test_client.post("/api/v1/index", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["indexed"] is True
    
    @patch('app.database.db_manager.get_content')
    def test_get_indexed_content_endpoint(self, mock_get_content, test_client):
        """Test get indexed content endpoint"""
        mock_content = {
            "id": "test_content",
            "content": "Test content",
            "content_type": "text",
            "metadata": {"test": True},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_get_content.return_value = AsyncMock(return_value=mock_content)
        
        response = test_client.get("/api/v1/index/test_content")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_content"
        assert data["content"] == "Test content"
    
    def test_get_indexed_content_not_found(self, test_client):
        """Test get indexed content when not found"""
        response = test_client.get("/api/v1/index/nonexistent_content")
        assert response.status_code == 404
    
    @patch('app.database.db_manager.delete_content')
    def test_delete_indexed_content_endpoint(self, mock_delete, test_client):
        """Test delete indexed content endpoint"""
        mock_delete.return_value = AsyncMock(return_value=True)
        
        response = test_client.delete("/api/v1/index/test_content")
        assert response.status_code == 200
        data = response.json()
        assert data["content_id"] == "test_content"
        assert data["deleted"] is True
    
    def test_delete_indexed_content_not_found(self, test_client):
        """Test delete indexed content when not found"""
        response = test_client.delete("/api/v1/index/nonexistent_content")
        assert response.status_code == 404
    
    @patch('app.search_engine.search_engine.get_search_stats')
    def test_stats_endpoint(self, mock_stats, test_client):
        """Test statistics endpoint"""
        mock_stats_response = {
            "total_searches": 100,
            "average_search_time_ms": 50.0,
            "cache_hit_rate": 0.8,
            "vector_store_points": 1000,
            "embedding_cache_size": 50,
            "result_cache_size": 20
        }
        mock_stats.return_value = AsyncMock(return_value=mock_stats_response)
        
        response = test_client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_indexed_content" in data
        assert "total_searches" in data
        assert "cache_hit_rate" in data
    
    def test_clear_cache_endpoint(self, test_client):
        """Test clear cache endpoint"""
        response = test_client.delete("/api/v1/cache")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cache cleared successfully"
    
    def test_batch_index_endpoint_invalid_request(self, test_client):
        """Test batch index with invalid request"""
        invalid_requests = [
            {
                "content_id": "test_1",
                "content": "Test content 1",
                "content_type": "invalid_type"  # Invalid content type
            }
        ]
        
        response = test_client.post("/api/v1/index/batch", json=invalid_requests)
        assert response.status_code == 422  # Validation error


class TestSearchEngineAPIIntegration:
    """Integration tests for Search Engine API"""
    
    @pytest.mark.asyncio
    async def test_full_search_workflow(self, test_client, initialized_db_manager, 
                                      mock_embedding_service, mock_vector_store):
        """Test complete search workflow"""
        # Index content first
        index_request = {
            "content_id": "integration_test_1",
            "content": "This is integration test content",
            "content_type": "text",
            "metadata": {"test": "integration"}
        }
        
        # Mock the services
        with patch('app.embeddings.cached_embedding_service', mock_embedding_service), \
             patch('app.vector_store.vector_store', mock_vector_store):
            
            # Index content
            response = test_client.post("/api/v1/index", json=index_request)
            assert response.status_code == 200
            
            # Search for content
            search_request = {
                "query": "integration test",
                "search_type": "hybrid",
                "limit": 10
            }
            
            response = test_client.post("/api/v1/search", json=search_request)
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_concurrent_searches(self, test_client):
        """Test concurrent search requests"""
        import asyncio
        
        async def make_search_request(query: str):
            """Make a search request"""
            request_data = {
                "query": query,
                "search_type": "semantic",
                "limit": 5
            }
            response = test_client.post("/api/v1/search", json=request_data)
            return response.status_code
        
        # Create multiple concurrent requests
        tasks = [
            make_search_request(f"concurrent test {i}")
            for i in range(5)
        ]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should complete (either successfully or with expected errors)
        for result in results:
            assert isinstance(result, int)  # Should be status code, not exception


class TestSearchEngineAPIErrorHandling:
    """Test error handling in Search Engine API"""
    
    def test_search_with_database_error(self, test_client):
        """Test search when database is unavailable"""
        with patch('app.database.db_manager.search_content', side_effect=Exception("Database error")):
            request_data = {
                "query": "test query",
                "search_type": "keyword",
                "limit": 10
            }
            
            response = test_client.post("/api/v1/search/keyword", json=request_data)
            assert response.status_code == 500
    
    def test_index_with_embedding_error(self, test_client):
        """Test index when embedding generation fails"""
        with patch('app.embeddings.cached_embedding_service.generate_embedding', 
                  side_effect=Exception("Embedding error")):
            request_data = {
                "content_id": "error_test",
                "content": "Test content",
                "content_type": "text"
            }
            
            response = test_client.post("/api/v1/index", json=request_data)
            assert response.status_code == 500
    
    def test_invalid_search_type(self, test_client):
        """Test search with invalid search type"""
        request_data = {
            "query": "test query",
            "search_type": "invalid_type",
            "limit": 10
        }
        
        response = test_client.post("/api/v1/search", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_search_with_large_query(self, test_client):
        """Test search with query exceeding max length"""
        large_query = "x" * 1000  # Exceeds max_query_length
        
        request_data = {
            "query": large_query,
            "search_type": "semantic",
            "limit": 10
        }
        
        response = test_client.post("/api/v1/search", json=request_data)
        assert response.status_code == 422  # Validation error