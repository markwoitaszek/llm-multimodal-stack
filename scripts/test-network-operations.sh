#!/bin/bash

# Test script for network operations
# Tests network isolation, conflict detection, health monitoring, and connectivity

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

# Network configuration
EXPECTED_NETWORKS=(
    "multimodal-core-net:172.30.0.0/24"
    "multimodal-inference-net:172.31.0.0/24"
    "multimodal-ai-net:172.32.0.0/24"
    "multimodal-ui-net:172.33.0.0/24"
    "multimodal-testing-net:172.34.0.0/24"
    "multimodal-monitoring-net:172.35.0.0/24"
)

# Test configuration
TEST_TIMEOUT=30
CONNECTIVITY_TIMEOUT=10

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

# Test network conflict detection
test_network_conflicts() {
    log_info "Testing network conflict detection..."
    
    # Run network conflict check
    if make check-network-conflicts >/dev/null 2>&1; then
        log_success "✅ Network conflict detection: PASSED"
        return 0
    else
        log_error "❌ Network conflict detection: FAILED"
        return 1
    fi
}

# Test network validation
test_network_validation() {
    log_info "Testing network validation..."
    
    # Run network validation
    if make validate-networks >/dev/null 2>&1; then
        log_success "✅ Network validation: PASSED"
        return 0
    else
        log_error "❌ Network validation: FAILED"
        return 1
    fi
}

# Test network health check
test_network_health() {
    log_info "Testing network health check..."
    
    # Run network health check
    if make check-network-health >/dev/null 2>&1; then
        log_success "✅ Network health check: PASSED"
        return 0
    else
        log_error "❌ Network health check: FAILED"
        return 1
    fi
}

