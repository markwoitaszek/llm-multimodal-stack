#!/bin/bash

# Comprehensive test runner for all enterprise features
# Orchestrates testing of stack operations, network management, data operations, and granular operations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Test configuration
TEST_SUITES=(
    "stack-operations"
    "network-operations"
    "data-operations"
    "granular-operations"
)

# Test result tracking
TOTAL_TESTS_PASSED=0
TOTAL_TESTS_FAILED=0
TOTAL_TESTS_TOTAL=0
SUITE_RESULTS=()

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

log_suite() {
    echo -e "${PURPLE}[SUITE]${NC} $1"
}

log_header() {
    echo -e "${CYAN}[HEADER]${NC} $1"
}

# Function to run a test suite
run_test_suite() {
    local suite_name="$1"
    local suite_script="$2"
    local suite_args="$3"
    
    log_suite "Starting $suite_name test suite..."
    log_info "Command: $suite_script $suite_args"
    
    local start_time=$(date +%s)
    
    if eval "$suite_script $suite_args"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        log_success "✅ $suite_name test suite: PASSED (${duration}s)"
        SUITE_RESULTS+=("$suite_name:PASSED:$duration")
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        log_error "❌ $suite_name test suite: FAILED (${duration}s)"
        SUITE_RESULTS+=("$suite_name:FAILED:$duration")
        return 1
    fi
}

# Function to run individual test suites
run_stack_operations_tests() {
    local args="$1"
    run_test_suite "Stack Operations" "$PROJECT_ROOT/scripts/test-stack-operations.sh" "$args"
}

run_network_operations_tests() {
    local args="$1"
    run_test_suite "Network Operations" "$PROJECT_ROOT/scripts/test-network-operations.sh" "$args"
}

run_data_operations_tests() {
    local args="$1"
    run_test_suite "Data Operations" "$PROJECT_ROOT/scripts/test-data-operations.sh" "$args"
}

run_granular_operations_tests() {
    local args="$1"
    run_test_suite "Granular Operations" "$PROJECT_ROOT/scripts/test-granular-operations.sh" "$args"
}

# Function to run all test suites
run_all_test_suites() {
    log_header "🧪 Running All Test Suites"
    log_info "========================================"
    
    local suites_passed=0
    local suites_failed=0
    local total_suites=${#TEST_SUITES[@]}
    
    for suite in "${TEST_SUITES[@]}"; do
        case $suite in
            "stack-operations")
                if run_stack_operations_tests "$@"; then
                    suites_passed=$((suites_passed + 1))
                else
                    suites_failed=$((suites_failed + 1))
                fi
                ;;
            "network-operations")
                if run_network_operations_tests "$@"; then
                    suites_passed=$((suites_passed + 1))
                else
                    suites_failed=$((suites_failed + 1))
                fi
                ;;
            "data-operations")
                if run_data_operations_tests "$@"; then
                    suites_passed=$((suites_passed + 1))
                else
                    suites_failed=$((suites_failed + 1))
                fi
                ;;
            "granular-operations")
                if run_granular_operations_tests "$@"; then
                    suites_passed=$((suites_passed + 1))
                else
                    suites_failed=$((suites_failed + 1))
                fi
                ;;
        esac
        
        # Add separator between test suites
        echo ""
        log_info "----------------------------------------"
        echo ""
    done
    
    log_info "========================================"
    log_info "🧪 All Test Suites Complete"
    log_info "========================================"
    log_info "Total Suites: $total_suites"
    log_success "Passed: $suites_passed"
    if [ $suites_failed -gt 0 ]; then
        log_error "Failed: $suites_failed"
    else
        log_info "Failed: $suites_failed"
    fi
    
    # Calculate success rate
    local success_rate=0
    if [ $total_suites -gt 0 ]; then
        success_rate=$((suites_passed * 100 / total_suites))
    fi
    
    log_info "Success Rate: $success_rate%"
    
    if [ $suites_failed -eq 0 ]; then
        log_success "🎉 All test suites passed!"
        return 0
    else
        log_error "❌ Some test suites failed!"
        return 1
    fi
}

# Function to run specific test suite
run_specific_test_suite() {
    local suite_name="$1"
    shift
    local args="$@"
    
    log_header "🧪 Running $suite_name Test Suite"
    log_info "========================================"
    
    case $suite_name in
        "stack-operations")
            run_stack_operations_tests "$args"
            ;;
        "network-operations")
            run_network_operations_tests "$args"
            ;;
        "data-operations")
            run_data_operations_tests "$args"
            ;;
        "granular-operations")
            run_granular_operations_tests "$args"
            ;;
        *)
            log_error "Unknown test suite: $suite_name"
            log_info "Available test suites: ${TEST_SUITES[*]}"
            return 1
            ;;
    esac
}

