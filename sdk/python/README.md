# Multimodal LLM Stack Python SDK

A comprehensive Python client for the Multimodal LLM Stack services.

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from multimodal_llm_client import MultimodalLLMClient

# Initialize client
client = MultimodalLLMClient(
    litellm_api_key="sk-your-litellm-key"
)

# Check service health
health = client.health_check()
print("Health Status:", health)

# Process an image
result = client.multimodal_worker.process_image(
    "path/to/image.jpg",
    document_name="my_image.jpg",
    metadata={"category": "test"}
)
print("Processing result:", result)

# Search for content
search_results = client.retrieval_proxy.search(
    "artificial intelligence",
    modalities=["text", "image"],
    limit=5
)
print("Search results:", search_results)

# Create an AI agent
agent = client.ai_agents.create_agent(
    name="Research Assistant",
    goal="Help with research tasks",
    tools=["web_search", "document_analysis"]
)
print("Created agent:", agent)

# Chat with LiteLLM
chat_response = client.litellm.chat_completion(
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ],
    model="gpt-3.5-turbo",
    max_tokens=100
)
print("Chat response:", chat_response)
```

## API Reference

### MultimodalLLMClient

Main client class that provides access to all services.

#### Constructor

```python
MultimodalLLMClient(
    litellm_base_url="http://localhost:4000",
    multimodal_worker_url="http://localhost:8001",
    retrieval_proxy_url="http://localhost:8002",
    ai_agents_url="http://localhost:8003",
    litellm_api_key=None,
    timeout=30
)
```

#### Methods

- `health_check()` - Check health status of all services

### LiteLLMClient

Client for the LiteLLM Router service.

#### Methods

- `chat_completion(messages, model, max_tokens, temperature, **kwargs)` - Create chat completion
- `list_models()` - List available models
- `health_check()` - Check service health

### MultimodalWorkerClient

Client for the Multimodal Worker service.

#### Methods

- `process_image(image_path, document_name, metadata)` - Process image file
- `process_video(video_path, document_name, metadata)` - Process video file
- `process_text(text, document_name, metadata)` - Process text content
- `get_models_status()` - Get model status
- `get_storage_status()` - Get storage status
- `health_check()` - Check service health

### RetrievalProxyClient

Client for the Retrieval Proxy service.

#### Methods

- `search(query, modalities, limit, filters, score_threshold)` - Perform search
- `get_search_sessions(limit)` - Get search sessions
- `get_context_bundle(session_id, format)` - Get context bundle
- `get_image_artifact(document_id)` - Get image artifact
- `get_video_artifact(document_id)` - Get video artifact
- `get_keyframe_artifact(keyframe_id)` - Get keyframe artifact
- `get_system_stats()` - Get system statistics
- `health_check()` - Check service health

### AIAgentsClient

Client for the AI Agents service.

#### Methods

- `create_agent(name, goal, tools, memory_window, user_id)` - Create agent
- `list_agents(user_id)` - List agents
- `get_agent(agent_id)` - Get agent details
- `execute_agent_task(agent_id, task, user_id)` - Execute agent task
- `delete_agent(agent_id, user_id)` - Delete agent
- `list_tools()` - List available tools
- `list_templates(category, search)` - List templates
- `get_template_details(template_name)` - Get template details
- `create_agent_from_template(template_name, agent_name, user_id)` - Create from template
- `get_agent_history(agent_id, limit)` - Get agent history
- `get_agent_stats(agent_id)` - Get agent statistics
- `health_check()` - Check service health

## Examples

### Complete Workflow

```python
from multimodal_llm_client import MultimodalLLMClient

client = MultimodalLLMClient(litellm_api_key="sk-your-key")

# 1. Process an image
image_result = client.multimodal_worker.process_image(
    "ai_diagram.jpg",
    document_name="neural_network_diagram.jpg",
    metadata={"category": "diagram", "tags": ["AI", "neural network"]}
)

# 2. Search for related content
search_results = client.retrieval_proxy.search(
    "neural network architecture",
    modalities=["image", "text"],
    limit=5,
    score_threshold=0.8
)

# 3. Create an AI agent to analyze the results
agent = client.ai_agents.create_agent(
    name="AI Diagram Analyzer",
    goal="Analyze AI diagrams and provide insights",
    tools=["image_analysis", "document_analysis"],
    memory_window=15
)

# 4. Execute analysis task
analysis_result = client.ai_agents.execute_agent_task(
    agent["agent_id"],
    "Analyze the neural network diagram and explain its architecture"
)

# 5. Chat about the results
chat_response = client.litellm.chat_completion(
    messages=[
        {"role": "system", "content": "You are an AI expert."},
        {"role": "user", "content": f"Based on this analysis: {analysis_result['result']}, what are the key insights?"}
    ],
    model="gpt-3.5-turbo",
    max_tokens=200
)
```

### Error Handling

```python
import requests
from multimodal_llm_client import MultimodalLLMClient

client = MultimodalLLMClient()

try:
    result = client.multimodal_worker.process_image("nonexistent.jpg")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("File not found")
    elif e.response.status_code == 413:
        print("File too large")
    else:
        print(f"HTTP error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Async Usage (with asyncio)

```python
import asyncio
import aiohttp
from multimodal_llm_client import MultimodalLLMClient

async def process_multiple_images(client, image_paths):
    tasks = []
    for path in image_paths:
        # Note: This is a synchronous client, but you can wrap it in asyncio
        task = asyncio.create_task(
            asyncio.to_thread(client.multimodal_worker.process_image, path)
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# Usage
async def main():
    client = MultimodalLLMClient()
    image_paths = ["image1.jpg", "image2.jpg", "image3.jpg"]
    results = await process_multiple_images(client, image_paths)
    print("Processing results:", results)

asyncio.run(main())
```

## Configuration

### Environment Variables

You can configure the client using environment variables:

```bash
export LITELLM_API_KEY="sk-your-litellm-key"
export LITELLM_BASE_URL="http://localhost:4000"
export MULTIMODAL_WORKER_URL="http://localhost:8001"
export RETRIEVAL_PROXY_URL="http://localhost:8002"
export AI_AGENTS_URL="http://localhost:8003"
```

### Custom Configuration

```python
client = MultimodalLLMClient(
    litellm_base_url="https://api.your-domain.com",
    multimodal_worker_url="https://worker.your-domain.com",
    retrieval_proxy_url="https://search.your-domain.com",
    ai_agents_url="https://agents.your-domain.com",
    litellm_api_key="sk-your-production-key",
    timeout=60
)
```

## License

MIT License - see LICENSE file for details.