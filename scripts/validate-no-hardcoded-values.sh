#!/bin/bash
# Validation Script for Hardcoded Values
# Ensures all containers, services, configurations, and scripts use environment variables

set -e

echo "🔍 Validating No Hardcoded Values"
echo "================================="

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

# Function to check for hardcoded passwords
check_hardcoded_passwords() {
    echo ""
    print_status "INFO" "Checking for hardcoded passwords..."
    
    local files_with_hardcoded_passwords=()
    
    # Check Docker Compose files
    for file in docker-compose*.yml; do
        if [ -f "$file" ]; then
            # Check for hardcoded passwords (not environment variables)
            if grep -q "PASSWORD=[^$]" "$file" 2>/dev/null; then
                files_with_hardcoded_passwords+=("$file")
            fi
        fi
    done
    
    # Check service config files
    for file in services/*/app/config.py; do
        if [ -f "$file" ]; then
            if grep -q 'getenv.*".*password.*".*"[^"]*"' "$file" 2>/dev/null; then
                files_with_hardcoded_passwords+=("$file")
            fi
        fi
    done
    
    if [ ${#files_with_hardcoded_passwords[@]} -eq 0 ]; then
        print_status "PASS" "No hardcoded passwords found"
    else
        print_status "FAIL" "Hardcoded passwords found in: ${files_with_hardcoded_passwords[*]}"
    fi
}

# Function to check for hardcoded API keys
check_hardcoded_api_keys() {
    echo ""
    print_status "INFO" "Checking for hardcoded API keys..."
    
    local files_with_hardcoded_keys=()
    
    # Check configuration files
    for file in configs/*.yaml configs/*.yml; do
        if [ -f "$file" ]; then
            # Check for hardcoded API keys (not environment variables)
            if grep -q "api_key: [^$]" "$file" 2>/dev/null; then
                files_with_hardcoded_keys+=("$file")
            fi
        fi
    done
    
    if [ ${#files_with_hardcoded_keys[@]} -eq 0 ]; then
        print_status "PASS" "No hardcoded API keys found"
    else
        print_status "FAIL" "Hardcoded API keys found in: ${files_with_hardcoded_keys[*]}"
    fi
}

# Function to check for hardcoded secrets
check_hardcoded_secrets() {
    echo ""
    print_status "INFO" "Checking for hardcoded secrets..."
    
    local files_with_hardcoded_secrets=()
    
    # Check for common hardcoded secret patterns (not environment variables)
    local secret_patterns=(
        "SECRET=[^$]"
        "KEY=[^$]"
        "TOKEN=[^$]"
        "JWT=[^$]"
    )
    
    for pattern in "${secret_patterns[@]}"; do
        for file in docker-compose*.yml configs/*.yaml configs/*.yml; do
            if [ -f "$file" ]; then
                if grep -qi "$pattern" "$file" 2>/dev/null; then
                    files_with_hardcoded_secrets+=("$file")
                fi
            fi
        done
    done
    
    if [ ${#files_with_hardcoded_secrets[@]} -eq 0 ]; then
        print_status "PASS" "No hardcoded secrets found"
    else
        print_status "FAIL" "Hardcoded secrets found in: ${files_with_hardcoded_secrets[*]}"
    fi
}

# Function to check for hardcoded usernames
check_hardcoded_usernames() {
    echo ""
    print_status "INFO" "Checking for hardcoded usernames..."
    
    local files_with_hardcoded_usernames=()
    
    # Check for hardcoded admin usernames
    for file in docker-compose*.yml; do
        if [ -f "$file" ]; then
            if grep -q "USER=admin" "$file" 2>/dev/null; then
                files_with_hardcoded_usernames+=("$file")
            fi
        fi
    done
    
    if [ ${#files_with_hardcoded_usernames[@]} -eq 0 ]; then
        print_status "PASS" "No hardcoded usernames found"
    else
        print_status "WARN" "Hardcoded usernames found in: ${files_with_hardcoded_usernames[*]}"
    fi
}

# Function to check for hardcoded database credentials
check_hardcoded_db_credentials() {
    echo ""
    print_status "INFO" "Checking for hardcoded database credentials..."
    
    local files_with_hardcoded_db=()
    
    # Check for hardcoded database URLs (not environment variables)
    for file in configs/*.yaml configs/*.yml; do
        if [ -f "$file" ]; then
            # Look for hardcoded credentials (not environment variables)
            if grep -q "postgresql://[^$]*:[^$]*@" "$file" 2>/dev/null; then
                files_with_hardcoded_db+=("$file")
            fi
        fi
    done
    
    if [ ${#files_with_hardcoded_db[@]} -eq 0 ]; then
        print_status "PASS" "No hardcoded database credentials found"
    else
        print_status "FAIL" "Hardcoded database credentials found in: ${files_with_hardcoded_db[*]}"
    fi
}

# Function to check for hardcoded encryption keys
check_hardcoded_encryption_keys() {
    echo ""
    print_status "INFO" "Checking for hardcoded encryption keys..."
    
    local files_with_hardcoded_keys=()
    
    # Check for hardcoded encryption keys
    for file in configs/*.yaml configs/*.yml configs/*.ini; do
        if [ -f "$file" ]; then
            if grep -q "encryption.*key.*=.*[^$]" "$file" 2>/dev/null; then
                files_with_hardcoded_keys+=("$file")
            fi
        fi
    done
    
    if [ ${#files_with_hardcoded_keys[@]} -eq 0 ]; then
        print_status "PASS" "No hardcoded encryption keys found"
    else
        print_status "WARN" "Hardcoded encryption keys found in: ${files_with_hardcoded_keys[*]}"
    fi
}

# Function to check environment variable usage
check_environment_variable_usage() {
    echo ""
    print_status "INFO" "Checking environment variable usage..."
    
    local files_without_env_vars=()
    
    # Check Docker Compose files for proper environment variable usage
    for file in docker-compose*.yml; do
        if [ -f "$file" ]; then
            # Check if file uses environment variables for sensitive data
            if ! grep -q "\${.*}" "$file" 2>/dev/null; then
                files_without_env_vars+=("$file")
            fi
        fi
    done
    
    if [ ${#files_without_env_vars[@]} -eq 0 ]; then
        print_status "PASS" "All Docker Compose files use environment variables"
    else
        print_status "WARN" "Files without environment variables: ${files_without_env_vars[*]}"
    fi
}

# Function to check schema compliance
check_schema_compliance() {
    echo ""
    print_status "INFO" "Checking schema compliance..."
    
    # Check if schema file exists
    if [ ! -f "configs/environment_schema.yaml" ]; then
        print_status "FAIL" "Environment schema file not found"
        return
    fi
    
    # Check if schema has all required sections
    local required_sections=("environments" "secret_types" "inheritance")
    local missing_sections=()
    
    for section in "${required_sections[@]}"; do
        if ! grep -q "^$section:" "configs/environment_schema.yaml" 2>/dev/null; then
            missing_sections+=("$section")
        fi
    done
    
    if [ ${#missing_sections[@]} -eq 0 ]; then
        print_status "PASS" "Schema file has all required sections"
    else
        print_status "FAIL" "Schema file missing sections: ${missing_sections[*]}"
    fi
}

# Main validation function
main() {
    echo ""
    print_status "INFO" "Starting hardcoded values validation..."
    echo ""
    
    check_hardcoded_passwords
    check_hardcoded_api_keys
    check_hardcoded_secrets
    check_hardcoded_usernames
    check_hardcoded_db_credentials
    check_hardcoded_encryption_keys
    check_environment_variable_usage
    check_schema_compliance
    
    # Summary
    echo ""
    echo "📊 Validation Summary"
    echo "==================="
    echo "Total checks: $TOTAL_CHECKS"
    echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
    echo -e "${YELLOW}Warnings: $WARNING_CHECKS${NC}"
    echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
    echo ""
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        if [ $WARNING_CHECKS -eq 0 ]; then
            echo -e "${GREEN}🎉 All checks passed! No hardcoded values found.${NC}"
            exit 0
        else
            echo -e "${YELLOW}⚠️  Validation passed with warnings. Review warnings before deployment.${NC}"
            exit 0
        fi
    else
        echo -e "${RED}❌ Validation failed. Fix hardcoded values before deployment.${NC}"
        exit 1
    fi
}

# Run main function
main "$@"

