#!/usr/bin/env python3
"""
Comprehensive Test Suite for Authentication & API Gateway
Part of Issue #54: Authentication & API Gateway Dependencies

This test suite covers:
- Authentication and authorization functionality
- User management and profile handling
- JWT token management and validation
- API gateway routing and rate limiting
- Security middleware and access control
- Integration testing
- Performance testing
- API endpoint validation
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import requests
import time

# Import the modules under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'auth'))

from auth_manager import (
    AuthManager, User, Token, Session, Permission, Role, UserRole, UserStatus,
    TokenType, AuthProvider
)
from api_gateway import (
    APIGateway, Route, RateLimit, CircuitBreaker, RequestLog, GatewayStats,
    RouteMethod, RateLimitType, CircuitState
)

class TestAuthManager:
    """Test suite for authentication manager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def auth_manager(self, temp_dir):
        """Create auth manager instance"""
        return AuthManager(temp_dir)
    
    def test_create_user(self, auth_manager):
        """Test user creation"""
        user = auth_manager.create_user(
            "testuser",
            "test@example.com",
            "password123",
            UserRole.USER
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.status == UserStatus.ACTIVE
        assert user.user_id in auth_manager.users
    
    def test_authenticate_user(self, auth_manager):
        """Test user authentication"""
        # Create user first
        auth_manager.create_user("testuser", "test@example.com", "password123")
        
        # Test successful authentication
        result = auth_manager.authenticate_user("testuser", "password123")
        
        assert result is not None
        assert result["user"].username == "testuser"
        assert "access_token" in result
        assert "refresh_token" in result
        assert "session_id" in result
    
    def test_authentication_failure(self, auth_manager):
        """Test authentication failure"""
        # Create user first
        auth_manager.create_user("testuser", "test@example.com", "password123")
        
        # Test wrong password
        result = auth_manager.authenticate_user("testuser", "wrongpassword")
        assert result is None
        
        # Test non-existent user
        result = auth_manager.authenticate_user("nonexistent", "password123")
        assert result is None
    
    def test_token_verification(self, auth_manager):
        """Test token verification"""
        # Create and authenticate user
        auth_manager.create_user("testuser", "test@example.com", "password123")
        auth_result = auth_manager.authenticate_user("testuser", "password123")
        
        # Verify access token
        user = auth_manager.verify_token(auth_result["access_token"])
        assert user is not None
        assert user.username == "testuser"
        
        # Test invalid token
        invalid_user = auth_manager.verify_token("invalid_token")
        assert invalid_user is None
    
    def test_token_refresh(self, auth_manager):
        """Test token refresh"""
        # Create and authenticate user
        auth_manager.create_user("testuser", "test@example.com", "password123")
        auth_result = auth_manager.authenticate_user("testuser", "password123")
        
        # Refresh token
        refresh_result = auth_manager.refresh_token(auth_result["refresh_token"])
        
        assert refresh_result is not None
        assert "access_token" in refresh_result
        assert "expires_in" in refresh_result
        
        # Verify new access token
        user = auth_manager.verify_token(refresh_result["access_token"])
        assert user is not None
        assert user.username == "testuser"
    
    def test_password_change(self, auth_manager):
        """Test password change"""
        # Create user
        user = auth_manager.create_user("testuser", "test@example.com", "password123")
        
        # Change password
        success = auth_manager.change_password(user.user_id, "password123", "newpassword456")
        assert success == True
        
        # Test authentication with new password
        result = auth_manager.authenticate_user("testuser", "newpassword456")
        assert result is not None
        
        # Test authentication with old password (should fail)
        result = auth_manager.authenticate_user("testuser", "password123")
        assert result is None
    
    def test_password_reset(self, auth_manager):
        """Test password reset flow"""
        # Create user
        user = auth_manager.create_user("testuser", "test@example.com", "password123")
        
        # Initiate password reset
        reset_token = auth_manager.reset_password("test@example.com")
        assert reset_token is not None
        
        # Confirm password reset
        success = auth_manager.confirm_password_reset(reset_token, "newpassword789")
        assert success == True
        
        # Test authentication with new password
        result = auth_manager.authenticate_user("testuser", "newpassword789")
        assert result is not None
        
        # Test authentication with old password (should fail)
        result = auth_manager.authenticate_user("testuser", "password123")
        assert result is None
    
    def test_mfa_enablement(self, auth_manager):
        """Test MFA enablement"""
        # Create user
        user = auth_manager.create_user("testuser", "test@example.com", "password123")
        
        # Enable MFA
        mfa_result = auth_manager.enable_mfa(user.user_id)
        
        assert "secret" in mfa_result
        assert "qr_code" in mfa_result
        assert user.mfa_enabled == True
        assert user.mfa_secret is not None
    
    def test_permission_checking(self, auth_manager):
        """Test permission checking"""
        # Create admin user
        admin_user = auth_manager.create_user("admin", "admin@example.com", "admin123", UserRole.ADMIN)
        
        # Create regular user
        regular_user = auth_manager.create_user("user", "user@example.com", "user123", UserRole.USER)
        
        # Test admin permissions
        assert auth_manager.check_permission(admin_user, "users", "read") == True
        assert auth_manager.check_permission(admin_user, "users", "write") == True
        assert auth_manager.check_permission(admin_user, "users", "delete") == True
        
        # Test regular user permissions
        assert auth_manager.check_permission(regular_user, "users", "read") == True
        assert auth_manager.check_permission(regular_user, "users", "write") == False
        assert auth_manager.check_permission(regular_user, "users", "delete") == False
    
    def test_user_management(self, auth_manager):
        """Test user management operations"""
        # Create user
        user = auth_manager.create_user("testuser", "test@example.com", "password123")
        
        # Get user by ID
        retrieved_user = auth_manager.get_user(user.user_id)
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        
        # Get user by username
        retrieved_user = auth_manager.get_user_by_username("testuser")
        assert retrieved_user is not None
        assert retrieved_user.user_id == user.user_id
        
        # Get user by email
        retrieved_user = auth_manager.get_user_by_email("test@example.com")
        assert retrieved_user is not None
        assert retrieved_user.user_id == user.user_id
        
        # Update user
        updated_user = auth_manager.update_user(user.user_id, role=UserRole.ADMIN)
        assert updated_user is not None
        assert updated_user.role == UserRole.ADMIN
        
        # List users
        users = auth_manager.list_users()
        assert len(users) >= 1
        
        # List users by role
        admin_users = auth_manager.list_users(role=UserRole.ADMIN)
        assert len(admin_users) >= 1
        
        # Delete user
        success = auth_manager.delete_user(user.user_id)
        assert success == True
        
        # Verify user is deleted
        deleted_user = auth_manager.get_user(user.user_id)
        assert deleted_user is None
    
    def test_failed_login_protection(self, auth_manager):
        """Test failed login protection"""
        # Create user
        auth_manager.create_user("testuser", "test@example.com", "password123")
        
        # Attempt multiple failed logins
        for i in range(5):
            result = auth_manager.authenticate_user("testuser", "wrongpassword")
            assert result is None
        
        # User should be locked now
        user = auth_manager.get_user_by_username("testuser")
        assert user.locked_until is not None
        
        # Authentication should fail even with correct password
        result = auth_manager.authenticate_user("testuser", "password123")
        assert result is None
    
    def test_auth_summary(self, auth_manager):
        """Test authentication summary"""
        # Create some users
        auth_manager.create_user("admin", "admin@example.com", "admin123", UserRole.ADMIN)
        auth_manager.create_user("user1", "user1@example.com", "user123", UserRole.USER)
        auth_manager.create_user("user2", "user2@example.com", "user123", UserRole.USER)
        
        # Get summary
        summary = auth_manager.get_auth_summary()
        
        assert summary["total_users"] >= 3
        assert summary["active_users"] >= 3
        assert "by_role" in summary
        assert "by_status" in summary

class TestAPIGateway:
    """Test suite for API gateway"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def api_gateway(self, temp_dir):
        """Create API gateway instance"""
        return APIGateway(temp_dir)
    
    def test_create_route(self, api_gateway):
        """Test route creation"""
        route = api_gateway.create_route(
            "test-route",
            "/api/test",
            RouteMethod.GET,
            "http://localhost:8001",
            timeout=30,
            auth_required=True
        )
        
        assert route.route_id == "test-route"
        assert route.path == "/api/test"
        assert route.method == RouteMethod.GET
        assert route.target_url == "http://localhost:8001"
        assert route.timeout == 30
        assert route.auth_required == True
    
    def test_find_route(self, api_gateway):
        """Test route finding"""
        # Create route
        api_gateway.create_route(
            "test-route",
            "/api/test",
            RouteMethod.GET,
            "http://localhost:8001"
        )
        
        # Find route
        route = api_gateway.find_route("/api/test", "GET")
        assert route is not None
        assert route.route_id == "test-route"
        
        # Test non-existent route
        route = api_gateway.find_route("/api/nonexistent", "GET")
        assert route is None
    
    def test_create_rate_limit(self, api_gateway):
        """Test rate limit creation"""
        rate_limit = api_gateway.create_rate_limit(
            "test-limit",
            "Test Rate Limit",
            RateLimitType.PER_MINUTE,
            100,
            60
        )
        
        assert rate_limit.limit_id == "test-limit"
        assert rate_limit.name == "Test Rate Limit"
        assert rate_limit.limit_type == RateLimitType.PER_MINUTE
        assert rate_limit.requests_per_period == 100
        assert rate_limit.period_seconds == 60
    
    def test_create_circuit_breaker(self, api_gateway):
        """Test circuit breaker creation"""
        circuit_breaker = api_gateway.create_circuit_breaker(
            "test-breaker",
            "Test Circuit Breaker",
            failure_threshold=5,
            recovery_timeout=60
        )
        
        assert circuit_breaker.breaker_id == "test-breaker"
        assert circuit_breaker.name == "Test Circuit Breaker"
        assert circuit_breaker.failure_threshold == 5
        assert circuit_breaker.recovery_timeout == 60
        assert circuit_breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_request_handling(self, api_gateway):
        """Test request handling"""
        # Create route
        api_gateway.create_route(
            "test-route",
            "/api/test",
            RouteMethod.GET,
            "http://httpbin.org/get"  # Use httpbin for testing
        )
        
        # Handle request
        response = await api_gateway.handle_request(
            "GET",
            "/api/test",
            {"Content-Type": "application/json"},
            {},
            user_id="testuser",
            ip_address="127.0.0.1",
            user_agent="Test Agent"
        )
        
        assert response is not None
        assert "status_code" in response
        assert "body" in response
        assert "headers" in response
    
    @pytest.mark.asyncio
    async def test_authentication_required(self, api_gateway):
        """Test authentication requirement"""
        # Create route with auth required
        api_gateway.create_route(
            "auth-route",
            "/api/auth",
            RouteMethod.GET,
            "http://localhost:8001",
            auth_required=True
        )
        
        # Handle request without authentication
        response = await api_gateway.handle_request(
            "GET",
            "/api/auth",
            {},
            {}
        )
        
        assert response["status_code"] == 401
        assert "Authentication required" in response["body"]
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, api_gateway):
        """Test rate limiting"""
        # Create rate limit
        api_gateway.create_rate_limit(
            "test-limit",
            "Test Rate Limit",
            RateLimitType.PER_MINUTE,
            2,  # Very low limit for testing
            60
        )
        
        # Create route with rate limit
        api_gateway.create_route(
            "rate-limited-route",
            "/api/rate-limited",
            RouteMethod.GET,
            "http://localhost:8001",
            rate_limit_id="test-limit"
        )
        
        # Make requests within limit
        for i in range(2):
            response = await api_gateway.handle_request(
                "GET",
                "/api/rate-limited",
                {},
                {},
                user_id="testuser"
            )
            assert response["status_code"] != 429
        
        # Make request that should be rate limited
        response = await api_gateway.handle_request(
            "GET",
            "/api/rate-limited",
            {},
            {},
            user_id="testuser"
        )
        assert response["status_code"] == 429
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self, api_gateway):
        """Test circuit breaker functionality"""
        # Create circuit breaker
        api_gateway.create_circuit_breaker(
            "test-breaker",
            "Test Circuit Breaker",
            failure_threshold=2,  # Low threshold for testing
            recovery_timeout=5
        )
        
        # Create route that will fail
        api_gateway.create_route(
            "failing-route",
            "/api/fail",
            RouteMethod.GET,
            "http://localhost:9999"  # Non-existent service
        )
        
        # Make requests that will fail
        for i in range(3):
            response = await api_gateway.handle_request(
                "GET",
                "/api/fail",
                {},
                {}
            )
            # First two should fail with 502, third might be 503 if circuit opens
            assert response["status_code"] in [502, 503]
        
        # Check circuit breaker state
        breaker = api_gateway.circuit_breakers["test-breaker"]
        assert breaker.state == CircuitState.OPEN
    
    def test_route_management(self, api_gateway):
        """Test route management operations"""
        # Create route
        route = api_gateway.create_route(
            "test-route",
            "/api/test",
            RouteMethod.GET,
            "http://localhost:8001"
        )
        
        # Get route
        retrieved_route = api_gateway.get_route("test-route")
        assert retrieved_route is not None
        assert retrieved_route.route_id == "test-route"
        
        # List routes
        routes = api_gateway.list_routes()
        assert len(routes) >= 1
        
        # List enabled routes only
        enabled_routes = api_gateway.list_routes(enabled_only=True)
        assert len(enabled_routes) >= 1
        
        # Update route
        updated_route = api_gateway.update_route("test-route", enabled=False)
        assert updated_route is not None
        assert updated_route.enabled == False
        
        # Delete route
        success = api_gateway.delete_route("test-route")
        assert success == True
        
        # Verify route is deleted
        deleted_route = api_gateway.get_route("test-route")
        assert deleted_route is None
    
    def test_request_logging(self, api_gateway):
        """Test request logging"""
        # Create route
        api_gateway.create_route(
            "test-route",
            "/api/test",
            RouteMethod.GET,
            "http://localhost:8001"
        )
        
        # Get initial log count
        initial_logs = len(api_gateway.request_logs)
        
        # Make a request (this will be logged)
        asyncio.run(api_gateway.handle_request(
            "GET",
            "/api/test",
            {},
            {},
            user_id="testuser",
            ip_address="127.0.0.1"
        ))
        
        # Check that log was created
        assert len(api_gateway.request_logs) > initial_logs
        
        # Get request logs
        logs = api_gateway.get_request_logs(route_id="test-route")
        assert len(logs) >= 1
        assert logs[0].route_id == "test-route"
        assert logs[0].user_id == "testuser"
    
    def test_gateway_stats(self, api_gateway):
        """Test gateway statistics"""
        # Get initial stats
        initial_stats = api_gateway.get_gateway_stats()
        
        # Create route and make some requests
        api_gateway.create_route(
            "test-route",
            "/api/test",
            RouteMethod.GET,
            "http://localhost:8001"
        )
        
        # Make some requests
        for i in range(3):
            asyncio.run(api_gateway.handle_request(
                "GET",
                "/api/test",
                {},
                {},
                user_id="testuser"
            ))
        
        # Check updated stats
        stats = api_gateway.get_gateway_stats()
        assert stats.total_requests >= initial_stats.total_requests + 3
    
    def test_route_stats(self, api_gateway):
        """Test route-specific statistics"""
        # Create route
        api_gateway.create_route(
            "test-route",
            "/api/test",
            RouteMethod.GET,
            "http://localhost:8001"
        )
        
        # Make some requests
        for i in range(5):
            asyncio.run(api_gateway.handle_request(
                "GET",
                "/api/test",
                {},
                {},
                user_id="testuser"
            ))
        
        # Get route stats
        stats = api_gateway.get_route_stats("test-route")
        
        assert stats["total_requests"] >= 5
        assert "success_rate" in stats
        assert "error_rate" in stats

class TestIntegration:
    """Integration tests for authentication and API gateway"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def managers(self, temp_dir):
        """Create all manager instances"""
        auth_mgr = AuthManager(temp_dir / "auth")
        gateway = APIGateway(temp_dir / "gateway", auth_mgr)
        return {"auth": auth_mgr, "gateway": gateway}
    
    def test_authenticated_request_flow(self, managers):
        """Test complete authenticated request flow"""
        auth_mgr = managers["auth"]
        gateway = managers["gateway"]
        
        # Create user
        user = auth_mgr.create_user("testuser", "test@example.com", "password123")
        
        # Authenticate user
        auth_result = auth_mgr.authenticate_user("testuser", "password123")
        assert auth_result is not None
        
        # Create protected route
        gateway.create_route(
            "protected-route",
            "/api/protected",
            RouteMethod.GET,
            "http://localhost:8001",
            auth_required=True
        )
        
        # Make authenticated request
        response = asyncio.run(gateway.handle_request(
            "GET",
            "/api/protected",
            {"Authorization": f"Bearer {auth_result['access_token']}"},
            {},
            user_id=user.user_id,
            ip_address="127.0.0.1"
        ))
        
        # Should not be 401 (authentication error)
        assert response["status_code"] != 401
    
    def test_permission_based_access(self, managers):
        """Test permission-based access control"""
        auth_mgr = managers["auth"]
        gateway = managers["gateway"]
        
        # Create admin and regular user
        admin_user = auth_mgr.create_user("admin", "admin@example.com", "admin123", UserRole.ADMIN)
        regular_user = auth_mgr.create_user("user", "user@example.com", "user123", UserRole.USER)
        
        # Authenticate both users
        admin_auth = auth_mgr.authenticate_user("admin", "admin123")
        user_auth = auth_mgr.authenticate_user("user", "user123")
        
        # Create route that requires admin permissions
        gateway.create_route(
            "admin-route",
            "/api/admin",
            RouteMethod.GET,
            "http://localhost:8001",
            auth_required=True
        )
        
        # Test admin access
        admin_response = asyncio.run(gateway.handle_request(
            "GET",
            "/api/admin",
            {"Authorization": f"Bearer {admin_auth['access_token']}"},
            {},
            user_id=admin_user.user_id
        ))
        
        # Test regular user access
        user_response = asyncio.run(gateway.handle_request(
            "GET",
            "/api/admin",
            {"Authorization": f"Bearer {user_auth['access_token']}"},
            {},
            user_id=regular_user.user_id
        ))
        
        # Both should pass gateway (permission checking would be in the target service)
        assert admin_response["status_code"] != 401
        assert user_response["status_code"] != 401
    
    def test_rate_limiting_per_user(self, managers):
        """Test per-user rate limiting"""
        auth_mgr = managers["auth"]
        gateway = managers["gateway"]
        
        # Create users
        user1 = auth_mgr.create_user("user1", "user1@example.com", "password123")
        user2 = auth_mgr.create_user("user2", "user2@example.com", "password123")
        
        # Create per-user rate limit
        gateway.create_rate_limit(
            "per-user-limit",
            "Per User Rate Limit",
            RateLimitType.PER_USER,
            2,  # Very low limit for testing
            60
        )
        
        # Create route with per-user rate limit
        gateway.create_route(
            "rate-limited-route",
            "/api/rate-limited",
            RouteMethod.GET,
            "http://localhost:8001",
            rate_limit_id="per-user-limit"
        )
        
        # User 1 makes requests within limit
        for i in range(2):
            response = asyncio.run(gateway.handle_request(
                "GET",
                "/api/rate-limited",
                {},
                {},
                user_id=user1.user_id
            ))
            assert response["status_code"] != 429
        
        # User 1 exceeds limit
        response = asyncio.run(gateway.handle_request(
            "GET",
            "/api/rate-limited",
            {},
            {},
            user_id=user1.user_id
        ))
        assert response["status_code"] == 429
        
        # User 2 should still be able to make requests
        response = asyncio.run(gateway.handle_request(
            "GET",
            "/api/rate-limited",
            {},
            {},
            user_id=user2.user_id
        ))
        assert response["status_code"] != 429
    
    def test_session_management(self, managers):
        """Test session management"""
        auth_mgr = managers["auth"]
        gateway = managers["gateway"]
        
        # Create user
        user = auth_mgr.create_user("testuser", "test@example.com", "password123")
        
        # Authenticate user
        auth_result = auth_mgr.authenticate_user("testuser", "password123")
        session_id = auth_result["session_id"]
        
        # Verify session exists
        assert session_id in auth_mgr.sessions
        session = auth_mgr.sessions[session_id]
        assert session.user_id == user.user_id
        assert session.is_active == True
        
        # Logout user
        success = auth_mgr.logout_user(session_id)
        assert success == True
        
        # Verify session is deactivated
        session = auth_mgr.sessions[session_id]
        assert session.is_active == False
    
    def test_token_revocation(self, managers):
        """Test token revocation"""
        auth_mgr = managers["auth"]
        gateway = managers["gateway"]
        
        # Create user
        user = auth_mgr.create_user("testuser", "test@example.com", "password123")
        
        # Authenticate user
        auth_result = auth_mgr.authenticate_user("testuser", "password123")
        access_token = auth_result["access_token"]
        
        # Verify token works
        verified_user = auth_mgr.verify_token(access_token)
        assert verified_user is not None
        
        # Revoke token
        success = auth_mgr.revoke_token(access_token)
        assert success == True
        
        # Verify token no longer works
        verified_user = auth_mgr.verify_token(access_token)
        assert verified_user is None

class TestPerformance:
    """Performance tests"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_user_creation_performance(self, temp_dir):
        """Test user creation performance"""
        auth_mgr = AuthManager(temp_dir)
        
        # Create 100 users
        start_time = time.time()
        
        for i in range(100):
            auth_mgr.create_user(
                f"user{i}",
                f"user{i}@example.com",
                "password123"
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 5.0  # Less than 5 seconds
        
        # Verify users were created
        assert len(auth_mgr.users) == 100
    
    def test_authentication_performance(self, temp_dir):
        """Test authentication performance"""
        auth_mgr = AuthManager(temp_dir)
        
        # Create user
        auth_mgr.create_user("testuser", "test@example.com", "password123")
        
        # Authenticate 100 times
        start_time = time.time()
        
        for i in range(100):
            result = auth_mgr.authenticate_user("testuser", "password123")
            assert result is not None
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 3.0  # Less than 3 seconds
    
    def test_route_creation_performance(self, temp_dir):
        """Test route creation performance"""
        gateway = APIGateway(temp_dir)
        
        # Create 100 routes
        start_time = time.time()
        
        for i in range(100):
            gateway.create_route(
                f"route-{i}",
                f"/api/route{i}",
                RouteMethod.GET,
                f"http://localhost:{8000 + i}"
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 2.0  # Less than 2 seconds
        
        # Verify routes were created
        assert len(gateway.routes) == 100
    
    @pytest.mark.asyncio
    async def test_request_handling_performance(self, temp_dir):
        """Test request handling performance"""
        gateway = APIGateway(temp_dir)
        
        # Create route
        gateway.create_route(
            "test-route",
            "/api/test",
            RouteMethod.GET,
            "http://httpbin.org/get"
        )
        
        # Handle 50 requests
        start_time = time.time()
        
        tasks = []
        for i in range(50):
            task = gateway.handle_request(
                "GET",
                "/api/test",
                {},
                {},
                user_id=f"user{i}"
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 10.0  # Less than 10 seconds
        
        # Verify all requests were handled
        assert len(responses) == 50
        assert all(response is not None for response in responses)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])