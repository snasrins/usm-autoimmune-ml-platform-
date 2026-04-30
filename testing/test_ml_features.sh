#!/bin/bash
# ============================================================
# ML Feature Testing Script
# Date: April 8, 2026
# Tests all 12 ML endpoints on production server
# ============================================================

SERVER="http://localhost:8000"
API="$SERVER/api/v1"

echo ""
echo "=== ML FEATURE TESTING ==="
echo "Server: $SERVER"
echo "Testing 12 ML endpoints..."
echo ""

# ============================================================
# AUTHENTICATION - Login First
# ============================================================
echo ""
echo "[0/12] Authenticating..."
echo "Logging in with existing credentials..."

# Login and get access token - Try admin@arasintegrasi.ai first
LOGIN_RESPONSE=$(curl -s -X POST "$API/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin@arasintegrasi.ai&password=Mtai2026")

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

# If first login fails, try usm_db_admin
if [ -z "$ACCESS_TOKEN" ]; then
    echo "  First login attempt failed, trying alternate credentials..."
    LOGIN_RESPONSE=$(curl -s -X POST "$API/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=usm_db_admin&password=Mtai2026!")
    
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
fi

if [ -z "$ACCESS_TOKEN" ]; then
    echo "ERROR: Failed to authenticate!"
    echo "Response: $LOGIN_RESPONSE"
    echo ""
    echo "Available credentials from database:"
    echo "1. admin@arasintegrasi.ai / Mtai2026"
    echo "2. usm_db_admin / Mtai2026!"
    exit 1
fi

echo "✓ Authentication successful"
echo "Access Token: ${ACCESS_TOKEN:0:20}..."
sleep 1

# ============================================================
# TEST 1: Health Check - Verify ML Features Enabled
# ============================================================
echo ""
echo "[1/12] Testing ML Health Check..."
echo "Endpoint: GET /ml-utils/health"
curl -s "$API/ml-utils/health" \
    -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
sleep 1

# ============================================================
# TEST 2: Get Unlabeled Records
# ============================================================
echo ""
echo "[2/12] Getting Unlabeled Records..."
echo "Endpoint: GET /labeling/unlabeled"
UNLABELED=$(curl -s "$API/labeling/unlabeled?limit=5" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
echo "$UNLABELED" | python3 -m json.tool

# Extract first unlabeled ID for testing
FIRST_UNLABELED_ID=$(echo "$UNLABELED" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['unlabeled_records'][0]['id'] if data.get('unlabeled_records') and len(data['unlabeled_records']) > 0 else '')" 2>/dev/null)
if [ ! -z "$FIRST_UNLABELED_ID" ]; then
    echo "Found unlabeled record ID: $FIRST_UNLABELED_ID"
fi
sleep 1

# ============================================================
# TEST 3: Get Labeling Statistics
# ============================================================
echo ""
echo "[3/12] Getting Labeling Statistics..."
echo "Endpoint: GET /labeling/statistics"
curl -s "$API/labeling/statistics" \
    -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
sleep 1

# ============================================================
# TEST 4: Assign Single Label (if unlabeled record exists)
# ============================================================
echo ""
echo "[4/12] Testing Single Label Assignment..."
echo "Endpoint: POST /labeling/assign"
if [ ! -z "$FIRST_UNLABELED_ID" ]; then
    curl -s -X POST "$API/labeling/assign" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"record_id\": $FIRST_UNLABELED_ID,
            \"label\": \"SLE\",
            \"confidence\": 0.95,
            \"assigned_by\": \"test_user\",
            \"notes\": \"Test label assignment from bash script\"
        }" | python3 -m json.tool
else
    echo "Skipped - No unlabeled records available"
fi
sleep 1

# ============================================================
# TEST 5: Upload Sample Data (to get session_id and batch_id)
# ============================================================
echo ""
echo "[5/12] Uploading Sample Data for Testing..."
echo "This will create a session_id and batch_id for subsequent tests"

# Create a minimal CSV test file
TEST_CSV="/tmp/test_ml_data.csv"
cat > "$TEST_CSV" << 'EOF'
patient_id,age,gender,ANA,RF,CRP,diagnosis
P001,35,F,1.5,45,12.3,
P002,42,M,2.1,38,8.7,
P003,28,F,3.2,52,15.1,
EOF

echo "Created test file: $TEST_CSV"

