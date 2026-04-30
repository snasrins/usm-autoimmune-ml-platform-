#!/bin/bash
# ============================================
# Post-Deployment Verification Script
# Server: shaggy@192.168.196.97
# Date: March 30, 2026
# ============================================

echo "=========================================="
echo "USM Autoimmune Platform - Health Check"
echo "Server: shaggy@192.168.196.97"
echo "=========================================="
echo ""

# 1. Check container status
echo "1. Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# 2. Check if all services are healthy
echo "2. Waiting for services to be ready..."
sleep 5
echo ""

# 3. Test PostgreSQL
echo "3. Testing PostgreSQL connection..."
docker exec usm-autoimmune-postgres pg_isready -U usm_db_admin
if [ $? -eq 0 ]; then
    echo "   ✓ PostgreSQL is ready"
else
    echo "   ✗ PostgreSQL is not ready"
fi
echo ""

# 4. Test FastAPI
echo "4. Testing FastAPI Health..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://192.168.196.97:8001/health 2>/dev/null)
if [ "$response" = "200" ]; then
    echo "   ✓ FastAPI is healthy (HTTP $response)"
else
    echo "   ⚠ FastAPI returned HTTP $response (may still be starting...)"
fi
echo ""

# 5. Test MinIO
echo "5. Testing MinIO..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://192.168.196.97:9000/minio/health/live 2>/dev/null)
if [ "$response" = "200" ]; then
    echo "   ✓ MinIO is healthy (HTTP $response)"
else
    echo "   ⚠ MinIO returned HTTP $response"
fi
echo ""

# 6. Show access URLs
echo "6. Access URLs:"
echo "   • API Documentation: http://192.168.196.97:8001/docs"
echo "   • API Health Check:  http://192.168.196.97:8001/health"
echo "   • pgAdmin:           http://192.168.196.97:5050"
echo "   • MinIO Console:     http://192.168.196.97:9001"
echo ""

# 7. Check logs for errors
echo "7. Recent Container Logs (last 10 lines each):"
echo ""
echo "   === FastAPI Logs ==="
docker logs usm-autoimmune-api --tail 10
echo ""
echo "   === PostgreSQL Logs ==="
docker logs usm-autoimmune-postgres --tail 10
echo ""

echo "=========================================="
echo "Health check complete!"
echo "=========================================="
