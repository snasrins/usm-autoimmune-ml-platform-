# 📋 SPRINT 1 - DATABASE & DATA INGESTION PLANNING

**Date:** March 13, 2026  
**Project:** USM Autoimmune ML Platform  
**Focus:** Autoimmune Disease Registry Database Design

---

## 📊 DATASET ANALYSIS SUMMARY

### Real Data Overview (AAM-SLE-E Dataset)
- **Total Patients:** 110 rows
- **Total Fields:** 61 columns
- **Primary Disease:** SLE (Systemic Lupus Erythematosus)
- **Related Conditions:** Lupus Nephritis (LN), Secondary Sjögren's Syndrome, RA, ILD, APS

### Data Categories

#### 1. **Patient Demographics** (6 columns)
- Hospitalization number (Patient ID)
- Age
- Gender (Yellow labels = male, very few)
- AAM (Menarche status: 0=No, 1=Yes)
- The first diagnosis
- Contact information

#### 2. **Blood Tests - Complete Blood Count** (5 columns)
- WBC: White Blood Cells (3.5-9.5×10^9/L)
- NEU%: Neutrophils percentage (50-70%)
- LYM%: Lymphocytes percentage (20-40%)
- HGB: Hemoglobin (115-150 g/L)
- PLT: Platelets (125-350×10^9/L)

#### 3. **Inflammation Markers** (4 columns)
- CRP: C-Reactive Protein (0-10 mg/L)
- ESR: Erythrocyte Sedimentation Rate (0-20 mm/h)
- ALB: Albumin (40-55 g/L)
- GLO: Globulin (20-40 g/L)

#### 4. **Kidney Function Tests** (4 columns)
- Urinary protein (qualitative: +, ++, +++, etc.)
- Urine protein quantification
- ACR: Albumin-to-Creatinine Ratio
- 24-hour urine protein quantification

#### 5. **Immune Cell Panel** (5 columns)
- CD3 (60-75.4%)
- CD4 (29.4-45.8%)
- CD8 (18.2-32.8%)
- NK: Natural Killer cells (8-26%)
- CD19 (9-14.1%)

#### 6. **Complement System** (2 columns)
- C3 (0.7-1.4 g/L)
- C4 (0.1-0.4 g/L)

#### 7. **Immunoglobulins** (4 columns)
- IgG (8.6-17.4 g/L)
- IgM (0.46-3.04 g/L)
- IgE (0-165 IU/ml)
- IgA (1.0-4.2 g/L)

#### 8. **Disease Activity Score** (1 column)
- SLEDAI: SLE Disease Activity Index
  - Mild: 0-6
  - Moderate: 7-12
  - Severe: >12

#### 9. **Autoantibodies - Primary Set** (11 columns)
- ANA: Anti-Nuclear Antibody
- nRNP/Sm
- SM: Anti-Smith
- SSA: Sjögren's-syndrome-related antigen A
- RO-52
- SSB: Sjögren's-syndrome-related antigen B
- Scl70: Anti-Scl-70
- Jo1: Anti-Jo-1
- CENPB: Anti-Centromere B
- dsDNA: Anti-double-stranded DNA
- Nucleosome

#### 10. **Autoantibodies - Secondary Set** (11 columns)
- Histone
- Ribosomal P protein
- ANA.1 (duplicate test)
- dsDNA.1 (duplicate test)
- SM.1 (duplicate test)
- SSA.1 (duplicate test)
- SSB (duplicate test)
- RNP70
- JO-1 (duplicate test)
- Scl-70 (duplicate test)
- AMA-2: Anti-Mitochondrial Antibody

#### 11. **Antiphospholipid Antibodies** (3 columns)
- Anti-β2 glycoprotein Ig(GAM) (0-20 AU/ml)
- Anticardiolipin antibody IgG (0-10 GPLU/ml)
- Anticardiolipin anti-antibody IgM (0-10 MPLU/ml)

#### 12. **ANCA Panel** (3 columns)
- PR3: Proteinase 3 (0-15 AU/ml)
- GBM: Anti-Glomerular Basement Membrane (0-10 AU/ml)
- MPO: Myeloperoxidase (0-15 AU/ml)

#### 13. **Vitamins** (1 column)
- 25-OH VitD: Vitamin D (20-80 ng/ml)

### Data Quality Issues Identified

