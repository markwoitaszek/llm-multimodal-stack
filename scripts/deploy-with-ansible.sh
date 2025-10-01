#!/bin/bash

# Deploy Multimodal LLM Stack using Ansible and OpenBao
# This script demonstrates how to deploy the stack using the normalized structure

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ANSIBLE_DIR="$PROJECT_ROOT/ansible"
INVENTORY_FILE="$ANSIBLE_DIR/inventory/example.yml"
PLAYBOOK_FILE="$ANSIBLE_DIR/render-env-templates.yml"

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

# Help function
show_help() {
    cat << EOF
Deploy Multimodal LLM Stack with Ansible and OpenBao

Usage: $0 [OPTIONS] ENVIRONMENT [TARGET_HOSTS]

Arguments:
    ENVIRONMENT     Target environment (dev, staging, prod)
    TARGET_HOSTS    Comma-separated list of hosts (optional)

Options:
    -h, --help              Show this help message
    -i, --inventory FILE    Use custom inventory file
    -p, --playbook FILE     Use custom playbook file
    -v, --verbose           Enable verbose output
    -c, --check             Run in check mode (dry run)
    -t, --tags TAGS         Run specific tags
    --vault-pass            Prompt for vault password
    --ask-pass              Prompt for SSH password
    --ask-become-pass       Prompt for become password

Examples:
    $0 dev                           # Deploy to development environment
    $0 staging llm-staging-01        # Deploy to specific staging host
    $0 prod -c                       # Check mode for production
    $0 dev -t core,env               # Run only core and env tags
    $0 prod --vault-pass             # Deploy to production with vault password

Environment Variables:
    VAULT_ADDR           OpenBao server address
    VAULT_ROLE_ID        OpenBao role ID for authentication
    VAULT_SECRET_ID      OpenBao secret ID for authentication
    DEBUG                Enable debug mode (true/false)
    LOG_LEVEL            Log level (DEBUG, INFO, WARN, ERROR)

EOF
}

# Parse command line arguments
VERBOSE=false
CHECK_MODE=false
VAULT_PASS=false
ASK_PASS=false
ASK_BECOME_PASS=false
TAGS=""
INVENTORY="$INVENTORY_FILE"
PLAYBOOK="$PLAYBOOK_FILE"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -i|--inventory)
            INVENTORY="$2"
            shift 2
            ;;
        -p|--playbook)
            PLAYBOOK="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--check)
            CHECK_MODE=true
            shift
            ;;
        -t|--tags)
            TAGS="$2"
            shift 2
            ;;
        --vault-pass)
            VAULT_PASS=true
            shift
            ;;
        --ask-pass)
            ASK_PASS=true
            shift
            ;;
        --ask-become-pass)
            ASK_BECOME_PASS=true
            shift
            ;;
        -*)
            log_error "Unknown option $1"
            show_help
            exit 1
            ;;
        *)
            if [[ -z "$ENVIRONMENT" ]]; then
                ENVIRONMENT="$1"
            elif [[ -z "$TARGET_HOSTS" ]]; then
                TARGET_HOSTS="$1"
            else
                log_error "Too many arguments"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "Environment is required"
    show_help
    exit 1
fi

# Validate environment
case "$ENVIRONMENT" in
    dev|development|staging|prod|production)
        log_info "Deploying to $ENVIRONMENT environment"
        ;;
    *)
        log_error "Invalid environment: $ENVIRONMENT"
        log_error "Valid environments: dev, staging, prod"
        exit 1
        ;;
esac

# Check if inventory file exists
if [[ ! -f "$INVENTORY" ]]; then
    log_error "Inventory file not found: $INVENTORY"
    exit 1
fi

# Check if playbook file exists
if [[ ! -f "$PLAYBOOK" ]]; then
    log_error "Playbook file not found: $PLAYBOOK"
    exit 1
fi

# Set environment variables
export ENV="$ENVIRONMENT"
export DEBUG="${DEBUG:-false}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Build ansible-playbook command
ANSIBLE_CMD="ansible-playbook"
ANSIBLE_CMD="$ANSIBLE_CMD -i $INVENTORY"
ANSIBLE_CMD="$ANSIBLE_CMD $PLAYBOOK"

