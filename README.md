# LLM Multimodal Stack - Phase-6A Production Ready

A comprehensive, production-ready multimodal LLM stack with advanced features including secrets management, monitoring, testing, and performance optimization.

## 🎯 **What's New in Phase-6A**

Phase-6A represents a complete production transformation with:
- ✅ **Production Secrets Management** - Encrypted secrets with rotation
- ✅ **Comprehensive Monitoring** - ELK stack, Prometheus, Grafana
- ✅ **Professional Testing** - Allure reporting, JMeter performance testing
- ✅ **Kubernetes Ready** - Helm charts and K8s manifests
- ✅ **Auto-scaling** - Production-grade scaling and optimization
- ✅ **Security Hardened** - Role-based access, audit logging

## 🚀 **Quick Start**

### **Prerequisites**
- Docker & Docker Compose
- Python 3.13+
- 8GB+ RAM, 50GB+ disk space
- NVIDIA GPU (optional, for acceleration)

### **1. Setup Secrets Management**
```bash
# Generate secure secrets and environment files
python3 setup_secrets.py
```

### **2. Start Development Environment**
```bash
# Start with automatic Docker cleanup and health checks
./start-environment.sh dev
```

### **3. Access Services**
- **OpenWebUI**: http://localhost:3030
- **LiteLLM API**: http://localhost:4000
- **Multimodal Worker**: http://localhost:8001
- **Retrieval Proxy**: http://localhost:8002
- **AI Agents**: http://localhost:8003
- **Search Engine**: http://localhost:8004
- **Memory System**: http://localhost:8005
- **User Management**: http://localhost:8006
- **n8n Workflow**: http://localhost:5678
- **n8n Monitoring**: http://localhost:8008
- **API Lifecycle Management**: http://localhost:8000
- **Analytics Dashboard**: http://localhost:8080
- **Kibana**: http://localhost:5601
- **Grafana**: http://localhost:3001

## 🏗️ **Services Overview**

### **Core Infrastructure Services**
- **PostgreSQL**: Primary database for all services
- **Redis**: Caching and session storage
- **Qdrant**: Vector database for semantic search
- **MinIO**: Object storage for files and artifacts

### **AI & ML Services**
- **vLLM**: High-performance LLM inference server
- **LiteLLM**: Universal API router for multiple LLM providers
- **Multimodal Worker**: Image, video, and text processing
- **Retrieval Proxy**: Multimodal search and retrieval
- **AI Agents**: Intelligent agent framework with tools and memory
- **Search Engine**: Advanced semantic search capabilities
- **Memory System**: Persistent memory and context management

### **User Interface & Management**
- **OpenWebUI**: Modern web interface for LLM interactions
- **User Management**: Authentication, authorization, and user profiles
- **n8n**: Workflow automation and orchestration
- **n8n Monitoring**: Workflow monitoring and analytics

### **Development & Operations**
- **API Lifecycle Management**: Version control, deployment, and monitoring
- **Analytics Engine**: Real-time analytics and insights
- **Performance Monitor**: System and application performance tracking
- **Security Auditor**: Comprehensive security scanning and compliance
- **Authentication Manager**: JWT-based auth with RBAC and MFA

### **Monitoring & Observability**
- **ELK Stack**: Elasticsearch, Logstash, Kibana, Filebeat
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Metrics visualization and dashboards
- **Allure**: Test reporting and analytics

### **Development Tools**
- **Python SDK**: Comprehensive Python client library
- **JavaScript SDK**: Browser and Node.js client library
- **IDE Bridge**: VS Code extension with real-time collaboration
- **MCP Integration**: Model Context Protocol support

## 🏗️ **Deployment Options**

### **Unified Schema Structure (Recommended)**
The stack now uses a **unified schema approach** where all Docker Compose files are generated from a single source of truth (`schemas/compose-schema.yaml`):

```bash
# Generate all compose files from schema
make generate-compose

# Core services only
make start-dev

# Full staging environment
make start-staging

# Production deployment with resource limits
make start-prod

# GPU-optimized deployment
make start-gpu

# Monitoring environment with ELK stack
make start-monitoring
```

### **Normalized Compose Structure**
The generated compose files use a normalized structure with profiles for flexible deployments:

