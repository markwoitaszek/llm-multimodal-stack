"""
Authentication and authorization logic for user management service
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import jwt
import bcrypt
import secrets
import uuid
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt as jose_jwt

from .config import settings
from .models import UserRole, UserStatus, TokenType
from .database import db_manager, get_user_by_id, create_audit_log

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT security scheme
security = HTTPBearer()

class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "type": TokenType.ACCESS,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "type": TokenType.REFRESH,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: TokenType = TokenType.ACCESS) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def generate_password_reset_token(self) -> str:
        """Generate a secure password reset token"""
        return secrets.token_urlsafe(32)
    
    def create_tokens(self, user_id: str, tenant_id: Optional[str] = None, role: str = UserRole.USER) -> Tuple[str, str]:
        """Create both access and refresh tokens"""
        token_data = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "role": role
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        return access_token, refresh_token

# Global auth manager instance
auth_manager = AuthManager()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = auth_manager.verify_token(token, TokenType.ACCESS)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_user_by_id(uuid.UUID(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user["status"] != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user"""
    if current_user["status"] != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current admin user"""
    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

def require_role(required_role: UserRole):
    """Decorator to require specific role"""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if current_user["role"] != required_role and current_user["role"] != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role or higher"
            )
        return current_user
    return role_checker

def require_any_role(*roles: UserRole):
    """Decorator to require any of the specified roles"""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if current_user["role"] not in roles and current_user["role"] != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of the following roles: {', '.join(roles)}"
            )
        return current_user
    return role_checker

async def check_user_permissions(
    current_user: Dict[str, Any],
    target_user_id: Optional[uuid.UUID] = None,
    target_tenant_id: Optional[uuid.UUID] = None,
    required_role: Optional[UserRole] = None
) -> bool:
    """Check if user has permissions for the requested action"""
    
    # Admin users have all permissions
    if current_user["role"] == UserRole.ADMIN:
        return True
    
    # Check role requirement
    if required_role and current_user["role"] != required_role:
        return False
    
    # Check tenant access
    if target_tenant_id and current_user["tenant_id"] != target_tenant_id:
        return False
    
    # Check user access (users can only access their own data unless they're admin/moderator)
    if target_user_id and current_user["id"] != target_user_id:
        if current_user["role"] not in [UserRole.ADMIN, UserRole.MODERATOR]:
            return False
    
    return True

async def authenticate_user(email: str, password: str, tenant_id: Optional[uuid.UUID] = None) -> Optional[Dict[str, Any]]:
    """Authenticate user with email and password"""
    try:
        user = await get_user_by_email(email, tenant_id)
        if not user:
            return None
        
        # Check if user is locked
        if user["locked_until"] and datetime.utcnow() < user["locked_until"]:
            logger.warning(f"Login attempt for locked user: {email}")
            return None
        
        # Check if user is active
        if user["status"] != UserStatus.ACTIVE:
            logger.warning(f"Login attempt for inactive user: {email}")
            return None
        
        # Verify password
        if not auth_manager.verify_password(password, user["password_hash"]):
            # Increment login attempts
            await increment_login_attempts(user["id"])
            logger.warning(f"Invalid password for user: {email}")
            return None
        
        # Reset login attempts on successful login
        await reset_login_attempts(user["id"])
        
        # Update last login
        await update_last_login(user["id"])
        
        return user
        
    except Exception as e:
        logger.error(f"Authentication error for user {email}: {e}")
        return None

async def increment_login_attempts(user_id: uuid.UUID):
    """Increment login attempts for user"""
    query = """
        UPDATE users 
        SET login_attempts = login_attempts + 1,
            locked_until = CASE 
                WHEN login_attempts + 1 >= $2 THEN NOW() + INTERVAL '$3 minutes'
                ELSE locked_until
            END
        WHERE id = $1
    """
    await db_manager.execute_command(
        query,
        user_id,
        settings.max_login_attempts,
        settings.lockout_duration_minutes
    )

async def reset_login_attempts(user_id: uuid.UUID):
    """Reset login attempts for user"""
    query = """
        UPDATE users 
        SET login_attempts = 0, locked_until = NULL
        WHERE id = $1
    """
    await db_manager.execute_command(query, user_id)

async def update_last_login(user_id: uuid.UUID):
    """Update last login timestamp for user"""
    query = """
        UPDATE users 
        SET last_login = NOW()
        WHERE id = $1
    """
    await db_manager.execute_command(query, user_id)

async def create_user_session(
    user_id: uuid.UUID,
    tenant_id: Optional[uuid.UUID],
    access_token: str,
    refresh_token: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> str:
    """Create user session"""
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    
    query = """
        INSERT INTO user_sessions (id, user_id, tenant_id, session_token, refresh_token, expires_at, ip_address, user_agent)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """
    await db_manager.execute_command(
        query,
        session_id,
        user_id,
        tenant_id,
        access_token,
        refresh_token,
        expires_at,
        ip_address,
        user_agent
    )
    
    return session_id

async def get_user_session(session_token: str) -> Optional[Dict[str, Any]]:
    """Get user session by token"""
    query = """
        SELECT s.*, u.email, u.username, u.role, u.status
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_token = $1 AND s.is_active = true AND s.expires_at > NOW()
    """
    return await db_manager.execute_one(query, session_token)

async def invalidate_user_session(session_token: str):
    """Invalidate user session"""
    query = """
        UPDATE user_sessions 
        SET is_active = false
        WHERE session_token = $1
    """
    await db_manager.execute_command(query, session_token)

async def invalidate_all_user_sessions(user_id: uuid.UUID):
    """Invalidate all sessions for a user"""
    query = """
        UPDATE user_sessions 
        SET is_active = false
        WHERE user_id = $1
    """
    await db_manager.execute_command(query, user_id)

async def cleanup_expired_sessions():
    """Clean up expired sessions"""
    query = """
        UPDATE user_sessions 
        SET is_active = false
        WHERE expires_at < NOW() AND is_active = true
    """
    await db_manager.execute_command(query)

async def log_auth_event(
    user_id: Optional[uuid.UUID],
    tenant_id: Optional[uuid.UUID],
    action: str,
    success: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Log authentication event"""
    await create_audit_log(
        user_id=user_id,
        tenant_id=tenant_id,
        action=action,
        resource_type="auth",
        resource_id=str(user_id) if user_id else None,
        details={
            "success": success,
            **(details or {})
        },
        ip_address=ip_address,
        user_agent=user_agent
    )

# Rate limiting functions
class RateLimiter:
    """Simple rate limiter using Redis"""
    
    def __init__(self):
        self.redis = None
    
    async def is_allowed(self, key: str, limit: int, window_minutes: int) -> bool:
        """Check if request is allowed based on rate limit"""
        # This would be implemented with Redis
        # For now, return True (no rate limiting)
        return True
    
    async def increment(self, key: str, window_minutes: int):
        """Increment rate limit counter"""
        # This would be implemented with Redis
        pass

rate_limiter = RateLimiter()

async def check_rate_limit(identifier: str, limit: int = None, window_minutes: int = None) -> bool:
    """Check rate limit for identifier"""
    if limit is None:
        limit = settings.rate_limit_requests
    if window_minutes is None:
        window_minutes = settings.rate_limit_window_minutes
    
    return await rate_limiter.is_allowed(identifier, limit, window_minutes)