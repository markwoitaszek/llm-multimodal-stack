"""
Redis cache manager for retrieval proxy service
"""
import json
import hashlib
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

import aioredis
from app.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager for retrieval proxy operations"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.connected = False
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = aioredis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                encoding="utf-8",
                decode_responses=True
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
    
    def _generate_cache_key(self, prefix: str, query: str, **kwargs) -> str:
        """Generate a consistent cache key from query and parameters"""
        # Create a hash of the query and parameters
        cache_data = {
            "query": query,
            "params": kwargs
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        return f"{prefix}:{cache_hash}"
    
    async def get_search_results(self, query: str, file_type: Optional[str] = None, 
                                limit: int = 10) -> Optional[Dict[str, Any]]:
        """Get cached search results"""
        if not self.connected:
            return None
            
        try:
            cache_key = self._generate_cache_key(
                "search", query, file_type=file_type, limit=limit
            )
            cached_data = await self.redis.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for search: {query}")
                return json.loads(cached_data)
            
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
        
        return None
    
    async def set_search_results(self, query: str, results: Dict[str, Any], 
                               file_type: Optional[str] = None, limit: int = 10,
                               ttl: int = 3600) -> bool:
        """Cache search results"""
        if not self.connected:
            return False
            
        try:
            cache_key = self._generate_cache_key(
                "search", query, file_type=file_type, limit=limit
            )
            
            # Add metadata
            cache_data = {
                "results": results,
                "cached_at": datetime.utcnow().isoformat(),
                "query": query,
                "file_type": file_type,
                "limit": limit
            }
            
            await self.redis.setex(cache_key, ttl, json.dumps(cache_data))
            logger.debug(f"Cached search results for: {query}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching results: {e}")
            return False
    
    async def get_context_bundle(self, session_id: str, query: str, 
                               results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get cached context bundle"""
        if not self.connected:
            return None
            
        try:
            # Create a hash of the results to identify the bundle
            results_hash = hashlib.md5(
                json.dumps(results, sort_keys=True).encode()
            ).hexdigest()
            
            cache_key = f"context:{session_id}:{results_hash}"
            cached_data = await self.redis.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for context bundle: {session_id}")
                return json.loads(cached_data)
            
        except Exception as e:
            logger.error(f"Error retrieving context bundle from cache: {e}")
        
        return None
    
    async def set_context_bundle(self, session_id: str, query: str, 
                               results: List[Dict[str, Any]], bundle: Dict[str, Any],
                               ttl: int = 1800) -> bool:
        """Cache context bundle"""
        if not self.connected:
            return False
            
        try:
            # Create a hash of the results to identify the bundle
            results_hash = hashlib.md5(
                json.dumps(results, sort_keys=True).encode()
            ).hexdigest()
            
            cache_key = f"context:{session_id}:{results_hash}"
            
            # Add metadata
            cache_data = {
                "bundle": bundle,
                "cached_at": datetime.utcnow().isoformat(),
                "session_id": session_id,
                "query": query,
                "results_count": len(results)
            }
            
            await self.redis.setex(cache_key, ttl, json.dumps(cache_data))
            logger.debug(f"Cached context bundle for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching context bundle: {e}")
            return False
    
    async def invalidate_search_cache(self, pattern: str = "*") -> int:
        """Invalidate search cache entries matching pattern"""
        if not self.connected:
            return 0
            
        try:
            keys = await self.redis.keys(f"search:{pattern}")
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Invalidated {deleted} search cache entries")
                return deleted
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
        
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
cache_manager = CacheManager()
