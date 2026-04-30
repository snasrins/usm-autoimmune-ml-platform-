#!/bin/bash
# ============================================================================
# Deploy Flexible Schema Migration
# Usage: ./deploy_migration.sh
# ============================================================================

set -e  # Exit on error

echo "=========================================="
echo "USM Autoimmune ML Platform"
echo "Flexible Schema Migration Deployment"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    exit 1
fi

# Step 1: Check database connection
echo -e "${YELLOW}1. Checking database connection...${NC}"
if sudo docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database connection OK${NC}"
else
    echo -e "${RED}❌ Cannot connect to database${NC}"
    exit 1
fi

# Step 2: Backup existing data (if any)
echo -e "${YELLOW}2. Backing up existing data...${NC}"
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
sudo docker exec usm-autoimmune-postgres pg_dump -U usm_db_admin -d usm_autoimmune_registry > "/tmp/$BACKUP_FILE" 2>/dev/null || true
if [ -f "/tmp/$BACKUP_FILE" ]; then
    echo -e "${GREEN}✅ Backup created: /tmp/$BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠️  No backup created (database might be empty)${NC}"
fi

# Step 3: Run SQL migration
echo -e "${YELLOW}3. Running SQL migration...${NC}"
if sudo docker exec -i usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry < scripts/migrations/001_create_flexible_schema.sql; then
    echo -e "${GREEN}✅ Migration completed successfully${NC}"
else
    echo -e "${RED}❌ Migration failed${NC}"
    exit 1
fi

# Step 4: Verify tables
echo -e "${YELLOW}4. Verifying tables...${NC}"
TABLE_COUNT=$(sudo docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | xargs)
echo -e "${GREEN}✅ Found $TABLE_COUNT tables${NC}"

# Step 5: List created tables
echo -e "${YELLOW}5. Created tables:${NC}"
sudo docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "\dt" | grep -E "(patients|diagnoses|lab_|disease_|uploaded_|data_ingestion)" || true

# Step 6: Restart API to load new models
echo -e "${YELLOW}6. Restarting API...${NC}"
sudo docker compose restart fastapi
sleep 5

# Step 7: Check API health
echo -e "${YELLOW}7. Checking API health...${NC}"
if sudo docker exec usm-autoimmune-api curl -s http://127.0.0.1:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ API is healthy${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ MIGRATION DEPLOYMENT COMPLETE!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Seed lab_test_definitions (Task 2)"
echo "  2. Test data insertion"
echo "  3. Import real datasets"
echo ""
