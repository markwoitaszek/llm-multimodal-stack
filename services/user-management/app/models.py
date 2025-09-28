"""
User Management Data Models
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timedelta
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    GUEST = "guest"


class UserStatus(str, Enum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    LOCKED = "locked"


class AuthProvider(str, Enum):
    """Authentication provider enumeration"""
    LOCAL = "local"
    OAUTH_GOOGLE = "oauth_google"
    OAUTH_GITHUB = "oauth_github"
    OAUTH_MICROSOFT = "oauth_microsoft"


class LoginRequest(BaseModel):
    """User login request model"""
    username: str = Field(..., min_length=3, max_length=50, description="Username or email")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: bool = Field(default=False, description="Remember login session")
    tenant_id: Optional[str] = Field(default=None, description="Tenant identifier")


class LoginResponse(BaseModel):
    """User login response model"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: 'UserResponse' = Field(..., description="User information")


class RegisterRequest(BaseModel):
    """User registration request model"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    full_name: Optional[str] = Field(default=None, max_length=100, description="Full name")
    phone: Optional[str] = Field(default=None, max_length=20, description="Phone number")
    tenant_id: Optional[str] = Field(default=None, description="Tenant identifier")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class UserResponse(BaseModel):
    """User response model"""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: Optional[str] = Field(default=None, description="Full name")
    phone: Optional[str] = Field(default=None, description="Phone number")
    role: UserRole = Field(..., description="User role")
    status: UserStatus = Field(..., description="User status")
    tenant_id: str = Field(..., description="Tenant identifier")
    auth_provider: AuthProvider = Field(..., description="Authentication provider")
    email_verified: bool = Field(..., description="Email verification status")
    phone_verified: bool = Field(..., description="Phone verification status")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class UserUpdateRequest(BaseModel):
    """User update request model"""
    full_name: Optional[str] = Field(default=None, max_length=100, description="Full name")
    phone: Optional[str] = Field(default=None, max_length=20, description="Phone number")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class PasswordChangeRequest(BaseModel):
    """Password change request model"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")


class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation request model"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str = Field(..., description="Refresh token")


class SessionResponse(BaseModel):
    """Session response model"""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    ip_address: Optional[str] = Field(default=None, description="IP address")
    user_agent: Optional[str] = Field(default=None, description="User agent")
    is_active: bool = Field(..., description="Session active status")


class LogoutRequest(BaseModel):
    """Logout request model"""
    session_id: Optional[str] = Field(default=None, description="Specific session to logout")
    logout_all_sessions: bool = Field(default=False, description="Logout all user sessions")


class TenantRequest(BaseModel):
    """Tenant creation request model"""
    name: str = Field(..., min_length=2, max_length=100, description="Tenant name")
    description: Optional[str] = Field(default=None, max_length=500, description="Tenant description")
    domain: Optional[str] = Field(default=None, max_length=100, description="Tenant domain")
    admin_user_id: Optional[str] = Field(default=None, description="Admin user identifier")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class TenantResponse(BaseModel):
    """Tenant response model"""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    name: str = Field(..., description="Tenant name")
    description: Optional[str] = Field(default=None, description="Tenant description")
    domain: Optional[str] = Field(default=None, description="Tenant domain")
    admin_user_id: Optional[str] = Field(default=None, description="Admin user identifier")
    user_count: int = Field(..., description="Number of users in tenant")
    max_users: int = Field(..., description="Maximum users allowed")
    created_at: datetime = Field(..., description="Tenant creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class TenantUpdateRequest(BaseModel):
    """Tenant update request model"""
    name: Optional[str] = Field(default=None, min_length=2, max_length=100, description="Tenant name")
    description: Optional[str] = Field(default=None, max_length=500, description="Tenant description")
    domain: Optional[str] = Field(default=None, max_length=100, description="Tenant domain")
    max_users: Optional[int] = Field(default=None, ge=1, description="Maximum users allowed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class UserListRequest(BaseModel):
    """User list request model"""
    tenant_id: Optional[str] = Field(default=None, description="Filter by tenant")
    role: Optional[UserRole] = Field(default=None, description="Filter by role")
    status: Optional[UserStatus] = Field(default=None, description="Filter by status")
    search: Optional[str] = Field(default=None, max_length=100, description="Search query")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")


class UserListResponse(BaseModel):
    """User list response model"""
    users: List[UserResponse] = Field(..., description="List of users")
    total_count: int = Field(..., ge=0, description="Total number of users")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")


class SessionListRequest(BaseModel):
    """Session list request model"""
    user_id: Optional[str] = Field(default=None, description="Filter by user")
    tenant_id: Optional[str] = Field(default=None, description="Filter by tenant")
    active_only: bool = Field(default=True, description="Show only active sessions")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")


class SessionListResponse(BaseModel):
    """Session list response model"""
    sessions: List[SessionResponse] = Field(..., description="List of sessions")
    total_count: int = Field(..., ge=0, description="Total number of sessions")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")
    dependencies: Dict[str, str] = Field(..., description="Dependency status")


class StatsResponse(BaseModel):
    """Service statistics response model"""
    total_users: int = Field(..., description="Total user count")
    total_tenants: int = Field(..., description="Total tenant count")
    active_sessions: int = Field(..., description="Active session count")
    users_by_role: Dict[str, int] = Field(..., description="User distribution by role")
    users_by_status: Dict[str, int] = Field(..., description="User distribution by status")
    tenants_by_user_count: Dict[str, int] = Field(..., description="Tenant distribution by user count")
    login_attempts_last_hour: int = Field(..., description="Login attempts in last hour")
    cache_hit_rate: float = Field(..., ge=0.0, le=1.0, description="Cache hit rate")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request identifier")


# Update forward references
LoginResponse.model_rebuild()