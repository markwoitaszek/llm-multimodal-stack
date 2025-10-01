#!/bin/bash

# Multi-Tier Backup Management Script
# Implements comprehensive backup strategies for all services and environments

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
BACKUP_CONFIG="$PROJECT_ROOT/configs/backup-strategies.yaml"
LOG_FILE="$PROJECT_ROOT/logs/backup-$(date +%Y%m%d).log"
BACKUP_BASE_DIR="$PROJECT_ROOT/backups"

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

# Function to load backup configuration
load_backup_config() {
    if [ ! -f "$BACKUP_CONFIG" ]; then
        print_status "$RED" "❌ Backup configuration file not found: $BACKUP_CONFIG"
        exit 1
    fi
    
    # Create logs and backup directories if they don't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$BACKUP_BASE_DIR"
    
    print_status "$GREEN" "✅ Loaded backup configuration from $BACKUP_CONFIG"
}

# Function to get environment-specific backup policy
get_environment_backup_policy() {
    local environment=$1
    local policy_key=$2
    
    python3 -c "
import yaml
import sys

try:
    with open('$BACKUP_CONFIG', 'r') as f:
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

# Function to get service-specific backup policy
get_service_backup_policy() {
    local service=$1
    local policy_key=$2
    
    python3 -c "
import yaml
import sys

try:
    with open('$BACKUP_CONFIG', 'r') as f:
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

# Function to create backup directory
create_backup_directory() {
    local service=$1
    local environment=$2
    local backup_type=$3
    
    local backup_dir="$BACKUP_BASE_DIR/$environment/$service/$backup_type"
    mkdir -p "$backup_dir"
    echo "$backup_dir"
}

# Function to generate backup filename
generate_backup_filename() {
    local service=$1
    local backup_type=$2
    local timestamp=$(date +%Y%m%d_%H%M%S)
    echo "${service}_${backup_type}_${timestamp}"
}

# Function to backup PostgreSQL
backup_postgres() {
    local environment=$1
    local backup_type=${2:-"full"}
    
    print_section "Backing up PostgreSQL ($backup_type)"
    
    # Check if PostgreSQL is running
    if ! docker ps --format "{{.Names}}" | grep -q "multimodal-postgres"; then
        print_status "$RED" "❌ PostgreSQL is not running"
        return 1
    fi
    
    # Get backup configuration
    local retention_days
    retention_days=$(get_service_backup_policy "postgres" "retention_days")
    local compression
    compression=$(get_service_backup_policy "postgres" "compression")
    
    # Create backup directory
    local backup_dir
    backup_dir=$(create_backup_directory "postgres" "$environment" "$backup_type")
    
    # Generate backup filename
    local backup_filename
    backup_filename=$(generate_backup_filename "postgres" "$backup_type")
    local backup_file="$backup_dir/${backup_filename}.sql"
    
    # Get PostgreSQL connection details
    local postgres_host="${POSTGRES_HOST:-localhost}"
    local postgres_port="${POSTGRES_PORT:-5432}"
    local postgres_user="${POSTGRES_USER:-postgres}"
    local postgres_db="${POSTGRES_DB:-multimodal}"
    
    print_status "$YELLOW" "🗄️  Creating $backup_type backup..."
    print_status "$BLUE" "   Database: $postgres_db"
    print_status "$BLUE" "   Backup file: $backup_file"
    
    # Create backup based on type
    case $backup_type in
        "full")
            docker exec multimodal-postgres pg_dump -U "$postgres_user" -d "$postgres_db" --format=custom --verbose --no-owner --no-privileges > "$backup_file"
            ;;
        "schema")
            docker exec multimodal-postgres pg_dump -U "$postgres_user" -d "$postgres_db" --schema-only --format=custom > "$backup_file"
            ;;
        "data")
            docker exec multimodal-postgres pg_dump -U "$postgres_user" -d "$postgres_db" --data-only --format=custom > "$backup_file"
            ;;
        *)
            print_status "$RED" "❌ Unknown backup type: $backup_type"
            return 1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        print_status "$GREEN" "✅ PostgreSQL backup completed"
        
        # Compress if enabled
        if [ "$compression" = "true" ]; then
            print_status "$YELLOW" "🗜️  Compressing backup..."
            gzip "$backup_file"
            backup_file="${backup_file}.gz"
        fi
        
        # Calculate backup size
        local backup_size
        backup_size=$(du -h "$backup_file" | cut -f1)
        print_status "$BLUE" "📊 Backup size: $backup_size"
        
        # Clean up old backups
        cleanup_old_backups "$backup_dir" "$retention_days"
        
        return 0
    else
        print_status "$RED" "❌ PostgreSQL backup failed"
        return 1
    fi
}

