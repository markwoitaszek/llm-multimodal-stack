#!/bin/bash

# Test script for data operations
# Tests data retention policies, backup operations, and data management

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Test configuration
TEST_ENVIRONMENTS=("development" "staging" "production" "testing")
TEST_SERVICES=("postgres" "redis" "qdrant" "minio" "vllm")
TEST_TIMEOUT=30

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test result tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_exit_code="${3:-0}"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    log_info "Running test: $test_name"
    
    if eval "$test_command"; then
        if [ $? -eq $expected_exit_code ]; then
            log_success "✅ $test_name: PASSED"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            log_error "❌ $test_name: FAILED (unexpected exit code)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        log_error "❌ $test_name: FAILED"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Test retention status commands
test_retention_status() {
    log_info "Testing retention status commands..."
    
    local status_tests_passed=0
    local status_tests_total=${#TEST_ENVIRONMENTS[@]}
    
    for env in "${TEST_ENVIRONMENTS[@]}"; do
        if make retention-status ENVIRONMENT=$env >/dev/null 2>&1; then
            log_success "✅ Retention status for $env: PASSED"
            status_tests_passed=$((status_tests_passed + 1))
        else
            log_error "❌ Retention status for $env: FAILED"
        fi
    done
    
    if [ $status_tests_passed -eq $status_tests_total ]; then
        log_success "✅ Retention status commands: PASSED ($status_tests_passed/$status_tests_total)"
        return 0
    else
        log_error "❌ Retention status commands: FAILED ($status_tests_passed/$status_tests_total)"
        return 1
    fi
}

# Test retention cleanup (dry run)
test_retention_cleanup_dry_run() {
    log_info "Testing retention cleanup (dry run)..."
    
    local cleanup_tests_passed=0
    local cleanup_tests_total=${#TEST_ENVIRONMENTS[@]}
    
    for env in "${TEST_ENVIRONMENTS[@]}"; do
        # Test dry run cleanup
        if make retention-cleanup ENVIRONMENT=$env >/dev/null 2>&1; then
            log_success "✅ Retention cleanup (dry run) for $env: PASSED"
            cleanup_tests_passed=$((cleanup_tests_passed + 1))
        else
            log_error "❌ Retention cleanup (dry run) for $env: FAILED"
        fi
    done
    
    if [ $cleanup_tests_passed -eq $cleanup_tests_total ]; then
        log_success "✅ Retention cleanup (dry run): PASSED ($cleanup_tests_passed/$cleanup_tests_total)"
        return 0
    else
        log_error "❌ Retention cleanup (dry run): FAILED ($cleanup_tests_passed/$cleanup_tests_total)"
        return 1
    fi
}

# Test retention test commands
test_retention_test() {
    log_info "Testing retention test commands..."
    
    local test_tests_passed=0
    local test_tests_total=${#TEST_ENVIRONMENTS[@]}
    
    for env in "${TEST_ENVIRONMENTS[@]}"; do
        if make retention-test ENVIRONMENT=$env >/dev/null 2>&1; then
            log_success "✅ Retention test for $env: PASSED"
            test_tests_passed=$((test_tests_passed + 1))
        else
            log_error "❌ Retention test for $env: FAILED"
        fi
    done
    
    if [ $test_tests_passed -eq $test_tests_total ]; then
        log_success "✅ Retention test commands: PASSED ($test_tests_passed/$test_tests_total)"
        return 0
    else
        log_error "❌ Retention test commands: FAILED ($test_tests_passed/$test_tests_total)"
        return 1
    fi
}

# Test retention schedule
test_retention_schedule() {
    log_info "Testing retention schedule..."
    
    if make retention-schedule >/dev/null 2>&1; then
        log_success "✅ Retention schedule: PASSED"
        return 0
    else
        log_error "❌ Retention schedule: FAILED"
        return 1
    fi
}

# Test backup status commands
test_backup_status() {
    log_info "Testing backup status commands..."
    
    local status_tests_passed=0
    local status_tests_total=${#TEST_ENVIRONMENTS[@]}
    
    for env in "${TEST_ENVIRONMENTS[@]}"; do
        if make backup-status ENVIRONMENT=$env >/dev/null 2>&1; then
            log_success "✅ Backup status for $env: PASSED"
            status_tests_passed=$((status_tests_passed + 1))
        else
            log_error "❌ Backup status for $env: FAILED"
        fi
    done
    
    if [ $status_tests_passed -eq $status_tests_total ]; then
        log_success "✅ Backup status commands: PASSED ($status_tests_passed/$status_tests_total)"
        return 0
    else
        log_error "❌ Backup status commands: FAILED ($status_tests_passed/$status_tests_total)"
        return 1
    fi
}

# Test backup full operations
test_backup_full() {
    log_info "Testing backup full operations..."
    
    local backup_tests_passed=0
    local backup_tests_total=${#TEST_ENVIRONMENTS[@]}
    
    for env in "${TEST_ENVIRONMENTS[@]}"; do
        if make backup-full ENVIRONMENT=$env >/dev/null 2>&1; then
            log_success "✅ Backup full for $env: PASSED"
            backup_tests_passed=$((backup_tests_passed + 1))
        else
            log_error "❌ Backup full for $env: FAILED"
        fi
    done
    
    if [ $backup_tests_passed -eq $backup_tests_total ]; then
        log_success "✅ Backup full operations: PASSED ($backup_tests_passed/$backup_tests_total)"
        return 0
    else
        log_error "❌ Backup full operations: FAILED ($backup_tests_passed/$backup_tests_total)"
        return 1
    fi
}

# Test backup service operations
test_backup_service() {
    log_info "Testing backup service operations..."
    
    local service_tests_passed=0
    local service_tests_total=0
    
    for env in "${TEST_ENVIRONMENTS[@]}"; do
        for service in "${TEST_SERVICES[@]}"; do
            service_tests_total=$((service_tests_total + 1))
            
            if make backup-service SERVICE=$service ENVIRONMENT=$env >/dev/null 2>&1; then
                log_success "✅ Backup service $service for $env: PASSED"
                service_tests_passed=$((service_tests_passed + 1))
            else
                log_error "❌ Backup service $service for $env: FAILED"
            fi
        done
    done
    
    if [ $service_tests_passed -eq $service_tests_total ]; then
        log_success "✅ Backup service operations: PASSED ($service_tests_passed/$service_tests_total)"
        return 0
    else
        log_error "❌ Backup service operations: FAILED ($service_tests_passed/$service_tests_total)"
        return 1
    fi
}

# Test backup list commands
test_backup_list() {
    log_info "Testing backup list commands..."
    
    local list_tests_passed=0
    local list_tests_total=${#TEST_ENVIRONMENTS[@]}
    
    for env in "${TEST_ENVIRONMENTS[@]}"; do
        if make backup-list ENVIRONMENT=$env >/dev/null 2>&1; then
            log_success "✅ Backup list for $env: PASSED"
            list_tests_passed=$((list_tests_passed + 1))
        else
            log_error "❌ Backup list for $env: FAILED"
        fi
    done
    
    if [ $list_tests_passed -eq $list_tests_total ]; then
        log_success "✅ Backup list commands: PASSED ($list_tests_passed/$list_tests_total)"
        return 0
    else
        log_error "❌ Backup list commands: FAILED ($list_tests_passed/$list_tests_total)"
        return 1
    fi
}

# Test backup schedule
test_backup_schedule() {
    log_info "Testing backup schedule..."
    
    if make backup-schedule >/dev/null 2>&1; then
        log_success "✅ Backup schedule: PASSED"
        return 0
    else
        log_error "❌ Backup schedule: FAILED"
        return 1
    fi
}

# Test data retention policies configuration
test_retention_policies_config() {
    log_info "Testing retention policies configuration..."
    
    local config_file="$PROJECT_ROOT/configs/retention-policies.yaml"
    
    if [ -f "$config_file" ]; then
        log_success "✅ Retention policies config file exists"
        
        # Test YAML syntax
        if python3 -c "import yaml; yaml.safe_load(open('$config_file'))" >/dev/null 2>&1; then
            log_success "✅ Retention policies config YAML syntax: PASSED"
        else
            log_error "❌ Retention policies config YAML syntax: FAILED"
            return 1
        fi
        
        # Test required sections
        local required_sections=("environments" "development" "staging" "production" "testing")
        local sections_found=0
        
        for section in "${required_sections[@]}"; do
            if grep -q "$section:" "$config_file"; then
                log_success "✅ Required section found: $section"
                sections_found=$((sections_found + 1))
            else
                log_error "❌ Required section missing: $section"
            fi
        done
        
        if [ $sections_found -eq ${#required_sections[@]} ]; then
            log_success "✅ Retention policies configuration: PASSED"
            return 0
        else
            log_error "❌ Retention policies configuration: FAILED"
            return 1
        fi
    else
        log_error "❌ Retention policies config file not found: $config_file"
        return 1
    fi
}

# Test backup strategies configuration
test_backup_strategies_config() {
    log_info "Testing backup strategies configuration..."
    
    local config_file="$PROJECT_ROOT/configs/backup-strategies.yaml"
    
    if [ -f "$config_file" ]; then
        log_success "✅ Backup strategies config file exists"
        
        # Test YAML syntax
        if python3 -c "import yaml; yaml.safe_load(open('$config_file'))" >/dev/null 2>&1; then
            log_success "✅ Backup strategies config YAML syntax: PASSED"
        else
            log_error "❌ Backup strategies config YAML syntax: FAILED"
            return 1
        fi
        
        # Test required sections
        local required_sections=("environments" "development" "staging" "production" "testing")
        local sections_found=0
        
        for section in "${required_sections[@]}"; do
            if grep -q "$section:" "$config_file"; then
                log_success "✅ Required section found: $section"
                sections_found=$((sections_found + 1))
            else
                log_error "❌ Required section missing: $section"
            fi
        done
        
        if [ $sections_found -eq ${#required_sections[@]} ]; then
            log_success "✅ Backup strategies configuration: PASSED"
            return 0
        else
            log_error "❌ Backup strategies configuration: FAILED"
            return 1
        fi
    else
        log_error "❌ Backup strategies config file not found: $config_file"
        return 1
    fi
}

# Test data management scripts
test_data_management_scripts() {
    log_info "Testing data management scripts..."
    
    local scripts=(
        "scripts/manage-retention.sh"
        "scripts/setup-retention-cron.sh"
        "scripts/manage-backups.sh"
        "scripts/setup-backup-cron.sh"
    )
    
    local scripts_found=0
    local total_scripts=${#scripts[@]}
    
    for script in "${scripts[@]}"; do
        local script_path="$PROJECT_ROOT/$script"
        
        if [ -f "$script_path" ]; then
            log_success "✅ Script found: $script"
            
            # Test script is executable
            if [ -x "$script_path" ]; then
                log_success "✅ Script is executable: $script"
                scripts_found=$((scripts_found + 1))
            else
                log_error "❌ Script is not executable: $script"
            fi
        else
            log_error "❌ Script not found: $script"
        fi
    done
    
    if [ $scripts_found -eq $total_scripts ]; then
        log_success "✅ Data management scripts: PASSED ($scripts_found/$total_scripts)"
        return 0
    else
        log_error "❌ Data management scripts: FAILED ($scripts_found/$total_scripts)"
        return 1
    fi
}

# Test data retention functionality
test_data_retention_functionality() {
    log_info "Testing data retention functionality..."
    
    # Test retention management script
    if [ -x "$PROJECT_ROOT/scripts/manage-retention.sh" ]; then
        # Test status command
        if "$PROJECT_ROOT/scripts/manage-retention.sh" status development >/dev/null 2>&1; then
            log_success "✅ Retention management status: PASSED"
        else
            log_error "❌ Retention management status: FAILED"
            return 1
        fi
        
        # Test cleanup command (dry run)
        if "$PROJECT_ROOT/scripts/manage-retention.sh" cleanup development >/dev/null 2>&1; then
            log_success "✅ Retention management cleanup: PASSED"
        else
            log_error "❌ Retention management cleanup: FAILED"
            return 1
        fi
    else
        log_error "❌ Retention management script not found or not executable"
        return 1
    fi
    
    log_success "✅ Data retention functionality: PASSED"
    return 0
}

# Test backup functionality
test_backup_functionality() {
    log_info "Testing backup functionality..."
    
    # Test backup management script
    if [ -x "$PROJECT_ROOT/scripts/manage-backups.sh" ]; then
        # Test status command
        if "$PROJECT_ROOT/scripts/manage-backups.sh" status development >/dev/null 2>&1; then
            log_success "✅ Backup management status: PASSED"
        else
            log_error "❌ Backup management status: FAILED"
            return 1
        fi
        
        # Test backup command
        if "$PROJECT_ROOT/scripts/manage-backups.sh" backup development >/dev/null 2>&1; then
            log_success "✅ Backup management backup: PASSED"
        else
            log_error "❌ Backup management backup: FAILED"
            return 1
        fi
    else
        log_error "❌ Backup management script not found or not executable"
        return 1
    fi
    
    log_success "✅ Backup functionality: PASSED"
    return 0
}

# Main test execution
main() {
    log_info "💾 Starting Data Operations Test Suite"
    log_info "======================================"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Test configuration files
    run_test "Retention Policies Configuration" "test_retention_policies_config"
    run_test "Backup Strategies Configuration" "test_backup_strategies_config"
    
    # Test data management scripts
    run_test "Data Management Scripts" "test_data_management_scripts"
    
    # Test retention operations
    run_test "Retention Status Commands" "test_retention_status"
    run_test "Retention Cleanup (Dry Run)" "test_retention_cleanup_dry_run"
    run_test "Retention Test Commands" "test_retention_test"
    run_test "Retention Schedule" "test_retention_schedule"
    
    # Test backup operations
    run_test "Backup Status Commands" "test_backup_status"
    run_test "Backup Full Operations" "test_backup_full"
    run_test "Backup Service Operations" "test_backup_service"
    run_test "Backup List Commands" "test_backup_list"
    run_test "Backup Schedule" "test_backup_schedule"
    
    # Test functionality
    run_test "Data Retention Functionality" "test_data_retention_functionality"
    run_test "Backup Functionality" "test_backup_functionality"
    
    # Print test summary
    log_info "======================================"
    log_info "💾 Data Operations Test Suite Complete"
    log_info "======================================"
    log_info "Total Tests: $TESTS_TOTAL"
    log_success "Passed: $TESTS_PASSED"
    if [ $TESTS_FAILED -gt 0 ]; then
        log_error "Failed: $TESTS_FAILED"
    else
        log_info "Failed: $TESTS_FAILED"
    fi
    
    # Calculate success rate
    local success_rate=0
    if [ $TESTS_TOTAL -gt 0 ]; then
        success_rate=$((TESTS_PASSED * 100 / TESTS_TOTAL))
    fi
    
    log_info "Success Rate: $success_rate%"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log_success "🎉 All tests passed!"
        exit 0
    else
        log_error "❌ Some tests failed!"
        exit 1
    fi
}

# Help function
show_help() {
    cat << EOF
Data Operations Test Suite

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -e, --environments      Test specific environments (comma-separated)
    -s, --services          Test specific services (comma-separated)
    --skip-backup           Skip backup tests
    --skip-retention        Skip retention tests
    --skip-config           Skip configuration tests

Examples:
    $0                      # Run all tests
    $0 --skip-backup        # Skip backup tests
    $0 -e development,staging # Test only development and staging environments
    $0 -s postgres,redis    # Test only postgres and redis services

EOF
}

# Parse command line arguments
VERBOSE=false
SKIP_BACKUP=false
SKIP_RETENTION=false
SKIP_CONFIG=false
CUSTOM_ENVIRONMENTS=""
CUSTOM_SERVICES=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -e|--environments)
            CUSTOM_ENVIRONMENTS="$2"
            shift 2
            ;;
        -s|--services)
            CUSTOM_SERVICES="$2"
            shift 2
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-retention)
            SKIP_RETENTION=true
            shift
            ;;
        --skip-config)
            SKIP_CONFIG=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Override environments if specified
if [ -n "$CUSTOM_ENVIRONMENTS" ]; then
    IFS=',' read -ra TEST_ENVIRONMENTS <<< "$CUSTOM_ENVIRONMENTS"
fi

# Override services if specified
if [ -n "$CUSTOM_SERVICES" ]; then
    IFS=',' read -ra TEST_SERVICES <<< "$CUSTOM_SERVICES"
fi

# Run main function
main
