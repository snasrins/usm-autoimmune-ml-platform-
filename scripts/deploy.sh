#!/bin/bash
# ============================================
# USM Autoimmune ML Platform - Auto Deploy Script
# Run this on the GPU server after uploading files
# ============================================

set -e  # Exit on error

echo "=========================================="
echo "USM Autoimmune ML Platform - Deployment"
echo "Date: $(date)"
echo "=========================================="
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check if running on correct server
echo -e "${YELLOW}[1/8] Checking environment...${NC}"
if [ ! -f ~/.zerotier_installed ]; then
    echo "ZeroTier not detected. Will install in next step."
fi
echo -e "${GREEN}✓ Environment check complete${NC}"
echo

# Step 2: Install ZeroTier
echo -e "${YELLOW}[2/8] Installing ZeroTier...${NC}"
if ! command -v zerotier-cli &> /dev/null; then
    echo "Installing ZeroTier..."
    curl -s https://install.zerotier.com | sudo bash
    touch ~/.zerotier_installed
    echo -e "${GREEN}✓ ZeroTier installed${NC}"
else
    echo -e "${GREEN}✓ ZeroTier already installed${NC}"
fi
echo

# Step 3: Join ZeroTier network
echo -e "${YELLOW}[3/8] Joining ZeroTier network...${NC}"
NETWORK_ID="d5e5fb653720782f"
sudo zerotier-cli join $NETWORK_ID
echo -e "${GREEN}✓ Joined network: $NETWORK_ID${NC}"
echo -e "${YELLOW}⚠️  Go to https://my.zerotier.com and AUTHORIZE this device!${NC}"
echo "Press Enter after authorizing the device..."
read

# Check ZeroTier IP
ZT_IP=$(ip addr show | grep -oP '172\.24\.\d+\.\d+' | head -1)
echo -e "${GREEN}✓ ZeroTier IP: $ZT_IP${NC}"
echo

# Step 4: Install Docker
echo -e "${YELLOW}[4/8] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✓ Docker installed${NC}"
else
    echo -e "${GREEN}✓ Docker already installed${NC}"
fi

# Check if user is in docker group
if ! groups | grep -q docker; then
    echo -e "${YELLOW}⚠️  User not in docker group yet${NC}"
    echo "You need to log out and log back in, then run this script again."
    echo "Or run with sudo for now (not recommended for production)"
    exit 1
fi
echo

# Step 5: Install NVIDIA Container Toolkit
echo -e "${YELLOW}[5/8] Installing NVIDIA Container Toolkit...${NC}"
if ! dpkg -l | grep -q nvidia-container-toolkit; then
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
        sudo tee /etc/apt/sources.list.d/nvidia-docker.list
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo systemctl restart docker
    echo -e "${GREEN}✓ NVIDIA Container Toolkit installed${NC}"
else
    echo -e "${GREEN}✓ NVIDIA Container Toolkit already installed${NC}"
fi

# Test GPU access
echo "Testing GPU access in Docker..."
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ GPU access working${NC}"
else
    echo -e "${RED}✗ GPU access failed${NC}"
    exit 1
fi
echo

# Step 6: Install Docker Compose
echo -e "${YELLOW}[6/8] Installing Docker Compose...${NC}"
if ! docker compose version &> /dev/null; then
    sudo apt-get install -y docker-compose-plugin
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✓ Docker Compose already installed${NC}"
fi
docker compose version
echo

# Step 7: Create directory structure
echo -e "${YELLOW}[7/8] Creating directory structure...${NC}"
cd ~/usm-autoimmune-ml-platform
mkdir -p data/uploads data/processed data/raw
mkdir -p models logs ssl
echo -e "${GREEN}✓ Directories created${NC}"
echo

# Verify .env exists
if [ ! -f .env ]; then
    echo -e "${RED}✗ .env file not found!${NC}"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env and update passwords!${NC}"
    echo "nano .env"
    exit 1
fi
echo -e "${GREEN}✓ .env file exists${NC}"
echo

# Step 8: Deploy platform
echo -e "${YELLOW}[8/8] Deploying platform...${NC}"
docker compose up -d

echo
echo "Waiting for services to start (30 seconds)..."
sleep 30

# Check service status
echo
echo "Service Status:"
docker compose ps
echo

# Test deployment
echo -e "${YELLOW}Testing deployment...${NC}"
API_URL="http://$ZT_IP:8000/health"
echo "Testing API: $API_URL"

RESPONSE=$(curl -s -w "\n%{http_code}" $API_URL)
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ API is healthy!${NC}"
    echo "Response: $BODY"
else
    echo -e "${RED}✗ API health check failed (HTTP $HTTP_CODE)${NC}"
    echo "Check logs: docker compose logs fastapi"
fi
echo

# Test database
echo -e "${YELLOW}Testing database...${NC}"
docker compose exec -T postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "\dt" | head -n 20
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database tables created${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
fi
echo

# Summary
echo "=========================================="
echo -e "${GREEN}DEPLOYMENT COMPLETE!${NC}"
echo "=========================================="
echo
echo "Access URLs (via ZeroTier):"
echo "  - API Docs:    http://$ZT_IP:8000/docs"
echo "  - API Health:  http://$ZT_IP:8000/health"
echo "  - PgAdmin:     http://$ZT_IP:5050"
echo "  - Database:    $ZT_IP:5432"
echo
echo "Next Steps:"
echo "  1. Install ZeroTier on your Windows laptop"
echo "  2. Join network: d5e5fb653720782f"
echo "  3. Access the URLs above from your browser"
echo "  4. Change default passwords in .env"
echo "  5. Start building authentication module (Sprint 1)"
echo
echo "View logs:"
echo "  docker compose logs -f"
echo
echo "Stop platform:"
echo "  docker compose down"
echo
echo "=========================================="
