# Quick Health Check - Sign Up Flow Verification
# Run this before testing to ensure all components are connected
Write-Host "🔍 USM Autoimmune ML Platform - Connection Health Check" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host ""

# Test 1: Backend API Health
Write-Host "[1/5] Testing Backend API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://192.168.196.97:8001/docs" -Method GET -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend API is UP (192.168.196.97:8001)" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Backend API is DOWN or unreachable" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Check if FastAPI container is running
Write-Host "[2/5] Checking FastAPI Container (via SSH)..." -ForegroundColor Yellow
Write-Host "   (This checks if Docker container is running on server)" -ForegroundColor Gray
try {
    $containerCheck = ssh shaggy@192.168.196.97 "docker ps | grep fastapi" 2>&1
    if ($containerCheck -match "fastapi") {
        Write-Host "✅ FastAPI container is running" -ForegroundColor Green
    } else {
        Write-Host "⚠️  FastAPI container not found (may need to start it)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not check container status (SSH may not be configured)" -ForegroundColor Yellow
}
Write-Host ""

# Test 3: Test Register Endpoint Directly
Write-Host "[3/5] Testing /auth/register endpoint..." -ForegroundColor Yellow
try {
    $testUser = @{
        username = "healthcheck_$(Get-Random -Maximum 9999)"
        email = "healthcheck_$(Get-Random -Maximum 9999)@test.com"
        password = "HealthCheck2026!"
        full_name = "Health Check User"
    } | ConvertTo-Json

    $headers = @{
        "Content-Type" = "application/json"
    }

    $response = Invoke-RestMethod -Uri "http://192.168.196.97:8001/api/v1/auth/register" `
                                   -Method POST `
                                   -Body $testUser `
                                   -Headers $headers `
                                   -TimeoutSec 10

    Write-Host "✅ Register endpoint is working!" -ForegroundColor Green
    Write-Host "   Created test user: $($response.username) (id: $($response.id))" -ForegroundColor Gray
    
    # Clean up test user
    Write-Host "   Cleaning up test user..." -ForegroundColor Gray
    ssh shaggy@192.168.196.97 "docker exec -it usm-autoimmune-postgres psql -U shaggy -d usm_autoimmune_ml -c ""DELETE FROM users WHERE username='$($response.username)';""" | Out-Null
    
} catch {
    if ($_.Exception.Message -match "400") {
        Write-Host "⚠️  Endpoint responded but returned 400 (may be duplicate test user)" -ForegroundColor Yellow
        Write-Host "   This is OK - endpoint is reachable" -ForegroundColor Gray
    } else {
        Write-Host "❌ Register endpoint failed" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}
Write-Host ""

# Test 4: Check PostgreSQL Database
Write-Host "[4/5] Checking PostgreSQL Database..." -ForegroundColor Yellow
try {
    $dbCheck = ssh shaggy@192.168.196.97 "docker exec -it usm-autoimmune-postgres psql -U shaggy -d usm_autoimmune_ml -c 'SELECT COUNT(*) FROM users;' -t" 2>&1
    if ($dbCheck -match "\d+") {
        $userCount = ($dbCheck | Select-String -Pattern "\d+").Matches.Value
        Write-Host "✅ Database is accessible" -ForegroundColor Green
        Write-Host "   Current user count: $userCount" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️  Could not verify database (SSH required)" -ForegroundColor Yellow
}
Write-Host ""

# Test 5: Check Frontend Dev Server
Write-Host "[5/5] Checking Frontend Dev Server..." -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 5 -UseBasicParsing
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "✅ Frontend dev server is running (localhost:3000)" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Frontend not running - Start with: npm run dev" -ForegroundColor Yellow
    Write-Host "   Directory: C:\Users\Syarifah\usm-autoimmune-ml-platform\frontend" -ForegroundColor Gray
}
Write-Host ""

# Summary
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host "📊 SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host ""
Write-Host "Backend API:         http://192.168.196.97:8001" -ForegroundColor White
Write-Host "API Docs (Swagger):  http://192.168.196.97:8001/docs" -ForegroundColor White
Write-Host "Frontend:            http://localhost:3000" -ForegroundColor White
Write-Host "Database:            postgres://192.168.196.97:5433/usm_autoimmune_ml" -ForegroundColor White
Write-Host ""
Write-Host "Ready to test? Try these URLs:" -ForegroundColor Cyan
Write-Host "  • Sign Up:  http://localhost:3000/signup" -ForegroundColor White
Write-Host "  • Login:    http://localhost:3000/login" -ForegroundColor White
Write-Host ""

# Show quick test command
Write-Host "Quick Test Command (manual curl):" -ForegroundColor Cyan
Write-Host 'curl -X POST "http://192.168.196.97:8001/api/v1/auth/register" `' -ForegroundColor Gray
Write-Host '  -H "Content-Type: application/json" `' -ForegroundColor Gray
Write-Host '  -d ''{"username":"manualtest","email":"manualtest@test.com","password":"Test1234!","full_name":"Manual Test"}''' -ForegroundColor Gray
Write-Host ""
