# Hardcoded Values Audit Report

## Executive Summary

This audit identified **multiple hardcoded values** across Docker Compose files, service configurations, and configuration files that need to be replaced with environment variables to ensure proper schema-driven configuration management.

## Critical Issues Found

### 1. Docker Compose Files

#### `docker-compose.test.yml` - **CRITICAL**
- **Line 11**: `POSTGRES_PASSWORD=test` (hardcoded)
- **Line 53**: `JWT_SECRET=test-secret-key` (hardcoded)
- **Line 144**: `JWT_SECRET=test-secret-key` (hardcoded)
- **Line 170**: `N8N_BASIC_AUTH_PASSWORD=admin` (hardcoded)

#### `docker-compose.yml` - **MODERATE**
- **Line 8**: `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}` (hardcoded default)
- **Line 10**: `MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin}` (hardcoded default)
- **Line 57**: `POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}` (hardcoded default)
- **Line 97**: `MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD:-minioadmin}` (hardcoded default)
- **Line 196**: `MINIO_ACCESS_KEY=${MINIO_ROOT_USER:-minioadmin}` (hardcoded default)
- **Line 197**: `MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD:-minioadmin}` (hardcoded default)
- **Line 246**: `MINIO_ACCESS_KEY=${MINIO_ROOT_USER:-minioadmin}` (hardcoded default)
- **Line 247**: `MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD:-minioadmin}` (hardcoded default)
- **Line 507**: `N8N_BASIC_AUTH_USER=admin` (hardcoded)

### 2. Service Configuration Files

#### `services/multimodal-worker/app/config.py` - **MODERATE**
- **Line 36**: `postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")` (hardcoded default)
- **Line 51**: `minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")` (hardcoded default)
- **Line 52**: `minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")` (hardcoded default)

#### `services/ai-agents/app/config.py` - **MODERATE**
- **Line 31**: `postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")` (hardcoded default)

### 3. Configuration Files

#### `configs/litellm_config.yaml` - **CRITICAL**
- **Line 6**: `api_key: vllm-key` (hardcoded)
- **Line 12**: `api_key: vllm-key` (hardcoded)

#### `configs/grafana.ini` - **MODERATE**
- **Line 21**: `secret_key = multimodal-grafana-secret-key` (hardcoded)

#### `configs/kibana.yml` - **MODERATE**
- **Line 10**: `xpack.encryptedSavedObjects.encryptionKey: "multimodal-encryption-key-32-chars"` (hardcoded)

#### `configs/test_data.yaml` - **MODERATE**
- **Line 49**: `database_url: "postgresql://test:test@localhost:5432/test_db"` (hardcoded)
- **Line 54**: `database_url: "postgresql://staging:staging@staging-db:5432/staging_db"` (hardcoded)
- **Line 59**: `database_url: "postgresql://prod:prod@prod-db:5432/prod_db"` (hardcoded)
- **Line 68**: `password: "admin123"` (hardcoded)
- **Line 73**: `password: "test123"` (hardcoded)

## Impact Assessment

### Security Risks
1. **Hardcoded Passwords**: Test passwords and default credentials exposed
2. **API Keys**: Hardcoded API keys in configuration files
3. **Encryption Keys**: Hardcoded encryption keys for sensitive services

### Operational Risks
1. **Environment Inconsistency**: Different environments may use different hardcoded values
2. **Deployment Failures**: Hardcoded values may not work in different environments
3. **Maintenance Overhead**: Changes require updates in multiple files

### Compliance Issues
1. **Security Standards**: Hardcoded secrets violate security best practices
2. **Audit Requirements**: Hardcoded values make auditing difficult
3. **Secret Rotation**: Cannot rotate hardcoded secrets

## Recommended Fixes

### 1. Immediate Actions (Critical)
1. **Remove hardcoded passwords** from `docker-compose.test.yml`
2. **Replace hardcoded API keys** in `configs/litellm_config.yaml`
3. **Update test environment** to use schema-generated values

### 2. Short-term Actions (Moderate)
1. **Remove hardcoded defaults** from Docker Compose files
2. **Update service configurations** to not have hardcoded defaults
3. **Replace hardcoded encryption keys** in configuration files

### 3. Long-term Actions (Preventive)
1. **Implement validation** to prevent hardcoded values
2. **Add automated scanning** for hardcoded secrets
3. **Update documentation** with security guidelines

## Files Requiring Updates

### Critical Priority
- `docker-compose.test.yml`
- `configs/litellm_config.yaml`

### High Priority
- `docker-compose.yml`
- `services/multimodal-worker/app/config.py`
- `services/ai-agents/app/config.py`

### Medium Priority
- `configs/grafana.ini`
- `configs/kibana.yml`
- `configs/test_data.yaml`

## Validation Checklist

After fixes, verify:
- [ ] No hardcoded passwords in any Docker Compose files
- [ ] No hardcoded API keys in configuration files
- [ ] No hardcoded encryption keys
- [ ] All services use environment variables
- [ ] Test environment works with schema-generated values
- [ ] All environments can start successfully
- [ ] No secrets are exposed in logs or configuration

## Conclusion

The audit revealed significant hardcoded values that compromise security and maintainability. Immediate action is required to replace these with environment variables and ensure the schema-driven approach is properly implemented across all components.

The schema-driven approach will only be effective if all components properly use environment variables instead of hardcoded values.

