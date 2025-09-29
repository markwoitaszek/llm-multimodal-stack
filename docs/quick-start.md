# 🚀 Quick Start Guide

**Get your Multimodal LLM Stack running in under 10 minutes!**

## 🎯 What You'll Get

After this guide, you'll have:
- 🤖 **ChatGPT-like AI interface** running locally
- 🔌 **OpenAI-compatible API** for development
- 💾 **Vector database** for intelligent search
- 📊 **Monitoring dashboards** for system health

## ⚡ One-Command Setup

```bash
# Download and run the stack
curl -fsSL https://raw.githubusercontent.com/markwoitaszek/llm-multimodal-stack/main/scripts/quick-deploy.sh | bash
```

## 📋 Manual Setup (5 Steps)

### Step 1: Prerequisites Check ✅

**Required:**
- Docker & Docker Compose
- Python 3.13+
- 8GB+ free disk space
- Internet connection

**Optional (for GPU acceleration):**
- NVIDIA GPU with 8GB+ VRAM

### Step 2: Setup Secrets Management 🔐

**Phase-6A includes production-grade secrets management:**

```bash
# Generate secure secrets and environment files
python3 setup_secrets.py
```

This automatically creates:
- ✅ **21 secure secrets** (passwords, API keys, etc.)
- ✅ **Encrypted storage** with proper permissions
- ✅ **Environment-specific** configurations
- ✅ **Docker Compose** integration with environment variables
- ✅ **Kubernetes secrets** templates
- ✅ **Configurable service ports and hosts**
- ✅ **Flexible service URLs for different environments**

**Quick Check:**
```bash
# Check if you have Docker
docker --version

# Check if you have GPU (optional)
nvidia-smi
```

### Step 2: Download the Stack 📥

```bash
# Clone the repository
git clone https://github.com/markwoitaszek/llm-multimodal-stack.git
cd llm-multimodal-stack
```

### Step 3: Automatic Setup 🔧

```bash
# This handles everything automatically:
# - Generates secure passwords
# - Configures GPU (if available)
# - Sets up storage paths
# - Checks for conflicts
./scripts/setup.sh
```

### Step 4: Start the AI Stack 🚀

```bash
# Start all services
docker-compose up -d

# Wait for services to load (first time takes 2-3 minutes)
echo "⏳ Starting services... This may take a few minutes on first run."
```

### Step 5: Access Your AI System 🌐

```bash
# Check if everything is working
./scripts/comprehensive-health-check.sh

# Open your AI interface
open http://localhost:3030
```

## 🎉 You're Done!

**Your AI system is now running at:**
- 🤖 **Chat Interface**: http://localhost:3030
- 🔌 **API Endpoint**: http://localhost:8000/v1
- 📊 **System Health**: Run `./scripts/stack-manager.sh status`

## 🆘 Troubleshooting

### ❓ Common Issues

**🐳 Docker not found:**
```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in
```

**🎮 GPU not detected:**
```bash
# Install NVIDIA Docker support
sudo apt-get update
sudo apt-get install nvidia-container-toolkit
sudo systemctl restart docker
```

**🔌 Port conflicts:**
```bash
# The setup script will detect and resolve most conflicts
# Check what's using ports:
ss -tulpn | grep -E ":(3030|8000|6333|9000)"
```

**🐌 Slow startup:**
```bash
# First time downloads models (~1GB), this is normal
# Monitor progress:
docker-compose logs vllm
```

### 🆘 Get Help

**Quick Diagnostics:**
```bash
# Run comprehensive health check
./scripts/comprehensive-health-check.sh

# Check service logs
./scripts/stack-manager.sh logs

# Get system info
./scripts/stack-manager.sh status
```

**Support Resources:**
- 📚 [Full Documentation](docs/)
- 🐛 [Report Issues](https://github.com/markwoitaszek/llm-multimodal-stack/issues)
- 💬 [Community Discussions](https://github.com/markwoitaszek/llm-multimodal-stack/discussions)

## 🎯 Next Steps

**Try These Features:**
1. **Chat with AI**: Ask questions, get summaries, creative writing
2. **Upload Images**: Drag & drop images for AI analysis (coming soon)
3. **API Development**: Use the OpenAI-compatible endpoint in your code
4. **Monitor System**: Check GPU usage and system health

**Example API Usage:**
```python
import openai

# Configure for your local stack
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "dummy-key"  # Not required for local use

# Chat with your AI
response = openai.ChatCompletion.create(
    model="microsoft/DialoGPT-medium",
    messages=[{"role": "user", "content": "Explain machine learning"}]
)

print(response.choices[0].message.content)
```

## 🚀 Advanced Usage

**Management Commands:**
```bash
# Use the unified management tool
./scripts/stack-manager.sh help

# Common commands:
./scripts/stack-manager.sh status     # System status
./scripts/stack-manager.sh restart   # Restart all services
./scripts/stack-manager.sh backup    # Create backup
./scripts/stack-manager.sh update    # Update software
```

**Scale Up:**
```bash
# Add more processing power
docker-compose up -d --scale multimodal-worker=2

# Monitor performance
./scripts/stack-manager.sh benchmark
```

---

**🎉 Welcome to your personal AI stack!** You now have enterprise-grade AI capabilities running on your own hardware. 🚀
