-- ============================================================================
-- PostgreSQL Data Retention Policy for USM Autoimmune ML Platform
-- ============================================================================
-- Purpose: Archive or delete old training jobs, predictions, and logs
-- Retention: 1 year for completed jobs, 6 months for failed jobs
-- Created: 2026-04-24
-- ============================================================================

-- 1. Archive old completed training jobs (older than 1 year)
CREATE OR REPLACE FUNCTION archive_old_training_jobs()
RETURNS TABLE(archived_count INTEGER) AS $$
DECLARE
    archived INTEGER := 0;
BEGIN
    -- Move completed jobs older than 1 year to archive table
    WITH archived_jobs AS (
        DELETE FROM training_jobs
        WHERE 
            status = 'COMPLETED'::jobstatus
            AND completed_at < NOW() - INTERVAL '1 year'
        RETURNING *
    )
    INSERT INTO training_jobs_archive 
    SELECT * FROM archived_jobs;
    
    GET DIAGNOSTICS archived = ROW_COUNT;
    
    RAISE NOTICE 'Archived % completed training jobs older than 1 year', archived;
    RETURN QUERY SELECT archived;
END;
$$ LANGUAGE plpgsql;

-- 2. Delete failed jobs (older than 6 months)
CREATE OR REPLACE FUNCTION delete_old_failed_jobs()
RETURNS TABLE(deleted_count INTEGER) AS $$
DECLARE
    deleted INTEGER := 0;
BEGIN
    DELETE FROM training_jobs
    WHERE 
        status = 'FAILED'::jobstatus
        AND completed_at < NOW() - INTERVAL '6 months';
    
    GET DIAGNOSTICS deleted = ROW_COUNT;
    
    RAISE NOTICE 'Deleted % failed training jobs older than 6 months', deleted;
    RETURN QUERY SELECT deleted;
END;
$$ LANGUAGE plpgsql;

-- 3. Delete old prediction history (older than 2 years)
CREATE OR REPLACE FUNCTION delete_old_predictions()
RETURNS TABLE(deleted_count INTEGER) AS $$
DECLARE
    deleted INTEGER := 0;
BEGIN
    -- Note: Actual predictions CSV files in MinIO will be deleted by lifecycle policy
    -- This only cleans up prediction metadata if stored in PostgreSQL
    
    -- If you have a predictions table:
    -- DELETE FROM predictions WHERE created_at < NOW() - INTERVAL '2 years';
    
    RAISE NOTICE 'Prediction cleanup - MinIO lifecycle policy handles file deletion';
    RETURN QUERY SELECT 0;
END;
$$ LANGUAGE plpgsql;

-- 4. Create archive table (run once during deployment)
CREATE TABLE IF NOT EXISTS training_jobs_archive (
    LIKE training_jobs INCLUDING ALL
);

-- Add archival metadata columns
ALTER TABLE training_jobs_archive 
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- 5. Create automated cleanup schedule (PostgreSQL cron extension required)
-- Option A: Using pg_cron (if installed)
/*
SELECT cron.schedule(
    'archive-old-training-jobs',
    '0 2 * * 0',  -- Every Sunday at 2 AM
    'SELECT archive_old_training_jobs();'
);

SELECT cron.schedule(
    'delete-old-failed-jobs',
    '0 3 * * 0',  -- Every Sunday at 3 AM
    'SELECT delete_old_failed_jobs();'
);
*/

-- Option B: Manual execution (recommended for initial setup)
-- Run these commands monthly via cron or scheduled task:
-- psql -U postgres -d usm_autoimmune_registry -c "SELECT archive_old_training_jobs();"
-- psql -U postgres -d usm_autoimmune_registry -c "SELECT delete_old_failed_jobs();"

-- 6. View retention policy summary
CREATE OR REPLACE VIEW retention_policy_status AS
SELECT 
    'Active Training Jobs' AS category,
    COUNT(*) AS count,
    MIN(created_at) AS oldest,
    MAX(created_at) AS newest
FROM training_jobs
UNION ALL
SELECT 
    'Archived Training Jobs',
    COUNT(*),
    MIN(created_at),
    MAX(created_at)
FROM training_jobs_archive
UNION ALL
SELECT 
    'Jobs Eligible for Archive',
    COUNT(*),
    MIN(completed_at),
    MAX(completed_at)
FROM training_jobs
WHERE status = 'COMPLETED'::jobstatus AND completed_at < NOW() - INTERVAL '1 year'
UNION ALL
SELECT 
    'Failed Jobs Eligible for Deletion',
    COUNT(*),
    MIN(completed_at),
    MAX(completed_at)
FROM training_jobs
WHERE status = 'FAILED'::jobstatus AND completed_at < NOW() - INTERVAL '6 months';

-- 7. Manual cleanup commands (run when needed)
-- View what will be archived:
-- SELECT job_id, model_name, completed_at FROM training_jobs 
-- WHERE status = 'COMPLETED'::jobstatus AND completed_at < NOW() - INTERVAL '1 year';

-- Execute archive:
-- SELECT archive_old_training_jobs();

-- Execute failed job cleanup:
-- SELECT delete_old_failed_jobs();

-- Check retention policy status:
-- SELECT * FROM retention_policy_status;

-- ============================================================================
-- Retention Policy Summary
-- ============================================================================
-- | Data Type              | Retention Period | Storage Location | Policy    |
-- |------------------------|------------------|------------------|-----------|
-- | Completed Training Jobs| 1 year (active)  | PostgreSQL       | Archive   |
-- |                        | Permanent        | Archive table    | Keep      |
-- | Failed Training Jobs   | 6 months         | PostgreSQL       | Delete    |
-- | Model Artifacts        | 1 year           | MinIO            | Delete    |
-- | OOF Predictions        | 1 year           | MinIO            | Delete    |
-- | Dataset Files          | 1 year           | MinIO            | Delete    |
-- | Prediction Results     | 2 years          | MinIO            | Delete    |
-- | User Accounts          | Permanent        | PostgreSQL       | Keep      |
-- | Audit Logs             | 2 years          | PostgreSQL       | Archive   |
-- ============================================================================
