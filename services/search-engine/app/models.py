"""
Pydantic models for the search engine service
"""
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class SearchType(str, Enum):
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    KEYWORD = "keyword"
    AUTOSUGGEST = "autosuggest"

class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"

class SortOrder(str, Enum):
    RELEVANCE = "relevance"
    DATE_ASC = "date_asc"
    DATE_DESC = "date_desc"
    SCORE_ASC = "score_asc"
    SCORE_DESC = "score_desc"

class SearchRequest(BaseModel):
    """Base search request model"""
    query: str = Field(..., description="Search query", max_length=500)
    content_types: Optional[List[ContentType]] = Field(default=None, description="Content types to search")
    limit: Optional[int] = Field(default=20, ge=1, le=100, description="Maximum number of results")
    offset: Optional[int] = Field(default=0, ge=0, description="Number of results to skip")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")
    sort_by: Optional[SortOrder] = Field(default=SortOrder.RELEVANCE, description="Sort order")
    include_metadata: Optional[bool] = Field(default=True, description="Include metadata in results")
    user_id: Optional[str] = Field(default=None, description="User ID for personalization")

class SemanticSearchRequest(SearchRequest):
    """Semantic search request"""
    similarity_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    embedding_model: Optional[str] = Field(default="default", description="Embedding model to use")
    expand_query: Optional[bool] = Field(default=True, description="Expand query with synonyms")

class HybridSearchRequest(SearchRequest):
    """Hybrid search request combining semantic and keyword search"""
    semantic_weight: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="Weight for semantic search")
    keyword_weight: Optional[float] = Field(default=0.3, ge=0.0, le=1.0, description="Weight for keyword search")
    fusion_method: Optional[str] = Field(default="rrf", description="Result fusion method")
    similarity_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")

class AutocompleteRequest(BaseModel):
    """Autocomplete request"""
    query: str = Field(..., description="Partial query", max_length=100)
    limit: Optional[int] = Field(default=10, ge=1, le=50, description="Maximum number of suggestions")
    content_types: Optional[List[ContentType]] = Field(default=None, description="Content types to search")

class SearchResult(BaseModel):
    """Individual search result"""
    id: str = Field(..., description="Result ID")
    title: str = Field(..., description="Result title")
    content: str = Field(..., description="Result content snippet")
    content_type: ContentType = Field(..., description="Type of content")
    score: float = Field(..., description="Relevance score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    url: Optional[str] = Field(default=None, description="URL to the content")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")

class SearchResponse(BaseModel):
    """Search response"""
    query: str = Field(..., description="Original query")
    search_type: SearchType = Field(..., description="Type of search performed")
    results: List[SearchResult] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")
    processing_time_ms: float = Field(..., description="Search processing time in milliseconds")
    suggestions: Optional[List[str]] = Field(default=None, description="Query suggestions")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")

class AutocompleteResponse(BaseModel):
    """Autocomplete response"""
    query: str = Field(..., description="Original query")
    suggestions: List[str] = Field(..., description="Autocomplete suggestions")
    total_count: int = Field(..., description="Total number of suggestions")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

class SearchAnalytics(BaseModel):
    """Search analytics data"""
    query: str = Field(..., description="Search query")
    search_type: SearchType = Field(..., description="Type of search")
    results_count: int = Field(..., description="Number of results returned")
    processing_time_ms: float = Field(..., description="Processing time")
    user_id: Optional[str] = Field(default=None, description="User ID")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Search timestamp")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Applied filters")
    clicked_results: Optional[List[str]] = Field(default=None, description="Clicked result IDs")

class SearchSession(BaseModel):
    """Search session data"""
    session_id: str = Field(..., description="Session ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity time")
    search_count: int = Field(default=0, description="Number of searches in session")
    queries: List[str] = Field(default_factory=list, description="Queries in session")

class FilterOption(BaseModel):
    """Filter option for faceted search"""
    field: str = Field(..., description="Filter field name")
    value: Any = Field(..., description="Filter value")
    count: int = Field(..., description="Number of results for this filter")
    label: Optional[str] = Field(default=None, description="Human-readable label")

class FacetedSearchResponse(BaseModel):
    """Faceted search response with filter options"""
    query: str = Field(..., description="Original query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    facets: Dict[str, List[FilterOption]] = Field(..., description="Available filter options")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

class SearchSuggestion(BaseModel):
    """Search suggestion"""
    text: str = Field(..., description="Suggestion text")
    type: str = Field(..., description="Suggestion type (query, correction, expansion)")
    score: float = Field(..., description="Suggestion relevance score")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class SuggestionsResponse(BaseModel):
    """Search suggestions response"""
    query: str = Field(..., description="Original query")
    suggestions: List[SearchSuggestion] = Field(..., description="Search suggestions")
    total_count: int = Field(..., description="Total number of suggestions")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

class HealthCheck(BaseModel):
    """Health check response"""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    components: Dict[str, str] = Field(..., description="Component statuses")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")

class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")