"""
Memory System Test Configuration and Fixtures
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
from app.models import (
    MemoryRequest, ConversationRequest, RetrieveRequest, ContextRequest,
    ConsolidateRequest, MemoryType, MemoryImportance
)
from app.database import db_manager, Memory, Conversation
from app.embeddings import cached_embedding_service

# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_memory.db"

# Test settings
TEST_SETTINGS = {
    "database_url": TEST_DATABASE_URL,
    "debug": True,
    "cache_ttl": 60,  # Shorter cache TTL for testing
    "memory_consolidation_threshold": 3,  # Lower threshold for testing
    "max_text_length": 512
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
        await conn.run_sync(Memory.metadata.create_all)
        await conn.run_sync(Conversation.metadata.create_all)
    
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
def sample_memory_request():
    """Sample memory request"""
    return MemoryRequest(
        content="This is a test memory for the memory system",
        memory_type=MemoryType.KNOWLEDGE,
        importance=MemoryImportance.MEDIUM,
        tags=["test", "memory"],
        metadata={"source": "test", "category": "sample"},
        user_id="test_user_1",
        session_id="test_session_1"
    )


@pytest.fixture
def sample_conversation_request():
    """Sample conversation request"""
    return ConversationRequest(
        messages=[
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "What's the weather like?"}
        ],
        user_id="test_user_1",
        session_id="test_session_1",
        context={"topic": "weather"},
        summary="User asked about weather"
    )


@pytest.fixture
def sample_retrieve_request():
    """Sample retrieve request"""
    return RetrieveRequest(
        query="test memory",
        memory_types=[MemoryType.KNOWLEDGE],
        importance_levels=[MemoryImportance.MEDIUM],
        user_id="test_user_1",
        session_id="test_session_1",
        limit=10
    )


@pytest.fixture
def sample_context_request():
    """Sample context request"""
    return ContextRequest(
        query="What did we discuss about weather?",
        user_id="test_user_1",
        session_id="test_session_1",
        context_window=20,
        include_conversations=True,
        include_memories=True
    )


@pytest.fixture
def sample_consolidate_request():
    """Sample consolidate request"""
    return ConsolidateRequest(
        user_id="test_user_1",
        session_id="test_session_1",
        memory_types=[MemoryType.KNOWLEDGE],
        force=False
    )


@pytest.fixture
def sample_embedding():
    """Sample embedding vector"""
    return [0.1] * 384  # 384-dimensional embedding


@pytest.fixture
def multiple_memory_requests():
    """Multiple memory requests for batch testing"""
    return [
        MemoryRequest(
            content=f"Test memory number {i}",
            memory_type=MemoryType.KNOWLEDGE,
            importance=MemoryImportance.MEDIUM,
            tags=["test", "batch"],
            user_id="test_user_1",
            session_id="test_session_1"
        )
        for i in range(1, 6)
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
        f.write("This is a test file for memory system testing")
        f.flush()
        yield f.name
    
    # Cleanup
    try:
        os.unlink(f.name)
    except OSError:
        pass


# Async fixtures
@pytest.fixture
async def async_sample_memory_request():
    """Async sample memory request"""
    return MemoryRequest(
        content="Async test memory content",
        memory_type=MemoryType.CONVERSATION,
        importance=MemoryImportance.HIGH,
        tags=["async", "test"],
        user_id="async_test_user",
        session_id="async_test_session"
    )


@pytest.fixture
async def async_sample_conversation_request():
    """Async sample conversation request"""
    return ConversationRequest(
        messages=[
            {"role": "user", "content": "Async test message"},
            {"role": "assistant", "content": "Async test response"}
        ],
        user_id="async_test_user",
        session_id="async_test_session"
    )


# Performance testing fixtures
@pytest.fixture
def performance_test_memories():
    """Large dataset for performance testing"""
    return [
        MemoryRequest(
            content=f"Performance test memory {i} with some content to test memory system performance",
            memory_type=MemoryType.KNOWLEDGE,
            importance=MemoryImportance.MEDIUM,
            tags=["performance", "test"],
            user_id="perf_test_user",
            session_id="perf_test_session"
        )
        for i in range(100)  # 100 memories for performance testing
    ]


@pytest.fixture
def concurrent_memory_requests():
    """Multiple concurrent memory requests"""
    return [
        MemoryRequest(
            content=f"Concurrent memory {i}",
            memory_type=MemoryType.KNOWLEDGE,
            importance=MemoryImportance.MEDIUM,
            user_id="concurrent_test_user",
            session_id="concurrent_test_session"
        )
        for i in range(10)  # 10 concurrent requests
    ]