"""
Database operations and schema for user management service
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import asyncpg
import asyncpg.pool
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import text
import uuid
import json

from .config import settings
from .models import UserRole, UserStatus, TenantStatus

logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()

class User(Base):
    """User database model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.USER)
    status = Column(String(20), nullable=False, default=UserStatus.ACTIVE)
    is_verified = Column(Boolean, default=False)
    preferences = Column(JSONB, default=dict)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    # Indexes
    __table_args__ = (
        Index('idx_users_email_tenant', 'email', 'tenant_id'),
        Index('idx_users_status_tenant', 'status', 'tenant_id'),
        Index('idx_users_role_tenant', 'role', 'tenant_id'),
    )

class Tenant(Base):
    """Tenant database model"""
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True, unique=True, index=True)
    status = Column(String(20), nullable=False, default=TenantStatus.ACTIVE)
    settings = Column(JSONB, default=dict)
    max_users = Column(Integer, nullable=True)
    features = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    audit_logs = relationship("AuditLog", back_populates="tenant")

class UserSession(Base):
    """User session database model"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    tenant = relationship("Tenant")

class AuditLog(Base):
    """Audit log database model"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True, index=True)
    details = Column(JSONB, default=dict)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    tenant = relationship("Tenant", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_logs_timestamp', 'timestamp'),
        Index('idx_audit_logs_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_logs_tenant_timestamp', 'tenant_id', 'timestamp'),
        Index('idx_audit_logs_action_timestamp', 'action', 'timestamp'),
    )