1. **High Missing Data (>50%)**
   - CENPB: 90% missing
   - Jo1: 86.36% missing
   - Scl70: 82.73% missing
   - SSB: 75.45% missing
   - Histone: 70% missing
   - Contact information: 64.55% missing

2. **Duplicate Columns**
   - ANA appears twice (ANA, ANA.1)
   - dsDNA appears twice (dsDNA, dsDNA.1)
   - SM appears twice (SM, SM.1)
   - SSA appears twice (SSA, SSA.1)
   - SSB appears twice
   - JO-1 appears twice (Jo1, JO-1)
   - Scl-70 appears twice (Scl70, Scl-70)

3. **Inconsistent Data Formats**
   - Diagnosis field contains free text with multiple conditions
   - Qualitative results mixed with quantitative (e.g., urinary protein: +, ++, +++, 3+)
   - Gender has "Yellow labels indicate male" as a value (should be cleaned)

---

## 🗄️ DATABASE SCHEMA DESIGN

### Core Tables

#### **1. patients**
```sql
CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    hospital_number VARCHAR(50) UNIQUE,  -- Anonymized hospital ID
    anonymous_id VARCHAR(50) UNIQUE NOT NULL,  -- Our generated anonymous ID
    age INTEGER,
    gender VARCHAR(10),  -- Male, Female
    menarche_status BOOLEAN,  -- AAM field
    first_diagnosis_date DATE,
    contact_encrypted TEXT,  -- Encrypted contact info
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Data quality
    data_source VARCHAR(100),  -- e.g., "AAM-SLE-E Dataset"
    import_batch_id UUID,
    
    INDEX idx_anonymous_id (anonymous_id),
    INDEX idx_hospital_number (hospital_number)
);
```

#### **2. diagnoses**
```sql
CREATE TABLE diagnoses (
    diagnosis_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
    disease_code VARCHAR(20),  -- ICD-10 code
    disease_name VARCHAR(200) NOT NULL,  -- SLE, LN, RA, etc.
    diagnosis_date DATE,
    is_primary BOOLEAN DEFAULT FALSE,
    severity VARCHAR(20),  -- Mild, Moderate, Severe
    notes TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    
    INDEX idx_patient_id (patient_id),
    INDEX idx_disease_name (disease_name)
);
```

#### **3. lab_results_blood**
```sql
CREATE TABLE lab_results_blood (
    lab_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
    test_date DATE NOT NULL,
    
    -- Complete Blood Count
    wbc DECIMAL(5,2),  -- White Blood Cells
    neu_percent DECIMAL(5,2),  -- Neutrophils %
    lym_percent DECIMAL(5,2),  -- Lymphocytes %
    hgb DECIMAL(5,2),  -- Hemoglobin
    plt DECIMAL(6,2),  -- Platelets
    
    -- Inflammation Markers
    crp DECIMAL(6,2),  -- C-Reactive Protein
    esr DECIMAL(5,1),  -- ESR
    alb DECIMAL(5,2),  -- Albumin
    glo DECIMAL(5,2),  -- Globulin
    
    -- Reference ranges stored as JSONB
    reference_ranges JSONB,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INTEGER REFERENCES users(id),
    
    INDEX idx_patient_test_date (patient_id, test_date)
);
```

#### **4. lab_results_kidney**
```sql
CREATE TABLE lab_results_kidney (
    kidney_lab_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
    test_date DATE NOT NULL,
    
    -- Urine Tests
    urinary_protein_qualitative VARCHAR(10),  -- +, ++, +++, 3+, etc.
    urinary_protein_quantitative DECIMAL(10,2),
    acr DECIMAL(10,2),  -- Albumin-to-Creatinine Ratio
    urine_protein_24h DECIMAL(10,2),
    
    -- Units
    acr_unit VARCHAR(20) DEFAULT 'mg/mmol',
    protein_24h_unit VARCHAR(20) DEFAULT 'g/24h',
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INTEGER REFERENCES users(id),
    
    INDEX idx_patient_test_date (patient_id, test_date)
);
```

