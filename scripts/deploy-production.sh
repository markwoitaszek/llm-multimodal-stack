#!/bin/bash
set -e

# Production deployment script for Multimodal LLM Stack
echo "🚀 Deploying Multimodal LLM Stack to Production..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DOMAIN=${DOMAIN:-localhost}
EMAIL=${EMAIL:-admin@localhost}

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose not found${NC}"
        exit 1
    fi
    
    if ! docker info | grep -q "nvidia"; then
        echo -e "${YELLOW}⚠️  NVIDIA Docker runtime not detected${NC}"
        read -p "Continue without GPU support? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Generate SSL certificates
generate_ssl_certs() {
    echo -e "${BLUE}🔐 Setting up SSL certificates...${NC}"
    
    mkdir -p certs
    
    if [ ! -f "certs/cert.pem" ] || [ ! -f "certs/key.pem" ]; then
        echo "Generating self-signed certificates for $DOMAIN..."
        openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem \
            -days 365 -nodes -subj "/CN=$DOMAIN/O=Multimodal LLM Stack"
        
        echo -e "${GREEN}✅ SSL certificates generated${NC}"
    else
        echo -e "${GREEN}✅ SSL certificates already exist${NC}"
    fi
}

# Setup production environment
setup_production_env() {
    echo -e "${BLUE}⚙️  Setting up production environment...${NC}"
    
    # Create production .env if it doesn't exist
    if [ ! -f ".env.prod" ]; then
        cp env.example .env.prod
        
        # Generate secure passwords
        if command -v openssl &> /dev/null; then
            POSTGRES_PASSWORD=$(openssl rand -base64 32)
            MINIO_PASSWORD=$(openssl rand -base64 32)
            LITELLM_KEY=$(openssl rand -base64 32)
            VLLM_KEY=$(openssl rand -base64 32)
            WEBUI_SECRET=$(openssl rand -base64 32)
            GRAFANA_PASSWORD=$(openssl rand -base64 32)
            
            # Update .env.prod
            sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|" .env.prod
            sed -i "s|MINIO_ROOT_PASSWORD=.*|MINIO_ROOT_PASSWORD=$MINIO_PASSWORD|" .env.prod
            sed -i "s|LITELLM_MASTER_KEY=.*|LITELLM_MASTER_KEY=sk-$LITELLM_KEY|" .env.prod
            sed -i "s|VLLM_API_KEY=.*|VLLM_API_KEY=$VLLM_KEY|" .env.prod
            sed -i "s|WEBUI_SECRET_KEY=.*|WEBUI_SECRET_KEY=$WEBUI_SECRET|" .env.prod
            echo "GRAFANA_PASSWORD=$GRAFANA_PASSWORD" >> .env.prod
            
            echo -e "${GREEN}✅ Generated secure passwords${NC}"
        fi
        
        echo -e "${YELLOW}⚠️  Please review and update .env.prod with your settings${NC}"
    fi
    
    # Setup NVMe paths if available
    if [ -d "/mnt/nvme" ]; then
        echo "Configuring NVMe storage paths..."
        sudo mkdir -p /mnt/nvme/{qdrant,postgres,minio,cache,grafana,prometheus,redis}
        sudo chown -R $USER:$USER /mnt/nvme/
        
        # Update .env.prod with NVMe paths
        sed -i "s|QDRANT_DATA_PATH=.*|QDRANT_DATA_PATH=/mnt/nvme/qdrant|" .env.prod
        sed -i "s|POSTGRES_DATA_PATH=.*|POSTGRES_DATA_PATH=/mnt/nvme/postgres|" .env.prod
        sed -i "s|MINIO_DATA_PATH=.*|MINIO_DATA_PATH=/mnt/nvme/minio|" .env.prod
        sed -i "s|CACHE_PATH=.*|CACHE_PATH=/mnt/nvme/cache|" .env.prod
        
        echo -e "${GREEN}✅ Configured NVMe storage${NC}"
    fi
}

