#!/usr/bin/env python3
"""
Basic AI Agent Usage Examples

This script demonstrates how to create and interact with AI agents
using the AI Agents service API.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8003/api/v1"

def create_agent_from_template(template_name: str, agent_name: str, user_id: str = "default") -> str:
    """Create an agent from a template"""
    response = requests.post(
        f"{API_BASE_URL}/agents/from-template",
        params={
            "template_name": template_name,
            "agent_name": agent_name,
            "user_id": user_id
        }
    )
    response.raise_for_status()
    return response.json()["agent_id"]

def execute_agent_task(agent_id: str, task: str, user_id: str = "default") -> Dict[str, Any]:
    """Execute a task with an agent"""
    response = requests.post(
        f"{API_BASE_URL}/agents/{agent_id}/execute",
        json={
            "task": task,
            "user_id": user_id
        }
    )
    response.raise_for_status()
    return response.json()

def get_agent_info(agent_id: str) -> Dict[str, Any]:
    """Get agent information"""
    response = requests.get(f"{API_BASE_URL}/agents/{agent_id}")
    response.raise_for_status()
    return response.json()

def list_agents(user_id: str = "default") -> list:
    """List all agents for a user"""
    response = requests.get(f"{API_BASE_URL}/agents", params={"user_id": user_id})
    response.raise_for_status()
    return response.json()

def get_agent_history(agent_id: str, limit: int = 10) -> Dict[str, Any]:
    """Get agent execution history"""
    response = requests.get(f"{API_BASE_URL}/agents/{agent_id}/history", params={"limit": limit})
    response.raise_for_status()
    return response.json()

def get_agent_stats(agent_id: str) -> Dict[str, Any]:
    """Get agent statistics"""
    response = requests.get(f"{API_BASE_URL}/agents/{agent_id}/stats")
    response.raise_for_status()
    return response.json()

def main():
    """Main example function"""
    print("🤖 AI Agents Service - Basic Usage Examples")
    print("=" * 50)
    
    try:
        # 1. Create a Research Assistant Agent
        print("\n1. Creating Research Assistant Agent...")
        agent_id = create_agent_from_template("research_assistant", "My Research Bot")
        print(f"✅ Created agent: {agent_id}")
        
        # 2. Get agent information
        print("\n2. Getting agent information...")
        agent_info = get_agent_info(agent_id)
        print(f"Agent Name: {agent_info['name']}")
        print(f"Agent Goal: {agent_info['goal']}")
        print(f"Available Tools: {', '.join(agent_info['tools'])}")
        
        # 3. Execute some tasks
        print("\n3. Executing tasks...")
        
        tasks = [
            "Research the latest trends in artificial intelligence",
            "Find information about machine learning applications",
            "Summarize the key points about neural networks"
        ]
        
        for i, task in enumerate(tasks, 1):
            print(f"\nTask {i}: {task}")
            result = execute_agent_task(agent_id, task)
            
            if result["success"]:
                print(f"✅ Result: {result['result'][:200]}...")
                if result.get("intermediate_steps"):
                    print(f"Steps taken: {len(result['intermediate_steps'])}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
            
            time.sleep(1)  # Brief pause between tasks
        
        # 4. Get execution history
        print("\n4. Getting execution history...")
        history = get_agent_history(agent_id)
        print(f"Total executions: {history['count']}")
        
        # 5. Get agent statistics
        print("\n5. Getting agent statistics...")
        stats = get_agent_stats(agent_id)
        print(f"Total executions: {stats['total_executions']}")
        print(f"Successful executions: {stats['successful_executions']}")
        print(f"Success rate: {stats['success_rate']}%")
        print(f"Average execution time: {stats['avg_execution_time_ms']}ms")
        
        # 6. List all agents
        print("\n6. Listing all agents...")
        agents = list_agents()
        print(f"Total agents: {len(agents)}")
        for agent in agents:
            print(f"  - {agent['name']} ({agent['status']})")
        
        print("\n🎉 Examples completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        print("Make sure the AI Agents service is running on localhost:8003")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
