"""
Redis cache manager for multimodal worker service
"""
import json
import hashlib
import logging
import pickle
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

import redis.asyncio as aioredis
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)


class ModelCacheManager:
    """Redis cache manager for multimodal worker model operations"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.connected = False
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = aioredis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                encoding="utf-8",
                decode_responses=False  # We need binary data for model caching
            )
            
            # Test connection
            await self.redis.ping()
            self.connected = True
            logger.info(f"Connected to Redis at {settings.redis_host}:{settings.redis_port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connected = False
            # Continue without caching if Redis is unavailable
            self.redis = None
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self.connected = False
            logger.info("Redis connection closed")
    
    def _generate_model_key(self, model_name: str, model_type: str, **kwargs) -> str:
        """Generate a cache key for model data"""
        cache_data = {
            "model_name": model_name,
            "model_type": model_type,
            "params": kwargs
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        return f"model:{model_type}:{cache_hash}"
    
    def _generate_embedding_key(self, content_hash: str, model_name: str) -> str:
        """Generate a cache key for embeddings"""
        return f"embedding:{model_name}:{content_hash}"
    
    async def get_model_metadata(self, model_name: str, model_type: str) -> Optional[Dict[str, Any]]:
        """Get cached model metadata"""
        if not self.connected:
            return None
            
        try:
            cache_key = self._generate_model_key(model_name, model_type)
            cached_data = await self.redis.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for model metadata: {model_name}")
                return json.loads(cached_data.decode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error retrieving model metadata from cache: {e}")
        
        return None
    
    async def set_model_metadata(self, model_name: str, model_type: str, 
                               metadata: Dict[str, Any], ttl: int = 86400) -> bool:
        """Cache model metadata"""
        if not self.connected:
            return False
            
        try:
            cache_key = self._generate_model_key(model_name, model_type)
            
            # Add cache metadata
            cache_data = {
                "metadata": metadata,
                "cached_at": datetime.utcnow().isoformat(),
                "model_name": model_name,
                "model_type": model_type
            }
            
            await self.redis.setex(cache_key, ttl, json.dumps(cache_data))
            logger.debug(f"Cached model metadata for: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching model metadata: {e}")
            return False
    
    async def get_embedding(self, content_hash: str, model_name: str) -> Optional[np.ndarray]:
        """Get cached embedding"""
        if not self.connected:
            return None
            
        try:
            cache_key = self._generate_embedding_key(content_hash, model_name)
            cached_data = await self.redis.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for embedding: {content_hash}")
                # Deserialize numpy array
                return pickle.loads(cached_data)
            
        except Exception as e:
            logger.error(f"Error retrieving embedding from cache: {e}")
        
        return None
    
    async def set_embedding(self, content_hash: str, model_name: str, 
                          embedding: np.ndarray, ttl: int = 86400) -> bool:
        """Cache embedding"""
        if not self.connected:
            return False
            
        try:
            cache_key = self._generate_embedding_key(content_hash, model_name)
            
            # Serialize numpy array
            serialized_embedding = pickle.dumps(embedding)
            await self.redis.setex(cache_key, ttl, serialized_embedding)
            logger.debug(f"Cached embedding for: {content_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching embedding: {e}")
            return False
    
    async def get_processing_result(self, file_hash: str, operation: str) -> Optional[Dict[str, Any]]:
        """Get cached processing result"""
        if not self.connected:
            return None
            
        try:
            cache_key = f"processing:{operation}:{file_hash}"
            cached_data = await self.redis.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for processing result: {operation}:{file_hash}")
                return json.loads(cached_data.decode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error retrieving processing result from cache: {e}")
        
        return None
    
    async def set_processing_result(self, file_hash: str, operation: str, 
                                  result: Dict[str, Any], ttl: int = 3600) -> bool:
        """Cache processing result"""
        if not self.connected:
            return False
            
        try:
            cache_key = f"processing:{operation}:{file_hash}"
            
            # Add cache metadata
            cache_data = {
                "result": result,
                "cached_at": datetime.utcnow().isoformat(),
                "file_hash": file_hash,
                "operation": operation
            }
            
            await self.redis.setex(cache_key, ttl, json.dumps(cache_data))
            logger.debug(f"Cached processing result for: {operation}:{file_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching processing result: {e}")
            return False
    
    async def invalidate_file_cache(self, file_hash: str) -> int:
        """Invalidate all cache entries for a specific file"""
        if not self.connected:
            return 0
            
        try:
            # Find all cache keys related to this file
            patterns = [
                f"embedding:*:{file_hash}",
                f"processing:*:{file_hash}"
            ]
            
            deleted_count = 0
            for pattern in patterns:
                keys = await self.redis.keys(pattern)
                if keys:
                    deleted = await self.redis.delete(*keys)
                    deleted_count += deleted
            
            logger.info(f"Invalidated {deleted_count} cache entries for file: {file_hash}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error invalidating file cache: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.connected:
            return {"connected": False}
            
        try:
            info = await self.redis.info()
            stats = {
                "connected": True,
                "memory_used": info.get("used_memory_human", "unknown"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "connected_clients": info.get("connected_clients", 0)
            }
            
            # Calculate hit rate
            hits = stats["keyspace_hits"]
            misses = stats["keyspace_misses"]
            total = hits + misses
            stats["hit_rate"] = (hits / total * 100) if total > 0 else 0
            
            # Count cache entries by type
            model_keys = await self.redis.keys("model:*")
            embedding_keys = await self.redis.keys("embedding:*")
            processing_keys = await self.redis.keys("processing:*")
            
            stats["cache_counts"] = {
                "models": len(model_keys),
                "embeddings": len(embedding_keys),
                "processing_results": len(processing_keys)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"connected": False, "error": str(e)}
    
    async def clear_all_cache(self) -> bool:
        """Clear all cache entries"""
        if not self.connected:
            return False
            
        try:
            await self.redis.flushdb()
            logger.info("Cleared all cache entries")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False


# Global cache manager instance
model_cache_manager = ModelCacheManager()
