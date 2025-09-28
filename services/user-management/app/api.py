"""
FastAPI routes and endpoints for user management service
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    TenantCreate, TenantUpdate, TenantResponse, TenantListResponse,
    LoginRequest, TokenResponse, RefreshTokenRequest, PasswordChangeRequest,
    PasswordResetRequest, PasswordResetConfirm, SessionListResponse,
    AuditLogListResponse, HealthResponse, ErrorResponse,
    UserSearchRequest, TenantSearchRequest, UserRole, UserStatus, TenantStatus
)
from .auth import (
    auth_manager, get_current_user, get_current_active_user, get_current_admin_user,
    authenticate_user, create_user_session, invalidate_user_session,
    invalidate_all_user_sessions, log_auth_event, check_rate_limit
)
from .user_manager import user_manager
from .tenant_manager import tenant_manager
from .cache import cache_manager, get_cache_stats

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Security scheme
security = HTTPBearer()

# Helper functions
def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def get_user_agent(request: Request) -> str:
    """Get user agent"""
    return request.headers.get("User-Agent", "unknown")

# Authentication endpoints
@router.post("/api/v1/auth/register", response_model=TokenResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    response: Response
):
    """Register a new user"""
    try:
        # Check rate limit
        client_ip = get_client_ip(request)
        if not await check_rate_limit(f"register:{client_ip}"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many registration attempts"
            )
        
        # Create user
        user = await user_manager.create_user(
            user_data,
            ip_address=client_ip,
            user_agent=get_user_agent(request)
        )
        
        # Create tokens
        access_token, refresh_token = auth_manager.create_tokens(
            str(user.id),
            str(user.tenant_id) if user.tenant_id else None,
            user.role.value
        )
        
        # Create session
        await create_user_session(
            user.id,
            user.tenant_id,
            access_token,
            refresh_token,
            client_ip,
            get_user_agent(request)
        )
        
        # Log auth event
        await log_auth_event(
            user.id,
            user.tenant_id,
            "user_registered",
            True,
            client_ip,
            get_user_agent(request)
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=user
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    response: Response
):
    """Login user"""
    try:
        # Check rate limit
        client_ip = get_client_ip(request)
        if not await check_rate_limit(f"login:{client_ip}"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts"
            )
        
        # Authenticate user
        user = await authenticate_user(
            login_data.email,
            login_data.password,
            login_data.tenant_id
        )
        
        if not user:
            # Log failed login
            await log_auth_event(
                None,
                login_data.tenant_id,
                "login_failed",
                False,
                client_ip,
                get_user_agent(request),
                {"email": login_data.email}
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create tokens
        access_token, refresh_token = auth_manager.create_tokens(
            str(user["id"]),
            str(user["tenant_id"]) if user["tenant_id"] else None,
            user["role"]
        )
        
        # Create session
        await create_user_session(
            user["id"],
            user["tenant_id"],
            access_token,
            refresh_token,
            client_ip,
            get_user_agent(request)
        )
        
        # Log successful login
        await log_auth_event(
            user["id"],
            user["tenant_id"],
            "login_success",
            True,
            client_ip,
            get_user_agent(request)
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=UserResponse(**user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/api/v1/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request
):
    """Refresh access token"""
    try:
        # Verify refresh token
        payload = auth_manager.verify_token(refresh_data.refresh_token, "refresh")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = await user_manager.get_user(uuid.UUID(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new tokens
        access_token, refresh_token = auth_manager.create_tokens(
            str(user.id),
            str(user.tenant_id) if user.tenant_id else None,
            user.role.value
        )
        
        # Update session
        await create_user_session(
            user.id,
            user.tenant_id,
            access_token,
            refresh_token,
            get_client_ip(request),
            get_user_agent(request)
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )

@router.post("/api/v1/auth/logout")
async def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Logout user"""
    try:
        # Get token from request
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            await invalidate_user_session(token)
        
        # Log logout event
        await log_auth_event(
            current_user["id"],
            current_user.get("tenant_id"),
            "logout",
            True,
            get_client_ip(request),
            get_user_agent(request)
        )
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