# Function to generate test report
generate_test_report() {
    local report_file="$PROJECT_ROOT/test-results/comprehensive-test-report-$(date +%Y%m%d-%H%M%S).md"
    
    log_info "Generating test report: $report_file"
    
    # Create test-results directory if it doesn't exist
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" << EOF
# Comprehensive Test Report

**Generated:** $(date)
**Project:** LLM Multimodal Stack
**Test Runner:** test-comprehensive.sh

## Test Suite Results

EOF
    
    for result in "${SUITE_RESULTS[@]}"; do
        local suite_name="${result%%:*}"
        local status="${result#*:}"
        status="${status%%:*}"
        local duration="${result##*:}"
        
        echo "### $suite_name" >> "$report_file"
        echo "" >> "$report_file"
        echo "- **Status:** $status" >> "$report_file"
        echo "- **Duration:** ${duration}s" >> "$report_file"
        echo "" >> "$report_file"
    done
    
    cat >> "$report_file" << EOF

## Summary

- **Total Suites:** ${#SUITE_RESULTS[@]}
- **Passed:** $(echo "${SUITE_RESULTS[@]}" | tr ' ' '\n' | grep -c "PASSED")
- **Failed:** $(echo "${SUITE_RESULTS[@]}" | tr ' ' '\n' | grep -c "FAILED")
- **Success Rate:** $(( $(echo "${SUITE_RESULTS[@]}" | tr ' ' '\n' | grep -c "PASSED") * 100 / ${#SUITE_RESULTS[@]} ))%

## Test Environment

- **OS:** $(uname -s)
- **Architecture:** $(uname -m)
- **Docker Version:** $(docker --version 2>/dev/null || echo "Not available")
- **Make Version:** $(make --version 2>/dev/null | head -n1 || echo "Not available")

## Test Configuration

- **Test Suites:** ${TEST_SUITES[*]}
- **Project Root:** $PROJECT_ROOT
- **Script Directory:** $SCRIPT_DIR

EOF
    
    log_success "✅ Test report generated: $report_file"
}

# Function to run quick tests (non-destructive)
run_quick_tests() {
    log_header "🚀 Running Quick Tests (Non-Destructive)"
    log_info "========================================"
    
    local quick_suites=(
        "stack-operations --skip-destructive"
        "network-operations --skip-connectivity"
        "data-operations --skip-backup"
        "granular-operations --skip-destructive"
    )
    
    local quick_passed=0
    local quick_failed=0
    local total_quick=${#quick_suites[@]}
    
    for suite in "${quick_suites[@]}"; do
        local suite_name="${suite%% *}"
        local suite_args="${suite#* }"
        
        case $suite_name in
            "stack-operations")
                if run_stack_operations_tests "$suite_args"; then
                    quick_passed=$((quick_passed + 1))
                else
                    quick_failed=$((quick_failed + 1))
                fi
                ;;
            "network-operations")
                if run_network_operations_tests "$suite_args"; then
                    quick_passed=$((quick_passed + 1))
                else
                    quick_failed=$((quick_failed + 1))
                fi
                ;;
            "data-operations")
                if run_data_operations_tests "$suite_args"; then
                    quick_passed=$((quick_passed + 1))
                else
                    quick_failed=$((quick_failed + 1))
                fi
                ;;
            "granular-operations")
                if run_granular_operations_tests "$suite_args"; then
                    quick_passed=$((quick_passed + 1))
                else
                    quick_failed=$((quick_failed + 1))
                fi
                ;;
        esac
        
        echo ""
        log_info "----------------------------------------"
        echo ""
    done
    
    log_info "========================================"
    log_info "🚀 Quick Tests Complete"
    log_info "========================================"
    log_info "Total Quick Suites: $total_quick"
    log_success "Passed: $quick_passed"
    if [ $quick_failed -gt 0 ]; then
        log_error "Failed: $quick_failed"
    else
        log_info "Failed: $quick_failed"
    fi
    
    local success_rate=0
    if [ $total_quick -gt 0 ]; then
        success_rate=$((quick_passed * 100 / total_quick))
    fi
    
    log_info "Success Rate: $success_rate%"
    
    if [ $quick_failed -eq 0 ]; then
        log_success "🎉 All quick tests passed!"
        return 0
    else
        log_error "❌ Some quick tests failed!"
        return 1
    fi
}

# Function to run performance tests
run_performance_tests() {
    log_header "⚡ Running Performance Tests"
    log_info "========================================"
    
    local performance_suites=(
        "stack-operations"
        "network-operations"
        "granular-operations"
    )
    
    local perf_passed=0
    local perf_failed=0
    local total_perf=${#performance_suites[@]}
    
    for suite in "${performance_suites[@]}"; do
        case $suite in
            "stack-operations")
                if run_stack_operations_tests ""; then
                    perf_passed=$((perf_passed + 1))
                else
                    perf_failed=$((perf_failed + 1))
                fi
                ;;
            "network-operations")
                if run_network_operations_tests ""; then
                    perf_passed=$((perf_passed + 1))
                else
                    perf_failed=$((perf_failed + 1))
                fi
                ;;
            "granular-operations")
                if run_granular_operations_tests ""; then
                    perf_passed=$((perf_passed + 1))
                else
                    perf_failed=$((perf_failed + 1))
                fi
                ;;
        esac
        
        echo ""
        log_info "----------------------------------------"
        echo ""
    done
    
    log_info "========================================"
    log_info "⚡ Performance Tests Complete"
    log_info "========================================"
    log_info "Total Performance Suites: $total_perf"
    log_success "Passed: $perf_passed"
    if [ $perf_failed -gt 0 ]; then
        log_error "Failed: $perf_failed"
    else
        log_info "Failed: $perf_failed"
    fi
    
    local success_rate=0
    if [ $total_perf -gt 0 ]; then
        success_rate=$((perf_passed * 100 / total_perf))
    fi
    
    log_info "Success Rate: $success_rate%"
    
    if [ $perf_failed -eq 0 ]; then
        log_success "🎉 All performance tests passed!"
        return 0
    else
        log_error "❌ Some performance tests failed!"
        return 1
    fi
}

