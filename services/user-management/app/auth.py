"""
Authentication and Authorization Service
"""
import asyncio
import time
import uuid
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import logging

from app.config import settings
from app.models import UserRole, UserStatus, AuthProvider
from app.database import db_manager

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication and authorization service"""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if len(password) < settings.password_min_length:
            return False, f"Password must be at least {settings.password_min_length} characters long"
        
        if settings.password_require_uppercase and not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if settings.password_require_lowercase and not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if settings.password_require_numbers and not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        if settings.password_require_special_chars and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is valid"
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
                return None
            
            return payload
        except JWTError:
            return None
    
    async def authenticate_user(self, username: str, password: str, 
                              ip_address: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Authenticate user with username/email and password"""
        try:
            # Get user by username or email
            user = await db_manager.get_user_by_username(username)
            if not user:
                user = await db_manager.get_user_by_email(username)
            
            if not user:
                # Log failed attempt
                if ip_address:
                    await db_manager.log_login_attempt(username, ip_address, False, "User not found")
                return None
            
            # Check if user is locked
            if user.get("locked_until") and datetime.utcnow() < user["locked_until"]:
                if ip_address:
                    await db_manager.log_login_attempt(username, ip_address, False, "Account locked")
                return None
            
            # Check user status
            if user["status"] != UserStatus.ACTIVE.value:
                if ip_address:
                    await db_manager.log_login_attempt(username, ip_address, False, f"Account {user['status']}")
                return None
            
            # Verify password
            if not self.verify_password(password, user["password_hash"]):
                # Increment failed attempts
                failed_attempts = user.get("failed_login_attempts", 0) + 1
                
                # Lock account if max attempts reached
                if failed_attempts >= settings.max_login_attempts:
                    locked_until = datetime.utcnow() + timedelta(minutes=settings.lockout_duration_minutes)
                    await db_manager.update_user(user["id"], locked_until=locked_until)
                
                await db_manager.update_user(user["id"], failed_login_attempts=failed_attempts)
                
                if ip_address:
                    await db_manager.log_login_attempt(username, ip_address, False, "Invalid password")
                return None
            
            # Successful login - reset failed attempts
            await db_manager.update_user(
                user["id"], 
                failed_login_attempts=0,
                locked_until=None,
                last_login=datetime.utcnow()
            )
            
            if ip_address:
                await db_manager.log_login_attempt(username, ip_address, True)
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None
    
    async def create_user_session(self, user: Dict[str, Any], ip_address: Optional[str] = None,
                                user_agent: Optional[str] = None) -> Tuple[str, str, str]:
        """Create user session and return tokens"""
        try:
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Create tokens
            token_data = {
                "sub": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "tenant_id": user["tenant_id"],
                "session_id": session_id
            }
            
            access_token = self.create_access_token(token_data)
            refresh_token = self.create_refresh_token({"sub": user["id"], "session_id": session_id})
            
            # Calculate session expiration
            expires_at = datetime.utcnow() + timedelta(minutes=settings.session_timeout_minutes)
            
            # Create session in database
            await db_manager.create_session(
                session_id=session_id,
                user_id=user["id"],
                tenant_id=user["tenant_id"],
                refresh_token=refresh_token,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return access_token, refresh_token, session_id
            
        except Exception as e:
            logger.error(f"Session creation error: {str(e)}")
            raise Exception(f"Failed to create session: {str(e)}")
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token, "refresh")
            if not payload:
                return None
            
            user_id = payload.get("sub")
            session_id = payload.get("session_id")
            
            if not user_id or not session_id:
                return None
            
            # Get session
            session = await db_manager.get_session(session_id)
            if not session or not session["is_active"]:
                return None
            
            # Check if session is expired
            if datetime.utcnow() > session["expires_at"]:
                await db_manager.deactivate_session(session_id)
                return None
            
            # Get user
            user = await db_manager.get_user_by_id(user_id)
            if not user or user["status"] != UserStatus.ACTIVE.value:
                return None
            
            # Create new access token
            token_data = {
                "sub": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "tenant_id": user["tenant_id"],
                "session_id": session_id
            }
            
            access_token = self.create_access_token(token_data)
            
            # Update session activity
            await db_manager.update_session_activity(session_id)
            
            return access_token, session_id
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return None
    
    async def logout_user(self, session_id: str) -> bool:
        """Logout user by deactivating session"""
        try:
            return await db_manager.deactivate_session(session_id)
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return False
    
    async def logout_all_user_sessions(self, user_id: str) -> int:
        """Logout all user sessions"""
        try:
            return await db_manager.deactivate_user_sessions(user_id)
        except Exception as e:
            logger.error(f"Logout all sessions error: {str(e)}")
            return 0
    
    async def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session and return user info"""
        try:
            # Get session
            session = await db_manager.get_session(session_id)
            if not session or not session["is_active"]:
                return None
            
            # Check if session is expired
            if datetime.utcnow() > session["expires_at"]:
                await db_manager.deactivate_session(session_id)
                return None
            
            # Get user
            user = await db_manager.get_user_by_id(session["user_id"])
            if not user or user["status"] != UserStatus.ACTIVE.value:
                return None
            
            # Update session activity
            await db_manager.update_session_activity(session_id)
            
            return {
                "user": user,
                "session": session
            }
            
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return None
    
    async def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from access token"""
        try:
            payload = self.verify_token(token, "access")
            if not payload:
                return None
            
            session_id = payload.get("session_id")
            if not session_id:
                return None
            
            # Validate session
            session_info = await self.validate_session(session_id)
            if not session_info:
                return None
            
            return session_info["user"]
            
        except Exception as e:
            logger.error(f"Get user from token error: {str(e)}")
            return None
    
    def check_permission(self, user_role: str, required_role: str) -> bool:
        """Check if user role has required permission"""
        role_hierarchy = {
            UserRole.GUEST.value: 0,
            UserRole.USER.value: 1,
            UserRole.MODERATOR.value: 2,
            UserRole.ADMIN.value: 3
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            return await db_manager.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Session cleanup error: {str(e)}")
            return 0


# Global auth service instance
auth_service = AuthService()