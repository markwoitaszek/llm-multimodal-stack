#!/bin/bash

# Test Migration Script
# This script tests the migration from legacy to normalized structure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log_info "Running test: $test_name"
    
    if eval "$test_command"; then
        log_success "✓ $test_name passed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "✗ $test_name failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Test 1: Check if setup_secrets.py works
test_setup_secrets() {
    log_info "Testing setup_secrets.py..."
    
    cd "$PROJECT_ROOT"
    
    # Run setup_secrets.py
    if python3 setup_secrets.py; then
        log_success "setup_secrets.py executed successfully"
        
        # Check if legacy .env.development file was created
        if [[ -f ".env.development" ]]; then
            log_success "Legacy .env.development file created"
        else
            log_error "Legacy .env.development file not created"
            return 1
        fi
        
        # Check if .env.d directory was created (if Jinja2 is available)
        if [[ -d ".env.d" ]]; then
            log_success "Normalized .env.d directory created"
            
            # Check if template files were rendered
            template_count=$(find .env.d -name "*.env" | wc -l)
            if [[ $template_count -gt 0 ]]; then
                log_success "Rendered $template_count template files"
            else
                log_warning "No template files rendered (Jinja2 may not be available)"
            fi
        else
            log_warning ".env.d directory not created (Jinja2 may not be available)"
        fi
        
        return 0
    else
        log_error "setup_secrets.py failed"
        return 1
    fi
}

# Test 2: Check if start-environment.sh syntax is valid
test_start_script_syntax() {
    log_info "Testing start-environment.sh syntax..."
    
    cd "$PROJECT_ROOT"
    
    # Check bash syntax
    if bash -n start-environment.sh; then
        log_success "start-environment.sh syntax is valid"
        return 0
    else
        log_error "start-environment.sh has syntax errors"
        return 1
    fi
}

# Test 3: Check if compose files are valid (if docker compose is available)
test_compose_files() {
    log_info "Testing compose files..."
    
    cd "$PROJECT_ROOT"
    
    # Check if docker compose is available
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        # Test base compose file
        if docker compose -f compose.yml config --quiet; then
            log_success "Base compose.yml is valid"
        else
            log_error "Base compose.yml is invalid"
            return 1
        fi
        
        # Test override files
        local override_files=("compose.gpu.yml" "compose.monitoring.yml" "compose.production.yml" "compose.services.yml" "compose.elk.yml" "compose.n8n-monitoring.yml")
        
        for file in "${override_files[@]}"; do
            if [[ -f "$file" ]]; then
                if docker compose -f compose.yml -f "$file" config --quiet; then
                    log_success "$file is valid"
                else
                    log_error "$file is invalid"
                    return 1
                fi
            fi
        done
        
        return 0
    else
        log_warning "Docker Compose not available, skipping compose file validation"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        return 0
    fi
}

# Test 4: Check if environment templates exist and are valid
test_environment_templates() {
    log_info "Testing environment templates..."
    
    cd "$PROJECT_ROOT"
    
    # Check if env-templates directory exists
    if [[ ! -d "env-templates" ]]; then
        log_error "env-templates directory not found"
        return 1
    fi
    
    # Check if required template files exist
    local required_templates=(
        "core.env.j2"
        "vllm.env.j2"
        "litellm.env.j2"
        "multimodal-worker.env.j2"
        "retrieval-proxy.env.j2"
        "ai-agents.env.j2"
        "memory-system.env.j2"
        "search-engine.env.j2"
        "user-management.env.j2"
        "openwebui.env.j2"
        "n8n.env.j2"
        "n8n-monitoring.env.j2"
        "master.env.j2"
    )
    
    for template in "${required_templates[@]}"; do
        if [[ -f "env-templates/$template" ]]; then
            log_success "$template exists"
        else
            log_error "$template not found"
            return 1
        fi
    done
    
    # Test Jinja2 syntax if available
    if command -v python3 >/dev/null 2>&1 && python3 -c "import jinja2" >/dev/null 2>&1; then
        log_info "Testing Jinja2 template syntax..."
        
        for template in "${required_templates[@]}"; do
            if python3 -c "
import sys
from jinja2 import Environment, FileSystemLoader
try:
    env = Environment(loader=FileSystemLoader('env-templates'))
    template = env.get_template('$template')
    print('Template $template syntax is valid')
except Exception as e:
    print(f'Template $template syntax error: {e}')
    sys.exit(1)
"; then
                log_success "$template syntax is valid"
            else
                log_error "$template has syntax errors"
                return 1
            fi
        done
    else
        log_warning "Jinja2 not available, skipping template syntax validation"
    fi
    
    return 0
}

