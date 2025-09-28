"""
User management functionality for user management service
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import uuid
from sqlalchemy.orm import Session

from .config import settings
from .models import UserCreate, UserUpdate, UserResponse, UserListResponse, UserRole, UserStatus
from .database import (
    db_manager, get_user_by_id, get_user_by_email, get_user_by_username,
    search_users, create_audit_log
)
from .auth import auth_manager, log_auth_event

logger = logging.getLogger(__name__)

class UserManager:
    """User management operations"""
    
    def __init__(self):
        self.db = db_manager
    
    async def create_user(
        self,
        user_data: UserCreate,
        created_by: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserResponse:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = await get_user_by_email(user_data.email, user_data.tenant_id)
            if existing_user:
                raise ValueError("User with this email already exists")
            
            existing_username = await get_user_by_username(user_data.username, user_data.tenant_id)
            if existing_username:
                raise ValueError("Username already taken")
            
            # Hash password
            password_hash = auth_manager.hash_password(user_data.password)
            
            # Create user
            user_id = uuid.uuid4()
            query = """
                INSERT INTO users (
                    id, email, username, password_hash, first_name, last_name,
                    role, status, is_verified, preferences, tenant_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """
            
            await self.db.execute_command(
                query,
                user_id,
                user_data.email,
                user_data.username,
                password_hash,
                user_data.first_name,
                user_data.last_name,
                user_data.role.value,
                user_data.status.value,
                user_data.is_verified,
                user_data.preferences,
                user_data.tenant_id
            )
            
            # Get created user
            user = await get_user_by_id(user_id)
            
            # Log audit event
            await create_audit_log(
                user_id=created_by,
                tenant_id=user_data.tenant_id,
                action="user_created",
                resource_type="user",
                resource_id=str(user_id),
                details={
                    "email": user_data.email,
                    "username": user_data.username,
                    "role": user_data.role.value
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"User created successfully: {user_data.email}")
            return UserResponse(**user)
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user(
        self,
        user_id: uuid.UUID,
        current_user: Optional[Dict[str, Any]] = None
    ) -> Optional[UserResponse]:
        """Get user by ID"""
        try:
            user = await get_user_by_id(user_id)
            if not user:
                return None
            
            # Check permissions
            if current_user and not await self._check_user_access(current_user, user_id, user.get("tenant_id")):
                return None
            
            return UserResponse(**user)
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise
    
    async def update_user(
        self,
        user_id: uuid.UUID,
        user_data: UserUpdate,
        current_user: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[UserResponse]:
        """Update user"""
        try:
            # Get existing user
            existing_user = await get_user_by_id(user_id)
            if not existing_user:
                return None
            
            # Check permissions
            if not await self._check_user_access(current_user, user_id, existing_user.get("tenant_id")):
                raise ValueError("Insufficient permissions")
            
            # Check if email is being changed and if it's already taken
            if user_data.email and user_data.email != existing_user["email"]:
                email_user = await get_user_by_email(user_data.email, existing_user.get("tenant_id"))
                if email_user and email_user["id"] != user_id:
                    raise ValueError("Email already taken")
            
            # Check if username is being changed and if it's already taken
            if user_data.username and user_data.username != existing_user["username"]:
                username_user = await get_user_by_username(user_data.username, existing_user.get("tenant_id"))
                if username_user and username_user["id"] != user_id:
                    raise ValueError("Username already taken")
            
            # Build update query
            update_fields = []
            params = []
            param_count = 0
            
            if user_data.email is not None:
                param_count += 1
                update_fields.append(f"email = ${param_count}")
                params.append(user_data.email)
            
            if user_data.username is not None:
                param_count += 1
                update_fields.append(f"username = ${param_count}")
                params.append(user_data.username)
            
            if user_data.first_name is not None:
                param_count += 1
                update_fields.append(f"first_name = ${param_count}")
                params.append(user_data.first_name)
            
            if user_data.last_name is not None:
                param_count += 1
                update_fields.append(f"last_name = ${param_count}")
                params.append(user_data.last_name)
            
            if user_data.role is not None:
                param_count += 1
                update_fields.append(f"role = ${param_count}")
                params.append(user_data.role.value)
            
            if user_data.status is not None:
                param_count += 1
                update_fields.append(f"status = ${param_count}")
                params.append(user_data.status.value)
            
            if user_data.preferences is not None:
                param_count += 1
                update_fields.append(f"preferences = ${param_count}")
                params.append(user_data.preferences)
            
            if not update_fields:
                # No fields to update
                user = await get_user_by_id(user_id)
                return UserResponse(**user)
            
            # Add updated_at
            param_count += 1
            update_fields.append(f"updated_at = ${param_count}")
            params.append(datetime.utcnow())
            
            # Add user_id parameter
            param_count += 1
            params.append(user_id)
            
            query = f"""
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = ${param_count}
            """
            
            await self.db.execute_command(query, *params)
            
            # Get updated user
            user = await get_user_by_id(user_id)
            
            # Log audit event
            await create_audit_log(
                user_id=current_user["id"],
                tenant_id=current_user.get("tenant_id"),
                action="user_updated",
                resource_type="user",
                resource_id=str(user_id),
                details={
                    "updated_fields": list(user_data.dict(exclude_unset=True).keys()),
                    "target_user_email": existing_user["email"]
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"User updated successfully: {user_id}")
            return UserResponse(**user)
            
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    async def delete_user(
        self,
        user_id: uuid.UUID,
        current_user: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Delete user (soft delete by setting status to inactive)"""
        try:
            # Get existing user
            existing_user = await get_user_by_id(user_id)
            if not existing_user:
                return False
            
            # Check permissions
            if not await self._check_user_access(current_user, user_id, existing_user.get("tenant_id")):
                raise ValueError("Insufficient permissions")
            
            # Prevent self-deletion
            if current_user["id"] == user_id:
                raise ValueError("Cannot delete your own account")
            
            # Soft delete by setting status to inactive
            query = """
                UPDATE users 
                SET status = $1, updated_at = $2
                WHERE id = $3
            """
            
            await self.db.execute_command(
                query,
                UserStatus.INACTIVE.value,
                datetime.utcnow(),
                user_id
            )
            
            # Log audit event
            await create_audit_log(
                user_id=current_user["id"],
                tenant_id=current_user.get("tenant_id"),
                action="user_deleted",
                resource_type="user",
                resource_id=str(user_id),
                details={
                    "deleted_user_email": existing_user["email"],
                    "deleted_user_username": existing_user["username"]
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"User deleted successfully: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise
    
    async def search_users(
        self,
        query: Optional[str] = None,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        tenant_id: Optional[uuid.UUID] = None,
        page: int = 1,
        size: int = 10,
        current_user: Optional[Dict[str, Any]] = None
    ) -> UserListResponse:
        """Search users with pagination"""
        try:
            # Check permissions for tenant access
            if tenant_id and current_user and current_user.get("tenant_id") != tenant_id:
                if current_user["role"] != UserRole.ADMIN:
                    raise ValueError("Insufficient permissions to access tenant users")
            
            users, total = await search_users(
                query=query,
                role=role.value if role else None,
                status=status.value if status else None,
                tenant_id=tenant_id,
                page=page,
                size=size
            )
            
            # Convert to response models
            user_responses = [UserResponse(**user) for user in users]
            
            pages = (total + size - 1) // size
            
            return UserListResponse(
                users=user_responses,
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Failed to search users: {e}")
            raise
    
    async def change_password(
        self,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
        current_user: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Change user password"""
        try:
            # Get user
            user = await get_user_by_id(user_id)
            if not user:
                return False
            
            # Check permissions
            if not await self._check_user_access(current_user, user_id, user.get("tenant_id")):
                raise ValueError("Insufficient permissions")
            
            # Verify current password
            if not auth_manager.verify_password(current_password, user["password_hash"]):
                raise ValueError("Current password is incorrect")
            
            # Hash new password
            new_password_hash = auth_manager.hash_password(new_password)
            
            # Update password
            query = """
                UPDATE users 
                SET password_hash = $1, updated_at = $2
                WHERE id = $3
            """
            
            await self.db.execute_command(
                query,
                new_password_hash,
                datetime.utcnow(),
                user_id
            )
            
            # Log audit event
            await create_audit_log(
                user_id=current_user["id"],
                tenant_id=current_user.get("tenant_id"),
                action="password_changed",
                resource_type="user",
                resource_id=str(user_id),
                details={
                    "target_user_email": user["email"]
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Password changed successfully for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to change password for user {user_id}: {e}")
            raise
    
    async def reset_password(
        self,
        user_id: uuid.UUID,
        new_password: str,
        current_user: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Reset user password (admin only)"""
        try:
            # Check if current user is admin
            if current_user["role"] != UserRole.ADMIN:
                raise ValueError("Only admins can reset passwords")
            
            # Get user
            user = await get_user_by_id(user_id)
            if not user:
                return False
            
            # Hash new password
            new_password_hash = auth_manager.hash_password(new_password)
            
            # Update password
            query = """
                UPDATE users 
                SET password_hash = $1, updated_at = $2, login_attempts = 0, locked_until = NULL
                WHERE id = $3
            """
            
            await self.db.execute_command(
                query,
                new_password_hash,
                datetime.utcnow(),
                user_id
            )
            
            # Log audit event
            await create_audit_log(
                user_id=current_user["id"],
                tenant_id=current_user.get("tenant_id"),
                action="password_reset",
                resource_type="user",
                resource_id=str(user_id),
                details={
                    "target_user_email": user["email"]
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Password reset successfully for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset password for user {user_id}: {e}")
            raise
    
    async def _check_user_access(
        self,
        current_user: Dict[str, Any],
        target_user_id: uuid.UUID,
        target_tenant_id: Optional[uuid.UUID]
    ) -> bool:
        """Check if current user has access to target user"""
        # Admin users have access to all users
        if current_user["role"] == UserRole.ADMIN:
            return True
        
        # Users can access their own data
        if current_user["id"] == target_user_id:
            return True
        
        # Moderators can access users in their tenant
        if current_user["role"] == UserRole.MODERATOR:
            return current_user.get("tenant_id") == target_tenant_id
        
        return False

# Global user manager instance
user_manager = UserManager()