"""
Unit tests for vector store operations in retrieval-proxy service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np

from app.vector_store import VectorStoreManager


class TestVectorStoreManager:
    """Test cases for VectorStoreManager"""

    @pytest.fixture
    def vector_manager(self):
        """Create VectorStoreManager instance for testing"""
        return VectorStoreManager()

    @pytest.mark.asyncio
    @patch('app.vector_store.QdrantClient')
    async def test_vector_manager_initialization(self, mock_qdrant_client, vector_manager):
        """Test VectorStoreManager initialization"""
        assert vector_manager is not None
        assert hasattr(vector_manager, 'client')
        assert hasattr(vector_manager, 'collection_name')

    @pytest.mark.asyncio
    @patch('app.vector_store.QdrantClient')
    async def test_initialize_success(self, mock_qdrant_client, vector_manager):
        """Test successful vector store initialization"""
        # Mock Qdrant client
        mock_client = AsyncMock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = {"collections": []}

        # Test initialization
        await vector_manager.initialize()

        # Verify client was created
        mock_qdrant_client.assert_called_once()
        assert vector_manager.client == mock_client

    @pytest.mark.asyncio
    @patch('app.vector_store.QdrantClient')
    async def test_initialize_create_collection(self, mock_qdrant_client, vector_manager):
        """Test vector store initialization with collection creation"""
        # Mock Qdrant client
        mock_client = AsyncMock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value = {"collections": []}

        # Test initialization
        await vector_manager.initialize()

        # Verify collection was created
        mock_client.create_collection.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.vector_store.QdrantClient')
    async def test_initialize_failure(self, mock_qdrant_client, vector_manager):
        """Test vector store initialization failure"""
        # Mock Qdrant client failure
        mock_qdrant_client.side_effect = Exception("Connection failed")

        # Test initialization
        with pytest.raises(Exception, match="Connection failed"):
            await vector_manager.initialize()

    @pytest.mark.asyncio
    async def test_upsert_vectors_success(self, vector_manager, mock_qdrant_client):
        """Test successful vector upsertion"""
        # Mock client
        vector_manager.client = mock_qdrant_client

        # Test data
        vectors = [
            {
                "id": "doc_1",
                "vector": np.random.rand(512).tolist(),
                "payload": {"content": "test content 1"}
            },
            {
                "id": "doc_2",
                "vector": np.random.rand(512).tolist(),
                "payload": {"content": "test content 2"}
            }
        ]

        # Test upsertion
        result = await vector_manager.upsert_vectors(vectors)

        # Verify result
        assert result is True
        mock_qdrant_client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_vectors_failure(self, vector_manager, mock_qdrant_client):
        """Test vector upsertion failure"""
        # Mock client with failure
        mock_qdrant_client.upsert.side_effect = Exception("Upsert failed")
        vector_manager.client = mock_qdrant_client

        # Test data
        vectors = [{"id": "doc_1", "vector": [0.1, 0.2], "payload": {}}]

        # Test upsertion
        with pytest.raises(Exception, match="Upsert failed"):
            await vector_manager.upsert_vectors(vectors)

    @pytest.mark.asyncio
    async def test_search_vectors_success(self, vector_manager, mock_qdrant_client, 
                                        mock_vector_search_result):
        """Test successful vector search"""
        # Mock client
        vector_manager.client = mock_qdrant_client
        mock_qdrant_client.search.return_value = mock_vector_search_result

        # Test search
        query_vector = np.random.rand(512).tolist()
        result = await vector_manager.search_vectors(
            query_vector=query_vector,
            limit=10,
            score_threshold=0.7
        )

        # Verify result
        assert len(result) == 2
        assert result[0]["id"] == "doc_1"
        assert result[0]["score"] == 0.95
        assert result[1]["id"] == "doc_2"
        assert result[1]["score"] == 0.87

    @pytest.mark.asyncio
    async def test_search_vectors_with_filters(self, vector_manager, mock_qdrant_client,
                                             mock_vector_search_result):
        """Test vector search with filters"""
        # Mock client
        vector_manager.client = mock_qdrant_client
        mock_qdrant_client.search.return_value = mock_vector_search_result

        # Test search with filters
        query_vector = np.random.rand(512).tolist()
        filters = {"content_type": "text"}
        
        result = await vector_manager.search_vectors(
            query_vector=query_vector,
            limit=10,
            score_threshold=0.7,
            filters=filters
        )

        # Verify result
        assert len(result) == 2
        mock_qdrant_client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_vectors_failure(self, vector_manager, mock_qdrant_client):
        """Test vector search failure"""
        # Mock client with failure
        mock_qdrant_client.search.side_effect = Exception("Search failed")
        vector_manager.client = mock_qdrant_client

        # Test search
        query_vector = np.random.rand(512).tolist()
        
        with pytest.raises(Exception, match="Search failed"):
            await vector_manager.search_vectors(
                query_vector=query_vector,
                limit=10
            )

    @pytest.mark.asyncio
    async def test_delete_vectors_success(self, vector_manager, mock_qdrant_client):
        """Test successful vector deletion"""
        # Mock client
        vector_manager.client = mock_qdrant_client

        # Test deletion
        vector_ids = ["doc_1", "doc_2"]
        result = await vector_manager.delete_vectors(vector_ids)

        # Verify result
        assert result is True
        mock_qdrant_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_vectors_failure(self, vector_manager, mock_qdrant_client):
        """Test vector deletion failure"""
        # Mock client with failure
        mock_qdrant_client.delete.side_effect = Exception("Delete failed")
        vector_manager.client = mock_qdrant_client

        # Test deletion
        vector_ids = ["doc_1", "doc_2"]
        
        with pytest.raises(Exception, match="Delete failed"):
            await vector_manager.delete_vectors(vector_ids)

    @pytest.mark.asyncio
    async def test_get_vector_by_id(self, vector_manager, mock_qdrant_client):
        """Test getting vector by ID"""
        # Mock client
        mock_qdrant_client.retrieve.return_value = [
            {
                "id": "doc_1",
                "vector": [0.1, 0.2, 0.3],
                "payload": {"content": "test content"}
            }
        ]
        vector_manager.client = mock_qdrant_client

        # Test getting vector
        result = await vector_manager.get_vector_by_id("doc_1")

        # Verify result
        assert result["id"] == "doc_1"
        assert result["vector"] == [0.1, 0.2, 0.3]
        assert result["payload"]["content"] == "test content"

    @pytest.mark.asyncio
    async def test_get_vector_by_id_not_found(self, vector_manager, mock_qdrant_client):
        """Test getting non-existent vector by ID"""
        # Mock client
        mock_qdrant_client.retrieve.return_value = []
        vector_manager.client = mock_qdrant_client

        # Test getting vector
        result = await vector_manager.get_vector_by_id("nonexistent_id")

        # Verify result
        assert result is None

    @pytest.mark.asyncio
    async def test_get_collection_info(self, vector_manager, mock_qdrant_client):
        """Test getting collection information"""
        # Mock client
        mock_qdrant_client.get_collection.return_value = {
            "status": "green",
            "vectors_count": 1000,
            "indexed_vectors_count": 1000
        }
        vector_manager.client = mock_qdrant_client

        # Test getting collection info
        result = await vector_manager.get_collection_info()

        # Verify result
        assert result["status"] == "green"
        assert result["vectors_count"] == 1000
        assert result["indexed_vectors_count"] == 1000

    @pytest.mark.asyncio
    async def test_health_check(self, vector_manager, mock_qdrant_client):
        """Test vector store health check"""
        # Mock client
        mock_qdrant_client.get_collections.return_value = {"collections": ["test_collection"]}
        vector_manager.client = mock_qdrant_client

        # Test health check
        result = await vector_manager.health_check()

        # Verify result
        assert result["status"] == "healthy"
        assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_health_check_failure(self, vector_manager, mock_qdrant_client):
        """Test vector store health check failure"""
        # Mock client with failure
        mock_qdrant_client.get_collections.side_effect = Exception("Connection failed")
        vector_manager.client = mock_qdrant_client

        # Test health check
        result = await vector_manager.health_check()

        # Verify result
        assert result["status"] == "unhealthy"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_batch_upsert_vectors(self, vector_manager, mock_qdrant_client):
        """Test batch vector upsertion"""
        # Mock client
        vector_manager.client = mock_qdrant_client

        # Test data - large batch
        vectors = [
            {
                "id": f"doc_{i}",
                "vector": np.random.rand(512).tolist(),
                "payload": {"content": f"test content {i}"}
            }
            for i in range(1000)
        ]

        # Test batch upsertion
        result = await vector_manager.batch_upsert_vectors(vectors, batch_size=100)

        # Verify result
        assert result is True
        # Should be called 10 times (1000 / 100)
        assert mock_qdrant_client.upsert.call_count == 10

    @pytest.mark.asyncio
    async def test_search_vectors_with_reranking(self, vector_manager, mock_qdrant_client,
                                               mock_vector_search_result):
        """Test vector search with reranking"""
        # Mock client
        vector_manager.client = mock_qdrant_client
        mock_qdrant_client.search.return_value = mock_vector_search_result

        # Test search with reranking
        query_vector = np.random.rand(512).tolist()
        result = await vector_manager.search_vectors(
            query_vector=query_vector,
            limit=10,
            score_threshold=0.7,
            rerank=True
        )

        # Verify result
        assert len(result) == 2
        mock_qdrant_client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_vector_stats(self, vector_manager, mock_qdrant_client):
        """Test getting vector statistics"""
        # Mock client
        mock_qdrant_client.get_collection.return_value = {
            "status": "green",
            "vectors_count": 1000,
            "indexed_vectors_count": 1000,
            "points_count": 1000
        }
        vector_manager.client = mock_qdrant_client

        # Test getting stats
        result = await vector_manager.get_vector_stats()

        # Verify result
        assert result["total_vectors"] == 1000
        assert result["indexed_vectors"] == 1000
        assert result["status"] == "green"
