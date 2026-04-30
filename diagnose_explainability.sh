#!/bin/bash
# Diagnostic script to check explainability endpoints
# Run on GPU server: bash diagnose_explainability.sh

echo "========================================"
echo "🔍 Diagnosing Explainability Endpoints"
echo "========================================"
echo ""

# Check if files exist
echo "1. Checking if files exist..."
echo ""

FILES=(
    "app/api/endpoints/explainability.py"
    "app/services/shap_explainer_service.py"
    "app/services/gemma_conversational_service.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists ($(wc -l < "$file") lines)"
    else
        echo "❌ $file NOT FOUND"
    fi
done

echo ""
echo "2. Checking Docker container..."
echo ""

# Check if container is running
docker compose ps fastapi

echo ""
echo "3. Checking for import errors in container..."
echo ""

# Test import in container
docker compose exec fastapi python3 -c "
try:
    from app.api.endpoints import explainability
    print('✅ explainability module imports successfully')
    print(f'   Router: {explainability.router}')
    print(f'   Routes: {len(explainability.router.routes)}')
    for route in explainability.router.routes:
        print(f'      - {route.methods} {route.path}')
except Exception as e:
    print(f'❌ Import error: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "4. Checking if services can import..."
echo ""

docker compose exec fastapi python3 -c "
try:
    from app.services.shap_explainer_service import SHAPExplainerService
    print('✅ SHAPExplainerService imports successfully')
except Exception as e:
    print(f'❌ SHAP service import error: {e}')

try:
    from app.services.gemma_conversational_service import GemmaConversationalService
    print('✅ GemmaConversationalService imports successfully')
except Exception as e:
    print(f'❌ Gemma service import error: {e}')
"

echo ""
echo "5. Checking recent container logs..."
echo ""

docker compose logs --tail=50 fastapi | grep -i "error\|warning\|explainability\|started"

echo ""
echo "6. Checking registered routes in FastAPI..."
echo ""

docker compose exec fastapi python3 -c "
from app.main import app
print('Registered routes:')
for route in app.routes:
    if hasattr(route, 'path') and '/ml/' in route.path:
        methods = getattr(route, 'methods', [])
        print(f'  {methods} {route.path}')
" | grep -E "explain|chat|ask"

echo ""
echo "========================================"
echo "Diagnosis complete!"
echo "========================================"
