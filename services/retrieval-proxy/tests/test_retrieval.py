"""
Unit tests for retrieval engine in retrieval-proxy service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np

from app.retrieval import RetrievalEngine


class TestRetrievalEngine:
    """Test cases for RetrievalEngine"""

    @pytest.fixture
    def retrieval_engine(self, mock_database_manager, mock_vector_store):
        """Create RetrievalEngine instance for testing"""
        return RetrievalEngine(mock_database_manager, mock_vector_store)

    @pytest.mark.asyncio
    async def test_retrieval_engine_initialization(self, retrieval_engine):
        """Test RetrievalEngine initialization"""
        assert retrieval_engine is not None
        assert hasattr(retrieval_engine, 'db_manager')
        assert hasattr(retrieval_engine, 'vector_manager')

    @pytest.mark.asyncio
    async def test_search_content_success(self, retrieval_engine, mock_vector_search_result,
                                        test_search_request):
        """Test successful content search"""
        # Mock vector search
        retrieval_engine.vector_manager.search_vectors.return_value = mock_vector_search_result

        # Test search
        result = await retrieval_engine.search_content(
            query=test_search_request["query"],
            content_types=test_search_request["content_types"],
            limit=test_search_request["limit"],
            threshold=test_search_request["threshold"]
        )

        # Verify result
        assert len(result) == 2
        assert result[0]["content_id"] == "doc_1"
        assert result[0]["score"] == 0.95
        assert result[1]["content_id"] == "doc_2"
        assert result[1]["score"] == 0.87

    @pytest.mark.asyncio
    async def test_search_content_with_filters(self, retrieval_engine, mock_vector_search_result):
        """Test content search with filters"""
        # Mock vector search
        retrieval_engine.vector_manager.search_vectors.return_value = mock_vector_search_result

        # Test search with filters
        filters = {"source": "test", "date_range": "2024-01-01"}
        result = await retrieval_engine.search_content(
            query="test query",
            content_types=["text", "image"],
            limit=10,
            threshold=0.7,
            filters=filters
        )

        # Verify result
        assert len(result) == 2
        retrieval_engine.vector_manager.search_vectors.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_content_empty_results(self, retrieval_engine):
        """Test content search with empty results"""
        # Mock empty vector search
        retrieval_engine.vector_manager.search_vectors.return_value = []

        # Test search
        result = await retrieval_engine.search_content(
            query="test query",
            content_types=["text"],
            limit=10
        )

        # Verify result
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_content_failure(self, retrieval_engine):
        """Test content search failure"""
        # Mock vector search failure
        retrieval_engine.vector_manager.search_vectors.side_effect = Exception("Search failed")

        # Test search
        with pytest.raises(Exception, match="Search failed"):
            await retrieval_engine.search_content(
                query="test query",
                content_types=["text"],
                limit=10
            )

    @pytest.mark.asyncio
    async def test_create_context_bundle_success(self, retrieval_engine, mock_context_bundle):
        """Test successful context bundle creation"""
        # Mock search results
        search_results = mock_context_bundle["results"]
        retrieval_engine.search_content.return_value = search_results

        # Test context bundle creation
        result = await retrieval_engine.create_context_bundle(
            query="test query",
            content_types=["text", "image"],
            max_results=10,
            threshold=0.7
        )

        # Verify result
        assert result["query"] == "test query"
        assert len(result["results"]) == 2
        assert result["total_results"] == 2
        assert "search_time_ms" in result

    @pytest.mark.asyncio
    async def test_create_context_bundle_with_reranking(self, retrieval_engine, mock_context_bundle):
        """Test context bundle creation with reranking"""
        # Mock search results
        search_results = mock_context_bundle["results"]
        retrieval_engine.search_content.return_value = search_results

        # Test context bundle creation with reranking
        result = await retrieval_engine.create_context_bundle(
            query="test query",
            content_types=["text", "image"],
            max_results=10,
            threshold=0.7,
            rerank=True
        )

        # Verify result
        assert result["query"] == "test query"
        assert len(result["results"]) == 2
        assert "reranked" in result

    @pytest.mark.asyncio
    async def test_index_content_success(self, retrieval_engine, test_index_request):
        """Test successful content indexing"""
        # Mock database and vector operations
        retrieval_engine.db_manager.insert_record.return_value = "test_content_id"
        retrieval_engine.vector_manager.upsert_vectors.return_value = True

        # Test indexing
        result = await retrieval_engine.index_content(
            content_id=test_index_request["content_id"],
            content_type=test_index_request["content_type"],
            content=test_index_request["content"],
            embeddings=test_index_request["embeddings"],
            metadata=test_index_request["metadata"]
        )

        # Verify result
        assert result["success"] is True
        assert result["content_id"] == "test_content_id"
        retrieval_engine.db_manager.insert_record.assert_called_once()
        retrieval_engine.vector_manager.upsert_vectors.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_content_failure(self, retrieval_engine, test_index_request):
        """Test content indexing failure"""
        # Mock database failure
        retrieval_engine.db_manager.insert_record.side_effect = Exception("Database error")

        # Test indexing
        result = await retrieval_engine.index_content(
            content_id=test_index_request["content_id"],
            content_type=test_index_request["content_type"],
            content=test_index_request["content"],
            embeddings=test_index_request["embeddings"],
            metadata=test_index_request["metadata"]
        )

        # Verify result
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_hybrid_search_success(self, retrieval_engine, mock_vector_search_result):
        """Test successful hybrid search"""
        # Mock vector search
        retrieval_engine.vector_manager.search_vectors.return_value = mock_vector_search_result

        # Test hybrid search
        result = await retrieval_engine.hybrid_search(
            query="test query",
            content_types=["text", "image"],
            limit=10,
            vector_weight=0.7,
            keyword_weight=0.3
        )

        # Verify result
        assert len(result) == 2
        assert "hybrid_scores" in result[0]

    @pytest.mark.asyncio
    async def test_semantic_search_success(self, retrieval_engine, mock_vector_search_result):
        """Test successful semantic search"""
        # Mock vector search
        retrieval_engine.vector_manager.search_vectors.return_value = mock_vector_search_result

        # Test semantic search
        result = await retrieval_engine.semantic_search(
            query="test query",
            content_types=["text"],
            limit=10,
            threshold=0.7
        )

        # Verify result
        assert len(result) == 2
        assert all("semantic_score" in item for item in result)

    @pytest.mark.asyncio
    async def test_keyword_search_success(self, retrieval_engine):
        """Test successful keyword search"""
        # Mock database search
        retrieval_engine.db_manager.execute_query.return_value = [
            {"id": "doc_1", "content": "test document 1", "score": 0.9},
            {"id": "doc_2", "content": "test document 2", "score": 0.8}
        ]

        # Test keyword search
        result = await retrieval_engine.keyword_search(
            query="test query",
            content_types=["text"],
            limit=10
        )

        # Verify result
        assert len(result) == 2
        assert result[0]["content_id"] == "doc_1"
        assert result[0]["keyword_score"] == 0.9

    @pytest.mark.asyncio
    async def test_get_similar_content_success(self, retrieval_engine, mock_vector_search_result):
        """Test getting similar content"""
        # Mock vector search
        retrieval_engine.vector_manager.search_vectors.return_value = mock_vector_search_result

        # Test getting similar content
        result = await retrieval_engine.get_similar_content(
            content_id="doc_1",
            limit=5,
            threshold=0.7
        )

        # Verify result
        assert len(result) == 2
        assert all("similarity_score" in item for item in result)

    @pytest.mark.asyncio
    async def test_delete_content_success(self, retrieval_engine):
        """Test successful content deletion"""
        # Mock database and vector operations
        retrieval_engine.db_manager.delete_record.return_value = True
        retrieval_engine.vector_manager.delete_vectors.return_value = True

        # Test deletion
        result = await retrieval_engine.delete_content("test_content_id")

        # Verify result
        assert result["success"] is True
        retrieval_engine.db_manager.delete_record.assert_called_once()
        retrieval_engine.vector_manager.delete_vectors.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_content_failure(self, retrieval_engine):
        """Test content deletion failure"""
        # Mock database failure
        retrieval_engine.db_manager.delete_record.side_effect = Exception("Delete failed")

        # Test deletion
        result = await retrieval_engine.delete_content("test_content_id")

        # Verify result
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_search_stats(self, retrieval_engine):
        """Test getting search statistics"""
        # Mock database stats
        retrieval_engine.db_manager.execute_query.return_value = [
            {
                "total_searches": 1000,
                "avg_response_time_ms": 150,
                "success_rate": 0.95
            }
        ]

        # Test getting stats
        result = await retrieval_engine.get_search_stats()

        # Verify result
        assert result["total_searches"] == 1000
        assert result["avg_response_time_ms"] == 150
        assert result["success_rate"] == 0.95

    @pytest.mark.asyncio
    async def test_health_check(self, retrieval_engine):
        """Test retrieval engine health check"""
        # Mock health checks
        retrieval_engine.db_manager.health_check.return_value = {"status": "healthy"}
        retrieval_engine.vector_manager.health_check.return_value = {"status": "healthy"}

        # Test health check
        result = await retrieval_engine.health_check()

        # Verify result
        assert result["status"] == "healthy"
        assert result["database"] == "healthy"
        assert result["vector_store"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_failure(self, retrieval_engine):
        """Test retrieval engine health check failure"""
        # Mock health check failure
        retrieval_engine.db_manager.health_check.return_value = {"status": "unhealthy"}
        retrieval_engine.vector_manager.health_check.return_value = {"status": "healthy"}

        # Test health check
        result = await retrieval_engine.health_check()

        # Verify result
        assert result["status"] == "unhealthy"
        assert result["database"] == "unhealthy"
        assert result["vector_store"] == "healthy"
