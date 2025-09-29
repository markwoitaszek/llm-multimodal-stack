"""
User Management API Tests
"""
import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.models import LoginRequest, RegisterRequest, UserRole, UserStatus
from app.api import app


class TestUserManagementAPI:
    """Test User Management API endpoints"""
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint"""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "User Management Service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "dependencies" in data
    
    @patch('app.auth.auth_service.authenticate_user')
    @patch('app.auth.auth_service.create_user_session')
    def test_login_endpoint(self, mock_create_session, mock_authenticate, test_client):
        """Test login endpoint"""
        # Mock authentication
        mock_user = {
            "id": "test_user_id",
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "phone": "+1234567890",
            "role": "user",
            "status": "active",
            "tenant_id": "default",
            "auth_provider": "local",
            "email_verified": True,
            "phone_verified": False,
            "last_login": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": {}
        }
        mock_authenticate.return_value = mock_user
        
        # Mock session creation
        mock_create_session.return_value = ("access_token", "refresh_token", "session_id")
        
        # Test login
        login_request = {
            "username": "testuser",
            "password": "testpassword",
            "remember_me": False
        }
        
        response = test_client.post("/api/v1/auth/login", json=login_request)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
    
    def test_login_endpoint_invalid_credentials(self, test_client):
        """Test login endpoint with invalid credentials"""
        with patch('app.auth.auth_service.authenticate_user') as mock_authenticate:
            mock_authenticate.return_value = None
            
            login_request = {
                "username": "invaliduser",
                "password": "wrongpassword"
            }
            
            response = test_client.post("/api/v1/auth/login", json=login_request)
            assert response.status_code == 401
    
    def test_login_endpoint_invalid_request(self, test_client):
        """Test login endpoint with invalid request"""
        invalid_request = {
            "username": "",  # Empty username
            "password": ""   # Empty password
        }
        
        response = test_client.post("/api/v1/auth/login", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    @patch('app.database.db_manager.get_user_by_username')
    @patch('app.database.db_manager.get_user_by_email')
    @patch('app.database.db_manager.create_user')
    def test_register_endpoint(self, mock_create_user, mock_get_email, mock_get_username, test_client):
        """Test register endpoint"""
        # Mock no existing user
        mock_get_username.return_value = None
        mock_get_email.return_value = None
        
        # Mock user creation
        mock_create_user.return_value = True
        
        # Test registration
        register_request = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "New User",
            "phone": "+1234567890"
        }
        
        response = test_client.post("/api/v1/auth/register", json=register_request)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
    
    def test_register_endpoint_weak_password(self, test_client):
        """Test register endpoint with weak password"""
        register_request = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "weak",  # Weak password
            "full_name": "New User"
        }
        
        response = test_client.post("/api/v1/auth/register", json=register_request)
        assert response.status_code == 400
    
    def test_register_endpoint_existing_username(self, test_client):
        """Test register endpoint with existing username"""
        with patch('app.database.db_manager.get_user_by_username') as mock_get_username:
            mock_existing_user = {
                "id": "existing_user_id",
                "username": "existinguser",
                "email": "existing@example.com"
            }
            mock_get_username.return_value = mock_existing_user
            
            register_request = {
                "username": "existinguser",
                "email": "new@example.com",
                "password": "SecurePass123!"
            }
            
            response = test_client.post("/api/v1/auth/register", json=register_request)
            assert response.status_code == 400
            assert "Username already exists" in response.json()["detail"]
    
    @patch('app.auth.auth_service.refresh_access_token')
    def test_refresh_token_endpoint(self, mock_refresh, test_client):
        """Test refresh token endpoint"""
        # Mock token refresh
        mock_refresh.return_value = ("new_access_token", "session_id")
        
        refresh_request = {
            "refresh_token": "valid_refresh_token"
        }
        
        response = test_client.post("/api/v1/auth/refresh", json=refresh_request)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_token_endpoint_invalid_token(self, test_client):
        """Test refresh token endpoint with invalid token"""
        with patch('app.auth.auth_service.refresh_access_token') as mock_refresh:
            mock_refresh.return_value = None
            
            refresh_request = {
                "refresh_token": "invalid_refresh_token"
            }
            
            response = test_client.post("/api/v1/auth/refresh", json=refresh_request)
            assert response.status_code == 401
    
    @patch('app.auth.auth_service.get_user_from_token')
    def test_get_current_user_endpoint(self, mock_get_user, test_client):
        """Test get current user endpoint"""
        # Mock authenticated user
        mock_user = {
            "id": "test_user_id",
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "phone": "+1234567890",
            "role": "user",
            "status": "active",
            "tenant_id": "default",
            "auth_provider": "local",
            "email_verified": True,
            "phone_verified": False,
            "last_login": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": {}
        }
        mock_get_user.return_value = mock_user
        
        # Test with valid token
        headers = {"Authorization": "Bearer valid_token"}
        response = test_client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    def test_get_current_user_endpoint_no_token(self, test_client):
        """Test get current user endpoint without token"""
        response = test_client.get("/api/v1/users/me")
        assert response.status_code == 403  # No authorization header
    
    def test_get_current_user_endpoint_invalid_token(self, test_client):
        """Test get current user endpoint with invalid token"""
        with patch('app.auth.auth_service.get_user_from_token') as mock_get_user:
            mock_get_user.return_value = None
            
            headers = {"Authorization": "Bearer invalid_token"}
            response = test_client.get("/api/v1/users/me", headers=headers)
            assert response.status_code == 401
    
    @patch('app.auth.auth_service.get_user_from_token')
    @patch('app.database.db_manager.update_user')
    @patch('app.database.db_manager.get_user_by_id')
    def test_update_current_user_endpoint(self, mock_get_user, mock_update_user, mock_get_user_from_token, test_client):
        """Test update current user endpoint"""
        # Mock authenticated user
        mock_user = {
            "id": "test_user_id",
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "phone": "+1234567890",
            "role": "user",
            "status": "active",
            "tenant_id": "default",
            "auth_provider": "local",
            "email_verified": True,
            "phone_verified": False,
            "last_login": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": {}
        }
        mock_get_user_from_token.return_value = mock_user
        
        # Mock user update
        mock_update_user.return_value = True
        
        # Mock get updated user
        updated_user = mock_user.copy()
        updated_user["full_name"] = "Updated User"
        updated_user["phone"] = "+0987654321"
        mock_get_user.return_value = updated_user
        
        # Test update
        update_request = {
            "full_name": "Updated User",
            "phone": "+0987654321",
            "metadata": {"updated": True}
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = test_client.put("/api/v1/users/me", json=update_request, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated User"
        assert data["phone"] == "+0987654321"
    
    @patch('app.database.db_manager.get_user_stats')
    def test_stats_endpoint(self, mock_get_stats, test_client):
        """Test statistics endpoint"""
        # Mock stats
        mock_stats = {
            "total_users": 100,
            "users_by_role": {"user": 90, "admin": 10},
            "users_by_status": {"active": 95, "inactive": 5},
            "login_attempts_last_hour": 25
        }
        mock_get_stats.return_value = mock_stats
        
        with patch('app.database.db_manager.get_tenant_count') as mock_tenant_count:
            mock_tenant_count.return_value = 5
            
            headers = {"Authorization": "Bearer valid_token"}
            response = test_client.get("/api/v1/stats", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["total_users"] == 100
            assert data["total_tenants"] == 5
            assert "users_by_role" in data
            assert "users_by_status" in data


class TestUserManagementAPIErrorHandling:
    """Test error handling in User Management API"""
    
    def test_login_with_database_error(self, test_client):
        """Test login when database is unavailable"""
        with patch('app.auth.auth_service.authenticate_user', side_effect=Exception("Database error")):
            login_request = {
                "username": "testuser",
                "password": "testpassword"
            }
            
            response = test_client.post("/api/v1/auth/login", json=login_request)
            assert response.status_code == 500
    
    def test_register_with_database_error(self, test_client):
        """Test register when database is unavailable"""
        with patch('app.database.db_manager.get_user_by_username', side_effect=Exception("Database error")):
            register_request = {
                "username": "newuser",
                "email": "new@example.com",
                "password": "SecurePass123!"
            }
            
            response = test_client.post("/api/v1/auth/register", json=register_request)
            assert response.status_code == 500
    
    def test_invalid_json_request(self, test_client):
        """Test API with invalid JSON request"""
        response = test_client.post(
            "/api/v1/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, test_client):
        """Test API with missing required fields"""
        login_request = {
            "username": "testuser"
            # Missing password
        }
        
        response = test_client.post("/api/v1/auth/login", json=login_request)
        assert response.status_code == 422  # Validation error


class TestUserManagementAPIIntegration:
    """Integration tests for User Management API"""
    
    @pytest.mark.asyncio
    async def test_full_auth_workflow(self, test_client):
        """Test complete authentication workflow"""
        # Mock the authentication flow
        with patch('app.auth.auth_service.authenticate_user') as mock_authenticate, \
             patch('app.auth.auth_service.create_user_session') as mock_create_session, \
             patch('app.auth.auth_service.get_user_from_token') as mock_get_user:
            
            # Mock user data
            mock_user = {
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
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "metadata": {}
            }
            
            # Mock authentication
            mock_authenticate.return_value = mock_user
            
            # Mock session creation
            mock_create_session.return_value = ("access_token", "refresh_token", "session_id")
            
            # Mock token validation
            mock_get_user.return_value = mock_user
            
            # Login
            login_request = {
                "username": "testuser",
                "password": "testpassword"
            }
            
            response = test_client.post("/api/v1/auth/login", json=login_request)
            assert response.status_code == 200
            
            # Use token to access protected endpoint
            login_data = response.json()
            access_token = login_data["access_token"]
            
            headers = {"Authorization": f"Bearer {access_token}"}
            response = test_client.get("/api/v1/users/me", headers=headers)
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, test_client):
        """Test concurrent API requests"""
        import asyncio
        
        async def make_login_request():
            """Make a login request"""
            login_request = {
                "username": f"user{i}",
                "password": "password"
            }
            response = test_client.post("/api/v1/auth/login", json=login_request)
            return response.status_code
        
        # Create multiple concurrent requests
        tasks = [
            make_login_request()
            for i in range(5)
        ]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should complete (either successfully or with expected errors)
        for result in results:
            assert isinstance(result, int)  # Should be status code, not exception