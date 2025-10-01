"""
Search Engine Service Configuration
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    service_name: str = "search-engine"
    service_port: int = 8004
    service_host: str = "0.0.0.0"
    debug: bool = False
    
    # Database Configuration
    postgres_host: str = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    postgres_db: str = os.getenv("POSTGRES_DB", "multimodal")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis Configuration
    redis_url: str = "redis://redis:6379/0"
    redis_password: Optional[str] = None
    redis_pool_size: int = 10
    
    # Qdrant Configuration
    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection_name: str = "multimodal_embeddings"
    
    # Search Configuration
    default_search_limit: int = 10
    max_search_limit: int = 100
    cache_ttl: int = 3600  # 1 hour
    search_timeout: int = 30
    
    # Model Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    max_query_length: int = 512
    
    # Performance Configuration
    batch_size: int = 32
    max_concurrent_searches: int = 10
    result_cache_size: int = 1000
    
    # Security Configuration
    api_key_header: str = "X-API-Key"
    rate_limit_per_minute: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()