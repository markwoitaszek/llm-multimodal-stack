"""
User Management API Endpoints
"""
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.models import (
    LoginRequest, LoginResponse, RegisterRequest, UserResponse, UserUpdateRequest,
    PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirmRequest,
    RefreshTokenRequest, LogoutRequest, SessionResponse,
    TenantRequest, TenantResponse, TenantUpdateRequest,
    UserListRequest, UserListResponse, SessionListRequest, SessionListResponse,
    HealthResponse, StatsResponse, ErrorResponse
)
from app.auth import auth_service
from app.database import db_manager
from app.config import settings

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="User Management Service",
    description="Advanced user management system with authentication, authorization, and multi-tenancy",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme
security = HTTPBearer()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize database
        await db_manager.initialize()
        logger.info("Database initialized")
        
        # Create default tenant if it doesn't exist
        default_tenant = await db_manager.get_tenant(settings.default_tenant_id)
        if not default_tenant:
            await db_manager.create_tenant(
                tenant_id=settings.default_tenant_id,
                name="Default Tenant",
                description="Default tenant for the system"
            )
            logger.info("Default tenant created")
        
        logger.info("User Management Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start User Management Service: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await db_manager.close()
        logger.info("User Management Service shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            timestamp=datetime.utcnow()
        ).dict()
    )


# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        user = await auth_service.get_user_from_token(token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Dependency to get current user with role check
async def get_current_user_with_role(required_role: str, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current user and check role permissions"""
    if not auth_service.check_permission(current_user["role"], required_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database health
        db_healthy = True
        try:
            await db_manager.get_user_count()
        except Exception:
            db_healthy = False
        
        overall_status = "healthy" if db_healthy else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            dependencies={
                "database": "healthy" if db_healthy else "unhealthy"
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )


# Authentication endpoints
@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request):
    """User login"""
    try:
        # Get client IP
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")
        
        # Authenticate user
        user = await auth_service.authenticate_user(
            username=request.username,
            password=request.password,
            ip_address=ip_address
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create session
        access_token, refresh_token, session_id = await auth_service.create_user_session(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Create user response
        user_response = UserResponse(
            user_id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            phone=user["phone"],
            role=user["role"],
            status=user["status"],
            tenant_id=user["tenant_id"],
            auth_provider=user["auth_provider"],
            email_verified=user["email_verified"],
            phone_verified=user["phone_verified"],
            last_login=user["last_login"],
            created_at=user["created_at"],
            updated_at=user["updated_at"],
            metadata=user["metadata"]
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    """User registration"""
    try:
        # Validate password strength
        is_valid, message = auth_service.validate_password_strength(request.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Check if username already exists
        existing_user = await db_manager.get_user_by_username(request.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email already exists
        existing_email = await db_manager.get_user_by_email(request.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Hash password
        password_hash = auth_service.get_password_hash(request.password)
        
        # Create user
        user_id = str(uuid.uuid4())
        tenant_id = request.tenant_id or settings.default_tenant_id
        
        success = await db_manager.create_user(
            user_id=user_id,
            username=request.username,
            email=request.email,
            password_hash=password_hash,
            full_name=request.full_name,
            phone=request.phone,
            tenant_id=tenant_id,
            metadata=request.metadata
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Get created user
        user = await db_manager.get_user_by_id(user_id)
        
        return UserResponse(
            user_id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            phone=user["phone"],
            role=user["role"],
            status=user["status"],
            tenant_id=user["tenant_id"],
            auth_provider=user["auth_provider"],
            email_verified=user["email_verified"],
            phone_verified=user["phone_verified"],
            last_login=user["last_login"],
            created_at=user["created_at"],
            updated_at=user["updated_at"],
            metadata=user["metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@app.post("/api/v1/auth/refresh", response_model=Dict[str, str])
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token"""
    try:
        result = await auth_service.refresh_access_token(request.refresh_token)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        access_token, session_id = result
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@app.post("/api/v1/auth/logout")
async def logout(request: LogoutRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """User logout"""
    try:
        if request.logout_all_sessions:
            # Logout all user sessions
            count = await auth_service.logout_all_user_sessions(current_user["id"])
            return {"message": f"Logged out from {count} sessions"}
        elif request.session_id:
            # Logout specific session
            success = await auth_service.logout_user(request.session_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            return {"message": "Logged out successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either session_id or logout_all_sessions must be provided"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


# User management endpoints
@app.get("/api/v1/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        user_id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        phone=current_user["phone"],
        role=current_user["role"],
        status=current_user["status"],
        tenant_id=current_user["tenant_id"],
        auth_provider=current_user["auth_provider"],
        email_verified=current_user["email_verified"],
        phone_verified=current_user["phone_verified"],
        last_login=current_user["last_login"],
        created_at=current_user["created_at"],
        updated_at=current_user["updated_at"],
        metadata=current_user["metadata"]
    )


@app.put("/api/v1/users/me", response_model=UserResponse)
async def update_current_user(request: UserUpdateRequest, 
                            current_user: Dict[str, Any] = Depends(get_current_user)):
    """Update current user information"""
    try:
        # Update user
        success = await db_manager.update_user(
            current_user["id"],
            full_name=request.full_name,
            phone=request.phone,
            metadata=request.metadata
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
        
        # Get updated user
        user = await db_manager.get_user_by_id(current_user["id"])
        
        return UserResponse(
            user_id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            phone=user["phone"],
            role=user["role"],
            status=user["status"],
            tenant_id=user["tenant_id"],
            auth_provider=user["auth_provider"],
            email_verified=user["email_verified"],
            phone_verified=user["phone_verified"],
            last_login=user["last_login"],
            created_at=user["created_at"],
            updated_at=user["updated_at"],
            metadata=user["metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update failed"
        )


@app.post("/api/v1/users/change-password")
async def change_password(request: PasswordChangeRequest, 
                         current_user: Dict[str, Any] = Depends(get_current_user)):
    """Change user password"""
    try:
        # Get user with password hash
        user = await db_manager.get_user_by_id(current_user["id"])
        
        # Verify current password
        if not auth_service.verify_password(request.current_password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        is_valid, message = auth_service.validate_password_strength(request.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Hash new password
        new_password_hash = auth_service.get_password_hash(request.new_password)
        
        # Update password
        success = await db_manager.update_user(
            current_user["id"],
            password_hash=new_password_hash
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


# Admin endpoints
@app.get("/api/v1/admin/users", response_model=UserListResponse)
async def list_users(request: UserListRequest = Depends(),
                    current_user: Dict[str, Any] = Depends(lambda u: get_current_user_with_role("admin", u))):
    """List users (admin only)"""
    try:
        # Get users
        users_data = await db_manager.search_users(
            tenant_id=request.tenant_id,
            role=request.role.value if request.role else None,
            status=request.status.value if request.status else None,
            search=request.search,
            limit=request.limit,
            offset=request.offset
        )
        
        # Convert to response models
        users = []
        for user_data in users_data:
            user = UserResponse(
                user_id=user_data["id"],
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                phone=user_data["phone"],
                role=user_data["role"],
                status=user_data["status"],
                tenant_id=user_data["tenant_id"],
                auth_provider=user_data["auth_provider"],
                email_verified=user_data["email_verified"],
                phone_verified=user_data["phone_verified"],
                last_login=user_data["last_login"],
                created_at=user_data["created_at"],
                updated_at=user_data["updated_at"],
                metadata=user_data["metadata"]
            )
            users.append(user)
        
        # Get total count
        total_count = await db_manager.get_user_count(request.tenant_id)
        
        return UserListResponse(
            users=users,
            total_count=total_count,
            limit=request.limit,
            offset=request.offset
        )
        
    except Exception as e:
        logger.error(f"List users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


# Statistics endpoint
@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get service statistics"""
    try:
        stats = await db_manager.get_user_stats()
        
        return StatsResponse(
            total_users=stats.get("total_users", 0),
            total_tenants=await db_manager.get_tenant_count(),
            active_sessions=0,  # Could be calculated from active sessions
            users_by_role=stats.get("users_by_role", {}),
            users_by_status=stats.get("users_by_status", {}),
            tenants_by_user_count={},  # Could be calculated
            login_attempts_last_hour=stats.get("login_attempts_last_hour", 0),
            cache_hit_rate=0.0  # Could be calculated
        )
        
    except Exception as e:
        logger.error(f"Get stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "User Management Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }