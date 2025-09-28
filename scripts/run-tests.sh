#!/bin/bash

# Comprehensive Test Runner for LLM Multimodal Stack
# Implements GitHub Issue #5: Comprehensive Testing Infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_TYPES=("unit" "integration" "performance" "all")
COVERAGE_THRESHOLD=80
PERFORMANCE_THRESHOLD=1000

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print header
print_header() {
    echo
    print_status $BLUE "=========================================="
    print_status $BLUE "$1"
    print_status $BLUE "=========================================="
    echo
}

# Function to check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Python version
    if ! python3 --version | grep -q "Python 3.11"; then
        print_status $RED "❌ Python 3.11 is required"
        exit 1
    fi
    print_status $GREEN "✅ Python 3.11 found"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_status $RED "❌ pip3 is required"
        exit 1
    fi
    print_status $GREEN "✅ pip3 found"
    
    # Check pytest
    if ! python3 -m pytest --version &> /dev/null; then
        print_status $YELLOW "⚠️  pytest not found, installing..."
        pip3 install pytest pytest-asyncio pytest-cov pytest-mock
    fi
    print_status $GREEN "✅ pytest found"
    
    # Check Docker (for integration tests)
    if ! command -v docker &> /dev/null; then
        print_status $YELLOW "⚠️  Docker not found - integration tests will be skipped"
    else
        print_status $GREEN "✅ Docker found"
    fi
}

# Function to install test dependencies
install_dependencies() {
    print_header "Installing Test Dependencies"
    
    if [ -f "requirements-test.txt" ]; then
        print_status $BLUE "Installing test requirements..."
        pip3 install -r requirements-test.txt
        print_status $GREEN "✅ Test dependencies installed"
    else
        print_status $YELLOW "⚠️  requirements-test.txt not found, installing basic dependencies..."
        pip3 install pytest pytest-asyncio pytest-cov pytest-mock httpx psutil
    fi
}

