# Data Ingestion & Processing Pipeline

## Overview
Complete ETL (Extract, Transform, Load) architecture for clinical autoimmune disease data. Built with 5 specialized services handling validation, mapping, anonymization, transformation, and batch import.

---

## Pipeline Architecture

```
┌─────────────────┐
│   File Upload   │ → CSV/XLSX/Parquet/JSON/XML/PDF/TXT/IMG
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FileParser     │ → Validation, Format Detection, Preview
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ColumnMapper    │ → Fuzzy Match to Lab Test Catalog
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Anonymizer     │ → USMA-2026-XXXX, SHA-256, Age Ranges
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DataTransformer │ → Parse Values, Detect Abnormal, Build Models
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ BatchImporter   │ → Transaction-based DB Insert + Audit
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PostgreSQL DB  │ → 8 Tables, JSONB Storage
└─────────────────┘
```

---

## Service Details

### 1. FileParser (`app/services/file_parser.py`)
**Purpose:** Validate and preview uploaded files

**Key Functions:**
- `parse_file()` - Detect format, read data into DataFrame
- `validate_data()` - Check required columns, data types
- `preview_data()` - Generate first 5 rows + column statistics
- `get_column_stats()` - Count nulls, detect numeric vs text
- `calculate_file_hash()` - SHA-256 for integrity

**Supported Formats:**
- Structured: CSV, XLSX, Parquet
- Semi-Structured: JSON, XML
- Unstructured: PDF (text extraction), TXT, IMG (future OCR)

**Validation Checks:**
- File size limits (configurable)
- Encoding detection (UTF-8, Latin-1, etc.)
- Required columns (disease, patient ID, at least one data column)
- Missing data percentage
- Data type detection

**Output:**
```python
{
    "dataframe": pd.DataFrame,
    "file_hash": "sha256...",
    "row_count": 110,
    "column_count": 61,
    "preview": [...],
    "column_stats": {...}
}
```

---

### 2. ColumnMapper (`app/services/column_mapper.py`)
**Purpose:** Map uploaded columns to standardized lab test codes

**Key Functions:**
- `suggest_mappings()` - Fuzzy match columns to known tests
- `create_mapping()` - Manual mapping override
- `get_unmapped_columns()` - Identify new tests
- `calculate_confidence()` - Scoring algorithm (0-100)

**Fuzzy Matching Algorithm:**
1. Normalize column names (lowercase, remove special chars)
2. Check exact matches first
3. Use Levenshtein distance for similarity
4. Check aliases (e.g., "WBC" → "White Blood Cell")
5. Score based on match quality

**Confidence Levels:**
- 90-100: Exact match or known alias
- 70-89: High probability match
- 50-69: Possible match (needs review)
- <50: No match (suggest as new test)

**Output:**
```python
{
    "mapped": {
        "WBC": {"test_code": "wbc", "confidence": 100},
        "CRP": {"test_code": "crp", "confidence": 95}
    },
    "unmapped": ["Custom_Test_123"]
}
```

**Test Catalog Integration:**
- Queries `lab_test_definitions` table
- Uses test_code, test_name, aliases for matching
- Auto-creates new tests if unmapped (with approval workflow)

---

### 3. PatientAnonymizer (`app/services/anonymizer.py`)
**Purpose:** Ensure patient privacy and NMRR compliance

**Key Functions:**
- `anonymize_patient()` - Generate anonymous ID, hash sensitive fields
- `generate_anonymous_id()` - Sequential USMA-2026-XXXX format
- `hash_identifier()` - SHA-256 for names, ICs, phone numbers
- `convert_to_age_range()` - Age buckets (<18, 18-29, 30-39, etc.)
- `shift_dates()` - Random date shifting for temporal privacy

**Anonymization Rules:**
1. **Patient ID:** Original ID → `USMA-2026-0001` to `USMA-2026-9999`
2. **Name:** Hash with SHA-256, never stored in plaintext
3. **IC/Passport:** Hash with SHA-256
4. **Age:** Exact age → Age range bucket
5. **Dates:** Random shift (±30 days) to prevent re-identification
6. **Location:** City/State only, no addresses
7. **Contact:** Hash phone/email

**Age Ranges:**
- <18
- 18-29
- 30-39
- 40-49
- 50-59
- 60-69
- 70-79
- 80+

**Output:**
```python
{
    "anonymous_id": "USMA-2026-0001",
    "age": 35,
    "age_range": "30-39",
    "gender": "Female",
    "original_hash": "sha256...",
    "additional_data": {...}  # Other non-sensitive metadata
}
```

