# MyAria-i Frontend Setup Script
# Run this script to set up and start the React frontend

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MyAria-i Frontend Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if Node.js is installed
Write-Host "[1/4] Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js $nodeVersion installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found!" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Navigate to frontend directory
Write-Host "`n[2/4] Navigating to frontend directory..." -ForegroundColor Yellow
Set-Location -Path "C:\Users\Syarifah\usm-autoimmune-ml-platform\frontend"
Write-Host "✅ Current directory: $PWD" -ForegroundColor Green

# Install dependencies
Write-Host "`n[3/4] Installing dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Start development server
Write-Host "`n[4/4] Starting development server..." -ForegroundColor Yellow
Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Gray

npm run dev
