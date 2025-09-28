#!/bin/bash

# Docker Build Optimization Script
# This script optimizes Docker builds for the Multimodal LLM Stack

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Docker Build Optimization Script${NC}"
echo "=================================="

# Enable BuildKit for advanced caching
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Function to build base image
build_base_image() {
    echo -e "${YELLOW}📦 Building shared base image...${NC}"
    
    # Build the shared base image
    docker build -t multimodal-base:latest \
        --cache-from multimodal-base:latest \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        -f docker/base/Dockerfile \
        docker/base/
    
    echo -e "${GREEN}✅ Base image built successfully${NC}"
}

# Function to build service with optimization
build_service() {
    local service_name=$1
    local service_path=$2
    local dockerfile=$3
    
    echo -e "${YELLOW}🔨 Building $service_name...${NC}"
    
    # Build with cache optimization
    docker build -t $service_name:latest \
        --cache-from multimodal-base:latest \
        --cache-from $service_name:latest \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        -f $dockerfile \
        $service_path
    
    echo -e "${GREEN}✅ $service_name built successfully${NC}"
}

# Function to clean up old images
cleanup_images() {
    echo -e "${YELLOW}🧹 Cleaning up old images...${NC}"
    
    # Remove dangling images
    docker image prune -f
    
    # Remove unused images (keep last 3 versions)
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}" | \
        grep -E "(multimodal-|retrieval-)" | \
        tail -n +4 | \
        awk '{print $2}' | \
        xargs -r docker rmi || true
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Function to show build statistics
show_stats() {
    echo -e "${BLUE}📊 Build Statistics${NC}"
    echo "=================="
    
    echo -e "${YELLOW}Docker System Usage:${NC}"
    docker system df
    
    echo -e "\n${YELLOW}Image Sizes:${NC}"
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | \
        grep -E "(multimodal-|retrieval-|base)"
}

# Main execution
main() {
    echo -e "${BLUE}Starting Docker build optimization...${NC}"
    
    # Build shared base image first
    build_base_image
    
    # Build all services with optimization
    build_service "multimodal-worker" "./services/multimodal-worker" "./services/multimodal-worker/Dockerfile.optimized"
    build_service "retrieval-proxy" "./services/retrieval-proxy" "./services/retrieval-proxy/Dockerfile.optimized"
    build_service "search-engine" "./services/search-engine" "./services/search-engine/Dockerfile.optimized"
    build_service "memory-system" "./services/memory-system" "./services/memory-system/Dockerfile.optimized"
    build_service "user-management" "./services/user-management" "./services/user-management/Dockerfile.optimized"
    build_service "ai-agents" "./services/ai-agents" "./services/ai-agents/Dockerfile.optimized"
    
    # Clean up old images
    cleanup_images
    
    # Show statistics
    show_stats
    
    echo -e "${GREEN}🎉 Docker build optimization completed!${NC}"
    echo -e "${BLUE}💡 Use 'docker-compose -f docker-compose.optimized.yml up -d' to run with optimized builds${NC}"
}

# Check if running with specific arguments
case "${1:-}" in
    "base")
        build_base_image
        ;;
    "cleanup")
        cleanup_images
        ;;
    "stats")
        show_stats
        ;;
    *)
        main
        ;;
esac
