#!/usr/bin/env python3
"""
Authentication and Authorization Management System
Part of Issue #54: Authentication & API Gateway Dependencies

This module provides comprehensive authentication and authorization including:
- JWT-based authentication with role-based access control
- User management and profile handling
- Token generation, validation, and refresh
- Password hashing and security
- Session management
- Multi-factor authentication support
"""

import asyncio
import json
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from pathlib import Path
import jwt
import bcrypt
from cryptography.fernet import Fernet
import qrcode
import io
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    DEVELOPER = "developer"
    OPERATOR = "operator"

class UserStatus(Enum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class TokenType(Enum):
    """Token type enumeration"""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"
    VERIFICATION = "verification"

class AuthProvider(Enum):
    """Authentication provider enumeration"""
    LOCAL = "local"
    LDAP = "ldap"
    OAUTH2 = "oauth2"
    SAML = "saml"

@dataclass
class User:
    """User data model"""
    user_id: str
    username: str
    email: str
    password_hash: str
    role: UserRole
    status: UserStatus
    created_at: str
    last_login: Optional[str] = None
    profile: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    failed_login_attempts: int = 0
    locked_until: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.LOCAL
    external_id: Optional[str] = None

@dataclass
class Token:
    """Token data model"""
    token_id: str
    user_id: str
    token_type: TokenType
    token_value: str
    expires_at: str
    created_at: str
    is_revoked: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Session:
    """Session data model"""
    session_id: str
    user_id: str
    created_at: str
    last_activity: str
    expires_at: str
    ip_address: str
    user_agent: str
    is_active: bool = True

@dataclass
class Permission:
    """Permission data model"""
    permission_id: str
    name: str
    description: str
    resource: str
    action: str
    conditions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Role:
    """Role data model"""
    role_id: str
    name: str
    description: str
    permissions: List[str] = field(default_factory=list)
    is_system_role: bool = False

class AuthManager:
    """Manages authentication and authorization"""
    
    def __init__(self, data_dir: Path, secret_key: Optional[str] = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # JWT configuration
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        
        # Encryption for sensitive data
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Storage
        self.users: Dict[str, User] = {}
        self.tokens: Dict[str, Token] = {}
        self.sessions: Dict[str, Session] = {}
        self.permissions: Dict[str, Permission] = {}
        self.roles: Dict[str, Role] = {}
        
        # Configuration files
        self.users_file = self.data_dir / "users.json"
        self.tokens_file = self.data_dir / "tokens.json"
        self.sessions_file = self.data_dir / "sessions.json"
        self.permissions_file = self.data_dir / "permissions.json"
        self.roles_file = self.data_dir / "roles.json"
        
        # Load existing data
        self._load_data()
        
        # Initialize default roles and permissions
        self._initialize_default_roles()
    
    def _load_data(self):
        """Load authentication data from files"""
        try:
            # Load users
            if self.users_file.exists():
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    for user_id, user_data in data.items():
                        user_data['role'] = UserRole(user_data['role'])
                        user_data['status'] = UserStatus(user_data['status'])
                        user_data['auth_provider'] = AuthProvider(user_data['auth_provider'])
                        self.users[user_id] = User(**user_data)
            
            # Load tokens
            if self.tokens_file.exists():
                with open(self.tokens_file, 'r') as f:
                    data = json.load(f)
                    for token_id, token_data in data.items():
                        token_data['token_type'] = TokenType(token_data['token_type'])
                        self.tokens[token_id] = Token(**token_data)
            
            # Load sessions
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r') as f:
                    data = json.load(f)
                    for session_id, session_data in data.items():
                        self.sessions[session_id] = Session(**session_data)
            
            # Load permissions
            if self.permissions_file.exists():
                with open(self.permissions_file, 'r') as f:
                    data = json.load(f)
                    for perm_id, perm_data in data.items():
                        self.permissions[perm_id] = Permission(**perm_data)
            
            # Load roles
            if self.roles_file.exists():
                with open(self.roles_file, 'r') as f:
                    data = json.load(f)
                    for role_id, role_data in data.items():
                        self.roles[role_id] = Role(**role_data)
            
            logger.info(f"Loaded {len(self.users)} users, {len(self.tokens)} tokens, {len(self.sessions)} sessions")
            
        except Exception as e:
            logger.error(f"Error loading authentication data: {e}")
    
    def _save_data(self):
        """Save authentication data to files"""
        try:
            # Save users
            users_data = {}
            for user_id, user in self.users.items():
                user_dict = asdict(user)
                user_dict['role'] = user.role.value
                user_dict['status'] = user.status.value
                user_dict['auth_provider'] = user.auth_provider.value
                users_data[user_id] = user_dict
            
            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2)
            
            # Save tokens
            tokens_data = {}
            for token_id, token in self.tokens.items():
                token_dict = asdict(token)
                token_dict['token_type'] = token.token_type.value
                tokens_data[token_id] = token_dict
            
            with open(self.tokens_file, 'w') as f:
                json.dump(tokens_data, f, indent=2)
            
            # Save sessions
            sessions_data = {session_id: asdict(session) for session_id, session in self.sessions.items()}
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
            
            # Save permissions
            permissions_data = {perm_id: asdict(perm) for perm_id, perm in self.permissions.items()}
            with open(self.permissions_file, 'w') as f:
                json.dump(permissions_data, f, indent=2)
            
            # Save roles
            roles_data = {role_id: asdict(role) for role_id, role in self.roles.items()}
            with open(self.roles_file, 'w') as f:
                json.dump(roles_data, f, indent=2)
            
            logger.info("Authentication data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving authentication data: {e}")
    
    def _initialize_default_roles(self):
        """Initialize default roles and permissions"""
        if not self.roles:
            # Create default permissions
            permissions = [
                Permission("read_users", "Read Users", "Read user information", "users", "read"),
                Permission("write_users", "Write Users", "Create and update users", "users", "write"),
                Permission("delete_users", "Delete Users", "Delete users", "users", "delete"),
                Permission("read_configs", "Read Configs", "Read configurations", "configs", "read"),
                Permission("write_configs", "Write Configs", "Create and update configurations", "configs", "write"),
                Permission("delete_configs", "Delete Configs", "Delete configurations", "configs", "delete"),
                Permission("read_deployments", "Read Deployments", "Read deployment information", "deployments", "read"),
                Permission("write_deployments", "Write Deployments", "Create and manage deployments", "deployments", "write"),
                Permission("read_monitoring", "Read Monitoring", "Read monitoring data", "monitoring", "read"),
                Permission("write_monitoring", "Write Monitoring", "Manage monitoring settings", "monitoring", "write"),
                Permission("admin_access", "Admin Access", "Full administrative access", "*", "*")
            ]
            
            for perm in permissions:
                self.permissions[perm.permission_id] = perm
            
            # Create default roles
            roles = [
                Role(
                    "admin",
                    "Administrator",
                    "Full system access",
                    [perm.permission_id for perm in permissions],
                    is_system_role=True
                ),
                Role(
                    "developer",
                    "Developer",
                    "Development and deployment access",
                    ["read_users", "read_configs", "write_configs", "read_deployments", "write_deployments", "read_monitoring"]
                ),
                Role(
                    "operator",
                    "Operator",
                    "Operations and monitoring access",
                    ["read_users", "read_configs", "read_deployments", "read_monitoring", "write_monitoring"]
                ),
                Role(
                    "viewer",
                    "Viewer",
                    "Read-only access",
                    ["read_users", "read_configs", "read_deployments", "read_monitoring"]
                )
            ]
            
            for role in roles:
                self.roles[role.role_id] = role
            
            self._save_data()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _generate_jwt_token(self, user_id: str, token_type: TokenType, expires_delta: Optional[timedelta] = None) -> str:
        """Generate JWT token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            if token_type == TokenType.ACCESS:
                expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            else:
                expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "user_id": user_id,
            "token_type": token_type.value,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def _verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.USER,
        profile: Dict[str, Any] = None,
        auth_provider: AuthProvider = AuthProvider.LOCAL,
        external_id: Optional[str] = None
    ) -> User:
        """Create a new user"""
        # Check if user already exists
        for user in self.users.values():
            if user.username == username or user.email == email:
                raise ValueError("User with this username or email already exists")
        
        user_id = str(uuid.uuid4())
        password_hash = self._hash_password(password)
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            status=UserStatus.ACTIVE,
            created_at=datetime.now().isoformat(),
            profile=profile or {},
            auth_provider=auth_provider,
            external_id=external_id
        )
        
        # Add role permissions
        if role.value in self.roles:
            user.permissions = self.roles[role.value].permissions.copy()
        
        self.users[user_id] = user
        self._save_data()
        
        logger.info(f"Created user: {username}")
        return user
    
    def authenticate_user(self, username: str, password: str, ip_address: str = "", user_agent: str = "") -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password"""
        # Find user by username or email
        user = None
        for u in self.users.values():
            if u.username == username or u.email == username:
                user = u
                break
        
        if not user:
            logger.warning(f"Authentication failed: user not found - {username}")
            return None
        
        # Check if user is locked
        if user.locked_until:
            locked_until = datetime.fromisoformat(user.locked_until)
            if datetime.now() < locked_until:
                logger.warning(f"Authentication failed: user locked - {username}")
                return None
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            logger.warning(f"Authentication failed: user not active - {username}")
            return None
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock user after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = (datetime.now() + timedelta(minutes=30)).isoformat()
                logger.warning(f"User locked due to failed login attempts - {username}")
            
            self._save_data()
            logger.warning(f"Authentication failed: invalid password - {username}")
            return None
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now().isoformat()
        
        # Generate tokens
        access_token = self._generate_jwt_token(user.user_id, TokenType.ACCESS)
        refresh_token = self._generate_jwt_token(user.user_id, TokenType.REFRESH)
        
        # Store tokens
        access_token_obj = Token(
            token_id=str(uuid.uuid4()),
            user_id=user.user_id,
            token_type=TokenType.ACCESS,
            token_value=access_token,
            expires_at=(datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)).isoformat(),
            created_at=datetime.now().isoformat()
        )
        
        refresh_token_obj = Token(
            token_id=str(uuid.uuid4()),
            user_id=user.user_id,
            token_type=TokenType.REFRESH,
            token_value=refresh_token,
            expires_at=(datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)).isoformat(),
            created_at=datetime.now().isoformat()
        )
        
        self.tokens[access_token_obj.token_id] = access_token_obj
        self.tokens[refresh_token_obj.token_id] = refresh_token_obj
        
        # Create session
        session = Session(
            session_id=str(uuid.uuid4()),
            user_id=user.user_id,
            created_at=datetime.now().isoformat(),
            last_activity=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(days=7)).isoformat(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[session.session_id] = session
        
        self._save_data()
        
        logger.info(f"User authenticated successfully: {username}")
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session_id": session.session_id,
            "expires_in": self.access_token_expire_minutes * 60
        }
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token"""
        # Verify refresh token
        payload = self._verify_jwt_token(refresh_token)
        if not payload or payload.get("token_type") != TokenType.REFRESH.value:
            return None
        
        user_id = payload.get("user_id")
        if not user_id or user_id not in self.users:
            return None
        
        user = self.users[user_id]
        if user.status != UserStatus.ACTIVE:
            return None
        
        # Generate new access token
        access_token = self._generate_jwt_token(user_id, TokenType.ACCESS)
        
        # Store new token
        access_token_obj = Token(
            token_id=str(uuid.uuid4()),
            user_id=user_id,
            token_type=TokenType.ACCESS,
            token_value=access_token,
            expires_at=(datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)).isoformat(),
            created_at=datetime.now().isoformat()
        )
        
        self.tokens[access_token_obj.token_id] = access_token_obj
        self._save_data()
        
        return {
            "access_token": access_token,
            "expires_in": self.access_token_expire_minutes * 60
        }
    
    def verify_token(self, token: str) -> Optional[User]:
        """Verify access token and return user"""
        payload = self._verify_jwt_token(token)
        if not payload or payload.get("token_type") != TokenType.ACCESS.value:
            return None
        
        user_id = payload.get("user_id")
        if not user_id or user_id not in self.users:
            return None
        
        user = self.users[user_id]
        if user.status != UserStatus.ACTIVE:
            return None
        
        return user
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token"""
        payload = self._verify_jwt_token(token)
        if not payload:
            return False
        
        # Find and revoke token
        for token_obj in self.tokens.values():
            if token_obj.token_value == token:
                token_obj.is_revoked = True
                self._save_data()
                return True
        
        return False
    
    def logout_user(self, session_id: str) -> bool:
        """Logout user and invalidate session"""
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            self._save_data()
            return True
        
        return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        if user_id not in self.users:
            return False
        
        user = self.users[user_id]
        
        # Verify old password
        if not self._verify_password(old_password, user.password_hash):
            return False
        
        # Update password
        user.password_hash = self._hash_password(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        
        # Revoke all existing tokens
        for token in self.tokens.values():
            if token.user_id == user_id:
                token.is_revoked = True
        
        self._save_data()
        
        logger.info(f"Password changed for user: {user.username}")
        return True
    
    def reset_password(self, email: str) -> Optional[str]:
        """Initiate password reset"""
        # Find user by email
        user = None
        for u in self.users.values():
            if u.email == email:
                user = u
                break
        
        if not user:
            return None
        
        # Generate reset token
        reset_token = self._generate_jwt_token(user.user_id, TokenType.RESET, timedelta(hours=1))
        
        # Store reset token
        reset_token_obj = Token(
            token_id=str(uuid.uuid4()),
            user_id=user.user_id,
            token_type=TokenType.RESET,
            token_value=reset_token,
            expires_at=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
            created_at=datetime.now().isoformat()
        )
        
        self.tokens[reset_token_obj.token_id] = reset_token_obj
        self._save_data()
        
        logger.info(f"Password reset initiated for user: {user.username}")
        return reset_token
    
    def confirm_password_reset(self, reset_token: str, new_password: str) -> bool:
        """Confirm password reset with new password"""
        payload = self._verify_jwt_token(reset_token)
        if not payload or payload.get("token_type") != TokenType.RESET.value:
            return False
        
        user_id = payload.get("user_id")
        if not user_id or user_id not in self.users:
            return False
        
        user = self.users[user_id]
        user.password_hash = self._hash_password(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        
        # Revoke all existing tokens
        for token in self.tokens.values():
            if token.user_id == user_id:
                token.is_revoked = True
        
        self._save_data()
        
        logger.info(f"Password reset completed for user: {user.username}")
        return True
    
    def enable_mfa(self, user_id: str) -> Dict[str, str]:
        """Enable multi-factor authentication for user"""
        if user_id not in self.users:
            raise ValueError("User not found")
        
        user = self.users[user_id]
        
        # Generate MFA secret
        mfa_secret = secrets.token_urlsafe(32)
        user.mfa_secret = mfa_secret
        user.mfa_enabled = True
        
        # Generate QR code
        qr_data = f"otpauth://totp/{user.username}?secret={mfa_secret}&issuer=API%20Lifecycle%20Management"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        self._save_data()
        
        return {
            "secret": mfa_secret,
            "qr_code": f"data:image/png;base64,{img_str}"
        }
    
    def verify_mfa(self, user_id: str, mfa_code: str) -> bool:
        """Verify MFA code"""
        if user_id not in self.users:
            return False
        
        user = self.users[user_id]
        if not user.mfa_enabled or not user.mfa_secret:
            return False
        
        # Simple MFA verification (in production, use proper TOTP library)
        # This is a simplified implementation for demonstration
        expected_code = hashlib.sha256(f"{user.mfa_secret}{datetime.now().strftime('%Y%m%d%H%M')}".encode()).hexdigest()[:6]
        
        return mfa_code == expected_code
    
    def check_permission(self, user: User, resource: str, action: str) -> bool:
        """Check if user has permission for resource and action"""
        # Admin users have all permissions
        if user.role == UserRole.ADMIN:
            return True
        
        # Check user permissions
        for permission_id in user.permissions:
            if permission_id in self.permissions:
                perm = self.permissions[permission_id]
                if (perm.resource == resource or perm.resource == "*") and (perm.action == action or perm.action == "*"):
                    return True
        
        return False
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def list_users(self, role: Optional[UserRole] = None, status: Optional[UserStatus] = None) -> List[User]:
        """List users with optional filters"""
        users = list(self.users.values())
        
        if role:
            users = [u for u in users if u.role == role]
        
        if status:
            users = [u for u in users if u.status == status]
        
        return users
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user information"""
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        
        # Update allowed fields
        allowed_fields = ['email', 'role', 'status', 'profile', 'permissions']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)
        
        self._save_data()
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        if user_id not in self.users:
            return False
        
        # Revoke all user tokens
        for token in self.tokens.values():
            if token.user_id == user_id:
                token.is_revoked = True
        
        # Deactivate all user sessions
        for session in self.sessions.values():
            if session.user_id == user_id:
                session.is_active = False
        
        # Delete user
        del self.users[user_id]
        self._save_data()
        
        logger.info(f"User deleted: {user_id}")
        return True
    
    def get_auth_summary(self) -> Dict[str, Any]:
        """Get authentication system summary"""
        summary = {
            "total_users": len(self.users),
            "active_users": len([u for u in self.users.values() if u.status == UserStatus.ACTIVE]),
            "total_sessions": len(self.sessions),
            "active_sessions": len([s for s in self.sessions.values() if s.is_active]),
            "total_tokens": len(self.tokens),
            "active_tokens": len([t for t in self.tokens.values() if not t.is_revoked]),
            "by_role": {},
            "by_status": {},
            "mfa_enabled": len([u for u in self.users.values() if u.mfa_enabled])
        }
        
        # Count by role
        for user in self.users.values():
            role = user.role.value
            summary["by_role"][role] = summary["by_role"].get(role, 0) + 1
        
        # Count by status
        for user in self.users.values():
            status = user.status.value
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
        
        return summary

async def main():
    """Main function to demonstrate auth manager"""
    data_dir = Path("./auth_data")
    manager = AuthManager(data_dir)
    
    # Create a user
    user = manager.create_user(
        "admin",
        "admin@example.com",
        "admin123",
        UserRole.ADMIN
    )
    
    print(f"Created user: {user.username}")
    
    # Authenticate user
    auth_result = manager.authenticate_user("admin", "admin123")
    if auth_result:
        print(f"Authentication successful: {auth_result['user'].username}")
        print(f"Access token: {auth_result['access_token'][:50]}...")
    
    # Get auth summary
    summary = manager.get_auth_summary()
    print(f"Auth summary: {summary}")

if __name__ == "__main__":
    asyncio.run(main())