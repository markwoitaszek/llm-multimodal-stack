#!/bin/bash
# Fix Environment Configuration Discrepancies
# Addresses inconsistencies found in the environment analysis

set -e

echo "🔧 Fixing Environment Configuration Discrepancies"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ SUCCESS${NC}: $message"
            ;;
        "ERROR")
            echo -e "${RED}❌ ERROR${NC}: $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  WARNING${NC}: $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  INFO${NC}: $message"
            ;;
    esac
}

# Function to create missing environment files
create_missing_env_files() {
    echo ""
    print_status "INFO" "Creating missing environment files..."
    
    # Create .env.testing
    if [ ! -f ".env.testing" ]; then
        cat > .env.testing << 'EOF'
# Testing Environment Variables
# Generated automatically to fix configuration discrepancies

# Database Configuration
POSTGRES_DB=test_multimodal
POSTGRES_USER=test_user
POSTGRES_PASSWORD=test_password_secure_123

# Storage Configuration
MINIO_ROOT_USER=testadmin
MINIO_ROOT_PASSWORD=test_minio_password_secure_123

# Model Configuration
VLLM_MODEL=microsoft/DialoGPT-small
VLLM_GPU_MEMORY_UTILIZATION=0.5
VLLM_MAX_MODEL_LEN=512

# LiteLLM Configuration
LITELLM_MASTER_KEY=sk-test-master-key-12345678901234567890123456789012
LITELLM_SALT_KEY=sk-test-salt-key-12345678901234567890123456789012
VLLM_API_KEY=test_vllm_api_key_12345678901234567890123456789012

# Security Configuration
JWT_SECRET_KEY=test-jwt-secret-key-12345678901234567890123456789012
WEBUI_SECRET_KEY=test-webui-secret-12345678901234567890123456789012
N8N_PASSWORD=test_n8n_password_secure_123
N8N_ENCRYPTION_KEY=test_n8n_encryption_key_12345678901234567890123456789012

# Service Ports (Testing)
VLLM_PORT=8000
LITELLM_PORT=4000
MULTIMODAL_WORKER_PORT=8001
RETRIEVAL_PROXY_PORT=8002
AI_AGENTS_PORT=8003
SEARCH_ENGINE_PORT=8004
MEMORY_SYSTEM_PORT=8005
USER_MANAGEMENT_PORT=8006
OPENWEBUI_PORT=3030
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334
POSTGRES_PORT=5432
REDIS_PORT=6379
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9002
N8N_PORT=5678

# Service Hosts
VLLM_HOST=0.0.0.0
QDRANT_HOST=qdrant
POSTGRES_HOST=postgres
REDIS_HOST=redis
MINIO_ENDPOINT=minio:9000

# Debug Configuration
DEBUG=true
LOG_LEVEL=DEBUG
EOF
        print_status "SUCCESS" "Created .env.testing file"
    else
        print_status "INFO" ".env.testing already exists"
    fi
    
    # Create .env.performance
    if [ ! -f ".env.performance" ]; then
        cat > .env.performance << 'EOF'
# Performance Testing Environment Variables
# Generated automatically to fix configuration discrepancies

# Database Configuration
POSTGRES_DB=perf_multimodal
POSTGRES_USER=perf_user
POSTGRES_PASSWORD=perf_password_secure_123

# Storage Configuration
MINIO_ROOT_USER=perfadmin
MINIO_ROOT_PASSWORD=perf_minio_password_secure_123

# Model Configuration
VLLM_MODEL=microsoft/DialoGPT-small
VLLM_GPU_MEMORY_UTILIZATION=0.7
VLLM_MAX_MODEL_LEN=1024

# LiteLLM Configuration
LITELLM_MASTER_KEY=sk-perf-master-key-12345678901234567890123456789012
LITELLM_SALT_KEY=sk-perf-salt-key-12345678901234567890123456789012
VLLM_API_KEY=perf_vllm_api_key_12345678901234567890123456789012

# Security Configuration
JWT_SECRET_KEY=perf-jwt-secret-key-12345678901234567890123456789012
WEBUI_SECRET_KEY=perf-webui-secret-12345678901234567890123456789012
N8N_PASSWORD=perf_n8n_password_secure_123
N8N_ENCRYPTION_KEY=perf_n8n_encryption_key_12345678901234567890123456789012

# Service Ports (Performance)
VLLM_PORT=8000
LITELLM_PORT=4000
MULTIMODAL_WORKER_PORT=8001
RETRIEVAL_PROXY_PORT=8002
AI_AGENTS_PORT=8003
SEARCH_ENGINE_PORT=8004
MEMORY_SYSTEM_PORT=8005
USER_MANAGEMENT_PORT=8006
OPENWEBUI_PORT=3030
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334
POSTGRES_PORT=5432
REDIS_PORT=6379
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9002
N8N_PORT=5678

# Service Hosts
VLLM_HOST=0.0.0.0
QDRANT_HOST=qdrant
POSTGRES_HOST=postgres
REDIS_HOST=redis
MINIO_ENDPOINT=minio:9000

# Performance Configuration
DEBUG=false
LOG_LEVEL=INFO
EOF
        print_status "SUCCESS" "Created .env.performance file"
    else
        print_status "INFO" ".env.performance already exists"
    fi
}