```bash
# Core services only
docker compose up -d

# With monitoring tools
docker compose --profile monitoring up -d

# With all services
docker compose --profile services --profile monitoring up -d

# Production deployment with resource limits
docker compose -f compose.yml -f compose.production.yml up -d

# GPU-optimized deployment
docker compose -f compose.yml -f compose.gpu.yml up -d
```

### **Legacy Environment Scripts**
| Environment | Command | Purpose |
|-------------|---------|---------|
| **Development** | `./start-environment.sh dev` | Core services for development |
| **Staging** | `./start-environment.sh staging` | Pre-production testing |
| **Production** | `./start-environment.sh production` | Full production stack |
| **Testing** | `./start-environment.sh testing` | Allure test reporting |
| **Performance** | `./start-environment.sh performance` | JMeter load testing |
| **Monitoring** | `./start-environment.sh monitoring` | ELK stack for observability |

> **📋 See [Compose Deployment Guide](docs/COMPOSE_DEPLOYMENT_GUIDE.md) and [Unified Schema Guide](docs/UNIFIED_SCHEMA_GUIDE.md) for detailed information about the unified schema approach and control plane integration.**

## 🏗️ **Unified Schema Architecture**

### **Single Source of Truth**
All Docker Compose configurations are generated from a unified schema:

- **Schema File**: `schemas/compose-schema.yaml` - Single source of truth for all services
- **Generator Script**: `scripts/compose-generator.py` - Converts schema to compose files
- **Makefile**: Easy commands for schema management and deployment

### **Generated Files**
The schema automatically generates:
- `compose.yml` - Base compose file with core services
- `compose.development.yml` - Development environment
- `compose.staging.yml` - Staging environment  
- `compose.production.yml` - Production environment
- `compose.gpu.yml` - GPU-optimized environment
- `compose.monitoring.yml` - Monitoring environment
- Profile-specific compose files (services, elk, n8n-monitoring)

### **Benefits**
- ✅ **No Duplication**: Single definition for each service
- ✅ **Consistency**: Same services across all environments
- ✅ **Maintainability**: Change once, apply everywhere
- ✅ **Validation**: Schema validation prevents configuration errors
- ✅ **Flexibility**: Environment-specific overrides and profiles

## 🔐 **Control Plane Integration**

### **Environment Templates**
The stack now includes Jinja2 environment templates for seamless integration with the Ops control plane:

- **Template Location**: `env-templates/` directory
- **Format**: Jinja2 templates (`.env.j2`) with OpenBao integration
- **Secrets**: All secrets prefixed with `vault_` for OpenBao compatibility
- **Rendering**: Templates render to `/etc/llm-ms/.env.d/` directory

### **Available Templates**
- `core.env.j2` - Core services (postgres, redis, minio, qdrant)
- `vllm.env.j2` - vLLM inference server
- `litellm.env.j2` - LiteLLM proxy service
- `multimodal-worker.env.j2` - Multimodal worker service
- `retrieval-proxy.env.j2` - Retrieval proxy service
- `ai-agents.env.j2` - AI agents service
- `memory-system.env.j2` - Memory system service
- `search-engine.env.j2` - Search engine service
- `user-management.env.j2` - User management service
- `openwebui.env.j2` - OpenWebUI interface
- `n8n.env.j2` - n8n workflow platform
- `n8n-monitoring.env.j2` - n8n monitoring service
- `master.env.j2` - Combined template for all services

### **Ansible Integration Example**
```yaml
- name: Render environment templates
  template:
    src: "env-templates/{{ item }}.j2"
    dest: "/etc/llm-ms/.env.d/{{ item | regex_replace('\\.env\\.j2$', '.env') }}"
    mode: '0600'
  loop:
    - core.env.j2
    - vllm.env.j2
    - litellm.env.j2
```

> **📋 See [Environment Templates README](env-templates/README.md) and [Secrets Mapping](env-templates/secrets-mapping.md) for detailed integration information.**

## 🔐 **Secrets Management**

Phase-6A includes a production-grade secrets management system:

