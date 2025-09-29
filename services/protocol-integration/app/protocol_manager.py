"""
Protocol Manager for managing multiple protocol servers and clients
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class ProtocolStatus(Enum):
    """Protocol server status"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class ProtocolServer:
    """Protocol server configuration"""
    id: str
    name: str
    protocol_type: str
    port: int
    host: str = "localhost"
    status: ProtocolStatus = ProtocolStatus.STOPPED
    config: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

@dataclass
class ProtocolClient:
    """Protocol client configuration"""
    id: str
    name: str
    protocol_type: str
    server_url: str
    status: ProtocolStatus = ProtocolStatus.STOPPED
    config: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

class ProtocolManager:
    """Manages multiple protocol servers and clients"""
    
    def __init__(self):
        self.servers: Dict[str, ProtocolServer] = {}
        self.clients: Dict[str, ProtocolClient] = {}
        self.running_servers: Set[str] = set()
        self.running_clients: Set[str] = set()
        self.server_processes: Dict[str, Any] = {}
        self.client_connections: Dict[str, Any] = {}
    
    async def initialize(self):
        """Initialize the protocol manager"""
        logger.info("Protocol manager initialized")
        
        # Initialize default servers
        await self._initialize_default_servers()
    
    async def _initialize_default_servers(self):
        """Initialize default protocol servers"""
        # LSP Server
        lsp_server = ProtocolServer(
            id="lsp-server-1",
            name="LSP Language Server",
            protocol_type="lsp",
            port=3000,
            capabilities=[
                "textDocument/completion",
                "textDocument/hover",
                "textDocument/definition",
                "textDocument/references",
                "textDocument/formatting",
                "textDocument/diagnostic"
            ]
        )
        await self.add_server(lsp_server)
        
        # MCP Server
        mcp_server = ProtocolServer(
            id="mcp-server-1",
            name="MCP Model Context Server",
            protocol_type="mcp",
            port=3001,
            capabilities=[
                "code_completion",
                "code_hover",
                "code_definition",
                "code_analysis",
                "code_generation",
                "context_management"
            ]
        )
        await self.add_server(mcp_server)
        
        # REST API Server
        rest_server = ProtocolServer(
            id="rest-server-1",
            name="REST API Server",
            protocol_type="rest",
            port=3002,
            capabilities=[
                "completion",
                "hover",
                "definition",
                "references",
                "formatting",
                "diagnostic"
            ]
        )
        await self.add_server(rest_server)
    
    async def add_server(self, server: ProtocolServer) -> bool:
        """Add a new protocol server"""
        try:
            self.servers[server.id] = server
            logger.info(f"Added protocol server: {server.name} ({server.protocol_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to add server {server.name}: {e}")
            return False
    
    async def remove_server(self, server_id: str) -> bool:
        """Remove a protocol server"""
        try:
            if server_id in self.running_servers:
                await self.stop_server(server_id)
            
            if server_id in self.servers:
                del self.servers[server_id]
                logger.info(f"Removed protocol server: {server_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove server {server_id}: {e}")
            return False
    
    async def start_server(self, server_id: str) -> bool:
        """Start a protocol server"""
        try:
            if server_id not in self.servers:
                logger.error(f"Server {server_id} not found")
                return False
            
            server = self.servers[server_id]
            if server.status == ProtocolStatus.RUNNING:
                logger.warning(f"Server {server_id} is already running")
                return True
            
            server.status = ProtocolStatus.STARTING
            logger.info(f"Starting protocol server: {server.name}")
            
            # Start the server process (placeholder implementation)
            # In a real implementation, this would start the actual server process
            await asyncio.sleep(1)  # Simulate startup time
            
            server.status = ProtocolStatus.RUNNING
            self.running_servers.add(server_id)
            logger.info(f"Protocol server {server.name} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start server {server_id}: {e}")
            if server_id in self.servers:
                self.servers[server_id].status = ProtocolStatus.ERROR
                self.servers[server_id].error_message = str(e)
            return False
    
    async def stop_server(self, server_id: str) -> bool:
        """Stop a protocol server"""
        try:
            if server_id not in self.servers:
                logger.error(f"Server {server_id} not found")
                return False
            
            server = self.servers[server_id]
            if server.status != ProtocolStatus.RUNNING:
                logger.warning(f"Server {server_id} is not running")
                return True
            
            server.status = ProtocolStatus.STOPPING
            logger.info(f"Stopping protocol server: {server.name}")
            
            # Stop the server process (placeholder implementation)
            # In a real implementation, this would stop the actual server process
            await asyncio.sleep(0.5)  # Simulate shutdown time
            
            server.status = ProtocolStatus.STOPPED
            self.running_servers.discard(server_id)
            logger.info(f"Protocol server {server.name} stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop server {server_id}: {e}")
            if server_id in self.servers:
                self.servers[server_id].status = ProtocolStatus.ERROR
                self.servers[server_id].error_message = str(e)
            return False
    
    async def restart_server(self, server_id: str) -> bool:
        """Restart a protocol server"""
        try:
            await self.stop_server(server_id)
            await asyncio.sleep(1)  # Wait for complete shutdown
            return await self.start_server(server_id)
        except Exception as e:
            logger.error(f"Failed to restart server {server_id}: {e}")
            return False
    
    async def add_client(self, client: ProtocolClient) -> bool:
        """Add a new protocol client"""
        try:
            self.clients[client.id] = client
            logger.info(f"Added protocol client: {client.name} ({client.protocol_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to add client {client.name}: {e}")
            return False
    
    async def remove_client(self, client_id: str) -> bool:
        """Remove a protocol client"""
        try:
            if client_id in self.running_clients:
                await self.disconnect_client(client_id)
            
            if client_id in self.clients:
                del self.clients[client_id]
                logger.info(f"Removed protocol client: {client_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove client {client_id}: {e}")
            return False
    
    async def connect_client(self, client_id: str) -> bool:
        """Connect a protocol client to its server"""
        try:
            if client_id not in self.clients:
                logger.error(f"Client {client_id} not found")
                return False
            
            client = self.clients[client_id]
            if client.status == ProtocolStatus.RUNNING:
                logger.warning(f"Client {client_id} is already connected")
                return True
            
            client.status = ProtocolStatus.STARTING
            logger.info(f"Connecting protocol client: {client.name}")
            
            # Connect to the server (placeholder implementation)
            # In a real implementation, this would establish the actual connection
            await asyncio.sleep(0.5)  # Simulate connection time
            
            client.status = ProtocolStatus.RUNNING
            self.running_clients.add(client_id)
            logger.info(f"Protocol client {client.name} connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect client {client_id}: {e}")
            if client_id in self.clients:
                self.clients[client_id].status = ProtocolStatus.ERROR
                self.clients[client_id].error_message = str(e)
            return False
    
    async def disconnect_client(self, client_id: str) -> bool:
        """Disconnect a protocol client from its server"""
        try:
            if client_id not in self.clients:
                logger.error(f"Client {client_id} not found")
                return False
            
            client = self.clients[client_id]
            if client.status != ProtocolStatus.RUNNING:
                logger.warning(f"Client {client_id} is not connected")
                return True
            
            client.status = ProtocolStatus.STOPPING
            logger.info(f"Disconnecting protocol client: {client.name}")
            
            # Disconnect from the server (placeholder implementation)
            # In a real implementation, this would close the actual connection
            await asyncio.sleep(0.2)  # Simulate disconnection time
            
            client.status = ProtocolStatus.STOPPED
            self.running_clients.discard(client_id)
            logger.info(f"Protocol client {client.name} disconnected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect client {client_id}: {e}")
            if client_id in self.clients:
                self.clients[client_id].status = ProtocolStatus.ERROR
                self.clients[client_id].error_message = str(e)
            return False
    
    async def get_server_status(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific server"""
        if server_id not in self.servers:
            return None
        
        server = self.servers[server_id]
        return {
            "id": server.id,
            "name": server.name,
            "protocol_type": server.protocol_type,
            "port": server.port,
            "host": server.host,
            "status": server.status.value,
            "capabilities": server.capabilities,
            "error_message": server.error_message
        }
    
    async def get_client_status(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific client"""
        if client_id not in self.clients:
            return None
        
        client = self.clients[client_id]
        return {
            "id": client.id,
            "name": client.name,
            "protocol_type": client.protocol_type,
            "server_url": client.server_url,
            "status": client.status.value,
            "error_message": client.error_message
        }
    
    async def get_all_servers(self) -> List[Dict[str, Any]]:
        """Get status of all servers"""
        servers = []
        for server_id in self.servers:
            status = await self.get_server_status(server_id)
            if status:
                servers.append(status)
        return servers
    
    async def get_all_clients(self) -> List[Dict[str, Any]]:
        """Get status of all clients"""
        clients = []
        for client_id in self.clients:
            status = await self.get_client_status(client_id)
            if status:
                clients.append(status)
        return clients
    
    async def get_running_servers(self) -> List[str]:
        """Get list of running server IDs"""
        return list(self.running_servers)
    
    async def get_running_clients(self) -> List[str]:
        """Get list of running client IDs"""
        return list(self.running_clients)
    
    async def start_all_servers(self) -> Dict[str, bool]:
        """Start all configured servers"""
        results = {}
        for server_id in self.servers:
            results[server_id] = await self.start_server(server_id)
        return results
    
    async def stop_all_servers(self) -> Dict[str, bool]:
        """Stop all running servers"""
        results = {}
        for server_id in list(self.running_servers):
            results[server_id] = await self.stop_server(server_id)
        return results
    
    async def connect_all_clients(self) -> Dict[str, bool]:
        """Connect all configured clients"""
        results = {}
        for client_id in self.clients:
            results[client_id] = await self.connect_client(client_id)
        return results
    
    async def disconnect_all_clients(self) -> Dict[str, bool]:
        """Disconnect all running clients"""
        results = {}
        for client_id in list(self.running_clients):
            results[client_id] = await self.disconnect_client(client_id)
        return results
    
    async def get_protocol_capabilities(self, protocol_type: str) -> List[str]:
        """Get capabilities for a specific protocol type"""
        capabilities = []
        for server in self.servers.values():
            if server.protocol_type == protocol_type:
                capabilities.extend(server.capabilities)
        return list(set(capabilities))  # Remove duplicates
    
    async def find_server_by_capability(self, capability: str) -> Optional[str]:
        """Find a server that supports a specific capability"""
        for server_id, server in self.servers.items():
            if capability in server.capabilities and server.status == ProtocolStatus.RUNNING:
                return server_id
        return None
    
    async def get_protocol_statistics(self) -> Dict[str, Any]:
        """Get protocol usage statistics"""
        total_servers = len(self.servers)
        running_servers = len(self.running_servers)
        total_clients = len(self.clients)
        running_clients = len(self.running_clients)
        
        protocol_counts = {}
        for server in self.servers.values():
            protocol_counts[server.protocol_type] = protocol_counts.get(server.protocol_type, 0) + 1
        
        return {
            "total_servers": total_servers,
            "running_servers": running_servers,
            "total_clients": total_clients,
            "running_clients": running_clients,
            "protocol_distribution": protocol_counts,
            "uptime": "N/A"  # Would be calculated in a real implementation
        }