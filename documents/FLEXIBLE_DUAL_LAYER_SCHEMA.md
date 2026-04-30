# Flexible Dual-Layer Schema Architecture

## Core Principle: Preview First, Save Later

### Current Problem ❌
```
CSV Upload → IMMEDIATE transformation → Save to normalized tables
                ↓
            No preview, no user control
```

### New Architecture ✅
```
Upload → Preview (staging) → User edits → Save to wide table → Optional normalize
```

---

## Schema Structure

### Layer 1: Wide Tables (PRIMARY - Always Used)

```sql
-- Staging/Preview Table (temporary, editable)
CREATE TABLE import_preview_staging (
    staging_id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,  -- Links to user session
    dataset_type VARCHAR(50),   -- 'SLE', 'Sjogren', etc.
    
    -- Dynamic data (ANY CSV structure)
    row_data JSONB NOT NULL,
    -- Example:
    -- {
    --   "patient_id": "M98929",
    --   "age": 34,
    --   "gender": "Male",
    --   "ANA": 1.2,
    --   "Anti-dsDNA": 5.3,
    --   "C3": 0.9,
    --   ... any other columns
    -- }
    
    row_number INT,  -- Original row number in CSV
    
    -- User editing tracking
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    edit_history JSONB,  -- Track what changed
    
    -- Validation
    validation_status VARCHAR(20),  -- 'pending', 'valid', 'invalid'
    validation_errors JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP  -- Auto-delete after 24 hours
);

CREATE INDEX idx_staging_session ON import_preview_staging(session_id);
CREATE INDEX idx_staging_deleted ON import_preview_staging(is_deleted);


-- Wide Tables (PERMANENT - After user saves)
-- One table per disease type for flexibility

CREATE TABLE sle_patients_wide (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) UNIQUE NOT NULL,  -- Hospital ID or anonymous
    
    -- Core demographics (common fields)
    age INT,
    gender VARCHAR(10),
    ethnicity VARCHAR(50),
    
    -- ALL lab results as JSONB (maximum flexibility)
    lab_results JSONB NOT NULL,
    -- Example:
    -- {
    --   "ANA": 1.2,
    --   "Anti-dsDNA": 5.3,
    --   "C3": 0.9,
    --   "C4": 0.7,
    --   "ESR": 45,
    --   "CRP": 8.2,
    --   "IL-6": 12.3,
    --   ... ANY lab results
    -- }
    
    -- Clinical data (flexible)
    clinical_data JSONB,
    -- Example:
    -- {
    --   "diagnosis_date": "2023-05-15",
    --   "disease_duration_years": 5,
    --   "SLEDAI_score": 12,
    --   "medications": ["Prednisone", "Hydroxychloroquine"]
    -- }
    
    -- Flexible extras
    additional_data JSONB,
    
    -- Import metadata
    dataset_source VARCHAR(100),
    import_batch_id UUID NOT NULL,
    import_method VARCHAR(50),  -- 'csv_upload', 'ocr_processed', 'manual_entry'
    
    -- Normalization tracking
    is_normalized BOOLEAN DEFAULT FALSE,  -- Has user normalized this?
    normalized_at TIMESTAMP,
    normalized_by INT,  -- User ID
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX idx_sle_wide_patient ON sle_patients_wide(patient_id);
CREATE INDEX idx_sle_wide_batch ON sle_patients_wide(import_batch_id);
CREATE INDEX idx_sle_wide_normalized ON sle_patients_wide(is_normalized);
CREATE INDEX idx_sle_wide_labs ON sle_patients_wide USING GIN (lab_results);
CREATE INDEX idx_sle_wide_clinical ON sle_patients_wide USING GIN (clinical_data);


-- Unstructured Data (OCR Results)
CREATE TABLE unstructured_processed_wide (
    id SERIAL PRIMARY KEY,
    document_id INT REFERENCES unstructured_documents(document_id),
    
    patient_id VARCHAR(50),  -- Extracted from document
    
    -- OCR extracted data (structured format)
    extracted_data JSONB NOT NULL,
    -- Example:
    -- {
    --   "demographics": {"age": 45, "gender": "Female"},
    --   "diagnoses": ["SLE", "Lupus Nephritis"],
    --   "symptoms": ["fatigue", "joint pain"],
    --   "lab_results": {"ANA": "1:320", "Anti-dsDNA": "Positive"},
    --   "medications": ["Prednisone 20mg"]
    -- }
    
    confidence_scores JSONB,  -- Per-field confidence
    
    -- User verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by INT,
    verification_date TIMESTAMP,
    
    -- Normalization tracking
    is_normalized BOOLEAN DEFAULT FALSE,
    
    import_batch_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_unstructured_wide_batch ON unstructured_processed_wide(import_batch_id);
CREATE INDEX idx_unstructured_wide_verified ON unstructured_processed_wide(is_verified);
```

