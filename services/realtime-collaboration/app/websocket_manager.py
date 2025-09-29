"""
WebSocket Manager for handling WebSocket connections and message broadcasting
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field

from fastapi import WebSocket

logger = logging.getLogger(__name__)

@dataclass
class ConnectionInfo:
    """WebSocket connection information"""
    connection_id: str
    websocket: WebSocket
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    subscriptions: Set[str] = field(default_factory=set)

class WebSocketManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.workspace_connections: Dict[str, Set[str]] = {}  # workspace_id -> connection_ids
        self.subscription_connections: Dict[str, Set[str]] = {}  # subscription -> connection_ids
        self.lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the WebSocket manager"""
        logger.info("WebSocket manager initialized")
    
    async def add_connection(self, connection_id: str, websocket: WebSocket, user_id: Optional[str] = None) -> bool:
        """Add a new WebSocket connection"""
        try:
            async with self.lock:
                connection_info = ConnectionInfo(
                    connection_id=connection_id,
                    websocket=websocket,
                    user_id=user_id
                )
                
                self.connections[connection_id] = connection_info
                
                # Update user connections mapping
                if user_id:
                    if user_id not in self.user_connections:
                        self.user_connections[user_id] = set()
                    self.user_connections[user_id].add(connection_id)
                
                logger.info(f"Added WebSocket connection: {connection_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add connection {connection_id}: {e}")
            return False
    
    async def remove_connection(self, connection_id: str) -> bool:
        """Remove a WebSocket connection"""
        try:
            async with self.lock:
                if connection_id not in self.connections:
                    logger.warning(f"Connection {connection_id} not found")
                    return False
                
                connection_info = self.connections[connection_id]
                
                # Remove from user connections mapping
                if connection_info.user_id:
                    if connection_info.user_id in self.user_connections:
                        self.user_connections[connection_info.user_id].discard(connection_id)
                        if not self.user_connections[connection_info.user_id]:
                            del self.user_connections[connection_info.user_id]
                
                # Remove from workspace connections mapping
                if connection_info.workspace_id:
                    if connection_info.workspace_id in self.workspace_connections:
                        self.workspace_connections[connection_info.workspace_id].discard(connection_id)
                        if not self.workspace_connections[connection_info.workspace_id]:
                            del self.workspace_connections[connection_info.workspace_id]
                
                # Remove from subscription mappings
                for subscription in connection_info.subscriptions:
                    if subscription in self.subscription_connections:
                        self.subscription_connections[subscription].discard(connection_id)
                        if not self.subscription_connections[subscription]:
                            del self.subscription_connections[subscription]
                
                del self.connections[connection_id]
                logger.info(f"Removed WebSocket connection: {connection_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove connection {connection_id}: {e}")
            return False
    
    async def update_connection_info(self, connection_id: str, **kwargs) -> bool:
        """Update connection information"""
        try:
            async with self.lock:
                if connection_id not in self.connections:
                    return False
                
                connection_info = self.connections[connection_id]
                
                # Update user_id if provided
                if "user_id" in kwargs:
                    old_user_id = connection_info.user_id
                    new_user_id = kwargs["user_id"]
                    
                    # Remove from old user mapping
                    if old_user_id and old_user_id in self.user_connections:
                        self.user_connections[old_user_id].discard(connection_id)
                        if not self.user_connections[old_user_id]:
                            del self.user_connections[old_user_id]
                    
                    # Add to new user mapping
                    if new_user_id:
                        if new_user_id not in self.user_connections:
                            self.user_connections[new_user_id] = set()
                        self.user_connections[new_user_id].add(connection_id)
                    
                    connection_info.user_id = new_user_id
                
                # Update workspace_id if provided
                if "workspace_id" in kwargs:
                    old_workspace_id = connection_info.workspace_id
                    new_workspace_id = kwargs["workspace_id"]
                    
                    # Remove from old workspace mapping
                    if old_workspace_id and old_workspace_id in self.workspace_connections:
                        self.workspace_connections[old_workspace_id].discard(connection_id)
                        if not self.workspace_connections[old_workspace_id]:
                            del self.workspace_connections[old_workspace_id]
                    
                    # Add to new workspace mapping
                    if new_workspace_id:
                        if new_workspace_id not in self.workspace_connections:
                            self.workspace_connections[new_workspace_id] = set()
                        self.workspace_connections[new_workspace_id].add(connection_id)
                    
                    connection_info.workspace_id = new_workspace_id
                
                # Update last activity
                connection_info.last_activity = datetime.utcnow()
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to update connection {connection_id}: {e}")
            return False
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific connection"""
        try:
            if connection_id not in self.connections:
                return False
            
            connection_info = self.connections[connection_id]
            websocket = connection_info.websocket
            
            # Check if WebSocket is still open
            if websocket.client_state.name != "CONNECTED":
                await self.remove_connection(connection_id)
                return False
            
            # Send message
            await websocket.send_text(json.dumps(message))
            
            # Update last activity
            connection_info.last_activity = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to connection {connection_id}: {e}")
            # Remove connection if it's no longer valid
            await self.remove_connection(connection_id)
            return False
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """Send a message to all connections of a user"""
        sent_count = 0
        
        if user_id in self.user_connections:
            for connection_id in list(self.user_connections[user_id]):
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        
        return sent_count
    
    async def broadcast_to_workspace(self, workspace_id: str, message: Dict[str, Any]) -> int:
        """Broadcast a message to all connections in a workspace"""
        sent_count = 0
        
        if workspace_id in self.workspace_connections:
            for connection_id in list(self.workspace_connections[workspace_id]):
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        
        return sent_count
    
    async def broadcast_to_subscription(self, subscription: str, message: Dict[str, Any]) -> int:
        """Broadcast a message to all connections subscribed to a topic"""
        sent_count = 0
        
        if subscription in self.subscription_connections:
            for connection_id in list(self.subscription_connections[subscription]):
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """Broadcast a message to all connections"""
        sent_count = 0
        
        for connection_id in list(self.connections.keys()):
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def add_subscription(self, connection_id: str, subscription: str) -> bool:
        """Add a subscription for a connection"""
        try:
            async with self.lock:
                if connection_id not in self.connections:
                    return False
                
                connection_info = self.connections[connection_id]
                connection_info.subscriptions.add(subscription)
                
                if subscription not in self.subscription_connections:
                    self.subscription_connections[subscription] = set()
                self.subscription_connections[subscription].add(connection_id)
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to add subscription {subscription} for connection {connection_id}: {e}")
            return False
    
    async def remove_subscription(self, connection_id: str, subscription: str) -> bool:
        """Remove a subscription for a connection"""
        try:
            async with self.lock:
                if connection_id not in self.connections:
                    return False
                
                connection_info = self.connections[connection_id]
                connection_info.subscriptions.discard(subscription)
                
                if subscription in self.subscription_connections:
                    self.subscription_connections[subscription].discard(connection_id)
                    if not self.subscription_connections[subscription]:
                        del self.subscription_connections[subscription]
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove subscription {subscription} for connection {connection_id}: {e}")
            return False
    
    async def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.connections)
    
    async def get_connection_info(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get connection information"""
        return self.connections.get(connection_id)
    
    async def get_all_connections(self) -> List[Dict[str, Any]]:
        """Get information about all connections"""
        connections = []
        for connection_id, connection_info in self.connections.items():
            connections.append({
                "connection_id": connection_id,
                "user_id": connection_info.user_id,
                "workspace_id": connection_info.workspace_id,
                "connected_at": connection_info.connected_at.isoformat(),
                "last_activity": connection_info.last_activity.isoformat(),
                "subscriptions": list(connection_info.subscriptions)
            })
        return connections
    
    async def get_user_connections(self, user_id: str) -> List[str]:
        """Get all connection IDs for a user"""
        return list(self.user_connections.get(user_id, set()))
    
    async def get_workspace_connections(self, workspace_id: str) -> List[str]:
        """Get all connection IDs for a workspace"""
        return list(self.workspace_connections.get(workspace_id, set()))
    
    async def get_subscription_connections(self, subscription: str) -> List[str]:
        """Get all connection IDs for a subscription"""
        return list(self.subscription_connections.get(subscription, set()))
    
    async def cleanup_stale_connections(self) -> int:
        """Clean up stale connections"""
        cleaned_count = 0
        current_time = datetime.utcnow()
        
        for connection_id in list(self.connections.keys()):
            connection_info = self.connections[connection_id]
            
            # Check if connection is stale (no activity for 5 minutes)
            time_since_activity = (current_time - connection_info.last_activity).total_seconds()
            if time_since_activity > 300:  # 5 minutes
                await self.remove_connection(connection_id)
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} stale connections")
        
        return cleaned_count
    
    async def disconnect_all(self) -> int:
        """Disconnect all connections"""
        disconnected_count = 0
        
        for connection_id in list(self.connections.keys()):
            try:
                connection_info = self.connections[connection_id]
                await connection_info.websocket.close()
                await self.remove_connection(connection_id)
                disconnected_count += 1
            except Exception as e:
                logger.error(f"Error disconnecting connection {connection_id}: {e}")
        
        logger.info(f"Disconnected {disconnected_count} connections")
        return disconnected_count
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        total_connections = len(self.connections)
        total_users = len(self.user_connections)
        total_workspaces = len(self.workspace_connections)
        total_subscriptions = len(self.subscription_connections)
        
        # Calculate average connections per user
        avg_connections_per_user = 0
        if total_users > 0:
            total_user_connections = sum(len(conns) for conns in self.user_connections.values())
            avg_connections_per_user = total_user_connections / total_users
        
        # Calculate average connections per workspace
        avg_connections_per_workspace = 0
        if total_workspaces > 0:
            total_workspace_connections = sum(len(conns) for conns in self.workspace_connections.values())
            avg_connections_per_workspace = total_workspace_connections / total_workspaces
        
        return {
            "total_connections": total_connections,
            "total_users": total_users,
            "total_workspaces": total_workspaces,
            "total_subscriptions": total_subscriptions,
            "avg_connections_per_user": round(avg_connections_per_user, 2),
            "avg_connections_per_workspace": round(avg_connections_per_workspace, 2),
            "timestamp": datetime.utcnow().isoformat()
        }