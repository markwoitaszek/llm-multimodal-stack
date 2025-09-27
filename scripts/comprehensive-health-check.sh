#!/bin/bash

# Comprehensive Health Check for Multimodal LLM Stack
echo "🏥 COMPREHENSIVE HEALTH CHECK"
echo "============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
total_checks=0
passed_checks=0

# Function to run a health check
check_health() {
    local service_name=$1
    local check_command=$2
    local description=$3
    
    echo -n "🔍 $service_name ($description): "
    ((total_checks++))
    
    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ HEALTHY${NC}"
        ((passed_checks++))
        return 0
    else
        echo -e "${RED}❌ UNHEALTHY${NC}"
        return 1
    fi
}

echo "📋 DOCKER CONTAINER STATUS:"
echo "----------------------------"
docker-compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🌐 SERVICE FUNCTIONALITY TESTS:"
echo "-------------------------------"

# Test each service functionality
check_health "PostgreSQL" "docker-compose exec -T postgres pg_isready -U postgres" "Database connectivity"

check_health "Qdrant" "curl -s -f http://localhost:6333/ | grep -q 'qdrant'" "Vector database API"

check_health "MinIO" "curl -s -I http://localhost:9000/minio/health/live | grep -q '200 OK'" "Object storage health"

check_health "vLLM" "curl -s http://localhost:8000/v1/models | grep -q 'microsoft/DialoGPT-medium'" "LLM model serving"

check_health "OpenWebUI" "curl -s http://localhost:3030/ | grep -q 'doctype html'" "Web interface"

echo ""
echo "🎮 GPU UTILIZATION:"
echo "-------------------"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits | while read line; do
        echo "🎮 GPU $line"
    done
else
    echo "❌ NVIDIA SMI not available"
fi

echo ""
echo "🐳 DOCKER HEALTH STATUS:"
echo "------------------------"
for container in $(docker-compose ps --services); do
    if docker-compose ps | grep -q "$container.*Up"; then
        health_status=$(docker inspect "multimodal-$container" --format='{{.State.Health.Status}}' 2>/dev/null || echo "no-healthcheck")
        case $health_status in
            "healthy")
                echo -e "🟢 $container: ${GREEN}HEALTHY${NC}"
                ;;
            "unhealthy")
                echo -e "🔴 $container: ${RED}UNHEALTHY${NC}"
                ;;
            "starting")
                echo -e "🟡 $container: ${YELLOW}STARTING${NC}"
                ;;
            "no-healthcheck")
                echo -e "⚪ $container: ${BLUE}NO HEALTH CHECK${NC}"
                ;;
            *)
                echo -e "⚫ $container: UNKNOWN ($health_status)"
                ;;
        esac
    else
        echo -e "🔴 $container: ${RED}NOT RUNNING${NC}"
    fi
done

echo ""
echo "🔗 NETWORK STATUS:"
echo "------------------"
echo "📋 Docker Networks:"
docker network ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" | grep -v "bridge\|host\|none"

echo ""
echo "📊 SUMMARY:"
echo "-----------"
echo "Functional Tests: $passed_checks/$total_checks passed"

# Calculate percentage
if [ $total_checks -gt 0 ]; then
    percentage=$(( (passed_checks * 100) / total_checks ))
    if [ $percentage -eq 100 ]; then
        echo -e "Overall Status: ${GREEN}✅ ALL SYSTEMS OPERATIONAL ($percentage%)${NC}"
        exit 0
    elif [ $percentage -ge 80 ]; then
        echo -e "Overall Status: ${YELLOW}⚠️  MOSTLY OPERATIONAL ($percentage%)${NC}"
        exit 1
    else
        echo -e "Overall Status: ${RED}❌ SYSTEM ISSUES ($percentage%)${NC}"
        exit 2
    fi
else
    echo -e "Overall Status: ${RED}❌ NO TESTS RUN${NC}"
    exit 3
fi