#### **5. lab_results_immune_cells**
```sql
CREATE TABLE lab_results_immune_cells (
    immune_lab_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
    test_date DATE NOT NULL,
    
    -- T-Cell Panel
    cd3_percent DECIMAL(5,2),
    cd4_percent DECIMAL(5,2),
    cd8_percent DECIMAL(5,2),
    nk_percent DECIMAL(5,2),
    cd19_percent DECIMAL(5,2),
    
    -- Complement System
    c3_level DECIMAL(5,3),  -- g/L
    c4_level DECIMAL(5,3),  -- g/L
    
    -- Immunoglobulins
    igg_level DECIMAL(6,2),  -- g/L
    igm_level DECIMAL(6,3),  -- g/L
    ige_level DECIMAL(8,2),  -- IU/ml
    iga_level DECIMAL(5,2),  -- g/L
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INTEGER REFERENCES users(id),
    
    INDEX idx_patient_test_date (patient_id, test_date)
);
```

#### **6. lab_results_autoantibodies**
```sql
CREATE TABLE lab_results_autoantibodies (
    autoantibody_lab_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
    test_date DATE NOT NULL,
    
    -- Primary Autoantibodies
    ana VARCHAR(50),  -- Can be qualitative (+/-) or titer (1:160)
    ana_pattern VARCHAR(100),  -- Homogeneous, Speckled, etc.
    ds_dna VARCHAR(50),
    sm VARCHAR(50),
    ssa VARCHAR(50),
    ro_52 VARCHAR(50),
    ssb VARCHAR(50),
    scl70 VARCHAR(50),
    jo1 VARCHAR(50),
    cenpb VARCHAR(50),
    nucleosome VARCHAR(50),
    histone VARCHAR(50),
    ribosomal_p VARCHAR(50),
    rnp70 VARCHAR(50),
    ama_2 VARCHAR(50),
    
    -- Antiphospholipid Antibodies
    anti_beta2_gp DECIMAL(8,2),  -- AU/ml
    anticardiolipin_igg DECIMAL(8,2),  -- GPLU/ml
    anticardiolipin_igm DECIMAL(8,2),  -- MPLU/ml
    
    -- ANCA Panel
    pr3 DECIMAL(8,2),  -- AU/ml
    mpo DECIMAL(8,2),  -- AU/ml
    gbm DECIMAL(8,2),  -- AU/ml
    
    -- Stored as JSONB for flexibility
    raw_results JSONB,  -- Store original values
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INTEGER REFERENCES users(id),
    
    INDEX idx_patient_test_date (patient_id, test_date)
);
```

#### **7. disease_activity_scores**
```sql
CREATE TABLE disease_activity_scores (
    score_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
    assessment_date DATE NOT NULL,
    
    -- SLE-specific
    sledai_score INTEGER,  -- 0-105
    sledai_category VARCHAR(20),  -- Mild, Moderate, Severe
    
    -- Other scoring systems (future)
    das28_score DECIMAL(4,2),  -- For RA
    essdai_score INTEGER,  -- For Sjögren's
    
    -- Clinical notes
    assessed_by INTEGER REFERENCES users(id),
    clinical_notes TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_patient_assessment (patient_id, assessment_date)
);
```

#### **8. vitamins_minerals**
```sql
CREATE TABLE vitamins_minerals (
    vitamin_lab_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
    test_date DATE NOT NULL,
    
    -- Vitamins
    vitamin_d_25oh DECIMAL(6,2),  -- ng/ml
    vitamin_b12 DECIMAL(8,2),
    folate DECIMAL(6,2),
    
    -- Minerals
    calcium DECIMAL(5,2),
    iron DECIMAL(6,2),
    ferritin DECIMAL(8,2),
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INTEGER REFERENCES users(id),
    
    INDEX idx_patient_test_date (patient_id, test_date)
);
```

#### **9. uploaded_files**
```sql
CREATE TABLE uploaded_files (
    file_id SERIAL PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,  -- UUID-based name
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_type VARCHAR(50) NOT NULL,  -- CSV, XLSX, PDF, DICOM
    mime_type VARCHAR(100),
    
    -- Encryption
    is_encrypted BOOLEAN DEFAULT TRUE,
    encryption_key_id VARCHAR(100),
    
    -- File metadata
    file_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash
    row_count INTEGER,  -- For CSV/Excel
    column_count INTEGER,
    
    -- Status
    upload_status VARCHAR(20) DEFAULT 'pending',  -- pending, validated, processed, failed
    validation_errors JSONB,
    processing_errors JSONB,
    
    -- Audit
    uploaded_by INTEGER REFERENCES users(id) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    
    INDEX idx_upload_status (upload_status),
    INDEX idx_uploaded_by (uploaded_by)
);
```

