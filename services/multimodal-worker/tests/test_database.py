"""
Unit tests for database operations in multimodal-worker service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
from datetime import datetime

from app.database import DatabaseManager


class TestDatabaseManager:
    """Test cases for DatabaseManager"""

    @pytest.fixture
    def db_manager(self):
        """Create DatabaseManager instance for testing"""
        return DatabaseManager()

    @pytest.mark.asyncio
    async def test_database_manager_initialization(self, db_manager):
        """Test DatabaseManager initialization"""
        assert db_manager is not None
        assert hasattr(db_manager, 'connection_pool')
        assert hasattr(db_manager, 'connection')

    @pytest.mark.asyncio
    @patch('app.database.asyncpg.create_pool')
    async def test_initialize_success(self, mock_create_pool, db_manager):
        """Test successful database initialization"""
        # Mock connection pool
        mock_pool = AsyncMock()
        mock_create_pool.return_value = mock_pool

        # Test initialization
        await db_manager.initialize()

        # Verify pool was created
        mock_create_pool.assert_called_once()
        assert db_manager.connection_pool == mock_pool

    @pytest.mark.asyncio
    @patch('app.database.asyncpg.create_pool')
    async def test_initialize_failure(self, mock_create_pool, db_manager):
        """Test database initialization failure"""
        # Mock connection failure
        mock_create_pool.side_effect = Exception("Connection failed")

        # Test initialization
        with pytest.raises(Exception, match="Connection failed"):
            await db_manager.initialize()

    @pytest.mark.asyncio
    async def test_close(self, db_manager):
        """Test database connection closing"""
        # Mock connection pool
        mock_pool = AsyncMock()
        db_manager.connection_pool = mock_pool

        # Test closing
        await db_manager.close()

        # Verify pool was closed
        mock_pool.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_success(self, db_manager):
        """Test successful query execution"""
        # Mock connection pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetch.return_value = [{"id": 1, "name": "test"}]
        db_manager.connection_pool = mock_pool

        # Test query execution
        result = await db_manager.execute_query("SELECT * FROM test_table")

        # Verify results
        assert result == [{"id": 1, "name": "test"}]
        mock_connection.fetch.assert_called_once_with("SELECT * FROM test_table")

    @pytest.mark.asyncio
    async def test_execute_query_failure(self, db_manager):
        """Test query execution failure"""
        # Mock connection pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetch.side_effect = Exception("Query failed")
        db_manager.connection_pool = mock_pool

        # Test query execution
        with pytest.raises(Exception, match="Query failed"):
            await db_manager.execute_query("SELECT * FROM test_table")

    @pytest.mark.asyncio
    async def test_insert_record_success(self, db_manager):
        """Test successful record insertion"""
        # Mock connection pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetchval.return_value = "test_id_123"
        db_manager.connection_pool = mock_pool

        # Test record insertion
        result = await db_manager.insert_record(
            "content_metadata",
            {
                "content_type": "image",
                "filename": "test.jpg",
                "size": 1024,
                "created_at": datetime.now()
            }
        )

        # Verify result
        assert result == "test_id_123"
        mock_connection.fetchval.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_record_success(self, db_manager):
        """Test successful record update"""
        # Mock connection pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.execute.return_value = "UPDATE 1"
        db_manager.connection_pool = mock_pool

        # Test record update
        result = await db_manager.update_record(
            "content_metadata",
            {"status": "processed"},
            {"id": "test_id_123"}
        )

        # Verify result
        assert result is True
        mock_connection.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_record_success(self, db_manager):
        """Test successful record deletion"""
        # Mock connection pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.execute.return_value = "DELETE 1"
        db_manager.connection_pool = mock_pool

        # Test record deletion
        result = await db_manager.delete_record(
            "content_metadata",
            {"id": "test_id_123"}
        )

        # Verify result
        assert result is True
        mock_connection.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_content_by_id(self, db_manager):
        """Test getting content by ID"""
        # Mock connection pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetchrow.return_value = {
            "id": "test_id_123",
            "content_type": "image",
            "filename": "test.jpg",
            "status": "processed"
        }
        db_manager.connection_pool = mock_pool

        # Test getting content
        result = await db_manager.get_content_by_id("test_id_123")

        # Verify result
        assert result["id"] == "test_id_123"
        assert result["content_type"] == "image"
        assert result["filename"] == "test.jpg"
        assert result["status"] == "processed"

    @pytest.mark.asyncio
    async def test_get_content_by_type(self, db_manager):
        """Test getting content by type"""
        # Mock connection pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetch.return_value = [
            {"id": "test_id_1", "content_type": "image"},
            {"id": "test_id_2", "content_type": "image"}
        ]
        db_manager.connection_pool = mock_pool

        # Test getting content by type
        result = await db_manager.get_content_by_type("image", limit=10)

        # Verify result
        assert len(result) == 2
        assert all(item["content_type"] == "image" for item in result)

    @pytest.mark.asyncio
    async def test_get_processing_stats(self, db_manager):
        """Test getting processing statistics"""
        # Mock connection pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetchrow.return_value = {
            "total_content": 100,
            "processed_content": 95,
            "failed_content": 5,
            "avg_processing_time_ms": 150
        }
        db_manager.connection_pool = mock_pool

        # Test getting stats
        result = await db_manager.get_processing_stats()

        # Verify result
        assert result["total_content"] == 100
        assert result["processed_content"] == 95
        assert result["failed_content"] == 5
        assert result["avg_processing_time_ms"] == 150

    @pytest.mark.asyncio
    async def test_health_check(self, db_manager):
        """Test database health check"""
        # Mock connection pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetchval.return_value = 1
        db_manager.connection_pool = mock_pool

        # Test health check
        result = await db_manager.health_check()

        # Verify result
        assert result["status"] == "healthy"
        assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_health_check_failure(self, db_manager):
        """Test database health check failure"""
        # Mock connection pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetchval.side_effect = Exception("Connection failed")
        db_manager.connection_pool = mock_pool

        # Test health check
        result = await db_manager.health_check()

        # Verify result
        assert result["status"] == "unhealthy"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_transaction_success(self, db_manager):
        """Test successful transaction"""
        # Mock connection pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.transaction.return_value.__aenter__.return_value = mock_connection
        db_manager.connection_pool = mock_pool

        # Test transaction
        async def transaction_operations(conn):
            await conn.execute("INSERT INTO test VALUES (1)")
            await conn.execute("UPDATE test SET value = 2")
            return "success"

        result = await db_manager.execute_transaction(transaction_operations)

        # Verify result
        assert result == "success"
        mock_connection.transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_transaction_failure(self, db_manager):
        """Test transaction failure with rollback"""
        # Mock connection pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.transaction.return_value.__aenter__.return_value = mock_connection
        db_manager.connection_pool = mock_pool

        # Test transaction with failure
        async def failing_transaction(conn):
            await conn.execute("INSERT INTO test VALUES (1)")
            raise Exception("Transaction failed")

        with pytest.raises(Exception, match="Transaction failed"):
            await db_manager.execute_transaction(failing_transaction)

        # Verify transaction was called (rollback should happen automatically)
        mock_connection.transaction.assert_called_once()
