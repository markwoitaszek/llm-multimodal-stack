# API Reference

Complete API documentation for the Multimodal LLM Stack services.

## Service Endpoints

| Service | Base URL | Port | Documentation |
|---------|----------|------|---------------|
| LiteLLM Router | `http://localhost:4000` | 4000 | OpenAI-compatible |
| Multimodal Worker | `http://localhost:8001` | 8001 | `/docs` |
| Retrieval Proxy | `http://localhost:8002` | 8002 | `/docs` |
| OpenWebUI | `http://localhost:3000` | 3000 | Web interface |

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

All services return consistent error responses:

```json
{
  "detail": "Error message here",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

Common HTTP status codes:
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid API key)
- `404` - Not Found (resource doesn't exist)
- `413` - Payload Too Large (file too big)
- `422` - Unprocessable Entity (invalid data)
- `500` - Internal Server Error
- `503` - Service Unavailable (service down)

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

## SDKs and Client Libraries

### Python

```python
import openai

# Configure for LiteLLM
openai.api_base = "http://localhost:4000/v1"
openai.api_key = "sk-your-litellm-key"

# Use OpenAI client normally
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### JavaScript/Node.js

```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'http://localhost:4000/v1',
  apiKey: 'sk-your-litellm-key',
});

const response = await openai.chat.completions.create({
  model: 'gpt-3.5-turbo',
  messages: [{ role: 'user', content: 'Hello!' }],
});
```

### cURL Examples

**Search with cURL:**
```bash
curl -X POST http://localhost:8002/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning tutorial",
    "modalities": ["text", "image"],
    "limit": 5
  }'
```

**Upload image with cURL:**
```bash
curl -X POST http://localhost:8001/api/v1/process/image \
  -F "file=@/path/to/image.jpg" \
  -F "document_name=my_image.jpg"
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

