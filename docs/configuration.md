# Configuration Guide

This guide covers detailed configuration options for the Multimodal LLM Stack.

## Environment Variables

**⚠️ Important**: Phase-6A uses a production-grade secrets management system. Environment variables are automatically generated and managed securely.

### Setup Secrets Management

```bash
# Generate secure secrets and environment files
python3 setup_secrets.py
```

This creates:
- `.env.development` - Development environment variables
- `secrets/.env.development.json` - Encrypted secrets storage
- `docker-compose.development.override.yml` - Docker overrides
- `k8s-secrets-development.yaml` - Kubernetes secrets template

### Database Configuration

```env
# PostgreSQL Settings (auto-generated)
POSTGRES_DB=multimodal                    # Database name
POSTGRES_USER=postgres                    # Database user
POSTGRES_PASSWORD=<secure_password>       # Database password (auto-generated)
POSTGRES_HOST=postgres                    # Database host
POSTGRES_PORT=5432                        # Database port
```

### Storage Configuration

```env
# MinIO S3-Compatible Storage
MINIO_ROOT_USER=minioadmin               # MinIO admin username
MINIO_ROOT_PASSWORD=your_secure_password # MinIO admin password (auto-generated)

# Storage Paths (for seismic-nvme integration)
QDRANT_DATA_PATH=/mnt/nvme/qdrant        # Qdrant data directory
POSTGRES_DATA_PATH=/mnt/nvme/postgres    # PostgreSQL data directory  
MINIO_DATA_PATH=/mnt/nvme/minio          # MinIO data directory
CACHE_PATH=/mnt/nvme/cache               # Model and processing cache
```

### Model Configuration

```env
# vLLM Configuration
VLLM_MODEL=microsoft/DialoGPT-medium     # LLM model to load
VLLM_API_KEY=your_secure_api_key         # API key for vLLM (auto-generated)
VLLM_HOST=0.0.0.0                        # vLLM host
VLLM_PORT=8000                           # vLLM port

# LiteLLM Configuration  
LITELLM_MASTER_KEY=sk-your_master_key    # Master key for LiteLLM (auto-generated)
LITELLM_SALT_KEY=sk-your_salt_key        # Salt key for encryption (auto-generated)
LITELLM_PORT=4000                        # LiteLLM port
```

### Service Configuration

```env
# Service Ports
VLLM_PORT=8000                           # vLLM inference server
LITELLM_PORT=4000                        # LiteLLM proxy router
MULTIMODAL_WORKER_PORT=8001              # Multimodal worker service
RETRIEVAL_PROXY_PORT=8002                # Retrieval proxy service
AI_AGENTS_PORT=8003                      # AI agents service
SEARCH_ENGINE_PORT=8004                  # Search engine service
MEMORY_SYSTEM_PORT=8005                  # Memory system service
USER_MANAGEMENT_PORT=8006                # User management service
OPENWEBUI_PORT=3030                      # OpenWebUI interface
QDRANT_HTTP_PORT=6333                    # Qdrant HTTP port
QDRANT_GRPC_PORT=6334                    # Qdrant gRPC port
REDIS_PORT=6379                          # Redis port
MINIO_PORT=9000                          # MinIO API port
MINIO_CONSOLE_PORT=9002                  # MinIO console port

# Additional Service Ports
IDE_BRIDGE_PORT=8007                     # IDE bridge service
IDE_BRIDGE_WEB_PORT=3002                 # IDE bridge web interface
N8N_MONITORING_PORT=8008                 # n8n monitoring service
N8N_MONITORING_DASHBOARD_PORT=3003       # n8n monitoring dashboard
N8N_PORT=5678                            # n8n workflow platform
REALTIME_COLLABORATION_PORT=3006         # Real-time collaboration service

# Service Hosts
VLLM_HOST=0.0.0.0                        # vLLM host
QDRANT_HOST=qdrant                       # Qdrant host
POSTGRES_HOST=postgres                   # PostgreSQL host
REDIS_HOST=redis                         # Redis host
MINIO_ENDPOINT=minio:9000                # MinIO endpoint
IDE_BRIDGE_HOST=0.0.0.0                  # IDE bridge host
N8N_MONITORING_HOST=0.0.0.0              # n8n monitoring host
N8N_HOST=localhost                       # n8n host

# Service URLs (Internal Communication)
MULTIMODAL_WORKER_URL=http://multimodal-worker:8001
RETRIEVAL_PROXY_URL=http://retrieval-proxy:8002
SEARCH_ENGINE_URL=http://search-engine:8004
MEMORY_SYSTEM_URL=http://memory-system:8005
USER_MANAGEMENT_URL=http://user-management:8006
LLM_BASE_URL=http://vllm:8000/v1
OPENAI_API_BASE_URL=http://vllm:8000/v1
AI_AGENTS_URL=http://ai-agents:8003
IDE_BRIDGE_URL=http://ide-bridge:8007
N8N_URL=http://n8n:5678
```

### GPU Configuration

```env
CUDA_VISIBLE_DEVICES=0                   # GPU device to use (0 for first GPU)
```

### Web Interface

```env
WEBUI_SECRET_KEY=your_webui_secret       # Secret key for OpenWebUI (auto-generated)
```

## Model Selection

### LLM Models (vLLM)

Choose from these popular models by setting `VLLM_MODEL`:

**Small/Fast Models:**
- `microsoft/DialoGPT-medium` (default, ~350MB)
- `microsoft/DialoGPT-large` (~750MB)
- `distilgpt2` (~320MB)

**Medium Models:**
- `gpt2-medium` (~1.5GB)
- `gpt2-large` (~3GB)
- `EleutherAI/gpt-neo-1.3B` (~5GB)

