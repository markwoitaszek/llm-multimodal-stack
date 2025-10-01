# LLM Multimodal Stack - Enterprise-Grade Infrastructure Management

A comprehensive, enterprise-grade multimodal LLM stack with advanced infrastructure management capabilities including stack-based architecture, network management, data retention policies, multi-tier backup systems, and automated operations.

## 🎯 **What's New in v3.0**

Version 3.0 represents a complete enterprise transformation with:
- ✅ **Stack-Based Architecture** - Modular service management with 6 independent stacks
- ✅ **Network Management** - Isolated networks with conflict detection and health monitoring
- ✅ **Data Retention Policies** - Automated cleanup with environment-specific policies
- ✅ **Multi-Tier Backup System** - Comprehensive backup strategies with multiple storage tiers
- ✅ **Granular Operations** - Fine-tuned wipe/reset operations for precise control
- ✅ **Production Secrets Management** - Encrypted secrets with rotation
- ✅ **Comprehensive Monitoring** - ELK stack, Prometheus, Grafana
- ✅ **Professional Testing** - Allure reporting, JMeter performance testing
- ✅ **Security Hardened** - Role-based access, audit logging
- ✅ **100+ Management Commands** - Complete operational control

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

## 🏗️ **Stack-Based Architecture**

The system is organized into 6 independent stacks for modular management:

### **Core Stack** - Foundation Infrastructure
```bash
# Start core services (PostgreSQL, Redis, Qdrant, MinIO)
make start-core

# Check core status
make status-core

# Stop core services
make stop-core
```

### **Inference Stack** - Model Serving
```bash
# Start inference services (vLLM, LiteLLM)
make start-inference

# Check inference status
make status-inference

# Stop inference services
make stop-inference
```

### **AI Stack** - AI Processing
```bash
# Start AI services (Multimodal Worker, Retrieval Proxy, AI Agents, etc.)
make start-ai

# Check AI status
make status-ai

# Stop AI services
make stop-ai
```

### **UI Stack** - User Interfaces
```bash
# Start UI services (OpenWebUI, n8n, n8n Monitoring, nginx)
make start-ui

# Check UI status
make status-ui

# Stop UI services
make stop-ui
```

### **Testing Stack** - Quality Assurance
```bash
# Start testing services (Allure, JMeter)
make start-testing

# Check testing status
make status-testing

# Stop testing services
make stop-testing
```

### **Monitoring Stack** - Observability
```bash
# Start monitoring services (Prometheus, Grafana, ELK)
make start-monitoring

# Check monitoring status
make status-monitoring

# Stop monitoring services
make stop-monitoring
```

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

## 🔧 **Advanced Management Features**

### **Network Management**
```bash
# Check for network conflicts
make check-network-conflicts

# Validate network configuration
make validate-networks

# Check network health
make check-network-health

# Cleanup orphaned networks
make cleanup-networks
```

### **Data Management**
```bash
# Check retention status
make retention-status ENVIRONMENT=development

# Run retention cleanup
make retention-cleanup ENVIRONMENT=development

# Test retention cleanup (dry run)
make retention-test ENVIRONMENT=development

# Check backup status
make backup-status ENVIRONMENT=production

# Run full backup
make backup-full ENVIRONMENT=production

# Backup specific service
make backup-service SERVICE=postgres ENVIRONMENT=production
```

### **Granular Operations**
```bash
# Wipe specific stacks
make wipe-core
make wipe-inference
make wipe-ai
make wipe-ui
make wipe-testing
make wipe-monitoring

# Wipe specific data types
make wipe-db
make wipe-cache
make wipe-models
make wipe-logs
make wipe-test-results

# Wipe entire environments
make wipe-dev
make wipe-staging
make wipe-prod
make wipe-testing
```

### **Testing Framework**
```bash
# Start testing stack
make start-testing

# Run test suites
make test-allure
make test-jmeter
make test-unit
make test-integration
make test-performance
make test-api

# Generate test reports
make generate-allure-report
make serve-allure-report
```

### **GPU Acceleration**
```bash
# Auto-detect and configure GPU
make detect-gpu
make configure-gpu

# Start with GPU optimization
make start-gpu-auto
```

### **Environment Management**
```bash
# Wipe and reset environment
make wipe
make reset

# Validate configuration
make validate-schema
make validate-security

# Validate credentials
make validate-credentials-dev
make validate-credentials-staging
make validate-credentials-prod
```

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

### **Prometheus + Grafana**
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization (http://localhost:3001)

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
- [Architecture Guide](docs/ARCHITECTURE.md) - Complete system architecture
- [Operations Guide](docs/OPERATIONS.md) - Daily operations and maintenance
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Debugging and issue resolution

### **Configuration Documentation**
- [Environment Templates](env-templates/README.md) - Jinja2 template system
- [Secrets Mapping](env-templates/secrets-mapping.md) - OpenBao integration
- [Enhanced Workflow Diagram](ENHANCED_WORKFLOW_DIAGRAM.md) - Complete system overview

### **Feature Documentation**
- [GPU Configuration](GPU_CONFIGURATION_SUCCESS.md) - GPU optimization guide
- [Container Logs Audit](container-logs-audit-report.md) - System health report
- [Data Retention Policies](configs/retention-policies.yaml) - Retention configuration
- [Backup Strategies](configs/backup-strategies.yaml) - Backup configuration

## 🎯 **GitHub Issues**

Track your deployment progress with our comprehensive issue tracking:
- [Issue #121](https://github.com/markwoitaszek/llm-multimodal-stack/issues/121) - Overall Deployment Strategy
- [Issue #122](https://github.com/markwoitaszek/llm-multimodal-stack/issues/122) - Phase 1: Development Setup
- [Issue #123](https://github.com/markwoitaszek/llm-multimodal-stack/issues/123) - Phase 2: Testing & Validation
- [Issue #124](https://github.com/markwoitaszek/llm-multimodal-stack/issues/124) - Phase 3: Performance Testing
- [Issue #125](https://github.com/markwoitaszek/llm-multimodal-stack/issues/125) - Phase 4: Staging Deployment
- [Issue #126](https://github.com/markwoitaszek/llm-multimodal-stack/issues/126) - Phase 5: Production Deployment

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