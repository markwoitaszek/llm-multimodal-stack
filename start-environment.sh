#!/bin/bash
# LLM Multimodal Stack - Environment Startup Script

set -e

echo "🚀 LLM Multimodal Stack - Environment Startup"
echo "=============================================="

# Function to display usage
usage() {
    echo "Usage: $0 [environment]"
    echo ""
    echo "Environments:"
    echo "  dev       - Development (base services only)"
    echo "  staging   - Staging environment"
    echo "  production - Production environment"
    echo "  testing   - Testing with Allure reports"
    echo "  performance - Performance testing with JMeter"
    echo "  monitoring - Add ELK stack for monitoring"
    echo "  optimized - Performance-optimized environment"
    echo ""
    echo "Examples:"
    echo "  $0 dev                    # Start development environment"
    echo "  $0 staging               # Start staging environment"
    echo "  $0 production            # Start production environment"
    echo "  $0 testing               # Start testing environment"
    echo "  $0 performance           # Start performance testing"
    echo "  $0 monitoring            # Add monitoring to current environment"
}

# Check if environment is specified
if [ $# -eq 0 ]; then
    usage
    exit 1
fi

ENVIRONMENT=$1

case $ENVIRONMENT in
    "dev"|"development")
        echo "🔧 Starting Development Environment..."
        docker-compose up -d
        echo "✅ Development environment started!"
        echo "📊 Services available:"
        echo "   - OpenWebUI: http://localhost:3030"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        ;;
    
    "staging")
        echo "🏗️ Starting Staging Environment..."
        docker-compose -f docker-compose.staging.yml up -d
        echo "✅ Staging environment started!"
        echo "📊 Services available:"
        echo "   - OpenWebUI: http://localhost:3030"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        ;;
    
    "production")
        echo "🚀 Starting Production Environment..."
        docker-compose -f docker-compose.production.yml up -d
        echo "✅ Production environment started!"
        echo "📊 Services available:"
        echo "   - OpenWebUI: http://localhost:3030"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        ;;
    
    "testing")
        echo "🧪 Starting Testing Environment..."
        docker-compose -f docker-compose.allure.yml up -d
        echo "✅ Testing environment started!"
        echo "📊 Services available:"
        echo "   - Allure Results: http://localhost:5050"
        echo "   - Allure Reports: http://localhost:8080"
        echo ""
        echo "🧪 To run tests:"
        echo "   python3 scripts/run_tests_with_allure.py --type all --serve"
        ;;
    
    "performance")
        echo "⚡ Starting Performance Testing Environment..."
        docker-compose -f docker-compose.jmeter.yml up -d
        echo "✅ Performance testing environment started!"
        echo "📊 Services available:"
        echo "   - JMeter: Available for load testing"
        echo ""
        echo "⚡ To run performance tests:"
        echo "   python3 scripts/run_jmeter_tests.py --test all"
        ;;
    
    "monitoring")
        echo "📊 Adding Monitoring (ELK Stack)..."
        docker-compose -f docker-compose.yml -f docker-compose.elk.yml up -d
        echo "✅ Monitoring environment started!"
        echo "📊 Services available:"
        echo "   - Kibana: http://localhost:5601"
        echo "   - Elasticsearch: http://localhost:9200"
        echo "   - Logstash: http://localhost:9600"
        ;;
    
    "optimized")
        echo "🎯 Starting Optimized Environment..."
        docker-compose -f docker-compose.optimized.yml up -d
        echo "✅ Optimized environment started!"
        echo "📊 Services available:"
        echo "   - OpenWebUI: http://localhost:3030"
        echo "   - LiteLLM: http://localhost:4000"
        echo "   - Multimodal Worker: http://localhost:8001"
        echo "   - Retrieval Proxy: http://localhost:8002"
        ;;
    
    *)
        echo "❌ Unknown environment: $ENVIRONMENT"
        usage
        exit 1
        ;;
esac

echo ""
echo "🔍 To check service status:"
echo "   docker-compose ps"
echo ""
echo "📋 To view logs:"
echo "   docker-compose logs -f [service-name]"
echo ""
echo "🛑 To stop environment:"
echo "   docker-compose down"
