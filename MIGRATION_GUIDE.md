# Migration Guide: Legacy to Normalized Structure

This guide explains how to migrate from the old Docker Compose structure to the new normalized structure while maintaining backward compatibility.

## 🎯 Migration Overview

The migration updates the existing deployment scripts to use the new normalized structure while maintaining full backward compatibility for existing workflows.

## ✅ What Was Updated

### 1. Updated `start-environment.sh`

**Before:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.development.override.yml up -d
```

**After:**
```bash
docker compose up -d
```

**Changes Made:**
- **Development**: Now uses `docker compose up -d` (core services only)
- **Staging**: Uses `docker compose -f compose.yml -f compose.production.yml --profile services --profile monitoring up -d`
- **Production**: Uses `docker compose -f compose.yml -f compose.production.yml --profile services --profile monitoring up -d`
- **Monitoring**: Uses `docker compose -f compose.yml -f compose.elk.yml --profile elk --profile monitoring up -d`
- **Optimized**: Uses `docker compose -f compose.yml -f compose.gpu.yml -f compose.production.yml up -d`
- **Testing/Performance**: Uses `docker compose up -d` (basic services for testing)

### 2. Updated `setup_secrets.py`

**New Features:**
- **Template Rendering**: Renders Jinja2 environment templates
- **Backward Compatibility**: Still creates legacy `.env.development` files
- **Dual Output**: Creates both normalized templates and legacy files
- **Fallback Support**: Works even if Jinja2 is not available

**Output Files:**
- **New Structure**: `.env.d/` directory with individual service files
- **Legacy Structure**: `.env.development` file for backward compatibility
- **Secrets Storage**: Maintains existing secrets storage format

### 3. Service Availability Changes

**Development Environment (Core Services Only):**
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379) 
- ✅ Qdrant (port 6333)
- ✅ MinIO (port 9000, console 9002)
- ✅ vLLM (port 8000)
- ✅ LiteLLM (port 4000)
- ✅ Multimodal Worker (port 8001)
- ✅ Retrieval Proxy (port 8002)

**Staging/Production Environment (Full Services):**
- ✅ All core services above
- ✅ AI Agents (port 8003)
- ✅ Search Engine (port 8004)
- ✅ Memory System (port 8005)
- ✅ User Management (port 8006)
- ✅ OpenWebUI (port 3030) - staging only
- ✅ n8n (port 5678)
- ✅ n8n Monitoring (port 8008)

**Monitoring Environment (ELK Stack):**
- ✅ All core services
- ✅ OpenWebUI (port 3030)
- ✅ n8n (port 5678)
- ✅ Kibana (port 5601)
- ✅ Elasticsearch (port 9200)
- ✅ Logstash (port 9600)

## 🔄 Migration Steps

### Step 1: Backup Existing Environment
```bash
# Backup existing environment files
cp .env .env.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp .env.development .env.development.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
```

### Step 2: Run Updated Setup
```bash
# Run the updated setup script
python3 setup_secrets.py
```

This will create:
- New normalized environment files in `.env.d/`
- Legacy `.env.development` file for backward compatibility
- Updated secrets storage

### Step 3: Test Development Environment
```bash
# Test the updated development environment
./start-environment.sh dev
```

### Step 4: Verify Services
```bash
# Check service status
docker compose ps

# Check logs if needed
docker compose logs -f [service-name]
```

### Step 5: Test Other Environments
```bash
# Test staging environment
./start-environment.sh staging

# Test production environment  
./start-environment.sh production

# Test monitoring environment
./start-environment.sh monitoring
```

## 🆚 Environment Comparison

| Environment | Old Command | New Command | Services |
|-------------|-------------|-------------|----------|
| **Development** | `docker-compose -f docker-compose.yml -f docker-compose.development.override.yml up -d` | `docker compose up -d` | Core services only |
| **Staging** | `docker-compose -f docker-compose.staging.yml up -d` | `docker compose -f compose.yml -f compose.production.yml --profile services --profile monitoring up -d` | Full services |
| **Production** | `docker-compose -f docker-compose.production.yml up -d` | `docker compose -f compose.yml -f compose.production.yml --profile services --profile monitoring up -d` | Full services |
| **Testing** | `docker-compose -f docker-compose.allure.yml up -d` | `docker compose up -d` | Core services for testing |
| **Performance** | `docker-compose -f docker-compose.jmeter.yml up -d` | `docker compose up -d` | Core services for testing |
| **Monitoring** | `docker-compose -f docker-compose.yml -f docker-compose.elk.yml up -d` | `docker compose -f compose.yml -f compose.elk.yml --profile elk --profile monitoring up -d` | ELK + monitoring |
| **Optimized** | `docker-compose -f docker-compose.optimized.yml up -d` | `docker compose -f compose.yml -f compose.gpu.yml -f compose.production.yml up -d` | GPU optimized |

## 🔧 Troubleshooting

### Issue: Docker Compose Command Not Found
**Solution:** Update to Docker Compose V2 (the new `docker compose` command)
```bash
# Install Docker Compose V2
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Or use the standalone version
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Issue: Jinja2 Not Available
**Solution:** Install Jinja2 or use legacy mode
```bash
# Install Jinja2
pip install jinja2

# Or use legacy mode (setup_secrets.py will automatically fall back)
```

### Issue: Services Not Starting
**Solution:** Check logs and verify environment files
```bash
# Check service logs
docker compose logs [service-name]

# Verify environment files exist
ls -la .env.d/
ls -la .env.development

# Check if secrets are properly set
grep -v "^#" .env.development | grep -v "^$"
```

### Issue: Port Conflicts
**Solution:** Check for existing services on the same ports
```bash
# Check what's using the ports
sudo netstat -tlnp | grep -E ":(5432|6379|6333|9000|8000|4000|8001|8002)"

# Stop conflicting services or change ports in environment files
```

## 📋 Validation Checklist

- [ ] `start-environment.sh dev` starts core services successfully
- [ ] `start-environment.sh staging` starts all services successfully  
- [ ] `start-environment.sh production` starts all services successfully
- [ ] `start-environment.sh monitoring` starts ELK stack successfully
- [ ] `setup_secrets.py` generates both template and legacy files
- [ ] All services respond to health checks
- [ ] Environment variables are properly loaded
- [ ] No port conflicts with existing services

## 🚀 Next Steps

### For Development
1. Use the updated scripts as normal
2. The new structure provides better organization
3. Templates are available for custom configurations

### For Production
1. Use Ansible with the new templates: `./scripts/deploy-with-ansible.sh prod`
2. Configure OpenBao secrets management
3. Use the normalized structure for better maintainability

### For CI/CD
1. Update deployment scripts to use new compose commands
2. Use environment templates for configuration management
3. Integrate with Semaphore and OpenBao for production deployments

## 📞 Support

If you encounter issues during migration:

1. **Check the logs**: `docker compose logs -f [service-name]`
2. **Verify environment files**: Ensure `.env.development` exists and has proper values
3. **Check Docker status**: `docker compose ps` to see service status
4. **Review this guide**: Most common issues are covered above
5. **Use legacy mode**: If templates don't work, the legacy environment generation still functions

The migration maintains full backward compatibility, so existing workflows should continue to work while providing access to the new normalized structure.