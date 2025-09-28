#!/usr/bin/env python3
"""
AI Agent Template Examples

This script demonstrates how to use different agent templates
for various use cases.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8003/api/v1"

def create_agent_from_template(template_name: str, agent_name: str) -> str:
    """Create an agent from a template"""
    response = requests.post(
        f"{API_BASE_URL}/agents/from-template",
        params={
            "template_name": template_name,
            "agent_name": agent_name
        }
    )
    response.raise_for_status()
    return response.json()["agent_id"]

def execute_agent_task(agent_id: str, task: str) -> Dict[str, Any]:
    """Execute a task with an agent"""
    response = requests.post(
        f"{API_BASE_URL}/agents/{agent_id}/execute",
        json={"task": task}
    )
    response.raise_for_status()
    return response.json()

def demonstrate_template(template_name: str, template_display_name: str, example_tasks: list):
    """Demonstrate a specific template"""
    print(f"\n🤖 {template_display_name} Template")
    print("-" * 40)
    
    try:
        # Create agent
        agent_id = create_agent_from_template(template_name, f"Demo {template_display_name}")
        print(f"✅ Created agent: {agent_id}")
        
        # Execute example tasks
        for i, task in enumerate(example_tasks, 1):
            print(f"\nTask {i}: {task}")
            result = execute_agent_task(agent_id, task)
            
            if result["success"]:
                print(f"✅ Result: {result['result'][:150]}...")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
            
            time.sleep(1)
            
    except Exception as e:
        print(f"❌ Error with {template_display_name}: {e}")

def main():
    """Main example function"""
    print("🤖 AI Agent Template Examples")
    print("=" * 50)
    
    # Define template examples
    template_examples = [
        {
            "name": "research_assistant",
            "display": "Research Assistant",
            "tasks": [
                "Research the latest developments in quantum computing",
                "Find information about sustainable energy solutions",
                "Summarize the key findings about climate change research"
            ]
        },
        {
            "name": "creative_writer",
            "display": "Creative Writer",
            "tasks": [
                "Write a short story about a robot learning to paint",
                "Create marketing copy for a new AI product",
                "Generate a poem about the future of technology"
            ]
        },
        {
            "name": "customer_service",
            "display": "Customer Service",
            "tasks": [
                "Help a customer with a billing question",
                "Provide information about product features",
                "Resolve a complaint about shipping delays"
            ]
        },
        {
            "name": "learning_tutor",
            "display": "Learning Tutor",
            "tasks": [
                "Explain how machine learning algorithms work",
                "Help with a math problem about derivatives",
                "Provide study tips for learning a new language"
            ]
        },
        {
            "name": "project_manager",
            "display": "Project Manager",
            "tasks": [
                "Create a project timeline for a software development project",
                "Identify potential risks in a marketing campaign",
                "Suggest ways to improve team collaboration"
            ]
        }
    ]
    
    try:
        # Demonstrate each template
        for template in template_examples:
            demonstrate_template(
                template["name"],
                template["display"],
                template["tasks"]
            )
            time.sleep(2)  # Pause between templates
        
        print("\n🎉 All template examples completed!")
        print("\n💡 Tips:")
        print("- Each template is optimized for specific use cases")
        print("- You can customize agents by modifying their goals and tools")
        print("- Check the web interface at http://localhost:3001 for more options")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the AI Agents service is running on localhost:8003")

if __name__ == "__main__":
    main()
