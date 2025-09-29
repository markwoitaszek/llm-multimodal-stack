# AI Agents API Documentation

## Overview

The AI Agents API provides comprehensive functionality for creating, managing, and executing AI agents. This service is the core of the Multimodal LLM Stack, enabling users to build and deploy intelligent agents for various tasks.

## Base URL

```
http://localhost:3000
```

## Authentication

The API uses JWT-based authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## API Endpoints

### Health Check

#### GET /health

Check the health status of the AI Agents service.

**Response:**
```json
{
  "status": "healthy",
  "service": "ai-agents",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0"
}
```

### Agent Management

#### POST /agents

Create a new AI agent.

**Request Body:**
```json
{
  "name": "Research Assistant",
  "description": "An AI agent that helps with research tasks",
  "goal": "Provide accurate and comprehensive research assistance",
  "tools": ["search_content", "generate_text", "analyze_data"],
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 1000,
  "system_prompt": "You are a helpful research assistant...",
  "metadata": {
    "category": "research",
    "tags": ["research", "analysis", "assistant"]
  }
}
```

**Response:**
```json
{
  "agent_id": "agent-123",
  "name": "Research Assistant",
  "description": "An AI agent that helps with research tasks",
  "goal": "Provide accurate and comprehensive research assistance",
  "tools": ["search_content", "generate_text", "analyze_data"],
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 1000,
  "status": "active",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### GET /agents

Get all agents with optional filtering and pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Number of agents per page (default: 10)
- `status` (optional): Filter by status (active, inactive)
- `model` (optional): Filter by model
- `search` (optional): Search in name and description

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "agent-123",
      "name": "Research Assistant",
      "description": "An AI agent that helps with research tasks",
      "goal": "Provide accurate and comprehensive research assistance",
      "tools": ["search_content", "generate_text", "analyze_data"],
      "model": "gpt-4",
      "temperature": 0.7,
      "max_tokens": 1000,
      "status": "active",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ],
  "count": 1,
  "page": 1,
  "limit": 10,
  "total_pages": 1
}
```

#### GET /agents/{agent_id}

Get a specific agent by ID.

**Response:**
```json
{
  "agent_id": "agent-123",
  "name": "Research Assistant",
  "description": "An AI agent that helps with research tasks",
  "goal": "Provide accurate and comprehensive research assistance",
  "tools": ["search_content", "generate_text", "analyze_data"],
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 1000,
  "status": "active",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "execution_count": 15,
  "success_rate": 95.5
}
```

#### PUT /agents/{agent_id}

Update an existing agent.

**Request Body:**
```json
{
  "name": "Updated Research Assistant",
  "description": "Updated description",
  "temperature": 0.8
}
```

**Response:**
```json
{
  "agent_id": "agent-123",
  "name": "Updated Research Assistant",
  "description": "Updated description",
  "goal": "Provide accurate and comprehensive research assistance",
  "tools": ["search_content", "generate_text", "analyze_data"],
  "model": "gpt-4",
  "temperature": 0.8,
  "max_tokens": 1000,
  "status": "active",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:05:00Z"
}
```

#### DELETE /agents/{agent_id}

Delete an agent.

**Response:**
```json
{
  "message": "Agent deleted successfully",
  "agent_id": "agent-123"
}
```

### Agent Execution

#### POST /agents/{agent_id}/execute

Execute an agent with a specific task.

**Request Body:**
```json
{
  "task": "Research the latest trends in artificial intelligence",
  "user_id": "user-456",
  "context": {
    "domain": "technology",
    "timeframe": "2024",
    "focus": "machine learning"
  },
  "options": {
    "max_steps": 10,
    "timeout": 300
  }
}
```

**Response:**
```json
{
  "execution_id": "exec-789",
  "agent_id": "agent-123",
  "task": "Research the latest trends in artificial intelligence",
  "user_id": "user-456",
  "status": "running",
  "progress": 0,
  "started_at": "2024-01-01T12:00:00Z",
  "estimated_completion": "2024-01-01T12:05:00Z"
}
```

#### GET /executions/{execution_id}

Get execution details and status.

