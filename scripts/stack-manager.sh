#!/bin/bash

# Unified Stack Management Tool
# Consolidates multiple helper scripts into a single management interface

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

show_help() {
    echo "🚀 Multimodal LLM Stack Manager"
    echo "==============================="
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  setup                 - Initial setup and configuration"
    echo "  start [service]       - Start all services or specific service"
    echo "  stop [service]        - Stop all services or specific service"
    echo "  restart [service]     - Restart all services or specific service"
    echo "  status               - Show comprehensive status"
    echo "  health               - Run health checks"
    echo "  test                 - Run test suite"
    echo "  benchmark            - Run performance benchmarks"
    echo "  logs [service]       - Show logs for all or specific service"
    echo "  update               - Update software stack"
    echo "  backup               - Create system backup"
    echo "  restore <backup>     - Restore from backup"
    echo "  clean                - Clean up unused containers and volumes"
    echo "  deploy <env>         - Deploy to environment (dev/staging/prod)"
    echo ""
    echo "Examples:"
    echo "  $0 setup             # Initial setup"
    echo "  $0 start             # Start all services"
    echo "  $0 status            # Show system status"
    echo "  $0 logs vllm         # Show vLLM logs"
    echo "  $0 deploy prod       # Deploy to production"
    echo ""
}

setup_stack() {
    echo -e "${BLUE}🔧 Setting up Multimodal LLM Stack...${NC}"
    cd "$PROJECT_DIR"
    
    # Run existing setup script
    ./scripts/setup.sh
    
    # Additional setup tasks
    echo "🔍 Running post-setup validation..."
    ./scripts/comprehensive-health-check.sh || echo "⚠️ Some services may need manual configuration"
    
    echo -e "${GREEN}✅ Setup completed!${NC}"
    echo "🌐 Access your AI interface at: http://localhost:3030"
}

start_services() {
    local service=$1
    echo -e "${BLUE}🚀 Starting services...${NC}"
    cd "$PROJECT_DIR"
    
    if [ -n "$service" ]; then
        echo "Starting service: $service"
        docker-compose up -d "$service"
    else
        echo "Starting all services..."
        docker-compose up -d
    fi
    
    echo "⏳ Waiting for services to initialize..."
    sleep 30
    
    echo "📊 Service Status:"
    docker-compose ps
}

stop_services() {
    local service=$1
    echo -e "${BLUE}🛑 Stopping services...${NC}"
    cd "$PROJECT_DIR"
    
    if [ -n "$service" ]; then
        echo "Stopping service: $service"
        docker-compose stop "$service"
    else
        echo "Stopping all services..."
        docker-compose down
    fi
}

restart_services() {
    local service=$1
    echo -e "${BLUE}🔄 Restarting services...${NC}"
    
    if [ -n "$service" ]; then
        stop_services "$service"
        start_services "$service"
    else
        stop_services
        start_services
    fi
}

show_status() {
    echo -e "${BLUE}📊 System Status${NC}"
    cd "$PROJECT_DIR"
    ./scripts/comprehensive-health-check.sh
}

run_health_checks() {
    echo -e "${BLUE}🏥 Running Health Checks${NC}"
    cd "$PROJECT_DIR"
    ./scripts/comprehensive-health-check.sh
}

run_tests() {
    echo -e "${BLUE}🧪 Running Test Suite${NC}"
    cd "$PROJECT_DIR"
    
    # Run existing test script
    ./scripts/test-multimodal.sh
    
    # Add future test implementations here
    echo "📋 Note: Comprehensive test suite implementation pending"
}

run_benchmarks() {
    echo -e "${BLUE}📊 Running Performance Benchmarks${NC}"
    cd "$PROJECT_DIR"
    ./scripts/benchmark.sh
}

show_logs() {
    local service=$1
    cd "$PROJECT_DIR"
    
    if [ -n "$service" ]; then
        echo -e "${BLUE}📋 Logs for $service:${NC}"
        docker-compose logs -f "$service"
    else
        echo -e "${BLUE}📋 All Service Logs:${NC}"
        docker-compose logs -f
    fi
}

update_stack() {
    echo -e "${BLUE}🔄 Updating Software Stack${NC}"
    cd "$PROJECT_DIR"
    
    echo "📦 Pulling latest images..."
    docker-compose pull
    
    echo "🏗️ Rebuilding services..."
    docker-compose build --no-cache
    
    echo "🔄 Restarting with updates..."
    docker-compose down
    docker-compose up -d
    
    echo "✅ Update completed!"
    show_status
}

