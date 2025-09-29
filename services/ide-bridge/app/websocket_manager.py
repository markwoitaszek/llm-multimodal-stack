"""
WebSocket manager for real-time IDE communication
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Set
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time IDE communication"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self.message_handlers: Dict[str, callable] = {}
        
        # Register default message handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.message_handlers["ping"] = self._handle_ping
        self.message_handlers["subscribe"] = self._handle_subscribe
        self.message_handlers["unsubscribe"] = self._handle_unsubscribe
        self.message_handlers["agent_execution"] = self._handle_agent_execution
        self.message_handlers["code_analysis"] = self._handle_code_analysis
        self.message_handlers["collaboration"] = self._handle_collaboration
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_metadata[websocket] = {
            "connected_at": datetime.now(),
            "subscriptions": set(),
            "user_id": None,
            "workspace": None
        }
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "welcome",
            "message": "Connected to IDE Bridge Service",
            "timestamp": datetime.now().isoformat()
        }, websocket)
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def disconnect_all(self):
        """Disconnect all WebSocket connections"""
        for websocket in list(self.active_connections):
            await self.disconnect(websocket)
    
    async def process_message(self, message: str) -> str:
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type in self.message_handlers:
                response = await self.message_handlers[message_type](data)
                return json.dumps(response)
            else:
                return json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.now().isoformat()
                })
        
        except json.JSONDecodeError:
            return json.dumps({
                "type": "error",
                "message": "Invalid JSON message",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            return json.dumps({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)
    
    async def broadcast_message(self, message: Dict[str, Any], exclude: WebSocket = None):
        """Broadcast a message to all connected WebSockets"""
        if not self.active_connections:
            return
        
        disconnected = []
        for websocket in self.active_connections:
            if websocket != exclude:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")
                    disconnected.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            await self.disconnect(websocket)
    
    async def send_to_subscribers(self, channel: str, message: Dict[str, Any]):
        """Send a message to all subscribers of a specific channel"""
        subscribers = []
        for websocket, metadata in self.connection_metadata.items():
            if channel in metadata.get("subscriptions", set()):
                subscribers.append(websocket)
        
        for websocket in subscribers:
            await self.send_personal_message({
                "type": "channel_message",
                "channel": channel,
                "data": message,
                "timestamp": datetime.now().isoformat()
            }, websocket)
    
    # Message handlers
    async def _handle_ping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping message"""
        return {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_subscribe(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription message"""
        # This would need to be called with the websocket context
        # For now, return a response indicating subscription was received
        channel = data.get("channel")
        if channel:
            return {
                "type": "subscribed",
                "channel": channel,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "type": "error",
                "message": "Channel not specified",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_unsubscribe(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unsubscription message"""
        channel = data.get("channel")
        if channel:
            return {
                "type": "unsubscribed",
                "channel": channel,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "type": "error",
                "message": "Channel not specified",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_agent_execution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent execution message"""
        agent_id = data.get("agent_id")
        task = data.get("task")
        
        if not agent_id or not task:
            return {
                "type": "error",
                "message": "Agent ID and task are required",
                "timestamp": datetime.now().isoformat()
            }
        
        # Broadcast agent execution start
        await self.broadcast_message({
            "type": "agent_execution_started",
            "agent_id": agent_id,
            "task": task,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "type": "agent_execution_received",
            "agent_id": agent_id,
            "task": task,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_code_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code analysis message"""
        code = data.get("code")
        language = data.get("language")
        
        if not code or not language:
            return {
                "type": "error",
                "message": "Code and language are required",
                "timestamp": datetime.now().isoformat()
            }
        
        # Broadcast code analysis request
        await self.broadcast_message({
            "type": "code_analysis_requested",
            "language": language,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "type": "code_analysis_received",
            "language": language,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_collaboration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle collaboration message"""
        action = data.get("action")
        workspace = data.get("workspace")
        
        if not action or not workspace:
            return {
                "type": "error",
                "message": "Action and workspace are required",
                "timestamp": datetime.now().isoformat()
            }
        
        # Broadcast collaboration event
        await self.send_to_subscribers(f"workspace:{workspace}", {
            "type": "collaboration_event",
            "action": action,
            "workspace": workspace,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "type": "collaboration_received",
            "action": action,
            "workspace": workspace,
            "timestamp": datetime.now().isoformat()
        }
    
    # Utility methods
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all connections"""
        info = []
        for websocket, metadata in self.connection_metadata.items():
            info.append({
                "connected_at": metadata["connected_at"].isoformat(),
                "subscriptions": list(metadata.get("subscriptions", set())),
                "user_id": metadata.get("user_id"),
                "workspace": metadata.get("workspace")
            })
        return info
    
    async def subscribe_to_channel(self, websocket: WebSocket, channel: str):
        """Subscribe a WebSocket to a channel"""
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["subscriptions"].add(channel)
            logger.info(f"WebSocket subscribed to channel: {channel}")
    
    async def unsubscribe_from_channel(self, websocket: WebSocket, channel: str):
        """Unsubscribe a WebSocket from a channel"""
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["subscriptions"].discard(channel)
            logger.info(f"WebSocket unsubscribed from channel: {channel}")
    
    async def set_user_context(self, websocket: WebSocket, user_id: str, workspace: str = None):
        """Set user context for a WebSocket connection"""
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["user_id"] = user_id
            if workspace:
                self.connection_metadata[websocket]["workspace"] = workspace
            logger.info(f"Set user context: {user_id} in workspace: {workspace}")