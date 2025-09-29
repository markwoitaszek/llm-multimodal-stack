"""
Memory System Database Operations
"""
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Float, Integer, JSON, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.config import settings

Base = declarative_base()


class Memory(Base):
    """Memory database model"""
    __tablename__ = "memories"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    importance: Mapped[str] = mapped_column(String(20), nullable=False)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    memory_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    related_memory_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    consolidated: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_memory_type', 'memory_type'),
        Index('idx_importance', 'importance'),
        Index('idx_user_id', 'user_id'),
        Index('idx_session_id', 'session_id'),
        Index('idx_created_at', 'created_at'),
        Index('idx_updated_at', 'updated_at'),
        Index('idx_accessed_at', 'accessed_at'),
        Index('idx_consolidated', 'consolidated'),
    )


class Conversation(Base):
    """Conversation database model"""
    __tablename__ = "conversations"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    messages: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_conversation_user_id', 'user_id'),
        Index('idx_conversation_session_id', 'session_id'),
        Index('idx_conversation_created_at', 'created_at'),
        Index('idx_conversation_updated_at', 'updated_at'),
    )


class MemoryAccessLog(Base):
    """Memory access log"""
    __tablename__ = "memory_access_logs"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    memory_id: Mapped[str] = mapped_column(String(255), nullable=False)
    access_type: Mapped[str] = mapped_column(String(50), nullable=False)  # read, update, delete
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
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
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.session_factory:
            raise Exception("Database not initialized")
        return self.session_factory()
    
    async def get_connection(self):
        """Get raw database connection"""
        if not self._connection_pool:
            raise Exception("Database not initialized")
        return self._connection_pool.acquire()
    
    # Memory operations
    async def create_memory(self, memory_id: str, content: str, memory_type: str,
                          importance: str, tags: Optional[List[str]] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          embedding: Optional[List[float]] = None,
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None,
                          related_memory_ids: Optional[List[str]] = None) -> bool:
        """Create new memory"""
        try:
            async with self.get_session() as session:
                memory = Memory(
                    id=memory_id,
                    content=content,
                    memory_type=memory_type,
                    importance=importance,
                    tags=tags,
                    metadata=metadata,
                    embedding=embedding,
                    user_id=user_id,
                    session_id=session_id,
                    related_memory_ids=related_memory_ids
                )
                session.add(memory)
                await session.commit()
                return True
        except Exception as e:
            if settings.debug:
                print(f"Error creating memory: {str(e)}")
            return False
    
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get memory by ID"""
        try:
            async with self.get_session() as session:
                result = await session.get(Memory, memory_id)
                if result:
                    # Update access tracking
                    result.accessed_at = datetime.utcnow()
                    result.access_count += 1
                    await session.commit()
                    
                    return {
                        "id": result.id,
                        "content": result.content,
                        "memory_type": result.memory_type,
                        "importance": result.importance,
                        "tags": result.tags,
                        "metadata": result.memory_metadata,
                        "embedding": result.embedding,
                        "user_id": result.user_id,
                        "session_id": result.session_id,
                        "related_memory_ids": result.related_memory_ids,
                        "created_at": result.created_at,
                        "updated_at": result.updated_at,
                        "accessed_at": result.accessed_at,
                        "access_count": result.access_count,
                        "consolidated": result.consolidated
                    }
                return None
        except Exception as e:
            if settings.debug:
                print(f"Error getting memory: {str(e)}")
            return None
    
    async def update_memory(self, memory_id: str, content: Optional[str] = None,
                          memory_type: Optional[str] = None,
                          importance: Optional[str] = None,
                          tags: Optional[List[str]] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          embedding: Optional[List[float]] = None) -> bool:
        """Update existing memory"""
        try:
            async with self.get_session() as session:
                result = await session.get(Memory, memory_id)
                if result:
                    if content is not None:
                        result.content = content
                    if memory_type is not None:
                        result.memory_type = memory_type
                    if importance is not None:
                        result.importance = importance
                    if tags is not None:
                        result.tags = tags
                    if metadata is not None:
                        result.memory_metadata = metadata
                    if embedding is not None:
                        result.embedding = embedding
                    result.updated_at = datetime.utcnow()
                    await session.commit()
                    return True
                return False
        except Exception as e:
            if settings.debug:
                print(f"Error updating memory: {str(e)}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory by ID"""
        try:
            async with self.get_session() as session:
                result = await session.get(Memory, memory_id)
                if result:
                    await session.delete(result)
                    await session.commit()
                    return True
                return False
        except Exception as e:
            if settings.debug:
                print(f"Error deleting memory: {str(e)}")
            return False
    
    async def search_memories(self, query: str, memory_types: Optional[List[str]] = None,
                            importance_levels: Optional[List[str]] = None,
                            tags: Optional[List[str]] = None,
                            user_id: Optional[str] = None,
                            session_id: Optional[str] = None,
                            limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Search memories using full-text search"""
        try:
            async with self.get_connection() as conn:
                # Build query
                base_query = """
                    SELECT id, content, memory_type, importance, tags, metadata, 
                           user_id, session_id, related_memory_ids, created_at, updated_at,
                           accessed_at, access_count, consolidated,
                           ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) as rank
                    FROM memories
                    WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)
                """
                
                params = [query]
                param_count = 1
                
                if memory_types:
                    param_count += 1
                    base_query += f" AND memory_type = ANY(${param_count})"
                    params.append(memory_types)
                
                if importance_levels:
                    param_count += 1
                    base_query += f" AND importance = ANY(${param_count})"
                    params.append(importance_levels)
                
                if user_id:
                    param_count += 1
                    base_query += f" AND user_id = ${param_count}"
                    params.append(user_id)
                
                if session_id:
                    param_count += 1
                    base_query += f" AND session_id = ${param_count}"
                    params.append(session_id)
                
                base_query += f" ORDER BY rank DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
                params.extend([limit, offset])
                
                rows = await conn.fetch(base_query, *params)
                
                return [
                    {
                        "id": row["id"],
                        "content": row["content"],
                        "memory_type": row["memory_type"],
                        "importance": row["importance"],
                        "tags": row["tags"],
                        "metadata": row["metadata"],
                        "user_id": row["user_id"],
                        "session_id": row["session_id"],
                        "related_memory_ids": row["related_memory_ids"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "accessed_at": row["accessed_at"],
                        "access_count": row["access_count"],
                        "consolidated": row["consolidated"],
                        "score": float(row["rank"])
                    }
                    for row in rows
                ]
        except Exception as e:
            if settings.debug:
                print(f"Error searching memories: {str(e)}")
            return []
    
    async def get_memory_count(self, memory_type: Optional[str] = None,
                             importance: Optional[str] = None,
                             user_id: Optional[str] = None) -> int:
        """Get total memory count"""
        try:
            async with self.get_connection() as conn:
                where_conditions = []
                params = []
                
                if memory_type:
                    where_conditions.append("memory_type = $1")
                    params.append(memory_type)
                
                if importance:
                    param_count = len(params) + 1
                    where_conditions.append(f"importance = ${param_count}")
                    params.append(importance)
                
                if user_id:
                    param_count = len(params) + 1
                    where_conditions.append(f"user_id = ${param_count}")
                    params.append(user_id)
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                result = await conn.fetchval(f"SELECT COUNT(*) FROM memories {where_clause}", *params)
                return result or 0
        except Exception as e:
            if settings.debug:
                print(f"Error getting memory count: {str(e)}")
            return 0
    
    # Conversation operations
    async def create_conversation(self, conversation_id: str, messages: List[Dict[str, Any]],
                                user_id: Optional[str] = None,
                                session_id: Optional[str] = None,
                                context: Optional[Dict[str, Any]] = None,
                                summary: Optional[str] = None) -> bool:
        """Create new conversation"""
        try:
            async with self.get_session() as session:
                conversation = Conversation(
                    id=conversation_id,
                    messages=messages,
                    user_id=user_id,
                    session_id=session_id,
                    context=context,
                    summary=summary
                )
                session.add(conversation)
                await session.commit()
                return True
        except Exception as e:
            if settings.debug:
                print(f"Error creating conversation: {str(e)}")
            return False
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        try:
            async with self.get_session() as session:
                result = await session.get(Conversation, conversation_id)
                if result:
                    # Update access tracking
                    result.accessed_at = datetime.utcnow()
                    result.access_count += 1
                    await session.commit()
                    
                    return {
                        "id": result.id,
                        "messages": result.messages,
                        "user_id": result.user_id,
                        "session_id": result.session_id,
                        "context": result.context,
                        "summary": result.summary,
                        "created_at": result.created_at,
                        "updated_at": result.updated_at,
                        "accessed_at": result.accessed_at,
                        "access_count": result.access_count
                    }
                return None
        except Exception as e:
            if settings.debug:
                print(f"Error getting conversation: {str(e)}")
            return None
    
    async def get_conversations_by_session(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversations by session ID"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM conversations WHERE session_id = $1 ORDER BY created_at DESC LIMIT $2",
                    session_id, limit
                )
                
                return [
                    {
                        "id": row["id"],
                        "messages": row["messages"],
                        "user_id": row["user_id"],
                        "session_id": row["session_id"],
                        "context": row["context"],
                        "summary": row["summary"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "accessed_at": row["accessed_at"],
                        "access_count": row["access_count"]
                    }
                    for row in rows
                ]
        except Exception as e:
            if settings.debug:
                print(f"Error getting conversations by session: {str(e)}")
            return []
    
    async def get_conversation_count(self, user_id: Optional[str] = None) -> int:
        """Get total conversation count"""
        try:
            async with self.get_connection() as conn:
                if user_id:
                    result = await conn.fetchval(
                        "SELECT COUNT(*) FROM conversations WHERE user_id = $1",
                        user_id
                    )
                else:
                    result = await conn.fetchval("SELECT COUNT(*) FROM conversations")
                return result or 0
        except Exception as e:
            if settings.debug:
                print(f"Error getting conversation count: {str(e)}")
            return 0
    
    # Memory consolidation operations
    async def get_memories_for_consolidation(self, user_id: Optional[str] = None,
                                           session_id: Optional[str] = None,
                                           memory_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get memories that need consolidation"""
        try:
            async with self.get_connection() as conn:
                base_query = """
                    SELECT * FROM memories 
                    WHERE consolidated = false
                """
                
                params = []
                param_count = 0
                
                if user_id:
                    param_count += 1
                    base_query += f" AND user_id = ${param_count}"
                    params.append(user_id)
                
                if session_id:
                    param_count += 1
                    base_query += f" AND session_id = ${param_count}"
                    params.append(session_id)
                
                if memory_types:
                    param_count += 1
                    base_query += f" AND memory_type = ANY(${param_count})"
                    params.append(memory_types)
                
                base_query += " ORDER BY created_at ASC LIMIT $1"
                params.insert(0, settings.memory_consolidation_threshold)
                
                rows = await conn.fetch(base_query, *params)
                
                return [
                    {
                        "id": row["id"],
                        "content": row["content"],
                        "memory_type": row["memory_type"],
                        "importance": row["importance"],
                        "tags": row["tags"],
                        "metadata": row["metadata"],
                        "user_id": row["user_id"],
                        "session_id": row["session_id"],
                        "created_at": row["created_at"]
                    }
                    for row in rows
                ]
        except Exception as e:
            if settings.debug:
                print(f"Error getting memories for consolidation: {str(e)}")
            return []
    
    async def mark_memories_consolidated(self, memory_ids: List[str]) -> bool:
        """Mark memories as consolidated"""
        try:
            async with self.get_session() as session:
                for memory_id in memory_ids:
                    result = await session.get(Memory, memory_id)
                    if result:
                        result.consolidated = True
                        result.updated_at = datetime.utcnow()
                await session.commit()
                return True
        except Exception as e:
            if settings.debug:
                print(f"Error marking memories consolidated: {str(e)}")
            return False
    
    # Statistics and cleanup
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            async with self.get_connection() as conn:
                # Get total counts
                total_memories = await conn.fetchval("SELECT COUNT(*) FROM memories")
                total_conversations = await conn.fetchval("SELECT COUNT(*) FROM conversations")
                
                # Get memory type distribution
                type_dist = await conn.fetch(
                    "SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type"
                )
                memory_types_distribution = {row["memory_type"]: row["count"] for row in type_dist}
                
                # Get importance distribution
                importance_dist = await conn.fetch(
                    "SELECT importance, COUNT(*) FROM memories GROUP BY importance"
                )
                importance_distribution = {row["importance"]: row["count"] for row in importance_dist}
                
                # Get average memory size
                avg_size = await conn.fetchval(
                    "SELECT AVG(LENGTH(content)) FROM memories"
                )
                
                return {
                    "total_memories": total_memories or 0,
                    "total_conversations": total_conversations or 0,
                    "memory_types_distribution": memory_types_distribution,
                    "importance_distribution": importance_distribution,
                    "average_memory_size": float(avg_size or 0)
                }
        except Exception as e:
            if settings.debug:
                print(f"Error getting memory stats: {str(e)}")
            return {
                "total_memories": 0,
                "total_conversations": 0,
                "memory_types_distribution": {},
                "importance_distribution": {},
                "average_memory_size": 0.0
            }
    
    async def cleanup_old_memories(self, days: int = None) -> int:
        """Clean up old memories"""
        if days is None:
            days = settings.memory_retention_days
        
        try:
            async with self.get_connection() as conn:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Get count of memories to delete
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM memories WHERE created_at < $1",
                    cutoff_date
                )
                
                # Delete old memories
                await conn.execute(
                    "DELETE FROM memories WHERE created_at < $1",
                    cutoff_date
                )
                
                return count or 0
        except Exception as e:
            if settings.debug:
                print(f"Error cleaning up old memories: {str(e)}")
            return 0


# Global database manager instance
db_manager = DatabaseManager()