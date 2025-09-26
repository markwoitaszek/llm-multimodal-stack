#!/bin/bash

# Benchmark script for Multimodal LLM Stack
echo "📊 Benchmarking Multimodal LLM Stack Performance..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
MULTIMODAL_WORKER_URL="http://localhost:8001"
RETRIEVAL_PROXY_URL="http://localhost:8002"
LITELLM_URL="http://localhost:4000"

# Results file
RESULTS_FILE="benchmark_results_$(date +%Y%m%d_%H%M%S).json"

# Check if required tools are available
check_dependencies() {
    local missing_deps=()
    
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}⚠️  jq not found. Installing for better output formatting...${NC}"
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y jq
        elif command -v yum &> /dev/null; then
            sudo yum install -y jq
        else
            echo -e "${RED}❌ Could not install jq. Results will be in raw JSON.${NC}"
        fi
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing dependencies: ${missing_deps[*]}${NC}"
        exit 1
    fi
}

# Function to benchmark endpoint
benchmark_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    local iterations=${5:-10}
    
    echo -e "${BLUE}📈 Benchmarking $name${NC}"
    echo "URL: $url"
    echo "Iterations: $iterations"
    echo "Method: $method"
    echo ""
    
    local total_time=0
    local successful_requests=0
    local failed_requests=0
    local min_time=999999
    local max_time=0
    local times=()
    
    for ((i=1; i<=iterations; i++)); do
        echo -n "Request $i/$iterations... "
        
        local start_time=$(date +%s%N)
        
        if [ "$method" = "GET" ]; then
            local response=$(curl -s -w "%{http_code}" -o /dev/null "$url")
        else
            local response=$(curl -s -w "%{http_code}" -o /dev/null -X "$method" \
                           -H "Content-Type: application/json" \
                           -d "$data" "$url")
        fi
        
        local end_time=$(date +%s%N)
        local request_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
        
        if [[ "$response" =~ ^2[0-9][0-9]$ ]]; then
            successful_requests=$((successful_requests + 1))
            total_time=$((total_time + request_time))
            times+=($request_time)
            
            if [ $request_time -lt $min_time ]; then
                min_time=$request_time
            fi
            if [ $request_time -gt $max_time ]; then
                max_time=$request_time
            fi
            
            echo -e "${GREEN}✅ ${request_time}ms${NC}"
        else
            failed_requests=$((failed_requests + 1))
            echo -e "${RED}❌ HTTP $response${NC}"
        fi
    done
    
    # Calculate statistics
    local avg_time=0
    local success_rate=0
    if [ $successful_requests -gt 0 ]; then
        avg_time=$((total_time / successful_requests))
        success_rate=$(( (successful_requests * 100) / iterations ))
    fi
    
    # Calculate median
    local median=0
    if [ ${#times[@]} -gt 0 ]; then
        IFS=$'\n' sorted_times=($(sort -n <<<"${times[*]}"))
        local mid=$((${#sorted_times[@]} / 2))
        median=${sorted_times[$mid]}
    fi
    
    # Calculate percentiles
    local p95=0
    local p99=0
    if [ ${#times[@]} -gt 0 ]; then
        local p95_idx=$(( (${#sorted_times[@]} * 95) / 100 ))
        local p99_idx=$(( (${#sorted_times[@]} * 99) / 100 ))
        p95=${sorted_times[$p95_idx]}
        p99=${sorted_times[$p99_idx]}
    fi
    
    echo ""
    echo "Results:"
    echo "  Success Rate: ${success_rate}% ($successful_requests/$iterations)"
    echo "  Average Time: ${avg_time}ms"
    echo "  Median Time: ${median}ms"
    echo "  Min Time: ${min_time}ms"
    echo "  Max Time: ${max_time}ms"
    echo "  95th Percentile: ${p95}ms"
    echo "  99th Percentile: ${p99}ms"
    echo ""
    
    # Store results
    local result="{
        \"name\": \"$name\",
        \"url\": \"$url\",
        \"method\": \"$method\",
        \"iterations\": $iterations,
        \"successful_requests\": $successful_requests,
        \"failed_requests\": $failed_requests,
        \"success_rate\": $success_rate,
        \"avg_time_ms\": $avg_time,
        \"median_time_ms\": $median,
        \"min_time_ms\": $min_time,
        \"max_time_ms\": $max_time,
        \"p95_time_ms\": $p95,
        \"p99_time_ms\": $p99,
        \"timestamp\": \"$(date -Iseconds)\"
    }"
    
    echo "$result" >> "$RESULTS_FILE.tmp"
}

# Function to benchmark concurrent requests
benchmark_concurrent() {
    local name=$1
    local url=$2
    local concurrency=$3
    local total_requests=$4
    
    echo -e "${BLUE}🚀 Concurrent Benchmark: $name${NC}"
    echo "URL: $url"
    echo "Concurrency: $concurrency"
    echo "Total Requests: $total_requests"
    echo ""
    
    local start_time=$(date +%s)
    
    # Use xargs for concurrent requests
    seq 1 $total_requests | xargs -n1 -P$concurrency -I{} curl -s -o /dev/null -w "%{http_code}\n" "$url" > /tmp/concurrent_results.txt
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Analyze results
    local successful=$(grep -c "^2[0-9][0-9]$" /tmp/concurrent_results.txt || echo 0)
    local failed=$((total_requests - successful))
    local rps=0
    if [ $duration -gt 0 ]; then
        rps=$((total_requests / duration))
    fi
    
    echo "Results:"
    echo "  Duration: ${duration}s"
    echo "  Successful: $successful"
    echo "  Failed: $failed"
    echo "  Requests/sec: $rps"
    echo ""
    
    rm -f /tmp/concurrent_results.txt
}

# Main benchmarking
main() {
    check_dependencies
    
    echo -e "${GREEN}🎯 Starting Performance Benchmarks${NC}"
    echo "Results will be saved to: $RESULTS_FILE"
    echo ""
    
    # Initialize results file
    echo "{\"benchmarks\": [" > "$RESULTS_FILE.tmp"
    
    # Health check benchmarks
    benchmark_endpoint "Multimodal Worker Health" "GET" "$MULTIMODAL_WORKER_URL/health" "" 50
    echo "," >> "$RESULTS_FILE.tmp"
    
    benchmark_endpoint "Retrieval Proxy Health" "GET" "$RETRIEVAL_PROXY_URL/health" "" 50
    echo "," >> "$RESULTS_FILE.tmp"
    
    # Text processing benchmark
    local text_data='{
        "text": "This is a benchmark test for text processing performance. It contains multiple sentences to test the chunking and embedding generation capabilities of the system.",
        "document_name": "benchmark_test.txt"
    }'
    
    benchmark_endpoint "Text Processing" "POST" "$MULTIMODAL_WORKER_URL/api/v1/process/text" "$text_data" 10
    echo "," >> "$RESULTS_FILE.tmp"
    
    # Search benchmark
    local search_data='{
        "query": "benchmark test performance",
        "modalities": ["text"],
        "limit": 10
    }'
    
    benchmark_endpoint "Search" "POST" "$RETRIEVAL_PROXY_URL/api/v1/search" "$search_data" 20
    
    # Close JSON array
    echo "]}" >> "$RESULTS_FILE.tmp"
    
    # Format final results file
    if command -v jq &> /dev/null; then
        jq '.' "$RESULTS_FILE.tmp" > "$RESULTS_FILE"
        rm "$RESULTS_FILE.tmp"
    else
        mv "$RESULTS_FILE.tmp" "$RESULTS_FILE"
    fi
    
    echo -e "${GREEN}📈 Concurrent Load Testing${NC}"
    echo "================================"
    
    # Concurrent benchmarks
    benchmark_concurrent "Health Check Load" "$MULTIMODAL_WORKER_URL/health" 10 100
    benchmark_concurrent "Search Load" "$RETRIEVAL_PROXY_URL/api/v1/stats" 5 50
    
    echo -e "${GREEN}🎉 Benchmarking Complete!${NC}"
    echo ""
    echo "Results saved to: $RESULTS_FILE"
    
    if command -v jq &> /dev/null; then
        echo ""
        echo "Summary:"
        echo "========"
        jq -r '.benchmarks[] | "- \(.name): \(.avg_time_ms)ms avg, \(.success_rate)% success"' "$RESULTS_FILE"
    fi
    
    echo ""
    echo "💡 Performance Tips:"
    echo "- Monitor GPU usage: nvidia-smi"
    echo "- Check Docker stats: docker stats"
    echo "- View service logs: docker-compose logs -f [service]"
    echo "- Scale services: docker-compose up -d --scale multimodal-worker=2"
}

# Run main function
main "$@"

