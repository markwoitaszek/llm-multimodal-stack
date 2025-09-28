#!/bin/bash

# Documentation System Test Runner
# Part of Issue #71: Documentation Rendering & Navigation

set -e

echo "🚀 Running Documentation System Tests"
echo "======================================"

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
if [ ! -f "docs/documentation_system.py" ]; then
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
required_packages=("fastapi" "uvicorn" "jinja2" "markdown" "pygments" "yaml" "aiofiles")
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
if [ ! -d "tests/documentation" ]; then
    print_status "Creating test directory..."
    mkdir -p tests/documentation
fi

# Run the documentation system tests
print_status "Running documentation system tests..."
echo ""

# Run tests with verbose output
if pytest tests/documentation/test_phase3_documentation_system.py -v --tb=short; then
    print_success "All documentation system tests passed!"
    echo ""
    
    # Run specific test categories
    print_status "Running individual test suites..."
    echo ""
    
    # Test Markdown Renderer
    print_status "Testing Markdown Renderer..."
    if pytest tests/documentation/test_phase3_documentation_system.py::TestMarkdownRenderer -v; then
        print_success "Markdown Renderer tests passed"
    else
        print_error "Markdown Renderer tests failed"
    fi
    echo ""
    
    # Test Content Validator
    print_status "Testing Content Validator..."
    if pytest tests/documentation/test_phase3_documentation_system.py::TestContentValidator -v; then
        print_success "Content Validator tests passed"
    else
        print_error "Content Validator tests failed"
    fi
    echo ""
    
    # Test Documentation Indexer
    print_status "Testing Documentation Indexer..."
    if pytest tests/documentation/test_phase3_documentation_system.py::TestDocumentationIndexer -v; then
        print_success "Documentation Indexer tests passed"
    else
        print_error "Documentation Indexer tests failed"
    fi
    echo ""
    
    # Test Content Manager
    print_status "Testing Content Manager..."
    if pytest tests/documentation/test_phase3_documentation_system.py::TestContentManager -v; then
        print_success "Content Manager tests passed"
    else
        print_error "Content Manager tests failed"
    fi
    echo ""
    
    # Test Advanced Search Engine
    print_status "Testing Advanced Search Engine..."
    if pytest tests/documentation/test_phase3_documentation_system.py::TestAdvancedSearchEngine -v; then
        print_success "Advanced Search Engine tests passed"
    else
        print_error "Advanced Search Engine tests failed"
    fi
    echo ""
    
    # Test Documentation Server
    print_status "Testing Documentation Server..."
    if pytest tests/documentation/test_phase3_documentation_system.py::TestDocumentationServer -v; then
        print_success "Documentation Server tests passed"
    else
        print_error "Documentation Server tests failed"
    fi
    echo ""
    
    # Test Integration
    print_status "Testing System Integration..."
    if pytest tests/documentation/test_phase3_documentation_system.py::TestDocumentationSystemIntegration -v; then
        print_success "System Integration tests passed"
    else
        print_error "System Integration tests failed"
    fi
    echo ""
    
    # Test Performance
    print_status "Testing System Performance..."
    if pytest tests/documentation/test_phase3_documentation_system.py::TestDocumentationSystemPerformance -v; then
        print_success "System Performance tests passed"
    else
        print_error "System Performance tests failed"
    fi
    echo ""
    
    # Generate test report
    print_status "Generating test report..."
    pytest tests/documentation/test_phase3_documentation_system.py --html=test_report_documentation.html --self-contained-html
    
    if [ -f "test_report_documentation.html" ]; then
        print_success "Test report generated: test_report_documentation.html"
    fi
    
    echo ""
    print_success "🎉 All documentation system tests completed successfully!"
    echo ""
    print_status "Test Summary:"
    echo "  ✅ Markdown Rendering"
    echo "  ✅ Content Validation"
    echo "  ✅ Documentation Indexing"
    echo "  ✅ Content Management"
    echo "  ✅ Advanced Search"
    echo "  ✅ Documentation Server"
    echo "  ✅ System Integration"
    echo "  ✅ Performance Testing"
    echo ""
    print_status "The documentation system is ready for production use!"
    
else
    print_error "Documentation system tests failed!"
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

# Optional: Run documentation server for manual testing
if [ "$1" = "--start-server" ]; then
    print_status "Starting documentation server for manual testing..."
    echo "Server will be available at: http://localhost:8080"
    echo "Press Ctrl+C to stop the server"
    echo ""
    
    cd docs
    python3 documentation_server.py
fi

echo ""
print_success "Documentation system test runner completed!"