# Function to backup Redis
backup_redis() {
    local environment=$1
    local backup_type=${2:-"rdb"}
    
    print_section "Backing up Redis ($backup_type)"
    
    # Check if Redis is running
    if ! docker ps --format "{{.Names}}" | grep -q "multimodal-redis"; then
        print_status "$RED" "❌ Redis is not running"
        return 1
    fi
    
    # Get backup configuration
    local retention_days
    retention_days=$(get_service_backup_policy "redis" "retention_days")
    local compression
    compression=$(get_service_backup_policy "redis" "compression")
    
    # Create backup directory
    local backup_dir
    backup_dir=$(create_backup_directory "redis" "$environment" "$backup_type")
    
    # Generate backup filename
    local backup_filename
    backup_filename=$(generate_backup_filename "redis" "$backup_type")
    local backup_file="$backup_dir/${backup_filename}.rdb"
    
    print_status "$YELLOW" "🗄️  Creating $backup_type backup..."
    print_status "$BLUE" "   Backup file: $backup_file"
    
    # Create backup based on type
    case $backup_type in
        "rdb")
            # Trigger RDB save and copy the file
            docker exec multimodal-redis redis-cli BGSAVE
            sleep 5  # Wait for background save to complete
            docker cp multimodal-redis:/data/dump.rdb "$backup_file"
            ;;
        "aof")
            # Copy AOF file if it exists
            docker cp multimodal-redis:/data/appendonly.aof "$backup_file" 2>/dev/null || true
            ;;
        *)
            print_status "$RED" "❌ Unknown backup type: $backup_type"
            return 1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        print_status "$GREEN" "✅ Redis backup completed"
        
        # Compress if enabled
        if [ "$compression" = "true" ]; then
            print_status "$YELLOW" "🗜️  Compressing backup..."
            gzip "$backup_file"
            backup_file="${backup_file}.gz"
        fi
        
        # Calculate backup size
        local backup_size
        backup_size=$(du -h "$backup_file" | cut -f1)
        print_status "$BLUE" "📊 Backup size: $backup_size"
        
        # Clean up old backups
        cleanup_old_backups "$backup_dir" "$retention_days"
        
        return 0
    else
        print_status "$RED" "❌ Redis backup failed"
        return 1
    fi
}

# Function to backup Qdrant
backup_qdrant() {
    local environment=$1
    local backup_type=${2:-"collection"}
    
    print_section "Backing up Qdrant ($backup_type)"
    
    # Check if Qdrant is running
    if ! docker ps --format "{{.Names}}" | grep -q "multimodal-qdrant"; then
        print_status "$RED" "❌ Qdrant is not running"
        return 1
    fi
    
    # Get backup configuration
    local retention_days
    retention_days=$(get_service_backup_policy "qdrant" "retention_days")
    local compression
    compression=$(get_service_backup_policy "qdrant" "compression")
    
    # Create backup directory
    local backup_dir
    backup_dir=$(create_backup_directory "qdrant" "$environment" "$backup_type")
    
    # Generate backup filename
    local backup_filename
    backup_filename=$(generate_backup_filename "qdrant" "$backup_type")
    local backup_file="$backup_dir/${backup_filename}.json"
    
    print_status "$YELLOW" "🗄️  Creating $backup_type backup..."
    print_status "$BLUE" "   Backup file: $backup_file"
    
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
    
    # Create backup based on type
    case $backup_type in
        "collection")
            # Backup each collection
            echo "$collections" | while read collection; do
                if [ -n "$collection" ]; then
                    print_status "$YELLOW" "   Backing up collection: $collection"
                    curl -s "http://localhost:6333/collections/$collection" > "$backup_dir/${collection}_${backup_filename}.json"
                fi
            done
            ;;
        "config")
            # Backup Qdrant configuration
            curl -s "http://localhost:6333/cluster" > "$backup_file"
            ;;
        *)
            print_status "$RED" "❌ Unknown backup type: $backup_type"
            return 1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        print_status "$GREEN" "✅ Qdrant backup completed"
        
        # Compress if enabled
        if [ "$compression" = "true" ]; then
            print_status "$YELLOW" "🗜️  Compressing backup..."
            tar -czf "${backup_file}.tar.gz" -C "$backup_dir" .
        fi
        
        # Calculate backup size
        local backup_size
        backup_size=$(du -sh "$backup_dir" | cut -f1)
        print_status "$BLUE" "📊 Backup size: $backup_size"
        
        # Clean up old backups
        cleanup_old_backups "$backup_dir" "$retention_days"
        
        return 0
    else
        print_status "$RED" "❌ Qdrant backup failed"
        return 1
    fi
}

