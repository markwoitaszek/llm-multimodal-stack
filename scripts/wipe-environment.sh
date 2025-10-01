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
PURPLE='\033[0;35m'
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
        "HEADER")
            echo -e "${PURPLE}📋 $message${NC}"
            ;;
    esac
}

# Function to scan and display what will be deleted
scan_for_deletion() {
    echo -e "${RED}🔍 SCANNING FOR DELETION TARGETS${NC}"
    echo "=================================="
    echo ""
    
    # Determine if we need sudo for docker commands
    local docker_cmd="docker"
    if ! docker ps >/dev/null 2>&1; then
        docker_cmd="sudo docker"
    fi
    
    # Scan containers
    print_status "HEADER" "CONTAINERS TO BE DELETED:"
    existing_containers=$($docker_cmd ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(multimodal|llm-multimodal)" 2>/dev/null || echo "   No multimodal containers found")
    if [ "$existing_containers" != "   No multimodal containers found" ]; then
        echo "$existing_containers"
    else
        echo "   No multimodal containers found"
    fi
    echo ""
    
    # Scan volumes
    print_status "HEADER" "VOLUMES TO BE DELETED:"
    existing_volumes=$($docker_cmd volume ls --format "table {{.Name}}\t{{.Driver}}\t{{.Size}}" | grep -E "(llm-multimodal-stack|postgres|multimodal)" 2>/dev/null || echo "   No multimodal volumes found")
    if [ "$existing_volumes" != "   No multimodal volumes found" ]; then
        echo "$existing_volumes"
    else
        echo "   No multimodal volumes found"
    fi
    echo ""
    
    # Scan networks
    print_status "HEADER" "NETWORKS TO BE DELETED:"
    existing_networks=$($docker_cmd network ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" | grep -E "(llm-multimodal-stack|multimodal)" 2>/dev/null || echo "   No multimodal networks found")
    if [ "$existing_networks" != "   No multimodal networks found" ]; then
        echo "$existing_networks"
    else
        echo "   No multimodal networks found"
    fi
    echo ""
    
    # Scan orphaned containers
    print_status "HEADER" "ORPHANED CONTAINERS TO BE CLEANED:"
    orphaned_containers=$($docker_cmd container ls -a --filter "status=exited" --format "table {{.Names}}\t{{.Status}}\t{{.CreatedAt}}" 2>/dev/null || echo "   No orphaned containers found")
    if [ "$orphaned_containers" != "   No orphaned containers found" ]; then
        echo "$orphaned_containers"
    else
        echo "   No orphaned containers found"
    fi
    echo ""
}

# Function to perform the actual wipe
perform_wipe() {
    echo -e "${RED}🧹 PERFORMING WIPE OPERATIONS${NC}"
    echo "==============================="
    echo ""
    
    # Determine if we need sudo for docker commands
    local docker_cmd="docker"
    if ! docker ps >/dev/null 2>&1; then
        docker_cmd="sudo docker"
        print_status "INFO" "Using sudo for Docker operations"
    fi
    
    print_status "INFO" "Stopping all compose services..."
    $docker_cmd compose down --remove-orphans 2>/dev/null || true
    
    print_status "INFO" "Removing all multimodal volumes (including PostgreSQL data)..."
    $docker_cmd volume ls -q | grep llm-multimodal-stack | xargs -r $docker_cmd volume rm 2>/dev/null || true
    
    # Additional cleanup for any remaining PostgreSQL data
    print_status "INFO" "Ensuring complete PostgreSQL data cleanup..."
    $docker_cmd volume ls -q | grep -E "(postgres|multimodal)" | xargs -r $docker_cmd volume rm 2>/dev/null || true
    
    print_status "INFO" "Removing all multimodal networks..."
    $docker_cmd network ls -q | grep llm-multimodal-stack | xargs -r $docker_cmd network rm 2>/dev/null || true
    
    print_status "INFO" "Cleaning up orphaned containers..."
    $docker_cmd container prune -f 2>/dev/null || true
    
    print_status "SUCCESS" "Environment wiped completely"
    echo ""
    echo -e "${BLUE}💡 Next steps:${NC}"
    echo "  make setup      # Regenerate environment from scratch"
    echo "  make start-dev  # Start development environment"
}

# Function to check sudo requirements
check_sudo_requirements() {
    echo -e "${BLUE}🔐 CHECKING PRIVILEGES${NC}"
    echo "======================"
    echo ""
    
    # Check if user is in docker group
    if groups $USER | grep -q docker; then
        print_status "SUCCESS" "User is in docker group - no sudo required"
        return 0
    fi
    
    # Check if docker command works without sudo
    if docker ps >/dev/null 2>&1; then
        print_status "SUCCESS" "Docker accessible without sudo"
        return 0
    fi
    
    # Check if sudo is available
    if ! command -v sudo >/dev/null 2>&1; then
        print_status "ERROR" "sudo command not found but required for Docker operations"
        echo -e "${RED}Please install sudo or add your user to the docker group${NC}"
        exit 1
    fi
    
    # Check if user can use sudo
    if ! sudo -n true >/dev/null 2>&1; then
        print_status "WARNING" "sudo privileges required for Docker operations"
        echo -e "${YELLOW}You may be prompted for your password during the wipe operation${NC}"
        echo ""
        return 1
    else
        print_status "SUCCESS" "sudo privileges confirmed"
        return 0
    fi
}

# Main execution
echo -e "${YELLOW}⚠️  WARNING: This will DELETE all data and containers!${NC}"
echo -e "${YELLOW}This includes PostgreSQL databases, MinIO data, and all volumes.${NC}"
echo ""

# Check sudo requirements
check_sudo_requirements
echo ""

# Scan and show what will be deleted
scan_for_deletion

# Confirmation prompt
echo -e "${RED}🚨 FINAL CONFIRMATION REQUIRED${NC}"
echo "=============================="
echo -e "${YELLOW}The above items will be PERMANENTLY DELETED.${NC}"
echo -e "${YELLOW}This action CANNOT be undone.${NC}"
echo ""
read -p "Type 'yes' to proceed with deletion: " confirm

if [ "$confirm" = "yes" ]; then
    echo ""
    perform_wipe
else
    echo ""
    print_status "INFO" "Operation cancelled by user"
    echo -e "${BLUE}💡 No changes were made to your environment${NC}"
    exit 0
fi
