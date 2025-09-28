"""
Configuration settings for the multimodal worker service
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Service settings
    service_name: str = "multimodal-worker"
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = False
    
    # GPU settings
    cuda_visible_devices: str = "0"
    device: str = "cuda" if os.getenv("CUDA_VISIBLE_DEVICES") else "cpu"
    
    # Model settings
    clip_model: str = "openai/clip-vit-base-patch32"
    blip_model: str = "Salesforce/blip-image-captioning-base"
    whisper_model: str = "base"
    sentence_transformer_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Cache settings
    cache_dir: str = "/app/cache"
    model_cache_dir: str = "/app/cache/models"
    temp_dir: str = "/tmp"
    
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
    minio_bucket_images: str = "images"
    minio_bucket_videos: str = "videos"
    minio_bucket_documents: str = "documents"
    minio_secure: bool = False
    
    # Redis settings (for model caching)
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    
    # Processing settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_video_duration: int = 3600  # 1 hour in seconds
    keyframe_interval: int = 30  # Extract keyframe every 30 seconds
    chunk_size: int = 512  # Text chunk size for embeddings
    chunk_overlap: int = 50  # Text chunk overlap
    
    # Image processing settings
    image_max_size: tuple = (1024, 1024)
    image_quality: int = 95
    supported_image_formats: list = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]
    
    # Video processing settings
    supported_video_formats: list = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"]
    video_thumbnail_size: tuple = (320, 240)
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        protected_namespaces=('settings_',),
        extra='ignore'
    )

# Create global settings instance
settings = Settings()

