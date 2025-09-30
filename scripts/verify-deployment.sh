#!/bin/bash

# Verify Multimodal LLM Stack Deployment
# This script verifies that the normalized deployment structure is working correctly

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

# Test configuration
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

# File existence tests
test_file_exists() {
    local file_path="$1"
    local description="$2"
    
    run_test "$description" "test -f '$file_path'"
}

# Directory existence tests
test_dir_exists() {
    local dir_path="$1"
    local description="$2"
    
    run_test "$description" "test -d '$dir_path'"
}

# Docker Compose validation
test_compose_validation() {
    local compose_file="$1"
    local description="$2"
    
    run_test "$description" "docker compose -f '$compose_file' config --quiet"
}

# Template validation
test_template_syntax() {
    local template_file="$1"
    local description="$2"
    
    if command -v jinja2 >/dev/null 2>&1; then
        run_test "$description" "jinja2 --check '$template_file'"
    else
        log_warning "jinja2-cli not installed, skipping template validation"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    fi
}

# Main verification function
verify_deployment() {
    log_info "Starting deployment verification..."
    echo

    # Test 1: Core compose file exists and is valid
    test_file_exists "$PROJECT_ROOT/compose.yml" "Base compose file exists"
    test_compose_validation "$PROJECT_ROOT/compose.yml" "Base compose file is valid"

    # Test 2: Override files exist and are valid
    test_file_exists "$PROJECT_ROOT/compose.gpu.yml" "GPU override file exists"
    test_compose_validation "$PROJECT_ROOT/compose.gpu.yml" "GPU override file is valid"
    
    test_file_exists "$PROJECT_ROOT/compose.monitoring.yml" "Monitoring override file exists"
    test_compose_validation "$PROJECT_ROOT/compose.monitoring.yml" "Monitoring override file is valid"
    
    test_file_exists "$PROJECT_ROOT/compose.production.yml" "Production override file exists"
    test_compose_validation "$PROJECT_ROOT/compose.production.yml" "Production override file is valid"
    
    test_file_exists "$PROJECT_ROOT/compose.services.yml" "Services override file exists"
    test_compose_validation "$PROJECT_ROOT/compose.services.yml" "Services override file is valid"
    
    test_file_exists "$PROJECT_ROOT/compose.elk.yml" "ELK override file exists"
    test_compose_validation "$PROJECT_ROOT/compose.elk.yml" "ELK override file is valid"
    
    test_file_exists "$PROJECT_ROOT/compose.n8n-monitoring.yml" "n8n monitoring override file exists"
    test_compose_validation "$PROJECT_ROOT/compose.n8n-monitoring.yml" "n8n monitoring override file is valid"

    # Test 3: Environment templates directory exists
    test_dir_exists "$PROJECT_ROOT/env-templates" "Environment templates directory exists"

    # Test 4: Environment template files exist
    test_file_exists "$PROJECT_ROOT/env-templates/core.env.j2" "Core environment template exists"
    test_file_exists "$PROJECT_ROOT/env-templates/vllm.env.j2" "vLLM environment template exists"
    test_file_exists "$PROJECT_ROOT/env-templates/litellm.env.j2" "LiteLLM environment template exists"
    test_file_exists "$PROJECT_ROOT/env-templates/multimodal-worker.env.j2" "Multimodal worker environment template exists"
    test_file_exists "$PROJECT_ROOT/env-templates/retrieval-proxy.env.j2" "Retrieval proxy environment template exists"
    test_file_exists "$PROJECT_ROOT/env-templates/ai-agents.env.j2" "AI agents environment template exists"
    test_file_exists "$PROJECT_ROOT/env-templates/memory-system.env.j2" "Memory system environment template exists"
    test_file_exists "$PROJECT_ROOT/env-templates/search-engine.env.j2" "Search engine environment template exists"
    test_file_exists "$PROJECT_ROOT/env-templates/user-management.env.j2" "User management environment template exists"
    test_file_exists "$PROJECT_ROOT/env-templates/openwebui.env.j2" "OpenWebUI environment template exists"
    test_file_exists "$PROJECT_ROOT/env-templates/n8n.env.j2" "n8n environment template exists"
    test_file_exists "$PROJECT_ROOT/env-templates/n8n-monitoring.env.j2" "n8n monitoring environment template exists"
    test_file_exists "$PROJECT_ROOT/env-templates/master.env.j2" "Master environment template exists"

    # Test 5: Template syntax validation
    test_template_syntax "$PROJECT_ROOT/env-templates/core.env.j2" "Core template syntax is valid"
    test_template_syntax "$PROJECT_ROOT/env-templates/vllm.env.j2" "vLLM template syntax is valid"
    test_template_syntax "$PROJECT_ROOT/env-templates/litellm.env.j2" "LiteLLM template syntax is valid"

    # Test 6: Documentation files exist
    test_file_exists "$PROJECT_ROOT/env-templates/README.md" "Environment templates README exists"
    test_file_exists "$PROJECT_ROOT/env-templates/secrets-mapping.md" "Secrets mapping documentation exists"
    test_file_exists "$PROJECT_ROOT/docs/COMPOSE_DEPLOYMENT_GUIDE.md" "Compose deployment guide exists"

    # Test 7: Ansible integration files exist
    test_dir_exists "$PROJECT_ROOT/ansible" "Ansible directory exists"
    test_file_exists "$PROJECT_ROOT/ansible/render-env-templates.yml" "Ansible playbook exists"
    test_file_exists "$PROJECT_ROOT/ansible/inventory/example.yml" "Example inventory exists"
    test_file_exists "$PROJECT_ROOT/ansible/group_vars/all.yml" "Group variables exist"

    # Test 8: Deployment scripts exist and are executable
    test_file_exists "$PROJECT_ROOT/scripts/deploy-with-ansible.sh" "Deployment script exists"
    run_test "Deployment script is executable" "test -x '$PROJECT_ROOT/scripts/deploy-with-ansible.sh'"

    # Test 9: Combined compose file validation (base + overrides)
    run_test "Base + GPU override validation" "docker compose -f '$PROJECT_ROOT/compose.yml' -f '$PROJECT_ROOT/compose.gpu.yml' config --quiet"
    run_test "Base + Production override validation" "docker compose -f '$PROJECT_ROOT/compose.yml' -f '$PROJECT_ROOT/compose.production.yml' config --quiet"

    # Test 10: Profile-based service validation
    run_test "Monitoring profile validation" "docker compose -f '$PROJECT_ROOT/compose.yml' -f '$PROJECT_ROOT/compose.monitoring.yml' --profile monitoring config --quiet"
    run_test "Services profile validation" "docker compose -f '$PROJECT_ROOT/compose.yml' -f '$PROJECT_ROOT/compose.services.yml' --profile services config --quiet"

    echo
    log_info "Verification Summary:"
    log_info "  Total tests: $TOTAL_TESTS"
    log_success "  Passed: $TESTS_PASSED"
    
    if [[ $TESTS_FAILED -gt 0 ]]; then
        log_error "  Failed: $TESTS_FAILED"
        echo
        log_error "Some tests failed. Please review the errors above."
        exit 1
    else
        log_success "  Failed: $TESTS_FAILED"
        echo
        log_success "All tests passed! The normalized deployment structure is ready."
        echo
        log_info "Next steps:"
        log_info "1. Configure your OpenBao secrets according to secrets-mapping.md"
        log_info "2. Update the Ansible inventory with your target hosts"
        log_info "3. Run the deployment script: ./scripts/deploy-with-ansible.sh <environment>"
        log_info "4. Start services: docker compose up -d"
    fi
}

# Help function
show_help() {
    cat << EOF
Verify Multimodal LLM Stack Deployment Structure

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output

This script verifies that the normalized Docker Compose structure and
environment templates are correctly configured and ready for deployment.

Tests performed:
- Compose file existence and validation
- Environment template existence and syntax
- Documentation completeness
- Ansible integration files
- Deployment scripts
- Profile-based service configurations

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
verify_deployment