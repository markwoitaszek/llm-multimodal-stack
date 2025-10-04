# Environment Configuration Guide - LLM Multimodal Stack

## 🎯 Overview

The LLM Multimodal Stack uses a **unified schema-driven approach** for environment configuration management. This system centralizes all environment definitions in a single YAML schema file and uses Jinja2 templates to generate secure, consistent configurations across all environments.

**Current Status**: Streamlined Makefile with essential commands by default and all extended functionality preserved. Interactive wipe mode restored with proper preview functionality.

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

# Essential environment commands (streamlined)
make start-dev         # Development environment
make start-staging     # Staging environment  
make start-dev-gpu     # Development with GPU support
make start-staging-gpu # Staging with GPU support

# Extended environment commands (via make help-extended)
make start-prod        # Production environment
make start-gpu         # GPU-optimized environment
make start-monitoring  # Monitoring with ELK stack
```

### Enhanced GPU Workflow
```bash
# Essential GPU commands (streamlined)
make start-dev-gpu     # Development with GPU support
make start-staging-gpu # Staging with GPU support

# Manual GPU configuration (if needed)
make detect-gpu        # Detect RTX 3090s and NVLink topology
make configure-gpu     # Configure optimal GPU settings
```

**✅ GPU Configuration Fixes Applied:**
- Fixed GPU configuration display showing correct values (CUDA_VISIBLE_DEVICES: 0,1, GPU_COUNT: 2)
- Enhanced GPU script to ensure proper environment file synchronization
- Eliminated duplicate GPU configuration script execution
- Fixed missing GPU_COUNT variable in environment files

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

### 4. GPU-Optimized Development Environment
**Purpose**: High-performance development with dual RTX 3090s  
**Command**: `make start-dev-gpu`

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

### 5. GPU-Optimized Staging Environment
**Purpose**: High-performance staging with dual RTX 3090s  
**Command**: `make start-staging-gpu`

### 6. Monitoring Environment (Extended Command)
**Purpose**: Centralized logging and monitoring  
**Command**: `make start-monitoring` (via `make help-extended`)

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

### Comprehensive Stop Commands

**✅ Enhanced Stop Functionality:**
- **`make stop`** - Basic stop (main compose file only)
- **`make stop-all`** - **NEW** - Stops ALL services from ALL compose files (recommended)
- **`make stop-dev`** - Stop development environment only
- **`make stop-staging`** - Stop staging environment only  
- **`make stop-prod`** - Stop production environment only
- **`make stop-gpu`** - Stop GPU services only

**Benefits of `make stop-all`:**
- Handles all 15+ compose files in the system
- Includes automatic cleanup of orphaned containers and networks
- Prevents issues with services running from multiple compose files
- Provides clear output showing what's being stopped at each step

### Comprehensive Environment Reset

```bash
# Nuclear wipe (recommended for complete reset)
make wipe-nuclear
# 🚨 DANGER: This will COMPLETELY DESTROY your entire environment!
# Shows system status and prompts: Type 'NUKE' to confirm

# Legacy wipe (deprecated - use wipe-nuclear instead)
make wipe
# ⚠️  DEPRECATED: 'make wipe' is deprecated. Use 'make wipe-nuclear' instead.

# Detailed preview wipe (alternative method)
./scripts/wipe-environment-fixed.sh preview  # Detailed preview
./scripts/wipe-environment-fixed.sh wipe     # Script with confirmation

# Nuclear reset option (wipe + setup)
make reset
# Wipes everything + regenerates from scratch
```

**What Gets Wiped (Nuclear)**:
- ALL multimodal containers and services
- ALL PostgreSQL database volumes (DATA LOSS!)
- ALL MinIO object storage volumes (DATA LOSS!)
- ALL Redis cache volumes (DATA LOSS!)
- ALL multimodal networks
- ALL orphaned containers and volumes
- Generated compose files

### Targeted Wipe Options (Extended Commands)

For more granular control, use targeted wipe commands via `make help-extended`:

```bash
# Stack-based wipes (preserve other stacks)
make wipe-core          # Core infrastructure only (postgres, redis, qdrant, minio)
make wipe-inference     # Inference services only (vllm, litellm)
make wipe-ai           # AI services only (multimodal-worker, retrieval-proxy, etc.)
make wipe-ui           # UI services only (openwebui, n8n, nginx)
make wipe-testing      # Testing services only (allure, jmeter)
make wipe-monitoring   # Monitoring services only (prometheus, grafana, elk)

