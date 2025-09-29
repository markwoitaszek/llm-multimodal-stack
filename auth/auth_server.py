#!/usr/bin/env python3
"""
Authentication and API Gateway Server
Part of Issue #54: Authentication & API Gateway Dependencies

This FastAPI server provides comprehensive authentication and API gateway functionality including:
- User authentication and authorization
- JWT token management
- API gateway with routing and rate limiting
- User management endpoints
- Security middleware
- Real-time monitoring and analytics
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
import uvicorn

# Import our authentication and gateway modules
from auth_manager import (
    AuthManager, User, Token, Session, Permission, Role, UserRole, UserStatus,
    TokenType, AuthProvider
)
from api_gateway import (
    APIGateway, Route, RateLimit, CircuitBreaker, RequestLog, GatewayStats,
    RouteMethod, RateLimitType, CircuitState
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Authentication & API Gateway",
    description="Comprehensive authentication and API gateway system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global managers
auth_manager: Optional[AuthManager] = None
api_gateway: Optional[APIGateway] = None

# Security
security = HTTPBearer()

# Pydantic models for API requests/responses
class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = "user"
    profile: Dict[str, Any] = {}

class UserLoginRequest(BaseModel):
    username: str
    password: str

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirmRequest(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=8)

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class RouteCreateRequest(BaseModel):
    route_id: str
    path: str
    method: str
    target_url: str
    enabled: bool = True
    timeout: int = 30
    retries: int = 3
    auth_required: bool = True
    rate_limit_id: Optional[str] = None
    headers: Dict[str, str] = {}
    middleware: List[str] = []

class RateLimitCreateRequest(BaseModel):
    limit_id: str
    name: str
    limit_type: str
    requests_per_period: int
    period_seconds: int
    burst_limit: int = 0

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    status: str
    created_at: str
    last_login: Optional[str] = None
    profile: Dict[str, Any] = {}
    mfa_enabled: bool = False

class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    session_id: str
    expires_in: int

class TokenResponse(BaseModel):
    access_token: str
    expires_in: int

# Dependency functions
def get_auth_manager() -> AuthManager:
    if not auth_manager:
        raise HTTPException(status_code=500, detail="Auth manager not initialized")
    return auth_manager

def get_api_gateway() -> APIGateway:
    if not api_gateway:
        raise HTTPException(status_code=500, detail="API gateway not initialized")
    return api_gateway

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_mgr: AuthManager = Depends(get_auth_manager)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    user = auth_mgr.verify_token(token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_permission(resource: str, action: str):
    """Decorator to require specific permission"""
    def permission_checker(
        current_user: User = Depends(get_current_active_user),
        auth_mgr: AuthManager = Depends(get_auth_manager)
    ) -> User:
        if not auth_mgr.check_permission(current_user, resource, action):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {action} on {resource}"
            )
        return current_user
    
    return permission_checker

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize managers on startup"""
    global auth_manager, api_gateway
    
    data_dir = Path("./auth_data")
    data_dir.mkdir(exist_ok=True)
    
    # Initialize managers
    auth_manager = AuthManager(data_dir / "auth")
    api_gateway = APIGateway(data_dir / "gateway", auth_manager)
    
    # Create default admin user if none exists
    if not auth_manager.get_user_by_username("admin"):
        auth_manager.create_user(
            "admin",
            "admin@example.com",
            "admin123",
            UserRole.ADMIN
        )
        logger.info("Created default admin user")
    
    logger.info("Authentication & API Gateway server started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Authentication & API Gateway server stopped")