**Large Models (requires more VRAM):**
- `EleutherAI/gpt-neo-2.7B` (~11GB)
- `EleutherAI/gpt-j-6B` (~24GB)
- `meta-llama/Llama-2-7b-chat-hf` (~13GB, requires approval)
- `mistralai/Mistral-7B-Instruct-v0.1` (~13GB)

**RTX 3090 Recommendations:**
- For 24GB VRAM: Use models up to 7B parameters
- For optimal performance: `microsoft/DialoGPT-large` or `EleutherAI/gpt-neo-2.7B`

### Multimodal Models

The following models are automatically configured:

**Vision Models:**
- CLIP: `openai/clip-vit-base-patch32` (image embeddings)
- BLIP-2: `Salesforce/blip-image-captioning-base` (image captioning)

**Audio Models:**
- Whisper: `openai/whisper-base` (audio transcription)

**Text Models:**
- Sentence Transformers: `sentence-transformers/all-MiniLM-L6-v2` (text embeddings)

## Storage Configuration

### NVMe Integration

If you have the seismic-nvme storage optimization setup:

```bash
# The setup script will automatically detect and configure NVMe paths
./scripts/setup.sh
```

Manual configuration:
```env
# Update .env with your NVMe mount points
QDRANT_DATA_PATH=/mnt/nvme/qdrant
POSTGRES_DATA_PATH=/mnt/nvme/postgres
MINIO_DATA_PATH=/mnt/nvme/minio
CACHE_PATH=/mnt/nvme/cache
```

### Storage Buckets

MinIO automatically creates these buckets:
- `images` - Processed images and keyframes
- `videos` - Video files
- `documents` - Text documents and metadata

## Service Configuration

### vLLM Settings

Advanced vLLM configuration in `docker-compose.yml`:

```yaml
command: >
  --model ${VLLM_MODEL}
  --host 0.0.0.0
  --port 8000
  --gpu-memory-utilization 0.8    # Use 80% of GPU memory
  --max-model-len 4096            # Maximum sequence length
  --dtype auto                    # Automatic precision
  --api-key ${VLLM_API_KEY}
```

### LiteLLM Router

Configure model routing in `configs/litellm_config.yaml`:

```yaml
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: openai/gpt-3.5-turbo
      api_base: http://vllm:8000/v1
      api_key: vllm-key

router_settings:
  routing_strategy: simple-shuffle
  
general_settings:
  completion_model: local-llm
  master_key: sk-1234
```

### Qdrant Collections

Vector collections are automatically created:
- `text_embeddings` - Text chunk embeddings
- `image_embeddings` - Image and keyframe embeddings  
- `video_embeddings` - Video transcription embeddings

## Security Configuration

### API Keys

All API keys are automatically generated during setup:
```bash
./scripts/setup.sh
```

### Manual Key Generation

```bash
# Generate secure random keys
openssl rand -base64 32
```

### Network Security

By default, all services are exposed on localhost only. For production:

1. **Use reverse proxy** (nginx, traefik)
2. **Enable HTTPS/TLS**
3. **Configure firewall rules**
4. **Use Docker secrets** instead of environment variables

## Performance Tuning

### GPU Memory Management

```env
# Adjust GPU memory utilization
VLLM_GPU_MEMORY_UTILIZATION=0.8    # 80% for vLLM
MULTIMODAL_GPU_MEMORY_FRACTION=0.2  # 20% for multimodal models
```

### Database Optimization

PostgreSQL tuning for large datasets:

```sql
-- Add to sql/init.sql for better performance
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
```

### Vector Store Optimization

Qdrant configuration for better performance:

```yaml
# In docker-compose.yml, add environment variables:
environment:
  - QDRANT__SERVICE__MAX_REQUEST_SIZE_MB=32
  - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=4
  - QDRANT__STORAGE__OPTIMIZERS__MEMMAP_THRESHOLD_KB=200000
```

## Monitoring Configuration

### Health Checks

All services include health checks with configurable intervals:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
  interval: 30s      # Check every 30 seconds
  timeout: 10s       # Timeout after 10 seconds
  retries: 3         # Retry 3 times
  start_period: 60s  # Wait 60s before first check
```

### Logging

Configure log levels:

```env
# Add to .env
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
ENABLE_JSON_LOGS=true       # Structured logging
LOG_FILE_PATH=/app/logs     # Log file location
```

## Development Configuration

### Hot Reload

For development, enable hot reload:

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  multimodal-worker:
    volumes:
      - ./services/multimodal-worker:/app
    command: ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
  
  retrieval-proxy:
    volumes:
      - ./services/retrieval-proxy:/app  
    command: ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]
```

### Debug Mode

Enable debug mode:

```env
DEBUG=true
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
```

## Troubleshooting

### Common Issues

**GPU Not Detected:**
```bash
# Check NVIDIA Docker runtime
docker info | grep nvidia

# Install nvidia-container-toolkit if missing
sudo apt-get install nvidia-container-toolkit
sudo systemctl restart docker
```

**Out of Memory:**
```bash
# Reduce GPU memory utilization
sed -i 's/gpu-memory-utilization 0.8/gpu-memory-utilization 0.6/' docker-compose.yml

# Use smaller models
sed -i 's/VLLM_MODEL=.*/VLLM_MODEL=microsoft\/DialoGPT-medium/' .env
```

**Slow Performance:**
```bash
# Check if using NVMe storage
df -h | grep nvme

# Monitor GPU usage
nvidia-smi -l 1

# Check Docker resource usage
docker stats
```

### Logs and Debugging

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f multimodal-worker

# Check service health
./scripts/health-check.sh

# Run performance tests
./scripts/benchmark.sh
```

