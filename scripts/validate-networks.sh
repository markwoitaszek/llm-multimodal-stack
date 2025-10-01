#!/bin/bash

# Network Validation Script
# Comprehensive network validation for stack deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SCHEMA_FILE="$PROJECT_ROOT/schemas/compose-schema.yaml"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print section headers
print_section() {
    echo ""
    print_status "$BLUE" "=== $1 ==="
    echo ""
}

# Function to validate network configuration
validate_network_config() {
    print_section "Network Configuration Validation"
    
    if [ ! -f "$SCHEMA_FILE" ]; then
        print_status "$RED" "❌ Schema file not found: $SCHEMA_FILE"
        return 1
    fi
    
    # Validate schema syntax
    if ! python3 -c "import yaml; yaml.safe_load(open('$SCHEMA_FILE'))" >/dev/null 2>&1; then
        print_status "$RED" "❌ Invalid YAML syntax in schema file"
        return 1
    fi
    
    print_status "$GREEN" "✅ Schema file syntax is valid"
    
    # Extract and validate stack networks
    local stack_networks
    stack_networks=$(python3 -c "
import yaml
import sys

try:
    with open('$SCHEMA_FILE', 'r') as f:
        schema = yaml.safe_load(f)
    
    stack_networks = schema.get('stack_networks', {})
    
    if not stack_networks:
        print('ERROR: No stack networks defined in schema')
        sys.exit(1)
    
    for network_name, config in stack_networks.items():
        if 'driver' not in config:
            print(f'ERROR: Network {network_name} missing driver')
            sys.exit(1)
        
        if 'ipam' not in config:
            print(f'ERROR: Network {network_name} missing IPAM configuration')
            sys.exit(1)
        
        if 'config' not in config['ipam']:
            print(f'ERROR: Network {network_name} missing IPAM config')
            sys.exit(1)
        
        for ipam_config in config['ipam']['config']:
            if 'subnet' not in ipam_config:
                print(f'ERROR: Network {network_name} missing subnet')
                sys.exit(1)
            
            subnet = ipam_config['subnet']
            if not subnet or not '/' in subnet:
                print(f'ERROR: Network {network_name} has invalid subnet: {subnet}')
                sys.exit(1)
            
            print(f'{network_name}:{subnet}')
    
    print('SUCCESS: All network configurations are valid')
    
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        print_status "$RED" "❌ Network configuration validation failed"
        echo "$stack_networks"
        return 1
    fi
    
    print_status "$GREEN" "✅ All network configurations are valid"
    return 0
}

# Function to check network connectivity
check_network_connectivity() {
    print_section "Network Connectivity Tests"
    
    local connectivity_issues=0
    
    # Test Docker daemon connectivity
    if ! docker info >/dev/null 2>&1; then
        print_status "$RED" "❌ Cannot connect to Docker daemon"
        connectivity_issues=1
    else
        print_status "$GREEN" "✅ Docker daemon is accessible"
    fi
    
    # Test network creation capability
    local test_network_name="multimodal-test-$(date +%s)"
    if docker network create "$test_network_name" >/dev/null 2>&1; then
        docker network rm "$test_network_name" >/dev/null 2>&1
        print_status "$GREEN" "✅ Network creation capability verified"
    else
        print_status "$RED" "❌ Cannot create networks"
        connectivity_issues=1
    fi
    
    # Test port availability for key services
    local ports_to_check=("5432" "6379" "8000" "8001" "8002" "8003" "8004" "8005" "9000" "9001" "6333" "6334")
    
    print_status "$YELLOW" "🔍 Checking port availability..."
    for port in "${ports_to_check[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            print_status "$YELLOW" "   Port $port: In use"
        else
            print_status "$GREEN" "   Port $port: Available"
        fi
    done
    
    if [ $connectivity_issues -eq 1 ]; then
        return 1
    fi
    
    print_status "$GREEN" "✅ Network connectivity tests passed"
    return 0
}

# Function to validate stack dependencies
validate_stack_dependencies() {
    print_section "Stack Dependencies Validation"
    
    local stack_deps
    stack_deps=$(python3 -c "
import yaml
import sys

try:
    with open('$SCHEMA_FILE', 'r') as f:
        schema = yaml.safe_load(f)
    
    stacks = schema.get('stacks', {})
    
    for stack_name, stack_config in stacks.items():
        dependencies = stack_config.get('dependencies', [])
        services = stack_config.get('services', [])
        
        # Convert lists to comma-separated strings
        deps_str = ','.join(dependencies) if dependencies else ''
        services_str = ','.join(services) if services else ''
        
        print(f'{stack_name}:{deps_str}:{services_str}')
    
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        print_status "$RED" "❌ Failed to validate stack dependencies"
        return 1
    fi
    
    local dependency_issues=0
    
    while IFS= read -r dep_info; do
        if [ -z "$dep_info" ]; then
            continue
        fi
        
        local stack_name=$(echo "$dep_info" | cut -d':' -f1)
        local dependencies=$(echo "$dep_info" | cut -d':' -f2)
        local services=$(echo "$dep_info" | cut -d':' -f3)
        
        # Check if dependencies exist as stacks
        if [ -n "$dependencies" ]; then
            IFS=',' read -ra deps_array <<< "$dependencies"
            for dep in "${deps_array[@]}"; do
                if [ -n "$dep" ] && ! echo "$stack_deps" | grep -q "^$dep:"; then
                    print_status "$RED" "❌ Stack '$stack_name' depends on non-existent stack '$dep'"
                    dependency_issues=1
                fi
            done
        fi
        
        # Check if services exist in schema
        if [ -n "$services" ]; then
            IFS=',' read -ra services_array <<< "$services"
            for service in "${services_array[@]}"; do
                if [ -n "$service" ]; then
                    local service_exists
                    service_exists=$(python3 -c "
import yaml
with open('$SCHEMA_FILE', 'r') as f:
    schema = yaml.safe_load(f)
if '$service' in schema.get('services', {}):
    print('EXISTS')
else:
    print('MISSING')
" 2>/dev/null)
                    
                    if [ "$service_exists" = "MISSING" ]; then
                        print_status "$RED" "❌ Stack '$stack_name' references non-existent service '$service'"
                        dependency_issues=1
                    fi
                fi
            done
        fi
    done <<< "$stack_deps"
    
    if [ $dependency_issues -eq 1 ]; then
        return 1
    fi
    
    print_status "$GREEN" "✅ All stack dependencies are valid"
    return 0
}

# Function to generate network report
generate_network_report() {
    print_section "Network Configuration Report"
    
    print_status "$BLUE" "Stack Networks:"
    python3 -c "
import yaml
with open('$SCHEMA_FILE', 'r') as f:
    schema = yaml.safe_load(f)

stack_networks = schema.get('stack_networks', {})
for network_name, config in stack_networks.items():
    if 'ipam' in config and 'config' in config['ipam']:
        for ipam_config in config['ipam']['config']:
            if 'subnet' in ipam_config:
                print(f'  {network_name}: {ipam_config[\"subnet\"]}')
" 2>/dev/null
    
    echo ""
    print_status "$BLUE" "Stack Dependencies:"
    python3 -c "
import yaml
with open('$SCHEMA_FILE', 'r') as f:
    schema = yaml.safe_load(f)

stacks = schema.get('stacks', {})
for stack_name, stack_config in stacks.items():
    dependencies = stack_config.get('dependencies', [])
    services = stack_config.get('services', [])
    print(f'  {stack_name}:')
    print(f'    Dependencies: {dependencies}')
    print(f'    Services: {len(services)} services')
" 2>/dev/null
}

# Main function
main() {
    print_status "$BLUE" "🌐 Network Validation and Health Check"
    print_status "$BLUE" "======================================"
    
    local validation_failed=0
    
    # Run all validation checks
    if ! validate_network_config; then
        validation_failed=1
    fi
    
    if ! check_network_connectivity; then
        validation_failed=1
    fi
    
    if ! validate_stack_dependencies; then
        validation_failed=1
    fi
    
    # Generate report
    generate_network_report
    
    if [ $validation_failed -eq 1 ]; then
        print_status "$RED" "❌ Network validation failed!"
        print_status "$RED" "Please resolve the issues above before starting stacks."
        exit 1
    fi
    
    print_status "$GREEN" "✅ All network validations passed!"
    print_status "$GREEN" "✅ Networks are ready for stack deployment"
}

# Handle command line arguments
case "${1:-validate}" in
    "validate")
        main
        ;;
    "report")
        generate_network_report
        ;;
    "connectivity")
        check_network_connectivity
        ;;
    "dependencies")
        validate_stack_dependencies
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [validate|report|connectivity|dependencies|help]"
        echo ""
        echo "Commands:"
        echo "  validate     - Run all network validations (default)"
        echo "  report       - Generate network configuration report"
        echo "  connectivity - Test network connectivity only"
        echo "  dependencies - Validate stack dependencies only"
        echo "  help         - Show this help message"
        ;;
    *)
        print_status "$RED" "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
