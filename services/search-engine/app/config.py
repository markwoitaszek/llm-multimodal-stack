"""
Configuration settings for the search engine service
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service settings
    service_name: str = "search-engine"
    host: str = "0.0.0.0"
    port: int = 8004
    debug: bool = False
    
    # Database settings
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "multimodal")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    # Qdrant settings
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_collection_text: str = "text_embeddings"
    qdrant_collection_image: str = "image_embeddings"
    qdrant_collection_video: str = "video_embeddings"
    
    # Redis settings
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "3"))
    
    # Search settings
    default_limit: int = 20
    max_limit: int = 100
    cache_ttl: int = 3600  # 1 hour
    similarity_threshold: float = 0.7
    
    # Query processing settings
    max_query_length: int = 500
    enable_query_expansion: bool = True
    enable_spell_check: bool = True
    enable_autocomplete: bool = True
    
    # Hybrid search settings
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    fusion_method: str = "rrf"  # reciprocal rank fusion
    
    # Performance settings
    max_concurrent_searches: int = 10
    search_timeout: int = 30  # seconds
    batch_size: int = 100
    
    # Analytics settings
    enable_analytics: bool = True
    analytics_retention_days: int = 30
    
    # External service URLs
    multimodal_worker_url: str = os.getenv("MULTIMODAL_WORKER_URL", "http://localhost:8001")
    retrieval_proxy_url: str = os.getenv("RETRIEVAL_PROXY_URL", "http://localhost:8002")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings()