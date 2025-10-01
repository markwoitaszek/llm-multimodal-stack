# Multimodal LLM Stack - Deployment Matrix

## Environment & Service Deployment Matrix

### Overview
This matrix defines which services are deployed in each environment, their configurations, and deployment characteristics.

## Service Categories

| Category | Services | Purpose |
|----------|----------|---------|
| **Core** | PostgreSQL, Redis, Qdrant, MinIO | Essential infrastructure services |
| **Inference** | vLLM, LiteLLM | AI model serving and API gateway |
| **Multimodal** | Multimodal Worker, Retrieval Proxy | Content processing and search |
| **AI Services** | AI Agents, Memory System, Search Engine, User Management | AI orchestration and management |
| **UI & Workflow** | OpenWebUI, n8n, n8n Monitoring | User interfaces and workflow automation |
| **Monitoring** | ELK Stack, Prometheus, Grafana | Observability and logging |

## Environment Deployment Matrix

### Development Environment
**Purpose**: Local development and testing
**Profile**: `development`
**Compose Files**: `compose.yml`, `compose.development.yml`

| Service | Deployed | Port | Configuration | Notes |
|---------|----------|------|---------------|-------|
| **Core Services** |
| PostgreSQL | ✅ | 5432 | Debug: true, Log: DEBUG | Local development database |
| Redis | ✅ | 6379 | Debug: true, Log: DEBUG | Caching and session storage |
| Qdrant | ✅ | 6333/6334 | Debug: true, Log: DEBUG | Vector database for embeddings |
| MinIO | ✅ | 9000/9002 | Debug: true, Log: DEBUG | Object storage for files |
| **Inference Services** |
| vLLM | ✅ | 8000 | GPU: Optional, Model: microsoft/DialoGPT-medium | AI model server |
| LiteLLM | ✅ | 4000 | Workers: 1, Debug: true | API gateway and proxy |
| **Multimodal Services** |
| Multimodal Worker | ✅ | 8001 | Debug: true, GPU: Optional | Content processing |
| Retrieval Proxy | ✅ | 8002 | Debug: true | Search and retrieval |
| **AI Services** | ❌ | - | - | Not deployed in development |
| **UI & Workflow** | ❌ | - | - | Not deployed in development |
| **Monitoring** | ❌ | - | - | Not deployed in development |

**Deployment Command**: `make start-dev`

### Staging Environment
**Purpose**: Integration testing and validation
**Profile**: `staging`
**Compose Files**: `compose.yml`, `compose.staging.yml`

| Service | Deployed | Port | Configuration | Notes |
|---------|----------|------|---------------|-------|
| **Core Services** |
| PostgreSQL | ✅ | 5432 | Debug: false, Log: INFO | Staging database |
| Redis | ✅ | 6379 | Debug: false, Log: INFO | Production-like caching |
| Qdrant | ✅ | 6333/6334 | Debug: false, Log: INFO | Vector database |
| MinIO | ✅ | 9000/9002 | Debug: false, Log: INFO | Object storage |
| **Inference Services** |
| vLLM | ✅ | 8000 | GPU: Recommended, Production model | AI model server |
| LiteLLM | ✅ | 4000 | Workers: 2, Debug: false | API gateway |
| **Multimodal Services** |
| Multimodal Worker | ✅ | 8001 | Debug: false, GPU: Recommended | Content processing |
| Retrieval Proxy | ✅ | 8002 | Debug: false | Search and retrieval |
| **AI Services** |
| AI Agents | ✅ | 8003 | Debug: false, Log: INFO | AI orchestration |
| Memory System | ✅ | 8005 | Debug: false, Log: INFO | Persistent memory |
| Search Engine | ✅ | 8004 | Debug: false, Log: INFO | Query processing |
| User Management | ✅ | 8006 | Debug: false, Log: INFO | Authentication |
| **UI & Workflow** |
| OpenWebUI | ✅ | 3030 | Debug: false | Web interface |
| n8n | ✅ | 5678 | Debug: false | Workflow automation |
| n8n Monitoring | ✅ | 8008 | Debug: false | Workflow monitoring |
| **Monitoring** |
| ELK Stack | ✅ | 5601/9200/9600 | Debug: false | Logging and analytics |

**Deployment Command**: `docker compose -f compose.yml -f compose.staging.yml --profile services --profile monitoring up -d`

### Production Environment
**Purpose**: Production deployment with high availability
**Profile**: `production`
**Compose Files**: `compose.yml`, `compose.production.yml`

| Service | Deployed | Port | Configuration | Notes |
|---------|----------|------|---------------|-------|
| **Core Services** |
| PostgreSQL | ✅ | 5432 | Debug: false, Log: WARN, Resources: Limited | Production database |
| Redis | ✅ | 6379 | Debug: false, Log: WARN, Resources: Limited | Production caching |
| Qdrant | ✅ | 6333/6334 | Debug: false, Log: WARN, Resources: Limited | Vector database |
| MinIO | ✅ | 9000/9002 | Debug: false, Log: WARN, Resources: Limited | Object storage |
| **Inference Services** |
| vLLM | ✅ | 8000 | GPU: Required, Production model, Resources: High | AI model server |
| LiteLLM | ✅ | 4000 | Workers: 4, Debug: false, Resources: Medium | API gateway |
| **Multimodal Services** |
| Multimodal Worker | ✅ | 8001 | Debug: false, GPU: Required, Resources: High | Content processing |
| Retrieval Proxy | ✅ | 8002 | Debug: false, Resources: Medium | Search and retrieval |
| **AI Services** |
| AI Agents | ✅ | 8003 | Debug: false, Log: WARN, Resources: Medium | AI orchestration |
| Memory System | ✅ | 8005 | Debug: false, Log: WARN, Resources: Medium | Persistent memory |
| Search Engine | ✅ | 8004 | Debug: false, Log: WARN, Resources: Medium | Query processing |
| User Management | ✅ | 8006 | Debug: false, Log: WARN, Resources: Medium | Authentication |
| **UI & Workflow** |
| OpenWebUI | ❌ | - | - | Not deployed in production |
| n8n | ✅ | 5678 | Debug: false, Resources: Medium | Workflow automation |
| n8n Monitoring | ✅ | 8008 | Debug: false, Resources: Medium | Workflow monitoring |
| **Monitoring** |
| ELK Stack | ✅ | 5601/9200/9600 | Debug: false, Resources: High | Logging and analytics |
| Prometheus | ✅ | 9090 | Debug: false, Resources: Medium | Metrics collection |
| Grafana | ✅ | 3000 | Debug: false, Resources: Medium | Dashboards |

**Deployment Command**: `docker compose -f compose.yml -f compose.production.yml --profile services --profile monitoring up -d`

## Specialized Deployment Profiles

### GPU-Optimized Environment
**Purpose**: High-performance AI inference with GPU acceleration
**Compose Files**: `compose.yml`, `compose.gpu.yml`, `compose.production.yml`

| Configuration | Value |
|---------------|-------|
| GPU Memory Utilization | 0.9 |
| Tensor Parallelism | Enabled |
| Model Loading | Optimized |
| Batch Processing | Enhanced |
| Resource Limits | GPU-specific |

**Deployment Command**: `make start-gpu`

### Monitoring Environment
**Purpose**: Comprehensive observability and logging
**Compose Files**: `compose.yml`, `compose.elk.yml`, `compose.monitoring.yml`

| Service | Deployed | Purpose |
|---------|----------|---------|
| ELK Stack | ✅ | Centralized logging |
| Prometheus | ✅ | Metrics collection |
| Grafana | ✅ | Visualization |
| n8n Monitoring | ✅ | Workflow monitoring |
| OpenWebUI | ✅ | Interface monitoring |

**Deployment Command**: `make start-monitoring`

## Environment-Specific Configurations

### Resource Allocation

| Environment | CPU | Memory | GPU | Storage |
|-------------|-----|--------|-----|---------|
| Development | 2 cores | 4GB | Optional | 20GB |
| Staging | 4 cores | 8GB | Recommended | 50GB |
| Production | 8+ cores | 16GB+ | Required | 100GB+ |

### Security Configuration

| Environment | TLS | Authentication | Secrets | Network |
|-------------|-----|----------------|---------|---------|
| Development | ❌ | Basic | Local files | Bridge |
| Staging | ✅ | JWT | OpenBao | Isolated |
| Production | ✅ | JWT + RBAC | OpenBao | Isolated + Firewall |

### Scaling Configuration

| Environment | Replicas | Load Balancing | Auto-scaling |
|-------------|----------|----------------|--------------|
| Development | 1 | ❌ | ❌ |
| Staging | 2-3 | ✅ | Manual |
| Production | 3+ | ✅ | Auto |

## Deployment Commands Summary

| Environment | Command | Description |
|-------------|---------|-------------|
| Development | `make start-dev` | Start development environment |
| Staging | `make start-staging` | Start staging environment |
| Production | `make start-prod` | Start production environment |
| GPU | `make start-gpu` | Start GPU-optimized environment |
| Monitoring | `make start-monitoring` | Start monitoring environment |
| Custom | `docker compose -f compose.yml -f compose.custom.yml --profile custom up -d` | Custom deployment |

## Ansible Deployment Matrix

### Target Hosts

| Environment | Hosts | Purpose |
|-------------|-------|---------|
| Development | llm-dev-01 | Local development |
| Staging | llm-staging-01 | Integration testing |
| Production | llm-prod-01, llm-prod-02 | Production deployment |

### Deployment Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `deploy-with-ansible.sh` | Automated deployment | `./scripts/deploy-with-ansible.sh [env]` |
| `verify-deployment.sh` | Deployment validation | `./scripts/verify-deployment.sh` |
| `test-migration.sh` | Migration testing | `./scripts/test-migration.sh` |

## Service Dependencies

### Core Dependencies
- All services depend on **Core Services** (PostgreSQL, Redis, Qdrant, MinIO)
- **Inference Services** are prerequisites for **Multimodal Services**
- **AI Services** require **Inference Services** and **Multimodal Services**
- **UI & Workflow** services depend on **AI Services**

### Startup Order
1. **Core Services** (PostgreSQL, Redis, Qdrant, MinIO)
2. **Inference Services** (vLLM, LiteLLM)
3. **Multimodal Services** (Multimodal Worker, Retrieval Proxy)
4. **AI Services** (AI Agents, Memory System, Search Engine, User Management)
5. **UI & Workflow** (OpenWebUI, n8n, n8n Monitoring)
6. **Monitoring** (ELK Stack, Prometheus, Grafana)

## Health Check Configuration

| Service | Check Type | Interval | Timeout | Retries |
|---------|------------|----------|---------|---------|
| PostgreSQL | pg_isready | 30s | 10s | 3 |
| Redis | redis-cli ping | 30s | 10s | 3 |
| Qdrant | pidof qdrant | 30s | 10s | 3 |
| vLLM | HTTP GET /health | 60s | 30s | 5 |
| LiteLLM | HTTP GET /health | 30s | 10s | 3 |
| All AI Services | HTTP GET /health | 30s | 10s | 3 |

This deployment matrix provides a comprehensive overview of how services are deployed across different environments, ensuring consistency and proper configuration management.