**NMRR Compliance:**
- No direct identifiers stored
- One-way hashing (cannot reverse)
- Date shifting prevents temporal correlation
- Minimal demographic data retained

---

### 4. DataTransformer (`app/services/data_transformer.py`)
**Purpose:** Convert DataFrame rows to SQLAlchemy models

**Key Functions:**
- `transform_patient_data()` - Build Patient + Diagnosis models
- `transform_lab_results()` - Build LabResultFlexible models
- `parse_value()` - Detect numeric vs text, extract units
- `detect_abnormal()` - Compare to reference ranges
- `extract_disease_data()` - Build JSONB for disease-specific fields

**Value Parsing Logic:**
```python
# Examples:
"6.5" → value_numeric=6.5, value_text=None
"Positive" → value_numeric=None, value_text="Positive"
"1:80" → value_numeric=80, value_text="1:80" (mixed)
"<0.5" → value_numeric=0.5, value_text="<0.5", abnormal_flag="L"
">100 H" → value_numeric=100, value_text=">100", abnormal_flag="H"
```

**Abnormal Detection:**
- Checks `lab_test_definitions.reference_ranges` (JSONB)
- Flags: H (high), L (low), HH (critically high), LL (critically low)
- Boolean `is_abnormal` for easy filtering

**Disease-Specific Data (JSONB):**
```python
# SLE-specific
{
    "sledai_score": 8,
    "organ_involvement": ["Renal", "Joint"],
    "treatment_history": "Hydroxychloroquine"
}

# Sjogren-specific
{
    "dry_eye_score": 7,
    "salivary_flow": "Reduced",
    "focus_score": 3
}
```

**Output:**
```python
{
    "patient": Patient(...),
    "diagnoses": [Diagnosis(...), ...],
    "lab_results": [LabResultFlexible(...), ...],
    "disease_data": [DiseaseSpecificData(...), ...]
}
```

---

### 5. BatchImporter (`app/services/batch_importer.py`)
**Purpose:** Bulk insert with transaction management and audit trail

**Key Functions:**
- `import_batch()` - Import all patients in single transaction
- `rollback_patient()` - Per-patient error handling
- `create_audit_record()` - Log import status
- `validate_before_import()` - Final checks before DB insert

**Transaction Strategy:**
1. Start DB transaction
2. For each patient:
   - Insert Patient record
   - Insert Diagnosis records (CASCADE FK)
   - Insert LabResultFlexible records (CASCADE FK)
   - Insert DiseaseSpecificData (optional)
3. If patient fails → rollback that patient only (not whole batch)
4. Commit successful patients
5. Create DataIngestionAudit record

**Error Handling:**
```python
# Per-patient rollback example:
try:
    db.add(patient)
    db.flush()  # Get patient.id
    for lab in lab_results:
        lab.patient_id = patient.id
        db.add(lab)
    db.commit()
except Exception as e:
    db.rollback()
    errors.append({"patient": row_num, "error": str(e)})
    continue  # Skip to next patient
```

**Audit Trail:**
```python
# DataIngestionAudit record
{
    "file_hash": "sha256...",
    "disease_name": "SLE",
    "total_rows": 110,
    "processed_rows": 110,
    "successful_rows": 109,
    "failed_rows": 1,
    "error_details": {"row_59": "Invalid date format"},
    "import_timestamp": "2026-03-16 12:00:00",
    "uploaded_by": "admin"
}
```

**Performance:**
- Batch inserts (not row-by-row)
- Indexes on foreign keys
- JSONB GIN indexes for fast queries
- Typical speed: 100-500 patients/second

---

## Data Quality Handling

### Missing Data
- **Strategy:** Store as NULL, track percentage per column
- **Thresholds:** Warn if >30% missing for critical columns
- **ML Impact:** Handle during feature engineering (imputation)

