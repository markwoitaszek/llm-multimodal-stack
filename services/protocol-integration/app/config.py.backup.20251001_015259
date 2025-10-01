"""
Configuration settings for Protocol Integration Service
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    PROTOCOL_INTEGRATION_HOST: str = Field(default="0.0.0.0", env="PROTOCOL_INTEGRATION_HOST")
    PROTOCOL_INTEGRATION_PORT: int = Field(default=8009, env="PROTOCOL_INTEGRATION_PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Protocol Configuration
    LSP_ENABLED: bool = Field(default=True, env="LSP_ENABLED")
    MCP_ENABLED: bool = Field(default=True, env="MCP_ENABLED")
    CUSTOM_PROTOCOLS_ENABLED: bool = Field(default=True, env="CUSTOM_PROTOCOLS_ENABLED")
    GRAPHQL_ENABLED: bool = Field(default=True, env="GRAPHQL_ENABLED")
    
    # LSP Configuration
    LSP_MAX_CONNECTIONS: int = Field(default=100, env="LSP_MAX_CONNECTIONS")
    LSP_TIMEOUT: int = Field(default=30, env="LSP_TIMEOUT")
    LSP_SUPPORTED_LANGUAGES: List[str] = Field(
        default=["python", "javascript", "typescript", "go", "rust", "java", "cpp", "c"],
        env="LSP_SUPPORTED_LANGUAGES"
    )
    
    # MCP Configuration
    MCP_MAX_TOOLS: int = Field(default=50, env="MCP_MAX_TOOLS")
    MCP_MAX_RESOURCES: int = Field(default=100, env="MCP_MAX_RESOURCES")
    MCP_TOOL_TIMEOUT: int = Field(default=60, env="MCP_TOOL_TIMEOUT")
    
    # Custom Protocol Configuration
    CUSTOM_PROTOCOL_TIMEOUT: int = Field(default=30, env="CUSTOM_PROTOCOL_TIMEOUT")
    MAX_CUSTOM_PROTOCOLS: int = Field(default=10, env="MAX_CUSTOM_PROTOCOLS")
    
    # IDE Integration
    AI_AGENTS_URL: str = Field(default="http://ai-agents:8003", env="AI_AGENTS_URL")
    IDE_BRIDGE_URL: str = Field(default="http://ide-bridge:8007", env="IDE_BRIDGE_URL")
    
    # Database Configuration
    POSTGRES_HOST: str = Field(default="postgres", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="multimodal", env="POSTGRES_DB")
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    
    # Redis Configuration
    REDIS_HOST: str = Field(default="redis", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=8, env="REDIS_DB")
    
    # WebSocket Configuration
    WS_MAX_CONNECTIONS: int = Field(default=100, env="WS_MAX_CONNECTIONS")
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    WS_MESSAGE_SIZE_LIMIT: int = Field(default=1024 * 1024, env="WS_MESSAGE_SIZE_LIMIT")  # 1MB
    
    # Plugin Configuration
    PLUGIN_DIRECTORY: str = Field(default="/app/plugins", env="PLUGIN_DIRECTORY")
    MAX_PLUGINS: int = Field(default=20, env="MAX_PLUGINS")
    PLUGIN_TIMEOUT: int = Field(default=30, env="PLUGIN_TIMEOUT")
    
    # Performance Configuration
    MAX_CONCURRENT_REQUESTS: int = Field(default=50, env="MAX_CONCURRENT_REQUESTS")
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT")
    CACHE_TTL: int = Field(default=300, env="CACHE_TTL")  # 5 minutes
    
    # Security
    SECRET_KEY: str = Field(default="protocol-integration-secret-key", env="SECRET_KEY")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["*"],  # Configure appropriately for production
        env="ALLOWED_ORIGINS"
    )
    API_KEY_REQUIRED: bool = Field(default=False, env="API_KEY_REQUIRED")
    API_KEY_HEADER: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Monitoring
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    HEALTH_CHECK_INTERVAL: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Database URL
DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

# Redis URL
REDIS_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"