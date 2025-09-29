# Phase 2 AI Agent Development Prompts

## 🎯 **Context & Setup**

You are working on the **LLM Multimodal Stack** project, specifically **Phase 2: Protocol & Search Enhancement**. You have access to the `development/phase-2` branch which includes Redis integration from Phase 1.

### **Current Project Architecture**
- **4 Existing Services**: LiteLLM Router, Multimodal Worker, Retrieval Proxy, AI Agents
- **Infrastructure**: PostgreSQL, Qdrant, Redis, MinIO, vLLM
- **API Pattern**: FastAPI with Pydantic models, async/await patterns
- **Docker**: Multi-service architecture with health checks

### **Your Mission**
Implement **3 new services** for Phase 2:
1. **P2.1**: Search Engine Service (Advanced search capabilities)
2. **P2.2**: Memory System Service (Persistent agent memory)
3. **P2.3**: User Management Service (Multi-tenant support)

---

## 🚀 **PROMPT 1: Search Engine Service (P2.1)**

### **Service Overview**
Create an advanced search engine service that provides semantic search, hybrid search, and intelligent query processing across all content types.

### **Technical Requirements**

#### **Service Structure**
```
services/search-engine/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── models.py          # Pydantic models
│   ├── database.py        # PostgreSQL operations
│   ├── vector_store.py    # Qdrant operations
│   ├── search_engine.py   # Core search logic
│   ├── query_processor.py # Query analysis and optimization
│   ├── cache.py          # Redis caching
│   └── api.py            # FastAPI routes
├── main.py               # Application entry point
├── requirements.txt      # Dependencies
├── Dockerfile           # Container definition
└── README.md           # Service documentation
```

#### **Configuration (app/config.py)**
```python
class Settings(BaseSettings):
    # Service settings
    service_name: str = "search-engine"
    host: str = "0.0.0.0"
    port: int = 8004
    debug: bool = False
    
    # Database settings
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "multimodal")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    # Qdrant settings
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Redis settings
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "3"))
    
    # Search settings
    default_limit: int = 20
    max_limit: int = 100
    cache_ttl: int = 3600  # 1 hour
    similarity_threshold: float = 0.7
```

#### **API Endpoints (app/api.py)**
```python
# Required endpoints:
@router.post("/api/v1/search/semantic")
@router.post("/api/v1/search/hybrid") 
@router.post("/api/v1/search/autocomplete")
@router.get("/api/v1/search/suggestions")
@router.post("/api/v1/search/filters")
@router.get("/api/v1/search/analytics")
@router.get("/health")
```

#### **Core Features to Implement**

1. **Semantic Search**
   - Vector similarity search using Qdrant
   - Query embedding generation
   - Multi-modal search (text, image, video)
   - Relevance scoring and ranking

2. **Hybrid Search**
   - Combine semantic + keyword search
   - Weighted scoring algorithms
   - Query expansion and optimization
   - Result fusion and re-ranking

3. **Query Processing**
   - Natural language query understanding
   - Intent classification
   - Query expansion and synonyms
   - Filter and facet extraction

4. **Caching & Performance**
   - Redis-based result caching
   - Query result memoization
   - Performance monitoring
   - Rate limiting

#### **Integration Points**
- **Qdrant**: Vector similarity search
- **PostgreSQL**: Metadata and search analytics
- **Redis**: Caching and session management
- **Existing Services**: Integrate with retrieval-proxy for content

### **Acceptance Criteria**
- [ ] Service starts successfully on port 8004
- [ ] All API endpoints respond correctly
- [ ] Semantic search returns relevant results
- [ ] Hybrid search combines multiple search types
- [ ] Caching reduces response times by 50%
- [ ] Health checks pass
- [ ] Docker container builds and runs
- [ ] Integration tests pass

---

## 🧠 **PROMPT 2: Memory System Service (P2.2)**

### **Service Overview**
Create a persistent memory management system for AI agents with conversation history, context retention, and knowledge base integration.

### **Technical Requirements**

#### **Service Structure**
```
services/memory-system/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── models.py          # Pydantic models
│   ├── database.py        # PostgreSQL operations
│   ├── memory_manager.py  # Core memory logic
│   ├── conversation.py    # Conversation management
│   ├── knowledge_base.py  # Knowledge storage
│   ├── cache.py          # Redis caching
│   └── api.py            # FastAPI routes
├── main.py               # Application entry point
├── requirements.txt      # Dependencies
├── Dockerfile           # Container definition
└── README.md           # Service documentation
```

#### **Configuration (app/config.py)**
```python
class Settings(BaseSettings):
    # Service settings
    service_name: str = "memory-system"
    host: str = "0.0.0.0"
    port: int = 8005
    debug: bool = False
    
    # Database settings
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "multimodal")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    # Redis settings
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "4"))
    
    # Memory settings
    max_conversation_length: int = 1000
    memory_retention_days: int = 30
    context_window_size: int = 10
    knowledge_base_limit: int = 10000
```

#### **API Endpoints (app/api.py)**
```python
# Required endpoints:
@router.post("/api/v1/memory/conversation")
@router.get("/api/v1/memory/conversation/{conversation_id}")
@router.put("/api/v1/memory/conversation/{conversation_id}")
@router.delete("/api/v1/memory/conversation/{conversation_id}")
@router.post("/api/v1/memory/knowledge")
@router.get("/api/v1/memory/knowledge")
@router.get("/api/v1/memory/context/{agent_id}")
@router.post("/api/v1/memory/summarize")
@router.get("/health")
```

