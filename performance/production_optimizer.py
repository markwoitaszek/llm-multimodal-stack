"""
Production Performance Optimization & Scaling System
Issue #106 Implementation
"""
import asyncio
import json
import logging
import os
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import shutil

logger = logging.getLogger(__name__)

class ProductionOptimizer:
    """Production performance optimization and scaling system"""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path)
        self.config_dir = self.workspace_path / "configs"
        self.performance_dir = self.workspace_path / "performance"
        self.docker_dir = self.workspace_path / "docker"
        
        # Performance optimization configurations
        self.optimization_configs = {
            'database': {
                'postgres': {
                    'max_connections': 200,
                    'shared_buffers': '512MB',
                    'effective_cache_size': '2GB',
                    'maintenance_work_mem': '128MB',
                    'checkpoint_completion_target': 0.9,
                    'wal_buffers': '16MB',
                    'random_page_cost': 1.1,
                    'effective_io_concurrency': 200
                },
                'redis': {
                    'maxmemory': '512mb',
                    'maxmemory_policy': 'allkeys-lru',
                    'tcp_keepalive': 60,
                    'timeout': 300
                }
            },
            'vector_db': {
                'qdrant': {
                    'max_search_threads': 4,
                    'memmap_threshold_kb': 200000,
                    'max_request_size_mb': 32,
                    'hnsw_config': {
                        'm': 16,
                        'ef_construct': 100,
                        'full_scan_threshold': 10000
                    }
                }
            },
            'storage': {
                'minio': {
                    'cache_drives': '/tmp/minio-cache',
                    'cache_max_use': 80,
                    'cache_quota': 80,
                    'cache_after': 3,
                    'cache_watermark_low': 70,
                    'cache_watermark_high': 90
                }
            },
            'inference': {
                'vllm': {
                    'gpu_memory_utilization': 0.85,
                    'max_model_len': 4096,
                    'dtype': 'auto',
                    'max_num_seqs': 8,
                    'tensor_parallel_size': 1,
                    'pipeline_parallel_size': 1
                }
            },
            'caching': {
                'redis': {
                    'ttl_search_results': 3600,
                    'ttl_model_metadata': 86400,
                    'ttl_embeddings': 86400,
                    'ttl_agent_memory': 2592000
                }
            }
        }
    
    async def optimize_docker_configurations(self) -> Dict[str, Any]:
        """Optimize Docker configurations for production"""
        logger.info("Optimizing Docker configurations for production")
        
        # Create optimized production Docker Compose
        optimized_compose = await self._create_optimized_compose()
        
        # Create auto-scaling configuration
        scaling_config = await self._create_scaling_config()
        
        # Create load balancer configuration
        load_balancer_config = await self._create_load_balancer_config()
        
        # Create caching configuration
        caching_config = await self._create_caching_config()
        
        return {
            'optimized_compose': optimized_compose,
            'scaling_config': scaling_config,
            'load_balancer_config': load_balancer_config,
            'caching_config': caching_config
        }
    
    async def _create_optimized_compose(self) -> str:
        """Create optimized Docker Compose configuration"""
        compose_file = self.workspace_path / "docker-compose.optimized.yml"
        
        compose_content = f"""# Optimized Production Docker Compose Configuration
# Generated on: {datetime.utcnow().isoformat()}

version: '3.8'

services:
  # Optimized PostgreSQL
  postgres:
    image: postgres:16-alpine
    container_name: multimodal-postgres-optimized
    environment:
      - POSTGRES_DB=${{POSTGRES_DB}}
      - POSTGRES_USER=${{POSTGRES_USER}}
      - POSTGRES_PASSWORD=${{POSTGRES_PASSWORD}}
    command: >
      postgres
      -c shared_preload_libraries=pg_stat_statements
      -c pg_stat_statements.track=all
      -c max_connections={self.optimization_configs['database']['postgres']['max_connections']}
      -c shared_buffers={self.optimization_configs['database']['postgres']['shared_buffers']}
      -c effective_cache_size={self.optimization_configs['database']['postgres']['effective_cache_size']}
      -c maintenance_work_mem={self.optimization_configs['database']['postgres']['maintenance_work_mem']}
      -c checkpoint_completion_target={self.optimization_configs['database']['postgres']['checkpoint_completion_target']}
      -c wal_buffers={self.optimization_configs['database']['postgres']['wal_buffers']}
      -c random_page_cost={self.optimization_configs['database']['postgres']['random_page_cost']}
      -c effective_io_concurrency={self.optimization_configs['database']['postgres']['effective_io_concurrency']}
      -c log_statement=all
      -c log_min_duration_statement=1000
    volumes:
      - postgres_optimized_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{POSTGRES_USER}}"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - multimodal-net

  # Optimized Redis with clustering
  redis:
    image: redis:7-alpine
    container_name: multimodal-redis-optimized
    command: >
      redis-server
      --maxmemory {self.optimization_configs['database']['redis']['maxmemory']}
      --maxmemory-policy {self.optimization_configs['database']['redis']['maxmemory_policy']}
      --tcp-keepalive {self.optimization_configs['database']['redis']['tcp_keepalive']}
      --timeout {self.optimization_configs['database']['redis']['timeout']}
      --appendonly yes
      --appendfsync everysec
      --save 900 1
      --save 300 10
      --save 60 10000
    volumes:
      - redis_optimized_data:/data
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - multimodal-net

  # Optimized Qdrant
  qdrant:
    image: qdrant/qdrant:v1.12.0
    container_name: multimodal-qdrant-optimized
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__SERVICE__MAX_REQUEST_SIZE_MB={self.optimization_configs['vector_db']['qdrant']['max_request_size_mb']}
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS={self.optimization_configs['vector_db']['qdrant']['max_search_threads']}
      - QDRANT__STORAGE__OPTIMIZERS__MEMMAP_THRESHOLD_KB={self.optimization_configs['vector_db']['qdrant']['memmap_threshold_kb']}
      - QDRANT__STORAGE__OPTIMIZERS__HNSW_CONFIG__M={self.optimization_configs['vector_db']['qdrant']['hnsw_config']['m']}
      - QDRANT__STORAGE__OPTIMIZERS__HNSW_CONFIG__EF_CONSTRUCT={self.optimization_configs['vector_db']['qdrant']['hnsw_config']['ef_construct']}
      - QDRANT__STORAGE__OPTIMIZERS__HNSW_CONFIG__FULL_SCAN_THRESHOLD={self.optimization_configs['vector_db']['qdrant']['hnsw_config']['full_scan_threshold']}
    volumes:
      - qdrant_optimized_data:/qdrant/storage
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
        reservations:
          memory: 4G
          cpus: '2.0'
    healthcheck:
      test: ["CMD-SHELL", "pidof qdrant || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - multimodal-net

  # Optimized vLLM with performance tuning
  vllm:
    image: vllm/vllm-openai:latest
    container_name: multimodal-vllm-optimized
    environment:
      - CUDA_VISIBLE_DEVICES=${{CUDA_VISIBLE_DEVICES:-0}}
      - VLLM_MODEL=${{VLLM_MODEL}}
      - VLLM_HOST=0.0.0.0
      - VLLM_PORT=8000
      - VLLM_API_KEY=${{VLLM_API_KEY}}
    command: >
      --model ${{VLLM_MODEL}}
      --host 0.0.0.0
      --port 8000
      --gpu-memory-utilization {self.optimization_configs['inference']['vllm']['gpu_memory_utilization']}
      --max-model-len {self.optimization_configs['inference']['vllm']['max_model_len']}
      --dtype {self.optimization_configs['inference']['vllm']['dtype']}
      --max-num-seqs {self.optimization_configs['inference']['vllm']['max_num_seqs']}
      --tensor-parallel-size {self.optimization_configs['inference']['vllm']['tensor_parallel_size']}
      --pipeline-parallel-size {self.optimization_configs['inference']['vllm']['pipeline_parallel_size']}
      --api-key ${{VLLM_API_KEY}}
      --served-model-name gpt-3.5-turbo
      --chat-template ./chat_templates/chatml.jinja
    volumes:
      - vllm_optimized_cache:/root/.cache
      - ./models:/models:ro
    deploy:
      resources:
        limits:
          memory: 16G
          cpus: '8.0'
        reservations:
          memory: 8G
          cpus: '4.0'
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD-SHELL", "python3 -c \\"import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/models', timeout=10)\\""]
      interval: 60s
      timeout: 30s
      retries: 5
    restart: unless-stopped
    networks:
      - multimodal-net

  # Optimized LiteLLM with enhanced config
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    container_name: multimodal-litellm-optimized
    environment:
      - LITELLM_MASTER_KEY=${{LITELLM_MASTER_KEY}}
      - LITELLM_SALT_KEY=${{LITELLM_SALT_KEY}}
      - LITELLM_LOG_LEVEL=INFO
      - LITELLM_DROP_PARAMS=true
      - LITELLM_SET_VERBOSE=false
      - LITELLM_MAX_BUDGET=1000
      - LITELLM_CACHE=True
    volumes:
      - ./configs/litellm_optimized.yaml:/app/config.yaml:ro
    command: ["--config", "/app/config.yaml", "--port", "4000", "--num_workers", "8"]
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'
    depends_on:
      vllm:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "python3 -c \\"import urllib.request; urllib.request.urlopen('http://localhost:4000/', timeout=5)\\""]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - multimodal-net

  # Optimized Multimodal Worker with auto-scaling
  multimodal-worker:
    build:
      context: ./services/multimodal-worker
      dockerfile: Dockerfile
    container_name: multimodal-worker-optimized
    environment:
      - CUDA_VISIBLE_DEVICES=${{CUDA_VISIBLE_DEVICES:-0}}
      - LOG_LEVEL=INFO
      - WORKERS=4
      - MAX_CONCURRENT_REQUESTS=20
      - CACHE_TTL_SEARCH_RESULTS={self.optimization_configs['caching']['redis']['ttl_search_results']}
      - CACHE_TTL_MODEL_METADATA={self.optimization_configs['caching']['redis']['ttl_model_metadata']}
      - CACHE_TTL_EMBEDDINGS={self.optimization_configs['caching']['redis']['ttl_embeddings']}
    volumes:
      - multimodal_optimized_cache:/app/cache
      - /tmp:/tmp
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 12G
          cpus: '6.0'
        reservations:
          memory: 6G
          cpus: '3.0'
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    depends_on:
      qdrant:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - multimodal-net

  # Optimized Retrieval Proxy
  retrieval-proxy:
    build:
      context: ./services/retrieval-proxy
      dockerfile: Dockerfile
    container_name: retrieval-proxy-optimized
    environment:
      - LOG_LEVEL=INFO
      - WORKERS=8
      - MAX_CONCURRENT_REQUESTS=40
      - CACHE_TTL_SEARCH_RESULTS={self.optimization_configs['caching']['redis']['ttl_search_results']}
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
    depends_on:
      multimodal-worker:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "python3 -c \\"import urllib.request; urllib.request.urlopen('http://localhost:8002/health', timeout=5)\\""]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - multimodal-net

  # Nginx Load Balancer with caching
  nginx:
    image: nginx:alpine
    container_name: multimodal-nginx-optimized
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./configs/nginx_optimized.conf:/etc/nginx/nginx.conf:ro
      - ./configs/ssl:/etc/nginx/certs:ro
      - nginx_cache:/var/cache/nginx
    depends_on:
      - litellm
      - multimodal-worker
      - retrieval-proxy
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
        reservations:
          memory: 256M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://127.0.0.1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - multimodal-net

volumes:
  postgres_optimized_data:
  redis_optimized_data:
  qdrant_optimized_data:
  vllm_optimized_cache:
  multimodal_optimized_cache:
  nginx_cache:

networks:
  multimodal-net:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.25.0.0/24
          gateway: 172.25.0.1
"""
        
        with open(compose_file, 'w') as f:
            f.write(compose_content)
        
        logger.info(f"Created optimized Docker Compose: {compose_file}")
        return str(compose_file)
    
    async def _create_scaling_config(self) -> str:
        """Create auto-scaling configuration"""
        scaling_file = self.config_dir / "auto_scaling.yaml"
        
        scaling_config = {
            'auto_scaling': {
                'enabled': True,
                'min_replicas': 1,
                'max_replicas': 10,
                'target_cpu_utilization': 70,
                'target_memory_utilization': 80,
                'scale_up_cooldown': '5m',
                'scale_down_cooldown': '10m',
                'services': {
                    'multimodal-worker': {
                        'min_replicas': 2,
                        'max_replicas': 8,
                        'target_cpu': 70,
                        'target_memory': 80,
                        'scale_up_threshold': 80,
                        'scale_down_threshold': 30
                    },
                    'retrieval-proxy': {
                        'min_replicas': 2,
                        'max_replicas': 6,
                        'target_cpu': 70,
                        'target_memory': 80,
                        'scale_up_threshold': 80,
                        'scale_down_threshold': 30
                    },
                    'litellm': {
                        'min_replicas': 1,
                        'max_replicas': 4,
                        'target_cpu': 70,
                        'target_memory': 80,
                        'scale_up_threshold': 80,
                        'scale_down_threshold': 30
                    }
                }
            },
            'resource_limits': {
                'cpu_limit_per_service': '8.0',
                'memory_limit_per_service': '16G',
                'storage_limit_per_service': '100G',
                'network_bandwidth_limit': '1Gbps'
            },
            'monitoring': {
                'metrics_collection_interval': '30s',
                'alert_thresholds': {
                    'cpu_usage': 80,
                    'memory_usage': 85,
                    'disk_usage': 90,
                    'network_usage': 80
                }
            }
        }
        
        with open(scaling_file, 'w') as f:
            yaml.dump(scaling_config, f, default_flow_style=False)
        
        logger.info(f"Created auto-scaling configuration: {scaling_file}")
        return str(scaling_file)
    
    async def _create_load_balancer_config(self) -> str:
        """Create load balancer configuration"""
        nginx_config_file = self.config_dir / "nginx_optimized.conf"
        
        nginx_config = """user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=5r/s;
    
    # Upstream servers
    upstream multimodal_worker {
        least_conn;
        server multimodal-worker-optimized:8001 max_fails=3 fail_timeout=30s;
        server multimodal-worker-optimized_2:8001 max_fails=3 fail_timeout=30s;
        server multimodal-worker-optimized_3:8001 max_fails=3 fail_timeout=30s;
    }
    
    upstream retrieval_proxy {
        least_conn;
        server retrieval-proxy-optimized:8002 max_fails=3 fail_timeout=30s;
        server retrieval-proxy-optimized_2:8002 max_fails=3 fail_timeout=30s;
    }
    
    upstream litellm {
        least_conn;
        server litellm-optimized:4000 max_fails=3 fail_timeout=30s;
    }
    
    upstream vllm {
        least_conn;
        server vllm-optimized:8000 max_fails=3 fail_timeout=30s;
    }
    
    # Cache configuration
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;
    
    server {
        listen 80;
        server_name _;
        
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }
        
        # API endpoints with caching
        location /api/v1/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://multimodal_worker;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Caching
            proxy_cache api_cache;
            proxy_cache_valid 200 302 10m;
            proxy_cache_valid 404 1m;
            proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
            
            # Timeouts
            proxy_connect_timeout 5s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # Retrieval endpoints
        location /api/v1/retrieval/ {
            limit_req zone=api burst=15 nodelay;
            
            proxy_pass http://retrieval_proxy;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Caching
            proxy_cache api_cache;
            proxy_cache_valid 200 302 5m;
            proxy_cache_valid 404 1m;
            
            # Timeouts
            proxy_connect_timeout 5s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
        
        # LiteLLM endpoints
        location /v1/ {
            limit_req zone=api burst=10 nodelay;
            
            proxy_pass http://litellm;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 5s;
            proxy_send_timeout 120s;
            proxy_read_timeout 120s;
        }
        
        # File upload endpoints
        location /api/v1/upload/ {
            limit_req zone=upload burst=5 nodelay;
            
            proxy_pass http://multimodal_worker;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts for large uploads
            proxy_connect_timeout 10s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
        }
        
        # Static content
        location /static/ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            try_files $uri =404;
        }
    }
}
"""
        
        with open(nginx_config_file, 'w') as f:
            f.write(nginx_config)
        
        logger.info(f"Created optimized Nginx configuration: {nginx_config_file}")
        return str(nginx_config_file)
    
    async def _create_caching_config(self) -> str:
        """Create caching configuration"""
        cache_config_file = self.config_dir / "caching_config.yaml"
        
        cache_config = {
            'redis_caching': {
                'enabled': True,
                'host': 'redis',
                'port': 6379,
                'db': 0,
                'password': '${REDIS_PASSWORD}',
                'max_connections': 20,
                'socket_timeout': 5,
                'socket_connect_timeout': 5,
                'retry_on_timeout': True,
                'health_check_interval': 30
            },
            'cache_policies': {
                'search_results': {
                    'ttl': self.optimization_configs['caching']['redis']['ttl_search_results'],
                    'max_size': '100MB',
                    'eviction_policy': 'lru'
                },
                'model_metadata': {
                    'ttl': self.optimization_configs['caching']['redis']['ttl_model_metadata'],
                    'max_size': '50MB',
                    'eviction_policy': 'lru'
                },
                'embeddings': {
                    'ttl': self.optimization_configs['caching']['redis']['ttl_embeddings'],
                    'max_size': '500MB',
                    'eviction_policy': 'lru'
                },
                'agent_memory': {
                    'ttl': self.optimization_configs['caching']['redis']['ttl_agent_memory'],
                    'max_size': '200MB',
                    'eviction_policy': 'lru'
                }
            },
            'http_caching': {
                'enabled': True,
                'cache_control': {
                    'api_responses': 'max-age=300',
                    'static_content': 'max-age=31536000',
                    'search_results': 'max-age=600',
                    'model_responses': 'max-age=60'
                }
            },
            'application_caching': {
                'enabled': True,
                'cache_layers': {
                    'l1': {
                        'type': 'memory',
                        'max_size': '100MB',
                        'ttl': 300
                    },
                    'l2': {
                        'type': 'redis',
                        'max_size': '1GB',
                        'ttl': 3600
                    }
                }
            }
        }
        
        with open(cache_config_file, 'w') as f:
            yaml.dump(cache_config, f, default_flow_style=False)
        
        logger.info(f"Created caching configuration: {cache_config_file}")
        return str(cache_config_file)
    
    async def create_performance_monitoring(self) -> Dict[str, Any]:
        """Create performance monitoring configuration"""
        logger.info("Creating performance monitoring configuration")
        
        # Create Prometheus configuration
        prometheus_config = await self._create_prometheus_config()
        
        # Create Grafana dashboards
        grafana_dashboards = await self._create_grafana_dashboards()
        
        # Create alerting rules
        alerting_rules = await self._create_alerting_rules()
        
        return {
            'prometheus_config': prometheus_config,
            'grafana_dashboards': grafana_dashboards,
            'alerting_rules': alerting_rules
        }
    
    async def _create_prometheus_config(self) -> str:
        """Create Prometheus configuration for performance monitoring"""
        prometheus_file = self.config_dir / "prometheus_optimized.yml"
        
        prometheus_config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    metrics_path: /nginx_status
    scrape_interval: 30s

  - job_name: 'multimodal-worker'
    static_configs:
      - targets: ['multimodal-worker:8001']
    metrics_path: /metrics
    scrape_interval: 15s

  - job_name: 'retrieval-proxy'
    static_configs:
      - targets: ['retrieval-proxy:8002']
    metrics_path: /metrics
    scrape_interval: 15s

  - job_name: 'litellm'
    static_configs:
      - targets: ['litellm:4000']
    metrics_path: /metrics
    scrape_interval: 15s

  - job_name: 'vllm'
    static_configs:
      - targets: ['vllm:8000']
    metrics_path: /metrics
    scrape_interval: 15s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 15s
