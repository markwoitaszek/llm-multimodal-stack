"""
Redis caching functionality for user management service
"""
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
import redis.asyncio as redis
from redis.asyncio import Redis

from .config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis cache manager for user management service"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.prefix = "user_mgmt:"
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = redis.Redis(
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
            await self.redis.ping()
            logger.info("Redis cache initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis cache connection closed")
    
    def _get_key(self, key: str) -> str:
        """Get prefixed cache key"""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if not self.redis:
                return None
            
            cache_key = self._get_key(key)
            value = await self.redis.get(cache_key)
            
            if value is None:
                return None
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache"""
        try:
            if not self.redis:
                return False
            
            cache_key = self._get_key(key)
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            # Set with expiration
            if expire:
                if isinstance(expire, timedelta):
                    expire_seconds = int(expire.total_seconds())
                else:
                    expire_seconds = expire
                
                await self.redis.setex(cache_key, expire_seconds, serialized_value)
            else:
                await self.redis.set(cache_key, serialized_value)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if not self.redis:
                return False
            
            cache_key = self._get_key(key)
            result = await self.redis.delete(cache_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if not self.redis:
                return False
            
            cache_key = self._get_key(key)
            return await self.redis.exists(cache_key) > 0
            
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        try:
            if not self.redis:
                return False
            
            cache_key = self._get_key(key)
            return await self.redis.expire(cache_key, seconds)
            
        except Exception as e:
            logger.error(f"Failed to set expiration for cache key {key}: {e}")
            return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        try:
            if not self.redis:
                return {}
            
            cache_keys = [self._get_key(key) for key in keys]
            values = await self.redis.mget(cache_keys)
            
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = value
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get multiple cache keys: {e}")
            return {}
    
    async def set_many(
        self,
        mapping: Dict[str, Any],
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set multiple values in cache"""
        try:
            if not self.redis:
                return False
            
            cache_mapping = {}
            for key, value in mapping.items():
                cache_key = self._get_key(key)
                if isinstance(value, (dict, list)):
                    cache_mapping[cache_key] = json.dumps(value)
                else:
                    cache_mapping[cache_key] = str(value)
            
            if expire:
                if isinstance(expire, timedelta):
                    expire_seconds = int(expire.total_seconds())
                else:
                    expire_seconds = expire
                
                # Set with expiration for each key
                pipe = self.redis.pipeline()
                for cache_key, value in cache_mapping.items():
                    pipe.setex(cache_key, expire_seconds, value)
                await pipe.execute()
            else:
                await self.redis.mset(cache_mapping)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set multiple cache keys: {e}")
            return False
    
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys from cache"""
        try:
            if not self.redis:
                return 0
            
            cache_keys = [self._get_key(key) for key in keys]
            return await self.redis.delete(*cache_keys)
            
        except Exception as e:
            logger.error(f"Failed to delete multiple cache keys: {e}")
            return 0
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            if not self.redis:
                return 0
            
            cache_pattern = self._get_key(pattern)
            keys = await self.redis.keys(cache_pattern)
            
            if keys:
                return await self.redis.delete(*keys)
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear cache pattern {pattern}: {e}")
            return 0
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment numeric value in cache"""
        try:
            if not self.redis:
                return None
            
            cache_key = self._get_key(key)
            return await self.redis.incrby(cache_key, amount)
            
        except Exception as e:
            logger.error(f"Failed to increment cache key {key}: {e}")
            return None
    
    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement numeric value in cache"""
        try:
            if not self.redis:
                return None
            
            cache_key = self._get_key(key)
            return await self.redis.decrby(cache_key, amount)
            
        except Exception as e:
            logger.error(f"Failed to decrement cache key {key}: {e}")
            return None

# Global cache manager instance
cache_manager = CacheManager()

# Cache decorators and utilities
def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_parts = []
    
    for arg in args:
        if hasattr(arg, 'id'):
            key_parts.append(f"{type(arg).__name__}:{arg.id}")
        else:
            key_parts.append(str(arg))
    
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")
    
    return ":".join(key_parts)

async def cached_user(user_id: str, expire: int = 300) -> Optional[Dict[str, Any]]:
    """Get cached user data"""
    key = f"user:{user_id}"
    return await cache_manager.get(key)

async def cache_user(user_id: str, user_data: Dict[str, Any], expire: int = 300):
    """Cache user data"""
    key = f"user:{user_id}"
    await cache_manager.set(key, user_data, expire)

async def invalidate_user_cache(user_id: str):
    """Invalidate user cache"""
    key = f"user:{user_id}"
    await cache_manager.delete(key)

async def cached_tenant(tenant_id: str, expire: int = 600) -> Optional[Dict[str, Any]]:
    """Get cached tenant data"""
    key = f"tenant:{tenant_id}"
    return await cache_manager.get(key)

async def cache_tenant(tenant_id: str, tenant_data: Dict[str, Any], expire: int = 600):
    """Cache tenant data"""
    key = f"tenant:{tenant_id}"
    await cache_manager.set(key, tenant_data, expire)

async def invalidate_tenant_cache(tenant_id: str):
    """Invalidate tenant cache"""
    key = f"tenant:{tenant_id}"
    await cache_manager.delete(key)

async def cached_session(session_token: str, expire: int = 1800) -> Optional[Dict[str, Any]]:
    """Get cached session data"""
    key = f"session:{session_token}"
    return await cache_manager.get(key)

async def cache_session(session_token: str, session_data: Dict[str, Any], expire: int = 1800):
    """Cache session data"""
    key = f"session:{session_token}"
    await cache_manager.set(key, session_data, expire)

async def invalidate_session_cache(session_token: str):
    """Invalidate session cache"""
    key = f"session:{session_token}"
    await cache_manager.delete(key)

async def invalidate_user_sessions_cache(user_id: str):
    """Invalidate all session caches for a user"""
    pattern = f"session:*:user:{user_id}"
    await cache_manager.clear_pattern(pattern)

# Rate limiting cache functions
async def get_rate_limit(key: str) -> int:
    """Get current rate limit count"""
    rate_key = f"rate_limit:{key}"
    count = await cache_manager.get(rate_key)
    return int(count) if count is not None else 0

async def increment_rate_limit(key: str, window_seconds: int = 900) -> int:
    """Increment rate limit counter"""
    rate_key = f"rate_limit:{key}"
    count = await cache_manager.increment(rate_key)
    
    if count == 1:
        # Set expiration on first increment
        await cache_manager.expire(rate_key, window_seconds)
    
    return count

async def reset_rate_limit(key: str):
    """Reset rate limit counter"""
    rate_key = f"rate_limit:{key}"
    await cache_manager.delete(rate_key)

# Session management cache functions
async def cache_user_session(
    session_token: str,
    user_id: str,
    tenant_id: Optional[str],
    expires_at: datetime
) -> bool:
    """Cache user session data"""
    session_data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Cache session data
    await cache_session(session_token, session_data)
    
    # Cache user sessions list
    user_sessions_key = f"user_sessions:{user_id}"
    sessions = await cache_manager.get(user_sessions_key) or []
    sessions.append(session_token)
    await cache_manager.set(user_sessions_key, sessions, expire=86400)  # 24 hours
    
    return True

async def get_cached_user_session(session_token: str) -> Optional[Dict[str, Any]]:
    """Get cached user session data"""
    session_data = await cached_session(session_token)
    
    if not session_data:
        return None
    
    # Check if session is expired
    expires_at = datetime.fromisoformat(session_data["expires_at"])
    if datetime.utcnow() > expires_at:
        await invalidate_session_cache(session_token)
        return None
    
    return session_data

async def invalidate_cached_user_session(session_token: str, user_id: str):
    """Invalidate cached user session"""
    # Remove from session cache
    await invalidate_session_cache(session_token)
    
    # Remove from user sessions list
    user_sessions_key = f"user_sessions:{user_id}"
    sessions = await cache_manager.get(user_sessions_key) or []
    if session_token in sessions:
        sessions.remove(session_token)
        await cache_manager.set(user_sessions_key, sessions, expire=86400)

async def invalidate_all_cached_user_sessions(user_id: str):
    """Invalidate all cached sessions for a user"""
    user_sessions_key = f"user_sessions:{user_id}"
    sessions = await cache_manager.get(user_sessions_key) or []
    
    # Invalidate all session caches
    for session_token in sessions:
        await invalidate_session_cache(session_token)
    
    # Clear user sessions list
    await cache_manager.delete(user_sessions_key)

# Cache warming functions
async def warm_user_cache(user_id: str):
    """Warm user cache with fresh data"""
    from .database import get_user_by_id
    
    user_data = await get_user_by_id(user_id)
    if user_data:
        await cache_user(user_id, user_data)

async def warm_tenant_cache(tenant_id: str):
    """Warm tenant cache with fresh data"""
    from .database import get_tenant_by_id
    
    tenant_data = await get_tenant_by_id(tenant_id)
    if tenant_data:
        await cache_tenant(tenant_id, tenant_data)

# Cache statistics
async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    try:
        if not cache_manager.redis:
            return {"status": "disconnected"}
        
        info = await cache_manager.redis.info()
        
        return {
            "status": "connected",
            "used_memory": info.get("used_memory_human", "0B"),
            "connected_clients": info.get("connected_clients", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"status": "error", "error": str(e)}