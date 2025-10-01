# Environment Templates

This directory contains Jinja2 environment templates for the Multimodal LLM Stack, designed for integration with the Ops control plane (Semaphore + OpenBao).

## Overview

Environment templates provide a standardized way to manage configuration across different deployment environments while maintaining security through secrets management integration.

## Template Structure

### Core Templates
- `core.env.j2` - Core services (postgres, redis, minio, qdrant)
- `vllm.env.j2` - vLLM inference server configuration
- `litellm.env.j2` - LiteLLM proxy configuration

### Service Templates
- `multimodal-worker.env.j2` - Multimodal worker service
- `retrieval-proxy.env.j2` - Retrieval proxy service
- `ai-agents.env.j2` - AI agents service
- `memory-system.env.j2` - Memory system service
- `search-engine.env.j2` - Search engine service
- `user-management.env.j2` - User management service

### UI and Monitoring Templates
- `openwebui.env.j2` - OpenWebUI interface
- `n8n.env.j2` - n8n workflow platform
- `n8n-monitoring.env.j2` - n8n monitoring service

### Combined Template
- `master.env.j2` - Combined template for all services

## Template Features

### Jinja2 Syntax
Templates use Jinja2 syntax for variable substitution:
```jinja2
{{ variable_name | default('default_value') }}
```

### Secrets Integration
Secrets are prefixed with `vault_` for OpenBao integration:
```jinja2
{{ vault_secret_name | default('fallback_default') }}
```

### Default Values
All variables include sensible defaults for development environments.

## Usage

### With Ansible
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

### With OpenBao
Secrets are retrieved from OpenBao and injected during template rendering:
```bash
# Example OpenBao secret path
vault kv get -field=password secret/multimodal-llm/prod/postgres
```

### Manual Rendering
For testing or development:
```bash
# Install Jinja2 CLI
pip install jinja2-cli

# Render template with variables
jinja2 core.env.j2 -D postgres_password=mysecret > core.env
```

## Variable Categories

### Database Configuration
- PostgreSQL connection settings
- Redis configuration
- Connection pooling and timeouts

### Storage Configuration
- MinIO S3-compatible storage
- Qdrant vector database
- File upload limits and paths

### API Configuration
- Service endpoints and ports
- Authentication tokens and keys
- Rate limiting and timeouts

### Security Configuration
- JWT secrets and algorithms
- Encryption keys
- Access control settings

### Performance Configuration
- Cache TTL settings
- Batch sizes and concurrency limits
- Resource allocation

## Secrets Management

### Required Secrets
See `secrets-mapping.md` for a complete list of required secrets and their purposes.

### Secret Naming Convention
- Database secrets: `vault_postgres_password`, `vault_redis_password`
- API secrets: `vault_vllm_api_key`, `vault_litellm_master_key`
- Authentication: `vault_jwt_secret_key`, `vault_webui_secret_key`
- Workflow: `vault_n8n_password`, `vault_n8n_encryption_key`

### OpenBao Integration
Secrets are stored in OpenBao KV v2 engine with paths like:
```
secret/multimodal-llm/{environment}/{service}/{secret_name}
```

## Environment-Specific Configuration

### Development Environment
- Default passwords and keys
- Debug logging enabled
- Minimal resource allocation
- Local development URLs

### Staging Environment
- Staging-specific secrets
- Production-like configuration
- Enhanced monitoring
- Load testing configuration

### Production Environment
- Production secrets from OpenBao
- Security hardening
- Performance optimization
- High availability configuration

## Best Practices

### Security
1. Never commit rendered environment files to version control
2. Use strong, unique secrets for each environment
3. Rotate secrets regularly
4. Implement least-privilege access

### Configuration Management
1. Use environment-specific variable files
2. Validate configuration before deployment
3. Document all custom variables
4. Test configuration changes in staging first

### Deployment
1. Render templates during deployment process
2. Set appropriate file permissions (600)
3. Verify environment variables after deployment
4. Monitor service health after configuration changes

## Troubleshooting

### Common Issues

1. **Template Rendering Errors**
   - Check Jinja2 syntax
   - Verify variable names and types
   - Ensure all required variables are defined

2. **Missing Secrets**
   - Verify OpenBao connectivity
   - Check secret paths and permissions
   - Ensure fallback defaults are appropriate

3. **Service Startup Failures**
   - Check rendered environment files
   - Verify variable values and formats
   - Review service logs for configuration errors

### Debug Commands
```bash
# Check rendered environment file
cat /etc/llm-ms/.env.d/core.env

# Validate template syntax
jinja2 --check core.env.j2

# Test template rendering
jinja2 core.env.j2 -D test_var=value
```

## Contributing

When adding new services or configuration options:

1. Create a new template file following the naming convention
2. Include comprehensive variable documentation
3. Add appropriate default values
4. Update the secrets mapping documentation
5. Test template rendering with various configurations
6. Update the master template if needed

## Support

For issues with environment templates:
1. Check the troubleshooting section
2. Review the secrets mapping documentation
3. Verify OpenBao integration
4. Test template rendering manually
5. Check Ansible playbook configuration