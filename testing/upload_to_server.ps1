# PowerShell script to upload optimized code to GPU server
# Run this from Windows PowerShell in the project directory

Write-Host "🚀 Uploading optimized files to gpulab1..." -ForegroundColor Cyan
Write-Host ""

# Upload main file
Write-Host "📤 Uploading standalone_unstructured_pipeline.py..." -ForegroundColor Yellow
scp standalone_unstructured_pipeline.py shaggy@gpulab1:~/usm-autoimmune-ml-platform/

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Upload successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Next steps:" -ForegroundColor Cyan
    Write-Host "   1. SSH into gpulab1:" -ForegroundColor White
    Write-Host "      ssh shaggy@gpulab1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   2. Navigate to project:" -ForegroundColor White
    Write-Host "      cd ~/usm-autoimmune-ml-platform" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   3. Activate virtual environment:" -ForegroundColor White
    Write-Host "      source venv_qwen3/bin/activate" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   4. Test optimized code:" -ForegroundColor White
    Write-Host "      python standalone_unstructured_pipeline.py 'Sample Medical Report.pdf'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🎯 Expected Results:" -ForegroundColor Cyan
    Write-Host "   ✅ See 'Processing 6 images in 2 batches of 4...'" -ForegroundColor Green
    Write-Host "   ✅ See 'Batch 1/2: Processing 4 pages...'" -ForegroundColor Green
    Write-Host "   ✅ Total time: ~90-120s (down from 376s)" -ForegroundColor Green
    Write-Host "   ✅ VRAM usage: 50-60% (up from 19%)" -ForegroundColor Green
} else {
    Write-Host "❌ Upload failed! Check SSH connection." -ForegroundColor Red
    Write-Host ""
    Write-Host "Debug steps:" -ForegroundColor Yellow
    Write-Host "   1. Test SSH connection: ssh shaggy@gpulab1" -ForegroundColor Gray
    Write-Host "   2. Check if SCP is available: where scp" -ForegroundColor Gray
    Write-Host "   3. Or use WinSCP/FileZilla to upload manually" -ForegroundColor Gray
}