backup_system() {
    echo -e "${BLUE}💾 Creating System Backup${NC}"
    cd "$PROJECT_DIR"
    
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    echo "📋 Backing up configuration..."
    cp .env "$backup_dir/" 2>/dev/null || echo "No .env file found"
    cp -r configs/ "$backup_dir/"
    
    echo "💾 Backing up data volumes..."
    docker run --rm -v llm-multimodal-stack_postgres_data:/data -v "$(pwd)/$backup_dir":/backup alpine tar czf /backup/postgres.tar.gz -C /data .
    docker run --rm -v llm-multimodal-stack_qdrant_data:/data -v "$(pwd)/$backup_dir":/backup alpine tar czf /backup/qdrant.tar.gz -C /data .
    docker run --rm -v llm-multimodal-stack_minio_data:/data -v "$(pwd)/$backup_dir":/backup alpine tar czf /backup/minio.tar.gz -C /data .
    
    echo -e "${GREEN}✅ Backup created: $backup_dir${NC}"
}

restore_system() {
    local backup_path=$1
    if [ -z "$backup_path" ]; then
        echo -e "${RED}❌ Please specify backup path${NC}"
        echo "Usage: $0 restore <backup_directory>"
        exit 1
    fi
    
    echo -e "${BLUE}🔄 Restoring System from Backup${NC}"
    cd "$PROJECT_DIR"
    
    if [ ! -d "$backup_path" ]; then
        echo -e "${RED}❌ Backup directory not found: $backup_path${NC}"
        exit 1
    fi
    
    echo "⚠️ This will overwrite current data. Continue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Restore cancelled."
        exit 0
    fi
    
    echo "🛑 Stopping services..."
    docker-compose down
    
    echo "🔄 Restoring data..."
    docker run --rm -v llm-multimodal-stack_postgres_data:/data -v "$(pwd)/$backup_path":/backup alpine tar xzf /backup/postgres.tar.gz -C /data
    docker run --rm -v llm-multimodal-stack_qdrant_data:/data -v "$(pwd)/$backup_path":/backup alpine tar xzf /backup/qdrant.tar.gz -C /data
    docker run --rm -v llm-multimodal-stack_minio_data:/data -v "$(pwd)/$backup_path":/backup alpine tar xzf /backup/minio.tar.gz -C /data
    
    echo "🚀 Starting services..."
    docker-compose up -d
    
    echo -e "${GREEN}✅ Restore completed!${NC}"
}

clean_system() {
    echo -e "${BLUE}🧹 Cleaning Up System${NC}"
    cd "$PROJECT_DIR"
    
    echo "🗑️ Removing unused containers..."
    docker container prune -f
    
    echo "🗑️ Removing unused images..."
    docker image prune -f
    
    echo "🗑️ Removing unused volumes..."
    docker volume prune -f
    
    echo "🗑️ Removing unused networks..."
    docker network prune -f
    
    echo -e "${GREEN}✅ Cleanup completed!${NC}"
}

deploy_environment() {
    local env=$1
    echo -e "${BLUE}🚀 Deploying to $env environment${NC}"
    cd "$PROJECT_DIR"
    
    case $env in
        "dev"|"development")
            echo "📋 Development deployment..."
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
            ;;
        "staging")
            echo "📋 Staging deployment..."
            docker-compose -f docker-compose.yml up -d
            ;;
        "prod"|"production")
            echo "📋 Production deployment..."
            ./scripts/deploy-production.sh
            ;;
        *)
            echo -e "${RED}❌ Unknown environment: $env${NC}"
            echo "Valid environments: dev, staging, prod"
            exit 1
            ;;
    esac
    
    echo "✅ Deployment completed!"
    show_status
}

# Main command dispatcher
case "${1:-help}" in
    "setup")
        setup_stack
        ;;
    "start")
        start_services "$2"
        ;;
    "stop")
        stop_services "$2"
        ;;
    "restart")
        restart_services "$2"
        ;;
    "status")
        show_status
        ;;
    "health")
        run_health_checks
        ;;
    "test")
        run_tests
        ;;
    "benchmark")
        run_benchmarks
        ;;
    "logs")
        show_logs "$2"
        ;;
    "update")
        update_stack
        ;;
    "backup")
        backup_system
        ;;
    "restore")
        restore_system "$2"
        ;;
    "clean")
        clean_system
        ;;
    "deploy")
        deploy_environment "$2"
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
