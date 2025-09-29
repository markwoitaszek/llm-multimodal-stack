#!/bin/bash
# Test Execution Script with Allure Integration

set -e

echo "🚀 Starting test execution with Allure integration..."

# Configuration
WORKSPACE_PATH="/workspace"
ALLURE_RESULTS_DIR="$WORKSPACE_PATH/allure-results"
ALLURE_REPORT_DIR="$WORKSPACE_PATH/allure-report"
TEST_TYPE="${1:-all}"

# Clean previous results
echo "🧹 Cleaning previous test results..."
rm -rf "$ALLURE_RESULTS_DIR"
mkdir -p "$ALLURE_RESULTS_DIR"

# Run tests
echo "🧪 Running $TEST_TYPE tests..."
case $TEST_TYPE in
    "unit")
        python3 -m pytest tests/ -m unit --alluredir=allure-results --allure-clean -v
        ;;
    "integration")
        python3 -m pytest tests/ -m integration --alluredir=allure-results --allure-clean -v
        ;;
    "performance")
        python3 -m pytest tests/ -m performance --alluredir=allure-results --allure-clean -v
        ;;
    "api")
        python3 -m pytest tests/ -m api --alluredir=allure-results --allure-clean -v
        ;;
    *)
        python3 -m pytest tests/ --alluredir=allure-results --allure-clean -v
        ;;
esac

# Generate Allure report
echo "📊 Generating Allure report..."
allure generate "$ALLURE_RESULTS_DIR" -o "$ALLURE_REPORT_DIR" --clean

# Check if report was generated
if [ -d "$ALLURE_REPORT_DIR" ]; then
    echo "✅ Allure report generated successfully"
    echo "📁 Report location: $ALLURE_REPORT_DIR"
    
    # Serve report if requested
    if [ "$2" = "serve" ]; then
        echo "🌐 Serving Allure report on port 8080..."
        allure open "$ALLURE_REPORT_DIR" --port 8080 --host 0.0.0.0
    fi
else
    echo "❌ Failed to generate Allure report"
    exit 1
fi

echo "🎉 Test execution completed successfully!"
