# Unified Schema Guide - Docker Compose Management

This guide explains how to use the unified schema approach for managing Docker Compose configurations in the Multimodal LLM Stack.

## 🎯 Overview

Instead of maintaining multiple separate Docker Compose files, the stack now uses a **unified schema** (`schemas/compose-schema.yaml`) that generates all compose files from a single source of truth.

## 📁 File Structure

```
schemas/
├── compose-schema.yaml          # Unified schema definition
scripts/
├── compose-generator.py         # Schema to compose file generator
Makefile                         # Easy commands for compose management
compose*.yml                     # Generated compose files (DO NOT EDIT)
```

## 🏗️ Schema Structure

The unified schema (`schemas/compose-schema.yaml`) contains:

### 1. Global Configuration
```yaml
config:
  project_name: "multimodal"
  network_name: "multimodal-net"
  default_restart_policy: "unless-stopped"
  network: { ... }
  volume_config: { ... }
  health_checks: { ... }
```

### 2. Service Definitions
```yaml
services:
  postgres:
    category: "core"
    image: "postgres:16-alpine"
    # ... full service definition
    volumes_required: ["postgres_data"]
    profiles: ["services", "monitoring"]  # Optional profiles
```

### 3. Environment Configurations
```yaml
environments:
  development:
    description: "Development environment with core services only"
    services:
      - "postgres"
      - "redis"
      - "qdrant"
      - "minio"
      - "vllm"
      - "litellm"
      - "multimodal-worker"
      - "retrieval-proxy"
    overrides:
      debug: true
      log_level: "DEBUG"
```

### 4. Volume Definitions
```yaml
volumes:
  postgres_data:
    driver: "local"
  # ... other volumes
```

## 🚀 Usage

### Generate All Compose Files
```bash
# Generate all compose files from schema
make generate-compose

# Or directly with the script
python3 scripts/compose-generator.py
```

### Validate Schema
```bash
# Validate schema for errors
make validate-schema

# Or directly
python3 scripts/compose-generator.py --validate-only
```

### Generate Specific Files
```bash
# Generate files for specific environment
python3 scripts/compose-generator.py --environment production

# Generate files for specific profile
python3 scripts/compose-generator.py --profile monitoring
```

## 📋 Generated Files

The schema generates the following compose files:

| File | Purpose | Generated From |
|------|---------|----------------|
| `compose.yml` | Base compose file with core services | Core services only |
| `compose.development.yml` | Development environment | `environments.development` |
| `compose.staging.yml` | Staging environment | `environments.staging` |
| `compose.production.yml` | Production environment | `environments.production` |
| `compose.gpu.yml` | GPU-optimized environment | `environments.gpu` |
| `compose.monitoring.yml` | Monitoring environment | `environments.monitoring` |
| `compose.services.yml` | Additional services profile | Services with `profiles: ["services"]` |
| `compose.elk.yml` | ELK stack profile | Services with `profiles: ["elk"]` |
| `compose.n8n-monitoring.yml` | n8n monitoring profile | Services with `profiles: ["n8n-monitoring"]` |

## 🔧 Service Categories

Services are organized into categories for better management:

- **`core`**: Essential infrastructure (postgres, redis, qdrant, minio)
- **`inference`**: AI inference services (vllm, litellm)
- **`multimodal`**: Multimodal processing (multimodal-worker, retrieval-proxy)
- **`ai-services`**: AI agents and related services
- **`ui`**: User interface services (openwebui, ai-agents-web)
- **`workflow`**: Workflow automation (n8n, n8n-monitoring)
- **`monitoring`**: Monitoring and logging (elasticsearch, logstash, kibana)
- **`infrastructure`**: Infrastructure services (nginx)

## 🎛️ Docker Profiles

Services can be assigned to profiles for selective deployment:

```yaml
services:
  ai-agents:
    # ... service definition
    profiles:
      - "services"    # Included when --profile services is used
      - "agents"      # Included when --profile agents is used
```

### Available Profiles

