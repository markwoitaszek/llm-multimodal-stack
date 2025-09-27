"""
Database manager for PostgreSQL operations (shared with multimodal-worker)
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
import asyncpg
import json
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL database connections and operations"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool created")
            
            # Test connection
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            logger.info("Database connection verified")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def search_documents(self, filters: Dict[str, Any] = None, 
                             limit: int = 50) -> List[Dict]:
        """Search documents with optional filters"""
        query = """
            SELECT id, filename, file_type, file_size, mime_type, 
                   content_hash, metadata, created_at, updated_at
            FROM documents
        """
        params = []
        conditions = []
        
        if filters:
            if 'file_type' in filters:
                conditions.append(f"file_type = ${len(params) + 1}")
                params.append(filters['file_type'])
            
            if 'filename_pattern' in filters:
                conditions.append(f"filename ILIKE ${len(params) + 1}")
                params.append(f"%{filters['filename_pattern']}%")
            
            if 'date_from' in filters:
                conditions.append(f"created_at >= ${len(params) + 1}")
                params.append(filters['date_from'])
            
            if 'date_to' in filters:
                conditions.append(f"created_at <= ${len(params) + 1}")
                params.append(filters['date_to'])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1}"
        params.append(limit)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def get_text_chunks_by_document(self, document_id: str) -> List[Dict]:
        """Get all text chunks for a document"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, chunk_text, chunk_index, start_position, end_position,
                       embedding_id, metadata, created_at
                FROM text_chunks
                WHERE document_id = $1
                ORDER BY chunk_index
            """, document_id)
            
            return [dict(row) for row in rows]
    
    async def get_images_by_document(self, document_id: str) -> List[Dict]:
        """Get all images for a document"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, image_path, width, height, format, caption,
                       embedding_id, features, created_at
                FROM images
                WHERE document_id = $1
                ORDER BY created_at
            """, document_id)
            
            return [dict(row) for row in rows]
    
    async def get_videos_by_document(self, document_id: str) -> List[Dict]:
        """Get all videos for a document"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, video_path, duration_seconds, width, height, fps,
                       format, transcription, embedding_id, metadata, created_at
                FROM videos
                WHERE document_id = $1
                ORDER BY created_at
            """, document_id)
            
            return [dict(row) for row in rows]
    
    async def get_video_keyframes(self, video_id: str) -> List[Dict]:
        """Get all keyframes for a video"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, keyframe_path, timestamp_seconds, caption,
                       embedding_id, created_at
                FROM video_keyframes
                WHERE video_id = $1
                ORDER BY timestamp_seconds
            """, video_id)
            
            return [dict(row) for row in rows]
    
    async def get_content_by_embedding_id(self, embedding_id: str) -> Optional[Dict]:
        """Get content details by embedding ID"""
        # Check text chunks
        async with self.pool.acquire() as conn:
            # Check text chunks
            row = await conn.fetchrow("""
                SELECT 'text' as content_type, tc.id, tc.document_id, tc.chunk_text as content,
                       tc.chunk_index, tc.metadata, d.filename, d.file_type
                FROM text_chunks tc
                JOIN documents d ON tc.document_id = d.id
                WHERE tc.embedding_id = $1
            """, embedding_id)
            
            if row:
                return dict(row)
            
            # Check images
            row = await conn.fetchrow("""
                SELECT 'image' as content_type, i.id, i.document_id, i.caption as content,
                       i.image_path, i.width, i.height, i.features, d.filename, d.file_type
                FROM images i
                JOIN documents d ON i.document_id = d.id
                WHERE i.embedding_id = $1
            """, embedding_id)
            
            if row:
                return dict(row)
            
            # Check videos (transcription)
            row = await conn.fetchrow("""
                SELECT 'video' as content_type, v.id, v.document_id, v.transcription as content,
                       v.video_path, v.duration_seconds, v.metadata, d.filename, d.file_type
                FROM videos v
                JOIN documents d ON v.document_id = d.id
                WHERE v.embedding_id = $1
            """, embedding_id)
            
            if row:
                return dict(row)
            
            # Check video keyframes
            row = await conn.fetchrow("""
                SELECT 'keyframe' as content_type, vk.id, vk.video_id as document_id, 
                       vk.caption as content, vk.keyframe_path, vk.timestamp_seconds,
                       v.video_path, d.filename, d.file_type
                FROM video_keyframes vk
                JOIN videos v ON vk.video_id = v.id
                JOIN documents d ON v.document_id = d.id
                WHERE vk.embedding_id = $1
            """, embedding_id)
            
            if row:
                return dict(row)
        
        return None
    
    async def get_related_content(self, document_id: str) -> Dict[str, List[Dict]]:
        """Get all related content for a document"""
        result = {
            "text_chunks": await self.get_text_chunks_by_document(document_id),
            "images": await self.get_images_by_document(document_id),
            "videos": await self.get_videos_by_document(document_id)
        }
        
        # Get keyframes for each video
        for video in result["videos"]:
            video["keyframes"] = await self.get_video_keyframes(video["id"])
        
        return result
    
    async def create_search_session(self, query: str, session_name: str = None,
                                  filters: Dict = None, results_count: int = 0,
                                  context_bundle: Dict = None) -> str:
        """Create a search session record"""
        import uuid
        session_id = str(uuid.uuid4())
        filters = filters or {}
        context_bundle = context_bundle or {}
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO search_sessions (id, session_name, query, filters, 
                                           results_count, context_bundle)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, session_id, session_name, query, json.dumps(filters), 
               results_count, json.dumps(context_bundle))
        
        return session_id
    
    async def get_search_sessions(self, limit: int = 20) -> List[Dict]:
        """Get recent search sessions"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, session_name, query, filters, results_count, 
                       context_bundle, created_at
                FROM search_sessions
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in rows]

