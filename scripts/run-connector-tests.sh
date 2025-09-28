#!/bin/bash

# API Connector Ecosystem Test Runner
# Part of Issue #10: API Connector Ecosystem

set -e

echo "🔌 Running API Connector Ecosystem Tests"
echo "========================================"

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
if [ ! -f "connectors/connector_framework.py" ]; then
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
required_packages=("fastapi" "uvicorn" "aiohttp" "yaml" "pydantic")
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
if [ ! -d "tests/connectors" ]; then
    print_status "Creating test directory..."
    mkdir -p tests/connectors
fi

# Run the connector ecosystem tests
print_status "Running connector ecosystem tests..."
echo ""

# Run tests with verbose output
if pytest tests/connectors/test_phase3_connector_ecosystem.py -v --tb=short; then
    print_success "All connector ecosystem tests passed!"
    echo ""
    
    # Run specific test categories
    print_status "Running individual test suites..."
    echo ""
    
    # Test Connector Config
    print_status "Testing Connector Configuration..."
    if pytest tests/connectors/test_phase3_connector_ecosystem.py::TestConnectorConfig -v; then
        print_success "Connector Configuration tests passed"
    else
        print_error "Connector Configuration tests failed"
    fi
    echo ""
    
    # Test Data Transformer
    print_status "Testing Data Transformer..."
    if pytest tests/connectors/test_phase3_connector_ecosystem.py::TestDataTransformer -v; then
        print_success "Data Transformer tests passed"
    else
        print_error "Data Transformer tests failed"
    fi
    echo ""
    
    # Test Connector Registry
    print_status "Testing Connector Registry..."
    if pytest tests/connectors/test_phase3_connector_ecosystem.py::TestConnectorRegistry -v; then
        print_success "Connector Registry tests passed"
    else
        print_error "Connector Registry tests failed"
    fi
    echo ""
    
    # Test Pre-built Connectors
    print_status "Testing Pre-built Connectors..."
    if pytest tests/connectors/test_phase3_connector_ecosystem.py::TestPrebuiltConnectors -v; then
        print_success "Pre-built Connectors tests passed"
    else
        print_error "Pre-built Connectors tests failed"
    fi
    echo ""
    
    # Test Connector Builder
    print_status "Testing Connector Builder..."
    if pytest tests/connectors/test_phase3_connector_ecosystem.py::TestConnectorBuilder -v; then
        print_success "Connector Builder tests passed"
    else
        print_error "Connector Builder tests failed"
    fi
    echo ""
    
    # Test Connector Manager
    print_status "Testing Connector Manager..."
    if pytest tests/connectors/test_phase3_connector_ecosystem.py::TestConnectorManager -v; then
        print_success "Connector Manager tests passed"
    else
        print_error "Connector Manager tests failed"
    fi
    echo ""
    
    # Test Connector Server
    print_status "Testing Connector Server..."
    if pytest tests/connectors/test_phase3_connector_ecosystem.py::TestConnectorServer -v; then
        print_success "Connector Server tests passed"
    else
        print_error "Connector Server tests failed"
    fi
    echo ""
    
    # Test Integration
    print_status "Testing System Integration..."
    if pytest tests/connectors/test_phase3_connector_ecosystem.py::TestConnectorIntegration -v; then
        print_success "System Integration tests passed"
    else
        print_error "System Integration tests failed"
    fi
    echo ""
    
    # Test Performance
    print_status "Testing System Performance..."
    if pytest tests/connectors/test_phase3_connector_ecosystem.py::TestConnectorPerformance -v; then
        print_success "System Performance tests passed"
    else
        print_error "System Performance tests failed"
    fi
    echo ""
    
    # Generate test report
    print_status "Generating test report..."
    pytest tests/connectors/test_phase3_connector_ecosystem.py --html=test_report_connectors.html --self-contained-html
    
    if [ -f "test_report_connectors.html" ]; then
        print_success "Test report generated: test_report_connectors.html"
    fi
    
    echo ""
    print_success "🎉 All connector ecosystem tests completed successfully!"
    echo ""
    print_status "Test Summary:"
    echo "  ✅ Connector Configuration"
    echo "  ✅ Data Transformation"
    echo "  ✅ Connector Registry"
    echo "  ✅ Pre-built Connectors"
    echo "  ✅ Connector Builder"
    echo "  ✅ Connector Manager"
    echo "  ✅ Connector Server"
    echo "  ✅ System Integration"
    echo "  ✅ Performance Testing"
    echo ""
    print_status "The API connector ecosystem is ready for production use!"
    
else
    print_error "Connector ecosystem tests failed!"
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

# Optional: Start connector server for manual testing
if [ "$1" = "--start-server" ]; then
    print_status "Starting connector server for manual testing..."
    echo "Server will be available at: http://localhost:8082"
    echo "Press Ctrl+C to stop the server"
    echo ""
    
    cd connectors
    python3 connector_server.py
fi

echo ""
print_success "Connector ecosystem test runner completed!"