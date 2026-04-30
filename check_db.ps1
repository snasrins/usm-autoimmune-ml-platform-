# Check PostgreSQL database for patient data
# Run this with: .\check_db.ps1

Write-Host "Connecting to database on remote server..." -ForegroundColor Cyan

# Check if we can reach the server
if (Test-Connection -ComputerName 100.106.132.15 -Count 1 -Quiet) {
    Write-Host "✓ Server reachable" -ForegroundColor Green
    
    # Create SQL query
    $query = "SELECT id, anonymous_id, additional_data->>'original_patient_id' as hospital_id, age, gender, import_batch_id, created_at FROM patients ORDER BY created_at DESC LIMIT 20;"
    
    Write-Host "`nTo check the database, run this on the SERVER:" -ForegroundColor Yellow
    Write-Host "docker exec -it usm-autoimmune-postgres psql -U usm_admin -d autoimmune_db -c `"$query`"" -ForegroundColor White
    Write-Host "`nOr use PgAdmin at: http://100.106.132.15:5050" -ForegroundColor Cyan
} else {
    Write-Host "✗ Cannot reach server at 100.106.132.15" -ForegroundColor Red
}
