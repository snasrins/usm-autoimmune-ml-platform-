-- ============================================================================
-- FIX: Update Patients Table with All Required Columns
-- ============================================================================

-- Add columns one by one (simple approach)
ALTER TABLE patients ADD COLUMN IF NOT EXISTS anonymous_id VARCHAR(50);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS original_id_hash VARCHAR(64);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS age INTEGER;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS age_range VARCHAR(20);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS ethnicity VARCHAR(50);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS contact_encrypted TEXT;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS data_source VARCHAR(100);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS import_batch_id UUID;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS is_anonymized BOOLEAN DEFAULT TRUE;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS additional_data JSONB;

-- Create indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_patients_anonymous_id_unique ON patients(anonymous_id);
CREATE INDEX IF NOT EXISTS idx_patients_anonymous_id ON patients(anonymous_id);
CREATE INDEX IF NOT EXISTS idx_patients_import_batch ON patients(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_patients_age_gender ON patients(age, gender);
CREATE UNIQUE INDEX IF NOT EXISTS idx_patients_original_hash ON patients(original_id_hash);

-- Verify structure
\d patients

-- Test insert
SELECT 'Patients table structure updated successfully!' as status;
