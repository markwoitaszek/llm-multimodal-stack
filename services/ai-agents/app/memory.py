"""
Memory management for AI agents
"""
import logging
from typing import Dict, List, Any, Optional
import asyncpg
import json
from datetime import datetime, timedelta

from .config import settings

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages persistent memory for AI agents"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize memory manager"""
        try:
            self.pool = await asyncpg.create_pool(
                settings.postgres_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            # Create agent-specific tables
            await self.create_agent_tables()
            
            logger.info("Memory Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Memory Manager: {e}")
            raise
    
    async def create_agent_tables(self):
        """Create database tables for agent memory"""
        async with self.pool.acquire() as conn:
            # Agent metadata table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_metadata (
                    agent_id UUID PRIMARY KEY,
                    agent_name VARCHAR(255) NOT NULL,
                    goal TEXT NOT NULL,
                    tools JSONB DEFAULT '[]',
                    user_id VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'active'
                )
            """)
            
            # Agent execution history
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_executions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_id UUID REFERENCES agent_metadata(agent_id) ON DELETE CASCADE,
                    task TEXT NOT NULL,
                    result JSONB,
                    user_id VARCHAR(255) NOT NULL,
                    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    execution_time_ms INTEGER,
                    success BOOLEAN DEFAULT true
                )
            """)
            
            # Agent memory/conversation history
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_memory (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_id UUID REFERENCES agent_metadata(agent_id) ON DELETE CASCADE,
                    message_type VARCHAR(50) NOT NULL, -- 'human', 'ai', 'system', 'tool'
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_metadata_user_id ON agent_metadata(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_id ON agent_executions(agent_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_memory_agent_id ON agent_memory(agent_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_memory_created_at ON agent_memory(created_at)")
    
    async def save_agent_metadata(self, 
                                 agent_id: str,
                                 agent_name: str,
                                 goal: str,
                                 tools: List[str],
                                 user_id: str,
                                 created_at: datetime) -> bool:
        """Save agent metadata"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_metadata (agent_id, agent_name, goal, tools, user_id, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (agent_id) DO UPDATE SET
                        agent_name = EXCLUDED.agent_name,
                        goal = EXCLUDED.goal,
                        tools = EXCLUDED.tools,
                        updated_at = CURRENT_TIMESTAMP
                """, agent_id, agent_name, goal, json.dumps(tools), user_id, created_at)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save agent metadata: {e}")
            return False
    
    async def get_agent_metadata(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent metadata"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT agent_id, agent_name, goal, tools, user_id, created_at, updated_at, status
                    FROM agent_metadata
                    WHERE agent_id = $1
                """, agent_id)
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get agent metadata: {e}")
            return None
    
    async def save_agent_execution(self,
                                  agent_id: str,
                                  task: str,
                                  result: Dict[str, Any],
                                  user_id: str,
                                  executed_at: datetime,
                                  execution_time_ms: int = None,
                                  success: bool = None) -> bool:
        """Save agent execution history"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_executions (agent_id, task, result, user_id, executed_at, execution_time_ms, success)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, agent_id, task, json.dumps(result), user_id, executed_at, execution_time_ms, success or result.get("success", True))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save agent execution: {e}")
            return False
    
    async def list_user_agents(self, user_id: str) -> List[Dict[str, Any]]:
        """List all agents for a user"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT agent_id, agent_name, goal, tools, created_at, status
                    FROM agent_metadata
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                """, user_id)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to list user agents: {e}")
            return []
    
    async def delete_agent(self, agent_id: str, user_id: str) -> bool:
        """Delete an agent and all its data"""
        try:
            async with self.pool.acquire() as conn:
                # Delete agent metadata (cascades to executions and memory)
                result = await conn.execute("""
                    DELETE FROM agent_metadata
                    WHERE agent_id = $1 AND user_id = $2
                """, agent_id, user_id)
                
                return result != "DELETE 0"
                
        except Exception as e:
            logger.error(f"Failed to delete agent: {e}")
            return False
    
    async def cleanup_old_data(self, retention_days: int = None):
        """Clean up old agent data"""
        try:
            retention_days = retention_days or settings.agent_memory_retention_days
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            async with self.pool.acquire() as conn:
                # Clean up old executions
                await conn.execute("""
                    DELETE FROM agent_executions
                    WHERE executed_at < $1
                """, cutoff_date)
                
                # Clean up old memory entries
                await conn.execute("""
                    DELETE FROM agent_memory
                    WHERE created_at < $1
                """, cutoff_date)
            
            logger.info(f"Cleaned up agent data older than {retention_days} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    async def close(self):
        """Close memory manager"""
        if self.pool:
            await self.pool.close()
            logger.info("Memory Manager closed")