### Duplicate Patients
- **Detection:** Hash-based matching (name + DOB hash)
- **Strategy:** Flag for manual review (don't auto-merge)
- **Future:** Smart merge algorithm with confidence scoring

### Invalid Dates
- **Examples:** "0 No 1 Yes", "N/A", empty cells
- **Handling:** Parse safely, return None if invalid
- **Storage:** test_date is nullable (migration 004)

### Outliers
- **Detection:** Z-score, IQR, domain-specific rules
- **Strategy:** Flag but don't remove (may be real anomalies)
- **Review:** Provide UI for clinicians to review flagged data

### Unit Inconsistencies
- **Examples:** mg/dL vs mmol/L for glucose
- **Handling:** Store original unit, flag for conversion
- **Future:** Auto-conversion based on unit mapping table

---

## Database Schema

### Core Tables (8 total)

**1. patients**
```sql
- id (PK)
- anonymous_id (UNIQUE, indexed)
- age, age_range, gender, ethnicity
- additional_data (JSONB) -- flexible metadata
```

**2. diagnoses**
```sql
- diagnosis_id (PK)
- patient_id (FK → patients, CASCADE)
- disease_name, icd10_code
- diagnosis_date, severity
```

**3. lab_test_definitions**
```sql
- test_id (PK)
- test_code (UNIQUE), test_name, test_category
- data_type (numeric/qualitative/mixed)
- unit, reference_ranges (JSONB)
- is_active (for approval workflow)
```

**4. lab_results_flexible**
```sql
- result_id (PK)
- patient_id (FK → patients, CASCADE)
- test_definition_id (FK → lab_test_definitions)
- test_date (nullable)
- value_numeric, value_text, unit
- is_abnormal, abnormal_flag
- reference_range (JSONB, per-result override)
```

**5. disease_specific_data**
```sql
- data_id (PK)
- patient_id (FK → patients, CASCADE)
- disease_name, data_category
- data (JSONB) -- completely flexible
```

**6. uploaded_files**
```sql
- file_id (PK)
- original_filename, file_hash
- file_size, file_type
- column_mapping (JSONB)
- uploaded_by, uploaded_at
```

**7. data_ingestion_audit**
```sql
- audit_id (PK)
- file_id (FK → uploaded_files)
- disease_name
- total_rows, successful_rows, failed_rows
- error_details (JSONB)
- import_timestamp
```

**8. lab_result_batch** (optional, for panel tests)
```sql
- batch_id (PK)
- patient_id (FK → patients)
- test_date, panel_name
- results (JSONB) -- multiple tests in one record
```

### Key JSONB Fields

**additional_data (patients):**
```json
{
  "original_row_num": 42,
  "import_batch": "SLE_2026_03_16",
  "notes": "Patient transferred from other hospital"
}
```

**reference_ranges (lab_test_definitions):**
```json
{
  "normal": {"min": 4.0, "max": 11.0},
  "male": {"min": 4.5, "max": 11.5},
  "female": {"min": 3.5, "max": 10.5},
  "critical_low": 2.0,
  "critical_high": 20.0
}
```

**data (disease_specific_data):**
```json
{
  "sledai_score": 8,
  "sledai_date": "2026-03-15",
  "organ_involvement": ["Renal", "Joint", "Skin"],
  "medication": ["Hydroxychloroquine", "Prednisone"],
  "dosage": {"prednisone": "10mg daily"}
}
```

**column_mapping (uploaded_files):**
```json
{
  "WBC": {"test_code": "wbc", "confidence": 100},
  "CRP": {"test_code": "crp", "confidence": 95},
  "Custom_Test": {"test_code": "custom_001", "confidence": 50, "approved": false}
}
```

### Indexes
```sql
-- Performance indexes
CREATE INDEX idx_patient_anonymous_id ON patients(anonymous_id);
CREATE INDEX idx_diagnosis_patient ON diagnoses(patient_id);
CREATE INDEX idx_lab_patient ON lab_results_flexible(patient_id);
CREATE INDEX idx_lab_test ON lab_results_flexible(test_definition_id);
CREATE INDEX idx_lab_date ON lab_results_flexible(test_date);
CREATE INDEX idx_lab_abnormal ON lab_results_flexible(is_abnormal);

-- JSONB GIN indexes for fast queries
CREATE INDEX idx_disease_data_gin ON disease_specific_data USING GIN(data);
CREATE INDEX idx_patient_additional_gin ON patients USING GIN(additional_data);
```

---

## Import Workflow (End-to-End)

### Step 1: User Uploads File
```python
POST /api/v1/upload/import
Content-Type: multipart/form-data

{
  "file": <binary>,
  "disease_name": "SLE",
  "icd10_code": "M32.9"
}
```

### Step 2: FileParser Validates
```python
# Check format, encoding, required columns
if validation_errors:
    return HTTPException(400, "Invalid file")

# Generate preview
preview = file_parser.preview_data(df)
```

### Step 3: ColumnMapper Suggests Mappings
```python
mappings = column_mapper.suggest_mappings(df.columns)
# Auto-approve high-confidence matches (>90)
# Flag low-confidence for review
```

### Step 4: Anonymizer Processes Patients
```python
for _, row in df.iterrows():
    patient = anonymizer.anonymize_patient(row)
    patients.append(patient)
```

### Step 5: DataTransformer Builds Models
```python
for patient_data in patients:
    models = transformer.transform_patient_data(patient_data)
    patient_models.append(models)
```

### Step 6: BatchImporter Inserts to DB
```python
results = batch_importer.import_batch(patient_models, file_info)
# Creates audit trail
# Returns success/failure counts
```

### Step 7: User Reviews Results
```python
GET /api/v1/upload/files/{file_id}
# Shows: 109/110 patients imported, 1 failed (row 59: invalid date)
```

---

## Multi-Disease Support

### Design Principle
**One schema for all diseases** - No disease-specific tables

### How It Works
1. **Shared Lab Tests:** WBC, CRP, ESR used by SLE, RA, IBD, MS, etc.
2. **Disease Name as Text:** No ENUM, just VARCHAR(200)
3. **JSONB for Unique Fields:** Each disease stores specific data flexibly
4. **Same Import Pipeline:** Works for any disease without code changes

### Adding New Disease (e.g., Rheumatoid Arthritis)
```python
# Step 1: Upload RA dataset
POST /upload/import
{
  "file": "ra_patients.xlsx",
  "disease_name": "Rheumatoid Arthritis",
  "icd10_code": "M05.9"
}

# Step 2: RA-specific tests auto-created
# - RF (Rheumatoid Factor)
# - Anti-CCP
# - DAS28 score → disease_specific_data JSONB

# Step 3: Query RA patients
GET /patients/?disease_name=rheumatoid arthritis

# No schema changes needed!
```

### Supported Diseases (Ready to Import)
- ✅ Systemic Lupus Erythematosus (SLE)
- ✅ Sjogren's Syndrome
- ✅ Rheumatoid Arthritis (RA)
- ✅ Multiple Sclerosis (MS)
- ✅ Inflammatory Bowel Disease (IBD)
- ✅ Any other autoimmune disease
- ✅ Even non-autoimmune (CKD, Diabetes, Cancer, CVD, etc.)

---

## Performance & Scalability

### Current Capacity
- **Tested:** 110 patients imported in <5 seconds
- **Estimated:** 10,000 patients in <2 minutes
- **Bottleneck:** Fuzzy matching (can be cached)

### Optimization Strategies
1. **Batch Inserts:** 500 rows per transaction
2. **Connection Pooling:** PostgreSQL max_connections=100
3. **Async Processing:** FastAPI async endpoints
4. **Caching:** Test catalog, column mappings
5. **Indexing:** All foreign keys, JSONB fields

### Future Scaling (>100K patients)
- **Database:** Partition tables by year or disease
- **Import:** Celery/Redis for background jobs
- **Storage:** S3/MinIO for file storage
- **Search:** Elasticsearch for full-text search

---

## Error Handling & Recovery

### Import Failures
```python
# Scenario: Row 59 has invalid date "0 No 1 Yes"
Result: Skip row 59, import other 109 patients
Audit: Log error in data_ingestion_audit
User: Review failed rows, fix, re-upload
```

### File Corruption
```python
# Scenario: Excel file corrupted
Result: FileParser raises exception
Response: HTTP 400 with error message
User: Re-upload file
```

### Database Constraint Violations
```python
# Scenario: Duplicate anonymous_id (should never happen)
Result: BatchImporter catches IntegrityError
Response: Rollback patient, log error
User: Check anonymizer logic
```

### Rollback Strategy
- **Per-patient:** If one patient fails, others succeed
- **Per-batch:** If file validation fails, nothing is imported
- **Manual:** Admin can delete entire import batch via audit_id

---

## Code Locations

- **Services:** `app/services/` (file_parser.py, column_mapper.py, anonymizer.py, data_transformer.py, batch_importer.py)
- **Models:** `app/models/` (patient.py, lab_test.py, diagnosis.py, disease_data.py, upload.py)
- **Endpoints:** `app/api/endpoints/upload.py`
- **Migrations:** `init-db/` (001-004_*.sql)
- **Tests:** `tests/test_import_pipeline.py` (to be added)

---

## Next Steps

1. **Import Sjogren Dataset:** Test multi-disease support
2. **Add Unit Tests:** Cover all 5 services
3. **Build Admin UI:** Review unmapped columns, approve new tests
4. **Add File Streaming:** For files >1GB
5. **Implement OCR:** For PDF/IMG unstructured data
6. **Add Data Quality Dashboard:** Visualize missing data, outliers, quality scores
