# ============================================
# SHOW AND CREATE SIT TEST USERS
# ============================================

Write-Host "=== Showing and Creating SIT Test Users ===" -ForegroundColor Cyan

# Upload SQL file to server
Write-Host "`n1. Uploading SQL file to server..." -ForegroundColor Yellow
scp show_and_create_users.sql root@100.106.132.15:/tmp/

# Execute SQL file
Write-Host "`n2. Executing SQL to show and create users..." -ForegroundColor Yellow
ssh root@100.106.132.15 @"
docker cp /tmp/show_and_create_users.sql usm-autoimmune-postgres:/tmp/
docker exec -e PGPASSWORD=Mtai2026! usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry -f /tmp/show_and_create_users.sql
"@

Write-Host "`n=== DONE! ===" -ForegroundColor Green
Write-Host "`nSIT Test Users Available:" -ForegroundColor Cyan
Write-Host "  1. ADMIN     : s.nasrin / USM@22" -ForegroundColor White
Write-Host "  2. RESEARCHER: researcher1 / test123" -ForegroundColor White
Write-Host "  3. VIEWER    : viewer1 / test123" -ForegroundColor White
