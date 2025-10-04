#!/bin/bash

# Credential Validation Script
# Validates environment credentials with strict/non-strict modes

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to validate credentials
validate_credentials() {
    local environment=${1:-development}
    local strict_mode=${2:-false}
    local env_file=""
    
    # Determine environment file
    case $environment in
        "development"|"dev")
            env_file=".env.development"
            ;;
        "staging")
            env_file=".env.staging"
            ;;
        "production"|"prod")
            env_file=".env.production"
            ;;
        *)
            print_status "$RED" "❌ Unknown environment: $environment"
            print_status "$YELLOW" "Available environments: development, staging, production"
            exit 1
            ;;
    esac
    
    print_status "$BLUE" "🔒 Validating credentials for $environment environment..."
    print_status "$CYAN" "Environment file: $env_file"
    print_status "$CYAN" "Strict mode: $strict_mode"
    echo ""
    
    if [ ! -f "$PROJECT_ROOT/$env_file" ]; then
        if [ "$strict_mode" = "true" ]; then
            print_status "$RED" "❌ Environment file not found: $env_file"
            exit 1
        else
            print_status "$YELLOW" "⚠️  Environment file not found: $env_file (creating default)"
            # Create a basic environment file
            cat > "$PROJECT_ROOT/$env_file" << EOF
# $environment Environment Configuration
POSTGRES_DB=multimodal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=changeme
JWT_SECRET_KEY=changeme
EOF
        fi
    fi
    
    # Load environment variables
    set -a
    source "$PROJECT_ROOT/$env_file" 2>/dev/null || true
    set +a
    
    local validation_failed=false
    
    # Required credentials to validate
    local required_vars=(
        "POSTGRES_DB"
        "POSTGRES_USER" 
        "POSTGRES_PASSWORD"
        "MINIO_ROOT_USER"
        "MINIO_ROOT_PASSWORD"
        "JWT_SECRET_KEY"
    )
    
    print_status "$YELLOW" "📋 Checking required credentials..."
    
    for var in "${required_vars[@]}"; do
        local value="${!var:-}"
        
        if [ -z "$value" ]; then
            if [ "$strict_mode" = "true" ]; then
                print_status "$RED" "❌ $var is not set"
                validation_failed=true
            else
                print_status "$YELLOW" "⚠️  $var is not set (using default)"
            fi
        elif [ "$value" = "changeme" ] || [ "$value" = "postgres" ] || [ "$value" = "minioadmin" ]; then
            # Allow default values for POSTGRES_USER and MINIO_ROOT_USER in staging
            if [ "$strict_mode" = "true" ] && [ "$environment" = "staging" ] && ([ "$var" = "POSTGRES_USER" ] || [ "$var" = "MINIO_ROOT_USER" ]); then
                print_status "$YELLOW" "⚠️  $var has default value: $value (allowed in staging)"
            elif [ "$strict_mode" = "true" ]; then
                print_status "$RED" "❌ $var has default value: $value"
                validation_failed=true
            else
                print_status "$YELLOW" "⚠️  $var has default value: $value"
            fi
        else
            print_status "$GREEN" "✅ $var is properly configured"
        fi
    done
    
    # GPU-specific validation (if GPU variables exist)
    local gpu_vars=(
        "CUDA_VISIBLE_DEVICES"
        "GPU_COUNT"
        "VLLM_TENSOR_PARALLEL_SIZE"
    )
    
    print_status "$YELLOW" "🎮 Checking GPU configuration..."
    
    local gpu_configured=false
    for var in "${gpu_vars[@]}"; do
        local value="${!var:-}"
        if [ -n "$value" ]; then
            print_status "$GREEN" "✅ $var: $value"
            gpu_configured=true
        fi
    done
    
    if [ "$gpu_configured" = "false" ]; then
        print_status "$YELLOW" "⚠️  No GPU configuration found (CPU-only mode)"
    fi
    
    echo ""
    
    if [ "$validation_failed" = "true" ]; then
        print_status "$RED" "❌ Credential validation failed!"
        print_status "$YELLOW" "💡 Run 'make setup-secrets-$environment' to generate proper credentials"
        exit 1
    else
        print_status "$GREEN" "✅ Credential validation passed!"
        if [ "$strict_mode" = "false" ]; then
            print_status "$YELLOW" "💡 For production, use strict mode: make validate-credentials ENV=$environment STRICT=true"
        fi
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [ENVIRONMENT] [STRICT]"
    echo ""
    echo "Arguments:"
    echo "  ENVIRONMENT    Target environment (development, staging, production)"
    echo "  STRICT         Strict validation mode (true, false)"
    echo ""
    echo "Examples:"
    echo "  $0 development false    # Non-strict validation for development"
    echo "  $0 staging true         # Strict validation for staging"
    echo "  $0 production true      # Strict validation for production"
    echo ""
    echo "Strict mode requirements:"
    echo "  • All credentials must be set"
    echo "  • No default values allowed"
    echo "  • Environment file must exist"
}

# Main function
main() {
    local environment=${1:-development}
    local strict=${2:-false}
    
    case $environment in
        "help"|"-h"|"--help")
            show_help
            exit 0
            ;;
    esac
    
    validate_credentials "$environment" "$strict"
}

# Run main function with all arguments
main "$@"