"""
Database operations for the memory system service
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import asyncpg
from asyncpg import Connection, Pool
from contextlib import asynccontextmanager

from .config import settings
from .models import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    MessageCreate, MessageResponse, MessageRole,
    KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse, KnowledgeCategory,
    MemorySummary, MemoryStats
)

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL database operations for memory system"""
    
    def __init__(self):
        self.pool: Optional[Pool] = None
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                settings.postgres_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            await self._create_tables()
            self.is_initialized = True
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def _create_tables(self):
        """Create database tables if they don't exist"""
        async with self.pool.acquire() as conn:
            # Conversations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_id VARCHAR(255) NOT NULL,
                    title VARCHAR(500),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    metadata JSONB
                )
            """)
            
            # Create indexes for conversations
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_agent_id ON conversations(agent_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_active ON conversations(is_active)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at)
            """)
            
            # Messages table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
                    content TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    metadata JSONB
                )
            """)
            
            # Create indexes for messages
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role)
            """)
            
            # Knowledge base table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_id VARCHAR(255) NOT NULL,
                    category VARCHAR(50) NOT NULL CHECK (category IN ('fact', 'procedure', 'preference', 'context', 'reference')),
                    title VARCHAR(500) NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT[],
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    metadata JSONB,
                    source VARCHAR(500)
                )
            """)
            
            # Create indexes for knowledge base
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_agent_id ON knowledge_base(agent_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_base(category)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge_base USING GIN(tags)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_created ON knowledge_base(created_at)
            """)
            
            # Memory summaries table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_summaries (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_id VARCHAR(255) NOT NULL,
                    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                    summary_type VARCHAR(100) NOT NULL,
                    content TEXT NOT NULL,
                    message_range_start INTEGER NOT NULL,
                    message_range_end INTEGER NOT NULL,
                    relevance_score FLOAT DEFAULT 0.0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Create indexes for memory summaries
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_summaries_agent_id ON memory_summaries(agent_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_summaries_conversation ON memory_summaries(conversation_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_summaries_relevance ON memory_summaries(relevance_score)
            """)
            
            # Create indexes for better performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_agent_active 
                ON conversations(agent_id, is_active) WHERE is_active = true
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_created 
                ON messages(conversation_id, created_at)
            """)
            
            logger.info("Database tables created successfully")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            raise RuntimeError("Database not initialized")
        async with self.pool.acquire() as conn:
            yield conn
    
    # Conversation operations
    async def create_conversation(self, conv_data: ConversationCreate) -> str:
        """Create a new conversation"""
        async with self.get_connection() as conn:
            conv_id = await conn.fetchval("""
                INSERT INTO conversations (agent_id, title, metadata)
                VALUES ($1, $2, $3)
                RETURNING id
            """, conv_data.agent_id, conv_data.title, conv_data.metadata)
            return str(conv_id)
    
    async def get_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT c.*, COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.id = $1
                GROUP BY c.id
            """, uuid.UUID(conv_id))
            return dict(row) if row else None
    
    async def update_conversation(self, conv_id: str, update_data: ConversationUpdate) -> bool:
        """Update conversation"""
        async with self.get_connection() as conn:
            # Build dynamic update query
            updates = []
            params = []
            param_count = 1
            
            if update_data.title is not None:
                updates.append(f"title = ${param_count}")
                params.append(update_data.title)
                param_count += 1
            
            if update_data.metadata is not None:
                updates.append(f"metadata = ${param_count}")
                params.append(update_data.metadata)
                param_count += 1
            
            if update_data.is_active is not None:
                updates.append(f"is_active = ${param_count}")
                params.append(update_data.is_active)
                param_count += 1
            
            if not updates:
                return True
            
            updates.append(f"updated_at = ${param_count}")
            params.append(datetime.utcnow())
            params.append(uuid.UUID(conv_id))
            
            result = await conn.execute(f"""
                UPDATE conversations 
                SET {', '.join(updates)}
                WHERE id = ${param_count + 1}
            """, *params)
            
            return result == "UPDATE 1"
    
    async def delete_conversation(self, conv_id: str) -> bool:
        """Delete conversation and all related data"""
        async with self.get_connection() as conn:
            result = await conn.execute("""
                DELETE FROM conversations WHERE id = $1
            """, uuid.UUID(conv_id))
            return result == "DELETE 1"
    
    async def list_conversations(self, agent_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List conversations for an agent"""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT c.*, COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.agent_id = $1
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                LIMIT $2 OFFSET $3
            """, agent_id, limit, offset)
            return [dict(row) for row in rows]
    
    # Message operations
    async def add_message(self, msg_data: MessageCreate) -> str:
        """Add a message to a conversation"""
        async with self.get_connection() as conn:
            msg_id = await conn.fetchval("""
                INSERT INTO messages (conversation_id, role, content, metadata)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, uuid.UUID(msg_data.conversation_id), msg_data.role.value, 
                msg_data.content, msg_data.metadata)
            
            # Update conversation updated_at
            await conn.execute("""
                UPDATE conversations 
                SET updated_at = NOW()
                WHERE id = $1
            """, uuid.UUID(msg_data.conversation_id))
            
            return str(msg_id)
    
    async def get_messages(self, conv_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get messages for a conversation"""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
                LIMIT $2 OFFSET $3
            """, uuid.UUID(conv_id), limit, offset)
            return [dict(row) for row in rows]
    
    async def get_recent_messages(self, conv_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages for a conversation"""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, uuid.UUID(conv_id), limit)
            return [dict(row) for row in reversed(rows)]  # Return in chronological order
    
    # Knowledge base operations
    async def create_knowledge(self, knowledge_data: KnowledgeCreate) -> str:
        """Create a new knowledge base entry"""
        async with self.get_connection() as conn:
            knowledge_id = await conn.fetchval("""
                INSERT INTO knowledge_base (agent_id, category, title, content, tags, metadata, source)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, knowledge_data.agent_id, knowledge_data.category.value, 
                knowledge_data.title, knowledge_data.content, knowledge_data.tags,
                knowledge_data.metadata, knowledge_data.source)
            return str(knowledge_id)
    
    async def get_knowledge(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        """Get knowledge base entry by ID"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM knowledge_base WHERE id = $1
            """, uuid.UUID(knowledge_id))
            return dict(row) if row else None
    
    async def update_knowledge(self, knowledge_id: str, update_data: KnowledgeUpdate) -> bool:
        """Update knowledge base entry"""
        async with self.get_connection() as conn:
            updates = []
            params = []
            param_count = 1
            
            if update_data.title is not None:
                updates.append(f"title = ${param_count}")
                params.append(update_data.title)
                param_count += 1
            
            if update_data.content is not None:
                updates.append(f"content = ${param_count}")
                params.append(update_data.content)
                param_count += 1
            
            if update_data.category is not None:
                updates.append(f"category = ${param_count}")
                params.append(update_data.category.value)
                param_count += 1
            
            if update_data.tags is not None:
                updates.append(f"tags = ${param_count}")
                params.append(update_data.tags)
                param_count += 1
            
            if update_data.metadata is not None:
                updates.append(f"metadata = ${param_count}")
                params.append(update_data.metadata)
                param_count += 1
            
            if not updates:
                return True
            
            updates.append(f"updated_at = ${param_count}")
            params.append(datetime.utcnow())
            params.append(uuid.UUID(knowledge_id))
            
            result = await conn.execute(f"""
                UPDATE knowledge_base 
                SET {', '.join(updates)}
                WHERE id = ${param_count + 1}
            """, *params)
            
            return result == "UPDATE 1"
    
    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """Delete knowledge base entry"""
        async with self.get_connection() as conn:
            result = await conn.execute("""
                DELETE FROM knowledge_base WHERE id = $1
            """, uuid.UUID(knowledge_id))
            return result == "DELETE 1"
    
    async def search_knowledge(self, agent_id: str, query: str, category: Optional[str] = None,
                              tags: Optional[List[str]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge base entries"""
        async with self.get_connection() as conn:
            # Build search query with text search
            search_conditions = ["agent_id = $1", "to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', $2)"]
            params = [agent_id, query]
            param_count = 3
            
            if category:
                search_conditions.append(f"category = ${param_count}")
                params.append(category)
                param_count += 1
            
            if tags:
                search_conditions.append(f"tags && ${param_count}")
                params.append(tags)
                param_count += 1
            
            rows = await conn.fetch(f"""
                SELECT *, ts_rank(to_tsvector('english', title || ' ' || content), plainto_tsquery('english', $2)) as rank
                FROM knowledge_base
                WHERE {' AND '.join(search_conditions)}
                ORDER BY rank DESC, updated_at DESC
                LIMIT ${param_count}
            """, *params, limit)
            
            return [dict(row) for row in rows]
    
    async def list_knowledge(self, agent_id: str, category: Optional[str] = None,
                           limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List knowledge base entries for an agent"""
        async with self.get_connection() as conn:
            if category:
                rows = await conn.fetch("""
                    SELECT * FROM knowledge_base
                    WHERE agent_id = $1 AND category = $2
                    ORDER BY updated_at DESC
                    LIMIT $3 OFFSET $4
                """, agent_id, category, limit, offset)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM knowledge_base
                    WHERE agent_id = $1
                    ORDER BY updated_at DESC
                    LIMIT $2 OFFSET $3
                """, agent_id, limit, offset)
            return [dict(row) for row in rows]
    
    # Memory summary operations
    async def create_summary(self, summary_data: MemorySummary) -> str:
        """Create a memory summary"""
        async with self.get_connection() as conn:
            summary_id = await conn.fetchval("""
                INSERT INTO memory_summaries (agent_id, conversation_id, summary_type, content, 
                                            message_range_start, message_range_end, relevance_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, summary_data.agent_id, uuid.UUID(summary_data.conversation_id),
                summary_data.summary_type, summary_data.content,
                summary_data.message_range_start, summary_data.message_range_end,
                summary_data.relevance_score)
            return str(summary_id)
    
    async def get_summaries(self, agent_id: str, conversation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get memory summaries"""
        async with self.get_connection() as conn:
            if conversation_id:
                rows = await conn.fetch("""
                    SELECT * FROM memory_summaries
                    WHERE agent_id = $1 AND conversation_id = $2
                    ORDER BY created_at DESC
                """, agent_id, uuid.UUID(conversation_id))
            else:
                rows = await conn.fetch("""
                    SELECT * FROM memory_summaries
                    WHERE agent_id = $1
                    ORDER BY created_at DESC
                """, agent_id)
            return [dict(row) for row in rows]
    
    # Statistics and cleanup operations
    async def get_memory_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get memory system statistics"""
        async with self.get_connection() as conn:
            if agent_id:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(DISTINCT c.id) as total_conversations,
                        COUNT(DISTINCT CASE WHEN c.is_active THEN c.id END) as active_conversations,
                        COUNT(DISTINCT m.id) as total_messages,
                        COUNT(DISTINCT k.id) as total_knowledge_items,
                        COUNT(DISTINCT s.id) as total_summaries
                    FROM conversations c
                    LEFT JOIN messages m ON c.id = m.conversation_id
                    LEFT JOIN knowledge_base k ON c.agent_id = k.agent_id
                    LEFT JOIN memory_summaries s ON c.agent_id = s.agent_id
                    WHERE c.agent_id = $1
                """, agent_id)
            else:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(DISTINCT c.id) as total_conversations,
                        COUNT(DISTINCT CASE WHEN c.is_active THEN c.id END) as active_conversations,
                        COUNT(DISTINCT m.id) as total_messages,
                        COUNT(DISTINCT k.id) as total_knowledge_items,
                        COUNT(DISTINCT s.id) as total_summaries
                    FROM conversations c
                    LEFT JOIN messages m ON c.id = m.conversation_id
                    LEFT JOIN knowledge_base k ON c.agent_id = k.agent_id
                    LEFT JOIN memory_summaries s ON c.agent_id = s.agent_id
                """)
            return dict(stats)
    
    async def cleanup_old_memories(self, retention_days: int = None) -> Dict[str, int]:
        """Clean up old memories based on retention policy"""
        if retention_days is None:
            retention_days = settings.memory_retention_days
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        async with self.get_connection() as conn:
            # Archive old conversations
            archived_conversations = await conn.execute("""
                UPDATE conversations 
                SET is_active = false, updated_at = NOW()
                WHERE created_at < $1 AND is_active = true
            """, cutoff_date)
            
            # Delete very old inactive conversations
            deleted_conversations = await conn.execute("""
                DELETE FROM conversations 
                WHERE created_at < $1 AND is_active = false
            """, cutoff_date - timedelta(days=30))
            
            return {
                "archived_conversations": int(archived_conversations.split()[1]) if archived_conversations.startswith("UPDATE") else 0,
                "deleted_conversations": int(deleted_conversations.split()[1]) if deleted_conversations.startswith("DELETE") else 0
            }