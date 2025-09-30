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

## 🏗️ **Deployment Options**

### **Normalized Compose Structure (Recommended)**
The stack now uses a normalized Docker Compose structure with profiles for flexible deployments:

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

> **📋 See [Compose Deployment Guide](docs/COMPOSE_DEPLOYMENT_GUIDE.md) for detailed information about the new normalized structure and control plane integration.**

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

- [Configuration Guide](./docs/configuration.md)
- [Quick Start Guide](./docs/quick-start.md)
- [Deployment Strategy](./DEPLOYMENT_TESTING_STRATEGY.md)
- [API Reference](./docs/api-reference.md)
- [Troubleshooting](./docs/troubleshooting.md)

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