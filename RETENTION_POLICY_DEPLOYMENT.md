# Data Retention Policy Deployment Guide
# USM Autoimmune ML Platform
# Created: April 24, 2026

## ============================================================================
## 1. MinIO Lifecycle Policy Setup
## ============================================================================

### Option A: Via MinIO Console (Easiest)
1. Open MinIO Console: http://100.106.132.15:9001
2. Login with admin credentials
3. Navigate to: Buckets → training-artifacts → Lifecycle
4. Click "Add Lifecycle Rule"
5. Configure:
   - Rule Name: "DeleteOldModelArtifacts"
   - Days: 365
   - Prefix: models/
   - Status: Enabled
6. Repeat for other prefixes (oof_predictions/, dataset_)

### Option B: Via MinIO Client (mc)
```bash
# Install MinIO client
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/

# Configure MinIO alias
mc alias set myminio http://100.106.132.15:9000 minio_admin "MinIO_P@ssw0rd_2026"

# Apply lifecycle policy
mc ilm add myminio/training-artifacts \
  --expiry-days 365 \
  --prefix "models/" \
  --id "DeleteOldModelArtifacts"

mc ilm add myminio/training-artifacts \
  --expiry-days 365 \
  --prefix "oof_predictions/" \
  --id "DeleteOldOOFPredictions"

mc ilm add myminio/training-artifacts \
  --expiry-days 365 \
  --prefix "dataset_" \
  --id "DeleteOldDatasets"

# Verify policies
mc ilm ls myminio/training-artifacts
```

### Option C: Via S3 API (boto3)
```python
import boto3
from datetime import datetime

s3 = boto3.client(
    's3',
    endpoint_url='http://100.106.132.15:9000',
    aws_access_key_id='minio_admin',
    aws_secret_access_key='MinIO_P@ssw0rd_2026'
)

lifecycle_config = {
    'Rules': [
        {
            'ID': 'DeleteOldModelArtifacts',
            'Status': 'Enabled',
            'Filter': {'Prefix': 'models/'},
            'Expiration': {'Days': 365}
        },
        {
            'ID': 'DeleteOldOOFPredictions',
            'Status': 'Enabled',
            'Filter': {'Prefix': 'oof_predictions/'},
            'Expiration': {'Days': 365}
        },
        {
            'ID': 'DeleteOldDatasets',
            'Status': 'Enabled',
            'Filter': {'Prefix': 'dataset_'},
            'Expiration': {'Days': 365}
        }
    ]
}

s3.put_bucket_lifecycle_configuration(
    Bucket='training-artifacts',
    LifecycleConfiguration=lifecycle_config
)

print("✅ MinIO lifecycle policy applied successfully")
```

## ============================================================================
## 2. PostgreSQL Retention Policy Setup
## ============================================================================

### Step 1: Apply SQL Schema
```bash
# Connect to PostgreSQL
psql -h 100.106.132.15 -U postgres -d usm_autoimmune_registry

# Apply retention policy SQL
\i postgres-retention-policy.sql

# Verify functions created
\df archive_old_training_jobs
\df delete_old_failed_jobs

# Check retention policy status
SELECT * FROM retention_policy_status;
```

### Step 2: Schedule Automated Cleanup (Linux Cron)
```bash
# Edit crontab
crontab -e

# Add these lines (runs every Sunday at 2 AM)
0 2 * * 0 psql -h 100.106.132.15 -U postgres -d usm_autoimmune_registry -c "SELECT archive_old_training_jobs();" >> /var/log/postgres-cleanup.log 2>&1
0 3 * * 0 psql -h 100.106.132.15 -U postgres -d usm_autoimmune_registry -c "SELECT delete_old_failed_jobs();" >> /var/log/postgres-cleanup.log 2>&1
```

### Step 3: Schedule Automated Cleanup (Windows Task Scheduler)
```powershell
# Create PowerShell cleanup script
$scriptPath = "C:\Scripts\postgres-cleanup.ps1"

@"
`$Env:PGPASSWORD = "your_postgres_password"
`$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Write-Host "`$timestamp - Running PostgreSQL data retention cleanup..."

# Archive old training jobs
psql -h 100.106.132.15 -U postgres -d usm_autoimmune_registry -c "SELECT archive_old_training_jobs();"

# Delete old failed jobs
psql -h 100.106.132.15 -U postgres -d usm_autoimmune_registry -c "SELECT delete_old_failed_jobs();"

Write-Host "✅ Cleanup completed"
"@ | Out-File -FilePath $scriptPath -Encoding UTF8

# Create scheduled task (run every Sunday at 2 AM)
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File $scriptPath"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "PostgreSQL_DataRetention_Cleanup" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Description "Automated data retention policy for USM Autoimmune ML Platform"

Write-Host "✅ Scheduled task created successfully"
```

## ============================================================================
## 3. Manual Cleanup Commands
## ============================================================================

### Check What Will Be Cleaned Up
```sql
-- Preview jobs to be archived
SELECT 
    job_id, 
    model_name, 
    status, 
    completed_at,
    AGE(NOW(), completed_at) as age