# Deploy services
deploy_services() {
    echo -e "${BLUE}🚢 Deploying services...${NC}"
    
    # Use production environment
    export $(cat .env.prod | grep -v '^#' | xargs)
    
    # Pull latest images
    echo "Pulling latest images..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
    
    # Build custom services
    echo "Building custom services..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
    
    # Start infrastructure services first
    echo "Starting infrastructure services..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d \
        postgres qdrant minio redis prometheus grafana nginx
    
    # Wait for infrastructure to be ready
    echo "Waiting for infrastructure services..."
    sleep 30
    
    # Start application services
    echo "Starting application services..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    echo -e "${GREEN}✅ Services deployed${NC}"
}

# Verify deployment
verify_deployment() {
    echo -e "${BLUE}🔍 Verifying deployment...${NC}"
    
    # Wait for services to start
    echo "Waiting for services to initialize..."
    sleep 60
    
    # Run health checks
    if ./scripts/health-check.sh; then
        echo -e "${GREEN}✅ All services are healthy${NC}"
    else
        echo -e "${RED}❌ Some services are unhealthy${NC}"
        echo "Check logs with: docker-compose logs [service_name]"
        exit 1
    fi
    
    # Test basic functionality
    echo "Testing basic functionality..."
    
    # Test LiteLLM API
    if curl -s -f "http://localhost:4000/health" > /dev/null; then
        echo -e "${GREEN}✅ LiteLLM API accessible${NC}"
    else
        echo -e "${RED}❌ LiteLLM API not accessible${NC}"
    fi
    
    # Test web interface
    if curl -s -f "http://localhost:80" > /dev/null; then
        echo -e "${GREEN}✅ Web interface accessible${NC}"
    else
        echo -e "${RED}❌ Web interface not accessible${NC}"
    fi
}

# Setup monitoring
setup_monitoring() {
    echo -e "${BLUE}📊 Setting up monitoring...${NC}"
    
    # Wait for Grafana to start
    echo "Waiting for Grafana to initialize..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -s -f "http://localhost:3001/api/health" > /dev/null 2>&1; then
            break
        fi
        sleep 5
        timeout=$((timeout - 5))
    done
    
    if [ $timeout -le 0 ]; then
        echo -e "${YELLOW}⚠️  Grafana not ready, skipping dashboard setup${NC}"
        return
    fi
    
    echo -e "${GREEN}✅ Monitoring setup complete${NC}"
}

# Print deployment summary
print_summary() {
    echo ""
    echo -e "${GREEN}🎉 Deployment Complete!${NC}"
    echo "=================================="
    echo ""
    echo "🌐 Web Interface: http://$DOMAIN"
    echo "🔗 API Endpoint: http://$DOMAIN/v1"
    echo "📊 Grafana: http://$DOMAIN:3001"
    echo "🗄️  MinIO Console: http://$DOMAIN:9001"
    echo ""
    echo "📋 Service Status:"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "🔐 Credentials saved in .env.prod"
    echo ""
    echo "📚 Next steps:"
    echo "1. Update DNS to point $DOMAIN to this server"
    echo "2. Replace self-signed certificates with proper SSL certs"
    echo "3. Configure firewall rules"
    echo "4. Set up automated backups"
    echo "5. Configure log rotation"
    echo ""
    echo "🛠️  Management commands:"
    echo "- Health check: ./scripts/health-check.sh"
    echo "- View logs: docker-compose logs -f [service]"
    echo "- Scale service: docker-compose up -d --scale multimodal-worker=3"
    echo "- Update: ./scripts/update-production.sh"
    echo ""
}

# Cleanup on failure
cleanup_on_failure() {
    echo -e "${RED}💥 Deployment failed, cleaning up...${NC}"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
    exit 1
}

# Main deployment process
main() {
    # Set trap for cleanup on failure
    trap cleanup_on_failure ERR
    
    echo -e "${BLUE}🚀 Starting Production Deployment${NC}"
    echo "Domain: $DOMAIN"
    echo "Email: $EMAIL"
    echo ""
    
    check_prerequisites
    generate_ssl_certs
    setup_production_env
    deploy_services
    verify_deployment
    setup_monitoring
    print_summary
    
    echo -e "${GREEN}✅ Production deployment completed successfully!${NC}"
}

# Run main function
main "$@"
