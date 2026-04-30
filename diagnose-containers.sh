#!/bin/bash
# ============================================
# Container Troubleshooting Script
# ============================================

echo "=========================================="
echo "Diagnosing Container Issues"
echo "=========================================="
echo ""

echo "1. All containers (including stopped):"
docker ps -a | grep -E "usm-autoimmune|CONTAINER"
echo ""

echo "2. Docker Compose service status:"
docker compose ps
echo ""

echo "3. Container logs - PostgreSQL:"
echo "================================"
docker logs usm-autoimmune-postgres --tail 50 2>&1
echo ""

echo "4. Container logs - FastAPI:"
echo "================================"
docker logs usm-autoimmune-api --tail 50 2>&1
echo ""

echo "5. Container logs - pgAdmin:"
echo "================================"
docker logs usm-autoimmune-pgadmin --tail 20 2>&1
echo ""

echo "6. Network status:"
docker network ls | grep usm
echo ""

echo "7. Volume status:"
docker volume ls | grep usm
echo ""

echo "=========================================="
echo "Diagnosis complete"
echo "=========================================="
