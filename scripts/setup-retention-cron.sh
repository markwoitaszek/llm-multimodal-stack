#!/bin/bash

# Setup Retention Cron Jobs Script
# Configures automated retention cleanup via cron

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
RETENTION_SCRIPT="$PROJECT_ROOT/scripts/manage-retention.sh"

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

# Function to check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_status "$YELLOW" "⚠️  Running as root. This is required for cron setup."
    else
        print_status "$RED" "❌ This script must be run as root to setup cron jobs"
        print_status "$YELLOW" "Please run: sudo $0"
        exit 1
    fi
}

# Function to setup cron job for environment
setup_environment_cron() {
    local environment=$1
    local schedule=$2
    
    print_section "Setting up cron job for $environment environment"
    
    # Create cron job entry
    local cron_entry="$schedule $RETENTION_SCRIPT cleanup $environment >> $PROJECT_ROOT/logs/retention-cron.log 2>&1"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$RETENTION_SCRIPT cleanup $environment"; then
        print_status "$YELLOW" "⚠️  Cron job for $environment already exists"
        return 0
    fi
    
    # Add cron job
    (crontab -l 2>/dev/null; echo "$cron_entry") | crontab -
    
    if [ $? -eq 0 ]; then
        print_status "$GREEN" "✅ Cron job added for $environment environment"
        print_status "$BLUE" "   Schedule: $schedule"
        print_status "$BLUE" "   Command: $RETENTION_SCRIPT cleanup $environment"
    else
        print_status "$RED" "❌ Failed to add cron job for $environment"
        return 1
    fi
}

# Function to setup all environment cron jobs
setup_all_cron_jobs() {
    print_section "Setting up all environment cron jobs"
    
    # Development environment - Daily at 1 AM
    setup_environment_cron "development" "0 1 * * *"
    
    # Staging environment - Daily at 2 AM
    setup_environment_cron "staging" "0 2 * * *"
    
    # Production environment - Weekly on Sunday at 3 AM
    setup_environment_cron "production" "0 3 * * 0"
    
    # Testing environment - Daily at midnight
    setup_environment_cron "testing" "0 0 * * *"
    
    print_status "$GREEN" "✅ All cron jobs setup completed"
}

# Function to show current cron jobs
show_cron_jobs() {
    print_section "Current Retention Cron Jobs"
    
    local cron_jobs
    cron_jobs=$(crontab -l 2>/dev/null | grep "$RETENTION_SCRIPT" || true)
    
    if [ -z "$cron_jobs" ]; then
        print_status "$YELLOW" "No retention cron jobs found"
    else
        echo "$cron_jobs" | while read -r job; do
            if [ -n "$job" ]; then
                print_status "$GREEN" "✅ $job"
            fi
        done
    fi
}

# Function to remove cron jobs
remove_cron_jobs() {
    print_section "Removing retention cron jobs"
    
    # Remove all retention-related cron jobs
    crontab -l 2>/dev/null | grep -v "$RETENTION_SCRIPT" | crontab -
    
    if [ $? -eq 0 ]; then
        print_status "$GREEN" "✅ All retention cron jobs removed"
    else
        print_status "$RED" "❌ Failed to remove cron jobs"
        return 1
    fi
}

# Function to test cron job
test_cron_job() {
    local environment=${1:-development}
    
    print_section "Testing cron job for $environment environment"
    
    print_status "$YELLOW" "🔍 Running retention cleanup in test mode..."
    "$RETENTION_SCRIPT" test "$environment"
    
    if [ $? -eq 0 ]; then
        print_status "$GREEN" "✅ Cron job test completed successfully"
    else
        print_status "$RED" "❌ Cron job test failed"
        return 1
    fi
}

# Function to show cron job status
show_cron_status() {
    print_section "Cron Service Status"
    
    # Check if cron service is running
    if systemctl is-active --quiet cron; then
        print_status "$GREEN" "✅ Cron service is running"
    else
        print_status "$RED" "❌ Cron service is not running"
        print_status "$YELLOW" "Start with: sudo systemctl start cron"
    fi
    
    # Check if cron service is enabled
    if systemctl is-enabled --quiet cron; then
        print_status "$GREEN" "✅ Cron service is enabled"
    else
        print_status "$YELLOW" "⚠️  Cron service is not enabled"
        print_status "$YELLOW" "Enable with: sudo systemctl enable cron"
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup                     Setup all retention cron jobs"
    echo "  setup-env <environment>   Setup cron job for specific environment"
    echo "  show                      Show current cron jobs"
    echo "  remove                    Remove all retention cron jobs"
    echo "  test [environment]        Test cron job for environment"
    echo "  status                    Show cron service status"
    echo "  help                      Show this help message"
    echo ""
    echo "Environments:"
    echo "  development, staging, production, testing"
    echo ""
    echo "Examples:"
    echo "  sudo $0 setup                    # Setup all cron jobs"
    echo "  sudo $0 setup-env development    # Setup dev cron job"
    echo "  sudo $0 show                     # Show current cron jobs"
    echo "  sudo $0 test production          # Test production cron job"
    echo "  sudo $0 remove                   # Remove all cron jobs"
}

# Main function
main() {
    local command=${1:-help}
    local target=${2:-}
    
    # Check if running as root
    check_root
    
    case $command in
        "setup")
            setup_all_cron_jobs
            show_cron_jobs
            ;;
        "setup-env")
            if [ -z "$target" ]; then
                print_status "$RED" "❌ Environment required"
                show_help
                exit 1
            fi
            
            # Get schedule for environment
            local schedule
            case $target in
                "development")
                    schedule="0 1 * * *"
                    ;;
                "staging")
                    schedule="0 2 * * *"
                    ;;
                "production")
                    schedule="0 3 * * 0"
                    ;;
                "testing")
                    schedule="0 0 * * *"
                    ;;
                *)
                    print_status "$RED" "❌ Unknown environment: $target"
                    exit 1
                    ;;
            esac
            
            setup_environment_cron "$target" "$schedule"
            ;;
        "show")
            show_cron_jobs
            ;;
        "remove")
            remove_cron_jobs
            ;;
        "test")
            test_cron_job "$target"
            ;;
        "status")
            show_cron_status
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
