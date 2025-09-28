"""
API routes for the memory system service
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from .models import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    MessageCreate, MessageResponse,
    KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse,
    ContextRequest, ContextResponse,
    MemoryConsolidationRequest, MemoryConsolidationResponse,
    KnowledgeSearchRequest, KnowledgeSearchResponse,
    MemoryStats, HealthResponse
)
from .memory_manager import MemoryManager
from .conversation import ConversationManager
from .knowledge_base import KnowledgeManager
from .database import DatabaseManager
from .cache import CacheManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get managers from app state
async def get_memory_manager(request) -> MemoryManager:
    """Get memory manager from FastAPI app state"""
    return request.app.state.memory_manager

async def get_conversation_manager(request) -> ConversationManager:
    """Get conversation manager from FastAPI app state"""
    return request.app.state.conversation_manager

async def get_knowledge_manager(request) -> KnowledgeManager:
    """Get knowledge manager from FastAPI app state"""
    return request.app.state.knowledge_manager

async def get_db_manager(request) -> DatabaseManager:
    """Get database manager from FastAPI app state"""
    return request.app.state.db_manager

async def get_cache_manager(request) -> CacheManager:
    """Get cache manager from FastAPI app state"""
    return request.app.state.cache_manager

# Conversation endpoints
@router.post("/api/v1/memory/conversation", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """Create a new conversation"""
    try:
        conversation = await conversation_manager.create_conversation(conversation_data)
        return conversation
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/memory/conversation/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """Get conversation by ID"""
    try:
        conversation = await conversation_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/v1/memory/conversation/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    update_data: ConversationUpdate,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """Update conversation"""
    try:
        success = await conversation_manager.update_conversation(conversation_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/v1/memory/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """Delete conversation"""
    try:
        success = await conversation_manager.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/memory/conversations/{agent_id}", response_model=List[ConversationResponse])
async def list_conversations(
    agent_id: str,
    limit: int = 50,
    offset: int = 0,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """List conversations for an agent"""
    try:
        conversations = await conversation_manager.list_conversations(agent_id, limit, offset)
        return conversations
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/memory/conversation/{conversation_id}/message", response_model=MessageResponse)
async def add_message(
    conversation_id: str,
    message_data: MessageCreate,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """Add a message to a conversation"""
    try:
        # Ensure conversation_id matches
        message_data.conversation_id = conversation_id
        message = await conversation_manager.add_message(message_data)
        return message
    except Exception as e:
        logger.error(f"Failed to add message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/memory/conversation/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = 100,
    offset: int = 0,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """Get messages for a conversation"""
    try:
        messages = await conversation_manager.get_messages(conversation_id, limit, offset)
        return messages
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Knowledge base endpoints
@router.post("/api/v1/memory/knowledge", response_model=KnowledgeResponse)
async def create_knowledge(
    knowledge_data: KnowledgeCreate,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """Create a new knowledge base entry"""
    try:
        knowledge = await knowledge_manager.create_knowledge(knowledge_data)
        return knowledge
    except Exception as e:
        logger.error(f"Failed to create knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/memory/knowledge/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge(
    knowledge_id: str,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """Get knowledge base entry by ID"""
    try:
        knowledge = await knowledge_manager.get_knowledge(knowledge_id)
        if not knowledge:
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        return knowledge
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/v1/memory/knowledge/{knowledge_id}")
async def update_knowledge(
    knowledge_id: str,
    update_data: KnowledgeUpdate,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """Update knowledge base entry"""
    try:
        success = await knowledge_manager.update_knowledge(knowledge_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        return {"message": "Knowledge entry updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/v1/memory/knowledge/{knowledge_id}")
async def delete_knowledge(
    knowledge_id: str,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """Delete knowledge base entry"""
    try:
        success = await knowledge_manager.delete_knowledge(knowledge_id)
        if not success:
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        return {"message": "Knowledge entry deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/memory/knowledge", response_model=List[KnowledgeResponse])
async def list_knowledge(
    agent_id: str,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """List knowledge base entries for an agent"""
    try:
        from .models import KnowledgeCategory
        category_enum = KnowledgeCategory(category) if category else None
        knowledge_items = await knowledge_manager.list_knowledge(agent_id, category_enum, limit, offset)
        return knowledge_items
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid category")
    except Exception as e:
        logger.error(f"Failed to list knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/memory/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    search_request: KnowledgeSearchRequest,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """Search knowledge base entries"""
    try:
        results = await knowledge_manager.search_knowledge(search_request)
        return results
    except Exception as e:
        logger.error(f"Failed to search knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Context management endpoints
@router.post("/api/v1/memory/context/{agent_id}", response_model=ContextResponse)
async def get_context(
    agent_id: str,
    context_request: ContextRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Get agent context"""
    try:
        context_request.agent_id = agent_id  # Ensure agent_id matches
        context = await memory_manager.get_agent_context(context_request)
        return context
    except Exception as e:
        logger.error(f"Failed to get context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Memory consolidation endpoints
@router.post("/api/v1/memory/summarize", response_model=MemoryConsolidationResponse)
async def consolidate_memory(
    consolidation_request: MemoryConsolidationRequest,
    background_tasks: BackgroundTasks,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Consolidate memory by creating summaries and extracting knowledge"""
    try:
        # Run consolidation in background for large operations
        if consolidation_request.force_consolidation:
            background_tasks.add_task(
                memory_manager.consolidate_memory, consolidation_request
            )
            return MemoryConsolidationResponse(
                success=True,
                conversations_processed=0,
                summaries_created=0,
                messages_archived=0,
                knowledge_extracted=0
            )
        else:
            result = await memory_manager.consolidate_memory(consolidation_request)
            return result
    except Exception as e:
        logger.error(f"Failed to consolidate memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Statistics and management endpoints
@router.get("/api/v1/memory/stats", response_model=Dict[str, Any])
async def get_memory_stats(
    agent_id: Optional[str] = None,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Get memory system statistics"""
    try:
        stats = await memory_manager.get_memory_stats(agent_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/memory/cleanup")
async def cleanup_memories(
    agent_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Clean up old memories"""
    try:
        if background_tasks:
            background_tasks.add_task(memory_manager.cleanup_old_memories, agent_id)
            return {"message": "Memory cleanup started in background"}
        else:
            result = await memory_manager.cleanup_old_memories(agent_id)
            return result
    except Exception as e:
        logger.error(f"Failed to cleanup memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/memory/cache/stats")
async def get_cache_stats(
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """Get cache statistics"""
    try:
        stats = await cache_manager.get_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/v1/memory/cache/clear")
async def clear_cache(
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """Clear all cache entries"""
    try:
        success = await cache_manager.invalidate_all_cache()
        if success:
            return {"message": "Cache cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health", response_model=HealthResponse)
async def health_check(
    db_manager: DatabaseManager = Depends(get_db_manager),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """Health check endpoint with comprehensive system status"""
    try:
        # Check database connection using dedicated health check method
        db_health = await db_manager.health_check()
        db_status = db_health["status"]
        
        # Check Redis connection using dedicated health check method
        redis_health = await cache_manager.health_check()
        redis_status = redis_health["status"]
        
        # Get memory stats with comprehensive error handling
        stats_model = None
        try:
            if db_status == "healthy":
                memory_stats = await db_manager.get_memory_stats()
                if memory_stats:
                    # Ensure all required fields are present with defaults
                    stats_data = {
                        "total_conversations": memory_stats.get("total_conversations", 0),
                        "total_messages": memory_stats.get("total_messages", 0),
                        "total_knowledge_items": memory_stats.get("total_knowledge_items", 0),
                        "total_summaries": memory_stats.get("total_summaries", 0),
                        "active_conversations": memory_stats.get("active_conversations", 0),
                        "cache_hit_rate": 0.0,  # Will be calculated from Redis stats
                        "memory_usage_mb": 0.0   # Will be calculated from Redis stats
                    }
                    
                    # Get cache hit rate from Redis if available
                    if redis_status == "healthy":
                        try:
                            cache_stats = await cache_manager.get_cache_stats()
                            if cache_stats.get("status") == "connected":
                                stats_data["cache_hit_rate"] = cache_stats.get("hit_rate", 0.0)
                                # Convert Redis memory usage to MB
                                used_memory = cache_stats.get("used_memory", 0)
                                stats_data["memory_usage_mb"] = used_memory / (1024 * 1024)
                        except Exception as e:
                            logger.warning(f"Failed to get cache stats for health check: {e}")
                    
                    stats_model = MemoryStats(**stats_data)
        except Exception as e:
            logger.warning(f"Failed to get memory stats for health check: {e}")
        
        # Determine overall status
        if db_status == "healthy" and redis_status == "healthy":
            overall_status = "healthy"
        elif db_status == "healthy" or redis_status == "healthy":
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        # Create health response
        health_response = HealthResponse(
            status=overall_status,
            service="memory-system",
            version="1.0.0",
            timestamp=datetime.utcnow(),
            database_status=db_status,
            redis_status=redis_status,
            memory_stats=stats_model
        )
        
        # Log health check results
        if overall_status == "healthy":
            logger.info("Health check passed - all systems healthy")
        elif overall_status == "degraded":
            logger.warning(f"Health check degraded - DB: {db_status}, Redis: {redis_status}")
        else:
            logger.error(f"Health check failed - DB: {db_status}, Redis: {redis_status}")
        
        return health_response
        
    except Exception as e:
        logger.error(f"Health check endpoint failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="memory-system",
            version="1.0.0",
            timestamp=datetime.utcnow(),
            database_status="unknown",
            redis_status="unknown"
        )