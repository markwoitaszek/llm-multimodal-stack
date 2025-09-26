# Multimodal LLM Stack

A **production-ready, Dockerized multimodal stack** for RTX 3090 GPU servers that provides unified text, image, and video processing capabilities with OpenAI-compatible APIs.

## 🚀 Features

- **OpenAI-compatible LLM inference** via vLLM + LiteLLM router
- **Multimodal processing**: Image embeddings (CLIP), captioning (BLIP-2), video transcription (Whisper)
- **Unified Retrieval Proxy** for text/image/video search with context bundling
- **Persistent storage**: Qdrant (vectors), PostgreSQL (metadata), MinIO (artifacts)
- **GPU-optimized** for RTX 3090 with seismic-nvme storage integration
- **Production-ready** with SSL, monitoring (Prometheus/Grafana), Redis caching
- **Cursor IDE integration** with intelligent code context and search

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   OpenWebUI     │    │   LiteLLM        │    │  vLLM Server    │
│   (Testing)     │◄──►│   (Router)       │◄──►│  (Inference)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Retrieval Proxy │◄──►│ Multimodal Worker│◄──►│    Storage      │
│ (Context Bundle)│    │ (CLIP/BLIP/Whisper)   │ Qdrant/PG/MinIO │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚦 Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd llm-multimodal-stack

# Automated setup (generates secure passwords, configures GPU, sets up storage)
./scripts/setup.sh

# Start the stack
docker-compose up -d

# Check health and run tests
./scripts/health-check.sh
./scripts/test-multimodal.sh

# Access the web interface
open http://localhost:3000
```

### Production Deployment

```bash
# Deploy with SSL, monitoring, and production optimizations
./scripts/deploy-production.sh

# Access production services
open https://your-domain.com        # Web interface
open https://your-domain.com:3001   # Grafana monitoring
```

## 📋 Services

| Service | Port | Description |
|---------|------|-------------|
| LiteLLM | 4000 | OpenAI-compatible API router |
| vLLM | 8000 | High-performance LLM inference |
| Multimodal Worker | 8001 | Image/video processing |
| Retrieval Proxy | 8002 | Unified search & context |
| OpenWebUI | 3000 | Web interface for testing |
| Qdrant | 6333 | Vector database |
| PostgreSQL | 5432 | Metadata & memory storage |
| MinIO | 9000 | S3-compatible artifact storage |

## 🔧 Configuration

See `docs/configuration.md` for detailed setup instructions.

## 📚 Documentation

- [Configuration Guide](docs/configuration.md)
- [API Reference](docs/api-reference.md)
- [Development Guide](docs/development.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🧪 Testing & Examples

```bash
# Run health checks
./scripts/health-check.sh

# Test multimodal capabilities
./scripts/test-multimodal.sh

# Performance benchmarks
./scripts/benchmark.sh

# API usage examples
python examples/api-examples.py

# Cursor IDE integration
# See examples/cursor-integration.md
```

## 🤝 Integration

This stack is designed to integrate seamlessly with:
- Cursor IDE (via OpenAI-compatible API)
- AI agents and workflows
- Existing ML pipelines
- Custom applications via REST APIs

## 📄 License

MIT License - see LICENSE file for details.

