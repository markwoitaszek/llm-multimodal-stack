#!/usr/bin/env python3
"""
Comprehensive Test Suite for MCP Support
Part of Issue #6: MCP Support

This test suite covers:
- MCP protocol implementation
- Tool discovery and execution
- Resource management and caching
- Prompt engineering and management
- Completion handling and streaming
- Integration with AI models
- Client/server architecture
- Performance testing
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import requests
import time

# Import the modules under test
import sys
sys.path.append('/workspace/mcp')

from mcp_protocol import (
    MCPClient, MCPServer, MCPTool, MCPResource, MCPPrompt, MCPCompletion,
    MCPError, MCPErrorCode, MCPMethod, MCPMessage
)
from mcp_integration import (
    MCPIntegrationManager, MCPToolExecutor, MCPResourceManager,
    IntegrationConfig, ModelConfig, ModelProvider, IntegrationType,
    ExecutionResult
)

class TestMCPProtocol:
    """Test suite for MCP protocol implementation"""
    
    @pytest.fixture
    def mcp_server(self):
        """Create MCP server instance"""
        return MCPServer()
    
    def test_mcp_server_creation(self, mcp_server):
        """Test MCP server creation"""
        assert mcp_server is not None
        assert len(mcp_server.tools) == 0
        assert len(mcp_server.resources) == 0
        assert len(mcp_server.prompts) == 0
    
    def test_tool_registration(self, mcp_server):
        """Test tool registration"""
        def echo_tool(arguments):
            return f"Echo: {arguments.get('message', 'Hello')}"
        
        tool = MCPTool(
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
        )
        
        mcp_server.register_tool(tool)
        
        assert "echo" in mcp_server.tools
        assert mcp_server.tools["echo"].name == "echo"
        assert mcp_server.tools["echo"].handler == echo_tool
    
    def test_resource_registration(self, mcp_server):
        """Test resource registration"""
        def file_resource():
            return "This is file content"
        
        resource = MCPResource(
            uri="file://example.txt",
            name="Example File",
            description="An example file resource",
            mime_type="text/plain",
            handler=file_resource
        )
        
        mcp_server.register_resource(resource)
        
        assert "file://example.txt" in mcp_server.resources
        assert mcp_server.resources["file://example.txt"].name == "Example File"
        assert mcp_server.resources["file://example.txt"].handler == file_resource
    
    def test_prompt_registration(self, mcp_server):
        """Test prompt registration"""
        def code_prompt(arguments):
            return f"Write code for: {arguments.get('task', 'Hello World')}"
        
        prompt = MCPPrompt(
            name="code_generator",
            description="Generate code for a given task",
            arguments=[
                {"name": "task", "description": "The task to generate code for", "required": True}
            ],
            handler=code_prompt
        )
        
        mcp_server.register_prompt(prompt)
        
        assert "code_generator" in mcp_server.prompts
        assert mcp_server.prompts["code_generator"].name == "code_generator"
        assert mcp_server.prompts["code_generator"].handler == code_prompt
    
    @pytest.mark.asyncio
    async def test_initialize_handling(self, mcp_server):
        """Test initialize message handling"""
        message = MCPMessage(
            id=1,
            method=MCPMethod.INITIALIZE.value,
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "clientInfo": {
                    "name": "Test Client",
                    "version": "1.0.0"
                }
            }
        )
        
        response = await mcp_server.handle_message(message, "test-client")
        
        assert response.id == 1
        assert response.result is not None
        assert "protocolVersion" in response.result
        assert "capabilities" in response.result
        assert "serverInfo" in response.result
    
    @pytest.mark.asyncio
    async def test_ping_handling(self, mcp_server):
        """Test ping message handling"""
        message = MCPMessage(
            id=1,
            method=MCPMethod.PING.value
        )
        
        response = await mcp_server.handle_message(message, "test-client")
        
        assert response.id == 1
        assert response.result is not None
        assert response.result.get("pong") == "pong"
    
    @pytest.mark.asyncio
    async def test_tools_list_handling(self, mcp_server):
        """Test tools list message handling"""
        # Register a tool first
        def echo_tool(arguments):
            return f"Echo: {arguments.get('message', 'Hello')}"
        
        tool = MCPTool(
            name="echo",
            description="Echo a message",
            input_schema={"type": "object"},
            handler=echo_tool
        )
        
        mcp_server.register_tool(tool)
        
        message = MCPMessage(
            id=1,
            method=MCPMethod.TOOLS_LIST.value
        )
        
        response = await mcp_server.handle_message(message, "test-client")
        
        assert response.id == 1
        assert response.result is not None
        assert "tools" in response.result
        assert len(response.result["tools"]) == 1
        assert response.result["tools"][0]["name"] == "echo"
    
    @pytest.mark.asyncio
    async def test_tool_call_handling(self, mcp_server):
        """Test tool call message handling"""
        # Register a tool first
        def echo_tool(arguments):
            return f"Echo: {arguments.get('message', 'Hello')}"
        
        tool = MCPTool(
            name="echo",
            description="Echo a message",
            input_schema={"type": "object"},
            handler=echo_tool
        )
        
        mcp_server.register_tool(tool)
        
        message = MCPMessage(
            id=1,
            method=MCPMethod.TOOLS_CALL.value,
            params={
                "name": "echo",
                "arguments": {"message": "Hello World"}
            }
        )
        
        response = await mcp_server.handle_message(message, "test-client")
        
        assert response.id == 1
        assert response.result is not None
        assert "content" in response.result
        assert len(response.result["content"]) == 1
        assert "Echo: Hello World" in response.result["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_resources_list_handling(self, mcp_server):
        """Test resources list message handling"""
        # Register a resource first
        def file_resource():
            return "This is file content"
        
        resource = MCPResource(
            uri="file://example.txt",
            name="Example File",
            description="An example file resource",
            mime_type="text/plain",
            handler=file_resource
        )
        
        mcp_server.register_resource(resource)
        
        message = MCPMessage(
            id=1,
            method=MCPMethod.RESOURCES_LIST.value
        )
        
        response = await mcp_server.handle_message(message, "test-client")
        
        assert response.id == 1
        assert response.result is not None
        assert "resources" in response.result
        assert len(response.result["resources"]) == 1
        assert response.result["resources"][0]["uri"] == "file://example.txt"
    
    @pytest.mark.asyncio
    async def test_resource_read_handling(self, mcp_server):
        """Test resource read message handling"""
        # Register a resource first
        def file_resource():
            return "This is file content"
        
        resource = MCPResource(
            uri="file://example.txt",
            name="Example File",
            description="An example file resource",
            mime_type="text/plain",
            handler=file_resource
        )
        
        mcp_server.register_resource(resource)
        
        message = MCPMessage(
            id=1,
            method=MCPMethod.RESOURCES_READ.value,
            params={"uri": "file://example.txt"}
        )
        
        response = await mcp_server.handle_message(message, "test-client")
        
        assert response.id == 1
        assert response.result is not None
        assert "contents" in response.result
        assert len(response.result["contents"]) == 1
        assert response.result["contents"][0]["text"] == "This is file content"
    
    @pytest.mark.asyncio
    async def test_prompts_list_handling(self, mcp_server):
        """Test prompts list message handling"""
        # Register a prompt first
        def code_prompt(arguments):
            return f"Write code for: {arguments.get('task', 'Hello World')}"
        
        prompt = MCPPrompt(
            name="code_generator",
            description="Generate code for a given task",
            arguments=[
                {"name": "task", "description": "The task to generate code for", "required": True}
            ],
            handler=code_prompt
        )
        
        mcp_server.register_prompt(prompt)
        
        message = MCPMessage(
            id=1,
            method=MCPMethod.PROMPTS_LIST.value
        )
        
        response = await mcp_server.handle_message(message, "test-client")
        
        assert response.id == 1
        assert response.result is not None
        assert "prompts" in response.result
        assert len(response.result["prompts"]) == 1
        assert response.result["prompts"][0]["name"] == "code_generator"
    
    @pytest.mark.asyncio
    async def test_prompt_get_handling(self, mcp_server):
        """Test prompt get message handling"""
        # Register a prompt first
        def code_prompt(arguments):
            return f"Write code for: {arguments.get('task', 'Hello World')}"
        
        prompt = MCPPrompt(
            name="code_generator",
            description="Generate code for a given task",
            arguments=[
                {"name": "task", "description": "The task to generate code for", "required": True}
            ],
            handler=code_prompt
        )
        
        mcp_server.register_prompt(prompt)
        
        message = MCPMessage(
            id=1,
            method=MCPMethod.PROMPTS_GET.value,
            params={
                "name": "code_generator",
                "arguments": {"task": "Hello World"}
            }
        )
        
        response = await mcp_server.handle_message(message, "test-client")
        
        assert response.id == 1
        assert response.result is not None
        assert "messages" in response.result
        assert len(response.result["messages"]) == 1
        assert "Write code for: Hello World" in response.result["messages"][0]["content"]["text"]
    
    @pytest.mark.asyncio
    async def test_completion_handling(self, mcp_server):
        """Test completion message handling"""
        message = MCPMessage(
            id=1,
            method=MCPMethod.COMPLETIONS_COMPLETE.value,
            params={
                "prompt": "Hello, how are you?",
                "maxTokens": 100
            }
        )
        
        response = await mcp_server.handle_message(message, "test-client")
        
        assert response.id == 1
        assert response.result is not None
        assert "completion" in response.result
        assert "isPartial" in response.result
        assert "finishReason" in response.result
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mcp_server):
        """Test error handling"""
        message = MCPMessage(
            id=1,
            method="unknown_method"
        )
        
        response = await mcp_server.handle_message(message, "test-client")
        
        assert response.id == 1
        assert response.error is not None
        assert response.error["code"] == MCPErrorCode.METHOD_NOT_FOUND.value

class TestMCPIntegration:
    """Test suite for MCP integration"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def integration_manager(self, temp_dir):
        """Create integration manager instance"""
        return MCPIntegrationManager(temp_dir)
    
    def test_integration_creation(self, integration_manager):
        """Test integration creation"""
        model_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4",
            api_key="test-key"
        )
        
        integration = integration_manager.create_integration(
            "test-integration",
            "Test Integration",
            "A test integration",
            IntegrationType.TOOL,
            model_config
        )
        
        assert integration.integration_id == "test-integration"
        assert integration.name == "Test Integration"
        assert integration.model_config.provider == ModelProvider.OPENAI
        assert integration.model_config.model_name == "gpt-4"
    
    def test_mcp_server_creation(self, integration_manager):
        """Test MCP server creation"""
        server = integration_manager.create_mcp_server("test-server")
        
        assert server is not None
        assert "test-server" in integration_manager.mcp_servers
    
    def test_tool_registration_on_server(self, integration_manager):
        """Test tool registration on server"""
        server = integration_manager.create_mcp_server("test-server")
        
        def echo_tool(arguments):
            return f"Echo: {arguments.get('message', 'Hello')}"
        
        tool = MCPTool(
            name="echo",
            description="Echo a message",
            input_schema={"type": "object"},
            handler=echo_tool
        )
        
        success = integration_manager.register_tool_on_server("test-server", tool)
        
        assert success == True
        assert "echo" in server.tools
    
    def test_resource_registration_on_server(self, integration_manager):
        """Test resource registration on server"""
        server = integration_manager.create_mcp_server("test-server")
        
        def file_resource():
            return "This is file content"
        
        resource = MCPResource(
            uri="file://example.txt",
            name="Example File",
            description="An example file resource",
            mime_type="text/plain",
            handler=file_resource
        )
        
        success = integration_manager.register_resource_on_server("test-server", resource)
        
        assert success == True
        assert "file://example.txt" in server.resources
    
    def test_prompt_registration_on_server(self, integration_manager):
        """Test prompt registration on server"""
        server = integration_manager.create_mcp_server("test-server")
        
        def code_prompt(arguments):
            return f"Write code for: {arguments.get('task', 'Hello World')}"
        
        prompt = MCPPrompt(
            name="code_generator",
            description="Generate code for a given task",
            arguments=[
                {"name": "task", "description": "The task to generate code for", "required": True}
            ],
            handler=code_prompt
        )
        
        success = integration_manager.register_prompt_on_server("test-server", prompt)
        
        assert success == True
        assert "code_generator" in server.prompts
    
    def test_integration_listing(self, integration_manager):
        """Test integration listing"""
        # Create some integrations
        model_config1 = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4"
        )
        
        model_config2 = ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3"
        )
        
        integration_manager.create_integration(
            "integration1", "Integration 1", "First integration",
            IntegrationType.TOOL, model_config1
        )
        
        integration_manager.create_integration(
            "integration2", "Integration 2", "Second integration",
            IntegrationType.RESOURCE, model_config2
        )
        
        integrations = integration_manager.list_integrations()
        
        assert len(integrations) == 2
        assert any(i.integration_id == "integration1" for i in integrations)
        assert any(i.integration_id == "integration2" for i in integrations)
    
    def test_integration_summary(self, integration_manager):
        """Test integration summary"""
        # Create some integrations
        model_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4"
        )
        
        integration_manager.create_integration(
            "test-integration", "Test Integration", "A test integration",
            IntegrationType.TOOL, model_config
        )
        
        summary = integration_manager.get_integration_summary()
        
        assert summary["total_integrations"] == 1
        assert summary["active_connections"] == 0
        assert summary["total_servers"] == 0
        assert summary["available_tools"] == 0
        assert summary["available_resources"] == 0
        assert summary["available_prompts"] == 0

