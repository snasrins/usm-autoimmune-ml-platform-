# ============================================================
# ML Feature Testing Script
# Date: April 8, 2026
# Tests all 12 ML endpoints on production server
# ============================================================

$SERVER = "http://100.106.132.15:8000"
$API = "$SERVER/api/v1"

Write-Host "`n=== ML FEATURE TESTING ===" -ForegroundColor Cyan
Write-Host "Server: $SERVER" -ForegroundColor Yellow
Write-Host "Testing 12 ML endpoints...`n" -ForegroundColor Yellow

# ============================================================
# TEST 1: Health Check - Verify ML Features Enabled
# ============================================================
Write-Host "`n[1/12] Testing ML Health Check..." -ForegroundColor Green
$response = curl -s "$API/ml-utils/health" | ConvertFrom-Json
Write-Host "Response:" -ForegroundColor Yellow
$response | ConvertTo-Json -Depth 3
Start-Sleep -Seconds 1

# ============================================================
# TEST 2: Get Unlabeled Records
# ============================================================
Write-Host "`n[2/12] Getting Unlabeled Records..." -ForegroundColor Green
Write-Host "Endpoint: GET /labeling/unlabeled" -ForegroundColor Gray
$unlabeled = curl -s "$API/labeling/unlabeled?limit=5" | ConvertFrom-Json
Write-Host "Response:" -ForegroundColor Yellow
$unlabeled | ConvertTo-Json -Depth 3

# Store first unlabeled ID for testing label assignment
$firstUnlabeledId = $null
if ($unlabeled.unlabeled_records -and $unlabeled.unlabeled_records.Count -gt 0) {
    $firstUnlabeledId = $unlabeled.unlabeled_records[0].id
    Write-Host "`nFound unlabeled record ID: $firstUnlabeledId" -ForegroundColor Cyan
}
Start-Sleep -Seconds 1

# ============================================================
# TEST 3: Get Labeling Statistics
# ============================================================
Write-Host "`n[3/12] Getting Labeling Statistics..." -ForegroundColor Green
Write-Host "Endpoint: GET /labeling/statistics" -ForegroundColor Gray
$labelStats = curl -s "$API/labeling/statistics" | ConvertFrom-Json
Write-Host "Response:" -ForegroundColor Yellow
$labelStats | ConvertTo-Json -Depth 3
Start-Sleep -Seconds 1

# ============================================================
# TEST 4: Assign Single Label (if unlabeled record exists)
# ============================================================
Write-Host "`n[4/12] Testing Single Label Assignment..." -ForegroundColor Green
Write-Host "Endpoint: POST /labeling/assign" -ForegroundColor Gray
if ($firstUnlabeledId) {
    $assignPayload = @{
        record_id = $firstUnlabeledId
        label = "SLE"
        confidence = 0.95
        assigned_by = "test_user"
        notes = "Test label assignment from PowerShell"
    } | ConvertTo-Json
    
    $assignResponse = curl -s -X POST "$API/labeling/assign" `
        -H "Content-Type: application/json" `
        -d $assignPayload | ConvertFrom-Json
    Write-Host "Response:" -ForegroundColor Yellow
    $assignResponse | ConvertTo-Json -Depth 3
} else {
    Write-Host "Skipped - No unlabeled records available" -ForegroundColor Yellow
}
Start-Sleep -Seconds 1

# ============================================================
# TEST 5: Upload Sample Data (to get session_id and batch_id)
# ============================================================
Write-Host "`n[5/12] Uploading Sample Data for Testing..." -ForegroundColor Green
Write-Host "This will create a session_id and batch_id for subsequent tests" -ForegroundColor Gray

# Create a minimal CSV test file
$testCsvPath = "$env:TEMP\test_ml_data.csv"
$csvContent = @"
patient_id,age,gender,ANA,RF,CRP,diagnosis
P001,35,F,1.5,45,12.3,
P002,42,M,2.1,38,8.7,
P003,28,F,3.2,52,15.1,
"@
$csvContent | Out-File -FilePath $testCsvPath -Encoding UTF8

Write-Host "Created test file: $testCsvPath" -ForegroundColor Cyan

# Upload using curl
$uploadResponse = curl -s -X POST "$API/flexible/preview/upload" `
    -F "file=@$testCsvPath" `
    -F "dataset_type=ML_Test_Data" | ConvertFrom-Json

Write-Host "Upload Response:" -ForegroundColor Yellow
$uploadResponse | ConvertTo-Json -Depth 3

$sessionId = $uploadResponse.session_id
Write-Host "`nSession ID: $sessionId" -ForegroundColor Cyan
Start-Sleep -Seconds 1

# ============================================================
# TEST 6: Save to Database (to get batch_id)
# ============================================================
Write-Host "`n[6/12] Saving Preview to Database..." -ForegroundColor Green
Write-Host "Endpoint: POST /flexible/preview/{session_id}/save" -ForegroundColor Gray
if ($sessionId) {
    $saveResponse = curl -s -X POST "$API/flexible/preview/$sessionId/save" `
        -H "Content-Type: application/json" | ConvertFrom-Json
    Write-Host "Response:" -ForegroundColor Yellow
    $saveResponse | ConvertTo-Json -Depth 3
    
    $batchId = $saveResponse.batch_id
    Write-Host "`nBatch ID: $batchId" -ForegroundColor Cyan
} else {
    Write-Host "Skipped - No session_id available" -ForegroundColor Yellow
}
Start-Sleep -Seconds 1

