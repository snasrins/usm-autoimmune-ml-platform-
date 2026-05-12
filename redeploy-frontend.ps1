# Force rebuild frontend on RTX6000
# Run this script from your local machine

$server = "100.122.108.118"
$username = "mtuser1"
$password = "mezPez19!@"

Write-Host "🔄 Connecting to RTX6000 and rebuilding frontend..." -ForegroundColor Cyan

# Create the rebuild commands
$commands = @"
cd usm-autoimmune-ml-platform
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker rmi usm-autoimmune-ml-platform-frontend 2>/dev/null || true
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache nginx  
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose ps
"@

# Connect via SSH and run commands
$sshCommand = "echo $password | ssh $username@$server '$commands'"

Write-Host "Executing rebuild on RTX6000..." -ForegroundColor Yellow
ssh $username@$server $commands

Write-Host ""
Write-Host "✅ Frontend rebuild complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Open browser to: http://100.122.108.118:8080"
Write-Host "2. Hard refresh browser: Ctrl+Shift+R"
Write-Host "3. Check if System section is gone from sidebar"
Write-Host "4. Verify all pages have the new header with search/bell/profile"