---

### Layer 2: Normalized Tables (OPTIONAL - User Triggered)

```sql
-- Traditional normalized schema (YOUR CURRENT TABLES)
-- Used ONLY when user explicitly normalizes a dataset

CREATE TABLE patients_normalized (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) UNIQUE NOT NULL,
    source_wide_table VARCHAR(100),  -- Links back to wide table
    source_record_id INT,  -- FK to wide table
    
    -- Demographics
    age INT,
    gender VARCHAR(10),
    ethnicity VARCHAR(50),
    
    -- Metadata
    normalized_from_batch UUID,
    normalized_at TIMESTAMP DEFAULT NOW(),
    normalized_by INT
);


CREATE TABLE lab_results_normalized (
    result_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) REFERENCES patients_normalized(patient_id),
    
    test_code VARCHAR(50),
    test_name VARCHAR(200),
    value_numeric NUMERIC(15,4),
    value_text TEXT,
    unit VARCHAR(50),
    
    test_date DATE,
    
    -- Link to source
    source_wide_table VARCHAR(100),
    source_record_id INT,
    
    created_at TIMESTAMP DEFAULT NOW()
);


CREATE TABLE diagnoses_normalized (
    diagnosis_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) REFERENCES patients_normalized(patient_id),
    
    disease_code VARCHAR(20),
    disease_name VARCHAR(200),
    diagnosis_date DATE,
    severity VARCHAR(20),
    
    -- Link to source
    source_wide_table VARCHAR(100),
    source_record_id INT,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## User Workflow

### Structured Data (CSV)

```javascript
// Step 1: Upload CSV
POST /api/v1/preview/upload-csv
→ Returns session_id
→ Data stored in import_preview_staging

// Step 2: User previews & edits
GET /api/v1/preview/{session_id}
→ Shows editable table
→ User can:
  - Delete rows (set is_deleted = true)
  - Edit cells (update row_data JSONB)
  - Fill missing values
  - Flag invalid rows

// Step 3: User saves to wide table
POST /api/v1/preview/{session_id}/save
→ Moves data from staging → sle_patients_wide
→ Clears staging (expires after 24h anyway)

// Step 4: OPTIONAL - User normalizes
POST /api/v1/normalize/batch/{batch_id}
→ Transforms wide data → normalized tables
→ Sets is_normalized = true on wide table
→ Both layers now available
```

### Unstructured Data (OCR)

```javascript
// Step 1: Upload file
POST /api/v1/unstructured/upload
→ Saves to MinIO
→ Returns document_id

// Step 2: OCR processing (background)
→ Extracts text + entities
→ Converts to structured format
→ Saves to import_preview_staging

// Step 3: User previews OCR results
GET /api/v1/unstructured/{document_id}/preview
→ Shows extracted data as editable table
→ User can correct OCR errors

// Step 4: User saves
POST /api/v1/unstructured/{document_id}/save
→ Moves to unstructured_processed_wide

