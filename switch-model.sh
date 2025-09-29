#!/bin/bash

# Model Switching Script for vLLM
# This script demonstrates how to easily switch between different model configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== vLLM Model Configuration Switcher ===${NC}"
echo

# Function to show current configuration
show_current() {
    echo -e "${YELLOW}Current Configuration:${NC}"
    echo "Model: $(docker-compose -f docker-compose.yml -f docker-compose.multi-gpu-optimized.yml config | grep -A 1 "VLLM_MODEL" | tail -1 | cut -d: -f2 | tr -d ' ')"
    echo "GPU Memory Utilization: $(docker-compose -f docker-compose.yml -f docker-compose.multi-gpu-optimized.yml config | grep -A 1 "VLLM_GPU_MEMORY_UTILIZATION" | tail -1 | cut -d: -f2 | tr -d ' ')"
    echo "Max Model Length: $(docker-compose -f docker-compose.yml -f docker-compose.multi-gpu-optimized.yml config | grep -A 1 "VLLM_MAX_MODEL_LEN" | tail -1 | cut -d: -f2 | tr -d ' ')"
    echo "Max Sequences: $(docker-compose -f docker-compose.yml -f docker-compose.multi-gpu-optimized.yml config | grep -A 1 "VLLM_MAX_NUM_SEQS" | tail -1 | cut -d: -f2 | tr -d ' ')"
    echo
}

# Function to show available configurations
show_configs() {
    echo -e "${YELLOW}Available Model Configurations:${NC}"
    echo "1. DialoGPT-large (Small, ~1.5GB) - Memory: 30%, Context: 1024, Batch: 8"
    echo "2. Llama-2-7b-chat (Medium, ~13GB) - Memory: 60%, Context: 4096, Batch: 8"
    echo "3. Mistral-7B-Instruct (Medium, ~13GB) - Memory: 50%, Context: 8192, Batch: 8"
    echo "4. CodeLlama-7b-Instruct (Medium, ~13GB) - Memory: 60%, Context: 16384, Batch: 4"
    echo "5. Llama-2-13b-chat (Large, ~26GB) - Memory: 80%, Context: 4096, Batch: 4"
    echo "6. Custom configuration"
    echo
}

# Function to apply configuration
apply_config() {
    local model=$1
    local memory=$2
    local context=$3
    local batch=$4
    
    echo -e "${YELLOW}Applying configuration...${NC}"
    echo "Model: $model"
    echo "GPU Memory Utilization: $memory"
    echo "Max Model Length: $context"
    echo "Max Sequences: $batch"
    echo
    
    # Stop current stack
    echo -e "${BLUE}Stopping current stack...${NC}"
    docker-compose -f docker-compose.yml -f docker-compose.multi-gpu-optimized.yml down
    
    # Start with new configuration
    echo -e "${BLUE}Starting with new configuration...${NC}"
    VLLM_MODEL="$model" \
    VLLM_GPU_MEMORY_UTILIZATION="$memory" \
    VLLM_MAX_MODEL_LEN="$context" \
    VLLM_MAX_NUM_SEQS="$batch" \
    docker-compose -f docker-compose.yml -f docker-compose.multi-gpu-optimized.yml up -d
    
    echo -e "${GREEN}Configuration applied successfully!${NC}"
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 30
    
    # Show GPU usage
    echo -e "${BLUE}Current GPU Usage:${NC}"
    nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv,noheader,nounits
    echo
}

# Main menu
case "${1:-menu}" in
    "1"|"dialogpt")
        apply_config "microsoft/DialoGPT-large" "0.3" "1024" "8"
        ;;
    "2"|"llama2-7b")
        apply_config "meta-llama/Llama-2-7b-chat-hf" "0.6" "4096" "8"
        ;;
    "3"|"mistral-7b")
        apply_config "mistralai/Mistral-7B-Instruct-v0.1" "0.5" "8192" "8"
        ;;
    "4"|"codellama-7b")
        apply_config "codellama/CodeLlama-7b-Instruct-hf" "0.6" "16384" "4"
        ;;
    "5"|"llama2-13b")
        apply_config "meta-llama/Llama-2-13b-chat-hf" "0.8" "4096" "4"
        ;;
    "6"|"custom")
        echo -e "${YELLOW}Custom Configuration:${NC}"
        read -p "Model name: " model
        read -p "GPU Memory Utilization (0.1-0.9): " memory
        read -p "Max Model Length: " context
        read -p "Max Sequences: " batch
        apply_config "$model" "$memory" "$context" "$batch"
        ;;
    "status"|"current")
        show_current
        ;;
    "menu"|*)
        show_current
        show_configs
        echo -e "${YELLOW}Usage:${NC}"
        echo "  $0 [1-6|model-name]  - Apply configuration"
        echo "  $0 status           - Show current configuration"
        echo "  $0 menu             - Show this menu"
        echo
        echo -e "${YELLOW}Examples:${NC}"
        echo "  $0 1                # Switch to DialoGPT-large"
        echo "  $0 llama2-7b        # Switch to Llama-2-7b"
        echo "  $0 custom           # Set custom configuration"
        ;;
esac
