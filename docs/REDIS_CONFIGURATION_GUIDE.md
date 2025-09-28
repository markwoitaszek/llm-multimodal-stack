# Redis Integration Configuration Guide

## Overview

This guide covers all configuration requirements for the Redis integration implemented in Issue #42. Redis is now a critical component of the multimodal LLM stack, providing caching and agent memory capabilities.

## 🔧 Required Configuration

### **1. Environment Variables**

#### **Core Redis Settings**
```bash
# Redis Connection
REDIS_HOST=redis                    # Redis container hostname
REDIS_PORT=6379                     # Redis port (default)
```

#### **Service-Specific Database Configuration**
```bash
# Database isolation for different services
REDIS_DB_MULTIMODAL_WORKER=0        # Model caching, embeddings
REDIS_DB_RETRIEVAL_PROXY=1          # Search results, context bundles
REDIS_DB_AI_AGENTS=2                # Agent memory, conversations
```

#### **Cache TTL Configuration**
```bash
# Cache expiration times (in seconds)
CACHE_TTL_SEARCH_RESULTS=3600       # 1 hour
CACHE_TTL_MODEL_METADATA=86400      # 24 hours
CACHE_TTL_EMBEDDINGS=86400          # 24 hours
CACHE_TTL_AGENT_MEMORY=2592000      # 30 days
```

### **2. Docker Compose Configuration**

The Redis service is automatically configured in `docker-compose.yml` with:

```yaml
redis:
  image: redis:7-alpine
  container_name: multimodal-redis
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 30s
    timeout: 10s
    retries: 3
  restart: unless-stopped
  networks:
    - multimodal-net
```

### **3. Service Dependencies**

All services that use Redis have been updated with:
- Redis environment variables
- Redis dependency in `depends_on`
- Cache manager initialization

## 🚀 Setup Instructions

### **Step 1: Environment Setup**

1. **Copy environment template**:
   ```bash
   cp env.example .env
   ```

2. **Update Redis configuration** (if needed):
   ```bash
   # Edit .env file
   nano .env
   
   # Redis settings are already configured with defaults
   REDIS_HOST=redis
   REDIS_PORT=6379
   REDIS_DB_MULTIMODAL_WORKER=0
   REDIS_DB_RETRIEVAL_PROXY=1
   REDIS_DB_AI_AGENTS=2
   ```

### **Step 2: Start Services**

1. **Start infrastructure services**:
   ```bash
   docker-compose up -d redis postgres qdrant minio
   ```

2. **Verify Redis is running**:
   ```bash
   docker-compose ps redis
   docker exec multimodal-redis redis-cli ping
   ```

3. **Start application services**:
   ```bash
   docker-compose up -d multimodal-worker retrieval-proxy ai-agents
   ```

### **Step 3: Verify Configuration**

1. **Run health checks**:
   ```bash
   ./scripts/health-check.sh
   ```

2. **Test Redis integration**:
   ```bash
   ./scripts/test-redis-integration.sh
   ```

3. **Check cache endpoints**:
   ```bash
   # Retrieval proxy cache stats
   curl http://localhost:8002/api/v1/cache/stats
   
   # Multimodal worker cache stats
   curl http://localhost:8001/api/v1/cache/stats
   ```

## 📊 Monitoring & Management

### **Cache Statistics**

Each service provides detailed cache statistics:

```bash
# Get cache statistics
curl http://localhost:8002/api/v1/cache/stats
curl http://localhost:8001/api/v1/cache/stats

# Example response:
{
  "connected": true,
  "memory_used": "2.5M",
  "keyspace_hits": 1250,
  "keyspace_misses": 150,
  "hit_rate": 89.3,
  "total_commands_processed": 2840,
  "connected_clients": 3
}
```

### **Cache Management**

```bash
# Clear all cache entries
curl -X DELETE http://localhost:8002/api/v1/cache/clear
curl -X DELETE http://localhost:8001/api/v1/cache/clear

# Invalidate specific cache patterns
curl -X DELETE http://localhost:8002/api/v1/cache/search/pattern
curl -X DELETE http://localhost:8001/api/v1/cache/file/file_hash
```

### **Redis Monitoring**

```bash
# Redis info
docker exec multimodal-redis redis-cli info

# Memory usage
docker exec multimodal-redis redis-cli info memory

# Statistics
docker exec multimodal-redis redis-cli info stats

# List all keys
docker exec multimodal-redis redis-cli keys "*"
```

## 🔒 Security Configuration

### **Network Security**
- Redis is only accessible within the Docker network
- No external port exposure required for internal services
- Port 6379 is exposed for development/testing only

### **Data Isolation**
- Each service uses a separate Redis database
- No cross-service data access possible
- Memory limits prevent resource exhaustion

