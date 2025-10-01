#!/bin/bash
# Cursor Environment Audit - Automated Restoration Script
# Restores functionality lost during migration from cursor-env-audit to phase-1-testing

set -e

echo "🔧 Starting Cursor Environment Audit Restoration"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_FILES=0
RESTORED_FILES=0
FAILED_FILES=0

# Function to restore file from cursor-env-audit branch
restore_file() {
    local file=$1
    local description=$2
    local criticality=$3
    
    TOTAL_FILES=$((TOTAL_FILES + 1))
    echo -e "${BLUE}📄 Restoring: $description${NC}"
    
    # Create directory if it doesn't exist
    local dir=$(dirname "$file")
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}✅ Created directory: $dir${NC}"
    fi
    
    # Backup existing file if it exists
    if [ -f "$file" ]; then
        cp "$file" "${file}.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${YELLOW}⚠️  Backed up existing file: $file${NC}"
    fi
    
    # Restore file from cursor-env-audit branch
    if git show cursor-env-audit:"$file" > "$file" 2>/dev/null; then
        echo -e "${GREEN}✅ Successfully restored: $file${NC}"
        RESTORED_FILES=$((RESTORED_FILES + 1))
        
        # Make scripts executable
        if [[ $file == scripts/*.sh ]]; then
            chmod +x "$file"
            echo -e "${GREEN}✅ Made executable: $file${NC}"
        fi
        
        # Validate critical files
        if [ "$criticality" = "CRITICAL" ]; then
            validate_critical_file "$file"
        fi
        
    else
        echo -e "${RED}❌ Failed to restore: $file${NC}"
        FAILED_FILES=$((FAILED_FILES + 1))
        return 1
    fi
}

# Function to validate critical files
validate_critical_file() {
    local file=$1
    
    case "$file" in
        "docker-compose.yml")
            echo -e "${BLUE}🔍 Validating Docker Compose syntax...${NC}"
            if docker-compose config > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Docker Compose syntax is valid${NC}"
            else
                echo -e "${RED}❌ Docker Compose syntax validation failed${NC}"
            fi
            ;;
        "scripts/validate-no-hardcoded-values.sh")
            echo -e "${BLUE}🔍 Validating hardcoded values script...${NC}"
            if bash -n "$file"; then
                echo -e "${GREEN}✅ Script syntax is valid${NC}"
            else
                echo -e "${RED}❌ Script syntax validation failed${NC}"
            fi
            ;;
        "configs/environment_schema.yaml")
            echo -e "${BLUE}🔍 Validating YAML syntax...${NC}"
            if python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
                echo -e "${GREEN}✅ YAML syntax is valid${NC}"
            else
                echo -e "${RED}❌ YAML syntax validation failed${NC}"
            fi
            ;;
    esac
}

# Function to test restored functionality
test_restored_functionality() {
    echo -e "${YELLOW}🧪 Testing Restored Functionality${NC}"
    echo "================================"
    
    # Test validation scripts
    if [ -f "scripts/validate-no-hardcoded-values.sh" ]; then
        echo -e "${BLUE}🔍 Testing hardcoded values validation...${NC}"
        if ./scripts/validate-no-hardcoded-values.sh --test 2>/dev/null; then
            echo -e "${GREEN}✅ Hardcoded values validation test passed${NC}"
        else
            echo -e "${YELLOW}⚠️  Hardcoded values validation test had warnings${NC}"
        fi
    fi
    
    # Test environment validation
    if [ -f "scripts/validate-environment.sh" ]; then
        echo -e "${BLUE}🔍 Testing environment validation...${NC}"
        if ./scripts/validate-environment.sh --test 2>/dev/null; then
            echo -e "${GREEN}✅ Environment validation test passed${NC}"
        else
            echo -e "${YELLOW}⚠️  Environment validation test had warnings${NC}"
        fi
    fi
    
    # Test compose generator
    if [ -f "scripts/compose-generator.py" ]; then
        echo -e "${BLUE}🔍 Testing compose generator...${NC}"
        if python3 scripts/compose-generator.py --validate 2>/dev/null; then
            echo -e "${GREEN}✅ Compose generator validation passed${NC}"
        else
            echo -e "${YELLOW}⚠️  Compose generator validation had warnings${NC}"
        fi
    fi
    
    # Test GPU configuration
    if [ -f "scripts/configure-gpu.sh" ]; then
        echo -e "${BLUE}🔍 Testing GPU configuration...${NC}"
        if ./scripts/configure-gpu.sh --detect 2>/dev/null; then
            echo -e "${GREEN}✅ GPU configuration test passed${NC}"
        else
            echo -e "${YELLOW}⚠️  GPU configuration test had warnings (may be expected on non-GPU systems)${NC}"
        fi
    fi
}

# Check prerequisites
echo -e "${BLUE}🔍 Checking Prerequisites${NC}"
echo "=========================="

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Check if cursor-env-audit branch exists
if ! git show-ref --verify --quiet refs/heads/cursor-env-audit && ! git show-ref --verify --quiet refs/remotes/origin/cursor-env-audit; then
    echo -e "${RED}❌ cursor-env-audit branch not found${NC}"
    echo -e "${YELLOW}💡 Available branches:${NC}"
    git branch -a | head -10
    exit 1
fi

echo -e "${GREEN}✅ Git repository and cursor-env-audit branch found${NC}"

# Phase 1: Critical Security Restoration
echo -e "${YELLOW}🔴 Phase 1: Critical Security Restoration${NC}"
echo "=============================================="

# Validation scripts
restore_file "scripts/validate-no-hardcoded-values.sh" "Hardcoded Values Validation Script" "CRITICAL"
restore_file "scripts/validate-environment.sh" "Environment Validation Script" "CRITICAL"
restore_file "scripts/fix-environment-discrepancies.sh" "Environment Discrepancy Fixes Script" "CRITICAL"

# Schema system
restore_file "configs/environment_schema.yaml" "Environment Schema Configuration" "CRITICAL"
restore_file "scripts/setup-environments.sh" "Environment Setup Script" "CRITICAL"
restore_file "scripts/compose-generator.py" "Docker Compose Generator Script" "CRITICAL"

# Base configuration
restore_file "docker-compose.yml" "Base Docker Compose Configuration" "CRITICAL"

# Phase 2: Documentation Restoration
echo -e "${YELLOW}🟡 Phase 2: Documentation Restoration${NC}"
echo "===================================="

# Security documentation
restore_file "COMPREHENSIVE_HARDCODED_VALUES_AUDIT.md" "Comprehensive Hardcoded Values Audit Report" "HIGH"
restore_file "HARDCODED_VALUES_AUDIT_REPORT.md" "Hardcoded Values Audit Report" "HIGH"
restore_file "CONFIGURATION_SYSTEM_OVERVIEW.md" "Configuration System Overview" "HIGH"

# Operational documentation
restore_file "DEPLOYMENT_TESTING_STRATEGY.md" "Deployment Testing Strategy Guide" "MEDIUM"
restore_file "ENVIRONMENT_CONFIGURATION_GUIDE.md" "Environment Configuration Guide" "MEDIUM"
restore_file "SCHEMA_DRIVEN_ENVIRONMENT_GUIDE.md" "Schema-Driven Environment Configuration Guide" "MEDIUM"

# Analysis documentation
restore_file "PHASE_1_TESTING_ANALYSIS.md" "Phase 1 Testing Analysis Report" "MEDIUM"
restore_file "PHASE_1_TESTING_FINAL_SUMMARY.md" "Phase 1 Testing Final Summary" "MEDIUM"

# Phase 3: Advanced Features
echo -e "${YELLOW}🟢 Phase 3: Advanced Features${NC}"
echo "=============================="

# GPU configuration
restore_file "scripts/configure-gpu.sh" "GPU Configuration Script" "MEDIUM"
restore_file "MULTI_GPU_CONFIGURATION_GUIDE.md" "Multi-GPU Configuration Guide" "LOW"

# Test restored functionality
test_restored_functionality

# Summary
echo -e "${GREEN}🎉 Restoration Summary${NC}"
echo "===================="
echo -e "Total files processed: ${BLUE}$TOTAL_FILES${NC}"
echo -e "Successfully restored: ${GREEN}$RESTORED_FILES${NC}"
echo -e "Failed to restore: ${RED}$FAILED_FILES${NC}"

if [ $FAILED_FILES -eq 0 ]; then
    echo -e "${GREEN}✅ All files restored successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Some files failed to restore. Check the output above for details.${NC}"
fi

echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Review restored files for any conflicts with current configuration"
echo "2. Run validation scripts to ensure system integrity"
echo "3. Test environment setup with restored schema system"
echo "4. Update documentation if needed"
echo "5. Commit changes to preserve restoration"

echo -e "${BLUE}🔧 Available Commands:${NC}"
echo "- Validate hardcoded values: ./scripts/validate-no-hardcoded-values.sh"
echo "- Validate environment: ./scripts/validate-environment.sh"
echo "- Fix discrepancies: ./scripts/fix-environment-discrepancies.sh"
echo "- Setup environments: ./scripts/setup-environments.sh"
echo "- Configure GPU: ./scripts/configure-gpu.sh"
echo "- Generate compose: python3 scripts/compose-generator.py"

echo -e "${GREEN}🎯 Restoration completed!${NC}"
