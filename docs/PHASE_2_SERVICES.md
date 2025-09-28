# Phase 2 Services Documentation

## Overview

Phase 2 of the LLM Multimodal Stack introduces three critical services that enhance the platform's capabilities with advanced search, memory management, and user management features. These services are designed to be production-ready with comprehensive test suites and enterprise-grade functionality.

## Services Overview

### 1. Search Engine Service (Port 8004)
**Purpose**: Advanced search capabilities with semantic and keyword search
**Status**: ✅ Complete with comprehensive test suite

### 2. Memory System Service (Port 8005)
**Purpose**: Conversation storage and memory management
**Status**: ✅ Complete with comprehensive test suite

### 3. User Management Service (Port 8006)
**Purpose**: Authentication, authorization, and multi-tenancy
**Status**: ✅ Complete with comprehensive test suite

---

## 🔍 Search Engine Service

### Features
- **Semantic Search**: Vector-based similarity search using embeddings
- **Keyword Search**: Full-text search with PostgreSQL
- **Hybrid Search**: Combines semantic and keyword search for optimal results
- **Advanced Filtering**: Content type, metadata, and custom filters
- **Caching**: Redis-based result caching for improved performance
- **Batch Operations**: Bulk indexing and deletion operations

### API Endpoints

#### Search Operations
```http
POST /api/v1/search
POST /api/v1/search/semantic
POST /api/v1/search/keyword
POST /api/v1/search/hybrid
```

#### Content Management
```http
POST /api/v1/index
GET /api/v1/index/{content_id}
DELETE /api/v1/index/{content_id}
POST /api/v1/index/batch
```

#### Monitoring
```http
GET /health
GET /api/v1/stats
DELETE /api/v1/cache
```

### Configuration
```yaml
# Search Engine Settings
service_port: 8004
default_search_limit: 10
max_search_limit: 100
cache_ttl: 3600
embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
embedding_dimension: 384
```

### Example Usage
```python
import httpx

# Search for content
search_request = {
    "query": "machine learning algorithms",
    "search_type": "hybrid",
    "limit": 10,
    "content_types": ["text", "document"]
}

response = httpx.post("http://localhost:8004/api/v1/search", json=search_request)
results = response.json()

# Index new content
index_request = {
    "content_id": "doc_123",
    "content": "Machine learning is a subset of artificial intelligence...",
    "content_type": "text",
    "metadata": {"author": "John Doe", "category": "AI"}
}

response = httpx.post("http://localhost:8004/api/v1/index", json=index_request)
```

---

## 🧠 Memory System Service

### Features
- **Memory Storage**: Store and retrieve different types of memories
- **Conversation Management**: Complete conversation history tracking
- **Memory Consolidation**: Automatic consolidation of related memories
- **Context Retrieval**: Get relevant context for queries
- **Multi-tenancy**: Tenant-isolated memory storage
- **Access Tracking**: Monitor memory access patterns

### Memory Types
- **Conversation**: Chat and dialogue memories
- **Knowledge**: Factual information storage
- **Context**: Contextual information for sessions
- **Fact**: Specific facts and data points
- **Preference**: User preferences and settings
- **Goal**: User goals and objectives

### API Endpoints

#### Memory Operations
```http
POST /api/v1/memories
GET /api/v1/memories/{memory_id}
PUT /api/v1/memories/{memory_id}
DELETE /api/v1/memories/{memory_id}
POST /api/v1/memories/retrieve
POST /api/v1/memories/consolidate
```

#### Conversation Management
```http
POST /api/v1/conversations
GET /api/v1/conversations/{conversation_id}
GET /api/v1/conversations/session/{session_id}
```

#### Context Retrieval
```http
POST /api/v1/context
```

### Configuration
```yaml
# Memory System Settings
service_port: 8005
max_conversation_length: 1000
max_memory_items: 10000
memory_consolidation_threshold: 100
context_window_size: 50
memory_retention_days: 30
```

### Example Usage
```python
import httpx

# Store a memory
memory_request = {
    "content": "User prefers Python for data science projects",
    "memory_type": "preference",
    "importance": "high",
    "tags": ["programming", "preference"],
    "user_id": "user_123",
    "session_id": "session_456"
}

response = httpx.post("http://localhost:8005/api/v1/memories", json=memory_request)

# Retrieve relevant memories
retrieve_request = {
    "query": "user programming preferences",
    "memory_types": ["preference", "knowledge"],
    "user_id": "user_123",
    "limit": 5
}

response = httpx.post("http://localhost:8005/api/v1/memories/retrieve", json=retrieve_request)
```

