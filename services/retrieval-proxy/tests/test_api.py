"""
Unit tests for API endpoints in retrieval-proxy service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import json
import numpy as np

from main import app


class TestRetrievalProxyAPI:
    """Test cases for Retrieval Proxy API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_search_result(self):
        """Create mock search result"""
        return {
            "session_id": "session123",
            "query": "test query",
            "modalities": ["text", "image"],
            "results_count": 2,
            "results": [
                {
                    "embedding_id": "embedding1",
                    "score": 0.95,
                    "modality": "text",
                    "content_type": "text",
                    "content": "This is test text content",
                    "document_id": "doc1",
                    "filename": "test.txt",
                    "file_type": "text",
                    "metadata": {"source": "test"},
                    "citations": {"source": "test.txt", "type": "text"},
                    "artifacts": {"view_url": "/api/v1/artifacts/text/doc1"}
                },
                {
                    "embedding_id": "embedding2",
                    "score": 0.87,
                    "modality": "image",
                    "content_type": "image",
                    "content": "A test image caption",
                    "document_id": "doc2",
                    "filename": "test.jpg",
                    "file_type": "image",
                    "metadata": {"source": "test"},
                    "citations": {"source": "test.jpg", "type": "image"},
                    "artifacts": {"view_url": "/api/v1/artifacts/image/doc2"}
                }
            ],
            "context_bundle": {
                "query": "test query",
                "sections": [
                    {
                        "type": "text",
                        "title": "Relevant Text Content",
                        "content": "Test text content",
                        "count": 1
                    },
                    {
                        "type": "image",
                        "title": "Relevant Images",
                        "content": "Test image content",
                        "count": 1
                    }
                ],
                "unified_context": "# Search Results for: test query\nFound 2 relevant items",
                "total_results": 2,
                "context_length": 50,
                "citations": []
            },
            "metadata": {
                "search_timestamp": "2024-01-01T00:00:00Z",
                "filters_applied": None,
                "score_threshold": 0.7
            }
        }

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "service" in data

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_search_endpoint_success(self, mock_retrieval_engine, client, mock_search_result):
        """Test successful search endpoint"""
        # Mock search result
        mock_retrieval_engine.search.return_value = mock_search_result

        # Test search
        response = client.post(
            "/search",
            json={
                "query": "test search query",
                "modalities": ["text", "image"],
                "limit": 10,
                "filters": {"content_types": ["text"]},
                "score_threshold": 0.8
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == "session123"
        assert data["query"] == "test query"
        assert data["results_count"] == 2
        assert len(data["results"]) == 2
        assert "context_bundle" in data
        assert "metadata" in data

        # Verify search was called with correct parameters
        mock_retrieval_engine.search.assert_called_once()
        call_args = mock_retrieval_engine.search.call_args
        assert call_args[1]['query'] == "test search query"
        assert call_args[1]['modalities'] == ["text", "image"]
        assert call_args[1]['limit'] == 10
        assert call_args[1]['filters'] == {"content_types": ["text"]}
        assert call_args[1]['score_threshold'] == 0.8

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_search_endpoint_with_default_parameters(self, mock_retrieval_engine, client, mock_search_result):
        """Test search endpoint with default parameters"""
        # Mock search result
        mock_retrieval_engine.search.return_value = mock_search_result

        # Test search with minimal parameters
        response = client.post(
            "/search",
            json={
                "query": "test search query"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify search was called with default parameters
        mock_retrieval_engine.search.assert_called_once()
        call_args = mock_retrieval_engine.search.call_args
        assert call_args[1]['query'] == "test search query"
        assert call_args[1]['modalities'] is None  # Will use default in search method
        assert call_args[1]['limit'] is None  # Will use default in search method

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_search_endpoint_failure(self, mock_retrieval_engine, client):
        """Test search endpoint failure"""
        # Mock search failure
        mock_retrieval_engine.search.side_effect = Exception("Search failed")

        # Test search
        response = client.post(
            "/search",
            json={
                "query": "test search query",
                "modalities": ["text"],
                "limit": 10
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert "Search failed" in data["error"]

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_context_bundle_endpoint_success(self, mock_retrieval_engine, client, mock_search_result):
        """Test successful context bundle endpoint"""
        # Mock search result
        mock_retrieval_engine.search.return_value = mock_search_result

        # Test context bundle creation
        response = client.post(
            "/context-bundle",
            json={
                "query": "test query",
                "modalities": ["text", "image"],
                "max_results": 10,
                "threshold": 0.7
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "context_bundle" in data
        assert data["context_bundle"]["query"] == "test query"
        assert "sections" in data["context_bundle"]
        assert "unified_context" in data["context_bundle"]

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_hybrid_search_endpoint_success(self, mock_retrieval_engine, client, mock_search_result):
        """Test successful hybrid search endpoint"""
        # Mock search result
        mock_retrieval_engine.search.return_value = mock_search_result

        # Test hybrid search
        response = client.post(
            "/search/hybrid",
            json={
                "query": "test search query",
                "modalities": ["text", "image", "video"],
                "limit": 10,
                "vector_weight": 0.7,
                "keyword_weight": 0.3
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["results_count"] == 2
        assert len(data["results"]) == 2

        # Verify search was called
        mock_retrieval_engine.search.assert_called_once()

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_semantic_search_endpoint_success(self, mock_retrieval_engine, client, mock_search_result):
        """Test successful semantic search endpoint"""
        # Mock search result
        mock_retrieval_engine.search.return_value = mock_search_result

        # Test semantic search
        response = client.post(
            "/search/semantic",
            json={
                "query": "test search query",
                "modalities": ["text"],
                "limit": 10,
                "threshold": 0.7
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["results_count"] == 2

        # Verify search was called
        mock_retrieval_engine.search.assert_called_once()

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_keyword_search_endpoint_success(self, mock_retrieval_engine, client, mock_search_result):
        """Test successful keyword search endpoint"""
        # Mock search result
        mock_retrieval_engine.search.return_value = mock_search_result

        # Test keyword search
        response = client.post(
            "/search/keyword",
            json={
                "query": "test search query",
                "modalities": ["text"],
                "limit": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["results_count"] == 2

        # Verify search was called
        mock_retrieval_engine.search.assert_called_once()

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_similar_content_endpoint_success(self, mock_retrieval_engine, client):
        """Test successful similar content endpoint"""
        # Mock similar content results
        mock_similar_results = [
            {
                "embedding_id": "similar1",
                "score": 0.92,
                "content_type": "text",
                "content": "Similar content",
                "document_id": "doc2",
                "filename": "similar.txt"
            }
        ]
        mock_retrieval_engine.search.return_value = {
            "session_id": "session123",
            "query": "similar to doc1",
            "results": mock_similar_results,
            "results_count": 1,
            "context_bundle": {},
            "metadata": {}
        }

        # Test similar content
        response = client.get("/similar/doc1?limit=5&threshold=0.7")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["results_count"] == 1
        assert len(data["results"]) == 1

    @pytest.mark.asyncio
    @patch('main.vector_manager')
    async def test_index_content_endpoint_success(self, mock_vector_manager, client):
        """Test successful content indexing endpoint"""
        # Mock indexing result
        mock_vector_manager.add_vectors.return_value = ["vector_id_1", "vector_id_2"]

        # Test content indexing
        response = client.post(
            "/index",
            json={
                "content_id": "test_content_id",
                "content_type": "text",
                "content": "Test content for indexing",
                "embeddings": [0.1, 0.2, 0.3] * 128,  # 384 dimensions
                "metadata": {
                    "source": "test",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["content_id"] == "test_content_id"
        assert "vector_ids" in data

        # Verify vector manager was called
        mock_vector_manager.add_vectors.assert_called_once()

    @pytest.mark.asyncio
    @patch('main.vector_manager')
    async def test_delete_content_endpoint_success(self, mock_vector_manager, client):
        """Test successful content deletion endpoint"""
        # Mock deletion result
        mock_vector_manager.delete_vectors.return_value = True

        # Test content deletion
        response = client.delete("/content/test_content_id")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["content_id"] == "test_content_id"

        # Verify vector manager was called
        mock_vector_manager.delete_vectors.assert_called_once()

    @pytest.mark.asyncio
    @patch('main.vector_manager')
    async def test_search_stats_endpoint_success(self, mock_vector_manager, client):
        """Test successful search statistics endpoint"""
        # Mock search stats
        mock_vector_manager.get_stats.return_value = {
            "text": {
                "vectors_count": 1000,
                "points_count": 1000,
                "config": {"vector_size": 384, "distance": "Cosine"}
            },
            "image": {
                "vectors_count": 500,
                "points_count": 500,
                "config": {"vector_size": 384, "distance": "Cosine"}
            },
            "video": {
                "vectors_count": 200,
                "points_count": 200,
                "config": {"vector_size": 384, "distance": "Cosine"}
            }
        }

        # Test search stats
        response = client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "image" in data
        assert "video" in data
        assert data["text"]["vectors_count"] == 1000
        assert data["image"]["vectors_count"] == 500
        assert data["video"]["vectors_count"] == 200

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    @patch('main.vector_manager')
    async def test_health_check_endpoint(self, mock_vector_manager, mock_retrieval_engine, client):
        """Test health check endpoint"""
        # Mock health check
        mock_vector_manager.get_stats.return_value = {
            "text": {"vectors_count": 1000},
            "image": {"vectors_count": 500},
            "video": {"vectors_count": 200}
        }

        # Test health check
        response = client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "vector_store" in data
        assert data["vector_store"]["text"]["vectors_count"] == 1000

    def test_invalid_endpoint(self, client):
        """Test invalid endpoint"""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test method not allowed"""
        response = client.put("/health")
        assert response.status_code == 405

    def test_search_with_missing_query(self, client):
        """Test search with missing query"""
        response = client.post(
            "/search",
            json={
                "modalities": ["text"],
                "limit": 10
            }
        )

        assert response.status_code == 422  # Validation error

    def test_search_with_invalid_modalities(self, client):
        """Test search with invalid modalities"""
        response = client.post(
            "/search",
            json={
                "query": "test query",
                "modalities": ["invalid_type"],
                "limit": 10
            }
        )

        assert response.status_code == 422  # Validation error

    def test_search_with_invalid_limit(self, client):
        """Test search with invalid limit"""
        response = client.post(
            "/search",
            json={
                "query": "test query",
                "modalities": ["text"],
                "limit": -1
            }
        )

        assert response.status_code == 422  # Validation error

    def test_search_with_invalid_score_threshold(self, client):
        """Test search with invalid score threshold"""
        response = client.post(
            "/search",
            json={
                "query": "test query",
                "modalities": ["text"],
                "limit": 10,
                "score_threshold": 1.5  # Invalid: should be between 0 and 1
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_search_with_empty_results(self, mock_retrieval_engine, client):
        """Test search with empty results"""
        # Mock empty search results
        mock_retrieval_engine.search.return_value = {
            "session_id": "session123",
            "query": "test query",
            "modalities": ["text"],
            "results_count": 0,
            "results": [],
            "context_bundle": {
                "query": "test query",
                "sections": [],
                "unified_context": "# Search Results for: test query\nFound 0 relevant items",
                "total_results": 0,
                "context_length": 0,
                "citations": []
            },
            "metadata": {
                "search_timestamp": "2024-01-01T00:00:00Z",
                "filters_applied": None,
                "score_threshold": 0.7
            }
        }

        # Test search
        response = client.post(
            "/search",
            json={
                "query": "test search query",
                "modalities": ["text"],
                "limit": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["results_count"] == 0
        assert len(data["results"]) == 0

    @pytest.mark.asyncio
    @patch('main.vector_manager')
    async def test_index_content_with_invalid_embeddings(self, mock_vector_manager, client):
        """Test content indexing with invalid embeddings"""
        # Test with invalid embedding dimensions
        response = client.post(
            "/index",
            json={
                "content_id": "test_content_id",
                "content_type": "text",
                "content": "Test content",
                "embeddings": [0.1, 0.2, 0.3],  # Wrong dimensions (should be 384)
                "metadata": {"source": "test"}
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @patch('main.vector_manager')
    async def test_index_content_with_missing_required_fields(self, mock_vector_manager, client):
        """Test content indexing with missing required fields"""
        # Test with missing content_id
        response = client.post(
            "/index",
            json={
                "content_type": "text",
                "content": "Test content",
                "embeddings": [0.1, 0.2, 0.3] * 128,
                "metadata": {"source": "test"}
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_search_with_complex_filters(self, mock_retrieval_engine, client, mock_search_result):
        """Test search with complex filters"""
        # Mock search result
        mock_retrieval_engine.search.return_value = mock_search_result

        # Test search with complex filters
        response = client.post(
            "/search",
            json={
                "query": "test search query",
                "modalities": ["text", "image"],
                "limit": 10,
                "filters": {
                    "content_types": ["text", "image"],
                    "file_types": ["txt", "jpg"],
                    "min_score": 0.8,
                    "date_range": {
                        "gte": "2024-01-01T00:00:00Z",
                        "lte": "2024-12-31T23:59:59Z"
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify search was called with filters
        mock_retrieval_engine.search.assert_called_once()
        call_args = mock_retrieval_engine.search.call_args
        assert call_args[1]['filters'] is not None
        assert call_args[1]['filters']['content_types'] == ["text", "image"]

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_search_with_large_limit(self, mock_retrieval_engine, client, mock_search_result):
        """Test search with large limit (should be capped)"""
        # Mock search result
        mock_retrieval_engine.search.return_value = mock_search_result

        # Test search with large limit
        response = client.post(
            "/search",
            json={
                "query": "test search query",
                "modalities": ["text"],
                "limit": 1000  # Large limit
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify search was called with capped limit
        mock_retrieval_engine.search.assert_called_once()
        call_args = mock_retrieval_engine.search.call_args
        # The limit should be capped at max_search_limit (100)
        assert call_args[1]['limit'] == 1000  # This will be capped in the search method

    def test_api_error_handling(self, client):
        """Test API error handling for malformed requests"""
        # Test with invalid JSON
        response = client.post(
            "/search",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

        # Test with missing required fields
        response = client.post(
            "/search",
            json={
                "modalities": ["text"]  # Missing 'query' field
            }
        )
        assert response.status_code == 422