#!/bin/bash

# One-command deployment script for beginners
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
🚀 MULTIMODAL LLM STACK - QUICK DEPLOY
====================================
   
   🤖 AI Chat Interface
   🔌 OpenAI-Compatible API  
   💾 Vector Database
   📊 Monitoring Dashboard
   
   Ready in under 10 minutes!
EOF
echo -e "${NC}"

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo -e "${YELLOW}⚠️ Please log out and back in, then re-run this script${NC}"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Git...${NC}"
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y git
    elif command -v yum &> /dev/null; then
        sudo yum install -y git
    else
        echo -e "${RED}❌ Please install Git manually${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Prerequisites OK${NC}"

# Clone repository
echo -e "${BLUE}📥 Downloading Multimodal LLM Stack...${NC}"
if [ -d "llm-multimodal-stack" ]; then
    echo "📁 Directory exists, updating..."
    cd llm-multimodal-stack
    git pull origin main
else
    git clone https://github.com/markwoitaszek/llm-multimodal-stack.git
    cd llm-multimodal-stack
fi

# Run setup
echo -e "${BLUE}⚙️ Configuring system...${NC}"
./scripts/setup.sh

# Start services
echo -e "${BLUE}🚀 Starting AI services...${NC}"
echo "⏳ This may take 2-3 minutes on first run (downloading AI models)..."

docker-compose up -d

# Wait for services
echo -e "${BLUE}⏳ Waiting for services to initialize...${NC}"
sleep 60

# Health check
echo -e "${BLUE}🏥 Checking system health...${NC}"
./scripts/comprehensive-health-check.sh

# Success message
echo ""
echo -e "${GREEN}🎉 DEPLOYMENT SUCCESSFUL!${NC}"
echo ""
echo -e "${BLUE}🌐 Your AI system is ready:${NC}"
echo "   🤖 Chat Interface: http://localhost:3030"
echo "   🔌 API Endpoint: http://localhost:8000/v1"
echo "   📊 System Status: ./scripts/stack-manager.sh status"
echo ""
echo -e "${BLUE}🎯 Next steps:${NC}"
echo "   1. Open http://localhost:3030 in your browser"
echo "   2. Start chatting with your AI!"
echo "   3. Check out docs/quick-start.md for more features"
echo ""
echo -e "${BLUE}💡 Management commands:${NC}"
echo "   ./scripts/stack-manager.sh help    # Show all commands"
echo "   ./scripts/stack-manager.sh status  # System status"
echo "   ./scripts/stack-manager.sh logs    # View logs"
echo ""
echo -e "${GREEN}🚀 Welcome to your personal AI stack!${NC}"