class TestMCPToolExecutor:
    """Test suite for MCP tool executor"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def tool_executor(self, temp_dir):
        """Create tool executor instance"""
        integration_manager = MCPIntegrationManager(temp_dir)
        return MCPToolExecutor(integration_manager)
    
    @pytest.mark.asyncio
    async def test_tool_chain_execution(self, tool_executor):
        """Test tool chain execution"""
        # Create a mock integration
        model_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4"
        )
        
        integration = tool_executor.integration_manager.create_integration(
            "test-integration",
            "Test Integration",
            "A test integration",
            IntegrationType.TOOL,
            model_config
        )
        
        # Create a mock MCP server
        server = tool_executor.integration_manager.create_mcp_server("test-server")
        
        def echo_tool(arguments):
            return f"Echo: {arguments.get('message', 'Hello')}"
        
        tool = MCPTool(
            name="echo",
            description="Echo a message",
            input_schema={"type": "object"},
            handler=echo_tool
        )
        
        tool_executor.integration_manager.register_tool_on_server("test-server", tool)
        
        # Mock the MCP client connection
        class MockMCPClient:
            async def call_tool(self, name, arguments):
                if name == "echo":
                    return {"content": [{"type": "text", "text": f"Echo: {arguments.get('message', 'Hello')}"}]}
                return {"content": [{"type": "text", "text": "Unknown tool"}]}
        
        tool_executor.integration_manager.mcp_clients["test-integration"] = MockMCPClient()
        
        # Execute tool chain
        tool_chain = [
            {
                "integration_id": "test-integration",
                "tool_name": "echo",
                "arguments": {"message": "Hello World"}
            },
            {
                "integration_id": "test-integration",
                "tool_name": "echo",
                "arguments": {"message": "Goodbye World"}
            }
        ]
        
        results = await tool_executor.execute_tool_chain(tool_chain)
        
        assert len(results) == 2
        assert results[0].success == True
        assert results[1].success == True
        assert "Hello World" in str(results[0].result)
        assert "Goodbye World" in str(results[1].result)
    
    @pytest.mark.asyncio
    async def test_parallel_tool_execution(self, tool_executor):
        """Test parallel tool execution"""
        # Create a mock integration
        model_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4"
        )
        
        integration = tool_executor.integration_manager.create_integration(
            "test-integration",
            "Test Integration",
            "A test integration",
            IntegrationType.TOOL,
            model_config
        )
        
        # Mock the MCP client connection
        class MockMCPClient:
            async def call_tool(self, name, arguments):
                if name == "echo":
                    return {"content": [{"type": "text", "text": f"Echo: {arguments.get('message', 'Hello')}"}]}
                return {"content": [{"type": "text", "text": "Unknown tool"}]}
        
        tool_executor.integration_manager.mcp_clients["test-integration"] = MockMCPClient()
        
        # Execute parallel tools
        tool_calls = [
            {
                "integration_id": "test-integration",
                "tool_name": "echo",
                "arguments": {"message": "Hello World"}
            },
            {
                "integration_id": "test-integration",
                "tool_name": "echo",
                "arguments": {"message": "Goodbye World"}
            }
        ]
        
        results = await tool_executor.execute_parallel_tools(tool_calls)
        
        assert len(results) == 2
        assert results[0].success == True
        assert results[1].success == True
        assert "Hello World" in str(results[0].result)
        assert "Goodbye World" in str(results[1].result)
    
    def test_execution_history(self, tool_executor):
        """Test execution history"""
        # Add some mock results to history
        result1 = ExecutionResult(
            success=True,
            result="Result 1",
            execution_time=0.1
        )
        
        result2 = ExecutionResult(
            success=False,
            result=None,
            error="Error occurred",
            execution_time=0.2
        )
        
        tool_executor.execution_history.append(result1)
        tool_executor.execution_history.append(result2)
        
        history = tool_executor.get_execution_history()
        
        assert len(history) == 2
        assert history[0].success == True
        assert history[1].success == False
        assert history[1].error == "Error occurred"
    
    def test_clear_execution_history(self, tool_executor):
        """Test clearing execution history"""
        # Add some mock results to history
        result = ExecutionResult(
            success=True,
            result="Result",
            execution_time=0.1
        )
        
        tool_executor.execution_history.append(result)
        
        assert len(tool_executor.execution_history) == 1
        
        tool_executor.clear_execution_history()
        
        assert len(tool_executor.execution_history) == 0

class TestMCPResourceManager:
    """Test suite for MCP resource manager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def resource_manager(self, temp_dir):
        """Create resource manager instance"""
        integration_manager = MCPIntegrationManager(temp_dir)
        return MCPResourceManager(integration_manager)
    
    @pytest.mark.asyncio
    async def test_resource_caching(self, resource_manager):
        """Test resource caching"""
        # Mock the MCP client
        class MockMCPClient:
            async def read_resource(self, uri):
                return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": "Resource content"}]}
        
        resource_manager.integration_manager.mcp_clients["test-integration"] = MockMCPClient()
        
        # First read - should fetch from server
        result1 = await resource_manager.get_resource("test-integration", "file://test.txt")
        
        assert result1.success == True
        assert result1.metadata.get("cached") != True
        
        # Second read - should use cache
        result2 = await resource_manager.get_resource("test-integration", "file://test.txt")
        
        assert result2.success == True
        assert result2.metadata.get("cached") == True
        assert result2.execution_time == 0.0
    
    @pytest.mark.asyncio
    async def test_resource_subscription(self, resource_manager):
        """Test resource subscription"""
        # Mock the MCP client
        class MockMCPClient:
            async def subscribe_to_resource(self, uri):
                return True
        
        resource_manager.integration_manager.mcp_clients["test-integration"] = MockMCPClient()
        
        success = await resource_manager.subscribe_to_resource("test-integration", "file://test.txt")
        
        assert success == True
    
    def test_cache_management(self, resource_manager):
        """Test cache management"""
        # Add some cached resources
        resource_manager.resource_cache["test:file1"] = {
            "data": "Content 1",
            "timestamp": time.time()
        }
        
        resource_manager.resource_cache["test:file2"] = {
            "data": "Content 2",
            "timestamp": time.time()
        }
        
        assert len(resource_manager.resource_cache) == 2
        
        # Clear cache
        resource_manager.clear_cache()
        
        assert len(resource_manager.resource_cache) == 0
    
    def test_cache_stats(self, resource_manager):
        """Test cache statistics"""
        # Add some cached resources
        resource_manager.resource_cache["test:file1"] = {
            "data": "Content 1",
            "timestamp": time.time()
        }
        
        stats = resource_manager.get_cache_stats()
        
        assert stats["cached_resources"] == 1
        assert stats["cache_ttl"] == 300

