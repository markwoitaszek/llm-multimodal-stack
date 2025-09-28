"""
Search Engine Data Models
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SearchType(str, Enum):
    """Search type enumeration"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    FILTERED = "filtered"


class ContentType(str, Enum):
    """Content type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, max_length=512, description="Search query")
    search_type: SearchType = Field(default=SearchType.HYBRID, description="Type of search to perform")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    content_types: Optional[List[ContentType]] = Field(default=None, description="Filter by content types")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")
    include_metadata: bool = Field(default=True, description="Include metadata in results")
    use_cache: bool = Field(default=True, description="Use cached results if available")


class SearchResult(BaseModel):
    """Individual search result"""
    id: str = Field(..., description="Unique identifier")
    content: str = Field(..., description="Content text or description")
    content_type: ContentType = Field(..., description="Type of content")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SearchResponse(BaseModel):
    """Search response model"""
    query: str = Field(..., description="Original search query")
    search_type: SearchType = Field(..., description="Type of search performed")
    total_results: int = Field(..., ge=0, description="Total number of matching results")
    results: List[SearchResult] = Field(..., description="Search results")
    execution_time_ms: float = Field(..., ge=0, description="Search execution time in milliseconds")
    cached: bool = Field(default=False, description="Whether results were served from cache")
    search_id: str = Field(..., description="Unique search identifier")


class IndexRequest(BaseModel):
    """Index content request model"""
    content_id: str = Field(..., description="Unique content identifier")
    content: str = Field(..., description="Content to index")
    content_type: ContentType = Field(..., description="Type of content")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    embedding: Optional[List[float]] = Field(default=None, description="Pre-computed embedding")


class IndexResponse(BaseModel):
    """Index content response model"""
    content_id: str = Field(..., description="Content identifier")
    indexed: bool = Field(..., description="Whether content was successfully indexed")
    embedding_dimension: Optional[int] = Field(default=None, description="Embedding dimension")
    indexed_at: datetime = Field(..., description="Indexing timestamp")


class DeleteRequest(BaseModel):
    """Delete content request model"""
    content_id: str = Field(..., description="Content identifier to delete")


class DeleteResponse(BaseModel):
    """Delete content response model"""
    content_id: str = Field(..., description="Content identifier")
    deleted: bool = Field(..., description="Whether content was successfully deleted")
    deleted_at: datetime = Field(..., description="Deletion timestamp")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")
    dependencies: Dict[str, str] = Field(..., description="Dependency status")


class StatsResponse(BaseModel):
    """Service statistics response model"""
    total_indexed_content: int = Field(..., description="Total indexed content count")
    total_searches: int = Field(..., description="Total search operations")
    cache_hit_rate: float = Field(..., ge=0.0, le=1.0, description="Cache hit rate")
    average_search_time_ms: float = Field(..., ge=0, description="Average search time")
    active_connections: int = Field(..., ge=0, description="Active database connections")
    memory_usage_mb: float = Field(..., ge=0, description="Memory usage in MB")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request identifier")