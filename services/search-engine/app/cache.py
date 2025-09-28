"""
Redis caching operations for the search engine service
"""
import logging
import json
import hashlib
from typing import List, Dict, Any, Optional, Union
import redis.asyncio as redis
from datetime import datetime, timedelta

from .config import settings
from .models import SearchResponse, AutocompleteResponse, SearchSuggestion

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages Redis caching operations for search results and analytics"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._start_time = datetime.utcnow()
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate a cache key from parameters"""
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        key_data = f"{prefix}:{':'.join(f'{k}={v}' for k, v in sorted_kwargs)}"
        
        # Hash long keys to avoid Redis key length limits
        if len(key_data) > 200:
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        
        return key_data
    
    async def get_search_results(
        self,
        query: str,
        search_type: str,
        content_types: Optional[List[str]] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached search results"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(
                "search_results",
                query=query,
                search_type=search_type,
                content_types=','.join(content_types) if content_types else 'all',
                limit=limit,
                filters=json.dumps(filters, sort_keys=True) if filters else 'none'
            )
            
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached search results: {e}")
            return None
    
    async def set_search_results(
        self,
        query: str,
        search_type: str,
        results: Dict[str, Any],
        content_types: Optional[List[str]] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache search results"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(
                "search_results",
                query=query,
                search_type=search_type,
                content_types=','.join(content_types) if content_types else 'all',
                limit=limit,
                filters=json.dumps(filters, sort_keys=True) if filters else 'none'
            )
            
            # Add cache metadata
            cache_data = {
                'results': results,
                'cached_at': datetime.utcnow().isoformat(),
                'query': query,
                'search_type': search_type
            }
            
            ttl = ttl or settings.cache_ttl
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache search results: {e}")
            return False
    
    async def get_autocomplete_suggestions(
        self,
        query: str,
        limit: int = 10
    ) -> Optional[List[str]]:
        """Get cached autocomplete suggestions"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(
                "autocomplete",
                query=query,
                limit=limit
            )
            
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached autocomplete suggestions: {e}")
            return None
    
    async def set_autocomplete_suggestions(
        self,
        query: str,
        suggestions: List[str],
        limit: int = 10,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache autocomplete suggestions"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(
                "autocomplete",
                query=query,
                limit=limit
            )
            
            ttl = ttl or (settings.cache_ttl // 2)  # Shorter TTL for autocomplete
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(suggestions)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache autocomplete suggestions: {e}")
            return False
    
    async def get_search_suggestions(
        self,
        query: str,
        limit: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached search suggestions"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(
                "search_suggestions",
                query=query,
                limit=limit
            )
            
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached search suggestions: {e}")
            return None
    
    async def set_search_suggestions(
        self,
        query: str,
        suggestions: List[Dict[str, Any]],
        limit: int = 10,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache search suggestions"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(
                "search_suggestions",
                query=query,
                limit=limit
            )
            
            ttl = ttl or (settings.cache_ttl // 2)  # Shorter TTL for suggestions
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(suggestions, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache search suggestions: {e}")
            return False
    
    async def get_user_search_history(
        self,
        user_id: str,
        limit: int = 20
    ) -> Optional[List[str]]:
        """Get cached user search history"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"user_history:{user_id}"
            
            # Get recent searches from sorted set
            searches = await self.redis_client.zrevrange(
                cache_key,
                0,
                limit - 1
            )
            
            return searches if searches else None
            
        except Exception as e:
            logger.error(f"Failed to get user search history: {e}")
            return None
    
    async def add_to_user_search_history(
        self,
        user_id: str,
        query: str,
        max_history: int = 100
    ) -> bool:
        """Add query to user search history"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = f"user_history:{user_id}"
            timestamp = datetime.utcnow().timestamp()
            
            # Add to sorted set with timestamp as score
            await self.redis_client.zadd(cache_key, {query: timestamp})
            
            # Trim to max_history size
            await self.redis_client.zremrangebyrank(cache_key, 0, -max_history - 1)
            
            # Set expiration
            await self.redis_client.expire(cache_key, settings.cache_ttl * 7)  # 7 days
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add to user search history: {e}")
            return False
    
    async def get_popular_queries(
        self,
        limit: int = 20,
        time_window_hours: int = 24
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached popular queries"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"popular_queries:{time_window_hours}h"
            
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached popular queries: {e}")
            return None
    
    async def set_popular_queries(
        self,
        queries: List[Dict[str, Any]],
        time_window_hours: int = 24,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache popular queries"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = f"popular_queries:{time_window_hours}h"
            
            ttl = ttl or (settings.cache_ttl // 4)  # Shorter TTL for popular queries
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(queries, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache popular queries: {e}")
            return False
    
    async def increment_query_frequency(
        self,
        query: str,
        increment: int = 1
    ) -> int:
        """Increment query frequency counter"""
        if not self.redis_client:
            return 0
        
        try:
            cache_key = f"query_freq:{query}"
            
            # Increment counter
            new_count = await self.redis_client.incrby(cache_key, increment)
            
            # Set expiration if this is the first increment
            if new_count == increment:
                await self.redis_client.expire(cache_key, settings.cache_ttl * 24)  # 24 hours
            
            return new_count
            
        except Exception as e:
            logger.error(f"Failed to increment query frequency: {e}")
            return 0
    
    async def get_query_frequency(self, query: str) -> int:
        """Get query frequency"""
        if not self.redis_client:
            return 0
        
        try:
            cache_key = f"query_freq:{query}"
            count = await self.redis_client.get(cache_key)
            return int(count) if count else 0
            
        except Exception as e:
            logger.error(f"Failed to get query frequency: {e}")
            return 0
    
    async def invalidate_search_cache(self, pattern: str) -> int:
        """Invalidate search cache entries matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(f"search_results:*{pattern}*")
            if keys:
                deleted_count = await self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted_count} search cache entries matching '{pattern}'")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to invalidate search cache: {e}")
            return 0
    
    async def clear_all_cache(self) -> bool:
        """Clear all cache entries"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.flushdb()
            logger.info("Cleared all cache entries")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear all cache: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {}
        
        try:
            info = await self.redis_client.info()
            
            # Count different types of cache entries
            search_keys = await self.redis_client.keys("search_results:*")
            autocomplete_keys = await self.redis_client.keys("autocomplete:*")
            suggestion_keys = await self.redis_client.keys("search_suggestions:*")
            history_keys = await self.redis_client.keys("user_history:*")
            popular_keys = await self.redis_client.keys("popular_queries:*")
            freq_keys = await self.redis_client.keys("query_freq:*")
            
            return {
                'redis_version': info.get('redis_version', 'unknown'),
                'used_memory_human': info.get('used_memory_human', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'cache_entries': {
                    'search_results': len(search_keys),
                    'autocomplete': len(autocomplete_keys),
                    'search_suggestions': len(suggestion_keys),
                    'user_history': len(history_keys),
                    'popular_queries': len(popular_keys),
                    'query_frequency': len(freq_keys)
                },
                'total_cache_entries': len(search_keys) + len(autocomplete_keys) + 
                                     len(suggestion_keys) + len(history_keys) + 
                                     len(popular_keys) + len(freq_keys)
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            if not self.redis_client:
                return False
            
            await self.redis_client.ping()
            return True
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def get_uptime(self) -> float:
        """Get service uptime in seconds"""
        return (datetime.utcnow() - self._start_time).total_seconds()

# Global cache manager instance
cache_manager = CacheManager()