# Docker Compose Deployment Guide

This guide explains how to use the normalized Docker Compose configuration for deploying the Multimodal LLM Stack with control plane integration.

## Overview

The deployment structure has been normalized to support:
- **Base compose file** (`compose.yml`) with core services
- **Override files** for different environments and features
- **Docker profiles** for optional service toggling
- **Environment templates** (`.env.j2`) for Ansible/OpenBao integration
- **Secrets management** through the control plane

## File Structure

```
├── compose.yml                    # Base compose file with core services
├── compose.gpu.yml               # GPU optimization overrides
├── compose.monitoring.yml        # Monitoring services (profiles)
├── compose.production.yml        # Production environment overrides
├── compose.services.yml          # Additional services (profiles)
├── compose.elk.yml              # ELK stack for logging (profiles)
├── compose.n8n-monitoring.yml   # n8n monitoring (profiles)
└── env-templates/               # Environment templates
    ├── master.env.j2            # Combined template for all services
    ├── core.env.j2              # Core services (postgres, redis, etc.)
    ├── vllm.env.j2              # vLLM inference service
    ├── litellm.env.j2           # LiteLLM proxy service
    ├── multimodal-worker.env.j2 # Multimodal worker service
    ├── retrieval-proxy.env.j2   # Retrieval proxy service
    ├── ai-agents.env.j2         # AI agents service
    ├── memory-system.env.j2     # Memory system service
    ├── search-engine.env.j2     # Search engine service
    ├── user-management.env.j2   # User management service
    ├── openwebui.env.j2         # OpenWebUI service
    ├── n8n.env.j2               # n8n workflow service
    ├── n8n-monitoring.env.j2    # n8n monitoring service
    └── secrets-mapping.md       # Secrets mapping documentation
```

## Docker Profiles

Profiles allow you to selectively start services based on your deployment needs:

### Available Profiles

- **monitoring**: OpenWebUI, n8n workflow management
- **webui**: OpenWebUI interface
- **workflow**: n8n workflow automation
- **services**: AI agents, memory system, search engine, user management
- **agents**: AI agents service only
- **memory**: Memory system service only
- **search**: Search engine service only
- **auth**: User management service only
- **web**: AI agents web interface
- **elk**: ELK stack for centralized logging
- **logging**: Logging services
- **n8n-monitoring**: n8n monitoring and dashboard

### Using Profiles

```bash
# Start core services only
docker compose up -d

# Start core services with monitoring
docker compose --profile monitoring up -d

# Start core services with all additional services
docker compose --profile services --profile monitoring up -d

# Start with ELK stack for logging
docker compose --profile elk up -d

# Start specific services only
docker compose --profile agents --profile memory up -d
```

## Environment Configurations

### Development Environment

```bash
# Basic development setup
docker compose up -d

# Development with monitoring tools
docker compose --profile monitoring up -d
```

### Production Environment

```bash
# Production deployment with resource limits
docker compose -f compose.yml -f compose.production.yml up -d

# Production with monitoring and all services
docker compose -f compose.yml -f compose.production.yml --profile services --profile monitoring up -d
```

### GPU-Optimized Environment

```bash
# GPU-optimized deployment
docker compose -f compose.yml -f compose.gpu.yml up -d

# GPU-optimized with monitoring
docker compose -f compose.yml -f compose.gpu.yml --profile monitoring up -d
```

## Environment Templates Integration

### Using with Ansible

The environment templates (`.env.j2`) are designed for integration with Ansible and OpenBao:

1. **Render templates**: Use Ansible to render templates with secrets from OpenBao
2. **Deploy to target**: Copy rendered files to `/etc/llm-ms/.env.d/` on target hosts
3. **Start services**: Use Docker Compose to start services with environment files

Example Ansible playbook structure:
```yaml
- name: Render environment templates
  template:
    src: "env-templates/{{ item }}.j2"
    dest: "/etc/llm-ms/.env.d/{{ item | regex_replace('\\.env\\.j2$', '.env') }}"
  loop:
    - core.env.j2
    - vllm.env.j2
    - litellm.env.j2
    # ... other templates
```

### Environment File Structure

Rendered environment files should be placed in `/etc/llm-ms/.env.d/`:
```
/etc/llm-ms/.env.d/
├── core.env
├── vllm.env
├── litellm.env
├── multimodal-worker.env
├── retrieval-proxy.env
├── ai-agents.env
├── memory-system.env
├── search-engine.env
├── user-management.env
├── openwebui.env
├── n8n.env
└── n8n-monitoring.env
```

## Service Dependencies

### Core Services (Always Required)
- **postgres**: Database for metadata and user data
- **redis**: Caching and session storage
- **qdrant**: Vector database for embeddings
- **minio**: S3-compatible object storage
- **vllm**: LLM inference server
- **litellm**: API proxy and routing
- **multimodal-worker**: Core multimodal processing
- **retrieval-proxy**: Retrieval and search proxy

### Optional Services (Profile-based)
- **ai-agents**: AI agent framework
- **memory-system**: Long-term memory management
- **search-engine**: Advanced search capabilities
- **user-management**: User authentication and authorization
- **openwebui**: Web interface for testing
- **n8n**: Workflow automation platform
- **n8n-monitoring**: n8n monitoring and alerting
- **elk-stack**: Centralized logging (elasticsearch, logstash, kibana)

## Health Checks

All services include comprehensive health checks:
- **Database services**: Connection and query validation
- **API services**: HTTP endpoint health checks
- **GPU services**: GPU availability and model loading
- **Storage services**: Storage accessibility and capacity

## Resource Management

### Development Resources
- Minimal resource allocation
- Single replica per service
- Basic health checks

### Production Resources
- Resource limits and reservations
- Multiple replicas for critical services
- Enhanced monitoring and logging

### GPU Resources
- Multi-GPU support with tensor parallelism
- GPU memory optimization
- CUDA device management

## Security Considerations

1. **Secrets Management**: All secrets are managed through OpenBao
2. **Network Isolation**: Services communicate through internal networks
3. **TLS/SSL**: Production deployments include SSL termination
4. **Access Control**: User management service provides authentication
5. **Audit Logging**: Comprehensive logging for security monitoring

## Troubleshooting

### Common Issues

1. **Service Dependencies**: Ensure core services start before optional services
2. **Resource Constraints**: Check Docker resource limits and host capacity
3. **Network Connectivity**: Verify internal network configuration
4. **Environment Variables**: Ensure all required environment variables are set
5. **Health Check Failures**: Check service logs for startup issues

### Debugging Commands

```bash
# Check service status
docker compose ps

# View service logs
docker compose logs <service-name>

# Check health status
docker compose exec <service-name> curl -f http://localhost:<port>/health

# Verify environment variables
docker compose exec <service-name> env | grep <VARIABLE_NAME>
```

## Migration from Legacy Structure

If migrating from the old `docker-compose*.yml` structure:

1. **Backup existing data**: Export volumes and configurations
2. **Update environment files**: Convert `.env` files to use new variable names
3. **Test deployment**: Deploy in development environment first
4. **Update CI/CD**: Modify deployment scripts to use new compose structure
5. **Update documentation**: Update any custom deployment documentation

## Support

For issues with the deployment structure:
1. Check the troubleshooting section above
2. Review service logs for error messages
3. Verify environment variable configuration
4. Ensure all dependencies are properly started
5. Check Docker and system resource availability