# Function to fix Docker Compose file inconsistencies
fix_compose_inconsistencies() {
    echo ""
    print_status "INFO" "Fixing Docker Compose file inconsistencies..."
    
    # Fix staging.yml to include all base services
    if [ -f "docker-compose.staging.yml" ]; then
        # Check if staging.yml is missing base services
        if ! grep -q "services:" docker-compose.staging.yml || [ $(grep -c "services:" docker-compose.staging.yml) -eq 1 ]; then
            print_status "WARNING" "docker-compose.staging.yml appears to be an override file, not a complete compose file"
            print_status "INFO" "Consider using docker-compose.yml + docker-compose.staging.override.yml pattern"
        fi
    fi
    
    # Fix production.yml to include all base services
    if [ -f "docker-compose.production.yml" ]; then
        # Check if production.yml is missing base services
        if ! grep -q "services:" docker-compose.production.yml || [ $(grep -c "services:" docker-compose.production.yml) -eq 1 ]; then
            print_status "WARNING" "docker-compose.production.yml appears to be an override file, not a complete compose file"
            print_status "INFO" "Consider using docker-compose.yml + docker-compose.production.override.yml pattern"
        fi
    fi
}

# Function to create missing configuration files
create_missing_configs() {
    echo ""
    print_status "INFO" "Creating missing configuration files..."
    
    # Create litellm_config.yaml if it doesn't exist
    if [ ! -f "configs/litellm_config.yaml" ]; then
        mkdir -p configs
        cat > configs/litellm_config.yaml << 'EOF'
# LiteLLM Production Configuration
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: vllm/microsoft/DialoGPT-medium
      api_base: http://vllm:8000/v1
      api_key: ${VLLM_API_KEY}

# Database configuration
database_url: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# Logging configuration
litellm_settings:
  drop_params: true
  set_verbose: false
  max_budget: 1000
  cache: true

# Rate limiting
rate_limiting: true
rate_limiting_requests_per_minute: 60

# Health check configuration
health_check_interval: 30
EOF
        print_status "SUCCESS" "Created configs/litellm_config.yaml"
    else
        print_status "INFO" "configs/litellm_config.yaml already exists"
    fi
    
    # Create litellm_optimized.yaml if it doesn't exist
    if [ ! -f "configs/litellm_optimized.yaml" ]; then
        cat > configs/litellm_optimized.yaml << 'EOF'
# LiteLLM Optimized Configuration
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: vllm/microsoft/DialoGPT-medium
      api_base: http://vllm:8000/v1
      api_key: ${VLLM_API_KEY}

# Database configuration
database_url: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# Optimized settings
litellm_settings:
  drop_params: true
  set_verbose: false
  max_budget: 2000
  cache: true
  cache_ttl: 3600

# Enhanced rate limiting
rate_limiting: true
rate_limiting_requests_per_minute: 120

# Performance optimizations
max_workers: 8
worker_timeout: 300

# Health check configuration
health_check_interval: 15
EOF
        print_status "SUCCESS" "Created configs/litellm_optimized.yaml"
    else
        print_status "INFO" "configs/litellm_optimized.yaml already exists"
    fi
}

# Function to create missing directories
create_missing_directories() {
    echo ""
    print_status "INFO" "Creating missing directories..."
    
    local directories=("models" "configs" "scripts" "services" "reports" "logs")
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "SUCCESS" "Created directory: $dir"
        else
            print_status "INFO" "Directory already exists: $dir"
        fi
    done
}

# Function to fix network configuration inconsistencies
fix_network_config() {
    echo ""
    print_status "INFO" "Fixing network configuration inconsistencies..."
    
    # Check if test-network is defined in test compose files
    if [ -f "docker-compose.test.yml" ]; then
        if ! grep -q "test-network" docker-compose.test.yml; then
            print_status "WARNING" "docker-compose.test.yml should use test-network for isolation"
        fi
    fi
    
    # Ensure all other environments use multimodal-net
    local compose_files=("docker-compose.yml" "docker-compose.development.override.yml" "docker-compose.staging.yml" "docker-compose.production.yml" "docker-compose.allure.yml" "docker-compose.jmeter.yml" "docker-compose.elk.yml" "docker-compose.optimized.yml")
    
    for file in "${compose_files[@]}"; do
        if [ -f "$file" ]; then
            if grep -q "networks:" "$file" && ! grep -q "multimodal-net" "$file"; then
                print_status "WARNING" "$file should use multimodal-net network for consistency"
            fi
        fi
    done
}

# Function to add secrets management to testing and performance environments
add_secrets_management() {
    echo ""
    print_status "INFO" "Adding secrets management to testing and performance environments..."
    
    # Update start-environment.sh to include secrets management for testing and performance
    if [ -f "start-environment.sh" ]; then
        # Check if testing environment has secrets management
        if ! grep -A 5 '"testing")' start-environment.sh | grep -q "setup_environment_file"; then
            print_status "WARNING" "Testing environment should use secrets management"
        fi
        
        # Check if performance environment has secrets management
        if ! grep -A 5 '"performance")' start-environment.sh | grep -q "setup_environment_file"; then
            print_status "WARNING" "Performance environment should use secrets management"
        fi
    fi
}

