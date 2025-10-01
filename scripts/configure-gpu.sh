#!/bin/bash

# GPU Configuration Script
# Helps users configure the appropriate GPU setup for their system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== GPU Configuration Setup ===${NC}"
echo

# Function to detect GPU configuration
detect_gpu_config() {
    echo -e "${YELLOW}Detecting GPU configuration...${NC}"
    
    if ! command -v nvidia-smi &> /dev/null; then
        echo -e "${RED}❌ NVIDIA GPU not detected${NC}"
        echo "   This system does not have NVIDIA GPUs or nvidia-smi is not available."
        echo "   The system will run in CPU-only mode."
        return 1
    fi
    
    gpu_count=$(nvidia-smi --list-gpus 2>/dev/null | wc -l)
    echo -e "${GREEN}✅ Found $gpu_count NVIDIA GPU(s)${NC}"
    
    if [ "$gpu_count" -ge 2 ]; then
        echo -e "${GREEN}✅ Multi-GPU setup detected${NC}"
        
        # Check NVLink topology
        if nvidia-smi topo -m &> /dev/null; then
            echo -e "${BLUE}🔗 NVLink Topology:${NC}"
            nvidia-smi topo -m | grep -E "(NV[0-9]|NODE)" | head -5
        fi
        
        return 2  # Multi-GPU
    else
        echo -e "${YELLOW}⚠️  Single GPU setup detected${NC}"
        return 1  # Single GPU
    fi
}

# Function to configure multi-GPU
configure_multi_gpu() {
    echo -e "${GREEN}Configuring Multi-GPU Setup (Dual RTX 3090)${NC}"
    echo
    
    # Set environment variables for multi-GPU
    export CUDA_VISIBLE_DEVICES="0,1"
    export NVIDIA_VISIBLE_DEVICES="0,1"
    export CUDA_DEVICE_ORDER="PCI_BUS_ID"
    export VLLM_TENSOR_PARALLEL_SIZE="2"
    export VLLM_PIPELINE_PARALLEL_SIZE="1"
    export GPU_COUNT="2"
    
    echo "Environment variables set:"
    echo "  CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
    echo "  NVIDIA_VISIBLE_DEVICES=$NVIDIA_VISIBLE_DEVICES"
    echo "  CUDA_DEVICE_ORDER=$CUDA_DEVICE_ORDER"
    echo "  VLLM_TENSOR_PARALLEL_SIZE=$VLLM_TENSOR_PARALLEL_SIZE"
    echo "  VLLM_PIPELINE_PARALLEL_SIZE=$VLLM_PIPELINE_PARALLEL_SIZE"
    echo "  GPU_COUNT=$GPU_COUNT"
    echo
    
    echo -e "${YELLOW}Recommended Docker Compose command:${NC}"
    echo "  docker-compose -f docker-compose.yml -f docker-compose.multi-gpu.yml up -d"
    echo
    
    echo -e "${BLUE}NVLink Optimization Details:${NC}"
    echo "  - Tensor parallelism across both GPUs"
    echo "  - PCI_BUS_ID device ordering for optimal NVLink usage"
    echo "  - Increased GPU memory utilization (0.8-0.9)"
    echo "  - Enhanced worker processes for better throughput"
}

# Function to configure single GPU
configure_single_gpu() {
    echo -e "${YELLOW}Configuring Single GPU Setup${NC}"
    echo
    
    # Set environment variables for single GPU
    export CUDA_VISIBLE_DEVICES="0"
    export NVIDIA_VISIBLE_DEVICES="0"
    export CUDA_DEVICE_ORDER="PCI_BUS_ID"
    export VLLM_TENSOR_PARALLEL_SIZE="1"
    export VLLM_PIPELINE_PARALLEL_SIZE="1"
    export GPU_COUNT="1"
    
    echo "Environment variables set:"
    echo "  CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
    echo "  NVIDIA_VISIBLE_DEVICES=$NVIDIA_VISIBLE_DEVICES"
    echo "  CUDA_DEVICE_ORDER=$CUDA_DEVICE_ORDER"
    echo "  VLLM_TENSOR_PARALLEL_SIZE=$VLLM_TENSOR_PARALLEL_SIZE"
    echo "  VLLM_PIPELINE_PARALLEL_SIZE=$VLLM_PIPELINE_PARALLEL_SIZE"
    echo "  GPU_COUNT=$GPU_COUNT"
    echo
    
    echo -e "${YELLOW}Recommended Docker Compose command:${NC}"
    echo "  docker-compose -f docker-compose.yml -f docker-compose.single-gpu.yml up -d"
    echo
    
    echo -e "${BLUE}Single GPU Optimization:${NC}"
    echo "  - Reduced worker processes to fit single GPU memory"
    echo "  - Optimized memory utilization"
    echo "  - Suitable for development and testing"
}

# Function to configure CPU-only
configure_cpu_only() {
    echo -e "${RED}Configuring CPU-Only Setup${NC}"
    echo
    
    echo -e "${YELLOW}⚠️  Warning: CPU-only mode will have significantly reduced performance${NC}"
    echo "  - No GPU acceleration"
    echo "  - Limited model capabilities"
    echo "  - Suitable only for testing and development"
    echo
    
    echo -e "${YELLOW}Recommended for CI/CD pipelines:${NC}"
    echo "  docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d"
}

# Main configuration logic
case "${1:-auto}" in
    "auto"|"detect")
        # Temporarily disable exit on error to capture return codes
        set +e
        detect_gpu_config
        gpu_status=$?
        set -e
        
        case $gpu_status in
            2)
                configure_multi_gpu
                ;;
            1)
                configure_single_gpu
                ;;
            *)
                configure_cpu_only
                ;;
        esac
        ;;
    
    "multi"|"dual")
        configure_multi_gpu
        ;;
    
    "single"|"one")
        configure_single_gpu
        ;;
    
    "cpu"|"none")
        configure_cpu_only
        ;;
    
    "help"|"-h"|"--help")
        echo -e "${BLUE}GPU Configuration Script${NC}"
        echo
        echo "Usage: $0 [option]"
        echo
        echo "Options:"
        echo "  auto, detect  - Automatically detect and configure GPU setup (default)"
        echo "  multi, dual   - Force multi-GPU configuration"
        echo "  single, one   - Force single GPU configuration"
        echo "  cpu, none     - Configure for CPU-only mode"
        echo "  help, -h      - Show this help message"
        echo
        echo "Examples:"
        echo "  $0                    # Auto-detect GPU configuration"
        echo "  $0 multi              # Force multi-GPU setup"
        echo "  $0 single             # Force single GPU setup"
        echo "  $0 cpu                # CPU-only mode for CI/CD"
        ;;
    
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac

echo
echo -e "${GREEN}✅ GPU configuration complete!${NC}"
echo -e "${YELLOW}💡 Tip: You can also set these environment variables in your .env files${NC}"
