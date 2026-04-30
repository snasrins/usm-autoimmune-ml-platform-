#!/bin/bash
# ============================================================
# Complete ML Feature Testing - All 12 Endpoints
# Date: April 8, 2026
# ============================================================

API="http://100.106.132.15:8001/api/v1/auth/login"

echo "=== COMPLETE ML FEATURE TEST ==="
echo "Testing all 12 ML endpoints"
echo ""

# ============================================================
# STEP 1: LOGIN & GET TOKEN
# ============================================================
echo "[STEP 1] Authenticating..."
LOGIN_RESPONSE=$(curl -s -X POST "$API/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=s.nasrin&password=USM@22" | \

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "ERROR: Login failed!"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

echo "✓ Authenticated successfully"
echo ""

# ============================================================
# STEP 2: UPLOAD TEST DATA
# ============================================================
echo "[STEP 2] Upload your SLE Excel file now using Swagger UI"
echo "Endpoint: POST /api/v1/flexible/preview/upload"
echo "After upload, enter the session_id and batch_id below:"
echo ""
read -p "Enter session_id: " SESSION_ID
read -p "Enter batch_id: " BATCH_ID
echo ""

# ============================================================
# TEST 1: ML Health Check
# ============================================================
echo "[1/12] ML Health Check"
curl -s "$API/ml-utils/health" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""
sleep 1

# ============================================================
# TEST 2: Schema Validation
# ============================================================
echo "[2/12] Schema Validation"
curl -s -X POST "$API/ml-utils/validate-schema/$SESSION_ID?target_column=clinical.diagnosis&min_records=5" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""
sleep 1

# ============================================================
# TEST 3: Upload Provenance
# ============================================================
echo "[3/12] Upload Provenance"
curl -s "$API/ml-utils/provenance/upload/$BATCH_ID" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""
sleep 1

# ============================================================
# TEST 4: Preprocessing Provenance
# ============================================================
echo "[4/12] Preprocessing Provenance"
curl -s "$API/ml-utils/provenance/preprocessing/$SESSION_ID" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""
sleep 1

# ============================================================
# TEST 5: Complete Provenance Chain
# ============================================================
echo "[5/12] Complete Provenance Chain"
curl -s "$API/ml-utils/provenance/chain/$BATCH_ID" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""
sleep 1

# ============================================================
# TEST 6: Prepare ML Data (ML Bridge)
# ============================================================
echo "[6/12] Prepare ML Data (Bridge Service)"
PREPARE_RESPONSE=$(curl -s -X POST "$API/ml-utils/prepare-data/$SESSION_ID?target_column=clinical.diagnosis&validate=false&drop_unlabeled=true" \
    -H "Authorization: Bearer $TOKEN")
echo "$PREPARE_RESPONSE" | python3 -m json.tool
echo ""
sleep 1

# ============================================================
# TEST 7: ML Statistics
# ============================================================
echo "[7/12] ML Statistics"
curl -s "$API/ml-utils/statistics/$BATCH_ID" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""
sleep 1

# ============================================================
# TEST 8: Get Unlabeled Records
# ============================================================
echo "[8/12] Get Unlabeled Records"
UNLABELED=$(curl -s "$API/labeling/unlabeled?limit=5" \
    -H "Authorization: Bearer $TOKEN")
echo "$UNLABELED" | python3 -m json.tool

# Extract first record ID
RECORD_ID=$(echo "$UNLABELED" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('unlabeled_records', [{}])[0].get('id', ''))" 2>/dev/null)
echo ""
echo "First unlabeled record ID: $RECORD_ID"
echo ""
sleep 1

# ============================================================
# TEST 9: Labeling Statistics
# ============================================================
echo "[9/12] Labeling Statistics"
curl -s "$API/labeling/statistics" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""
sleep 1

# ============================================================
# TEST 10: Assign Single Label
# ============================================================
echo "[10/12] Assign Single Label"
if [ ! -z "$RECORD_ID" ]; then
    curl -s -X POST "$API/labeling/assign?target_column=labels_disease_classification" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"record_id\": \"$RECORD_ID\",
            \"label\": \"SLE\",
            \"confidence\": 0.95,
            \"notes\": \"Test single label assignment\"
        }" | python3 -m json.tool
else
    echo "Skipped - No record ID available"
fi
echo ""
sleep 1

# ============================================================
# TEST 11: Bulk Assign Labels
# ============================================================
echo "[11/12] Bulk Assign Labels"
# Get multiple IDs
IDS=$(echo "$UNLABELED" | python3 -c "import sys, json; data=json.load(sys.stdin); ids=[str(r['id']) for r in data.get('unlabeled_records', [])[:3]]; print('[' + ','.join(['\"' + i + '\"' for i in ids]) + ']')" 2>/dev/null)

if [ "$IDS" != "[]" ]; then
    curl -s -X POST "$API/labeling/bulk-assign?target_column=labels_disease_classification" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"record_ids\": $IDS,
            \"label\": \"SLE\",
            \"confidence\": 0.9,
            \"notes\": \"Bulk label assignment test\"
        }" | python3 -m json.tool
else
    echo "Skipped - No unlabeled records"
fi
echo ""
sleep 1

# ============================================================
# TEST 12: Batch Assign Label
# ============================================================
echo "[12/12] Batch Assign Label (All Records)"
curl -s -X POST "$API/labeling/batch-assign?target_column=labels_disease_classification" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"batch_id\": \"$BATCH_ID\",
        \"label\": \"SLE\",
        \"confidence\": 1.0,
        \"notes\": \"Complete batch labeled as SLE patients\"
    }" | python3 -m json.tool
echo ""

# ============================================================
# SUMMARY
# ============================================================
echo ""
echo "=== TEST COMPLETE ==="
echo "✓ All 12 ML endpoints tested!"
echo ""
echo "Session ID: $SESSION_ID"
echo "Batch ID: $BATCH_ID"
echo "Token: ${TOKEN:0:20}..."
echo ""
echo "Results saved above. Check for any errors or failed tests."
echo ""