# Function to run unit tests
run_unit_tests() {
    print_header "Running Unit Tests"
    
    local total_coverage=0
    local service_count=0
    
    # Test each service
    for service in services/*/; do
        if [ -d "${service}tests" ]; then
            service_name=$(basename "$service")
            print_status $BLUE "Testing $service_name..."
            
            cd "$service"
            if python3 -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=$COVERAGE_THRESHOLD; then
                print_status $GREEN "✅ $service_name unit tests passed"
                
                # Extract coverage percentage
                coverage=$(python3 -m pytest tests/ --cov=app --cov-report=term-missing | grep "TOTAL" | awk '{print $4}' | sed 's/%//')
                if [ ! -z "$coverage" ]; then
                    total_coverage=$((total_coverage + coverage))
                    service_count=$((service_count + 1))
                fi
            else
                print_status $RED "❌ $service_name unit tests failed"
                return 1
            fi
            cd - > /dev/null
        fi
    done
    
    # Calculate average coverage
    if [ $service_count -gt 0 ]; then
        avg_coverage=$((total_coverage / service_count))
        print_status $GREEN "✅ Average unit test coverage: ${avg_coverage}%"
        
        if [ $avg_coverage -ge $COVERAGE_THRESHOLD ]; then
            print_status $GREEN "✅ Coverage threshold ($COVERAGE_THRESHOLD%) met"
        else
            print_status $RED "❌ Coverage threshold ($COVERAGE_THRESHOLD%) not met"
            return 1
        fi
    fi
}

# Function to run integration tests
run_integration_tests() {
    print_header "Running Integration Tests"
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        print_status $YELLOW "⚠️  Docker not available, skipping integration tests"
        return 0
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        print_status $YELLOW "⚠️  docker-compose not available, skipping integration tests"
        return 0
    fi
    
    # Start test environment
    print_status $BLUE "Starting test environment..."
    if docker-compose -f docker-compose.test.yml up -d; then
        print_status $GREEN "✅ Test environment started"
    else
        print_status $RED "❌ Failed to start test environment"
        return 1
    fi
    
    # Wait for services to be ready
    print_status $BLUE "Waiting for services to be ready..."
    sleep 30
    
    # Run integration tests
    print_status $BLUE "Running integration tests..."
    if python3 -m pytest tests/integration/ -v -m integration; then
        print_status $GREEN "✅ Integration tests passed"
    else
        print_status $RED "❌ Integration tests failed"
        docker-compose -f docker-compose.test.yml down
        return 1
    fi
    
    # Cleanup
    print_status $BLUE "Cleaning up test environment..."
    docker-compose -f docker-compose.test.yml down
    print_status $GREEN "✅ Test environment cleaned up"
}

# Function to run performance tests
run_performance_tests() {
    print_header "Running Performance Tests"
    
    print_status $BLUE "Running performance tests..."
    if python3 -m pytest tests/performance/ -v -m performance; then
        print_status $GREEN "✅ Performance tests passed"
    else
        print_status $RED "❌ Performance tests failed"
        return 1
    fi
}

# Function to run security tests
run_security_tests() {
    print_header "Running Security Tests"
    
    # Check if bandit is available
    if command -v bandit &> /dev/null; then
        print_status $BLUE "Running Bandit security scan..."
        if bandit -r services/ -f json -o bandit-report.json; then
            print_status $GREEN "✅ Bandit security scan passed"
        else
            print_status $YELLOW "⚠️  Bandit found security issues (see bandit-report.json)"
        fi
    else
        print_status $YELLOW "⚠️  Bandit not available, skipping security scan"
    fi
    
    # Check if safety is available
    if command -v safety &> /dev/null; then
        print_status $BLUE "Running Safety vulnerability check..."
        if safety check --json --output safety-report.json; then
            print_status $GREEN "✅ Safety vulnerability check passed"
        else
            print_status $YELLOW "⚠️  Safety found vulnerabilities (see safety-report.json)"
        fi
    else
        print_status $YELLOW "⚠️  Safety not available, skipping vulnerability check"
    fi
}

# Function to generate test report
generate_report() {
    print_header "Generating Test Report"
    
    local report_file="test-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$report_file" << EOF
# Test Report - $(date)

## Test Summary

- **Date**: $(date)
- **Branch**: $(git branch --show-current 2>/dev/null || echo "unknown")
- **Commit**: $(git rev-parse HEAD 2>/dev/null || echo "unknown")

## Test Results

### Unit Tests
- **Status**: $([ $? -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")
- **Coverage**: ${avg_coverage:-0}% (threshold: ${COVERAGE_THRESHOLD}%)

### Integration Tests
- **Status**: $([ $? -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")

### Performance Tests
- **Status**: $([ $? -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")

### Security Tests
- **Status**: $([ $? -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")

## Files Generated

- Coverage reports: \`htmlcov/\`
- Security reports: \`bandit-report.json\`, \`safety-report.json\`
- Test artifacts: \`test-results/\`

## Next Steps

1. Review any failed tests
2. Address security issues if found
3. Improve coverage if below threshold
4. Update performance baselines if needed

EOF

    print_status $GREEN "✅ Test report generated: $report_file"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [TEST_TYPE]"
    echo
    echo "Test Types:"
    for type in "${TEST_TYPES[@]}"; do
        echo "  - $type"
    done
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Verbose output"
    echo "  --coverage     Show coverage report"
    echo "  --no-cleanup   Don't cleanup test environment"
    echo
    echo "Examples:"
    echo "  $0 unit                    # Run only unit tests"
    echo "  $0 integration             # Run only integration tests"
    echo "  $0 performance             # Run only performance tests"
    echo "  $0 all                     # Run all tests"
    echo "  $0 --coverage unit         # Run unit tests with coverage report"
}

# Main function
main() {
    local test_type="all"
    local verbose=false
    local show_coverage=false
    local no_cleanup=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            --coverage)
                show_coverage=true
                shift
                ;;
            --no-cleanup)
                no_cleanup=true
                shift
                ;;
            unit|integration|performance|all)
                test_type="$1"
                shift
                ;;
            *)
                print_status $RED "❌ Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Start test execution
    print_header "🧪 LLM Multimodal Stack - Comprehensive Test Suite"
    print_status $BLUE "Test Type: $test_type"
    print_status $BLUE "Coverage Threshold: ${COVERAGE_THRESHOLD}%"
    echo
    
    # Check prerequisites
    check_prerequisites
    
    # Install dependencies
    install_dependencies
    
    # Run tests based on type
    case $test_type in
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        performance)
            run_performance_tests
            ;;
        all)
            run_unit_tests && \
            run_integration_tests && \
            run_performance_tests && \
            run_security_tests
            ;;
    esac
    
    # Generate report
    generate_report
    
    # Show coverage if requested
    if [ "$show_coverage" = true ] && [ -d "htmlcov" ]; then
        print_status $BLUE "Coverage report available at: htmlcov/index.html"
    fi
    
    print_header "🎉 Test Execution Complete"
    
    if [ $? -eq 0 ]; then
        print_status $GREEN "✅ All tests passed successfully!"
        exit 0
    else
        print_status $RED "❌ Some tests failed. Please check the output above."
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
