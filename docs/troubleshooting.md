# Troubleshooting Guide

Common issues and solutions for the Multimodal LLM Stack.

## Quick Diagnostics

### Health Check Script
```bash
./scripts/health-check.sh
```

### Service Status
```bash
docker-compose ps
docker-compose logs --tail=50 [service_name]
```

## Common Issues

### 1. GPU Not Detected

**Symptoms:**
- Services start but models fail to load
- CUDA errors in logs
- Slow performance

**Solutions:**

```bash
# Check NVIDIA Docker runtime
docker info | grep nvidia

# If not found, install nvidia-container-toolkit
sudo apt-get update
sudo apt-get install nvidia-container-toolkit
sudo systemctl restart docker

# Verify GPU access in container
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi
```

**Alternative Solutions:**
```bash
# Force CPU mode if GPU unavailable
echo "CUDA_VISIBLE_DEVICES=" >> .env
docker-compose up -d
```

### 2. Out of Memory Errors

**Symptoms:**
- Services crash with OOM errors
- `torch.cuda.OutOfMemoryError`
- System becomes unresponsive

**GPU Memory Solutions:**
```bash
# Reduce GPU memory utilization
sed -i 's/gpu-memory-utilization 0.8/gpu-memory-utilization 0.6/' docker-compose.yml

# Use smaller models
sed -i 's/VLLM_MODEL=.*/VLLM_MODEL=microsoft\/DialoGPT-medium/' .env
```

**System Memory Solutions:**
```bash
# Check memory usage
free -h
docker stats

# Increase swap if needed
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 3. Database Connection Issues

**Symptoms:**
- `asyncpg.exceptions.ConnectionDoesNotExistError`
- Services can't connect to PostgreSQL
- Database health check fails

**Solutions:**

```bash
# Check PostgreSQL status
docker-compose logs postgres

# Reset database
docker-compose down
docker volume rm llm-multimodal-stack_postgres_data
docker-compose up -d postgres

# Check connection manually
docker-compose exec postgres psql -U postgres -d multimodal -c "SELECT 1;"
```

**Connection String Issues:**
```bash
# Verify environment variables
docker-compose exec multimodal-worker env | grep POSTGRES

# Test connection from service
docker-compose exec multimodal-worker python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://postgres:postgres@postgres:5432/multimodal')
    print(await conn.fetchval('SELECT 1'))
    await conn.close()
asyncio.run(test())
"
```

### 4. Vector Store Issues

**Symptoms:**
- Qdrant connection failures
- Vector search returns no results
- Collection not found errors

**Solutions:**

```bash
# Check Qdrant status
curl http://localhost:6333/health
curl http://localhost:6333/collections

# Reset Qdrant data
docker-compose down
docker volume rm llm-multimodal-stack_qdrant_data
docker-compose up -d qdrant

# Recreate collections
curl -X PUT http://localhost:6333/collections/text_embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }'
```

### 5. Storage Issues (MinIO)

**Symptoms:**
- File upload failures
- S3 connection errors
- Artifact retrieval fails

**Solutions:**

```bash
# Check MinIO status
curl http://localhost:9000/minio/health/live

# Access MinIO console
open http://localhost:9001
# Login: minioadmin / minioadmin (or your configured credentials)

# Create buckets manually
docker-compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker-compose exec minio mc mb local/images
docker-compose exec minio mc mb local/videos
docker-compose exec minio mc mb local/documents
```

### 6. Model Loading Issues

**Symptoms:**
- `OSError: Unable to load model`
- `HuggingFace Hub connection errors`
- Models download but fail to load

**Solutions:**

```bash
# Clear model cache
docker-compose down
docker volume rm llm-multimodal-stack_vllm_cache
docker volume rm llm-multimodal-stack_multimodal_cache

# Check disk space
df -h

# Download models manually
docker-compose exec multimodal-worker python -c "
from transformers import CLIPModel, CLIPProcessor
model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
print('CLIP model loaded successfully')
"
```

**Offline Mode:**
```bash
# Set offline mode if no internet
echo "TRANSFORMERS_OFFLINE=1" >> .env
echo "HF_HUB_OFFLINE=1" >> .env
```

### 7. Performance Issues

**Symptoms:**
- Slow response times
- High CPU/GPU usage
- Memory leaks

**Diagnostic Commands:**
```bash
# Monitor resource usage
htop
nvidia-smi -l 1
docker stats

# Check service metrics
curl http://localhost:8001/api/v1/models/status
curl http://localhost:8002/api/v1/stats

# Run performance tests
./scripts/benchmark.sh
```

**Performance Tuning:**
```bash
# Optimize database
docker-compose exec postgres psql -U postgres -d multimodal -c "
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();
"

# Scale services
docker-compose up -d --scale multimodal-worker=2

# Use faster storage
# Move to NVMe if available
sudo mkdir -p /mnt/nvme/{qdrant,postgres,minio,cache}
sudo chown -R $USER:$USER /mnt/nvme/
# Update .env with NVMe paths
```

### 8. Network Issues

**Symptoms:**
- Services can't communicate
- Port conflicts
- External API calls fail

**Solutions:**

```bash
# Check port conflicts
netstat -tulpn | grep -E ':(3000|4000|5432|6333|8001|8002|9000)'

