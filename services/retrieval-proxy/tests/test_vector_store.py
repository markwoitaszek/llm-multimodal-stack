"""
Unit tests for vector store operations in retrieval-proxy service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np
import uuid
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range, MatchValue

from app.vector_store import VectorStoreManager


class TestVectorStoreManager:
    """Test cases for VectorStoreManager"""

    @pytest.fixture
    def vector_store_manager(self):
        """Create VectorStoreManager instance for testing"""
        with patch('app.vector_store.settings') as mock_settings:
            mock_settings.qdrant_host = 'localhost'
            mock_settings.qdrant_port = 6333
            mock_settings.qdrant_collection_text = 'test-text'
            mock_settings.qdrant_collection_image = 'test-image'
            mock_settings.qdrant_collection_video = 'test-video'
            return VectorStoreManager()

    @pytest.fixture
    def mock_qdrant_client(self):
        """Create mock Qdrant client"""
        client = Mock()
        client.get_collections.return_value = Mock(collections=[])
        client.get_collection.return_value = Mock()
        client.create_collection.return_value = None
        client.close.return_value = None
        client.upsert.return_value = None
        client.search.return_value = []
        client.retrieve.return_value = []
        client.delete.return_value = None
        client.set_payload.return_value = None
        return client

    @pytest.fixture
    def test_vectors(self):
        """Create test vectors"""
        return [
            np.random.rand(384).astype(np.float32),
            np.random.rand(384).astype(np.float32),
            np.random.rand(384).astype(np.float32)
        ]

    @pytest.fixture
    def test_metadata(self):
        """Create test metadata"""
        return [
            {"content_type": "text", "document_id": "doc1", "chunk_index": 0},
            {"content_type": "text", "document_id": "doc1", "chunk_index": 1},
            {"content_type": "image", "document_id": "doc2", "filename": "test.jpg"}
        ]

    @pytest.mark.asyncio
    async def test_initialize_success(self, vector_store_manager, mock_qdrant_client):
        """Test successful vector store initialization"""
        with patch('app.vector_store.QdrantClient', return_value=mock_qdrant_client) as mock_qdrant:
            # Test initialization
            await vector_store_manager.initialize()

            # Verify Qdrant client was created
            mock_qdrant.assert_called_once_with(
                host='localhost',
                port=6333
            )

            # Verify collections were checked and created
            assert mock_qdrant_client.get_collection.call_count == 3
            assert mock_qdrant_client.create_collection.call_count == 3

            # Verify client was stored
            assert vector_store_manager.client == mock_qdrant_client

    @pytest.mark.asyncio
    async def test_initialize_with_existing_collections(self, vector_store_manager, mock_qdrant_client):
        """Test initialization when collections already exist"""
        # Mock existing collections
        mock_qdrant_client.get_collection.return_value = Mock()

        with patch('app.vector_store.QdrantClient', return_value=mock_qdrant_client) as mock_qdrant:
            # Test initialization
            await vector_store_manager.initialize()

            # Verify collections were checked but not created
            assert mock_qdrant_client.get_collection.call_count == 3
            assert mock_qdrant_client.create_collection.call_count == 0

    @pytest.mark.asyncio
    async def test_initialize_failure(self, vector_store_manager):
        """Test vector store initialization failure"""
        with patch('app.vector_store.QdrantClient', side_effect=Exception("Connection failed")):
            # Test that exception is raised
            with pytest.raises(Exception, match="Connection failed"):
                await vector_store_manager.initialize()

    @pytest.mark.asyncio
    async def test_close(self, vector_store_manager, mock_qdrant_client):
        """Test vector store connection closure"""
        vector_store_manager.client = mock_qdrant_client

        # Test close
        await vector_store_manager.close()

        # Verify client was closed
        mock_qdrant_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_client(self, vector_store_manager):
        """Test close when no client exists"""
        # Test close without client
        await vector_store_manager.close()
        # Should not raise exception

    def test_add_vectors_success(self, vector_store_manager, mock_qdrant_client, test_vectors, test_metadata):
        """Test successful vector addition"""
        vector_store_manager.client = mock_qdrant_client

        # Test vector addition
        vector_ids = vector_store_manager.add_vectors(
            collection_name="test-collection",
            vectors=test_vectors,
            metadata_list=test_metadata
        )

        # Verify vector IDs are returned
        assert isinstance(vector_ids, list)
        assert len(vector_ids) == 3
        assert all(isinstance(vid, str) for vid in vector_ids)

        # Verify Qdrant client was called
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        assert call_args[1]['collection_name'] == "test-collection"
        assert len(call_args[1]['points']) == 3

    def test_add_vectors_with_numpy_arrays(self, vector_store_manager, mock_qdrant_client):
        """Test vector addition with numpy arrays"""
        vector_store_manager.client = mock_qdrant_client

        # Test with numpy arrays
        vectors = [np.array([0.1, 0.2, 0.3, 0.4])]
        metadata = [{"test": "data"}]

        vector_ids = vector_store_manager.add_vectors(
            collection_name="test-collection",
            vectors=vectors,
            metadata_list=metadata
        )

        # Verify vector IDs are returned
        assert len(vector_ids) == 1

        # Verify vectors were converted to lists
        call_args = mock_qdrant_client.upsert.call_args
        point = call_args[1]['points'][0]
        assert isinstance(point.vector, list)

    def test_search_vectors_success(self, vector_store_manager, mock_qdrant_client, test_vectors):
        """Test successful vector search"""
        vector_store_manager.client = mock_qdrant_client

        # Mock search results
        mock_results = [
            Mock(id="result1", score=0.95, payload={"content": "test1"}),
            Mock(id="result2", score=0.87, payload={"content": "test2"})
        ]
        mock_qdrant_client.search.return_value = mock_results

        # Test vector search
        query_vector = test_vectors[0]
        results = vector_store_manager.search_vectors(
            collection_name="test-collection",
            query_vector=query_vector,
            limit=10,
            score_threshold=0.8
        )

        # Verify results
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]['id'] == "result1"
        assert results[0]['score'] == 0.95
        assert results[0]['payload']['content'] == "test1"

        # Verify Qdrant client was called
        mock_qdrant_client.search.assert_called_once()
        call_args = mock_qdrant_client.search.call_args
        assert call_args[1]['collection_name'] == "test-collection"
        assert call_args[1]['limit'] == 10
        assert call_args[1]['score_threshold'] == 0.8

    def test_search_vectors_with_filters(self, vector_store_manager, mock_qdrant_client, test_vectors):
        """Test vector search with filters"""
        vector_store_manager.client = mock_qdrant_client

        # Mock search results
        mock_results = [Mock(id="result1", score=0.95, payload={"content": "test1"})]
        mock_qdrant_client.search.return_value = mock_results

        # Test vector search with filters
        query_vector = test_vectors[0]
        filters = {
            "document_id": "doc1",
            "content_type": "text",
            "date_range": {"gte": "2024-01-01", "lte": "2024-12-31"}
        }

        results = vector_store_manager.search_vectors(
            collection_name="test-collection",
            query_vector=query_vector,
            limit=10,
            filters=filters
        )

        # Verify results
        assert len(results) == 1

        # Verify filter was applied
        call_args = mock_qdrant_client.search.call_args
        assert call_args[1]['query_filter'] is not None

    def test_search_vectors_with_numpy_array(self, vector_store_manager, mock_qdrant_client, test_vectors):
        """Test vector search with numpy array"""
        vector_store_manager.client = mock_qdrant_client

        # Mock search results
        mock_results = [Mock(id="result1", score=0.95, payload={"content": "test1"})]
        mock_qdrant_client.search.return_value = mock_results

        # Test with numpy array
        query_vector = np.array([0.1, 0.2, 0.3, 0.4])
        results = vector_store_manager.search_vectors(
            collection_name="test-collection",
            query_vector=query_vector,
            limit=10
        )

        # Verify results
        assert len(results) == 1

        # Verify vector was converted to list
        call_args = mock_qdrant_client.search.call_args
        assert isinstance(call_args[1]['query_vector'], list)

    def test_get_vector_success(self, vector_store_manager, mock_qdrant_client):
        """Test successful vector retrieval"""
        vector_store_manager.client = mock_qdrant_client

        # Mock retrieve result
        mock_point = Mock()
        mock_point.id = "test-id"
        mock_point.vector = [0.1, 0.2, 0.3]
        mock_point.payload = {"content": "test"}
        mock_qdrant_client.retrieve.return_value = [mock_point]

        # Test vector retrieval
        result = vector_store_manager.get_vector("test-collection", "test-id")

        # Verify result
        assert result is not None
        assert result['id'] == "test-id"
        assert result['vector'] == [0.1, 0.2, 0.3]
        assert result['payload']['content'] == "test"

        # Verify Qdrant client was called
        mock_qdrant_client.retrieve.assert_called_once()
        call_args = mock_qdrant_client.retrieve.call_args
        assert call_args[1]['collection_name'] == "test-collection"
        assert call_args[1]['ids'] == ["test-id"]

    def test_get_vector_not_found(self, vector_store_manager, mock_qdrant_client):
        """Test vector retrieval when not found"""
        vector_store_manager.client = mock_qdrant_client

        # Mock no results
        mock_qdrant_client.retrieve.return_value = []

        # Test vector retrieval
        result = vector_store_manager.get_vector("test-collection", "nonexistent-id")

        # Verify result
        assert result is None

    def test_delete_vectors_success(self, vector_store_manager, mock_qdrant_client):
        """Test successful vector deletion"""
        vector_store_manager.client = mock_qdrant_client

        # Test vector deletion
        vector_ids = ["id1", "id2", "id3"]
        result = vector_store_manager.delete_vectors("test-collection", vector_ids)

        # Verify result
        assert result is True

        # Verify Qdrant client was called
        mock_qdrant_client.delete.assert_called_once()
        call_args = mock_qdrant_client.delete.call_args
        assert call_args[1]['collection_name'] == "test-collection"
        assert call_args[1]['points_selector'] == vector_ids

    def test_delete_vectors_failure(self, vector_store_manager, mock_qdrant_client):
        """Test vector deletion failure"""
        vector_store_manager.client = mock_qdrant_client

        # Mock deletion failure
        mock_qdrant_client.delete.side_effect = Exception("Deletion failed")

        # Test vector deletion
        vector_ids = ["id1", "id2"]
        result = vector_store_manager.delete_vectors("test-collection", vector_ids)

        # Verify result
        assert result is False

    def test_update_vector_payload_success(self, vector_store_manager, mock_qdrant_client):
        """Test successful vector payload update"""
        vector_store_manager.client = mock_qdrant_client

        # Test payload update
        payload = {"updated": "data", "timestamp": "2024-01-01"}
        result = vector_store_manager.update_vector_payload("test-collection", "test-id", payload)

        # Verify result
        assert result is True

        # Verify Qdrant client was called
        mock_qdrant_client.set_payload.assert_called_once()
        call_args = mock_qdrant_client.set_payload.call_args
        assert call_args[1]['collection_name'] == "test-collection"
        assert call_args[1]['payload'] == payload
        assert call_args[1]['points'] == ["test-id"]

    def test_update_vector_payload_failure(self, vector_store_manager, mock_qdrant_client):
        """Test vector payload update failure"""
        vector_store_manager.client = mock_qdrant_client

        # Mock update failure
        mock_qdrant_client.set_payload.side_effect = Exception("Update failed")

        # Test payload update
        payload = {"updated": "data"}
        result = vector_store_manager.update_vector_payload("test-collection", "test-id", payload)

        # Verify result
        assert result is False

    def test_get_collection_info_success(self, vector_store_manager, mock_qdrant_client):
        """Test successful collection info retrieval"""
        vector_store_manager.client = mock_qdrant_client

        # Mock collection info
        mock_info = Mock()
        mock_info.vectors_count = 1000
        mock_info.indexed_vectors_count = 1000
        mock_info.points_count = 1000
        mock_info.segments_count = 5
        mock_info.config.params.vectors.size = 384
        mock_info.config.params.vectors.distance = Distance.COSINE
        mock_qdrant_client.get_collection.return_value = mock_info

        # Test collection info retrieval
        result = vector_store_manager.get_collection_info("test-collection")

        # Verify result
        assert result['name'] == "test-collection"
        assert result['vectors_count'] == 1000
        assert result['points_count'] == 1000
        assert result['config']['vector_size'] == 384
        assert result['config']['distance'] == "Cosine"

    def test_get_collection_info_failure(self, vector_store_manager, mock_qdrant_client):
        """Test collection info retrieval failure"""
        vector_store_manager.client = mock_qdrant_client

        # Mock failure
        mock_qdrant_client.get_collection.side_effect = Exception("Collection not found")

        # Test collection info retrieval
        result = vector_store_manager.get_collection_info("nonexistent-collection")

        # Verify result
        assert result == {}

    def test_search_hybrid_success(self, vector_store_manager, mock_qdrant_client, test_vectors):
        """Test successful hybrid search"""
        vector_store_manager.client = mock_qdrant_client

        # Mock search results for different modalities
        mock_text_results = [Mock(id="text1", score=0.95, payload={"content": "text1"})]
        mock_image_results = [Mock(id="img1", score=0.87, payload={"content": "image1"})]
        mock_video_results = [Mock(id="vid1", score=0.82, payload={"content": "video1"})]

        def search_side_effect(collection_name, **kwargs):
            if "text" in collection_name:
                return mock_text_results
            elif "image" in collection_name:
                return mock_image_results
            elif "video" in collection_name:
                return mock_video_results
            return []

        mock_qdrant_client.search.side_effect = search_side_effect

        # Test hybrid search
        query_vector = test_vectors[0]
        results = vector_store_manager.search_hybrid(
            query_vector=query_vector,
            query_text="test query",
            limit=10,
            modalities=['text', 'image', 'video']
        )

        # Verify results
        assert len(results) == 3
        assert results[0]['score'] == 0.95  # Highest score first
        assert results[0]['modality'] == 'text'
        assert results[1]['modality'] == 'image'
        assert results[2]['modality'] == 'video'

    def test_search_hybrid_with_specific_modalities(self, vector_store_manager, mock_qdrant_client, test_vectors):
        """Test hybrid search with specific modalities"""
        vector_store_manager.client = mock_qdrant_client

        # Mock search results
        mock_text_results = [Mock(id="text1", score=0.95, payload={"content": "text1"})]
        mock_qdrant_client.search.return_value = mock_text_results

        # Test hybrid search with only text modality
        query_vector = test_vectors[0]
        results = vector_store_manager.search_hybrid(
            query_vector=query_vector,
            limit=10,
            modalities=['text']
        )

        # Verify results
        assert len(results) == 1
        assert results[0]['modality'] == 'text'

    def test_search_hybrid_with_score_threshold(self, vector_store_manager, mock_qdrant_client, test_vectors):
        """Test hybrid search with score threshold"""
        vector_store_manager.client = mock_qdrant_client

        # Mock search results
        mock_results = [Mock(id="result1", score=0.95, payload={"content": "test1"})]
        mock_qdrant_client.search.return_value = mock_results

        # Test hybrid search with score threshold
        query_vector = test_vectors[0]
        results = vector_store_manager.search_hybrid(
            query_vector=query_vector,
            limit=10,
            score_threshold=0.8
        )

        # Verify results
        assert len(results) == 1

        # Verify score threshold was passed
        call_args = mock_qdrant_client.search.call_args
        assert call_args[1]['score_threshold'] == 0.8

    def test_get_stats_success(self, vector_store_manager, mock_qdrant_client):
        """Test successful stats retrieval"""
        vector_store_manager.client = mock_qdrant_client

        # Mock collection info
        mock_info = Mock()
        mock_info.vectors_count = 1000
        mock_info.indexed_vectors_count = 1000
        mock_info.points_count = 1000
        mock_info.segments_count = 5
        mock_info.config.params.vectors.size = 384
        mock_info.config.params.vectors.distance = Distance.COSINE
        mock_qdrant_client.get_collection.return_value = mock_info

        # Test stats retrieval
        result = vector_store_manager.get_stats()

        # Verify result
        assert 'text' in result
        assert 'image' in result
        assert 'video' in result
        assert result['text']['vectors_count'] == 1000

    def test_get_stats_with_missing_collection(self, vector_store_manager, mock_qdrant_client):
        """Test stats retrieval with missing collection"""
        vector_store_manager.client = mock_qdrant_client

        # Mock one collection missing
        def get_collection_side_effect(collection_name):
            if collection_name == "test-text":
                mock_info = Mock()
                mock_info.vectors_count = 1000
                mock_info.indexed_vectors_count = 1000
                mock_info.points_count = 1000
                mock_info.segments_count = 5
                mock_info.config.params.vectors.size = 384
                mock_info.config.params.vectors.distance = Distance.COSINE
                return mock_info
            else:
                raise Exception("Collection not found")

        mock_qdrant_client.get_collection.side_effect = get_collection_side_effect

        # Test stats retrieval
        result = vector_store_manager.get_stats()

        # Verify result
        assert result['text']['vectors_count'] == 1000
        assert result['image']['status'] == "not_found"
        assert result['video']['status'] == "not_found"

    def test_vector_store_manager_initialization(self, vector_store_manager):
        """Test VectorStoreManager initialization"""
        # Verify initial state
        assert vector_store_manager.client is None
        assert isinstance(vector_store_manager.collections, dict)
        assert len(vector_store_manager.collections) == 3
        assert "text" in vector_store_manager.collections
        assert "image" in vector_store_manager.collections
        assert "video" in vector_store_manager.collections
        assert vector_store_manager.vector_size == 384

    def test_add_vectors_with_empty_input(self, vector_store_manager, mock_qdrant_client):
        """Test vector addition with empty input"""
        vector_store_manager.client = mock_qdrant_client

        # Test with empty vectors
        vector_ids = vector_store_manager.add_vectors(
            collection_name="test-collection",
            vectors=[],
            metadata_list=[]
        )

        # Verify result
        assert vector_ids == []

        # Verify Qdrant client was called with empty points
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        assert len(call_args[1]['points']) == 0

    def test_search_vectors_with_empty_results(self, vector_store_manager, mock_qdrant_client, test_vectors):
        """Test vector search with empty results"""
        vector_store_manager.client = mock_qdrant_client

        # Mock empty results
        mock_qdrant_client.search.return_value = []

        # Test vector search
        query_vector = test_vectors[0]
        results = vector_store_manager.search_vectors(
            collection_name="test-collection",
            query_vector=query_vector,
            limit=10
        )

        # Verify results
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_hybrid_with_empty_results(self, vector_store_manager, mock_qdrant_client, test_vectors):
        """Test hybrid search with empty results"""
        vector_store_manager.client = mock_qdrant_client

        # Mock empty results
        mock_qdrant_client.search.return_value = []

        # Test hybrid search
        query_vector = test_vectors[0]
        results = vector_store_manager.search_hybrid(
            query_vector=query_vector,
            limit=10
        )

        # Verify results
        assert isinstance(results, list)
        assert len(results) == 0