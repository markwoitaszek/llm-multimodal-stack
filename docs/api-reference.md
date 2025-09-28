# API Reference

Complete API documentation for the Multimodal LLM Stack services.

## 🚀 Quick Start

### Interactive Documentation
- **Swagger UI**: [http://localhost:8080/swagger-ui.html](http://localhost:8080/swagger-ui.html)
- **OpenAPI Specs**: [http://localhost:8080/openapi/](http://localhost:8080/openapi/)

### Service Overview

| Service | Base URL | Port | Purpose | Authentication |
|---------|----------|------|---------|----------------|
| **LiteLLM Router** | `http://localhost:4000` | 4000 | OpenAI-compatible API router | Bearer Token |
| **Multimodal Worker** | `http://localhost:8001` | 8001 | Image/video/text processing | None |
| **Retrieval Proxy** | `http://localhost:8002` | 8002 | Unified search & context bundling | None |
| **AI Agents** | `http://localhost:8003` | 8003 | LangChain autonomous agents | None |
| **OpenWebUI** | `http://localhost:3000` | 3000 | Web interface | None |

### Common Use Cases

1. **Chat with AI**: Use LiteLLM Router for OpenAI-compatible chat completions
2. **Process Media**: Upload images/videos to Multimodal Worker for AI analysis
3. **Search Content**: Use Retrieval Proxy to search across all processed content
4. **Create Agents**: Build autonomous AI agents with the AI Agents service

## LiteLLM Router API

### Chat Completions

**OpenAI-compatible chat completions endpoint**

```http
POST /v1/chat/completions
Content-Type: application/json
Authorization: Bearer sk-your-litellm-key

{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "max_tokens": 150,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant", 
        "content": "Hello! I'm doing well, thank you for asking."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 12,
    "total_tokens": 21
  }
}
```

### Models

**List available models**

```http
GET /v1/models
Authorization: Bearer sk-your-litellm-key
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-3.5-turbo",
      "object": "model",
      "created": 1677610602,
      "owned_by": "openai"
    }
  ]
}
```

## Multimodal Worker API

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "multimodal-worker",
  "version": "1.0.0"
}
```

### Process Image

**Upload and process an image**

```http
POST /api/v1/process/image
Content-Type: multipart/form-data

file: [binary image data]
document_name: "my_image.jpg" (optional)
metadata: "{\"category\": \"photo\"}" (optional)
```

**Response:**
```json
{
  "success": true,
  "message": "Image processed successfully",
  "data": {
    "document_id": "uuid-here",
    "image_id": "uuid-here", 
    "caption": "A photo of a cat sitting on a chair",
    "dimensions": [800, 600],
    "storage_path": "images/ab/abcd1234_my_image.jpg"
  }
}
```

### Process Video

**Upload and process a video**

```http
POST /api/v1/process/video
Content-Type: multipart/form-data

file: [binary video data]
document_name: "my_video.mp4" (optional)
metadata: "{\"category\": \"demo\"}" (optional)
```

**Response:**
```json
{
  "success": true,
  "message": "Video processed successfully", 
  "data": {
    "document_id": "uuid-here",
    "video_id": "uuid-here",
    "transcription": "Hello, this is a test video...",
    "keyframes_count": 5,
    "duration": 30.5,
    "storage_path": "videos/cd/cdef5678_my_video.mp4"
  }
}
```

### Process Text

**Process text document**

```http
POST /api/v1/process/text
Content-Type: application/json

{
  "text": "This is a sample document about artificial intelligence...",
  "document_name": "ai_article.txt",
  "metadata": {
    "author": "John Doe",
    "category": "AI"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Text processed successfully",
  "data": {
    "document_id": "uuid-here",
    "chunks_count": 3
  }
}
```

### Model Status

**Check status of loaded models**

```http
GET /api/v1/models/status
```

**Response:**
```json
{
  "clip": "loaded",
  "blip": "loaded",
  "whisper": "loaded", 
  "sentence_transformer": "loaded"
}
```

### Storage Status

**Check storage system status**

```http
GET /api/v1/storage/status
```

**Response:**
```json
{
  "minio": "connected",
  "postgres": "connected", 
  "qdrant": "connected"
}
```

## Retrieval Proxy API

### Search

**Unified multimodal search**

```http
POST /api/v1/search
Content-Type: application/json

{
  "query": "artificial intelligence machine learning",
  "modalities": ["text", "image", "video"],
  "limit": 10,
  "filters": {
    "file_types": ["pdf", "txt"],
    "min_score": 0.7
  },
  "score_threshold": 0.8
}
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "query": "artificial intelligence machine learning",
  "modalities": ["text", "image", "video"],
  "results_count": 5,
  "results": [
    {
      "embedding_id": "uuid-here",
      "score": 0.95,
      "modality": "text",
      "content_type": "text",
      "content": "Machine learning is a subset of artificial intelligence...",
      "document_id": "uuid-here",
      "filename": "ai_basics.pdf",
      "file_type": "pdf",
      "citations": {
        "source": "ai_basics.pdf",
        "type": "text",
        "document_id": "uuid-here"
      },
      "artifacts": {
        "view_url": "/api/v1/artifacts/document/uuid-here"
      }
    }
  ],
  "context_bundle": {
    "query": "artificial intelligence machine learning",
    "sections": [
      {
        "type": "text",
        "title": "Relevant Text Content",
        "content": "[1] Machine learning is a subset...",
        "count": 3
      }
    ],
    "unified_context": "# Search Results for: artificial intelligence...",
    "total_results": 5,
    "context_length": 1250,
    "citations": [...]
  },
  "metadata": {
    "search_timestamp": "2024-01-01T12:00:00Z",
    "filters_applied": {...},
    "score_threshold": 0.8
  }
}
```

### Get Context Bundle

**Retrieve context bundle for a search session**

```http
GET /api/v1/context/{session_id}?format=markdown
```

**Response:**
```json
{
  "context": "# Search Results for: artificial intelligence...\n\n## Relevant Text Content (3 items)\n\n[1] Machine learning is a subset..."
}
```

### Search Sessions

**Get recent search sessions**

```http
GET /api/v1/search/sessions?limit=20
```

**Response:**
```json
{
  "sessions": [
    {
      "id": "uuid-here",
      "session_name": null,
      "query": "artificial intelligence",
      "filters": {},
      "results_count": 5,
      "context_bundle": {...},
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "count": 1
}
```

### Artifacts

**Get image artifact**

```http
GET /api/v1/artifacts/image/{document_id}
```

**Response:**
```json
{
  "document_id": "uuid-here",
  "image_path": "images/ab/abcd1234_photo.jpg",
  "format": "jpg",
  "filename": "photo.jpg",
  "view_url": "/api/v1/artifacts/image/uuid-here",
  "download_url": "/api/v1/artifacts/download/uuid-here"
}
```

**Get video artifact**

```http
GET /api/v1/artifacts/video/{document_id}
```

**Get keyframe artifact**

```http
GET /api/v1/artifacts/keyframe/{keyframe_id}
```

### System Stats

**Get system statistics**

```http
GET /api/v1/stats
```

**Response:**
```json
{
  "database": {
    "documents": {
      "text": 150,
      "image": 75,
      "video": 25
    },
    "totals": {
      "documents": 250,
      "text_chunks": 1500,
      "images": 75,
      "videos": 25,
      "keyframes": 125
    }
  },
  "vector_store": {
    "text": {
      "name": "text_embeddings",
      "vectors_count": 1500,
      "points_count": 1500
    },
    "image": {
      "name": "image_embeddings", 
      "vectors_count": 200,
      "points_count": 200
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Service Status

**Get service status**

```http
GET /api/v1/status
```

**Response:**
```json
{
  "service": "retrieval-proxy",
  "status": "healthy",
  "components": {
    "database": "healthy",
    "vector_store": "healthy"
  },
  "version": "1.0.0"
}
```

## Error Responses

All services return consistent error responses with detailed information:

### Error Response Format

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "service-name",
  "request_id": "optional-request-id"
}
```

### HTTP Status Codes

| Code | Status | Description | Common Causes |
|------|--------|-------------|---------------|
| `200` | OK | Request successful | - |
| `400` | Bad Request | Invalid request parameters | Missing required fields, invalid format |
| `401` | Unauthorized | Authentication required/failed | Missing/invalid API key |
| `403` | Forbidden | Access denied | Insufficient permissions |
| `404` | Not Found | Resource doesn't exist | Invalid ID, deleted resource |
| `413` | Payload Too Large | File/request too large | File exceeds size limit |
| `422` | Unprocessable Entity | Validation errors | Invalid data format, business logic errors |
| `429` | Too Many Requests | Rate limit exceeded | Too many requests per minute |
| `500` | Internal Server Error | Server error | Database issues, model loading failures |
| `503` | Service Unavailable | Service temporarily down | Maintenance, overload |

### Service-Specific Error Codes

#### LiteLLM Router
- `INVALID_API_KEY` - Invalid or missing API key
- `MODEL_NOT_FOUND` - Requested model doesn't exist
- `RATE_LIMIT_EXCEEDED` - Too many requests (60/minute default)
- `INVALID_REQUEST_FORMAT` - Malformed request body

#### Multimodal Worker
- `INVALID_FILE_TYPE` - Unsupported file format
- `FILE_TOO_LARGE` - File exceeds size limit (100MB default)
- `MODEL_NOT_LOADED` - Required AI model not available
- `PROCESSING_FAILED` - Error during file processing
- `STORAGE_ERROR` - File storage operation failed

#### Retrieval Proxy
- `INVALID_QUERY` - Empty or malformed search query
- `INVALID_MODALITY` - Unsupported content modality
- `SEARCH_FAILED` - Error during search operation
- `SESSION_NOT_FOUND` - Invalid session ID
- `VECTOR_STORE_ERROR` - Vector database operation failed

#### AI Agents
- `AGENT_NOT_FOUND` - Invalid agent ID
- `TEMPLATE_NOT_FOUND` - Invalid template name
- `EXECUTION_FAILED` - Agent task execution error
- `TOOL_NOT_AVAILABLE` - Required tool not accessible
- `MEMORY_ERROR` - Agent memory operation failed

### Error Response Examples

#### 400 Bad Request
```json
{
  "detail": "File must be an image (jpg, png, gif)",
  "error_code": "INVALID_FILE_TYPE",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "multimodal-worker"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Invalid API key provided",
  "error_code": "INVALID_API_KEY",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "litellm-router"
}
```

#### 404 Not Found
```json
{
  "detail": "Agent with ID '550e8400-e29b-41d4-a716-446655440000' not found",
  "error_code": "AGENT_NOT_FOUND",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "ai-agents"
}
```

#### 422 Unprocessable Entity
```json
{
  "detail": "Memory window must be between 1 and 100",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "ai-agents"
}
```

#### 429 Rate Limit Exceeded
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "litellm-router"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "An internal server error occurred",
  "error_code": "INTERNAL_SERVER_ERROR",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "multimodal-worker",
  "request_id": "req_123456789"
}
```

## Rate Limits

Default rate limits (configurable):
- **LiteLLM**: 60 requests/minute per API key
- **Multimodal Worker**: 30 uploads/minute per IP
- **Retrieval Proxy**: 120 searches/minute per IP

## Authentication

### API Keys

**LiteLLM Router:**
```bash
Authorization: Bearer sk-your-litellm-master-key
```

**Other Services:**
Currently no authentication required for internal services. In production, implement:
- JWT tokens
- API key authentication
- OAuth 2.0
- mTLS for service-to-service communication

## 📚 Comprehensive Examples

### Complete Workflow Example

Here's a complete example of processing an image, searching for it, and creating an AI agent to analyze it:

#### Step 1: Process an Image
```bash
# Upload and process an image
curl -X POST http://localhost:8001/api/v1/process/image \
  -F "file=@/path/to/ai_diagram.jpg" \
  -F "document_name=ai_architecture_diagram.jpg" \
  -F 'metadata={"category": "diagram", "tags": ["AI", "architecture"]}'
```

**Response:**
```json
{
  "success": true,
  "message": "Image processed successfully",
  "data": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "image_id": "550e8400-e29b-41d4-a716-446655440001",
    "caption": "A diagram showing the architecture of a neural network with input, hidden, and output layers",
    "dimensions": [1200, 800],
    "storage_path": "images/ab/abcd1234_ai_architecture_diagram.jpg"
  }
}
```

#### Step 2: Search for the Image
```bash
# Search for AI-related content
curl -X POST http://localhost:8002/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural network architecture diagram",
    "modalities": ["image", "text"],
    "limit": 5,
    "score_threshold": 0.8
  }'
```

#### Step 3: Create an AI Agent
```bash
# Create an agent to analyze the image
curl -X POST http://localhost:8003/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Image Analysis Expert",
    "goal": "Analyze images and provide detailed descriptions and insights",
    "tools": ["image_analysis", "document_analysis"],
    "memory_window": 15
  }'
```

#### Step 4: Execute Agent Task
```bash
# Have the agent analyze the image
curl -X POST http://localhost:8003/api/v1/agents/550e8400-e29b-41d4-a716-446655440002/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze the AI architecture diagram and explain the neural network structure"
  }'
```

### Service-Specific Examples

#### LiteLLM Router Examples

**Basic Chat Completion:**
```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-litellm-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "system", "content": "You are a helpful AI assistant."},
      {"role": "user", "content": "Explain machine learning in simple terms."}
    ],
    "max_tokens": 200,
    "temperature": 0.7
  }'
```

**Multimodal Chat (with image):**
```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-litellm-key" \
  -d '{
    "model": "gpt-4-vision-preview",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "What do you see in this image?"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
            }
          }
        ]
      }
    ],
    "max_tokens": 300
  }'
```

#### Multimodal Worker Examples

**Process Video with Metadata:**
```bash
curl -X POST http://localhost:8001/api/v1/process/video \
  -F "file=@/path/to/presentation.mp4" \
  -F "document_name=ai_presentation.mp4" \
  -F 'metadata={"category": "presentation", "language": "en", "duration": 120}'
```

**Process Text Document:**
```bash
curl -X POST http://localhost:8001/api/v1/process/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data...",
    "document_name": "ml_introduction.txt",
    "metadata": {
      "author": "Dr. Jane Smith",
      "category": "tutorial",
      "tags": ["machine learning", "AI", "introduction"]
    }
  }'
```

#### Retrieval Proxy Examples

**Advanced Search with Filters:**
```bash
curl -X POST http://localhost:8002/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "deep learning neural networks",
    "modalities": ["text", "image"],
    "limit": 10,
    "filters": {
      "file_types": ["pdf", "jpg", "png"],
      "date_range": {
        "start": "2024-01-01",
        "end": "2024-12-31"
      },
      "min_score": 0.7
    },
    "score_threshold": 0.8
  }'
```

**Get Search Session Context:**
```bash
curl -X GET "http://localhost:8002/api/v1/context/550e8400-e29b-41d4-a716-446655440000?format=markdown"
```

#### AI Agents Examples

**Create Agent from Template:**
```bash
curl -X POST http://localhost:8003/api/v1/agents/from-template \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "research_assistant",
    "agent_name": "My Research Bot",
    "user_id": "user123"
  }'
```

**List Available Templates:**
```bash
curl -X GET "http://localhost:8003/api/v1/templates?category=research"
```

**Get Agent Statistics:**
```bash
curl -X GET http://localhost:8003/api/v1/agents/550e8400-e29b-41d4-a716-446655440000/stats
```

## SDKs and Client Libraries

### Python SDK

```python
import openai
import requests
import json

# Configure LiteLLM Router
openai.api_base = "http://localhost:4000/v1"
openai.api_key = "sk-your-litellm-key"

# Chat completion
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Multimodal Worker - Process image
def process_image(image_path, document_name=None):
    url = "http://localhost:8001/api/v1/process/image"
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'document_name': document_name} if document_name else {}
        response = requests.post(url, files=files, data=data)
    return response.json()

# Retrieval Proxy - Search
def search_content(query, modalities=None, limit=10):
    url = "http://localhost:8002/api/v1/search"
    data = {
        "query": query,
        "modalities": modalities or ["text", "image", "video"],
        "limit": limit
    }
    response = requests.post(url, json=data)
    return response.json()

# AI Agents - Create agent
def create_agent(name, goal, tools=None):
    url = "http://localhost:8003/api/v1/agents"
    data = {
        "name": name,
        "goal": goal,
        "tools": tools or []
    }
    response = requests.post(url, json=data)
    return response.json()

# Example usage
image_result = process_image("diagram.jpg", "AI_diagram.jpg")
search_results = search_content("neural network architecture")
agent = create_agent("AI Expert", "Help with AI questions", ["web_search"])
```

### JavaScript/Node.js SDK

```javascript
import OpenAI from 'openai';
import axios from 'axios';

// Configure LiteLLM Router
const openai = new OpenAI({
  baseURL: 'http://localhost:4000/v1',
  apiKey: 'sk-your-litellm-key',
});

// Chat completion
const response = await openai.chat.completions.create({
  model: 'gpt-3.5-turbo',
  messages: [{ role: 'user', content: 'Hello!' }],
});

// Multimodal Worker - Process image
async function processImage(imagePath, documentName = null) {
  const formData = new FormData();
  formData.append('file', imagePath);
  if (documentName) formData.append('document_name', documentName);
  
  const response = await axios.post(
    'http://localhost:8001/api/v1/process/image',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
}

// Retrieval Proxy - Search
async function searchContent(query, modalities = null, limit = 10) {
  const response = await axios.post('http://localhost:8002/api/v1/search', {
    query,
    modalities: modalities || ['text', 'image', 'video'],
    limit
  });
  return response.data;
}

// AI Agents - Create agent
async function createAgent(name, goal, tools = []) {
  const response = await axios.post('http://localhost:8003/api/v1/agents', {
    name,
    goal,
    tools
  });
  return response.data;
}

// Example usage
const imageResult = await processImage('diagram.jpg', 'AI_diagram.jpg');
const searchResults = await searchContent('neural network architecture');
const agent = await createAgent('AI Expert', 'Help with AI questions', ['web_search']);
```

### cURL Examples

**Complete Workflow with cURL:**
```bash
#!/bin/bash

# 1. Process an image
echo "Processing image..."
IMAGE_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/process/image \
  -F "file=@/path/to/image.jpg" \
  -F "document_name=test_image.jpg")

echo "Image processing result: $IMAGE_RESPONSE"

# 2. Search for content
echo "Searching for content..."
SEARCH_RESPONSE=$(curl -s -X POST http://localhost:8002/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "modalities": ["text", "image"],
    "limit": 5
  }')

echo "Search results: $SEARCH_RESPONSE"

# 3. Create an AI agent
echo "Creating AI agent..."
AGENT_RESPONSE=$(curl -s -X POST http://localhost:8003/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Agent",
    "goal": "Help with testing and development",
    "tools": ["web_search"]
  }')

echo "Agent creation result: $AGENT_RESPONSE"

# 4. Chat with LiteLLM
echo "Chatting with LiteLLM..."
CHAT_RESPONSE=$(curl -s -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-litellm-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 100
  }')

echo "Chat response: $CHAT_RESPONSE"
```

## WebSocket Support

Real-time updates for long-running operations:

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/process');

ws.onmessage = function(event) {
  const update = JSON.parse(event.data);
  console.log('Processing update:', update);
};

// Send processing request
ws.send(JSON.stringify({
  type: 'process_video',
  file_path: '/path/to/video.mp4'
}));
```

## Batch Operations

Process multiple files at once:

```http
POST /api/v1/batch/process
Content-Type: application/json

{
  "operations": [
    {
      "type": "image",
      "file_path": "/path/to/image1.jpg"
    },
    {
      "type": "text", 
      "content": "Text content here..."
    }
  ],
  "callback_url": "http://your-app.com/webhook"
}
```