class TestIntegration:
    """Integration tests for MCP system"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_complete_mcp_workflow(self, temp_dir):
        """Test complete MCP workflow"""
        # Create integration manager
        manager = MCPIntegrationManager(temp_dir)
        
        # Create integration
        model_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4"
        )
        
        integration = manager.create_integration(
            "test-integration",
            "Test Integration",
            "A test integration",
            IntegrationType.TOOL,
            model_config
        )
        
        # Create MCP server
        server = manager.create_mcp_server("test-server")
        
        # Register tools, resources, and prompts
        def echo_tool(arguments):
            return f"Echo: {arguments.get('message', 'Hello')}"
        
        tool = MCPTool(
            name="echo",
            description="Echo a message",
            input_schema={"type": "object"},
            handler=echo_tool
        )
        
        manager.register_tool_on_server("test-server", tool)
        
        def file_resource():
            return "This is file content"
        
        resource = MCPResource(
            uri="file://example.txt",
            name="Example File",
            description="An example file resource",
            mime_type="text/plain",
            handler=file_resource
        )
        
        manager.register_resource_on_server("test-server", resource)
        
        def code_prompt(arguments):
            return f"Write code for: {arguments.get('task', 'Hello World')}"
        
        prompt = MCPPrompt(
            name="code_generator",
            description="Generate code for a given task",
            arguments=[
                {"name": "task", "description": "The task to generate code for", "required": True}
            ],
            handler=code_prompt
        )
        
        manager.register_prompt_on_server("test-server", prompt)
        
        # Verify everything is registered
        assert len(server.tools) == 1
        assert len(server.resources) == 1
        assert len(server.prompts) == 1
        
        # Test message handling
        message = MCPMessage(
            id=1,
            method=MCPMethod.TOOLS_LIST.value
        )
        
        response = await server.handle_message(message, "test-client")
        
        assert response.id == 1
        assert response.result is not None
        assert len(response.result["tools"]) == 1
        assert response.result["tools"][0]["name"] == "echo"
    
    def test_integration_persistence(self, temp_dir):
        """Test integration persistence"""
        # Create integration manager
        manager1 = MCPIntegrationManager(temp_dir)
        
        # Create integration
        model_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4"
        )
        
        integration = manager1.create_integration(
            "test-integration",
            "Test Integration",
            "A test integration",
            IntegrationType.TOOL,
            model_config
        )
        
        # Create new manager instance (simulates restart)
        manager2 = MCPIntegrationManager(temp_dir)
        
        # Verify integration was persisted
        retrieved_integration = manager2.get_integration("test-integration")
        
        assert retrieved_integration is not None
        assert retrieved_integration.integration_id == "test-integration"
        assert retrieved_integration.name == "Test Integration"
        assert retrieved_integration.model_config.provider == ModelProvider.OPENAI

class TestPerformance:
    """Performance tests"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_integration_creation_performance(self, temp_dir):
        """Test integration creation performance"""
        manager = MCPIntegrationManager(temp_dir)
        
        # Create 100 integrations
        start_time = time.time()
        
        for i in range(100):
            model_config = ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4"
            )
            
            manager.create_integration(
                f"integration-{i}",
                f"Integration {i}",
                f"Integration {i} description",
                IntegrationType.TOOL,
                model_config
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 2.0  # Less than 2 seconds
        
        # Verify integrations were created
        assert len(manager.integrations) == 100
    
    def test_tool_registration_performance(self, temp_dir):
        """Test tool registration performance"""
        manager = MCPIntegrationManager(temp_dir)
        server = manager.create_mcp_server("test-server")
        
        # Register 100 tools
        start_time = time.time()
        
        for i in range(100):
            def tool_handler(arguments):
                return f"Tool {i} result"
            
            tool = MCPTool(
                name=f"tool-{i}",
                description=f"Tool {i} description",
                input_schema={"type": "object"},
                handler=tool_handler
            )
            
            manager.register_tool_on_server("test-server", tool)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 1.0  # Less than 1 second
        
        # Verify tools were registered
        assert len(server.tools) == 100
    
    @pytest.mark.asyncio
    async def test_message_handling_performance(self, temp_dir):
        """Test message handling performance"""
        manager = MCPIntegrationManager(temp_dir)
        server = manager.create_mcp_server("test-server")
        
        # Register a tool
        def echo_tool(arguments):
            return f"Echo: {arguments.get('message', 'Hello')}"
        
        tool = MCPTool(
            name="echo",
            description="Echo a message",
            input_schema={"type": "object"},
            handler=echo_tool
        )
        
        manager.register_tool_on_server("test-server", tool)
        
        # Handle 100 messages
        start_time = time.time()
        
        for i in range(100):
            message = MCPMessage(
                id=i,
                method=MCPMethod.TOOLS_LIST.value
            )
            
            response = await server.handle_message(message, "test-client")
            assert response.id == i
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 2.0  # Less than 2 seconds

if __name__ == "__main__":
    pytest.main([__file__, "-v"])