#### **10. data_ingestion_audit**
```sql
CREATE TABLE data_ingestion_audit (
    audit_id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES uploaded_files(file_id),
    batch_id UUID NOT NULL,
    
    -- Action details
    action_type VARCHAR(50) NOT NULL,  -- upload, validate, transform, load, delete
    action_status VARCHAR(20) NOT NULL,  -- success, failed, warning
    
    -- Data affected
    table_name VARCHAR(100),
    records_affected INTEGER DEFAULT 0,
    patients_affected INTEGER DEFAULT 0,
    
    -- Error tracking
    error_message TEXT,
    error_details JSONB,
    
    -- Performance
    execution_time_ms INTEGER,
    
    -- User context
    performed_by INTEGER REFERENCES users(id) NOT NULL,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    INDEX idx_batch_id (batch_id),
    INDEX idx_action_type (action_type),
    INDEX idx_performed_at (performed_at)
);
```

#### **11. anonymization_log**
```sql
CREATE TABLE anonymization_log (
    anon_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
    
    -- Original data (hashed)
    original_identifier_hash VARCHAR(64) NOT NULL,  -- SHA-256 of original ID
    original_name_hash VARCHAR(64),  -- SHA-256 of name (if exists)
    
    -- Anonymized data
    anonymous_id VARCHAR(50) NOT NULL,  -- Our generated ID
    anonymization_method VARCHAR(100),  -- e.g., "UUID-v4", "Sequential", "Hash-based"
    
    -- PII removed
    pii_fields_removed JSONB,  -- List of fields anonymized
    
    -- Audit
    anonymized_by INTEGER REFERENCES users(id) NOT NULL,
    anonymized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- De-anonymization control
    can_be_reversed BOOLEAN DEFAULT FALSE,
    deidentification_key_id VARCHAR(100),  -- Reference to encryption key (if reversible)
    
    INDEX idx_original_hash (original_identifier_hash),
    INDEX idx_anonymous_id (anonymous_id)
);
```

---

## 🔧 TASKS BREAKDOWN - SPRINT 1

### Task 1: Database Schema Implementation
**JIRA:** USMA-16 (Autoimmune Disease Registry Database)

**Subtasks:**
- [ ] Create database migration script for all 11 tables
- [ ] Add foreign key constraints and indexes
- [ ] Create database views for common queries
- [ ] Add CHECK constraints for data validation
- [ ] Create trigger functions for updated_at timestamps
- [ ] Test schema with sample data

**Deliverable:** `app/db/migrations/001_create_autoimmune_registry_schema.py`

---

### Task 2: File Validation Pipeline
**JIRA:** USMA-19 (Implement File Validation Pipeline)

**Validation Rules:**
1. **File Type Validation**
   - Allowed: .xlsx, .xls, .csv, .pdf (medical reports), .dcm (DICOM images)
   - Max size: 100MB per file
   - Reject executable files, scripts

2. **Data Format Validation**
   - Required columns must be present
   - Date formats: YYYY-MM-DD or DD/MM/YYYY
   - Numeric ranges validated against reference ranges
   - Qualitative results checked against allowed values

3. **Data Quality Checks**
   - Duplicate patient records detection
   - Missing critical fields flagged
   - Outlier detection for lab values
   - Date consistency checks (e.g., test_date not in future)

4. **Security Validation**
   - Virus/malware scan
   - File hash generation
   - Check for SQL injection patterns in text fields
   - Validate file integrity

**Deliverable:** `app/services/file_validation.py`

---

### Task 3: Secure Data Upload Interface (API)
**JIRA:** USMA-17 (Develop Secure Data Upload Interface)

**API Endpoints:**
```python
POST /api/v1/upload/file
- Upload single file (Excel/CSV)
- Returns: file_id, validation_status

POST /api/v1/upload/batch
- Upload multiple files
- Returns: batch_id, file_list with statuses

GET /api/v1/upload/{file_id}/status
- Check upload and validation status

GET /api/v1/upload/{file_id}/validation-report
- Get detailed validation results

DELETE /api/v1/upload/{file_id}
- Delete uploaded file (soft delete)
```

**Security Features:**
- File encryption at rest
- Temporary upload directory with restrictive permissions
- Rate limiting (max 10 uploads per hour per user)
- Role-based access (only admin and researcher can upload)

**Deliverable:** `app/api/endpoints/upload.py`

---

### Task 4: Patient Data Anonymization
**JIRA:** USMA-16.1 (Implement Patient Data Anonymization)

**Anonymization Strategy:**

