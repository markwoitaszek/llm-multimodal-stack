#!/bin/bash

# Docker Compose Manager Script
# Helps manage different Docker Compose configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to show usage
show_usage() {
    echo -e "${BLUE}🐳 Docker Compose Manager${NC}"
    echo "=========================="
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  dev          Start development environment (optimized)"
    echo "  dev-std      Start standard development environment"
    echo "  test         Start test environment"
    echo "  prod         Start production environment"
    echo "  db           Start enhanced database environment"
    echo "  stop         Stop all services"
    echo "  status       Show service status"
    echo "  logs         Show logs for all services"
    echo "  clean        Clean up unused containers and images"
    echo "  list         List available configurations"
    echo ""
    echo "Options:"
    echo "  -d, --detach     Run in background (default)"
    echo "  -f, --foreground Run in foreground"
    echo "  -b, --build      Build images before starting"
    echo "  --no-cache       Build without cache"
    echo ""
    echo "Examples:"
    echo "  $0 dev                    # Start optimized development"
    echo "  $0 test -f                # Start test environment in foreground"
    echo "  $0 prod -b                # Build and start production"
    echo "  $0 logs                   # Show logs"
    echo "  $0 clean                  # Clean up"
}

# Function to start development environment
start_dev() {
    local build_flag=""
    local detach_flag="-d"
    
    if [[ "$*" == *"-b"* ]] || [[ "$*" == *"--build"* ]]; then
        build_flag="--build"
    fi
    
    if [[ "$*" == *"-f"* ]] || [[ "$*" == *"--foreground"* ]]; then
        detach_flag=""
    fi
    
    echo -e "${YELLOW}🚀 Starting optimized development environment...${NC}"
    docker-compose -f docker-compose.optimized.yml up $detach_flag $build_flag
}

# Function to start standard development environment
start_dev_std() {
    local build_flag=""
    local detach_flag="-d"
    
    if [[ "$*" == *"-b"* ]] || [[ "$*" == *"--build"* ]]; then
        build_flag="--build"
    fi
    
    if [[ "$*" == *"-f"* ]] || [[ "$*" == *"--foreground"* ]]; then
        detach_flag=""
    fi
    
    echo -e "${YELLOW}🚀 Starting standard development environment...${NC}"
    docker-compose up $detach_flag $build_flag
}

# Function to start test environment
start_test() {
    local build_flag=""
    local detach_flag="-d"
    
    if [[ "$*" == *"-b"* ]] || [[ "$*" == *"--build"* ]]; then
        build_flag="--build"
    fi
    
    if [[ "$*" == *"-f"* ]] || [[ "$*" == *"--foreground"* ]]; then
        detach_flag=""
    fi
    
    echo -e "${YELLOW}🧪 Starting test environment...${NC}"
    docker-compose -f docker-compose.test.yml up $detach_flag $build_flag
}

# Function to start production environment
start_prod() {
    local build_flag=""
    local detach_flag="-d"
    
    if [[ "$*" == *"-b"* ]] || [[ "$*" == *"--build"* ]]; then
        build_flag="--build"
    fi
    
    if [[ "$*" == *"-f"* ]] || [[ "$*" == *"--foreground"* ]]; then
        detach_flag=""
    fi
    
    echo -e "${YELLOW}🏭 Starting production environment...${NC}"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up $detach_flag $build_flag
}

# Function to start enhanced database environment
start_db() {
    local build_flag=""
    local detach_flag="-d"
    
    if [[ "$*" == *"-b"* ]] || [[ "$*" == *"--build"* ]]; then
        build_flag="--build"
    fi
    
    if [[ "$*" == *"-f"* ]] || [[ "$*" == *"--foreground"* ]]; then
        detach_flag=""
    fi
    
    echo -e "${YELLOW}🗄️ Starting enhanced database environment...${NC}"
    docker-compose -f docker-compose.enhanced-postgres.yml up $detach_flag $build_flag
}

# Function to stop all services
stop_services() {
    echo -e "${YELLOW}🛑 Stopping all services...${NC}"
    
    # Stop all possible configurations
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.optimized.yml down 2>/dev/null || true
    docker-compose -f docker-compose.test.yml down 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    docker-compose -f docker-compose.enhanced-postgres.yml down 2>/dev/null || true
    
    echo -e "${GREEN}✅ All services stopped${NC}"
}

# Function to show service status
show_status() {
    echo -e "${BLUE}📊 Service Status${NC}"
    echo "=================="
    
    # Check which configurations are running
    if docker-compose ps 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}Standard Development:${NC}"
        docker-compose ps
    fi
    
    if docker-compose -f docker-compose.optimized.yml ps 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}Optimized Development:${NC}"
        docker-compose -f docker-compose.optimized.yml ps
    fi
    
    if docker-compose -f docker-compose.test.yml ps 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}Test Environment:${NC}"
        docker-compose -f docker-compose.test.yml ps
    fi
    
    if docker-compose -f docker-compose.prod.yml ps 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}Production Environment:${NC}"
        docker-compose -f docker-compose.prod.yml ps
    fi
    
    if docker-compose -f docker-compose.enhanced-postgres.yml ps 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}Enhanced Database:${NC}"
        docker-compose -f docker-compose.enhanced-postgres.yml ps
    fi
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}📋 Service Logs${NC}"
    echo "==============="
    
    # Show logs for running configurations
    if docker-compose ps 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}Standard Development Logs:${NC}"
        docker-compose logs --tail=50
    fi
    
    if docker-compose -f docker-compose.optimized.yml ps 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}Optimized Development Logs:${NC}"
        docker-compose -f docker-compose.optimized.yml logs --tail=50
    fi
}

# Function to clean up
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up unused containers and images...${NC}"
    
    # Stop all services first
    stop_services
    
    # Remove unused containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful!)
    echo -e "${YELLOW}⚠️  Remove unused volumes? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
    
    # Remove unused networks
    docker network prune -f
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Function to list configurations
list_configs() {
    echo -e "${BLUE}📁 Available Docker Compose Configurations${NC}"
    echo "============================================="
    echo ""
    echo -e "${GREEN}Core Files:${NC}"
    echo "  docker-compose.yml              - Main development stack"
    echo "  docker-compose.optimized.yml    - Performance optimized builds"
    echo ""
    echo -e "${GREEN}Environment-Specific:${NC}"
    echo "  docker-compose.prod.yml         - Production with monitoring"
    echo "  docker-compose.test.yml         - Testing environment"
    echo "  docker-compose.enhanced-postgres.yml - Enhanced database"
    echo ""
    echo -e "${GREEN}Override Files:${NC}"
    echo "  docker-compose.override.yml     - GPU settings (auto-loaded)"
    echo ""
    echo -e "${GREEN}Usage Examples:${NC}"
    echo "  $0 dev                         - Start optimized development"
    echo "  $0 test                        - Start test environment"
    echo "  $0 prod                        - Start production"
    echo "  $0 db                          - Start enhanced database"
}

# Main script logic
case "${1:-}" in
    "dev")
        start_dev "$@"
        ;;
    "dev-std")
        start_dev_std "$@"
        ;;
    "test")
        start_test "$@"
        ;;
    "prod")
        start_prod "$@"
        ;;
    "db")
        start_db "$@"
        ;;
    "stop")
        stop_services
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "clean")
        cleanup
        ;;
    "list")
        list_configs
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    "")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