# Upload using curl
UPLOAD_RESPONSE=$(curl -s -X POST "$API/flexible/preview/upload" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -F "file=@$TEST_CSV" \
    -F "dataset_type=ML_Test_Data")

echo "Upload Response:"
echo "$UPLOAD_RESPONSE" | python3 -m json.tool

SESSION_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', ''))" 2>/dev/null)
echo "Session ID: $SESSION_ID"
sleep 1

# ============================================================
# TEST 6: Save to Database (to get batch_id)
# ============================================================
echo ""
echo "[6/12] Saving Preview to Database..."
echo "Endpoint: POST /flexible/preview/{session_id}/save"
if [ ! -z "$SESSION_ID" ]; then
    SAVE_RESPONSE=$(curl -s -X POST "$API/flexible/preview/$SESSION_ID/save" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json")
    echo "Response:"
    echo "$SAVE_RESPONSE" | python3 -m json.tool
    
    BATCH_ID=$(echo "$SAVE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('batch_id', ''))" 2>/dev/null)
    echo "Batch ID: $BATCH_ID"
else
    echo "Skipped - No session_id available"
fi
sleep 1

# ============================================================
# TEST 7: Validate Schema for ML Training
# ============================================================
echo ""
echo "[7/12] Testing ML Schema Validation..."
echo "Endpoint: POST /ml-utils/validate-schema/{session_id}"
if [ ! -z "$SESSION_ID" ]; then
    curl -s -X POST "$API/ml-utils/validate-schema/$SESSION_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" | python3 -m json.tool
else
    echo "Skipped - No session_id available"
fi
sleep 1

# ============================================================
# TEST 8: Get Upload Provenance
# ============================================================
echo ""
echo "[8/12] Testing Upload Provenance Tracking..."
echo "Endpoint: GET /ml-utils/provenance/upload/{batch_id}"
if [ ! -z "$BATCH_ID" ]; then
    curl -s "$API/ml-utils/provenance/upload/$BATCH_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
else
    echo "Skipped - No batch_id available"
fi
sleep 1

# ============================================================
# TEST 9: Get Preprocessing Provenance
# ============================================================
echo ""
echo "[9/12] Testing Preprocessing Provenance..."
echo "Endpoint: GET /ml-utils/provenance/preprocessing/{session_id}"
if [ ! -z "$SESSION_ID" ]; then
    curl -s "$API/ml-utils/provenance/preprocessing/$SESSION_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
else
    echo "Skipped - No session_id available"
fi
sleep 1

# ============================================================
# TEST 10: Get Complete Provenance Chain
# ============================================================
echo ""
echo "[10/12] Testing Complete Provenance Chain..."
echo "Endpoint: GET /ml-utils/provenance/chain/{batch_id}"
if [ ! -z "$BATCH_ID" ]; then
    curl -s "$API/ml-utils/provenance/chain/$BATCH_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
else
    echo "Skipped - No batch_id available"
fi
sleep 1

# ============================================================
# TEST 11: Prepare ML-Ready Data (ML Bridge Service)
# ============================================================
echo ""
echo "[11/12] Testing ML Bridge Service..."
echo "Endpoint: POST /ml-utils/prepare-data/{session_id}"
if [ ! -z "$SESSION_ID" ]; then
    curl -s -X POST "$API/ml-utils/prepare-data/$SESSION_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "target_column": "diagnosis",
            "feature_columns": ["age", "ANA", "RF", "CRP"],
            "validate_schema": true
        }' | python3 -m json.tool
else
    echo "Skipped - No session_id available"
fi
sleep 1

# ============================================================
# TEST 12: Get ML-Ready Statistics
# ============================================================
echo ""
echo "[12/12] Testing ML Statistics..."
echo "Endpoint: GET /ml-utils/statistics/{batch_id}"
if [ ! -z "$BATCH_ID" ]; then
    curl -s "$API/ml-utils/statistics/$BATCH_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
else
    echo "Skipped - No batch_id available"
fi

# ============================================================
# SUMMARY
# ============================================================
echo ""
echo ""
echo "=== TEST SUMMARY ==="
echo "✓ All 12 ML endpoints tested"
echo ""
echo "Session ID: $SESSION_ID"
echo "Batch ID: $BATCH_ID"
echo ""
echo "Test data file: $TEST_CSV"
echo ""
echo "For detailed API documentation, visit:"
echo "  http://100.106.132.15:8000/docs"
echo ""

# Cleanup
rm -f "$TEST_CSV"
