#!/bin/bash
# Focused Restoration - Critical Operational Features Only
# Restores GPU/NVLink optimization, Docker environment wipe, and fixes hardcoded security issues

set -e

echo "🎯 Focused Restoration - Critical Operational Features"
echo "====================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
RESTORED_FEATURES=0
FIXED_ISSUES=0

# Function to check if cursor-env-audit branch exists
check_branch() {
    if ! git show-ref --verify --quiet refs/heads/cursor-env-audit && ! git show-ref --verify --quiet refs/remotes/origin/cursor-env-audit; then
        echo -e "${RED}❌ cursor-env-audit branch not found${NC}"
        echo -e "${YELLOW}💡 Available branches:${NC}"
        git branch -a | head -10
        exit 1
    fi
    echo -e "${GREEN}✅ cursor-env-audit branch found${NC}"
}

# Function to restore file with validation
restore_file() {
    local file=$1
    local description=$2
    
    echo -e "${BLUE}📄 Restoring: $description${NC}"
    
    # Create directory if needed
    local dir=$(dirname "$file")
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
    fi
    
    # Backup existing file
    if [ -f "$file" ]; then
        cp "$file" "${file}.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${YELLOW}⚠️  Backed up existing file${NC}"
    fi
    
    # Restore file
    if git show cursor-env-audit:"$file" > "$file" 2>/dev/null; then
        echo -e "${GREEN}✅ Successfully restored: $file${NC}"
        RESTORED_FEATURES=$((RESTORED_FEATURES + 1))
        
        # Make scripts executable
        if [[ $file == scripts/*.sh ]]; then
            chmod +x "$file"
            echo -e "${GREEN}✅ Made executable: $file${NC}"
        fi
    else
        echo -e "${RED}❌ Failed to restore: $file${NC}"
        return 1
    fi
}

# Function to fix hardcoded security issues
fix_hardcoded_issues() {
    echo -e "${BLUE}🔒 Fixing Hardcoded Security Issues...${NC}"
    
    local files_fixed=0
    
    # Fix schema defaults
    if [ -f "schemas/compose-schema.yaml" ]; then
        echo -e "${YELLOW}🔧 Fixing schema hardcoded defaults...${NC}"
        
        # Remove hardcoded defaults
        sed -i.bak 's/POSTGRES_USER=${POSTGRES_USER:-postgres}/POSTGRES_USER=${POSTGRES_USER}/g' schemas/compose-schema.yaml
        sed -i.bak 's/MINIO_ROOT_USER=${MINIO_ROOT_USER:-minioadmin}/MINIO_ROOT_USER=${MINIO_ROOT_USER}/g' schemas/compose-schema.yaml
        
        # Check if changes were made
        if ! grep -q ":-postgres\|:-minioadmin" schemas/compose-schema.yaml; then
            echo -e "${GREEN}✅ Schema hardcoded defaults removed${NC}"
            files_fixed=$((files_fixed + 1))
        else
            echo -e "${RED}❌ Some schema defaults still present${NC}"
        fi
    fi
    
    # Fix service config defaults
    echo -e "${YELLOW}🔧 Fixing service config hardcoded defaults...${NC}"
    
    for config_file in services/*/app/config.py; do
        if [ -f "$config_file" ]; then
            echo -e "${BLUE}  Processing: $config_file${NC}"
            
            # Backup original
            cp "$config_file" "${config_file}.backup.$(date +%Y%m%d_%H%M%S)"
            
            # Remove hardcoded defaults
            sed -i.bak 's/os.getenv("POSTGRES_PASSWORD", "postgres")/os.getenv("POSTGRES_PASSWORD")/g' "$config_file"
            sed -i.bak 's/os.getenv("MINIO_ACCESS_KEY", "minioadmin")/os.getenv("MINIO_ACCESS_KEY")/g' "$config_file"
            sed -i.bak 's/os.getenv("MINIO_SECRET_KEY", "minioadmin")/os.getenv("MINIO_SECRET_KEY")/g' "$config_file"
            
            # Check if changes were made
            if ! grep -q ', "postgres")\|, "minioadmin")' "$config_file"; then
                echo -e "${GREEN}  ✅ Hardcoded defaults removed from $config_file${NC}"
                files_fixed=$((files_fixed + 1))
            else
                echo -e "${RED}  ❌ Some defaults still present in $config_file${NC}"
            fi
        fi
    done
    
    FIXED_ISSUES=$files_fixed
    echo -e "${GREEN}✅ Fixed hardcoded issues in $files_fixed files${NC}"
}

# Function to test GPU functionality
test_gpu_functionality() {
    echo -e "${BLUE}🧪 Testing GPU Functionality...${NC}"
    
    if [ -f "scripts/configure-gpu.sh" ]; then
        echo -e "${YELLOW}🔍 Testing GPU detection...${NC}"
        
        # Test GPU detection (may fail on non-GPU systems, which is expected)
        if ./scripts/configure-gpu.sh --detect 2>/dev/null; then
            echo -e "${GREEN}✅ GPU detection working${NC}"
        else
            echo -e "${YELLOW}⚠️  GPU detection test inconclusive (expected on non-GPU systems)${NC}"
        fi
        
        # Check if script is executable and has expected functions
        if grep -q "configure_multi_gpu\|configure_single_gpu" scripts/configure-gpu.sh; then
            echo -e "${GREEN}✅ GPU configuration functions present${NC}"
        else
            echo -e "${RED}❌ GPU configuration functions missing${NC}"
        fi
    else
        echo -e "${RED}❌ GPU configuration script not found${NC}"
    fi
}

# Function to test docker wipe functionality
test_docker_wipe() {
    echo -e "${BLUE}🧪 Testing Docker Wipe Functionality...${NC}"
    
    if [ -f "start-environment.sh" ]; then
        # Check if first_run_setup function exists
        if grep -q "first_run_setup" start-environment.sh; then
            echo -e "${GREEN}✅ Docker wipe functionality (first_run_setup) exists${NC}"
            
            # Check for key components
            if grep -q "docker volume.*rm.*llm-multimodal-stack" start-environment.sh; then
                echo -e "${GREEN}✅ Volume cleanup functionality present${NC}"
            else
                echo -e "${YELLOW}⚠️  Volume cleanup functionality may be incomplete${NC}"
            fi
            
            if grep -q "docker network.*rm.*llm-multimodal-stack" start-environment.sh; then
                echo -e "${GREEN}✅ Network cleanup functionality present${NC}"
            else
                echo -e "${YELLOW}⚠️  Network cleanup functionality may be incomplete${NC}"
            fi
            
            echo -e "${BLUE}💡 Usage: ./start-environment.sh first-run (DESTRUCTIVE!)${NC}"
        else
            echo -e "${RED}❌ Docker wipe functionality (first_run_setup) missing${NC}"
            echo -e "${YELLOW}🔧 This needs manual restoration${NC}"
        fi
    else
        echo -e "${RED}❌ start-environment.sh not found${NC}"
    fi
}

# Function to validate security fixes
validate_security_fixes() {
    echo -e "${BLUE}🔍 Validating Security Fixes...${NC}"
    
    local issues_found=0
    
    # Check for remaining hardcoded defaults
    if grep -q ":-postgres\|:-minioadmin" schemas/compose-schema.yaml 2>/dev/null; then
        echo -e "${RED}❌ Schema still contains hardcoded defaults${NC}"
        issues_found=$((issues_found + 1))
    else
        echo -e "${GREEN}✅ Schema hardcoded defaults removed${NC}"
    fi
    
    # Check service configs
    for config_file in services/*/app/config.py; do
        if [ -f "$config_file" ]; then
            if grep -q ', "postgres")\|, "minioadmin")' "$config_file"; then
                echo -e "${RED}❌ $config_file still contains hardcoded defaults${NC}"
                issues_found=$((issues_found + 1))
            fi
        fi
    done
    
    if [ $issues_found -eq 0 ]; then
        echo -e "${GREEN}✅ All hardcoded security issues fixed${NC}"
    else
        echo -e "${RED}❌ $issues_found security issues still present${NC}"
    fi
}

# Main execution
echo -e "${BLUE}🔍 Checking Prerequisites...${NC}"
check_branch

echo ""
echo -e "${BLUE}🎮 Phase 1: Restoring GPU/NVLink Optimization...${NC}"
echo "=================================================="

# Restore GPU configuration
restore_file "scripts/configure-gpu.sh" "GPU Configuration Script"
restore_file "MULTI_GPU_CONFIGURATION_GUIDE.md" "Multi-GPU Configuration Guide"

echo ""
echo -e "${BLUE}🧹 Phase 2: Verifying Docker Environment Wipe...${NC}"
echo "=============================================="

# Check current docker wipe functionality
test_docker_wipe

echo ""
echo -e "${BLUE}🔒 Phase 3: Fixing Hardcoded Security Issues...${NC}"
echo "============================================="

# Fix hardcoded security issues
fix_hardcoded_issues

echo ""
echo -e "${BLUE}🧪 Phase 4: Testing Restored Functionality...${NC}"
echo "============================================="

# Test GPU functionality
test_gpu_functionality

# Test docker wipe functionality
test_docker_wipe

# Validate security fixes
validate_security_fixes

echo ""
echo -e "${GREEN}🎉 Focused Restoration Summary${NC}"
echo "============================="
echo -e "Features restored: ${BLUE}$RESTORED_FEATURES${NC}"
echo -e "Security issues fixed: ${BLUE}$FIXED_ISSUES${NC}"

echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Test GPU configuration: ./scripts/configure-gpu.sh --detect"
echo "2. Test environment wipe: ./start-environment.sh first-run (DESTRUCTIVE!)"
echo "3. Generate fresh secrets: python3 setup_secrets.py"
echo "4. Verify no hardcoded values remain in configuration files"

echo ""
echo -e "${BLUE}🔧 Available Commands:${NC}"
echo "- GPU detection: ./scripts/configure-gpu.sh --detect"
echo "- GPU configuration: ./scripts/configure-gpu.sh --configure"
echo "- Environment wipe: ./start-environment.sh first-run"
echo "- Secrets generation: python3 setup_secrets.py"

echo ""
echo -e "${GREEN}🎯 Focused restoration completed!${NC}"
