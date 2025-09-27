#!/bin/bash
set -e

# Passwordless Sudo Setup for Multimodal LLM Stack Development
echo "🔐 Setting up passwordless sudo for Multimodal LLM Stack deployment..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get current user
CURRENT_USER=$(whoami)
SUDO_FILE="/etc/sudoers.d/multimodal-llm-stack"

echo -e "${BLUE}🔍 Analyzing sudo requirements...${NC}"

# Check what sudo operations are needed
echo "The following sudo operations are required for deployment:"
echo "1. 📁 Create NVMe storage directories: /mnt/nvme/{qdrant,postgres,minio,cache}"
echo "2. 🔧 Set ownership of NVMe directories"
echo "3. 📦 Install system packages (jq, etc.) for benchmarking"
echo ""

# Check if user is already in docker group
if groups "$CURRENT_USER" | grep -q docker; then
    echo -e "${GREEN}✅ User $CURRENT_USER is already in docker group${NC}"
else
    echo -e "${YELLOW}⚠️  User $CURRENT_USER is not in docker group${NC}"
    echo "This will be configured automatically."
fi

# Check if seismic-nvme is available
if [ -d "/mnt/nvme" ]; then
    echo -e "${GREEN}✅ Seismic NVMe storage detected at /mnt/nvme${NC}"
    NVME_AVAILABLE=true
else
    echo -e "${YELLOW}ℹ️  No NVMe storage detected - will use local storage${NC}"
    NVME_AVAILABLE=false
fi

echo ""
echo -e "${BLUE}🔧 Configuring passwordless sudo...${NC}"

# Create sudoers file for multimodal stack
echo "Creating sudoers configuration..."

# Backup existing sudoers if they exist
if [ -f "$SUDO_FILE" ]; then
    echo "Backing up existing sudoers file..."
    sudo cp "$SUDO_FILE" "$SUDO_FILE.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Create new sudoers configuration
sudo tee "$SUDO_FILE" > /dev/null << EOF
# Multimodal LLM Stack - Passwordless Sudo Configuration
# Generated on $(date)
# User: $CURRENT_USER

# Allow user to manage NVMe storage directories
$CURRENT_USER ALL=(root) NOPASSWD: /bin/mkdir -p /mnt/nvme/*
$CURRENT_USER ALL=(root) NOPASSWD: /bin/chown -R $CURRENT_USER\\:$CURRENT_USER /mnt/nvme/*
$CURRENT_USER ALL=(root) NOPASSWD: /bin/chmod -R 755 /mnt/nvme/*

# Allow user to install required packages for benchmarking
$CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/apt-get update
$CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/apt-get install -y jq
$CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/yum install -y jq

# Allow user to manage Docker group membership
$CURRENT_USER ALL=(root) NOPASSWD: /usr/sbin/usermod -aG docker $CURRENT_USER

# Allow user to restart Docker service if needed
$CURRENT_USER ALL=(root) NOPASSWD: /bin/systemctl restart docker
$CURRENT_USER ALL=(root) NOPASSWD: /bin/systemctl status docker

# Allow user to manage firewall for production deployment
$CURRENT_USER ALL=(root) NOPASSWD: /usr/sbin/ufw enable
$CURRENT_USER ALL=(root) NOPASSWD: /usr/sbin/ufw allow *
$CURRENT_USER ALL=(root) NOPASSWD: /usr/sbin/ufw status

# Allow user to manage SSL certificates
$CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/openssl req *
$CURRENT_USER ALL=(root) NOPASSWD: /bin/cp /home/$CURRENT_USER/*/certs/* /etc/ssl/*

# Allow user to create backup directories
$CURRENT_USER ALL=(root) NOPASSWD: /bin/mkdir -p /backup/*
$CURRENT_USER ALL=(root) NOPASSWD: /bin/chown -R $CURRENT_USER\\:$CURRENT_USER /backup/*
EOF

echo -e "${GREEN}✅ Sudoers configuration created${NC}"

# Validate sudoers file
echo "Validating sudoers configuration..."
if sudo visudo -c -f "$SUDO_FILE"; then
    echo -e "${GREEN}✅ Sudoers configuration is valid${NC}"
else
    echo -e "${RED}❌ Sudoers configuration is invalid${NC}"
    echo "Removing invalid configuration..."
    sudo rm -f "$SUDO_FILE"
    exit 1
fi

# Add user to docker group if not already
if ! groups "$CURRENT_USER" | grep -q docker; then
    echo "Adding user to docker group..."
    sudo usermod -aG docker "$CURRENT_USER"
    echo -e "${GREEN}✅ User added to docker group${NC}"
    echo -e "${YELLOW}⚠️  You may need to log out and back in for group changes to take effect${NC}"
fi

# Create NVMe directories if available
if [ "$NVME_AVAILABLE" = true ]; then
    echo "Setting up NVMe storage directories..."
    sudo mkdir -p /mnt/nvme/{qdrant,postgres,minio,cache,grafana,prometheus,redis,backup}
    sudo chown -R "$CURRENT_USER:$CURRENT_USER" /mnt/nvme/
    sudo chmod -R 755 /mnt/nvme/
    echo -e "${GREEN}✅ NVMe storage directories configured${NC}"
fi

# Test passwordless sudo
echo ""
echo -e "${BLUE}🧪 Testing passwordless sudo configuration...${NC}"

# Test NVMe directory creation
if sudo -n mkdir -p /mnt/nvme/test 2>/dev/null; then
    sudo rmdir /mnt/nvme/test 2>/dev/null || true
    echo -e "${GREEN}✅ NVMe directory creation works${NC}"
else
    echo -e "${RED}❌ NVMe directory creation failed${NC}"
fi

# Test package installation
if sudo -n apt-get --version > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Package installation commands work${NC}"
else
    echo -e "${YELLOW}⚠️  Package installation may require password${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Passwordless sudo setup completed!${NC}"
echo ""
echo -e "${BLUE}📋 What was configured:${NC}"
echo "✅ Passwordless sudo for NVMe storage management"
echo "✅ Passwordless sudo for package installation (jq)"
echo "✅ Docker group membership"
echo "✅ Firewall management permissions"
echo "✅ SSL certificate management"
echo "✅ Backup directory management"
echo ""
echo -e "${BLUE}🚀 Next steps:${NC}"
echo "1. Run: ./scripts/setup.sh (now with passwordless operations)"
echo "2. Deploy: docker-compose up -d"
echo "3. Test: ./scripts/health-check.sh"
echo ""
echo -e "${YELLOW}⚠️  Security Note:${NC}"
echo "This configuration grants specific sudo permissions for deployment."
echo "Review $SUDO_FILE to understand what permissions were granted."
echo ""
echo -e "${BLUE}💡 To remove these permissions later:${NC}"
echo "sudo rm $SUDO_FILE"