class PasswordResetToken(Base):
    """Password reset token database model"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

class DatabaseManager:
    """Database manager for user management service"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.pool = None
        
    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            # Create SQLAlchemy engine
            self.engine = create_engine(
                settings.postgres_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=settings.debug
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            # Create asyncpg connection pool for raw SQL operations
            self.pool = await asyncpg.create_pool(
                settings.postgres_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
        if self.engine:
            self.engine.dispose()
        logger.info("Database connections closed")
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute raw SQL query"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def execute_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute query and return single row"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def execute_command(self, query: str, *args) -> str:
        """Execute command and return result"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *args)
            return result

# Global database manager instance
db_manager = DatabaseManager()

# Database utility functions
async def get_user_by_id(user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    query = """
        SELECT u.*, t.name as tenant_name, t.domain as tenant_domain
        FROM users u
        LEFT JOIN tenants t ON u.tenant_id = t.id
        WHERE u.id = $1
    """
    return await db_manager.execute_one(query, user_id)

async def get_user_by_email(email: str, tenant_id: Optional[uuid.UUID] = None) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    if tenant_id:
        query = """
            SELECT u.*, t.name as tenant_name, t.domain as tenant_domain
            FROM users u
            LEFT JOIN tenants t ON u.tenant_id = t.id
            WHERE u.email = $1 AND u.tenant_id = $2
        """
        return await db_manager.execute_one(query, email, tenant_id)
    else:
        query = """
            SELECT u.*, t.name as tenant_name, t.domain as tenant_domain
            FROM users u
            LEFT JOIN tenants t ON u.tenant_id = t.id
            WHERE u.email = $1
        """
        return await db_manager.execute_one(query, email)

async def get_user_by_username(username: str, tenant_id: Optional[uuid.UUID] = None) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    if tenant_id:
        query = """
            SELECT u.*, t.name as tenant_name, t.domain as tenant_domain
            FROM users u
            LEFT JOIN tenants t ON u.tenant_id = t.id
            WHERE u.username = $1 AND u.tenant_id = $2
        """
        return await db_manager.execute_one(query, username, tenant_id)
    else:
        query = """
            SELECT u.*, t.name as tenant_name, t.domain as tenant_domain
            FROM users u
            LEFT JOIN tenants t ON u.tenant_id = t.id
            WHERE u.username = $1
        """
        return await db_manager.execute_one(query, username)

async def get_tenant_by_id(tenant_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Get tenant by ID"""
    query = """
        SELECT t.*, COUNT(u.id) as user_count
        FROM tenants t
        LEFT JOIN users u ON t.id = u.tenant_id
        WHERE t.id = $1
        GROUP BY t.id
    """
    return await db_manager.execute_one(query, tenant_id)

async def get_tenant_by_domain(domain: str) -> Optional[Dict[str, Any]]:
    """Get tenant by domain"""
    query = """
        SELECT t.*, COUNT(u.id) as user_count
        FROM tenants t
        LEFT JOIN users u ON t.id = u.tenant_id
        WHERE t.domain = $1
        GROUP BY t.id
    """
    return await db_manager.execute_one(query, domain)

async def search_users(
    query: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    tenant_id: Optional[uuid.UUID] = None,
    page: int = 1,
    size: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    """Search users with pagination"""
    offset = (page - 1) * size
    
    # Build WHERE clause
    where_conditions = []
    params = []
    param_count = 0
    
    if query:
        param_count += 1
        where_conditions.append(f"(u.email ILIKE ${param_count} OR u.username ILIKE ${param_count} OR u.first_name ILIKE ${param_count} OR u.last_name ILIKE ${param_count})")
        params.append(f"%{query}%")
    
    if role:
        param_count += 1
        where_conditions.append(f"u.role = ${param_count}")
        params.append(role)
    
    if status:
        param_count += 1
        where_conditions.append(f"u.status = ${param_count}")
        params.append(status)
    
    if tenant_id:
        param_count += 1
        where_conditions.append(f"u.tenant_id = ${param_count}")
        params.append(tenant_id)
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    # Get total count
    count_query = f"""
        SELECT COUNT(*)
        FROM users u
        WHERE {where_clause}
    """
    total = await db_manager.execute_one(count_query, *params)
    total_count = total['count'] if total else 0
    
    # Get users
    param_count += 1
    params.append(size)
    param_count += 1
    params.append(offset)
    
    users_query = f"""
        SELECT u.*, t.name as tenant_name, t.domain as tenant_domain
        FROM users u
        LEFT JOIN tenants t ON u.tenant_id = t.id
        WHERE {where_clause}
        ORDER BY u.created_at DESC
        LIMIT ${param_count - 1} OFFSET ${param_count}
    """
    
    users = await db_manager.execute_query(users_query, *params)
    return users, total_count

async def search_tenants(
    query: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    size: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    """Search tenants with pagination"""
    offset = (page - 1) * size
    
    # Build WHERE clause
    where_conditions = []
    params = []
    param_count = 0
    
    if query:
        param_count += 1
        where_conditions.append(f"(t.name ILIKE ${param_count} OR t.description ILIKE ${param_count})")
        params.append(f"%{query}%")
    
    if status:
        param_count += 1
        where_conditions.append(f"t.status = ${param_count}")
        params.append(status)
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    # Get total count
    count_query = f"""
        SELECT COUNT(*)
        FROM tenants t
        WHERE {where_clause}
    """
    total = await db_manager.execute_one(count_query, *params)
    total_count = total['count'] if total else 0
    
    # Get tenants
    param_count += 1
    params.append(size)
    param_count += 1
    params.append(offset)
    
    tenants_query = f"""
        SELECT t.*, COUNT(u.id) as user_count
        FROM tenants t
        LEFT JOIN users u ON t.id = u.tenant_id
        WHERE {where_clause}
        GROUP BY t.id
        ORDER BY t.created_at DESC
        LIMIT ${param_count - 1} OFFSET ${param_count}
    """
    
    tenants = await db_manager.execute_query(tenants_query, *params)
    return tenants, total_count

async def create_audit_log(
    user_id: Optional[uuid.UUID],
    tenant_id: Optional[uuid.UUID],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Create audit log entry"""
    query = """
        INSERT INTO audit_logs (user_id, tenant_id, action, resource_type, resource_id, details, ip_address, user_agent)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """
    await db_manager.execute_command(
        query,
        user_id,
        tenant_id,
        action,
        resource_type,
        resource_id,
        json.dumps(details) if details else None,
        ip_address,
        user_agent
    )

async def get_audit_logs(
    user_id: Optional[uuid.UUID] = None,
    tenant_id: Optional[uuid.UUID] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    page: int = 1,
    size: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    """Get audit logs with pagination"""
    offset = (page - 1) * size
    
    # Build WHERE clause
    where_conditions = []
    params = []
    param_count = 0
    
    if user_id:
        param_count += 1
        where_conditions.append(f"user_id = ${param_count}")
        params.append(user_id)
    
    if tenant_id:
        param_count += 1
        where_conditions.append(f"tenant_id = ${param_count}")
        params.append(tenant_id)
    
    if action:
        param_count += 1
        where_conditions.append(f"action = ${param_count}")
        params.append(action)
    
    if resource_type:
        param_count += 1
        where_conditions.append(f"resource_type = ${param_count}")
        params.append(resource_type)
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    # Get total count
    count_query = f"""
        SELECT COUNT(*)
        FROM audit_logs
        WHERE {where_clause}
    """
    total = await db_manager.execute_one(count_query, *params)
    total_count = total['count'] if total else 0
    
    # Get audit logs
    param_count += 1
    params.append(size)
    param_count += 1
    params.append(offset)
    
    logs_query = f"""
        SELECT *
        FROM audit_logs
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT ${param_count - 1} OFFSET ${param_count}
    """
    
    logs = await db_manager.execute_query(logs_query, *params)
    return logs, total_count