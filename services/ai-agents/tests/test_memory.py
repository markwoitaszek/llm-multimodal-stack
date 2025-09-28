"""
Unit tests for memory operations in ai-agents service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from app.memory import MemoryManager


class TestMemoryManager:
    """Test cases for MemoryManager"""

    @pytest.fixture
    def memory_manager(self, mock_database_manager):
        """Create MemoryManager instance for testing"""
        return MemoryManager(mock_database_manager)

    @pytest.mark.asyncio
    async def test_memory_manager_initialization(self, memory_manager):
        """Test MemoryManager initialization"""
        assert memory_manager is not None
        assert hasattr(memory_manager, 'db_manager')
        assert hasattr(memory_manager, 'memory_cache')

    @pytest.mark.asyncio
    async def test_store_memory_success(self, memory_manager, mock_agent_memory):
        """Test successful memory storage"""
        # Mock database operations
        memory_manager.db_manager.insert_record.return_value = "memory_id_123"

        # Test memory storage
        result = await memory_manager.store_memory(
            agent_id=mock_agent_memory["agent_id"],
            conversation_id=mock_agent_memory["conversation_id"],
            user_input=mock_agent_memory["user_input"],
            agent_response=mock_agent_memory["agent_response"],
            metadata=mock_agent_memory["metadata"]
        )

        # Verify result
        assert result["success"] is True
        assert result["memory_id"] == "memory_id_123"
        memory_manager.db_manager.insert_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_memory_failure(self, memory_manager):
        """Test memory storage failure"""
        # Mock database failure
        memory_manager.db_manager.insert_record.side_effect = Exception("Database error")

        # Test memory storage
        result = await memory_manager.store_memory(
            agent_id="test_agent_123",
            conversation_id="conv_123",
            user_input="Test input",
            agent_response="Test response",
            metadata={}
        )

        # Verify result
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_retrieve_memory_success(self, memory_manager, mock_agent_memory):
        """Test successful memory retrieval"""
        # Mock database query
        memory_manager.db_manager.execute_query.return_value = [mock_agent_memory]

        # Test memory retrieval
        result = await memory_manager.retrieve_memory(
            agent_id="test_agent_123",
            conversation_id="conv_123",
            limit=10
        )

        # Verify result
        assert result["success"] is True
        assert len(result["memories"]) == 1
        assert result["memories"][0]["agent_id"] == "test_agent_123"

    @pytest.mark.asyncio
    async def test_retrieve_memory_empty(self, memory_manager):
        """Test memory retrieval with no results"""
        # Mock empty database query
        memory_manager.db_manager.execute_query.return_value = []

        # Test memory retrieval
        result = await memory_manager.retrieve_memory(
            agent_id="test_agent_123",
            conversation_id="conv_123",
            limit=10
        )

        # Verify result
        assert result["success"] is True
        assert len(result["memories"]) == 0

    @pytest.mark.asyncio
    async def test_retrieve_memory_failure(self, memory_manager):
        """Test memory retrieval failure"""
        # Mock database failure
        memory_manager.db_manager.execute_query.side_effect = Exception("Database error")

        # Test memory retrieval
        result = await memory_manager.retrieve_memory(
            agent_id="test_agent_123",
            conversation_id="conv_123",
            limit=10
        )

        # Verify result
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_conversation_context_success(self, memory_manager, mock_agent_memory):
        """Test successful conversation context retrieval"""
        # Mock database query
        memory_manager.db_manager.execute_query.return_value = [mock_agent_memory]

        # Test conversation context retrieval
        result = await memory_manager.get_conversation_context(
            agent_id="test_agent_123",
            conversation_id="conv_123",
            window_size=5
        )

        # Verify result
        assert result["success"] is True
        assert "context" in result
        assert len(result["context"]) == 1

    @pytest.mark.asyncio
    async def test_get_conversation_context_with_window(self, memory_manager):
        """Test conversation context retrieval with window size"""
        # Mock database query with multiple memories
        memories = [
            {
                "id": f"memory_{i}",
                "agent_id": "test_agent_123",
                "conversation_id": "conv_123",
                "user_input": f"User input {i}",
                "agent_response": f"Agent response {i}",
                "timestamp": datetime.now().isoformat()
            }
            for i in range(10)
        ]
        memory_manager.db_manager.execute_query.return_value = memories

        # Test conversation context retrieval with window size
        result = await memory_manager.get_conversation_context(
            agent_id="test_agent_123",
            conversation_id="conv_123",
            window_size=5
        )

        # Verify result
        assert result["success"] is True
        assert len(result["context"]) == 5  # Should be limited by window size

    @pytest.mark.asyncio
    async def test_delete_memory_success(self, memory_manager):
        """Test successful memory deletion"""
        # Mock database operations
        memory_manager.db_manager.delete_record.return_value = True

        # Test memory deletion
        result = await memory_manager.delete_memory("memory_id_123")

        # Verify result
        assert result["success"] is True
        memory_manager.db_manager.delete_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_memory_failure(self, memory_manager):
        """Test memory deletion failure"""
        # Mock database failure
        memory_manager.db_manager.delete_record.side_effect = Exception("Database error")

        # Test memory deletion
        result = await memory_manager.delete_memory("memory_id_123")

        # Verify result
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_delete_conversation_memories_success(self, memory_manager):
        """Test successful conversation memories deletion"""
        # Mock database operations
        memory_manager.db_manager.delete_record.return_value = True

        # Test conversation memories deletion
        result = await memory_manager.delete_conversation_memories(
            agent_id="test_agent_123",
            conversation_id="conv_123"
        )

        # Verify result
        assert result["success"] is True
        memory_manager.db_manager.delete_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_memory_stats_success(self, memory_manager):
        """Test successful memory statistics retrieval"""
        # Mock database query
        memory_manager.db_manager.execute_query.return_value = [
            {
                "total_memories": 1000,
                "total_conversations": 50,
                "avg_memories_per_conversation": 20
            }
        ]

        # Test getting memory stats
        result = await memory_manager.get_memory_stats("test_agent_123")

        # Verify result
        assert result["success"] is True
        assert result["stats"]["total_memories"] == 1000
        assert result["stats"]["total_conversations"] == 50
        assert result["stats"]["avg_memories_per_conversation"] == 20

    @pytest.mark.asyncio
    async def test_search_memories_success(self, memory_manager, mock_agent_memory):
        """Test successful memory search"""
        # Mock database query
        memory_manager.db_manager.execute_query.return_value = [mock_agent_memory]

        # Test memory search
        result = await memory_manager.search_memories(
            agent_id="test_agent_123",
            query="test query",
            limit=10
        )

        # Verify result
        assert result["success"] is True
        assert len(result["memories"]) == 1

    @pytest.mark.asyncio
    async def test_search_memories_empty(self, memory_manager):
        """Test memory search with no results"""
        # Mock empty database query
        memory_manager.db_manager.execute_query.return_value = []

        # Test memory search
        result = await memory_manager.search_memories(
            agent_id="test_agent_123",
            query="nonexistent query",
            limit=10
        )

        # Verify result
        assert result["success"] is True
        assert len(result["memories"]) == 0

    @pytest.mark.asyncio
    async def test_update_memory_success(self, memory_manager):
        """Test successful memory update"""
        # Mock database operations
        memory_manager.db_manager.update_record.return_value = True

        # Test memory update
        update_data = {
            "user_input": "Updated input",
            "agent_response": "Updated response"
        }
        result = await memory_manager.update_memory("memory_id_123", update_data)

        # Verify result
        assert result["success"] is True
        memory_manager.db_manager.update_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_memory_failure(self, memory_manager):
        """Test memory update failure"""
        # Mock database failure
        memory_manager.db_manager.update_record.side_effect = Exception("Database error")

        # Test memory update
        update_data = {"user_input": "Updated input"}
        result = await memory_manager.update_memory("memory_id_123", update_data)

        # Verify result
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_cleanup_old_memories_success(self, memory_manager):
        """Test successful old memories cleanup"""
        # Mock database operations
        memory_manager.db_manager.execute_query.return_value = [{"id": "old_memory_1"}, {"id": "old_memory_2"}]
        memory_manager.db_manager.delete_record.return_value = True

        # Test old memories cleanup
        result = await memory_manager.cleanup_old_memories(
            agent_id="test_agent_123",
            days_old=30
        )

        # Verify result
        assert result["success"] is True
        assert result["deleted_count"] == 2

    @pytest.mark.asyncio
    async def test_health_check(self, memory_manager):
        """Test memory manager health check"""
        # Mock database health check
        memory_manager.db_manager.health_check.return_value = {"status": "healthy"}

        # Test health check
        result = await memory_manager.health_check()

        # Verify result
        assert result["status"] == "healthy"
        assert "database" in result
        assert "cache_size" in result

    @pytest.mark.asyncio
    async def test_health_check_failure(self, memory_manager):
        """Test memory manager health check failure"""
        # Mock database health check failure
        memory_manager.db_manager.health_check.return_value = {"status": "unhealthy"}

        # Test health check
        result = await memory_manager.health_check()

        # Verify result
        assert result["status"] == "unhealthy"
        assert result["database"] == "unhealthy"
