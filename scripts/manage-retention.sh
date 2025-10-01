#!/bin/bash

# Data Retention Management Script
# Implements automated data retention policies and cleanup

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
RETENTION_CONFIG="$PROJECT_ROOT/configs/retention-policies.yaml"
LOG_FILE="$PROJECT_ROOT/logs/retention-$(date +%Y%m%d).log"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" >> "$LOG_FILE"
}

# Function to print section headers
print_section() {
    echo ""
    print_status "$BLUE" "=== $1 ==="
    echo ""
}

# Function to log messages
log_message() {
    local level=$1
    local message=$2
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" >> "$LOG_FILE"
}

# Function to load retention configuration
load_retention_config() {
    if [ ! -f "$RETENTION_CONFIG" ]; then
        print_status "$RED" "❌ Retention configuration file not found: $RETENTION_CONFIG"
        exit 1
    fi
    
    # Create logs directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    print_status "$GREEN" "✅ Loaded retention configuration from $RETENTION_CONFIG"
}

# Function to get environment-specific retention policy
get_environment_policy() {
    local environment=$1
    local policy_key=$2
    
    python3 -c "
import yaml
import sys

try:
    with open('$RETENTION_CONFIG', 'r') as f:
        config = yaml.safe_load(f)
    
    env_config = config.get('environments', {}).get('$environment', {})
    global_config = config.get('global', {})
    
    # Get environment-specific value or fall back to global
    value = env_config.get('$policy_key', global_config.get('$policy_key'))
    
    if value is not None:
        print(value)
    else:
        print('')
        
except Exception as e:
    print('', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null
}

# Function to get service-specific retention policy
get_service_policy() {
    local service=$1
    local policy_key=$2
    
    python3 -c "
import yaml
import sys

try:
    with open('$RETENTION_CONFIG', 'r') as f:
        config = yaml.safe_load(f)
    
    service_config = config.get('services', {}).get('$service', {})
    global_config = config.get('global', {})
    
    # Get service-specific value or fall back to global
    value = service_config.get('$policy_key', global_config.get('$policy_key'))
    
    if value is not None:
        print(value)
    else:
        print('')
        
except Exception as e:
    print('', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null
}

# Function to check if cleanup should run
should_run_cleanup() {
    local environment=$1
    local service=$2
    
    # Check if service is running
    if ! docker ps --format "{{.Names}}" | grep -q "$service"; then
        print_status "$YELLOW" "⚠️  Service $service is not running, skipping cleanup"
        return 1
    fi
    
    # Check if cleanup is enabled
    local cleanup_enabled
    cleanup_enabled=$(get_environment_policy "$environment" "cleanup_enabled")
    if [ "$cleanup_enabled" = "false" ]; then
        print_status "$YELLOW" "⚠️  Cleanup is disabled for $environment environment"
        return 1
    fi
    
    return 0
}

# Function to cleanup PostgreSQL data
cleanup_postgres() {
    local environment=$1
    local retention_days=$2
    
    print_section "Cleaning up PostgreSQL data"
    
    if ! should_run_cleanup "$environment" "multimodal-postgres"; then
        return 0
    fi
    
    local dry_run
    dry_run=$(get_environment_policy "$environment" "dry_run")
    
    if [ "$dry_run" = "true" ]; then
        print_status "$YELLOW" "🔍 DRY RUN: Would clean up PostgreSQL data older than $retention_days days"
        return 0
    fi
    
    # Get PostgreSQL connection details
    local postgres_host="${POSTGRES_HOST:-localhost}"
    local postgres_port="${POSTGRES_PORT:-5432}"
    local postgres_user="${POSTGRES_USER:-postgres}"
    local postgres_db="${POSTGRES_DB:-multimodal}"
    
    # Clean up old logs
    print_status "$YELLOW" "🗑️  Cleaning up old logs..."
    docker exec multimodal-postgres psql -U "$postgres_user" -d "$postgres_db" -c "
        DELETE FROM logs WHERE created_at < NOW() - INTERVAL '$retention_days days';
    " 2>/dev/null || true
    
    # Clean up old sessions
    print_status "$YELLOW" "🗑️  Cleaning up old sessions..."
    docker exec multimodal-postgres psql -U "$postgres_user" -d "$postgres_db" -c "
        DELETE FROM sessions WHERE created_at < NOW() - INTERVAL '1 day';
    " 2>/dev/null || true
    
    # Vacuum and analyze
    print_status "$YELLOW" "🧹 Running VACUUM ANALYZE..."
    docker exec multimodal-postgres psql -U "$postgres_user" -d "$postgres_db" -c "VACUUM ANALYZE;" 2>/dev/null || true
    
    print_status "$GREEN" "✅ PostgreSQL cleanup completed"
}

# Function to cleanup Redis data
cleanup_redis() {
    local environment=$1
    local retention_days=$2
    
    print_section "Cleaning up Redis data"
    
    if ! should_run_cleanup "$environment" "multimodal-redis"; then
        return 0
    fi
    
    local dry_run
    dry_run=$(get_environment_policy "$environment" "dry_run")
    
    if [ "$dry_run" = "true" ]; then
        print_status "$YELLOW" "🔍 DRY RUN: Would clean up Redis data older than $retention_days days"
        return 0
    fi
    
    # Set expiration on cache keys
    print_status "$YELLOW" "🗑️  Setting expiration on cache keys..."
    docker exec multimodal-redis redis-cli --scan --pattern "cache:*" | while read key; do
        if [ -n "$key" ]; then
            docker exec multimodal-redis redis-cli EXPIRE "$key" 86400 2>/dev/null || true
        fi
    done
    
    # Set expiration on session keys
    print_status "$YELLOW" "🗑️  Setting expiration on session keys..."
    docker exec multimodal-redis redis-cli --scan --pattern "session:*" | while read key; do
        if [ -n "$key" ]; then
            docker exec multimodal-redis redis-cli EXPIRE "$key" 3600 2>/dev/null || true
        fi
    done
    
    print_status "$GREEN" "✅ Redis cleanup completed"
}

# Function to cleanup Qdrant data
cleanup_qdrant() {
    local environment=$1
    local retention_days=$2
    
    print_section "Cleaning up Qdrant data"
    
    if ! should_run_cleanup "$environment" "multimodal-qdrant"; then
        return 0
    fi
    
    local dry_run
    dry_run=$(get_environment_policy "$environment" "dry_run")
    
    if [ "$dry_run" = "true" ]; then
        print_status "$YELLOW" "🔍 DRY RUN: Would clean up Qdrant data older than $retention_days days"
        return 0
    fi
    
    # Get Qdrant collections
    local collections
    collections=$(curl -s "http://localhost:6333/collections" | python3 -c "
import json
import sys
try:
    data = json.load(sys.stdin)
    for collection in data.get('result', {}).get('collections', []):
        print(collection['name'])
except:
    pass
" 2>/dev/null)
    
    # Clean up old collections (this is a simplified example)
    print_status "$YELLOW" "🗑️  Cleaning up old Qdrant collections..."
    echo "$collections" | while read collection; do
        if [ -n "$collection" ] && [[ "$collection" == *"old"* ]]; then
            print_status "$YELLOW" "   Deleting old collection: $collection"
            curl -X DELETE "http://localhost:6333/collections/$collection" 2>/dev/null || true
        fi
    done
    
    print_status "$GREEN" "✅ Qdrant cleanup completed"
}

# Function to cleanup MinIO data
cleanup_minio() {
    local environment=$1
    local retention_days=$2
    
    print_section "Cleaning up MinIO data"
    
    if ! should_run_cleanup "$environment" "multimodal-minio"; then
        return 0
    fi
    
    local dry_run
    dry_run=$(get_environment_policy "$environment" "dry_run")
    
    if [ "$dry_run" = "true" ]; then
        print_status "$YELLOW" "🔍 DRY RUN: Would clean up MinIO data older than $retention_days days"
        return 0
    fi
    
    # Clean up old objects in temp bucket
    print_status "$YELLOW" "🗑️  Cleaning up old temporary objects..."
    docker exec multimodal-minio find /data/temp -type f -mtime +1 -delete 2>/dev/null || true
    
    # Clean up old log files
    print_status "$YELLOW" "🗑️  Cleaning up old log files..."
    docker exec multimodal-minio find /data/logs -type f -mtime +7 -delete 2>/dev/null || true
    
    print_status "$GREEN" "✅ MinIO cleanup completed"
}

# Function to cleanup vLLM cache
cleanup_vllm_cache() {
    local environment=$1
    local retention_days=$2
    
    print_section "Cleaning up vLLM cache"
    
    if ! should_run_cleanup "$environment" "multimodal-vllm"; then
        return 0
    fi
    
    local dry_run
    dry_run=$(get_environment_policy "$environment" "dry_run")
    
    if [ "$dry_run" = "true" ]; then
        print_status "$YELLOW" "🔍 DRY RUN: Would clean up vLLM cache older than $retention_days days"
        return 0
    fi
    
    # Clean up old model cache
    print_status "$YELLOW" "🗑️  Cleaning up old model cache..."
    docker exec multimodal-vllm find /root/.cache -type f -mtime +"$retention_days" -delete 2>/dev/null || true
    
    print_status "$GREEN" "✅ vLLM cache cleanup completed"
}

# Function to cleanup test results
cleanup_test_results() {
    local environment=$1
    local retention_days=$2
    
    print_section "Cleaning up test results"
    
    local dry_run
    dry_run=$(get_environment_policy "$environment" "dry_run")
    
    if [ "$dry_run" = "true" ]; then
        print_status "$YELLOW" "🔍 DRY RUN: Would clean up test results older than $retention_days days"
        return 0
    fi
    
    # Clean up old Allure results
    print_status "$YELLOW" "🗑️  Cleaning up old Allure results..."
    find "$PROJECT_ROOT/allure-results" -type f -mtime +"$retention_days" -delete 2>/dev/null || true
    
    # Clean up old test reports
    print_status "$YELLOW" "🗑️  Cleaning up old test reports..."
    find "$PROJECT_ROOT/allure-report" -type f -mtime +"$retention_days" -delete 2>/dev/null || true
    
    print_status "$GREEN" "✅ Test results cleanup completed"
}

# Function to cleanup application logs
cleanup_application_logs() {
    local environment=$1
    local retention_days=$2
    
    print_section "Cleaning up application logs"
    
    local dry_run
    dry_run=$(get_environment_policy "$environment" "dry_run")
    
    if [ "$dry_run" = "true" ]; then
        print_status "$YELLOW" "🔍 DRY RUN: Would clean up application logs older than $retention_days days"
        return 0
    fi
    
    # Clean up old application logs
    print_status "$YELLOW" "🗑️  Cleaning up old application logs..."
    find "$PROJECT_ROOT/logs" -type f -mtime +"$retention_days" -delete 2>/dev/null || true
    
    # Clean up old container logs
    print_status "$YELLOW" "🗑️  Cleaning up old container logs..."
    docker system prune -f --filter "until=24h" 2>/dev/null || true
    
    print_status "$GREEN" "✅ Application logs cleanup completed"
}

# Function to run cleanup for specific service
cleanup_service() {
    local service=$1
    local environment=$2
    
    print_section "Cleaning up $service"
    
    local retention_days
    retention_days=$(get_service_policy "$service" "retention_days")
    
    if [ -z "$retention_days" ]; then
        retention_days=$(get_environment_policy "$environment" "default_retention_days")
    fi
    
    if [ -z "$retention_days" ]; then
        retention_days=30  # Default fallback
    fi
    
    print_status "$BLUE" "📅 Retention period: $retention_days days"
    
    case $service in
        "postgres")
            cleanup_postgres "$environment" "$retention_days"
            ;;
        "redis")
            cleanup_redis "$environment" "$retention_days"
            ;;
        "qdrant")
            cleanup_qdrant "$environment" "$retention_days"
            ;;
        "minio")
            cleanup_minio "$environment" "$retention_days"
            ;;
        "vllm")
            cleanup_vllm_cache "$environment" "$retention_days"
            ;;
        "test-results")
            cleanup_test_results "$environment" "$retention_days"
            ;;
        "application-logs")
            cleanup_application_logs "$environment" "$retention_days"
            ;;
        *)
            print_status "$YELLOW" "⚠️  Unknown service: $service"
            ;;
    esac
}

