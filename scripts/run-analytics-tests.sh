#!/bin/bash

# Analytics & Insights Dashboard Test Runner
# Part of Issue #9: Analytics & Insights Dashboard

set -e

echo "📊 Running Analytics & Insights Dashboard Tests"
echo "==============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "analytics/analytics_engine.py" ]; then
    print_error "Please run this script from the workspace root directory"
    exit 1
fi

# Check Python version
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
print_success "Python version: $python_version"

# Check if pytest is available
print_status "Checking test dependencies..."
if ! command -v pytest &> /dev/null; then
    print_warning "pytest not found. Installing..."
    pip install pytest pytest-asyncio
fi

# Check if required packages are available
required_packages=("fastapi" "uvicorn" "jinja2" "psutil" "aiofiles" "aiosqlite")
missing_packages=()

for package in "${required_packages[@]}"; do
    if ! python3 -c "import $package" 2>/dev/null; then
        missing_packages+=("$package")
    fi
done

if [ ${#missing_packages[@]} -ne 0 ]; then
    print_warning "Missing packages: ${missing_packages[*]}"
    print_status "Installing missing packages..."
    pip install "${missing_packages[@]}"
fi

# Create test directory if it doesn't exist
if [ ! -d "tests/analytics" ]; then
    print_status "Creating test directory..."
    mkdir -p tests/analytics
fi

# Run the analytics dashboard tests
print_status "Running analytics dashboard tests..."
echo ""

# Run tests with verbose output
if pytest tests/analytics/test_phase3_analytics_dashboard.py -v --tb=short; then
    print_success "All analytics dashboard tests passed!"
    echo ""
    
    # Run specific test categories
    print_status "Running individual test suites..."
    echo ""
    
    # Test Analytics Event
    print_status "Testing Analytics Event..."
    if pytest tests/analytics/test_phase3_analytics_dashboard.py::TestAnalyticsEvent -v; then
        print_success "Analytics Event tests passed"
    else
        print_error "Analytics Event tests failed"
    fi
    echo ""
    
    # Test Performance Metrics
    print_status "Testing Performance Metrics..."
    if pytest tests/analytics/test_phase3_analytics_dashboard.py::TestPerformanceMetrics -v; then
        print_success "Performance Metrics tests passed"
    else
        print_error "Performance Metrics tests failed"
    fi
    echo ""
    
    # Test Analytics Collector
    print_status "Testing Analytics Collector..."
    if pytest tests/analytics/test_phase3_analytics_dashboard.py::TestAnalyticsCollector -v; then
        print_success "Analytics Collector tests passed"
    else
        print_error "Analytics Collector tests failed"
    fi
    echo ""
    
    # Test Analytics Insights
    print_status "Testing Analytics Insights..."
    if pytest tests/analytics/test_phase3_analytics_dashboard.py::TestAnalyticsInsights -v; then
        print_success "Analytics Insights tests passed"
    else
        print_error "Analytics Insights tests failed"
    fi
    echo ""
    
    # Test Dashboard Server
    print_status "Testing Dashboard Server..."
    if pytest tests/analytics/test_phase3_analytics_dashboard.py::TestDashboardServer -v; then
        print_success "Dashboard Server tests passed"
    else
        print_error "Dashboard Server tests failed"
    fi
    echo ""
    
    # Test Integration
    print_status "Testing System Integration..."
    if pytest tests/analytics/test_phase3_analytics_dashboard.py::TestAnalyticsIntegration -v; then
        print_success "System Integration tests passed"
    else
        print_error "System Integration tests failed"
    fi
    echo ""
    
    # Test Performance
    print_status "Testing System Performance..."
    if pytest tests/analytics/test_phase3_analytics_dashboard.py::TestAnalyticsPerformance -v; then
        print_success "System Performance tests passed"
    else
        print_error "System Performance tests failed"
    fi
    echo ""
    
    # Generate test report
    print_status "Generating test report..."
    pytest tests/analytics/test_phase3_analytics_dashboard.py --html=test_report_analytics.html --self-contained-html
    
    if [ -f "test_report_analytics.html" ]; then
        print_success "Test report generated: test_report_analytics.html"
    fi
    
    echo ""
    print_success "🎉 All analytics dashboard tests completed successfully!"
    echo ""
    print_status "Test Summary:"
    echo "  ✅ Analytics Event Management"
    echo "  ✅ Performance Metrics Tracking"
    echo "  ✅ Analytics Data Collection"
    echo "  ✅ Insights Generation"
    echo "  ✅ Dashboard Server"
    echo "  ✅ System Integration"
    echo "  ✅ Performance Testing"
    echo ""
    print_status "The analytics & insights dashboard is ready for production use!"
    
else
    print_error "Analytics dashboard tests failed!"
    echo ""
    print_status "Please check the test output above for details."
    print_status "Common issues:"
    echo "  - Missing dependencies (install with pip)"
    echo "  - Python version compatibility"
    echo "  - File permissions"
    echo "  - Test environment setup"
    echo ""
    exit 1
fi

# Optional: Start analytics dashboard for manual testing
if [ "$1" = "--start-dashboard" ]; then
    print_status "Starting analytics dashboard for manual testing..."
    echo "Dashboard will be available at: http://localhost:8081"
    echo "Press Ctrl+C to stop the dashboard"
    echo ""
    
    cd analytics
    python3 insights_dashboard.py
fi

echo ""
print_success "Analytics dashboard test runner completed!"