-- ============================================
-- USM Autoimmune ML Platform - Database Schema
-- Data Engineer: Syarifah Fajriyah
-- Sprint 1: UPB-06 - Implement Registry Database Schema
-- ============================================

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- TABLE 1: users (Authentication & RBAC)
-- ============================================

CREATE TYPE user_role AS ENUM ('ADMIN', 'RESEARCHER', 'VIEWER', 'ENGINEER');

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'VIEWER',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(user_id),
    last_login TIMESTAMP,
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

COMMENT ON TABLE users IS 'User authentication and role-based access control';

-- ============================================
-- TABLE 2: patients (Anonymised Patient Identity)
-- ============================================

CREATE TABLE patients (
    patient_uuid UUID PRIMARY KEY,
    age_band VARCHAR(10) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    ethnicity VARCHAR(30),
    region_code VARCHAR(10),
    dataset_version VARCHAR(50) NOT NULL,
    is_anonymised BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT age_band_format CHECK (age_band ~ '^\d+-\d+$'),
    CONSTRAINT gender_values CHECK (gender IN ('Female', 'Male', 'Other')),
    CONSTRAINT must_be_anonymised CHECK (is_anonymised = TRUE)
);

CREATE INDEX idx_patients_dataset_version ON patients(dataset_version);
CREATE INDEX idx_patients_ethnicity ON patients(ethnicity);
CREATE INDEX idx_patients_age_band ON patients(age_band);

COMMENT ON TABLE patients IS 'Anonymised patient identity (SHA-256 hashed UUID)';
COMMENT ON COLUMN patients.patient_uuid IS 'SHA-256 hash of original patient ID - NEVER store raw IC/NRIC';
COMMENT ON COLUMN patients.age_band IS 'Age grouped: 15-24, 25-34, 35-44, etc. NOT exact DOB';

-- ============================================
-- TABLE 3: lab_results (Laboratory Test Values)
-- ============================================

CREATE TABLE lab_results (
    result_id BIGSERIAL PRIMARY KEY,
    patient_uuid UUID NOT NULL REFERENCES patients(patient_uuid) ON DELETE CASCADE,
    
    -- Autoantibody Tests
    ana_positive BOOLEAN,
    ana_titre VARCHAR(20),
    anti_dsdna_titre FLOAT,
    anti_ro_ssa BOOLEAN,
    anti_la_ssb BOOLEAN,
    anti_sm BOOLEAN,
    
    -- Complement Levels (LOW values = clinically significant, NOT errors)
    complement_c3 FLOAT,
    complement_c4 FLOAT,
    
    -- Complete Blood Count
    wbc_count FLOAT,
    platelet_count FLOAT,
    haemoglobin FLOAT,
    
    -- Inflammation Markers
    esr FLOAT,
    crp FLOAT,
    
    -- Metadata
    collected_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Validation Constraints
    CONSTRAINT positive_anti_dsdna CHECK (anti_dsdna_titre IS NULL OR anti_dsdna_titre >= 0),
    CONSTRAINT positive_c3 CHECK (complement_c3 IS NULL OR complement_c3 >= 0),
    CONSTRAINT positive_c4 CHECK (complement_c4 IS NULL OR complement_c4 >= 0),
    CONSTRAINT positive_wbc CHECK (wbc_count IS NULL OR wbc_count >= 0),
    CONSTRAINT positive_platelets CHECK (platelet_count IS NULL OR platelet_count >= 0),
    CONSTRAINT positive_hb CHECK (haemoglobin IS NULL OR haemoglobin >= 0)
);

CREATE INDEX idx_lab_results_patient ON lab_results(patient_uuid);
CREATE INDEX idx_lab_results_date ON lab_results(collected_date);

COMMENT ON TABLE lab_results IS 'Laboratory test values per patient visit';
COMMENT ON COLUMN lab_results.complement_c3 IS 'LOW values (<50) are clinically significant in SLE - DO NOT treat as outlier errors';
COMMENT ON COLUMN lab_results.complement_c4 IS 'LOW values (<8) are clinically significant in SLE - DO NOT treat as outlier errors';
COMMENT ON COLUMN lab_results.wbc_count IS 'Leucopenia (low WBC) is a feature of active SLE - preserve low outliers';

