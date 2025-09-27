"""
Configuration for Setup Wizard Service
"""

import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service configuration
    host: str = "0.0.0.0"
    port: int = 8004
    debug: bool = False
    
    # Database configuration
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "multimodal"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    
    # Storage paths
    env_file_path: str = "/app/.env"
    scripts_path: str = "/app/scripts"
    
    # Setup wizard configuration
    max_setup_attempts: int = 3
    setup_timeout: int = 300  # 5 minutes
    
    class Config:
        env_file = ".env"
        env_prefix = "SETUP_WIZARD_"


settings = Settings()