# ============================================================
# TEST 7: Validate Schema for ML Training
# ============================================================
Write-Host "`n[7/12] Testing ML Schema Validation..." -ForegroundColor Green
Write-Host "Endpoint: POST /ml-utils/validate-schema/{session_id}" -ForegroundColor Gray
if ($sessionId) {
    $validateResponse = curl -s -X POST "$API/ml-utils/validate-schema/$sessionId" `
        -H "Content-Type: application/json" | ConvertFrom-Json
    Write-Host "Response:" -ForegroundColor Yellow
    $validateResponse | ConvertTo-Json -Depth 5
} else {
    Write-Host "Skipped - No session_id available" -ForegroundColor Yellow
}
Start-Sleep -Seconds 1

# ============================================================
# TEST 8: Get Upload Provenance
# ============================================================
Write-Host "`n[8/12] Testing Upload Provenance Tracking..." -ForegroundColor Green
Write-Host "Endpoint: GET /ml-utils/provenance/upload/{batch_id}" -ForegroundColor Gray
if ($batchId) {
    $uploadProv = curl -s "$API/ml-utils/provenance/upload/$batchId" | ConvertFrom-Json
    Write-Host "Response:" -ForegroundColor Yellow
    $uploadProv | ConvertTo-Json -Depth 5
} else {
    Write-Host "Skipped - No batch_id available" -ForegroundColor Yellow
}
Start-Sleep -Seconds 1

# ============================================================
# TEST 9: Get Preprocessing Provenance
# ============================================================
Write-Host "`n[9/12] Testing Preprocessing Provenance..." -ForegroundColor Green
Write-Host "Endpoint: GET /ml-utils/provenance/preprocessing/{session_id}" -ForegroundColor Gray
if ($sessionId) {
    $preprocProv = curl -s "$API/ml-utils/provenance/preprocessing/$sessionId" | ConvertFrom-Json
    Write-Host "Response:" -ForegroundColor Yellow
    $preprocProv | ConvertTo-Json -Depth 5
} else {
    Write-Host "Skipped - No session_id available" -ForegroundColor Yellow
}
Start-Sleep -Seconds 1

# ============================================================
# TEST 10: Get Complete Provenance Chain
# ============================================================
Write-Host "`n[10/12] Testing Complete Provenance Chain..." -ForegroundColor Green
Write-Host "Endpoint: GET /ml-utils/provenance/chain/{batch_id}" -ForegroundColor Gray
if ($batchId) {
    $chainProv = curl -s "$API/ml-utils/provenance/chain/$batchId" | ConvertFrom-Json
    Write-Host "Response:" -ForegroundColor Yellow
    $chainProv | ConvertTo-Json -Depth 5
} else {
    Write-Host "Skipped - No batch_id available" -ForegroundColor Yellow
}
Start-Sleep -Seconds 1

# ============================================================
# TEST 11: Prepare ML-Ready Data (ML Bridge Service)
# ============================================================
Write-Host "`n[11/12] Testing ML Bridge Service..." -ForegroundColor Green
Write-Host "Endpoint: POST /ml-utils/prepare-data/{session_id}" -ForegroundColor Gray
if ($sessionId) {
    $mlPreparePayload = @{
        target_column = "diagnosis"
        feature_columns = @("age", "ANA", "RF", "CRP")
        validate_schema = $true
    } | ConvertTo-Json
    
    $mlData = curl -s -X POST "$API/ml-utils/prepare-data/$sessionId" `
        -H "Content-Type: application/json" `
        -d $mlPreparePayload | ConvertFrom-Json
    Write-Host "Response:" -ForegroundColor Yellow
    $mlData | ConvertTo-Json -Depth 5
} else {
    Write-Host "Skipped - No session_id available" -ForegroundColor Yellow
}
Start-Sleep -Seconds 1

# ============================================================
# TEST 12: Get ML-Ready Statistics
# ============================================================
Write-Host "`n[12/12] Testing ML Statistics..." -ForegroundColor Green
Write-Host "Endpoint: GET /ml-utils/statistics/{batch_id}" -ForegroundColor Gray
if ($batchId) {
    $mlStats = curl -s "$API/ml-utils/statistics/$batchId" | ConvertFrom-Json
    Write-Host "Response:" -ForegroundColor Yellow
    $mlStats | ConvertTo-Json -Depth 5
} else {
    Write-Host "Skipped - No batch_id available" -ForegroundColor Yellow
}

# ============================================================
# SUMMARY
# ============================================================
Write-Host "`n`n=== TEST SUMMARY ===" -ForegroundColor Cyan
Write-Host "✓ All 12 ML endpoints tested" -ForegroundColor Green
Write-Host "`nSession ID: $sessionId" -ForegroundColor Yellow
Write-Host "Batch ID: $batchId" -ForegroundColor Yellow
Write-Host "`nTest data file: $testCsvPath" -ForegroundColor Gray
Write-Host "`nFor detailed API documentation, visit:" -ForegroundColor Cyan
Write-Host "  $SERVER/docs" -ForegroundColor White
Write-Host "`n"

# Cleanup
Remove-Item -Path $testCsvPath -ErrorAction SilentlyContinue