# Data-type wipes (preserve other data)
make wipe-db           # Database volumes only (postgres)
make wipe-cache        # Cache volumes only (redis)
make wipe-models       # Model storage only (minio models bucket)
make wipe-logs         # Log volumes only
```

**Benefits of Targeted Wipes**:
- **Precision**: Only remove what's needed
- **Speed**: Faster than nuclear wipe
- **Safety**: Preserve other stacks and data
- **Debugging**: Isolate specific issues
- **Development**: Quick reset of specific components

### Routine Maintenance

```bash
# Clean up containers and volumes
make clean

# Stop services (choose appropriate command)
make stop                   # Stop main services (basic)
make stop-all               # Stop ALL services from ALL compose files (recommended)
make stop-staging           # Stop staging environment only
make stop-dev               # Stop development environment only

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

#### **Multi-GPU Configuration (RTX 3090s)**
```bash
# NVLink Optimization Settings
CUDA_VISIBLE_DEVICES=0,1
NVIDIA_VISIBLE_DEVICES=0,1
CUDA_DEVICE_ORDER=PCI_BUS_ID
VLLM_TENSOR_PARALLEL_SIZE=2
VLLM_PIPELINE_PARALLEL_SIZE=1
GPU_COUNT=2
VLLM_GPU_MEMORY_UTILIZATION=0.8
```

#### **Single GPU Configuration (Fallback)**
```bash
# Single GPU Settings
CUDA_VISIBLE_DEVICES=0
NVIDIA_VISIBLE_DEVICES=0
CUDA_DEVICE_ORDER=PCI_BUS_ID
VLLM_TENSOR_PARALLEL_SIZE=1
VLLM_PIPELINE_PARALLEL_SIZE=1
GPU_COUNT=1
VLLM_GPU_MEMORY_UTILIZATION=0.8
```

#### **CPU-Only Configuration (CI/CD)**
```bash
# No GPU environment variables needed
# Uses CPU-only mode
```

### NVLink Optimization

#### **RTX 3090 NVLink Configuration**
The RTX 3090 supports NVLink 3.0 with the following specifications:
- **Bandwidth**: 600 GB/s bidirectional
- **Latency**: Ultra-low latency for GPU-to-GPU communication
- **Topology**: Direct GPU-to-GPU connection

#### **vLLM Tensor Parallelism**
Tensor parallelism splits the model across multiple GPUs:
- **Model Sharding**: Each GPU holds a portion of the model
- **Communication**: NVLink enables fast inter-GPU communication
- **Memory Efficiency**: Reduces per-GPU memory requirements
- **Performance**: Near-linear scaling with proper NVLink setup

### Performance Tuning

#### **GPU Memory Utilization by Environment**

| Environment | Memory Utilization | Rationale |
|-------------|-------------------|-----------|
| Development | 0.8 (80%) | Balanced performance and stability |
| Staging | 0.85 (85%) | Higher utilization for testing |
| Production | 0.9 (90%) | Maximum performance |
| Optimized | 0.9 (90%) | Reduced from 0.95 for stability |

#### **Worker Configuration**

**Multi-GPU Setup:**
- LiteLLM Workers: 8
- Multimodal Worker Processes: 4
- Retrieval Proxy Workers: 8

**Single GPU Setup:**
- LiteLLM Workers: 4
- Multimodal Worker Processes: 2
- Retrieval Proxy Workers: 4

## 📊 Available Makefile Targets