---

## 👥 User Management Service

### Features
- **Authentication**: JWT-based authentication with refresh tokens
- **Authorization**: Role-based access control (RBAC)
- **Multi-tenancy**: Tenant isolation and management
- **Session Management**: Secure session handling with activity tracking
- **Password Security**: Strong password requirements and hashing
- **Rate Limiting**: Protection against brute force attacks
- **Account Security**: Account locking and failed attempt tracking

### User Roles
- **Admin**: Full system access
- **Moderator**: Content and user management
- **User**: Standard user access
- **Guest**: Limited access

### API Endpoints

#### Authentication
```http
POST /api/v1/auth/login
POST /api/v1/auth/register
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
```

#### User Management
```http
GET /api/v1/users/me
PUT /api/v1/users/me
POST /api/v1/users/change-password
GET /api/v1/admin/users
```

#### Tenant Management
```http
POST /api/v1/tenants
GET /api/v1/tenants/{tenant_id}
PUT /api/v1/tenants/{tenant_id}
DELETE /api/v1/tenants/{tenant_id}
```

### Configuration
```yaml
# User Management Settings
service_port: 8006
access_token_expire_minutes: 30
refresh_token_expire_days: 7
password_min_length: 8
max_login_attempts: 5
lockout_duration_minutes: 15
session_timeout_minutes: 120
```

### Example Usage
```python
import httpx

# User registration
register_request = {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "tenant_id": "company_abc"
}

response = httpx.post("http://localhost:8006/api/v1/auth/register", json=register_request)

# User login
login_request = {
    "username": "john_doe",
    "password": "SecurePass123!",
    "remember_me": True
}

response = httpx.post("http://localhost:8006/api/v1/auth/login", json=login_request)
tokens = response.json()

# Use access token for authenticated requests
headers = {"Authorization": f"Bearer {tokens['access_token']}"}
response = httpx.get("http://localhost:8006/api/v1/users/me", headers=headers)
```

---

## 🧪 Testing

### Test Coverage
Each Phase 2 service includes comprehensive test suites with:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Service integration testing
- **API Tests**: Endpoint functionality testing
- **Error Handling Tests**: Exception and error scenario testing
- **Performance Tests**: Load and concurrent operation testing

### Running Tests
```bash
# Search Engine Service Tests
cd services/search-engine
pytest tests/ -v --cov=app

# Memory System Service Tests
cd services/memory-system
pytest tests/ -v --cov=app

# User Management Service Tests
cd services/user-management
pytest tests/ -v --cov=app
```

### Test Statistics
- **Search Engine**: 50+ test cases covering all functionality
- **Memory System**: 45+ test cases with comprehensive scenarios
- **User Management**: 40+ test cases including security testing

---

## 🚀 Deployment

### Docker Compose Integration
All Phase 2 services are integrated into the main docker-compose.yml:

```bash
# Start all services including Phase 2
docker-compose up -d

# Start only Phase 2 services
docker-compose up -d search-engine memory-system user-management

# Check service health
docker-compose ps
```

### Service Ports
- **Search Engine**: http://localhost:8004
- **Memory System**: http://localhost:8005
- **User Management**: http://localhost:8006

### Health Checks
All services include health check endpoints:
```bash
curl http://localhost:8004/health  # Search Engine
curl http://localhost:8005/health  # Memory System
curl http://localhost:8006/health  # User Management
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=multimodal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Qdrant Configuration
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Security Configuration
JWT_SECRET_KEY=your-secret-key-here
DEBUG=false
```

### Service Dependencies
- **PostgreSQL**: All services use PostgreSQL for data persistence
- **Redis**: Caching and session storage
- **Qdrant**: Vector storage for semantic search (Search Engine and Memory System)

---

## 📊 Monitoring and Statistics

### Service Statistics
Each service provides detailed statistics:

#### Search Engine Stats
```json
{
  "total_searches": 1250,
  "average_search_time_ms": 45.2,
  "cache_hit_rate": 0.78,
  "vector_store_points": 50000,
  "embedding_cache_size": 150
}
```