### **Authentication**
- No authentication required for internal services
- Redis runs in trusted Docker network environment

## ⚙️ Advanced Configuration

### **Memory Optimization**

```bash
# Adjust memory limits in docker-compose.yml
command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru

# Monitor memory usage
docker exec multimodal-redis redis-cli info memory | grep used_memory_human
```

### **Persistence Configuration**

```bash
# AOF (Append Only File) persistence is enabled by default
# Adjust sync frequency if needed:
command: redis-server --appendonly yes --appendfsync everysec --maxmemory 256mb
```

### **Performance Tuning**

```bash
# Adjust cache TTL values in .env
CACHE_TTL_SEARCH_RESULTS=7200      # 2 hours
CACHE_TTL_MODEL_METADATA=172800    # 48 hours
CACHE_TTL_EMBEDDINGS=172800        # 48 hours
```

## 🐛 Troubleshooting

### **Common Issues**

1. **Redis connection failed**
   ```bash
   # Check if Redis container is running
   docker-compose ps redis
   
   # Check Redis logs
   docker logs multimodal-redis
   
   # Test connection manually
   docker exec multimodal-redis redis-cli ping
   ```

2. **Cache not working**
   ```bash
   # Check service logs for Redis errors
   docker logs multimodal-worker
   docker logs retrieval-proxy
   
   # Verify Redis connectivity from services
   docker exec multimodal-worker redis-cli -h redis ping
   docker exec retrieval-proxy redis-cli -h redis ping
   ```

3. **Memory issues**
   ```bash
   # Check Redis memory usage
   docker exec multimodal-redis redis-cli info memory
   
   # Clear cache if needed
   curl -X DELETE http://localhost:8002/api/v1/cache/clear
   curl -X DELETE http://localhost:8001/api/v1/cache/clear
   ```

4. **Database isolation issues**
   ```bash
   # Test database isolation
   docker exec multimodal-redis redis-cli -n 0 set test0 "value0"
   docker exec multimodal-redis redis-cli -n 1 set test1 "value1"
   docker exec multimodal-redis redis-cli -n 2 set test2 "value2"
   
   # Verify isolation
   docker exec multimodal-redis redis-cli -n 0 get test0
   docker exec multimodal-redis redis-cli -n 1 get test1
   docker exec multimodal-redis redis-cli -n 2 get test2
   ```

### **Debug Commands**

```bash
# Redis connection test
docker exec multimodal-redis redis-cli ping

# Check Redis configuration
docker exec multimodal-redis redis-cli config get "*"

# Monitor Redis commands in real-time
docker exec multimodal-redis redis-cli monitor

# Check cache statistics
curl http://localhost:8002/api/v1/cache/stats | jq
curl http://localhost:8001/api/v1/cache/stats | jq
```

## 📈 Performance Monitoring

### **Key Metrics to Monitor**

1. **Cache Hit Rate**: Should be >80% for optimal performance
2. **Memory Usage**: Should stay under 256MB limit
3. **Connection Count**: Should match number of services
4. **Command Processing**: Monitor for high latency

### **Performance Benchmarks**

Expected performance improvements:
- **30-50% faster response times** for cached queries
- **90%+ cache hit rate** for model loading
- **<100ms response time** for cached searches
- **Agent memory persistence** across restarts

## 🔄 Backup & Recovery

### **Redis Data Backup**

```bash
# Create Redis backup
docker exec multimodal-redis redis-cli BGSAVE

# Copy backup file
docker cp multimodal-redis:/data/dump.rdb ./redis-backup-$(date +%Y%m%d).rdb
```

### **Restore from Backup**

```bash
# Stop Redis
docker-compose stop redis

# Replace dump file
docker cp ./redis-backup-20240101.rdb multimodal-redis:/data/dump.rdb

# Start Redis
docker-compose start redis
```

## 🎯 Production Considerations

### **Scaling**

For production environments:
- Consider Redis clustering for high availability
- Implement Redis Sentinel for automatic failover
- Use Redis persistence with appropriate sync settings
- Monitor memory usage and implement eviction policies

### **Security**

For production:
- Enable Redis AUTH with strong passwords
- Use TLS encryption for Redis connections
- Implement network segmentation
- Regular security updates and monitoring

## 📚 Additional Resources

- [Redis Documentation](https://redis.io/documentation)
- [Redis Configuration Reference](https://redis.io/docs/management/config/)
- [Redis Monitoring Guide](https://redis.io/docs/management/monitoring/)
- [Redis Persistence Guide](https://redis.io/docs/management/persistence/)

---

**Note**: This configuration is optimized for development and small team usage. For production deployments, additional security, monitoring, and scaling considerations should be implemented.
