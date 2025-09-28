#!/bin/bash

# Health Check Script for Multimodal LLM Stack
echo "🏥 Checking health of all services..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service health
check_service() {
    local service_name=$1
    local health_url=$2
    local expected_status=${3:-200}
    local auth_header=${4:-""}
    
    echo -n "Checking $service_name... "
    
    if [ -n "$auth_header" ]; then
        if curl -s -f -H "$auth_header" "$health_url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Healthy${NC}"
            return 0
        else
            echo -e "${RED}❌ Unhealthy${NC}"
            return 1
        fi
    else
        if curl -s -f "$health_url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Healthy${NC}"
            return 0
        else
            echo -e "${RED}❌ Unhealthy${NC}"
            return 1
        fi
    fi
}

# Function to check Docker service status
check_docker_service() {
    local service_name=$1
    
    echo -n "Checking Docker service $service_name... "
    
    if docker-compose ps | grep -q "$service_name.*Up"; then
        echo -e "${GREEN}✅ Running${NC}"
        return 0
    else
        echo -e "${RED}❌ Not running${NC}"
        return 1
    fi
}

echo "📋 Docker Services Status:"
echo "=========================="

# Check Docker services
services=("qdrant" "postgres" "redis" "minio" "vllm" "litellm" "multimodal-worker" "retrieval-proxy" "openwebui")
docker_healthy=0

for service in "${services[@]}"; do
    if check_docker_service "$service"; then
        ((docker_healthy++))
    fi
done

echo ""
echo "🌐 HTTP Health Checks:"
echo "======================"

# Check HTTP endpoints
http_healthy=0
total_http_checks=0

# Qdrant
((total_http_checks++))
if check_service "Qdrant" "http://localhost:6333/"; then
    ((http_healthy++))
fi

# PostgreSQL (indirect check via pg_isready)
echo -n "Checking PostgreSQL... "
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Healthy${NC}"
    ((http_healthy++))
else
    echo -e "${RED}❌ Unhealthy${NC}"
fi
((total_http_checks++))

# Redis
echo -n "Checking Redis... "
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Healthy${NC}"
    ((http_healthy++))
else
    echo -e "${RED}❌ Unhealthy${NC}"
fi
((total_http_checks++))

# MinIO
((total_http_checks++))
if check_service "MinIO" "http://localhost:9000/minio/health/live"; then
    ((http_healthy++))
fi

# vLLM
((total_http_checks++))
if check_service "vLLM" "http://localhost:8000/health"; then
    ((http_healthy++))
fi

# LiteLLM
((total_http_checks++))
if check_service "LiteLLM" "http://localhost:4000/health" 200 "Authorization: Bearer sk-zfiSGe7bXx85c0hlkcjp+4SGtAYqXR/y8jBY9DWusm0="; then
    ((http_healthy++))
fi

# Multimodal Worker
((total_http_checks++))
if check_service "Multimodal Worker" "http://localhost:8001/health"; then
    ((http_healthy++))
fi

# Retrieval Proxy
((total_http_checks++))
if check_service "Retrieval Proxy" "http://localhost:8002/health"; then
    ((http_healthy++))
fi

# OpenWebUI
((total_http_checks++))
if check_service "OpenWebUI" "http://localhost:3000/health"; then
    ((http_healthy++))
fi

echo ""
echo "📊 Summary:"
echo "==========="
echo "Docker Services: $docker_healthy/${#services[@]} running"
echo "HTTP Endpoints: $http_healthy/$total_http_checks healthy"

# Overall status
total_services=$((${#services[@]} + total_http_checks))
total_healthy=$((docker_healthy + http_healthy))

if [ $total_healthy -eq $total_services ]; then
    echo -e "Overall Status: ${GREEN}✅ All systems healthy${NC}"
    exit 0
elif [ $total_healthy -gt $((total_services / 2)) ]; then
    echo -e "Overall Status: ${YELLOW}⚠️  Partially healthy ($total_healthy/$total_services)${NC}"
    exit 1
else
    echo -e "Overall Status: ${RED}❌ System unhealthy ($total_healthy/$total_services)${NC}"
    exit 2
fi

