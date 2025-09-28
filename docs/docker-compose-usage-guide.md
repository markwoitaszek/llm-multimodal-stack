# 🐳 Docker Compose Usage Guide

## 📋 **Overview**

The Multimodal LLM Stack uses multiple Docker Compose configurations for different environments and use cases. This guide explains each configuration and when to use them.

## 📁 **Available Configurations**

### **Core Files**

#### **1. `docker-compose.yml` - Main Development**
- **Purpose**: Complete development stack with all services
- **Size**: 13.9KB
- **Services**: All Phase 1 + Phase 2 services
- **Usage**: Primary development environment

#### **2. `docker-compose.optimized.yml` - Performance Optimized**
- **Purpose**: Build cache optimization and performance improvements
- **Size**: 15.0KB
- **Services**: All services with optimized builds
- **Usage**: Recommended for development (faster builds)

### **Environment-Specific Files**

#### **3. `docker-compose.prod.yml` - Production**
- **Purpose**: Production deployment with monitoring and security
- **Size**: 6.9KB
- **Services**: Production overrides + monitoring stack
- **Usage**: Production deployment

#### **4. `docker-compose.test.yml` - Testing**
- **Purpose**: Isolated testing environment
- **Size**: 4.0KB
- **Services**: Test databases and debug services
- **Usage**: Running tests and debugging

#### **5. `docker-compose.enhanced-postgres.yml` - Database**
- **Purpose**: Enhanced PostgreSQL with Supabase-like features
- **Size**: 2.3KB
- **Services**: PostgREST, pgAdmin, performance tuning
- **Usage**: Database development and management

### **Override Files**

#### **6. `docker-compose.override.yml` - GPU Settings**
- **Purpose**: GPU resource allocation and tensor parallelism
- **Size**: 1.2KB
- **Services**: GPU configuration overrides with multi-GPU support
- **Usage**: Automatically loaded (GPU systems)

#### **7. `docker-compose.multi-gpu.yml` - Multi-GPU Configuration**
- **Purpose**: Dedicated multi-GPU setup with tensor parallelism
- **Size**: 3.1KB
- **Services**: vLLM with tensor-parallel-size=2, multimodal-worker
- **Usage**: Dual RTX 3090 systems with NVLink

---

## 🚀 **Usage Instructions**

### **Development Environments**

#### **Standard Development**
```bash
# Start all services for development
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### **Optimized Development (Recommended)**
```bash
# Start with optimized builds (faster subsequent builds)
docker-compose -f docker-compose.optimized.yml up -d

# View logs
docker-compose -f docker-compose.optimized.yml logs -f

# Stop services
docker-compose -f docker-compose.optimized.yml down
```

#### **Multi-GPU Development (Dual RTX 3090)**
```bash
# Start with tensor parallelism on both GPUs
docker-compose -f docker-compose.optimized.yml -f docker-compose.override.yml up -d

# Alternative: Use dedicated multi-GPU configuration
docker-compose -f docker-compose.multi-gpu.yml up -d

# Check GPU utilization
nvidia-smi

# Test tensor parallelism
curl -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "microsoft/DialoGPT-small", "prompt": "Hello", "max_tokens": 50}'
```

### **Testing Environment**

#### **Run Tests**
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run tests (example)
docker-compose -f docker-compose.test.yml exec multimodal-worker-test python -m pytest

# Stop test environment
docker-compose -f docker-compose.test.yml down
```

### **Production Deployment**

#### **Production Setup**
```bash
# Start production stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View production logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Stop production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
```

### **Database Development**

#### **Enhanced PostgreSQL**
```bash
# Start enhanced database stack
docker-compose -f docker-compose.enhanced-postgres.yml up -d

# Access pgAdmin: http://localhost:5050
# Access PostgREST API: http://localhost:3001

# Stop enhanced database
docker-compose -f docker-compose.enhanced-postgres.yml down
```

---

## 🔧 **Configuration Details**

### **Service Ports**

| Service | Port | Purpose |
|---------|------|---------|
| **vLLM** | 8000 | LLM inference |
| **Multimodal Worker** | 8001 | Media processing |
| **Retrieval Proxy** | 8002 | Search and retrieval |
| **AI Agents** | 8003 | Agent framework |
| **Search Engine** | 8004 | Search service |
| **Memory System** | 8005 | Memory management |
| **User Management** | 8006 | Authentication |
| **LiteLLM** | 4000 | LLM proxy |
| **OpenWebUI** | 3030 | Web interface |
| **AI Agents Web** | 3001 | Agent web interface |
| **n8n** | 5678 | Workflow automation |
| **PostgreSQL** | 5432 | Database |
| **Redis** | 6379 | Cache |
| **Qdrant** | 6333 | Vector database |
| **MinIO** | 9000 | Object storage |

### **Test Environment Ports**

