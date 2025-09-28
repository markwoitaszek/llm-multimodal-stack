"""
Unit tests for AgentManager in ai-agents service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid
from datetime import datetime

from app.agent_manager import AgentManager
from app.tools import ToolRegistry
from app.memory import MemoryManager


class TestAgentManager:
    """Test cases for AgentManager"""

    @pytest.fixture
    def mock_tool_registry(self):
        """Create mock tool registry"""
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.get_tools = AsyncMock(return_value=[])
        return mock_registry

    @pytest.fixture
    def mock_memory_manager(self):
        """Create mock memory manager"""
        mock_memory = Mock(spec=MemoryManager)
        mock_memory.save_agent_metadata = AsyncMock(return_value=True)
        mock_memory.save_agent_execution = AsyncMock(return_value=True)
        mock_memory.get_agent_metadata = AsyncMock(return_value=None)
        mock_memory.list_user_agents = AsyncMock(return_value=[])
        mock_memory.delete_agent = AsyncMock(return_value=True)
        return mock_memory

    @pytest.fixture
    def agent_manager(self, mock_tool_registry, mock_memory_manager):
        """Create agent manager instance"""
        return AgentManager(mock_tool_registry, mock_memory_manager)

    @pytest.mark.asyncio
    @patch('app.agent_manager.ChatOpenAI')
    async def test_initialize_success(self, mock_chat_openai, agent_manager):
        """Test successful initialization"""
        # Mock ChatOpenAI
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Test initialization
        await agent_manager.initialize()

        # Verify LLM was created
        mock_chat_openai.assert_called_once()
        assert agent_manager.llm == mock_llm

    @pytest.mark.asyncio
    @patch('app.agent_manager.ChatOpenAI')
    async def test_initialize_failure(self, mock_chat_openai, agent_manager):
        """Test initialization failure"""
        # Mock ChatOpenAI to raise exception
        mock_chat_openai.side_effect = Exception("LLM connection failed")

        # Test initialization should raise exception
        with pytest.raises(Exception, match="LLM connection failed"):
            await agent_manager.initialize()

    @pytest.mark.asyncio
    @patch('app.agent_manager.ChatOpenAI')
    @patch('app.agent_manager.create_openai_functions_agent')
    @patch('app.agent_manager.AgentExecutor')
    @patch('app.agent_manager.ConversationBufferWindowMemory')
    async def test_create_agent_success(self, mock_memory, mock_agent_executor, 
                                      mock_create_agent, mock_chat_openai, 
                                      agent_manager, mock_tool_registry, mock_memory_manager):
        """Test successful agent creation"""
        # Setup mocks
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        mock_tools = [Mock(name="test_tool")]
        mock_tool_registry.get_tools.return_value = mock_tools
        
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance
        
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent
        
        mock_executor = Mock()
        mock_agent_executor.return_value = mock_executor

        # Initialize agent manager
        await agent_manager.initialize()

        # Test agent creation
        agent_id = await agent_manager.create_agent(
            agent_name="Test Agent",
            goal="Test goal",
            tools=["test_tool"],
            memory_window=5,
            user_id="test_user"
        )

        # Verify agent was created
        assert agent_id is not None
        assert agent_id in agent_manager.agents
        assert agent_manager.agents[agent_id] == mock_executor

        # Verify tool registry was called
        mock_tool_registry.get_tools.assert_called_once_with(["test_tool"])

        # Verify memory was created
        mock_memory.assert_called_once_with(
            k=5,
            memory_key="chat_history",
            return_messages=True
        )

        # Verify agent was created
        mock_create_agent.assert_called_once_with(
            llm=mock_llm,
            tools=mock_tools,
            prompt=mock_create_agent.call_args[1]['prompt']
        )

        # Verify agent executor was created
        mock_agent_executor.assert_called_once()

        # Verify metadata was saved
        mock_memory_manager.save_agent_metadata.assert_called_once()
        call_args = mock_memory_manager.save_agent_metadata.call_args
        assert call_args[1]['agent_name'] == "Test Agent"
        assert call_args[1]['goal'] == "Test goal"
        assert call_args[1]['tools'] == ["test_tool"]
        assert call_args[1]['user_id'] == "test_user"

    @pytest.mark.asyncio
    @patch('app.agent_manager.ChatOpenAI')
    async def test_create_agent_with_default_parameters(self, mock_chat_openai, 
                                                       agent_manager, mock_tool_registry):
        """Test agent creation with default parameters"""
        # Setup mocks
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        mock_tool_registry.get_tools.return_value = []

        # Initialize agent manager
        await agent_manager.initialize()

        # Test agent creation with minimal parameters
        agent_id = await agent_manager.create_agent(
            agent_name="Test Agent",
            goal="Test goal"
        )

        # Verify agent was created
        assert agent_id is not None
        assert agent_id in agent_manager.agents

        # Verify tool registry was called with None (default)
        mock_tool_registry.get_tools.assert_called_once_with(None)

    @pytest.mark.asyncio
    @patch('app.agent_manager.ChatOpenAI')
    async def test_create_agent_failure(self, mock_chat_openai, agent_manager):
        """Test agent creation failure"""
        # Setup mocks
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Initialize agent manager
        await agent_manager.initialize()

        # Mock tool registry to raise exception
        agent_manager.tool_registry.get_tools.side_effect = Exception("Tool registry failed")

        # Test agent creation should raise exception
        with pytest.raises(Exception, match="Tool registry failed"):
            await agent_manager.create_agent(
                agent_name="Test Agent",
                goal="Test goal"
            )

    @pytest.mark.asyncio
    async def test_execute_agent_success(self, agent_manager, mock_memory_manager):
        """Test successful agent execution"""
        # Setup agent
        agent_id = str(uuid.uuid4())
        mock_executor = Mock()
        mock_executor.ainvoke = AsyncMock(return_value={
            "output": "Task completed successfully",
            "intermediate_steps": [{"action": "test_action", "observation": "test_observation"}]
        })
        agent_manager.agents[agent_id] = mock_executor

        # Test agent execution
        result = await agent_manager.execute_agent(
            agent_id=agent_id,
            task="Test task",
            user_id="test_user"
        )

        # Verify execution result
        assert result["agent_id"] == agent_id
        assert result["task"] == "Test task"
        assert result["result"] == "Task completed successfully"
        assert result["success"] is True
        assert result["intermediate_steps"] == [{"action": "test_action", "observation": "test_observation"}]
        assert "execution_time_ms" in result
        assert "timestamp" in result

        # Verify agent was called
        mock_executor.ainvoke.assert_called_once_with({"input": "Test task"})

        # Verify execution was saved
        mock_memory_manager.save_agent_execution.assert_called_once()
        call_args = mock_memory_manager.save_agent_execution.call_args
        assert call_args[1]['agent_id'] == agent_id
        assert call_args[1]['task'] == "Test task"
        assert call_args[1]['user_id'] == "test_user"
        assert call_args[1]['success'] is True

    @pytest.mark.asyncio
    async def test_execute_agent_not_found(self, agent_manager):
        """Test agent execution with non-existent agent"""
        # Test execution with non-existent agent
        result = await agent_manager.execute_agent(
            agent_id="non-existent-agent",
            task="Test task"
        )

        # Verify error result
        assert result["agent_id"] == "non-existent-agent"
        assert result["task"] == "Test task"
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"]
        assert "execution_time_ms" in result

    @pytest.mark.asyncio
    async def test_execute_agent_execution_failure(self, agent_manager, mock_memory_manager):
        """Test agent execution failure"""
        # Setup agent
        agent_id = str(uuid.uuid4())
        mock_executor = Mock()
        mock_executor.ainvoke = AsyncMock(side_effect=Exception("Execution failed"))
        agent_manager.agents[agent_id] = mock_executor

        # Test agent execution
        result = await agent_manager.execute_agent(
            agent_id=agent_id,
            task="Test task",
            user_id="test_user"
        )

        # Verify error result
        assert result["agent_id"] == agent_id
        assert result["task"] == "Test task"
        assert result["success"] is False
        assert result["error"] == "Execution failed"
        assert "execution_time_ms" in result

        # Verify failed execution was saved
        mock_memory_manager.save_agent_execution.assert_called_once()
        call_args = mock_memory_manager.save_agent_execution.call_args
        assert call_args[1]['success'] is False

    @pytest.mark.asyncio
    async def test_get_agent_info_success(self, agent_manager, mock_memory_manager):
        """Test successful agent info retrieval"""
        # Setup agent
        agent_id = str(uuid.uuid4())
        mock_executor = Mock()
        agent_manager.agents[agent_id] = mock_executor

        # Mock metadata
        mock_metadata = {
            "agent_name": "Test Agent",
            "goal": "Test goal",
            "tools": ["test_tool"],
            "created_at": datetime.utcnow()
        }
        mock_memory_manager.get_agent_metadata.return_value = mock_metadata

        # Test agent info retrieval
        info = await agent_manager.get_agent_info(agent_id)

        # Verify agent info
        assert info["agent_id"] == agent_id
        assert info["name"] == "Test Agent"
        assert info["goal"] == "Test goal"
        assert info["tools"] == ["test_tool"]
        assert info["status"] == "active"

        # Verify memory manager was called
        mock_memory_manager.get_agent_metadata.assert_called_once_with(agent_id)

    @pytest.mark.asyncio
    async def test_get_agent_info_not_found(self, agent_manager, mock_memory_manager):
        """Test agent info retrieval for non-existent agent"""
        # Mock metadata not found
        mock_memory_manager.get_agent_metadata.return_value = None

        # Test agent info retrieval
        info = await agent_manager.get_agent_info("non-existent-agent")

        # Verify no info returned
        assert info is None

    @pytest.mark.asyncio
    async def test_get_agent_info_inactive(self, agent_manager, mock_memory_manager):
        """Test agent info retrieval for inactive agent"""
        # Mock metadata
        mock_metadata = {
            "agent_name": "Test Agent",
            "goal": "Test goal",
            "tools": ["test_tool"],
            "created_at": datetime.utcnow()
        }
        mock_memory_manager.get_agent_metadata.return_value = mock_metadata

        # Test agent info retrieval (agent not in active agents)
        info = await agent_manager.get_agent_info("inactive-agent")

        # Verify agent info with inactive status
        assert info["agent_id"] == "inactive-agent"
        assert info["status"] == "inactive"

    @pytest.mark.asyncio
    async def test_list_agents_success(self, agent_manager, mock_memory_manager):
        """Test successful agent listing"""
        # Mock user agents
        mock_agents = [
            {
                "agent_id": "agent1",
                "agent_name": "Agent 1",
                "goal": "Goal 1",
                "tools": ["tool1"],
                "created_at": datetime.utcnow(),
                "status": "active"
            },
            {
                "agent_id": "agent2",
                "agent_name": "Agent 2",
                "goal": "Goal 2",
                "tools": ["tool2"],
                "created_at": datetime.utcnow(),
                "status": "active"
            }
        ]
        mock_memory_manager.list_user_agents.return_value = mock_agents

        # Mock get_agent_info for each agent
        async def mock_get_agent_info(agent_id):
            for agent in mock_agents:
                if agent["agent_id"] == agent_id:
                    return {
                        "agent_id": agent["agent_id"],
                        "name": agent["agent_name"],
                        "goal": agent["goal"],
                        "tools": agent["tools"],
                        "created_at": agent["created_at"],
                        "status": "active"
                    }
            return None

        agent_manager.get_agent_info = mock_get_agent_info

        # Test agent listing
        agents = await agent_manager.list_agents("test_user")

        # Verify agents list
        assert len(agents) == 2
        assert agents[0]["agent_id"] == "agent1"
        assert agents[1]["agent_id"] == "agent2"

        # Verify memory manager was called
        mock_memory_manager.list_user_agents.assert_called_once_with("test_user")

    @pytest.mark.asyncio
    async def test_list_agents_empty(self, agent_manager, mock_memory_manager):
        """Test agent listing with no agents"""
        # Mock empty agents list
        mock_memory_manager.list_user_agents.return_value = []

        # Test agent listing
        agents = await agent_manager.list_agents("test_user")

        # Verify empty list
        assert agents == []

    @pytest.mark.asyncio
    async def test_list_agents_failure(self, agent_manager, mock_memory_manager):
        """Test agent listing failure"""
        # Mock memory manager to raise exception
        mock_memory_manager.list_user_agents.side_effect = Exception("Database error")

        # Test agent listing should return empty list
        agents = await agent_manager.list_agents("test_user")

        # Verify empty list returned
        assert agents == []

    @pytest.mark.asyncio
    async def test_delete_agent_success(self, agent_manager, mock_memory_manager):
        """Test successful agent deletion"""
        # Setup agent
        agent_id = str(uuid.uuid4())
        mock_executor = Mock()
        agent_manager.agents[agent_id] = mock_executor

        # Test agent deletion
        result = await agent_manager.delete_agent(agent_id, "test_user")

        # Verify deletion result
        assert result is True
        assert agent_id not in agent_manager.agents

        # Verify memory manager was called
        mock_memory_manager.delete_agent.assert_called_once_with(agent_id, "test_user")

    @pytest.mark.asyncio
    async def test_delete_agent_not_in_memory(self, agent_manager, mock_memory_manager):
        """Test agent deletion when agent not in memory"""
        # Test deletion of non-existent agent
        result = await agent_manager.delete_agent("non-existent-agent", "test_user")

        # Verify deletion result
        assert result is True

        # Verify memory manager was called
        mock_memory_manager.delete_agent.assert_called_once_with("non-existent-agent", "test_user")

    @pytest.mark.asyncio
    async def test_delete_agent_failure(self, agent_manager, mock_memory_manager):
        """Test agent deletion failure"""
        # Mock memory manager to raise exception
        mock_memory_manager.delete_agent.side_effect = Exception("Database error")

        # Test agent deletion should return False
        result = await agent_manager.delete_agent("test-agent", "test_user")

        # Verify deletion failed
        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup(self, agent_manager):
        """Test agent manager cleanup"""
        # Setup agents
        agent_id1 = str(uuid.uuid4())
        agent_id2 = str(uuid.uuid4())
        agent_manager.agents[agent_id1] = Mock()
        agent_manager.agents[agent_id2] = Mock()

        # Test cleanup
        await agent_manager.cleanup()

        # Verify agents were cleared
        assert len(agent_manager.agents) == 0

    @pytest.mark.asyncio
    @patch('app.agent_manager.ChatOpenAI')
    async def test_agent_execution_with_timing(self, mock_chat_openai, agent_manager, mock_memory_manager):
        """Test agent execution timing measurement"""
        # Setup mocks
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Initialize agent manager
        await agent_manager.initialize()

        # Setup agent
        agent_id = str(uuid.uuid4())
        mock_executor = Mock()
        mock_executor.ainvoke = AsyncMock(return_value={"output": "Task completed"})
        agent_manager.agents[agent_id] = mock_executor

        # Test agent execution
        result = await agent_manager.execute_agent(
            agent_id=agent_id,
            task="Test task"
        )

        # Verify timing was measured
        assert "execution_time_ms" in result
        assert isinstance(result["execution_time_ms"], int)
        assert result["execution_time_ms"] >= 0

        # Verify execution was saved with timing
        mock_memory_manager.save_agent_execution.assert_called_once()
        call_args = mock_memory_manager.save_agent_execution.call_args
        assert call_args[1]['execution_time_ms'] == result["execution_time_ms"]

    @pytest.mark.asyncio
    @patch('app.agent_manager.ChatOpenAI')
    async def test_agent_creation_with_custom_memory_window(self, mock_chat_openai, 
                                                          agent_manager, mock_tool_registry):
        """Test agent creation with custom memory window"""
        # Setup mocks
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        mock_tool_registry.get_tools.return_value = []

        # Initialize agent manager
        await agent_manager.initialize()

        # Test agent creation with custom memory window
        agent_id = await agent_manager.create_agent(
            agent_name="Test Agent",
            goal="Test goal",
            memory_window=20
        )

        # Verify agent was created
        assert agent_id is not None
        assert agent_id in agent_manager.agents

    @pytest.mark.asyncio
    @patch('app.agent_manager.ChatOpenAI')
    async def test_agent_creation_with_specific_tools(self, mock_chat_openai, 
                                                    agent_manager, mock_tool_registry):
        """Test agent creation with specific tools"""
        # Setup mocks
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        mock_tools = [Mock(name="tool1"), Mock(name="tool2")]
        mock_tool_registry.get_tools.return_value = mock_tools

        # Initialize agent manager
        await agent_manager.initialize()

        # Test agent creation with specific tools
        agent_id = await agent_manager.create_agent(
            agent_name="Test Agent",
            goal="Test goal",
            tools=["tool1", "tool2"]
        )

        # Verify agent was created
        assert agent_id is not None
        assert agent_id in agent_manager.agents

        # Verify specific tools were requested
        mock_tool_registry.get_tools.assert_called_once_with(["tool1", "tool2"])