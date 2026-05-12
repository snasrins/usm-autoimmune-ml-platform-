#!/bin/bash
# ============================================
# USM Autoimmune ML Platform - Deployment Script for RTX6000
# Usage: ./deploy.sh
# ============================================

set -e  # Exit on any error
set -u  # Exit on undefined variable
set -o pipefail  # Catch errors in pipes

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

print_status()  { echo -e "${GREEN}[✓]${NC} $1"; }
print_error()   { echo -e "${RED}[✗]${NC} $1"; }
print_info()    { echo -e "${YELLOW}[i]${NC} $1"; }
print_header()  { echo -e "${BLUE}=== $1 ===${NC}"; }

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_DIR="$(pwd)"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"

# ── Pre-flight Checks ─────────────────────────────────────────────────────────
print_header "Pre-flight Checks"

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi
print_status "Docker found"

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed"
    exit 1
fi
print_status "Docker Compose found"

if [ ! -f ".env" ]; then
    print_error ".env file not found. Copy .env.example to .env and configure it."
    exit 1
fi
print_status ".env file found"

# ── Pull Latest Code ──────────────────────────────────────────────────────────
print_header "Pulling Latest Code"
git pull origin main || {
    print_info "Git pull failed or not in a git repository. Continuing anyway..."
}

# ── Build and Start Services ──────────────────────────────────────────────────
print_header "Building and Starting Services"

print_info "Stopping existing containers..."
docker compose $COMPOSE_FILES down || true

print_info "Building images (this may take several minutes)..."
docker compose $COMPOSE_FILES build

print_info "Starting services..."
docker compose $COMPOSE_FILES up -d

# ── Wait for Services ─────────────────────────────────────────────────────────
print_header "Waiting for Services to Start"
print_info "Waiting 30 seconds for services to initialize..."
sleep 30

# ── Verify Deployment ─────────────────────────────────────────────────────────
print_header "Verifying Deployment"

# Check container status
print_info "Checking container status..."
if docker compose $COMPOSE_FILES ps | grep -q "Exit"; then
    print_error "Some containers failed to start:"
    docker compose $COMPOSE_FILES ps
    echo ""
    print_info "Showing logs for failed containers:"
    docker compose $COMPOSE_FILES logs --tail=50
    exit 1
fi
print_status "All containers are running"

# Test backend health endpoint
print_info "Testing backend health endpoint..."
if curl -sf http://localhost/api/health > /dev/null 2>&1; then
    print_status "Backend health check passed"
else
    print_error "Backend health check failed. Showing backend logs:"
    docker compose $COMPOSE_FILES logs fastapi --tail=30
    exit 1
fi

# Test frontend
print_info "Testing frontend..."
if curl -sf http://localhost/ > /dev/null 2>&1; then
    print_status "Frontend is responding"
else
    print_error "Frontend is not responding"
fi

# ── Cleanup ───────────────────────────────────────────────────────────────────
print_header "Cleanup"
print_info "Removing unused images..."
docker image prune -f

# ── Deployment Summary ────────────────────────────────────────────────────────
print_header "Deployment Summary"

echo ""
docker compose $COMPOSE_FILES ps
echo ""

print_status "Deployment complete!"
echo ""
print_info "Services are running on:"
print_info "  - Backend API: http://localhost/api"
print_info "  - API Docs: http://localhost/docs"
print_info "  - Frontend: http://localhost/"
print_info "  - Health Check: http://localhost/api/health"
echo ""

# Get server IP
SERVER_IP=$(ip addr show | grep "inet " | grep -v "127.0.0.1" | head -n 1 | awk '{print $2}' | cut -d/ -f1)
if [ -n "$SERVER_IP" ]; then
    echo ""
    print_header "Information for Reverse Proxy"
    echo ""
    echo "  Server IP: $SERVER_IP"
    echo "  Port: 80"
    echo "  Give to your senior: ${SERVER_IP}:80"
    echo ""
    echo "  Health check URL: http://${SERVER_IP}:80/api/health"
    echo "  Frontend URL: http://${SERVER_IP}:80/"
    echo ""
fi

print_info "To view logs: docker compose $COMPOSE_FILES logs -f"
print_info "To stop services: docker compose $COMPOSE_FILES down"