# User endpoints
@router.get("/api/v1/users/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get current user profile"""
    return UserResponse(**current_user)

@router.put("/api/v1/users/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Update current user profile"""
    try:
        user = await user_manager.update_user(
            current_user["id"],
            user_data,
            current_user,
            get_client_ip(request),
            get_user_agent(request)
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@router.post("/api/v1/users/me/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Change user password"""
    try:
        success = await user_manager.change_password(
            current_user["id"],
            password_data.current_password,
            password_data.new_password,
            current_user,
            get_client_ip(request),
            get_user_agent(request)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed"
            )
        
        return {"message": "Password changed successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.get("/api/v1/users", response_model=UserListResponse)
async def list_users(
    search_request: UserSearchRequest = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List users with search and pagination"""
    try:
        # Check permissions
        if current_user["role"] not in [UserRole.ADMIN, UserRole.MODERATOR]:
            # Regular users can only see themselves
            if search_request.query and search_request.query not in [current_user["email"], current_user["username"]]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            search_request.tenant_id = current_user.get("tenant_id")
        
        users = await user_manager.search_users(
            query=search_request.query,
            role=search_request.role,
            status=search_request.status,
            tenant_id=search_request.tenant_id,
            page=search_request.page,
            size=search_request.size,
            current_user=current_user
        )
        
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User list failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User list failed"
        )

@router.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user by ID"""
    try:
        user = await user_manager.get_user(user_id, current_user)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Get user failed"
        )

@router.put("/api/v1/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user"""
    try:
        user = await user_manager.update_user(
            user_id,
            user_data,
            current_user,
            get_client_ip(request),
            get_user_agent(request)
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"User update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )

@router.delete("/api/v1/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete user"""
    try:
        success = await user_manager.delete_user(
            user_id,
            current_user,
            get_client_ip(request),
            get_user_agent(request)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"User deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )

# Tenant endpoints
@router.post("/api/v1/tenants", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Create a new tenant"""
    try:
        tenant, admin_user = await tenant_manager.create_tenant(
            tenant_data,
            current_user["id"],
            get_client_ip(request),
            get_user_agent(request)
        )
        
        return tenant
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Tenant creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant creation failed"
        )

@router.get("/api/v1/tenants", response_model=TenantListResponse)
async def list_tenants(
    search_request: TenantSearchRequest = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """List tenants with search and pagination"""
    try:
        tenants = await tenant_manager.search_tenants(
            query=search_request.query,
            status=search_request.status,
            page=search_request.page,
            size=search_request.size,
            current_user=current_user
        )
        
        return tenants
        
    except Exception as e:
        logger.error(f"Tenant list failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant list failed"
        )

@router.get("/api/v1/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get tenant by ID"""
    try:
        tenant = await tenant_manager.get_tenant(tenant_id, current_user)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        return tenant
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get tenant failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Get tenant failed"
        )

@router.put("/api/v1/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: uuid.UUID,
    tenant_data: TenantUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update tenant"""
    try:
        tenant = await tenant_manager.update_tenant(
            tenant_id,
            tenant_data,
            current_user,
            get_client_ip(request),
            get_user_agent(request)
        )
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        return tenant
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Tenant update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant update failed"
        )

@router.delete("/api/v1/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: uuid.UUID,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Delete tenant"""
    try:
        success = await tenant_manager.delete_tenant(
            tenant_id,
            current_user,
            get_client_ip(request),
            get_user_agent(request)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        return {"message": "Tenant deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Tenant deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant deletion failed"
        )

# Health check endpoint
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_status = "connected"
        try:
            from .database import db_manager
            await db_manager.execute_one("SELECT 1")
        except Exception:
            db_status = "disconnected"
        
        # Check Redis connection
        cache_status = "connected"
        try:
            await cache_manager.redis.ping()
        except Exception:
            cache_status = "disconnected"
        
        return HealthResponse(
            status="healthy" if db_status == "connected" and cache_status == "connected" else "unhealthy",
            service=settings.service_name,
            version=settings.app_version,
            timestamp=datetime.utcnow(),
            dependencies={
                "database": db_status,
                "cache": cache_status
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service=settings.service_name,
            version=settings.app_version,
            timestamp=datetime.utcnow(),
            dependencies={"error": str(e)}
        )

# Cache stats endpoint (admin only)
@router.get("/api/v1/cache/stats")
async def get_cache_statistics(
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Get cache statistics"""
    try:
        stats = await get_cache_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Cache stats failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cache stats failed"
        )

# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return ErrorResponse(
        error=exc.detail,
        message=exc.detail,
        timestamp=datetime.utcnow()
    )

@router.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return ErrorResponse(
        error="Internal server error",
        message="An unexpected error occurred",
        timestamp=datetime.utcnow()
    )