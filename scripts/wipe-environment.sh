#!/bin/bash
# Comprehensive Environment Wipe Script
# Complements PR 130's unified schema system

set -e

echo "🧹 Comprehensive Environment Wipe"
echo "================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ SUCCESS${NC}: $message"
            ;;
        "ERROR")
            echo -e "${RED}❌ ERROR${NC}: $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  WARNING${NC}: $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  INFO${NC}: $message"
            ;;
    esac
}

print_status "INFO" "Stopping all compose services..."
docker compose down --remove-orphans 2>/dev/null || true

print_status "INFO" "Removing all multimodal volumes (including PostgreSQL data)..."
docker volume ls -q | grep llm-multimodal-stack | xargs -r docker volume rm 2>/dev/null || true

# Additional cleanup for any remaining PostgreSQL data
print_status "INFO" "Ensuring complete PostgreSQL data cleanup..."
docker volume ls -q | grep -E "(postgres|multimodal)" | xargs -r docker volume rm 2>/dev/null || true

print_status "INFO" "Removing all multimodal networks..."
docker network ls -q | grep llm-multimodal-stack | xargs -r docker network rm 2>/dev/null || true

print_status "INFO" "Cleaning up orphaned containers..."
docker container prune -f 2>/dev/null || true

print_status "SUCCESS" "Environment wiped completely"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo "  make setup      # Regenerate environment from scratch"
echo "  make start-dev  # Start development environment"
