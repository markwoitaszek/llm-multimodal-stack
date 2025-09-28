"""
Conversation management for the memory system service
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from .database import DatabaseManager
from .cache import CacheManager
from .models import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    MessageCreate, MessageResponse, MessageRole,
    MemorySummary
)

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages conversation operations and context"""
    
    def __init__(self, db_manager: DatabaseManager, cache_manager: CacheManager):
        self.db = db_manager
        self.cache = cache_manager
    
    async def create_conversation(self, conv_data: ConversationCreate) -> ConversationResponse:
        """Create a new conversation"""
        try:
            conv_id = await self.db.create_conversation(conv_data)
            
            # Get the created conversation
            conv_dict = await self.db.get_conversation(conv_id)
            if not conv_dict:
                raise RuntimeError("Failed to retrieve created conversation")
            
            conversation = ConversationResponse(**conv_dict)
            
            # Cache the conversation
            await self.cache.cache_conversation(conversation)
            
            logger.info(f"Created conversation {conv_id} for agent {conv_data.agent_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    async def get_conversation(self, conv_id: str) -> Optional[ConversationResponse]:
        """Get conversation by ID with caching"""
        try:
            # Try cache first
            conversation = await self.cache.get_cached_conversation(conv_id)
            if conversation:
                return conversation
            
            # Get from database
            conv_dict = await self.db.get_conversation(conv_id)
            if not conv_dict:
                return None
            
            conversation = ConversationResponse(**conv_dict)
            
            # Cache the result
            await self.cache.cache_conversation(conversation)
            
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to get conversation {conv_id}: {e}")
            return None
    
    async def update_conversation(self, conv_id: str, update_data: ConversationUpdate) -> bool:
        """Update conversation"""
        try:
            success = await self.db.update_conversation(conv_id, update_data)
            
            if success:
                # Invalidate cache to force refresh
                await self.cache.invalidate_conversation(conv_id)
                logger.info(f"Updated conversation {conv_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update conversation {conv_id}: {e}")
            return False
    
    async def delete_conversation(self, conv_id: str) -> bool:
        """Delete conversation and all related data"""
        try:
            success = await self.db.delete_conversation(conv_id)
            
            if success:
                # Invalidate all related cache
                await self.cache.invalidate_conversation(conv_id)
                logger.info(f"Deleted conversation {conv_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete conversation {conv_id}: {e}")
            return False
    
    async def list_conversations(self, agent_id: str, limit: int = 50, offset: int = 0) -> List[ConversationResponse]:
        """List conversations for an agent"""
        try:
            conv_dicts = await self.db.list_conversations(agent_id, limit, offset)
            conversations = [ConversationResponse(**conv_dict) for conv_dict in conv_dicts]
            
            # Cache each conversation
            for conversation in conversations:
                await self.cache.cache_conversation(conversation)
            
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to list conversations for agent {agent_id}: {e}")
            return []
    
    async def add_message(self, msg_data: MessageCreate) -> MessageResponse:
        """Add a message to a conversation"""
        try:
            msg_id = await self.db.add_message(msg_data)
            
            # Get the created message
            messages = await self.db.get_recent_messages(msg_data.conversation_id, 1)
            if not messages:
                raise RuntimeError("Failed to retrieve created message")
            
            message = MessageResponse(**messages[0])
            
            # Invalidate conversation cache to force refresh
            await self.cache.invalidate_conversation(msg_data.conversation_id)
            
            logger.info(f"Added message {msg_id} to conversation {msg_data.conversation_id}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise
    
    async def get_messages(self, conv_id: str, limit: int = 100, offset: int = 0) -> List[MessageResponse]:
        """Get messages for a conversation with caching"""
        try:
            # Try cache first for common limits
            if offset == 0 and limit in [10, 50, 100]:
                cached_messages = await self.cache.get_cached_messages(conv_id, limit)
                if cached_messages:
                    return cached_messages
            
            # Get from database
            msg_dicts = await self.db.get_messages(conv_id, limit, offset)
            messages = [MessageResponse(**msg_dict) for msg_dict in msg_dicts]
            
            # Cache common requests
            if offset == 0 and limit in [10, 50, 100]:
                await self.cache.cache_messages(conv_id, messages, limit)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages for conversation {conv_id}: {e}")
            return []
    
    async def get_recent_messages(self, conv_id: str, limit: int = 10) -> List[MessageResponse]:
        """Get recent messages for a conversation"""
        try:
            # Try cache first
            cached_messages = await self.cache.get_cached_messages(conv_id, limit)
            if cached_messages:
                return cached_messages[-limit:]  # Return most recent
            
            # Get from database
            msg_dicts = await self.db.get_recent_messages(conv_id, limit)
            messages = [MessageResponse(**msg_dict) for msg_dict in msg_dicts]
            
            # Cache the result
            await self.cache.cache_messages(conv_id, messages, limit)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get recent messages for conversation {conv_id}: {e}")
            return []
    
    async def get_conversation_context(self, conv_id: str, max_messages: int = 10) -> List[MessageResponse]:
        """Get conversation context for AI processing"""
        try:
            # Get recent messages
            messages = await self.get_recent_messages(conv_id, max_messages)
            
            # Ensure we have a reasonable context window
            if len(messages) > max_messages:
                messages = messages[-max_messages:]
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get conversation context for {conv_id}: {e}")
            return []
    
    async def should_consolidate(self, conv_id: str) -> bool:
        """Check if conversation should be consolidated"""
        try:
            messages = await self.get_messages(conv_id, limit=1000)  # Get all messages
            return len(messages) >= self.cache.cache_ttl_seconds  # Use consolidation threshold from config
            
        except Exception as e:
            logger.error(f"Failed to check consolidation for conversation {conv_id}: {e}")
            return False
    
    async def consolidate_conversation(self, conv_id: str, agent_id: str) -> Optional[MemorySummary]:
        """Consolidate conversation by creating a summary"""
        try:
            from .memory_manager import MemoryManager
            
            # Get all messages
            messages = await self.get_messages(conv_id, limit=1000)
            if len(messages) < 10:  # Don't consolidate short conversations
                return None
            
            # Create memory manager instance
            memory_manager = MemoryManager(self.db, self.cache)
            
            # Generate summary
            summary_content = await memory_manager._generate_summary(messages)
            
            # Create summary record
            summary_data = MemorySummary(
                id=str(uuid4()),
                agent_id=agent_id,
                conversation_id=conv_id,
                summary_type="conversation_consolidation",
                content=summary_content,
                message_range_start=0,
                message_range_end=len(messages) - 1,
                relevance_score=1.0
            )
            
            # Save to database
            summary_id = await self.db.create_summary(summary_data)
            summary_data.id = summary_id
            
            # Cache the summary
            await self.cache.cache_summary(agent_id, conv_id, summary_data.model_dump())
            
            logger.info(f"Consolidated conversation {conv_id} with summary {summary_id}")
            return summary_data
            
        except Exception as e:
            logger.error(f"Failed to consolidate conversation {conv_id}: {e}")
            return None
    
    async def get_conversation_stats(self, conv_id: str) -> Dict[str, Any]:
        """Get conversation statistics"""
        try:
            conversation = await self.get_conversation(conv_id)
            if not conversation:
                return {}
            
            messages = await self.get_messages(conv_id)
            
            # Calculate stats
            stats = {
                "conversation_id": conv_id,
                "message_count": len(messages),
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
                "is_active": conversation.is_active,
                "role_distribution": {},
                "total_characters": 0,
                "average_message_length": 0
            }
            
            # Analyze message roles and content
            for message in messages:
                role = message.role.value
                stats["role_distribution"][role] = stats["role_distribution"].get(role, 0) + 1
                stats["total_characters"] += len(message.content)
            
            if messages:
                stats["average_message_length"] = stats["total_characters"] / len(messages)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get conversation stats for {conv_id}: {e}")
            return {}