# Authentication Endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register_user(
    request: UserCreateRequest,
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """Register a new user"""
    try:
        role = UserRole(request.role) if request.role in [r.value for r in UserRole] else UserRole.USER
        
        user = auth_mgr.create_user(
            request.username,
            request.email,
            request.password,
            role,
            request.profile
        )
        
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            role=user.role.value,
            status=user.status.value,
            created_at=user.created_at,
            last_login=user.last_login,
            profile=user.profile,
            mfa_enabled=user.mfa_enabled
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", response_model=AuthResponse)
async def login_user(
    request: UserLoginRequest,
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """Authenticate user and return tokens"""
    try:
        auth_result = auth_mgr.authenticate_user(
            request.username,
            request.password,
            ip_address="127.0.0.1",  # In production, get from request
            user_agent="API Client"  # In production, get from request
        )
        
        if not auth_result:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )
        
        user = auth_result["user"]
        
        return AuthResponse(
            user=UserResponse(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                role=user.role.value,
                status=user.status.value,
                created_at=user.created_at,
                last_login=user.last_login,
                profile=user.profile,
                mfa_enabled=user.mfa_enabled
            ),
            access_token=auth_result["access_token"],
            refresh_token=auth_result["refresh_token"],
            session_id=auth_result["session_id"],
            expires_in=auth_result["expires_in"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """Refresh access token"""
    try:
        result = auth_mgr.refresh_token(request.refresh_token)
        
        if not result:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
        
        return TokenResponse(
            access_token=result["access_token"],
            expires_in=result["expires_in"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/logout")
async def logout_user(
    session_id: str,
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """Logout user and invalidate session"""
    try:
        success = auth_mgr.logout_user(session_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """Change user password"""
    try:
        success = auth_mgr.change_password(
            current_user.user_id,
            request.old_password,
            request.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Invalid old password"
            )
        
        return {"message": "Password changed successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/reset-password")
async def reset_password(
    request: PasswordResetRequest,
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """Initiate password reset"""
    try:
        reset_token = auth_mgr.reset_password(request.email)
        
        if not reset_token:
            # Don't reveal if email exists or not
            return {"message": "If the email exists, a reset link has been sent"}
        
        # In production, send email with reset token
        logger.info(f"Password reset token for {request.email}: {reset_token}")
        
        return {"message": "If the email exists, a reset link has been sent"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/confirm-reset")
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """Confirm password reset"""
    try:
        success = auth_mgr.confirm_password_reset(
            request.reset_token,
            request.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset token"
            )
        
        return {"message": "Password reset successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/enable-mfa")
async def enable_mfa(
    current_user: User = Depends(get_current_active_user),
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """Enable multi-factor authentication"""
    try:
        result = auth_mgr.enable_mfa(current_user.user_id)
        
        return {
            "secret": result["secret"],
            "qr_code": result["qr_code"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/verify-mfa")
async def verify_mfa(
    mfa_code: str,
    current_user: User = Depends(get_current_active_user),
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """Verify MFA code"""
    try:
        success = auth_mgr.verify_mfa(current_user.user_id, mfa_code)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Invalid MFA code"
            )
        
        return {"message": "MFA verified successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# User Management Endpoints
@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        status=current_user.status.value,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        profile=current_user.profile,
        mfa_enabled=current_user.mfa_enabled
    )

@app.get("/users", response_model=List[UserResponse])
async def list_users(
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_permission("users", "read")),
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """List users (admin only)"""
    try:
        user_role = UserRole(role) if role else None
        user_status = UserStatus(status) if status else None
        
        users = auth_mgr.list_users(user_role, user_status)
        
        return [
            UserResponse(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                role=user.role.value,
                status=user.status.value,
                created_at=user.created_at,
                last_login=user.last_login,
                profile=user.profile,
                mfa_enabled=user.mfa_enabled
            )
            for user in users
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_permission("users", "read")),
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """Get user by ID (admin only)"""
    try:
        user = auth_mgr.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            role=user.role.value,
            status=user.status.value,
            created_at=user.created_at,
            last_login=user.last_login,
            profile=user.profile,
            mfa_enabled=user.mfa_enabled
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/users/{user_id}")
async def update_user(
    user_id: str,
    role: Optional[str] = None,
    status: Optional[str] = None,
    profile: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(require_permission("users", "write")),
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """Update user (admin only)"""
    try:
        update_data = {}
        
        if role:
            update_data["role"] = UserRole(role)
        
        if status:
            update_data["status"] = UserStatus(status)
        
        if profile is not None:
            update_data["profile"] = profile
        
        user = auth_mgr.update_user(user_id, **update_data)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_permission("users", "delete")),
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """Delete user (admin only)"""
    try:
        success = auth_mgr.delete_user(user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# API Gateway Endpoints
@app.post("/gateway/routes")
async def create_route(
    request: RouteCreateRequest,
    current_user: User = Depends(require_permission("deployments", "write")),
    gateway: APIGateway = Depends(get_api_gateway)
):
    """Create a new route (admin/developer only)"""
    try:
        method = RouteMethod(request.method.upper())
        
        route = gateway.create_route(
            request.route_id,
            request.path,
            method,
            request.target_url,
            request.enabled,
            request.timeout,
            request.retries,
            request.auth_required,
            request.rate_limit_id,
            request.headers,
            request.middleware
        )
        
        return {"message": "Route created successfully", "route_id": route.route_id}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/gateway/routes")
async def list_routes(
    enabled_only: bool = Query(False),
    current_user: User = Depends(require_permission("deployments", "read")),
    gateway: APIGateway = Depends(get_api_gateway)
):
    """List routes"""
    try:
        routes = gateway.list_routes(enabled_only)
        
        return [
            {
                "route_id": route.route_id,
                "path": route.path,
                "method": route.method.value,
                "target_url": route.target_url,
                "enabled": route.enabled,
                "timeout": route.timeout,
                "retries": route.retries,
                "auth_required": route.auth_required,
                "rate_limit": route.rate_limit,
                "headers": route.headers,
                "middleware": route.middleware
            }
            for route in routes
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/gateway/routes/{route_id}")
async def get_route(
    route_id: str,
    current_user: User = Depends(require_permission("deployments", "read")),
    gateway: APIGateway = Depends(get_api_gateway)
):
    """Get route by ID"""
    try:
        route = gateway.get_route(route_id)
        
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        
        return {
            "route_id": route.route_id,
            "path": route.path,
            "method": route.method.value,
            "target_url": route.target_url,
            "enabled": route.enabled,
            "timeout": route.timeout,
            "retries": route.retries,
            "auth_required": route.auth_required,
            "rate_limit": route.rate_limit,
            "headers": route.headers,
            "middleware": route.middleware
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/gateway/routes/{route_id}")
async def update_route(
    route_id: str,
    enabled: Optional[bool] = None,
    timeout: Optional[int] = None,
    retries: Optional[int] = None,
    auth_required: Optional[bool] = None,
    headers: Optional[Dict[str, str]] = None,
    middleware: Optional[List[str]] = None,
    current_user: User = Depends(require_permission("deployments", "write")),
    gateway: APIGateway = Depends(get_api_gateway)
):
    """Update route"""
    try:
        update_data = {}
        
        if enabled is not None:
            update_data["enabled"] = enabled
        
        if timeout is not None:
            update_data["timeout"] = timeout
        
        if retries is not None:
            update_data["retries"] = retries
        
        if auth_required is not None:
            update_data["auth_required"] = auth_required
        
        if headers is not None:
            update_data["headers"] = headers
        
        if middleware is not None:
            update_data["middleware"] = middleware
        
        route = gateway.update_route(route_id, **update_data)
        
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        
        return {"message": "Route updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/gateway/routes/{route_id}")
async def delete_route(
    route_id: str,
    current_user: User = Depends(require_permission("deployments", "write")),
    gateway: APIGateway = Depends(get_api_gateway)
):
    """Delete route"""
    try:
        success = gateway.delete_route(route_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Route not found")
        
        return {"message": "Route deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/gateway/rate-limits")
async def create_rate_limit(
    request: RateLimitCreateRequest,
    current_user: User = Depends(require_permission("deployments", "write")),
    gateway: APIGateway = Depends(get_api_gateway)
):
    """Create a new rate limit"""
    try:
        limit_type = RateLimitType(request.limit_type)
        
        rate_limit = gateway.create_rate_limit(
            request.limit_id,
            request.name,
            limit_type,
            request.requests_per_period,
            request.period_seconds,
            request.burst_limit
        )
        
        return {"message": "Rate limit created successfully", "limit_id": rate_limit.limit_id}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Monitoring and Analytics Endpoints
@app.get("/gateway/stats")
async def get_gateway_stats(
    current_user: User = Depends(require_permission("monitoring", "read")),
    gateway: APIGateway = Depends(get_api_gateway)
):
    """Get gateway statistics"""
    try:
        stats = gateway.get_gateway_stats()
        
        return {
            "total_requests": stats.total_requests,
            "successful_requests": stats.successful_requests,
            "failed_requests": stats.failed_requests,
            "rate_limited_requests": stats.rate_limited_requests,
            "circuit_breaker_trips": stats.circuit_breaker_trips,
            "average_response_time": stats.average_response_time,
            "requests_per_minute": stats.requests_per_minute,
            "error_rate": stats.error_rate
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/gateway/routes/{route_id}/stats")
async def get_route_stats(
    route_id: str,
    period_hours: int = Query(24),
    current_user: User = Depends(require_permission("monitoring", "read")),
    gateway: APIGateway = Depends(get_api_gateway)
):
    """Get route statistics"""
    try:
        stats = gateway.get_route_stats(route_id, period_hours)
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/gateway/logs")
async def get_request_logs(
    route_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    limit: int = Query(100),
    current_user: User = Depends(require_permission("monitoring", "read")),
    gateway: APIGateway = Depends(get_api_gateway)
):
    """Get request logs"""
    try:
        logs = gateway.get_request_logs(
            route_id=route_id,
            user_id=user_id,
            limit=limit
        )
        
        return [
            {
                "log_id": log.log_id,
                "route_id": log.route_id,
                "method": log.method,
                "path": log.path,
                "user_id": log.user_id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "request_time": log.request_time,
                "response_time": log.response_time,
                "status_code": log.status_code,
                "response_time_ms": log.response_time_ms,
                "error_message": log.error_message
            }
            for log in logs
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# System Endpoints
@app.get("/auth/summary")
async def get_auth_summary(
    current_user: User = Depends(require_permission("users", "read")),
    auth_mgr: AuthManager = Depends(get_auth_manager)
):
    """Get authentication system summary"""
    try:
        summary = auth_mgr.get_auth_summary()
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "authentication-api-gateway"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Authentication & API Gateway",
        "version": "1.0.0",
        "description": "Comprehensive authentication and API gateway system",
        "endpoints": {
            "authentication": "/auth/*",
            "user_management": "/users/*",
            "api_gateway": "/gateway/*",
            "monitoring": "/gateway/stats",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "auth_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )