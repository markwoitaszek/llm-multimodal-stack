"""
Unit tests for API endpoints in retrieval-proxy service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import json

from main import app


class TestRetrievalProxyAPI:
    """Test cases for Retrieval Proxy API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

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
    async def test_search_endpoint_success(self, mock_retrieval_engine, client):
        """Test successful search endpoint"""
        # Mock search results
        mock_retrieval_engine.search_content.return_value = [
            {
                "content_id": "doc_1",
                "content_type": "text",
                "content": "Test document 1",
                "score": 0.95,
                "metadata": {"source": "test"}
            },
            {
                "content_id": "doc_2",
                "content_type": "image",
                "content": "Test image 2",
                "score": 0.87,
                "metadata": {"source": "test"}
            }
        ]

        # Test search
        response = client.post(
            "/search",
            json={
                "query": "test search query",
                "content_types": ["text", "image"],
                "limit": 10,
                "threshold": 0.7
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == 2
        assert data["total_results"] == 2
        assert "search_time_ms" in data

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_search_endpoint_with_filters(self, mock_retrieval_engine, client):
        """Test search endpoint with filters"""
        # Mock search results
        mock_retrieval_engine.search_content.return_value = []

        # Test search with filters
        response = client.post(
            "/search",
            json={
                "query": "test search query",
                "content_types": ["text"],
                "limit": 10,
                "threshold": 0.7,
                "filters": {
                    "source": "test",
                    "date_range": "2024-01-01"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == 0

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_search_endpoint_failure(self, mock_retrieval_engine, client):
        """Test search endpoint failure"""
        # Mock search failure
        mock_retrieval_engine.search_content.side_effect = Exception("Search failed")

        # Test search
        response = client.post(
            "/search",
            json={
                "query": "test search query",
                "content_types": ["text"],
                "limit": 10
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_context_bundle_endpoint_success(self, mock_retrieval_engine, client):
        """Test successful context bundle endpoint"""
        # Mock context bundle
        mock_retrieval_engine.create_context_bundle.return_value = {
            "query": "test query",
            "results": [
                {
                    "content_id": "doc_1",
                    "content_type": "text",
                    "content": "Test document 1",
                    "score": 0.95,
                    "metadata": {"source": "test"}
                }
            ],
            "total_results": 1,
            "search_time_ms": 50
        }

        # Test context bundle creation
        response = client.post(
            "/context-bundle",
            json={
                "query": "test query",
                "content_types": ["text", "image"],
                "max_results": 10,
                "threshold": 0.7
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["query"] == "test query"
        assert len(data["results"]) == 1
        assert data["total_results"] == 1

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_hybrid_search_endpoint_success(self, mock_retrieval_engine, client):
        """Test successful hybrid search endpoint"""
        # Mock hybrid search results
        mock_retrieval_engine.hybrid_search.return_value = [
            {
                "content_id": "doc_1",
                "content_type": "text",
                "content": "Test document 1",
                "vector_score": 0.95,
                "keyword_score": 0.85,
                "hybrid_score": 0.92
            }
        ]

        # Test hybrid search
        response = client.post(
            "/search/hybrid",
            json={
                "query": "test search query",
                "content_types": ["text"],
                "limit": 10,
                "vector_weight": 0.7,
                "keyword_weight": 0.3
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == 1
        assert "hybrid_score" in data["results"][0]

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_semantic_search_endpoint_success(self, mock_retrieval_engine, client):
        """Test successful semantic search endpoint"""
        # Mock semantic search results
        mock_retrieval_engine.semantic_search.return_value = [
            {
                "content_id": "doc_1",
                "content_type": "text",
                "content": "Test document 1",
                "semantic_score": 0.95
            }
        ]

        # Test semantic search
        response = client.post(
            "/search/semantic",
            json={
                "query": "test search query",
                "content_types": ["text"],
                "limit": 10,
                "threshold": 0.7
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == 1
        assert "semantic_score" in data["results"][0]

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_keyword_search_endpoint_success(self, mock_retrieval_engine, client):
        """Test successful keyword search endpoint"""
        # Mock keyword search results
        mock_retrieval_engine.keyword_search.return_value = [
            {
                "content_id": "doc_1",
                "content_type": "text",
                "content": "Test document 1",
                "keyword_score": 0.9
            }
        ]

        # Test keyword search
        response = client.post(
            "/search/keyword",
            json={
                "query": "test search query",
                "content_types": ["text"],
                "limit": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == 1
        assert "keyword_score" in data["results"][0]

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_similar_content_endpoint_success(self, mock_retrieval_engine, client):
        """Test successful similar content endpoint"""
        # Mock similar content results
        mock_retrieval_engine.get_similar_content.return_value = [
            {
                "content_id": "doc_2",
                "content_type": "text",
                "content": "Similar document",
                "similarity_score": 0.88
            }
        ]

        # Test similar content
        response = client.get("/similar/doc_1?limit=5&threshold=0.7")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == 1
        assert "similarity_score" in data["results"][0]

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_index_content_endpoint_success(self, mock_retrieval_engine, client):
        """Test successful content indexing endpoint"""
        # Mock indexing result
        mock_retrieval_engine.index_content.return_value = {
            "success": True,
            "content_id": "test_content_id"
        }

        # Test content indexing
        response = client.post(
            "/index",
            json={
                "content_id": "test_content_id",
                "content_type": "text",
                "content": "Test content for indexing",
                "embeddings": [0.1, 0.2, 0.3] * 170,  # 512 dimensions
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

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_delete_content_endpoint_success(self, mock_retrieval_engine, client):
        """Test successful content deletion endpoint"""
        # Mock deletion result
        mock_retrieval_engine.delete_content.return_value = {
            "success": True,
            "content_id": "test_content_id"
        }

        # Test content deletion
        response = client.delete("/content/test_content_id")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["content_id"] == "test_content_id"

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_search_stats_endpoint_success(self, mock_retrieval_engine, client):
        """Test successful search statistics endpoint"""
        # Mock search stats
        mock_retrieval_engine.get_search_stats.return_value = {
            "total_searches": 1000,
            "avg_response_time_ms": 150,
            "success_rate": 0.95
        }

        # Test search stats
        response = client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_searches"] == 1000
        assert data["avg_response_time_ms"] == 150
        assert data["success_rate"] == 0.95

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_health_check_endpoint(self, mock_retrieval_engine, client):
        """Test health check endpoint"""
        # Mock health check
        mock_retrieval_engine.health_check.return_value = {
            "status": "healthy",
            "database": "healthy",
            "vector_store": "healthy"
        }

        # Test health check
        response = client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "healthy"
        assert data["vector_store"] == "healthy"

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
                "content_types": ["text"],
                "limit": 10
            }
        )

        assert response.status_code == 422  # Validation error

    def test_search_with_invalid_content_types(self, client):
        """Test search with invalid content types"""
        response = client.post(
            "/search",
            json={
                "query": "test query",
                "content_types": ["invalid_type"],
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
                "content_types": ["text"],
                "limit": -1
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @patch('main.retrieval_engine')
    async def test_search_with_empty_results(self, mock_retrieval_engine, client):
        """Test search with empty results"""
        # Mock empty search results
        mock_retrieval_engine.search_content.return_value = []

        # Test search
        response = client.post(
            "/search",
            json={
                "query": "test search query",
                "content_types": ["text"],
                "limit": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == 0
        assert data["total_results"] == 0
