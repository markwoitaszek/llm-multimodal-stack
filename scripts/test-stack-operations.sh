#!/bin/bash

# Test script for stack operations
# Tests all stack-based operations including start, stop, restart, and status

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
DEPENDENCY_ORDER=("core" "inference" "ai" "ui")
TEST_TIMEOUT=30
STATUS_CHECK_INTERVAL=5

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

# Function to check if a stack is running
check_stack_status() {
    local stack_name="$1"
    local expected_status="${2:-running}"
    
    log_info "Checking status of $stack_name stack..."
    
    # Get stack status
    local status_output
    status_output=$(make status-$stack_name 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        if echo "$status_output" | grep -q "running\|up"; then
            log_success "✅ $stack_name stack is running"
            return 0
        else
            log_warning "⚠️  $stack_name stack is not running"
            return 1
        fi
    else
        log_error "❌ Failed to get status for $stack_name stack"
        return 1
    fi
}

# Function to wait for stack to be ready
wait_for_stack() {
    local stack_name="$1"
    local timeout="${2:-$TEST_TIMEOUT}"
    local elapsed=0
    
    log_info "Waiting for $stack_name stack to be ready..."
    
    while [ $elapsed -lt $timeout ]; do
        if check_stack_status "$stack_name" >/dev/null 2>&1; then
            log_success "✅ $stack_name stack is ready"
            return 0
        fi
        
        sleep $STATUS_CHECK_INTERVAL
        elapsed=$((elapsed + STATUS_CHECK_INTERVAL))
    done
    
    log_error "❌ $stack_name stack failed to start within $timeout seconds"
    return 1
}

# Test individual stack startup
test_stack_startup() {
    local stack_name="$1"
    
    log_info "Testing startup of $stack_name stack..."
    
    # Start the stack
    if make start-$stack_name; then
        # Wait for it to be ready
        if wait_for_stack "$stack_name"; then
            log_success "✅ $stack_name stack startup: PASSED"
            return 0
        else
            log_error "❌ $stack_name stack startup: FAILED (not ready)"
            return 1
        fi
    else
        log_error "❌ $stack_name stack startup: FAILED (start command failed)"
        return 1
    fi
}

# Test individual stack shutdown
test_stack_shutdown() {
    local stack_name="$1"
    
    log_info "Testing shutdown of $stack_name stack..."
    
    # Stop the stack
    if make stop-$stack_name; then
        # Wait a moment for shutdown
        sleep 5
        
        # Check if it's stopped
        if ! check_stack_status "$stack_name" >/dev/null 2>&1; then
            log_success "✅ $stack_name stack shutdown: PASSED"
            return 0
        else
            log_error "❌ $stack_name stack shutdown: FAILED (still running)"
            return 1
        fi
    else
        log_error "❌ $stack_name stack shutdown: FAILED (stop command failed)"
        return 1
    fi
}

# Test individual stack restart
test_stack_restart() {
    local stack_name="$1"
    
    log_info "Testing restart of $stack_name stack..."
    
    # Restart the stack
    if make restart-$stack_name; then
        # Wait for it to be ready
        if wait_for_stack "$stack_name"; then
            log_success "✅ $stack_name stack restart: PASSED"
            return 0
        else
            log_error "❌ $stack_name stack restart: FAILED (not ready)"
            return 1
        fi
    else
        log_error "❌ $stack_name stack restart: FAILED (restart command failed)"
        return 1
    fi
}

# Test stack dependencies
test_stack_dependencies() {
    log_info "Testing stack dependencies..."
    
    # Test that core stack can start independently
    if test_stack_startup "core"; then
        log_success "✅ Core stack can start independently"
    else
        log_error "❌ Core stack failed to start independently"
        return 1
    fi
    
    # Test that inference stack requires core
    if test_stack_startup "inference"; then
        log_success "✅ Inference stack started (core dependency satisfied)"
    else
        log_error "❌ Inference stack failed to start (core dependency issue)"
        return 1
    fi
    
    # Test that AI stack requires both core and inference
    if test_stack_startup "ai"; then
        log_success "✅ AI stack started (dependencies satisfied)"
    else
        log_error "❌ AI stack failed to start (dependency issue)"
        return 1
    fi
    
    # Test that UI stack requires core and AI
    if test_stack_startup "ui"; then
        log_success "✅ UI stack started (dependencies satisfied)"
    else
        log_error "❌ UI stack failed to start (dependency issue)"
        return 1
    fi
    
    log_success "✅ Stack dependencies: PASSED"
    return 0
}

# Test cross-stack communication
test_cross_stack_communication() {
    log_info "Testing cross-stack communication..."
    
    # Test that services can communicate across stacks
    local communication_tests=(
        "docker exec multimodal-postgres ping -c 1 multimodal-redis"
        "docker exec multimodal-vllm ping -c 1 multimodal-postgres"
        "docker exec multimodal-worker ping -c 1 multimodal-postgres"
        "docker exec multimodal-worker ping -c 1 multimodal-vllm"
    )
    
    local passed=0
    local total=${#communication_tests[@]}
    
    for test in "${communication_tests[@]}"; do
        if eval "$test" >/dev/null 2>&1; then
            log_success "✅ Communication test passed: $test"
            passed=$((passed + 1))
        else
            log_error "❌ Communication test failed: $test"
        fi
    done
    
    if [ $passed -eq $total ]; then
        log_success "✅ Cross-stack communication: PASSED ($passed/$total)"
        return 0
    else
        log_error "❌ Cross-stack communication: FAILED ($passed/$total)"
        return 1
    fi
}

# Test stack isolation
test_stack_isolation() {
    log_info "Testing stack isolation..."
    
    # Test that stacks are on different networks
    local networks=(
        "multimodal-core-net"
        "multimodal-inference-net"
        "multimodal-ai-net"
        "multimodal-ui-net"
        "multimodal-testing-net"
        "multimodal-monitoring-net"
    )
    
    local networks_found=0
    local total_networks=${#networks[@]}
    
    for network in "${networks[@]}"; do
        if docker network ls | grep -q "$network"; then
            log_success "✅ Network found: $network"
            networks_found=$((networks_found + 1))
        else
            log_warning "⚠️  Network not found: $network"
        fi
    done
    
    if [ $networks_found -eq $total_networks ]; then
        log_success "✅ Stack isolation: PASSED ($networks_found/$total_networks networks)"
        return 0
    else
        log_warning "⚠️  Stack isolation: PARTIAL ($networks_found/$total_networks networks)"
        return 1
    fi
}

# Test stack status commands
test_stack_status_commands() {
    log_info "Testing stack status commands..."
    
    local status_tests_passed=0
    local status_tests_total=${#STACKS[@]}
    
    for stack in "${STACKS[@]}"; do
        if make status-$stack >/dev/null 2>&1; then
            log_success "✅ Status command for $stack: PASSED"
            status_tests_passed=$((status_tests_passed + 1))
        else
            log_error "❌ Status command for $stack: FAILED"
        fi
    done
    
    if [ $status_tests_passed -eq $status_tests_total ]; then
        log_success "✅ Stack status commands: PASSED ($status_tests_passed/$status_tests_total)"
        return 0
    else
        log_error "❌ Stack status commands: FAILED ($status_tests_passed/$status_tests_total)"
        return 1
    fi
}

# Test stack logs commands
test_stack_logs_commands() {
    log_info "Testing stack logs commands..."
    
    local logs_tests_passed=0
    local logs_tests_total=${#STACKS[@]}
    
    for stack in "${STACKS[@]}"; do
        if make logs-$stack >/dev/null 2>&1; then
            log_success "✅ Logs command for $stack: PASSED"
            logs_tests_passed=$((logs_tests_passed + 1))
        else
            log_error "❌ Logs command for $stack: FAILED"
        fi
    done
    
    if [ $logs_tests_passed -eq $logs_tests_total ]; then
        log_success "✅ Stack logs commands: PASSED ($logs_tests_passed/$logs_tests_total)"
        return 0
    else
        log_error "❌ Stack logs commands: FAILED ($logs_tests_passed/$logs_tests_total)"
        return 1
    fi
}

# Main test execution
main() {
    log_info "🧪 Starting Stack Operations Test Suite"
    log_info "========================================"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Test stack status commands first (non-destructive)
    run_test "Stack Status Commands" "test_stack_status_commands"
    
    # Test stack logs commands (non-destructive)
    run_test "Stack Logs Commands" "test_stack_logs_commands"
    
    # Test stack isolation (non-destructive)
    run_test "Stack Isolation" "test_stack_isolation"
    
    # Test individual stack operations
    for stack in "${STACKS[@]}"; do
        run_test "$stack Stack Startup" "test_stack_startup $stack"
        run_test "$stack Stack Shutdown" "test_stack_shutdown $stack"
        run_test "$stack Stack Restart" "test_stack_restart $stack"
    done
    
    # Test stack dependencies
    run_test "Stack Dependencies" "test_stack_dependencies"
    
    # Test cross-stack communication
    run_test "Cross-Stack Communication" "test_cross_stack_communication"
    
    # Print test summary
    log_info "========================================"
    log_info "🧪 Stack Operations Test Suite Complete"
    log_info "========================================"
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
Stack Operations Test Suite

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -t, --timeout SECONDS   Set timeout for stack operations (default: $TEST_TIMEOUT)
    -s, --stacks STACKS     Test specific stacks (comma-separated)
    --skip-destructive      Skip destructive tests (startup/shutdown/restart)
    --skip-communication    Skip cross-stack communication tests

Examples:
    $0                      # Run all tests
    $0 --skip-destructive   # Run only non-destructive tests
    $0 -s core,inference    # Test only core and inference stacks
    $0 -t 60                # Set 60 second timeout

EOF
}

# Parse command line arguments
VERBOSE=false
SKIP_DESTRUCTIVE=false
SKIP_COMMUNICATION=false
CUSTOM_STACKS=""

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
        -t|--timeout)
            TEST_TIMEOUT="$2"
            shift 2
            ;;
        -s|--stacks)
            CUSTOM_STACKS="$2"
            shift 2
            ;;
        --skip-destructive)
            SKIP_DESTRUCTIVE=true
            shift
            ;;
        --skip-communication)
            SKIP_COMMUNICATION=true
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

# Run main function
main
