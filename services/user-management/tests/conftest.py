"""
Test configuration and fixtures for User Management Service
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.api import app
from app.database import db_manager

# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_user.db"

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
        await conn.run_sync(db_manager.Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncSession:
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
    """Create test client for API testing"""
    return TestClient(app)


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "role": "user",
        "tenant_id": "default"
    }


@pytest.fixture
def sample_login_data():
    """Sample login data for testing"""
    return {
        "username": "testuser",
        "password": "testpassword123"
    }


@pytest.fixture
def mock_user():
    """Mock user object for testing"""
    return {
        "id": "test_user_id",
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user",
        "status": "active",
        "tenant_id": "default",
        "auth_provider": "local",
        "email_verified": True,
        "phone_verified": False,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
        "user_metadata": {}
    }


@pytest.fixture
def mock_tokens():
    """Mock JWT tokens for testing"""
    return {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "token_type": "bearer",
        "expires_in": 3600
    }


@pytest.fixture
def mock_session():
    """Mock user session for testing"""
    return {
        "session_id": "mock_session_id",
        "user_id": "test_user_id",
        "tenant_id": "default",
        "created_at": "2023-01-01T00:00:00Z",
        "expires_at": "2023-01-01T01:00:00Z"
    }


@pytest.fixture
async def async_test_client():
    """Create async test client for testing async endpoints"""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def clean_test_environment():
    """Clean test environment"""
    # Clear any existing test data
    yield
    
    # Cleanup after tests
    if hasattr(db_manager, 'engine') and db_manager.engine:
        await db_manager.close()
