"""
Search Engine Database Operations
"""
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Float, Integer, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.config import settings

Base = declarative_base()


class SearchContent(Base):
    """Search content database model"""
    __tablename__ = "search_content"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_content_type', 'content_type'),
        Index('idx_created_at', 'created_at'),
        Index('idx_updated_at', 'updated_at'),
    )


class SearchLog(Base):
    """Search operation log"""
    __tablename__ = "search_logs"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    query: Mapped[str] = mapped_column(Text, nullable=False)
    search_type: Mapped[str] = mapped_column(String(50), nullable=False)
    results_count: Mapped[int] = mapped_column(Integer, nullable=False)
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    cached: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """Database connection and operation manager"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._connection_pool = None
    
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Create async engine
            self.engine = create_async_engine(
                settings.database_url,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                echo=settings.debug
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Create connection pool for raw queries
            self._connection_pool = await asyncpg.create_pool(
                settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
                min_size=5,
                max_size=settings.database_pool_size
            )
            
        except Exception as e:
            raise Exception(f"Failed to initialize database: {str(e)}")
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
        if self._connection_pool:
            await self._connection_pool.close()
    
    def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.session_factory:
            raise Exception("Database not initialized")
        return self.session_factory()
    
    def get_connection(self):
        """Get raw database connection"""
        if not self._connection_pool:
            raise Exception("Database not initialized")
        return self._connection_pool.acquire()
    
    # Content operations
    async def create_content(self, content_id: str, content: str, content_type: str, 
                           metadata: Optional[Dict[str, Any]] = None, 
                           embedding: Optional[List[float]] = None) -> bool:
        """Create new searchable content"""
        try:
            async with self.get_session() as session:
                search_content = SearchContent(
                    id=content_id,
                    content=content,
                    content_type=content_type,
                    metadata=metadata,
                    embedding=embedding
                )
                session.add(search_content)
                await session.commit()
                return True
        except Exception as e:
            if settings.debug:
                print(f"Error creating content: {str(e)}")
            return False
    
    async def get_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Get content by ID"""
        try:
            async with self.get_session() as session:
                result = await session.get(SearchContent, content_id)
                if result:
                    return {
                        "id": result.id,
                        "content": result.content,
                        "content_type": result.content_type,
                        "metadata": result.content_metadata,
                        "embedding": result.embedding,
                        "created_at": result.created_at,
                        "updated_at": result.updated_at
                    }
                return None
        except Exception as e:
            if settings.debug:
                print(f"Error getting content: {str(e)}")
            return None
    
    async def update_content(self, content_id: str, content: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None,
                           embedding: Optional[List[float]] = None) -> bool:
        """Update existing content"""
        try:
            async with self.get_session() as session:
                result = await session.get(SearchContent, content_id)
                if result:
                    if content is not None:
                        result.content = content
                    if metadata is not None:
                        result.content_metadata = metadata
                    if embedding is not None:
                        result.embedding = embedding
                    result.updated_at = datetime.utcnow()
                    await session.commit()
                    return True
                return False
        except Exception as e:
            if settings.debug:
                print(f"Error updating content: {str(e)}")
            return False
    
    async def delete_content(self, content_id: str) -> bool:
        """Delete content by ID"""
        try:
            async with self.get_session() as session:
                result = await session.get(SearchContent, content_id)
                if result:
                    await session.delete(result)
                    await session.commit()
                    return True
                return False
        except Exception as e:
            if settings.debug:
                print(f"Error deleting content: {str(e)}")
            return False
    
    async def search_content(self, query: str, content_types: Optional[List[str]] = None,
                           limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Search content using full-text search"""
        try:
            async with self.get_connection() as conn:
                # Build query
                base_query = """
                    SELECT id, content, content_type, metadata, created_at, updated_at,
                           ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) as rank
                    FROM search_content
                    WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)
                """
                
                params = [query]
                param_count = 1
                
                if content_types:
                    param_count += 1
                    base_query += f" AND content_type = ANY(${param_count})"
                    params.append(content_types)
                
                base_query += f" ORDER BY rank DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
                params.extend([limit, offset])
                
                rows = await conn.fetch(base_query, *params)
                
                return [
                    {
                        "id": row["id"],
                        "content": row["content"],
                        "content_type": row["content_type"],
                        "metadata": row["metadata"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "score": float(row["rank"])
                    }
                    for row in rows
                ]
        except Exception as e:
            if settings.debug:
                print(f"Error searching content: {str(e)}")
            return []
    
    async def get_content_count(self, content_type: Optional[str] = None) -> int:
        """Get total content count"""
        try:
            async with self.get_connection() as conn:
                if content_type:
                    result = await conn.fetchval(
                        "SELECT COUNT(*) FROM search_content WHERE content_type = $1",
                        content_type
                    )
                else:
                    result = await conn.fetchval("SELECT COUNT(*) FROM search_content")
                return result or 0
        except Exception as e:
            if settings.debug:
                print(f"Error getting content count: {str(e)}")
            return 0
    
    # Search logging
    async def log_search(self, query: str, search_type: str, results_count: int, 
                        execution_time_ms: float, cached: bool = False) -> bool:
        """Log search operation"""
        try:
            async with self.get_session() as session:
                search_log = SearchLog(
                    query=query,
                    search_type=search_type,
                    results_count=results_count,
                    execution_time_ms=execution_time_ms,
                    cached=cached
                )
                session.add(search_log)
                await session.commit()
                return True
        except Exception as e:
            if settings.debug:
                print(f"Error logging search: {str(e)}")
            return False
    
    async def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics"""
        try:
            async with self.get_connection() as conn:
                total_searches = await conn.fetchval("SELECT COUNT(*) FROM search_logs")
                avg_execution_time = await conn.fetchval(
                    "SELECT AVG(execution_time_ms) FROM search_logs"
                )
                cache_hit_rate = await conn.fetchval(
                    "SELECT AVG(CASE WHEN cached THEN 1.0 ELSE 0.0 END) FROM search_logs"
                )
                
                return {
                    "total_searches": total_searches or 0,
                    "average_execution_time_ms": float(avg_execution_time or 0),
                    "cache_hit_rate": float(cache_hit_rate or 0)
                }
        except Exception as e:
            if settings.debug:
                print(f"Error getting search stats: {str(e)}")
            return {
                "total_searches": 0,
                "average_execution_time_ms": 0.0,
                "cache_hit_rate": 0.0
            }


# Global database manager instance
db_manager = DatabaseManager()