-- ============================================
-- TABLE 4: clinical_symptoms (Physical Exam & Symptoms)
-- ============================================

CREATE TABLE clinical_symptoms (
    symptom_id BIGSERIAL PRIMARY KEY,
    patient_uuid UUID NOT NULL REFERENCES patients(patient_uuid) ON DELETE CASCADE,
    
    -- SLE-specific symptoms
    malar_rash BOOLEAN DEFAULT FALSE,
    discoid_rash BOOLEAN DEFAULT FALSE,
    photosensitivity BOOLEAN DEFAULT FALSE,
    oral_ulcers BOOLEAN DEFAULT FALSE,
    joint_pain BOOLEAN DEFAULT FALSE,
    non_erosive_arthritis BOOLEAN DEFAULT FALSE,
    skin_rash BOOLEAN DEFAULT FALSE,
    
    -- Sjögren's-specific symptoms
    dry_eyes BOOLEAN DEFAULT FALSE,
    dry_mouth BOOLEAN DEFAULT FALSE,
    parotid_enlargement BOOLEAN DEFAULT FALSE,
    
    -- Severity scores
    fatigue_score SMALLINT,
    disease_activity_score FLOAT,
    
    -- Organ involvement
    organ_involvement VARCHAR[] DEFAULT '{}',
    renal_involvement BOOLEAN DEFAULT FALSE,
    neuropsychiatric BOOLEAN DEFAULT FALSE,
    serositis BOOLEAN DEFAULT FALSE,
    haematological_involvement BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    assessment_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Validation
    CONSTRAINT valid_fatigue_score CHECK (fatigue_score IS NULL OR (fatigue_score >= 0 AND fatigue_score <= 10))
);

CREATE INDEX idx_symptoms_patient ON clinical_symptoms(patient_uuid);
CREATE INDEX idx_symptoms_date ON clinical_symptoms(assessment_date);
CREATE INDEX idx_symptoms_renal ON clinical_symptoms(renal_involvement);

COMMENT ON TABLE clinical_symptoms IS 'Clinical symptoms and physical exam findings';
COMMENT ON COLUMN clinical_symptoms.organ_involvement IS 'Array: {kidney, lung, heart, cns, liver, skin}';

-- ============================================
-- TABLE 5: diagnoses (ML Target Variable)
-- ============================================

CREATE TABLE diagnoses (
    diagnosis_id BIGSERIAL PRIMARY KEY,
    patient_uuid UUID NOT NULL REFERENCES patients(patient_uuid) ON DELETE CASCADE,
    
    -- ML TARGET VARIABLE
    confirmed_autoimmune BOOLEAN NOT NULL,
    
    -- Disease classification
    disease_class VARCHAR(50),
    disease_subtype VARCHAR(50),
    icd10_code VARCHAR(10),
    
    -- Diagnostic scores
    acreular_score FLOAT,
    sledai_score SMALLINT,
    
    -- Metadata
    diagnosis_date DATE NOT NULL,
    diagnosed_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Validation
    CONSTRAINT valid_disease_class CHECK (disease_class IN ('SLE', 'Sjogrens', 'RA', 'Undifferentiated', 'Other', NULL)),
    CONSTRAINT valid_sledai CHECK (sledai_score IS NULL OR (sledai_score >= 0 AND sledai_score <= 105))
);

CREATE INDEX idx_diagnoses_patient ON diagnoses(patient_uuid);
CREATE INDEX idx_diagnoses_target ON diagnoses(confirmed_autoimmune);
CREATE INDEX idx_diagnoses_class ON diagnoses(disease_class);

COMMENT ON TABLE diagnoses IS 'Target variable for ML prediction: confirmed_autoimmune';
COMMENT ON COLUMN diagnoses.confirmed_autoimmune IS 'ML TARGET: TRUE = confirmed autoimmune diagnosis';
COMMENT ON COLUMN diagnoses.sledai_score IS 'SLE Disease Activity Index: 0 = inactive, >4 = mild, >8 = moderate, >12 = severe';

-- ============================================
-- TABLE 6: ml_experiments (Model Training Logs)
-- ============================================

CREATE TYPE experiment_status AS ENUM ('queued', 'running', 'success', 'failed');
CREATE TYPE model_type AS ENUM ('CatBoost', 'XGBoost', 'AdaBoost', 'DecisionTree', 'RandomForest', 'StackingEnsemble');

