-- =====================================================
-- Flexible Data Tables - Preview & Wide Storage
-- Date: April 10, 2026
-- For CSV upload, preview, and flexible data storage
-- =====================================================

-- =====================================================
-- STAGING TABLE: Import Preview
-- Temporary storage for CSV preview & editing
-- Auto-expires after 24 hours
-- =====================================================
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_staging_session ON import_preview_staging(session_id);
CREATE INDEX IF NOT EXISTS idx_staging_deleted ON import_preview_staging(is_deleted);
CREATE INDEX IF NOT EXISTS idx_staging_expires ON import_preview_staging(expires_at);

COMMENT ON TABLE import_preview_staging IS 'Temporary staging for CSV preview & editing - expires after 24 hours';
COMMENT ON COLUMN import_preview_staging.row_data IS 'Complete CSV row stored as JSONB - supports ANY schema';


-- =====================================================
-- MAIN TABLE: Flexible Dataset Wide
-- Universal wide table for ALL datasets
-- No hardcoded columns - everything in JSONB
-- =====================================================
CREATE TABLE IF NOT EXISTS flexible_dataset_wide (
    id SERIAL PRIMARY KEY,
    
    -- Record identifier
    record_id VARCHAR(100) NOT NULL,
    
    -- Dataset classification
    dataset_type VARCHAR(50) NOT NULL,
    dataset_name VARCHAR(100),
    dataset_version VARCHAR(20),
    
    -- FLEXIBLE: ALL data as JSONB
    data JSONB NOT NULL,
    
    -- Schema metadata
    schema_definition JSONB,
    
    -- Import source tracking
    dataset_source VARCHAR(100),
    import_batch_id UUID NOT NULL,
    import_method VARCHAR(50),
    
    -- Normalization tracking
    is_normalized BOOLEAN DEFAULT FALSE,
    normalized_at TIMESTAMP WITH TIME ZONE,
    normalized_by INTEGER REFERENCES users(id),
    
    -- Quality metrics
    data_quality_score INTEGER,
    missing_fields_count INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_flexible_dataset_type ON flexible_dataset_wide(dataset_type);
CREATE INDEX IF NOT EXISTS idx_flexible_record_id ON flexible_dataset_wide(record_id);
CREATE INDEX IF NOT EXISTS idx_flexible_batch ON flexible_dataset_wide(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_flexible_data_gin ON flexible_dataset_wide USING GIN(data);

COMMENT ON TABLE flexible_dataset_wide IS 'Universal flexible table for ALL datasets - supports any schema via JSONB';
COMMENT ON COLUMN flexible_dataset_wide.data IS 'All patient/sample data stored as JSONB - completely flexible schema';


-- =====================================================
-- SCHEMA REGISTRY TABLE
-- Track auto-detected schemas from CSV uploads
-- =====================================================
CREATE TABLE IF NOT EXISTS dataset_schema (
    schema_id SERIAL PRIMARY KEY,
    dataset_type VARCHAR(50) UNIQUE NOT NULL,
    dataset_name VARCHAR(100),
    
    -- Auto-detected schema definition
    schema_definition JSONB NOT NULL,
    
    -- Metadata
    created_by INTEGER REFERENCES users(id),
    last_import_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_schema_type ON dataset_schema(dataset_type);

COMMENT ON TABLE dataset_schema IS 'Registry of auto-detected schemas from CSV uploads';


-- =====================================================
-- CLEANUP FUNCTION
-- Auto-delete expired preview sessions
-- =====================================================
CREATE OR REPLACE FUNCTION cleanup_expired_previews()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM import_preview_staging
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_previews() IS 'Delete expired preview sessions (older than 24 hours)';


-- Optional: Schedule cleanup job (requires pg_cron extension)
-- Run every hour to clean up expired previews
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule('cleanup-previews', '0 * * * *', 'SELECT cleanup_expired_previews();');
