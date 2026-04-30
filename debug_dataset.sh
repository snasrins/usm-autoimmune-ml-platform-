#!/bin/bash
# Debug dataset generation
API="http://100.106.132.15:8001/api/v1"

echo "=== DATASET GENERATION DEBUG ==="
echo ""

# Login
TOKEN=$(curl -s -X POST "$API/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=s.nasrin&password=USM@22" | \
    grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "✓ Logged in"
echo ""

# Using ML bridge service (which works) to check flattened structure
echo "[1/2] Check flattened columns via ML Bridge Service"
curl -s -X POST "$API/ml-utils/prepare-data/66bc02fa-4d3c-419b-a634-07ad447e02bb?target_column=labels_disease_classification&validate=false&drop_unlabeled=false" \
    -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'metadata' in data:
    print('Columns found:', data['metadata'].get('column_count', 'N/A'))
    print('Has target:', data['metadata'].get('has_target', False))
    print('Labeled count:', data['metadata'].get('labeled_count', 0))
" 2>/dev/null
echo ""

# Try dataset generation
echo "[2/2] Check dataset generation columns"
echo "(This will likely fail, but we can see the error details)"
curl -s -X POST "$API/ml/train/prepare-dataset" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"import_batch_id":"05665dc5-624c-4480-9f5f-3781f3ba27fb","target_column":"labels_disease_classification","test_size":0.2}' \
    | python3 -m json.tool

echo ""
echo "=== ANALYSIS  ==="
echo "If ML Bridge Service finds the target column but dataset generation doesn't,"
echo "there's a discrepancy in the JSONB flattening logic between the two services."