1. **Identifier Anonymization**
   - Hospital Number → Anonymous UUID (e.g., "USMA-2026-0001")
   - Name → Completely removed
   - IC/Passport → Hashed (SHA-256) + removed from display

2. **Quasi-Identifiers**
   - Age → Age ranges (20-29, 30-39, etc.) for analysis
   - Gender → Keep (necessary for research)
   - Date of birth → Remove, keep only age
   - Contact info → Encrypted, only accessible by admin

3. **Date Shifting**
   - All dates shifted by random offset (-90 to +90 days)
   - Offset consistent per patient to maintain time relationships
   - Original dates encrypted and stored separately

4. **Free Text Sanitization**
   - Scan diagnosis notes for names, addresses
   - Redact using regex patterns
   - Flag for manual review if uncertain

**Deliverable:** `app/services/anonymization.py`

---

### Task 5: Data Ingestion Audit Trail
**JIRA:** USMA-19.1 (Implement Data Ingestion Audit Trail)

**Audit Events:**
- File upload initiated
- File validation started/completed
- Patient anonymization performed
- Data transformation applied
- Records inserted/updated/deleted
- Errors encountered
- User actions (who, when, what)

**Audit Interface:**
```python
GET /api/v1/audit/logs
- List all audit logs (paginated)
- Filters: user, date_range, action_type, status

GET /api/v1/audit/batch/{batch_id}
- Get all logs for a specific import batch

GET /api/v1/audit/patient/{patient_id}/history
- Get complete audit trail for a patient's data

GET /api/v1/audit/stats
- Summary statistics (uploads per day, errors, etc.)
```

**Deliverable:** `app/api/endpoints/audit.py`

---

### Task 6: Dataset Preview Interface
**JIRA:** USMA-18 (Implement Dataset Preview Interface)

**Preview Features:**
1. **File Preview (Before Import)**
   - Show first 10 rows
   - Display column headers and data types
   - Show detected patient count
   - Highlight validation warnings

2. **Patient Data Preview**
   - List patients with basic info (anonymous ID, age, gender, diagnosis)
   - Filter by disease, date range
   - Search by anonymous ID
   - Show latest lab results summary

3. **Lab Results Preview**
   - Display in tabular format
   - Color-code abnormal values (red=high, blue=low)
   - Show reference ranges
   - Plot trends over time

**API Endpoints:**
```python
POST /api/v1/preview/file
- Upload file for preview only (not stored)
- Returns: column_info, sample_rows, validation_warnings

GET /api/v1/patients/preview
- List patients (paginated, filtered)

GET /api/v1/patients/{patient_id}/labs/latest
- Get latest lab results for all test types

GET /api/v1/patients/{patient_id}/labs/trends
- Get time series data for plotting
```

**Deliverable:** `app/api/endpoints/preview.py`

---

## 📅 IMPLEMENTATION TIMELINE

### Week 1 (March 13-15)
- **Day 1 (Today):** Planning complete ✓
- **Day 2:** Database schema + migrations
- **Day 3:** File validation pipeline + tests

### Week 2 (March 16-19)
- **Day 4:** Upload API implementation
- **Day 5:** Anonymization service
- **Day 6:** Audit trail implementation
- **Day 7:** Dataset preview interface

### Week 3 (March 20-22)
- **Day 8-9:** Integration testing
- **Day 10:** Documentation + Sprint review

---

## 🧪 TESTING STRATEGY

### Unit Tests
- Each validation rule tested independently
- Anonymization functions with sample PII
- Database constraints validation

### Integration Tests
- End-to-end file upload → validation → anonymization → storage
- Audit log generation for each action
- API authentication and authorization

### Test Data
- Use sample from AAM-SLE-E dataset (create test subset with 10 patients)
- Create synthetic patients with edge cases
- Test with intentionally malformed files

---

## 📝 NOTES

### Data Privacy Compliance
- Ensure PDPA (Malaysia) compliance
- HIPAA-like standards for medical data
- Right to be forgotten implementation plan

### Performance Considerations
- Batch inserts for large datasets (use COPY command)
- Index strategy for fast patient lookups
- File processing queue for large uploads

### Future Enhancements (Sprint 2+)
- DICOM image storage and viewer
- PDF report parsing (OCR)
- Multi-language support (Malay, Chinese)
- Data export functionality
- Advanced search with Elasticsearch

---

**Status:** ✅ Ready to implement  
**Next Action:** Create database migration scripts

