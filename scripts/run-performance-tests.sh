#!/bin/bash
# Performance Testing Script for LLM Multimodal Stack
# Phase 3 Production Readiness

set -e

echo "🚀 Starting Performance Testing Suite"
echo "======================================"

# Configuration
BASE_URL=${BASE_URL:-"http://localhost:8000"}
OUTPUT_DIR=${OUTPUT_DIR:-"./performance_reports"}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "📊 Configuration:"
echo "  Base URL: $BASE_URL"
echo "  Output Directory: $OUTPUT_DIR"
echo "  Timestamp: $TIMESTAMP"
echo ""

# Check if services are running
echo "🔍 Checking service availability..."
services=("multimodal-worker" "retrieval-proxy" "ai-agents" "memory-system" "search-engine" "user-management")

for service in "${services[@]}"; do
    port=""
    case $service in
        "multimodal-worker") port="8001" ;;
        "retrieval-proxy") port="8002" ;;
        "ai-agents") port="8003" ;;
        "memory-system") port="8005" ;;
        "search-engine") port="8004" ;;
        "user-management") port="8006" ;;
    esac
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "  ✅ $service (port $port) - Healthy"
    else
        echo "  ❌ $service (port $port) - Unavailable"
        echo "     Please ensure all services are running before running performance tests"
        exit 1
    fi
done

echo ""

# Run performance tests
echo "🧪 Running Performance Tests..."
echo "==============================="

# Run comprehensive performance test suite
python3 performance/run_performance_tests.py \
    --base-url "$BASE_URL" \
    --output "$OUTPUT_DIR/performance_report_$TIMESTAMP.json" \
    --verbose

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Performance tests completed successfully!"
    
    # Generate additional reports
    echo "📈 Generating additional reports..."
    
    # Convert JSON to HTML report (if jq is available)
    if command -v jq >/dev/null 2>&1; then
        echo "  Generating HTML report..."
        python3 -c "
import json
import sys

