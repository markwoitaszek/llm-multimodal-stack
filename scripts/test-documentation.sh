#!/bin/bash

# Documentation testing framework
# Tests documentation completeness, accuracy, and consistency

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Documentation files to test
DOCUMENTATION_FILES=(
    "README.md"
    "ENHANCED_WORKFLOW_DIAGRAM.md"
    "docs/ARCHITECTURE.md"
    "docs/OPERATIONS.md"
    "docs/TROUBLESHOOTING.md"
    "PR_NOTES.md"
    "TESTING_STRATEGY.md"
)

# Configuration files to test
CONFIG_FILES=(
    "schemas/compose-schema.yaml"
    "configs/retention-policies.yaml"
    "configs/backup-strategies.yaml"
)

# Script files to test
SCRIPT_FILES=(
    "scripts/validate-credentials.sh"
    "scripts/configure-gpu.sh"
    "scripts/check-network-conflicts.sh"
    "scripts/validate-networks.sh"
    "scripts/wipe-environment.sh"
    "scripts/manage-retention.sh"
    "scripts/setup-retention-cron.sh"
    "scripts/manage-backups.sh"
    "scripts/setup-backup-cron.sh"
    "scripts/test-stack-operations.sh"
    "scripts/test-network-operations.sh"
    "scripts/test-data-operations.sh"
    "scripts/test-granular-operations.sh"
    "scripts/test-comprehensive.sh"
    "scripts/test-monitoring.sh"
)

# Test result tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

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

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_exit_code="${3:-0}"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    log_info "Running test: $test_name"
    
    if eval "$test_command"; then
        if [ $? -eq $expected_exit_code ]; then
            log_success "✅ $test_name: PASSED"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            log_error "❌ $test_name: FAILED (unexpected exit code)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        log_error "❌ $test_name: FAILED"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Test file existence
test_file_existence() {
    log_info "Testing file existence..."
    
    local files_found=0
    local total_files=0
    
    # Test documentation files
    for file in "${DOCUMENTATION_FILES[@]}"; do
        total_files=$((total_files + 1))
        if [ -f "$PROJECT_ROOT/$file" ]; then
            log_success "✅ Documentation file exists: $file"
            files_found=$((files_found + 1))
        else
            log_error "❌ Documentation file missing: $file"
        fi
    done
    
    # Test configuration files
    for file in "${CONFIG_FILES[@]}"; do
        total_files=$((total_files + 1))
        if [ -f "$PROJECT_ROOT/$file" ]; then
            log_success "✅ Configuration file exists: $file"
            files_found=$((files_found + 1))
        else
            log_error "❌ Configuration file missing: $file"
        fi
    done
    
    # Test script files
    for file in "${SCRIPT_FILES[@]}"; do
        total_files=$((total_files + 1))
        if [ -f "$PROJECT_ROOT/$file" ]; then
            log_success "✅ Script file exists: $file"
            files_found=$((files_found + 1))
        else
            log_error "❌ Script file missing: $file"
        fi
    done
    
    if [ $files_found -eq $total_files ]; then
        log_success "✅ File existence: PASSED ($files_found/$total_files)"
        return 0
    else
        log_error "❌ File existence: FAILED ($files_found/$total_files)"
        return 1
    fi
}

