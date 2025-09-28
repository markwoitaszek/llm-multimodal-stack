"""
User Management Database Operations
"""
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Boolean, Integer, JSON, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
import hashlib

from app.config import settings
from app.models import UserRole, UserStatus, AuthProvider

Base = declarative_base()


class User(Base):
    """User database model"""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_provider: Mapped[str] = mapped_column(String(20), nullable=False, default="local")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
        Index('idx_user_tenant_id', 'tenant_id'),
        Index('idx_user_role', 'role'),
        Index('idx_user_status', 'status'),
        Index('idx_user_created_at', 'created_at'),
    )


class Tenant(Base):
    """Tenant database model"""
    __tablename__ = "tenants"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    admin_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    max_users: Mapped[int] = mapped_column(Integer, default=1000)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_tenant_name', 'name'),
        Index('idx_tenant_domain', 'domain'),
        Index('idx_tenant_admin_user_id', 'admin_user_id'),
    )


class Session(Base):
    """User session database model"""
    __tablename__ = "sessions"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey('users.id'), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_session_user_id', 'user_id'),
        Index('idx_session_tenant_id', 'tenant_id'),
        Index('idx_session_refresh_token', 'refresh_token'),
        Index('idx_session_expires_at', 'expires_at'),
        Index('idx_session_is_active', 'is_active'),
    )


class LoginAttempt(Base):
    """Login attempt tracking model"""
    __tablename__ = "login_attempts"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_login_attempt_username', 'username'),
        Index('idx_login_attempt_ip_address', 'ip_address'),
        Index('idx_login_attempt_created_at', 'created_at'),
    )


