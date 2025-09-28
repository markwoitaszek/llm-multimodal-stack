#!/usr/bin/env python3
"""
n8n Integration Examples for AI Agents Service

This script demonstrates how to integrate the AI Agents service with n8n workflows.
"""

import httpx
import asyncio
import json
from typing import Dict, Any, List

class N8NAIAgentsIntegration:
    """Integration class for connecting n8n workflows with AI Agents"""
    
    def __init__(self, ai_agents_url: str = "http://localhost:8003"):
        self.ai_agents_url = ai_agents_url
        self.client = httpx.AsyncClient()
    
    async def create_agent_from_n8n_workflow(self, workflow_data: Dict[str, Any]) -> str:
        """Create an AI agent based on n8n workflow configuration"""
        
        # Extract agent configuration from n8n workflow
        agent_config = {
            "name": workflow_data.get("name", "n8n-workflow-agent"),
            "goal": workflow_data.get("description", "Execute n8n workflow tasks"),
            "tools": workflow_data.get("tools", ["search_content", "generate_text"]),
            "memory_window": workflow_data.get("memory_window", 10),
            "user_id": workflow_data.get("user_id", "n8n-system")
        }
        
        # Create agent via API
        response = await self.client.post(
            f"{self.ai_agents_url}/agents",
            json=agent_config
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["agent_id"]
        else:
            raise Exception(f"Failed to create agent: {response.text}")
    
    async def execute_agent_task_from_n8n(self, agent_id: str, task: str, user_id: str = "n8n-system") -> Dict[str, Any]:
        """Execute an agent task triggered by n8n workflow"""
        
        response = await self.client.post(
            f"{self.ai_agents_url}/agents/{agent_id}/execute",
            json={"task": task, "user_id": user_id}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to execute agent task: {response.text}")
    
    async def get_agent_status_for_n8n(self, agent_id: str) -> Dict[str, Any]:
        """Get agent status for n8n workflow monitoring"""
        
        response = await self.client.get(f"{self.ai_agents_url}/agents/{agent_id}")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get agent status: {response.text}")
    
    async def list_agents_for_n8n(self) -> List[Dict[str, Any]]:
        """List all agents for n8n workflow selection"""
        
        response = await self.client.get(f"{self.ai_agents_url}/agents")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to list agents: {response.text}")

# Example n8n workflow configurations
N8N_WORKFLOW_EXAMPLES = {
    "customer_support_automation": {
        "name": "Customer Support Bot",
        "description": "Automatically handle customer inquiries and escalate when needed",
        "tools": ["search_content", "generate_text"],
        "memory_window": 15,
        "trigger": "new_customer_ticket",
        "actions": [
            "analyze_customer_inquiry",
            "search_knowledge_base",
            "generate_response",
            "update_ticket_status"
        ]
    },
    
    "content_moderation": {
        "name": "Content Moderator",
        "description": "Automatically moderate user-generated content",
        "tools": ["analyze_image", "generate_text"],
        "memory_window": 5,
        "trigger": "new_user_content",
        "actions": [
            "analyze_content",
            "check_policy_compliance",
            "generate_moderation_decision",
            "notify_moderators_if_needed"
        ]
    },
    
    "research_assistant": {
        "name": "Research Assistant",
        "description": "Conduct research on specific topics and compile reports",
        "tools": ["web_search", "search_content", "generate_text"],
        "memory_window": 20,
        "trigger": "research_request",
        "actions": [
            "gather_information",
            "analyze_sources",
            "compile_findings",
            "generate_research_report"
        ]
    }
}

async def main():
    """Example usage of n8n integration"""
    
    integration = N8NAIAgentsIntegration()
    
    # Example 1: Create agent from n8n workflow
    workflow_config = N8N_WORKFLOW_EXAMPLES["customer_support_automation"]
    agent_id = await integration.create_agent_from_n8n_workflow(workflow_config)
    print(f"Created agent: {agent_id}")
    
    # Example 2: Execute agent task
    result = await integration.execute_agent_task_from_n8n(
        agent_id, 
        "A customer is asking about our refund policy. Please provide a helpful response.",
        "n8n-system"
    )
    print(f"Agent response: {result}")
    
    # Example 3: Monitor agent status
    status = await integration.get_agent_status_for_n8n(agent_id)
    print(f"Agent status: {status}")

if __name__ == "__main__":
    asyncio.run(main())
