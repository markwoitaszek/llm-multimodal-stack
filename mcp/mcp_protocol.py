#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Implementation
Part of Issue #6: MCP Support

This module provides comprehensive MCP protocol support including:
- MCP protocol message handling
- Tool discovery and execution
- Resource management and caching
- Client/server architecture
- AI model integration
- Protocol validation and error handling
"""

import asyncio
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Awaitable
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from pathlib import Path
import aiohttp
import websockets
from websockets.server import WebSocketServerProtocol
import sseclient
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPMessageType(Enum):
    """MCP message type enumeration"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

class MCPMethod(Enum):
    """MCP method enumeration"""
    # Core methods
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    PING = "ping"
    PONG = "pong"
    
    # Tool methods
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    
    # Resource methods
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"
    RESOURCES_UNSUBSCRIBE = "resources/unsubscribe"
    
    # Prompt methods
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    
    # Completion methods
    COMPLETIONS_COMPLETE = "completions/complete"

class MCPErrorCode(Enum):
    """MCP error code enumeration"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR = -32000
    TOOL_ERROR = -32001
    RESOURCE_ERROR = -32002
    PROMPT_ERROR = -32003
    COMPLETION_ERROR = -32004

@dataclass
class MCPMessage:
    """MCP message structure"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Optional[Callable] = None

@dataclass
class MCPResource:
    """MCP resource definition"""
    uri: str
    name: str
    description: str
    mime_type: str
    handler: Optional[Callable] = None

@dataclass
class MCPPrompt:
    """MCP prompt definition"""
    name: str
    description: str
    arguments: List[Dict[str, Any]]
    handler: Optional[Callable] = None

@dataclass
class MCPCompletion:
    """MCP completion definition"""
    completion: str
    is_partial: bool = False
    finish_reason: Optional[str] = None