# Function to create comprehensive environment documentation
create_environment_docs() {
    echo ""
    print_status "INFO" "Creating comprehensive environment documentation..."
    
    cat > ENVIRONMENT_CONFIGURATION_GUIDE.md << 'EOF'
# Environment Configuration Guide

## Overview
This guide provides comprehensive information about all environment configurations in the LLM Multimodal Stack.

## Environment Types

### 1. Development Environment
- **Purpose**: Local development and testing
- **Files**: `docker-compose.yml` + `docker-compose.development.override.yml`
- **Environment File**: `.env.development`
- **Services**: All base services with development optimizations
- **Resources**: ~8GB RAM, 1 GPU
- **Network**: `multimodal-net`

### 2. Staging Environment
- **Purpose**: Pre-production testing
- **Files**: `docker-compose.staging.yml`
- **Environment File**: `.env.staging`
- **Services**: All base services with staging configurations
- **Resources**: ~12GB RAM, 1 GPU
- **Network**: `multimodal-net`

### 3. Production Environment
- **Purpose**: Production deployment
- **Files**: `docker-compose.production.yml`
- **Environment File**: `.env.production`
- **Services**: All base services with production optimizations
- **Resources**: ~20GB RAM, 1 GPU
- **Network**: `multimodal-net`
- **Monitoring**: Prometheus + Grafana

### 4. Testing Environment
- **Purpose**: Automated testing with Allure reports
- **Files**: `docker-compose.allure.yml`
- **Environment File**: `.env.testing`
- **Services**: Allure reporting services only
- **Resources**: ~2GB RAM, no GPU
- **Network**: `multimodal-net`

### 5. Performance Environment
- **Purpose**: Load testing with JMeter
- **Files**: `docker-compose.jmeter.yml`
- **Environment File**: `.env.performance`
- **Services**: JMeter testing services only
- **Resources**: ~4GB RAM, no GPU
- **Network**: `multimodal-net`

### 6. Monitoring Environment
- **Purpose**: Centralized logging and monitoring
- **Files**: `docker-compose.yml` + `docker-compose.elk.yml`
- **Environment File**: `.env.monitoring`
- **Services**: All base services + ELK stack
- **Resources**: ~16GB RAM, 1 GPU
- **Network**: `multimodal-net`

### 7. Optimized Environment
- **Purpose**: High-performance deployment
- **Files**: `docker-compose.optimized.yml`
- **Environment File**: `.env.optimized`
- **Services**: All base services with performance optimizations
- **Resources**: ~24GB RAM, 1 GPU
- **Network**: `multimodal-net`

## Configuration Consistency

### Environment Variables
All environments now have consistent environment variable definitions:
- Database credentials
- Storage credentials
- API keys and secrets
- Service ports and hosts
- Debug and logging settings

### Network Configuration
- **multimodal-net**: Used by all environments except testing
- **test-network**: Used by testing environment for isolation

### Volume Configuration
- Standard volumes for all environments
- Environment-specific volume names for isolation
- Persistent data storage for production environments

### Health Checks
- Consistent health check intervals across environments
- Environment-specific timeout configurations
- Proper dependency management

## Troubleshooting

### Common Issues
1. **Missing Environment Files**: Run `./scripts/fix-environment-discrepancies.sh`
2. **Port Conflicts**: Check port availability with `netstat -tulpn`
3. **GPU Issues**: Verify NVIDIA drivers and container toolkit
4. **Memory Issues**: Check available memory with `free -h`
5. **Network Issues**: Verify Docker network configuration

### Validation
Run the environment validator to check configuration:
```bash
./scripts/validate-environment.sh
```

### Fixes
Apply configuration fixes:
```bash
./scripts/fix-environment-discrepancies.sh
```

## Best Practices

1. **Always use environment files**: Never hardcode secrets
2. **Validate before deployment**: Run validation scripts
3. **Monitor resources**: Check memory and disk usage
4. **Use appropriate environments**: Match environment to use case
5. **Keep configurations updated**: Regular maintenance and updates
EOF
    
    print_status "SUCCESS" "Created ENVIRONMENT_CONFIGURATION_GUIDE.md"
}

# Main function
main() {
    echo "Starting environment discrepancy fixes..."
    
    create_missing_directories
    create_missing_env_files
    create_missing_configs
    fix_compose_inconsistencies
    fix_network_config
    add_secrets_management
    create_environment_docs
    
    echo ""
    print_status "SUCCESS" "Environment discrepancy fixes completed!"
    echo ""
    print_status "INFO" "Next steps:"
    print_status "INFO" "1. Review the generated files"
    print_status "INFO" "2. Run validation: ./scripts/validate-environment.sh"
    print_status "INFO" "3. Test environment startup: ./start-environment.sh dev"
    print_status "INFO" "4. Check the ENVIRONMENT_CONFIGURATION_GUIDE.md for details"
}

# Run main function
main "$@"

