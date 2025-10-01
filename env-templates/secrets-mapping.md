# Secrets Mapping for Control Plane Integration

This document provides a mapping of all secrets required by each service in the Multimodal LLM Stack, organized for integration with the Ops control plane (Semaphore + OpenBao).

## Secret Categories

### Database Secrets
- `vault_postgres_password` - PostgreSQL database password
- `vault_redis_password` - Redis password (optional, usually empty)

### Storage Secrets
- `vault_minio_root_password` - MinIO S3 storage root password

### API and Authentication Secrets
- `vault_vllm_api_key` - vLLM inference API key
- `vault_litellm_master_key` - LiteLLM proxy master key
- `vault_litellm_salt_key` - LiteLLM proxy salt key
- `vault_jwt_secret_key` - JWT signing secret for user management
- `vault_webui_secret_key` - OpenWebUI secret key

### Workflow and Monitoring Secrets
- `vault_n8n_password` - n8n workflow platform password
- `vault_n8n_encryption_key` - n8n encryption key
- `vault_n8n_api_key` - n8n API key (optional)
- `vault_n8n_monitoring_secret_key` - n8n monitoring service secret

### External Service Secrets (Optional)
- `vault_openai_api_key` - OpenAI API key
- `vault_anthropic_api_key` - Anthropic API key
- `vault_google_api_key` - Google API key
- `vault_slack_webhook_url` - Slack webhook URL for alerts
- `vault_smtp_password` - SMTP password for email alerts

## Service-Specific Secret Requirements

### Core Services
- **postgres**: `vault_postgres_password`
- **redis**: `vault_redis_password` (optional)
- **minio**: `vault_minio_root_password`
- **qdrant**: No secrets required

### Inference Services
- **vllm**: `vault_vllm_api_key`
- **litellm**: `vault_litellm_master_key`, `vault_litellm_salt_key`

### Multimodal Services
- **multimodal-worker**: Uses database and storage secrets
- **retrieval-proxy**: Uses database and storage secrets

### AI Services
- **ai-agents**: Uses database secrets
- **memory-system**: Uses database secrets
- **search-engine**: Uses database secrets
- **user-management**: `vault_jwt_secret_key`

### Monitoring and UI Services
- **openwebui**: `vault_webui_secret_key`
- **n8n**: `vault_n8n_password`, `vault_n8n_encryption_key`
- **n8n-monitoring**: `vault_n8n_monitoring_secret_key`

## OpenBao Integration Notes

1. **Secret Engine**: Use KV v2 secret engine
2. **Path Structure**: `/secret/multimodal-llm/{environment}/{service}/`
3. **Environment Variables**: Prefix secrets with `vault_` in templates
4. **Default Values**: All secrets have fallback defaults for development

## Ansible Integration Notes

1. **Variable Names**: Use `vault_*` prefix for secrets
2. **Template Rendering**: Use Jinja2 templates with `{{ vault_secret_name }}` syntax
3. **Environment Files**: Render to `/etc/llm-ms/.env.d/` directory
4. **File Permissions**: Set 600 for rendered environment files

## Security Considerations

1. **Secret Rotation**: Implement regular secret rotation policies
2. **Access Control**: Use OpenBao policies to restrict secret access
3. **Audit Logging**: Enable audit logging for all secret access
4. **Encryption**: Use TLS for all secret transmission
5. **Backup**: Regularly backup secret configurations

## Deployment Examples

### Development Environment
```bash
# Render environment files for development
ansible-playbook render-env-templates.yml -e environment=dev
```

### Production Environment
```bash
# Render environment files for production with OpenBao secrets
ansible-playbook render-env-templates.yml -e environment=prod --ask-vault-pass
```

### Service-Specific Deployment
```bash
# Deploy only core services
docker compose up -d

# Deploy with monitoring
docker compose --profile monitoring up -d

# Deploy with all services
docker compose --profile services --profile monitoring up -d
```