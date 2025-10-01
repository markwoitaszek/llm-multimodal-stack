# Environment Configuration Guide - LLM Multimodal Stack

## 🎯 Overview

The LLM Multimodal Stack uses a **unified schema-driven approach** for environment configuration management. This system centralizes all environment definitions in a single YAML schema file and uses Jinja2 templates to generate secure, consistent configurations across all environments.

## 🏗️ System Architecture

### Current Implementation (Post PR 130 + Enhancements)

```
schemas/
├── compose-schema.yaml          # Unified schema definition (844 lines)
scripts/
├── compose-generator.py         # Schema to compose file generator
├── configure-gpu.sh            # GPU detection and configuration
├── wipe-environment.sh         # Comprehensive environment reset
env-templates/                   # Jinja2 environment templates
├── core.env.j2                 # Core services configuration
├── vllm.env.j2                 # vLLM inference server
├── litellm.env.j2              # LiteLLM proxy
├── master.env.j2               # Combined template
└── [service-specific templates]
compose*.yml                     # Generated compose files (DO NOT EDIT)
Makefile                        # Unified command interface
```

## 🚀 Quick Start

### Prerequisites
```bash
# Check system requirements
make validate-schema    # Validate schema syntax
make detect-gpu         # Detect GPU configuration
```

### Basic Environment Setup
```bash
# Complete setup from scratch
make setup             # Generate compose files + setup secrets + validate

# Start specific environments
make start-dev         # Development environment
make start-staging     # Staging environment  
make start-prod        # Production environment
make start-gpu         # GPU-optimized environment
make start-monitoring  # Monitoring with ELK stack
```

### Enhanced GPU Workflow
```bash
# Auto-detect and configure GPU
make detect-gpu        # Detect RTX 3090s and NVLink topology
make configure-gpu     # Configure optimal GPU settings
make start-gpu-auto    # Start with automatic GPU configuration
```

## 🌍 Available Environments

### 1. Development Environment
**Purpose**: Local development with debugging enabled  
**Command**: `make start-dev`

```bash
# Configuration
- Base: compose.yml
- GPU: Single GPU (CUDA_VISIBLE_DEVICES=0)
- Memory: 8GB minimum
- Services: All core services
- Debug: Enabled
- Log Level: DEBUG
```

**Services Available**:
- LiteLLM: http://localhost:4000
- Multimodal Worker: http://localhost:8001
- Retrieval Proxy: http://localhost:8002
- vLLM: http://localhost:8000
- Qdrant: http://localhost:6333
- MinIO Console: http://localhost:9002

### 2. Staging Environment
**Purpose**: Pre-production testing  
**Command**: `make start-staging`

```bash
# Configuration
- Base: compose.yml + compose.production.yml
- Profiles: services + monitoring
- GPU: Single GPU
- Memory: 12GB minimum
- Services: All base services
- Debug: Disabled
- Log Level: INFO
```

### 3. Production Environment
**Purpose**: Production deployment with full monitoring  
**Command**: `make start-prod`

```bash
# Configuration
- Base: compose.yml + compose.production.yml
- Profiles: services + monitoring
- GPU: Single GPU
- Memory: 20GB minimum
- Services: All base services + Prometheus + Grafana
- Debug: Disabled
- Log Level: WARNING
```

### 4. GPU-Optimized Environment
**Purpose**: High-performance inference with dual RTX 3090s  
**Command**: `make start-gpu` or `make start-gpu-auto`

```bash
# Configuration
- Base: compose.yml + compose.gpu.yml + compose.production.yml
- GPU: Dual RTX 3090 with NVLink optimization
- Memory: 24GB minimum
- CUDA_VISIBLE_DEVICES: 0,1
- VLLM_TENSOR_PARALLEL_SIZE: 2
- GPU Memory Utilization: 0.8-0.9
```

