# Getting Started Guide

Welcome to the Multimodal LLM Stack! This guide will walk you through setting up and using your AI stack for the first time.

## 🎯 What You'll Learn

By the end of this guide, you'll be able to:
- Set up your AI stack using the interactive wizard
- Have your first AI conversation
- Understand the basic architecture
- Know where to find help and resources

## 📋 Prerequisites

Before you begin, make sure you have:

### Required
- **Docker** and **Docker Compose** installed
- **8GB+ free disk space**
- **Internet connection** for downloading models
- **Basic command line knowledge**

### Optional (Recommended)
- **NVIDIA GPU** with 8GB+ VRAM for better performance
- **NVIDIA Docker runtime** for GPU acceleration
- **NVMe storage** for faster model loading

### Quick Prerequisites Check
```bash
# Check Docker installation
docker --version
docker-compose --version

# Check GPU (optional)
nvidia-smi

# Check disk space
df -h
```

## 🚀 Setup Options

### Option 1: Interactive Setup Wizard (Recommended)

The Setup Wizard provides a guided, beginner-friendly experience:

1. **Start the Stack**
   ```bash
   git clone <repo-url>
   cd llm-multimodal-stack
   docker-compose up -d
   ```

2. **Open Setup Wizard**
   - Navigate to: `http://localhost:8004`
   - Follow the step-by-step guided setup
   - Complete the interactive tutorials

3. **Benefits of the Wizard**
   - ✅ Automatic system checks
   - ✅ Model recommendations based on your hardware
   - ✅ Guided configuration
   - ✅ Progress tracking
   - ✅ Built-in tutorials

### Option 2: Quick Automated Setup

For users comfortable with command line:

```bash
# Clone the repository
git clone <repo-url>
cd llm-multimodal-stack

# Run automated setup
./scripts/setup.sh

# Start all services
docker-compose up -d

# Check system health
./scripts/health-check.sh
```

## 🎮 Your First AI Conversation

Once your stack is running, you can start chatting with your AI:

### Using the Web Interface
1. **Open the Web UI**: `http://localhost:3030`
2. **Start a conversation**: Click "New Chat"
3. **Try these example prompts**:
   - "Hello! Can you introduce yourself?"
   - "Explain what machine learning is in simple terms"
   - "Help me write a Python function to sort a list"

### Using the API
```python
import openai

# Configure for your local stack
openai.api_base = "http://localhost:4000/v1"
openai.api_key = "dummy-key"  # Not required for local use

# Chat with your AI
response = openai.ChatCompletion.create(
    model="microsoft/DialoGPT-medium",
    messages=[{"role": "user", "content": "Hello, how are you?"}]
)

print(response.choices[0].message.content)
```

## 🏗️ Understanding Your Stack

Your AI stack consists of several interconnected services:

### Core Services
- **vLLM Server** - Runs the AI models
- **LiteLLM Router** - Provides OpenAI-compatible API
- **OpenWebUI** - Web interface for chatting
- **Setup Wizard** - Interactive setup and tutorials

### Storage Services
- **Qdrant** - Vector database for embeddings
- **PostgreSQL** - Metadata and conversation storage
- **MinIO** - File storage for images/videos

### Processing Services
- **Multimodal Worker** - Processes images and videos
- **Retrieval Proxy** - Unified search across all content types
- **AI Agents** - Autonomous agents using LangChain

## 📊 Monitoring Your Stack

### Health Checks
```bash
# Quick health check
./scripts/health-check.sh

# Comprehensive check
./scripts/comprehensive-health-check.sh

# Check specific service
curl http://localhost:4000/health
```

### Service Status
```bash
# View all running services
docker-compose ps

# Check service logs
docker-compose logs -f [service-name]

# View resource usage
docker stats
```

## 🎓 Next Steps

### Complete the Tutorials
The Setup Wizard includes comprehensive tutorials:
1. **Getting Started** - Basic usage and navigation
2. **API Integration** - Using the OpenAI-compatible API
3. **Multimodal Features** - Working with images and videos
4. **Troubleshooting** - Common issues and solutions

### Explore Advanced Features
- [[Multimodal Features]] - Image and video processing
- [[API Reference]] - Complete API documentation
- [[Custom Model Integration]] - Adding your own models

### Join the Community
- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Wiki Documentation**: Comprehensive guides and references

## 🆘 Getting Help

### Common Issues
- **Services won't start**: Check [[Basic Troubleshooting]]
- **Slow performance**: See [[Performance Optimization]]
- **API not responding**: Verify endpoints and authentication

### Support Resources
- **Setup Wizard**: Interactive help at `http://localhost:8004`
- **Health Checks**: Automated diagnostics
- **Logs**: Detailed error information
- **Community**: GitHub discussions and issues

## 🎉 Congratulations!

You've successfully set up your Multimodal LLM Stack! You now have:
- ✅ A running AI chat interface
- ✅ OpenAI-compatible API endpoints
- ✅ Multimodal processing capabilities
- ✅ Vector search and retrieval
- ✅ Monitoring and health checks

**What's next?** Explore the tutorials in the Setup Wizard or dive into the advanced features documented in this wiki.

---

**Need help?** The Setup Wizard at `http://localhost:8004` provides interactive tutorials and guidance for all skill levels.
