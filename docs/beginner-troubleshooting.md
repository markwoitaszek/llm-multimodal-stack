# 🆘 Beginner Troubleshooting Guide

**New to Docker, AI, or self-hosting? This guide is for you!**

## 🚨 Emergency Quick Fixes

### 🔥 "Nothing is working!"
```bash
# Nuclear reset - fixes 90% of issues
./scripts/stack-manager.sh stop
./scripts/stack-manager.sh clean
./scripts/stack-manager.sh setup
./scripts/stack-manager.sh start
```

### 🐌 "It's taking forever to start"
```bash
# First time downloads 1-2GB of AI models - this is normal!
# Monitor progress:
docker-compose logs vllm
# Look for: "Downloading pytorch_model.bin: 45%"
```

### 🚫 "I can't access the interface"
```bash
# Check if services are running:
./scripts/stack-manager.sh status

# Try different URL:
curl http://localhost:3030  # Should return HTML
curl http://localhost:8000/v1/models  # Should return JSON
```

## 📋 Step-by-Step Problem Solving

### Step 1: Check System Requirements ✅

**Minimum Requirements:**
- 8GB RAM (16GB recommended)
- 10GB free disk space
- Ubuntu 20.04+ or similar Linux distribution
- Internet connection for initial setup

**GPU Requirements (Optional):**
- NVIDIA GPU with 8GB+ VRAM
- NVIDIA drivers installed

**Check Your System:**
```bash
# Check RAM
free -h

# Check disk space
df -h

# Check GPU (if you have one)
nvidia-smi
```

### Step 2: Verify Docker Installation 🐳

**Test Docker:**
```bash
# Check Docker version
docker --version

# Test Docker works
docker run hello-world

# Check if you can run Docker without sudo
docker ps
```

**If Docker doesn't work:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add yourself to docker group
sudo usermod -aG docker $USER

# Log out and back in, then test:
docker run hello-world
```

### Step 3: Check for Port Conflicts 🔌

**Ports Used by the Stack:**
- 3030 - Web Interface
- 8000 - AI API
- 6333 - Vector Database
- 9000 - File Storage
- 5432 - Database

**Check for conflicts:**
```bash
# See what's using these ports
ss -tulpn | grep -E ":(3030|8000|6333|9000|5432)"

# If something is using port 3030:
sudo fuser -k 3030/tcp  # Kills the process using port 3030
```

### Step 4: Diagnose Service Issues 🔍

**Check Service Status:**
```bash
# Quick status
docker-compose ps

# Detailed health check
./scripts/comprehensive-health-check.sh

# Check specific service logs
docker-compose logs postgres    # Database
docker-compose logs vllm       # AI Model
docker-compose logs openwebui  # Web Interface
```

**Common Service Issues:**

**🗄️ Database Issues:**
```bash
# Symptoms: "connection refused", "authentication failed"
# Fix: Reset database
docker-compose stop postgres
docker volume rm llm-multimodal-stack_postgres_data
docker-compose up -d postgres
```

**🤖 AI Model Issues:**
```bash
# Symptoms: "model not found", "CUDA out of memory"
# Check GPU memory:
nvidia-smi

# Use smaller model:
echo "VLLM_MODEL=microsoft/DialoGPT-small" >> .env
docker-compose restart vllm
```

**🌐 Web Interface Issues:**
```bash
# Symptoms: "502 Bad Gateway", "connection refused"
# Check if API is running:
curl http://localhost:8000/v1/models

# Restart web interface:
docker-compose restart openwebui
```

## 🎯 Common Error Messages

### "Permission denied"
```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
# Log out and back in
```

### "Port already in use"
```bash
# Find what's using the port
sudo lsof -i :3030

# Kill the process or change port in docker-compose.yml
```

### "No space left on device"
```bash
# Clean up Docker
docker system prune -a
docker volume prune

# Check disk space
df -h
```

### "CUDA out of memory"
```bash
# Use smaller model
echo "VLLM_MODEL=microsoft/DialoGPT-small" >> .env

# Or reduce GPU memory usage
sed -i 's/gpu-memory-utilization 0.8/gpu-memory-utilization 0.6/' docker-compose.yml
docker-compose restart vllm
```

### "Model download failed"
```bash
# Check internet connection
curl -I https://huggingface.co

# Clear model cache and retry
docker volume rm llm-multimodal-stack_vllm_cache
docker-compose restart vllm
```

## 🔧 Environment-Specific Issues

### 🐧 Linux Issues

**Ubuntu/Debian:**
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Install required packages
sudo apt install curl git build-essential
```

**CentOS/RHEL:**
```bash
# Update system
sudo yum update

# Install packages
sudo yum install curl git gcc
```

### 🖥️ Server Issues

**Headless Server (No GUI):**
```bash
# Access web interface from another machine
# Replace localhost with your server IP:
http://your-server-ip:3030
```

**Firewall Issues:**
```bash
# Open required ports
sudo ufw allow 3030  # Web interface
sudo ufw allow 8000  # API
sudo ufw status
```

### 🏠 Home Network Issues

**Router/NAT Issues:**
```bash
# Access from other devices on network
# Use server's local IP instead of localhost
ip addr show | grep "inet 192"  # Find your local IP
# Then use: http://192.168.x.x:3030
```

## 🆘 Getting Help

### Self-Diagnosis Tools

**Automated Diagnostics:**
```bash
# Comprehensive system check
./scripts/comprehensive-health-check.sh

# Generate debug report
./scripts/stack-manager.sh status > debug-report.txt
docker-compose logs >> debug-report.txt
nvidia-smi >> debug-report.txt 2>/dev/null || echo "No GPU" >> debug-report.txt
```

**Manual Checks:**
```bash
# Check Docker daemon
systemctl status docker

# Check available resources
free -h          # Memory
df -h            # Disk space
nvidia-smi       # GPU (if available)
```

### When to Ask for Help

**Ask for help if:**
- System requirements are met but setup still fails
- Error messages are unclear or not covered here
- Performance is significantly slower than expected
- You need help with advanced configuration

**Before asking:**
1. Run `./scripts/comprehensive-health-check.sh`
2. Check this troubleshooting guide
3. Search existing GitHub issues
4. Collect debug information

### Support Channels

- 🐛 **GitHub Issues**: Technical problems and bugs
- 💬 **Discussions**: General questions and help
- 📚 **Documentation**: Comprehensive guides
- 🔍 **Search**: Often someone has solved your problem already

## 💡 Pro Tips

### Performance Optimization
```bash
# Monitor resource usage
htop                    # CPU and memory
nvidia-smi -l 1        # GPU usage
docker stats           # Container resources
```

### Maintenance
```bash
# Weekly maintenance
./scripts/stack-manager.sh clean    # Clean up unused resources
./scripts/stack-manager.sh backup   # Create backup
./scripts/stack-manager.sh update   # Update software
```

### Customization
```bash
# Change AI model (edit .env file)
nano .env
# Look for VLLM_MODEL= and change it

# Scale up processing
docker-compose up -d --scale multimodal-worker=2
```

---

**Remember**: This is advanced software made beginner-friendly. Don't hesitate to ask for help - the community is here to support you! 🤝
