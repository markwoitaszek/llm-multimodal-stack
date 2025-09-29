"""
Global pytest configuration and fixtures for LLM Multimodal Stack
"""
import asyncio
import os
import tempfile
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import AsyncGenerator, Generator
import httpx
import numpy as np
from PIL import Image
import json

# Test configuration
TEST_CONFIG = {
    "database_url": "postgresql://test:test@localhost:5432/test_multimodal",
    "redis_url": "redis://localhost:6379/1",
    "qdrant_url": "http://localhost:6333",
    "minio_url": "http://localhost:9000",
    "minio_access_key": "test_access_key",
    "minio_secret_key": "test_secret_key",
    "minio_bucket": "test-bucket",
    "model_cache_dir": "/tmp/test_models",
    "test_data_dir": "/tmp/test_data"
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """Test configuration"""
    return TEST_CONFIG.copy()

@pytest.fixture
def temp_dir():
    """Temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def mock_image():
    """Create a mock PIL Image for testing"""
    return Image.new('RGB', (224, 224), color='red')

@pytest.fixture
def mock_embedding():
    """Create a mock embedding vector"""
    return np.random.rand(512).astype(np.float32)

@pytest.fixture
def mock_text():
    """Sample text for testing"""
    return "This is a test document for multimodal processing."

@pytest.fixture
def mock_audio_data():
    """Mock audio data for testing"""
    return np.random.rand(16000).astype(np.float32)  # 1 second of audio at 16kHz

@pytest.fixture
def mock_video_data():
    """Mock video data for testing"""
    return np.random.randint(0, 255, (30, 224, 224, 3), dtype=np.uint8)  # 30 frames

@pytest.fixture
def mock_database_manager():
    """Mock database manager"""
    mock_db = AsyncMock()
    mock_db.initialize = AsyncMock()
    mock_db.close = AsyncMock()
    mock_db.execute_query = AsyncMock(return_value=[])
    mock_db.insert_record = AsyncMock(return_value=1)
    mock_db.update_record = AsyncMock(return_value=True)
    mock_db.delete_record = AsyncMock(return_value=True)
    return mock_db

@pytest.fixture
def mock_storage_manager():
    """Mock storage manager"""
    mock_storage = AsyncMock()
    mock_storage.initialize = AsyncMock()
    mock_storage.upload_file = AsyncMock(return_value="test_file_url")
    mock_storage.download_file = AsyncMock(return_value=b"test_file_content")
    mock_storage.delete_file = AsyncMock(return_value=True)
    mock_storage.list_files = AsyncMock(return_value=["file1.jpg", "file2.mp4"])
    return mock_storage

@pytest.fixture
def mock_vector_store():
    """Mock vector store manager"""
    mock_vector = AsyncMock()
    mock_vector.initialize = AsyncMock()
    mock_vector.upsert_vectors = AsyncMock(return_value=True)
    mock_vector.search_vectors = AsyncMock(return_value=[])
    mock_vector.delete_vectors = AsyncMock(return_value=True)
    return mock_vector

@pytest.fixture
def mock_model_manager():
    """Mock model manager"""
    mock_models = AsyncMock()
    mock_models.load_models = AsyncMock()
    mock_models.get_model = Mock(return_value=Mock())
    mock_models.get_processor = Mock(return_value=Mock())
    mock_models.cleanup = AsyncMock()
    return mock_models

@pytest.fixture
def mock_http_client():
    """Mock HTTP client for API testing"""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock()
    mock_client.post = AsyncMock()
    mock_client.put = AsyncMock()
    mock_client.delete = AsyncMock()
    return mock_client

@pytest.fixture
def test_api_response():
    """Mock API response"""
    return {
        "status": "success",
        "data": {"test": "data"},
        "message": "Test response"
    }

@pytest.fixture
def mock_agent_manager():
    """Mock agent manager"""
    mock_agent = AsyncMock()
    mock_agent.create_agent = AsyncMock(return_value="test_agent_id")
    mock_agent.get_agent = AsyncMock(return_value={"id": "test_agent_id", "name": "Test Agent"})
    mock_agent.execute_agent = AsyncMock(return_value={"success": True, "result": "Test result"})
    mock_agent.delete_agent = AsyncMock(return_value=True)
    mock_agent.list_agents = AsyncMock(return_value=[])
    return mock_agent

@pytest.fixture
def mock_retrieval_engine():
    """Mock retrieval engine"""
    mock_retrieval = AsyncMock()
    mock_retrieval.search_content = AsyncMock(return_value=[])
    mock_retrieval.create_context_bundle = AsyncMock(return_value={"context": "test context"})
    mock_retrieval.index_content = AsyncMock(return_value=True)
    return mock_retrieval

@pytest.fixture
def test_processing_request():
    """Test processing request data"""
    return {
        "content_type": "text",
        "content": "Test content for processing",
        "metadata": {"source": "test", "timestamp": "2024-01-01T00:00:00Z"}
    }

@pytest.fixture
def test_processing_result():
    """Test processing result data"""
    return {
        "content_id": "test_content_id",
        "embeddings": np.random.rand(512).tolist(),
        "metadata": {"processed_at": "2024-01-01T00:00:00Z"},
        "success": True
    }

# Performance testing fixtures
@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing"""
    return {
        "api_response_time_ms": 1000,
        "model_inference_time_ms": 5000,
        "database_query_time_ms": 100,
        "vector_search_time_ms": 200,
        "file_upload_time_ms": 2000
    }

# Integration testing fixtures
@pytest.fixture
async def test_services():
    """Mock services for integration testing"""
    services = {
        "multimodal_worker": {
            "url": "http://localhost:8001",
            "health_endpoint": "/health",
            "process_endpoint": "/process"
        },
        "retrieval_proxy": {
            "url": "http://localhost:8002", 
            "health_endpoint": "/health",
            "search_endpoint": "/search"
        },
        "ai_agents": {
            "url": "http://localhost:8003",
            "health_endpoint": "/health",
            "agents_endpoint": "/api/v1/agents"
        }
    }
    return services

# Test data generators
@pytest.fixture
def generate_test_images():
    """Generate test images"""
    def _generate(count=5):
        images = []
        for i in range(count):
            img = Image.new('RGB', (224, 224), color=(i*50, i*30, i*20))
            images.append(img)
        return images
    return _generate

@pytest.fixture
def generate_test_texts():
    """Generate test texts"""
    def _generate(count=5):
        texts = []
        for i in range(count):
            texts.append(f"Test document {i} with some content for processing.")
        return texts
    return _generate

@pytest.fixture
def generate_test_embeddings():
    """Generate test embeddings"""
    def _generate(count=5, dim=512):
        embeddings = []
        for i in range(count):
            embedding = np.random.rand(dim).astype(np.float32)
            embeddings.append(embedding)
        return embeddings
    return _generate

# Cleanup fixtures
@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_data():
    """Cleanup test data after each test"""
    yield
    # Add cleanup logic here if needed
    pass
