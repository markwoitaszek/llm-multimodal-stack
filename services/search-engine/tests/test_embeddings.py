"""
Embedding Service Tests
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from app.embeddings import EmbeddingService, CachedEmbeddingService
from app.config import settings


class TestEmbeddingService:
    """Test Embedding Service functionality"""
    
    @pytest.fixture
    def embedding_service(self):
        """Create embedding service instance"""
        return EmbeddingService()
    
    @pytest.mark.asyncio
    async def test_initialize(self, embedding_service):
        """Test embedding service initialization"""
        with patch('app.embeddings.SentenceTransformer') as mock_model_class:
            # Setup mock model
            mock_model = MagicMock()
            mock_model.encode.return_value = [0.1] * 384
            mock_model_class.return_value = mock_model
            
            # Initialize service
            await embedding_service.initialize()
            
            assert embedding_service.model is not None
            assert embedding_service.model_name == settings.embedding_model
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, embedding_service):
        """Test generating single embedding"""
        with patch('app.embeddings.SentenceTransformer') as mock_model_class:
            # Setup mock model
            mock_model = MagicMock()
            mock_embedding = [0.1, 0.2, 0.3] + [0.0] * 381  # 384 dimensions
            mock_model.encode.return_value = mock_embedding
            mock_model_class.return_value = mock_model
            
            embedding_service.model = mock_model
            
            # Generate embedding
            result = await embedding_service.generate_embedding("test text")
            
            assert result == mock_embedding
            mock_model.encode.assert_called_once_with("test text", convert_to_numpy=True)
    
    @pytest.mark.asyncio
    async def test_generate_embedding_long_text(self, embedding_service):
        """Test generating embedding for long text"""
        with patch('app.embeddings.SentenceTransformer') as mock_model_class:
            # Setup mock model
            mock_model = MagicMock()
            mock_embedding = [0.1] * 384
            mock_model.encode.return_value = mock_embedding
            mock_model_class.return_value = mock_model
            
            embedding_service.model = mock_model
            
            # Generate embedding for long text
            long_text = "x" * 1000  # Exceeds max_query_length
            result = await embedding_service.generate_embedding(long_text)
            
            # Should be truncated
            assert result == mock_embedding
            # Verify the text was truncated
            truncated_text = long_text[:settings.max_query_length]
            mock_model.encode.assert_called_once_with(truncated_text, convert_to_numpy=True)
    
    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, embedding_service):
        """Test generating embedding for empty text"""
        with patch('app.embeddings.SentenceTransformer') as mock_model_class:
            # Setup mock model
            mock_model = MagicMock()
            mock_embedding = [0.0] * 384
            mock_model.encode.return_value = mock_embedding
            mock_model_class.return_value = mock_model
            
            embedding_service.model = mock_model
            
            # Generate embedding for empty text
            result = await embedding_service.generate_embedding("")
            
            assert result == mock_embedding
            mock_model.encode.assert_called_once_with("", convert_to_numpy=True)
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, embedding_service):
        """Test generating batch embeddings"""
        with patch('app.embeddings.SentenceTransformer') as mock_model_class:
            # Setup mock model
            mock_model = MagicMock()
            mock_embeddings = [[0.1] * 384, [0.2] * 384, [0.3] * 384]
            mock_model.encode.return_value = mock_embeddings
            mock_model_class.return_value = mock_model
            
            embedding_service.model = mock_model
            
            # Generate batch embeddings
            texts = ["text 1", "text 2", "text 3"]
            results = await embedding_service.generate_embeddings_batch(texts)
            
            assert len(results) == 3
            assert results == mock_embeddings
            mock_model.encode.assert_called_once_with(texts, convert_to_numpy=True)
    
    @pytest.mark.asyncio
    async def test_generate_embedding_not_initialized(self, embedding_service):
        """Test generating embedding when not initialized"""
        with pytest.raises(Exception, match="Embedding model not initialized"):
            await embedding_service.generate_embedding("test text")
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_not_initialized(self, embedding_service):
        """Test generating batch embeddings when not initialized"""
        with pytest.raises(Exception, match="Embedding model not initialized"):
            await embedding_service.generate_embeddings_batch(["text 1", "text 2"])
    
    @pytest.mark.asyncio
    async def test_get_embedding_info(self, embedding_service):
        """Test getting embedding service info"""
        info = await embedding_service.get_embedding_info()
        
        assert info["model_name"] == settings.embedding_model
        assert info["embedding_dimension"] == settings.embedding_dimension
        assert info["max_query_length"] == settings.max_query_length
        assert info["initialized"] is False
    
    @pytest.mark.asyncio
    async def test_health_check_initialized(self, embedding_service):
        """Test health check when initialized"""
        with patch('app.embeddings.SentenceTransformer') as mock_model_class:
            # Setup mock model
            mock_model = MagicMock()
            mock_embedding = [0.1] * 384
            mock_model.encode.return_value = mock_embedding
            mock_model_class.return_value = mock_model
            
            embedding_service.model = mock_model
            
            # Test health check
            healthy = await embedding_service.health_check()
            
            assert healthy is True
    
    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, embedding_service):
        """Test health check when not initialized"""
        healthy = await embedding_service.health_check()
        assert healthy is False
    
    @pytest.mark.asyncio
    async def test_health_check_error(self, embedding_service):
        """Test health check with error"""
        with patch('app.embeddings.SentenceTransformer') as mock_model_class:
            # Setup mock model with error
            mock_model = MagicMock()
            mock_model.encode.side_effect = Exception("Model error")
            mock_model_class.return_value = mock_model
            
            embedding_service.model = mock_model
            
            # Test health check
            healthy = await embedding_service.health_check()
            
            assert healthy is False


class TestCachedEmbeddingService:
    """Test Cached Embedding Service functionality"""
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service"""
        mock_service = MagicMock()
        mock_service.generate_embedding = AsyncMock(return_value=[0.1] * 384)
        mock_service.generate_embeddings_batch = AsyncMock(return_value=[[0.1] * 384, [0.2] * 384])
        return mock_service
    
    @pytest.fixture
    def cached_embedding_service(self, mock_embedding_service):
        """Create cached embedding service instance"""
        return CachedEmbeddingService(mock_embedding_service)
    
    @pytest.mark.asyncio
    async def test_generate_embedding_with_cache(self, cached_embedding_service, mock_embedding_service):
        """Test generating embedding with caching"""
        text = "test text"
        
        # First call - should not be cached
        result1 = await cached_embedding_service.generate_embedding(text, use_cache=True)
        
        # Second call - should be cached
        result2 = await cached_embedding_service.generate_embedding(text, use_cache=True)
        
        assert result1 == result2
        assert result1 == [0.1] * 384
        
        # Should only call underlying service once
        mock_embedding_service.generate_embedding.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_embedding_without_cache(self, cached_embedding_service, mock_embedding_service):
        """Test generating embedding without caching"""
        text = "test text"
        
        # First call
        result1 = await cached_embedding_service.generate_embedding(text, use_cache=False)
        
        # Second call
        result2 = await cached_embedding_service.generate_embedding(text, use_cache=False)
        
        assert result1 == result2
        assert result1 == [0.1] * 384
        
        # Should call underlying service twice
        assert mock_embedding_service.generate_embedding.call_count == 2
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_with_cache(self, cached_embedding_service, mock_embedding_service):
        """Test generating batch embeddings with caching"""
        texts = ["text 1", "text 2"]
        
        # First call - should not be cached
        result1 = await cached_embedding_service.generate_embeddings_batch(texts, use_cache=True)
        
        # Second call - should be cached
        result2 = await cached_embedding_service.generate_embeddings_batch(texts, use_cache=True)
        
        assert result1 == result2
        assert len(result1) == 2
        
        # Should only call underlying service once
        mock_embedding_service.generate_embeddings_batch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_mixed_cache(self, cached_embedding_service, mock_embedding_service):
        """Test generating batch embeddings with mixed cache hits"""
        # Setup individual embedding generation for cache misses
        mock_embedding_service.generate_embedding.return_value = [0.3] * 384
        
        # First batch
        texts1 = ["text 1", "text 2"]
        result1 = await cached_embedding_service.generate_embeddings_batch(texts1, use_cache=True)
        
        # Second batch with one new text
        texts2 = ["text 1", "text 3"]  # text 1 is cached, text 3 is new
        result2 = await cached_embedding_service.generate_embeddings_batch(texts2, use_cache=True)
        
        assert len(result1) == 2
        assert len(result2) == 2
        assert result2[0] == result1[0]  # text 1 should be same (cached)
        assert result2[1] == [0.3] * 384  # text 3 should be newly generated
    
    @pytest.mark.asyncio
    async def test_cache_size_limit(self, cached_embedding_service, mock_embedding_service):
        """Test cache size limit"""
        # Set small cache size
        cached_embedding_service._cache_size = 2
        
        # Add items to cache
        await cached_embedding_service.generate_embedding("text 1", use_cache=True)
        await cached_embedding_service.generate_embedding("text 2", use_cache=True)
        await cached_embedding_service.generate_embedding("text 3", use_cache=True)
        
        # Cache should only contain 2 items (oldest removed)
        assert len(cached_embedding_service._cache) == 2
        assert "text 1" not in cached_embedding_service._cache  # Should be removed
        assert "text 2" in cached_embedding_service._cache
        assert "text 3" in cached_embedding_service._cache
    
    def test_clear_cache(self, cached_embedding_service):
        """Test clearing cache"""
        # Add items to cache
        cached_embedding_service._cache["test_key"] = [0.1] * 384
        
        assert len(cached_embedding_service._cache) == 1
        
        # Clear cache
        cached_embedding_service.clear_cache()
        
        assert len(cached_embedding_service._cache) == 0
    
    def test_get_cache_info(self, cached_embedding_service):
        """Test getting cache information"""
        # Add items to cache
        cached_embedding_service._cache["test_key_1"] = [0.1] * 384
        cached_embedding_service._cache["test_key_2"] = [0.2] * 384
        
        info = cached_embedding_service.get_cache_info()
        
        assert info["cache_size"] == 2
        assert info["max_cache_size"] == 1000
        assert "cache_hit_ratio" in info


