-- ============================================================================
-- USM Autoimmune ML Platform - Flexible Schema Migration
-- Date: March 16, 2026
-- Description: Create flexible database schema for multi-disease support
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ============================================================================
-- 1. UPDATE PATIENTS TABLE (Make it flexible)
-- ============================================================================

-- Drop old patient table if exists (backup data first if needed!)
-- DROP TABLE IF EXISTS patients CASCADE;

ALTER TABLE IF EXISTS patients DROP COLUMN IF EXISTS full_name;
ALTER TABLE IF EXISTS patients DROP COLUMN IF EXISTS date_of_birth;
ALTER TABLE IF EXISTS patients DROP COLUMN IF EXISTS ic_number;
ALTER TABLE IF EXISTS patients DROP COLUMN IF EXISTS phone;
ALTER TABLE IF EXISTS patients DROP COLUMN IF EXISTS email;
ALTER TABLE IF EXISTS patients DROP COLUMN IF EXISTS address;
ALTER TABLE IF EXISTS patients DROP COLUMN IF EXISTS diagnosis;
ALTER TABLE IF EXISTS patients DROP COLUMN IF EXISTS diagnosis_date;
ALTER TABLE IF EXISTS patients DROP COLUMN IF EXISTS disease_type;
ALTER TABLE IF EXISTS patients DROP COLUMN IF EXISTS risk_score;
ALTER TABLE IF EXISTS patients DROP COLUMN IF EXISTS prediction_data;
ALTER TABLE IF EXISTS patients DROP COLUMN IF EXISTS last_prediction_at;
ALTER TABLE IF EXISTS patients DROP COLUMN IF EXISTS patient_id;