class DatabaseManager:
    """Database connection and operation manager"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._connection_pool = None
    
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Create async engine
            self.engine = create_async_engine(
                settings.database_url,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                echo=settings.debug
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Create connection pool for raw queries
            self._connection_pool = await asyncpg.create_pool(
                settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
                min_size=5,
                max_size=settings.database_pool_size
            )
            
        except Exception as e:
            raise Exception(f"Failed to initialize database: {str(e)}")
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
        if self._connection_pool:
            await self._connection_pool.close()
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.session_factory:
            raise Exception("Database not initialized")
        return self.session_factory()
    
    async def get_connection(self):
        """Get raw database connection"""
        if not self._connection_pool:
            raise Exception("Database not initialized")
        return self._connection_pool.acquire()
    
    # User operations
    async def create_user(self, user_id: str, username: str, email: str, password_hash: str,
                         full_name: Optional[str] = None, phone: Optional[str] = None,
                         role: str = "user", tenant_id: str = None,
                         auth_provider: str = "local", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Create new user"""
        try:
            if tenant_id is None:
                tenant_id = settings.default_tenant_id
                
            async with self.get_session() as session:
                user = User(
                    id=user_id,
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    full_name=full_name,
                    phone=phone,
                    role=role,
                    tenant_id=tenant_id,
                    auth_provider=auth_provider,
                    metadata=metadata
                )
                session.add(user)
                await session.commit()
                return True
        except Exception as e:
            if settings.debug:
                print(f"Error creating user: {str(e)}")
            return False
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            async with self.get_session() as session:
                result = await session.get(User, user_id)
                if result:
                    return {
                        "id": result.id,
                        "username": result.username,
                        "email": result.email,
                        "password_hash": result.password_hash,
                        "full_name": result.full_name,
                        "phone": result.phone,
                        "role": result.role,
                        "status": result.status,
                        "tenant_id": result.tenant_id,
                        "auth_provider": result.auth_provider,
                        "email_verified": result.email_verified,
                        "phone_verified": result.phone_verified,
                        "last_login": result.last_login,
                        "failed_login_attempts": result.failed_login_attempts,
                        "locked_until": result.locked_until,
                        "created_at": result.created_at,
                        "updated_at": result.updated_at,
                        "metadata": result.metadata
                    }
                return None
        except Exception as e:
            if settings.debug:
                print(f"Error getting user by ID: {str(e)}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE username = $1",
                    username
                )
                if row:
                    return dict(row)
                return None
        except Exception as e:
            if settings.debug:
                print(f"Error getting user by username: {str(e)}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE email = $1",
                    email
                )
                if row:
                    return dict(row)
                return None
        except Exception as e:
            if settings.debug:
                print(f"Error getting user by email: {str(e)}")
            return None
    
    async def update_user(self, user_id: str, **kwargs) -> bool:
        """Update user"""
        try:
            async with self.get_session() as session:
                result = await session.get(User, user_id)
                if result:
                    for key, value in kwargs.items():
                        if hasattr(result, key):
                            setattr(result, key, value)
                    result.updated_at = datetime.utcnow()
                    await session.commit()
                    return True
                return False
        except Exception as e:
            if settings.debug:
                print(f"Error updating user: {str(e)}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        try:
            async with self.get_session() as session:
                result = await session.get(User, user_id)
                if result:
                    await session.delete(result)
                    await session.commit()
                    return True
                return False
        except Exception as e:
            if settings.debug:
                print(f"Error deleting user: {str(e)}")
            return False
    
    async def search_users(self, tenant_id: Optional[str] = None, role: Optional[str] = None,
                          status: Optional[str] = None, search: Optional[str] = None,
                          limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Search users"""
        try:
            async with self.get_connection() as conn:
                # Build query
                base_query = "SELECT * FROM users WHERE 1=1"
                params = []
                param_count = 0
                
                if tenant_id:
                    param_count += 1
                    base_query += f" AND tenant_id = ${param_count}"
                    params.append(tenant_id)
                
                if role:
                    param_count += 1
                    base_query += f" AND role = ${param_count}"
                    params.append(role)
                
                if status:
                    param_count += 1
                    base_query += f" AND status = ${param_count}"
                    params.append(status)
                
                if search:
                    param_count += 1
                    search_term = f"%{search}%"
                    base_query += f" AND (username ILIKE ${param_count} OR email ILIKE ${param_count} OR full_name ILIKE ${param_count})"
                    params.append(search_term)
                
                base_query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
                params.extend([limit, offset])
                
                rows = await conn.fetch(base_query, *params)
                return [dict(row) for row in rows]
                
        except Exception as e:
            if settings.debug:
                print(f"Error searching users: {str(e)}")
            return []
    
    async def get_user_count(self, tenant_id: Optional[str] = None) -> int:
        """Get total user count"""
        try:
            async with self.get_connection() as conn:
                if tenant_id:
                    result = await conn.fetchval(
                        "SELECT COUNT(*) FROM users WHERE tenant_id = $1",
                        tenant_id
                    )
                else:
                    result = await conn.fetchval("SELECT COUNT(*) FROM users")
                return result or 0
        except Exception as e:
            if settings.debug:
                print(f"Error getting user count: {str(e)}")
            return 0
    
    # Tenant operations
    async def create_tenant(self, tenant_id: str, name: str, description: Optional[str] = None,
                           domain: Optional[str] = None, admin_user_id: Optional[str] = None,
                           max_users: int = 1000, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Create new tenant"""
        try:
            async with self.get_session() as session:
                tenant = Tenant(
                    id=tenant_id,
                    name=name,
                    description=description,
                    domain=domain,
                    admin_user_id=admin_user_id,
                    max_users=max_users,
                    metadata=metadata
                )
                session.add(tenant)
                await session.commit()
                return True
        except Exception as e:
            if settings.debug:
                print(f"Error creating tenant: {str(e)}")
            return False
    
    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID"""
        try:
            async with self.get_session() as session:
                result = await session.get(Tenant, tenant_id)
                if result:
                    # Get user count
                    user_count = await self.get_user_count(tenant_id)
                    
                    return {
                        "id": result.id,
                        "name": result.name,
                        "description": result.description,
                        "domain": result.domain,
                        "admin_user_id": result.admin_user_id,
                        "user_count": user_count,
                        "max_users": result.max_users,
                        "created_at": result.created_at,
                        "updated_at": result.updated_at,
                        "metadata": result.metadata
                    }
                return None
        except Exception as e:
            if settings.debug:
                print(f"Error getting tenant: {str(e)}")
            return None
    
    async def update_tenant(self, tenant_id: str, **kwargs) -> bool:
        """Update tenant"""
        try:
            async with self.get_session() as session:
                result = await session.get(Tenant, tenant_id)
                if result:
                    for key, value in kwargs.items():
                        if hasattr(result, key):
                            setattr(result, key, value)
                    result.updated_at = datetime.utcnow()
                    await session.commit()
                    return True
                return False
        except Exception as e:
            if settings.debug:
                print(f"Error updating tenant: {str(e)}")
            return False
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant"""
        try:
            async with self.get_session() as session:
                result = await session.get(Tenant, tenant_id)
                if result:
                    await session.delete(result)
                    await session.commit()
                    return True
                return False
        except Exception as e:
            if settings.debug:
                print(f"Error deleting tenant: {str(e)}")
            return False
    
    async def get_tenant_count(self) -> int:
        """Get total tenant count"""
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval("SELECT COUNT(*) FROM tenants")
                return result or 0
        except Exception as e:
            if settings.debug:
                print(f"Error getting tenant count: {str(e)}")
            return 0
    
    # Session operations
    async def create_session(self, session_id: str, user_id: str, tenant_id: str,
                           refresh_token: str, expires_at: datetime,
                           ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None) -> bool:
        """Create new session"""
        try:
            async with self.get_session() as session:
                session_obj = Session(
                    id=session_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    refresh_token=refresh_token,
                    expires_at=expires_at,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                session.add(session_obj)
                await session.commit()
                return True
        except Exception as e:
            if settings.debug:
                print(f"Error creating session: {str(e)}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        try:
            async with self.get_session() as session:
                result = await session.get(Session, session_id)
                if result:
                    return {
                        "id": result.id,
                        "user_id": result.user_id,
                        "tenant_id": result.tenant_id,
                        "refresh_token": result.refresh_token,
                        "ip_address": result.ip_address,
                        "user_agent": result.user_agent,
                        "created_at": result.created_at,
                        "expires_at": result.expires_at,
                        "last_activity": result.last_activity,
                        "is_active": result.is_active
                    }
                return None
        except Exception as e:
            if settings.debug:
                print(f"Error getting session: {str(e)}")
            return None
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity"""
        try:
            async with self.get_session() as session:
                result = await session.get(Session, session_id)
                if result:
                    result.last_activity = datetime.utcnow()
                    await session.commit()
                    return True
                return False
        except Exception as e:
            if settings.debug:
                print(f"Error updating session activity: {str(e)}")
            return False
    
    async def deactivate_session(self, session_id: str) -> bool:
        """Deactivate session"""
        try:
            async with self.get_session() as session:
                result = await session.get(Session, session_id)
                if result:
                    result.is_active = False
                    await session.commit()
                    return True
                return False
        except Exception as e:
            if settings.debug:
                print(f"Error deactivating session: {str(e)}")
            return False
    
    async def deactivate_user_sessions(self, user_id: str) -> int:
        """Deactivate all user sessions"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    "UPDATE sessions SET is_active = false WHERE user_id = $1",
                    user_id
                )
                await session.commit()
                return result.rowcount
        except Exception as e:
            if settings.debug:
                print(f"Error deactivating user sessions: {str(e)}")
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    "UPDATE sessions SET is_active = false WHERE expires_at < NOW()"
                )
                await session.commit()
                return result.rowcount
        except Exception as e:
            if settings.debug:
                print(f"Error cleaning up expired sessions: {str(e)}")
            return 0
    
    # Login attempt tracking
    async def log_login_attempt(self, username: str, ip_address: str, success: bool,
                               failure_reason: Optional[str] = None) -> bool:
        """Log login attempt"""
        try:
            async with self.get_session() as session:
                attempt = LoginAttempt(
                    username=username,
                    ip_address=ip_address,
                    success=success,
                    failure_reason=failure_reason
                )
                session.add(attempt)
                await session.commit()
                return True
        except Exception as e:
            if settings.debug:
                print(f"Error logging login attempt: {str(e)}")
            return False
    
    async def get_login_attempts_count(self, username: str, ip_address: str,
                                     since: datetime) -> int:
        """Get login attempts count since timestamp"""
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval(
                    "SELECT COUNT(*) FROM login_attempts WHERE username = $1 AND ip_address = $2 AND created_at > $3",
                    username, ip_address, since
                )
                return result or 0
        except Exception as e:
            if settings.debug:
                print(f"Error getting login attempts count: {str(e)}")
            return 0
    
    # Statistics
    async def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            async with self.get_connection() as conn:
                # Total users
                total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
                
                # Users by role
                role_dist = await conn.fetch(
                    "SELECT role, COUNT(*) FROM users GROUP BY role"
                )
                users_by_role = {row["role"]: row["count"] for row in role_dist}
                
                # Users by status
                status_dist = await conn.fetch(
                    "SELECT status, COUNT(*) FROM users GROUP BY status"
                )
                users_by_status = {row["status"]: row["count"] for row in status_dist}
                
                # Login attempts last hour
                last_hour = datetime.utcnow() - timedelta(hours=1)
                login_attempts_last_hour = await conn.fetchval(
                    "SELECT COUNT(*) FROM login_attempts WHERE created_at > $1",
                    last_hour
                )
                
                return {
                    "total_users": total_users or 0,
                    "users_by_role": users_by_role,
                    "users_by_status": users_by_status,
                    "login_attempts_last_hour": login_attempts_last_hour or 0
                }
        except Exception as e:
            if settings.debug:
                print(f"Error getting user stats: {str(e)}")
            return {
                "total_users": 0,
                "users_by_role": {},
                "users_by_status": {},
                "login_attempts_last_hour": 0
            }


# Global database manager instance
db_manager = DatabaseManager()