"""
Memory System Data Models
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MemoryType(str, Enum):
    """Memory type enumeration"""
    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    CONTEXT = "context"
    FACT = "fact"
    PREFERENCE = "preference"
    GOAL = "goal"


class MemoryImportance(str, Enum):
    """Memory importance enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryRequest(BaseModel):
    """Memory storage request model"""
    content: str = Field(..., min_length=1, max_length=2048, description="Memory content")
    memory_type: MemoryType = Field(..., description="Type of memory")
    importance: MemoryImportance = Field(default=MemoryImportance.MEDIUM, description="Memory importance")
    tags: Optional[List[str]] = Field(default=None, description="Memory tags")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    related_memory_ids: Optional[List[str]] = Field(default=None, description="Related memory IDs")


class MemoryResponse(BaseModel):
    """Memory storage response model"""
    memory_id: str = Field(..., description="Unique memory identifier")
    content: str = Field(..., description="Memory content")
    memory_type: MemoryType = Field(..., description="Type of memory")
    importance: MemoryImportance = Field(..., description="Memory importance")
    tags: Optional[List[str]] = Field(default=None, description="Memory tags")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    embedding: Optional[List[float]] = Field(default=None, description="Memory embedding")


class ConversationRequest(BaseModel):
    """Conversation storage request model"""
    messages: List[Dict[str, Any]] = Field(..., min_items=1, description="Conversation messages")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Conversation context")
    summary: Optional[str] = Field(default=None, description="Conversation summary")


class ConversationResponse(BaseModel):
    """Conversation storage response model"""
    conversation_id: str = Field(..., description="Unique conversation identifier")
    messages: List[Dict[str, Any]] = Field(..., description="Conversation messages")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Conversation context")
    summary: Optional[str] = Field(default=None, description="Conversation summary")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class RetrieveRequest(BaseModel):
    """Memory retrieval request model"""
    query: str = Field(..., min_length=1, max_length=512, description="Retrieval query")
    memory_types: Optional[List[MemoryType]] = Field(default=None, description="Filter by memory types")
    importance_levels: Optional[List[MemoryImportance]] = Field(default=None, description="Filter by importance levels")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    include_metadata: bool = Field(default=True, description="Include metadata in results")
    similarity_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Similarity threshold")


class RetrieveResponse(BaseModel):
    """Memory retrieval response model"""
    query: str = Field(..., description="Original query")
    memories: List[MemoryResponse] = Field(..., description="Retrieved memories")
    total_results: int = Field(..., ge=0, description="Total number of matching results")
    execution_time_ms: float = Field(..., ge=0, description="Retrieval execution time")
    retrieval_id: str = Field(..., description="Unique retrieval identifier")


class ConsolidateRequest(BaseModel):
    """Memory consolidation request model"""
    user_id: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    memory_types: Optional[List[MemoryType]] = Field(default=None, description="Memory types to consolidate")
    force: bool = Field(default=False, description="Force consolidation even if threshold not met")


class ConsolidateResponse(BaseModel):
    """Memory consolidation response model"""
    consolidated_count: int = Field(..., ge=0, description="Number of memories consolidated")
    new_memories_created: int = Field(..., ge=0, description="Number of new consolidated memories created")
    consolidation_time_ms: float = Field(..., ge=0, description="Consolidation execution time")
    consolidation_id: str = Field(..., description="Unique consolidation identifier")


class ContextRequest(BaseModel):
    """Context retrieval request model"""
    query: str = Field(..., min_length=1, max_length=512, description="Context query")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    context_window: int = Field(default=50, ge=1, le=200, description="Context window size")
    include_conversations: bool = Field(default=True, description="Include conversation context")
    include_memories: bool = Field(default=True, description="Include memory context")


class ContextResponse(BaseModel):
    """Context retrieval response model"""
    query: str = Field(..., description="Original query")
    context: List[Dict[str, Any]] = Field(..., description="Retrieved context")
    total_context_items: int = Field(..., ge=0, description="Total number of context items")
    execution_time_ms: float = Field(..., ge=0, description="Context retrieval execution time")
    context_id: str = Field(..., description="Unique context identifier")


class UpdateRequest(BaseModel):
    """Memory update request model"""
    memory_id: str = Field(..., description="Memory identifier to update")
    content: Optional[str] = Field(default=None, min_length=1, max_length=2048, description="Updated content")
    memory_type: Optional[MemoryType] = Field(default=None, description="Updated memory type")
    importance: Optional[MemoryImportance] = Field(default=None, description="Updated importance")
    tags: Optional[List[str]] = Field(default=None, description="Updated tags")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Updated metadata")


class DeleteRequest(BaseModel):
    """Memory deletion request model"""
    memory_id: str = Field(..., description="Memory identifier to delete")


class DeleteResponse(BaseModel):
    """Memory deletion response model"""
    memory_id: str = Field(..., description="Memory identifier")
    deleted: bool = Field(..., description="Whether memory was successfully deleted")
    deleted_at: datetime = Field(..., description="Deletion timestamp")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    service: str = Field(default="memory-system", description="Service name")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")
    database_status: str = Field(..., description="Database health status")
    redis_status: str = Field(..., description="Redis health status")
    memory_stats: Optional[Dict[str, Any]] = Field(None, description="Memory statistics")


class StatsResponse(BaseModel):
    """Service statistics response model"""
    total_memories: int = Field(..., description="Total memory count")
    total_conversations: int = Field(..., description="Total conversation count")
    memory_types_distribution: Dict[str, int] = Field(..., description="Memory types distribution")
    importance_distribution: Dict[str, int] = Field(..., description="Importance distribution")
    average_memory_size: float = Field(..., ge=0, description="Average memory size")
    cache_hit_rate: float = Field(..., ge=0.0, le=1.0, description="Cache hit rate")
    active_sessions: int = Field(..., ge=0, description="Active session count")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request identifier")