**Response:**
```json
{
  "execution_id": "exec-789",
  "agent_id": "agent-123",
  "task": "Research the latest trends in artificial intelligence",
  "user_id": "user-456",
  "status": "completed",
  "progress": 100,
  "result": "Based on my research, here are the latest trends in AI...",
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:04:30Z",
  "execution_time": 270,
  "intermediate_steps": [
    {
      "step": 1,
      "action": "search_content",
      "query": "artificial intelligence trends 2024",
      "result": "Found 15 relevant articles",
      "timestamp": "2024-01-01T12:00:30Z"
    },
    {
      "step": 2,
      "action": "analyze_data",
      "input": "15 articles about AI trends",
      "result": "Identified 5 key trends",
      "timestamp": "2024-01-01T12:02:15Z"
    }
  ],
  "metadata": {
    "tokens_used": 1250,
    "cost": 0.025
  }
}
```

#### GET /agents/{agent_id}/executions

Get all executions for a specific agent.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Number of executions per page (default: 10)
- `status` (optional): Filter by status (running, completed, failed)
- `user_id` (optional): Filter by user ID

**Response:**
```json
{
  "executions": [
    {
      "execution_id": "exec-789",
      "agent_id": "agent-123",
      "task": "Research the latest trends in artificial intelligence",
      "user_id": "user-456",
      "status": "completed",
      "progress": 100,
      "started_at": "2024-01-01T12:00:00Z",
      "completed_at": "2024-01-01T12:04:30Z",
      "execution_time": 270
    }
  ],
  "count": 1,
  "page": 1,
  "limit": 10,
  "total_pages": 1
}
```

#### GET /executions

Get all executions with optional filtering.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Number of executions per page (default: 10)
- `status` (optional): Filter by status
- `user_id` (optional): Filter by user ID
- `agent_id` (optional): Filter by agent ID
- `start_date` (optional): Filter by start date (ISO format)
- `end_date` (optional): Filter by end date (ISO format)

**Response:**
```json
{
  "executions": [
    {
      "execution_id": "exec-789",
      "agent_id": "agent-123",
      "task": "Research the latest trends in artificial intelligence",
      "user_id": "user-456",
      "status": "completed",
      "progress": 100,
      "started_at": "2024-01-01T12:00:00Z",
      "completed_at": "2024-01-01T12:04:30Z",
      "execution_time": 270
    }
  ],
  "count": 1,
  "page": 1,
  "limit": 10,
  "total_pages": 1
}
```

#### PUT /executions/{execution_id}

Update an execution (e.g., cancel it).

**Request Body:**
```json
{
  "status": "cancelled",
  "reason": "User requested cancellation"
}
```

**Response:**
```json
{
  "execution_id": "exec-789",
  "status": "cancelled",
  "updated_at": "2024-01-01T12:02:00Z"
}
```

### Statistics and Analytics

#### GET /agents/{agent_id}/statistics

Get statistics for a specific agent.

**Response:**
```json
{
  "agent_id": "agent-123",
  "name": "Research Assistant",
  "total_executions": 150,
  "successful_executions": 142,
  "failed_executions": 8,
  "success_rate": 94.67,
  "avg_execution_time": 245.5,
  "total_tokens_used": 187500,
  "total_cost": 3.75,
  "last_execution": "2024-01-01T12:00:00Z",
  "execution_trends": {
    "daily": [
      {"date": "2024-01-01", "count": 15},
      {"date": "2024-01-02", "count": 18},
      {"date": "2024-01-03", "count": 12}
    ],
    "weekly": [
      {"week": "2024-W01", "count": 105},
      {"week": "2024-W02", "count": 98}
    ]
  }
}
```

#### GET /statistics

Get overall system statistics.

**Response:**
```json
{
  "total_agents": 25,
  "total_executions": 1250,
  "successful_executions": 1180,
  "failed_executions": 70,
  "success_rate": 94.4,
  "avg_execution_time": 280.5,
  "total_tokens_used": 1562500,
  "total_cost": 31.25,
  "active_agents": 20,
  "most_used_agents": [
    {
      "agent_id": "agent-123",
      "name": "Research Assistant",
      "execution_count": 150
    }
  ],
  "execution_trends": {
    "daily": [
      {"date": "2024-01-01", "count": 85},
      {"date": "2024-01-02", "count": 92},
      {"date": "2024-01-03", "count": 78}
    ]
  }
}
```

