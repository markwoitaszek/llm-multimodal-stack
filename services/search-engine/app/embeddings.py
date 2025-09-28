"""
Embedding Generation Service
"""
import asyncio
from typing import List, Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
from functools import lru_cache

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self):
        self.model = None
        self.model_name = settings.embedding_model
        self.embedding_dimension = settings.embedding_dimension
    
    async def initialize(self):
        """Initialize embedding model"""
        try:
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                lambda: SentenceTransformer(self.model_name)
            )
            
            # Verify embedding dimension
            test_embedding = await self.generate_embedding("test")
            if len(test_embedding) != self.embedding_dimension:
                logger.warning(f"Model embedding dimension ({len(test_embedding)}) doesn't match config ({self.embedding_dimension})")
            
            logger.info(f"Embedding service initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {str(e)}")
            raise Exception(f"Embedding service initialization failed: {str(e)}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            if not self.model:
                raise Exception("Embedding model not initialized")
            
            # Clean and truncate text
            text = self._clean_text(text)
            
            # Generate embedding in thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.model.encode(text, convert_to_numpy=True)
            )
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            if not self.model:
                raise Exception("Embedding model not initialized")
            
            # Clean texts
            cleaned_texts = [self._clean_text(text) for text in texts]
            
            # Generate embeddings in thread pool
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(cleaned_texts, convert_to_numpy=True)
            )
            
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise Exception(f"Failed to generate batch embeddings: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text for embedding"""
        if not text:
            return ""
        
        # Truncate if too long
        if len(text) > settings.max_query_length:
            text = text[:settings.max_query_length]
        
        # Basic cleaning
        text = text.strip()
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = ' '.join(text.split())  # Remove extra whitespace
        
        return text
    
    async def get_embedding_info(self) -> Dict[str, Any]:
        """Get embedding service information"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
            "max_query_length": settings.max_query_length,
            "initialized": self.model is not None
        }
    
    async def health_check(self) -> bool:
        """Check embedding service health"""
        try:
            if not self.model:
                return False
            
            # Test embedding generation
            test_embedding = await self.generate_embedding("health check")
            return len(test_embedding) == self.embedding_dimension
            
        except Exception as e:
            logger.error(f"Embedding service health check failed: {str(e)}")
            return False


class CachedEmbeddingService:
    """Embedding service with caching"""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self._cache = {}
        self._cache_size = 1000  # Maximum cache size
    
    async def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """Generate embedding with caching"""
        if use_cache and text in self._cache:
            return self._cache[text]
        
        # Generate embedding
        embedding = await self.embedding_service.generate_embedding(text)
        
        # Cache if enabled
        if use_cache:
            self._add_to_cache(text, embedding)
        
        return embedding
    
    async def generate_embeddings_batch(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """Generate batch embeddings with caching"""
        embeddings = []
        texts_to_generate = []
        indices_to_generate = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            if use_cache and text in self._cache:
                embeddings.append(self._cache[text])
            else:
                embeddings.append(None)  # Placeholder
                texts_to_generate.append(text)
                indices_to_generate.append(i)
        
        # Generate missing embeddings
        if texts_to_generate:
            generated_embeddings = await self.embedding_service.generate_embeddings_batch(texts_to_generate)
            
            # Fill in the embeddings and cache them
            for i, embedding in enumerate(generated_embeddings):
                original_index = indices_to_generate[i]
                original_text = texts_to_generate[i]
                
                embeddings[original_index] = embedding
                
                if use_cache:
                    self._add_to_cache(original_text, embedding)
        
        return embeddings
    
    def _add_to_cache(self, text: str, embedding: List[float]):
        """Add embedding to cache with size limit"""
        if len(self._cache) >= self._cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[text] = embedding
    
    def clear_cache(self):
        """Clear embedding cache"""
        self._cache.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        return {
            "cache_size": len(self._cache),
            "max_cache_size": self._cache_size,
            "cache_hit_ratio": 0.0  # Could be calculated with hit/miss counters
        }


# Global embedding service instances
embedding_service = EmbeddingService()
cached_embedding_service = CachedEmbeddingService(embedding_service)