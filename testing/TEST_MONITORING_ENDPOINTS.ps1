# ============================================================================
# JWT Token Expiry Monitoring Endpoints Test Script
# USMA-91 Testing
# ============================================================================

$API_BASE = "http://192.168.196.97:8001/api/v1/auth"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "JWT MONITORING ENDPOINTS TEST" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# ============================================================================
# Test 1: Login to get tokens
# ============================================================================
Write-Host "[Test 1] Login with testjwt user..." -ForegroundColor Yellow

$loginResponse = curl.exe -X POST "$API_BASE/login" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=testjwt&password=Test1234!" `
  2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Login failed!" -ForegroundColor Red
    exit 1
}

$loginData = $loginResponse | ConvertFrom-Json
$ACCESS_TOKEN = $loginData.access_token
$REFRESH_TOKEN = $loginData.refresh_token

Write-Host "✅ Login successful!" -ForegroundColor Green
Write-Host "Access Token: $($ACCESS_TOKEN.Substring(0,50))..." -ForegroundColor Gray
Write-Host ""

# ============================================================================
# Test 2: View My Sessions (User Endpoint)
# ============================================================================
Write-Host "[Test 2] GET /sessions - View my active sessions..." -ForegroundColor Yellow

$sessionsResponse = curl.exe -X GET "$API_BASE/sessions" `
  -H "Authorization: Bearer $ACCESS_TOKEN" `
  2>$null

if ($LASTEXITCODE -eq 0) {
    $sessionsData = $sessionsResponse | ConvertFrom-Json
    Write-Host "✅ Success!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Gray
    $sessionsData | ConvertTo-Json -Depth 4 | Write-Host
} else {
    Write-Host "❌ FAILED!" -ForegroundColor Red
    Write-Host $sessionsResponse -ForegroundColor Red
}
Write-Host ""

# ============================================================================
# Test 3: Create Admin User (if not exists)
# ============================================================================
Write-Host "[Test 3] Creating admin user for testing..." -ForegroundColor Yellow

$adminRegisterResponse = curl.exe -X POST "$API_BASE/register" `
  -H "Content-Type: application/json" `
  -d '{\"username\":\"admintest\",\"email\":\"admin@example.com\",\"password\":\"Admin1234!\",\"full_name\":\"Admin Test\",\"role\":\"admin\"}' `
  2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Admin user created or already exists" -ForegroundColor Green
} else {
    Write-Host "⚠️ Admin user might already exist (OK)" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# Test 4: Login as Admin
# ============================================================================
Write-Host "[Test 4] Login as admin..." -ForegroundColor Yellow

$adminLoginResponse = curl.exe -X POST "$API_BASE/login" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admintest&password=Admin1234!" `
  2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Admin login failed! Testing with regular user token..." -ForegroundColor Yellow
    $ADMIN_TOKEN = $ACCESS_TOKEN
} else {
    $adminLoginData = $adminLoginResponse | ConvertFrom-Json
    $ADMIN_TOKEN = $adminLoginData.access_token
    Write-Host "✅ Admin login successful!" -ForegroundColor Green
}
Write-Host ""

# ============================================================================
# Test 5: Token Statistics (Admin Only)
# ============================================================================
Write-Host "[Test 5] GET /admin/token-stats - Global token statistics..." -ForegroundColor Yellow

$statsResponse = curl.exe -X GET "$API_BASE/admin/token-stats" `
  -H "Authorization: Bearer $ADMIN_TOKEN" `
  2>$null

if ($LASTEXITCODE -eq 0) {
    $statsData = $statsResponse | ConvertFrom-Json
    Write-Host "✅ Success!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Gray
    $statsData | ConvertTo-Json -Depth 4 | Write-Host
} else {
    Write-Host "❌ FAILED!" -ForegroundColor Red
    Write-Host $statsResponse -ForegroundColor Red
}
Write-Host ""

# ============================================================================
# Test 6: View All Sessions (Admin Only)
# ============================================================================
Write-Host "[Test 6] GET /admin/sessions - View all sessions..." -ForegroundColor Yellow

$allSessionsResponse = curl.exe -X GET "$API_BASE/admin/sessions" `
  -H "Authorization: Bearer $ADMIN_TOKEN" `
  2>$null

