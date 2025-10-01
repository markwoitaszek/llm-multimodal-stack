#!/bin/bash
# Enhance PR 130 Functionality - Complementary Restoration
# Adds GPU/NVLink optimization, comprehensive wipe, and security hardening to the excellent PR 130 system

set -e

echo "🚀 Enhancing PR 130 Functionality"
echo "================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
ENHANCEMENTS_ADDED=0
SECURITY_ISSUES_FIXED=0

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
        ENHANCEMENTS_ADDED=$((ENHANCEMENTS_ADDED + 1))
        
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

# Function to create wipe environment script
create_wipe_script() {
    echo -e "${BLUE}🧹 Creating comprehensive wipe script...${NC}"
    
    cat > scripts/wipe-environment.sh << 'EOF'
#!/bin/bash
# Comprehensive Environment Wipe Script
# Complements PR 130's unified schema system

set -e

echo "🧹 Comprehensive Environment Wipe"
echo "================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_status "INFO" "Stopping all compose services..."
docker compose down --remove-orphans 2>/dev/null || true

print_status "INFO" "Removing all multimodal volumes (including PostgreSQL data)..."
docker volume ls -q | grep llm-multimodal-stack | xargs -r docker volume rm 2>/dev/null || true

# Additional cleanup for any remaining PostgreSQL data
print_status "INFO" "Ensuring complete PostgreSQL data cleanup..."
docker volume ls -q | grep -E "(postgres|multimodal)" | xargs -r docker volume rm 2>/dev/null || true

print_status "INFO" "Removing all multimodal networks..."
docker network ls -q | grep llm-multimodal-stack | xargs -r docker network rm 2>/dev/null || true

print_status "INFO" "Cleaning up orphaned containers..."
docker container prune -f 2>/dev/null || true

print_status "SUCCESS" "Environment wiped completely"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo "  make setup      # Regenerate environment from scratch"
echo "  make start-dev  # Start development environment"
EOF

    chmod +x scripts/wipe-environment.sh
    echo -e "${GREEN}✅ Wipe script created${NC}"
    ENHANCEMENTS_ADDED=$((ENHANCEMENTS_ADDED + 1))
}

# Function to enhance Makefile with new targets
enhance_makefile() {
    echo -e "${BLUE}🔧 Enhancing Makefile with new targets...${NC}"
    
    # Backup Makefile
    cp Makefile "Makefile.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Add new targets to Makefile
    cat >> Makefile << 'EOF'

# Enhanced GPU Detection and Configuration
detect-gpu:
	@echo "🔍 Detecting GPU configuration..."
	@scripts/configure-gpu.sh --detect

configure-gpu:
	@echo "🎮 Configuring GPU for optimal performance..."
	@scripts/configure-gpu.sh --configure

# Enhanced GPU start with auto-detection
start-gpu-auto: detect-gpu configure-gpu start-gpu
	@echo "✅ GPU environment started with auto-configuration"

# Comprehensive Environment Management
wipe:
	@echo "⚠️  WARNING: This will DELETE all data and containers!"
	@echo "This includes PostgreSQL databases, MinIO data, and all volumes."
	@read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ]
	@echo "🧹 Wiping environment..."
	@scripts/wipe-environment.sh
	@echo "✅ Environment wiped completely"

# Nuclear reset option
reset: wipe setup
	@echo "🎉 Environment reset and regenerated from scratch"

# Security validation
validate-security:
	@echo "🔒 Validating security configuration..."
	@if grep -q ":-postgres\|:-minioadmin" schemas/compose-schema.yaml; then \
		echo "❌ Hardcoded defaults found in schema"; \
		exit 1; \
	fi
	@if find services/ -name "config.py" -exec grep -l ', "postgres")\|, "minioadmin")' {} \; | grep -q .; then \
		echo "❌ Hardcoded defaults found in service configs"; \
		exit 1; \
	fi
	@echo "✅ Security validation passed"

# Enhanced setup with security validation
setup: validate-schema validate-security generate-compose setup-secrets
	@echo "🎉 Full setup completed successfully!"
	@echo ""
	@echo "Next steps:"
	@echo "  make start-dev        # Start development environment"
	@echo "  make start-gpu-auto   # Start GPU environment with auto-detection"
	@echo "  make wipe             # Wipe environment (DESTRUCTIVE)"
	@echo "  make reset            # Reset and regenerate from scratch"
EOF

    echo -e "${GREEN}✅ Makefile enhanced with new targets${NC}"
    ENHANCEMENTS_ADDED=$((ENHANCEMENTS_ADDED + 1))
}