# Add target hosts if specified
if [[ -n "$TARGET_HOSTS" ]]; then
    ANSIBLE_CMD="$ANSIBLE_CMD --limit $TARGET_HOSTS"
else
    # Use environment-specific hosts
    case "$ENVIRONMENT" in
        dev|development)
            ANSIBLE_CMD="$ANSIBLE_CMD --limit development"
            ;;
        staging)
            ANSIBLE_CMD="$ANSIBLE_CMD --limit staging"
            ;;
        prod|production)
            ANSIBLE_CMD="$ANSIBLE_CMD --limit production"
            ;;
    esac
fi

# Add optional flags
if [[ "$VERBOSE" == true ]]; then
    ANSIBLE_CMD="$ANSIBLE_CMD -vvv"
fi

if [[ "$CHECK_MODE" == true ]]; then
    ANSIBLE_CMD="$ANSIBLE_CMD --check"
fi

if [[ -n "$TAGS" ]]; then
    ANSIBLE_CMD="$ANSIBLE_CMD --tags $TAGS"
fi

if [[ "$VAULT_PASS" == true ]]; then
    ANSIBLE_CMD="$ANSIBLE_CMD --ask-vault-pass"
fi

if [[ "$ASK_PASS" == true ]]; then
    ANSIBLE_CMD="$ANSIBLE_CMD --ask-pass"
fi

if [[ "$ASK_BECOME_PASS" == true ]]; then
    ANSIBLE_CMD="$ANSIBLE_CMD --ask-become-pass"
fi

# Add extra variables
ANSIBLE_CMD="$ANSIBLE_CMD -e env=$ENVIRONMENT"
ANSIBLE_CMD="$ANSIBLE_CMD -e debug_env=$DEBUG"
ANSIBLE_CMD="$ANSIBLE_CMD -e log_level_env=$LOG_LEVEL"

# Add OpenBao configuration if provided
if [[ -n "$VAULT_ADDR" ]]; then
    ANSIBLE_CMD="$ANSIBLE_CMD -e vault_addr_env=$VAULT_ADDR"
fi

if [[ -n "$VAULT_ROLE_ID" ]]; then
    ANSIBLE_CMD="$ANSIBLE_CMD -e vault_role_id_env=$VAULT_ROLE_ID"
fi

if [[ -n "$VAULT_SECRET_ID" ]]; then
    ANSIBLE_CMD="$ANSIBLE_CMD -e vault_secret_id_env=$VAULT_SECRET_ID"
fi

# Display configuration
log_info "Deployment Configuration:"
log_info "  Environment: $ENVIRONMENT"
log_info "  Inventory: $INVENTORY"
log_info "  Playbook: $PLAYBOOK"
log_info "  Target Hosts: ${TARGET_HOSTS:-"environment-specific"}"
log_info "  Check Mode: $CHECK_MODE"
log_info "  Verbose: $VERBOSE"
log_info "  Tags: ${TAGS:-"all"}"

if [[ -n "$VAULT_ADDR" ]]; then
    log_info "  OpenBao Address: $VAULT_ADDR"
fi

# Confirm deployment (unless in check mode)
if [[ "$CHECK_MODE" != true ]]; then
    echo
    read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled"
        exit 0
    fi
fi

# Execute deployment
log_info "Starting deployment..."
echo

# Run the ansible-playbook command
eval $ANSIBLE_CMD

# Check exit status
if [[ $? -eq 0 ]]; then
    log_success "Deployment completed successfully"
    
    if [[ "$CHECK_MODE" != true ]]; then
        echo
        log_info "Next steps:"
        log_info "1. Verify environment files in /etc/llm-ms/.env.d/"
        log_info "2. Start Docker Compose services:"
        log_info "   docker compose up -d"
        log_info "3. Check service health:"
        log_info "   docker compose ps"
        log_info "4. View service logs:"
        log_info "   docker compose logs <service-name>"
    fi
else
    log_error "Deployment failed"
    exit 1
fi