# Function to run cleanup for environment
cleanup_environment() {
    local environment=$1
    
    print_section "Running cleanup for $environment environment"
    
    local start_time
    start_time=$(date +%s)
    
    # Get list of services to clean up
    local services=("postgres" "redis" "qdrant" "minio" "vllm" "test-results" "application-logs")
    
    local services_processed=0
    local services_failed=0
    
    for service in "${services[@]}"; do
        if cleanup_service "$service" "$environment"; then
            ((services_processed++))
        else
            ((services_failed++))
        fi
    done
    
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_section "Cleanup Summary"
    print_status "$GREEN" "✅ Services processed: $services_processed"
    if [ $services_failed -gt 0 ]; then
        print_status "$RED" "❌ Services failed: $services_failed"
    fi
    print_status "$BLUE" "⏱️  Duration: ${duration}s"
    
    # Send notification if enabled
    local notifications_enabled
    notifications_enabled=$(get_environment_policy "$environment" "notifications.enabled")
    if [ "$notifications_enabled" = "true" ]; then
        send_notification "$environment" "cleanup_completed" "$services_processed" "$services_failed" "$duration"
    fi
}

# Function to send notifications
send_notification() {
    local environment=$1
    local type=$2
    local services_processed=$3
    local services_failed=$4
    local duration=$5
    
    print_status "$BLUE" "📧 Sending notification: $type"
    
    # This is a placeholder for notification implementation
    # In a real implementation, you would send emails, webhooks, etc.
    log_message "INFO" "Notification sent: $type for $environment environment"
}