"""
        
        with open(prometheus_file, 'w') as f:
            f.write(prometheus_config)
        
        logger.info(f"Created Prometheus configuration: {prometheus_file}")
        return str(prometheus_file)
    
    async def _create_grafana_dashboards(self) -> List[str]:
        """Create Grafana dashboards for performance monitoring"""
        dashboards_dir = self.config_dir / "grafana" / "dashboards"
        dashboards_dir.mkdir(parents=True, exist_ok=True)
        
        created_dashboards = []
        
        # System Performance Dashboard
        system_dashboard = {
            "dashboard": {
                "id": None,
                "title": "System Performance",
                "tags": ["performance", "system"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "CPU Usage",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
                                "legendFormat": "CPU Usage %"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "Memory Usage",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
                                "legendFormat": "Memory Usage %"
                            }
                        ]
                    },
                    {
                        "id": 3,
                        "title": "Disk I/O",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(node_disk_io_time_seconds_total[5m])",
                                "legendFormat": "Disk I/O"
                            }
                        ]
                    },
                    {
                        "id": 4,
                        "title": "Network I/O",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(node_network_receive_bytes_total[5m])",
                                "legendFormat": "Network Receive"
                            },
                            {
                                "expr": "rate(node_network_transmit_bytes_total[5m])",
                                "legendFormat": "Network Transmit"
                            }
                        ]
                    }
                ]
            }
        }
        
        system_dashboard_file = dashboards_dir / "system_performance.json"
        with open(system_dashboard_file, 'w') as f:
            json.dump(system_dashboard, f, indent=2)
        created_dashboards.append(str(system_dashboard_file))
        
        # Application Performance Dashboard
        app_dashboard = {
            "dashboard": {
                "id": None,
                "title": "Application Performance",
                "tags": ["performance", "application"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "API Response Time",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                                "legendFormat": "95th percentile"
                            },
                            {
                                "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
                                "legendFormat": "50th percentile"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "Request Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(http_requests_total[5m])",
                                "legendFormat": "Requests/sec"
                            }
                        ]
                    },
                    {
                        "id": 3,
                        "title": "Error Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
                                "legendFormat": "5xx Errors/sec"
                            }
                        ]
                    },
                    {
                        "id": 4,
                        "title": "Active Connections",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "nginx_connections_active",
                                "legendFormat": "Active Connections"
                            }
                        ]
                    }
                ]
            }
        }
        
        app_dashboard_file = dashboards_dir / "application_performance.json"
        with open(app_dashboard_file, 'w') as f:
            json.dump(app_dashboard, f, indent=2)
        created_dashboards.append(str(app_dashboard_file))
        
        logger.info(f"Created {len(created_dashboards)} Grafana dashboards")
        return created_dashboards
    
    async def _create_alerting_rules(self) -> str:
        """Create alerting rules for performance monitoring"""
        alerting_file = self.config_dir / "alert_rules.yml"
        
        alerting_rules = """groups:
