"""
End-to-end tests for user workflows
"""

import pytest
import asyncio
import httpx
import websockets
import json
from typing import Dict, Any, List

@pytest.mark.e2e
class TestUserWorkflows:
    """End-to-end tests for complete user workflows"""
    
    @pytest.fixture
    async def api_client(self):
        """Create HTTP client for API testing"""
        async with httpx.AsyncClient(base_url="http://localhost:3000") as client:
            yield client
    
    @pytest.fixture
    async def websocket_client(self):
        """Create WebSocket client for real-time testing"""
        async with websockets.connect("ws://localhost:3006/ws") as websocket:
            yield websocket
    
    @pytest.mark.asyncio
    async def test_complete_agent_workflow(self, api_client, websocket_client):
        """Test complete agent creation and execution workflow"""
        # Step 1: Create an agent
        agent_data = {
            "name": "E2E Test Agent",
            "description": "Agent for end-to-end testing",
            "goal": "Complete workflow testing",
            "tools": ["search_content", "generate_text"],
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = await api_client.post("/agents", json=agent_data)
        assert response.status_code == 201
        agent_id = response.json()["agent_id"]
        
        # Step 2: Verify agent was created
        response = await api_client.get(f"/agents/{agent_id}")
        assert response.status_code == 200
        agent = response.json()
        assert agent["name"] == agent_data["name"]
        assert agent["description"] == agent_data["description"]
        assert agent["goal"] == agent_data["goal"]
        
        # Step 3: Execute the agent
        execution_data = {
            "task": "Generate a summary of the latest AI trends",
            "user_id": "e2e_test_user"
        }
        
        response = await api_client.post(f"/agents/{agent_id}/execute", json=execution_data)
        assert response.status_code == 200
        execution_id = response.json()["execution_id"]
        
        # Step 4: Monitor execution via WebSocket
        await websocket_client.send(json.dumps({
            "type": "subscribe_agent",
            "data": {"agent_id": agent_id}
        }))
        
        # Wait for execution updates
        execution_completed = False
        timeout = 30  # 30 seconds timeout
        
        while not execution_completed and timeout > 0:
            try:
                message = await asyncio.wait_for(websocket_client.recv(), timeout=1.0)
                data = json.loads(message)
                
                if data.get("type") == "agent_execution_update":
                    execution_data = data.get("data", {})
                    if execution_data.get("execution_id") == execution_id:
                        status = execution_data.get("status")
                        if status in ["completed", "failed"]:
                            execution_completed = True
                            assert status == "completed", f"Execution failed: {execution_data.get('error')}"
                
                timeout -= 1
            except asyncio.TimeoutError:
                timeout -= 1
                continue
        
        assert execution_completed, "Execution did not complete within timeout"
        
        # Step 5: Verify execution result
        response = await api_client.get(f"/executions/{execution_id}")
        assert response.status_code == 200
        execution = response.json()
        assert execution["status"] == "completed"
        assert execution["result"] is not None
        
        # Step 6: Check agent statistics
        response = await api_client.get(f"/agents/{agent_id}/statistics")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_executions"] >= 1
        assert stats["successful_executions"] >= 1
    
    @pytest.mark.asyncio
    async def test_collaborative_workspace_workflow(self, api_client, websocket_client):
        """Test collaborative workspace workflow"""
        # Step 1: Create a workspace
        workspace_data = {
            "name": "E2E Test Workspace",
            "description": "Workspace for end-to-end testing",
            "created_by": "e2e_test_user"
        }
        
        response = await api_client.post("/workspaces", json=workspace_data)
        assert response.status_code == 201
        workspace_id = response.json()["workspace_id"]
        
        # Step 2: Join workspace via WebSocket
        await websocket_client.send(json.dumps({
            "type": "join_workspace",
            "data": {
                "workspace_id": workspace_id,
                "user_id": "e2e_test_user"
            }
        }))
        
        # Step 3: Create an agent in the workspace
        agent_data = {
            "name": "Workspace Agent",
            "description": "Agent for workspace testing",
            "goal": "Workspace collaboration",
            "tools": ["search_content", "generate_text"],
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = await api_client.post("/agents", json=agent_data)
        assert response.status_code == 201
        agent_id = response.json()["agent_id"]
        
        # Step 4: Add agent to workspace
        response = await api_client.post(f"/workspaces/{workspace_id}/agents", json={"agent_id": agent_id})
        assert response.status_code == 200
        
        # Step 5: Execute agent in workspace
        execution_data = {
            "task": "Analyze market trends for Q4 2024",
            "user_id": "e2e_test_user"
        }
        
        response = await api_client.post(f"/agents/{agent_id}/execute", json=execution_data)
        assert response.status_code == 200
        execution_id = response.json()["execution_id"]
        
        # Step 6: Monitor workspace updates via WebSocket
        workspace_update_received = False
        timeout = 30
        
        while not workspace_update_received and timeout > 0:
            try:
                message = await asyncio.wait_for(websocket_client.recv(), timeout=1.0)
                data = json.loads(message)
                
                if data.get("type") == "workspace_update":
                    update_data = data.get("data", {})
                    if update_data.get("workspace_id") == workspace_id:
                        workspace_update_received = True
                
                timeout -= 1
            except asyncio.TimeoutError:
                timeout -= 1
                continue
        
        assert workspace_update_received, "Workspace update not received"
        
        # Step 7: Verify workspace contains the agent
        response = await api_client.get(f"/workspaces/{workspace_id}")
        assert response.status_code == 200
        workspace = response.json()
        assert agent_id in workspace["agents"]
    
    @pytest.mark.asyncio
    async def test_multi_user_collaboration_workflow(self, api_client):
        """Test multi-user collaboration workflow"""
        # Step 1: Create workspace
        workspace_data = {
            "name": "Multi-User Workspace",
            "description": "Workspace for multi-user testing",
            "created_by": "user1"
        }
        
        response = await api_client.post("/workspaces", json=workspace_data)
        assert response.status_code == 201
        workspace_id = response.json()["workspace_id"]
        
        # Step 2: User 1 joins workspace
        response = await api_client.post(f"/workspaces/{workspace_id}/join", json={"user_id": "user1"})
        assert response.status_code == 200
        
        # Step 3: User 2 joins workspace
        response = await api_client.post(f"/workspaces/{workspace_id}/join", json={"user_id": "user2"})
        assert response.status_code == 200
        
        # Step 4: User 1 creates an agent
        agent_data = {
            "name": "Collaborative Agent",
            "description": "Agent for multi-user collaboration",
            "goal": "Multi-user testing",
            "tools": ["search_content", "generate_text"],
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = await api_client.post("/agents", json=agent_data)
        assert response.status_code == 201
        agent_id = response.json()["agent_id"]
        
        # Step 5: User 2 executes the agent
        execution_data = {
            "task": "Generate a report on renewable energy trends",
            "user_id": "user2"
        }
        
        response = await api_client.post(f"/agents/{agent_id}/execute", json=execution_data)
        assert response.status_code == 200
        execution_id = response.json()["execution_id"]
        
        # Step 6: Verify execution was created by user 2
        response = await api_client.get(f"/executions/{execution_id}")
        assert response.status_code == 200
        execution = response.json()
        assert execution["user_id"] == "user2"
        
        # Step 7: Check workspace users
        response = await api_client.get(f"/workspaces/{workspace_id}/users")
        assert response.status_code == 200
        users = response.json()["users"]
        assert "user1" in users
        assert "user2" in users
    
    @pytest.mark.asyncio
    async def test_protocol_integration_workflow(self, api_client):
        """Test protocol integration workflow"""
        # Step 1: Check protocol integration service health
        response = await api_client.get("http://localhost:3005/health")
        assert response.status_code == 200
        
        # Step 2: Get available protocols
        response = await api_client.get("http://localhost:3005/protocols")
        assert response.status_code == 200
        protocols = response.json()["protocols"]
        assert len(protocols) > 0
        
        # Step 3: Test protocol translation
        translation_data = {
            "from_protocol": "lsp",
            "to_protocol": "mcp",
            "request": {
                "method": "textDocument/completion",
                "params": {
                    "textDocument": {"uri": "file:///test.py"},
                    "position": {"line": 10, "character": 5}
                }
            }
        }
        
        response = await api_client.post("http://localhost:3005/translate", json=translation_data)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "result" in result
        
        # Step 4: Test protocol server status
        response = await api_client.get("http://localhost:3005/servers")
        assert response.status_code == 200
        servers = response.json()["servers"]
        assert len(servers) > 0
    
    @pytest.mark.asyncio
    async def test_ide_bridge_integration_workflow(self, api_client):
        """Test IDE Bridge integration workflow"""
        # Step 1: Check IDE Bridge service health
        response = await api_client.get("http://localhost:3004/health")
        assert response.status_code == 200
        
        # Step 2: Test code analysis
        analysis_data = {
            "file_path": "/test.py",
            "content": "def hello_world():\n    print('Hello, World!')",
            "language": "python"
        }
        
        response = await api_client.post("http://localhost:3004/analyze", json=analysis_data)
        assert response.status_code == 200
        result = response.json()
        assert "analysis" in result
        
        # Step 3: Test code completion
        completion_data = {
            "file_path": "/test.py",
            "content": "import numpy as np\nnp.",
            "position": {"line": 1, "character": 3}
        }
        
        response = await api_client.post("http://localhost:3004/completion", json=completion_data)
        assert response.status_code == 200
        result = response.json()
        assert "completions" in result
        
        # Step 4: Test hover information
        hover_data = {
            "file_path": "/test.py",
            "content": "def hello_world():\n    print('Hello, World!')",
            "position": {"line": 0, "character": 4}
        }
        
        response = await api_client.post("http://localhost:3004/hover", json=hover_data)
        assert response.status_code == 200
        result = response.json()
        assert "hover" in result
    
    @pytest.mark.asyncio
    async def test_n8n_workflow_automation(self, api_client):
        """Test n8n workflow automation"""
        # Step 1: Check n8n service health
        response = await api_client.get("http://localhost:5678/health")
        assert response.status_code == 200
        
        # Step 2: Get available workflows
        response = await api_client.get("http://localhost:5678/workflows")
        assert response.status_code == 200
        workflows = response.json()["workflows"]
        assert len(workflows) > 0
        
        # Step 3: Execute a workflow
        workflow_data = {
            "workflow_id": "customer-support-automation",
            "input_data": {
                "customer_query": "I need help with my order",
                "customer_id": "12345"
            }
        }
        
        response = await api_client.post("http://localhost:5678/execute", json=workflow_data)
        assert response.status_code == 200
        result = response.json()
        assert "execution_id" in result
        
        # Step 4: Check workflow execution status
        execution_id = result["execution_id"]
        response = await api_client.get(f"http://localhost:5678/executions/{execution_id}")
        assert response.status_code == 200
        execution = response.json()
        assert execution["status"] in ["running", "completed", "failed"]
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, api_client):
        """Test error handling in workflows"""
        # Step 1: Try to create agent with invalid data
        invalid_agent_data = {
            "name": "",  # Empty name
            "description": "Invalid agent",
            "goal": "Test error handling"
        }
        
        response = await api_client.post("/agents", json=invalid_agent_data)
        assert response.status_code == 400
        
        # Step 2: Try to get non-existent agent
        response = await api_client.get("/agents/nonexistent-id")
        assert response.status_code == 404
        
        # Step 3: Try to execute non-existent agent
        execution_data = {
            "task": "Test task",
            "user_id": "test_user"
        }
        
        response = await api_client.post("/agents/nonexistent-id/execute", json=execution_data)
        assert response.status_code == 404
        
        # Step 4: Try to execute agent with invalid data
        # First create a valid agent
        agent_data = {
            "name": "Error Test Agent",
            "description": "Agent for error testing",
            "goal": "Error handling",
            "tools": ["search_content"],
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = await api_client.post("/agents", json=agent_data)
        assert response.status_code == 201
        agent_id = response.json()["agent_id"]
        
        # Try to execute with invalid data
        invalid_execution_data = {
            "task": "",  # Empty task
            "user_id": "test_user"
        }
        
        response = await api_client.post(f"/agents/{agent_id}/execute", json=invalid_execution_data)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, api_client):
        """Test system performance under load"""
        # Step 1: Create multiple agents concurrently
        tasks = []
        for i in range(10):
            agent_data = {
                "name": f"Load Test Agent {i}",
                "description": f"Agent {i} for load testing",
                "goal": "Load testing",
                "tools": ["search_content", "generate_text"],
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            task = asyncio.create_task(api_client.post("/agents", json=agent_data))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Step 2: Verify all agents were created successfully
        success_count = sum(1 for result in results if result.status_code == 201)
        assert success_count == 10, f"Only {success_count}/10 agents created successfully"
        
        # Step 3: Execute agents concurrently
        agent_ids = [result.json()["agent_id"] for result in results if result.status_code == 201]
        
        execution_tasks = []
        for i, agent_id in enumerate(agent_ids):
            execution_data = {
                "task": f"Load test task {i}",
                "user_id": f"load_test_user_{i}"
            }
            
            task = asyncio.create_task(api_client.post(f"/agents/{agent_id}/execute", json=execution_data))
            execution_tasks.append(task)
        
        execution_results = await asyncio.gather(*execution_tasks)
        
        # Step 4: Verify all executions were started successfully
        execution_success_count = sum(1 for result in execution_results if result.status_code == 200)
        assert execution_success_count == 10, f"Only {execution_success_count}/10 executions started successfully"
        
        # Step 5: Check system statistics
        response = await api_client.get("/statistics")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_agents"] >= 10
        assert stats["total_executions"] >= 10