try:
    with open('$OUTPUT_DIR/performance_report_$TIMESTAMP.json', 'r') as f:
        data = json.load(f)
    
    # Generate simple HTML report
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Performance Test Report - {data['test_summary']['start_time']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
            .metric {{ margin: 10px 0; padding: 10px; border-left: 4px solid #007cba; }}
            .critical {{ border-left-color: #d32f2f; }}
            .warning {{ border-left-color: #f57c00; }}
            .success {{ border-left-color: #388e3c; }}
        </style>
    </head>
    <body>
        <div class=\"header\">
            <h1>Performance Test Report</h1>
            <p><strong>Test Suite:</strong> {data['test_summary']['test_suite']}</p>
            <p><strong>Duration:</strong> {data['test_summary']['duration_seconds']:.1f} seconds</p>
            <p><strong>Performance Score:</strong> {data['test_summary']['performance_score']:.1f}/100</p>
            <p><strong>Performance Grade:</strong> {data['test_summary']['performance_grade']}</p>
        </div>
        
        <h2>Load Test Results</h2>
        <div class=\"metric success\">
            <h3>Suite Summary</h3>
            <p><strong>Total Requests:</strong> {data['load_test_results']['suite_summary']['total_requests']}</p>
            <p><strong>Success Rate:</strong> {100 - data['load_test_results']['suite_summary']['overall_error_rate']:.1f}%</p>
            <p><strong>Average RPS:</strong> {data['load_test_results']['suite_summary']['avg_requests_per_second']:.1f}</p>
            <p><strong>Average Response Time:</strong> {data['load_test_results']['suite_summary']['avg_response_time_ms']:.1f}ms</p>
        </div>
        
        <h2>Performance Analysis</h2>
        <div class=\"metric {'critical' if data['performance_analysis']['system_health_score'] < 70 else 'warning' if data['performance_analysis']['system_health_score'] < 80 else 'success'}\">
            <h3>System Health</h3>
            <p><strong>Health Score:</strong> {data['performance_analysis']['system_health_score']:.1f}/100</p>
            <p><strong>Total Bottlenecks:</strong> {data['performance_analysis']['total_bottlenecks']}</p>
            <p><strong>Critical Issues:</strong> {data['performance_analysis']['critical_bottlenecks']}</p>
        </div>
        
        <h2>Recommendations</h2>
        <h3>Immediate Actions</h3>
        {''.join([f'<div class=\"metric critical\"><p><strong>{rec[\"title\"]}</strong></p><p>{rec[\"description\"]}</p></div>' for rec in data['recommendations']['immediate_actions']])}
        
        <h3>High Priority Actions</h3>
        {''.join([f'<div class=\"metric warning\"><p><strong>{rec[\"title\"]}</strong></p><p>{rec[\"description\"]}</p></div>' for rec in data['recommendations']['high_priority_actions']])}
        
        <p><em>Report generated at: {data['test_summary']['end_time']}</em></p>
    </body>
    </html>
    '''
    
    with open('$OUTPUT_DIR/performance_report_$TIMESTAMP.html', 'w') as f:
        f.write(html)
    
    print('  HTML report generated: $OUTPUT_DIR/performance_report_$TIMESTAMP.html')
    
except Exception as e:
    print(f'  Error generating HTML report: {e}')
"
    fi
    
    # Generate summary
    echo ""
    echo "📋 Performance Test Summary:"
    echo "============================"
    
    # Extract key metrics from JSON report
    python3 -c "
import json

try:
    with open('$OUTPUT_DIR/performance_report_$TIMESTAMP.json', 'r') as f:
        data = json.load(f)
    
    summary = data['test_summary']
    load_results = data['load_test_results']['suite_summary']
    analysis = data['performance_analysis']
    
    print(f'  Test Duration: {summary[\"duration_seconds\"]:.1f} seconds')
    print(f'  Performance Score: {summary[\"performance_score\"]:.1f}/100 ({summary[\"performance_grade\"]})')
    print(f'  Total Requests: {load_results[\"total_requests\"]}')
    print(f'  Success Rate: {100 - load_results[\"overall_error_rate\"]:.1f}%')
    print(f'  Average RPS: {load_results[\"avg_requests_per_second\"]:.1f}')
    print(f'  Average Response Time: {load_results[\"avg_response_time_ms\"]:.1f}ms')
    print(f'  System Health Score: {analysis[\"system_health_score\"]:.1f}/100')
    print(f'  Total Bottlenecks: {analysis[\"total_bottlenecks\"]}')
    print(f'  Critical Issues: {analysis[\"critical_bottlenecks\"]}')
    print(f'  Total Recommendations: {analysis[\"total_recommendations\"]}')
    
    # Show critical recommendations
    immediate_actions = data['recommendations']['immediate_actions']
    if immediate_actions:
        print('')
        print('  🚨 IMMEDIATE ACTIONS REQUIRED:')
        for action in immediate_actions:
            print(f'    - {action[\"title\"]}')
    
except Exception as e:
    print(f'  Error generating summary: {e}')
"
    
    echo ""
    echo "📁 Reports generated:"
    echo "  - JSON: $OUTPUT_DIR/performance_report_$TIMESTAMP.json"
    if [ -f "$OUTPUT_DIR/performance_report_$TIMESTAMP.html" ]; then
        echo "  - HTML: $OUTPUT_DIR/performance_report_$TIMESTAMP.html"
    fi
    
    echo ""
    echo "🎉 Performance testing completed successfully!"
    echo "   All systems are ready for production deployment."
    
else
    echo ""
    echo "❌ Performance tests failed!"
    echo "   Please review the test results and address any issues before production deployment."
    exit 1
fi

echo ""
echo "🔗 Next Steps:"
echo "  1. Review the performance report"
echo "  2. Address any critical recommendations"
echo "  3. Implement high-priority optimizations"
echo "  4. Schedule regular performance monitoring"
echo "  5. Set up production alerting"
echo ""
echo "📚 Documentation:"
echo "  - Performance Implementation Guide: PERFORMANCE_OPTIMIZATION_IMPLEMENTATION.md"
echo "  - Test Results: $OUTPUT_DIR/performance_report_$TIMESTAMP.json"
echo ""