CREATE TABLE ml_experiments (
    experiment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_type model_type NOT NULL,
    dataset_version VARCHAR(50) NOT NULL,
    
    -- Model configuration
    feature_set JSONB NOT NULL,
    hyperparameters JSONB NOT NULL,
    
    -- Performance metrics
    accuracy FLOAT,
    precision_score FLOAT,
    recall_score FLOAT,
    f1_score FLOAT,
    auc_roc FLOAT,
    confusion_matrix JSONB,
    
    -- Execution metadata
    status experiment_status DEFAULT 'queued',
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    run_duration_sec FLOAT,
    model_artifact_path VARCHAR(255),
    notes TEXT,
    
    -- Traceability
    executed_by UUID REFERENCES users(user_id),
    
    -- Validation
    CONSTRAINT valid_accuracy CHECK (accuracy IS NULL OR (accuracy >= 0 AND accuracy <= 1)),
    CONSTRAINT valid_precision CHECK (precision_score IS NULL OR (precision_score >= 0 AND precision_score <= 1)),
    CONSTRAINT valid_recall CHECK (recall_score IS NULL OR (recall_score >= 0 AND recall_score <= 1))
);

CREATE INDEX idx_ml_experiments_version ON ml_experiments(dataset_version);
CREATE INDEX idx_ml_experiments_model ON ml_experiments(model_type);
CREATE INDEX idx_ml_experiments_status ON ml_experiments(status);
CREATE INDEX idx_ml_experiments_timestamp ON ml_experiments(run_timestamp);

COMMENT ON TABLE ml_experiments IS 'ML training experiment logs - written by Iznie';
COMMENT ON COLUMN ml_experiments.precision_score IS 'Named precision_score to avoid SQL reserved keyword conflict';

-- ============================================
-- TABLE 7: ingestion_log (Immutable Audit Trail)
-- ============================================

CREATE TYPE validation_status AS ENUM ('passed', 'failed', 'partial');
CREATE TYPE pipeline_status AS ENUM ('queued', 'processing', 'complete', 'error');

CREATE TABLE ingestion_log (
    log_id BIGSERIAL PRIMARY KEY,
    uploader_user_id UUID NOT NULL REFERENCES users(user_id),
    
    -- File metadata
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    file_size_bytes BIGINT NOT NULL,
    record_count INTEGER,
    
    -- Validation results
    validation_status validation_status NOT NULL,
    validation_errors JSONB DEFAULT '[]',
    
    -- Dataset versioning
    dataset_version VARCHAR(50) NOT NULL,
    
    -- Processing status
    pipeline_status pipeline_status DEFAULT 'queued',
    
    -- Timestamps (immutable)
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Validation
    CONSTRAINT positive_file_size CHECK (file_size_bytes > 0),
    CONSTRAINT valid_file_type CHECK (file_type IN ('CSV', 'XLSX', 'PDF', 'IMAGE', 'DICOM', 'JSON'))
);

CREATE INDEX idx_ingestion_log_uploader ON ingestion_log(uploader_user_id);
CREATE INDEX idx_ingestion_log_dataset_version ON ingestion_log(dataset_version);
CREATE INDEX idx_ingestion_log_timestamp ON ingestion_log(ingested_at);
CREATE INDEX idx_ingestion_log_file_hash ON ingestion_log(file_hash);

-- Make ingestion_log immutable (INSERT only, no UPDATE/DELETE)
CREATE OR REPLACE FUNCTION prevent_ingestion_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'ingestion_log is immutable - no UPDATE or DELETE allowed';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER immutable_ingestion_log
BEFORE UPDATE OR DELETE ON ingestion_log
FOR EACH ROW EXECUTE FUNCTION prevent_ingestion_log_modification();

COMMENT ON TABLE ingestion_log IS 'Immutable audit trail of all data uploads - NMRR/PDPA compliance';
COMMENT ON COLUMN ingestion_log.file_hash IS 'SHA-256 hash of file content - detects duplicate uploads';

-- ============================================
-- TABLE 8: password_resets (Password Reset Tokens)
-- ============================================

CREATE TABLE password_resets (
    token_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT token_not_expired CHECK (expires_at > created_at)
);