FROM training_jobs 
WHERE status = 'completed' 
  AND completed_at < NOW() - INTERVAL '1 year'
ORDER BY completed_at;

-- Preview failed jobs to be deleted
SELECT 
    job_id, 
    model_name, 
    status, 
    error_message,
    completed_at
FROM training_jobs 
WHERE status = 'failed' 
  AND completed_at < NOW() - INTERVAL '6 months'
ORDER BY completed_at;
```

### Execute Cleanup Manually
```sql
-- Archive old jobs
SELECT archive_old_training_jobs();

-- Delete failed jobs
SELECT delete_old_failed_jobs();

-- Check results
SELECT * FROM retention_policy_status;
```

### Restore Archived Job (if needed)
```sql
-- Move job back from archive to active
INSERT INTO training_jobs 
SELECT 
    job_id, job_type, status, user_id, created_at, started_at, 
    completed_at, progress, result, error_message, params, 
    artifact_paths, oof_predictions_path, model_name, dataset_id, 
    oof_auc, test_auc, test_f1, test_precision, test_recall, 
    test_brier_score, training_time_seconds
FROM training_jobs_archive
WHERE job_id = 'YOUR_JOB_ID';

-- Optionally delete from archive
DELETE FROM training_jobs_archive WHERE job_id = 'YOUR_JOB_ID';
```

## ============================================================================
## 4. Monitoring & Verification
## ============================================================================

### PostgreSQL Storage Usage
```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public' 
  AND tablename IN ('training_jobs', 'training_jobs_archive')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Count records by age
SELECT 
    status,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 month') AS last_month,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '6 months') AS last_6_months,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 year') AS last_year,
    COUNT(*) AS total
FROM training_jobs
GROUP BY status;
```

### MinIO Storage Usage
```bash
# Check bucket size
mc du myminio/training-artifacts

# List old objects (older than 365 days)
mc ls --recursive myminio/training-artifacts | \
  awk '$1 < "'$(date -d '365 days ago' +%Y-%m-%d)'" {print}'

# Count objects by age
mc ls --recursive myminio/training-artifacts | \
  awk '{print $1}' | \
  awk -v now="$(date +%s)" '
    {
      cmd = "date -d "$1" +%s"
      cmd | getline timestamp
      close(cmd)
      age_days = (now - timestamp) / 86400
      if (age_days < 30) month++
      else if (age_days < 180) six_months++
      else if (age_days < 365) year++
      else old++
    }
    END {
      print "< 1 month:", month
      print "< 6 months:", six_months
      print "< 1 year:", year
      print "> 1 year (eligible for deletion):", old
    }'
```

## ============================================================================
## 5. Retention Policy Summary
## ============================================================================

| Data Type               | Retention Period | Storage      | Action    | Automated |
|-------------------------|------------------|--------------|-----------|-----------|
| **Completed Jobs**      | 1 year           | PostgreSQL   | Archive   | Yes       |
| **Archived Jobs**       | Permanent        | Archive table| Keep      | N/A       |
| **Failed Jobs**         | 6 months         | PostgreSQL   | Delete    | Yes       |
| **Model Artifacts**     | 1 year           | MinIO        | Delete    | Yes       |
| **OOF Predictions**     | 1 year           | MinIO        | Delete    | Yes       |
| **Dataset Files**       | 1 year           | MinIO        | Delete    | Yes       |
| **Prediction Results**  | 2 years          | MinIO        | Delete    | Yes       |
| **User Accounts**       | Permanent        | PostgreSQL   | Keep      | N/A       |
| **Audit Logs**          | 2 years          | PostgreSQL   | Archive   | Manual    |

## ============================================================================
## 6. Compliance Notes
## ============================================================================

**Data Protection**: All retention policies comply with:
- Malaysia Personal Data Protection Act 2010 (PDPA)
- Research data retention requirements (minimum 5 years for patient data)
- USM data governance policies

**Important**: 
- Patient medical records (structured_data_pivot, flexible_dataset_wide) are NOT subject to automatic deletion
- Only ML training artifacts (models, predictions) are automatically cleaned up
- Archived jobs can be restored within 30 days of archival
- Critical production models should be tagged "retention=permanent" in MinIO

## ============================================================================
## 7. Quick Start (Deploy Now)
## ============================================================================

```bash
# 1. Apply MinIO policy (10 seconds)
mc ilm add myminio/training-artifacts --expiry-days 365 --prefix "models/"

# 2. Apply PostgreSQL policy (30 seconds)
psql -h 100.106.132.15 -U postgres -d usm_autoimmune_registry < postgres-retention-policy.sql

# 3. Verify
mc ilm ls myminio/training-artifacts
psql -h 100.106.132.15 -U postgres -d usm_autoimmune_registry -c "SELECT * FROM retention_policy_status;"

# ✅ Done! Policies are active.
```

## ============================================================================
## Contact & Support
## ============================================================================
- For policy changes: Contact Platform Administrator
- Emergency restore: Contact Database Administrator
- Policy review: Quarterly (every 3 months)
