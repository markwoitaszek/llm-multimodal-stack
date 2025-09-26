"""
Storage manager for MinIO/S3 operations
"""
import logging
from typing import BinaryIO, Optional
import os
from minio import Minio
from minio.error import S3Error
import hashlib

from .config import settings

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages MinIO/S3 storage operations"""
    
    def __init__(self):
        self.client: Optional[Minio] = None
        self.buckets = [
            settings.minio_bucket_images,
            settings.minio_bucket_videos,
            settings.minio_bucket_documents
        ]
    
    async def initialize(self):
        """Initialize MinIO client and create buckets"""
        try:
            self.client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure
            )
            
            # Create buckets if they don't exist
            for bucket_name in self.buckets:
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
                    logger.info(f"Created bucket: {bucket_name}")
                else:
                    logger.info(f"Bucket exists: {bucket_name}")
            
            logger.info("Storage manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize storage: {e}")
            raise
    
    async def close(self):
        """Close storage connections"""
        # MinIO client doesn't need explicit closing
        logger.info("Storage manager closed")
    
    def upload_file(self, bucket_name: str, object_name: str, 
                   file_path: str, content_type: str = None) -> bool:
        """Upload a file to MinIO"""
        try:
            self.client.fput_object(
                bucket_name, 
                object_name, 
                file_path,
                content_type=content_type
            )
            logger.info(f"Uploaded {file_path} to {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to upload file: {e}")
            return False
    
    def upload_data(self, bucket_name: str, object_name: str, 
                   data: bytes, content_type: str = None) -> bool:
        """Upload binary data to MinIO"""
        try:
            from io import BytesIO
            data_stream = BytesIO(data)
            
            self.client.put_object(
                bucket_name,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type
            )
            logger.info(f"Uploaded data to {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to upload data: {e}")
            return False
    
    def download_file(self, bucket_name: str, object_name: str, 
                     file_path: str) -> bool:
        """Download a file from MinIO"""
        try:
            self.client.fget_object(bucket_name, object_name, file_path)
            logger.info(f"Downloaded {bucket_name}/{object_name} to {file_path}")
            return True
        except S3Error as e:
            logger.error(f"Failed to download file: {e}")
            return False
    
    def get_object_url(self, bucket_name: str, object_name: str) -> str:
        """Get presigned URL for an object"""
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                bucket_name, 
                object_name, 
                expires=timedelta(hours=1)
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to get object URL: {e}")
            return ""
    
    def delete_object(self, bucket_name: str, object_name: str) -> bool:
        """Delete an object from MinIO"""
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"Deleted {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete object: {e}")
            return False
    
    def object_exists(self, bucket_name: str, object_name: str) -> bool:
        """Check if an object exists"""
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def list_objects(self, bucket_name: str, prefix: str = "") -> list:
        """List objects in a bucket with optional prefix"""
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Failed to list objects: {e}")
            return []
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate SHA-256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def calculate_data_hash(data: bytes) -> str:
        """Calculate SHA-256 hash of binary data"""
        return hashlib.sha256(data).hexdigest()
    
    def generate_object_path(self, file_hash: str, filename: str, 
                           prefix: str = "") -> str:
        """Generate object path based on hash and filename"""
        # Use first 2 chars of hash for directory structure
        dir_prefix = file_hash[:2]
        if prefix:
            return f"{prefix}/{dir_prefix}/{file_hash}_{filename}"
        return f"{dir_prefix}/{file_hash}_{filename}"