### **Generated Files**
- `.env.development` - Development environment variables
- `secrets/.env.development.json` - Encrypted secrets storage
- `docker-compose.development.override.yml` - Docker overrides
- `k8s-secrets-development.yaml` - Kubernetes secrets template

### **Features**
- **21 secure secrets** automatically generated
- **Encrypted storage** with proper permissions
- **Environment-specific** configurations
- **Secret rotation** policies
- **Audit logging** and compliance

## 📊 **Monitoring & Observability**

### **ELK Stack**
- **Elasticsearch**: Log storage and search
- **Logstash**: Log processing
- **Kibana**: Log visualization (http://localhost:5601)
- **Filebeat**: Log shipping and collection

### **Prometheus + Grafana**
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization (http://localhost:3001)

### **Advanced Analytics Engine**
- **Real-time Analytics**: Comprehensive data collection and processing
- **Performance Metrics**: System health monitoring with thresholds
- **User Behavior Analytics**: Session tracking and usage patterns
- **Insights Generation**: Automated analysis and recommendations
- **Data Export**: JSON format with historical data retention

### **Performance Monitoring**
- **System Metrics**: CPU, memory, disk I/O, network monitoring
- **Application Metrics**: API response times, model inference times
- **Alert System**: Configurable thresholds with callback support
- **Statistical Analysis**: Mean, median, P95, P99 percentiles
- **Real-time Dashboards**: Live performance visualization

## 🧪 **Testing Framework**

### **Allure Test Reporting**
```bash
# Run comprehensive tests
python3 scripts/run_tests_with_allure.py --type all --serve
```
- **Reports**: http://localhost:8080
- **Results**: http://localhost:5050

### **JMeter Performance Testing**
```bash
# Run performance tests
python3 scripts/run_jmeter_tests.py --test all
```

### **Comprehensive Test Suite**
- **Unit Tests**: Individual component testing
- **Integration Tests**: Service interaction testing
- **API Tests**: Endpoint validation and testing
- **Performance Tests**: Load and stress testing
- **Security Tests**: Vulnerability scanning and validation
- **End-to-End Tests**: Complete workflow testing

## 🔐 **Security & Authentication**

### **Authentication System**
- **JWT-based Authentication**: Secure token management
- **Role-based Access Control**: Admin, Developer, Operator, Viewer roles
- **Multi-factor Authentication**: TOTP support with QR code generation
- **Session Management**: Secure session handling with expiration
- **Password Policies**: Strong password requirements and rotation
- **Account Lockout**: Protection against brute force attacks

### **Security Audit Framework**
- **Comprehensive Security Scanning**: Automated vulnerability detection
- **Compliance Checking**: OWASP Top 10, CIS Docker Benchmark, NIST Cybersecurity Framework
- **Configuration Validation**: Security misconfiguration detection
- **Dependency Scanning**: Vulnerable package identification
- **Container Security**: Docker security best practices validation
- **Network Security**: Port exposure and firewall configuration checks

### **Secrets Management**
- **Encrypted Storage**: Fernet encryption for sensitive data
- **Environment Variable Validation**: Secure credential management
- **Secret Rotation**: Automated key rotation policies
- **Audit Logging**: Complete security event tracking

## 🚀 **Production Deployment**

### **Docker Compose**
```bash
# Production environment
./start-environment.sh production
```

### **Kubernetes**
```bash
# Deploy to Kubernetes
kubectl apply -f k8s-secrets-development.yaml
kubectl apply -f deployment/k8s/
```

### **Helm Charts**
```bash
# Deploy with Helm
helm install multimodal deployment/helm/multimodal/
```

## 🔌 **API Lifecycle Management**

### **Version Management**
- **API Versioning**: Semantic versioning with compatibility checking
- **Change Tracking**: Detailed change logs with impact assessment
- **Migration Strategies**: Automated migration path generation
- **Deprecation Policies**: Structured API deprecation workflows

### **Deployment Management**
- **Environment Management**: Development, staging, production environments
- **Deployment Strategies**: Blue-green, canary, rolling deployments
- **Rollback Capabilities**: Automated rollback with reason tracking
- **Deployment Logs**: Comprehensive deployment logging and monitoring

### **Configuration Management**
- **Environment-specific Configs**: Secure configuration per environment
- **Secret Management**: Encrypted secret storage and rotation
- **Configuration Validation**: Schema validation and security checks
- **Template System**: Jinja2 templates for dynamic configuration

### **Monitoring & Alerting**
- **Health Checks**: Automated service health monitoring
- **Alert Rules**: Configurable alerting with severity levels
- **Metrics Collection**: Performance and usage metrics
- **Incident Management**: Alert acknowledgment and resolution tracking

## 🔗 **API Connector Ecosystem**

### **Universal Connector Framework**
- **Multi-protocol Support**: REST, GraphQL, WebSocket, gRPC
- **Authentication Methods**: API Key, OAuth2, Basic Auth, Bearer Token
- **Data Transformation**: Field mapping and format conversion
- **Rate Limiting**: Built-in rate limiting and throttling
- **Error Handling**: Comprehensive error handling with retry logic

### **Connector Registry**
- **Dynamic Registration**: Runtime connector registration and management
- **Health Monitoring**: Connector health and performance tracking
- **Configuration Management**: Centralized connector configuration
- **Metrics Collection**: Detailed connector usage and performance metrics

### **Pre-built Connectors**
- **Database Connectors**: PostgreSQL, MongoDB, Redis, Elasticsearch
- **Cloud Service Connectors**: AWS, Azure, GCP services
- **API Connectors**: RESTful APIs, GraphQL endpoints
- **Message Queue Connectors**: RabbitMQ, Kafka, Redis Streams

## 🤖 **MCP Integration Framework**

### **Model Context Protocol Support**
- **AI Model Integration**: Seamless integration with various AI models
- **Tool Execution**: Dynamic tool discovery and execution
- **Resource Management**: Efficient resource caching and management
- **Prompt Engineering**: Advanced prompt management and optimization

### **MCP Server & Client**
- **Server Implementation**: Full MCP server with tool, resource, and prompt support
- **Client Integration**: MCP client for connecting to external services
- **Protocol Compliance**: Full compliance with MCP specification
- **Streaming Support**: Real-time streaming for completions and updates

### **Integration Management**
- **Multi-provider Support**: OpenAI, Anthropic, Google, Cohere, Local models
- **Connection Management**: Automatic connection handling and recovery
- **Capability Discovery**: Dynamic capability detection and registration
- **Execution Framework**: Parallel and sequential tool execution

## 🛠️ **Development Tools & SDKs**

### **Python SDK**
- **Comprehensive Client**: Full-featured Python client for all services
- **Service-specific Clients**: Dedicated clients for each service
- **Async Support**: Asynchronous operations for high performance
- **Error Handling**: Robust error handling with detailed error messages

### **JavaScript SDK**
- **Browser & Node.js Support**: Works in both browser and Node.js environments
- **TypeScript Support**: Full TypeScript definitions and type safety
- **Modern ES6+ Features**: Promise-based API with async/await support
- **Bundle Optimization**: Tree-shaking and minimal bundle size

### **IDE Bridge**
- **VS Code Extension**: Native VS Code integration
- **Real-time Collaboration**: Live collaboration features
- **Code Intelligence**: Enhanced code completion and analysis
- **Debugging Support**: Integrated debugging capabilities

## 📈 **Advanced Features**

### **Real-time Collaboration**
- **Live Editing**: Real-time collaborative editing
- **Conflict Resolution**: Automatic conflict detection and resolution
- **User Presence**: Real-time user presence and activity tracking
- **Version Control**: Automatic versioning and change tracking

### **Protocol Integration**
- **Multi-protocol Support**: Support for various communication protocols
- **Protocol Translation**: Automatic protocol translation and adaptation
- **Message Routing**: Intelligent message routing and load balancing
- **Protocol Optimization**: Performance optimization for each protocol

### **Memory System**
- **Persistent Memory**: Long-term memory storage and retrieval
- **Memory Optimization**: Efficient memory usage and garbage collection
- **Memory Analytics**: Memory usage patterns and optimization insights
- **Distributed Memory**: Shared memory across multiple instances

### **Search Engine**
- **Multimodal Search**: Text, image, and video search capabilities
- **Semantic Search**: Vector-based semantic search
- **Faceted Search**: Advanced filtering and faceting
- **Search Analytics**: Search patterns and optimization insights

## 📋 **Deployment Strategy**

See [DEPLOYMENT_TESTING_STRATEGY.md](./DEPLOYMENT_TESTING_STRATEGY.md) for the complete 5-phase deployment strategy:

1. **Phase 1**: Local Development Setup
2. **Phase 2**: Testing & Validation  
3. **Phase 3**: Performance Testing
4. **Phase 4**: Staging Deployment
5. **Phase 5**: Production Deployment

## 🔧 **Configuration**

### **Environment Variables**
All environment variables are managed through the secrets management system. See [docs/configuration.md](./docs/configuration.md) for detailed configuration options.

### **Docker Cleanup**
The system includes automatic Docker cleanup to prevent disk space issues:
- **Threshold**: 30% reclaimable space
- **Action**: Automatic `docker system prune -f`
- **Integration**: Built into all environment startup scripts

## 📚 **Documentation**

### **Core Documentation**
- [Configuration Guide](./docs/configuration.md)
- [Quick Start Guide](./docs/quick-start.md)
- [Deployment Strategy](./DEPLOYMENT_TESTING_STRATEGY.md)
- [API Reference](./docs/api-reference.md)
- [Troubleshooting](./docs/troubleshooting.md)

### **Advanced Documentation**
- [Unified Schema Guide](./docs/UNIFIED_SCHEMA_GUIDE.md)
- [Compose Deployment Guide](./docs/COMPOSE_DEPLOYMENT_GUIDE.md)
- [Environment Configuration Guide](./ENVIRONMENT_CONFIGURATION_GUIDE.md)
- [GPU Configuration Guide](./docs/gpu-configuration-guide.md)
- [Redis Configuration Guide](./docs/REDIS_CONFIGURATION_GUIDE.md)
- [Secrets Management Guide](./docs/SECRETS_MANAGEMENT.md)

### **API Documentation**
- [AI Agents API](./docs/api/ai-agents/README.md)
- [OpenAPI Specifications](./docs/openapi/)
- [Swagger UI](./docs/swagger-ui.html)

### **Development Resources**
- [SDK Documentation](./sdk/)
- [Testing Framework](./docs/testing/)
- [Security Guidelines](./docs/security/)
- [Performance Optimization](./docs/performance/)

## 🎯 **GitHub Issues**

Track your deployment progress with our comprehensive issue tracking:

### **Deployment Strategy Issues**
- [Issue #121](https://github.com/markwoitaszek/llm-multimodal-stack/issues/121) - Overall Deployment Strategy
- [Issue #122](https://github.com/markwoitaszek/llm-multimodal-stack/issues/122) - Phase 1: Development Setup
- [Issue #123](https://github.com/markwoitaszek/llm-multimodal-stack/issues/123) - Phase 2: Testing & Validation
- [Issue #124](https://github.com/markwoitaszek/llm-multimodal-stack/issues/124) - Phase 3: Performance Testing
- [Issue #125](https://github.com/markwoitaszek/llm-multimodal-stack/issues/125) - Phase 4: Staging Deployment
- [Issue #126](https://github.com/markwoitaszek/llm-multimodal-stack/issues/126) - Phase 5: Production Deployment

### **Feature Implementation Issues**
- [Issue #6](https://github.com/markwoitaszek/llm-multimodal-stack/issues/6) - MCP Support
- [Issue #9](https://github.com/markwoitaszek/llm-multimodal-stack/issues/9) - Analytics & Insights Dashboard
- [Issue #10](https://github.com/markwoitaszek/llm-multimodal-stack/issues/10) - API Connector Ecosystem
- [Issue #46](https://github.com/markwoitaszek/llm-multimodal-stack/issues/46) - API Lifecycle Management
- [Issue #54](https://github.com/markwoitaszek/llm-multimodal-stack/issues/54) - Authentication & API Gateway Dependencies

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 **Support**

- **Documentation**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/markwoitaszek/llm-multimodal-stack/issues)
- **Discussions**: [GitHub Discussions](https://github.com/markwoitaszek/llm-multimodal-stack/discussions)

---

**Phase-6A Production Ready** - Built for scale, security, and reliability.