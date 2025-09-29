"""
Integration tests for AI Agents API
"""

import pytest
import httpx
import json
from typing import AsyncGenerator

@pytest.fixture
async def api_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create HTTP client for API testing"""
    async with httpx.AsyncClient(base_url="http://localhost:3000") as client:
        yield client

@pytest.fixture
def sample_agent_data():
    """Sample agent data for testing"""
    return {
        "name": "Integration Test Agent",
        "description": "An agent for integration testing",
        "goal": "Test API integration",
        "tools": ["search_content", "generate_text"],
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1000
    }

@pytest.mark.integration
class TestAIAgentsAPI:
    """Integration tests for AI Agents API"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, api_client):
        """Test health check endpoint"""
        response = await api_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-agents"
    
    @pytest.mark.asyncio
    async def test_create_agent(self, api_client, sample_agent_data):
        """Test creating an agent via API"""
        response = await api_client.post("/agents", json=sample_agent_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "agent_id" in data
        assert data["name"] == sample_agent_data["name"]
        assert data["description"] == sample_agent_data["description"]
        assert data["goal"] == sample_agent_data["goal"]
        assert data["tools"] == sample_agent_data["tools"]
        assert data["model"] == sample_agent_data["model"]
        assert data["temperature"] == sample_agent_data["temperature"]
        assert data["max_tokens"] == sample_agent_data["max_tokens"]
        
        return data["agent_id"]
    
    @pytest.mark.asyncio
    async def test_get_agent(self, api_client, sample_agent_data):
        """Test getting an agent via API"""
        # Create agent first
        create_response = await api_client.post("/agents", json=sample_agent_data)
        assert create_response.status_code == 201
        agent_id = create_response.json()["agent_id"]
        
        # Get agent
        response = await api_client.get(f"/agents/{agent_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["agent_id"] == agent_id
        assert data["name"] == sample_agent_data["name"]
        assert data["description"] == sample_agent_data["description"]
        assert data["goal"] == sample_agent_data["goal"]
        assert data["tools"] == sample_agent_data["tools"]
        assert data["model"] == sample_agent_data["model"]
        assert data["temperature"] == sample_agent_data["temperature"]
        assert data["max_tokens"] == sample_agent_data["max_tokens"]
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, api_client):
        """Test getting a non-existent agent"""
        response = await api_client.get("/agents/nonexistent-id")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_get_all_agents(self, api_client, sample_agent_data):
        """Test getting all agents"""
        # Create multiple agents
        agent_ids = []
        for i in range(3):
            data = sample_agent_data.copy()
            data["name"] = f"Test Agent {i}"
            response = await api_client.post("/agents", json=data)
            assert response.status_code == 201
            agent_ids.append(response.json()["agent_id"])
        
        # Get all agents
        response = await api_client.get("/agents")
        assert response.status_code == 200
        
        data = response.json()
        assert "agents" in data
        assert "count" in data
        assert len(data["agents"]) >= 3
        
        # Verify our agents are in the list
        agent_names = [agent["name"] for agent in data["agents"]]
        assert "Test Agent 0" in agent_names
        assert "Test Agent 1" in agent_names
        assert "Test Agent 2" in agent_names
    
    @pytest.mark.asyncio
    async def test_update_agent(self, api_client, sample_agent_data):
        """Test updating an agent via API"""
        # Create agent first
        create_response = await api_client.post("/agents", json=sample_agent_data)
        assert create_response.status_code == 201
        agent_id = create_response.json()["agent_id"]
        
        # Update agent
        updates = {
            "name": "Updated Agent",
            "description": "Updated description",
            "temperature": 0.9
        }
        
        response = await api_client.put(f"/agents/{agent_id}", json=updates)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Agent"
        assert data["description"] == "Updated description"
        assert data["temperature"] == 0.9
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_agent(self, api_client):
        """Test updating a non-existent agent"""
        updates = {"name": "Updated Agent"}
        response = await api_client.put("/agents/nonexistent-id", json=updates)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_agent(self, api_client, sample_agent_data):
        """Test deleting an agent via API"""
        # Create agent first
        create_response = await api_client.post("/agents", json=sample_agent_data)
        assert create_response.status_code == 201
        agent_id = create_response.json()["agent_id"]
        
        # Delete agent
        response = await api_client.delete(f"/agents/{agent_id}")
        assert response.status_code == 200
        
        # Verify agent was deleted
        get_response = await api_client.get(f"/agents/{agent_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_agent(self, api_client):
        """Test deleting a non-existent agent"""
        response = await api_client.delete("/agents/nonexistent-id")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_execute_agent(self, api_client, sample_agent_data):
        """Test executing an agent via API"""
        # Create agent first
        create_response = await api_client.post("/agents", json=sample_agent_data)
        assert create_response.status_code == 201
        agent_id = create_response.json()["agent_id"]
        
        # Execute agent
        execution_data = {
            "task": "Test task execution",
            "user_id": "test_user"
        }
        
        response = await api_client.post(f"/agents/{agent_id}/execute", json=execution_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "execution_id" in data
        assert data["agent_id"] == agent_id
        assert data["task"] == "Test task execution"
        assert data["user_id"] == "test_user"
        assert data["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_agent(self, api_client):
        """Test executing a non-existent agent"""
        execution_data = {
            "task": "Test task",
            "user_id": "test_user"
        }
        
        response = await api_client.post("/agents/nonexistent-id/execute", json=execution_data)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_execution(self, api_client, sample_agent_data):
        """Test getting an execution via API"""
        # Create agent and execute it
        create_response = await api_client.post("/agents", json=sample_agent_data)
        agent_id = create_response.json()["agent_id"]
        
        execution_data = {
            "task": "Test task",
            "user_id": "test_user"
        }
        
        execute_response = await api_client.post(f"/agents/{agent_id}/execute", json=execution_data)
        execution_id = execute_response.json()["execution_id"]
        
        # Get execution
        response = await api_client.get(f"/executions/{execution_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["execution_id"] == execution_id
        assert data["agent_id"] == agent_id
        assert data["task"] == "Test task"
        assert data["user_id"] == "test_user"
        assert data["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_execution(self, api_client):
        """Test getting a non-existent execution"""
        response = await api_client.get("/executions/nonexistent-id")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_agent_executions(self, api_client, sample_agent_data):
        """Test getting executions for an agent"""
        # Create agent and execute it multiple times
        create_response = await api_client.post("/agents", json=sample_agent_data)
        agent_id = create_response.json()["agent_id"]
        
        execution_data = {
            "task": "Test task",
            "user_id": "test_user"
        }
        
        # Create multiple executions
        for i in range(3):
            execution_data["task"] = f"Test task {i}"
            response = await api_client.post(f"/agents/{agent_id}/execute", json=execution_data)
            assert response.status_code == 200
        
        # Get agent executions
        response = await api_client.get(f"/agents/{agent_id}/executions")
        assert response.status_code == 200
        
        data = response.json()
        assert "executions" in data
        assert "count" in data
        assert len(data["executions"]) >= 3
    
    @pytest.mark.asyncio
    async def test_get_user_executions(self, api_client, sample_agent_data):
        """Test getting executions for a user"""
        # Create agent and execute it
        create_response = await api_client.post("/agents", json=sample_agent_data)
        agent_id = create_response.json()["agent_id"]
        
        execution_data = {
            "task": "Test task",
            "user_id": "test_user"
        }
        
        # Create multiple executions
        for i in range(3):
            execution_data["task"] = f"Test task {i}"
            response = await api_client.post(f"/agents/{agent_id}/execute", json=execution_data)
            assert response.status_code == 200
        
        # Get user executions
        response = await api_client.get("/executions?user_id=test_user")
        assert response.status_code == 200
        
        data = response.json()
        assert "executions" in data
        assert "count" in data
        assert len(data["executions"]) >= 3
    
    @pytest.mark.asyncio
    async def test_update_execution(self, api_client, sample_agent_data):
        """Test updating an execution via API"""
        # Create agent and execute it
        create_response = await api_client.post("/agents", json=sample_agent_data)
        agent_id = create_response.json()["agent_id"]
        
        execution_data = {
            "task": "Test task",
            "user_id": "test_user"
        }
        
        execute_response = await api_client.post(f"/agents/{agent_id}/execute", json=execution_data)
        execution_id = execute_response.json()["execution_id"]
        
        # Update execution
        updates = {
            "status": "completed",
            "result": "Task completed successfully",
            "progress": 100
        }
        
        response = await api_client.put(f"/executions/{execution_id}", json=updates)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"] == "Task completed successfully"
        assert data["progress"] == 100
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_execution(self, api_client):
        """Test updating a non-existent execution"""
        updates = {"status": "completed"}
        response = await api_client.put("/executions/nonexistent-id", json=updates)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_agent_statistics(self, api_client, sample_agent_data):
        """Test getting agent statistics via API"""
        # Create agent and execute it
        create_response = await api_client.post("/agents", json=sample_agent_data)
        agent_id = create_response.json()["agent_id"]
        
        execution_data = {
            "task": "Test task",
            "user_id": "test_user"
        }
        
        execute_response = await api_client.post(f"/agents/{agent_id}/execute", json=execution_data)
        assert execute_response.status_code == 200
        
        # Get agent statistics
        response = await api_client.get(f"/agents/{agent_id}/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "agent_id" in data
        assert "total_executions" in data
        assert "successful_executions" in data
        assert "failed_executions" in data
        assert "success_rate" in data
        assert "avg_execution_time" in data
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, api_client, sample_agent_data):
        """Test getting overall statistics via API"""
        # Create agent and execute it
        create_response = await api_client.post("/agents", json=sample_agent_data)
        agent_id = create_response.json()["agent_id"]
        
        execution_data = {
            "task": "Test task",
            "user_id": "test_user"
        }
        
        execute_response = await api_client.post(f"/agents/{agent_id}/execute", json=execution_data)
        assert execute_response.status_code == 200
        
        # Get overall statistics
        response = await api_client.get("/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_agents" in data
        assert "total_executions" in data
        assert "successful_executions" in data
        assert "failed_executions" in data
        assert "success_rate" in data
        assert "avg_execution_time" in data
    
    @pytest.mark.asyncio
    async def test_search_agents(self, api_client, sample_agent_data):
        """Test searching agents via API"""
        # Create agents with different names
        data1 = sample_agent_data.copy()
        data1["name"] = "Research Assistant"
        data1["description"] = "Helps with research tasks"
        response1 = await api_client.post("/agents", json=data1)
        assert response1.status_code == 201
        
        data2 = sample_agent_data.copy()
        data2["name"] = "Content Creator"
        data2["description"] = "Creates content for blogs"
        response2 = await api_client.post("/agents", json=data2)
        assert response2.status_code == 201
        
        # Search by name
        response = await api_client.get("/agents/search?query=Research")
        assert response.status_code == 200
        
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) >= 1
        assert any(agent["name"] == "Research Assistant" for agent in data["agents"])
        
        # Search by description
        response = await api_client.get("/agents/search?query=content")
        assert response.status_code == 200
        
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) >= 1
        assert any(agent["name"] == "Content Creator" for agent in data["agents"])
    
    @pytest.mark.asyncio
    async def test_invalid_agent_data(self, api_client):
        """Test creating agent with invalid data"""
        invalid_data = {
            "name": "",  # Empty name
            "description": "Test description",
            "goal": "Test goal"
        }
        
        response = await api_client.post("/agents", json=invalid_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_invalid_execution_data(self, api_client, sample_agent_data):
        """Test executing agent with invalid data"""
        # Create agent first
        create_response = await api_client.post("/agents", json=sample_agent_data)
        agent_id = create_response.json()["agent_id"]
        
        # Try to execute with invalid data
        invalid_data = {
            "task": "",  # Empty task
            "user_id": "test_user"
        }
        
        response = await api_client.post(f"/agents/{agent_id}/execute", json=invalid_data)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, api_client, sample_agent_data):
        """Test handling concurrent requests"""
        import asyncio
        
        async def create_agent(index):
            data = sample_agent_data.copy()
            data["name"] = f"Concurrent Agent {index}"
            response = await api_client.post("/agents", json=data)
            return response.status_code == 201
        
        # Create agents concurrently
        tasks = [create_agent(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Verify all requests succeeded
        assert all(results)
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, api_client):
        """Test API error handling"""
        # Test invalid endpoint
        response = await api_client.get("/invalid-endpoint")
        assert response.status_code == 404
        
        # Test invalid method
        response = await api_client.post("/health")
        assert response.status_code == 405
        
        # Test invalid JSON
        response = await api_client.post("/agents", content="invalid json")
        assert response.status_code == 422