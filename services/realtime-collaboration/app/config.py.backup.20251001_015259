"""
Configuration settings for the Real-Time Collaboration Service
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Service configuration
    PORT: int = Field(default=3006, env="PORT")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    
    # Database configuration
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/realtime_collaboration",
        env="DATABASE_URL"
    )
    
    # Redis configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # Authentication
    JWT_SECRET: str = Field(
        default="",
        env="JWT_SECRET"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # WebSocket configuration
    MAX_CONNECTIONS: int = Field(default=1000, env="MAX_CONNECTIONS")
    HEARTBEAT_INTERVAL: int = Field(default=30, env="HEARTBEAT_INTERVAL")
    CONNECTION_TIMEOUT: int = Field(default=300, env="CONNECTION_TIMEOUT")
    
    # Message queue configuration
    MESSAGE_QUEUE_SIZE: int = Field(default=10000, env="MESSAGE_QUEUE_SIZE")
    MESSAGE_RETENTION_HOURS: int = Field(default=24, env="MESSAGE_RETENTION_HOURS")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # External services
    AI_AGENTS_URL: str = Field(
        default="http://localhost:3000",
        env="AI_AGENTS_URL"
    )
    IDE_BRIDGE_URL: str = Field(
        default="http://localhost:3004",
        env="IDE_BRIDGE_URL"
    )
    N8N_URL: str = Field(
        default="http://localhost:5678",
        env="N8N_URL"
    )
    
    # CORS configuration
    CORS_ORIGINS: list = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="CORS_ORIGINS"
    )
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # Security
    ENABLE_RATE_LIMITING: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    ENABLE_AUTHENTICATION: bool = Field(default=True, env="ENABLE_AUTHENTICATION")
    
    # Workspace configuration
    MAX_WORKSPACE_USERS: int = Field(default=50, env="MAX_WORKSPACE_USERS")
    MAX_WORKSPACE_AGENTS: int = Field(default=20, env="MAX_WORKSPACE_AGENTS")
    
    # Agent monitoring
    AGENT_CHECK_INTERVAL: int = Field(default=5, env="AGENT_CHECK_INTERVAL")
    AGENT_TIMEOUT: int = Field(default=300, env="AGENT_TIMEOUT")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

def get_settings() -> Settings:
    """Get application settings"""
    return Settings()