# Function to backup MinIO
backup_minio() {
    local environment=$1
    local backup_type=${2:-"bucket"}
    
    print_section "Backing up MinIO ($backup_type)"
    
    # Check if MinIO is running
    if ! docker ps --format "{{.Names}}" | grep -q "multimodal-minio"; then
        print_status "$RED" "❌ MinIO is not running"
        return 1
    fi
    
    # Get backup configuration
    local retention_days
    retention_days=$(get_service_backup_policy "minio" "retention_days")
    local compression
    compression=$(get_service_backup_policy "minio" "compression")
    
    # Create backup directory
    local backup_dir
    backup_dir=$(create_backup_directory "minio" "$environment" "$backup_type")
    
    # Generate backup filename
    local backup_filename
    backup_filename=$(generate_backup_filename "minio" "$backup_type")
    local backup_file="$backup_dir/${backup_filename}.tar"
    
    print_status "$YELLOW" "🗄️  Creating $backup_type backup..."
    print_status "$BLUE" "   Backup file: $backup_file"
    
    # Create backup based on type
    case $backup_type in
        "bucket")
            # Backup MinIO data directory
            docker exec multimodal-minio tar -cf - /data > "$backup_file"
            ;;
        "config")
            # Backup MinIO configuration
            docker exec multimodal-minio cat /root/.minio/config.json > "$backup_file" 2>/dev/null || true
            ;;
        *)
            print_status "$RED" "❌ Unknown backup type: $backup_type"
            return 1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        print_status "$GREEN" "✅ MinIO backup completed"
        
        # Compress if enabled
        if [ "$compression" = "true" ]; then
            print_status "$YELLOW" "🗜️  Compressing backup..."
            gzip "$backup_file"
            backup_file="${backup_file}.gz"
        fi
        
        # Calculate backup size
        local backup_size
        backup_size=$(du -h "$backup_file" | cut -f1)
        print_status "$BLUE" "📊 Backup size: $backup_size"
        
        # Clean up old backups
        cleanup_old_backups "$backup_dir" "$retention_days"
        
        return 0
    else
        print_status "$RED" "❌ MinIO backup failed"
        return 1
    fi
}

# Function to backup vLLM cache
backup_vllm_cache() {
    local environment=$1
    local backup_type=${2:-"models"}
    
    print_section "Backing up vLLM cache ($backup_type)"
    
    # Check if vLLM is running
    if ! docker ps --format "{{.Names}}" | grep -q "multimodal-vllm"; then
        print_status "$RED" "❌ vLLM is not running"
        return 1
    fi
    
    # Get backup configuration
    local retention_days
    retention_days=$(get_service_backup_policy "vllm" "retention_days")
    local compression
    compression=$(get_service_backup_policy "vllm" "compression")
    
    # Create backup directory
    local backup_dir
    backup_dir=$(create_backup_directory "vllm" "$environment" "$backup_type")
    
    # Generate backup filename
    local backup_filename
    backup_filename=$(generate_backup_filename "vllm" "$backup_type")
    local backup_file="$backup_dir/${backup_filename}.tar"
    
    print_status "$YELLOW" "🗄️  Creating $backup_type backup..."
    print_status "$BLUE" "   Backup file: $backup_file"
    
    # Create backup based on type
    case $backup_type in
        "models")
            # Backup model cache
            docker exec multimodal-vllm tar -cf - /root/.cache > "$backup_file"
            ;;
        "config")
            # Backup vLLM configuration
            docker exec multimodal-vllm find /app -name "*.json" -o -name "*.yaml" -o -name "*.yml" | tar -cf - -T - > "$backup_file"
            ;;
        *)
            print_status "$RED" "❌ Unknown backup type: $backup_type"
            return 1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        print_status "$GREEN" "✅ vLLM cache backup completed"
        
        # Compress if enabled
        if [ "$compression" = "true" ]; then
            print_status "$YELLOW" "🗜️  Compressing backup..."
            gzip "$backup_file"
            backup_file="${backup_file}.gz"
        fi
        
        # Calculate backup size
        local backup_size
        backup_size=$(du -h "$backup_file" | cut -f1)
        print_status "$BLUE" "📊 Backup size: $backup_size"
        
        # Clean up old backups
        cleanup_old_backups "$backup_dir" "$retention_days"
        
        return 0
    else
        print_status "$RED" "❌ vLLM cache backup failed"
        return 1
    fi
}