- **`services`**: Additional AI services (ai-agents, memory-system, search-engine, user-management)
- **`monitoring`**: Monitoring services (openwebui, n8n)
- **`webui`**: Web interface services
- **`workflow`**: Workflow automation services
- **`agents`**: AI agents service only
- **`memory`**: Memory system service only
- **`search`**: Search engine service only
- **`auth`**: User management service only
- **`web`**: AI agents web interface
- **`elk`**: ELK stack for logging
- **`logging`**: Logging services
- **`n8n-monitoring`**: n8n monitoring and dashboard

## 🌍 Environment Overrides

Environments can override service configurations:

```yaml
environments:
  production:
    services: [...]
    overrides:
      debug: false
      log_level: "WARN"
      replicas:
        multimodal-worker: 3
        retrieval-proxy: 3
      resources:
        postgres:
          limits:
            memory: "4G"
            cpus: "2.0"
```

## 🔄 Workflow

### 1. Modify Schema
Edit `schemas/compose-schema.yaml` to:
- Add new services
- Modify existing services
- Update environment configurations
- Change profiles

### 2. Validate Changes
```bash
make validate-schema
```

### 3. Regenerate Files
```bash
make generate-compose
```

### 4. Test Generated Files
```bash
make test-compose
```

### 5. Deploy
```bash
make start-dev      # Development
make start-staging  # Staging
make start-prod     # Production
```

## 📝 Adding New Services

To add a new service to the schema:

1. **Add service definition**:
```yaml
services:
  my-new-service:
    category: "ai-services"
    image: "my-service:latest"
    container_name: "multimodal-my-service"
    ports:
      - "${MY_SERVICE_PORT:-8007}:8007"
    environment:
      - "MY_SERVICE_CONFIG=${MY_SERVICE_CONFIG}"
    depends_on:
      - "postgres"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8007/health"]
      template: "standard"
    profiles:
      - "services"
```

2. **Add to environments**:
```yaml
environments:
  staging:
    services:
      - "postgres"
      - "redis"
      # ... other services
      - "my-new-service"  # Add here
```

3. **Add volumes if needed**:
```yaml
volumes:
  my_service_data:
    driver: "local"
```

4. **Regenerate files**:
```bash
make generate-compose
```

## 🎯 Benefits

### 1. Single Source of Truth
- All service definitions in one place
- No duplication across multiple files
- Consistent configuration management

### 2. Easy Maintenance
- Add/modify services in one location
- Automatic generation of all compose files
- Validation prevents configuration errors

### 3. Environment Consistency
- Same services across environments
- Environment-specific overrides
- Profile-based service selection

### 4. Developer Experience
- Simple commands with Makefile
- Clear separation of concerns
- Easy to understand and modify

## 🚨 Important Notes

### ⚠️ DO NOT EDIT GENERATED FILES
- Generated `compose*.yml` files should **NEVER** be edited manually
- All changes must be made in `schemas/compose-schema.yaml`
- Regenerate files after making schema changes

### 🔄 Always Regenerate After Schema Changes
```bash
# After modifying schemas/compose-schema.yaml
make generate-compose
```

### ✅ Validate Before Deployment
```bash
# Always validate before deploying
make validate-schema
make test-compose
```

## 🛠️ Troubleshooting

### Schema Validation Errors
```bash
# Check for common issues
python3 scripts/compose-generator.py --validate-only
```

### Compose File Errors
```bash
# Test individual files
docker compose -f compose.yml config --quiet
docker compose -f compose.production.yml config --quiet
```

### Missing Dependencies
```bash
# Install required Python packages
pip install pyyaml jinja2
```

## 📚 Examples

### Adding GPU Support to a Service
```yaml
services:
  my-gpu-service:
    # ... service definition
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### Environment-Specific Resource Limits
```yaml
environments:
  production:
    overrides:
      resources:
        my-service:
          limits:
            memory: "8G"
            cpus: "4.0"
          reservations:
            memory: "4G"
            cpus: "2.0"
```

### Service Dependencies
```yaml
services:
  dependent-service:
    depends_on:
      - "postgres"
      - "redis"
      - "other-service"
```

This unified schema approach provides a maintainable, scalable way to manage Docker Compose configurations for the Multimodal LLM Stack.