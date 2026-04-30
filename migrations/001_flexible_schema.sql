-- Migration: Add Flexible JSONB-Based Schema
-- Description: Create flexible tables that support ANY dataset structure
-- Date: 2026-04-06
-- Author: Syarifah Fajriyah

-- ============================================================================
-- STEP 1: Create Flexible Tables (No Hardcoded Columns)
-- ============================================================================

-- Import Preview Staging (Temporary, Editable)
CREATE TABLE IF NOT EXISTS import_preview_staging (
    staging_id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    
    -- Dataset metadata
    dataset_type VARCHAR(50),
    dataset_name VARCHAR(100),
    
    -- FLEXIBLE: Store entire CSV row as JSONB
    row_data JSONB NOT NULL,
    row_number INTEGER,
    
    -- User editing
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    edit_history JSONB,
    
    -- Validation
    validation_status VARCHAR(20) DEFAULT 'pending',
    validation_errors JSONB,
    
    -- Auto-cleanup
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for staging
CREATE INDEX IF NOT EXISTS idx_staging_session ON import_preview_staging(session_id);
CREATE INDEX IF NOT EXISTS idx_staging_deleted ON import_preview_staging(is_deleted);
CREATE INDEX IF NOT EXISTS idx_staging_expires ON import_preview_staging(expires_at);
CREATE INDEX IF NOT EXISTS idx_staging_data ON import_preview_staging USING GIN (row_data);

COMMENT ON TABLE import_preview_staging IS 'Temporary staging for CSV preview & editing before saving';


-- ============================================================================
-- Flexible Dataset Wide (PRIMARY TABLE - Replaces all disease-specific tables)
-- ============================================================================

CREATE TABLE IF NOT EXISTS flexible_dataset_wide (
    id SERIAL PRIMARY KEY,
    
    -- Record identifier (patient_id, sample_id, etc.)
    record_id VARCHAR(100) NOT NULL,
    
    -- Dataset classification
    dataset_type VARCHAR(50) NOT NULL,
    dataset_name VARCHAR(100),
    dataset_version VARCHAR(20),
    
    -- FLEXIBLE: ALL data as JSONB (NO HARDCODED COLUMNS!)
    data JSONB NOT NULL,
    
    -- Schema metadata (auto-detected from CSV)
    schema_definition JSONB,
    
    -- Import source tracking
    dataset_source VARCHAR(100),
    import_batch_id UUID NOT NULL,
    import_method VARCHAR(50),
    
    -- Normalization tracking (optional feature)
    is_normalized BOOLEAN DEFAULT FALSE,
    normalized_at TIMESTAMP WITH TIME ZONE,
    normalized_by INTEGER REFERENCES users(id),
    
    -- Quality metrics
    data_quality_score INTEGER,
    missing_fields_count INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by INTEGER REFERENCES users(id)
);

-- Indexes for flexible_dataset_wide
CREATE INDEX IF NOT EXISTS idx_flexible_record ON flexible_dataset_wide(record_id);
CREATE INDEX IF NOT EXISTS idx_flexible_dataset_type ON flexible_dataset_wide(dataset_type);
CREATE INDEX IF NOT EXISTS idx_flexible_batch ON flexible_dataset_wide(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_flexible_normalized ON flexible_dataset_wide(is_normalized);
CREATE INDEX IF NOT EXISTS idx_flexible_created ON flexible_dataset_wide(created_at);
CREATE INDEX IF NOT EXISTS idx_flexible_data ON flexible_dataset_wide USING GIN (data);
CREATE INDEX IF NOT EXISTS idx_flexible_schema ON flexible_dataset_wide USING GIN (schema_definition);

-- Unique constraint on record_id + dataset_type (prevent duplicates within dataset)
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_record_dataset 
ON flexible_dataset_wide(record_id, dataset_type);

COMMENT ON TABLE flexible_dataset_wide IS 'Universal flexible wide table - stores ANY dataset structure';
COMMENT ON COLUMN flexible_dataset_wide.data IS 'All data as JSONB - demographics, lab results, clinical data, etc.';


-- ============================================================================
-- Unstructured Document Processed (OCR/NER Results)
-- ============================================================================

CREATE TABLE IF NOT EXISTS unstructured_document_processed (
    id SERIAL PRIMARY KEY,
    
    -- Link to original document
    document_id INTEGER,
    document_filename VARCHAR(255),
    
    -- Extracted record identifier (if found)
    extracted_record_id VARCHAR(100),
    
    -- FLEXIBLE: OCR extracted data as JSONB
    extracted_data JSONB NOT NULL,
    
    -- Confidence scores per field
    confidence_scores JSONB,
    
    -- Processing metadata
    ocr_engine VARCHAR(50),
    ner_model VARCHAR(50),
    processing_version VARCHAR(20),
    
    -- User verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by INTEGER REFERENCES users(id),
    verification_date TIMESTAMP WITH TIME ZONE,
    verification_notes TEXT,
    
    -- Dataset classification
    dataset_type VARCHAR(50),
    classification_confidence INTEGER,
    
    -- Normalization tracking
    is_normalized BOOLEAN DEFAULT FALSE,
    is_saved_to_wide_table BOOLEAN DEFAULT FALSE,
    saved_wide_table_id INTEGER,
    
    -- Import tracking
    import_batch_id UUID DEFAULT gen_random_uuid(),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for unstructured_document_processed
CREATE INDEX IF NOT EXISTS idx_unstructured_proc_batch ON unstructured_document_processed(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_unstructured_proc_verified ON unstructured_document_processed(is_verified);
CREATE INDEX IF NOT EXISTS idx_unstructured_proc_saved ON unstructured_document_processed(is_saved_to_wide_table);
CREATE INDEX IF NOT EXISTS idx_unstructured_proc_data ON unstructured_document_processed USING GIN (extracted_data);

COMMENT ON TABLE unstructured_document_processed IS 'OCR/NER results from unstructured documents';


-- ============================================================================
-- Dataset Schemas (Registry of dynamically created schemas)
-- ============================================================================

CREATE TABLE IF NOT EXISTS dataset_schemas (
    schema_id SERIAL PRIMARY KEY,
    
    -- Dataset identification
    dataset_type VARCHAR(50) NOT NULL UNIQUE,
    dataset_name VARCHAR(100),
    dataset_description TEXT,
    
    -- Schema definition (auto-detected from first import)
    schema_definition JSONB NOT NULL,
    
    -- Example data (for reference)
    example_record JSONB,
    
    -- Statistics
    record_count INTEGER DEFAULT 0,
    last_import_date TIMESTAMP WITH TIME ZONE,
    
    -- Version control
    schema_version VARCHAR(20) DEFAULT '1.0',
    parent_schema_id INTEGER REFERENCES dataset_schemas(schema_id),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_dataset_schemas_type ON dataset_schemas(dataset_type);
CREATE INDEX IF NOT EXISTS idx_dataset_schemas_active ON dataset_schemas(is_active);

COMMENT ON TABLE dataset_schemas IS 'Registry of dataset schemas - tracks column structure for each dataset type';


-- ============================================================================
-- ML Feature Store (Versioned features for ML training)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ml_feature_store (
    feature_id SERIAL PRIMARY KEY,
    
    -- Source record link
    source_table VARCHAR(100),
    source_record_id INTEGER,
    patient_id VARCHAR(100),
    
    -- Dataset classification
    dataset_type VARCHAR(50) NOT NULL,
    
    -- FLEXIBLE: Raw and processed features
    raw_features JSONB,
    processed_features JSONB NOT NULL,
    
    -- Feature metadata
    feature_names JSONB,
    feature_vector JSONB,
    
    -- Labels (for supervised learning)
    label_name VARCHAR(100),
    label_value VARCHAR(100),
    label_encoded INTEGER,
    
    -- Versioning (CRITICAL for ML reproducibility)
    feature_version VARCHAR(20) NOT NULL,
    preprocessing_pipeline JSONB,
    feature_selection_method VARCHAR(100),
    
    -- Train/Test split
    dataset_split VARCHAR(20),
    split_strategy VARCHAR(50),
    split_seed INTEGER,
    
    -- Quality metrics
    data_quality_score INTEGER,
    missing_feature_count INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for ml_feature_store
CREATE INDEX IF NOT EXISTS idx_ml_patient ON ml_feature_store(patient_id);
CREATE INDEX IF NOT EXISTS idx_ml_dataset ON ml_feature_store(dataset_type, dataset_split);
CREATE INDEX IF NOT EXISTS idx_ml_version ON ml_feature_store(feature_version);
CREATE INDEX IF NOT EXISTS idx_ml_label ON ml_feature_store(label_value);
CREATE INDEX IF NOT EXISTS idx_ml_split ON ml_feature_store(dataset_split);
CREATE INDEX IF NOT EXISTS idx_ml_features ON ml_feature_store USING GIN (processed_features);

COMMENT ON TABLE ml_feature_store IS 'Versioned feature store for ML training with full lineage tracking';


-- ============================================================================
-- Model Predictions (Store classification results)
-- ============================================================================

CREATE TABLE IF NOT EXISTS model_predictions (
    prediction_id SERIAL PRIMARY KEY,
    
    -- Record identification
    record_id VARCHAR(100) NOT NULL,
    dataset_type VARCHAR(50),
    
    -- Model information
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    model_type VARCHAR(50),
    
    -- For ensemble models
    base_models JSONB,
    base_model_predictions JSONB,
    
    -- Predictions
    predicted_class VARCHAR(50) NOT NULL,
    probability_score INTEGER NOT NULL,
    
    -- All class probabilities
    all_class_probabilities JSONB,
    
    -- Input features snapshot
    input_features JSONB,
    feature_version VARCHAR(20),
    
    -- Explainability
    feature_importance JSONB,
    prediction_explanation TEXT,
    
    -- Confidence level
    prediction_confidence VARCHAR(20),
    
    -- Ground truth (if available)
    actual_class VARCHAR(50),
    is_correct BOOLEAN,
    
    -- Performance metrics
    inference_time_ms INTEGER,
    
    -- User feedback
    feedback_score INTEGER,
    feedback_notes TEXT,
    corrected_by INTEGER REFERENCES users(id),
    
    -- Timestamps
    prediction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    predicted_by INTEGER REFERENCES users(id)
);

-- Indexes for model_predictions
CREATE INDEX IF NOT EXISTS idx_pred_record ON model_predictions(record_id);
CREATE INDEX IF NOT EXISTS idx_pred_model ON model_predictions(model_name, model_version);
CREATE INDEX IF NOT EXISTS idx_pred_class ON model_predictions(predicted_class);
CREATE INDEX IF NOT EXISTS idx_pred_timestamp ON model_predictions(prediction_timestamp);

COMMENT ON TABLE model_predictions IS 'Store model predictions and probabilities for classification dashboard';


-- ============================================================================
-- STEP 2: Create Auto-Cleanup Function (for staging table)
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_expired_staging()
RETURNS void AS $$
BEGIN
    DELETE FROM import_preview_staging
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_staging IS 'Removes expired staging records (older than 24 hours)';


-- ============================================================================
-- STEP 3: Grant Permissions (if needed)
-- ============================================================================

-- Grant permissions to application user (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO usm_admin;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO usm_admin;


-- ============================================================================
-- STEP 4: Verification Queries
-- ============================================================================

-- Verify tables created
DO $$
BEGIN
    RAISE NOTICE 'Checking created tables...';
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'flexible_dataset_wide') THEN
        RAISE NOTICE '✓ flexible_dataset_wide created';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'import_preview_staging') THEN
        RAISE NOTICE '✓ import_preview_staging created';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ml_feature_store') THEN
        RAISE NOTICE '✓ ml_feature_store created';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'model_predictions') THEN
        RAISE NOTICE '✓ model_predictions created';
    END IF;
END $$;


-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Next steps:
-- 1. Run this migration: psql -U usm_admin -d autoimmune_db -f migration_flexible_schema.sql
-- 2. Implement preview/staging service
-- 3. Implement flexible import service
-- 4. Update API endpoints
-- 5. Test with sample CSV data