# Test network isolation
test_network_isolation() {
    log_info "Testing network isolation..."
    
    local networks_found=0
    local total_networks=${#EXPECTED_NETWORKS[@]}
    
    for network_config in "${EXPECTED_NETWORKS[@]}"; do
        local network_name="${network_config%%:*}"
        local expected_subnet="${network_config##*:}"
        
        # Check if network exists
        if docker network ls | grep -q "$network_name"; then
            log_success "✅ Network found: $network_name"
            
            # Check subnet configuration
            local actual_subnet
            actual_subnet=$(docker network inspect "$network_name" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null || echo "unknown")
            
            if [ "$actual_subnet" = "$expected_subnet" ]; then
                log_success "✅ Subnet correct for $network_name: $actual_subnet"
                networks_found=$((networks_found + 1))
            else
                log_warning "⚠️  Subnet mismatch for $network_name: expected $expected_subnet, got $actual_subnet"
            fi
        else
            log_warning "⚠️  Network not found: $network_name"
        fi
    done
    
    if [ $networks_found -eq $total_networks ]; then
        log_success "✅ Network isolation: PASSED ($networks_found/$total_networks networks)"
        return 0
    else
        log_warning "⚠️  Network isolation: PARTIAL ($networks_found/$total_networks networks)"
        return 1
    fi
}

# Test network connectivity
test_network_connectivity() {
    log_info "Testing network connectivity..."
    
    # Test connectivity between services in different stacks
    local connectivity_tests=(
        "docker exec multimodal-postgres ping -c 1 -W $CONNECTIVITY_TIMEOUT multimodal-redis"
        "docker exec multimodal-vllm ping -c 1 -W $CONNECTIVITY_TIMEOUT multimodal-postgres"
        "docker exec multimodal-worker ping -c 1 -W $CONNECTIVITY_TIMEOUT multimodal-postgres"
        "docker exec multimodal-worker ping -c 1 -W $CONNECTIVITY_TIMEOUT multimodal-vllm"
        "docker exec multimodal-retrieval-proxy ping -c 1 -W $CONNECTIVITY_TIMEOUT multimodal-postgres"
        "docker exec multimodal-retrieval-proxy ping -c 1 -W $CONNECTIVITY_TIMEOUT multimodal-qdrant"
    )
    
    local passed=0
    local total=${#connectivity_tests[@]}
    
    for test in "${connectivity_tests[@]}"; do
        if eval "$test" >/dev/null 2>&1; then
            log_success "✅ Connectivity test passed: $test"
            passed=$((passed + 1))
        else
            log_error "❌ Connectivity test failed: $test"
        fi
    done
    
    if [ $passed -eq $total ]; then
        log_success "✅ Network connectivity: PASSED ($passed/$total)"
        return 0
    else
        log_error "❌ Network connectivity: FAILED ($passed/$total)"
        return 1
    fi
}

# Test network cleanup
test_network_cleanup() {
    log_info "Testing network cleanup..."
    
    # Test network cleanup command
    if make cleanup-networks >/dev/null 2>&1; then
        log_success "✅ Network cleanup: PASSED"
        return 0
    else
        log_error "❌ Network cleanup: FAILED"
        return 1
    fi
}

# Test network creation
test_network_creation() {
    log_info "Testing network creation..."
    
    # Test creating a temporary network
    local test_network="test-network-$(date +%s)"
    
    if docker network create --driver bridge "$test_network" >/dev/null 2>&1; then
        log_success "✅ Network creation: PASSED"
        
        # Clean up test network
        if docker network rm "$test_network" >/dev/null 2>&1; then
            log_success "✅ Network cleanup: PASSED"
        else
            log_warning "⚠️  Failed to clean up test network: $test_network"
        fi
        
        return 0
    else
        log_error "❌ Network creation: FAILED"
        return 1
    fi
}

# Test network inspection
test_network_inspection() {
    log_info "Testing network inspection..."
    
    local inspection_tests_passed=0
    local inspection_tests_total=${#EXPECTED_NETWORKS[@]}
    
    for network_config in "${EXPECTED_NETWORKS[@]}"; do
        local network_name="${network_config%%:*}"
        
        # Test network inspection
        if docker network inspect "$network_name" >/dev/null 2>&1; then
            log_success "✅ Network inspection for $network_name: PASSED"
            inspection_tests_passed=$((inspection_tests_passed + 1))
        else
            log_error "❌ Network inspection for $network_name: FAILED"
        fi
    done
    
    if [ $inspection_tests_passed -eq $inspection_tests_total ]; then
        log_success "✅ Network inspection: PASSED ($inspection_tests_passed/$inspection_tests_total)"
        return 0
    else
        log_error "❌ Network inspection: FAILED ($inspection_tests_passed/$inspection_tests_total)"
        return 1
    fi
}

# Test network performance
test_network_performance() {
    log_info "Testing network performance..."
    
    # Test network latency between services
    local performance_tests=(
        "docker exec multimodal-postgres ping -c 3 multimodal-redis | grep 'avg'"
        "docker exec multimodal-vllm ping -c 3 multimodal-postgres | grep 'avg'"
    )
    
    local passed=0
    local total=${#performance_tests[@]}
    
    for test in "${performance_tests[@]}"; do
        if eval "$test" >/dev/null 2>&1; then
            log_success "✅ Performance test passed: $test"
            passed=$((passed + 1))
        else
            log_error "❌ Performance test failed: $test"
        fi
    done
    
    if [ $passed -eq $total ]; then
        log_success "✅ Network performance: PASSED ($passed/$total)"
        return 0
    else
        log_error "❌ Network performance: FAILED ($passed/$total)"
        return 1
    fi
}

# Test network security
test_network_security() {
    log_info "Testing network security..."
    
    # Test that services can only communicate with expected services
    local security_tests=(
        # Test that external services can't reach internal services
        "! docker run --rm --network multimodal-core-net alpine ping -c 1 multimodal-postgres"
        "! docker run --rm --network multimodal-inference-net alpine ping -c 1 multimodal-postgres"
    )
    
    local passed=0
    local total=${#security_tests[@]}
    
    for test in "${security_tests[@]}"; do
        if eval "$test" >/dev/null 2>&1; then
            log_success "✅ Security test passed: $test"
            passed=$((passed + 1))
        else
            log_error "❌ Security test failed: $test"
        fi
    done
    
    if [ $passed -eq $total ]; then
        log_success "✅ Network security: PASSED ($passed/$total)"
        return 0
    else
        log_error "❌ Network security: FAILED ($passed/$total)"
        return 1
    fi
}

# Test network monitoring
test_network_monitoring() {
    log_info "Testing network monitoring..."
    
    # Test network statistics
    local monitoring_tests=(
        "docker network ls | grep multimodal"
        "docker network inspect multimodal-core-net --format '{{.Containers}}'"
    )
    
    local passed=0
    local total=${#monitoring_tests[@]}
    
    for test in "${monitoring_tests[@]}"; do
        if eval "$test" >/dev/null 2>&1; then
            log_success "✅ Monitoring test passed: $test"
            passed=$((passed + 1))
        else
            log_error "❌ Monitoring test failed: $test"
        fi
    done
    
    if [ $passed -eq $total ]; then
        log_success "✅ Network monitoring: PASSED ($passed/$total)"
        return 0
    else
        log_error "❌ Network monitoring: FAILED ($passed/$total)"
        return 1
    fi
}

# Main test execution
main() {
    log_info "🌐 Starting Network Operations Test Suite"
    log_info "=========================================="
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Test network conflict detection
    run_test "Network Conflict Detection" "test_network_conflicts"
    
    # Test network validation
    run_test "Network Validation" "test_network_validation"
    
    # Test network health check
    run_test "Network Health Check" "test_network_health"
    
    # Test network isolation
    run_test "Network Isolation" "test_network_isolation"
    
    # Test network connectivity
    run_test "Network Connectivity" "test_network_connectivity"
    
    # Test network cleanup
    run_test "Network Cleanup" "test_network_cleanup"
    
    # Test network creation
    run_test "Network Creation" "test_network_creation"
    
    # Test network inspection
    run_test "Network Inspection" "test_network_inspection"
    
    # Test network performance
    run_test "Network Performance" "test_network_performance"
    
    # Test network security
    run_test "Network Security" "test_network_security"
    
    # Test network monitoring
    run_test "Network Monitoring" "test_network_monitoring"
    
    # Print test summary
    log_info "=========================================="
    log_info "🌐 Network Operations Test Suite Complete"
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
Network Operations Test Suite

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -t, --timeout SECONDS   Set timeout for connectivity tests (default: $CONNECTIVITY_TIMEOUT)
    --skip-connectivity     Skip connectivity tests
    --skip-performance      Skip performance tests
    --skip-security         Skip security tests

Examples:
    $0                      # Run all tests
    $0 --skip-connectivity  # Skip connectivity tests
    $0 -t 5                 # Set 5 second timeout for connectivity tests

EOF
}

# Parse command line arguments
VERBOSE=false
SKIP_CONNECTIVITY=false
SKIP_PERFORMANCE=false
SKIP_SECURITY=false

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
            CONNECTIVITY_TIMEOUT="$2"
            shift 2
            ;;
        --skip-connectivity)
            SKIP_CONNECTIVITY=true
            shift
            ;;
        --skip-performance)
            SKIP_PERFORMANCE=true
            shift
            ;;
        --skip-security)
            SKIP_SECURITY=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main function
main
