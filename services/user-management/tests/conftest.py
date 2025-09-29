"""
Test configuration and fixtures for User Management Service
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.api import app


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