**GPU Detection Results** (Your System):
```
✅ Found 2 NVIDIA GPU(s)
✅ Multi-GPU setup detected
🔗 NVLink Topology:
GPU0   X   NV4  0-31  0   N/A
GPU1  NV4   X   0-31  0   N/A
```

### 5. Monitoring Environment
**Purpose**: Centralized logging and monitoring  
**Command**: `make start-monitoring`

```bash
# Configuration
- Base: compose.yml + compose.elk.yml
- Profiles: elk + monitoring
- GPU: Not required
- Memory: 16GB minimum
- Services: ELK stack (Elasticsearch, Logstash, Kibana)
```

**Services Available**:
- Kibana: http://localhost:5601
- Elasticsearch: http://localhost:9200
- Logstash: http://localhost:9600

## 🔧 Environment Management

### Schema-Driven Configuration

The system uses `schemas/compose-schema.yaml` as the single source of truth:

```yaml
# Example schema structure
version: "3.8"

config:
  project_name: "multimodal"
  network_name: "multimodal-net"
  default_restart_policy: "unless-stopped"

services:
  postgres:
    category: "core"
    image: "postgres:16-alpine"
    environment:
      - "POSTGRES_DB=${POSTGRES_DB}"
      - "POSTGRES_USER=${POSTGRES_USER}"
      - "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}"
    volumes_required: ["postgres_data"]
    profiles: ["services", "monitoring"]

environments:
  development:
    description: "Development environment with core services only"
    services: ["postgres", "redis", "qdrant", "minio", "vllm", "litellm"]
    gpu_required: true
    memory_min_gb: 8
```

### Environment Templates

Jinja2 templates in `env-templates/` provide standardized configuration:

```jinja2
# Example: vllm.env.j2
CUDA_VISIBLE_DEVICES={{ cuda_visible_devices | default('0') }}
VLLM_HOST={{ vllm_host | default('0.0.0.0') }}
VLLM_PORT={{ vllm_port | default('8000') }}
VLLM_MODEL_NAME={{ vllm_model_name | default('microsoft/DialoGPT-medium') }}
VLLM_TENSOR_PARALLEL_SIZE={{ vllm_tensor_parallel_size | default('1') }}
```

## 🔒 Security Configuration

### Secrets Management

The system uses secure secrets generation with no hardcoded defaults:

```bash
# Generate secure secrets
make setup-secrets

# Validate security configuration
make validate-security
```

**Security Features**:
- ✅ No hardcoded passwords or secrets
- ✅ Environment-specific secret generation
- ✅ Secure defaults with validation
- ✅ Secret rotation capabilities

### Environment Variables

**Required Variables** (no defaults):
```bash
POSTGRES_DB=multimodal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<generated_secret>
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=<generated_secret>
JWT_SECRET=<generated_secret>
```

## 🧹 Environment Management

### Comprehensive Environment Reset

```bash
# Complete environment wipe (DESTRUCTIVE!)
make wipe
# ⚠️  WARNING: This will DELETE all data and containers!
# This includes PostgreSQL databases, MinIO data, and all volumes.

# Nuclear reset option
make reset
# Wipes everything + regenerates from scratch
```

**What Gets Wiped**:
- All multimodal containers
- PostgreSQL data volumes
- MinIO data volumes
- All multimodal networks
- Orphaned containers

### Routine Maintenance

```bash
# Clean up containers and volumes
make clean

# Stop all services
make stop

# View logs
make logs

# Check service status
make status
```

## 🎮 GPU Configuration

### Automatic GPU Detection

```bash
# Detect and configure GPU automatically
make detect-gpu
make configure-gpu
make start-gpu-auto
```

### Manual GPU Configuration

```bash
# Run GPU configuration script directly
./scripts/configure-gpu.sh auto      # Auto-detect and configure
./scripts/configure-gpu.sh multi     # Force multi-GPU setup
./scripts/configure-gpu.sh single    # Force single GPU setup
./scripts/configure-gpu.sh cpu       # CPU-only mode
```

