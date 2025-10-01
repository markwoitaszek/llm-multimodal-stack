"""
Configuration settings for n8n Monitoring Service
"""

import os
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    N8N_MONITORING_HOST: str = Field(default="0.0.0.0", env="N8N_MONITORING_HOST")
    N8N_MONITORING_PORT: int = Field(default=8008, env="N8N_MONITORING_PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # n8n Integration
    N8N_URL: str = Field(default="http://n8n:5678", env="N8N_URL")
    N8N_API_KEY: Optional[str] = Field(default=None, env="N8N_API_KEY")
    N8N_WEBHOOK_URL: str = Field(default="http://n8n-monitoring:8008/webhooks/n8n", env="N8N_WEBHOOK_URL")
    
    # AI Agents Integration
    AI_AGENTS_URL: str = Field(default="http://ai-agents:8003", env="AI_AGENTS_URL")
    
    # Database Configuration
    POSTGRES_HOST: str = Field(default="postgres", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="multimodal", env="POSTGRES_DB")
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    
    # Redis Configuration
    REDIS_HOST: str = Field(default="redis", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=7, env="REDIS_DB")
    
    # Monitoring Configuration
    MONITORING_INTERVAL: int = Field(default=30, env="MONITORING_INTERVAL")  # seconds
    METRICS_RETENTION_DAYS: int = Field(default=90, env="METRICS_RETENTION_DAYS")
    MAX_EXECUTION_HISTORY: int = Field(default=1000, env="MAX_EXECUTION_HISTORY")
    
    # Alert Configuration
    ALERT_EMAIL_ENABLED: bool = Field(default=True, env="ALERT_EMAIL_ENABLED")
    ALERT_SLACK_ENABLED: bool = Field(default=True, env="ALERT_SLACK_ENABLED")
    ALERT_WEBHOOK_ENABLED: bool = Field(default=False, env="ALERT_WEBHOOK_ENABLED")
    
    # Alert Thresholds
    ALERT_THRESHOLD_ERROR_RATE: float = Field(default=5.0, env="ALERT_THRESHOLD_ERROR_RATE")  # percentage
    ALERT_THRESHOLD_RESPONSE_TIME: int = Field(default=30000, env="ALERT_THRESHOLD_RESPONSE_TIME")  # milliseconds
    ALERT_THRESHOLD_FAILURE_COUNT: int = Field(default=5, env="ALERT_THRESHOLD_FAILURE_COUNT")
    
    # Email Configuration
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: Optional[str] = Field(default=None, env="SMTP_FROM_EMAIL")
    
    # Slack Configuration
    SLACK_WEBHOOK_URL: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    SLACK_CHANNEL: str = Field(default="#n8n-monitoring", env="SLACK_CHANNEL")
    
    # WebSocket Configuration
    WS_MAX_CONNECTIONS: int = Field(default=100, env="WS_MAX_CONNECTIONS")
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    
    # Performance Configuration
    MAX_CONCURRENT_MONITORS: int = Field(default=10, env="MAX_CONCURRENT_MONITORS")
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # Security
    SECRET_KEY: str = Field(default="n8n-monitoring-secret-key", env="SECRET_KEY")
    ALLOWED_ORIGINS: Union[str, List[str]] = Field(
        default="*",  # Configure appropriately for production
        env="ALLOWED_ORIGINS"
    )
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from string or list"""
        if isinstance(v, str):
            # Handle "*" or comma-separated values
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",")]
        return v
    
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