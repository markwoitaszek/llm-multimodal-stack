"""
Tenant management functionality for multi-tenant support
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import uuid
import json

from .config import settings
from .models import (
    TenantCreate, TenantUpdate, TenantResponse, TenantListResponse,
    TenantStatus, UserCreate, UserRole, UserStatus, UserResponse
)
from .database import (
    db_manager, get_tenant_by_id, get_tenant_by_domain, search_tenants,
    create_audit_log
)
from .user_manager import user_manager

logger = logging.getLogger(__name__)

class TenantManager:
    """Tenant management operations"""
    
    def __init__(self):
        self.db = db_manager
    
    async def create_tenant(
        self,
        tenant_data: TenantCreate,
        created_by: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[TenantResponse, UserResponse]:
        """Create a new tenant with admin user"""
        try:
            # Check if tenant domain already exists
            if tenant_data.domain:
                existing_tenant = await get_tenant_by_domain(tenant_data.domain)
                if existing_tenant:
                    raise ValueError("Tenant with this domain already exists")
            
            # Create tenant
            tenant_id = uuid.uuid4()
            query = """
                INSERT INTO tenants (
                    id, name, description, domain, status, settings, max_users, features
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """
            
            await self.db.execute_command(
                query,
                tenant_id,
                tenant_data.name,
                tenant_data.description,
                tenant_data.domain,
                tenant_data.status.value,
                json.dumps(tenant_data.settings),
                tenant_data.max_users,
                json.dumps(tenant_data.features)
            )
            
            # Create admin user for the tenant
            admin_user_data = UserCreate(
                email=tenant_data.admin_email,
                username=tenant_data.admin_username,
                password=tenant_data.admin_password,
                first_name=tenant_data.admin_first_name,
                last_name=tenant_data.admin_last_name,
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                is_verified=True,
                tenant_id=tenant_id
            )
            
            admin_user = await user_manager.create_user(
                admin_user_data,
                created_by=created_by,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Get created tenant
            tenant = await get_tenant_by_id(tenant_id)
            
            # Log audit event
            await create_audit_log(
                user_id=created_by,
                tenant_id=tenant_id,
                action="tenant_created",
                resource_type="tenant",
                resource_id=str(tenant_id),
                details={
                    "name": tenant_data.name,
                    "domain": tenant_data.domain,
                    "admin_email": tenant_data.admin_email
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Tenant created successfully: {tenant_data.name}")
            return TenantResponse(**tenant), admin_user
            
        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            raise
    
    async def get_tenant(
        self,
        tenant_id: uuid.UUID,
        current_user: Optional[Dict[str, Any]] = None
    ) -> Optional[TenantResponse]:
        """Get tenant by ID"""
        try:
            tenant = await get_tenant_by_id(tenant_id)
            if not tenant:
                return None
            
            # Check permissions
            if current_user and not await self._check_tenant_access(current_user, tenant_id):
                return None
            
            return TenantResponse(**tenant)
            
        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {e}")
            raise
    
    async def get_tenant_by_domain(
        self,
        domain: str
    ) -> Optional[TenantResponse]:
        """Get tenant by domain"""
        try:
            tenant = await get_tenant_by_domain(domain)
            if not tenant:
                return None
            
            return TenantResponse(**tenant)
            
        except Exception as e:
            logger.error(f"Failed to get tenant by domain {domain}: {e}")
            raise
    
    async def update_tenant(
        self,
        tenant_id: uuid.UUID,
        tenant_data: TenantUpdate,
        current_user: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[TenantResponse]:
        """Update tenant"""
        try:
            # Get existing tenant
            existing_tenant = await get_tenant_by_id(tenant_id)
            if not existing_tenant:
                return None
            
            # Check permissions
            if not await self._check_tenant_access(current_user, tenant_id):
                raise ValueError("Insufficient permissions")
            
            # Check if domain is being changed and if it's already taken
            if tenant_data.domain and tenant_data.domain != existing_tenant["domain"]:
                domain_tenant = await get_tenant_by_domain(tenant_data.domain)
                if domain_tenant and domain_tenant["id"] != tenant_id:
                    raise ValueError("Domain already taken")
            
            # Build update query
            update_fields = []
            params = []
            param_count = 0
            
            if tenant_data.name is not None:
                param_count += 1
                update_fields.append(f"name = ${param_count}")
                params.append(tenant_data.name)
            
            if tenant_data.description is not None:
                param_count += 1
                update_fields.append(f"description = ${param_count}")
                params.append(tenant_data.description)
            
            if tenant_data.domain is not None:
                param_count += 1
                update_fields.append(f"domain = ${param_count}")
                params.append(tenant_data.domain)
            
            if tenant_data.status is not None:
                param_count += 1
                update_fields.append(f"status = ${param_count}")
                params.append(tenant_data.status.value)
            
            if tenant_data.settings is not None:
                param_count += 1
                update_fields.append(f"settings = ${param_count}")
                params.append(json.dumps(tenant_data.settings))
            
            if tenant_data.max_users is not None:
                param_count += 1
                update_fields.append(f"max_users = ${param_count}")
                params.append(tenant_data.max_users)
            
            if tenant_data.features is not None:
                param_count += 1
                update_fields.append(f"features = ${param_count}")
                params.append(json.dumps(tenant_data.features))
            
            if not update_fields:
                # No fields to update
                tenant = await get_tenant_by_id(tenant_id)
                return TenantResponse(**tenant)
            
            # Add updated_at
            param_count += 1
            update_fields.append(f"updated_at = ${param_count}")
            params.append(datetime.utcnow())
            
            # Add tenant_id parameter
            param_count += 1
            params.append(tenant_id)
            
            query = f"""
                UPDATE tenants 
                SET {', '.join(update_fields)}
                WHERE id = ${param_count}
            """
            
            await self.db.execute_command(query, *params)
            
            # Get updated tenant
            tenant = await get_tenant_by_id(tenant_id)
            
            # Log audit event
            await create_audit_log(
                user_id=current_user["id"],
                tenant_id=current_user.get("tenant_id"),
                action="tenant_updated",
                resource_type="tenant",
                resource_id=str(tenant_id),
                details={
                    "updated_fields": list(tenant_data.dict(exclude_unset=True).keys()),
                    "target_tenant_name": existing_tenant["name"]
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Tenant updated successfully: {tenant_id}")
            return TenantResponse(**tenant)
            
        except Exception as e:
            logger.error(f"Failed to update tenant {tenant_id}: {e}")
            raise
    
    async def delete_tenant(
        self,
        tenant_id: uuid.UUID,
        current_user: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Delete tenant (soft delete by setting status to inactive)"""
        try:
            # Check if current user is admin
            if current_user["role"] != UserRole.ADMIN:
                raise ValueError("Only admins can delete tenants")
            
            # Get existing tenant
            existing_tenant = await get_tenant_by_id(tenant_id)
            if not existing_tenant:
                return False
            
            # Soft delete by setting status to inactive
            query = """
                UPDATE tenants 
                SET status = $1, updated_at = $2
                WHERE id = $3
            """
            
            await self.db.execute_command(
                query,
                TenantStatus.INACTIVE.value,
                datetime.utcnow(),
                tenant_id
            )
            
            # Log audit event
            await create_audit_log(
                user_id=current_user["id"],
                tenant_id=current_user.get("tenant_id"),
                action="tenant_deleted",
                resource_type="tenant",
                resource_id=str(tenant_id),
                details={
                    "deleted_tenant_name": existing_tenant["name"],
                    "deleted_tenant_domain": existing_tenant["domain"]
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Tenant deleted successfully: {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id}: {e}")
            raise
    
    async def search_tenants(
        self,
        query: Optional[str] = None,
        status: Optional[TenantStatus] = None,
        page: int = 1,
        size: int = 10,
        current_user: Optional[Dict[str, Any]] = None
    ) -> TenantListResponse:
        """Search tenants with pagination"""
        try:
            # Check permissions
            if current_user and current_user["role"] != UserRole.ADMIN:
                raise ValueError("Only admins can search all tenants")
            
            tenants, total = await search_tenants(
                query=query,
                status=status.value if status else None,
                page=page,
                size=size
            )
            
            # Convert to response models
            tenant_responses = [TenantResponse(**tenant) for tenant in tenants]
            
            pages = (total + size - 1) // size
            
            return TenantListResponse(
                tenants=tenant_responses,
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Failed to search tenants: {e}")
            raise
    
    async def get_tenant_users(
        self,
        tenant_id: uuid.UUID,
        page: int = 1,
        size: int = 10,
        current_user: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get users for a specific tenant"""
        try:
            # Check permissions
            if current_user and not await self._check_tenant_access(current_user, tenant_id):
                raise ValueError("Insufficient permissions to access tenant users")
            
            # Get tenant users
            users, total = await search_users(
                tenant_id=tenant_id,
                page=page,
                size=size
            )
            
            return users
            
        except Exception as e:
            logger.error(f"Failed to get tenant users for {tenant_id}: {e}")
            raise
    
    async def get_tenant_stats(
        self,
        tenant_id: uuid.UUID,
        current_user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get tenant statistics"""
        try:
            # Check permissions
            if current_user and not await self._check_tenant_access(current_user, tenant_id):
                raise ValueError("Insufficient permissions to access tenant stats")
            
            # Get tenant
            tenant = await get_tenant_by_id(tenant_id)
            if not tenant:
                return {}
            
            # Get user counts by status
            query = """
                SELECT status, COUNT(*) as count
                FROM users
                WHERE tenant_id = $1
                GROUP BY status
            """
            
            status_counts = await self.db.execute_query(query, tenant_id)
            
            # Get user counts by role
            query = """
                SELECT role, COUNT(*) as count
                FROM users
                WHERE tenant_id = $1
                GROUP BY role
            """
            
            role_counts = await self.db.execute_query(query, tenant_id)
            
            # Get recent activity (last 30 days)
            query = """
                SELECT COUNT(*) as count
                FROM audit_logs
                WHERE tenant_id = $1 AND timestamp >= NOW() - INTERVAL '30 days'
            """
            
            recent_activity = await self.db.execute_one(query, tenant_id)
            
            return {
                "tenant": {
                    "id": str(tenant_id),
                    "name": tenant["name"],
                    "status": tenant["status"],
                    "max_users": tenant["max_users"],
                    "user_count": tenant["user_count"]
                },
                "user_stats": {
                    "by_status": {row["status"]: row["count"] for row in status_counts},
                    "by_role": {row["role"]: row["count"] for row in role_counts}
                },
                "activity": {
                    "recent_actions": recent_activity["count"] if recent_activity else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get tenant stats for {tenant_id}: {e}")
            raise
    
    async def update_tenant_settings(
        self,
        tenant_id: uuid.UUID,
        settings: Dict[str, Any],
        current_user: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Update tenant settings"""
        try:
            # Check permissions
            if not await self._check_tenant_access(current_user, tenant_id):
                raise ValueError("Insufficient permissions")
            
            # Get existing tenant
            existing_tenant = await get_tenant_by_id(tenant_id)
            if not existing_tenant:
                return False
            
            # Merge with existing settings
            existing_settings = existing_tenant.get("settings", {})
            if isinstance(existing_settings, str):
                existing_settings = json.loads(existing_settings)
            
            updated_settings = {**existing_settings, **settings}
            
            # Update settings
            query = """
                UPDATE tenants 
                SET settings = $1, updated_at = $2
                WHERE id = $3
            """
            
            await self.db.execute_command(
                query,
                json.dumps(updated_settings),
                datetime.utcnow(),
                tenant_id
            )
            
            # Log audit event
            await create_audit_log(
                user_id=current_user["id"],
                tenant_id=current_user.get("tenant_id"),
                action="tenant_settings_updated",
                resource_type="tenant",
                resource_id=str(tenant_id),
                details={
                    "updated_settings": list(settings.keys()),
                    "target_tenant_name": existing_tenant["name"]
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Tenant settings updated successfully: {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update tenant settings for {tenant_id}: {e}")
            raise
    
    async def _check_tenant_access(
        self,
        current_user: Dict[str, Any],
        target_tenant_id: uuid.UUID
    ) -> bool:
        """Check if current user has access to target tenant"""
        # Admin users have access to all tenants
        if current_user["role"] == UserRole.ADMIN:
            return True
        
        # Users can only access their own tenant
        return current_user.get("tenant_id") == target_tenant_id

# Global tenant manager instance
tenant_manager = TenantManager()