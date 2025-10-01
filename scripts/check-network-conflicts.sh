#!/bin/bash

# Network Conflict Detection Script
# Checks for potential network conflicts before starting stacks

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

# Function to check if a subnet overlaps with existing networks
check_subnet_conflict() {
    local subnet=$1
    local network_name=$2
    
    # Extract network and CIDR from subnet (e.g., "172.30.0.0/24")
    local network=$(echo "$subnet" | cut -d'/' -f1)
    local cidr=$(echo "$subnet" | cut -d'/' -f2)
    
    # Get all existing Docker networks
    local existing_networks
    existing_networks=$(docker network ls --format "{{.Name}}" | grep -v "^bridge$\|^host$\|^none$" || true)
    
    if [ -z "$existing_networks" ]; then
        return 0  # No existing networks, no conflict
    fi
    
    # Check each existing network for subnet conflicts
    while IFS= read -r existing_network; do
        if [ -z "$existing_network" ]; then
            continue
        fi
        
        # Get subnet information for existing network
        local existing_subnet
        existing_subnet=$(docker network inspect "$existing_network" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null || echo "")
        
        if [ -z "$existing_subnet" ]; then
            continue
        fi
        
        # Check if subnets overlap using Python for precise calculation
        local conflict_check
        conflict_check=$(python3 -c "
import ipaddress
try:
    new_net = ipaddress.ip_network('$subnet')
    existing_net = ipaddress.ip_network('$existing_subnet')
    
    if new_net.overlaps(existing_net):
        print('CONFLICT')
    else:
        print('OK')
except Exception as e:
    print('ERROR')
" 2>/dev/null || echo "ERROR")
        
        if [ "$conflict_check" = "CONFLICT" ]; then
            print_status "$RED" "❌ Network conflict detected!"
            print_status "$RED" "   New network: $network_name ($subnet)"
            print_status "$RED" "   Existing network: $existing_network ($existing_subnet)"
            return 1
        fi
    done <<< "$existing_networks"
    
    return 0
}

# Function to validate network configuration from schema
validate_network_config() {
    print_section "Validating Network Configuration"
    
    if [ ! -f "$SCHEMA_FILE" ]; then
        print_status "$RED" "❌ Schema file not found: $SCHEMA_FILE"
        return 1
    fi
    
    # Extract stack networks from schema
    local stack_networks
    stack_networks=$(python3 -c "
import yaml
import sys

try:
    with open('$SCHEMA_FILE', 'r') as f:
        schema = yaml.safe_load(f)
    
    stack_networks = schema.get('stack_networks', {})
    
    for network_name, config in stack_networks.items():
        if 'ipam' in config and 'config' in config['ipam']:
            for ipam_config in config['ipam']['config']:
                if 'subnet' in ipam_config:
                    print(f'{network_name}:{ipam_config[\"subnet\"]}')
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        print_status "$RED" "❌ Failed to parse schema file"
        return 1
    fi
    
    local conflicts_found=0
    
    # Check each stack network for conflicts
    while IFS= read -r network_info; do
        if [ -z "$network_info" ]; then
            continue
        fi
        
        local network_name=$(echo "$network_info" | cut -d':' -f1)
        local subnet=$(echo "$network_info" | cut -d':' -f2)
        
        print_status "$YELLOW" "🔍 Checking network: $network_name ($subnet)"
        
        if ! check_subnet_conflict "$subnet" "$network_name"; then
            conflicts_found=1
        else
            print_status "$GREEN" "   ✅ No conflicts detected"
        fi
    done <<< "$stack_networks"
    
    if [ $conflicts_found -eq 1 ]; then
        return 1
    fi
    
    print_status "$GREEN" "✅ All network configurations are valid"
    return 0
}

# Function to check existing Docker networks
check_existing_networks() {
    print_section "Existing Docker Networks"
    
    local networks
    networks=$(docker network ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" | grep -v "^NAME" || true)
    
    if [ -z "$networks" ]; then
        print_status "$YELLOW" "No Docker networks found"
        return 0
    fi
    
    echo "$networks"
    echo ""
    
    # Show detailed network information
    print_status "$BLUE" "Network Details:"
    while IFS= read -r line; do
        if [ -z "$line" ] || [[ "$line" == NAME* ]]; then
            continue
        fi
        
        local network_name=$(echo "$line" | awk '{print $1}')
        if [[ "$network_name" =~ ^(bridge|host|none)$ ]]; then
            continue
        fi
        
        local subnet
        subnet=$(docker network inspect "$network_name" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null || echo "Unknown")
        
        print_status "$YELLOW" "  $network_name: $subnet"
    done <<< "$networks"
}

# Function to suggest network configuration
suggest_network_config() {
    print_section "Network Configuration Suggestions"
    
    print_status "$BLUE" "Current stack network configuration:"
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
" 2>/dev/null || print_status "$RED" "Failed to read network configuration"
    
    echo ""
    print_status "$BLUE" "Available subnet ranges (not in use):"
    print_status "$YELLOW" "  172.30.0.0/16 - 172.30.255.255 (Current stack range)"
    print_status "$YELLOW" "  172.31.0.0/16 - 172.31.255.255"
    print_status "$YELLOW" "  172.32.0.0/16 - 172.32.255.255"
    print_status "$YELLOW" "  192.168.100.0/24 - 192.168.100.255"
    print_status "$YELLOW" "  192.168.200.0/24 - 192.168.200.255"
}

# Function to clean up orphaned networks
cleanup_orphaned_networks() {
    print_section "Cleaning Up Orphaned Networks"
    
    local orphaned_networks
    orphaned_networks=$(docker network ls --format "{{.Name}}" | grep "multimodal" | grep -v "multimodal-net" || true)
    
    if [ -z "$orphaned_networks" ]; then
        print_status "$GREEN" "✅ No orphaned multimodal networks found"
        return 0
    fi
    
    print_status "$YELLOW" "Found orphaned networks:"
    echo "$orphaned_networks"
    echo ""
    
    read -p "Do you want to remove these orphaned networks? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        while IFS= read -r network; do
            if [ -n "$network" ]; then
                print_status "$YELLOW" "Removing network: $network"
                docker network rm "$network" 2>/dev/null || print_status "$RED" "Failed to remove $network"
            fi
        done <<< "$orphaned_networks"
        print_status "$GREEN" "✅ Orphaned networks cleaned up"
    else
        print_status "$YELLOW" "Skipping network cleanup"
    fi
}

# Main function
main() {
    print_status "$BLUE" "🌐 Network Conflict Detection and Management"
    print_status "$BLUE" "=============================================="
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_status "$RED" "❌ Docker is not running or not accessible"
        exit 1
    fi
    
    # Check existing networks
    check_existing_networks
    
    # Validate network configuration
    if ! validate_network_config; then
        print_status "$RED" "❌ Network conflicts detected!"
        echo ""
        suggest_network_config
        echo ""
        print_status "$RED" "Please resolve network conflicts before starting stacks."
        exit 1
    fi
    
    # Suggest cleanup if needed
    local orphaned_networks
    orphaned_networks=$(docker network ls --format "{{.Name}}" | grep "multimodal" | grep -v "multimodal-net" || true)
    
    if [ -n "$orphaned_networks" ]; then
        echo ""
        print_status "$YELLOW" "⚠️  Orphaned multimodal networks detected"
        cleanup_orphaned_networks
    fi
    
    print_status "$GREEN" "✅ Network conflict check completed successfully"
    print_status "$GREEN" "✅ All networks are ready for stack deployment"
}

# Handle command line arguments
case "${1:-check}" in
    "check")
        main
        ;;
    "cleanup")
        cleanup_orphaned_networks
        ;;
    "suggest")
        suggest_network_config
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [check|cleanup|suggest|help]"
        echo ""
        echo "Commands:"
        echo "  check   - Check for network conflicts (default)"
        echo "  cleanup - Clean up orphaned networks"
        echo "  suggest - Show network configuration suggestions"
        echo "  help    - Show this help message"
        ;;
    *)
        print_status "$RED" "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
