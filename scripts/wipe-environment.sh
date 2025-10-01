#!/bin/bash

# Granular Wipe/Reset Operations Script
# Provides fine-grained control over different parts of the infrastructure

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SCHEMA_FILE="$PROJECT_ROOT/schemas/compose-schema.yaml"

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

# Function to confirm destructive operations
confirm_operation() {
    local operation=$1
    local description=$2
    
    print_status "$YELLOW" "⚠️  WARNING: This operation will $description"
    print_status "$YELLOW" "Operation: $operation"
    echo ""
    
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo
    
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        return 0
    else
        print_status "$YELLOW" "Operation cancelled by user"
        return 1
    fi
}

# Function to wipe entire stacks
wipe_stack() {
    local stack_name=$1
    local compose_file="compose.$stack_name.yml"
    
    print_section "Wiping $stack_name Stack"
    
    if [ ! -f "$PROJECT_ROOT/$compose_file" ]; then
        print_status "$RED" "❌ Compose file not found: $compose_file"
        return 1
    fi
    
    print_status "$YELLOW" "🛑 Stopping $stack_name stack..."
    docker compose -f "$PROJECT_ROOT/$compose_file" down --volumes --remove-orphans 2>/dev/null || true
    
    print_status "$YELLOW" "🧹 Removing $stack_name containers..."
    docker compose -f "$PROJECT_ROOT/$compose_file" rm -f 2>/dev/null || true
    
    print_status "$YELLOW" "🗑️  Removing $stack_name volumes..."
    docker compose -f "$PROJECT_ROOT/$compose_file" down -v 2>/dev/null || true
    
    print_status "$YELLOW" "🌐 Removing $stack_name networks..."
    docker compose -f "$PROJECT_ROOT/$compose_file" down --remove-orphans 2>/dev/null || true
    
    print_status "$GREEN" "✅ $stack_name stack wiped successfully"
}

# Function to restart stacks (no data loss)
restart_stack() {
    local stack_name=$1
    local compose_file="compose.$stack_name.yml"
    
    print_section "Restarting $stack_name Stack"
    
    if [ ! -f "$PROJECT_ROOT/$compose_file" ]; then
        print_status "$RED" "❌ Compose file not found: $compose_file"
        return 1
    fi
    
    print_status "$YELLOW" "🔄 Restarting $stack_name stack..."
    docker compose -f "$PROJECT_ROOT/$compose_file" restart
    
    print_status "$GREEN" "✅ $stack_name stack restarted successfully"
}

# Function to rebuild stacks (force image rebuild)
rebuild_stack() {
    local stack_name=$1
    local compose_file="compose.$stack_name.yml"
    
    print_section "Rebuilding $stack_name Stack"
    
    if [ ! -f "$PROJECT_ROOT/$compose_file" ]; then
        print_status "$RED" "❌ Compose file not found: $compose_file"
        return 1
    fi
    
    print_status "$YELLOW" "🛑 Stopping $stack_name stack..."
    docker compose -f "$PROJECT_ROOT/$compose_file" down
    
    print_status "$YELLOW" "🔨 Rebuilding $stack_name images..."
    docker compose -f "$PROJECT_ROOT/$compose_file" build --no-cache
    
    print_status "$YELLOW" "🚀 Starting $stack_name stack..."
    docker compose -f "$PROJECT_ROOT/$compose_file" up -d
    
    print_status "$GREEN" "✅ $stack_name stack rebuilt successfully"
}

# Function to wipe specific data types
wipe_data_type() {
    local data_type=$1
    
    print_section "Wiping $data_type Data"
    
    case $data_type in
        "db"|"database")
            print_status "$YELLOW" "🗑️  Wiping database volumes..."
            docker volume rm $(docker volume ls -q | grep -E "(postgres|multimodal.*postgres)" || true) 2>/dev/null || true
            print_status "$GREEN" "✅ Database volumes wiped"
            ;;
        "cache")
            print_status "$YELLOW" "🗑️  Wiping cache volumes..."
            docker volume rm $(docker volume ls -q | grep -E "(redis|vllm_cache|multimodal_cache)" || true) 2>/dev/null || true
            print_status "$GREEN" "✅ Cache volumes wiped"
            ;;
        "models")
            print_status "$YELLOW" "🗑️  Wiping model cache..."
            docker volume rm $(docker volume ls -q | grep -E "(vllm_cache|models)" || true) 2>/dev/null || true
            print_status "$GREEN" "✅ Model cache wiped"
            ;;
        "logs")
            print_status "$YELLOW" "🗑️  Wiping log volumes..."
            docker volume rm $(docker volume ls -q | grep -E "(logs|elasticsearch)" || true) 2>/dev/null || true
            print_status "$GREEN" "✅ Log volumes wiped"
            ;;
        "test-results")
            print_status "$YELLOW" "🗑️  Wiping test results..."
            docker volume rm $(docker volume ls -q | grep -E "(allure|test)" || true) 2>/dev/null || true
            print_status "$GREEN" "✅ Test results wiped"
            ;;
        *)
            print_status "$RED" "❌ Unknown data type: $data_type"
            print_status "$YELLOW" "Available data types: db, cache, models, logs, test-results"
            return 1
            ;;
    esac
}

