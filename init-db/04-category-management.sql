-- =====================================================
-- Category Management System - ZERO Hardcoding
-- Dynamic lookup tables for diagnosis categorization
-- =====================================================

-- =====================================================
-- LOOKUP TABLE: Disease Categories
-- Admins can add/edit categories without code changes
-- =====================================================
CREATE TABLE IF NOT EXISTS dim_disease_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,  -- "SLE_with_LN", "SLE_uncomplicated", etc.
    category_code VARCHAR(50) UNIQUE,  -- "sle_ln", "sle_uncomp" (for APIs)
    category_label VARCHAR(200),  -- "SLE with Lupus Nephritis" (display name)
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INTEGER
);

CREATE INDEX idx_disease_cat_active ON dim_disease_categories(is_active);
CREATE INDEX idx_disease_cat_code ON dim_disease_categories(category_code);

COMMENT ON TABLE dim_disease_categories IS 'Lookup table for diagnosis categories - managed via admin API, NO hardcoding';

-- =====================================================
-- MAPPING TABLE: Diagnosis → Category
-- Maps diagnosis strings to categories dynamically
-- Supports pattern matching for flexibility
-- =====================================================
CREATE TABLE IF NOT EXISTS diagnosis_category_mappings (
    mapping_id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES dim_disease_categories(category_id) ON DELETE CASCADE,
    
    -- Pattern matching for diagnosis field
    diagnosis_pattern VARCHAR(200) NOT NULL,  -- "Systemic lupus erythematosus with lupus nephritis"
    match_type VARCHAR(20) DEFAULT 'exact',  -- 'exact', 'contains', 'starts_with', 'regex'
    
    -- Priority for overlapping patterns
    priority INTEGER DEFAULT 0,  -- Higher priority wins if multiple matches
    
    -- Conditional logic (optional)
    condition_field VARCHAR(100),  -- e.g., "renal_involvement"
    condition_value VARCHAR(100),  -- e.g., "Yes"
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INTEGER,
    
    UNIQUE(diagnosis_pattern, match_type)
);

CREATE INDEX idx_mapping_category ON diagnosis_category_mappings(category_id);
CREATE INDEX idx_mapping_active ON diagnosis_category_mappings(is_active);
CREATE INDEX idx_mapping_priority ON diagnosis_category_mappings(priority DESC);

COMMENT ON TABLE diagnosis_category_mappings IS 'Dynamic diagnosis→category mappings - NO hardcoding required';

-- =====================================================
-- SEED DATA (Initial SLE Categories - Can be modified via API)
-- IMPORTANT: These are EXAMPLES - modify via admin interface!
-- =====================================================

-- Insert categories
INSERT INTO dim_disease_categories (category_name, category_code, category_label, description) VALUES
('SLE_with_LN', 'sle_ln', 'SLE with Lupus Nephritis', 'Systemic Lupus Erythematosus with renal involvement'),
('SLE_uncomplicated', 'sle_uncomp', 'SLE Uncomplicated', 'Systemic Lupus Erythematosus without major organ involvement'),
('SLE_with_APL', 'sle_apl', 'SLE with Antiphospholipid Syndrome', 'SLE with antiphospholipid antibodies'),
('SLE_with_ILD', 'sle_ild', 'SLE with Interstitial Lung Disease', 'SLE with pulmonary fibrosis/ILD')
ON CONFLICT (category_name) DO NOTHING;

-- Insert mappings (pattern-based)
INSERT INTO diagnosis_category_mappings (category_id, diagnosis_pattern, match_type, priority) VALUES
-- Lupus Nephritis (highest priority - specific)
((SELECT category_id FROM dim_disease_categories WHERE category_code = 'sle_ln'), 
 'lupus nephritis', 'contains', 100),
((SELECT category_id FROM dim_disease_categories WHERE category_code = 'sle_ln'), 
 'with lupus nephritis', 'contains', 100),
((SELECT category_id FROM dim_disease_categories WHERE category_code = 'sle_ln'), 
 'renal involvement', 'contains', 90),