#### **Core Features to Implement**

1. **Conversation Management**
   - Store and retrieve conversation history
   - Context window management
   - Conversation summarization
   - Thread-based organization

2. **Knowledge Base**
   - Persistent knowledge storage
   - Knowledge retrieval and search
   - Knowledge versioning
   - Knowledge sharing between agents

3. **Memory Operations**
   - Short-term memory (Redis)
   - Long-term memory (PostgreSQL)
   - Memory consolidation
   - Memory retrieval and ranking

4. **Context Management**
   - Agent-specific context
   - Context compression
   - Context relevance scoring
   - Context expiration

#### **Integration Points**
- **PostgreSQL**: Long-term memory storage
- **Redis**: Short-term memory and caching
- **AI Agents Service**: Memory integration
- **Search Engine**: Knowledge base search

### **Acceptance Criteria**
- [ ] Service starts successfully on port 8005
- [ ] Conversation history is stored and retrieved
- [ ] Knowledge base operations work correctly
- [ ] Context management functions properly
- [ ] Memory consolidation works
- [ ] Health checks pass
- [ ] Docker container builds and runs
- [ ] Integration tests pass

---

## 👥 **PROMPT 3: User Management Service (P2.3)**

### **Service Overview**
Create a comprehensive user management system with multi-tenant support, JWT authentication, and role-based access control.

### **Technical Requirements**

#### **Service Structure**
```
services/user-management/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── models.py          # Pydantic models
│   ├── database.py        # PostgreSQL operations
│   ├── auth.py            # Authentication logic
│   ├── user_manager.py    # User management
│   ├── tenant_manager.py  # Multi-tenant support
│   ├── cache.py          # Redis caching
│   └── api.py            # FastAPI routes
├── main.py               # Application entry point
├── requirements.txt      # Dependencies
├── Dockerfile           # Container definition
└── README.md           # Service documentation
```

#### **Configuration (app/config.py)**
```python
class Settings(BaseSettings):
    # Service settings
    service_name: str = "user-management"
    host: str = "0.0.0.0"
    port: int = 8006
    debug: bool = False
    
    # Database settings
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "multimodal")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    # Redis settings
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "5"))
    
    # JWT settings
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Security settings
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
```

#### **API Endpoints (app/api.py)**
```python
# Required endpoints:
@router.post("/api/v1/auth/register")
@router.post("/api/v1/auth/login")
@router.post("/api/v1/auth/refresh")
@router.post("/api/v1/auth/logout")
@router.get("/api/v1/users/me")
@router.put("/api/v1/users/me")
@router.get("/api/v1/users")
@router.post("/api/v1/tenants")
@router.get("/api/v1/tenants")
@router.get("/health")
```

#### **Core Features to Implement**

1. **Authentication**
   - User registration and login
   - JWT token generation and validation
   - Password hashing and verification
   - Token refresh mechanism

2. **User Management**
   - User profile management
   - User search and filtering
   - User status management
   - User preferences

3. **Multi-tenant Support**
   - Tenant creation and management
   - User-tenant associations
   - Tenant-specific configurations
   - Data isolation

4. **Security**
   - Rate limiting
   - Account lockout
   - Session management
   - Audit logging

#### **Integration Points**
- **PostgreSQL**: User and tenant data
- **Redis**: Session management and caching
- **All Services**: Authentication middleware
- **Existing Auth**: Build on current authentication

### **Acceptance Criteria**
- [ ] Service starts successfully on port 8006
- [ ] User registration and login work
- [ ] JWT tokens are generated and validated
- [ ] Multi-tenant support functions
- [ ] Security measures are implemented
- [ ] Health checks pass
- [ ] Docker container builds and runs
- [ ] Integration tests pass

---

## 🔧 **Development Guidelines**

### **Code Standards**
1. **Follow existing patterns** from multimodal-worker and retrieval-proxy
2. **Use async/await** for all I/O operations
3. **Implement proper error handling** with try/catch blocks
4. **Add comprehensive logging** using Python's logging module
5. **Use Pydantic models** for request/response validation
6. **Implement health checks** for all services

### **Testing Requirements**
1. **Unit tests** for all core functions
2. **Integration tests** for API endpoints
3. **Health check tests** for service startup
4. **Performance tests** for critical operations

### **Docker Integration**
1. **Add service to docker-compose.yml** with proper dependencies
2. **Configure health checks** for service monitoring
3. **Set up proper networking** with existing services
4. **Configure environment variables** for all settings

### **Documentation**
1. **README.md** for each service with setup instructions
2. **API documentation** using FastAPI's automatic docs
3. **Code comments** for complex logic
4. **Integration examples** for other services

---

## 🚀 **Getting Started**

1. **Checkout the branch**: `git checkout development/phase-2`
2. **Start with P2.1 (Search Engine)** - most independent
3. **Follow the service structure** exactly as specified
4. **Test each service** before moving to the next
5. **Commit frequently** with descriptive messages
6. **Ask questions** if you need clarification on any requirements

### **Priority Order**
1. **P2.1 Search Engine** (Start here - most independent)
2. **P2.2 Memory System** (Can use search engine for knowledge base)
3. **P2.3 User Management** (Critical for Phase 3 dependencies)

**Remember**: You're building production-ready services that will integrate with the existing stack. Focus on reliability, performance, and maintainability.

Good luck! 🚀
