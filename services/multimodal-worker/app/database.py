"""
Database manager for PostgreSQL operations
"""
import logging
from typing import Dict, List, Optional, Any
import asyncpg
import json
from datetime import datetime
import uuid

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
    
    async def create_document(self, filename: str, file_type: str, 
                            file_size: int, mime_type: str, 
                            content_hash: str, metadata: Dict = None) -> str:
        """Create a new document record"""
        document_id = str(uuid.uuid4())
        metadata = metadata or {}
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO documents (id, filename, file_type, file_size, 
                                     mime_type, content_hash, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, document_id, filename, file_type, file_size, mime_type, 
               content_hash, json.dumps(metadata))
        
        return document_id
    
    async def get_document_by_hash(self, content_hash: str) -> Optional[Dict]:
        """Get document by content hash"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, filename, file_type, file_size, mime_type, 
                       content_hash, metadata, created_at, updated_at
                FROM documents WHERE content_hash = $1
            """, content_hash)
            
            if row:
                return dict(row)
        return None
    
    async def create_text_chunk(self, document_id: str, chunk_text: str, 
                              chunk_index: int, start_pos: int = None, 
                              end_pos: int = None, embedding_id: str = None,
                              metadata: Dict = None) -> str:
        """Create a text chunk record"""
        chunk_id = str(uuid.uuid4())
        metadata = metadata or {}
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO text_chunks (id, document_id, chunk_text, chunk_index,
                                       start_position, end_position, embedding_id, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, chunk_id, document_id, chunk_text, chunk_index, start_pos, 
               end_pos, embedding_id, json.dumps(metadata))
        
        return chunk_id
    
    async def create_image(self, document_id: str, image_path: str, 
                         width: int = None, height: int = None, 
                         format: str = None, caption: str = None,
                         embedding_id: str = None, features: Dict = None) -> str:
        """Create an image record"""
        image_id = str(uuid.uuid4())
        features = features or {}
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO images (id, document_id, image_path, width, height,
                                  format, caption, embedding_id, features)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, image_id, document_id, image_path, width, height, format, 
               caption, embedding_id, json.dumps(features))
        
        return image_id
    
    async def create_video(self, document_id: str, video_path: str, 
                         duration: float = None, width: int = None, 
                         height: int = None, fps: float = None,
                         format: str = None, transcription: str = None,
                         embedding_id: str = None, metadata: Dict = None) -> str:
        """Create a video record"""
        video_id = str(uuid.uuid4())
        metadata = metadata or {}
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO videos (id, document_id, video_path, duration_seconds,
                                  width, height, fps, format, transcription, 
                                  embedding_id, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, video_id, document_id, video_path, duration, width, height, 
               fps, format, transcription, embedding_id, json.dumps(metadata))
        
        return video_id
    
    async def create_video_keyframe(self, video_id: str, keyframe_path: str,
                                  timestamp: float, caption: str = None,
                                  embedding_id: str = None) -> str:
        """Create a video keyframe record"""
        keyframe_id = str(uuid.uuid4())
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO video_keyframes (id, video_id, keyframe_path, 
                                           timestamp_seconds, caption, embedding_id)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, keyframe_id, video_id, keyframe_path, timestamp, caption, embedding_id)
        
        return keyframe_id
    
    async def create_search_session(self, query: str, session_name: str = None,
                                  filters: Dict = None, results_count: int = 0,
                                  context_bundle: Dict = None) -> str:
        """Create a search session record"""
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
    
    async def add_conversation_message(self, session_id: str, role: str, 
                                     content: str, metadata: Dict = None) -> str:
        """Add a conversation message"""
        message_id = str(uuid.uuid4())
        metadata = metadata or {}
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversations (id, session_id, role, content, metadata)
                VALUES ($1, $2, $3, $4, $5)
            """, message_id, session_id, role, content, json.dumps(metadata))
        
        return message_id
    
    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history for a session"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, role, content, metadata, created_at
                FROM conversations 
                WHERE session_id = $1
                ORDER BY created_at ASC
                LIMIT $2
            """, session_id, limit)
            
            return [dict(row) for row in rows]