# Function to wipe environment-specific data
wipe_environment() {
    local environment=$1
    
    print_section "Wiping $environment Environment"
    
    case $environment in
        "dev"|"development")
            print_status "$YELLOW" "🗑️  Wiping development environment..."
            docker compose -f "$PROJECT_ROOT/compose.development.yml" down --volumes --remove-orphans 2>/dev/null || true
            ;;
        "staging")
            print_status "$YELLOW" "🗑️  Wiping staging environment..."
            docker compose -f "$PROJECT_ROOT/compose.staging.yml" down --volumes --remove-orphans 2>/dev/null || true
            ;;
        "prod"|"production")
            print_status "$YELLOW" "🗑️  Wiping production environment..."
            docker compose -f "$PROJECT_ROOT/compose.production.yml" down --volumes --remove-orphans 2>/dev/null || true
            ;;
        "testing")
            print_status "$YELLOW" "🗑️  Wiping testing environment..."
            docker compose -f "$PROJECT_ROOT/compose.testing.yml" down --volumes --remove-orphans 2>/dev/null || true
            ;;
        *)
            print_status "$RED" "❌ Unknown environment: $environment"
            print_status "$YELLOW" "Available environments: dev, staging, prod, testing"
            return 1
            ;;
    esac
    
    print_status "$GREEN" "✅ $environment environment wiped successfully"
}

# Function to show current status
show_status() {
    print_section "Current System Status"
    
    print_status "$BLUE" "📊 Running Containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -20
    
    echo ""
    print_status "$BLUE" "📊 Docker Volumes:"
    docker volume ls --format "table {{.Name}}\t{{.Driver}}\t{{.Size}}"
    
    echo ""
    print_status "$BLUE" "📊 Docker Networks:"
    docker network ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"
}

# Function to show help
show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Stack Operations:"
    echo "  wipe-stack <stack>           Wipe entire stack (containers + data)"
    echo "  restart-stack <stack>        Restart stack (no data loss)"
    echo "  rebuild-stack <stack>        Rebuild stack (force image rebuild)"
    echo ""
    echo "Data Operations:"
    echo "  wipe-db                      Wipe database volumes only"
    echo "  wipe-cache                   Wipe cache volumes only"
    echo "  wipe-models                  Wipe model cache only"
    echo "  wipe-logs                    Wipe log volumes only"
    echo "  wipe-test-results            Wipe test results only"
    echo ""
    echo "Environment Operations:"
    echo "  wipe-dev                     Wipe development environment"
    echo "  wipe-staging                 Wipe staging environment"
    echo "  wipe-prod                    Wipe production environment"
    echo "  wipe-testing                 Wipe testing environment"
    echo ""
    echo "Utility Operations:"
    echo "  status                       Show current system status"
    echo "  help                         Show this help message"
    echo ""
    echo "Available Stacks:"
    echo "  core, inference, ai, ui, testing, monitoring"
    echo ""
    echo "Examples:"
    echo "  $0 wipe-stack core           # Wipe core infrastructure"
    echo "  $0 restart-stack ai          # Restart AI services"
    echo "  $0 rebuild-stack inference   # Rebuild inference stack"
    echo "  $0 wipe-db                   # Wipe database only"
    echo "  $0 wipe-staging              # Wipe staging environment"
}

# Main function
main() {
    local command=${1:-help}
    local target=${2:-}
    
    case $command in
        "wipe-stack")
            if [ -z "$target" ]; then
                print_status "$RED" "❌ Stack name required"
                show_help
                exit 1
            fi
            
            if confirm_operation "wipe-stack $target" "completely remove the $target stack and all its data"; then
                wipe_stack "$target"
            fi
            ;;
        "restart-stack")
            if [ -z "$target" ]; then
                print_status "$RED" "❌ Stack name required"
                show_help
                exit 1
            fi
            
            restart_stack "$target"
            ;;
        "rebuild-stack")
            if [ -z "$target" ]; then
                print_status "$RED" "❌ Stack name required"
                show_help
                exit 1
            fi
            
            if confirm_operation "rebuild-stack $target" "rebuild the $target stack (this will take time)"; then
                rebuild_stack "$target"
            fi
            ;;
        "wipe-db"|"wipe-database")
            if confirm_operation "wipe-db" "remove all database data"; then
                wipe_data_type "db"
            fi
            ;;
        "wipe-cache")
            if confirm_operation "wipe-cache" "remove all cache data"; then
                wipe_data_type "cache"
            fi
            ;;
        "wipe-models")
            if confirm_operation "wipe-models" "remove all model cache"; then
                wipe_data_type "models"
            fi
            ;;
        "wipe-logs")
            if confirm_operation "wipe-logs" "remove all log data"; then
                wipe_data_type "logs"
            fi
            ;;
        "wipe-test-results")
            if confirm_operation "wipe-test-results" "remove all test results"; then
                wipe_data_type "test-results"
            fi
            ;;
        "wipe-dev"|"wipe-development")
            if confirm_operation "wipe-dev" "remove the development environment"; then
                wipe_environment "dev"
            fi
            ;;
        "wipe-staging")
            if confirm_operation "wipe-staging" "remove the staging environment"; then
                wipe_environment "staging"
            fi
            ;;
        "wipe-prod"|"wipe-production")
            if confirm_operation "wipe-prod" "remove the production environment"; then
                wipe_environment "prod"
            fi
            ;;
        "wipe-testing")
            if confirm_operation "wipe-testing" "remove the testing environment"; then
                wipe_environment "testing"
            fi
            ;;
        "status")
            show_status
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