### GPU Environment Variables

```bash
# Multi-GPU Configuration (RTX 3090s)
CUDA_VISIBLE_DEVICES=0,1
NVIDIA_VISIBLE_DEVICES=0,1
CUDA_DEVICE_ORDER=PCI_BUS_ID
VLLM_TENSOR_PARALLEL_SIZE=2
VLLM_PIPELINE_PARALLEL_SIZE=1
GPU_COUNT=2
VLLM_GPU_MEMORY_UTILIZATION=0.8
```

## 📊 Available Makefile Targets

### Core Commands
```bash
make help                    # Show all available commands
make setup                   # Complete setup from scratch
make validate-schema         # Validate unified schema
make generate-compose        # Generate all compose files
make setup-secrets          # Generate environment files and secrets
```

### Environment Management
```bash
make start-dev              # Start development environment
make start-staging          # Start staging environment
make start-prod             # Start production environment
make start-gpu              # Start GPU-optimized environment
make start-monitoring       # Start monitoring environment
make stop                   # Stop all services
make logs                   # View logs for all services
make status                 # Show status of all services
```

### Enhanced Features (New)
```bash
make detect-gpu             # Detect GPU configuration
make configure-gpu          # Configure GPU for optimal performance
make start-gpu-auto         # Start GPU environment with auto-detection
make wipe                   # Wipe environment (DESTRUCTIVE!)
make reset                  # Reset and regenerate from scratch
make validate-security      # Validate no hardcoded defaults
```

### Maintenance
```bash
make clean                  # Clean up containers, volumes, and networks
make clean-compose          # Remove all generated compose files
make test-compose           # Test generated compose files for syntax errors
```

## 🔄 Workflow Examples

### Development Workflow
```bash
# Initial setup
make setup

# Start development environment
make start-dev

# Check status
make status

# View logs
make logs

# Stop when done
make stop
```

### GPU Development Workflow
```bash
# Setup with GPU detection
make setup
make detect-gpu
make start-gpu-auto

# Check GPU utilization
nvidia-smi

# Monitor services
make logs
```

### Production Deployment Workflow
```bash
# Validate and setup
make validate-schema
make validate-security
make setup

# Deploy to production
make start-prod

# Monitor deployment
make status
make logs
```

### Environment Reset Workflow
```bash
# Complete reset (when things go wrong)
make wipe
make reset

# Verify fresh setup
make validate-security
make start-dev
```

## 🛠️ Troubleshooting

### Common Issues

**1. Schema Validation Errors**
```bash
make validate-schema
# Fix any syntax errors in schemas/compose-schema.yaml
```

**2. GPU Detection Issues**
```bash
make detect-gpu
# Check nvidia-smi output and CUDA installation
```

**3. Security Validation Failures**
```bash
make validate-security
# Ensure no hardcoded defaults remain
```

**4. Environment Conflicts**
```bash
make wipe
make reset
# Complete environment reset
```

### Getting Help

```bash
# Show all available commands
make help

# Get GPU configuration help
./scripts/configure-gpu.sh help

# Validate system configuration
make validate-schema
make validate-security
```

## 📈 Performance Optimization

### GPU Optimization
- **Dual RTX 3090s**: Automatic NVLink detection and configuration
- **Tensor Parallelism**: Automatic configuration for dual GPU setups
- **Memory Utilization**: Optimized GPU memory usage (0.8-0.9)
- **PCI Bus Ordering**: Optimal GPU device ordering for NVLink

### Environment-Specific Tuning
- **Development**: Lower resource usage, debug enabled
- **Staging**: Production-like with monitoring
- **Production**: Full optimization with monitoring and logging
- **GPU**: Maximum performance with dual GPU utilization

---

**Last Updated**: October 1, 2024  
**Compatible With**: PR 130 + GPU/wipe/security enhancements  
**Schema Version**: Unified compose schema v1.0
