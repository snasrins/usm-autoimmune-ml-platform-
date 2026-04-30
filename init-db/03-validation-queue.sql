-- ============================================
-- USM Autoimmune ML Platform - Validation Queue Table
-- For Unstructured Data Pipeline (OCR + NER)
-- Author: Syarifah Fajriyah
-- Date: April 3, 2026
-- ============================================

-- Create validation_queue table for human-in-the-loop workflow
CREATE TABLE IF NOT EXISTS validation_queue (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER DEFAULT NULL,
    stage VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending_review',
    assigned_to INTEGER DEFAULT NULL,
    reviewed_by INTEGER DEFAULT NULL,
    reviewed_at TIMESTAMP DEFAULT NULL,
    validation_data JSONB NOT NULL,
    rejection_reason TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_validation_status ON validation_queue(status);
CREATE INDEX IF NOT EXISTS idx_validation_stage ON validation_queue(stage);
CREATE INDEX IF NOT EXISTS idx_validation_assigned ON validation_queue(assigned_to);
CREATE INDEX IF NOT EXISTS idx_validation_created ON validation_queue(created_at DESC);

-- Comment
COMMENT ON TABLE validation_queue IS 'Human validation queue for unstructured data (OCR + NER results)';
COMMENT ON COLUMN validation_queue.validation_data IS 'JSONB containing document metadata, extracted text, and medical entities';
COMMENT ON COLUMN validation_queue.stage IS 'Pipeline stage: ocr_complete, ner_complete, validated, rejected';
COMMENT ON COLUMN validation_queue.status IS 'Review status: pending_review, in_review, approved, rejected';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Validation Queue Table Created';
    RAISE NOTICE 'Table: validation_queue';
    RAISE NOTICE 'Purpose: Human-in-the-loop validation for';
    RAISE NOTICE '         unstructured data (PDF/TXT OCR)';
    RAISE NOTICE '========================================';
END $$;
