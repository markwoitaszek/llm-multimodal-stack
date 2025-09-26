#!/bin/bash

# Test script for multimodal capabilities
echo "🧪 Testing Multimodal LLM Stack..."

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

# Test files directory
TEST_DIR="./test_files"
mkdir -p "$TEST_DIR"

# Function to test API endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    local expected_status=${5:-200}
    
    echo -n "Testing $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" -o /tmp/test_response "$url")
    else
        response=$(curl -s -w "%{http_code}" -o /tmp/test_response -X "$method" \
                   -H "Content-Type: application/json" \
                   -d "$data" "$url")
    fi
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✅ Passed${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed (HTTP $response)${NC}"
        echo "Response: $(cat /tmp/test_response)"
        return 1
    fi
}

# Function to create test image
create_test_image() {
    local filename="$TEST_DIR/test_image.jpg"
    
    if command -v convert &> /dev/null; then
        # Create a simple test image using ImageMagick
        convert -size 300x200 xc:blue -fill white -gravity center \
                -annotate +0+0 "Test Image" "$filename"
        echo "$filename"
    elif command -v python3 &> /dev/null; then
        # Create test image using Python
        python3 -c "
from PIL import Image, ImageDraw, ImageFont
import os
img = Image.new('RGB', (300, 200), color='blue')
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.load_default()
    draw.text((150, 100), 'Test Image', fill='white', anchor='mm', font=font)
except:
    draw.text((120, 90), 'Test Image', fill='white')
img.save('$filename')
print('$filename')
"
        echo "$filename"
    else
        echo ""
    fi
}

echo ""
echo -e "${BLUE}🔍 Testing Service Endpoints${NC}"
echo "================================"

# Test basic health endpoints
test_endpoint "Multimodal Worker Health" "GET" "$MULTIMODAL_WORKER_URL/health"
test_endpoint "Retrieval Proxy Health" "GET" "$RETRIEVAL_PROXY_URL/health" 
test_endpoint "LiteLLM Health" "GET" "$LITELLM_URL/health"

echo ""
echo -e "${BLUE}📊 Testing Status Endpoints${NC}"
echo "================================"

# Test status endpoints
test_endpoint "Multimodal Worker Models Status" "GET" "$MULTIMODAL_WORKER_URL/api/v1/models/status"
test_endpoint "Multimodal Worker Storage Status" "GET" "$MULTIMODAL_WORKER_URL/api/v1/storage/status"
test_endpoint "Retrieval Proxy Status" "GET" "$RETRIEVAL_PROXY_URL/api/v1/status"
test_endpoint "Retrieval Proxy Stats" "GET" "$RETRIEVAL_PROXY_URL/api/v1/stats"

echo ""
echo -e "${BLUE}📝 Testing Text Processing${NC}"
echo "================================"

# Test text processing
text_data='{
    "text": "This is a test document about artificial intelligence and machine learning. It contains information about neural networks, deep learning, and natural language processing.",
    "document_name": "test_document.txt",
    "metadata": {"test": true, "category": "AI"}
}'

test_endpoint "Text Processing" "POST" "$MULTIMODAL_WORKER_URL/api/v1/process/text" "$text_data"

echo ""
echo -e "${BLUE}🖼️  Testing Image Processing${NC}"
echo "================================"

# Create test image
echo "Creating test image..."
test_image=$(create_test_image)

if [ -n "$test_image" ] && [ -f "$test_image" ]; then
    echo "Test image created: $test_image"
    
    # Test image upload (this would need to be a multipart form request)
    echo -n "Testing Image Upload... "
    response=$(curl -s -w "%{http_code}" -o /tmp/test_response \
               -X POST \
               -F "file=@$test_image" \
               -F "document_name=test_image.jpg" \
               "$MULTIMODAL_WORKER_URL/api/v1/process/image")
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ Passed${NC}"
    else
        echo -e "${RED}❌ Failed (HTTP $response)${NC}"
        echo "Response: $(cat /tmp/test_response)"
    fi
else
    echo -e "${YELLOW}⚠️  Skipping image tests (no image creation tools available)${NC}"
fi

echo ""
echo -e "${BLUE}🔍 Testing Search Functionality${NC}"
echo "================================"

# Test search
search_data='{
    "query": "artificial intelligence machine learning",
    "modalities": ["text"],
    "limit": 5
}'

test_endpoint "Text Search" "POST" "$RETRIEVAL_PROXY_URL/api/v1/search" "$search_data"

# Test search sessions
test_endpoint "Search Sessions" "GET" "$RETRIEVAL_PROXY_URL/api/v1/search/sessions?limit=5"

echo ""
echo -e "${BLUE}🤖 Testing LLM Integration${NC}"
echo "================================"

# Test LiteLLM chat completion
llm_data='{
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 50
}'

test_endpoint "LLM Chat Completion" "POST" "$LITELLM_URL/v1/chat/completions" "$llm_data"

echo ""
echo -e "${BLUE}📈 Performance Tests${NC}"
echo "================================"

# Simple performance test
echo -n "Testing concurrent requests... "
start_time=$(date +%s)

# Run 5 concurrent health checks
for i in {1..5}; do
    curl -s "$MULTIMODAL_WORKER_URL/health" > /dev/null &
done
wait

end_time=$(date +%s)
duration=$((end_time - start_time))

if [ $duration -lt 5 ]; then
    echo -e "${GREEN}✅ Passed (${duration}s)${NC}"
else
    echo -e "${YELLOW}⚠️  Slow (${duration}s)${NC}"
fi

echo ""
echo -e "${BLUE}🧹 Cleanup${NC}"
echo "================================"

# Cleanup test files
if [ -d "$TEST_DIR" ]; then
    rm -rf "$TEST_DIR"
    echo "Cleaned up test files"
fi

rm -f /tmp/test_response

echo ""
echo "🎉 Testing completed!"
echo ""
echo "💡 Tips:"
echo "- Check docker-compose logs if any tests failed"
echo "- Use scripts/health-check.sh for detailed health status"
echo "- Visit http://localhost:3000 for the web interface"
echo "- API documentation available at:"
echo "  - Multimodal Worker: http://localhost:8001/docs"
echo "  - Retrieval Proxy: http://localhost:8002/docs"

