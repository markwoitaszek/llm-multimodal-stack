"""
Unit tests for AgentManager in ai-agents service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from app.agent_manager import AgentManager


class TestAgentManager:
    """Test cases for AgentManager"""

    @pytest.fixture
    def agent_manager(self, mock_database_manager):
        """Create AgentManager instance for testing"""
        return AgentManager(mock_database_manager)

    @pytest.mark.asyncio
    async def test_agent_manager_initialization(self, agent_manager):
        """Test AgentManager initialization"""
        assert agent_manager is not None
        assert hasattr(agent_manager, 'db_manager')
        assert hasattr(agent_manager, 'agents')
        assert hasattr(agent_manager, 'templates')

    @pytest.mark.asyncio
    async def test_create_agent_success(self, agent_manager, test_agent_creation_request):
        """Test successful agent creation"""
        # Mock database operations
        agent_manager.db_manager.insert_record.return_value = "test_agent_123"

        # Test agent creation
        result = await agent_manager.create_agent(test_agent_creation_request)

        # Verify result
        assert result["success"] is True
        assert result["agent_id"] == "test_agent_123"
        assert result["agent"]["name"] == "Test Agent"
        assert result["agent"]["goal"] == "Test agent for unit testing"
        assert result["agent"]["tools"] == ["search_content", "generate_text"]

    @pytest.mark.asyncio
    async def test_create_agent_from_template_success(self, agent_manager, mock_agent_template):
        """Test successful agent creation from template"""
        # Mock template retrieval
        agent_manager.templates = {"research_assistant": mock_agent_template}
        agent_manager.db_manager.insert_record.return_value = "test_agent_123"

        # Test agent creation from template
        result = await agent_manager.create_agent_from_template(
            "research_assistant",
            "My Research Agent"
        )

        # Verify result
        assert result["success"] is True
        assert result["agent_id"] == "test_agent_123"
        assert result["agent"]["name"] == "My Research Agent"
        assert result["agent"]["goal"] == mock_agent_template["goal"]

    @pytest.mark.asyncio
    async def test_create_agent_from_template_not_found(self, agent_manager):
        """Test agent creation from non-existent template"""
        # Test with non-existent template
        result = await agent_manager.create_agent_from_template(
            "nonexistent_template",
            "Test Agent"
        )

        # Verify result
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_agent_success(self, agent_manager, mock_agent):
        """Test successful agent retrieval"""
        # Mock database query
        agent_manager.db_manager.execute_query.return_value = [mock_agent]

        # Test agent retrieval
        result = await agent_manager.get_agent("test_agent_123")

        # Verify result
        assert result["success"] is True
        assert result["agent"]["id"] == "test_agent_123"
        assert result["agent"]["name"] == "Test Agent"

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, agent_manager):
        """Test agent retrieval for non-existent agent"""
        # Mock empty database query
        agent_manager.db_manager.execute_query.return_value = []

        # Test agent retrieval
        result = await agent_manager.get_agent("nonexistent_agent")

        # Verify result
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_list_agents_success(self, agent_manager, mock_agent):
        """Test successful agent listing"""
        # Mock database query
        agent_manager.db_manager.execute_query.return_value = [mock_agent]

        # Test agent listing
        result = await agent_manager.list_agents(limit=10, offset=0)

        # Verify result
        assert result["success"] is True
        assert len(result["agents"]) == 1
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_update_agent_success(self, agent_manager):
        """Test successful agent update"""
        # Mock database operations
        agent_manager.db_manager.update_record.return_value = True

        # Test agent update
        update_data = {
            "name": "Updated Agent Name",
            "goal": "Updated goal"
        }
        result = await agent_manager.update_agent("test_agent_123", update_data)

        # Verify result
        assert result["success"] is True
        agent_manager.db_manager.update_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_agent_success(self, agent_manager):
        """Test successful agent deletion"""
        # Mock database operations
        agent_manager.db_manager.delete_record.return_value = True

        # Test agent deletion
        result = await agent_manager.delete_agent("test_agent_123")

        # Verify result
        assert result["success"] is True
        agent_manager.db_manager.delete_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_agent_success(self, agent_manager, test_agent_execution_request):
        """Test successful agent execution"""
        # Mock agent retrieval
        mock_agent = {
            "id": "test_agent_123",
            "name": "Test Agent",
            "goal": "Test agent",
            "tools": ["search_content", "generate_text"],
            "system_prompt": "You are a test agent."
        }
        agent_manager.db_manager.execute_query.return_value = [mock_agent]

        # Mock tool execution
        with patch.object(agent_manager, '_execute_tool') as mock_execute_tool:
            mock_execute_tool.return_value = {
                "success": True,
                "result": "Tool execution result"
            }

            # Test agent execution
            result = await agent_manager.execute_agent(
                "test_agent_123",
                test_agent_execution_request
            )

            # Verify result
            assert result["success"] is True
            assert "result" in result
            assert "execution_time_ms" in result

    @pytest.mark.asyncio
    async def test_execute_agent_not_found(self, agent_manager, test_agent_execution_request):
        """Test agent execution for non-existent agent"""
        # Mock empty database query
        agent_manager.db_manager.execute_query.return_value = []

        # Test agent execution
        result = await agent_manager.execute_agent(
            "nonexistent_agent",
            test_agent_execution_request
        )

        # Verify result
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_agent_stats_success(self, agent_manager):
        """Test successful agent statistics retrieval"""
        # Mock database query
        agent_manager.db_manager.execute_query.return_value = [
            {
                "total_executions": 100,
                "successful_executions": 95,
                "failed_executions": 5,
                "avg_execution_time_ms": 150
            }
        ]

        # Test getting agent stats
        result = await agent_manager.get_agent_stats("test_agent_123")

        # Verify result
        assert result["success"] is True
        assert result["stats"]["total_executions"] == 100
        assert result["stats"]["successful_executions"] == 95
        assert result["stats"]["failed_executions"] == 5
        assert result["stats"]["avg_execution_time_ms"] == 150

    @pytest.mark.asyncio
    async def test_get_agent_history_success(self, agent_manager, mock_agent_memory):
        """Test successful agent history retrieval"""
        # Mock database query
        agent_manager.db_manager.execute_query.return_value = [mock_agent_memory]

        # Test getting agent history
        result = await agent_manager.get_agent_history("test_agent_123", limit=10)

        # Verify result
        assert result["success"] is True
        assert len(result["history"]) == 1
        assert result["history"][0]["agent_id"] == "test_agent_123"

    @pytest.mark.asyncio
    async def test_get_available_templates_success(self, agent_manager, mock_agent_template):
        """Test successful template listing"""
        # Setup templates
        agent_manager.templates = {"research_assistant": mock_agent_template}

        # Test getting templates
        result = await agent_manager.get_available_templates()

        # Verify result
        assert result["success"] is True
        assert len(result["templates"]) == 1
        assert "research_assistant" in result["templates"]

    @pytest.mark.asyncio
    async def test_validate_agent_config_success(self, agent_manager):
        """Test successful agent configuration validation"""
        # Test valid configuration
        config = {
            "name": "Test Agent",
            "goal": "Test goal",
            "tools": ["search_content", "generate_text"],
            "memory_window": 10
        }

        result = await agent_manager.validate_agent_config(config)

        # Verify result
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_agent_config_invalid(self, agent_manager):
        """Test agent configuration validation with invalid config"""
        # Test invalid configuration
        config = {
            "name": "",  # Invalid: empty name
            "goal": "Test goal",
            "tools": [],  # Invalid: no tools
            "memory_window": -1  # Invalid: negative memory window
        }

        result = await agent_manager.validate_agent_config(config)

        # Verify result
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_health_check(self, agent_manager):
        """Test agent manager health check"""
        # Mock database health check
        agent_manager.db_manager.health_check.return_value = {"status": "healthy"}

        # Test health check
        result = await agent_manager.health_check()

        # Verify result
        assert result["status"] == "healthy"
        assert "database" in result
        assert "templates_loaded" in result

    @pytest.mark.asyncio
    async def test_health_check_failure(self, agent_manager):
        """Test agent manager health check failure"""
        # Mock database health check failure
        agent_manager.db_manager.health_check.return_value = {"status": "unhealthy"}

        # Test health check
        result = await agent_manager.health_check()

        # Verify result
        assert result["status"] == "unhealthy"
        assert result["database"] == "unhealthy"