# Function to backup test results
backup_test_results() {
    local environment=$1
    local backup_type=${2:-"reports"}
    
    print_section "Backing up test results ($backup_type)"
    
    # Get backup configuration
    local retention_days
    retention_days=$(get_service_backup_policy "allure" "retention_days")
    local compression
    compression=$(get_service_backup_policy "allure" "compression")
    
    # Create backup directory
    local backup_dir
    backup_dir=$(create_backup_directory "test-results" "$environment" "$backup_type")
    
    # Generate backup filename
    local backup_filename
    backup_filename=$(generate_backup_filename "test-results" "$backup_type")
    local backup_file="$backup_dir/${backup_filename}.tar"
    
    print_status "$YELLOW" "🗄️  Creating $backup_type backup..."
    print_status "$BLUE" "   Backup file: $backup_file"
    
    # Create backup based on type
    case $backup_type in
        "reports")
            # Backup Allure reports
            if [ -d "$PROJECT_ROOT/allure-report" ]; then
                tar -cf "$backup_file" -C "$PROJECT_ROOT" allure-report
            fi
            ;;
        "results")
            # Backup Allure results
            if [ -d "$PROJECT_ROOT/allure-results" ]; then
                tar -cf "$backup_file" -C "$PROJECT_ROOT" allure-results
            fi
            ;;
        *)
            print_status "$RED" "❌ Unknown backup type: $backup_type"
            return 1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        print_status "$GREEN" "✅ Test results backup completed"
        
        # Compress if enabled
        if [ "$compression" = "true" ]; then
            print_status "$YELLOW" "🗜️  Compressing backup..."
            gzip "$backup_file"
            backup_file="${backup_file}.gz"
        fi
        
        # Calculate backup size
        local backup_size
        backup_size=$(du -h "$backup_file" | cut -f1)
        print_status "$BLUE" "📊 Backup size: $backup_size"
        
        # Clean up old backups
        cleanup_old_backups "$backup_dir" "$retention_days"
        
        return 0
    else
        print_status "$RED" "❌ Test results backup failed"
        return 1
    fi
}

# Function to cleanup old backups
cleanup_old_backups() {
    local backup_dir=$1
    local retention_days=$2
    
    if [ -z "$retention_days" ]; then
        retention_days=30  # Default retention
    fi
    
    print_status "$YELLOW" "🧹 Cleaning up backups older than $retention_days days..."
    
    # Find and remove old backup files
    find "$backup_dir" -type f -mtime +"$retention_days" -delete 2>/dev/null || true
    
    print_status "$GREEN" "✅ Old backups cleaned up"
}

# Function to backup specific service
backup_service() {
    local service=$1
    local environment=$2
    local backup_type=${3:-"full"}
    
    print_section "Backing up $service"
    
    case $service in
        "postgres")
            backup_postgres "$environment" "$backup_type"
            ;;
        "redis")
            backup_redis "$environment" "$backup_type"
            ;;
        "qdrant")
            backup_qdrant "$environment" "$backup_type"
            ;;
        "minio")
            backup_minio "$environment" "$backup_type"
            ;;
        "vllm")
            backup_vllm_cache "$environment" "$backup_type"
            ;;
        "test-results")
            backup_test_results "$environment" "$backup_type"
            ;;
        *)
            print_status "$RED" "❌ Unknown service: $service"
            return 1
            ;;
    esac
}

# Function to backup environment
backup_environment() {
    local environment=$1
    
    print_section "Running backup for $environment environment"
    
    local start_time
    start_time=$(date +%s)
    
    # Get list of services to backup
    local services=("postgres" "redis" "qdrant" "minio" "vllm" "test-results")
    
    local services_backed_up=0
    local services_failed=0
    
    for service in "${services[@]}"; do
        if backup_service "$service" "$environment"; then
            ((services_backed_up++))
        else
            ((services_failed++))
        fi
    done
    
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_section "Backup Summary"
    print_status "$GREEN" "✅ Services backed up: $services_backed_up"
    if [ $services_failed -gt 0 ]; then
        print_status "$RED" "❌ Services failed: $services_failed"
    fi
    print_status "$BLUE" "⏱️  Duration: ${duration}s"
    
    # Send notification if enabled
    local notifications_enabled
    notifications_enabled=$(get_environment_backup_policy "$environment" "notifications.enabled")
    if [ "$notifications_enabled" = "true" ]; then
        send_notification "$environment" "backup_completed" "$services_backed_up" "$services_failed" "$duration"
    fi
}

