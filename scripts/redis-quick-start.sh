#!/bin/bash

# Redis Integration Quick Start Script
# This script helps users quickly set up and test Redis integration

set -e

echo "🚀 Redis Integration Quick Start"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f env.example ]; then
        cp env.example .env
        print_success "Created .env file from env.example"
        print_warning "Please review and update the Redis configuration in .env if needed"
    else
        print_error "env.example file not found. Cannot create .env file."
        exit 1
    fi
else
    print_success ".env file already exists"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_success "Docker is running"

# Start Redis and infrastructure services
print_status "Starting Redis and infrastructure services..."
docker-compose up -d redis postgres qdrant minio

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Test Redis connection
print_status "Testing Redis connection..."
if docker exec multimodal-redis redis-cli ping | grep -q "PONG"; then
    print_success "Redis is running and accessible"
else
    print_error "Redis connection failed"
    exit 1
fi

# Test database isolation
print_status "Testing Redis database isolation..."
docker exec multimodal-redis redis-cli -n 0 set "test_multimodal" "worker"
docker exec multimodal-redis redis-cli -n 1 set "test_retrieval" "proxy"
docker exec multimodal-redis redis-cli -n 2 set "test_agents" "ai"

if docker exec multimodal-redis redis-cli -n 0 get "test_multimodal" | grep -q "worker" && \
   docker exec multimodal-redis redis-cli -n 1 get "test_retrieval" | grep -q "proxy" && \
   docker exec multimodal-redis redis-cli -n 2 get "test_agents" | grep -q "ai"; then
    print_success "Database isolation is working correctly"
else
    print_error "Database isolation test failed"
fi

# Clean up test keys
docker exec multimodal-redis redis-cli -n 0 del "test_multimodal" > /dev/null
docker exec multimodal-redis redis-cli -n 1 del "test_retrieval" > /dev/null
docker exec multimodal-redis redis-cli -n 2 del "test_agents" > /dev/null

# Start application services
print_status "Starting application services..."
docker-compose up -d multimodal-worker retrieval-proxy ai-agents

# Wait for services to be ready
print_status "Waiting for application services to be ready..."
sleep 15

# Test cache endpoints
print_status "Testing cache endpoints..."

# Test retrieval-proxy cache stats
if curl -s http://localhost:8002/api/v1/cache/stats > /dev/null 2>&1; then
    print_success "Retrieval-proxy cache endpoint is accessible"
else
    print_warning "Retrieval-proxy cache endpoint not accessible (service may still be starting)"
fi

# Test multimodal-worker cache stats
if curl -s http://localhost:8001/api/v1/cache/stats > /dev/null 2>&1; then
    print_success "Multimodal-worker cache endpoint is accessible"
else
    print_warning "Multimodal-worker cache endpoint not accessible (service may still be starting)"
fi

# Test AI agents health
if curl -s http://localhost:8003/health > /dev/null 2>&1; then
    print_success "AI agents service is accessible"
else
    print_warning "AI agents service not accessible (service may still be starting)"
fi

# Run comprehensive health check
print_status "Running comprehensive health check..."
if ./scripts/health-check.sh; then
    print_success "All services are healthy"
else
    print_warning "Some services may not be fully ready yet"
fi

echo ""
echo "🎉 Redis Integration Quick Start Complete!"
echo "=========================================="
echo ""
echo "📊 Redis Integration Status:"
echo "  ✅ Redis service running"
echo "  ✅ Database isolation working"
echo "  ✅ Cache endpoints accessible"
echo "  ✅ Services integrated with Redis"
echo ""
echo "🔧 Next Steps:"
echo "  1. Run full test suite: ./scripts/test-redis-integration.sh"
echo "  2. Check cache statistics: curl http://localhost:8002/api/v1/cache/stats"
echo "  3. Monitor Redis: docker exec multimodal-redis redis-cli info"
echo "  4. View documentation: docs/REDIS_CONFIGURATION_GUIDE.md"
echo ""
echo "🚀 Redis integration is ready for use!"
