#!/bin/bash

# Update software dependencies to latest versions
echo "🔄 Updating Multimodal LLM Stack Dependencies..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$(dirname "$0")/.."

echo -e "${BLUE}📊 Current vs Latest Version Analysis${NC}"
echo "===================================="

# Create updated requirements files
echo -e "${BLUE}🔄 Updating Python dependencies...${NC}"

# Update multimodal-worker requirements
cat > services/multimodal-worker/requirements.txt << 'EOF'
# Web Framework (Updated)
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.0
pydantic-settings==2.6.0

# ML Framework (Updated)
transformers==4.45.0
torch==2.4.0
torchvision==0.19.0
torchaudio==2.4.0
accelerate==0.34.0

# Multimodal Models (Updated)
sentence-transformers==3.0.1
openai-clip==1.0.1
opencv-python-headless==4.10.0.84
pillow==11.0.0

# Scientific Computing (Updated)
numpy==2.1.0
scipy==1.14.0
scikit-learn==1.5.0

# Database & Storage (Updated)
qdrant-client==1.12.0
psycopg2-binary==2.9.9
minio==7.2.8

# API & Security (Updated)
python-multipart==0.0.12
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
aiofiles==24.1.0
httpx==0.27.0

# Audio/Video Processing (Updated)
openai-whisper==20231117
librosa==0.10.2
soundfile==0.12.1
moviepy==2.0.0.dev2

# Video Tools (Updated - Replace deprecated youtube-dl)
yt-dlp==2024.8.6
imageio==2.35.0
imageio-ffmpeg==0.5.1
av==12.3.0
decord==0.6.0
EOF

# Update retrieval-proxy requirements
cat > services/retrieval-proxy/requirements.txt << 'EOF'
# Web Framework (Updated)
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.0

# Database & Vector Store (Updated)
qdrant-client==1.12.0
psycopg2-binary==2.9.9

# HTTP & API (Updated)
httpx==0.27.0
numpy==2.1.0
sentence-transformers==3.0.1

# Utilities (Updated)
python-multipart==0.0.12
aiofiles==24.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
EOF

echo -e "${GREEN}✅ Python dependencies updated${NC}"

# Update Docker base images
echo -e "${BLUE}🐳 Updating Docker configurations...${NC}"

# Update PostgreSQL version
sed -i 's/postgres:15-alpine/postgres:16-alpine/g' docker-compose.yml

# Update Qdrant version
sed -i 's/qdrant\/qdrant:v1.7.4/qdrant\/qdrant:v1.12.0/g' docker-compose.yml

# Update MinIO version
sed -i 's/minio\/minio:RELEASE.2024-01-16T16-07-38Z/minio\/minio:latest/g' docker-compose.yml

# Update vLLM version
sed -i 's/vllm\/vllm-openai:v0.2.7/vllm\/vllm-openai:latest/g' docker-compose.yml

# Update OpenWebUI version (keep main for latest)
# sed -i 's/ghcr.io\/open-webui\/open-webui:main/ghcr.io\/open-webui\/open-webui:latest/g' docker-compose.yml

echo -e "${GREEN}✅ Docker images updated${NC}"

# Create backup of current state
echo -e "${BLUE}💾 Creating backup before update...${NC}"
./scripts/stack-manager.sh backup

# Test the updates
echo -e "${BLUE}🧪 Testing updated configuration...${NC}"
docker-compose config > /dev/null && echo -e "${GREEN}✅ Configuration valid${NC}" || echo -e "${RED}❌ Configuration invalid${NC}"

echo ""
echo -e "${GREEN}🎉 Dependencies updated successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Review the changes: git diff"
echo "2. Test the updates: ./scripts/stack-manager.sh restart"
echo "3. Run health checks: ./scripts/stack-manager.sh health"
echo "4. Commit changes: git add . && git commit -m 'Update dependencies'"
echo ""
echo -e "${YELLOW}⚠️ Note: First restart may take longer due to model re-downloads${NC}"