// Step 5: OPTIONAL - Normalize
POST /api/v1/normalize/unstructured/{batch_id}
```

---

## Querying Examples

### Fast ML Queries (Wide Tables)
```sql
-- Get all patients with lab results (NO JOINS!)
SELECT 
    patient_id,
    age,
    gender,
    lab_results->>'ANA' as ana,
    lab_results->>'Anti-dsDNA' as anti_dsdna,
    lab_results->>'C3' as c3,
    lab_results->>'ESR' as esr
FROM sle_patients_wide
WHERE import_batch_id = 'xxx';

-- Extract all lab columns dynamically
SELECT 
    patient_id,
    jsonb_each_text(lab_results)  -- Expands JSONB to rows
FROM sle_patients_wide;
```

### Clinical Queries (Normalized - if user normalized)
```sql
-- Time-series lab trends (only if normalized)
SELECT 
    p.patient_id,
    l.test_code,
    l.value_numeric,
    l.test_date
FROM patients_normalized p
JOIN lab_results_normalized l ON p.patient_id = l.patient_id
WHERE l.test_code = 'ESR'
ORDER BY p.patient_id, l.test_date;
```

---

## Benefits of This Approach

✅ **Flexibility**
- Wide tables accept ANY CSV structure
- No predefined columns required
- Future-proof for new datasets

✅ **User Control**
- Preview before saving
- Edit/delete/fill at preprocessing stage
- Choose when to normalize

✅ **Performance**
- Fast ML queries (wide format)
- Optional normalized for clinical queries
- Both layers coexist

✅ **No Data Loss**
- Original data preserved in wide table
- Normalized tables are derived copies
- Can always re-normalize differently

✅ **Compliance**
- Audit trail (edit_history, normalized_by)
- Data lineage (source_wide_table links)
- Version control (import_batch_id)

---

## Migration Path

### Keep Your Current Tables
```sql
-- Your existing tables become "normalized layer"
-- Rename for clarity:
ALTER TABLE patients RENAME TO patients_normalized_legacy;
ALTER TABLE lab_results_flexible RENAME TO lab_results_normalized_legacy;

-- Reference: Keep as fallback or archive
```

### Add New Wide Tables
```sql
-- Implement new schema alongside existing
-- Dual-mode import:
--   Mode 1: Direct to wide table (new default)
--   Mode 2: To normalized (legacy support)
```

---

## API Endpoints Needed

### Preview & Preprocessing
```
POST   /api/v1/preview/upload          # Upload to staging
GET    /api/v1/preview/{session_id}    # Get preview data
PATCH  /api/v1/preview/{session_id}/row/{row_id}  # Edit row
DELETE /api/v1/preview/{session_id}/row/{row_id}  # Delete row
POST   /api/v1/preview/{session_id}/fill-missing  # Auto-fill
POST   /api/v1/preview/{session_id}/save          # Save to wide table
```

### Normalization (Optional)
```
POST   /api/v1/normalize/batch/{batch_id}  # Normalize entire batch
GET    /api/v1/normalize/status/{batch_id} # Check status
DELETE /api/v1/normalize/batch/{batch_id}  # Remove normalized version
```

### Querying
```
GET    /api/v1/patients/wide/{batch_id}       # Wide format (ML-ready)
GET    /api/v1/patients/normalized/{batch_id} # Normalized (if exists)
```

---

## Summary

### What Changes:
1. ❌ Remove immediate transformation (BatchImporter complexity)
2. ✅ Add staging table for preview
3. ✅ Add wide tables (JSONB-based, flexible)
4. ✅ Keep normalized tables as optional layer
5. ✅ Add user-triggered normalization

### What You Get:
- ✅ Preview before save (your requirement)
- ✅ User control at preprocessing (your requirement)
- ✅ No hardcoded schema (your requirement)
- ✅ Future-ready flexibility (your requirement)
- ✅ Optional normalization (user decides)
- ✅ Fast ML queries (wide format)
- ✅ Clinical queries available (if normalized)

**This is the flexible, future-ready architecture your proposal needs.**