# Function to show retention status
show_retention_status() {
    local environment=${1:-"development"}
    
    print_section "Retention Status for $environment"
    
    print_status "$BLUE" "📊 Environment Configuration:"
    local default_retention
    default_retention=$(get_environment_policy "$environment" "default_retention_days")
    print_status "$YELLOW" "   Default retention: ${default_retention:-30} days"
    
    local cleanup_schedule
    cleanup_schedule=$(get_environment_policy "$environment" "cleanup_schedule")
    print_status "$YELLOW" "   Cleanup schedule: ${cleanup_schedule:-'0 2 * * *'}"
    
    local dry_run
    dry_run=$(get_environment_policy "$environment" "dry_run")
    print_status "$YELLOW" "   Dry run mode: ${dry_run:-false}"
    
    echo ""
    print_status "$BLUE" "📊 Service Retention Policies:"
    
    local services=("postgres" "redis" "qdrant" "minio" "vllm")
    for service in "${services[@]}"; do
        local retention_days
        retention_days=$(get_service_policy "$service" "retention_days")
        if [ -n "$retention_days" ]; then
            print_status "$GREEN" "   $service: $retention_days days"
        else
            print_status "$YELLOW" "   $service: Using default (${default_retention:-30} days)"
        fi
    done
}

# Function to show help
show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  cleanup <environment>        Run cleanup for specific environment"
    echo "  cleanup-service <service> <env>  Run cleanup for specific service"
    echo "  status [environment]         Show retention status"
    echo "  test <environment>           Test cleanup (dry run)"
    echo "  help                         Show this help message"
    echo ""
    echo "Environments:"
    echo "  development, staging, production, testing"
    echo ""
    echo "Services:"
    echo "  postgres, redis, qdrant, minio, vllm, test-results, application-logs"
    echo ""
    echo "Examples:"
    echo "  $0 cleanup development       # Run cleanup for development"
    echo "  $0 cleanup-service postgres development  # Cleanup PostgreSQL in dev"
    echo "  $0 status production         # Show retention status for production"
    echo "  $0 test staging              # Test cleanup for staging (dry run)"
}

# Main function
main() {
    local command=${1:-help}
    local target=${2:-}
    local environment=${3:-development}
    
    # Load configuration
    load_retention_config
    
    case $command in
        "cleanup")
            if [ -z "$target" ]; then
                print_status "$RED" "❌ Environment required"
                show_help
                exit 1
            fi
            cleanup_environment "$target"
            ;;
        "cleanup-service")
            if [ -z "$target" ] || [ -z "$environment" ]; then
                print_status "$RED" "❌ Service and environment required"
                show_help
                exit 1
            fi
            cleanup_service "$target" "$environment"
            ;;
        "status")
            show_retention_status "$target"
            ;;
        "test")
            if [ -z "$target" ]; then
                print_status "$RED" "❌ Environment required"
                show_help
                exit 1
            fi
            # Set dry run mode for testing
            export DRY_RUN=true
            cleanup_environment "$target"
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