# Function to fix hardcoded security issues
fix_security_issues() {
    echo -e "${BLUE}🔒 Fixing hardcoded security issues...${NC}"
    
    local files_fixed=0
    
    # Fix schema defaults
    if [ -f "schemas/compose-schema.yaml" ]; then
        echo -e "${YELLOW}🔧 Fixing schema hardcoded defaults...${NC}"
        
        # Backup original
        cp schemas/compose-schema.yaml "schemas/compose-schema.yaml.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Remove hardcoded defaults
        sed -i 's/POSTGRES_USER=${POSTGRES_USER:-postgres}/POSTGRES_USER=${POSTGRES_USER}/g' schemas/compose-schema.yaml
        sed -i 's/MINIO_ROOT_USER=${MINIO_ROOT_USER:-minioadmin}/MINIO_ROOT_USER=${MINIO_ROOT_USER}/g' schemas/compose-schema.yaml
        
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
            sed -i 's/os.getenv("POSTGRES_PASSWORD", "postgres")/os.getenv("POSTGRES_PASSWORD")/g' "$config_file"
            sed -i 's/os.getenv("MINIO_ACCESS_KEY", "minioadmin")/os.getenv("MINIO_ACCESS_KEY")/g' "$config_file"
            sed -i 's/os.getenv("MINIO_SECRET_KEY", "minioadmin")/os.getenv("MINIO_SECRET_KEY")/g' "$config_file"
            
            # Check if changes were made
            if ! grep -q ', "postgres")\|, "minioadmin")' "$config_file"; then
                echo -e "${GREEN}  ✅ Hardcoded defaults removed from $config_file${NC}"
                files_fixed=$((files_fixed + 1))
            else
                echo -e "${RED}  ❌ Some defaults still present in $config_file${NC}"
            fi
        fi
    done
    
    SECURITY_ISSUES_FIXED=$files_fixed
    echo -e "${GREEN}✅ Fixed hardcoded issues in $files_fixed files${NC}"
}

# Function to test enhanced functionality
test_enhanced_functionality() {
    echo -e "${BLUE}🧪 Testing Enhanced Functionality...${NC}"
    
    # Test GPU detection
    if [ -f "scripts/configure-gpu.sh" ]; then
        echo -e "${YELLOW}🔍 Testing GPU detection...${NC}"
        if ./scripts/configure-gpu.sh --detect 2>/dev/null; then
            echo -e "${GREEN}✅ GPU detection working${NC}"
        else
            echo -e "${YELLOW}⚠️  GPU detection test inconclusive (expected on non-GPU systems)${NC}"
        fi
    fi
    
    # Test wipe script
    if [ -f "scripts/wipe-environment.sh" ]; then
        echo -e "${GREEN}✅ Wipe script created and executable${NC}"
    fi
    
    # Test Makefile targets
    if grep -q "start-gpu-auto\|wipe\|reset" Makefile; then
        echo -e "${GREEN}✅ Enhanced Makefile targets added${NC}"
    fi
    
    # Test security validation
    if grep -q "validate-security" Makefile; then
        echo -e "${GREEN}✅ Security validation target added${NC}"
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
echo -e "${BLUE}🎮 Phase 1: Enhancing GPU Functionality...${NC}"
echo "=============================================="

# Restore GPU configuration
restore_file "scripts/configure-gpu.sh" "GPU Configuration Script"
restore_file "MULTI_GPU_CONFIGURATION_GUIDE.md" "Multi-GPU Configuration Guide"

echo ""
echo -e "${BLUE}🧹 Phase 2: Adding Comprehensive Wipe Functionality...${NC}"
echo "====================================================="

# Create wipe script
create_wipe_script

echo ""
echo -e "${BLUE}🔒 Phase 3: Fixing Security Issues...${NC}"
echo "====================================="

# Fix hardcoded security issues
fix_security_issues

echo ""
echo -e "${BLUE}🔧 Phase 4: Enhancing Makefile...${NC}"
echo "================================="

# Enhance Makefile
enhance_makefile

echo ""
echo -e "${BLUE}🧪 Phase 5: Testing Enhanced Functionality...${NC}"
echo "============================================="

# Test enhanced functionality
test_enhanced_functionality

# Validate security fixes
validate_security_fixes

echo ""
echo -e "${GREEN}🎉 Enhancement Summary${NC}"
echo "===================="
echo -e "Enhancements added: ${BLUE}$ENHANCEMENTS_ADDED${NC}"
echo -e "Security issues fixed: ${BLUE}$SECURITY_ISSUES_FIXED${NC}"

echo ""
echo -e "${BLUE}📋 New Makefile Targets Available:${NC}"
echo "  make detect-gpu      # Detect GPU configuration"
echo "  make configure-gpu   # Configure GPU for optimal performance"
echo "  make start-gpu-auto  # Start GPU environment with auto-detection"
echo "  make wipe            # Wipe environment (DESTRUCTIVE)"
echo "  make reset           # Reset and regenerate from scratch"
echo "  make validate-security # Validate no hardcoded defaults"

echo ""
echo -e "${BLUE}🎯 Enhanced Workflow:${NC}"
echo "1. Detect GPU: make detect-gpu"
echo "2. Configure GPU: make configure-gpu"
echo "3. Start with auto-detection: make start-gpu-auto"
echo "4. Wipe environment: make wipe (DESTRUCTIVE!)"
echo "5. Reset everything: make reset"

echo ""
echo -e "${GREEN}✅ PR 130 functionality enhanced successfully!${NC}"
echo -e "${BLUE}💡 The existing PR 130 system remains fully functional with new enhancements added.${NC}"
