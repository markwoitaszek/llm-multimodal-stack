"""
Unit tests for API endpoints in ai-agents service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import json
from datetime import datetime

from main import app


class TestAIAgentsAPI:
    """Test cases for AI Agents API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_agent_manager(self):
        """Create mock agent manager"""
        mock_manager = Mock()
        mock_manager.create_agent = AsyncMock(return_value="test-agent-id")
        mock_manager.list_agents = AsyncMock(return_value=[])
        mock_manager.get_agent_info = AsyncMock(return_value=None)
        mock_manager.execute_agent = AsyncMock(return_value={
            "agent_id": "test-agent-id",
            "task": "Test task",
            "result": "Task completed",
            "success": True,
            "intermediate_steps": []
        })
        mock_manager.delete_agent = AsyncMock(return_value=True)
        return mock_manager

    @pytest.fixture
    def mock_tool_registry(self):
        """Create mock tool registry"""
        mock_registry = Mock()
        mock_registry.list_available_tools = AsyncMock(return_value={
            "analyze_image": "Analyze images",
            "search_content": "Search content",
            "generate_text": "Generate text"
        })
        return mock_registry

    @pytest.fixture
    def mock_memory_manager(self):
        """Create mock memory manager"""
        mock_memory = Mock()
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_memory.pool = mock_pool
        return mock_memory

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "service" in data

    @pytest.mark.asyncio
    async def test_create_agent_success(self, client, mock_agent_manager):
        """Test successful agent creation"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager

        # Test agent creation
        response = client.post(
            "/api/v1/agents",
            json={
                "name": "Test Agent",
                "goal": "Test goal",
                "tools": ["analyze_image", "search_content"],
                "memory_window": 10,
                "user_id": "test_user"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "test-agent-id"
        assert data["message"] == "Agent 'Test Agent' created successfully"
        assert data["goal"] == "Test goal"
        assert data["tools"] == ["analyze_image", "search_content"]
        assert data["status"] == "created"

        # Verify agent manager was called
        mock_agent_manager.create_agent.assert_called_once()
        call_args = mock_agent_manager.create_agent.call_args
        assert call_args[1]['agent_name'] == "Test Agent"
        assert call_args[1]['goal'] == "Test goal"
        assert call_args[1]['tools'] == ["analyze_image", "search_content"]
        assert call_args[1]['memory_window'] == 10
        assert call_args[1]['user_id'] == "test_user"

    @pytest.mark.asyncio
    async def test_create_agent_with_defaults(self, client, mock_agent_manager):
        """Test agent creation with default parameters"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager

        # Test agent creation with minimal parameters
        response = client.post(
            "/api/v1/agents",
            json={
                "name": "Test Agent",
                "goal": "Test goal"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "test-agent-id"
        assert data["tools"] == []

        # Verify agent manager was called with defaults
        mock_agent_manager.create_agent.assert_called_once()
        call_args = mock_agent_manager.create_agent.call_args
        assert call_args[1]['tools'] is None
        assert call_args[1]['memory_window'] == 10
        assert call_args[1]['user_id'] == "default"

    @pytest.mark.asyncio
    async def test_create_agent_missing_required_fields(self, client, mock_agent_manager):
        """Test agent creation with missing required fields"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager

        # Test agent creation without name
        response = client.post(
            "/api/v1/agents",
            json={
                "goal": "Test goal"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "Name and goal are required" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_agent_failure(self, client, mock_agent_manager):
        """Test agent creation failure"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager
        mock_agent_manager.create_agent.side_effect = Exception("Agent creation failed")

        # Test agent creation
        response = client.post(
            "/api/v1/agents",
            json={
                "name": "Test Agent",
                "goal": "Test goal"
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert "Agent creation failed" in data["detail"]

    @pytest.mark.asyncio
    async def test_list_agents_success(self, client, mock_agent_manager):
        """Test successful agents listing"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager

        # Mock agents data
        mock_agents = [
            {
                "agent_id": "agent1",
                "name": "Agent 1",
                "goal": "Goal 1",
                "tools": ["tool1"],
                "created_at": datetime.utcnow(),
                "status": "active"
            },
            {
                "agent_id": "agent2",
                "name": "Agent 2",
                "goal": "Goal 2",
                "tools": ["tool2"],
                "created_at": datetime.utcnow(),
                "status": "active"
            }
        ]
        mock_agent_manager.list_agents.return_value = mock_agents

        # Test agents listing
        response = client.get("/api/v1/agents?user_id=test_user")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["agent_id"] == "agent1"
        assert data[0]["name"] == "Agent 1"
        assert data[1]["agent_id"] == "agent2"
        assert data[1]["name"] == "Agent 2"

        # Verify agent manager was called
        mock_agent_manager.list_agents.assert_called_once_with("test_user")

    @pytest.mark.asyncio
    async def test_list_agents_empty(self, client, mock_agent_manager):
        """Test agents listing with no agents"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager
        mock_agent_manager.list_agents.return_value = []

        # Test agents listing
        response = client.get("/api/v1/agents")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_list_agents_failure(self, client, mock_agent_manager):
        """Test agents listing failure"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager
        mock_agent_manager.list_agents.side_effect = Exception("Database error")

        # Test agents listing
        response = client.get("/api/v1/agents")

        assert response.status_code == 500
        data = response.json()
        assert "Database error" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_agent_success(self, client, mock_agent_manager):
        """Test successful agent retrieval"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager

        # Mock agent data
        mock_agent = {
            "agent_id": "test-agent-id",
            "name": "Test Agent",
            "goal": "Test goal",
            "tools": ["tool1", "tool2"],
            "created_at": datetime.utcnow(),
            "status": "active"
        }
        mock_agent_manager.get_agent_info.return_value = mock_agent

        # Test agent retrieval
        response = client.get("/api/v1/agents/test-agent-id")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "test-agent-id"
        assert data["name"] == "Test Agent"
        assert data["goal"] == "Test goal"
        assert data["tools"] == ["tool1", "tool2"]
        assert data["status"] == "active"

        # Verify agent manager was called
        mock_agent_manager.get_agent_info.assert_called_once_with("test-agent-id")

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, client, mock_agent_manager):
        """Test agent retrieval for non-existent agent"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager
        mock_agent_manager.get_agent_info.return_value = None

        # Test agent retrieval
        response = client.get("/api/v1/agents/non-existent-agent")

        assert response.status_code == 404
        data = response.json()
        assert "Agent not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_execute_agent_task_success(self, client, mock_agent_manager):
        """Test successful agent task execution"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager

        # Test agent task execution
        response = client.post(
            "/api/v1/agents/test-agent-id/execute",
            json={
                "task": "Test task",
                "user_id": "test_user"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "test-agent-id"
        assert data["task"] == "Test task"
        assert data["result"] == "Task completed"
        assert data["success"] is True
        assert data["intermediate_steps"] == []

        # Verify agent manager was called
        mock_agent_manager.execute_agent.assert_called_once()
        call_args = mock_agent_manager.execute_agent.call_args
        assert call_args[1]['agent_id'] == "test-agent-id"
        assert call_args[1]['task'] == "Test task"
        assert call_args[1]['user_id'] == "test_user"

    @pytest.mark.asyncio
    async def test_execute_agent_task_with_intermediate_steps(self, client, mock_agent_manager):
        """Test agent task execution with intermediate steps"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager

        # Mock execution result with intermediate steps
        mock_agent_manager.execute_agent.return_value = {
            "agent_id": "test-agent-id",
            "task": "Test task",
            "result": "Task completed",
            "success": True,
            "intermediate_steps": [
                {"action": "search", "observation": "Found relevant content"},
                {"action": "analyze", "observation": "Analysis complete"}
            ]
        }

        # Test agent task execution
        response = client.post(
            "/api/v1/agents/test-agent-id/execute",
            json={
                "task": "Test task"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["intermediate_steps"]) == 2
        assert data["intermediate_steps"][0]["action"] == "search"
        assert data["intermediate_steps"][1]["action"] == "analyze"

    @pytest.mark.asyncio
    async def test_execute_agent_task_failure(self, client, mock_agent_manager):
        """Test agent task execution failure"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager
        mock_agent_manager.execute_agent.side_effect = Exception("Execution failed")

        # Test agent task execution
        response = client.post(
            "/api/v1/agents/test-agent-id/execute",
            json={
                "task": "Test task"
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert "Execution failed" in data["detail"]

    @pytest.mark.asyncio
    async def test_delete_agent_success(self, client, mock_agent_manager):
        """Test successful agent deletion"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager

        # Test agent deletion
        response = client.delete("/api/v1/agents/test-agent-id?user_id=test_user")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Agent test-agent-id deleted successfully"
        assert data["agent_id"] == "test-agent-id"

        # Verify agent manager was called
        mock_agent_manager.delete_agent.assert_called_once_with("test-agent-id", "test_user")

    @pytest.mark.asyncio
    async def test_delete_agent_not_found(self, client, mock_agent_manager):
        """Test agent deletion for non-existent agent"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager
        mock_agent_manager.delete_agent.return_value = False

        # Test agent deletion
        response = client.delete("/api/v1/agents/non-existent-agent")

        assert response.status_code == 404
        data = response.json()
        assert "Agent not found or could not be deleted" in data["detail"]

    @pytest.mark.asyncio
    async def test_delete_agent_failure(self, client, mock_agent_manager):
        """Test agent deletion failure"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager
        mock_agent_manager.delete_agent.side_effect = Exception("Database error")

        # Test agent deletion
        response = client.delete("/api/v1/agents/test-agent-id")

        assert response.status_code == 500
        data = response.json()
        assert "Database error" in data["detail"]

    @pytest.mark.asyncio
    async def test_list_tools_success(self, client, mock_tool_registry):
        """Test successful tools listing"""
        # Setup app state
        client.app.state.tool_registry = mock_tool_registry

        # Test tools listing
        response = client.get("/api/v1/tools")

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "count" in data
        assert data["count"] == 3
        assert "analyze_image" in data["tools"]
        assert "search_content" in data["tools"]
        assert "generate_text" in data["tools"]

        # Verify tool registry was called
        mock_tool_registry.list_available_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_failure(self, client, mock_tool_registry):
        """Test tools listing failure"""
        # Setup app state
        client.app.state.tool_registry = mock_tool_registry
        mock_tool_registry.list_available_tools.side_effect = Exception("Tool registry error")

        # Test tools listing
        response = client.get("/api/v1/tools")

        assert response.status_code == 500
        data = response.json()
        assert "Tool registry error" in data["detail"]

    @pytest.mark.asyncio
    @patch('app.api.get_all_templates')
    async def test_list_templates_success(self, mock_get_templates, client):
        """Test successful templates listing"""
        # Mock templates
        mock_templates = {
            "research_agent": Mock(
                name="Research Agent",
                description="Agent for research tasks",
                goal="Conduct research",
                tools=["search_content", "generate_text"],
                memory_window=10,
                category="research",
                use_cases=["academic research", "market analysis"]
            )
        }
        mock_get_templates.return_value = mock_templates

        # Test templates listing
        response = client.get("/api/v1/templates")

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "count" in data
        assert data["count"] == 1
        assert len(data["templates"]) == 1
        assert data["templates"][0]["name"] == "research_agent"
        assert data["templates"][0]["display_name"] == "Research Agent"

    @pytest.mark.asyncio
    @patch('app.api.get_templates_by_category')
    async def test_list_templates_by_category(self, mock_get_templates, client):
        """Test templates listing by category"""
        # Mock templates
        mock_templates = {
            "research_agent": Mock(
                name="Research Agent",
                description="Agent for research tasks",
                goal="Conduct research",
                tools=["search_content"],
                memory_window=10,
                category="research",
                use_cases=["research"]
            )
        }
        mock_get_templates.return_value = mock_templates

        # Test templates listing by category
        response = client.get("/api/v1/templates?category=research")

        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "research"
        assert len(data["templates"]) == 1

    @pytest.mark.asyncio
    @patch('app.api.search_templates')
    async def test_list_templates_by_search(self, mock_search_templates, client):
        """Test templates listing by search"""
        # Mock templates
        mock_templates = {
            "research_agent": Mock(
                name="Research Agent",
                description="Agent for research tasks",
                goal="Conduct research",
                tools=["search_content"],
                memory_window=10,
                category="research",
                use_cases=["research"]
            )
        }
        mock_search_templates.return_value = mock_templates

        # Test templates listing by search
        response = client.get("/api/v1/templates?search=research")

        assert response.status_code == 200
        data = response.json()
        assert data["search"] == "research"
        assert len(data["templates"]) == 1

    @pytest.mark.asyncio
    @patch('app.api.get_template')
    async def test_get_template_details_success(self, mock_get_template, client):
        """Test successful template details retrieval"""
        # Mock template
        mock_template = Mock(
            name="Research Agent",
            description="Agent for research tasks",
            goal="Conduct research",
            tools=["search_content", "generate_text"],
            memory_window=10,
            category="research",
            use_cases=["academic research", "market analysis"]
        )
        mock_get_template.return_value = mock_template

        # Test template details retrieval
        response = client.get("/api/v1/templates/research_agent")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "research_agent"
        assert data["display_name"] == "Research Agent"
        assert data["description"] == "Agent for research tasks"
        assert data["goal"] == "Conduct research"
        assert data["tools"] == ["search_content", "generate_text"]
        assert data["category"] == "research"

    @pytest.mark.asyncio
    @patch('app.api.get_template')
    async def test_get_template_details_not_found(self, mock_get_template, client):
        """Test template details retrieval for non-existent template"""
        # Mock template not found
        mock_get_template.side_effect = ValueError("Template not found")

        # Test template details retrieval
        response = client.get("/api/v1/templates/non-existent-template")

        assert response.status_code == 404
        data = response.json()
        assert "Template not found" in data["detail"]

    @pytest.mark.asyncio
    @patch('app.api.get_template')
    async def test_create_agent_from_template_success(self, mock_get_template, client, mock_agent_manager):
        """Test successful agent creation from template"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager

        # Mock template
        mock_template = Mock(
            name="Research Agent",
            goal="Conduct research",
            tools=["search_content", "generate_text"],
            memory_window=10
        )
        mock_get_template.return_value = mock_template

        # Test agent creation from template
        response = client.post(
            "/api/v1/agents/from-template?template_name=research_agent&agent_name=My Research Agent&user_id=test_user"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "test-agent-id"
        assert data["template_name"] == "research_agent"
        assert data["agent_name"] == "My Research Agent"
        assert data["goal"] == "Conduct research"
        assert data["tools"] == ["search_content", "generate_text"]

        # Verify agent manager was called
        mock_agent_manager.create_agent.assert_called_once()
        call_args = mock_agent_manager.create_agent.call_args
        assert call_args[1]['agent_name'] == "My Research Agent"
        assert call_args[1]['goal'] == "Conduct research"
        assert call_args[1]['tools'] == ["search_content", "generate_text"]
        assert call_args[1]['user_id'] == "test_user"

    @pytest.mark.asyncio
    @patch('app.api.get_template')
    async def test_create_agent_from_template_with_default_name(self, mock_get_template, client, mock_agent_manager):
        """Test agent creation from template with default name"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager

        # Mock template
        mock_template = Mock(
            name="Research Agent",
            goal="Conduct research",
            tools=["search_content"],
            memory_window=10
        )
        mock_get_template.return_value = mock_template

        # Test agent creation from template without custom name
        response = client.post(
            "/api/v1/agents/from-template?template_name=research_agent"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agent_name"] == "Research Agent"  # Uses template name

        # Verify agent manager was called with template name
        mock_agent_manager.create_agent.assert_called_once()
        call_args = mock_agent_manager.create_agent.call_args
        assert call_args[1]['agent_name'] == "Research Agent"

    @pytest.mark.asyncio
    @patch('app.api.get_template')
    async def test_create_agent_from_template_not_found(self, mock_get_template, client):
        """Test agent creation from non-existent template"""
        # Mock template not found
        mock_get_template.side_effect = ValueError("Template not found")

        # Test agent creation from template
        response = client.post(
            "/api/v1/agents/from-template?template_name=non-existent-template"
        )

        assert response.status_code == 404
        data = response.json()
        assert "Template not found" in data["detail"]

    @pytest.mark.asyncio
    @patch('app.api.AgentTemplates')
    async def test_list_template_categories_success(self, mock_agent_templates, client):
        """Test successful template categories listing"""
        # Mock categories
        mock_agent_templates.get_categories.return_value = ["research", "analysis", "creative"]

        # Test template categories listing
        response = client.get("/api/v1/templates/categories")

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "count" in data
        assert data["count"] == 3
        assert "research" in data["categories"]
        assert "analysis" in data["categories"]
        assert "creative" in data["categories"]

    @pytest.mark.asyncio
    async def test_get_agent_history_success(self, client, mock_memory_manager):
        """Test successful agent history retrieval"""
        # Setup app state
        client.app.state.memory_manager = mock_memory_manager

        # Mock database rows
        mock_rows = [
            {
                "task": "Task 1",
                "result": {"output": "Result 1"},
                "executed_at": datetime.utcnow(),
                "success": True,
                "execution_time_ms": 1000
            },
            {
                "task": "Task 2",
                "result": {"output": "Result 2"},
                "executed_at": datetime.utcnow(),
                "success": False,
                "execution_time_ms": 2000
            }
        ]
        mock_conn = mock_memory_manager.pool.acquire.return_value.__aenter__.return_value
        mock_conn.fetch.return_value = mock_rows

        # Test agent history retrieval
        response = client.get("/api/v1/agents/test-agent-id/history?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "test-agent-id"
        assert "history" in data
        assert "count" in data
        assert data["count"] == 2
        assert len(data["history"]) == 2
        assert data["history"][0]["task"] == "Task 1"
        assert data["history"][1]["task"] == "Task 2"

    @pytest.mark.asyncio
    async def test_get_agent_stats_success(self, client, mock_memory_manager):
        """Test successful agent statistics retrieval"""
        # Setup app state
        client.app.state.memory_manager = mock_memory_manager

        # Mock database row
        mock_row = {
            "total_executions": 10,
            "successful_executions": 8,
            "avg_execution_time": 1500.5,
            "last_execution": datetime.utcnow()
        }
        mock_conn = mock_memory_manager.pool.acquire.return_value.__aenter__.return_value
        mock_conn.fetchrow.return_value = mock_row

        # Test agent statistics retrieval
        response = client.get("/api/v1/agents/test-agent-id/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "test-agent-id"
        assert data["total_executions"] == 10
        assert data["successful_executions"] == 8
        assert data["success_rate"] == 80.0
        assert data["avg_execution_time_ms"] == 1500.5
        assert "last_execution" in data

    @pytest.mark.asyncio
    async def test_get_agent_stats_no_executions(self, client, mock_memory_manager):
        """Test agent statistics retrieval with no executions"""
        # Setup app state
        client.app.state.memory_manager = mock_memory_manager

        # Mock empty database row
        mock_conn = mock_memory_manager.pool.acquire.return_value.__aenter__.return_value
        mock_conn.fetchrow.return_value = None

        # Test agent statistics retrieval
        response = client.get("/api/v1/agents/test-agent-id/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "test-agent-id"
        assert data["total_executions"] == 0
        assert data["successful_executions"] == 0
        assert data["success_rate"] == 0
        assert data["avg_execution_time_ms"] == 0
        assert data["last_execution"] is None

    def test_get_service_status(self, client):
        """Test service status endpoint"""
        response = client.get("/api/v1/status")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "ai-agents"
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "features" in data
        assert data["features"]["langchain"] == "enabled"
        assert data["features"]["multimodal_tools"] == "enabled"
        assert data["features"]["persistent_memory"] == "enabled"
        assert data["features"]["autonomous_execution"] == "enabled"

    def test_invalid_endpoint(self, client):
        """Test invalid endpoint"""
        response = client.get("/api/v1/invalid/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test method not allowed"""
        response = client.put("/api/v1/health")
        assert response.status_code == 405

    def test_create_agent_invalid_json(self, client):
        """Test agent creation with invalid JSON"""
        response = client.post(
            "/api/v1/agents",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_execute_agent_invalid_json(self, client):
        """Test agent execution with invalid JSON"""
        response = client.post(
            "/api/v1/agents/test-agent-id/execute",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_execute_agent_missing_task(self, client):
        """Test agent execution with missing task"""
        response = client.post(
            "/api/v1/agents/test-agent-id/execute",
            json={
                "user_id": "test_user"
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_agent_with_empty_tools(self, client, mock_agent_manager):
        """Test agent creation with empty tools list"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager

        # Test agent creation with empty tools
        response = client.post(
            "/api/v1/agents",
            json={
                "name": "Test Agent",
                "goal": "Test goal",
                "tools": []
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tools"] == []

        # Verify agent manager was called with empty tools
        mock_agent_manager.create_agent.assert_called_once()
        call_args = mock_agent_manager.create_agent.call_args
        assert call_args[1]['tools'] == []

    @pytest.mark.asyncio
    async def test_execute_agent_with_default_user_id(self, client, mock_agent_manager):
        """Test agent execution with default user ID"""
        # Setup app state
        client.app.state.agent_manager = mock_agent_manager

        # Test agent execution without user_id
        response = client.post(
            "/api/v1/agents/test-agent-id/execute",
            json={
                "task": "Test task"
            }
        )

        assert response.status_code == 200

        # Verify agent manager was called with default user_id
        mock_agent_manager.execute_agent.assert_called_once()
        call_args = mock_agent_manager.execute_agent.call_args
        assert call_args[1]['user_id'] == "default"