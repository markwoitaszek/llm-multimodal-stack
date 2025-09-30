#!/bin/bash
# Environment Configuration Validator
# Validates all environment configurations for consistency and completeness

set -e

echo "🔍 Environment Configuration Validator"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    case $status in
        "PASS")
            echo -e "${GREEN}✅ PASS${NC}: $message"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            ;;
        "FAIL")
            echo -e "${RED}❌ FAIL${NC}: $message"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  WARN${NC}: $message"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  INFO${NC}: $message"
            ;;
    esac
}

# Function to check if file exists
check_file_exists() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        print_status "PASS" "$description exists: $file"
    else
        print_status "FAIL" "$description missing: $file"
    fi
}

# Function to check if directory exists
check_directory_exists() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        print_status "PASS" "$description exists: $dir"
    else
        print_status "FAIL" "$description missing: $dir"
    fi
}

# Function to check Docker Compose file syntax
check_compose_syntax() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        if docker-compose -f "$file" config >/dev/null 2>&1; then
            print_status "PASS" "$description syntax is valid: $file"
        else
            print_status "FAIL" "$description syntax is invalid: $file"
        fi
    else
        print_status "FAIL" "$description file not found: $file"
    fi
}

# Function to check environment variable consistency
check_env_consistency() {
    local env_file=$1
    local description=$2
    
    if [ -f "$env_file" ]; then
        # Check for required variables
        local required_vars=("POSTGRES_PASSWORD" "MINIO_ROOT_PASSWORD" "LITELLM_MASTER_KEY" "VLLM_API_KEY")
        local missing_vars=()
        
        for var in "${required_vars[@]}"; do
            if ! grep -q "^$var=" "$env_file"; then
                missing_vars+=("$var")
            fi
        done
        
        if [ ${#missing_vars[@]} -eq 0 ]; then
            print_status "PASS" "$description has all required variables"
        else
            print_status "FAIL" "$description missing variables: ${missing_vars[*]}"
        fi
        
        # Check for placeholder values
        if grep -q "your_secure_\|change-me\|placeholder" "$env_file"; then
            print_status "WARN" "$description contains placeholder values"
        else
            print_status "PASS" "$description has no placeholder values"
        fi
    else
        print_status "FAIL" "$description file not found: $env_file"
    fi
}

# Function to check port conflicts
check_port_conflicts() {
    local ports=("3030" "4000" "8000" "8001" "8002" "8003" "8004" "8005" "8006" "5432" "6379" "6333" "9000" "9002" "5678")
    local conflicting_ports=()
    
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            conflicting_ports+=("$port")
        fi
    done
    
    if [ ${#conflicting_ports[@]} -eq 0 ]; then
        print_status "PASS" "No port conflicts detected"
    else
        print_status "WARN" "Port conflicts detected: ${conflicting_ports[*]}"
    fi
}

# Function to check resource availability
check_resources() {
    # Check available memory
    local available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    local required_memory=8192  # 8GB minimum
    
    if [ "$available_memory" -ge "$required_memory" ]; then
        print_status "PASS" "Sufficient memory available: ${available_memory}MB"
    else
        print_status "WARN" "Low memory available: ${available_memory}MB (minimum: ${required_memory}MB)"
    fi
    
    # Check available disk space
    local available_disk=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
    local required_disk=20  # 20GB minimum
    
    if [ "$available_disk" -ge "$required_disk" ]; then
        print_status "PASS" "Sufficient disk space available: ${available_disk}GB"
    else
        print_status "WARN" "Low disk space available: ${available_disk}GB (minimum: ${required_disk}GB)"
    fi
}

# Function to check Docker and dependencies
check_dependencies() {
    # Check Docker
    if command -v docker &> /dev/null; then
        print_status "PASS" "Docker is installed"
        
        # Check if Docker daemon is running
        if docker info >/dev/null 2>&1; then
            print_status "PASS" "Docker daemon is running"
        else
            print_status "FAIL" "Docker daemon is not running"
        fi
    else
        print_status "FAIL" "Docker is not installed"
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        print_status "PASS" "Docker Compose is installed"
    else
        print_status "FAIL" "Docker Compose is not installed"
    fi
    
    # Check NVIDIA GPU for GPU-required environments
    if command -v nvidia-smi &> /dev/null; then
        print_status "PASS" "NVIDIA GPU is available"
    else
        print_status "WARN" "NVIDIA GPU not available (required for dev, staging, production, monitoring, optimized)"
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        print_status "PASS" "Python 3 is installed"
    else
        print_status "FAIL" "Python 3 is not installed"
    fi
}

# Function to check network configuration
check_network_config() {
    # Check if multimodal-net network exists
    if docker network ls | grep -q "multimodal-net"; then
        print_status "PASS" "multimodal-net network exists"
    else
        print_status "WARN" "multimodal-net network does not exist (will be created automatically)"
    fi
    
    # Check if test-network exists
    if docker network ls | grep -q "test-network"; then
        print_status "PASS" "test-network exists"
    else
        print_status "WARN" "test-network does not exist (will be created automatically)"
    fi
}

# Function to check volume configuration
check_volume_config() {
    local volumes=("qdrant_data" "postgres_data" "redis_data" "minio_data" "vllm_cache" "multimodal_cache" "openwebui_data" "n8n_data")
    local existing_volumes=()
    
    for volume in "${volumes[@]}"; do
        if docker volume ls | grep -q "$volume"; then
            existing_volumes+=("$volume")
        fi
    done
    
    if [ ${#existing_volumes[@]} -eq 0 ]; then
        print_status "PASS" "No existing volumes found (clean state)"
    else
        print_status "INFO" "Existing volumes found: ${existing_volumes[*]}"
    fi
}

# Main validation function
main() {
    echo ""
    print_status "INFO" "Starting environment validation..."
    echo ""
    
    # Check dependencies
    echo "🔧 Checking Dependencies..."
    check_dependencies
    echo ""
    
    # Check resources
    echo "💾 Checking System Resources..."
    check_resources
    echo ""
    
    # Check port conflicts
    echo "🌐 Checking Port Conflicts..."
    check_port_conflicts
    echo ""
    
    # Check network configuration
    echo "🔗 Checking Network Configuration..."
    check_network_config
    echo ""
    
    # Check volume configuration
    echo "💿 Checking Volume Configuration..."
    check_volume_config
    echo ""
    
    # Check core files
    echo "📄 Checking Core Files..."
    check_file_exists "start-environment.sh" "Startup script"
    check_file_exists "setup_secrets.py" "Secrets manager"
    check_file_exists "env.example" "Environment template"
    echo ""
    
    # Check Docker Compose files
    echo "🐳 Checking Docker Compose Files..."
    check_compose_syntax "docker-compose.yml" "Base compose file"
    check_compose_syntax "docker-compose.development.override.yml" "Development override"
    check_compose_syntax "docker-compose.staging.yml" "Staging compose file"
    check_compose_syntax "docker-compose.production.yml" "Production compose file"
    check_compose_syntax "docker-compose.allure.yml" "Testing compose file"
    check_compose_syntax "docker-compose.jmeter.yml" "Performance testing compose file"
    check_compose_syntax "docker-compose.elk.yml" "Monitoring compose file"
    check_compose_syntax "docker-compose.optimized.yml" "Optimized compose file"
    echo ""
    
    # Check environment files
    echo "🔐 Checking Environment Files..."
    check_env_consistency ".env.development" "Development environment"
    check_env_consistency ".env.staging" "Staging environment"
    check_env_consistency ".env.production" "Production environment"
    check_env_consistency ".env.monitoring" "Monitoring environment"
    check_env_consistency ".env.optimized" "Optimized environment"
    echo ""
    
    # Check configuration files
    echo "⚙️  Checking Configuration Files..."
    check_file_exists "configs/litellm_simple.yaml" "LiteLLM simple config"
    check_file_exists "configs/litellm_config.yaml" "LiteLLM production config"
    check_file_exists "configs/litellm_optimized.yaml" "LiteLLM optimized config"
    check_file_exists "configs/nginx.conf" "Nginx config"
    check_file_exists "configs/nginx_optimized.conf" "Nginx optimized config"
    echo ""
    
    # Check directories
    echo "📁 Checking Required Directories..."
    check_directory_exists "models" "Models directory"
    check_directory_exists "configs" "Configs directory"
    check_directory_exists "scripts" "Scripts directory"
    check_directory_exists "services" "Services directory"
    echo ""
    
    # Summary
    echo "📊 Validation Summary"
    echo "==================="
    echo "Total checks: $TOTAL_CHECKS"
    echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
    echo -e "${YELLOW}Warnings: $WARNING_CHECKS${NC}"
    echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
    echo ""
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        if [ $WARNING_CHECKS -eq 0 ]; then
            echo -e "${GREEN}🎉 All checks passed! Environment is ready for deployment.${NC}"
            exit 0
        else
            echo -e "${YELLOW}⚠️  Environment is ready but has warnings. Review warnings before deployment.${NC}"
            exit 0
        fi
    else
        echo -e "${RED}❌ Environment has critical issues. Fix failed checks before deployment.${NC}"
        exit 1
    fi
}

# Run main function
main "$@"