CREATE INDEX idx_password_resets_user ON password_resets(user_id);
CREATE INDEX idx_password_resets_token ON password_resets(token_hash);

COMMENT ON TABLE password_resets IS 'Password reset tokens with expiry';

-- ============================================
-- INITIAL DATA: Create default admin user
-- ============================================

-- Default password: "ChangeThisSecurePassword123!"
-- This should be changed immediately after first login
INSERT INTO users (email, password_hash, role, is_active)
VALUES (
    'admin@usm.edu.my',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeP4C9M5.WfzHHCXK',  -- bcrypt hash
    'ADMIN',
    TRUE
);

-- ============================================
-- DATABASE STATISTICS & MONITORING
-- ============================================

-- View to monitor table sizes
CREATE VIEW table_sizes AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- View to monitor recent ingestions
CREATE VIEW recent_ingestions AS
SELECT
    il.log_id,
    u.email AS uploader,
    il.filename,
    il.file_type,
    il.record_count,
    il.validation_status,
    il.pipeline_status,
    il.dataset_version,
    il.ingested_at
FROM ingestion_log il
JOIN users u ON il.uploader_user_id = u.user_id
ORDER BY il.ingested_at DESC
LIMIT 50;

-- ============================================
-- RBAC Helper Functions
-- ============================================

-- Function to check if user has required role
CREATE OR REPLACE FUNCTION user_has_role(check_user_id UUID, required_role user_role)
RETURNS BOOLEAN AS $$
DECLARE
    user_role_value user_role;
BEGIN
    SELECT role INTO user_role_value FROM users WHERE user_id = check_user_id AND is_active = TRUE;
    RETURN user_role_value = required_role OR user_role_value = 'ADMIN';
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- DATA QUALITY VIEWS
-- ============================================

-- View to identify patients with missing critical lab values
CREATE VIEW patients_missing_critical_labs AS
SELECT
    p.patient_uuid,
    p.age_band,
    p.gender,
    p.ethnicity,
    CASE WHEN lr.ana_positive IS NULL THEN TRUE ELSE FALSE END AS missing_ana,
    CASE WHEN lr.anti_dsdna_titre IS NULL THEN TRUE ELSE FALSE END AS missing_anti_dsdna,
    CASE WHEN lr.complement_c3 IS NULL THEN TRUE ELSE FALSE END AS missing_c3,
    CASE WHEN lr.complement_c4 IS NULL THEN TRUE ELSE FALSE END AS missing_c4
FROM patients p
LEFT JOIN lab_results lr ON p.patient_uuid = lr.patient_uuid
WHERE lr.ana_positive IS NULL
   OR lr.anti_dsdna_titre IS NULL
   OR lr.complement_c3 IS NULL
   OR lr.complement_c4 IS NULL;

-- ============================================
-- GRANT PERMISSIONS
-- ============================================

-- Create read-only role for VIEWER and ENGINEER roles
GRANT SELECT ON ALL TABLES IN SCHEMA public TO PUBLIC;
GRANT INSERT, UPDATE ON users, patients, lab_results, clinical_symptoms, diagnoses TO PUBLIC;
GRANT INSERT ON ingestion_log, ml_experiments TO PUBLIC;

-- ============================================
-- COMPLETION NOTICE
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'USM Autoimmune ML Platform Database';
    RAISE NOTICE 'Schema initialization complete';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables created: 8';
    RAISE NOTICE '- users (authentication + RBAC)';
    RAISE NOTICE '- patients (anonymised identity)';
    RAISE NOTICE '- lab_results (laboratory tests)';
    RAISE NOTICE '- clinical_symptoms (physical exam)';
    RAISE NOTICE '- diagnoses (ML target variable)';
    RAISE NOTICE '- ml_experiments (training logs)';
    RAISE NOTICE '- ingestion_log (audit trail - IMMUTABLE)';
    RAISE NOTICE '- password_resets (auth support)';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Default admin user created:';
    RAISE NOTICE 'Email: admin@usm.edu.my';
    RAISE NOTICE 'Password: ChangeThisSecurePassword123!';
    RAISE NOTICE 'CHANGE THIS PASSWORD IMMEDIATELY';
    RAISE NOTICE '========================================';
END $$;
