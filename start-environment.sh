#!/bin/bash
# LLM Multimodal Stack - Environment Startup Script

set -e

echo "🚀 LLM Multimodal Stack - Environment Startup"
echo "=============================================="

# Function to validate environment prerequisites
validate_environment() {
    echo "🔍 Validating environment prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check GPU for GPU-required environments
    if [[ "$ENVIRONMENT" =~ ^(dev|staging|production|monitoring|optimized)$ ]]; then
        if ! command -v nvidia-smi &> /dev/null; then
            echo "❌ NVIDIA GPU not available for $ENVIRONMENT environment"
            exit 1
        fi
        
        # Check for dual GPU setup
        gpu_count=$(nvidia-smi --list-gpus 2>/dev/null | wc -l)
        if [ "$gpu_count" -lt 2 ]; then
            echo "⚠️  Warning: Only $gpu_count GPU(s) detected. Multi-GPU configuration may not be optimal."
            echo "   Consider setting CUDA_VISIBLE_DEVICES=0 for single GPU usage."
        else
            echo "✅ Dual GPU setup detected ($gpu_count GPUs available)"
            
            # Check NVLink topology if available
            if nvidia-smi topo -m &> /dev/null; then
                echo "🔗 Checking NVLink topology..."
                nvidia-smi topo -m | grep -E "(NV[0-9]|NODE)" | head -5
            fi
        fi
    fi
    
    # Check available memory
    local available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    local required_memory=8192  # 8GB minimum
    
    if [ "$available_memory" -lt "$required_memory" ]; then
        echo "⚠️  Warning: Available memory ($available_memory MB) is below recommended minimum ($required_memory MB)"
    fi
    
    # Check port availability
    check_ports() {
        local ports=("3030" "4000" "8000" "8001" "8002" "8003" "8004" "8005" "8006" "5432" "6379" "6333" "9000" "9002" "5678")
        for port in "${ports[@]}"; do
            if netstat -tuln 2>/dev/null | grep -q ":$port "; then
                echo "⚠️  Warning: Port $port is already in use"
            fi
        done
    }
    
    check_ports
    echo "✅ Environment validation complete"
}

# Function to setup environment file
setup_environment_file() {
    local env_type=$1
    local env_file=".env.$env_type"
    
    if [ ! -f "$env_file" ]; then
        echo "🔐 Generating environment file: $env_file"
        if [ -f "setup_secrets.py" ]; then
            python3 setup_secrets.py
        else
            echo "❌ setup_secrets.py not found. Cannot generate environment file."
            exit 1
        fi
    else
        echo "✅ Environment file exists: $env_file"
    fi
}

# Function to wait for services to be healthy
wait_for_services() {
    local compose_files=$1
    echo "⏳ Waiting for services to be healthy..."
    
    # Wait for critical services
    local critical_services=("postgres" "redis" "qdrant" "minio")
    
    for service in "${critical_services[@]}"; do
        echo "   Waiting for $service..."
        # Give services time to start
        sleep 5
    done
    
    echo "✅ Critical services startup initiated"
}

