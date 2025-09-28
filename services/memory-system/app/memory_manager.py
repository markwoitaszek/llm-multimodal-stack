"""
Memory Management Core Logic
"""
import asyncio
import time
import uuid
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from datetime import datetime
import logging

from app.models import (
    MemoryRequest, MemoryResponse, RetrieveRequest, RetrieveResponse,
    ConversationRequest, ConversationResponse, ConsolidateRequest, ConsolidateResponse,
    ContextRequest, ContextResponse, MemoryType, MemoryImportance
)
from app.database import db_manager
from app.embeddings import cached_embedding_service
from app.config import settings

logger = logging.getLogger(__name__)


class MemoryManager:
    """Core memory management implementation"""
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = settings.cache_ttl
        self.max_concurrent_operations = settings.max_concurrent_operations
        self._semaphore = asyncio.Semaphore(self.max_concurrent_operations)
    
    async def store_memory(self, request: MemoryRequest) -> MemoryResponse:
        """Store a new memory"""
        try:
            async with self._semaphore:
                memory_id = str(uuid.uuid4())
                
                # Generate embedding
                embedding = await cached_embedding_service.generate_embedding(
                    request.content, use_cache=True
                )
                
                # Store in database
                success = await db_manager.create_memory(
                    memory_id=memory_id,
                    content=request.content,
                    memory_type=request.memory_type.value,
                    importance=request.importance.value,
                    tags=request.tags,
                    metadata=request.metadata,
                    embedding=embedding,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    related_memory_ids=request.related_memory_ids
                )
                
                if not success:
                    raise Exception("Failed to store memory in database")
                
                # Create response
                response = MemoryResponse(
                    memory_id=memory_id,
                    content=request.content,
                    memory_type=request.memory_type,
                    importance=request.importance,
                    tags=request.tags,
                    metadata=request.metadata,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    embedding=embedding
                )
                
                return response
                
        except Exception as e:
            logger.error(f"Memory storage error: {str(e)}")
            raise Exception(f"Failed to store memory: {str(e)}")
    
    async def retrieve_memories(self, request: RetrieveRequest) -> RetrieveResponse:
        """Retrieve memories based on query"""
        start_time = time.time()
        retrieval_id = str(uuid.uuid4())
        
        try:
            async with self._semaphore:
                # Check cache first
                cache_key = self._generate_cache_key(request)
                if cache_key in self.cache:
                    cached_result = self.cache[cache_key]
                    if time.time() - cached_result["timestamp"] < self.cache_ttl:
                        cached_result.cached = True
                        return cached_result["response"]
                
                # Perform retrieval
                memories = await self._perform_memory_retrieval(request)
                
                # Create response
                execution_time_ms = (time.time() - start_time) * 1000
                response = RetrieveResponse(
                    query=request.query,
                    memories=memories,
                    total_results=len(memories),
                    execution_time_ms=execution_time_ms,
                    retrieval_id=retrieval_id
                )
                
                # Cache result
                self.cache[cache_key] = {
                    "response": response,
                    "timestamp": time.time()
                }
                
                return response
                
        except Exception as e:
            logger.error(f"Memory retrieval error: {str(e)}")
            raise Exception(f"Failed to retrieve memories: {str(e)}")
    
    async def _perform_memory_retrieval(self, request: RetrieveRequest) -> List[MemoryResponse]:
        """Perform the actual memory retrieval"""
        # Search database for relevant memories
        db_results = await db_manager.search_memories(
            query=request.query,
            memory_types=[mt.value for mt in request.memory_types] if request.memory_types else None,
            importance_levels=[imp.value for imp in request.importance_levels] if request.importance_levels else None,
            tags=request.tags,
            user_id=request.user_id,
            session_id=request.session_id,
            limit=request.limit
        )
        
        # Convert to MemoryResponse objects
        memories = []
        for db_result in db_results:
            # Filter by similarity threshold if needed
            if db_result["score"] < request.similarity_threshold:
                continue
            
            memory = MemoryResponse(
                memory_id=db_result["id"],
                content=db_result["content"],
                memory_type=MemoryType(db_result["memory_type"]),
                importance=MemoryImportance(db_result["importance"]),
                tags=db_result["tags"],
                metadata=db_result["metadata"] if request.include_metadata else None,
                created_at=db_result["created_at"],
                updated_at=db_result["updated_at"],
                embedding=None  # Don't include embedding in response for security
            )
            memories.append(memory)
        
        return memories[:request.limit]
    
    async def store_conversation(self, request: ConversationRequest) -> ConversationResponse:
        """Store a new conversation"""
        try:
            async with self._semaphore:
                conversation_id = str(uuid.uuid4())
                
                # Store in database
                success = await db_manager.create_conversation(
                    conversation_id=conversation_id,
                    messages=request.messages,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    context=request.context,
                    summary=request.summary
                )
                
                if not success:
                    raise Exception("Failed to store conversation in database")
                
                # Create response
                response = ConversationResponse(
                    conversation_id=conversation_id,
                    messages=request.messages,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    context=request.context,
                    summary=request.summary,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                return response
                
        except Exception as e:
            logger.error(f"Conversation storage error: {str(e)}")
            raise Exception(f"Failed to store conversation: {str(e)}")
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationResponse]:
        """Get conversation by ID"""
        try:
            db_result = await db_manager.get_conversation(conversation_id)
            
            if not db_result:
                return None
            
            response = ConversationResponse(
                conversation_id=db_result["id"],
                messages=db_result["messages"],
                user_id=db_result["user_id"],
                session_id=db_result["session_id"],
                context=db_result["context"],
                summary=db_result["summary"],
                created_at=db_result["created_at"],
                updated_at=db_result["updated_at"]
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Get conversation error: {str(e)}")
            return None
    
    async def get_context(self, request: ContextRequest) -> ContextResponse:
        """Get context for a query"""
        start_time = time.time()
        context_id = str(uuid.uuid4())
        
        try:
            async with self._semaphore:
                context_items = []
                
                # Get conversation context if requested
                if request.include_conversations:
                    conversations = await db_manager.get_conversations_by_session(
                        request.session_id, request.context_window // 2
                    )
                    
                    for conv in conversations:
                        context_items.append({
                            "type": "conversation",
                            "id": conv["id"],
                            "content": conv["messages"],
                            "summary": conv["summary"],
                            "created_at": conv["created_at"],
                            "relevance_score": 1.0  # Could be calculated based on similarity
                        })
                
                # Get memory context if requested
                if request.include_memories:
                    memory_request = RetrieveRequest(
                        query=request.query,
                        user_id=request.user_id,
                        session_id=request.session_id,
                        limit=request.context_window // 2,
                        include_metadata=True
                    )
                    
                    memories = await self._perform_memory_retrieval(memory_request)
                    
                    for memory in memories:
                        context_items.append({
                            "type": "memory",
                            "id": memory.memory_id,
                            "content": memory.content,
                            "memory_type": memory.memory_type.value,
                            "importance": memory.importance.value,
                            "tags": memory.tags,
                            "created_at": memory.created_at,
                            "relevance_score": 1.0  # Could be calculated based on similarity
                        })
                
                # Sort by relevance and limit
                context_items.sort(key=lambda x: x["relevance_score"], reverse=True)
                context_items = context_items[:request.context_window]
                
                # Create response
                execution_time_ms = (time.time() - start_time) * 1000
                response = ContextResponse(
                    query=request.query,
                    context=context_items,
                    total_context_items=len(context_items),
                    execution_time_ms=execution_time_ms,
                    context_id=context_id
                )
                
                return response
                
        except Exception as e:
            logger.error(f"Context retrieval error: {str(e)}")
            raise Exception(f"Failed to get context: {str(e)}")
    
    async def consolidate_memories(self, request: ConsolidateRequest) -> ConsolidateResponse:
        """Consolidate memories"""
        start_time = time.time()
        consolidation_id = str(uuid.uuid4())
        
        try:
            async with self._semaphore:
                # Get memories for consolidation
                memories_to_consolidate = await db_manager.get_memories_for_consolidation(
                    user_id=request.user_id,
                    session_id=request.session_id,
                    memory_types=[mt.value for mt in request.memory_types] if request.memory_types else None
                )
                
                if not request.force and len(memories_to_consolidate) < settings.memory_consolidation_threshold:
                    return ConsolidateResponse(
                        consolidated_count=0,
                        new_memories_created=0,
                        consolidation_time_ms=(time.time() - start_time) * 1000,
                        consolidation_id=consolidation_id
                    )
                
                # Perform consolidation
                new_memories_created = await self._perform_consolidation(memories_to_consolidate)
                
                # Mark original memories as consolidated
                memory_ids = [mem["id"] for mem in memories_to_consolidate]
                await db_manager.mark_memories_consolidated(memory_ids)
                
                # Create response
                execution_time_ms = (time.time() - start_time) * 1000
                response = ConsolidateResponse(
                    consolidated_count=len(memories_to_consolidate),
                    new_memories_created=new_memories_created,
                    consolidation_time_ms=execution_time_ms,
                    consolidation_id=consolidation_id
                )
                
                return response
                
        except Exception as e:
            logger.error(f"Memory consolidation error: {str(e)}")
            raise Exception(f"Failed to consolidate memories: {str(e)}")
    
    async def _perform_consolidation(self, memories: List[Dict[str, Any]]) -> int:
        """Perform actual memory consolidation"""
        # Group memories by type and importance
        grouped_memories = {}
        for memory in memories:
            key = (memory["memory_type"], memory["importance"])
            if key not in grouped_memories:
                grouped_memories[key] = []
            grouped_memories[key].append(memory)
        
        new_memories_created = 0
        
        # Consolidate each group
        for (memory_type, importance), group_memories in grouped_memories.items():
            if len(group_memories) < 3:  # Need at least 3 memories to consolidate
                continue
            
            # Create consolidated content
            consolidated_content = await self._create_consolidated_content(group_memories)
            
            # Create new consolidated memory
            consolidated_memory_id = str(uuid.uuid4())
            
            # Get tags from original memories
            all_tags = []
            for mem in group_memories:
                if mem["tags"]:
                    all_tags.extend(mem["tags"])
            unique_tags = list(set(all_tags))
            
            # Get metadata
            consolidated_metadata = {
                "consolidated_from": [mem["id"] for mem in group_memories],
                "consolidation_date": datetime.utcnow().isoformat(),
                "original_count": len(group_memories)
            }
            
            # Store consolidated memory
            success = await db_manager.create_memory(
                memory_id=consolidated_memory_id,
                content=consolidated_content,
                memory_type=memory_type,
                importance=importance,
                tags=unique_tags,
                metadata=consolidated_metadata,
                user_id=group_memories[0]["user_id"],
                session_id=group_memories[0]["session_id"]
            )
            
            if success:
                new_memories_created += 1
        
        return new_memories_created
    
    async def _create_consolidated_content(self, memories: List[Dict[str, Any]]) -> str:
        """Create consolidated content from multiple memories"""
        # Simple consolidation: combine content with separators
        # In a real implementation, this could use LLM summarization
        
        content_parts = []
        for memory in memories:
            content_parts.append(f"- {memory['content']}")
        
        consolidated = "Consolidated memories:\n" + "\n".join(content_parts)
        
        # Truncate if too long
        if len(consolidated) > settings.max_text_length:
            consolidated = consolidated[:settings.max_text_length] + "..."
        
        return consolidated
    
    async def update_memory(self, memory_id: str, update_request) -> Optional[MemoryResponse]:
        """Update existing memory"""
        try:
            async with self._semaphore:
                # Update in database
                success = await db_manager.update_memory(
                    memory_id=memory_id,
                    content=update_request.content,
                    memory_type=update_request.memory_type.value if update_request.memory_type else None,
                    importance=update_request.importance.value if update_request.importance else None,
                    tags=update_request.tags,
                    metadata=update_request.metadata
                )
                
                if not success:
                    return None
                
                # Get updated memory
                db_result = await db_manager.get_memory(memory_id)
                
                if not db_result:
                    return None
                
                response = MemoryResponse(
                    memory_id=db_result["id"],
                    content=db_result["content"],
                    memory_type=MemoryType(db_result["memory_type"]),
                    importance=MemoryImportance(db_result["importance"]),
                    tags=db_result["tags"],
                    metadata=db_result["metadata"],
                    created_at=db_result["created_at"],
                    updated_at=db_result["updated_at"]
                )
                
                return response
                
        except Exception as e:
            logger.error(f"Memory update error: {str(e)}")
            return None
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory"""
        try:
            async with self._semaphore:
                return await db_manager.delete_memory(memory_id)
                
        except Exception as e:
            logger.error(f"Memory deletion error: {str(e)}")
            return False
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        try:
            # Get database stats
            db_stats = await db_manager.get_memory_stats()
            
            # Get cache info
            cache_info = {
                "cache_size": len(self.cache),
                "cache_ttl": self.cache_ttl
            }
            
            return {
                **db_stats,
                **cache_info,
                "active_sessions": 0,  # Could be calculated from active sessions
                "cache_hit_rate": 0.0  # Could be calculated with hit/miss counters
            }
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            return {}
    
    def _generate_cache_key(self, request: RetrieveRequest) -> str:
        """Generate cache key for request"""
        key_parts = [
            request.query,
            str(sorted(request.memory_types)) if request.memory_types else None,
            str(sorted(request.importance_levels)) if request.importance_levels else None,
            str(sorted(request.tags)) if request.tags else None,
            request.user_id,
            request.session_id,
            request.limit,
            request.similarity_threshold,
            request.include_metadata
        ]
        
        return str(hash(tuple(key_parts)))
    
    def clear_cache(self):
        """Clear memory cache"""
        self.cache.clear()


# Global memory manager instance
memory_manager = MemoryManager()