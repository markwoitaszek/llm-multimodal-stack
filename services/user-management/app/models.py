"""
Pydantic models for user management service
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, validator
import uuid

class UserRole(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    MODERATOR = "moderator"

class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    LOCKED = "locked"

class TenantStatus(str, Enum):
    """Tenant status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"

class TokenType(str, Enum):
    """Token types"""
    ACCESS = "access"
    REFRESH = "refresh"

# Base models
class BaseUser(BaseModel):
    """Base user model"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    is_verified: bool = False
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()

class UserCreate(BaseUser):
    """User creation model"""
    password: str = Field(..., min_length=8)
    tenant_id: Optional[uuid.UUID] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    preferences: Optional[Dict[str, Any]] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if not v.replace('_', '').replace('-', '').isalnum():
                raise ValueError('Username must contain only alphanumeric characters, hyphens, and underscores')
            return v.lower()
        return v

class UserResponse(BaseUser):
    """User response model"""
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """User list response model"""
    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int

# Tenant models
class BaseTenant(BaseModel):
    """Base tenant model"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    domain: Optional[str] = Field(None, max_length=255)
    status: TenantStatus = TenantStatus.ACTIVE
    settings: Dict[str, Any] = Field(default_factory=dict)
    max_users: Optional[int] = None
    features: List[str] = Field(default_factory=list)

class TenantCreate(BaseTenant):
    """Tenant creation model"""
    admin_email: EmailStr
    admin_username: str = Field(..., min_length=3, max_length=50)
    admin_password: str = Field(..., min_length=8)
    admin_first_name: str = Field(..., min_length=1, max_length=100)
    admin_last_name: str = Field(..., min_length=1, max_length=100)

class TenantUpdate(BaseModel):
    """Tenant update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    domain: Optional[str] = Field(None, max_length=255)
    status: Optional[TenantStatus] = None
    settings: Optional[Dict[str, Any]] = None
    max_users: Optional[int] = None
    features: Optional[List[str]] = None

class TenantResponse(BaseTenant):
    """Tenant response model"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    user_count: int = 0
    
    class Config:
        from_attributes = True

class TenantListResponse(BaseModel):
    """Tenant list response model"""
    tenants: List[TenantResponse]
    total: int
    page: int
    size: int
    pages: int

# Authentication models
class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str
    tenant_id: Optional[uuid.UUID] = None
    remember_me: bool = False

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str

class PasswordChangeRequest(BaseModel):
    """Password change request model"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr
    tenant_id: Optional[uuid.UUID] = None

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model"""
    token: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

# Session models
class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    user_id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class SessionListResponse(BaseModel):
    """Session list response model"""
    sessions: List[SessionInfo]
    total: int

# Audit models
class AuditLogEntry(BaseModel):
    """Audit log entry model"""
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    tenant_id: Optional[uuid.UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

class AuditLogListResponse(BaseModel):
    """Audit log list response model"""
    entries: List[AuditLogEntry]
    total: int
    page: int
    size: int
    pages: int

# Health check model
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    service: str
    version: str
    timestamp: datetime
    dependencies: Dict[str, str] = Field(default_factory=dict)

# Error models
class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

# Search and filter models
class UserSearchRequest(BaseModel):
    """User search request model"""
    query: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    tenant_id: Optional[uuid.UUID] = None
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)

class TenantSearchRequest(BaseModel):
    """Tenant search request model"""
    query: Optional[str] = None
    status: Optional[TenantStatus] = None
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)