class TestEmbeddingServiceErrorHandling:
    """Test embedding service error handling"""
    
    @pytest.mark.asyncio
    async def test_generate_embedding_error(self):
        """Test error handling in generate_embedding"""
        embedding_service = EmbeddingService()
        
        with patch('app.embeddings.SentenceTransformer') as mock_model_class:
            # Setup mock model with error
            mock_model = MagicMock()
            mock_model.encode.side_effect = Exception("Encoding error")
            mock_model_class.return_value = mock_model
            
            embedding_service.model = mock_model
            
            with pytest.raises(Exception, match="Failed to generate embedding"):
                await embedding_service.generate_embedding("test text")
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_error(self):
        """Test error handling in generate_embeddings_batch"""
        embedding_service = EmbeddingService()
        
        with patch('app.embeddings.SentenceTransformer') as mock_model_class:
            # Setup mock model with error
            mock_model = MagicMock()
            mock_model.encode.side_effect = Exception("Batch encoding error")
            mock_model_class.return_value = mock_model
            
            embedding_service.model = mock_model
            
            with pytest.raises(Exception, match="Failed to generate batch embeddings"):
                await embedding_service.generate_embeddings_batch(["text 1", "text 2"])
    
    @pytest.mark.asyncio
    async def test_initialize_error(self):
        """Test error handling in initialization"""
        embedding_service = EmbeddingService()
        
        with patch('app.embeddings.SentenceTransformer', side_effect=Exception("Model loading error")):
            with pytest.raises(Exception, match="Embedding service initialization failed"):
                await embedding_service.initialize()


class TestEmbeddingServiceTextCleaning:
    """Test text cleaning functionality"""
    
    @pytest.mark.asyncio
    async def test_clean_text_whitespace(self):
        """Test text cleaning with whitespace"""
        embedding_service = EmbeddingService()
        
        # Test with extra whitespace
        cleaned = embedding_service._clean_text("  test   text  \n\r  ")
        assert cleaned == "test text"
    
    @pytest.mark.asyncio
    async def test_clean_text_truncation(self):
        """Test text cleaning with truncation"""
        embedding_service = EmbeddingService()
        
        # Test with long text
        long_text = "x" * 1000
        cleaned = embedding_service._clean_text(long_text)
        assert len(cleaned) == settings.max_query_length
    
    @pytest.mark.asyncio
    async def test_clean_text_empty(self):
        """Test text cleaning with empty text"""
        embedding_service = EmbeddingService()
        
        # Test with empty text
        cleaned = embedding_service._clean_text("")
        assert cleaned == ""
    
    @pytest.mark.asyncio
    async def test_clean_text_none(self):
        """Test text cleaning with None"""
        embedding_service = EmbeddingService()
        
        # Test with None
        cleaned = embedding_service._clean_text(None)
        assert cleaned == ""