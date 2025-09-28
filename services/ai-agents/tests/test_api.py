"""
Unit tests for API endpoints in ai-agents service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import json

from main import app


class TestAIAgentsAPI:
    """Test cases for AI Agents API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

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
    @patch('main.agent_manager')
    async def test_create_agent_endpoint_success(self, mock_agent_manager, client, test_agent_creation_request):
        """Test successful agent creation endpoint"""
        # Mock agent creation
        mock_agent_manager.create_agent.return_value = {
            "success": True,
            "agent_id": "test_agent_123",
            "agent": {
                "id": "test_agent_123",
                "name": "Test Agent",
                "goal": "Test agent for unit testing",
                "tools": ["search_content", "generate_text"]
            }
        }

        # Test agent creation
        response = client.post("/api/v1/agents", json=test_agent_creation_request)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == "test_agent_123"
        assert data["agent"]["name"] == "Test Agent"

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_create_agent_from_template_endpoint_success(self, mock_agent_manager, client):
        """Test successful agent creation from template endpoint"""
        # Mock agent creation from template
        mock_agent_manager.create_agent_from_template.return_value = {
            "success": True,
            "agent_id": "test_agent_123",
            "agent": {
                "id": "test_agent_123",
                "name": "My Research Agent",
                "goal": "Help users with research tasks"
            }
        }

        # Test agent creation from template
        response = client.post(
            "/api/v1/agents/from-template",
            params={
                "template_name": "research_assistant",
                "agent_name": "My Research Agent"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == "test_agent_123"
        assert data["agent"]["name"] == "My Research Agent"

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_get_agent_endpoint_success(self, mock_agent_manager, client, mock_agent):
        """Test successful agent retrieval endpoint"""
        # Mock agent retrieval
        mock_agent_manager.get_agent.return_value = {
            "success": True,
            "agent": mock_agent
        }

        # Test agent retrieval
        response = client.get("/api/v1/agents/test_agent_123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent"]["id"] == "test_agent_123"
        assert data["agent"]["name"] == "Test Agent"

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_get_agent_endpoint_not_found(self, mock_agent_manager, client):
        """Test agent retrieval endpoint for non-existent agent"""
        # Mock agent not found
        mock_agent_manager.get_agent.return_value = {
            "success": False,
            "error": "Agent not found"
        }

        # Test agent retrieval
        response = client.get("/api/v1/agents/nonexistent_agent")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_list_agents_endpoint_success(self, mock_agent_manager, client, mock_agent):
        """Test successful agent listing endpoint"""
        # Mock agent listing
        mock_agent_manager.list_agents.return_value = {
            "success": True,
            "agents": [mock_agent],
            "total": 1
        }

        # Test agent listing
        response = client.get("/api/v1/agents?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["agents"]) == 1
        assert data["total"] == 1

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_update_agent_endpoint_success(self, mock_agent_manager, client):
        """Test successful agent update endpoint"""
        # Mock agent update
        mock_agent_manager.update_agent.return_value = {
            "success": True,
            "agent_id": "test_agent_123"
        }

        # Test agent update
        update_data = {
            "name": "Updated Agent Name",
            "goal": "Updated goal"
        }
        response = client.put("/api/v1/agents/test_agent_123", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == "test_agent_123"

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_delete_agent_endpoint_success(self, mock_agent_manager, client):
        """Test successful agent deletion endpoint"""
        # Mock agent deletion
        mock_agent_manager.delete_agent.return_value = {
            "success": True,
            "agent_id": "test_agent_123"
        }

        # Test agent deletion
        response = client.delete("/api/v1/agents/test_agent_123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == "test_agent_123"

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_execute_agent_endpoint_success(self, mock_agent_manager, client, test_agent_execution_request):
        """Test successful agent execution endpoint"""
        # Mock agent execution
        mock_agent_manager.execute_agent.return_value = {
            "success": True,
            "result": "Agent execution result",
            "execution_time_ms": 150,
            "tools_used": ["search_content"]
        }

        # Test agent execution
        response = client.post(
            "/api/v1/agents/test_agent_123/execute",
            json=test_agent_execution_request
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"] == "Agent execution result"
        assert data["execution_time_ms"] == 150

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_execute_agent_endpoint_failure(self, mock_agent_manager, client, test_agent_execution_request):
        """Test agent execution endpoint failure"""
        # Mock agent execution failure
        mock_agent_manager.execute_agent.return_value = {
            "success": False,
            "error": "Execution failed"
        }

        # Test agent execution
        response = client.post(
            "/api/v1/agents/test_agent_123/execute",
            json=test_agent_execution_request
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_get_agent_stats_endpoint_success(self, mock_agent_manager, client):
        """Test successful agent statistics endpoint"""
        # Mock agent stats
        mock_agent_manager.get_agent_stats.return_value = {
            "success": True,
            "stats": {
                "total_executions": 100,
                "successful_executions": 95,
                "failed_executions": 5,
                "avg_execution_time_ms": 150
            }
        }

        # Test agent stats
        response = client.get("/api/v1/agents/test_agent_123/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["stats"]["total_executions"] == 100
        assert data["stats"]["successful_executions"] == 95

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_get_agent_history_endpoint_success(self, mock_agent_manager, client, mock_agent_memory):
        """Test successful agent history endpoint"""
        # Mock agent history
        mock_agent_manager.get_agent_history.return_value = {
            "success": True,
            "history": [mock_agent_memory]
        }

        # Test agent history
        response = client.get("/api/v1/agents/test_agent_123/history?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["history"]) == 1

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_get_templates_endpoint_success(self, mock_agent_manager, client, mock_agent_template):
        """Test successful templates endpoint"""
        # Mock templates
        mock_agent_manager.get_available_templates.return_value = {
            "success": True,
            "templates": {"research_assistant": mock_agent_template}
        }

        # Test templates
        response = client.get("/api/v1/templates")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "research_assistant" in data["templates"]

    @pytest.mark.asyncio
    @patch('main.tool_manager')
    async def test_get_tools_endpoint_success(self, mock_tool_manager, client):
        """Test successful tools endpoint"""
        # Mock tools
        mock_tool_manager.list_tools.return_value = {
            "search_content": {"name": "search_content", "description": "Search content"},
            "generate_text": {"name": "generate_text", "description": "Generate text"}
        }

        # Test tools
        response = client.get("/api/v1/tools")

        assert response.status_code == 200
        data = response.json()
        assert "search_content" in data["tools"]
        assert "generate_text" in data["tools"]

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_health_check_endpoint(self, mock_agent_manager, client):
        """Test health check endpoint"""
        # Mock health check
        mock_agent_manager.health_check.return_value = {
            "status": "healthy",
            "database": "healthy",
            "templates_loaded": 5
        }

        # Test health check
        response = client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "healthy"
        assert data["templates_loaded"] == 5

    def test_invalid_endpoint(self, client):
        """Test invalid endpoint"""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test method not allowed"""
        response = client.put("/health")
        assert response.status_code == 405

    def test_create_agent_with_missing_fields(self, client):
        """Test agent creation with missing required fields"""
        response = client.post(
            "/api/v1/agents",
            json={
                "name": "Test Agent"
                # Missing required fields: goal, tools
            }
        )

        assert response.status_code == 422  # Validation error

    def test_create_agent_with_invalid_tools(self, client):
        """Test agent creation with invalid tools"""
        response = client.post(
            "/api/v1/agents",
            json={
                "name": "Test Agent",
                "goal": "Test goal",
                "tools": ["invalid_tool"]  # Invalid tool
            }
        )

        assert response.status_code == 422  # Validation error

    def test_execute_agent_with_missing_task(self, client):
        """Test agent execution with missing task"""
        response = client.post(
            "/api/v1/agents/test_agent_123/execute",
            json={
                "context": {"user_id": "test_user"}
                # Missing required field: task
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_list_agents_with_pagination(self, mock_agent_manager, client, mock_agent):
        """Test agent listing with pagination"""
        # Mock agent listing
        mock_agent_manager.list_agents.return_value = {
            "success": True,
            "agents": [mock_agent],
            "total": 1,
            "limit": 10,
            "offset": 0
        }

        # Test agent listing with pagination
        response = client.get("/api/v1/agents?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["limit"] == 10
        assert data["offset"] == 0

    @pytest.mark.asyncio
    @patch('main.agent_manager')
    async def test_agent_execution_with_timeout(self, mock_agent_manager, client):
        """Test agent execution with timeout"""
        # Mock agent execution with timeout
        mock_agent_manager.execute_agent.return_value = {
            "success": False,
            "error": "Execution timeout"
        }

        # Test agent execution
        response = client.post(
            "/api/v1/agents/test_agent_123/execute",
            json={
                "task": "Test task",
                "parameters": {"timeout_seconds": 5}
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "timeout" in data["error"].lower()