#### Memory System Stats
```json
{
  "total_memories": 10000,
  "total_conversations": 2500,
  "memory_types_distribution": {
    "conversation": 6000,
    "knowledge": 3000,
    "preference": 1000
  },
  "average_memory_size": 125.5
}
```

#### User Management Stats
```json
{
  "total_users": 150,
  "total_tenants": 5,
  "active_sessions": 45,
  "users_by_role": {
    "user": 140,
    "admin": 8,
    "moderator": 2
  },
  "login_attempts_last_hour": 12
}
```

---

## 🔐 Security Features

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **Role-Based Access**: Granular permission system
- **Session Management**: Secure session handling
- **Password Security**: Strong password requirements
- **Rate Limiting**: Protection against abuse

### Data Protection
- **Tenant Isolation**: Complete data separation
- **Encrypted Storage**: Secure password hashing
- **Access Logging**: Comprehensive audit trails
- **Input Validation**: Protection against injection attacks

---

## 🚀 Performance Optimization

### Caching Strategy
- **Redis Caching**: Result caching for improved performance
- **Embedding Cache**: Cached embeddings for faster searches
- **Session Caching**: Efficient session management

### Database Optimization
- **Connection Pooling**: Optimized database connections
- **Indexed Queries**: Fast database operations
- **Batch Operations**: Efficient bulk operations

### Scalability Features
- **Horizontal Scaling**: Multi-instance deployment support
- **Load Balancing**: Request distribution capabilities
- **Resource Management**: Efficient resource utilization

---

## 📈 Future Enhancements

### Planned Features
1. **Advanced Analytics**: Usage analytics and insights
2. **API Rate Limiting**: Advanced rate limiting strategies
3. **Webhook Support**: Event-driven integrations
4. **Advanced Search**: More sophisticated search algorithms
5. **Memory Optimization**: Enhanced memory consolidation

### Integration Opportunities
1. **External APIs**: Third-party service integrations
2. **Notification System**: Email and push notifications
3. **Audit Logging**: Comprehensive audit trails
4. **Backup & Recovery**: Automated backup systems

---

## 📚 API Documentation

### Interactive Documentation
Each service provides interactive API documentation:
- **Search Engine**: http://localhost:8004/docs
- **Memory System**: http://localhost:8005/docs
- **User Management**: http://localhost:8006/docs

### OpenAPI Specifications
All services follow OpenAPI 3.0 specifications for easy integration and testing.

---

## 🆘 Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check service logs
docker-compose logs search-engine
docker-compose logs memory-system
docker-compose logs user-management

# Check service health
curl http://localhost:8004/health
```

#### Database Connection Issues
```bash
# Verify database connectivity
docker-compose exec postgres psql -U postgres -d multimodal -c "SELECT 1;"

# Check database logs
docker-compose logs postgres
```

#### Redis Connection Issues
```bash
# Test Redis connectivity
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis
```

### Performance Issues
- **Check resource usage**: `docker stats`
- **Monitor logs**: Look for error patterns
- **Verify configuration**: Ensure proper environment variables
- **Test connectivity**: Verify inter-service communication

---

## 📞 Support

### Getting Help
1. **Check Documentation**: Review service-specific documentation
2. **Review Logs**: Examine service logs for error details
3. **Test Connectivity**: Verify service dependencies
4. **Check Configuration**: Ensure proper environment setup

### Contributing
1. **Follow Patterns**: Use existing code patterns
2. **Add Tests**: Include comprehensive test coverage
3. **Update Documentation**: Keep documentation current
4. **Performance Testing**: Verify performance impact

---

## 🎯 Success Metrics

### Implementation Success
- ✅ **3 Services Implemented**: All Phase 2 services complete
- ✅ **Comprehensive Testing**: 135+ test cases across all services
- ✅ **Production Ready**: Docker integration and health checks
- ✅ **Documentation**: Complete API and deployment documentation
- ✅ **Security**: Enterprise-grade security features

### Performance Targets
- **Search Response Time**: < 100ms for cached results
- **Memory Retrieval**: < 50ms for context retrieval
- **Authentication**: < 200ms for login operations
- **Availability**: 99.9% uptime target

---

**Phase 2 Implementation Complete** 🎉

The LLM Multimodal Stack now includes three powerful new services that significantly enhance the platform's capabilities. All services are production-ready with comprehensive test suites, security features, and monitoring capabilities.