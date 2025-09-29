"""
Workspace Manager for handling collaborative workspaces
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)

@dataclass
class Workspace:
    """Workspace data structure"""
    id: str
    name: str
    description: Optional[str] = None
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    users: Set[str] = field(default_factory=set)
    agents: Set[str] = field(default_factory=set)
    settings: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

@dataclass
class WorkspaceActivity:
    """Workspace activity log entry"""
    id: str
    workspace_id: str
    user_id: str
    activity_type: str
    description: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

class WorkspaceManager:
    """Manages collaborative workspaces"""
    
    def __init__(self):
        self.workspaces: Dict[str, Workspace] = {}
        self.user_workspaces: Dict[str, Set[str]] = {}  # user_id -> workspace_ids
        self.agent_workspaces: Dict[str, Set[str]] = {}  # agent_id -> workspace_ids
        self.activity_logs: List[WorkspaceActivity] = []
        self.lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the workspace manager"""
        logger.info("Workspace manager initialized")
        
        # Create default workspace
        await self._create_default_workspace()
    
    async def _create_default_workspace(self):
        """Create a default workspace"""
        default_workspace = Workspace(
            id="default-workspace",
            name="Default Workspace",
            description="Default collaborative workspace",
            created_by="system"
        )
        await self.create_workspace(default_workspace)
    
    async def create_workspace(self, workspace: Workspace) -> str:
        """Create a new workspace"""
        try:
            async with self.lock:
                # Generate ID if not provided
                if not workspace.id:
                    workspace.id = str(uuid.uuid4())
                
                # Validate workspace
                if workspace.id in self.workspaces:
                    raise ValueError(f"Workspace {workspace.id} already exists")
                
                # Add to workspaces
                self.workspaces[workspace.id] = workspace
                
                # Add creator to workspace
                if workspace.created_by:
                    workspace.users.add(workspace.created_by)
                    if workspace.created_by not in self.user_workspaces:
                        self.user_workspaces[workspace.created_by] = set()
                    self.user_workspaces[workspace.created_by].add(workspace.id)
                
                # Log activity
                await self._log_activity(
                    workspace.id,
                    workspace.created_by,
                    "workspace_created",
                    f"Workspace '{workspace.name}' was created"
                )
                
                logger.info(f"Created workspace: {workspace.name} ({workspace.id})")
                return workspace.id
                
        except Exception as e:
            logger.error(f"Failed to create workspace: {e}")
            raise
    
    async def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get a workspace by ID"""
        return self.workspaces.get(workspace_id)
    
    async def get_all_workspaces(self) -> List[Workspace]:
        """Get all workspaces"""
        return list(self.workspaces.values())
    
    async def get_workspace_count(self) -> int:
        """Get the number of workspaces"""
        return len(self.workspaces)
    
    async def update_workspace(self, workspace_id: str, updates: Dict[str, Any]) -> bool:
        """Update workspace information"""
        try:
            async with self.lock:
                if workspace_id not in self.workspaces:
                    return False
                
                workspace = self.workspaces[workspace_id]
                
                # Update fields
                if "name" in updates:
                    workspace.name = updates["name"]
                if "description" in updates:
                    workspace.description = updates["description"]
                if "settings" in updates:
                    workspace.settings.update(updates["settings"])
                
                workspace.updated_at = datetime.utcnow()
                
                # Log activity
                await self._log_activity(
                    workspace_id,
                    "system",
                    "workspace_updated",
                    f"Workspace '{workspace.name}' was updated"
                )
                
                logger.info(f"Updated workspace: {workspace_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update workspace {workspace_id}: {e}")
            return False
    
    async def delete_workspace(self, workspace_id: str) -> bool:
        """Delete a workspace"""
        try:
            async with self.lock:
                if workspace_id not in self.workspaces:
                    return False
                
                workspace = self.workspaces[workspace_id]
                
                # Remove from user mappings
                for user_id in workspace.users:
                    if user_id in self.user_workspaces:
                        self.user_workspaces[user_id].discard(workspace_id)
                        if not self.user_workspaces[user_id]:
                            del self.user_workspaces[user_id]
                
                # Remove from agent mappings
                for agent_id in workspace.agents:
                    if agent_id in self.agent_workspaces:
                        self.agent_workspaces[agent_id].discard(workspace_id)
                        if not self.agent_workspaces[agent_id]:
                            del self.agent_workspaces[agent_id]
                
                # Log activity
                await self._log_activity(
                    workspace_id,
                    "system",
                    "workspace_deleted",
                    f"Workspace '{workspace.name}' was deleted"
                )
                
                del self.workspaces[workspace_id]
                logger.info(f"Deleted workspace: {workspace_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete workspace {workspace_id}: {e}")
            return False
    
    async def join_workspace(self, workspace_id: str, user_id: str) -> bool:
        """Add a user to a workspace"""
        try:
            async with self.lock:
                if workspace_id not in self.workspaces:
                    return False
                
                workspace = self.workspaces[workspace_id]
                
                # Check if user is already in workspace
                if user_id in workspace.users:
                    return True
                
                # Add user to workspace
                workspace.users.add(user_id)
                
                # Update user mappings
                if user_id not in self.user_workspaces:
                    self.user_workspaces[user_id] = set()
                self.user_workspaces[user_id].add(workspace_id)
                
                # Log activity
                await self._log_activity(
                    workspace_id,
                    user_id,
                    "user_joined",
                    f"User {user_id} joined the workspace"
                )
                
                logger.info(f"User {user_id} joined workspace {workspace_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add user {user_id} to workspace {workspace_id}: {e}")
            return False
    
    async def leave_workspace(self, workspace_id: str, user_id: str) -> bool:
        """Remove a user from a workspace"""
        try:
            async with self.lock:
                if workspace_id not in self.workspaces:
                    return False
                
                workspace = self.workspaces[workspace_id]
                
                # Check if user is in workspace
                if user_id not in workspace.users:
                    return True
                
                # Remove user from workspace
                workspace.users.discard(user_id)
                
                # Update user mappings
                if user_id in self.user_workspaces:
                    self.user_workspaces[user_id].discard(workspace_id)
                    if not self.user_workspaces[user_id]:
                        del self.user_workspaces[user_id]
                
                # Log activity
                await self._log_activity(
                    workspace_id,
                    user_id,
                    "user_left",
                    f"User {user_id} left the workspace"
                )
                
                logger.info(f"User {user_id} left workspace {workspace_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove user {user_id} from workspace {workspace_id}: {e}")
            return False
    
    async def add_agent_to_workspace(self, workspace_id: str, agent_id: str) -> bool:
        """Add an agent to a workspace"""
        try:
            async with self.lock:
                if workspace_id not in self.workspaces:
                    return False
                
                workspace = self.workspaces[workspace_id]
                
                # Check if agent is already in workspace
                if agent_id in workspace.agents:
                    return True
                
                # Add agent to workspace
                workspace.agents.add(agent_id)
                
                # Update agent mappings
                if agent_id not in self.agent_workspaces:
                    self.agent_workspaces[agent_id] = set()
                self.agent_workspaces[agent_id].add(workspace_id)
                
                # Log activity
                await self._log_activity(
                    workspace_id,
                    "system",
                    "agent_added",
                    f"Agent {agent_id} was added to the workspace"
                )
                
                logger.info(f"Agent {agent_id} added to workspace {workspace_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add agent {agent_id} to workspace {workspace_id}: {e}")
            return False
    
    async def remove_agent_from_workspace(self, workspace_id: str, agent_id: str) -> bool:
        """Remove an agent from a workspace"""
        try:
            async with self.lock:
                if workspace_id not in self.workspaces:
                    return False
                
                workspace = self.workspaces[workspace_id]
                
                # Check if agent is in workspace
                if agent_id not in workspace.agents:
                    return True
                
                # Remove agent from workspace
                workspace.agents.discard(agent_id)
                
                # Update agent mappings
                if agent_id in self.agent_workspaces:
                    self.agent_workspaces[agent_id].discard(workspace_id)
                    if not self.agent_workspaces[agent_id]:
                        del self.agent_workspaces[agent_id]
                
                # Log activity
                await self._log_activity(
                    workspace_id,
                    "system",
                    "agent_removed",
                    f"Agent {agent_id} was removed from the workspace"
                )
                
                logger.info(f"Agent {agent_id} removed from workspace {workspace_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove agent {agent_id} from workspace {workspace_id}: {e}")
            return False
    
    async def get_workspace_users(self, workspace_id: str) -> List[str]:
        """Get all users in a workspace"""
        if workspace_id not in self.workspaces:
            return []
        
        workspace = self.workspaces[workspace_id]
        return list(workspace.users)
    
    async def get_workspace_agents(self, workspace_id: str) -> List[str]:
        """Get all agents in a workspace"""
        if workspace_id not in self.workspaces:
            return []
        
        workspace = self.workspaces[workspace_id]
        return list(workspace.agents)
    
    async def get_user_workspaces(self, user_id: str) -> List[str]:
        """Get all workspaces for a user"""
        return list(self.user_workspaces.get(user_id, set()))
    
    async def get_agent_workspaces(self, agent_id: str) -> List[str]:
        """Get all workspaces for an agent"""
        return list(self.agent_workspaces.get(agent_id, set()))
    
    async def get_workspace_activity(self, workspace_id: str, limit: int = 50) -> List[WorkspaceActivity]:
        """Get workspace activity log"""
        activities = [
            activity for activity in self.activity_logs
            if activity.workspace_id == workspace_id
        ]
        
        # Sort by timestamp (newest first) and limit
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        return activities[:limit]
    
    async def _log_activity(self, workspace_id: str, user_id: str, activity_type: str, description: str, metadata: Optional[Dict[str, Any]] = None):
        """Log workspace activity"""
        activity = WorkspaceActivity(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            metadata=metadata or {}
        )
        
        self.activity_logs.append(activity)
        
        # Keep only last 1000 activities to prevent memory issues
        if len(self.activity_logs) > 1000:
            self.activity_logs = self.activity_logs[-1000:]
    
    async def get_workspace_statistics(self) -> Dict[str, Any]:
        """Get workspace statistics"""
        total_workspaces = len(self.workspaces)
        total_users = len(self.user_workspaces)
        total_agents = len(self.agent_workspaces)
        total_activities = len(self.activity_logs)
        
        # Calculate average users per workspace
        avg_users_per_workspace = 0
        if total_workspaces > 0:
            total_workspace_users = sum(len(workspace.users) for workspace in self.workspaces.values())
            avg_users_per_workspace = total_workspace_users / total_workspaces
        
        # Calculate average agents per workspace
        avg_agents_per_workspace = 0
        if total_workspaces > 0:
            total_workspace_agents = sum(len(workspace.agents) for workspace in self.workspaces.values())
            avg_agents_per_workspace = total_workspace_agents / total_workspaces
        
        # Get activity distribution
        activity_distribution = {}
        for activity in self.activity_logs:
            activity_type = activity.activity_type
            activity_distribution[activity_type] = activity_distribution.get(activity_type, 0) + 1
        
        return {
            "total_workspaces": total_workspaces,
            "total_users": total_users,
            "total_agents": total_agents,
            "total_activities": total_activities,
            "avg_users_per_workspace": round(avg_users_per_workspace, 2),
            "avg_agents_per_workspace": round(avg_agents_per_workspace, 2),
            "activity_distribution": activity_distribution,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def search_workspaces(self, query: str) -> List[Workspace]:
        """Search workspaces by name or description"""
        query_lower = query.lower()
        results = []
        
        for workspace in self.workspaces.values():
            if (query_lower in workspace.name.lower() or 
                (workspace.description and query_lower in workspace.description.lower())):
                results.append(workspace)
        
        return results
    
    async def get_workspace_permissions(self, workspace_id: str, user_id: str) -> Dict[str, bool]:
        """Get user permissions for a workspace"""
        if workspace_id not in self.workspaces:
            return {}
        
        workspace = self.workspaces[workspace_id]
        
        # Basic permissions
        can_view = user_id in workspace.users
        can_edit = user_id == workspace.created_by
        can_delete = user_id == workspace.created_by
        can_manage_users = user_id == workspace.created_by
        can_manage_agents = user_id == workspace.created_by
        
        return {
            "can_view": can_view,
            "can_edit": can_edit,
            "can_delete": can_delete,
            "can_manage_users": can_manage_users,
            "can_manage_agents": can_manage_agents
        }