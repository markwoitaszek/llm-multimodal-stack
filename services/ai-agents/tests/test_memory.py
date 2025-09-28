"""
Unit tests for MemoryManager in ai-agents service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncpg
import json
from datetime import datetime, timedelta

from app.memory import MemoryManager


class TestMemoryManager:
    """Test cases for MemoryManager"""

    @pytest.fixture
    def memory_manager(self):
        """Create memory manager instance"""
        return MemoryManager()

    @pytest.fixture
    def mock_pool(self):
        """Create mock connection pool"""
        mock_pool = AsyncMock(spec=asyncpg.Pool)
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        return mock_pool, mock_conn

    @pytest.mark.asyncio
    @patch('app.memory.asyncpg.create_pool')
    async def test_initialize_success(self, mock_create_pool, memory_manager, mock_pool):
        """Test successful memory manager initialization"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        mock_create_pool.return_value = mock_pool_instance

        # Test initialization
        await memory_manager.initialize()

        # Verify pool was created
        mock_create_pool.assert_called_once()
        assert memory_manager.pool == mock_pool_instance

        # Verify tables were created
        assert mock_conn.execute.call_count >= 3  # At least 3 table creation calls

    @pytest.mark.asyncio
    @patch('app.memory.asyncpg.create_pool')
    async def test_initialize_failure(self, mock_create_pool, memory_manager):
        """Test memory manager initialization failure"""
        # Setup mock to raise exception
        mock_create_pool.side_effect = Exception("Database connection failed")

        # Test initialization should raise exception
        with pytest.raises(Exception, match="Database connection failed"):
            await memory_manager.initialize()

    @pytest.mark.asyncio
    async def test_create_agent_tables(self, memory_manager, mock_pool):
        """Test agent tables creation"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        memory_manager.pool = mock_pool_instance

        # Test table creation
        await memory_manager.create_agent_tables()

        # Verify table creation calls
        assert mock_conn.execute.call_count >= 3

        # Verify specific table creation calls
        execute_calls = [call[0][0] for call in mock_conn.execute.call_args_list]
        
        # Check for agent_metadata table
        metadata_table_call = next((call for call in execute_calls if "agent_metadata" in call), None)
        assert metadata_table_call is not None
        assert "CREATE TABLE IF NOT EXISTS agent_metadata" in metadata_table_call

        # Check for agent_executions table
        executions_table_call = next((call for call in execute_calls if "agent_executions" in call), None)
        assert executions_table_call is not None
        assert "CREATE TABLE IF NOT EXISTS agent_executions" in executions_table_call

        # Check for agent_memory table
        memory_table_call = next((call for call in execute_calls if "agent_memory" in call), None)
        assert memory_table_call is not None
        assert "CREATE TABLE IF NOT EXISTS agent_memory" in memory_table_call

    @pytest.mark.asyncio
    async def test_save_agent_metadata_success(self, memory_manager, mock_pool):
        """Test successful agent metadata saving"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        memory_manager.pool = mock_pool_instance

        # Test metadata saving
        result = await memory_manager.save_agent_metadata(
            agent_id="test-agent-id",
            agent_name="Test Agent",
            goal="Test goal",
            tools=["tool1", "tool2"],
            user_id="test_user",
            created_at=datetime.utcnow()
        )

        # Verify result
        assert result is True

        # Verify database call
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert "INSERT INTO agent_metadata" in call_args[0][0]
        assert call_args[0][1] == "test-agent-id"
        assert call_args[0][2] == "Test Agent"
        assert call_args[0][3] == "Test goal"
        assert call_args[0][4] == json.dumps(["tool1", "tool2"])
        assert call_args[0][5] == "test_user"

    @pytest.mark.asyncio
    async def test_save_agent_metadata_failure(self, memory_manager, mock_pool):
        """Test agent metadata saving failure"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        mock_conn.execute.side_effect = Exception("Database error")
        memory_manager.pool = mock_pool_instance

        # Test metadata saving
        result = await memory_manager.save_agent_metadata(
            agent_id="test-agent-id",
            agent_name="Test Agent",
            goal="Test goal",
            tools=["tool1"],
            user_id="test_user",
            created_at=datetime.utcnow()
        )

        # Verify result
        assert result is False

    @pytest.mark.asyncio
    async def test_get_agent_metadata_success(self, memory_manager, mock_pool):
        """Test successful agent metadata retrieval"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        memory_manager.pool = mock_pool_instance

        # Mock database row
        mock_row = {
            "agent_id": "test-agent-id",
            "agent_name": "Test Agent",
            "goal": "Test goal",
            "tools": json.dumps(["tool1", "tool2"]),
            "user_id": "test_user",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active"
        }
        mock_conn.fetchrow.return_value = mock_row

        # Test metadata retrieval
        result = await memory_manager.get_agent_metadata("test-agent-id")

        # Verify result
        assert result is not None
        assert result["agent_id"] == "test-agent-id"
        assert result["agent_name"] == "Test Agent"
        assert result["goal"] == "Test goal"
        assert result["tools"] == json.dumps(["tool1", "tool2"])
        assert result["user_id"] == "test_user"
        assert result["status"] == "active"

        # Verify database call
        mock_conn.fetchrow.assert_called_once()
        call_args = mock_conn.fetchrow.call_args
        assert "SELECT" in call_args[0][0]
        assert "agent_metadata" in call_args[0][0]
        assert call_args[0][1] == "test-agent-id"

    @pytest.mark.asyncio
    async def test_get_agent_metadata_not_found(self, memory_manager, mock_pool):
        """Test agent metadata retrieval for non-existent agent"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        mock_conn.fetchrow.return_value = None
        memory_manager.pool = mock_pool_instance

        # Test metadata retrieval
        result = await memory_manager.get_agent_metadata("non-existent-agent")

        # Verify result
        assert result is None

    @pytest.mark.asyncio
    async def test_get_agent_metadata_failure(self, memory_manager, mock_pool):
        """Test agent metadata retrieval failure"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        mock_conn.fetchrow.side_effect = Exception("Database error")
        memory_manager.pool = mock_pool_instance

        # Test metadata retrieval
        result = await memory_manager.get_agent_metadata("test-agent-id")

        # Verify result
        assert result is None

    @pytest.mark.asyncio
    async def test_save_agent_execution_success(self, memory_manager, mock_pool):
        """Test successful agent execution saving"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        memory_manager.pool = mock_pool_instance

        # Test execution data
        execution_result = {
            "agent_id": "test-agent-id",
            "task": "Test task",
            "result": "Task completed successfully",
            "success": True,
            "execution_time_ms": 1500
        }

        # Test execution saving
        result = await memory_manager.save_agent_execution(
            agent_id="test-agent-id",
            task="Test task",
            result=execution_result,
            user_id="test_user",
            executed_at=datetime.utcnow(),
            execution_time_ms=1500,
            success=True
        )

        # Verify result
        assert result is True

        # Verify database call
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert "INSERT INTO agent_executions" in call_args[0][0]
        assert call_args[0][1] == "test-agent-id"
        assert call_args[0][2] == "Test task"
        assert call_args[0][3] == json.dumps(execution_result)
        assert call_args[0][4] == "test_user"
        assert call_args[0][6] == 1500
        assert call_args[0][7] is True

    @pytest.mark.asyncio
    async def test_save_agent_execution_with_defaults(self, memory_manager, mock_pool):
        """Test agent execution saving with default parameters"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        memory_manager.pool = mock_pool_instance

        # Test execution data
        execution_result = {
            "agent_id": "test-agent-id",
            "task": "Test task",
            "result": "Task completed successfully",
            "success": True
        }

        # Test execution saving with minimal parameters
        result = await memory_manager.save_agent_execution(
            agent_id="test-agent-id",
            task="Test task",
            result=execution_result,
            user_id="test_user",
            executed_at=datetime.utcnow()
        )

        # Verify result
        assert result is True

        # Verify database call
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert call_args[0][6] is None  # execution_time_ms
        assert call_args[0][7] is True  # success (from result)

    @pytest.mark.asyncio
    async def test_save_agent_execution_failure(self, memory_manager, mock_pool):
        """Test agent execution saving failure"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        mock_conn.execute.side_effect = Exception("Database error")
        memory_manager.pool = mock_pool_instance

        # Test execution saving
        result = await memory_manager.save_agent_execution(
            agent_id="test-agent-id",
            task="Test task",
            result={"success": True},
            user_id="test_user",
            executed_at=datetime.utcnow()
        )

        # Verify result
        assert result is False

    @pytest.mark.asyncio
    async def test_list_user_agents_success(self, memory_manager, mock_pool):
        """Test successful user agents listing"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        memory_manager.pool = mock_pool_instance

        # Mock database rows
        mock_rows = [
            {
                "agent_id": "agent1",
                "agent_name": "Agent 1",
                "goal": "Goal 1",
                "tools": json.dumps(["tool1"]),
                "created_at": datetime.utcnow(),
                "status": "active"
            },
            {
                "agent_id": "agent2",
                "agent_name": "Agent 2",
                "goal": "Goal 2",
                "tools": json.dumps(["tool2"]),
                "created_at": datetime.utcnow(),
                "status": "active"
            }
        ]
        mock_conn.fetch.return_value = mock_rows

        # Test user agents listing
        result = await memory_manager.list_user_agents("test_user")

        # Verify result
        assert len(result) == 2
        assert result[0]["agent_id"] == "agent1"
        assert result[0]["agent_name"] == "Agent 1"
        assert result[1]["agent_id"] == "agent2"
        assert result[1]["agent_name"] == "Agent 2"

        # Verify database call
        mock_conn.fetch.assert_called_once()
        call_args = mock_conn.fetch.call_args
        assert "SELECT" in call_args[0][0]
        assert "agent_metadata" in call_args[0][0]
        assert call_args[0][1] == "test_user"

    @pytest.mark.asyncio
    async def test_list_user_agents_empty(self, memory_manager, mock_pool):
        """Test user agents listing with no agents"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        mock_conn.fetch.return_value = []
        memory_manager.pool = mock_pool_instance

        # Test user agents listing
        result = await memory_manager.list_user_agents("test_user")

        # Verify result
        assert result == []

    @pytest.mark.asyncio
    async def test_list_user_agents_failure(self, memory_manager, mock_pool):
        """Test user agents listing failure"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        mock_conn.fetch.side_effect = Exception("Database error")
        memory_manager.pool = mock_pool_instance

        # Test user agents listing
        result = await memory_manager.list_user_agents("test_user")

        # Verify result
        assert result == []

    @pytest.mark.asyncio
    async def test_delete_agent_success(self, memory_manager, mock_pool):
        """Test successful agent deletion"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        mock_conn.execute.return_value = "DELETE 1"
        memory_manager.pool = mock_pool_instance

        # Test agent deletion
        result = await memory_manager.delete_agent("test-agent-id", "test_user")

        # Verify result
        assert result is True

        # Verify database call
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert "DELETE FROM agent_metadata" in call_args[0][0]
        assert call_args[0][1] == "test-agent-id"
        assert call_args[0][2] == "test_user"

    @pytest.mark.asyncio
    async def test_delete_agent_not_found(self, memory_manager, mock_pool):
        """Test agent deletion for non-existent agent"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        mock_conn.execute.return_value = "DELETE 0"
        memory_manager.pool = mock_pool_instance

        # Test agent deletion
        result = await memory_manager.delete_agent("non-existent-agent", "test_user")

        # Verify result
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_agent_failure(self, memory_manager, mock_pool):
        """Test agent deletion failure"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        mock_conn.execute.side_effect = Exception("Database error")
        memory_manager.pool = mock_pool_instance

        # Test agent deletion
        result = await memory_manager.delete_agent("test-agent-id", "test_user")

        # Verify result
        assert result is False

    @pytest.mark.asyncio
    @patch('app.memory.settings')
    async def test_cleanup_old_data_success(self, mock_settings, memory_manager, mock_pool):
        """Test successful old data cleanup"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        memory_manager.pool = mock_pool_instance
        mock_settings.agent_memory_retention_days = 30

        # Test cleanup
        await memory_manager.cleanup_old_data()

        # Verify database calls
        assert mock_conn.execute.call_count == 2  # Two DELETE statements

        # Verify cleanup calls
        execute_calls = [call[0][0] for call in mock_conn.execute.call_args_list]
        
        # Check for executions cleanup
        executions_cleanup_call = next((call for call in execute_calls if "agent_executions" in call), None)
        assert executions_cleanup_call is not None
        assert "DELETE FROM agent_executions" in executions_cleanup_call

        # Check for memory cleanup
        memory_cleanup_call = next((call for call in execute_calls if "agent_memory" in call), None)
        assert memory_cleanup_call is not None
        assert "DELETE FROM agent_memory" in memory_cleanup_call

    @pytest.mark.asyncio
    @patch('app.memory.settings')
    async def test_cleanup_old_data_with_custom_retention(self, mock_settings, memory_manager, mock_pool):
        """Test old data cleanup with custom retention period"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        memory_manager.pool = mock_pool_instance

        # Test cleanup with custom retention
        await memory_manager.cleanup_old_data(retention_days=7)

        # Verify database calls
        assert mock_conn.execute.call_count == 2

        # Verify custom retention was used
        execute_calls = mock_conn.execute.call_args_list
        for call in execute_calls:
            # Check that the cutoff date is approximately 7 days ago
            cutoff_date = call[0][1]
            expected_cutoff = datetime.utcnow() - timedelta(days=7)
            time_diff = abs((cutoff_date - expected_cutoff).total_seconds())
            assert time_diff < 60  # Within 1 minute tolerance

    @pytest.mark.asyncio
    async def test_cleanup_old_data_failure(self, memory_manager, mock_pool):
        """Test old data cleanup failure"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        mock_conn.execute.side_effect = Exception("Database error")
        memory_manager.pool = mock_pool_instance

        # Test cleanup should not raise exception
        await memory_manager.cleanup_old_data()

        # Verify database calls were attempted
        assert mock_conn.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_close(self, memory_manager, mock_pool):
        """Test memory manager close"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        memory_manager.pool = mock_pool_instance

        # Test close
        await memory_manager.close()

        # Verify pool was closed
        mock_pool_instance.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_pool(self, memory_manager):
        """Test memory manager close without pool"""
        # Test close without pool
        await memory_manager.close()

        # Should not raise exception
        assert True

    @pytest.mark.asyncio
    async def test_save_agent_execution_with_failed_result(self, memory_manager, mock_pool):
        """Test saving agent execution with failed result"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        memory_manager.pool = mock_pool_instance

        # Test execution data with failure
        execution_result = {
            "agent_id": "test-agent-id",
            "task": "Test task",
            "error": "Task failed",
            "success": False
        }

        # Test execution saving
        result = await memory_manager.save_agent_execution(
            agent_id="test-agent-id",
            task="Test task",
            result=execution_result,
            user_id="test_user",
            executed_at=datetime.utcnow(),
            success=False
        )

        # Verify result
        assert result is True

        # Verify database call
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert call_args[0][7] is False  # success parameter

    @pytest.mark.asyncio
    async def test_save_agent_metadata_with_tools_list(self, memory_manager, mock_pool):
        """Test saving agent metadata with tools list"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        memory_manager.pool = mock_pool_instance

        # Test metadata saving with tools
        tools = ["analyze_image", "search_content", "generate_text"]

        result = await memory_manager.save_agent_metadata(
            agent_id="test-agent-id",
            agent_name="Test Agent",
            goal="Test goal",
            tools=tools,
            user_id="test_user",
            created_at=datetime.utcnow()
        )

        # Verify result
        assert result is True

        # Verify tools were JSON serialized
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert call_args[0][4] == json.dumps(tools)

    @pytest.mark.asyncio
    async def test_get_agent_metadata_with_json_tools(self, memory_manager, mock_pool):
        """Test getting agent metadata with JSON tools"""
        # Setup mocks
        mock_pool_instance, mock_conn = mock_pool
        memory_manager.pool = mock_pool_instance

        # Mock database row with JSON tools
        tools_json = json.dumps(["analyze_image", "search_content"])
        mock_row = {
            "agent_id": "test-agent-id",
            "agent_name": "Test Agent",
            "goal": "Test goal",
            "tools": tools_json,
            "user_id": "test_user",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active"
        }
        mock_conn.fetchrow.return_value = mock_row

        # Test metadata retrieval
        result = await memory_manager.get_agent_metadata("test-agent-id")

        # Verify result
        assert result is not None
        assert result["tools"] == tools_json