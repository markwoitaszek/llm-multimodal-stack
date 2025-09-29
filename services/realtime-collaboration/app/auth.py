"""
Authentication Manager for WebSocket connections
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field
import jwt
import hashlib
import secrets

logger = logging.getLogger(__name__)

@dataclass
class UserSession:
    """User session information"""
    user_id: str
    username: str
    email: Optional[str] = None
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True

@dataclass
class AuthToken:
    """Authentication token information"""
    token: str
    user_id: str
    token_type: str = "bearer"
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))
    is_revoked: bool = False

class AuthManager:
    """Manages authentication for WebSocket connections"""
    
    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}
        self.tokens: Dict[str, AuthToken] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids
        self.lock = asyncio.Lock()
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.jwt_algorithm = "HS256"
        self.token_expiration_hours = 24
        self.session_expiration_hours = 8
    
    async def initialize(self):
        """Initialize the authentication manager"""
        logger.info("Authentication manager initialized")
        
        # Create default admin user for testing
        await self._create_default_admin()
    
    async def _create_default_admin(self):
        """Create a default admin user for testing"""
        admin_user = UserSession(
            user_id="admin",
            username="admin",
            email="admin@example.com",
            roles={"admin", "user"},
            permissions={"read", "write", "admin"}
        )
        
        # Create a session for the admin user
        session_id = await self.create_session(admin_user)
        logger.info(f"Created default admin session: {session_id}")
    
    async def create_session(self, user: UserSession) -> str:
        """Create a new user session"""
        try:
            async with self.lock:
                session_id = secrets.token_urlsafe(32)
                
                # Set session expiration
                user.expires_at = datetime.utcnow() + timedelta(hours=self.session_expiration_hours)
                
                # Store session
                self.sessions[session_id] = user
                
                # Update user sessions mapping
                if user.user_id not in self.user_sessions:
                    self.user_sessions[user.user_id] = set()
                self.user_sessions[user.user_id].add(session_id)
                
                logger.info(f"Created session for user {user.username} ({user.user_id})")
                return session_id
                
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get user session by session ID"""
        try:
            async with self.lock:
                if session_id not in self.sessions:
                    return None
                
                session = self.sessions[session_id]
                
                # Check if session is expired
                if session.expires_at and datetime.utcnow() > session.expires_at:
                    await self.revoke_session(session_id)
                    return None
                
                # Update last activity
                session.last_activity = datetime.utcnow()
                
                return session
                
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a user session"""
        try:
            async with self.lock:
                if session_id not in self.sessions:
                    return False
                
                session = self.sessions[session_id]
                
                # Remove from user sessions mapping
                if session.user_id in self.user_sessions:
                    self.user_sessions[session.user_id].discard(session_id)
                    if not self.user_sessions[session.user_id]:
                        del self.user_sessions[session.user_id]
                
                del self.sessions[session_id]
                logger.info(f"Revoked session {session_id} for user {session.user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to revoke session {session_id}: {e}")
            return False
    
    async def revoke_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user"""
        try:
            async with self.lock:
                if user_id not in self.user_sessions:
                    return 0
                
                session_ids = list(self.user_sessions[user_id])
                revoked_count = 0
                
                for session_id in session_ids:
                    if await self.revoke_session(session_id):
                        revoked_count += 1
                
                logger.info(f"Revoked {revoked_count} sessions for user {user_id}")
                return revoked_count
                
        except Exception as e:
            logger.error(f"Failed to revoke sessions for user {user_id}: {e}")
            return 0
    
    async def create_token(self, user_id: str, token_type: str = "bearer") -> str:
        """Create a JWT token for a user"""
        try:
            async with self.lock:
                # Create JWT payload
                payload = {
                    "user_id": user_id,
                    "token_type": token_type,
                    "iat": datetime.utcnow(),
                    "exp": datetime.utcnow() + timedelta(hours=self.token_expiration_hours)
                }
                
                # Generate JWT token
                token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
                
                # Store token information
                auth_token = AuthToken(
                    token=token,
                    user_id=user_id,
                    token_type=token_type
                )
                
                self.tokens[token] = auth_token
                
                logger.info(f"Created token for user {user_id}")
                return token
                
        except Exception as e:
            logger.error(f"Failed to create token for user {user_id}: {e}")
            raise
    
    async def validate_token(self, token: str) -> Optional[UserSession]:
        """Validate a JWT token and return user session"""
        try:
            async with self.lock:
                # Check if token is revoked
                if token in self.tokens and self.tokens[token].is_revoked:
                    return None
                
                # Decode and validate JWT
                try:
                    payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
                    user_id = payload.get("user_id")
                    
                    if not user_id:
                        return None
                    
                    # Get user session
                    session = await self.get_session_by_user_id(user_id)
                    return session
                    
                except jwt.ExpiredSignatureError:
                    logger.warning("Token has expired")
                    return None
                except jwt.InvalidTokenError:
                    logger.warning("Invalid token")
                    return None
                
        except Exception as e:
            logger.error(f"Failed to validate token: {e}")
            return None
    
    async def revoke_token(self, token: str) -> bool:
        """Revoke a JWT token"""
        try:
            async with self.lock:
                if token in self.tokens:
                    self.tokens[token].is_revoked = True
                    logger.info(f"Revoked token for user {self.tokens[token].user_id}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False
    
    async def get_session_by_user_id(self, user_id: str) -> Optional[UserSession]:
        """Get the most recent session for a user"""
        try:
            async with self.lock:
                if user_id not in self.user_sessions:
                    return None
                
                # Get the most recent session
                session_ids = list(self.user_sessions[user_id])
                if not session_ids:
                    return None
                
                # Find the most recent active session
                for session_id in session_ids:
                    if session_id in self.sessions:
                        session = self.sessions[session_id]
                        if session.is_active and (not session.expires_at or datetime.utcnow() <= session.expires_at):
                            return session
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get session for user {user_id}: {e}")
            return None
    
    async def authenticate_user(self, username: str, password: str) -> Optional[UserSession]:
        """Authenticate a user with username and password"""
        try:
            # In a real implementation, this would validate against a database
            # For now, we'll use simple hardcoded credentials
            
            if username == "admin" and password == "admin123":
                return UserSession(
                    user_id="admin",
                    username="admin",
                    email="admin@example.com",
                    roles={"admin", "user"},
                    permissions={"read", "write", "admin"}
                )
            elif username == "user" and password == "user123":
                return UserSession(
                    user_id="user",
                    username="user",
                    email="user@example.com",
                    roles={"user"},
                    permissions={"read", "write"}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to authenticate user {username}: {e}")
            return None
    
    async def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if a user has a specific permission"""
        try:
            session = await self.get_session_by_user_id(user_id)
            if not session:
                return False
            
            return permission in session.permissions
            
        except Exception as e:
            logger.error(f"Failed to check permission for user {user_id}: {e}")
            return False
    
    async def check_role(self, user_id: str, role: str) -> bool:
        """Check if a user has a specific role"""
        try:
            session = await self.get_session_by_user_id(user_id)
            if not session:
                return False
            
            return role in session.roles
            
        except Exception as e:
            logger.error(f"Failed to check role for user {user_id}: {e}")
            return False
    
    async def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for a user"""
        try:
            session = await self.get_session_by_user_id(user_id)
            if not session:
                return set()
            
            return session.permissions
            
        except Exception as e:
            logger.error(f"Failed to get permissions for user {user_id}: {e}")
            return set()
    
    async def get_user_roles(self, user_id: str) -> Set[str]:
        """Get all roles for a user"""
        try:
            session = await self.get_session_by_user_id(user_id)
            if not session:
                return set()
            
            return session.roles
            
        except Exception as e:
            logger.error(f"Failed to get roles for user {user_id}: {e}")
            return set()
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            async with self.lock:
                current_time = datetime.utcnow()
                expired_sessions = []
                
                for session_id, session in self.sessions.items():
                    if session.expires_at and current_time > session.expires_at:
                        expired_sessions.append(session_id)
                
                # Remove expired sessions
                for session_id in expired_sessions:
                    await self.revoke_session(session_id)
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
                return len(expired_sessions)
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens"""
        try:
            async with self.lock:
                current_time = datetime.utcnow()
                expired_tokens = []
                
                for token, auth_token in self.tokens.items():
                    if current_time > auth_token.expires_at:
                        expired_tokens.append(token)
                
                # Remove expired tokens
                for token in expired_tokens:
                    del self.tokens[token]
                
                if expired_tokens:
                    logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
                
                return len(expired_tokens)
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")
            return 0
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        try:
            async with self.lock:
                total_sessions = len(self.sessions)
                total_tokens = len(self.tokens)
                total_users = len(self.user_sessions)
                
                # Count active sessions
                active_sessions = 0
                for session in self.sessions.values():
                    if session.is_active and (not session.expires_at or datetime.utcnow() <= session.expires_at):
                        active_sessions += 1
                
                # Count active tokens
                active_tokens = 0
                for token in self.tokens.values():
                    if not token.is_revoked and datetime.utcnow() <= token.expires_at:
                        active_tokens += 1
                
                return {
                    "total_sessions": total_sessions,
                    "active_sessions": active_sessions,
                    "total_tokens": total_tokens,
                    "active_tokens": active_tokens,
                    "total_users": total_users,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get authentication statistics: {e}")
            return {}
    
    async def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256"""
        try:
            return hashlib.sha256(password.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Failed to hash password: {e}")
            raise
    
    async def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return await self.hash_password(password) == hashed_password
        except Exception as e:
            logger.error(f"Failed to verify password: {e}")
            return False