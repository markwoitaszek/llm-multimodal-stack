"""
User Management Service Configuration
"""
import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    service_name: str = "user-management"
    service_port: int = 8006
    service_host: str = "0.0.0.0"
    debug: bool = False
    
    # Database Configuration
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/multimodal"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis Configuration
    redis_url: str = "redis://redis:6379/0"
    redis_password: Optional[str] = None
    redis_pool_size: int = 10
    
    # JWT Configuration
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Password Configuration
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special_chars: bool = True
    
    # Rate Limiting Configuration
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    
    # Session Configuration
    session_timeout_minutes: int = 120
    max_concurrent_sessions: int = 5
    session_cleanup_interval_minutes: int = 30
    
    # Multi-tenancy Configuration
    default_tenant_id: str = "default"
    tenant_isolation_enabled: bool = True
    max_users_per_tenant: int = 1000
    
    # Security Configuration
    api_key_header: str = "X-API-Key"
    cors_origins: list = ["*"]
    require_email_verification: bool = False
    require_phone_verification: bool = False
    
    # Performance Configuration
    max_concurrent_operations: int = 10
    cache_ttl: int = 3600  # 1 hour
    
    # Email Configuration (for notifications)
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    from_email: str = "noreply@example.com"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()