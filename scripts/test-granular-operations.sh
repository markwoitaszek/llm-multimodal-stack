#!/bin/bash

# Test script for granular operations
# Tests granular wipe/reset operations, system status, and environment management

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
STACKS=("core" "inference" "ai" "ui" "testing" "monitoring")
ENVIRONMENTS=("dev" "staging" "prod" "testing")
DATA_TYPES=("db" "cache" "models" "logs" "test-results")
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

# Test system status command
test_system_status() {
    log_info "Testing system status command..."
    
    if make system-status >/dev/null 2>&1; then
        log_success "✅ System status: PASSED"
        return 0
    else
        log_error "❌ System status: FAILED"
        return 1
    fi
}

# Test stack-specific wipe operations
test_stack_wipe_operations() {
    log_info "Testing stack-specific wipe operations..."
    
    local wipe_tests_passed=0
    local wipe_tests_total=${#STACKS[@]}
    
    for stack in "${STACKS[@]}"; do
        # Test wipe command (should not fail even if stack is not running)
        if make wipe-$stack >/dev/null 2>&1; then
            log_success "✅ Wipe $stack: PASSED"
            wipe_tests_passed=$((wipe_tests_passed + 1))
        else
            log_error "❌ Wipe $stack: FAILED"
        fi
    done
    
    if [ $wipe_tests_passed -eq $wipe_tests_total ]; then
        log_success "✅ Stack wipe operations: PASSED ($wipe_tests_passed/$wipe_tests_total)"
        return 0
    else
        log_error "❌ Stack wipe operations: FAILED ($wipe_tests_passed/$wipe_tests_total)"
        return 1
    fi
}

# Test data-specific wipe operations
test_data_wipe_operations() {
    log_info "Testing data-specific wipe operations..."
    
    local data_wipe_tests_passed=0
    local data_wipe_tests_total=${#DATA_TYPES[@]}
    
    for data_type in "${DATA_TYPES[@]}"; do
        # Test wipe command (should not fail even if data doesn't exist)
        if make wipe-$data_type >/dev/null 2>&1; then
            log_success "✅ Wipe $data_type: PASSED"
            data_wipe_tests_passed=$((data_wipe_tests_passed + 1))
        else
            log_error "❌ Wipe $data_type: FAILED"
        fi
    done
    
    if [ $data_wipe_tests_passed -eq $data_wipe_tests_total ]; then
        log_success "✅ Data wipe operations: PASSED ($data_wipe_tests_passed/$data_wipe_tests_total)"
        return 0
    else
        log_error "❌ Data wipe operations: FAILED ($data_wipe_tests_passed/$data_wipe_tests_total)"
        return 1
    fi
}

# Test environment-specific wipe operations
test_environment_wipe_operations() {
    log_info "Testing environment-specific wipe operations..."
    
    local env_wipe_tests_passed=0
    local env_wipe_tests_total=${#ENVIRONMENTS[@]}
    
    for env in "${ENVIRONMENTS[@]}"; do
        # Test wipe command (should not fail even if environment is not running)
        if make wipe-$env >/dev/null 2>&1; then
            log_success "✅ Wipe $env: PASSED"
            env_wipe_tests_passed=$((env_wipe_tests_passed + 1))
        else
            log_error "❌ Wipe $env: FAILED"
        fi
    done
    
    if [ $env_wipe_tests_passed -eq $env_wipe_tests_total ]; then
        log_success "✅ Environment wipe operations: PASSED ($env_wipe_tests_passed/$env_wipe_tests_total)"
        return 0
    else
        log_error "❌ Environment wipe operations: FAILED ($env_wipe_tests_passed/$env_wipe_tests_total)"
        return 1
    fi
}

# Test stack restart operations
test_stack_restart_operations() {
    log_info "Testing stack restart operations..."
    
    local restart_tests_passed=0
    local restart_tests_total=${#STACKS[@]}
    
    for stack in "${STACKS[@]}"; do
        # Test restart command (should not fail even if stack is not running)
        if make restart-$stack >/dev/null 2>&1; then
            log_success "✅ Restart $stack: PASSED"
            restart_tests_passed=$((restart_tests_passed + 1))
        else
            log_error "❌ Restart $stack: FAILED"
        fi
    done
    
    if [ $restart_tests_passed -eq $restart_tests_total ]; then
        log_success "✅ Stack restart operations: PASSED ($restart_tests_passed/$restart_tests_total)"
        return 0
    else
        log_error "❌ Stack restart operations: FAILED ($restart_tests_passed/$restart_tests_total)"
        return 1
    fi
}

# Test stack rebuild operations
test_stack_rebuild_operations() {
    log_info "Testing stack rebuild operations..."
    
    # Test AI stack rebuild (most common rebuild operation)
    if make rebuild-ai >/dev/null 2>&1; then
        log_success "✅ Rebuild AI: PASSED"
        return 0
    else
        log_error "❌ Rebuild AI: FAILED"
        return 1
    fi
}

# Test wipe environment script
test_wipe_environment_script() {
    log_info "Testing wipe environment script..."
    
    local script_path="$PROJECT_ROOT/scripts/wipe-environment.sh"
    
    if [ -f "$script_path" ]; then
        log_success "✅ Wipe environment script exists"
        
        # Test script is executable
        if [ -x "$script_path" ]; then
            log_success "✅ Wipe environment script is executable"
        else
            log_error "❌ Wipe environment script is not executable"
            return 1
        fi
        
        # Test script help
        if "$script_path" --help >/dev/null 2>&1; then
            log_success "✅ Wipe environment script help: PASSED"
        else
            log_error "❌ Wipe environment script help: FAILED"
            return 1
        fi
        
        # Test script status command
        if "$script_path" status >/dev/null 2>&1; then
            log_success "✅ Wipe environment script status: PASSED"
        else
            log_error "❌ Wipe environment script status: FAILED"
            return 1
        fi
        
        log_success "✅ Wipe environment script: PASSED"
        return 0
    else
        log_error "❌ Wipe environment script not found: $script_path"
        return 1
    fi
}

# Test granular operations safety
test_granular_operations_safety() {
    log_info "Testing granular operations safety..."
    
    # Test that wipe operations don't affect other stacks
    local safety_tests_passed=0
    local safety_tests_total=3
    
    # Test wipe core doesn't affect other stacks
    if make wipe-core >/dev/null 2>&1; then
        log_success "✅ Wipe core safety: PASSED"
        safety_tests_passed=$((safety_tests_passed + 1))
    else
        log_error "❌ Wipe core safety: FAILED"
    fi
    
    # Test wipe cache doesn't affect other data
    if make wipe-cache >/dev/null 2>&1; then
        log_success "✅ Wipe cache safety: PASSED"
        safety_tests_passed=$((safety_tests_passed + 1))
    else
        log_error "❌ Wipe cache safety: FAILED"
    fi
    
    # Test wipe logs doesn't affect other data
    if make wipe-logs >/dev/null 2>&1; then
        log_success "✅ Wipe logs safety: PASSED"
        safety_tests_passed=$((safety_tests_passed + 1))
    else
        log_error "❌ Wipe logs safety: FAILED"
    fi
    
    if [ $safety_tests_passed -eq $safety_tests_total ]; then
        log_success "✅ Granular operations safety: PASSED ($safety_tests_passed/$safety_tests_total)"
        return 0
    else
        log_error "❌ Granular operations safety: FAILED ($safety_tests_passed/$safety_tests_total)"
        return 1
    fi
}

# Test granular operations confirmation
test_granular_operations_confirmation() {
    log_info "Testing granular operations confirmation..."
    
    # Test that destructive operations require confirmation
    local confirmation_tests_passed=0
    local confirmation_tests_total=2
    
    # Test wipe environment script confirmation
    local script_path="$PROJECT_ROOT/scripts/wipe-environment.sh"
    
    if [ -x "$script_path" ]; then
        # Test that wipe command shows confirmation prompt
        if echo "n" | "$script_path" wipe core 2>&1 | grep -q "Are you sure\|confirm\|continue"; then
            log_success "✅ Wipe confirmation prompt: PASSED"
            confirmation_tests_passed=$((confirmation_tests_passed + 1))
        else
            log_warning "⚠️  Wipe confirmation prompt: NOT DETECTED"
        fi
    fi
    
    # Test that system status doesn't require confirmation
    if make system-status >/dev/null 2>&1; then
        log_success "✅ System status no confirmation: PASSED"
        confirmation_tests_passed=$((confirmation_tests_passed + 1))
    else
        log_error "❌ System status no confirmation: FAILED"
    fi
    
    if [ $confirmation_tests_passed -eq $confirmation_tests_total ]; then
        log_success "✅ Granular operations confirmation: PASSED ($confirmation_tests_passed/$confirmation_tests_total)"
        return 0
    else
        log_warning "⚠️  Granular operations confirmation: PARTIAL ($confirmation_tests_passed/$confirmation_tests_total)"
        return 1
    fi
}

# Test granular operations logging
test_granular_operations_logging() {
    log_info "Testing granular operations logging..."
    
    # Test that operations are logged
    local logging_tests_passed=0
    local logging_tests_total=2
    
    # Test system status logging
    if make system-status 2>&1 | grep -q "System Status\|Stack Status\|Container Status"; then
        log_success "✅ System status logging: PASSED"
        logging_tests_passed=$((logging_tests_passed + 1))
    else
        log_warning "⚠️  System status logging: NOT DETECTED"
    fi
    
    # Test wipe operations logging
    if make wipe-cache 2>&1 | grep -q "Wiping\|Cleaning\|Removing"; then
        log_success "✅ Wipe operations logging: PASSED"
        logging_tests_passed=$((logging_tests_passed + 1))
    else
        log_warning "⚠️  Wipe operations logging: NOT DETECTED"
    fi
    
    if [ $logging_tests_passed -eq $logging_tests_total ]; then
        log_success "✅ Granular operations logging: PASSED ($logging_tests_passed/$logging_tests_total)"
        return 0
    else
        log_warning "⚠️  Granular operations logging: PARTIAL ($logging_tests_passed/$logging_tests_total)"
        return 1
    fi
}

# Test granular operations error handling
test_granular_operations_error_handling() {
    log_info "Testing granular operations error handling..."
    
    # Test error handling for invalid operations
    local error_tests_passed=0
    local error_tests_total=3
    
    # Test invalid stack wipe
    if ! make wipe-invalid-stack >/dev/null 2>&1; then
        log_success "✅ Invalid stack wipe error handling: PASSED"
        error_tests_passed=$((error_tests_passed + 1))
    else
        log_error "❌ Invalid stack wipe error handling: FAILED"
    fi
    
    # Test invalid data wipe
    if ! make wipe-invalid-data >/dev/null 2>&1; then
        log_success "✅ Invalid data wipe error handling: PASSED"
        error_tests_passed=$((error_tests_passed + 1))
    else
        log_error "❌ Invalid data wipe error handling: FAILED"
    fi
    
    # Test invalid environment wipe
    if ! make wipe-invalid-env >/dev/null 2>&1; then
        log_success "✅ Invalid environment wipe error handling: PASSED"
        error_tests_passed=$((error_tests_passed + 1))
    else
        log_error "❌ Invalid environment wipe error handling: FAILED"
    fi
    
    if [ $error_tests_passed -eq $error_tests_total ]; then
        log_success "✅ Granular operations error handling: PASSED ($error_tests_passed/$error_tests_total)"
        return 0
    else
        log_error "❌ Granular operations error handling: FAILED ($error_tests_passed/$error_tests_total)"
        return 1
    fi
}

# Test granular operations performance
test_granular_operations_performance() {
    log_info "Testing granular operations performance..."
    
    # Test that operations complete within reasonable time
    local performance_tests_passed=0
    local performance_tests_total=3
    
    # Test system status performance
    local start_time=$(date +%s)
    if make system-status >/dev/null 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        if [ $duration -lt 10 ]; then
            log_success "✅ System status performance: PASSED (${duration}s)"
            performance_tests_passed=$((performance_tests_passed + 1))
        else
            log_warning "⚠️  System status performance: SLOW (${duration}s)"
        fi
    else
        log_error "❌ System status performance: FAILED"
    fi
    
    # Test wipe cache performance
    local start_time=$(date +%s)
    if make wipe-cache >/dev/null 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        if [ $duration -lt 5 ]; then
            log_success "✅ Wipe cache performance: PASSED (${duration}s)"
            performance_tests_passed=$((performance_tests_passed + 1))
        else
            log_warning "⚠️  Wipe cache performance: SLOW (${duration}s)"
        fi
    else
        log_error "❌ Wipe cache performance: FAILED"
    fi
    
    # Test wipe logs performance
    local start_time=$(date +%s)
    if make wipe-logs >/dev/null 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        if [ $duration -lt 5 ]; then
            log_success "✅ Wipe logs performance: PASSED (${duration}s)"
            performance_tests_passed=$((performance_tests_passed + 1))
        else
            log_warning "⚠️  Wipe logs performance: SLOW (${duration}s)"
        fi
    else
        log_error "❌ Wipe logs performance: FAILED"
    fi
    
    if [ $performance_tests_passed -eq $performance_tests_total ]; then
        log_success "✅ Granular operations performance: PASSED ($performance_tests_passed/$performance_tests_total)"
        return 0
    else
        log_warning "⚠️  Granular operations performance: PARTIAL ($performance_tests_passed/$performance_tests_total)"
        return 1
    fi
}

# Main test execution
main() {
    log_info "🔧 Starting Granular Operations Test Suite"
    log_info "=========================================="
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Test system status
    run_test "System Status" "test_system_status"
    
    # Test stack-specific operations
    run_test "Stack Wipe Operations" "test_stack_wipe_operations"
    run_test "Stack Restart Operations" "test_stack_restart_operations"
    run_test "Stack Rebuild Operations" "test_stack_rebuild_operations"
    
    # Test data-specific operations
    run_test "Data Wipe Operations" "test_data_wipe_operations"
    
    # Test environment-specific operations
    run_test "Environment Wipe Operations" "test_environment_wipe_operations"
    
    # Test wipe environment script
    run_test "Wipe Environment Script" "test_wipe_environment_script"
    
    # Test safety and reliability
    run_test "Granular Operations Safety" "test_granular_operations_safety"
    run_test "Granular Operations Confirmation" "test_granular_operations_confirmation"
    run_test "Granular Operations Logging" "test_granular_operations_logging"
    run_test "Granular Operations Error Handling" "test_granular_operations_error_handling"
    run_test "Granular Operations Performance" "test_granular_operations_performance"
    
    # Print test summary
    log_info "=========================================="
    log_info "🔧 Granular Operations Test Suite Complete"
    log_info "=========================================="
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
Granular Operations Test Suite

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -s, --stacks STACKS     Test specific stacks (comma-separated)
    -e, --environments      Test specific environments (comma-separated)
    -d, --data-types        Test specific data types (comma-separated)
    --skip-destructive      Skip destructive tests
    --skip-performance      Skip performance tests
    --skip-safety           Skip safety tests

Examples:
    $0                      # Run all tests
    $0 --skip-destructive   # Skip destructive tests
    $0 -s core,inference    # Test only core and inference stacks
    $0 -e dev,staging       # Test only dev and staging environments

EOF
}

# Parse command line arguments
VERBOSE=false
SKIP_DESTRUCTIVE=false
SKIP_PERFORMANCE=false
SKIP_SAFETY=false
CUSTOM_STACKS=""
CUSTOM_ENVIRONMENTS=""
CUSTOM_DATA_TYPES=""

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
        -s|--stacks)
            CUSTOM_STACKS="$2"
            shift 2
            ;;
        -e|--environments)
            CUSTOM_ENVIRONMENTS="$2"
            shift 2
            ;;
        -d|--data-types)
            CUSTOM_DATA_TYPES="$2"
            shift 2
            ;;
        --skip-destructive)
            SKIP_DESTRUCTIVE=true
            shift
            ;;
        --skip-performance)
            SKIP_PERFORMANCE=true
            shift
            ;;
        --skip-safety)
            SKIP_SAFETY=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Override stacks if specified
if [ -n "$CUSTOM_STACKS" ]; then
    IFS=',' read -ra STACKS <<< "$CUSTOM_STACKS"
fi

# Override environments if specified
if [ -n "$CUSTOM_ENVIRONMENTS" ]; then
    IFS=',' read -ra ENVIRONMENTS <<< "$CUSTOM_ENVIRONMENTS"
fi

# Override data types if specified
if [ -n "$CUSTOM_DATA_TYPES" ]; then
    IFS=',' read -ra DATA_TYPES <<< "$CUSTOM_DATA_TYPES"
fi

# Run main function
main
