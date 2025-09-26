"""
Configuration settings for the retrieval proxy service
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service settings
    service_name: str = "retrieval-proxy"
    host: str = "0.0.0.0"
    port: int = 8002
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
    
    # MinIO settings
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    minio_secure: bool = False
    
    # Multimodal worker settings
    multimodal_worker_url: str = os.getenv("MULTIMODAL_WORKER_URL", "http://localhost:8001")
    
    # Search settings
    default_search_limit: int = 10
    max_search_limit: int = 100
    similarity_threshold: float = 0.7
    
    # Context bundling settings
    max_context_length: int = 4000  # Maximum tokens in context bundle
    context_overlap_ratio: float = 0.1  # Overlap between context chunks
    
    # Citation settings
    enable_citations: bool = True
    citation_format: str = "markdown"  # markdown, json, plain
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings()