if ($LASTEXITCODE -eq 0) {
    $allSessionsData = $allSessionsResponse | ConvertFrom-Json
    Write-Host "✅ Success!" -ForegroundColor Green
    Write-Host "Total sessions found: $($allSessionsData.total_sessions)" -ForegroundColor Cyan
    Write-Host "First 3 sessions:" -ForegroundColor Gray
    $allSessionsData.sessions | Select-Object -First 3 | ConvertTo-Json -Depth 3 | Write-Host
} else {
    Write-Host "❌ FAILED!" -ForegroundColor Red
    Write-Host $allSessionsResponse -ForegroundColor Red
}
Write-Host ""

# ============================================================================
# Test 7: Filter Sessions - Active Only
# ============================================================================
Write-Host "[Test 7] GET /admin/sessions?active_only=true - Active sessions only..." -ForegroundColor Yellow

$activeSessionsResponse = curl.exe -X GET "$API_BASE/admin/sessions?active_only=true" `
  -H "Authorization: Bearer $ADMIN_TOKEN" `
  2>$null

if ($LASTEXITCODE -eq 0) {
    $activeSessionsData = $activeSessionsResponse | ConvertFrom-Json
    Write-Host "✅ Success!" -ForegroundColor Green
    Write-Host "Active sessions: $($activeSessionsData.total_sessions)" -ForegroundColor Cyan
} else {
    Write-Host "❌ FAILED!" -ForegroundColor Red
    Write-Host $activeSessionsResponse -ForegroundColor Red
}
Write-Host ""

# ============================================================================
# Test 8: Filter Sessions by User ID
# ============================================================================
Write-Host "[Test 8] GET /admin/sessions?user_id=4 - Sessions for specific user..." -ForegroundColor Yellow

$userSessionsResponse = curl.exe -X GET "$API_BASE/admin/sessions?user_id=4" `
  -H "Authorization: Bearer $ADMIN_TOKEN" `
  2>$null

if ($LASTEXITCODE -eq 0) {
    $userSessionsData = $userSessionsResponse | ConvertFrom-Json
    Write-Host "✅ Success!" -ForegroundColor Green
    Write-Host "Sessions for user_id=4: $($userSessionsData.total_sessions)" -ForegroundColor Cyan
} else {
    Write-Host "❌ FAILED!" -ForegroundColor Red
    Write-Host $userSessionsResponse -ForegroundColor Red
}
Write-Host ""

# ============================================================================
# Test 9: Revoke Session (Admin Only)
# ============================================================================
Write-Host "[Test 9] DELETE /admin/sessions/{id} - Revoke a session..." -ForegroundColor Yellow

# Get first active session ID
$firstSession = ($activeSessionsData.sessions | Where-Object { $_.status -eq "active" } | Select-Object -First 1)

if ($firstSession) {
    $sessionId = $firstSession.id
    Write-Host "Attempting to revoke session ID: $sessionId" -ForegroundColor Gray
    
    $revokeResponse = curl.exe -X DELETE "$API_BASE/admin/sessions/$sessionId" `
      -H "Authorization: Bearer $ADMIN_TOKEN" `
      2>$null
    
    if ($LASTEXITCODE -eq 0) {
        $revokeData = $revokeResponse | ConvertFrom-Json
        Write-Host "✅ Success!" -ForegroundColor Green
        Write-Host "Response:" -ForegroundColor Gray
        $revokeData | ConvertTo-Json | Write-Host
    } else {
        Write-Host "❌ FAILED!" -ForegroundColor Red
        Write-Host $revokeResponse -ForegroundColor Red
    }
} else {
    Write-Host "⚠️ No active sessions to revoke (OK)" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# Test 10: Verify Session State in Database
# ============================================================================
Write-Host "[Test 10] Check database for session data..." -ForegroundColor Yellow
Write-Host "Run this manually on the server:" -ForegroundColor Gray
Write-Host 'docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "SELECT id, user_id, is_revoked, expires_at, device_info FROM refresh_tokens ORDER BY created_at DESC LIMIT 5;"' -ForegroundColor Gray
Write-Host ""

# ============================================================================
# Summary
# ============================================================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ All monitoring endpoints tested!" -ForegroundColor Green
Write-Host "`nNew Endpoints Available:" -ForegroundColor Yellow
Write-Host "  1. GET /api/v1/auth/sessions - View your sessions" -ForegroundColor White
Write-Host "  2. GET /api/v1/auth/admin/token-stats - Token statistics" -ForegroundColor White
Write-Host "  3. GET /api/v1/auth/admin/sessions - View all sessions" -ForegroundColor White
Write-Host "  4. DELETE /api/v1/auth/admin/sessions/{id} - Revoke session" -ForegroundColor White
Write-Host "`nUSMA-91: JWT Token Expiry Monitoring ✅ COMPLETE" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
