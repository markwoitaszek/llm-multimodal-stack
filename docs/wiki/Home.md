# Welcome to the Multimodal LLM Stack Wiki

Welcome to the comprehensive documentation for the **Multimodal LLM Stack** - a production-ready, Dockerized multimodal stack for RTX 3090 GPU servers that provides unified text, image, and video processing capabilities with OpenAI-compatible APIs.

## 🚀 Quick Navigation

### For Beginners
- [[Getting Started Guide]] - Your first steps with the stack
- [[Setup Wizard Tutorial]] - Interactive setup assistance
- [[First AI Conversation]] - Learn to chat with your AI
- [[Basic Troubleshooting]] - Common issues and solutions

### For Developers
- [[API Reference]] - Complete API documentation
- [[Configuration Guide]] - Detailed configuration options
- [[Development Setup]] - Setting up for development
- [[Deployment Guide]] - Production deployment instructions

### For Advanced Users
- [[Multimodal Features]] - Image and video processing
- [[Custom Model Integration]] - Adding your own models
- [[Performance Optimization]] - Tuning for your hardware
- [[Monitoring and Logging]] - System observability

## 🏗️ Architecture Overview

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

## 🎯 What You Can Do

### 🤖 AI Chat Interface
- **OpenWebUI** at `http://localhost:3030` - ChatGPT-like interface
- **OpenAI-compatible API** at `http://localhost:4000/v1`
- **Multiple AI models** from small to enterprise-grade

### 🎨 Multimodal Processing
- **Image Analysis** - CLIP embeddings, BLIP-2 captioning
- **Video Processing** - Whisper transcription, frame analysis
- **Unified Search** - Search across text, images, and videos

### 🔧 Development Tools
- **n8n Workflows** - Visual workflow automation
- **AI Agents** - LangChain autonomous agents
- **Monitoring** - Prometheus/Grafana dashboards

## 📋 Service Overview

| Service | Port | Description |
|---------|------|-------------|
| **Setup Wizard** | 8004 | Interactive setup and tutorials |
| **OpenWebUI** | 3030 | Web interface for testing |
| **LiteLLM** | 4000 | OpenAI-compatible API router |
| **vLLM** | 8000 | High-performance LLM inference |
| **Multimodal Worker** | 8001 | Image/video processing |
| **Retrieval Proxy** | 8002 | Unified search & context |
| **AI Agents** | 8003 | LangChain autonomous agents |
| **n8n** | 5678 | Visual workflow automation |
| **Qdrant** | 6333 | Vector database |
| **PostgreSQL** | 5432 | Metadata & memory storage |
| **MinIO** | 9000 | S3-compatible artifact storage |

## 🚦 Getting Started

### Option 1: Interactive Setup (Recommended for Beginners)
1. Start the stack: `docker-compose up -d`
2. Open the Setup Wizard: `http://localhost:8004`
3. Follow the guided setup process
4. Complete the tutorials

### Option 2: Quick Start
```bash
# Clone and setup
git clone <repo-url>
cd llm-multimodal-stack

# Automated setup
./scripts/setup.sh

# Start the stack
docker-compose up -d

# Access the web interface
open http://localhost:3030
```

## 🆘 Need Help?

- **Setup Issues**: Check [[Basic Troubleshooting]]
- **API Questions**: See [[API Reference]]
- **Performance**: Read [[Performance Optimization]]
- **Advanced Features**: Explore [[Multimodal Features]]

## 📚 Additional Resources

- **GitHub Repository**: [View Source Code](https://github.com/your-repo/llm-multimodal-stack)
- **Issues & Discussions**: [GitHub Issues](https://github.com/your-repo/llm-multimodal-stack/issues)
- **Community**: [GitHub Discussions](https://github.com/your-repo/llm-multimodal-stack/discussions)

---

**🎉 Welcome to your personal AI stack!** You now have enterprise-grade AI capabilities running on your own hardware.
