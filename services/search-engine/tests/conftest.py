"""
Search Engine Test Configuration and Fixtures
"""
import pytest
import asyncio
import tempfile
import os
from typing import AsyncGenerator, Dict, Any, List
from datetime import datetime
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.api import app
from app.config import settings
from app.models import SearchRequest, IndexRequest, SearchType, ContentType
from app.database import db_manager, SearchContent
from app.vector_store import vector_store
from app.embeddings import cached_embedding_service

# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Test settings
TEST_SETTINGS = {
    "database_url": TEST_DATABASE_URL,
    "redis_url": "redis://localhost:6379/1",  # Use different Redis DB for testing
    "qdrant_url": "http://localhost:6333",
    "qdrant_collection_name": "test_search_embeddings",
    "debug": True,
    "cache_ttl": 60,  # Shorter cache TTL for testing
    "result_cache_size": 100
}

# Override settings for testing
settings.__dict__.update(TEST_SETTINGS)

# Test base for database
TestBase = declarative_base()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SearchContent.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def initialized_db_manager(test_engine):
    """Initialize database manager for testing"""
    # Override the engine in db_manager
    db_manager.engine = test_engine
    db_manager.session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Initialize the database manager
    await db_manager.initialize()
    
    yield db_manager
    
    # Cleanup
    await db_manager.close()


@pytest.fixture
def test_client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_search_request():
    """Sample search request"""
    return SearchRequest(
        query="test search query",
        search_type=SearchType.HYBRID,
        limit=10,
        content_types=[ContentType.TEXT]
    )


@pytest.fixture
def sample_index_request():
    """Sample index request"""
    return IndexRequest(
        content_id="test_content_1",
        content="This is a test document for search indexing",
        content_type=ContentType.TEXT,
        metadata={"source": "test", "category": "sample"}
    )


@pytest.fixture
def sample_embedding():
    """Sample embedding vector"""
    return [0.1] * 384  # 384-dimensional embedding


@pytest.fixture
def sample_content_data():
    """Sample content data for testing"""
    return {
        "id": "test_content_1",
        "content": "This is a test document for search indexing",
        "content_type": "text",
        "metadata": {"source": "test", "category": "sample"},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def multiple_content_data():
    """Multiple content data for batch testing"""
    return [
        {
            "id": f"test_content_{i}",
            "content": f"This is test document number {i}",
            "content_type": "text",
            "metadata": {"source": "test", "category": "sample", "number": i},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        for i in range(1, 6)
    ]


@pytest.fixture
def mock_vector_results():
    """Mock vector search results"""
    return [
        {
            "id": "test_content_1",
            "score": 0.95,
            "metadata": {"content_type": "text", "source": "test"}
        },
        {
            "id": "test_content_2",
            "score": 0.87,
            "metadata": {"content_type": "text", "source": "test"}
        }
    ]


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service"""
    class MockEmbeddingService:
        def __init__(self):
            self.embedding_dimension = 384
        
        async def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
            # Generate deterministic embedding based on text hash
            import hashlib
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            # Create embedding with values based on hash
            embedding = []
            for i in range(self.embedding_dimension):
                val = (hash_val + i) % 1000 / 1000.0
                embedding.append(val)
            return embedding
        
        async def generate_embeddings_batch(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
            embeddings = []
            for text in texts:
                embedding = await self.generate_embedding(text, use_cache)
                embeddings.append(embedding)
            return embeddings
        
        async def health_check(self) -> bool:
            return True
    
    return MockEmbeddingService()


@pytest.fixture
def mock_vector_store():
    """Mock vector store"""
    class MockVectorStore:
        def __init__(self):
            self.storage = {}
        
        async def initialize(self):
            pass
        
        async def close(self):
            pass
        
        async def upsert_embedding(self, content_id: str, embedding: List[float], metadata: Dict[str, Any] = None) -> bool:
            self.storage[content_id] = {
                "embedding": embedding,
                "metadata": metadata or {}
            }
            return True
        
        async def search_similar(self, query_embedding: List[float], limit: int = 10, 
                               score_threshold: float = 0.0, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
            results = []
            for content_id, data in self.storage.items():
                # Simple similarity calculation (dot product)
                similarity = sum(a * b for a, b in zip(query_embedding, data["embedding"]))
                if similarity >= score_threshold:
                    results.append({
                        "id": content_id,
                        "score": similarity,
                        "metadata": data["metadata"]
                    })
            
            # Sort by score and limit
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:limit]
        
        async def delete_embedding(self, content_id: str) -> bool:
            if content_id in self.storage:
                del self.storage[content_id]
                return True
            return False
        
        async def health_check(self) -> bool:
            return True
        
        async def get_collection_info(self) -> Dict[str, Any]:
            return {
                "points_count": len(self.storage),
                "status": "green"
            }
    
    return MockVectorStore()


@pytest.fixture
async def clean_test_environment():
    """Clean test environment"""
    # Clear any existing test data
    yield
    
    # Cleanup after tests
    if hasattr(db_manager, 'engine') and db_manager.engine:
        await db_manager.close()
    
    # Clear caches
    if hasattr(cached_embedding_service, 'clear_cache'):
        cached_embedding_service.clear_cache()


@pytest.fixture
async def async_test_client():
    """Create async test client for testing async endpoints"""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def temp_file():
    """Temporary file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("This is a test file for search engine testing")
        f.flush()
        yield f.name
    
    # Cleanup
    try:
        os.unlink(f.name)
    except OSError:
        pass


# Async fixtures
@pytest.fixture
async def async_sample_search_request():
    """Async sample search request"""
    return SearchRequest(
        query="async test search query",
        search_type=SearchType.SEMANTIC,
        limit=5
    )


@pytest.fixture
async def async_sample_index_request():
    """Async sample index request"""
    return IndexRequest(
        content_id=str(uuid.uuid4()),
        content="This is an async test document",
        content_type=ContentType.TEXT,
        metadata={"async": True, "test": True}
    )


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Large dataset for performance testing"""
    return [
        {
            "id": f"perf_test_{i}",
            "content": f"Performance test document number {i} with some content to search through",
            "content_type": "text",
            "metadata": {"test_type": "performance", "index": i}
        }
        for i in range(1000)  # 1000 documents for performance testing
    ]


@pytest.fixture
def concurrent_search_requests():
    """Multiple concurrent search requests"""
    return [
        SearchRequest(
            query=f"concurrent search {i}",
            search_type=SearchType.HYBRID,
            limit=10
        )
        for i in range(10)  # 10 concurrent searches
    ]