# Check Docker network
docker network ls
docker network inspect llm-multimodal-stack_multimodal-net

# Reset network
docker-compose down
docker network prune -f
docker-compose up -d
```

### 9. SSL/TLS Issues

**Symptoms:**
- HTTPS certificate errors
- SSL handshake failures
- Mixed content warnings

**Solutions:**

```bash
# Generate self-signed certificates for development
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost"

# Add to docker-compose.yml
volumes:
  - ./certs:/app/certs
environment:
  - SSL_CERT_PATH=/app/certs/cert.pem
  - SSL_KEY_PATH=/app/certs/key.pem
```

### 10. File Upload Issues

**Symptoms:**
- Large file uploads fail
- Timeout errors
- File corruption

**Solutions:**

```bash
# Increase upload limits
# Add to docker-compose.yml for services
environment:
  - MAX_FILE_SIZE=100MB
  - UPLOAD_TIMEOUT=300

# For nginx proxy (if used)
client_max_body_size 100M;
proxy_read_timeout 300s;
proxy_send_timeout 300s;
```

## Service-Specific Issues

### vLLM Issues

```bash
# Check vLLM logs
docker-compose logs vllm

# Test vLLM directly
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'

# Restart with different model
docker-compose down vllm
sed -i 's/VLLM_MODEL=.*/VLLM_MODEL=microsoft\/DialoGPT-small/' .env
docker-compose up -d vllm
```

### LiteLLM Issues

```bash
# Check LiteLLM configuration
cat configs/litellm_config.yaml

# Test configuration
docker-compose exec litellm litellm --test --config /app/config.yaml

# Check API key
curl -X GET http://localhost:4000/health \
  -H "Authorization: Bearer your-litellm-key"
```

### OpenWebUI Issues

```bash
# Reset OpenWebUI data
docker-compose down openwebui
docker volume rm llm-multimodal-stack_openwebui_data
docker-compose up -d openwebui

# Check configuration
docker-compose logs openwebui

# Access directly
open http://localhost:3000
```

## Monitoring and Logging

### Centralized Logging

```yaml
# Add to docker-compose.yml
x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"

services:
  multimodal-worker:
    logging: *default-logging
```

### Health Monitoring

```bash
# Continuous health monitoring
watch -n 30 './scripts/health-check.sh'

# Set up alerts (example with webhook)
#!/bin/bash
if ! ./scripts/health-check.sh; then
  curl -X POST https://hooks.slack.com/your-webhook \
    -d '{"text": "Multimodal stack health check failed!"}'
fi
```

### Log Analysis

```bash
# Search for errors across all services
docker-compose logs | grep -i error

# Monitor specific service
docker-compose logs -f multimodal-worker | grep -E "(ERROR|WARN)"

# Export logs for analysis
docker-compose logs > system_logs_$(date +%Y%m%d).log
```

## Recovery Procedures

### Complete System Reset

```bash
#!/bin/bash
# Stop all services
docker-compose down

# Remove all volumes (WARNING: This deletes all data!)
docker volume prune -f

# Remove all containers and images
docker system prune -af

# Restart fresh
./scripts/setup.sh
docker-compose up -d
```

### Partial Reset (Keep Data)

```bash
# Reset only application containers
docker-compose restart multimodal-worker retrieval-proxy litellm openwebui

# Reset only infrastructure
docker-compose restart qdrant postgres minio
```

### Backup and Restore

```bash
# Backup data volumes
docker run --rm -v llm-multimodal-stack_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
docker run --rm -v llm-multimodal-stack_qdrant_data:/data -v $(pwd):/backup alpine tar czf /backup/qdrant_backup.tar.gz -C /data .
docker run --rm -v llm-multimodal-stack_minio_data:/data -v $(pwd):/backup alpine tar czf /backup/minio_backup.tar.gz -C /data .

# Restore data volumes
docker volume create llm-multimodal-stack_postgres_data
docker run --rm -v llm-multimodal-stack_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## Getting Help

### Debug Information Collection

```bash
#!/bin/bash
# Collect debug information
echo "=== System Information ===" > debug_info.txt
uname -a >> debug_info.txt
docker --version >> debug_info.txt
docker-compose --version >> debug_info.txt

echo "=== Service Status ===" >> debug_info.txt
docker-compose ps >> debug_info.txt

echo "=== Service Logs ===" >> debug_info.txt
docker-compose logs --tail=100 >> debug_info.txt

echo "=== Resource Usage ===" >> debug_info.txt
docker stats --no-stream >> debug_info.txt
free -h >> debug_info.txt
df -h >> debug_info.txt

echo "=== GPU Status ===" >> debug_info.txt
nvidia-smi >> debug_info.txt 2>/dev/null || echo "No GPU detected" >> debug_info.txt
```

### Support Channels

- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Check docs/ directory for detailed guides
- **Community**: Join discussions and get help from other users

### Before Reporting Issues

1. Run health check: `./scripts/health-check.sh`
2. Check logs: `docker-compose logs [service]`
3. Collect debug info with the script above
4. Try common solutions from this guide
5. Search existing GitHub issues