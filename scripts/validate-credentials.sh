#!/bin/bash
# Pre-deployment credential validation script
# Validates credentials before starting services to prevent authentication failures

set -euo pipefail

# Configuration
ENVIRONMENT="${1:-development}"
STRICT_MODE="${2:-false}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
}

# Change to project root
cd "$PROJECT_ROOT"

# Banner
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           Credential Validation Pre-Deployment Check         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
log_info "Environment: $ENVIRONMENT"
log_info "Strict Mode: $STRICT_MODE"
echo ""

# Check Python is available
if ! command -v python3 &> /dev/null; then
    log_error "python3 is not installed or not in PATH"
    exit 1
fi

# Step 1: Check credential files exist
log_step "Step 1/7: Checking credential files exist..."
SECRETS_FILE="secrets/.env.${ENVIRONMENT}.json"
ENV_FILE=".env.${ENVIRONMENT}"

if [ ! -f "$SECRETS_FILE" ]; then
    log_error "Secrets file not found: $SECRETS_FILE"
    log_info "Run: make setup-secrets"
    exit 1
fi
log_success "Found secrets file: $SECRETS_FILE"

if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file not found: $ENV_FILE"
    log_info "Run: make setup-secrets"
    exit 1
fi
log_success "Found environment file: $ENV_FILE"

# Step 2: Validate compose schema
log_step "Step 2/7: Validating Docker Compose schema..."
if [ -f "scripts/compose-generator.py" ]; then
    if python3 scripts/compose-generator.py --validate-only 2>&1; then
        log_success "Schema validation passed"
    else
        log_error "Schema validation failed"
        exit 1
    fi
else
    log_warning "compose-generator.py not found, skipping schema validation"
fi

# Step 3: Validate security (no hardcoded defaults)
log_step "Step 3/7: Validating security configuration..."
HARDCODED_FOUND=0

if [ -f "schemas/compose-schema.yaml" ]; then
    if grep -q ":-postgres\|:-minioadmin" schemas/compose-schema.yaml 2>/dev/null; then
        log_error "Hardcoded defaults found in schema"
        HARDCODED_FOUND=1
    fi
fi

if find services/ -name "config.py" -exec grep -l ', "postgres")\|, "minioadmin")' {} \; 2>/dev/null | grep -q .; then
    log_error "Hardcoded defaults found in service configs"
    HARDCODED_FOUND=1
fi

if [ $HARDCODED_FOUND -eq 0 ]; then
    log_success "No hardcoded defaults detected"
else
    log_error "Security validation failed"
    exit 1
fi

# Step 4: Validate credential strength
log_step "Step 4/7: Validating credential strength..."
if python3 -m security.credential_validator strength \
    --environment "$ENVIRONMENT" \
    --workspace . 2>&1; then
    log_success "Credential strength validation passed"
else
    log_error "Credential strength validation failed"
    if [ "$STRICT_MODE" = "true" ]; then
        exit 1
    else
        log_warning "Continuing despite warnings (strict mode disabled)"
    fi
fi

# Step 5: Check for placeholder values
log_step "Step 5/7: Checking for placeholder values..."
if [ "$ENVIRONMENT" = "production" ] || [ "$STRICT_MODE" = "true" ]; then
    STRICT_FLAG="--strict"
else
    STRICT_FLAG=""
fi

if python3 -m security.credential_validator placeholders \
    --environment "$ENVIRONMENT" \
    --workspace . \
    $STRICT_FLAG 2>&1; then
    log_success "No placeholder values detected"
else
    log_error "Placeholder values detected"
    if [ "$ENVIRONMENT" = "production" ] || [ "$STRICT_MODE" = "true" ]; then
        log_error "Placeholders are not allowed in $ENVIRONMENT environment"
        exit 1
    else
        log_warning "Placeholders found (OK for development)"
    fi
fi

# Step 6: Validate consistency
log_step "Step 6/7: Validating credential consistency..."
if python3 -m security.credential_validator consistency \
    --environment "$ENVIRONMENT" \
    --workspace . 2>&1; then
    log_success "Credential consistency validated"
else
    log_error "Credential consistency validation failed"
    log_info "Secrets in JSON file don't match .env file"
    exit 1
fi

# Step 7: Validate template rendering
log_step "Step 7/7: Validating Jinja2 template rendering..."
if python3 -m security.credential_validator templates \
    --environment "$ENVIRONMENT" \
    --workspace . 2>&1; then
    log_success "All templates render correctly"
else
    log_error "Template validation failed"
    if [ "$STRICT_MODE" = "true" ]; then
        exit 1
    else
        log_warning "Template errors detected (continuing)"
    fi
fi

# Summary
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Validation Summary                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Run comprehensive validation and get JSON output
VALIDATION_OUTPUT=$(python3 -m security.credential_validator validate \
    --environment "$ENVIRONMENT" \
    --workspace . \
    --json 2>&1 || true)

# Parse JSON output
PASSED=$(echo "$VALIDATION_OUTPUT" | grep -o '"passed": [a-z]*' | grep -o '[a-z]*$' || echo "false")
ERROR_COUNT=$(echo "$VALIDATION_OUTPUT" | grep -o '"errors":' | wc -l || echo "0")
WARNING_COUNT=$(echo "$VALIDATION_OUTPUT" | grep -o '"warnings":' | wc -l || echo "0")

echo "Environment: $ENVIRONMENT"
echo "Validation Status: $([ "$PASSED" = "true" ] && echo -e "${GREEN}PASSED${NC}" || echo -e "${RED}FAILED${NC}")"
echo "Errors: $ERROR_COUNT"
echo "Warnings: $WARNING_COUNT"
echo ""

if [ "$PASSED" = "true" ]; then
    log_success "All validation checks passed!"
    echo ""
    log_info "Safe to deploy with: make start-$ENVIRONMENT"
    echo ""
    exit 0
else
    log_error "Validation failed. Please fix the issues before deploying."
    echo ""
    log_info "Run with details: python3 -m security.credential_validator validate -e $ENVIRONMENT"
    echo ""
    exit 1
fi

