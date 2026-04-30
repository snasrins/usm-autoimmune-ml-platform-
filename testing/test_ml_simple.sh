#!/bin/bash
# Simple ML Endpoint Test Script
API="http://100.106.132.15:8001/api/v1"
SESSION_ID="66bc02fa-4d3c-419b-a634-07ad447e02bb"
BATCH_ID="05665dc5-624c-4480-9f5f-3781f3ba27fb"

echo "=== ML FEATURE TEST ==="
echo "Session: $SESSION_ID"
echo "Batch: $BATCH_ID"
echo ""

# Login
echo "Logging in..."
TOKEN=$(curl -s -X POST "$API/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=s.nasrin&password=USM@22" | \
    grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Login failed"
    exit 1
fi
echo "Token obtained"
echo ""

# Test endpoints
echo "[1/12] Health Check"
curl -s "$API/ml-utils/health" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "[2/12] Schema Validation"
curl -s -X POST "$API/ml-utils/validate-schema/$SESSION_ID?target_column=clinical.diagnosis" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "[3/12] Upload Provenance"
curl -s "$API/ml-utils/provenance/upload/$BATCH_ID" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "[4/12] Preprocessing Provenance"
curl -s "$API/ml-utils/provenance/preprocessing/$SESSION_ID" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "[5/12] Provenance Chain"
curl -s "$API/ml-utils/provenance/chain/$BATCH_ID" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "[6/12] Prepare ML Data"
curl -s -X POST "$API/ml-utils/prepare-data/$SESSION_ID?target_column=clinical.diagnosis&validate=false&drop_unlabeled=true" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "[7/12] ML Statistics"
curl -s "$API/ml-utils/statistics/$BATCH_ID" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "[8/12] Get Unlabeled"
curl -s "$API/labeling/unlabeled?limit=5" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "[9/12] Labeling Statistics"
curl -s "$API/labeling/statistics" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "[10/12] Batch Assign (skip single/bulk for now)"
curl -s -X POST "$API/labeling/batch-assign?target_column=labels_disease_classification" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"batch_id\":\"$BATCH_ID\",\"label\":\"SLE\",\"confidence\":1.0}" | python3 -m json.tool
echo ""

echo "=== COMPLETE ==="
echo "10 key endpoints tested!"
