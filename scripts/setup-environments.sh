#!/bin/bash
# Schema-Driven Environment Setup Script
# Uses the environment schema to generate all environment configurations

set -e

echo "🔧 Schema-Driven Environment Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ SUCCESS${NC}: $message"
            ;;
        "ERROR")
            echo -e "${RED}❌ ERROR${NC}: $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  WARNING${NC}: $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  INFO${NC}: $message"
            ;;
    esac
}

# Function to check prerequisites
check_prerequisites() {
    echo ""
    print_status "INFO" "Checking prerequisites..."
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        print_status "ERROR" "Python 3 is not installed or not in PATH"
        exit 1
    fi
    print_status "SUCCESS" "Python 3 is available"
    
    # Check if schema file exists
    if [ ! -f "configs/environment_schema.yaml" ]; then
        print_status "ERROR" "Environment schema file not found: configs/environment_schema.yaml"
        exit 1
    fi
    print_status "SUCCESS" "Environment schema file found"
    
    # Check if secrets manager exists
    if [ ! -f "setup_secrets.py" ]; then
        print_status "ERROR" "Secrets manager not found: setup_secrets.py"
        exit 1
    fi
    print_status "SUCCESS" "Secrets manager found"
    
    # Check if PyYAML is available
    if ! python3 -c "import yaml" 2>/dev/null; then
        print_status "WARNING" "PyYAML not available, installing..."
        pip3 install PyYAML
    fi
    print_status "SUCCESS" "PyYAML is available"
}

# Function to validate schema
validate_schema() {
    echo ""
    print_status "INFO" "Validating environment schema..."
    
    # Basic YAML syntax validation
    if ! python3 -c "
import yaml
import sys
try:
    with open('configs/environment_schema.yaml', 'r') as f:
        schema = yaml.safe_load(f)
    if 'environments' not in schema:
        print('ERROR: No environments section found in schema')
        sys.exit(1)
    if 'secret_types' not in schema:
        print('ERROR: No secret_types section found in schema')
        sys.exit(1)
    print(f'SUCCESS: Schema validation passed. Found {len(schema[\"environments\"])} environments')
except Exception as e:
    print(f'ERROR: Schema validation failed: {e}')
    sys.exit(1)
"; then
        print_status "ERROR" "Schema validation failed"
        exit 1
    fi
    print_status "SUCCESS" "Schema validation passed"
}

# Function to generate environments
generate_environments() {
    echo ""
    print_status "INFO" "Generating environment configurations..."
    
    # Run the schema-driven secrets manager
    if python3 setup_secrets.py; then
        print_status "SUCCESS" "Environment configurations generated successfully"
    else
        print_status "ERROR" "Failed to generate environment configurations"
        exit 1
    fi
}

# Function to validate generated files
validate_generated_files() {
    echo ""
    print_status "INFO" "Validating generated files..."
    
    # Check for generated environment files
    local env_files=("development" "staging" "production" "testing" "performance" "monitoring" "optimized")
    local missing_files=()
    
    for env in "${env_files[@]}"; do
        if [ ! -f ".env.$env" ]; then
            missing_files+=("$env")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        print_status "SUCCESS" "All environment files generated"
    else
        print_status "WARNING" "Missing environment files: ${missing_files[*]}"
    fi
    
    # Check for generated secrets files
    if [ -d "secrets" ]; then
        local secrets_count=$(find secrets -name "*.json" | wc -l)
        print_status "SUCCESS" "Generated $secrets_count secrets files"
    else
        print_status "WARNING" "Secrets directory not found"
    fi
    
    # Check for generated Kubernetes secrets
    local k8s_files=$(find . -name "k8s-secrets-*.yaml" | wc -l)
    if [ "$k8s_files" -gt 0 ]; then
        print_status "SUCCESS" "Generated $k8s_files Kubernetes secrets files"
    else
        print_status "WARNING" "No Kubernetes secrets files generated"
    fi
}

# Function to display environment summary
display_environment_summary() {
    echo ""
    print_status "INFO" "Environment Summary"
    echo "=================="
    
    # Parse schema to show environment details
    python3 -c "
import yaml
import sys

try:
    with open('configs/environment_schema.yaml', 'r') as f:
        schema = yaml.safe_load(f)
    
    print('Available Environments:')
    print('-' * 50)
    
    for env_name, env_config in schema['environments'].items():
        description = env_config.get('description', 'No description')
        gpu_required = env_config.get('gpu_required', False)
        memory_min = env_config.get('memory_min_gb', 'Unknown')
        services = env_config.get('services', [])
        
        print(f'Environment: {env_name}')
        print(f'  Description: {description}')
        print(f'  GPU Required: {\"Yes\" if gpu_required else \"No\"}')
        print(f'  Memory Min: {memory_min}GB')
        print(f'  Services: {len(services)} services')
        print(f'  Files: .env.{env_name}, k8s-secrets-{env_name}.yaml')
        print()
        
except Exception as e:
    print(f'Error reading schema: {e}')
    sys.exit(1)
"
}

# Function to show next steps
show_next_steps() {
    echo ""
    print_status "INFO" "Next Steps"
    echo "=========="
    echo "1. Review the generated .env.{environment} files"
    echo "2. Customize any environment-specific settings if needed"
    echo "3. Run environment validation: ./scripts/validate-environment.sh"
    echo "4. Start your desired environment: ./start-environment.sh {environment}"
    echo ""
    echo "Available environments:"
    echo "  - development: Local development with debugging"
    echo "  - staging: Pre-production testing"
    echo "  - production: Production deployment with monitoring"
    echo "  - testing: Testing with Allure reports"
    echo "  - performance: Performance testing with JMeter"
    echo "  - monitoring: Monitoring with ELK stack"
    echo "  - optimized: High-performance optimized deployment"
    echo ""
    echo "Example usage:"
    echo "  ./start-environment.sh development"
    echo "  ./start-environment.sh production"
    echo "  ./start-environment.sh testing"
}

# Main function
main() {
    echo "Starting schema-driven environment setup..."
    
    check_prerequisites
    validate_schema
    generate_environments
    validate_generated_files
    display_environment_summary
    show_next_steps
    
    echo ""
    print_status "SUCCESS" "Schema-driven environment setup completed successfully!"
    echo ""
    print_status "INFO" "All environment configurations have been generated based on the schema"
    print_status "INFO" "The secrets manager now uses configs/environment_schema.yaml as the source of truth"
    print_status "INFO" "This approach ensures consistency and maintainability across all environments"
}

# Run main function
main "$@"

