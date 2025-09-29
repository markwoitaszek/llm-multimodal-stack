"""
Vector Store Tests
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from app.vector_store import VectorStoreManager
from app.config import settings


class TestVectorStoreManager:
    """Test Vector Store Manager functionality"""
    
    @pytest.fixture
    def vector_store_manager(self):
        """Create vector store manager instance"""
        return VectorStoreManager()
    
    @pytest.fixture
    def sample_embedding(self):
        """Sample embedding vector"""
        return [0.1] * 384
    
    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata"""
        return {
            "content_type": "text",
            "source": "test",
            "category": "sample"
        }
    
    @pytest.mark.asyncio
    async def test_initialize(self, vector_store_manager):
        """Test vector store initialization"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Mock collection check
            mock_collections = MagicMock()
            mock_collections.collections = []
            mock_client.get_collections.return_value = mock_collections
            
            # Mock collection creation
            mock_client.create_collection.return_value = None
            
            # Initialize
            await vector_store_manager.initialize()
            
            assert vector_store_manager.client is not None
            mock_client.get_collections.assert_called_once()
            mock_client.create_collection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_existing_collection(self, vector_store_manager):
        """Test initialization with existing collection"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Mock existing collection
            mock_collection = MagicMock()
            mock_collection.name = settings.qdrant_collection_name
            
            mock_collections = MagicMock()
            mock_collections.collections = [mock_collection]
            mock_client.get_collections.return_value = mock_collections
            
            # Initialize
            await vector_store_manager.initialize()
            
            # Should not create collection
            mock_client.create_collection.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_upsert_embedding(self, vector_store_manager, sample_embedding, sample_metadata):
        """Test upserting embedding"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Mock upsert
            mock_client.upsert.return_value = None
            
            # Test upsert
            success = await vector_store_manager.upsert_embedding(
                content_id="test_1",
                embedding=sample_embedding,
                metadata=sample_metadata
            )
            
            assert success is True
            mock_client.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upsert_embedding_dimension_error(self, vector_store_manager):
        """Test upserting embedding with wrong dimension"""
        wrong_embedding = [0.1] * 100  # Wrong dimension
        
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Test upsert with wrong dimension
            success = await vector_store_manager.upsert_embedding(
                content_id="test_1",
                embedding=wrong_embedding
            )
            
            assert success is False
            mock_client.upsert.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_search_similar(self, vector_store_manager, sample_embedding):
        """Test searching similar embeddings"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Mock search result
            mock_hit = MagicMock()
            mock_hit.id = "test_result_1"
            mock_hit.score = 0.95
            mock_hit.payload = {"content_type": "text"}
            
            mock_client.search.return_value = [mock_hit]
            
            # Test search
            results = await vector_store_manager.search_similar(
                query_embedding=sample_embedding,
                limit=10
            )
            
            assert len(results) == 1
            assert results[0]["id"] == "test_result_1"
            assert results[0]["score"] == 0.95
            assert results[0]["metadata"] == {"content_type": "text"}
    
    @pytest.mark.asyncio
    async def test_search_similar_with_filters(self, vector_store_manager, sample_embedding):
        """Test searching with filters"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Mock search result
            mock_hit = MagicMock()
            mock_hit.id = "test_result_1"
            mock_hit.score = 0.95
            mock_hit.payload = {"content_type": "text"}
            
            mock_client.search.return_value = [mock_hit]
            
            # Test search with filters
            filters = {"content_type": "text"}
            results = await vector_store_manager.search_similar(
                query_embedding=sample_embedding,
                limit=10,
                filters=filters
            )
            
            assert len(results) == 1
            mock_client.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_similar_dimension_error(self, vector_store_manager):
        """Test searching with wrong embedding dimension"""
        wrong_embedding = [0.1] * 100  # Wrong dimension
        
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Test search with wrong dimension
            results = await vector_store_manager.search_similar(
                query_embedding=wrong_embedding,
                limit=10
            )
            
            assert results == []
            mock_client.search.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_embedding(self, vector_store_manager):
        """Test deleting embedding"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Mock delete
            mock_client.delete.return_value = None
            
            # Test delete
            success = await vector_store_manager.delete_embedding("test_1")
            
            assert success is True
            mock_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_embedding(self, vector_store_manager):
        """Test getting embedding"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Mock retrieve result
            mock_point = MagicMock()
            mock_point.vector = [0.1] * 384
            
            mock_client.retrieve.return_value = [mock_point]
            
            # Test get embedding
            embedding = await vector_store_manager.get_embedding("test_1")
            
            assert embedding == [0.1] * 384
            mock_client.retrieve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_embedding_not_found(self, vector_store_manager):
        """Test getting non-existent embedding"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Mock empty result
            mock_client.retrieve.return_value = []
            
            # Test get embedding
            embedding = await vector_store_manager.get_embedding("nonexistent")
            
            assert embedding is None
    
    @pytest.mark.asyncio
    async def test_get_collection_info(self, vector_store_manager):
        """Test getting collection information"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Mock collection info
            mock_config = MagicMock()
            mock_config.params.vectors.size = 384
            
            mock_collection_info = MagicMock()
            mock_collection_info.config = mock_config
            mock_collection_info.vectors_count = 100
            mock_collection_info.indexed_vectors_count = 100
            mock_collection_info.points_count = 100
            mock_collection_info.segments_count = 1
            mock_collection_info.status = "green"
            mock_collection_info.optimizer_status = "ok"
            
            mock_client.get_collection.return_value = mock_collection_info
            
            # Test get collection info
            info = await vector_store_manager.get_collection_info()
            
            assert info["name"] == 384
            assert info["vectors_count"] == 100
            assert info["points_count"] == 100
            assert info["status"] == "green"
    
    @pytest.mark.asyncio
    async def test_batch_upsert_embeddings(self, vector_store_manager):
        """Test batch upserting embeddings"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Mock upsert
            mock_client.upsert.return_value = None
            
            # Prepare batch data
            embeddings_data = [
                ("test_1", [0.1] * 384, {"type": "text"}),
                ("test_2", [0.2] * 384, {"type": "image"}),
                ("test_3", [0.3] * 384, {"type": "video"})
            ]
            
            # Test batch upsert
            count = await vector_store_manager.batch_upsert_embeddings(embeddings_data)
            
            assert count == 3
            mock_client.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_upsert_with_invalid_embeddings(self, vector_store_manager):
        """Test batch upsert with invalid embeddings"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Prepare batch data with invalid embedding
            embeddings_data = [
                ("test_1", [0.1] * 384, {"type": "text"}),
                ("test_2", [0.2] * 100, {"type": "invalid"}),  # Wrong dimension
                ("test_3", [0.3] * 384, {"type": "video"})
            ]
            
            # Test batch upsert
            count = await vector_store_manager.batch_upsert_embeddings(embeddings_data)
            
            # Should only process valid embeddings
            assert count == 2
            mock_client.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_delete_embeddings(self, vector_store_manager):
        """Test batch deleting embeddings"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Mock delete
            mock_client.delete.return_value = None
            
            # Test batch delete
            content_ids = ["test_1", "test_2", "test_3"]
            count = await vector_store_manager.batch_delete_embeddings(content_ids)
            
            assert count == 3
            mock_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check(self, vector_store_manager):
        """Test health check"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Mock healthy collection
            mock_collection_info = MagicMock()
            mock_collection_info.status = "green"
            mock_client.get_collection.return_value = mock_collection_info
            
            # Test health check
            healthy = await vector_store_manager.health_check()
            
            assert healthy is True
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, vector_store_manager):
        """Test health check when unhealthy"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Mock unhealthy collection
            mock_collection_info = MagicMock()
            mock_collection_info.status = "red"
            mock_client.get_collection.return_value = mock_collection_info
            
            # Test health check
            healthy = await vector_store_manager.health_check()
            
            assert healthy is False
    
    @pytest.mark.asyncio
    async def test_health_check_error(self, vector_store_manager):
        """Test health check with error"""
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store_manager.client = mock_client
            
            # Mock error
            mock_client.get_collection.side_effect = Exception("Connection error")
            
            # Test health check
            healthy = await vector_store_manager.health_check()
            
            assert healthy is False


