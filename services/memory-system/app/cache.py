"""
Redis caching layer for the memory system service
"""
import logging
import json
from datetime import timedelta
from typing import Dict, List, Optional, Any, Union
import redis.asyncio as redis
from redis.asyncio import Redis

from .config import settings
from .models import MessageResponse, KnowledgeResponse, ConversationResponse

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages Redis caching for memory system"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize Redis connection with enhanced error handling"""
        try:
            self.redis = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=20
            )
            
            # Test connection with timeout
            await self.redis.ping()
            self.is_initialized = True
            logger.info("Redis cache connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            self.is_initialized = False
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis cache connection closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive Redis health check"""
        health_info = {
            "status": "unhealthy",
            "connected_clients": 0,
            "used_memory": 0,
            "error": None
        }
        
        try:
            if not self.redis or not self.is_initialized:
                health_info["error"] = "Redis not initialized"
                return health_info
            
            # Test basic connectivity
            pong = await self.redis.ping()
            if not pong:
                health_info["error"] = "Redis ping failed"
                return health_info
            
            # Get Redis info
            info = await self.redis.info()
            health_info.update({
                "status": "healthy",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0)
            })
            
        except Exception as e:
            health_info["error"] = str(e)
            logger.warning(f"Redis health check failed: {e}")
        
        return health_info
    
    def _get_conversation_key(self, conv_id: str) -> str:
        """Get cache key for conversation"""
        return f"conv:{conv_id}"
    
    def _get_messages_key(self, conv_id: str, limit: int = 100) -> str:
        """Get cache key for conversation messages"""
        return f"msgs:{conv_id}:{limit}"
    
    def _get_knowledge_key(self, agent_id: str, query: str = None) -> str:
        """Get cache key for knowledge base"""
        if query:
            return f"knowledge:{agent_id}:search:{hash(query)}"
        return f"knowledge:{agent_id}:list"
    
    def _get_context_key(self, agent_id: str, conv_id: str = None) -> str:
        """Get cache key for agent context"""
        if conv_id:
            return f"context:{agent_id}:conv:{conv_id}"
        return f"context:{agent_id}"
    
    def _get_summary_key(self, agent_id: str, conv_id: str) -> str:
        """Get cache key for conversation summary"""
        return f"summary:{agent_id}:conv:{conv_id}"
    
    # Conversation caching
    async def cache_conversation(self, conversation: ConversationResponse, ttl: int = None) -> bool:
        """Cache conversation data"""
        if not self.redis:
            return False
        
        try:
            key = self._get_conversation_key(conversation.id)
            data = conversation.model_dump_json()
            ttl = ttl or settings.conversation_cache_ttl
            await self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Failed to cache conversation: {e}")
            return False
    
    async def get_cached_conversation(self, conv_id: str) -> Optional[ConversationResponse]:
        """Get cached conversation"""
        if not self.redis:
            return None
        
        try:
            key = self._get_conversation_key(conv_id)
            data = await self.redis.get(key)
            if data:
                return ConversationResponse.model_validate_json(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached conversation: {e}")
            return None
    
    # Message caching
    async def cache_messages(self, conv_id: str, messages: List[MessageResponse], 
                           limit: int = 100, ttl: int = None) -> bool:
        """Cache conversation messages"""
        if not self.redis:
            return False
        
        try:
            key = self._get_messages_key(conv_id, limit)
            data = json.dumps([msg.model_dump() for msg in messages])
            ttl = ttl or settings.conversation_cache_ttl
            await self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Failed to cache messages: {e}")
            return False
    
    async def get_cached_messages(self, conv_id: str, limit: int = 100) -> Optional[List[MessageResponse]]:
        """Get cached messages"""
        if not self.redis:
            return None
        
        try:
            key = self._get_messages_key(conv_id, limit)
            data = await self.redis.get(key)
            if data:
                messages_data = json.loads(data)
                return [MessageResponse.model_validate(msg) for msg in messages_data]
            return None
        except Exception as e:
            logger.error(f"Failed to get cached messages: {e}")
            return None
    
    # Knowledge base caching
    async def cache_knowledge_search(self, agent_id: str, query: str, 
                                   results: List[KnowledgeResponse], ttl: int = None) -> bool:
        """Cache knowledge base search results"""
        if not self.redis:
            return False
        
        try:
            key = self._get_knowledge_key(agent_id, query)
            data = json.dumps([kb.model_dump() for kb in results])
            ttl = ttl or settings.knowledge_cache_ttl
            await self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Failed to cache knowledge search: {e}")
            return False
    
    async def get_cached_knowledge_search(self, agent_id: str, query: str) -> Optional[List[KnowledgeResponse]]:
        """Get cached knowledge search results"""
        if not self.redis:
            return None
        
        try:
            key = self._get_knowledge_key(agent_id, query)
            data = await self.redis.get(key)
            if data:
                knowledge_data = json.loads(data)
                return [KnowledgeResponse.model_validate(kb) for kb in knowledge_data]
            return None
        except Exception as e:
            logger.error(f"Failed to get cached knowledge search: {e}")
            return None
    
    async def cache_knowledge_list(self, agent_id: str, knowledge_items: List[KnowledgeResponse], 
                                 ttl: int = None) -> bool:
        """Cache knowledge base list"""
        if not self.redis:
            return False
        
        try:
            key = self._get_knowledge_key(agent_id)
            data = json.dumps([kb.model_dump() for kb in knowledge_items])
            ttl = ttl or settings.knowledge_cache_ttl
            await self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Failed to cache knowledge list: {e}")
            return False
    
    async def get_cached_knowledge_list(self, agent_id: str) -> Optional[List[KnowledgeResponse]]:
        """Get cached knowledge list"""
        if not self.redis:
            return None
        
        try:
            key = self._get_knowledge_key(agent_id)
            data = await self.redis.get(key)
            if data:
                knowledge_data = json.loads(data)
                return [KnowledgeResponse.model_validate(kb) for kb in knowledge_data]
            return None
        except Exception as e:
            logger.error(f"Failed to get cached knowledge list: {e}")
            return None
    
    # Context caching
    async def cache_context(self, agent_id: str, context_data: Dict[str, Any], 
                          conv_id: str = None, ttl: int = None) -> bool:
        """Cache agent context"""
        if not self.redis:
            return False
        
        try:
            key = self._get_context_key(agent_id, conv_id)
            data = json.dumps(context_data)
            ttl = ttl or settings.cache_ttl_seconds
            await self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Failed to cache context: {e}")
            return False
    
    async def get_cached_context(self, agent_id: str, conv_id: str = None) -> Optional[Dict[str, Any]]:
        """Get cached agent context"""
        if not self.redis:
            return None
        
        try:
            key = self._get_context_key(agent_id, conv_id)
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached context: {e}")
            return None
    
    # Summary caching
    async def cache_summary(self, agent_id: str, conv_id: str, summary_data: Dict[str, Any], 
                          ttl: int = None) -> bool:
        """Cache conversation summary"""
        if not self.redis:
            return False
        
        try:
            key = self._get_summary_key(agent_id, conv_id)
            data = json.dumps(summary_data)
            ttl = ttl or settings.knowledge_cache_ttl
            await self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Failed to cache summary: {e}")
            return False
    
    async def get_cached_summary(self, agent_id: str, conv_id: str) -> Optional[Dict[str, Any]]:
        """Get cached conversation summary"""
        if not self.redis:
            return None
        
        try:
            key = self._get_summary_key(agent_id, conv_id)
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached summary: {e}")
            return None
    
    # Cache invalidation
    async def invalidate_conversation(self, conv_id: str) -> bool:
        """Invalidate conversation cache"""
        if not self.redis:
            return False
        
        try:
            # Remove conversation and related caches
            keys_to_delete = [
                self._get_conversation_key(conv_id),
                self._get_messages_key(conv_id, 100),
                self._get_messages_key(conv_id, 50),
                self._get_messages_key(conv_id, 10)
            ]
            
            # Get all context and summary keys for this conversation
            pattern = f"context:*:conv:{conv_id}"
            context_keys = await self.redis.keys(pattern)
            keys_to_delete.extend(context_keys)
            
            pattern = f"summary:*:conv:{conv_id}"
            summary_keys = await self.redis.keys(pattern)
            keys_to_delete.extend(summary_keys)
            
            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate conversation cache: {e}")
            return False
    
    async def invalidate_agent_knowledge(self, agent_id: str) -> bool:
        """Invalidate agent knowledge cache"""
        if not self.redis:
            return False
        
        try:
            # Remove all knowledge-related keys for agent
            patterns = [
                f"knowledge:{agent_id}:*",
                f"context:{agent_id}*"
            ]
            
            keys_to_delete = []
            for pattern in patterns:
                keys = await self.redis.keys(pattern)
                keys_to_delete.extend(keys)
            
            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate agent knowledge cache: {e}")
            return False
    
    async def invalidate_all_cache(self) -> bool:
        """Invalidate all cache entries"""
        if not self.redis:
            return False
        
        try:
            await self.redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate all cache: {e}")
            return False
    
    # Cache statistics
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis:
            return {"status": "not_connected"}
        
        try:
            info = await self.redis.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0))
                ) * 100
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}

# Global cache manager instance
cache_manager = CacheManager()