# Test file permissions
test_file_permissions() {
    log_info "Testing file permissions..."
    
    local permissions_ok=0
    local total_scripts=${#SCRIPT_FILES[@]}
    
    for file in "${SCRIPT_FILES[@]}"; do
        if [ -x "$PROJECT_ROOT/$file" ]; then
            log_success "✅ Script is executable: $file"
            permissions_ok=$((permissions_ok + 1))
        else
            log_error "❌ Script is not executable: $file"
        fi
    done
    
    if [ $permissions_ok -eq $total_scripts ]; then
        log_success "✅ File permissions: PASSED ($permissions_ok/$total_scripts)"
        return 0
    else
        log_error "❌ File permissions: FAILED ($permissions_ok/$total_scripts)"
        return 1
    fi
}

# Test YAML syntax
test_yaml_syntax() {
    log_info "Testing YAML syntax..."
    
    local yaml_ok=0
    local total_yaml=${#CONFIG_FILES[@]}
    
    for file in "${CONFIG_FILES[@]}"; do
        if python3 -c "import yaml; yaml.safe_load(open('$PROJECT_ROOT/$file'))" >/dev/null 2>&1; then
            log_success "✅ YAML syntax valid: $file"
            yaml_ok=$((yaml_ok + 1))
        else
            log_error "❌ YAML syntax invalid: $file"
        fi
    done
    
    if [ $yaml_ok -eq $total_yaml ]; then
        log_success "✅ YAML syntax: PASSED ($yaml_ok/$total_yaml)"
        return 0
    else
        log_error "❌ YAML syntax: FAILED ($yaml_ok/$total_yaml)"
        return 1
    fi
}

# Test shell script syntax
test_shell_syntax() {
    log_info "Testing shell script syntax..."
    
    local shell_ok=0
    local total_shell=${#SCRIPT_FILES[@]}
    
    for file in "${SCRIPT_FILES[@]}"; do
        if bash -n "$PROJECT_ROOT/$file" >/dev/null 2>&1; then
            log_success "✅ Shell syntax valid: $file"
            shell_ok=$((shell_ok + 1))
        else
            log_error "❌ Shell syntax invalid: $file"
        fi
    done
    
    if [ $shell_ok -eq $total_shell ]; then
        log_success "✅ Shell syntax: PASSED ($shell_ok/$total_shell)"
        return 0
    else
        log_error "❌ Shell syntax: FAILED ($shell_ok/$total_shell)"
        return 1
    fi
}

# Test documentation completeness
test_documentation_completeness() {
    log_info "Testing documentation completeness..."
    
    local completeness_ok=0
    local total_docs=${#DOCUMENTATION_FILES[@]}
    
    for file in "${DOCUMENTATION_FILES[@]}"; do
        local file_path="$PROJECT_ROOT/$file"
        
        if [ -f "$file_path" ]; then
            local file_size=$(wc -c < "$file_path")
            
            if [ $file_size -gt 1000 ]; then
                log_success "✅ Documentation complete: $file (${file_size} bytes)"
                completeness_ok=$((completeness_ok + 1))
            else
                log_warning "⚠️  Documentation incomplete: $file (${file_size} bytes)"
            fi
        fi
    done
    
    if [ $completeness_ok -eq $total_docs ]; then
        log_success "✅ Documentation completeness: PASSED ($completeness_ok/$total_docs)"
        return 0
    else
        log_warning "⚠️  Documentation completeness: PARTIAL ($completeness_ok/$total_docs)"
        return 1
    fi
}

# Test documentation consistency
test_documentation_consistency() {
    log_info "Testing documentation consistency..."
    
    local consistency_ok=0
    local total_checks=0
    
    # Check for consistent project name
    local project_name_mentions=0
    for file in "${DOCUMENTATION_FILES[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            if grep -q "LLM Multimodal Stack\|llm-multimodal-stack" "$PROJECT_ROOT/$file"; then
                project_name_mentions=$((project_name_mentions + 1))
            fi
        fi
    done
    
    total_checks=$((total_checks + 1))
    if [ $project_name_mentions -gt 0 ]; then
        log_success "✅ Project name consistency: PASSED ($project_name_mentions files)"
        consistency_ok=$((consistency_ok + 1))
    else
        log_error "❌ Project name consistency: FAILED"
    fi
    
    # Check for consistent version references
    local version_mentions=0
    for file in "${DOCUMENTATION_FILES[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            if grep -q "v3\.0\|version 3\.0\|Version 3\.0" "$PROJECT_ROOT/$file"; then
                version_mentions=$((version_mentions + 1))
            fi
        fi
    done
    
    total_checks=$((total_checks + 1))
    if [ $version_mentions -gt 0 ]; then
        log_success "✅ Version consistency: PASSED ($version_mentions files)"
        consistency_ok=$((consistency_ok + 1))
    else
        log_warning "⚠️  Version consistency: NOT DETECTED"
    fi
    
    # Check for consistent command references
    local command_mentions=0
    for file in "${DOCUMENTATION_FILES[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            if grep -q "make \|makefile\|Makefile" "$PROJECT_ROOT/$file"; then
                command_mentions=$((command_mentions + 1))
            fi
        fi
    done
    
    total_checks=$((total_checks + 1))
    if [ $command_mentions -gt 0 ]; then
        log_success "✅ Command reference consistency: PASSED ($command_mentions files)"
        consistency_ok=$((consistency_ok + 1))
    else
        log_warning "⚠️  Command reference consistency: NOT DETECTED"
    fi
    
    if [ $consistency_ok -eq $total_checks ]; then
        log_success "✅ Documentation consistency: PASSED ($consistency_ok/$total_checks)"
        return 0
    else
        log_warning "⚠️  Documentation consistency: PARTIAL ($consistency_ok/$total_checks)"
        return 1
    fi
}

# Test documentation accuracy
test_documentation_accuracy() {
    log_info "Testing documentation accuracy..."
    
    local accuracy_ok=0
    local total_checks=0
    
    # Check README.md for accurate command references
    if [ -f "$PROJECT_ROOT/README.md" ]; then
        local readme_commands=$(grep -o "make [a-zA-Z0-9_-]*" "$PROJECT_ROOT/README.md" | sort -u | wc -l)
        total_checks=$((total_checks + 1))
        
        if [ $readme_commands -gt 10 ]; then
            log_success "✅ README command accuracy: PASSED ($readme_commands commands)"
            accuracy_ok=$((accuracy_ok + 1))
        else
            log_warning "⚠️  README command accuracy: LOW ($readme_commands commands)"
        fi
    fi
    
    # Check ENHANCED_WORKFLOW_DIAGRAM.md for accurate version
    if [ -f "$PROJECT_ROOT/ENHANCED_WORKFLOW_DIAGRAM.md" ]; then
        total_checks=$((total_checks + 1))
        
        if grep -q "Diagram Version.*3\.0" "$PROJECT_ROOT/ENHANCED_WORKFLOW_DIAGRAM.md"; then
            log_success "✅ Workflow diagram version accuracy: PASSED"
            accuracy_ok=$((accuracy_ok + 1))
        else
            log_warning "⚠️  Workflow diagram version accuracy: NOT DETECTED"
        fi
    fi
    
    # Check docs/ARCHITECTURE.md for accurate stack references
    if [ -f "$PROJECT_ROOT/docs/ARCHITECTURE.md" ]; then
        local stack_mentions=$(grep -o "core\|inference\|ai\|ui\|testing\|monitoring" "$PROJECT_ROOT/docs/ARCHITECTURE.md" | wc -l)
        total_checks=$((total_checks + 1))
        
        if [ $stack_mentions -gt 10 ]; then
            log_success "✅ Architecture stack accuracy: PASSED ($stack_mentions mentions)"
            accuracy_ok=$((accuracy_ok + 1))
        else
            log_warning "⚠️  Architecture stack accuracy: LOW ($stack_mentions mentions)"
        fi
    fi
    
    if [ $accuracy_ok -eq $total_checks ]; then
        log_success "✅ Documentation accuracy: PASSED ($accuracy_ok/$total_checks)"
        return 0
    else
        log_warning "⚠️  Documentation accuracy: PARTIAL ($accuracy_ok/$total_checks)"
        return 1
    fi
}

# Test documentation links
test_documentation_links() {
    log_info "Testing documentation links..."
    
    local links_ok=0
    local total_links=0
    
    for file in "${DOCUMENTATION_FILES[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            # Find markdown links
            local markdown_links=$(grep -o '\[.*\](.*)' "$PROJECT_ROOT/$file" | wc -l)
            total_links=$((total_links + markdown_links))
            
            if [ $markdown_links -gt 0 ]; then
                log_success "✅ Links found in $file: $markdown_links"
                links_ok=$((links_ok + 1))
            fi
        fi
    done
    
    if [ $total_links -gt 0 ]; then
        log_success "✅ Documentation links: PASSED ($total_links total links)"
        return 0
    else
        log_warning "⚠️  Documentation links: NOT DETECTED"
        return 1
    fi
}

# Test configuration completeness
test_configuration_completeness() {
    log_info "Testing configuration completeness..."
    
    local config_ok=0
    local total_configs=${#CONFIG_FILES[@]}
    
    for file in "${CONFIG_FILES[@]}"; do
        local file_path="$PROJECT_ROOT/$file"
        
        if [ -f "$file_path" ]; then
            local file_size=$(wc -c < "$file_path")
            
            if [ $file_size -gt 500 ]; then
                log_success "✅ Configuration complete: $file (${file_size} bytes)"
                config_ok=$((config_ok + 1))
            else
                log_warning "⚠️  Configuration incomplete: $file (${file_size} bytes)"
            fi
        fi
    done
    
    if [ $config_ok -eq $total_configs ]; then
        log_success "✅ Configuration completeness: PASSED ($config_ok/$total_configs)"
        return 0
    else
        log_warning "⚠️  Configuration completeness: PARTIAL ($config_ok/$total_configs)"
        return 1
    fi
}

# Test script help functionality
test_script_help() {
    log_info "Testing script help functionality..."
    
    local help_ok=0
    local total_scripts=${#SCRIPT_FILES[@]}
    
    for file in "${SCRIPT_FILES[@]}"; do
        local file_path="$PROJECT_ROOT/$file"
        
        if [ -f "$file_path" ] && [ -x "$file_path" ]; then
            # Test help command
            if "$file_path" --help >/dev/null 2>&1 || "$file_path" -h >/dev/null 2>&1; then
                log_success "✅ Script help available: $file"
                help_ok=$((help_ok + 1))
            else
                log_warning "⚠️  Script help not available: $file"
            fi
        fi
    done
    
    if [ $help_ok -eq $total_scripts ]; then
        log_success "✅ Script help: PASSED ($help_ok/$total_scripts)"
        return 0
    else
        log_warning "⚠️  Script help: PARTIAL ($help_ok/$total_scripts)"
        return 1
    fi
}

# Test documentation formatting
test_documentation_formatting() {
    log_info "Testing documentation formatting..."
    
    local formatting_ok=0
    local total_checks=0
    
    for file in "${DOCUMENTATION_FILES[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            total_checks=$((total_checks + 1))
            
            # Check for proper markdown headers
            if grep -q "^#" "$PROJECT_ROOT/$file"; then
                log_success "✅ Markdown headers found: $file"
                formatting_ok=$((formatting_ok + 1))
            else
                log_warning "⚠️  No markdown headers found: $file"
            fi
        fi
    done
    
    if [ $formatting_ok -eq $total_checks ]; then
        log_success "✅ Documentation formatting: PASSED ($formatting_ok/$total_checks)"
        return 0
    else
        log_warning "⚠️  Documentation formatting: PARTIAL ($formatting_ok/$total_checks)"
        return 1
    fi
}

# Main test execution
main() {
    log_info "📚 Starting Documentation Testing Suite"
    log_info "======================================="
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Test file existence
    run_test "File Existence" "test_file_existence"
    
    # Test file permissions
    run_test "File Permissions" "test_file_permissions"
    
    # Test syntax
    run_test "YAML Syntax" "test_yaml_syntax"
    run_test "Shell Syntax" "test_shell_syntax"
    
    # Test documentation
    run_test "Documentation Completeness" "test_documentation_completeness"
    run_test "Documentation Consistency" "test_documentation_consistency"
    run_test "Documentation Accuracy" "test_documentation_accuracy"
    run_test "Documentation Links" "test_documentation_links"
    run_test "Documentation Formatting" "test_documentation_formatting"
    
    # Test configuration
    run_test "Configuration Completeness" "test_configuration_completeness"
    
    # Test scripts
    run_test "Script Help" "test_script_help"
    
    # Print test summary
    log_info "======================================="
    log_info "📚 Documentation Testing Suite Complete"
    log_info "======================================="
    log_info "Total Tests: $TESTS_TOTAL"
    log_success "Passed: $TESTS_PASSED"
    if [ $TESTS_FAILED -gt 0 ]; then
        log_error "Failed: $TESTS_FAILED"
    else
        log_info "Failed: $TESTS_FAILED"
    fi
    
    # Calculate success rate
    local success_rate=0
    if [ $TESTS_TOTAL -gt 0 ]; then
        success_rate=$((TESTS_PASSED * 100 / TESTS_TOTAL))
    fi
    
    log_info "Success Rate: $success_rate%"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log_success "🎉 All tests passed!"
        exit 0
    else
        log_error "❌ Some tests failed!"
        exit 1
    fi
}

# Help function
show_help() {
    cat << EOF
Documentation Testing Framework

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    --skip-syntax           Skip syntax tests
    --skip-formatting       Skip formatting tests
    --skip-accuracy         Skip accuracy tests

Examples:
    $0                      # Run all tests
    $0 --skip-syntax        # Skip syntax tests
    $0 --verbose            # Enable verbose output

EOF
}

# Parse command line arguments
VERBOSE=false
SKIP_SYNTAX=false
SKIP_FORMATTING=false
SKIP_ACCURACY=false

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
        --skip-syntax)
            SKIP_SYNTAX=true
            shift
            ;;
        --skip-formatting)
            SKIP_FORMATTING=true
            shift
            ;;
        --skip-accuracy)
            SKIP_ACCURACY=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main function
main
