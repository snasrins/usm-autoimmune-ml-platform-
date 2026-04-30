#!/bin/bash
# Test Dataset Versioning API - USMA-27
# Run this script on the server to validate all 7 endpoints

BASE_URL="http://100.106.132.15:8001"
API_PREFIX="/api/v1"

echo "=========================================="
echo "Dataset Versioning API Test Suite"
echo "=========================================="
echo ""

# Step 1: Get authentication token
echo "📝 Step 1: Authenticating..."
echo "Username: s.nasrin"
read -sp "Password: " PASSWORD
echo ""

TOKEN=$(curl -s -X POST "$BASE_URL$API_PREFIX/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=s.nasrin&password=$PASSWORD" | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Authentication failed! Check username/password"
  exit 1
fi

echo "✅ Authenticated successfully"
echo ""

# Step 2: Create first dataset version (v1.0.0)
echo "📊 Step 2: Creating initial dataset version (v1.0.0)..."
RESPONSE=$(curl -s -X POST "$BASE_URL$API_PREFIX/dataset-versions/versions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_name": "SLE_Patient_Registry_Test",
    "file_type": "CSV",
    "storage_path": "usm-processed/sle_registry_v1.csv",
    "file_size_bytes": 1048576,
    "row_count": 150,
    "column_count": 25,
    "bump_type": "major",
    "changelog": "Initial SLE patient registry dataset",
    "tags": ["initial", "baseline"]
  }')

DATASET_ID_1=$(echo $RESPONSE | jq -r '.dataset_id')
VERSION_1=$(echo $RESPONSE | jq -r '.semantic_version')

echo "Response:"
echo $RESPONSE | jq '.'
echo ""

if [ "$DATASET_ID_1" = "null" ]; then
  echo "❌ Failed to create dataset version"
  exit 1
fi

echo "✅ Created dataset: $DATASET_ID_1 (Version: $VERSION_1)"
echo ""

# Step 3: Create second version (v1.1.0 - minor bump)
echo "📊 Step 3: Creating v1.1.0 (minor bump - add biomarkers)..."
RESPONSE=$(curl -s -X POST "$BASE_URL$API_PREFIX/dataset-versions/versions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"dataset_name\": \"SLE_Patient_Registry_Test\",
    \"file_type\": \"CSV\",
    \"storage_path\": \"usm-processed/sle_registry_v1_1.csv\",
    \"file_size_bytes\": 1153434,
    \"row_count\": 150,
    \"column_count\": 30,
    \"parent_dataset_id\": \"$DATASET_ID_1\",
    \"bump_type\": \"minor\",
    \"changelog\": \"Added anti-dsDNA and complement biomarker columns\",
    \"tags\": [\"biomarkers\", \"stable\"]
  }")

DATASET_ID_2=$(echo $RESPONSE | jq -r '.dataset_id')
VERSION_2=$(echo $RESPONSE | jq -r '.semantic_version')

echo "Response:"
echo $RESPONSE | jq '.'
echo ""
echo "✅ Created version: $VERSION_2 (Parent: $DATASET_ID_1)"
echo ""

# Step 4: List all versions
echo "📋 Step 4: Listing all versions of SLE_Patient_Registry_Test..."
curl -s "$BASE_URL$API_PREFIX/dataset-versions/datasets/SLE_Patient_Registry_Test/versions" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# Step 5: Promote v1.1.0 to production
echo "🚀 Step 5: Promoting $VERSION_2 to production..."
curl -s -X POST "$BASE_URL$API_PREFIX/dataset-versions/datasets/$DATASET_ID_2/promote" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Validated by clinician, biomarkers approved for ML training"
  }' | jq '.'
echo ""

# Step 6: Add additional tags
echo "🏷️  Step 6: Adding tags to $VERSION_2..."
curl -s -X POST "$BASE_URL$API_PREFIX/dataset-versions/datasets/$DATASET_ID_2/tag?tags=validated&tags=ml-ready" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# Step 7: View version lineage (tree)
echo "🌳 Step 7: Viewing version lineage..."
curl -s "$BASE_URL$API_PREFIX/dataset-versions/datasets/$DATASET_ID_2/lineage" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# Step 8: List production datasets
echo "⭐ Step 8: Listing all production datasets..."
curl -s "$BASE_URL$API_PREFIX/dataset-versions/production" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# Step 9: Create patch version (v1.1.1)
echo "🔧 Step 9: Creating v1.1.1 (patch - data quality fix)..."
RESPONSE=$(curl -s -X POST "$BASE_URL$API_PREFIX/dataset-versions/versions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"dataset_name\": \"SLE_Patient_Registry_Test\",
    \"file_type\": \"CSV\",
    \"storage_path\": \"usm-processed/sle_registry_v1_1_1.csv\",
    \"file_size_bytes\": 1153500,
    \"row_count\": 150,
    \"column_count\": 30,
    \"parent_dataset_id\": \"$DATASET_ID_2\",
    \"bump_type\": \"patch\",
    \"changelog\": \"Fixed missing values in complement C3 column\",
    \"tags\": [\"bugfix\"]
  }")

DATASET_ID_3=$(echo $RESPONSE | jq -r '.dataset_id')
VERSION_3=$(echo $RESPONSE | jq -r '.semantic_version')

echo "Response:"
echo $RESPONSE | jq '.'
echo ""
echo "✅ Created version: $VERSION_3 (Parent: $DATASET_ID_2)"
echo ""

# Step 10: View final lineage
echo "🌳 Step 10: Viewing final version lineage tree..."
curl -s "$BASE_URL$API_PREFIX/dataset-versions/datasets/$DATASET_ID_3/lineage" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

echo "=========================================="
echo "✅ All Tests Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  • Created 3 versions: $VERSION_1 → $VERSION_2 → $VERSION_3"
echo "  • Production version: $VERSION_2"
echo "  • Dataset IDs:"
echo "    - v1.0.0: $DATASET_ID_1"
echo "    - v1.1.0: $DATASET_ID_2 (PRODUCTION)"
echo "    - v1.1.1: $DATASET_ID_3"
echo ""
echo "Next steps:"
echo "  1. View Swagger docs: http://100.106.132.15:8001/docs"
echo "  2. Check dataset lineage in database"
echo "  3. Test with real datasets"
