#!/usr/bin/env python3
"""
MCP Integration Framework
Part of Issue #6: MCP Support

This module provides comprehensive MCP integration including:
- AI model integration via MCP
- Tool execution framework
- Resource management and caching
- Prompt engineering and management
- Completion handling and streaming
- Integration with existing systems
"""

import asyncio
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Awaitable, AsyncGenerator
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from pathlib import Path
import aiohttp
import httpx
from contextlib import asynccontextmanager

# Import MCP protocol
from mcp_protocol import (
    MCPClient, MCPServer, MCPTool, MCPResource, MCPPrompt, MCPCompletion,
    MCPError, MCPErrorCode, MCPMethod
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    """AI model provider enumeration"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    LOCAL = "local"

class IntegrationType(Enum):
    """Integration type enumeration"""
    TOOL = "tool"
    RESOURCE = "resource"
    PROMPT = "prompt"
    COMPLETION = "completion"

@dataclass
class ModelConfig:
    """AI model configuration"""
    provider: ModelProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

@dataclass
class IntegrationConfig:
    """Integration configuration"""
    integration_id: str
    name: str
    description: str
    integration_type: IntegrationType
    model_config: ModelConfig
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionResult:
    """Tool execution result"""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class MCPIntegrationManager:
    """MCP integration manager"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Storage
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.mcp_clients: Dict[str, MCPClient] = {}
        self.mcp_servers: Dict[str, MCPServer] = {}
        self.tool_cache: Dict[str, Any] = {}
        self.resource_cache: Dict[str, Any] = {}
        self.prompt_cache: Dict[str, Any] = {}
        
        # Configuration files
        self.integrations_file = self.data_dir / "integrations.json"
        self.cache_file = self.data_dir / "cache.json"
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load integration data from files"""
        try:
            # Load integrations
            if self.integrations_file.exists():
                with open(self.integrations_file, 'r') as f:
                    data = json.load(f)
                    for integration_id, integration_data in data.items():
                        integration_data['integration_type'] = IntegrationType(integration_data['integration_type'])
                        integration_data['model_config']['provider'] = ModelProvider(integration_data['model_config']['provider'])
                        self.integrations[integration_id] = IntegrationConfig(**integration_data)
            
            # Load cache
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    self.tool_cache = cache_data.get("tools", {})
                    self.resource_cache = cache_data.get("resources", {})
                    self.prompt_cache = cache_data.get("prompts", {})
            
            logger.info(f"Loaded {len(self.integrations)} integrations")
            
        except Exception as e:
            logger.error(f"Error loading integration data: {e}")
    
    def _save_data(self):
        """Save integration data to files"""
        try:
            # Save integrations
            integrations_data = {}
            for integration_id, integration in self.integrations.items():
                integration_dict = asdict(integration)
                integration_dict['integration_type'] = integration.integration_type.value
                integration_dict['model_config']['provider'] = integration.model_config.provider.value
                integrations_data[integration_id] = integration_dict
            
            with open(self.integrations_file, 'w') as f:
                json.dump(integrations_data, f, indent=2)
            
            # Save cache
            cache_data = {
                "tools": self.tool_cache,
                "resources": self.resource_cache,
                "prompts": self.prompt_cache
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info("Integration data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving integration data: {e}")
    
    def create_integration(
        self,
        integration_id: str,
        name: str,
        description: str,
        integration_type: IntegrationType,
        model_config: ModelConfig,
        metadata: Dict[str, Any] = None
    ) -> IntegrationConfig:
        """Create a new integration"""
        if integration_id in self.integrations:
            raise ValueError(f"Integration {integration_id} already exists")
        
        integration = IntegrationConfig(
            integration_id=integration_id,
            name=name,
            description=description,
            integration_type=integration_type,
            model_config=model_config,
            metadata=metadata or {}
        )
        
        self.integrations[integration_id] = integration
        self._save_data()
        
        logger.info(f"Created integration: {integration_id}")
        return integration
    
    async def connect_to_mcp_server(self, integration_id: str, server_url: str) -> bool:
        """Connect to MCP server"""
        if integration_id not in self.integrations:
            raise ValueError(f"Integration {integration_id} not found")
        
        try:
            client = MCPClient(server_url)
            await client.connect()
            
            self.mcp_clients[integration_id] = client
            
            # Discover and cache tools, resources, and prompts
            await self._discover_mcp_capabilities(integration_id)
            
            logger.info(f"Connected to MCP server for integration {integration_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server for integration {integration_id}: {e}")
            return False
    
    async def _discover_mcp_capabilities(self, integration_id: str):
        """Discover MCP server capabilities"""
        if integration_id not in self.mcp_clients:
            return
        
        client = self.mcp_clients[integration_id]
        
        try:
            # Discover tools
            tools = await client.list_tools()
            for tool in tools:
                tool_key = f"{integration_id}:{tool['name']}"
                self.tool_cache[tool_key] = tool
            
            # Discover resources
            resources = await client.list_resources()
            for resource in resources:
                resource_key = f"{integration_id}:{resource['uri']}"
                self.resource_cache[resource_key] = resource
            
            # Discover prompts
            prompts = await client.list_prompts()
            for prompt in prompts:
                prompt_key = f"{integration_id}:{prompt['name']}"
                self.prompt_cache[prompt_key] = prompt
            
            logger.info(f"Discovered capabilities for integration {integration_id}")
            
        except Exception as e:
            logger.error(f"Error discovering capabilities for integration {integration_id}: {e}")
    
    async def execute_tool(
        self,
        integration_id: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a tool via MCP"""
        start_time = time.time()
        
        try:
            if integration_id not in self.mcp_clients:
                return ExecutionResult(
                    success=False,
                    result=None,
                    error=f"No MCP client for integration {integration_id}",
                    execution_time=time.time() - start_time
                )
            
            client = self.mcp_clients[integration_id]
            result = await client.call_tool(tool_name, arguments)
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"integration_id": integration_id, "tool_name": tool_name}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time,
                metadata={"integration_id": integration_id, "tool_name": tool_name}
            )
    
    async def read_resource(
        self,
        integration_id: str,
        resource_uri: str
    ) -> ExecutionResult:
        """Read a resource via MCP"""
        start_time = time.time()
        
        try:
            if integration_id not in self.mcp_clients:
                return ExecutionResult(
                    success=False,
                    result=None,
                    error=f"No MCP client for integration {integration_id}",
                    execution_time=time.time() - start_time
                )
            
            client = self.mcp_clients[integration_id]
            result = await client.read_resource(resource_uri)
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"integration_id": integration_id, "resource_uri": resource_uri}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time,
                metadata={"integration_id": integration_id, "resource_uri": resource_uri}
            )
    
    async def get_prompt(
        self,
        integration_id: str,
        prompt_name: str,
        arguments: Dict[str, Any] = None
    ) -> ExecutionResult:
        """Get a prompt via MCP"""
        start_time = time.time()
        
        try:
            if integration_id not in self.mcp_clients:
                return ExecutionResult(
                    success=False,
                    result=None,
                    error=f"No MCP client for integration {integration_id}",
                    execution_time=time.time() - start_time
                )
            
            client = self.mcp_clients[integration_id]
            result = await client.get_prompt(prompt_name, arguments or {})
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"integration_id": integration_id, "prompt_name": prompt_name}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time,
                metadata={"integration_id": integration_id, "prompt_name": prompt_name}
            )
    
    async def get_completion(
        self,
        integration_id: str,
        prompt: str,
        max_tokens: int = 1000
    ) -> ExecutionResult:
        """Get completion via MCP"""
        start_time = time.time()
        
        try:
            if integration_id not in self.mcp_clients:
                return ExecutionResult(
                    success=False,
                    result=None,
                    error=f"No MCP client for integration {integration_id}",
                    execution_time=time.time() - start_time
                )
            
            client = self.mcp_clients[integration_id]
            completion = await client.complete(prompt, max_tokens)
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                result=completion,
                execution_time=execution_time,
                metadata={"integration_id": integration_id, "max_tokens": max_tokens}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time,
                metadata={"integration_id": integration_id, "max_tokens": max_tokens}
            )
    
    async def stream_completion(
        self,
        integration_id: str,
        prompt: str,
        max_tokens: int = 1000
    ) -> AsyncGenerator[str, None]:
        """Stream completion via MCP"""
        try:
            if integration_id not in self.mcp_clients:
                yield f"Error: No MCP client for integration {integration_id}"
                return
            
            client = self.mcp_clients[integration_id]
            
            # For streaming, we would implement a streaming version of the completion
            # For now, we'll simulate streaming by yielding chunks
            completion = await client.complete(prompt, max_tokens)
            
            # Simulate streaming by yielding chunks
            text = completion.completion
            chunk_size = 10
            
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                yield chunk
                await asyncio.sleep(0.1)  # Simulate streaming delay
            
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def create_mcp_server(
        self,
        server_id: str,
        server_info: Dict[str, Any] = None
    ) -> MCPServer:
        """Create an MCP server"""
        server = MCPServer(server_info)
        self.mcp_servers[server_id] = server
        
        logger.info(f"Created MCP server: {server_id}")
        return server
    
    def register_tool_on_server(
        self,
        server_id: str,
        tool: MCPTool
    ) -> bool:
        """Register a tool on an MCP server"""
        if server_id not in self.mcp_servers:
            return False
        
        server = self.mcp_servers[server_id]
        server.register_tool(tool)
        
        return True
    
    def register_resource_on_server(
        self,
        server_id: str,
        resource: MCPResource
    ) -> bool:
        """Register a resource on an MCP server"""
        if server_id not in self.mcp_servers:
            return False
        
        server = self.mcp_servers[server_id]
        server.register_resource(resource)
        
        return True
    
    def register_prompt_on_server(
        self,
        server_id: str,
        prompt: MCPPrompt
    ) -> bool:
        """Register a prompt on an MCP server"""
        if server_id not in self.mcp_servers:
            return False
        
        server = self.mcp_servers[server_id]
        server.register_prompt(prompt)
        
        return True
    
    def list_integrations(self) -> List[IntegrationConfig]:
        """List all integrations"""
        return list(self.integrations.values())
    
    def get_integration(self, integration_id: str) -> Optional[IntegrationConfig]:
        """Get integration by ID"""
        return self.integrations.get(integration_id)
    
    def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all available tools across integrations"""
        tools = []
        for tool_key, tool_data in self.tool_cache.items():
            integration_id, tool_name = tool_key.split(":", 1)
            tools.append({
                "integration_id": integration_id,
                "name": tool_name,
                "data": tool_data
            })
        return tools
    
    def list_available_resources(self) -> List[Dict[str, Any]]:
        """List all available resources across integrations"""
        resources = []
        for resource_key, resource_data in self.resource_cache.items():
            integration_id, resource_uri = resource_key.split(":", 1)
            resources.append({
                "integration_id": integration_id,
                "uri": resource_uri,
                "data": resource_data
            })
        return resources
    
    def list_available_prompts(self) -> List[Dict[str, Any]]:
        """List all available prompts across integrations"""
        prompts = []
        for prompt_key, prompt_data in self.prompt_cache.items():
            integration_id, prompt_name = prompt_key.split(":", 1)
            prompts.append({
                "integration_id": integration_id,
                "name": prompt_name,
                "data": prompt_data
            })
        return prompts
    
    async def disconnect_integration(self, integration_id: str) -> bool:
        """Disconnect an integration"""
        if integration_id in self.mcp_clients:
            try:
                await self.mcp_clients[integration_id].disconnect()
                del self.mcp_clients[integration_id]
                logger.info(f"Disconnected integration: {integration_id}")
                return True
            except Exception as e:
                logger.error(f"Error disconnecting integration {integration_id}: {e}")
                return False
        
        return False
    
    async def disconnect_all(self):
        """Disconnect all integrations"""
        for integration_id in list(self.mcp_clients.keys()):
            await self.disconnect_integration(integration_id)
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """Get integration summary"""
        return {
            "total_integrations": len(self.integrations),
            "active_connections": len(self.mcp_clients),
            "total_servers": len(self.mcp_servers),
            "available_tools": len(self.tool_cache),
            "available_resources": len(self.resource_cache),
            "available_prompts": len(self.prompt_cache),
            "integrations_by_type": {
                integration_type.value: len([
                    i for i in self.integrations.values()
                    if i.integration_type == integration_type
                ])
                for integration_type in IntegrationType
            }
        }

class MCPToolExecutor:
    """MCP tool execution framework"""
    
    def __init__(self, integration_manager: MCPIntegrationManager):
        self.integration_manager = integration_manager
        self.execution_history: List[ExecutionResult] = []
    
    async def execute_tool_chain(
        self,
        tool_chain: List[Dict[str, Any]]
    ) -> List[ExecutionResult]:
        """Execute a chain of tools"""
        results = []
        
        for tool_call in tool_chain:
            integration_id = tool_call.get("integration_id")
            tool_name = tool_call.get("tool_name")
            arguments = tool_call.get("arguments", {})
            
            if not integration_id or not tool_name:
                results.append(ExecutionResult(
                    success=False,
                    result=None,
                    error="Missing integration_id or tool_name"
                ))
                continue
            
            result = await self.integration_manager.execute_tool(
                integration_id, tool_name, arguments
            )
            
            results.append(result)
            self.execution_history.append(result)
            
            # If a tool fails, we might want to stop the chain
            if not result.success:
                logger.warning(f"Tool execution failed: {result.error}")
                break
        
        return results
    
    async def execute_parallel_tools(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[ExecutionResult]:
        """Execute multiple tools in parallel"""
        tasks = []
        
        for tool_call in tool_calls:
            integration_id = tool_call.get("integration_id")
            tool_name = tool_call.get("tool_name")
            arguments = tool_call.get("arguments", {})
            
            if integration_id and tool_name:
                task = self.integration_manager.execute_tool(
                    integration_id, tool_name, arguments
                )
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to ExecutionResult
        execution_results = []
        for result in results:
            if isinstance(result, Exception):
                execution_results.append(ExecutionResult(
                    success=False,
                    result=None,
                    error=str(result)
                ))
            else:
                execution_results.append(result)
                self.execution_history.append(result)
        
        return execution_results
    
    def get_execution_history(self) -> List[ExecutionResult]:
        """Get execution history"""
        return self.execution_history.copy()
    
    def clear_execution_history(self):
        """Clear execution history"""
        self.execution_history.clear()

class MCPResourceManager:
    """MCP resource management and caching"""
    
    def __init__(self, integration_manager: MCPIntegrationManager):
        self.integration_manager = integration_manager
        self.cache_ttl = 300  # 5 minutes
        self.resource_cache: Dict[str, Dict[str, Any]] = {}
    
    async def get_resource(
        self,
        integration_id: str,
        resource_uri: str,
        use_cache: bool = True
    ) -> ExecutionResult:
        """Get resource with optional caching"""
        cache_key = f"{integration_id}:{resource_uri}"
        
        # Check cache first
        if use_cache and cache_key in self.resource_cache:
            cached_data = self.resource_cache[cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return ExecutionResult(
                    success=True,
                    result=cached_data["data"],
                    execution_time=0.0,
                    metadata={"cached": True}
                )
        
        # Fetch from MCP server
        result = await self.integration_manager.read_resource(integration_id, resource_uri)
        
        # Cache successful results
        if result.success and use_cache:
            self.resource_cache[cache_key] = {
                "data": result.result,
                "timestamp": time.time()
            }
        
        return result
    
    async def subscribe_to_resource(
        self,
        integration_id: str,
        resource_uri: str
    ) -> bool:
        """Subscribe to resource changes"""
        try:
            if integration_id not in self.integration_manager.mcp_clients:
                return False
            
            client = self.integration_manager.mcp_clients[integration_id]
            return await client.subscribe_to_resource(resource_uri)
            
        except Exception as e:
            logger.error(f"Error subscribing to resource {resource_uri}: {e}")
            return False
    
    def clear_cache(self):
        """Clear resource cache"""
        self.resource_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cached_resources": len(self.resource_cache),
            "cache_ttl": self.cache_ttl
        }

async def main():
    """Main function to demonstrate MCP integration"""
    data_dir = Path("./mcp_data")
    manager = MCPIntegrationManager(data_dir)
    
    # Create an integration
    model_config = ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-4",
        api_key="your-api-key"
    )
    
    integration = manager.create_integration(
        "openai-integration",
        "OpenAI Integration",
        "Integration with OpenAI models via MCP",
        IntegrationType.TOOL,
        model_config
    )
    
    print(f"Created integration: {integration.integration_id}")
    
    # Create an MCP server
    server = manager.create_mcp_server("example-server")
    
    # Register a tool on the server
    def example_tool(arguments):
        return f"Tool executed with arguments: {arguments}"
    
    from mcp_protocol import MCPTool
    tool = MCPTool(
        name="example_tool",
        description="An example tool",
        input_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string"}
            }
        },
        handler=example_tool
    )
    
    manager.register_tool_on_server("example-server", tool)
    
    print("MCP integration setup completed")
    
    # Get summary
    summary = manager.get_integration_summary()
    print(f"Integration summary: {summary}")

if __name__ == "__main__":
    asyncio.run(main())