"""
PostgreSQL database operations for the search engine service
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncpg
from asyncpg import Pool, Connection
from contextlib import asynccontextmanager

from .config import settings
from .models import SearchAnalytics, SearchSession, SearchSuggestion

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL database connections and operations"""
    
    def __init__(self):
        self.pool: Optional[Pool] = None
        self._start_time = datetime.utcnow()
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                settings.postgres_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'application_name': 'search-engine',
                    'timezone': 'UTC'
                }
            )
            logger.info("Database connection pool initialized")
            
            # Create tables if they don't exist
            await self._create_tables()
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def _create_tables(self):
        """Create necessary tables for search analytics and sessions"""
        async with self.pool.acquire() as conn:
            # Search analytics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS search_analytics (
                    id SERIAL PRIMARY KEY,
                    query TEXT NOT NULL,
                    search_type VARCHAR(50) NOT NULL,
                    results_count INTEGER NOT NULL,
                    processing_time_ms FLOAT NOT NULL,
                    user_id VARCHAR(255),
                    session_id VARCHAR(255),
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    filters JSONB,
                    clicked_results JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Search sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS search_sessions (
                    id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    search_count INTEGER DEFAULT 0,
                    queries JSONB DEFAULT '[]'::jsonb
                )
            """)
            
            # Search suggestions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS search_suggestions (
                    id SERIAL PRIMARY KEY,
                    query TEXT NOT NULL,
                    suggestion TEXT NOT NULL,
                    suggestion_type VARCHAR(50) NOT NULL,
                    score FLOAT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(query, suggestion)
                )
            """)
            
            # Query logs table for autocomplete
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS query_logs (
                    id SERIAL PRIMARY KEY,
                    query TEXT NOT NULL,
                    user_id VARCHAR(255),
                    session_id VARCHAR(255),
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    result_count INTEGER,
                    clicked BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Create indexes for better performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_analytics_timestamp 
                ON search_analytics(timestamp)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_analytics_user_id 
                ON search_analytics(user_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_sessions_user_id 
                ON search_sessions(user_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_suggestions_query 
                ON search_suggestions(query)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_logs_timestamp 
                ON query_logs(timestamp)
            """)
            
            logger.info("Database tables created/verified")
    
    @asynccontextmanager
    async def acquire_connection(self):
        """Context manager for acquiring database connections"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            await self.pool.release(conn)
    
    async def log_search_analytics(self, analytics: SearchAnalytics):
        """Log search analytics data"""
        try:
            async with self.acquire_connection() as conn:
                await conn.execute("""
                    INSERT INTO search_analytics 
                    (query, search_type, results_count, processing_time_ms, user_id, 
                     session_id, filters, clicked_results)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, 
                analytics.query,
                analytics.search_type,
                analytics.results_count,
                analytics.processing_time_ms,
                analytics.user_id,
                analytics.session_id,
                analytics.filters,
                analytics.clicked_results
                )
        except Exception as e:
            logger.error(f"Failed to log search analytics: {e}")
    
    async def get_search_analytics(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get search analytics data"""
        try:
            async with self.acquire_connection() as conn:
                query = "SELECT * FROM search_analytics WHERE 1=1"
                params = []
                param_count = 0
                
                if start_date:
                    param_count += 1
                    query += f" AND timestamp >= ${param_count}"
                    params.append(start_date)
                
                if end_date:
                    param_count += 1
                    query += f" AND timestamp <= ${param_count}"
                    params.append(end_date)
                
                if user_id:
                    param_count += 1
                    query += f" AND user_id = ${param_count}"
                    params.append(user_id)
                
                query += f" ORDER BY timestamp DESC LIMIT ${param_count + 1}"
                params.append(limit)
                
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            return []
    
    async def get_popular_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most popular search queries"""
        try:
            async with self.acquire_connection() as conn:
                rows = await conn.fetch("""
                    SELECT query, COUNT(*) as search_count, 
                           AVG(processing_time_ms) as avg_processing_time,
                           AVG(results_count) as avg_results_count
                    FROM search_analytics
                    WHERE timestamp >= NOW() - INTERVAL '7 days'
                    GROUP BY query
                    ORDER BY search_count DESC
                    LIMIT $1
                """, limit)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get popular queries: {e}")
            return []
    
    async def create_search_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """Create a new search session"""
        try:
            async with self.acquire_connection() as conn:
                await conn.execute("""
                    INSERT INTO search_sessions (id, user_id, created_at, last_activity)
                    VALUES ($1, $2, NOW(), NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        last_activity = NOW(),
                        search_count = search_sessions.search_count + 1
                """, session_id, user_id)
                return True
        except Exception as e:
            logger.error(f"Failed to create search session: {e}")
            return False
    
    async def update_search_session(self, session_id: str, query: str):
        """Update search session with new query"""
        try:
            async with self.acquire_connection() as conn:
                await conn.execute("""
                    UPDATE search_sessions 
                    SET last_activity = NOW(),
                        search_count = search_count + 1,
                        queries = queries || $2::jsonb
                    WHERE id = $1
                """, session_id, f'["{query}"]')
        except Exception as e:
            logger.error(f"Failed to update search session: {e}")
    
    async def get_search_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get search session data"""
        try:
            async with self.acquire_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM search_sessions WHERE id = $1
                """, session_id)
                
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get search session: {e}")
            return None
    
    async def cleanup_old_sessions(self, days: int = 7):
        """Clean up old search sessions"""
        try:
            async with self.acquire_connection() as conn:
                result = await conn.execute("""
                    DELETE FROM search_sessions 
                    WHERE last_activity < NOW() - INTERVAL '%s days'
                """, days)
                
                logger.info(f"Cleaned up old search sessions: {result}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
    
    async def add_search_suggestion(
        self, 
        query: str, 
        suggestion: str, 
        suggestion_type: str, 
        score: float
    ):
        """Add or update search suggestion"""
        try:
            async with self.acquire_connection() as conn:
                await conn.execute("""
                    INSERT INTO search_suggestions (query, suggestion, suggestion_type, score)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (query, suggestion) DO UPDATE SET
                        usage_count = search_suggestions.usage_count + 1,
                        score = GREATEST(search_suggestions.score, $4),
                        updated_at = NOW()
                """, query, suggestion, suggestion_type, score)
                
        except Exception as e:
            logger.error(f"Failed to add search suggestion: {e}")
    
    async def get_search_suggestions(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[SearchSuggestion]:
        """Get search suggestions for a query"""
        try:
            async with self.acquire_connection() as conn:
                rows = await conn.fetch("""
                    SELECT suggestion, suggestion_type, score, usage_count
                    FROM search_suggestions
                    WHERE query ILIKE $1
                    ORDER BY score DESC, usage_count DESC
                    LIMIT $2
                """, f"%{query}%", limit)
                
                return [
                    SearchSuggestion(
                        text=row['suggestion'],
                        type=row['suggestion_type'],
                        score=row['score'],
                        metadata={'usage_count': row['usage_count']}
                    )
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []
    
    async def log_query(self, query: str, user_id: Optional[str] = None, 
                       session_id: Optional[str] = None, result_count: int = 0):
        """Log a query for autocomplete and analytics"""
        try:
            async with self.acquire_connection() as conn:
                await conn.execute("""
                    INSERT INTO query_logs (query, user_id, session_id, result_count)
                    VALUES ($1, $2, $3, $4)
                """, query, user_id, session_id, result_count)
                
        except Exception as e:
            logger.error(f"Failed to log query: {e}")
    
    async def get_autocomplete_suggestions(
        self, 
        partial_query: str, 
        limit: int = 10
    ) -> List[str]:
        """Get autocomplete suggestions based on query logs"""
        try:
            async with self.acquire_connection() as conn:
                rows = await conn.fetch("""
                    SELECT DISTINCT query, COUNT(*) as frequency
                    FROM query_logs
                    WHERE query ILIKE $1
                    AND timestamp >= NOW() - INTERVAL '30 days'
                    GROUP BY query
                    ORDER BY frequency DESC, query
                    LIMIT $2
                """, f"{partial_query}%", limit)
                
                return [row['query'] for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get autocomplete suggestions: {e}")
            return []
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            async with self.acquire_connection() as conn:
                stats = {}
                
                # Get table counts
                tables = ['search_analytics', 'search_sessions', 'search_suggestions', 'query_logs']
                for table in tables:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = count
                
                # Get recent activity
                recent_searches = await conn.fetchval("""
                    SELECT COUNT(*) FROM search_analytics 
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                """)
                stats['recent_searches_24h'] = recent_searches
                
                # Get unique users
                unique_users = await conn.fetchval("""
                    SELECT COUNT(DISTINCT user_id) FROM search_analytics 
                    WHERE timestamp >= NOW() - INTERVAL '7 days'
                    AND user_id IS NOT NULL
                """)
                stats['unique_users_7d'] = unique_users
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.acquire_connection() as conn:
                await conn.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_uptime(self) -> float:
        """Get service uptime in seconds"""
        return (datetime.utcnow() - self._start_time).total_seconds()

# Global database manager instance
db_manager = DatabaseManager()