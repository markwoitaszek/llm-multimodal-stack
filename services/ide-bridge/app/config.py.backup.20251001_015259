"""
Configuration settings for IDE Bridge Service
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    IDE_BRIDGE_HOST: str = Field(default="0.0.0.0", env="IDE_BRIDGE_HOST")
    IDE_BRIDGE_PORT: int = Field(default=8007, env="IDE_BRIDGE_PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # LSP Configuration
    LSP_MAX_CONNECTIONS: int = Field(default=100, env="LSP_MAX_CONNECTIONS")
    LSP_TIMEOUT: int = Field(default=30, env="LSP_TIMEOUT")
    LSP_ENABLED: bool = Field(default=True, env="LSP_ENABLED")
    
    # MCP Configuration
    MCP_ENABLED: bool = Field(default=True, env="MCP_ENABLED")
    MCP_TOOLS_PATH: str = Field(default="/app/tools", env="MCP_TOOLS_PATH")
    MCP_MAX_TOOLS: int = Field(default=50, env="MCP_MAX_TOOLS")
    
    # WebSocket Configuration
    WS_MAX_CONNECTIONS: int = Field(default=50, env="WS_MAX_CONNECTIONS")
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    WS_ENABLED: bool = Field(default=True, env="WS_ENABLED")
    
    # Agent Integration
    AI_AGENTS_URL: str = Field(default="http://ai-agents:8003", env="AI_AGENTS_URL")
    AGENT_TIMEOUT: int = Field(default=60, env="AGENT_TIMEOUT")
    AGENT_ENABLED: bool = Field(default=True, env="AGENT_ENABLED")
    
    # Code Analysis
    CODE_ANALYSIS_ENABLED: bool = Field(default=True, env="CODE_ANALYSIS_ENABLED")
    SUPPORTED_LANGUAGES: List[str] = Field(
        default=["python", "javascript", "typescript", "go", "rust", "java", "cpp", "c"],
        env="SUPPORTED_LANGUAGES"
    )
    
    # Database Configuration
    POSTGRES_HOST: str = Field(default="postgres", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="multimodal", env="POSTGRES_DB")
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    
    # Redis Configuration
    REDIS_HOST: str = Field(default="redis", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=6, env="REDIS_DB")
    
    # Security
    SECRET_KEY: str = Field(default="ide-bridge-secret-key", env="SECRET_KEY")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["*"],  # Configure appropriately for production
        env="ALLOWED_ORIGINS"
    )
    
    # Performance
    MAX_REQUEST_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Database URL
DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

# Redis URL
REDIS_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"