class MCPError(Exception):
    """MCP protocol error"""
    def __init__(self, code: MCPErrorCode, message: str, data: Optional[Any] = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

class MCPClient:
    """MCP client implementation"""
    
    def __init__(self, server_url: str, client_info: Dict[str, Any] = None):
        self.server_url = server_url
        self.client_info = client_info or {
            "name": "MCP Client",
            "version": "1.0.0"
        }
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[WebSocketServerProtocol] = None
        self.message_id = 0
        self.pending_requests: Dict[Union[str, int], asyncio.Future] = {}
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        self.initialized = False
        
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    async def connect(self):
        """Connect to MCP server"""
        try:
            if self.server_url.startswith("ws://") or self.server_url.startswith("wss://"):
                await self._connect_websocket()
            else:
                await self._connect_http()
            
            # Initialize the connection
            await self.initialize()
            
            logger.info(f"Connected to MCP server: {self.server_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise
    
    async def _connect_websocket(self):
        """Connect via WebSocket"""
        self.websocket = await websockets.connect(self.server_url)
        
        # Start message handler
        asyncio.create_task(self._handle_websocket_messages())
    
    async def _connect_http(self):
        """Connect via HTTP"""
        self.session = aiohttp.ClientSession()
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("Disconnected from MCP server")
    
    async def _handle_websocket_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error handling WebSocket messages: {e}")
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming message"""
        message = MCPMessage(**data)
        
        if message.id and message.id in self.pending_requests:
            # This is a response to a pending request
            future = self.pending_requests.pop(message.id)
            if message.error:
                future.set_exception(MCPError(
                    MCPErrorCode(message.error.get("code", -32603)),
                    message.error.get("message", "Unknown error"),
                    message.error.get("data")
                ))
            else:
                future.set_result(message.result)
        else:
            # This is a notification
            await self._handle_notification(message)
    
    async def _handle_notification(self, message: MCPMessage):
        """Handle notification message"""
        if message.method == "notifications/resource_changed":
            # Handle resource change notification
            await self._handle_resource_change(message.params)
        elif message.method == "notifications/tool_result":
            # Handle tool result notification
            await self._handle_tool_result(message.params)
    
    async def _handle_resource_change(self, params: Dict[str, Any]):
        """Handle resource change notification"""
        uri = params.get("uri")
        if uri in self.resources:
            logger.info(f"Resource changed: {uri}")
            # Update resource cache or trigger refresh
    
    async def _handle_tool_result(self, params: Dict[str, Any]):
        """Handle tool result notification"""
        tool_name = params.get("name")
        result = params.get("result")
        logger.info(f"Tool result: {tool_name} -> {result}")
    
    async def _send_message(self, message: MCPMessage) -> Any:
        """Send message and wait for response"""
        if self.websocket:
            return await self._send_websocket_message(message)
        else:
            return await self._send_http_message(message)
    
    async def _send_websocket_message(self, message: MCPMessage) -> Any:
        """Send WebSocket message"""
        if message.id is None:
            # Notification - no response expected
            await self.websocket.send(json.dumps(asdict(message)))
            return None
        
        # Request - wait for response
        future = asyncio.Future()
        self.pending_requests[message.id] = future
        
        await self.websocket.send(json.dumps(asdict(message)))
        
        try:
            return await asyncio.wait_for(future, timeout=30.0)
        except asyncio.TimeoutError:
            self.pending_requests.pop(message.id, None)
            raise MCPError(MCPErrorCode.SERVER_ERROR, "Request timeout")
    
    async def _send_http_message(self, message: MCPMessage) -> Any:
        """Send HTTP message"""
        if not self.session:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "No HTTP session")
        
        async with self.session.post(
            self.server_url,
            json=asdict(message),
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                raise MCPError(MCPErrorCode.SERVER_ERROR, f"HTTP error: {response.status}")
            
            data = await response.json()
            response_message = MCPMessage(**data)
            
            if response_message.error:
                raise MCPError(
                    MCPErrorCode(response_message.error.get("code", -32603)),
                    response_message.error.get("message", "Unknown error"),
                    response_message.error.get("data")
                )
            
            return response_message.result
    
    def _get_next_id(self) -> int:
        """Get next message ID"""
        self.message_id += 1
        return self.message_id
    
    async def initialize(self):
        """Initialize MCP connection"""
        message = MCPMessage(
            id=self._get_next_id(),
            method=MCPMethod.INITIALIZE.value,
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "clientInfo": self.client_info
            }
        )
        
        result = await self._send_message(message)
        
        # Send initialized notification
        initialized_message = MCPMessage(
            method=MCPMethod.INITIALIZED.value
        )
        await self._send_message(initialized_message)
        
        self.initialized = True
        return result
    
    async def ping(self) -> str:
        """Send ping to server"""
        message = MCPMessage(
            id=self._get_next_id(),
            method=MCPMethod.PING.value
        )
        
        result = await self._send_message(message)
        return result.get("pong", "pong")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        message = MCPMessage(
            id=self._get_next_id(),
            method=MCPMethod.TOOLS_LIST.value
        )
        
        result = await self._send_message(message)
        return result.get("tools", [])
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool"""
        message = MCPMessage(
            id=self._get_next_id(),
            method=MCPMethod.TOOLS_CALL.value,
            params={
                "name": name,
                "arguments": arguments
            }
        )
        
        result = await self._send_message(message)
        return result
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources"""
        message = MCPMessage(
            id=self._get_next_id(),
            method=MCPMethod.RESOURCES_LIST.value
        )
        
        result = await self._send_message(message)
        return result.get("resources", [])
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource"""
        message = MCPMessage(
            id=self._get_next_id(),
            method=MCPMethod.RESOURCES_READ.value,
            params={"uri": uri}
        )
        
        result = await self._send_message(message)
        return result
    
    async def subscribe_to_resource(self, uri: str) -> bool:
        """Subscribe to resource changes"""
        message = MCPMessage(
            id=self._get_next_id(),
            method=MCPMethod.RESOURCES_SUBSCRIBE.value,
            params={"uri": uri}
        )
        
        result = await self._send_message(message)
        return result.get("subscribed", False)
    
    async def unsubscribe_from_resource(self, uri: str) -> bool:
        """Unsubscribe from resource changes"""
        message = MCPMessage(
            id=self._get_next_id(),
            method=MCPMethod.RESOURCES_UNSUBSCRIBE.value,
            params={"uri": uri}
        )
        
        result = await self._send_message(message)
        return result.get("unsubscribed", False)
    
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List available prompts"""
        message = MCPMessage(
            id=self._get_next_id(),
            method=MCPMethod.PROMPTS_LIST.value
        )
        
        result = await self._send_message(message)
        return result.get("prompts", [])
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get a prompt"""
        message = MCPMessage(
            id=self._get_next_id(),
            method=MCPMethod.PROMPTS_GET.value,
            params={
                "name": name,
                "arguments": arguments or {}
            }
        )
        
        result = await self._send_message(message)
        return result
    
    async def complete(self, prompt: str, max_tokens: int = 1000) -> MCPCompletion:
        """Get completion for a prompt"""
        message = MCPMessage(
            id=self._get_next_id(),
            method=MCPMethod.COMPLETIONS_COMPLETE.value,
            params={
                "prompt": prompt,
                "maxTokens": max_tokens
            }
        )
        
        result = await self._send_message(message)
        
        return MCPCompletion(
            completion=result.get("completion", ""),
            is_partial=result.get("isPartial", False),
            finish_reason=result.get("finishReason")
        )

class MCPServer:
    """MCP server implementation"""
    
    def __init__(self, server_info: Dict[str, Any] = None):
        self.server_info = server_info or {
            "name": "MCP Server",
            "version": "1.0.0"
        }
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        self.clients: Dict[str, Any] = {}
        self.resource_subscriptions: Dict[str, List[str]] = {}  # uri -> client_ids
        
    def register_tool(self, tool: MCPTool):
        """Register a tool"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def register_resource(self, resource: MCPResource):
        """Register a resource"""
        self.resources[resource.uri] = resource
        logger.info(f"Registered resource: {resource.uri}")
    
    def register_prompt(self, prompt: MCPPrompt):
        """Register a prompt"""
        self.prompts[prompt.name] = prompt
        logger.info(f"Registered prompt: {prompt.name}")
    
    async def handle_message(self, message: MCPMessage, client_id: str) -> MCPMessage:
        """Handle incoming message"""
        try:
            if message.method == MCPMethod.INITIALIZE.value:
                return await self._handle_initialize(message, client_id)
            elif message.method == MCPMethod.PING.value:
                return await self._handle_ping(message)
            elif message.method == MCPMethod.TOOLS_LIST.value:
                return await self._handle_tools_list(message)
            elif message.method == MCPMethod.TOOLS_CALL.value:
                return await self._handle_tools_call(message)
            elif message.method == MCPMethod.RESOURCES_LIST.value:
                return await self._handle_resources_list(message)
            elif message.method == MCPMethod.RESOURCES_READ.value:
                return await self._handle_resources_read(message)
            elif message.method == MCPMethod.RESOURCES_SUBSCRIBE.value:
                return await self._handle_resources_subscribe(message, client_id)
            elif message.method == MCPMethod.RESOURCES_UNSUBSCRIBE.value:
                return await self._handle_resources_unsubscribe(message, client_id)
            elif message.method == MCPMethod.PROMPTS_LIST.value:
                return await self._handle_prompts_list(message)
            elif message.method == MCPMethod.PROMPTS_GET.value:
                return await self._handle_prompts_get(message)
            elif message.method == MCPMethod.COMPLETIONS_COMPLETE.value:
                return await self._handle_completions_complete(message)
            else:
                return self._create_error_response(
                    message.id,
                    MCPErrorCode.METHOD_NOT_FOUND,
                    f"Unknown method: {message.method}"
                )
        
        except MCPError as e:
            return self._create_error_response(message.id, e.code, e.message, e.data)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return self._create_error_response(
                message.id,
                MCPErrorCode.INTERNAL_ERROR,
                f"Internal error: {str(e)}"
            )
    
    async def _handle_initialize(self, message: MCPMessage, client_id: str) -> MCPMessage:
        """Handle initialize request"""
        self.clients[client_id] = {
            "info": message.params.get("clientInfo", {}),
            "capabilities": message.params.get("capabilities", {}),
            "initialized": False
        }
        
        return MCPMessage(
            id=message.id,
            result={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": True, "listChanged": True},
                    "prompts": {"listChanged": True}
                },
                "serverInfo": self.server_info
            }
        )
    
    async def _handle_ping(self, message: MCPMessage) -> MCPMessage:
        """Handle ping request"""
        return MCPMessage(
            id=message.id,
            result={"pong": "pong"}
        )
    
    async def _handle_tools_list(self, message: MCPMessage) -> MCPMessage:
        """Handle tools list request"""
        tools = []
        for tool in self.tools.values():
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            })
        
        return MCPMessage(
            id=message.id,
            result={"tools": tools}
        )
    
    async def _handle_tools_call(self, message: MCPMessage) -> MCPMessage:
        """Handle tool call request"""
        name = message.params.get("name")
        arguments = message.params.get("arguments", {})
        
        if name not in self.tools:
            return self._create_error_response(
                message.id,
                MCPErrorCode.TOOL_ERROR,
                f"Tool not found: {name}"
            )
        
        tool = self.tools[name]
        
        try:
            if tool.handler:
                if asyncio.iscoroutinefunction(tool.handler):
                    result = await tool.handler(arguments)
                else:
                    result = tool.handler(arguments)
            else:
                result = {"message": f"Tool {name} called with arguments: {arguments}"}
            
            return MCPMessage(
                id=message.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": str(result)
                        }
                    ]
                }
            )
        
        except Exception as e:
            return self._create_error_response(
                message.id,
                MCPErrorCode.TOOL_ERROR,
                f"Tool execution error: {str(e)}"
            )
    
    async def _handle_resources_list(self, message: MCPMessage) -> MCPMessage:
        """Handle resources list request"""
        resources = []
        for resource in self.resources.values():
            resources.append({
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": resource.mime_type
            })
        
        return MCPMessage(
            id=message.id,
            result={"resources": resources}
        )
    
    async def _handle_resources_read(self, message: MCPMessage) -> MCPMessage:
        """Handle resource read request"""
        uri = message.params.get("uri")
        
        if uri not in self.resources:
            return self._create_error_response(
                message.id,
                MCPErrorCode.RESOURCE_ERROR,
                f"Resource not found: {uri}"
            )
        
        resource = self.resources[uri]
        
        try:
            if resource.handler:
                if asyncio.iscoroutinefunction(resource.handler):
                    content = await resource.handler()
                else:
                    content = resource.handler()
            else:
                content = f"Resource content for {uri}"
            
            return MCPMessage(
                id=message.id,
                result={
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": resource.mime_type,
                            "text": str(content)
                        }
                    ]
                }
            )
        
        except Exception as e:
            return self._create_error_response(
                message.id,
                MCPErrorCode.RESOURCE_ERROR,
                f"Resource read error: {str(e)}"
            )
    
    async def _handle_resources_subscribe(self, message: MCPMessage, client_id: str) -> MCPMessage:
        """Handle resource subscription request"""
        uri = message.params.get("uri")
        
        if uri not in self.resources:
            return self._create_error_response(
                message.id,
                MCPErrorCode.RESOURCE_ERROR,
                f"Resource not found: {uri}"
            )
        
        if uri not in self.resource_subscriptions:
            self.resource_subscriptions[uri] = []
        
        if client_id not in self.resource_subscriptions[uri]:
            self.resource_subscriptions[uri].append(client_id)
        
        return MCPMessage(
            id=message.id,
            result={"subscribed": True}
        )
    
    async def _handle_resources_unsubscribe(self, message: MCPMessage, client_id: str) -> MCPMessage:
        """Handle resource unsubscription request"""
        uri = message.params.get("uri")
        
        if uri in self.resource_subscriptions:
            if client_id in self.resource_subscriptions[uri]:
                self.resource_subscriptions[uri].remove(client_id)
        
        return MCPMessage(
            id=message.id,
            result={"unsubscribed": True}
        )
    
    async def _handle_prompts_list(self, message: MCPMessage) -> MCPMessage:
        """Handle prompts list request"""
        prompts = []
        for prompt in self.prompts.values():
            prompts.append({
                "name": prompt.name,
                "description": prompt.description,
                "arguments": prompt.arguments
            })
        
        return MCPMessage(
            id=message.id,
            result={"prompts": prompts}
        )
    
    async def _handle_prompts_get(self, message: MCPMessage) -> MCPMessage:
        """Handle prompt get request"""
        name = message.params.get("name")
        arguments = message.params.get("arguments", {})
        
        if name not in self.prompts:
            return self._create_error_response(
                message.id,
                MCPErrorCode.PROMPT_ERROR,
                f"Prompt not found: {name}"
            )
        
        prompt = self.prompts[name]
        
        try:
            if prompt.handler:
                if asyncio.iscoroutinefunction(prompt.handler):
                    result = await prompt.handler(arguments)
                else:
                    result = prompt.handler(arguments)
            else:
                result = f"Prompt {name} with arguments: {arguments}"
            
            return MCPMessage(
                id=message.id,
                result={
                    "description": prompt.description,
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": str(result)
                            }
                        }
                    ]
                }
            )
        
        except Exception as e:
            return self._create_error_response(
                message.id,
                MCPErrorCode.PROMPT_ERROR,
                f"Prompt execution error: {str(e)}"
            )
    
    async def _handle_completions_complete(self, message: MCPMessage) -> MCPMessage:
        """Handle completion request"""
        prompt = message.params.get("prompt", "")
        max_tokens = message.params.get("maxTokens", 1000)
        
        # Simple completion implementation
        completion = f"Completion for: {prompt[:50]}..."
        
        return MCPMessage(
            id=message.id,
            result={
                "completion": completion,
                "isPartial": False,
                "finishReason": "stop"
            }
        )
    
    def _create_error_response(self, message_id: Optional[Union[str, int]], code: MCPErrorCode, message: str, data: Optional[Any] = None) -> MCPMessage:
        """Create error response"""
        return MCPMessage(
            id=message_id,
            error={
                "code": code.value,
                "message": message,
                "data": data
            }
        )
    
    async def notify_resource_changed(self, uri: str):
        """Notify clients of resource change"""
        if uri in self.resource_subscriptions:
            for client_id in self.resource_subscriptions[uri]:
                # In a real implementation, this would send notifications to clients
                logger.info(f"Notifying client {client_id} of resource change: {uri}")

async def main():
    """Main function to demonstrate MCP protocol"""
    # Create MCP server
    server = MCPServer()
    
    # Register some tools
    def echo_tool(arguments):
        return f"Echo: {arguments.get('message', 'Hello')}"
    
    server.register_tool(MCPTool(
        name="echo",
        description="Echo a message",
        input_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message to echo"}
            },
            "required": ["message"]
        },
        handler=echo_tool
    ))
    
    # Register some resources
    def file_resource():
        return "This is file content"
    
    server.register_resource(MCPResource(
        uri="file://example.txt",
        name="Example File",
        description="An example file resource",
        mime_type="text/plain",
        handler=file_resource
    ))
    
    # Register some prompts
    def code_prompt(arguments):
        return f"Write code for: {arguments.get('task', 'Hello World')}"
    
    server.register_prompt(MCPPrompt(
        name="code_generator",
        description="Generate code for a given task",
        arguments=[
            {"name": "task", "description": "The task to generate code for", "required": True}
        ],
        handler=code_prompt
    ))
    
    print("MCP Server created with tools, resources, and prompts")
    print(f"Tools: {list(server.tools.keys())}")
    print(f"Resources: {list(server.resources.keys())}")
    print(f"Prompts: {list(server.prompts.keys())}")

if __name__ == "__main__":
    asyncio.run(main())