-- Antiphospholipid Syndrome
((SELECT category_id FROM dim_disease_categories WHERE category_code = 'sle_apl'), 
 'antiphospholipid syndrome', 'contains', 80),
((SELECT category_id FROM dim_disease_categories WHERE category_code = 'sle_apl'), 
 'APL syndrome', 'contains', 80),
((SELECT category_id FROM dim_disease_categories WHERE category_code = 'sle_apl'), 
 'APS', 'contains', 70),

-- Interstitial Lung Disease
((SELECT category_id FROM dim_disease_categories WHERE category_code = 'sle_ild'), 
 'interstitial lung disease', 'contains', 80),
((SELECT category_id FROM dim_disease_categories WHERE category_code = 'sle_ild'), 
 'pulmonary fibrosis', 'contains', 80),
((SELECT category_id FROM dim_disease_categories WHERE category_code = 'sle_ild'), 
 'ILD', 'contains', 70),

-- Uncomplicated SLE (lowest priority - catch-all)
((SELECT category_id FROM dim_disease_categories WHERE category_code = 'sle_uncomp'), 
 'Systemic lupus erythematosus', 'starts_with', 10),
((SELECT category_id FROM dim_disease_categories WHERE category_code = 'sle_uncomp'), 
 'SLE', 'exact', 10)
ON CONFLICT (diagnosis_pattern, match_type) DO NOTHING;

-- =====================================================
-- HELPER FUNCTION: Get category for a diagnosis
-- Usage: SELECT get_diagnosis_category('Systemic lupus erythematosus with lupus nephritis');
-- Returns: 'SLE_with_LN'
-- =====================================================
CREATE OR REPLACE FUNCTION get_diagnosis_category(diagnosis_text TEXT)
RETURNS TEXT AS $$
DECLARE
    matched_category TEXT;
BEGIN
    -- Find best matching category (highest priority)
    SELECT 
        dc.category_name
    INTO matched_category
    FROM diagnosis_category_mappings dcm
    JOIN dim_disease_categories dc ON dcm.category_id = dc.category_id
    WHERE 
        dcm.is_active = TRUE 
        AND dc.is_active = TRUE
        AND (
            -- Match type handling
            (dcm.match_type = 'exact' AND LOWER(diagnosis_text) = LOWER(dcm.diagnosis_pattern))
            OR (dcm.match_type = 'contains' AND LOWER(diagnosis_text) LIKE '%' || LOWER(dcm.diagnosis_pattern) || '%')
            OR (dcm.match_type = 'starts_with' AND LOWER(diagnosis_text) LIKE LOWER(dcm.diagnosis_pattern) || '%')
            OR (dcm.match_type = 'regex' AND diagnosis_text ~* dcm.diagnosis_pattern)
        )
    ORDER BY dcm.priority DESC, dcm.created_at ASC
    LIMIT 1;
    
    RETURN COALESCE(matched_category, 'Unknown');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION get_diagnosis_category IS 'Dynamically maps diagnosis text to category using lookup tables';

-- =====================================================
-- EXAMPLE: Apply categorization to existing data
-- =====================================================
-- Uncomment to apply to flexible_dataset_wide table:
/*
UPDATE flexible_dataset_wide
SET data = jsonb_set(
    data, 
    '{clinical,diagnosis_category}', 
    to_jsonb(get_diagnosis_category(data->'clinical'->>'diagnosis'))
)
WHERE data->'clinical'->>'diagnosis' IS NOT NULL;
*/

-- =====================================================
-- AUDIT: Track category changes
-- =====================================================
CREATE TABLE IF NOT EXISTS category_audit_log (
    audit_id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,  -- 'dim_disease_categories' or 'diagnosis_category_mappings'
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
    old_data JSONB,
    new_data JSONB,
    changed_by INTEGER,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_table ON category_audit_log(table_name, record_id);
CREATE INDEX idx_audit_time ON category_audit_log(changed_at DESC);

COMMENT ON TABLE category_audit_log IS 'Audit trail for category management changes';
