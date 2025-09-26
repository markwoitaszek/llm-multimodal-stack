# Configuration Guide

This guide covers detailed configuration options for the Multimodal LLM Stack.

## Environment Variables

### Database Configuration

```env
# PostgreSQL Settings
POSTGRES_DB=multimodal                    # Database name
POSTGRES_USER=postgres                    # Database user
POSTGRES_PASSWORD=your_secure_password    # Database password (auto-generated)
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

# LiteLLM Configuration  
LITELLM_MASTER_KEY=sk-your_master_key    # Master key for LiteLLM (auto-generated)
LITELLM_SALT_KEY=sk-your_salt_key        # Salt key for encryption (auto-generated)
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

