"""
AI Agents specific pytest configuration and fixtures
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
from typing import Dict, List, Any

@pytest.fixture
def mock_agent():
    """Mock agent instance"""
    return {
        "id": "test_agent_123",
        "name": "Test Agent",
        "goal": "Test agent for unit testing",
        "tools": ["search_content", "generate_text"],
        "memory_window": 10,
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

@pytest.fixture
def mock_agent_template():
    """Mock agent template"""
    return {
        "name": "research_assistant",
        "display_name": "Research Assistant",
        "description": "An agent specialized in research tasks",
        "goal": "Help users with research tasks and information gathering",
        "tools": ["search_content", "web_search", "generate_text"],
        "memory_window": 20,
        "system_prompt": "You are a helpful research assistant...",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 1000
        }
    }

@pytest.fixture
def mock_agent_execution():
    """Mock agent execution result"""
    return {
        "agent_id": "test_agent_123",
        "task": "Test task execution",
        "result": "Test execution result",
        "success": True,
        "execution_time_ms": 150,
        "tools_used": ["search_content"],
        "timestamp": datetime.now().isoformat()
    }

@pytest.fixture
def mock_agent_memory():
    """Mock agent memory entry"""
    return {
        "agent_id": "test_agent_123",
        "conversation_id": "conv_123",
        "user_input": "Hello, can you help me?",
        "agent_response": "Of course! I'd be happy to help you.",
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "tools_used": ["generate_text"],
            "execution_time_ms": 100
        }
    }

@pytest.fixture
def mock_tool_result():
    """Mock tool execution result"""
    return {
        "tool_name": "search_content",
        "success": True,
        "result": "Search results for the query",
        "execution_time_ms": 50,
        "metadata": {
            "query": "test query",
            "results_count": 5
        }
    }

@pytest.fixture
def test_agent_creation_request():
    """Test agent creation request"""
    return {
        "name": "Test Agent",
        "goal": "Test agent for unit testing",
        "tools": ["search_content", "generate_text"],
        "memory_window": 10,
        "system_prompt": "You are a test agent.",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 1000
        }
    }

@pytest.fixture
def test_agent_execution_request():
    """Test agent execution request"""
    return {
        "task": "Test task for agent execution",
        "context": {
            "user_id": "test_user",
            "session_id": "test_session"
        },
        "parameters": {
            "max_iterations": 5,
            "timeout_seconds": 30
        }
    }
