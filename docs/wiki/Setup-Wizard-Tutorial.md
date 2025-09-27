# Setup Wizard Tutorial

The Setup Wizard is your interactive guide to setting up and learning about the Multimodal LLM Stack. It provides a beginner-friendly experience with step-by-step guidance, system checks, and built-in tutorials.

## 🎯 What is the Setup Wizard?

The Setup Wizard is a web-based interface that helps you:
- ✅ **Check system requirements** automatically
- ✅ **Choose the right AI model** for your hardware
- ✅ **Configure storage and security** settings
- ✅ **Deploy your stack** with proper configuration
- ✅ **Learn through interactive tutorials**

## 🚀 Accessing the Setup Wizard

### After Starting Your Stack
1. **Start the stack**: `docker-compose up -d`
2. **Open the wizard**: `http://localhost:8004`
3. **Follow the guided setup** process

### Direct Access
The Setup Wizard runs on port 8004 and is accessible once the `setup-wizard` service is running.

## 📋 Setup Wizard Steps

### Step 1: Welcome
- **Overview** of what you'll accomplish
- **System requirements** check
- **Introduction** to the setup process

### Step 2: System Check
The wizard automatically checks:
- ✅ **Docker installation** and version
- ✅ **Docker Compose** availability
- ✅ **NVIDIA GPU** detection (if available)
- ✅ **NVIDIA Docker runtime** support
- ✅ **Available disk space** and memory
- ✅ **Port conflicts** and network issues
- ✅ **NVMe storage** availability

### Step 3: Model Selection
Choose from recommended models based on your hardware:

#### Small/Fast Models (Recommended for Beginners)
- **DialoGPT Medium** - Fast conversational model (~350MB)
- **DistilGPT-2** - Lightweight and efficient (~320MB)

#### Medium Models
- **GPT-2 Medium** - Balanced performance (~1.5GB)
- **GPT-Neo 1.3B** - High-quality generation (~5GB)

#### Large Models (Requires More Resources)
- **GPT-Neo 2.7B** - High-performance (~11GB)
- **Llama 2 7B** - Meta's model (~13GB, requires approval)

### Step 4: Storage Configuration
- **Local storage** vs **NVMe storage**
- **Data directory** configuration
- **Cache settings** optimization

### Step 5: Security Configuration
- **Automatic password generation** (recommended)
- **Custom password** setup
- **SSL configuration** (for production)

### Step 6: Deployment Configuration
- **Development** vs **Production** deployment
- **Monitoring** and **logging** options
- **Service scaling** configuration

### Step 7: Validation and Deployment
- **Configuration validation**
- **Deployment process** monitoring
- **Health checks** and verification

## 🎓 Built-in Tutorials

The Setup Wizard includes comprehensive tutorials:

### Getting Started Tutorial
- **Welcome to your AI Stack** - Overview of capabilities
- **Accessing the interface** - Opening the web UI
- **Your first AI conversation** - Example prompts and tips

### API Integration Tutorial
- **API basics** - Understanding endpoints
- **Python integration** - Using the OpenAI library
- **cURL examples** - Direct API usage

### Multimodal Features Tutorial
- **Image processing** - CLIP embeddings and captioning
- **Video analysis** - Whisper transcription
- **Unified search** - Cross-modal retrieval

### Troubleshooting Tutorial
- **Health checks** - System diagnostics
- **Common issues** - Solutions and workarounds
- **Performance optimization** - Hardware utilization

## 🔧 Advanced Features

### Progress Tracking
- **Session management** - Save and resume setup
- **Progress persistence** - Don't lose your place
- **Error recovery** - Handle setup failures gracefully

### System Validation
- **Real-time checks** - Continuous system monitoring
- **Conflict detection** - Port and resource conflicts
- **Performance recommendations** - Hardware optimization tips

### Configuration Management
- **Environment file generation** - Automatic .env creation
- **Docker Compose overrides** - GPU and storage optimization
- **Security hardening** - Best practices implementation

## 🎮 Using the Tutorials

### Starting a Tutorial
1. **Complete the setup** process first
2. **Navigate to tutorials** in the wizard interface
3. **Select a tutorial** based on your interests
4. **Follow step-by-step** instructions
5. **Mark progress** as you complete steps

### Tutorial Features
- **Interactive examples** with code snippets
- **Expected outcomes** for each step
- **Helpful tips** and best practices
- **Progress tracking** and completion rewards
- **Video demonstrations** (when available)

## 🆘 Troubleshooting the Setup Wizard

### Common Issues

#### Wizard Won't Load
```bash
# Check if the service is running
docker-compose ps setup-wizard

# Check service logs
docker-compose logs setup-wizard

# Restart the service
docker-compose restart setup-wizard
```

#### System Check Fails
- **Docker not found**: Install Docker and Docker Compose
- **GPU not detected**: Check NVIDIA drivers and Docker runtime
- **Port conflicts**: Stop conflicting services or use alternative ports

#### Model Selection Issues
- **Model too large**: Choose a smaller model for your hardware
- **Download fails**: Check internet connection and disk space
- **Permission errors**: Ensure proper Docker permissions

### Getting Help
- **Setup Wizard logs**: `docker-compose logs setup-wizard`
- **Health check**: `http://localhost:8004/api/setup/health`
- **Community support**: GitHub discussions and issues

## 🚀 Production Considerations

### Security
- **Change default passwords** after setup
- **Enable SSL** for production deployments
- **Configure firewalls** and network security
- **Regular updates** and security patches

### Performance
- **Use NVMe storage** for better performance
- **Enable GPU acceleration** for faster inference
- **Scale services** based on load requirements
- **Monitor resource usage** with Grafana dashboards

### Backup and Recovery
- **Regular backups** of configuration and data
- **Disaster recovery** procedures
- **Version control** for configuration changes
- **Rollback procedures** for failed deployments

## 🎉 Next Steps

After completing the Setup Wizard:

1. **Explore the web interface** at `http://localhost:3030`
2. **Try the API endpoints** documented in [[API Reference]]
3. **Complete advanced tutorials** for multimodal features
4. **Set up monitoring** with Prometheus and Grafana
5. **Join the community** for support and feature requests

---

**The Setup Wizard is your gateway to mastering the Multimodal LLM Stack!** Use it to learn, configure, and optimize your AI infrastructure.
