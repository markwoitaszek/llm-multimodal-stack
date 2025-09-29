"""
Unit tests for AI Agents service - Agent Manager
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from services.ai-agents.app.agent_manager import AgentManager, Agent, AgentExecution


class TestAgentManager:
    """Test cases for AgentManager"""
    
    @pytest.fixture
    async def agent_manager(self):
        """Create AgentManager instance for testing"""
        manager = AgentManager()
        await manager.initialize()
        return manager
    
    @pytest.fixture
    def sample_agent_data(self):
        """Sample agent data for testing"""
        return {
            "name": "Test Agent",
            "description": "A test agent",
            "goal": "Test agent functionality",
            "tools": ["search_content", "generate_text"],
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        }
    
    @pytest.mark.asyncio
    async def test_create_agent(self, agent_manager, sample_agent_data):
        """Test creating a new agent"""
        agent_id = await agent_manager.create_agent(sample_agent_data)
        
        assert agent_id is not None
        assert isinstance(agent_id, str)
        
        # Verify agent was created
        agent = await agent_manager.get_agent(agent_id)
        assert agent is not None
        assert agent.name == sample_agent_data["name"]
        assert agent.description == sample_agent_data["description"]
        assert agent.goal == sample_agent_data["goal"]
        assert agent.tools == sample_agent_data["tools"]
        assert agent.model == sample_agent_data["model"]
        assert agent.temperature == sample_agent_data["temperature"]
        assert agent.max_tokens == sample_agent_data["max_tokens"]
    
    @pytest.mark.asyncio
    async def test_create_agent_with_invalid_data(self, agent_manager):
        """Test creating agent with invalid data"""
        invalid_data = {
            "name": "",  # Empty name
            "description": "Test description",
            "goal": "Test goal"
        }
        
        with pytest.raises(ValueError):
            await agent_manager.create_agent(invalid_data)
    
    @pytest.mark.asyncio
    async def test_get_agent(self, agent_manager, sample_agent_data):
        """Test getting an agent by ID"""
        agent_id = await agent_manager.create_agent(sample_agent_data)
        agent = await agent_manager.get_agent(agent_id)
        
        assert agent is not None
        assert agent.agent_id == agent_id
        assert agent.name == sample_agent_data["name"]
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, agent_manager):
        """Test getting a non-existent agent"""
        agent = await agent_manager.get_agent("nonexistent-id")
        assert agent is None
    
    @pytest.mark.asyncio
    async def test_get_all_agents(self, agent_manager, sample_agent_data):
        """Test getting all agents"""
        # Create multiple agents
        agent_ids = []
        for i in range(3):
            data = sample_agent_data.copy()
            data["name"] = f"Test Agent {i}"
            agent_id = await agent_manager.create_agent(data)
            agent_ids.append(agent_id)
        
        agents = await agent_manager.get_all_agents()
        
        assert len(agents) >= 3
        agent_names = [agent.name for agent in agents]
        assert "Test Agent 0" in agent_names
        assert "Test Agent 1" in agent_names
        assert "Test Agent 2" in agent_names
    
    @pytest.mark.asyncio
    async def test_update_agent(self, agent_manager, sample_agent_data):
        """Test updating an agent"""
        agent_id = await agent_manager.create_agent(sample_agent_data)
        
        updates = {
            "name": "Updated Agent",
            "description": "Updated description",
            "temperature": 0.9
        }
        
        success = await agent_manager.update_agent(agent_id, updates)
        assert success is True
        
        # Verify updates
        agent = await agent_manager.get_agent(agent_id)
        assert agent.name == "Updated Agent"
        assert agent.description == "Updated description"
        assert agent.temperature == 0.9
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_agent(self, agent_manager):
        """Test updating a non-existent agent"""
        updates = {"name": "Updated Agent"}
        success = await agent_manager.update_agent("nonexistent-id", updates)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_delete_agent(self, agent_manager, sample_agent_data):
        """Test deleting an agent"""
        agent_id = await agent_manager.create_agent(sample_agent_data)
        
        success = await agent_manager.delete_agent(agent_id)
        assert success is True
        
        # Verify agent was deleted
        agent = await agent_manager.get_agent(agent_id)
        assert agent is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_agent(self, agent_manager):
        """Test deleting a non-existent agent"""
        success = await agent_manager.delete_agent("nonexistent-id")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_execute_agent(self, agent_manager, sample_agent_data):
        """Test executing an agent"""
        agent_id = await agent_manager.create_agent(sample_agent_data)
        task = "Test task"
        user_id = "test_user"
        
        execution_id = await agent_manager.execute_agent(agent_id, task, user_id)
        
        assert execution_id is not None
        assert isinstance(execution_id, str)
        
        # Verify execution was created
        execution = await agent_manager.get_execution(execution_id)
        assert execution is not None
        assert execution.agent_id == agent_id
        assert execution.task == task
        assert execution.user_id == user_id
        assert execution.status == "running"
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_agent(self, agent_manager):
        """Test executing a non-existent agent"""
        execution_id = await agent_manager.execute_agent("nonexistent-id", "task", "user")
        assert execution_id is None
    
    @pytest.mark.asyncio
    async def test_get_execution(self, agent_manager, sample_agent_data):
        """Test getting an execution by ID"""
        agent_id = await agent_manager.create_agent(sample_agent_data)
        execution_id = await agent_manager.execute_agent(agent_id, "Test task", "test_user")
        
        execution = await agent_manager.get_execution(execution_id)
        
        assert execution is not None
        assert execution.execution_id == execution_id
        assert execution.agent_id == agent_id
        assert execution.task == "Test task"
        assert execution.user_id == "test_user"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_execution(self, agent_manager):
        """Test getting a non-existent execution"""
        execution = await agent_manager.get_execution("nonexistent-id")
        assert execution is None
    
    @pytest.mark.asyncio
    async def test_get_agent_executions(self, agent_manager, sample_agent_data):
        """Test getting executions for an agent"""
        agent_id = await agent_manager.create_agent(sample_agent_data)
        
        # Create multiple executions
        execution_ids = []
        for i in range(3):
            execution_id = await agent_manager.execute_agent(agent_id, f"Task {i}", "test_user")
            execution_ids.append(execution_id)
        
        executions = await agent_manager.get_agent_executions(agent_id)
        
        assert len(executions) == 3
        execution_ids_found = [exec.execution_id for exec in executions]
        for execution_id in execution_ids:
            assert execution_id in execution_ids_found
    
    @pytest.mark.asyncio
    async def test_get_user_executions(self, agent_manager, sample_agent_data):
        """Test getting executions for a user"""
        agent_id = await agent_manager.create_agent(sample_agent_data)
        user_id = "test_user"
        
        # Create multiple executions
        execution_ids = []
        for i in range(3):
            execution_id = await agent_manager.execute_agent(agent_id, f"Task {i}", user_id)
            execution_ids.append(execution_id)
        
        executions = await agent_manager.get_user_executions(user_id)
        
        assert len(executions) == 3
        execution_ids_found = [exec.execution_id for exec in executions]
        for execution_id in execution_ids:
            assert execution_id in execution_ids_found
    
    @pytest.mark.asyncio
    async def test_update_execution(self, agent_manager, sample_agent_data):
        """Test updating an execution"""
        agent_id = await agent_manager.create_agent(sample_agent_data)
        execution_id = await agent_manager.execute_agent(agent_id, "Test task", "test_user")
        
        updates = {
            "status": "completed",
            "result": "Task completed successfully",
            "progress": 100
        }
        
        success = await agent_manager.update_execution(execution_id, updates)
        assert success is True
        
        # Verify updates
        execution = await agent_manager.get_execution(execution_id)
        assert execution.status == "completed"
        assert execution.result == "Task completed successfully"
        assert execution.progress == 100
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_execution(self, agent_manager):
        """Test updating a non-existent execution"""
        updates = {"status": "completed"}
        success = await agent_manager.update_execution("nonexistent-id", updates)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_get_agent_statistics(self, agent_manager, sample_agent_data):
        """Test getting agent statistics"""
        agent_id = await agent_manager.create_agent(sample_agent_data)
        
        # Create some executions
        await agent_manager.execute_agent(agent_id, "Task 1", "user1")
        await agent_manager.execute_agent(agent_id, "Task 2", "user2")
        
        stats = await agent_manager.get_agent_statistics(agent_id)
        
        assert stats is not None
        assert stats["agent_id"] == agent_id
        assert stats["total_executions"] >= 2
        assert stats["successful_executions"] >= 0
        assert stats["failed_executions"] >= 0
        assert "success_rate" in stats
        assert "avg_execution_time" in stats
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, agent_manager, sample_agent_data):
        """Test getting overall statistics"""
        # Create some agents and executions
        agent_id = await agent_manager.create_agent(sample_agent_data)
        await agent_manager.execute_agent(agent_id, "Task 1", "user1")
        
        stats = await agent_manager.get_statistics()
        
        assert stats is not None
        assert "total_agents" in stats
        assert "total_executions" in stats
        assert "successful_executions" in stats
        assert "failed_executions" in stats
        assert "success_rate" in stats
        assert "avg_execution_time" in stats
        assert stats["total_agents"] >= 1
        assert stats["total_executions"] >= 1
    
    @pytest.mark.asyncio
    async def test_search_agents(self, agent_manager, sample_agent_data):
        """Test searching agents"""
        # Create agents with different names
        data1 = sample_agent_data.copy()
        data1["name"] = "Research Assistant"
        data1["description"] = "Helps with research tasks"
        await agent_manager.create_agent(data1)
        
        data2 = sample_agent_data.copy()
        data2["name"] = "Content Creator"
        data2["description"] = "Creates content for blogs"
        await agent_manager.create_agent(data2)
        
        # Search by name
        results = await agent_manager.search_agents("Research")
        assert len(results) >= 1
        assert any(agent.name == "Research Assistant" for agent in results)
        
        # Search by description
        results = await agent_manager.search_agents("content")
        assert len(results) >= 1
        assert any(agent.name == "Content Creator" for agent in results)
    
    @pytest.mark.asyncio
    async def test_agent_validation(self, agent_manager):
        """Test agent data validation"""
        # Test missing required fields
        invalid_data = {
            "description": "Test description",
            "goal": "Test goal"
            # Missing name
        }
        
        with pytest.raises(ValueError):
            await agent_manager.create_agent(invalid_data)
        
        # Test invalid temperature
        invalid_data = {
            "name": "Test Agent",
            "description": "Test description",
            "goal": "Test goal",
            "temperature": 2.0  # Invalid temperature
        }
        
        with pytest.raises(ValueError):
            await agent_manager.create_agent(invalid_data)
        
        # Test invalid max_tokens
        invalid_data = {
            "name": "Test Agent",
            "description": "Test description",
            "goal": "Test goal",
            "max_tokens": -1  # Invalid max_tokens
        }
        
        with pytest.raises(ValueError):
            await agent_manager.create_agent(invalid_data)
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_creation(self, agent_manager, sample_agent_data):
        """Test concurrent agent creation"""
        import asyncio
        
        async def create_agent(index):
            data = sample_agent_data.copy()
            data["name"] = f"Concurrent Agent {index}"
            return await agent_manager.create_agent(data)
        
        # Create agents concurrently
        tasks = [create_agent(i) for i in range(5)]
        agent_ids = await asyncio.gather(*tasks)
        
        # Verify all agents were created
        assert len(agent_ids) == 5
        assert all(agent_id is not None for agent_id in agent_ids)
        
        # Verify all agents exist
        for agent_id in agent_ids:
            agent = await agent_manager.get_agent(agent_id)
            assert agent is not None
    
    @pytest.mark.asyncio
    async def test_agent_lifecycle(self, agent_manager, sample_agent_data):
        """Test complete agent lifecycle"""
        # Create agent
        agent_id = await agent_manager.create_agent(sample_agent_data)
        assert agent_id is not None
        
        # Verify agent exists
        agent = await agent_manager.get_agent(agent_id)
        assert agent is not None
        assert agent.name == sample_agent_data["name"]
        
        # Update agent
        updates = {"name": "Updated Agent"}
        success = await agent_manager.update_agent(agent_id, updates)
        assert success is True
        
        # Verify update
        agent = await agent_manager.get_agent(agent_id)
        assert agent.name == "Updated Agent"
        
        # Execute agent
        execution_id = await agent_manager.execute_agent(agent_id, "Test task", "test_user")
        assert execution_id is not None
        
        # Verify execution
        execution = await agent_manager.get_execution(execution_id)
        assert execution is not None
        assert execution.agent_id == agent_id
        
        # Delete agent
        success = await agent_manager.delete_agent(agent_id)
        assert success is True
        
        # Verify agent was deleted
        agent = await agent_manager.get_agent(agent_id)
        assert agent is None