-- Add new flexible columns
ALTER TABLE IF EXISTS patients 
    ADD COLUMN IF NOT EXISTS anonymous_id VARCHAR(50) UNIQUE NOT NULL DEFAULT 'USMA-2026-' || LPAD(id::TEXT, 4, '0'),
    ADD COLUMN IF NOT EXISTS original_id_hash VARCHAR(64) UNIQUE,
    ADD COLUMN IF NOT EXISTS age INTEGER,
    ADD COLUMN IF NOT EXISTS age_range VARCHAR(20),
    ADD COLUMN IF NOT EXISTS gender VARCHAR(10),
    ADD COLUMN IF NOT EXISTS ethnicity VARCHAR(50),
    ADD COLUMN IF NOT EXISTS contact_encrypted TEXT,
    ADD COLUMN IF NOT EXISTS data_source VARCHAR(100),
    ADD COLUMN IF NOT EXISTS import_batch_id UUID DEFAULT uuid_generate_v4(),
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS is_anonymized BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_patients_anonymous_id ON patients(anonymous_id);
CREATE INDEX IF NOT EXISTS idx_patients_import_batch ON patients(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_patients_age_gender ON patients(age, gender);

-- ============================================================================
-- 2. DIAGNOSES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS diagnoses (
    diagnosis_id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    disease_code VARCHAR(20),
    disease_name VARCHAR(200) NOT NULL,
    diagnosis_date DATE,
    is_primary BOOLEAN DEFAULT FALSE,
    severity VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_diagnoses_patient_disease ON diagnoses(patient_id, disease_name);

-- ============================================================================
-- 3. LAB_TEST_DEFINITIONS TABLE (Catalog of all tests)
-- ============================================================================

CREATE TABLE IF NOT EXISTS lab_test_definitions (
    test_id SERIAL PRIMARY KEY,
    test_code VARCHAR(50) UNIQUE NOT NULL,
    test_name VARCHAR(200) NOT NULL,
    test_category VARCHAR(100),
    default_reference_range JSONB,
    unit VARCHAR(50),
    data_type VARCHAR(20),
    relevant_diseases TEXT[],
    description TEXT,
    alternative_names JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_lab_test_code ON lab_test_definitions(test_code);
CREATE INDEX IF NOT EXISTS idx_lab_test_category ON lab_test_definitions(test_category);

-- ============================================================================
-- 4. LAB_RESULTS_FLEXIBLE TABLE (Flexible lab results)
-- ============================================================================

CREATE TABLE IF NOT EXISTS lab_results_flexible (
    result_id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    test_id INTEGER NOT NULL REFERENCES lab_test_definitions(test_id),
    test_date DATE NOT NULL,
    value_numeric NUMERIC(15,4),
    value_text TEXT,
    value_jsonb JSONB,
    unit VARCHAR(50),
    reference_range JSONB,
    is_abnormal BOOLEAN,
    abnormal_flag VARCHAR(10),
    result_status VARCHAR(20) DEFAULT 'final',
    specimen_type VARCHAR(50),
    notes TEXT,
    uploaded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_has_value CHECK (
        value_numeric IS NOT NULL OR 
        value_text IS NOT NULL OR 
        value_jsonb IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_lab_results_patient_test_date ON lab_results_flexible(patient_id, test_id, test_date);
CREATE INDEX IF NOT EXISTS idx_lab_results_test_date ON lab_results_flexible(test_date);

-- ============================================================================
-- 5. LAB_RESULTS_BATCH TABLE (Batch/panel results)
-- ============================================================================

CREATE TABLE IF NOT EXISTS lab_results_batch (
    batch_id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    batch_name VARCHAR(200),
    test_date DATE NOT NULL,
    results JSONB NOT NULL,
    panel_type VARCHAR(100),
    test_count INTEGER,
    uploaded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lab_batch_patient_date ON lab_results_batch(patient_id, test_date);
CREATE INDEX IF NOT EXISTS idx_lab_batch_panel_type ON lab_results_batch(panel_type);
CREATE INDEX IF NOT EXISTS idx_lab_batch_results_gin ON lab_results_batch USING gin(results);

-- ============================================================================
-- 6. DISEASE_SPECIFIC_DATA TABLE (Pure JSONB storage)
-- ============================================================================

CREATE TABLE IF NOT EXISTS disease_specific_data (
    data_id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    disease_name VARCHAR(100) NOT NULL,
    data_category VARCHAR(100),
    data JSONB NOT NULL,
    collection_date DATE,
    notes TEXT,
    uploaded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_disease_data_patient_disease ON disease_specific_data(patient_id, disease_name);
CREATE INDEX IF NOT EXISTS idx_disease_data_category ON disease_specific_data(data_category);
CREATE INDEX IF NOT EXISTS idx_disease_data_gin ON disease_specific_data USING gin(data);

-- ============================================================================
-- 7. UPLOADED_FILES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS uploaded_files (
    file_id SERIAL PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100),
    is_encrypted BOOLEAN DEFAULT TRUE,
    encryption_key_id VARCHAR(100),
    file_hash VARCHAR(64) NOT NULL,
    row_count INTEGER,
    column_count INTEGER,
    column_mapping JSONB,
    upload_status VARCHAR(20) DEFAULT 'pending',
    validation_errors JSONB,
    processing_errors JSONB,
    import_stats JSONB,
    dataset_type VARCHAR(100),
    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_uploads_status ON uploaded_files(upload_status);
CREATE INDEX IF NOT EXISTS idx_uploads_user ON uploaded_files(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_uploads_date ON uploaded_files(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_uploads_hash ON uploaded_files(file_hash);

-- ============================================================================
-- 8. DATA_INGESTION_AUDIT TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS data_ingestion_audit (
    audit_id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES uploaded_files(file_id) ON DELETE SET NULL,
    batch_id VARCHAR(36) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    action_status VARCHAR(20) NOT NULL,
    table_name VARCHAR(100),
    records_affected INTEGER DEFAULT 0,
    patients_affected INTEGER DEFAULT 0,
    error_message TEXT,
    error_details JSONB,
    execution_time_ms INTEGER,
    performed_by INTEGER NOT NULL REFERENCES users(id),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_batch_id ON data_ingestion_audit(batch_id);
CREATE INDEX IF NOT EXISTS idx_audit_action_type ON data_ingestion_audit(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_action_status ON data_ingestion_audit(action_status);
CREATE INDEX IF NOT EXISTS idx_audit_performed_at ON data_ingestion_audit(performed_at);

-- ============================================================================
-- 9. UPDATE TRIGGERS (auto-update updated_at)
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'pgsql';

-- Apply trigger to patients
DROP TRIGGER IF EXISTS update_patients_updated_at ON patients;
CREATE TRIGGER update_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to disease_specific_data
DROP TRIGGER IF EXISTS update_disease_data_updated_at ON disease_specific_data;
CREATE TRIGGER update_disease_data_updated_at
    BEFORE UPDATE ON disease_specific_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify table creation
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    AND table_name IN (
        'patients', 'diagnoses', 'lab_test_definitions', 
        'lab_results_flexible', 'lab_results_batch', 
        'disease_specific_data', 'uploaded_files', 'data_ingestion_audit'
    )
ORDER BY table_name;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ Flexible schema migration complete!';
    RAISE NOTICE '========================================';
END $$;
