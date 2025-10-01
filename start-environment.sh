#!/bin/bash
# LLM Multimodal Stack - Environment Startup Script

set -e

echo "🚀 LLM Multimodal Stack - Environment Startup"
echo "=============================================="

# Function to check and cleanup Docker system if needed
check_docker_cleanup() {
    echo "🔍 Checking Docker system health..."
    
    # Get reclaimable space percentage
    RECLAIMABLE=$(docker system df --format "{{.Reclaimable}}" | head -1 | sed 's/[()%]//g' | sed 's/[^0-9.]//g' | cut -d'.' -f1 2>/dev/null || echo "0")
    
    if [ "$RECLAIMABLE" -gt 30 ]; then
        echo "⚠️  High Docker reclaimable space detected: $RECLAIMABLE%"
        echo "🧹 Running automatic cleanup..."
        docker system prune -f
        echo "✅ Docker cleanup complete"
    else
        echo "✅ Docker system healthy ($RECLAIMABLE% reclaimable)"
    fi
    echo ""
}

# Function to perform first-run setup
first_run_setup() {
    echo "🚨 FIRST RUN SETUP - DESTRUCTIVE OPERATION"
    echo "=========================================="
    echo ""
    echo "⚠️  WARNING: This will DELETE all existing data and containers!"
    echo ""
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        echo "❌ This operation requires sudo privileges for safety."
        echo "   Please run: sudo $0 first-run"
        exit 1
    fi
    
    # Show what will be deleted
    echo "🔍 Scanning current environment to show what will be deleted..."
    echo ""
    
    # Check for existing containers
    echo "📦 EXISTING CONTAINERS:"
    existing_containers=$(docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(multimodal|llm-multimodal)" || echo "   No multimodal containers found")
    if [ "$existing_containers" != "   No multimodal containers found" ]; then
        echo "$existing_containers"
    else
        echo "   No multimodal containers found"
    fi
    echo ""
    
    # Check for existing volumes
    echo "💾 EXISTING VOLUMES:"
    existing_volumes=$(docker volume ls --format "table {{.Name}}\t{{.Driver}}\t{{.Size}}" | grep llm-multimodal-stack || echo "   No multimodal volumes found")
    if [ "$existing_volumes" != "   No multimodal volumes found" ]; then
        echo "$existing_volumes"
    else
        echo "   No multimodal volumes found"
    fi
    echo ""
    
    # Check for existing networks
    echo "🌐 EXISTING NETWORKS:"
    existing_networks=$(docker network ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" | grep llm-multimodal-stack || echo "   No multimodal networks found")
    if [ "$existing_networks" != "   No multimodal networks found" ]; then
        echo "$existing_networks"
    else
        echo "   No multimodal networks found"
    fi
    echo ""
    
    # Check for existing environment files
    echo "📄 EXISTING ENVIRONMENT FILES:"
    if [ -f ".env" ]; then
        echo "   - .env (will be backed up and regenerated)"
    else
        echo "   - No .env file found (will be created)"
    fi
    if [ -f ".env.development" ]; then
        echo "   - .env.development (will be backed up and regenerated)"
    fi
    echo ""
    
    # Show what will happen
    echo "🎯 OPERATIONS TO BE PERFORMED:"
    echo "   1. Stop and remove all multimodal containers"
    echo "   2. Delete all multimodal Docker volumes (ALL DATA WILL BE LOST)"
    echo "   3. Remove all multimodal Docker networks"
    echo "   4. Clean up orphaned containers"
    echo "   5. Backup existing environment files"
    echo "   6. Generate new secure environment configuration"
    echo "   7. Start fresh development environment"
    echo ""
    
    # Final confirmation
    echo "⚠️  FINAL WARNING: This will permanently delete all data!"
    echo "   Are you absolutely sure you want to proceed?"
    echo "   Type 'DELETE' to continue:"
    read -r confirmation
    if [ "$confirmation" != "DELETE" ]; then
        echo "❌ Operation cancelled by user."
        exit 1
    fi
    
    echo ""
    echo "🧹 Step 1: Cleaning existing environment..."
    
    # Stop and remove all containers
    echo "   - Stopping all multimodal containers..."
    docker compose down --remove-orphans 2>/dev/null || true
    
    # Show what volumes will be deleted
    echo "   - Volumes to be deleted:"
    volumes_to_delete=$(docker volume ls -q | grep llm-multimodal-stack || echo "   (none found)")
    if [ "$volumes_to_delete" != "   (none found)" ]; then
        echo "$volumes_to_delete" | sed 's/^/     /'
    else
        echo "     (none found)"
    fi
    
    # Remove all volumes
    echo "   - Removing all multimodal volumes..."
    docker volume ls -q | grep llm-multimodal-stack | xargs -r docker volume rm 2>/dev/null || true
    
    # Show what networks will be deleted
    echo "   - Networks to be deleted:"
    networks_to_delete=$(docker network ls -q | grep llm-multimodal-stack || echo "   (none found)")
    if [ "$networks_to_delete" != "   (none found)" ]; then
        echo "$networks_to_delete" | sed 's/^/     /'
    else
        echo "     (none found)"
    fi
    
    # Remove all networks
    echo "   - Removing all multimodal networks..."
    docker network ls -q | grep llm-multimodal-stack | xargs -r docker network rm 2>/dev/null || true
    
    # Clean up any orphaned containers
    echo "   - Cleaning up orphaned containers..."
    docker container prune -f 2>/dev/null || true
    
    echo "✅ Environment cleanup complete"
    echo ""
    
    echo "🔐 Step 2: Generating secure environment configuration..."
    
    # Backup existing environment files
    if [ -f ".env" ]; then
        echo "   - Backing up existing .env to .env.backup.$(date +%Y%m%d_%H%M%S)"
        cp .env ".env.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    if [ -f ".env.development" ]; then
        echo "   - Backing up existing .env.development to .env.development.backup.$(date +%Y%m%d_%H%M%S)"
        cp .env.development ".env.development.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Check if setup_secrets.py exists
    if [ -f "setup_secrets.py" ]; then
        echo "   - Running secrets generator..."
        python3 setup_secrets.py
        if [ $? -eq 0 ]; then
            echo "✅ Secure environment configuration generated"
        else
            echo "❌ Failed to generate environment configuration"
            exit 1
        fi
    else
        echo "   - setup_secrets.py not found, using fallback method..."
        # Fallback to basic setup
        if [ -f "scripts/setup.sh" ]; then
            bash scripts/setup.sh
        else
            echo "❌ No setup script found. Please ensure setup_secrets.py or scripts/setup.sh exists."
            exit 1
        fi
    fi
    
    echo ""
    echo "🚀 Step 3: Starting development environment..."
    
    # Start the development environment using new normalized structure
    docker compose up -d
    
    echo ""
    echo "🎉 First run setup completed successfully!"
    echo ""
    echo "📊 Services available:"
    echo "   - OpenWebUI: http://localhost:3030"
    echo "   - LiteLLM: http://localhost:4000"
    echo "   - Multimodal Worker: http://localhost:8001"
    echo "   - Retrieval Proxy: http://localhost:8002"
    echo "   - vLLM: http://localhost:8000"
    echo "   - Qdrant: http://localhost:6333"
    echo "   - MinIO Console: http://localhost:9002"
    echo ""
    echo "🔍 To check service status:"
    echo "   docker-compose ps"
    echo ""
    echo "📋 To view logs:"
    echo "   docker-compose logs -f [service-name]"
    echo ""
    echo "🛑 To stop environment:"
    echo "   docker-compose down"
}

# Function to display usage
usage() {
    echo "Usage: $0 [environment]"
    echo ""
    echo "Environments:"
    echo "  dev       - Development (base services only)"
    echo "  staging   - Staging environment"
    echo "  production - Production environment"
    echo "  testing   - Testing with Allure reports"
    echo "  performance - Performance testing with JMeter"
    echo "  monitoring - Add ELK stack for monitoring"
    echo "  optimized - Performance-optimized environment"
    echo "  first-run - Complete first-time setup (REQUIRES SUDO)"
    echo ""
    echo "Examples:"
    echo "  $0 dev                    # Start development environment"
    echo "  $0 staging               # Start staging environment"
    echo "  $0 production            # Start production environment"
    echo "  $0 testing               # Start testing environment"
    echo "  $0 performance           # Start performance testing"
    echo "  $0 monitoring            # Add monitoring to current environment"
    echo "  $0 first-run             # Complete first-time setup (DESTRUCTIVE)"
    echo ""
    echo "⚠️  WARNING: 'first-run' will DELETE all existing data and containers!"
}

# Check if environment is specified
if [ $# -eq 0 ]; then
    usage
    exit 1
fi

ENVIRONMENT=$1

# Run Docker cleanup check before starting environment
check_docker_cleanup

case $ENVIRONMENT in
    "first-run")
        first_run_setup
        ;;
    
    "dev"|"development")
        echo "🔧 Starting Development Environment..."
        docker compose up -d
        echo "✅ Development environment started!"
        echo "📊 Services available:"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        echo "   - vLLM: http://localhost:8000"
        echo "   - Qdrant: http://localhost:6333"
        echo "   - MinIO Console: http://localhost:9002"
        ;;
    
    "staging")
        echo "🏗️ Starting Staging Environment..."
        docker compose -f compose.yml -f compose.production.yml --profile services --profile monitoring up -d
        echo "✅ Staging environment started!"
        echo "📊 Services available:"
        echo "   - OpenWebUI: http://localhost:3030"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        echo "   - AI Agents: http://localhost:8003"
        echo "   - Search Engine: http://localhost:8004"
        echo "   - Memory System: http://localhost:8005"
        echo "   - User Management: http://localhost:8006"
        echo "   - n8n: http://localhost:5678"
        ;;
    
    "production")
        echo "🚀 Starting Production Environment..."
        docker compose -f compose.yml -f compose.production.yml --profile services --profile monitoring up -d
        echo "✅ Production environment started!"
        echo "📊 Services available:"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        echo "   - AI Agents: http://localhost:8003"
        echo "   - Search Engine: http://localhost:8004"
        echo "   - Memory System: http://localhost:8005"
        echo "   - User Management: http://localhost:8006"
        echo "   - n8n: http://localhost:5678"
        echo "   - n8n Monitoring: http://localhost:8008"
        ;;
    
    "testing")
        echo "🧪 Starting Testing Environment..."
        docker compose up -d
        # Note: Allure testing would need to be added as a separate profile
        echo "✅ Testing environment started!"
        echo "📊 Services available:"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        echo "   - vLLM: http://localhost:8000"
        echo ""
        echo "🧪 To run tests:"
        echo "   python3 scripts/run_tests_with_allure.py --type all --serve"
        ;;
    
    "performance")
        echo "⚡ Starting Performance Testing Environment..."
        docker compose up -d
        # Note: JMeter testing would need to be added as a separate profile
        echo "✅ Performance testing environment started!"
        echo "📊 Services available:"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        echo "   - vLLM: http://localhost:8000"
        echo ""
        echo "⚡ To run performance tests:"
        echo "   python3 scripts/run_jmeter_tests.py --test all"
        ;;
    
    "monitoring")
        echo "📊 Adding Monitoring (ELK Stack)..."
        docker compose -f compose.yml -f compose.elk.yml --profile elk --profile monitoring up -d
        echo "✅ Monitoring environment started!"
        echo "📊 Services available:"
        echo "   - Kibana: http://localhost:5601"
        echo "   - Elasticsearch: http://localhost:9200"
        echo "   - Logstash: http://localhost:9600"
        echo "   - OpenWebUI: http://localhost:3030"
        echo "   - n8n: http://localhost:5678"
        ;;
    
    "optimized")
        echo "🎯 Starting Optimized Environment..."
        docker compose -f compose.yml -f compose.gpu.yml -f compose.production.yml up -d
        echo "✅ Optimized environment started!"
        echo "📊 Services available:"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        echo "   - vLLM: http://localhost:8000 (GPU optimized)"
        echo "   - Qdrant: http://localhost:6333"
        echo "   - MinIO Console: http://localhost:9002"
        ;;
    
    *)
        echo "❌ Unknown environment: $ENVIRONMENT"
        usage
        exit 1
        ;;
esac

echo ""
echo "🔍 To check service status:"
echo "   docker compose ps"
echo ""
echo "📋 To view logs:"
echo "   docker compose logs -f [service-name]"
echo ""
echo "🛑 To stop environment:"
echo "   docker compose down"