# Main function
main() {
    local start_time=$(date +%s)
    
    log_header "🧪 LLM Multimodal Stack - Comprehensive Test Suite"
    log_info "=================================================="
    log_info "Project: $PROJECT_ROOT"
    log_info "Started: $(date)"
    log_info "=================================================="
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Parse command line arguments
    local test_mode="all"
    local generate_report=false
    local quick_mode=false
    local performance_mode=false
    local specific_suite=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -a|--all)
                test_mode="all"
                shift
                ;;
            -s|--suite)
                test_mode="specific"
                specific_suite="$2"
                shift 2
                ;;
            -q|--quick)
                test_mode="quick"
                shift
                ;;
            -p|--performance)
                test_mode="performance"
                shift
                ;;
            -r|--report)
                generate_report=true
                shift
                ;;
            -v|--verbose)
                set -x
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Run tests based on mode
    case $test_mode in
        "all")
            run_all_test_suites
            ;;
        "specific")
            if [ -z "$specific_suite" ]; then
                log_error "No specific suite specified"
                show_help
                exit 1
            fi
            run_specific_test_suite "$specific_suite"
            ;;
        "quick")
            run_quick_tests
            ;;
        "performance")
            run_performance_tests
            ;;
    esac
    
    local end_time=$(date +%s)
    local total_duration=$((end_time - start_time))
    
    log_info "=================================================="
    log_info "🧪 Comprehensive Test Suite Complete"
    log_info "=================================================="
    log_info "Total Duration: ${total_duration}s"
    log_info "Finished: $(date)"
    
    # Generate report if requested
    if [ "$generate_report" = true ]; then
        generate_test_report
    fi
    
    # Exit with appropriate code
    if [ $? -eq 0 ]; then
        log_success "🎉 All tests completed successfully!"
        exit 0
    else
        log_error "❌ Some tests failed!"
        exit 1
    fi
}

# Help function
show_help() {
    cat << EOF
LLM Multimodal Stack - Comprehensive Test Suite

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -a, --all               Run all test suites (default)
    -s, --suite SUITE       Run specific test suite
    -q, --quick             Run quick tests (non-destructive)
    -p, --performance       Run performance tests
    -r, --report            Generate test report
    -v, --verbose           Enable verbose output

Available Test Suites:
    stack-operations        Test stack-based operations
    network-operations      Test network management
    data-operations         Test data retention and backup
    granular-operations     Test granular wipe/reset operations

Examples:
    $0                      # Run all test suites
    $0 --quick              # Run quick tests only
    $0 --suite stack-operations  # Run specific test suite
    $0 --performance        # Run performance tests
    $0 --report             # Generate test report

EOF
}

# Run main function
main "$@"
