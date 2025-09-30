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


