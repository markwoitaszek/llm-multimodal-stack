#!/bin/bash

# Fixed Environment Wipe Script with Preview
# Provides clear preview of what will be deleted before confirmation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print section headers
print_section() {
    echo ""
    print_status "$BLUE" "=== $1 ==="
    echo ""
}

# Function to show what will be wiped
show_wipe_preview() {
    print_section "Environment Wipe Preview"
    
    print_status "$CYAN" "📊 Current System Status:"
    echo ""
    
    # Show running containers
    print_status "$YELLOW" "🖥️  Running Multimodal Containers:"
    local containers=$(docker ps --format "{{.Names}}" | grep -E "(multimodal|postgres|redis|qdrant|minio|vllm|litellm)" || true)
    if [ -n "$containers" ]; then
        echo "$containers" | sed 's/^/   • /'
    else
        echo "   (none running)"
    fi
    echo ""
    
    # Show volumes
    print_status "$YELLOW" "💾 Multimodal Volumes:"
    local volumes=$(docker volume ls --format "{{.Name}}" | grep -E "(multimodal|postgres|redis|qdrant|minio|vllm)" || true)
    if [ -n "$volumes" ]; then
        echo "$volumes" | sed 's/^/   • /'
        echo ""
        print_status "$CYAN" "   Volume sizes:"
        for vol in $volumes; do
            local size=$(docker system df -v 2>/dev/null | grep "$vol" | awk '{print $3}' || echo "unknown")
            echo "   • $vol: $size"
        done
    else
        echo "   (none found)"
    fi
    echo ""
    
    # Show networks
    print_status "$YELLOW" "🌐 Multimodal Networks:"
    local networks=$(docker network ls --format "{{.Name}}" | grep -E "(multimodal|bridge)" || true)
    if [ -n "$networks" ]; then
        echo "$networks" | sed 's/^/   • /'
    else
        echo "   (none found)"
    fi
    echo ""
    
    # Show compose files
    print_status "$YELLOW" "📄 Compose Files:"
    local compose_files=$(find "$PROJECT_ROOT" -name "compose*.yml" -type f 2>/dev/null || true)
    if [ -n "$compose_files" ]; then
        echo "$compose_files" | sed "s|$PROJECT_ROOT/||" | sed 's/^/   • /'
    else
        echo "   (none found)"
    fi
    echo ""
    
    # Show environment files
    print_status "$YELLOW" "🔐 Environment Files:"
    local env_files=$(find "$PROJECT_ROOT" -name ".env*" -type f 2>/dev/null || true)
    if [ -n "$env_files" ]; then
        echo "$env_files" | sed "s|$PROJECT_ROOT/||" | sed 's/^/   • /'
    else
        echo "   (none found)"
    fi
    echo ""
    
    print_status "$RED" "⚠️  WARNING: The following will be DELETED:"
    echo "   • All running multimodal containers"
    echo "   • All multimodal volumes (including database data)"
    echo "   • All multimodal networks"
    echo "   • All orphaned containers and volumes"
    echo "   • Generated compose files"
    echo ""
}

# Function to confirm destructive operations
confirm_wipe() {
    print_status "$RED" "⚠️  DESTRUCTIVE OPERATION CONFIRMATION"
    print_status "$RED" "======================================"
    echo ""
    print_status "$YELLOW" "This operation will PERMANENTLY DELETE:"
    echo "   • All multimodal containers and their data"
    echo "   • All database volumes (PostgreSQL data will be lost)"
    echo "   • All object storage volumes (MinIO data will be lost)"
    echo "   • All cache volumes (Redis data will be lost)"
    echo "   • All multimodal networks"
    echo ""
    print_status "$YELLOW" "This action CANNOT be undone!"
    echo ""
    read -p "Type 'DELETE' to confirm wipe operation: " -r
    echo ""
    
    if [[ $REPLY = "DELETE" ]]; then
        return 0
    else
        print_status "$YELLOW" "❌ Wipe operation cancelled by user"
        return 1
    fi
}

# Function to perform the actual wipe
perform_wipe() {
    print_section "Performing Environment Wipe"
    
    # Stop all compose services
    print_status "$YELLOW" "🛑 Stopping all compose services..."
    cd "$PROJECT_ROOT"
    
    # Try to stop services from all possible compose files
    for compose_file in compose*.yml; do
        if [ -f "$compose_file" ]; then
            print_status "$CYAN" "   Stopping services from $compose_file..."
            docker compose -f "$compose_file" down --volumes --remove-orphans 2>/dev/null || true
        fi
    done
    
    # Stop any remaining multimodal containers
    print_status "$YELLOW" "🛑 Stopping remaining multimodal containers..."
    local running_containers=$(docker ps --format "{{.Names}}" | grep -E "(multimodal|postgres|redis|qdrant|minio|vllm|litellm)" || true)
    if [ -n "$running_containers" ]; then
        echo "$running_containers" | xargs -r docker stop
        echo "$running_containers" | xargs -r docker rm
    fi
    
    # Remove multimodal volumes
    print_status "$YELLOW" "🗑️  Removing multimodal volumes..."
    local volumes=$(docker volume ls --format "{{.Name}}" | grep -E "(multimodal|postgres|redis|qdrant|minio|vllm)" || true)
    if [ -n "$volumes" ]; then
        echo "$volumes" | xargs -r docker volume rm
    fi
    
    # Remove multimodal networks
    print_status "$YELLOW" "🌐 Removing multimodal networks..."
    local networks=$(docker network ls --format "{{.Name}}" | grep -E "(multimodal)" || true)
    if [ -n "$networks" ]; then
        echo "$networks" | xargs -r docker network rm
    fi
    
    # Clean up orphaned containers and volumes
    print_status "$YELLOW" "🧹 Cleaning up orphaned resources..."
    docker container prune -f 2>/dev/null || true
    docker volume prune -f 2>/dev/null || true
    docker network prune -f 2>/dev/null || true
    
    # Remove generated compose files (optional)
    print_status "$YELLOW" "📄 Removing generated compose files..."
    rm -f "$PROJECT_ROOT"/compose*.yml 2>/dev/null || true
    
    print_status "$GREEN" "✅ Environment wipe completed successfully!"
    echo ""
    print_status "$CYAN" "💡 Next steps:"
    echo "   make setup     # Set up fresh environment"
    echo "   make reset     # Nuclear reset (wipe + setup)"
    echo ""
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  preview, -p     Show what will be wiped (default)"
    echo "  wipe, -w        Perform wipe with confirmation"
    echo "  force, -f       Force wipe without confirmation (DANGEROUS)"
    echo "  help, -h        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Show preview of what will be wiped"
    echo "  $0 preview      # Same as above"
    echo "  $0 wipe         # Perform wipe with confirmation"
    echo "  $0 force        # Force wipe without confirmation (DANGEROUS)"
    echo ""
    echo "⚠️  WARNING: This script will permanently delete all multimodal data!"
}

# Main function
main() {
    local command=${1:-preview}
    
    case $command in
        "preview"|"-p")
            show_wipe_preview
            ;;
        "wipe"|"-w")
            show_wipe_preview
            if confirm_wipe; then
                perform_wipe
            fi
            ;;
        "force"|"-f")
            print_status "$RED" "⚠️  FORCE WIPE MODE - NO CONFIRMATION!"
            perform_wipe
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_status "$RED" "❌ Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