| Service | Port | Purpose |
|---------|------|---------|
| **PostgreSQL Test** | 5433 | Test database |
| **Redis Test** | 6380 | Test cache |
| **Qdrant Test** | 6334 | Test vector DB |
| **MinIO Test** | 9001 | Test storage |
| **Multimodal Worker Test** | 8004 | Test worker |
| **Retrieval Proxy Test** | 8005 | Test proxy |
| **AI Agents Test** | 8006 | Test agents |

### **Production Monitoring Ports**

| Service | Port | Purpose |
|---------|------|---------|
| **Prometheus** | 9090 | Metrics collection |
| **Grafana** | 3001 | Monitoring dashboard |
| **Nginx** | 80/443 | Reverse proxy |
| **pgAdmin** | 5050 | Database management |
| **PostgREST** | 3001 | Database API |

---

## 🛠️ **Advanced Usage**

### **Custom Configurations**

#### **Combine Multiple Files**
```bash
# Development with enhanced database
docker-compose -f docker-compose.yml -f docker-compose.enhanced-postgres.yml up -d

# Production with optimized builds
docker-compose -f docker-compose.optimized.yml -f docker-compose.prod.yml up -d
```

#### **Environment Variables**
```bash
# Set custom environment
export POSTGRES_PASSWORD=mysecurepassword
export VLLM_MODEL=microsoft/DialoGPT-medium

# Start with custom environment
docker-compose up -d
```

### **Build Commands**

#### **Build Specific Services**
```bash
# Build only multimodal worker
docker-compose build multimodal-worker

# Build with no cache
docker-compose build --no-cache multimodal-worker

# Build optimized services
docker-compose -f docker-compose.optimized.yml build
```

#### **Scale Services**
```bash
# Scale multimodal worker (production)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale multimodal-worker=2
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Port Conflicts**
```bash
# Check port usage
netstat -tulpn | grep :8000

# Use different ports
docker-compose -f docker-compose.test.yml up -d
```

#### **Service Health Checks**
```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs service-name

# Restart specific service
docker-compose restart service-name
```

#### **Volume Issues**
```bash
# Remove volumes (WARNING: data loss)
docker-compose down -v

# Recreate volumes
docker-compose up -d
```

### **Performance Issues**

#### **Memory Usage**
```bash
# Check resource usage
docker stats

# Limit memory usage
docker-compose -f docker-compose.prod.yml up -d
```

#### **Build Performance**
```bash
# Use optimized builds
docker-compose -f docker-compose.optimized.yml up -d

# Clean build cache
docker system prune -a
```

#### **GPU Issues**
```bash
# Check GPU status
nvidia-smi

# Check NVLink status
nvidia-smi nvlink --status

# Check GPU topology
nvidia-smi topo -m

# Restart with tensor parallelism
docker-compose -f docker-compose.optimized.yml -f docker-compose.override.yml restart vllm

# Check vLLM logs for GPU issues
docker logs multimodal-vllm --tail 50
```

---

## 📊 **Best Practices**

### **Development Workflow**

1. **Start with optimized configuration** for faster builds
2. **Use test environment** for running tests
3. **Use enhanced database** for database development
4. **Clean up regularly** to free disk space

### **Production Deployment**

1. **Use production configuration** with monitoring
2. **Set secure environment variables**
3. **Enable resource limits**
4. **Monitor with Prometheus/Grafana**

### **Maintenance**

1. **Regular cleanup** of unused images and volumes
2. **Update base images** regularly
3. **Monitor resource usage**
4. **Backup important data**

---

## 🎯 **Quick Reference**

### **Most Common Commands**

```bash
# Development (recommended)
docker-compose -f docker-compose.optimized.yml up -d

# Testing
docker-compose -f docker-compose.test.yml up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Database development
docker-compose -f docker-compose.enhanced-postgres.yml up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### **File Selection Guide**

| Use Case | Configuration | Command |
|----------|---------------|---------|
| **Development** | Optimized | `docker-compose -f docker-compose.optimized.yml up -d` |
| **Testing** | Test | `docker-compose -f docker-compose.test.yml up -d` |
| **Production** | Main + Prod | `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d` |
| **Database Dev** | Enhanced DB | `docker-compose -f docker-compose.enhanced-postgres.yml up -d` |
| **GPU Systems** | Main + Override | `docker-compose up -d` (auto-loads override) |
| **Multi-GPU (RTX 3090)** | Optimized + Override | `docker-compose -f docker-compose.optimized.yml -f docker-compose.override.yml up -d` |
| **Dedicated Multi-GPU** | Multi-GPU Config | `docker-compose -f docker-compose.multi-gpu.yml up -d` |

---

This guide provides comprehensive instructions for using all Docker Compose configurations in the Multimodal LLM Stack. Choose the appropriate configuration for your use case and follow the best practices for optimal performance.
