"""
Configuration settings for the memory system service
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service settings
    service_name: str = "memory-system"
    host: str = "0.0.0.0"
    port: int = 8005
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
    
    # Redis settings
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "4"))
    
    # Memory settings
    max_conversation_length: int = 1000
    memory_retention_days: int = 30
    context_window_size: int = 10
    knowledge_base_limit: int = 10000
    
    # Cache settings
    cache_ttl_seconds: int = 3600  # 1 hour
    conversation_cache_ttl: int = 1800  # 30 minutes
    knowledge_cache_ttl: int = 7200  # 2 hours
    
    # Memory consolidation settings
    consolidation_threshold: int = 50  # Consolidate when conversation reaches this length
    summary_length: int = 200  # Target summary length in words
    relevance_threshold: float = 0.7  # Minimum relevance score for memory retention
    
    # Context management
    max_context_tokens: int = 4000
    context_compression_ratio: float = 0.5
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        protected_namespaces = ('settings_',)

# Create global settings instance
settings = Settings()