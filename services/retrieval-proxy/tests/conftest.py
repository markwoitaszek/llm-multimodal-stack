"""
Retrieval Proxy specific pytest configuration and fixtures
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
import numpy as np
from typing import List, Dict, Any

@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client"""
    mock_client = AsyncMock()
    mock_client.upsert = AsyncMock(return_value=True)
    mock_client.search = AsyncMock(return_value=[])
    mock_client.delete = AsyncMock(return_value=True)
    mock_client.get_collections = AsyncMock(return_value={"collections": []})
    return mock_client

@pytest.fixture
def mock_vector_search_result():
    """Mock vector search result"""
    return [
        {
            "id": "doc_1",
            "score": 0.95,
            "payload": {
                "content_type": "text",
                "content": "Test document 1",
                "metadata": {"source": "test"}
            }
        },
        {
            "id": "doc_2", 
            "score": 0.87,
            "payload": {
                "content_type": "image",
                "content": "Test image 2",
                "metadata": {"source": "test"}
            }
        }
    ]

@pytest.fixture
def mock_context_bundle():
    """Mock context bundle"""
    return {
        "query": "test query",
        "results": [
            {
                "content_id": "doc_1",
                "content_type": "text",
                "content": "Test document 1",
                "score": 0.95,
                "metadata": {"source": "test"}
            },
            {
                "content_id": "doc_2",
                "content_type": "image", 
                "content": "Test image 2",
                "score": 0.87,
                "metadata": {"source": "test"}
            }
        ],
        "total_results": 2,
        "search_time_ms": 50
    }

@pytest.fixture
def test_search_request():
    """Test search request"""
    return {
        "query": "test search query",
        "content_types": ["text", "image"],
        "limit": 10,
        "threshold": 0.7,
        "filters": {"source": "test"}
    }

@pytest.fixture
def test_index_request():
    """Test index request"""
    return {
        "content_id": "test_content_123",
        "content_type": "text",
        "content": "Test content for indexing",
        "embeddings": np.random.rand(512).tolist(),
        "metadata": {
            "source": "test",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }
