# Focused Restoration Plan - Critical Operational Features

## Overview

Based on your specific concerns, this plan focuses on restoring the three most critical operational features that were lost during the migration from `cursor-env-audit` to `phase-1-testing`:

1. **GPU/NVLink Optimizations** - Multi-GPU configuration and performance tuning
2. **Docker Environment Wipe** - Complete environment reset capability  
3. **Hardcoded Values Reversion** - Remove security vulnerabilities from hardcoded defaults

## 1. 🎮 GPU/NVLink Optimization Restoration

### Current State Analysis
- ✅ Basic GPU support exists (`CUDA_VISIBLE_DEVICES=0,1` in env templates)
- ❌ **Missing**: Advanced NVLink topology detection
- ❌ **Missing**: Automatic multi-GPU configuration
- ❌ **Missing**: Tensor parallelism optimization
- ❌ **Missing**: GPU-specific environment generation

### Lost Functionality
The `cursor-env-audit` branch had a comprehensive GPU configuration system:

```bash
# Advanced GPU detection and configuration
scripts/configure-gpu.sh --detect    # Auto-detect GPU setup
scripts/configure-gpu.sh --configure # Configure for optimal performance
```

**Key Features Lost**:
- **NVLink Topology Detection**: `nvidia-smi topo -m` analysis
- **Dual RTX 3090 Optimization**: Specialized configuration for RTX 3090s
- **Tensor Parallelism**: Automatic `VLLM_TENSOR_PARALLEL_SIZE=2` configuration
- **Memory Optimization**: GPU memory utilization tuning (0.8-0.9)
- **Device Ordering**: PCI_BUS_ID optimization for NVLink

### Restoration Commands
```bash
# Restore GPU configuration script
git show cursor-env-audit:scripts/configure-gpu.sh > scripts/configure-gpu.sh
chmod +x scripts/configure-gpu.sh

# Restore GPU documentation
git show cursor-env-audit:MULTI_GPU_CONFIGURATION_GUIDE.md > MULTI_GPU_CONFIGURATION_GUIDE.md

# Test GPU detection
./scripts/configure-gpu.sh --detect
```

## 2. 🧹 Docker Environment Wipe Restoration

### Current State Analysis
- ✅ Basic cleanup exists (`docker system prune -f` in start-environment.sh)
- ❌ **Missing**: Complete environment reset (`first-run` mode)
- ❌ **Missing**: Database volume clearing
- ❌ **Missing**: Network cleanup
- ❌ **Missing**: Secure secrets regeneration

### Lost Functionality
The `cursor-env-audit` branch had a comprehensive environment wipe system:

```bash
# Complete environment reset
./start-environment.sh first-run  # Nuclear option - wipes everything
```

**Key Features Lost**:
- **Complete Database Wipe**: PostgreSQL data volume removal
- **Network Cleanup**: All multimodal networks removed
- **Container Pruning**: Orphaned container cleanup
- **Volume Management**: Complete volume deletion with safety checks
- **Secrets Regeneration**: Fresh secure secrets after wipe
- **Environment File Backup**: Automatic backup before wipe

### Current vs Lost Functionality

| Feature | Current | Lost |
|---------|---------|------|
| Basic cleanup | ✅ `docker system prune -f` | - |
| Container cleanup | ❌ | ✅ Complete multimodal container removal |
| Volume cleanup | ❌ | ✅ PostgreSQL data volume deletion |
| Network cleanup | ❌ | ✅ All multimodal network removal |
| Secrets regeneration | ❌ | ✅ Fresh secrets after wipe |
| Safety checks | ❌ | ✅ Sudo requirement, confirmation prompts |

### Restoration Commands
```bash
# The first-run functionality is already in start-environment.sh but may be incomplete
# Let's verify what's missing and restore the complete functionality

# Check current first-run implementation
grep -A 50 "first_run_setup" start-environment.sh

# If incomplete, restore from cursor-env-audit
git show cursor-env-audit:start-environment.sh > start-environment.sh.backup
# Then manually merge the first_run_setup function
```

## 3. 🔒 Hardcoded Values Reversion

### Current Security Issues
The current system has several hardcoded security vulnerabilities:

#### Critical Issues Found:
```bash
# In schemas/compose-schema.yaml
POSTGRES_USER=${POSTGRES_USER:-postgres}           # ❌ Hardcoded default
MINIO_ROOT_USER=${MINIO_ROOT_USER:-minioadmin}     # ❌ Hardcoded default

# In services/multimodal-worker/app/config.py  
postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")     # ❌ Hardcoded default
minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")     # ❌ Hardcoded default
minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")     # ❌ Hardcoded default

# In services/ai-agents/app/config.py
postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")     # ❌ Hardcoded default
```

### Security Risk Assessment
- **Database Security**: Hardcoded `postgres` password allows unauthorized access
- **Storage Security**: Hardcoded `minioadmin` credentials expose object storage
- **Production Risk**: Default credentials will be used in production if not explicitly set

### Required Fixes

#### 1. Remove Hardcoded Defaults from Schema
```yaml
# BEFORE (Insecure)
POSTGRES_USER=${POSTGRES_USER:-postgres}

# AFTER (Secure)  
POSTGRES_USER=${POSTGRES_USER}
```

#### 2. Remove Hardcoded Defaults from Service Configs
```python
# BEFORE (Insecure)
postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")

# AFTER (Secure)
postgres_password: str = os.getenv("POSTGRES_PASSWORD")
if not postgres_password:
    raise ValueError("POSTGRES_PASSWORD environment variable is required")
```

## 🚀 Focused Restoration Script

Create a targeted restoration script for these three critical features:

```bash
#!/bin/bash
# Focused Restoration - Critical Operational Features Only

set -e

echo "🎯 Focused Restoration - Critical Operational Features"
echo "====================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. Restore GPU/NVLink Optimization
echo -e "${BLUE}🎮 Restoring GPU/NVLink Optimization...${NC}"
git show cursor-env-audit:scripts/configure-gpu.sh > scripts/configure-gpu.sh
git show cursor-env-audit:MULTI_GPU_CONFIGURATION_GUIDE.md > MULTI_GPU_CONFIGURATION_GUIDE.md
chmod +x scripts/configure-gpu.sh
echo -e "${GREEN}✅ GPU optimization restored${NC}"

# 2. Verify Docker Wipe Functionality
echo -e "${BLUE}🧹 Checking Docker Environment Wipe...${NC}"
if grep -q "first_run_setup" start-environment.sh; then
    echo -e "${GREEN}✅ Docker wipe functionality exists${NC}"
    echo -e "${YELLOW}💡 Usage: ./start-environment.sh first-run${NC}"
else
    echo -e "${RED}❌ Docker wipe functionality missing${NC}"
    echo -e "${YELLOW}🔧 Restoring from cursor-env-audit...${NC}"
    # Restore first_run_setup function
fi

# 3. Fix Hardcoded Security Issues
echo -e "${BLUE}🔒 Fixing Hardcoded Security Issues...${NC}"

# Fix schema defaults
sed -i 's/POSTGRES_USER=${POSTGRES_USER:-postgres}/POSTGRES_USER=${POSTGRES_USER}/g' schemas/compose-schema.yaml
sed -i 's/MINIO_ROOT_USER=${MINIO_ROOT_USER:-minioadmin}/MINIO_ROOT_USER=${MINIO_ROOT_USER}/g' schemas/compose-schema.yaml

# Fix service config defaults
sed -i 's/os.getenv("POSTGRES_PASSWORD", "postgres")/os.getenv("POSTGRES_PASSWORD")/g' services/*/app/config.py
sed -i 's/os.getenv("MINIO_ACCESS_KEY", "minioadmin")/os.getenv("MINIO_ACCESS_KEY")/g' services/*/app/config.py
sed -i 's/os.getenv("MINIO_SECRET_KEY", "minioadmin")/os.getenv("MINIO_SECRET_KEY")/g' services/*/app/config.py

echo -e "${GREEN}✅ Hardcoded security issues fixed${NC}"

# Test restored functionality
echo -e "${BLUE}🧪 Testing Restored Functionality...${NC}"

# Test GPU detection
if ./scripts/configure-gpu.sh --detect 2>/dev/null; then
    echo -e "${GREEN}✅ GPU detection working${NC}"
else
    echo -e "${YELLOW}⚠️  GPU detection test inconclusive (may be expected on non-GPU systems)${NC}"
fi

# Test environment wipe
if grep -q "first_run_setup" start-environment.sh; then
    echo -e "${GREEN}✅ Docker wipe functionality available${NC}"
else
    echo -e "${RED}❌ Docker wipe functionality still missing${NC}"
fi

# Test security fixes
if ! grep -q ":-postgres" schemas/compose-schema.yaml; then
    echo -e "${GREEN}✅ Hardcoded defaults removed from schema${NC}"
else
    echo -e "${RED}❌ Some hardcoded defaults still present${NC}"
fi

echo -e "${GREEN}🎉 Focused restoration completed!${NC}"
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Test GPU configuration: ./scripts/configure-gpu.sh --detect"
echo "2. Test environment wipe: ./start-environment.sh first-run (DESTRUCTIVE!)"
echo "3. Verify no hardcoded values remain"
echo "4. Generate fresh secrets: python3 setup_secrets.py"
```

## ⚡ Immediate Actions

### Priority 1: Security Fix (5 minutes)
```bash
# Remove hardcoded defaults immediately
sed -i 's/:-postgres//g' schemas/compose-schema.yaml
sed -i 's/:-minioadmin//g' schemas/compose-schema.yaml
sed -i 's/, "postgres")//g' services/*/app/config.py
sed -i 's/, "minioadmin")//g' services/*/app/config.py
```

### Priority 2: GPU Optimization (10 minutes)
```bash
# Restore GPU configuration
git show cursor-env-audit:scripts/configure-gpu.sh > scripts/configure-gpu.sh
chmod +x scripts/configure-gpu.sh
./scripts/configure-gpu.sh --detect
```

### Priority 3: Docker Wipe Verification (5 minutes)
```bash
# Verify wipe functionality
grep -A 10 "first_run_setup" start-environment.sh
# If missing, restore the complete function
```

## 🎯 Success Criteria

- [ ] **GPU Detection**: `./scripts/configure-gpu.sh --detect` works correctly
- [ ] **Multi-GPU Config**: Dual RTX 3090 configuration available
- [ ] **Environment Wipe**: `./start-environment.sh first-run` completely resets environment
- [ ] **Security**: No hardcoded passwords or secrets in configuration files
- [ ] **Database Wipe**: PostgreSQL data volumes are completely removed during wipe

---

**Estimated Restoration Time**: 20-30 minutes  
**Risk Level**: Low (focused, targeted changes)  
**Testing Required**: GPU detection, environment wipe, security validation
