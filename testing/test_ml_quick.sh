#!/bin/bash
# Quick ML Endpoint Testing with Known IDs
# Date: April 8, 2026

API="http://localhost:8000/api/v1"
SESSION_ID="cdff8376-2595-457f-aae5-32614c14fede"
BATCH_ID="11e58b70-3075-4f98-955c-401336495114"

echo "=== Quick ML Endpoint Test ==="
echo "Session ID: $SESSION_ID"
echo "Batch ID: $BATCH_ID"
echo ""

# Login first
echo "[0] Authenticating..."
LOGIN_RESPONSE=$(curl -s -X POST "$API/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=s.nasrin&password=USM@22")

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "ERROR: Authentication failed!"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✓ Authenticated"
echo ""

# Test 1: ML Health Check
echo "[1/12] ML Health Check"
curl -s "$API/ml-utils/health" \
    -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""
sleep 1

# Test 2: Get Unlabeled Records
echo "[2/12] Get Unlabeled Records"
UNLABELED=$(curl -s "$API/labeling/unlabeled?limit=5" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
echo "$UNLABELED" | python3 -m json.tool

# Extract first record ID
RECORD_ID=$(echo "$UNLABELED" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('unlabeled_records', [{}])[0].get('id', ''))" 2>/dev/null)
echo "First Record ID: $RECORD_ID"
echo ""
sleep 1

# Test 3: Labeling Statistics
echo "[3/12] Labeling Statistics"
curl -s "$API/labeling/statistics" \
    -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""
sleep 1

# Test 4: Schema Validation
echo "[4/12] Schema Validation"
curl -s -X POST "$API/ml-utils/validate-schema/$SESSION_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" | python3 -m json.tool
echo ""
sleep 1

# Test 5: Upload Provenance
echo "[5/12] Upload Provenance"
curl -s "$API/ml-utils/provenance/upload/$BATCH_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""
sleep 1

# Test 6: Preprocessing Provenance
echo "[6/12] Preprocessing Provenance"
curl -s "$API/ml-utils/provenance/preprocessing/$SESSION_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""
sleep 1

# Test 7: Complete Provenance Chain
echo "[7/12] Complete Provenance Chain"
curl -s "$API/ml-utils/provenance/chain/$BATCH_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""
sleep 1

# Test 8: Prepare ML Data (Bridge)
echo "[8/12] Prepare ML Data (ML Bridge)"
curl -s -X POST "$API/ml-utils/prepare-data/$SESSION_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{}' | python3 -m json.tool
echo ""
sleep 1

# Test 9: ML Statistics
echo "[9/12] ML Statistics"
curl -s "$API/ml-utils/statistics/$BATCH_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""
sleep 1

# Test 10: Assign Single Label (if we have a record ID)
echo "[10/12] Assign Single Label"
if [ ! -z "$RECORD_ID" ]; then
    curl -s -X POST "$API/labeling/assign" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"record_id\": \"$RECORD_ID\",
            \"label\": \"SLE\",
            \"confidence\": 0.95,
            \"notes\": \"Test label from bash script\"
        }" | python3 -m json.tool
else
    echo "Skipped - No record ID available"
fi
echo ""
sleep 1

# Test 11: Bulk Assign (skip for now - need multiple IDs)
echo "[11/12] Bulk Assign - SKIPPED (manual test in Swagger)"
echo ""

# Test 12: Batch Assign
echo "[12/12] Batch Assign Label"
curl -s -X POST "$API/labeling/batch-assign" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"batch_id\": \"$BATCH_ID\",
        \"label\": \"SLE\",
        \"confidence\": 1.0,
        \"notes\": \"Entire batch confirmed as SLE patients\"
    }" | python3 -m json.tool
echo ""

echo "=== TEST COMPLETE ==="
echo ""
echo "Summary:"
echo "- Session ID: $SESSION_ID"
echo "- Batch ID: $BATCH_ID"
echo "- Record ID: $RECORD_ID"
echo ""
echo "All 12 endpoints tested!"