# Function to send notifications
send_notification() {
    local environment=$1
    local type=$2
    local services_backed_up=$3
    local services_failed=$4
    local duration=$5
    
    print_status "$BLUE" "📧 Sending notification: $type"
    
    # This is a placeholder for notification implementation
    # In a real implementation, you would send emails, webhooks, etc.
    log_message "INFO" "Notification sent: $type for $environment environment"
}

# Function to show backup status
show_backup_status() {
    local environment=${1:-"development"}
    
    print_section "Backup Status for $environment"
    
    print_status "$BLUE" "📊 Environment Configuration:"
    local retention_days
    retention_days=$(get_environment_backup_policy "$environment" "retention_days")
    print_status "$YELLOW" "   Retention: ${retention_days:-30} days"
    
    local backup_schedule
    backup_schedule=$(get_environment_backup_policy "$environment" "backup_schedule")
    print_status "$YELLOW" "   Schedule: ${backup_schedule:-'0 3 * * *'}"
    
    local compression
    compression=$(get_environment_backup_policy "$environment" "compression.enabled")
    print_status "$YELLOW" "   Compression: ${compression:-true}"
    
    echo ""
    print_status "$BLUE" "📊 Service Backup Policies:"
    
    local services=("postgres" "redis" "qdrant" "minio" "vllm")
    for service in "${services[@]}"; do
        local retention_days
        retention_days=$(get_service_backup_policy "$service" "retention_days")
        local backup_frequency
        backup_frequency=$(get_service_backup_policy "$service" "backup_frequency")
        if [ -n "$retention_days" ]; then
            print_status "$GREEN" "   $service: $retention_days days ($backup_frequency)"
        else
            print_status "$YELLOW" "   $service: Using default (${retention_days:-30} days)"
        fi
    done
    
    echo ""
    print_status "$BLUE" "📊 Recent Backups:"
    if [ -d "$BACKUP_BASE_DIR/$environment" ]; then
        find "$BACKUP_BASE_DIR/$environment" -type f -name "*.gz" -o -name "*.tar" -o -name "*.sql" | head -10 | while read backup_file; do
            local file_size
            file_size=$(du -h "$backup_file" | cut -f1)
            local file_date
            file_date=$(stat -c %y "$backup_file" | cut -d' ' -f1)
            print_status "$GREEN" "   $(basename "$backup_file"): $file_size ($file_date)"
        done
    else
        print_status "$YELLOW" "   No backups found for $environment"
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  backup <environment>        Run backup for specific environment"
    echo "  backup-service <service> <env> [type]  Run backup for specific service"
    echo "  status [environment]         Show backup status"
    echo "  restore <service> <env> <file>  Restore from backup"
    echo "  list [environment]           List available backups"
    echo "  help                         Show this help message"
    echo ""
    echo "Environments:"
    echo "  development, staging, production, testing"
    echo ""
    echo "Services:"
    echo "  postgres, redis, qdrant, minio, vllm, test-results"
    echo ""
    echo "Backup Types:"
    echo "  full, schema, data, rdb, aof, collection, config, bucket, models, reports, results"
    echo ""
    echo "Examples:"
    echo "  $0 backup development       # Run backup for development"
    echo "  $0 backup-service postgres development full  # Backup PostgreSQL in dev"
    echo "  $0 status production         # Show backup status for production"
    echo "  $0 list staging              # List available backups for staging"
}

# Main function
main() {
    local command=${1:-help}
    local target=${2:-}
    local environment=${3:-development}
    local backup_type=${4:-full}
    
    # Load configuration
    load_backup_config
    
    case $command in
        "backup")
            if [ -z "$target" ]; then
                print_status "$RED" "❌ Environment required"
                show_help
                exit 1
            fi
            backup_environment "$target"
            ;;
        "backup-service")
            if [ -z "$target" ] || [ -z "$environment" ]; then
                print_status "$RED" "❌ Service and environment required"
                show_help
                exit 1
            fi
            backup_service "$target" "$environment" "$backup_type"
            ;;
        "status")
            show_backup_status "$target"
            ;;
        "list")
            if [ -z "$target" ]; then
                print_status "$RED" "❌ Environment required"
                show_help
                exit 1
            fi
            show_backup_status "$target"
            ;;
        "restore")
            print_status "$YELLOW" "⚠️  Restore functionality not implemented yet"
            print_status "$BLUE" "This would restore from a specific backup file"
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
