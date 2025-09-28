#!/usr/bin/env python3
"""
Multimodal LLM Stack Python SDK

A comprehensive Python client for the Multimodal LLM Stack services.
"""

import requests
import json
import os
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import openai


class MultimodalLLMClient:
    """
    Main client for interacting with the Multimodal LLM Stack services.
    """
    
    def __init__(
        self,
        litellm_base_url: str = "http://localhost:4000",
        multimodal_worker_url: str = "http://localhost:8001",
        retrieval_proxy_url: str = "http://localhost:8002",
        ai_agents_url: str = "http://localhost:8003",
        litellm_api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize the Multimodal LLM Stack client.
        
        Args:
            litellm_base_url: Base URL for LiteLLM Router service
            multimodal_worker_url: Base URL for Multimodal Worker service
            retrieval_proxy_url: Base URL for Retrieval Proxy service
            ai_agents_url: Base URL for AI Agents service
            litellm_api_key: API key for LiteLLM Router (optional)
            timeout: Request timeout in seconds
        """
        self.litellm_base_url = litellm_base_url.rstrip('/')
        self.multimodal_worker_url = multimodal_worker_url.rstrip('/')
        self.retrieval_proxy_url = retrieval_proxy_url.rstrip('/')
        self.ai_agents_url = ai_agents_url.rstrip('/')
        self.timeout = timeout
        
        # Configure OpenAI client for LiteLLM Router
        if litellm_api_key:
            openai.api_key = litellm_api_key
            openai.api_base = f"{self.litellm_base_url}/v1"
        
        # Initialize service clients
        self.litellm = LiteLLMClient(self.litellm_base_url, litellm_api_key, timeout)
        self.multimodal_worker = MultimodalWorkerClient(self.multimodal_worker_url, timeout)
        self.retrieval_proxy = RetrievalProxyClient(self.retrieval_proxy_url, timeout)
        self.ai_agents = AIAgentsClient(self.ai_agents_url, timeout)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health status of all services.
        
        Returns:
            Dictionary with health status of each service
        """
        health_status = {}
        
        services = [
            ("litellm", self.litellm_base_url),
            ("multimodal_worker", self.multimodal_worker_url),
            ("retrieval_proxy", self.retrieval_proxy_url),
            ("ai_agents", self.ai_agents_url)
        ]
        
        for service_name, base_url in services:
            try:
                response = requests.get(f"{base_url}/health", timeout=self.timeout)
                health_status[service_name] = response.json() if response.status_code == 200 else {"status": "unhealthy"}
            except Exception as e:
                health_status[service_name] = {"status": "unhealthy", "error": str(e)}
        
        return health_status


class LiteLLMClient:
    """Client for LiteLLM Router service."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 30):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion.
        
        Args:
            messages: List of message objects
            model: Model to use for completion
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Chat completion response
        """
        data = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        if temperature is not None:
            data["temperature"] = temperature
        
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers={**self.headers, "Content-Type": "application/json"},
            json=data,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def list_models(self) -> Dict[str, Any]:
        """
        List available models.
        
        Returns:
            List of available models
        """
        response = requests.get(
            f"{self.base_url}/v1/models",
            headers=self.headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()


class MultimodalWorkerClient:
    """Client for Multimodal Worker service."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
    
    def process_image(
        self,
        image_path: Union[str, Path],
        document_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an image file.
        
        Args:
            image_path: Path to the image file
            document_name: Optional name for the document
            metadata: Optional metadata dictionary
            
        Returns:
            Processing result
        """
        files = {"file": open(image_path, "rb")}
        data = {}
        
        if document_name:
            data["document_name"] = document_name
        if metadata:
            data["metadata"] = json.dumps(metadata)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/process/image",
                files=files,
                data=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        finally:
            files["file"].close()
    
    def process_video(
        self,
        video_path: Union[str, Path],
        document_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a video file.
        
        Args:
            video_path: Path to the video file
            document_name: Optional name for the document
            metadata: Optional metadata dictionary
            
        Returns:
            Processing result
        """
        files = {"file": open(video_path, "rb")}
        data = {}
        
        if document_name:
            data["document_name"] = document_name
        if metadata:
            data["metadata"] = json.dumps(metadata)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/process/video",
                files=files,
                data=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        finally:
            files["file"].close()
    
    def process_text(
        self,
        text: str,
        document_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process text content.
        
        Args:
            text: Text content to process
            document_name: Optional name for the document
            metadata: Optional metadata dictionary
            
        Returns:
            Processing result
        """
        data = {"text": text}
        
        if document_name:
            data["document_name"] = document_name
        if metadata:
            data["metadata"] = metadata
        
        response = requests.post(
            f"{self.base_url}/api/v1/process/text",
            headers={"Content-Type": "application/json"},
            json=data,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_models_status(self) -> Dict[str, Any]:
        """Get status of loaded models."""
        response = requests.get(f"{self.base_url}/api/v1/models/status", timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def get_storage_status(self) -> Dict[str, Any]:
        """Get storage system status."""
        response = requests.get(f"{self.base_url}/api/v1/storage/status", timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()


class RetrievalProxyClient:
    """Client for Retrieval Proxy service."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
    
    def search(
        self,
        query: str,
        modalities: Optional[List[str]] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Perform multimodal search.
        
        Args:
            query: Search query
            modalities: Content types to search (text, image, video)
            limit: Maximum number of results
            filters: Additional filters
            score_threshold: Minimum similarity score
            
        Returns:
            Search results
        """
        data = {
            "query": query,
            "limit": limit
        }
        
        if modalities:
            data["modalities"] = modalities
        if filters:
            data["filters"] = filters
        if score_threshold is not None:
            data["score_threshold"] = score_threshold
        
        response = requests.post(
            f"{self.base_url}/api/v1/search",
            headers={"Content-Type": "application/json"},
            json=data,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_search_sessions(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get recent search sessions.
        
        Args:
            limit: Number of sessions to retrieve
            
        Returns:
            Search sessions
        """
        response = requests.get(
            f"{self.base_url}/api/v1/search/sessions",
            params={"limit": limit},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_context_bundle(
        self,
        session_id: str,
        format: str = "markdown"
    ) -> Dict[str, Any]:
        """
        Get context bundle for a search session.
        
        Args:
            session_id: Search session ID
            format: Output format (markdown, json, plain)
            
        Returns:
            Context bundle
        """
        response = requests.get(
            f"{self.base_url}/api/v1/context/{session_id}",
            params={"format": format},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_image_artifact(self, document_id: str) -> Dict[str, Any]:
        """Get image artifact by document ID."""
        response = requests.get(
            f"{self.base_url}/api/v1/artifacts/image/{document_id}",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_video_artifact(self, document_id: str) -> Dict[str, Any]:
        """Get video artifact by document ID."""
        response = requests.get(
            f"{self.base_url}/api/v1/artifacts/video/{document_id}",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_keyframe_artifact(self, keyframe_id: str) -> Dict[str, Any]:
        """Get keyframe artifact by keyframe ID."""
        response = requests.get(
            f"{self.base_url}/api/v1/artifacts/keyframe/{keyframe_id}",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        response = requests.get(f"{self.base_url}/api/v1/stats", timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()


class AIAgentsClient:
    """Client for AI Agents service."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
    
    def create_agent(
        self,
        name: str,
        goal: str,
        tools: Optional[List[str]] = None,
        memory_window: int = 10,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Create a new AI agent.
        
        Args:
            name: Agent name
            goal: Agent goal or purpose
            tools: List of tool names to enable
            memory_window: Conversation memory window size
            user_id: User ID
            
        Returns:
            Agent creation result
        """
        data = {
            "name": name,
            "goal": goal,
            "memory_window": memory_window,
            "user_id": user_id
        }
        
        if tools:
            data["tools"] = tools
        
        response = requests.post(
            f"{self.base_url}/api/v1/agents",
            headers={"Content-Type": "application/json"},
            json=data,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def list_agents(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """
        List all agents for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of agents
        """
        response = requests.get(
            f"{self.base_url}/api/v1/agents",
            params={"user_id": user_id},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent information.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent information
        """
        response = requests.get(
            f"{self.base_url}/api/v1/agents/{agent_id}",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def execute_agent_task(
        self,
        agent_id: str,
        task: str,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Execute a task with an agent.
        
        Args:
            agent_id: Agent ID
            task: Task for the agent to execute
            user_id: User ID
            
        Returns:
            Task execution result
        """
        data = {
            "task": task,
            "user_id": user_id
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/agents/{agent_id}/execute",
            headers={"Content-Type": "application/json"},
            json=data,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def delete_agent(self, agent_id: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent ID
            user_id: User ID
            
        Returns:
            Deletion result
        """
        response = requests.delete(
            f"{self.base_url}/api/v1/agents/{agent_id}",
            params={"user_id": user_id},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def list_tools(self) -> Dict[str, Any]:
        """List available tools for agents."""
        response = requests.get(f"{self.base_url}/api/v1/tools", timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def list_templates(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List available agent templates.
        
        Args:
            category: Filter by category
            search: Search templates by name or description
            
        Returns:
            List of templates
        """
        params = {}
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        
        response = requests.get(
            f"{self.base_url}/api/v1/templates",
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_template_details(self, template_name: str) -> Dict[str, Any]:
        """
        Get details for a specific template.
        
        Args:
            template_name: Template name
            
        Returns:
            Template details
        """
        response = requests.get(
            f"{self.base_url}/api/v1/templates/{template_name}",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def create_agent_from_template(
        self,
        template_name: str,
        agent_name: Optional[str] = None,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Create an agent from a template.
        
        Args:
            template_name: Name of the template to use
            agent_name: Custom name for the agent
            user_id: User ID
            
        Returns:
            Agent creation result
        """
        data = {
            "template_name": template_name,
            "user_id": user_id
        }
        
        if agent_name:
            data["agent_name"] = agent_name
        
        response = requests.post(
            f"{self.base_url}/api/v1/agents/from-template",
            headers={"Content-Type": "application/json"},
            json=data,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_agent_history(self, agent_id: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get conversation history for an agent.
        
        Args:
            agent_id: Agent ID
            limit: Number of history entries to retrieve
            
        Returns:
            Agent history
        """
        response = requests.get(
            f"{self.base_url}/api/v1/agents/{agent_id}/history",
            params={"limit": limit},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """
        Get statistics for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent statistics
        """
        response = requests.get(
            f"{self.base_url}/api/v1/agents/{agent_id}/stats",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()


# Convenience functions for quick usage
def create_client(
    litellm_api_key: Optional[str] = None,
    **kwargs
) -> MultimodalLLMClient:
    """
    Create a MultimodalLLMClient with default settings.
    
    Args:
        litellm_api_key: API key for LiteLLM Router
        **kwargs: Additional client configuration
        
    Returns:
        Configured MultimodalLLMClient instance
    """
    return MultimodalLLMClient(litellm_api_key=litellm_api_key, **kwargs)


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = create_client(litellm_api_key="sk-your-litellm-key")
    
    # Check health
    health = client.health_check()
    print("Health Status:", health)
    
    # Example: Process an image
    try:
        result = client.multimodal_worker.process_image(
            "example.jpg",
            document_name="test_image.jpg",
            metadata={"category": "test"}
        )
        print("Image processing result:", result)
    except Exception as e:
        print(f"Error processing image: {e}")
    
    # Example: Search for content
    try:
        search_results = client.retrieval_proxy.search(
            "artificial intelligence",
            modalities=["text", "image"],
            limit=5
        )
        print("Search results:", search_results)
    except Exception as e:
        print(f"Error searching: {e}")
    
    # Example: Create an agent
    try:
        agent = client.ai_agents.create_agent(
            name="Test Agent",
            goal="Help with testing and development",
            tools=["web_search"]
        )
        print("Created agent:", agent)
    except Exception as e:
        print(f"Error creating agent: {e}")
    
    # Example: Chat completion
    try:
        chat_response = client.litellm.chat_completion(
            messages=[
                {"role": "user", "content": "Hello, how are you?"}
            ],
            model="gpt-3.5-turbo",
            max_tokens=100
        )
        print("Chat response:", chat_response)
    except Exception as e:
        print(f"Error with chat completion: {e}")