# Function to handle startup errors
handle_startup_error() {
    local exit_code=$1
    local environment=$2
    
    if [ $exit_code -ne 0 ]; then
        echo "❌ Failed to start $environment environment"
        echo "🔍 Troubleshooting steps:"
        echo "   1. Check Docker status: docker info"
        echo "   2. Check available resources: free -h && df -h"
        echo "   3. Check port conflicts: netstat -tulpn | grep -E '(3030|4000|8000|5432|6379|6333|9000|9002|5678)'"
        echo "   4. Check logs: docker-compose logs"
        echo "   5. Clean up: docker-compose down --remove-orphans"
        exit $exit_code
    fi
}

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
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Force stop any remaining PostgreSQL containers
    echo "   - Ensuring PostgreSQL containers are stopped..."
    docker stop $(docker ps -q --filter "name=postgres") 2>/dev/null || true
    docker rm $(docker ps -aq --filter "name=postgres") 2>/dev/null || true
    
    # Show what volumes will be deleted
    echo "   - Volumes to be deleted:"
    volumes_to_delete=$(docker volume ls -q | grep llm-multimodal-stack || echo "   (none found)")
    if [ "$volumes_to_delete" != "   (none found)" ]; then
        echo "$volumes_to_delete" | sed 's/^/     /'
    else
        echo "     (none found)"
    fi
    
    # Remove all volumes (including PostgreSQL data)
    echo "   - Removing all multimodal volumes (including PostgreSQL databases)..."
    docker volume ls -q | grep llm-multimodal-stack | xargs -r docker volume rm 2>/dev/null || true
    
    # Additional cleanup for any remaining PostgreSQL data
    echo "   - Ensuring complete PostgreSQL data cleanup..."
    docker volume ls -q | grep -E "(postgres|multimodal)" | xargs -r docker volume rm 2>/dev/null || true
    
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
    
    # Start the development environment
    docker-compose -f docker-compose.yml -f docker-compose.development.override.yml up -d
    
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
        validate_environment
        setup_environment_file "development"
        docker-compose -f docker-compose.yml -f docker-compose.development.override.yml up -d
        handle_startup_error $? "development"
        wait_for_services "-f docker-compose.yml -f docker-compose.development.override.yml"
        echo "✅ Development environment started!"
        echo "📊 Services available:"
        echo "   - OpenWebUI: http://localhost:3030"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        ;;
    
    "staging")
        echo "🏗️ Starting Staging Environment..."
        validate_environment
        setup_environment_file "staging"
        docker-compose -f docker-compose.staging.yml up -d
        handle_startup_error $? "staging"
        wait_for_services "-f docker-compose.staging.yml"
        echo "✅ Staging environment started!"
        echo "📊 Services available:"
        echo "   - OpenWebUI: http://localhost:3030"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        ;;
    
    "production")
        echo "🚀 Starting Production Environment..."
        validate_environment
        setup_environment_file "production"
        docker-compose -f docker-compose.production.yml up -d
        handle_startup_error $? "production"
        wait_for_services "-f docker-compose.production.yml"
        echo "✅ Production environment started!"
        echo "📊 Services available:"
        echo "   - OpenWebUI: http://localhost:3030"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        ;;
    
    "testing")
        echo "🧪 Starting Testing Environment..."
        validate_environment
        docker-compose -f docker-compose.allure.yml up -d
        handle_startup_error $? "testing"
        wait_for_services "-f docker-compose.allure.yml"
        echo "✅ Testing environment started!"
        echo "📊 Services available:"
        echo "   - Allure Results: http://localhost:5050"
        echo "   - Allure Reports: http://localhost:8080"
        echo ""
        echo "🧪 To run tests:"
        echo "   python3 scripts/run_tests_with_allure.py --type all --serve"
        ;;
    
    "performance")
        echo "⚡ Starting Performance Testing Environment..."
        validate_environment
        docker-compose -f docker-compose.jmeter.yml up -d
        handle_startup_error $? "performance"
        wait_for_services "-f docker-compose.jmeter.yml"
        echo "✅ Performance testing environment started!"
        echo "📊 Services available:"
        echo "   - JMeter: Available for load testing"
        echo ""
        echo "⚡ To run performance tests:"
        echo "   python3 scripts/run_jmeter_tests.py --test all"
        ;;
    
    "monitoring")
        echo "📊 Adding Monitoring (ELK Stack)..."
        validate_environment
        setup_environment_file "monitoring"
        docker-compose -f docker-compose.yml -f docker-compose.elk.yml up -d
        handle_startup_error $? "monitoring"
        wait_for_services "-f docker-compose.yml -f docker-compose.elk.yml"
        echo "✅ Monitoring environment started!"
        echo "📊 Services available:"
        echo "   - Kibana: http://localhost:5601"
        echo "   - Elasticsearch: http://localhost:9200"
        echo "   - Logstash: http://localhost:9600"
        ;;
    
    "optimized")
        echo "🎯 Starting Optimized Environment..."
        validate_environment
        setup_environment_file "optimized"
        docker-compose -f docker-compose.optimized.yml up -d
        handle_startup_error $? "optimized"
        wait_for_services "-f docker-compose.optimized.yml"
        echo "✅ Optimized environment started!"
        echo "📊 Services available:"
        echo "   - OpenWebUI: http://localhost:3030"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        ;;
    
    *)
        echo "❌ Unknown environment: $ENVIRONMENT"
        usage
        exit 1
        ;;
esac

echo ""
echo "🔍 To check service status:"
echo "   docker-compose ps"
echo ""
echo "📋 To view logs:"
echo "   docker-compose logs -f [service-name]"
echo ""
echo "🛑 To stop environment:"
echo "   docker-compose down"