### Essential Commands (Default)
```bash
make help                   # Show essential commands (15 total)
make setup                  # Complete setup from scratch
make start-dev              # Start development environment
make start-staging          # Start staging environment
make start-dev-gpu          # Start development with GPU support
make start-staging-gpu      # Start staging with GPU support
make detect-gpu             # Detect GPU configuration
make configure-gpu          # Configure GPU for optimal performance
make stop                   # Stop main services (basic)
make stop-all               # Stop ALL services from ALL compose files
make stop-dev               # Stop development environment
make stop-staging           # Stop staging environment
make stop-prod              # Stop production environment
make wipe-nuclear           # Nuclear wipe (complete destruction - type 'NUKE')
make reset                  # Nuclear reset (wipe + setup)
make status                 # Show status of all services
make logs                   # View logs for all services
make help-extended          # Show all extended commands (100+)
```

### Extended Commands (via make help-extended)
```bash
# Schema & Compose Management
make validate-schema        # Validate unified schema
make generate-compose       # Generate all compose files
make setup-secrets          # Generate environment files and secrets
make validate-security      # Validate no hardcoded defaults

# Extended Environment Management
make start-prod             # Start production environment
make start-gpu              # Start GPU-optimized environment
make start-monitoring       # Start monitoring environment

# Stack Management
make start-{core,inference,ai,ui,testing,monitoring}  # Individual stacks
make stop-{core,inference,ai,ui,testing,monitoring}   # Stop individual stacks
make restart-{core,inference,ai,ui,testing,monitoring} # Restart individual stacks

# Network Management
make check-network-conflicts  # Check for network conflicts
make validate-networks        # Validate network configuration
make cleanup-networks         # Clean up orphaned networks

# Wipe Management
make wipe-nuclear             # Nuclear wipe (complete destruction - type 'NUKE')
make wipe-{core,inference,ai,ui,testing,monitoring}  # Stack-specific wipes
make wipe-{db,cache,models,logs}  # Data-type specific wipes

# Testing Framework
make start-testing          # Start testing environment
make test-allure            # Run tests with Allure reporting
make test-jmeter            # Run JMeter performance tests
make test-{unit,integration,api,performance}  # Specific test types

# Data Management
make retention-{status,cleanup,test}  # Data retention management
make backup-{status,full,list,verify} # Backup management
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
make stop-all               # Stop ALL services (recommended)
```

### GPU Development Workflow
```bash
# Essential GPU development (streamlined)
make setup
make start-dev-gpu

# Check GPU utilization
nvidia-smi

# Monitor services
make logs
```

### Production Deployment Workflow (Extended Commands)
```bash
# Access extended commands
make help-extended

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
# Nuclear wipe (recommended for complete reset)
make wipe-nuclear
# Type 'NUKE' to confirm complete destruction

# Alternative: Detailed preview
./scripts/wipe-environment-fixed.sh preview
./scripts/wipe-environment-fixed.sh wipe

# Nuclear reset (wipe + setup)
make reset

# Verify fresh setup
make validate-security
make start-dev
```

### Targeted Reset Workflow (Extended Commands)
```bash
# Access extended commands
make help-extended

# For specific issues (preserve other data)
make wipe-ui           # Only reset UI services (fixes n8n issues)
make wipe-core         # Only reset infrastructure (postgres, redis)
make wipe-cache        # Only clear cache (redis volumes)

# For development workflow
make wipe-ai           # Reset AI services only
make wipe-testing      # Reset testing environment only
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
# Nuclear wipe (complete reset)
make wipe-nuclear
# Type 'NUKE' to confirm

# Or detailed preview wipe
./scripts/wipe-environment-fixed.sh wipe

# Complete environment reset (wipe + setup)
make reset

# For specific issues (preserve other data)
make wipe-ui           # Fix UI/n8n issues only
make wipe-core         # Reset infrastructure only
```

### Getting Help

```bash
# Show essential commands (default)
make help

# Show all extended commands (100+)
make help-extended

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

**Last Updated**: January 2025  
**Compatible With**: Streamlined Makefile + Nuclear Wipe + Essential/Extended Commands  
**Schema Version**: Unified compose schema v1.0  
**Essential Commands**: 16 (streamlined for daily use)  
**Extended Commands**: 100+ (accessible via `make help-extended`)  
**Wipe Modes**: 4 (nuclear, targeted, detailed preview, legacy deprecated)  
**Targeted Wipe Options**: 12+ (stack-specific and data-type specific)
