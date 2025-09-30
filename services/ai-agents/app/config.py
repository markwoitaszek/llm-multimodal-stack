"""
Configuration settings for the AI agents service
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Service settings
    service_name: str = "ai-agents"
    host: str = "0.0.0.0"
    port: int = 8003
    debug: bool = False
    
    # LangChain settings
    langchain_verbose: bool = True
    langchain_debug: bool = False
    
    # LLM settings
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://vllm:8000/v1")
    llm_model: str = os.getenv("LLM_MODEL", "microsoft/DialoGPT-medium")
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1000
    
    # Database settings (shared with other services)
    postgres_host: str = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "multimodal")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")
    
    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    # Qdrant settings
    qdrant_host: str = os.getenv("QDRANT_HOST", "qdrant")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_collection_agents: str = "agent_memory"
    
    # Redis settings (for agent memory and caching)
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = 1  # Use different DB than other services
    
    # Multimodal service URLs
    multimodal_worker_url: str = os.getenv("MULTIMODAL_WORKER_URL", "http://multimodal-worker:8001")
    retrieval_proxy_url: str = os.getenv("RETRIEVAL_PROXY_URL", "http://retrieval-proxy:8002")
    
    # Phase 2 service URLs
    search_engine_url: str = os.getenv("SEARCH_ENGINE_URL", "http://search-engine:8004")
    memory_system_url: str = os.getenv("MEMORY_SYSTEM_URL", "http://memory-system:8005")
    user_management_url: str = os.getenv("USER_MANAGEMENT_URL", "http://user-management:8006")
    
    # Agent settings
    max_agents_per_user: int = 10
    agent_execution_timeout: int = 300  # 5 minutes
    max_tool_calls_per_execution: int = 50
    agent_memory_retention_days: int = 30
    
    # Tool settings
    enable_web_search: bool = True
    enable_file_operations: bool = True
    enable_code_execution: bool = False  # Disabled by default for security
    
    # Security settings
    require_authentication: bool = False  # Will be enabled with user management
    allowed_origins: list = ["*"]  # Will be restricted in production
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra='ignore'
    )

# Create global settings instance
settings = Settings()
