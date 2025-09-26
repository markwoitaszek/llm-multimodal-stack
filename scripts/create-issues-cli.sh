#!/bin/bash

# Create GitHub issues using GitHub CLI or curl
echo "🐛 Creating GitHub issues for deployment problems..."

# Check if GitHub CLI is available
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI detected, creating issues..."
    
    # Issue 1: LiteLLM Authentication
    gh issue create \
        --title "[BUG] LiteLLM database authentication failure during deployment" \
        --body "## 🐛 Bug Description

LiteLLM service fails to start due to PostgreSQL authentication errors during deployment.

**Error**: P1000: Authentication failed against database server at \`postgres\`

**Environment**: seismic server, RTX 3090, develop branch

**Workaround**: OpenWebUI connected directly to vLLM

**Impact**: Blocks OpenAI-compatible API routing" \
        --label "bug,priority/high,component/api,deployment"
    
    # Issue 2: CUDA Compatibility
    gh issue create \
        --title "[BUG] Multimodal Worker CUDA base image compatibility issue" \
        --body "## 🐛 Bug Description

Multimodal Worker fails to build due to unavailable CUDA base image.

**Error**: nvidia/cuda:11.8-devel-ubuntu22.04: not found

**Environment**: CUDA 13.0, Docker 27.5.1

**Solution**: Update Dockerfile to use CUDA 12.x base image

**Impact**: Blocks multimodal processing (CLIP, BLIP-2, Whisper)" \
        --label "bug,priority/medium,component/worker,docker,gpu"
    
    # Issue 3: Health Checks
    gh issue create \
        --title "[TASK] Fix service health check endpoints and timing" \
        --body "## 📋 Task Description

Services showing as unhealthy despite being functional.

**Issues**:
- Qdrant: Wrong health endpoint
- MinIO: Timing issues
- vLLM: Model loading time

**Goal**: All functional services show as healthy" \
        --label "task,priority/medium,component/docker,monitoring"
    
    # Issue 4: Port Conflicts
    gh issue create \
        --title "[TASK] Resolve port conflicts with existing services" \
        --body "## 📋 Task Description

Port conflicts with existing seismic server services.

**Resolved**: MinIO console moved from 9001 to 9002 (Portainer conflict)

**Remaining**: Document all port assignments and update docs

**Goal**: Clean port management and updated documentation" \
        --label "task,priority/medium,component/docker,configuration"
    
    # Issue 5: Complete Deployment
    gh issue create \
        --title "[ENHANCEMENT] Complete multimodal worker deployment" \
        --body "## ✨ Enhancement Description

Complete the multimodal worker deployment for full stack functionality.

**Current**: vLLM working (16GB GPU usage)
**Goal**: Add CLIP, BLIP-2, Whisper processing

**Benefits**: 
- Image embeddings and captioning
- Video transcription and keyframes
- Cross-modal search capabilities

**GPU**: Optimize memory allocation between vLLM and multimodal models" \
        --label "enhancement,priority/high,component/worker,gpu"
    
    echo "🎉 Issues created successfully!"
    echo "🔗 View issues: https://github.com/markwoitaszek/llm-multimodal-stack/issues"

elif command -v curl &> /dev/null; then
    echo "❌ GitHub CLI not found"
    echo "📋 Please install GitHub CLI or set up GITHUB_TOKEN"
    echo ""
    echo "🔧 Install GitHub CLI:"
    echo "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg"
    echo "echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null"
    echo "sudo apt update && sudo apt install gh"
    echo ""
    echo "🔐 Then authenticate:"
    echo "gh auth login"
    echo ""
    echo "🐛 Or create issues manually at:"
    echo "https://github.com/markwoitaszek/llm-multimodal-stack/issues/new/choose"

else
    echo "❌ Neither GitHub CLI nor curl available"
    echo "📋 Please install GitHub CLI or create issues manually"
fi
