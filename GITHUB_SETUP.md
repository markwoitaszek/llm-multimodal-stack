# 🔧 GitHub Token Setup for Issue Creation

## 🎯 Quick Setup

### Step 1: Create GitHub Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Set these permissions:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `issues` (Read and write issues)
   - ✅ `pull_requests` (Read and write pull requests)

### Step 2: Set Environment Variable

```bash
# Set the token (replace with your actual token)
export GITHUB_TOKEN=ghp_your_token_here

# Verify it's set
echo "Token set: ${GITHUB_TOKEN:0:10}..."
```

### Step 3: Create Issues

```bash
# Run the issue creation script
python3 scripts/create-deployment-issues.py
```

## 🐛 Issues to Create

The script will create these issues based on our deployment:

### 1. **LiteLLM Database Authentication Failure**
- **Priority**: High
- **Component**: API Router
- **Status**: Blocking OpenAI-compatible API routing

### 2. **Multimodal Worker CUDA Compatibility**
- **Priority**: Medium
- **Component**: Multimodal Worker
- **Status**: Blocking image/video processing

### 3. **Service Health Check Issues**
- **Priority**: Medium
- **Component**: Docker/Monitoring
- **Status**: Cosmetic but affects monitoring

### 4. **Port Conflicts Resolution**
- **Priority**: Medium
- **Component**: Configuration
- **Status**: Partially resolved, needs documentation

### 5. **Complete Multimodal Deployment**
- **Priority**: High
- **Component**: Enhancement
- **Status**: Core functionality for full stack

## 🔄 Alternative: Manual Issue Creation

If you prefer to create issues manually, here are the quick templates:

### Issue 1: LiteLLM Authentication
```
Title: [BUG] LiteLLM database authentication failure during deployment
Labels: bug, priority/high, component/api, deployment
```

### Issue 2: CUDA Compatibility  
```
Title: [BUG] Multimodal Worker CUDA base image compatibility issue
Labels: bug, priority/medium, component/worker, docker, gpu
```

### Issue 3: Health Checks
```
Title: [TASK] Fix service health check endpoints and timing
Labels: task, priority/medium, component/docker, monitoring
```

### Issue 4: Port Conflicts
```
Title: [TASK] Resolve port conflicts with existing services
Labels: task, priority/medium, component/docker, configuration
```

### Issue 5: Multimodal Enhancement
```
Title: [ENHANCEMENT] Complete multimodal worker deployment
Labels: enhancement, priority/high, component/worker, gpu
```

## 🎯 After Creating Issues

1. **Assign to yourself** for tracking
2. **Add to project board** for visibility
3. **Link related issues** if applicable
4. **Set milestones** for release planning

The GitHub Actions workflows will automatically:
- ✅ Add issues to project boards
- ✅ Apply additional labels based on content
- ✅ Track metrics and progress
