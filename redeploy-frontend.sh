#!/bin/bash
# Force rebuild frontend with no cache
# Run this on RTX6000 to update frontend

echo "🔄 Forcing frontend rebuild with no cache..."

# Stop containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Remove frontend image to force rebuild
docker rmi usm-autoimmune-ml-platform-frontend 2>/dev/null || true

# Rebuild frontend with no cache
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache frontend

# Rebuild nginx (which routes to frontend)
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache nginx

# Start everything
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "✅ Frontend rebuilt and deployed!"
echo ""
echo "📋 Next steps:"
echo "1. Wait 10 seconds for containers to start"
echo "2. Check status: docker compose ps"
echo "3. Open browser to: http://100.122.108.118:8080"
echo "4. Hard refresh browser: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)"