class TestVectorStoreErrorHandling:
    """Test vector store error handling"""
    
    @pytest.mark.asyncio
    async def test_upsert_embedding_error(self):
        """Test error handling in upsert_embedding"""
        vector_store = VectorStoreManager()
        
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client with error
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store.client = mock_client
            
            # Mock upsert error
            mock_client.upsert.side_effect = Exception("Upsert error")
            
            # Test upsert with error
            success = await vector_store.upsert_embedding(
                content_id="test_1",
                embedding=[0.1] * 384
            )
            
            assert success is False
    
    @pytest.mark.asyncio
    async def test_search_similar_error(self):
        """Test error handling in search_similar"""
        vector_store = VectorStoreManager()
        
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client with error
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store.client = mock_client
            
            # Mock search error
            mock_client.search.side_effect = Exception("Search error")
            
            # Test search with error
            results = await vector_store.search_similar(
                query_embedding=[0.1] * 384,
                limit=10
            )
            
            assert results == []
    
    @pytest.mark.asyncio
    async def test_delete_embedding_error(self):
        """Test error handling in delete_embedding"""
        vector_store = VectorStoreManager()
        
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client with error
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store.client = mock_client
            
            # Mock delete error
            mock_client.delete.side_effect = Exception("Delete error")
            
            # Test delete with error
            success = await vector_store.delete_embedding("test_1")
            
            assert success is False


class TestVectorStoreConcurrency:
    """Test vector store concurrency"""
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent vector store operations"""
        vector_store = VectorStoreManager()
        
        with patch('app.vector_store.QdrantClient') as mock_client_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            vector_store.client = mock_client
            
            # Mock operations
            mock_client.upsert.return_value = None
            mock_client.delete.return_value = None
            
            # Create concurrent tasks
            tasks = []
            for i in range(10):
                task = vector_store.upsert_embedding(
                    content_id=f"concurrent_test_{i}",
                    embedding=[0.1] * 384
                )
                tasks.append(task)
            
            # Execute concurrently
            results = await asyncio.gather(*tasks)
            
            # All operations should succeed
            assert all(results)
            assert mock_client.upsert.call_count == 10