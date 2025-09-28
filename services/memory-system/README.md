# Memory System Service

A persistent memory management system for AI agents with conversation history, context retention, and knowledge base integration.

## Overview

The Memory System Service provides comprehensive memory management capabilities for AI agents, including:

- **Conversation Management**: Store and retrieve conversation history with context window management
- **Knowledge Base**: Persistent knowledge storage with search and categorization
- **Memory Consolidation**: Automatic summarization and knowledge extraction from conversations
- **Context Management**: Agent-specific context with relevance scoring and compression
- **Caching**: Redis-based caching for improved performance

## Features

### Core Capabilities

- **Conversation Storage**: Thread-based conversation organization with message history
- **Knowledge Persistence**: Categorized knowledge base with search capabilities
- **Memory Consolidation**: Automatic conversation summarization and knowledge extraction
- **Context Retrieval**: Intelligent context assembly for AI agents
- **Performance Optimization**: Multi-level caching with Redis

### API Endpoints

#### Conversation Management
- `POST /api/v1/memory/conversation` - Create conversation
- `GET /api/v1/memory/conversation/{id}` - Get conversation
- `PUT /api/v1/memory/conversation/{id}` - Update conversation
- `DELETE /api/v1/memory/conversation/{id}` - Delete conversation
- `GET /api/v1/memory/conversations/{agent_id}` - List conversations

#### Message Management
- `POST /api/v1/memory/conversation/{id}/message` - Add message
- `GET /api/v1/memory/conversation/{id}/messages` - Get messages

#### Knowledge Base
- `POST /api/v1/memory/knowledge` - Create knowledge entry
- `GET /api/v1/memory/knowledge/{id}` - Get knowledge entry
- `PUT /api/v1/memory/knowledge/{id}` - Update knowledge entry
- `DELETE /api/v1/memory/knowledge/{id}` - Delete knowledge entry
- `GET /api/v1/memory/knowledge` - List knowledge entries
- `POST /api/v1/memory/knowledge/search` - Search knowledge

#### Context & Memory
- `POST /api/v1/memory/context/{agent_id}` - Get agent context
- `POST /api/v1/memory/summarize` - Consolidate memory
- `GET /api/v1/memory/stats` - Get memory statistics

#### System Management
- `GET /health` - Health check
- `GET /api/v1/memory/cache/stats` - Cache statistics
- `DELETE /api/v1/memory/cache/clear` - Clear cache

## Configuration

### Environment Variables

```bash
# Service Configuration
SERVICE_NAME=memory-system
HOST=0.0.0.0
PORT=8005
DEBUG=false

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=multimodal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=4

# Memory Settings
MAX_CONVERSATION_LENGTH=1000
MEMORY_RETENTION_DAYS=30
CONTEXT_WINDOW_SIZE=10
KNOWLEDGE_BASE_LIMIT=10000
```

## Quick Start

### Docker Compose

The Memory System Service is included in the main docker-compose.yml file:

```bash
# Start all services including memory-system
docker-compose up -d

# Check service status
docker-compose ps memory-system

# View logs
docker-compose logs -f memory-system
```

### Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   export POSTGRES_HOST=localhost
   export POSTGRES_PORT=5432
   export POSTGRES_DB=multimodal
   export POSTGRES_USER=postgres
   export POSTGRES_PASSWORD=postgres
   export REDIS_HOST=localhost
   export REDIS_PORT=6379
   export REDIS_DB=4
   ```

3. **Run the Service**
   ```bash
   python main.py
   ```

## API Usage Examples

### Creating a Conversation

```python
import httpx

async def create_conversation(agent_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8005/api/v1/memory/conversation",
            json={
                "agent_id": agent_id,
                "title": "User Support Session",
                "metadata": {"session_type": "support"}
            }
        )
        return response.json()
```

### Adding Messages

```python
async def add_message(conversation_id: str, role: str, content: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8005/api/v1/memory/conversation/{conversation_id}/message",
            json={
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "metadata": {"timestamp": "2024-01-01T00:00:00Z"}
            }
        )
        return response.json()
```

### Getting Agent Context

```python
async def get_agent_context(agent_id: str, conversation_id: str = None):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8005/api/v1/memory/context/{agent_id}",
            json={
                "agent_id": agent_id,
                "conversation_id": conversation_id,
                "max_messages": 10,
                "include_knowledge": True,
                "include_summaries": True
            }
        )
        return response.json()
```

## Architecture

### Components

1. **DatabaseManager**: PostgreSQL operations and connection pooling
2. **CacheManager**: Redis caching and invalidation
3. **ConversationManager**: Conversation and message management
4. **KnowledgeManager**: Knowledge base operations and search
5. **MemoryManager**: Core memory orchestration and consolidation

### Data Flow

1. **Input**: API requests for memory operations
2. **Processing**: Business logic in managers
3. **Storage**: PostgreSQL for persistence, Redis for caching
4. **Output**: Structured responses with memory data

## Integration

### With AI Agents Service

The Memory System Service integrates seamlessly with the AI Agents Service:

1. **Context Retrieval**: Agents request context before processing
2. **Memory Storage**: Conversations and knowledge are automatically stored
3. **Consolidation**: Regular memory consolidation maintains performance
4. **Knowledge Sharing**: Knowledge can be shared between agents

### Service Dependencies

- **PostgreSQL**: Long-term memory storage
- **Redis**: Short-term memory and caching
- **AI Agents Service**: Memory integration
- **Search Engine**: Knowledge base search

## Health Monitoring

The service provides comprehensive health checks at `/health`:

```json
{
  "status": "healthy",
  "service": "memory-system",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "database_status": "healthy",
  "redis_status": "healthy",
  "memory_stats": {
    "total_conversations": 150,
    "total_messages": 5000,
    "total_knowledge_items": 200,
    "active_conversations": 25
  }
}
```

## License

This service is part of the LLM Multimodal Stack project.