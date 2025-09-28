"""
Core memory management logic for the memory system service
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
import hashlib
import json

from .database import DatabaseManager
from .cache import CacheManager
from .conversation import ConversationManager
from .knowledge_base import KnowledgeManager
from .models import (
    ContextRequest, ContextResponse, MemorySummary,
    MemoryConsolidationRequest, MemoryConsolidationResponse,
    MessageResponse, KnowledgeResponse, ConversationResponse
)

logger = logging.getLogger(__name__)

class MemoryManager:
    """Core memory management orchestrator"""
    
    def __init__(self, db_manager: DatabaseManager, cache_manager: CacheManager):
        self.db = db_manager
        self.cache = cache_manager
        self.conversation_manager = ConversationManager(db_manager, cache_manager)
        self.knowledge_manager = KnowledgeManager(db_manager, cache_manager)
    
    async def get_agent_context(self, request: ContextRequest) -> ContextResponse:
        """Get comprehensive context for an agent"""
        try:
            # Try cache first
            cached_context = await self.cache.get_cached_context(
                request.agent_id, request.conversation_id
            )
            if cached_context:
                return ContextResponse(**cached_context)
            
            # Get conversation messages
            messages = []
            if request.conversation_id:
                messages = await self.conversation_manager.get_conversation_context(
                    request.conversation_id, request.max_messages or 10
                )
            
            # Get relevant knowledge
            knowledge = []
            if request.include_knowledge:
                knowledge_items = await self.knowledge_manager.list_knowledge(
                    request.agent_id, limit=50
                )
                knowledge = knowledge_items[:20]  # Limit for context window
            
            # Get summaries
            summaries = []
            if request.include_summaries:
                summary_dicts = await self.db.get_summaries(
                    request.agent_id, request.conversation_id
                )
                summaries = [dict(summary) for summary in summary_dicts[:5]]  # Limit summaries
            
            # Calculate token usage
            total_tokens = self._calculate_tokens(messages, knowledge, summaries)
            context_window_used = total_tokens / 4000  # Assuming 4K context window
            
            context_response = ContextResponse(
                agent_id=request.agent_id,
                conversation_id=request.conversation_id,
                messages=messages,
                knowledge=knowledge,
                summaries=summaries,
                total_tokens=total_tokens,
                context_window_used=context_window_used
            )
            
            # Cache the context
            await self.cache.cache_context(
                request.agent_id, context_response.model_dump(), request.conversation_id
            )
            
            return context_response
            
        except Exception as e:
            logger.error(f"Failed to get agent context: {e}")
            return ContextResponse(
                agent_id=request.agent_id,
                conversation_id=request.conversation_id,
                messages=[],
                knowledge=[],
                summaries=[],
                total_tokens=0,
                context_window_used=0.0
            )
    
    def _calculate_tokens(self, messages: List[MessageResponse], 
                         knowledge: List[KnowledgeResponse], 
                         summaries: List[Dict[str, Any]]) -> int:
        """Calculate approximate token count"""
        total_tokens = 0
        
        # Messages tokens (rough estimate: 1 token ≈ 4 characters)
        for message in messages:
            total_tokens += len(message.content) // 4
        
        # Knowledge tokens
        for kb in knowledge:
            total_tokens += len(kb.content) // 4
        
        # Summary tokens
        for summary in summaries:
            total_tokens += len(summary.get('content', '')) // 4
        
        return total_tokens
    
    async def consolidate_memory(self, request: MemoryConsolidationRequest) -> MemoryConsolidationResponse:
        """Consolidate memory by creating summaries and extracting knowledge"""
        try:
            conversations_processed = 0
            summaries_created = 0
            messages_archived = 0
            knowledge_extracted = 0
            
            # Get conversations to consolidate
            if request.conversation_id:
                conversations = [await self.conversation_manager.get_conversation(request.conversation_id)]
                conversations = [conv for conv in conversations if conv]
            else:
                conversations = await self.conversation_manager.list_conversations(
                    request.agent_id, limit=100
                )
            
            for conversation in conversations:
                if not conversation:
                    continue
                
                # Check if consolidation is needed
                should_consolidate = (
                    request.force_consolidation or 
                    await self.conversation_manager.should_consolidate(conversation.id)
                )
                
                if not should_consolidate:
                    continue
                
                try:
                    # Consolidate conversation
                    summary = await self.conversation_manager.consolidate_conversation(
                        conversation.id, request.agent_id
                    )
                    
                    if summary:
                        summaries_created += 1
                    
                    # Extract knowledge from conversation
                    messages = await self.conversation_manager.get_messages(conversation.id)
                    message_dicts = [msg.model_dump() for msg in messages]
                    
                    extracted_knowledge = await self.knowledge_manager.extract_knowledge_from_conversation(
                        request.agent_id, conversation.id, message_dicts
                    )
                    
                    # Create knowledge entries
                    for knowledge_data in extracted_knowledge:
                        try:
                            await self.knowledge_manager.create_knowledge(knowledge_data)
                            knowledge_extracted += 1
                        except Exception as e:
                            logger.warning(f"Failed to create knowledge entry: {e}")
                    
                    # Archive old messages (keep recent ones)
                    if len(messages) > 50:  # Keep last 50 messages
                        messages_to_archive = messages[:-50]
                        messages_archived += len(messages_to_archive)
                        
                        # In a real implementation, you might move these to an archive table
                        # For now, we'll just mark them as archived in metadata
                    
                    conversations_processed += 1
                    
                except Exception as e:
                    logger.error(f"Failed to consolidate conversation {conversation.id}: {e}")
            
            # Consolidate knowledge base
            try:
                consolidation_stats = await self.knowledge_manager.consolidate_knowledge(request.agent_id)
                logger.info(f"Knowledge consolidation stats: {consolidation_stats}")
            except Exception as e:
                logger.error(f"Failed to consolidate knowledge: {e}")
            
            return MemoryConsolidationResponse(
                success=True,
                conversations_processed=conversations_processed,
                summaries_created=summaries_created,
                messages_archived=messages_archived,
                knowledge_extracted=knowledge_extracted
            )
            
        except Exception as e:
            logger.error(f"Failed to consolidate memory: {e}")
            return MemoryConsolidationResponse(
                success=False,
                conversations_processed=0,
                summaries_created=0,
                messages_archived=0,
                knowledge_extracted=0
            )
    
    async def _generate_summary(self, messages: List[MessageResponse]) -> str:
        """Generate a summary of conversation messages"""
        try:
            # Simple extractive summarization
            # In a real implementation, you would use an LLM or advanced NLP
            
            # Group messages by role
            user_messages = [msg.content for msg in messages if msg.role.value == 'user']
            assistant_messages = [msg.content for msg in messages if msg.role.value == 'assistant']
            
            # Create summary
            summary_parts = []
            
            if user_messages:
                # Extract key topics from user messages
                topics = self._extract_topics(user_messages)
                if topics:
                    summary_parts.append(f"User discussed: {', '.join(topics[:3])}")
            
            if assistant_messages:
                # Extract key responses from assistant
                key_responses = self._extract_key_responses(assistant_messages)
                if key_responses:
                    summary_parts.append(f"Assistant provided: {', '.join(key_responses[:2])}")
            
            # Add conversation stats
            summary_parts.append(f"Total messages: {len(messages)}")
            summary_parts.append(f"Duration: {messages[0].created_at.strftime('%Y-%m-%d')} to {messages[-1].created_at.strftime('%Y-%m-%d')}")
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return f"Conversation with {len(messages)} messages"
    
    def _extract_topics(self, messages: List[str]) -> List[str]:
        """Extract topics from messages (simple implementation)"""
        # Simple keyword extraction
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        word_freq = {}
        for message in messages:
            words = message.lower().split()
            for word in words:
                if len(word) > 3 and word not in common_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top topics
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:5]]
    
    def _extract_key_responses(self, messages: List[str]) -> List[str]:
        """Extract key responses from assistant messages"""
        key_responses = []
        
        for message in messages:
            # Look for sentences that start with action words or provide information
            sentences = message.split('.')
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 20 and any(word in sentence.lower() for word in 
                    ['here', 'you', 'can', 'should', 'need', 'have', 'is', 'are']):
                    key_responses.append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
                    break
        
        return key_responses[:3]
    
    async def cleanup_old_memories(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Clean up old memories based on retention policy"""
        try:
            cleanup_stats = await self.db.cleanup_old_memories()
            
            # Invalidate relevant caches
            if agent_id:
                await self.cache.invalidate_agent_knowledge(agent_id)
            else:
                await self.cache.invalidate_all_cache()
            
            logger.info(f"Memory cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Failed to cleanup old memories: {e}")
            return {"error": str(e)}
    
    async def get_memory_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        try:
            # Get database stats
            db_stats = await self.db.get_memory_stats(agent_id)
            
            # Get cache stats
            cache_stats = await self.cache.get_cache_stats()
            
            # Get knowledge stats if agent_id provided
            knowledge_stats = {}
            if agent_id:
                knowledge_stats = await self.knowledge_manager.get_knowledge_stats(agent_id)
            
            return {
                "database_stats": db_stats,
                "cache_stats": cache_stats,
                "knowledge_stats": knowledge_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}
    
    async def compress_context(self, context: ContextResponse, 
                             target_ratio: float = 0.5) -> ContextResponse:
        """Compress context to fit within token limits"""
        try:
            target_tokens = int(context.total_tokens * target_ratio)
            
            # Sort messages by importance (simple heuristic)
            messages = sorted(
                context.messages, 
                key=lambda msg: len(msg.content), 
                reverse=True
            )
            
            # Keep most important messages
            compressed_messages = []
            current_tokens = 0
            
            for message in messages:
                message_tokens = len(message.content) // 4
                if current_tokens + message_tokens <= target_tokens:
                    compressed_messages.append(message)
                    current_tokens += message_tokens
                else:
                    break
            
            # Sort back to chronological order
            compressed_messages.sort(key=lambda msg: msg.created_at)
            
            # Compress knowledge similarly
            compressed_knowledge = context.knowledge[:len(context.knowledge)//2]
            
            return ContextResponse(
                agent_id=context.agent_id,
                conversation_id=context.conversation_id,
                messages=compressed_messages,
                knowledge=compressed_knowledge,
                summaries=context.summaries,
                total_tokens=current_tokens + sum(len(kb.content) // 4 for kb in compressed_knowledge),
                context_window_used=(current_tokens + sum(len(kb.content) // 4 for kb in compressed_knowledge)) / 4000
            )
            
        except Exception as e:
            logger.error(f"Failed to compress context: {e}")
            return context