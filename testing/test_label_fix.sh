#!/bin/bash
# Test Label Persistence Fix
API="http://100.106.132.15:8001/api/v1"
BATCH_ID="05665dc5-624c-4480-9f5f-3781f3ba27fb"

echo "=== TESTING LABEL PERSISTENCE FIX ==="
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
echo "✓ Token obtained"
echo ""

# Check initial state
echo "[1/4] Initial Label Count"
INITIAL=$(curl -s "$API/labeling/statistics" \
    -H "Authorization: Bearer $TOKEN" | grep -o '"labeled_count":[0-9]*' | cut -d':' -f2)
echo "Labeled records: $INITIAL"
echo ""

# Get unlabeled records
echo "[2/4] Get Unlabeled Records"
UNLABELED=$(curl -s "$API/labeling/unlabeled?limit=100" \
    -H "Authorization: Bearer $TOKEN")
UNLABELED_COUNT=$(echo "$UNLABELED" | grep -o '"total_unlabeled":[0-9]*' | cut -d':' -f2)
echo "Unlabeled records: $UNLABELED_COUNT"
echo ""

# Assign labels to batch
echo "[3/4] Batch Assign Labels (SLE)"
ASSIGN_RESPONSE=$(curl -s -X POST "$API/labeling/batch-assign?target_column=labels_disease_classification" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"batch_id\": \"$BATCH_ID\",
        \"label\": \"SLE\",
        \"confidence\": 1.0
    }")
echo "$ASSIGN_RESPONSE" | python3 -m json.tool
echo ""

# Verify labels persisted
echo "[4/4] Verify Labels Persisted"
sleep 2
FINAL=$(curl -s "$API/labeling/statistics" \
    -H "Authorization: Bearer $TOKEN")
echo "$FINAL" | python3 -m json.tool
echo ""

# Extract counts
FINAL_LABELED=$(echo "$FINAL" | grep -o '"labeled_count":[0-9]*' | cut -d':' -f2)
FINAL_UNLABELED=$(echo "$FINAL" | grep -o '"unlabeled_count":[0-9]*' | cut -d':' -f2)

echo "=== RESULTS ==="
echo "Before: $INITIAL labeled"
echo "After:  $FINAL_LABELED labeled"
echo "Unlabeled: $FINAL_UNLABELED"
echo ""

if [ "$FINAL_LABELED" -gt "$INITIAL" ]; then
    echo "✓ SUCCESS! Labels persisted to database!"
    echo "✓ flag_modified() fix is working!"
else
    echo "✗ FAILED - Labels still not persisting"
    echo "  Check if labeling.py was transferred and Docker rebuilt"
fi
