-- Migration: Make test_date nullable in lab_results_flexible
-- Reason: Lab results may not always have test dates in source data
-- Date: 2026-03-16

BEGIN;

-- Make test_date nullable
ALTER TABLE lab_results_flexible 
ALTER COLUMN test_date DROP NOT NULL;

-- Add comment  
COMMENT ON COLUMN lab_results_flexible.test_date IS 
'Date when test was performed. Nullable to accommodate historical data without dates.';

COMMIT;
