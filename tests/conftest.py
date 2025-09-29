"""
Global test configuration and fixtures
"""

import asyncio
import os
import pytest
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["LOG_LEVEL"] = "DEBUG"

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db() -> AsyncGenerator[MagicMock, None]:
    """Test database fixture"""
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    yield db

@pytest.fixture
async def test_redis() -> AsyncGenerator[MagicMock, None]:
    """Test Redis fixture"""
    redis = MagicMock()
    redis.get = AsyncMock()
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.exists = AsyncMock()
    redis.expire = AsyncMock()
    yield redis

@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Temporary directory fixture"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def mock_ai_agents_service() -> MagicMock:
    """Mock AI Agents service"""
    service = MagicMock()
    service.create_agent = AsyncMock()
    service.get_agent = AsyncMock()
    service.update_agent = AsyncMock()
    service.delete_agent = AsyncMock()
    service.execute_agent = AsyncMock()
    return service

@pytest.fixture
def mock_ide_bridge_service() -> MagicMock:
    """Mock IDE Bridge service"""
    service = MagicMock()
    service.analyze_code = AsyncMock()
    service.get_completions = AsyncMock()
    service.get_hover = AsyncMock()
    service.get_definition = AsyncMock()
    return service

@pytest.fixture
def mock_protocol_integration_service() -> MagicMock:
    """Mock Protocol Integration service"""
    service = MagicMock()
    service.translate_protocol = AsyncMock()
    service.get_protocol_status = AsyncMock()
    service.start_server = AsyncMock()
    service.stop_server = AsyncMock()
    return service

@pytest.fixture
def mock_realtime_collaboration_service() -> MagicMock:
    """Mock Real-Time Collaboration service"""
    service = MagicMock()
    service.broadcast_message = AsyncMock()
    service.get_connections = AsyncMock()
    service.get_workspaces = AsyncMock()
    return service

@pytest.fixture
def mock_n8n_service() -> MagicMock:
    """Mock n8n service"""
    service = MagicMock()
    service.create_workflow = AsyncMock()
    service.execute_workflow = AsyncMock()
    service.get_workflow_status = AsyncMock()
    return service

@pytest.fixture
def sample_agent_data() -> dict:
    """Sample agent data for testing"""
    return {
        "name": "Test Agent",
        "description": "A test agent for unit testing",
        "goal": "Test agent functionality",
        "tools": ["search_content", "generate_text"],
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1000
    }

@pytest.fixture
def sample_workspace_data() -> dict:
    """Sample workspace data for testing"""
    return {
        "name": "Test Workspace",
        "description": "A test workspace for unit testing",
        "created_by": "test_user",
        "users": ["test_user"],
        "agents": ["test_agent"]
    }

@pytest.fixture
def sample_protocol_data() -> dict:
    """Sample protocol data for testing"""
    return {
        "id": "test-protocol",
        "name": "Test Protocol",
        "version": "1.0.0",
        "category": "test",
        "description": "A test protocol",
        "schema": {
            "methods": ["test_method"],
            "notifications": ["test_notification"]
        },
        "capabilities": ["test_capability"]
    }