### Search and Discovery

#### GET /agents/search

Search agents by name, description, or tags.

**Query Parameters:**
- `query` (required): Search query
- `page` (optional): Page number (default: 1)
- `limit` (optional): Number of results per page (default: 10)

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "agent-123",
      "name": "Research Assistant",
      "description": "An AI agent that helps with research tasks",
      "goal": "Provide accurate and comprehensive research assistance",
      "tools": ["search_content", "generate_text", "analyze_data"],
      "model": "gpt-4",
      "status": "active",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "count": 1,
  "page": 1,
  "limit": 10,
  "total_pages": 1,
  "query": "research"
}
```

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "field": "name",
      "reason": "Name is required"
    },
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req-123"
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Invalid request data
- `AGENT_NOT_FOUND`: Agent with specified ID not found
- `EXECUTION_NOT_FOUND`: Execution with specified ID not found
- `AGENT_INACTIVE`: Agent is not active
- `EXECUTION_FAILED`: Agent execution failed
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded
- `AUTHENTICATION_ERROR`: Authentication failed
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `INTERNAL_ERROR`: Internal server error

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Default limits**: 1000 requests per hour per user
- **Execution limits**: 10 executions per minute per user
- **Burst limits**: 100 requests per minute per user

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## WebSocket Support

### Real-Time Execution Updates

Connect to the WebSocket endpoint for real-time execution updates:

```
ws://localhost:3000/ws/executions
```

**Message Format:**
```json
{
  "type": "execution_update",
  "data": {
    "execution_id": "exec-789",
    "agent_id": "agent-123",
    "status": "running",
    "progress": 60,
    "current_step": "Analyzing data",
    "timestamp": "2024-01-01T12:02:00Z"
  }
}
```

## SDKs and Libraries

### Python SDK

```python
from ai_agents_sdk import AIAgentsClient

client = AIAgentsClient(api_key="your-api-key")

# Create an agent
agent = client.create_agent({
    "name": "Research Assistant",
    "description": "Helps with research tasks",
    "goal": "Provide research assistance",
    "tools": ["search_content", "generate_text"],
    "model": "gpt-4"
})

# Execute the agent
execution = client.execute_agent(agent.id, "Research AI trends")
result = client.wait_for_completion(execution.id)
```

### JavaScript SDK

```javascript
import { AIAgentsClient } from 'ai-agents-sdk';

const client = new AIAgentsClient('your-api-key');

// Create an agent
const agent = await client.createAgent({
  name: 'Research Assistant',
  description: 'Helps with research tasks',
  goal: 'Provide research assistance',
  tools: ['search_content', 'generate_text'],
  model: 'gpt-4'
});

// Execute the agent
const execution = await client.executeAgent(agent.id, 'Research AI trends');
const result = await client.waitForCompletion(execution.id);
```

## Examples

### Complete Workflow Example

```python
import requests
import time

# Create an agent
agent_data = {
    "name": "Content Creator",
    "description": "Creates engaging content",
    "goal": "Generate high-quality content",
    "tools": ["generate_text", "search_content"],
    "model": "gpt-4",
    "temperature": 0.8
}

response = requests.post("http://localhost:3000/agents", json=agent_data)
agent = response.json()
agent_id = agent["agent_id"]

# Execute the agent
execution_data = {
    "task": "Write a blog post about sustainable energy",
    "user_id": "user-123"
}

response = requests.post(f"http://localhost:3000/agents/{agent_id}/execute", json=execution_data)
execution = response.json()
execution_id = execution["execution_id"]

# Poll for completion
while True:
    response = requests.get(f"http://localhost:3000/executions/{execution_id}")
    execution = response.json()
    
    if execution["status"] in ["completed", "failed"]:
        break
    
    time.sleep(2)

# Get the result
if execution["status"] == "completed":
    print(f"Result: {execution['result']}")
else:
    print(f"Execution failed: {execution['error']}")
```

## Changelog

### Version 1.0.0
- Initial release
- Agent management API
- Execution API
- Statistics and analytics
- WebSocket support
- Rate limiting
- Authentication