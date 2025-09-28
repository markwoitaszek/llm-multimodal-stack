"""
Pydantic models for the memory system service
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class MemoryType(str, Enum):
    """Types of memory storage"""
    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    CONTEXT = "context"
    SUMMARY = "summary"

class MessageRole(str, Enum):
    """Roles in conversation messages"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class KnowledgeCategory(str, Enum):
    """Categories for knowledge base items"""
    FACT = "fact"
    PROCEDURE = "procedure"
    PREFERENCE = "preference"
    CONTEXT = "context"
    REFERENCE = "reference"

class ConversationCreate(BaseModel):
    """Model for creating a new conversation"""
    agent_id: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversationUpdate(BaseModel):
    """Model for updating a conversation"""
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ConversationResponse(BaseModel):
    """Model for conversation response"""
    id: str
    agent_id: str
    title: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    message_count: int
    metadata: Optional[Dict[str, Any]]

class MessageCreate(BaseModel):
    """Model for creating a new message"""
    conversation_id: str
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    """Model for message response"""
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]]

class KnowledgeCreate(BaseModel):
    """Model for creating knowledge base entry"""
    agent_id: str
    category: KnowledgeCategory
    title: str
    content: str
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    source: Optional[str] = None

class KnowledgeUpdate(BaseModel):
    """Model for updating knowledge base entry"""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[KnowledgeCategory] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class KnowledgeResponse(BaseModel):
    """Model for knowledge base response"""
    id: str
    agent_id: str
    category: KnowledgeCategory
    title: str
    content: str
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]]
    source: Optional[str]

class ContextRequest(BaseModel):
    """Model for context retrieval request"""
    agent_id: str
    conversation_id: Optional[str] = None
    max_messages: Optional[int] = None
    include_knowledge: bool = True
    include_summaries: bool = True

class ContextResponse(BaseModel):
    """Model for context response"""
    agent_id: str
    conversation_id: Optional[str]
    messages: List[MessageResponse]
    knowledge: List[KnowledgeResponse]
    summaries: List[Dict[str, Any]]
    total_tokens: int
    context_window_used: float

class MemorySummary(BaseModel):
    """Model for memory summary"""
    id: str
    agent_id: str
    conversation_id: str
    summary_type: str
    content: str
    message_range_start: int
    message_range_end: int
    created_at: datetime
    relevance_score: float

class MemoryConsolidationRequest(BaseModel):
    """Model for memory consolidation request"""
    agent_id: str
    conversation_id: Optional[str] = None
    force_consolidation: bool = False

class MemoryConsolidationResponse(BaseModel):
    """Model for memory consolidation response"""
    success: bool
    conversations_processed: int
    summaries_created: int
    messages_archived: int
    knowledge_extracted: int

class KnowledgeSearchRequest(BaseModel):
    """Model for knowledge base search request"""
    agent_id: str
    query: str
    category: Optional[KnowledgeCategory] = None
    tags: Optional[List[str]] = None
    limit: int = 10
    threshold: float = 0.7

class KnowledgeSearchResponse(BaseModel):
    """Model for knowledge base search response"""
    results: List[KnowledgeResponse]
    total_found: int
    query: str
    search_time_ms: int

class MemoryStats(BaseModel):
    """Model for memory system statistics"""
    total_conversations: int
    total_messages: int
    total_knowledge_items: int
    total_summaries: int
    active_conversations: int
    cache_hit_rate: float
    memory_usage_mb: float

class HealthResponse(BaseModel):
    """Model for health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime
    database_status: str
    redis_status: str
    memory_stats: Optional[MemoryStats] = None