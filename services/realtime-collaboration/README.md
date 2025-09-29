# Real-Time Collaboration Service

## Overview

The Real-Time Collaboration Service provides WebSocket-based real-time communication, live agent execution monitoring, and collaborative workspace features for the Multimodal LLM Stack.

## Features

- **WebSocket Communication**: Real-time bidirectional communication between clients and servers
- **Live Agent Monitoring**: Real-time tracking of agent executions, status updates, and performance metrics
- **Collaborative Workspaces**: Multi-user collaboration with shared workspaces and real-time updates
- **Event Broadcasting**: System-wide event broadcasting for notifications and updates
- **Connection Management**: Robust connection handling with reconnection and heartbeat mechanisms
- **Message Queuing**: Reliable message delivery with queuing and persistence
- **Authentication**: Secure WebSocket connections with JWT authentication
- **Rate Limiting**: Protection against abuse with configurable rate limits

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Client    │    │   Mobile App     │    │   VS Code       │
│                 │    │                  │    │   Extension     │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                       │
          │ WebSocket            │ WebSocket             │ WebSocket
          │                      │                       │
          └──────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │  Real-Time Collaboration  │
                    │         Service           │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │    Message Queue          │
                    │    (Redis)                │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │    Database               │
                    │    (PostgreSQL)           │
                    └───────────────────────────┘
```

## API Endpoints

### WebSocket Endpoints

- `ws://localhost:3006/ws` - Main WebSocket endpoint
- `ws://localhost:3006/ws/agents` - Agent-specific WebSocket endpoint
- `ws://localhost:3006/ws/workspaces` - Workspace collaboration WebSocket endpoint

### REST Endpoints

- `GET /health` - Health check
- `GET /status` - Service status
- `GET /connections` - Active connections
- `GET /workspaces` - List workspaces
- `POST /workspaces` - Create workspace
- `GET /workspaces/{id}` - Get workspace details
- `POST /workspaces/{id}/join` - Join workspace
- `POST /workspaces/{id}/leave` - Leave workspace
- `GET /workspaces/{id}/users` - Get workspace users
- `GET /agents/status` - Get agent status
- `POST /agents/{id}/subscribe` - Subscribe to agent updates
- `POST /agents/{id}/unsubscribe` - Unsubscribe from agent updates

## WebSocket Message Types

### Agent Messages

```json
{
  "type": "agent_execution_start",
  "data": {
    "agent_id": "agent-123",
    "task": "Analyze market trends",
    "user_id": "user-456",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

```json
{
  "type": "agent_execution_update",
  "data": {
    "agent_id": "agent-123",
    "status": "running",
    "progress": 60,
    "current_step": "Processing data",
    "timestamp": "2024-01-01T12:01:00Z"
  }
}
```

```json
{
  "type": "agent_execution_complete",
  "data": {
    "agent_id": "agent-123",
    "status": "completed",
    "result": "Analysis complete",
    "execution_time": 120,
    "timestamp": "2024-01-01T12:02:00Z"
  }
}
```

### Workspace Messages

```json
{
  "type": "user_joined",
  "data": {
    "workspace_id": "workspace-789",
    "user_id": "user-456",
    "username": "john_doe",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

```json
{
  "type": "user_left",
  "data": {
    "workspace_id": "workspace-789",
    "user_id": "user-456",
    "username": "john_doe",
    "timestamp": "2024-01-01T12:05:00Z"
  }
}
```

```json
{
  "type": "workspace_update",
  "data": {
    "workspace_id": "workspace-789",
    "update_type": "agent_added",
    "agent_id": "agent-123",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## Configuration

### Environment Variables

- `ENVIRONMENT` - Environment (development, staging, production)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `PORT` - Service port (default: 3006)
- `REDIS_URL` - Redis connection URL
- `DATABASE_URL` - PostgreSQL connection URL
- `JWT_SECRET` - JWT secret for authentication
- `AI_AGENTS_URL` - AI Agents service URL
- `IDE_BRIDGE_URL` - IDE Bridge service URL
- `MAX_CONNECTIONS` - Maximum WebSocket connections
- `HEARTBEAT_INTERVAL` - Heartbeat interval in seconds
- `MESSAGE_QUEUE_SIZE` - Maximum message queue size

## Quick Start

1. **Start the service**:
   ```bash
   docker-compose -f docker-compose.realtime-collaboration.yml up -d
   ```

2. **Connect via WebSocket**:
   ```javascript
   const ws = new WebSocket('ws://localhost:3006/ws');
   
   ws.onopen = () => {
     console.log('Connected to real-time collaboration service');
   };
   
   ws.onmessage = (event) => {
     const message = JSON.parse(event.data);
     console.log('Received:', message);
   };
   ```

3. **Subscribe to agent updates**:
   ```javascript
   ws.send(JSON.stringify({
     type: 'subscribe_agent',
     data: { agent_id: 'agent-123' }
   }));
   ```

4. **Join a workspace**:
   ```javascript
   ws.send(JSON.stringify({
     type: 'join_workspace',
     data: { workspace_id: 'workspace-789' }
   }));
   ```

## Development

### Prerequisites

- Python 3.11+
- Redis
- PostgreSQL
- Docker and Docker Compose

### Local Development

1. **Install dependencies**:
   ```bash
   cd services/realtime-collaboration
   pip install -r requirements.txt
   ```

2. **Start Redis and PostgreSQL**:
   ```bash
   docker-compose -f docker-compose.realtime-collaboration.yml up -d redis postgres
   ```

3. **Run the service**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 3006 --reload
   ```

### Testing

```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=app tests/
```

## Monitoring

### Health Checks

- **Service Health**: `GET /health`
- **WebSocket Health**: `GET /ws/health`
- **Database Health**: `GET /health/database`
- **Redis Health**: `GET /health/redis`

### Metrics

- Active WebSocket connections
- Message throughput
- Agent execution monitoring
- Workspace activity
- Error rates
- Response times

## Security

- JWT-based authentication for WebSocket connections
- Rate limiting to prevent abuse
- Input validation and sanitization
- Secure WebSocket connections (WSS)
- CORS configuration
- Connection timeout handling

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check if the service is running
   - Verify the WebSocket URL
   - Check firewall settings

2. **Authentication Errors**
   - Verify JWT token validity
   - Check JWT secret configuration
   - Ensure proper token format

3. **Message Delivery Issues**
   - Check Redis connection
   - Verify message queue status
   - Check network connectivity

### Logs

```bash
# View service logs
docker logs realtime-collaboration

# View WebSocket logs
docker logs realtime-collaboration | grep "WebSocket"

# View error logs
docker logs realtime-collaboration | grep "ERROR"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License