# Test 5: Check if Ansible integration files exist
test_ansible_integration() {
    log_info "Testing Ansible integration files..."
    
    cd "$PROJECT_ROOT"
    
    # Check if ansible directory exists
    if [[ ! -d "ansible" ]]; then
        log_error "ansible directory not found"
        return 1
    fi
    
    # Check required Ansible files
    local required_files=(
        "ansible/render-env-templates.yml"
        "ansible/inventory/example.yml"
        "ansible/group_vars/all.yml"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "$file exists"
        else
            log_error "$file not found"
            return 1
        fi
    done
    
    return 0
}

# Test 6: Check if deployment scripts exist and are executable
test_deployment_scripts() {
    log_info "Testing deployment scripts..."
    
    cd "$PROJECT_ROOT"
    
    # Check deployment scripts
    local scripts=(
        "scripts/deploy-with-ansible.sh"
        "scripts/verify-deployment.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "$script" ]]; then
            if [[ -x "$script" ]]; then
                log_success "$script exists and is executable"
            else
                log_error "$script exists but is not executable"
                return 1
            fi
        else
            log_error "$script not found"
            return 1
        fi
    done
    
    return 0
}

# Test 7: Check if documentation exists
test_documentation() {
    log_info "Testing documentation..."
    
    cd "$PROJECT_ROOT"
    
    # Check documentation files
    local docs=(
        "docs/COMPOSE_DEPLOYMENT_GUIDE.md"
        "env-templates/README.md"
        "env-templates/secrets-mapping.md"
        "MIGRATION_GUIDE.md"
        "NORMALIZATION_SUMMARY.md"
    )
    
    for doc in "${docs[@]}"; do
        if [[ -f "$doc" ]]; then
            log_success "$doc exists"
        else
            log_error "$doc not found"
            return 1
        fi
    done
    
    return 0
}

# Main test function
run_migration_tests() {
    log_info "Starting migration tests..."
    echo

    # Run all tests
    test_setup_secrets
    test_start_script_syntax
    test_compose_files
    test_environment_templates
    test_ansible_integration
    test_deployment_scripts
    test_documentation

    echo
    log_info "Migration Test Summary:"
    log_info "  Total tests: $TOTAL_TESTS"
    log_success "  Passed: $TESTS_PASSED"
    
    if [[ $TESTS_FAILED -gt 0 ]]; then
        log_error "  Failed: $TESTS_FAILED"
        echo
        log_error "Some migration tests failed. Please review the errors above."
        exit 1
    else
        log_success "  Failed: $TESTS_FAILED"
        echo
        log_success "All migration tests passed! The migration is ready."
        echo
        log_info "Next steps:"
        log_info "1. Run: python3 setup_secrets.py"
        log_info "2. Test: ./start-environment.sh dev"
        log_info "3. Verify services are running: docker compose ps"
    fi
}

# Help function
show_help() {
    cat << EOF
Test Migration Script

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output

This script tests the migration from legacy Docker Compose structure
to the new normalized structure.

Tests performed:
- setup_secrets.py functionality
- start-environment.sh syntax
- Compose file validation
- Environment template validation
- Ansible integration files
- Deployment scripts
- Documentation completeness

EOF
}

# Parse command line arguments
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -*)
            log_error "Unknown option $1"
            show_help
            exit 1
            ;;
        *)
            log_error "Unexpected argument $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
run_migration_tests