@pytest.fixture
def sample_websocket_message() -> dict:
    """Sample WebSocket message for testing"""
    return {
        "type": "test_message",
        "data": {
            "message": "Test message",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    }

@pytest.fixture
def sample_execution_data() -> dict:
    """Sample execution data for testing"""
    return {
        "agent_id": "test_agent",
        "task": "Test task",
        "user_id": "test_user",
        "status": "running",
        "progress": 50,
        "current_step": "Processing",
        "started_at": "2024-01-01T12:00:00Z"
    }

@pytest.fixture
def mock_websocket() -> MagicMock:
    """Mock WebSocket connection"""
    websocket = MagicMock()
    websocket.send_text = AsyncMock()
    websocket.receive_text = AsyncMock()
    websocket.close = AsyncMock()
    websocket.accept = AsyncMock()
    return websocket

@pytest.fixture
def mock_http_client() -> MagicMock:
    """Mock HTTP client"""
    client = MagicMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    return client

@pytest.fixture
def mock_jwt_token() -> str:
    """Mock JWT token"""
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidGVzdF91c2VyIiwiaWF0IjoxNjQwOTk1MjAwLCJleHAiOjE2NDEwODE2MDB9.test_signature"

@pytest.fixture
def mock_user_session() -> dict:
    """Mock user session data"""
    return {
        "user_id": "test_user",
        "username": "test_user",
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": ["read", "write"],
        "created_at": "2024-01-01T12:00:00Z",
        "last_activity": "2024-01-01T12:00:00Z"
    }

@pytest.fixture
def mock_rate_limit_config() -> dict:
    """Mock rate limit configuration"""
    return {
        "websocket": {"requests": 100, "window": 60, "burst": 20},
        "api": {"requests": 1000, "window": 3600, "burst": 100},
        "agent_execution": {"requests": 10, "window": 60, "burst": 5}
    }

@pytest.fixture
def mock_message_queue() -> MagicMock:
    """Mock message queue"""
    queue = MagicMock()
    queue.enqueue_message = AsyncMock()
    queue.dequeue_message = AsyncMock()
    queue.process_messages = AsyncMock()
    queue.get_status = AsyncMock()
    return queue

@pytest.fixture
def mock_agent_monitor() -> MagicMock:
    """Mock agent monitor"""
    monitor = MagicMock()
    monitor.start_execution = AsyncMock()
    monitor.update_execution = AsyncMock()
    monitor.complete_execution = AsyncMock()
    monitor.get_agent_status = AsyncMock()
    monitor.subscribe_connection = AsyncMock()
    monitor.unsubscribe_connection = AsyncMock()
    return monitor

@pytest.fixture
def mock_workspace_manager() -> MagicMock:
    """Mock workspace manager"""
    manager = MagicMock()
    manager.create_workspace = AsyncMock()
    manager.get_workspace = AsyncMock()
    manager.join_workspace = AsyncMock()
    manager.leave_workspace = AsyncMock()
    manager.get_workspace_users = AsyncMock()
    return manager

@pytest.fixture
def mock_websocket_manager() -> MagicMock:
    """Mock WebSocket manager"""
    manager = MagicMock()
    manager.add_connection = AsyncMock()
    manager.remove_connection = AsyncMock()
    manager.send_to_connection = AsyncMock()
    manager.broadcast_to_all = AsyncMock()
    manager.broadcast_to_workspace = AsyncMock()
    manager.get_connection_count = AsyncMock()
    return manager

@pytest.fixture
def mock_auth_manager() -> MagicMock:
    """Mock authentication manager"""
    manager = MagicMock()
    manager.create_session = AsyncMock()
    manager.get_session = AsyncMock()
    manager.revoke_session = AsyncMock()
    manager.validate_token = AsyncMock()
    manager.check_permission = AsyncMock()
    manager.check_role = AsyncMock()
    return manager

@pytest.fixture
def mock_rate_limiter() -> MagicMock:
    """Mock rate limiter"""
    limiter = MagicMock()
    limiter.check_rate_limit = AsyncMock()
    limiter.get_rate_limit_status = AsyncMock()
    limiter.reset_rate_limit = AsyncMock()
    limiter.is_blocked = AsyncMock()
    return limiter

@pytest.fixture
def mock_protocol_translator() -> MagicMock:
    """Mock protocol translator"""
    translator = MagicMock()
    translator.translate = AsyncMock()
    translator.get_supported_translations = AsyncMock()
    return translator

@pytest.fixture
def mock_protocol_manager() -> MagicMock:
    """Mock protocol manager"""
    manager = MagicMock()
    manager.add_server = AsyncMock()
    manager.remove_server = AsyncMock()
    manager.start_server = AsyncMock()
    manager.stop_server = AsyncMock()
    manager.get_server_status = AsyncMock()
    manager.get_all_servers = AsyncMock()
    return manager

@pytest.fixture
def mock_protocol_registry() -> MagicMock:
    """Mock protocol registry"""
    registry = MagicMock()
    registry.register_protocol = AsyncMock()
    registry.get_protocol = AsyncMock()
    registry.get_all_protocols = AsyncMock()
    registry.validate_message = AsyncMock()
    registry.get_statistics = AsyncMock()
    return registry

# Test configuration
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # Set test environment variables
    os.environ.update({
        "TEST_ENVIRONMENT": "testing",
        "TEST_DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",
        "TEST_REDIS_URL": "redis://localhost:6379/1",
        "TEST_AI_AGENTS_URL": "http://localhost:3000",
        "TEST_IDE_BRIDGE_URL": "http://localhost:3004",
        "TEST_PROTOCOL_INTEGRATION_URL": "http://localhost:3005",
        "TEST_REALTIME_COLLABORATION_URL": "http://localhost:3006"
    })
    
    yield
    
    # Cleanup after tests
    # Remove test environment variables if needed
    for key in list(os.environ.keys()):
        if key.startswith("TEST_"):
            del os.environ[key]

# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Add slow marker to tests that take more than 1 second
        if "slow" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Add unit marker to tests in unit directory
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to tests in integration directory
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker to tests in performance directory
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Add e2e marker to tests in e2e directory
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)