- name: performance_alerts
  rules:
  - alert: HighCPUUsage
    expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage detected"
      description: "CPU usage is above 80% for more than 5 minutes"

  - alert: HighMemoryUsage
    expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
      description: "Memory usage is above 85% for more than 5 minutes"

  - alert: HighDiskUsage
    expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 90
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High disk usage detected"
      description: "Disk usage is above 90% for more than 5 minutes"

  - alert: HighAPIResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High API response time"
      description: "95th percentile API response time is above 2 seconds"

  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is above 10% for more than 5 minutes"

  - alert: ServiceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Service is down"
      description: "Service {{ $labels.instance }} is down"

- name: scaling_alerts
  rules:
  - alert: AutoScalingTriggered
    expr: avg_over_time(container_cpu_usage_seconds_total[5m]) > 0.7
    for: 2m
    labels:
      severity: info
    annotations:
      summary: "Auto-scaling triggered"
      description: "CPU usage above 70% for 2 minutes, triggering auto-scaling"
"""
        
        with open(alerting_file, 'w') as f:
            f.write(alerting_rules)
        
        logger.info(f"Created alerting rules: {alerting_file}")
        return str(alerting_file)
    
    async def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate performance optimization report"""
        logger.info("Generating performance optimization report")
        
        report = {
            'optimization_timestamp': datetime.utcnow().isoformat(),
            'optimization_summary': {
                'docker_optimizations': 'completed',
                'auto_scaling': 'configured',
                'load_balancing': 'configured',
                'caching': 'configured',
                'monitoring': 'configured'
            },
            'performance_improvements': {
                'database_optimization': {
                    'postgres_max_connections': self.optimization_configs['database']['postgres']['max_connections'],
                    'postgres_shared_buffers': self.optimization_configs['database']['postgres']['shared_buffers'],
                    'redis_memory_policy': self.optimization_configs['database']['redis']['maxmemory_policy']
                },
                'vector_db_optimization': {
                    'qdrant_search_threads': self.optimization_configs['vector_db']['qdrant']['max_search_threads'],
                    'qdrant_memmap_threshold': self.optimization_configs['vector_db']['qdrant']['memmap_threshold_kb']
                },
                'inference_optimization': {
                    'vllm_gpu_utilization': self.optimization_configs['inference']['vllm']['gpu_memory_utilization'],
                    'vllm_max_model_len': self.optimization_configs['inference']['vllm']['max_model_len']
                },
                'caching_optimization': {
                    'search_results_ttl': self.optimization_configs['caching']['redis']['ttl_search_results'],
                    'embeddings_ttl': self.optimization_configs['caching']['redis']['ttl_embeddings']
                }
            },
            'scaling_configuration': {
                'auto_scaling_enabled': True,
                'max_replicas': 10,
                'target_cpu_utilization': 70,
                'target_memory_utilization': 80
            },
            'monitoring_setup': {
                'prometheus_configured': True,
                'grafana_dashboards': 2,
                'alerting_rules': 6
            },
            'recommendations': [
                'Deploy optimized configuration to production environment',
                'Monitor performance metrics for 24-48 hours',
                'Adjust auto-scaling thresholds based on actual usage patterns',
                'Implement additional caching layers as needed',
                'Consider implementing CDN for static content',
                'Regular performance testing and optimization reviews'
            ],
            'next_steps': [
                'Deploy optimized Docker Compose configuration',
                'Set up monitoring and alerting',
                'Configure auto-scaling policies',
                'Run performance tests to validate improvements',
                'Document performance baselines and targets'
            ]
        }
        
        # Save report
        report_file = self.workspace_path / "reports" / "performance_optimization_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Performance optimization report generated: {report_file}")
        return report

# Global production optimizer instance
production_optimizer = ProductionOptimizer()