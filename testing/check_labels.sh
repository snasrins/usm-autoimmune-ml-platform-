#!/bin/bash
# Quick database check script
API="http://100.106.132.15:8001/api/v1"
BATCH_ID="05665dc5-624c-4480-9f5f-3781f3ba27fb"

echo "=== CHECKING LABEL STATUS ==="
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

# Check labeling statistics
echo "[1/3] Current Labeling Statistics"
curl -s "$API/labeling/statistics" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Get a few labeled records to see the actual data
echo "[2/3] Sample Labeled Records (if any)"
curl -s "$API/labeling/unlabeled?limit=3&include_labeled=true" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -50
echo ""

# Try to get batch records
echo "[3/3] Batch Records Check"
curl -s "$API/labeling/statistics?batch_id=$BATCH_ID" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "=== ANALYSIS COMPLETE ==="
echo "If all records show '0 labeled', the labels may not have been saved to the database."
echo "Check if labels_disease_classification column exists and has values."
