#!/bin/bash
set -e

# Multimodal LLM Stack Setup Script
echo "🚀 Setting up Multimodal LLM Stack..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if NVIDIA Docker runtime is available (for GPU support)
if docker info | grep -q "nvidia"; then
    echo "✅ NVIDIA Docker runtime detected"
    GPU_SUPPORT=true
else
    echo "⚠️  NVIDIA Docker runtime not detected. GPU acceleration will not be available."
    GPU_SUPPORT=false
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ Created .env file. Please review and update the configuration."
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p models
mkdir -p data/{qdrant,postgres,minio}
mkdir -p logs

# Set permissions
echo "🔧 Setting permissions..."
chmod +x scripts/*.sh

# Check if seismic-nvme storage is available and configure paths
if [ -d "/mnt/nvme" ]; then
    echo "💾 Seismic NVMe storage detected, updating paths..."
    
    # Update .env with NVMe paths if they exist
    if grep -q "QDRANT_DATA_PATH" .env; then
        sed -i 's|QDRANT_DATA_PATH=.*|QDRANT_DATA_PATH=/mnt/nvme/qdrant|' .env
        sed -i 's|POSTGRES_DATA_PATH=.*|POSTGRES_DATA_PATH=/mnt/nvme/postgres|' .env
        sed -i 's|MINIO_DATA_PATH=.*|MINIO_DATA_PATH=/mnt/nvme/minio|' .env
        sed -i 's|CACHE_PATH=.*|CACHE_PATH=/mnt/nvme/cache|' .env
    fi
    
    # Create NVMe directories
    sudo mkdir -p /mnt/nvme/{qdrant,postgres,minio,cache}
    sudo chown -R $USER:$USER /mnt/nvme/{qdrant,postgres,minio,cache}
    
    echo "✅ Configured NVMe storage paths"
else
    echo "ℹ️  Using local storage (no NVMe detected)"
fi

# Generate secure secrets
echo "🔐 Generating secure secrets..."
if command -v openssl &> /dev/null; then
    # Generate random passwords
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    MINIO_PASSWORD=$(openssl rand -base64 32)
    LITELLM_KEY=$(openssl rand -base64 32)
    VLLM_KEY=$(openssl rand -base64 32)
    WEBUI_SECRET=$(openssl rand -base64 32)
    
    # Update .env with generated secrets
    sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|" .env
    sed -i "s|MINIO_ROOT_PASSWORD=.*|MINIO_ROOT_PASSWORD=$MINIO_PASSWORD|" .env
    sed -i "s|LITELLM_MASTER_KEY=.*|LITELLM_MASTER_KEY=sk-$LITELLM_KEY|" .env
    sed -i "s|VLLM_API_KEY=.*|VLLM_API_KEY=$VLLM_KEY|" .env
    sed -i "s|WEBUI_SECRET_KEY=.*|WEBUI_SECRET_KEY=$WEBUI_SECRET|" .env
    
    echo "✅ Generated secure secrets"
else
    echo "⚠️  OpenSSL not found. Using default passwords (update them manually!)"
fi

# Download default model if not exists
echo "📦 Checking for models..."
if [ ! -f "models/README.md" ]; then
    echo "Creating models directory structure..."
    cat > models/README.md << EOF
# Models Directory

This directory will contain downloaded models for the multimodal stack.

Models are automatically downloaded on first use, but you can pre-download them:

## Text Models
- sentence-transformers/all-MiniLM-L6-v2 (for text embeddings)

## Vision Models  
- openai/clip-vit-base-patch32 (for image embeddings)
- Salesforce/blip-image-captioning-base (for image captioning)

## Audio Models
- openai/whisper-base (for audio transcription)

## LLM Models
Configure your preferred model in the .env file under VLLM_MODEL.
Popular options:
- microsoft/DialoGPT-medium (default, small)
- meta-llama/Llama-2-7b-chat-hf (requires approval)
- mistralai/Mistral-7B-Instruct-v0.1

Models will be cached in this directory after first download.
EOF
fi

# Create docker-compose override for GPU support
if [ "$GPU_SUPPORT" = true ]; then
    echo "🎮 Creating GPU-optimized Docker Compose override..."
    cat > docker-compose.override.yml << EOF
version: '3.8'
services:
  vllm:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0
  
  multimodal-worker:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0
EOF
    echo "✅ Created GPU support configuration"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Review and update .env file with your preferred settings"
echo "2. Start the stack: docker-compose up -d"
echo "3. Check status: docker-compose ps"
echo "4. View logs: docker-compose logs -f"
echo ""
echo "Services will be available at:"
echo "- LiteLLM API: http://localhost:4000"
echo "- Multimodal Worker: http://localhost:8001"
echo "- Retrieval Proxy: http://localhost:8002"
echo "- OpenWebUI: http://localhost:3000"
echo "- Qdrant: http://localhost:6333"
echo "- MinIO Console: http://localhost:9001"
echo ""
echo "📚 See docs/ for detailed configuration and usage instructions."

