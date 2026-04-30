# 🏗️ USM Autoimmune Platform - Architecture Revision
**Date:** March 20, 2026  
**Data Engineer:** Syarifah Fajriyah  
**Based on PM Feedback - Critical Changes**

---

## 🚨 **Critical Issues Identified**

### **1. Schema Rigidity Problem**

**Current (❌ WRONG):**
```
patients
├── sle_patients
├── lupus_patients  
├── sjogren_patients
└── [breaks when new disease added]
```

**Revised (✅ CORRECT):**
```
patients (high-level)
└── disease_associations
    └── diseases (flexible, can add SLE, Lupus, Sjogren, IBD, etc.)
```

### **2. OCR Pipeline Placement Problem**

**Current (❌ WRONG):**
```
Unstructured Data → Storage → Data Prep → [OCR Separate Stage]
```

**Revised (✅ CORRECT):**
```
Unstructured Data → Storage → [OCR + NER + Cleaning INSIDE Pipeline] → Data Prep
```

### **3. Human Validation Missing**

**Current (❌ WRONG):**
- System automatically processes data
- No approval checkpoints
- User cannot review before execution

**Revised (✅ CORRECT):**
- User reviews OCR output → Approve/Reject
- User selects cleaning operations → Confirm
- User validates extracted features → Execute
- Audit trail logs all actions

---

## 🏛️ **Revised System Architecture**

### **Layer 1: Data Ingestion & Discovery**

```
┌─────────────────────────────────────────────────────────────┐
│  USER UPLOADS DATA (CSV, Excel, PDF, Images, etc.)         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  AUTOMATIC COLUMN EXTRACTION & METADATA STORAGE             │
│  - Detect all columns                                        │
│  - Register entities (patient_id, age, diagnosis, etc.)     │
│  - Store in metadata catalog                                 │
│  - Create dataset version (v1)                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  USER VALIDATION #1: Column Mapping                          │
│  ✔ Review detected columns                                   │
│  ✔ Confirm entity types                                      │
│  ✔ Map to schema (Patient, Lab Test, Diagnosis)            │
│  → User clicks "Confirm Mapping"                             │
└─────────────────────────────────────────────────────────────┘
```

### **Layer 2: Unstructured Data Processing Pipeline**

```
┌─────────────────────────────────────────────────────────────┐
│  IF FILE = PDF/IMAGE (Unstructured)                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: OCR PROCESSING (INSIDE PIPELINE)                  │
│  - Extract text using Qwen-VL / Tesseract                   │
│  - Store OCR result with confidence scores                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  USER VALIDATION #2: OCR Output Review                       │
│  ✔ Show extracted text preview                               │
│  ✔ Confidence: 85%                                           │
│  ✔ User reviews: "Patient Name: John Doe"                   │
│  → Accept / Reject / Re-run with different engine            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 2: TEXT CLEANING (USER-CONTROLLED)                   │
│  User selects operations:                                    │
│  [ ] Remove punctuation?                                     │
│  [✓] Fix casing?                                            │
│  [ ] Remove stopwords?                                       │
│  [✓] Normalize units? (10mg → 10 mg)                       │
│  [✓] Standardize dates? (01/15/2024 → 2024-01-15)          │
│  [ ] Fix OCR errors?                                         │
│  → User clicks "Execute Cleaning"                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 3: NER & FEATURE EXTRACTION                          │
│  - Extract entities: Name, Diagnosis, Medication, Dates     │
│  - Map to schema tables                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  USER VALIDATION #3: Extracted Features Review               │
│  Detected entities:                                          │
│  - Name: John Doe                                            │
│  - Diagnosis: Systemic Lupus Erythematosus (SLE)           │
│  - Medication: Hydroxychloroquine 200mg                      │
│  - Date: 2024-01-15                                          │
│  → Confirm / Edit / Reject                                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  VERSIONING & AUDIT TRAIL                                    │
│  - Dataset version: v2 (after cleaning)                      │
│  - User: syarifah@usm.my                                     │
│  - Timestamp: 2026-03-20 10:45:00                            │
│  - Actions: OCR → Cleaned → Features Extracted              │
└─────────────────────────────────────────────────────────────┘
```

### **Layer 3: Flexible Schema Storage**

```
┌─────────────────────────────────────────────────────────────┐
│  FACT TABLE: patient_visits (Measurable Events)             │
│  - visit_id, patient_id, date, hospital_id                   │
│  - lab_test_id, result_value, diagnosis_id                   │
└─────────────────────────────────────────────────────────────┘
                          ↑
                Links to Dimensions
                          ↓
┌──────────────────────┬──────────────────┬──────────────────┐
│ DIM: patients         │ DIM: diseases    │ DIM: hospitals   │
│ - patient_id          │ - disease_id     │ - hospital_id    │
│ - anonymized_id       │ - disease_name   │ - name           │
│ - age_range           │ - category       │ - location       │
│ - gender              │ - icd_code       │                  │
└──────────────────────┴──────────────────┴──────────────────┘
                          ↓
┌──────────────────────┬──────────────────┬──────────────────┐
│ DIM: lab_tests        │ DIM: medications │ DIM: time        │
│ - test_id             │ - medication_id  │ - date           │
│ - test_name           │ - drug_name      │ - year           │
│ - category            │ - dosage         │ - month          │
│ - unit                │                  │ - quarter        │
└──────────────────────┴──────────────────┴──────────────────┘
```

**Key Features:**
- ✅ **New diseases** can be added without schema change
- ✅ **New lab tests** registered dynamically
- ✅ **Snowflake-style normalization** reduces redundancy
- ✅ **Supports schema evolution** (Iceberg-compatible)

### **Layer 4: Security & RBAC**

```
┌─────────────────────────────────────────────────────────────┐
│  ROLE-BASED ACCESS CONTROL (RBAC)                           │
│                                                              │
│  👤 Data Engineer (You)   → Upload, Validate, Execute       │
│  👩‍⚕️ Clinician (USM)        → Upload, Review, Approve         │
│  🔬 ML Engineer (Iznie)   → Read, Export, Train Models      │
│  👨‍💼 Admin                  → All privileges                   │
│  👁️ Auditor                → Read-only, Audit trail          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  ZERO-TRUST PRINCIPLES                                       │
│  - Every API call requires JWT token                         │
│  - User identity verified at each step                       │
│  - Audit log for sensitive operations                        │
│  - Data encryption at rest & in transit                      │
└─────────────────────────────────────────────────────────────┘
```

### **Layer 5: ML Pipeline (Iznie's Layer)**

```
┌─────────────────────────────────────────────────────────────┐
│  FEATURE STORE (Validated Features)                         │
│  - Longitudinal features (time-series)                       │
│  - Derived features (ratios, trends)                         │
│  - Embeddings (from Qwen)                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  ML MODELS (11 Algorithms)                                   │
│  - Logistic Regression, Random Forest, XGBoost, etc.        │
│  - Training only starts AFTER feature validation            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  USER VALIDATION #4: Model Training Approval                 │
│  → User reviews feature set                                  │
│  → Confirms training parameters                              │
│  → Clicks "Start Training"                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 **End-to-End User Flow**

### **Scenario: Clinician Uploads Scanned Lab Report**

1. **Upload** PDF file via Swagger UI
2. **System** automatically detects file type, extracts columns/metadata
3. **User** reviews column mapping → Confirms
4. **System** runs OCR (Qwen-VL)
5. **User** reviews OCR output (85% confidence) → Accepts
6. **System** shows cleaning options (checkboxes)
7. **User** selects: Fix casing, Normalize units → Clicks Execute
8. **System** extracts entities (NER)
9. **User** validates extracted features → Confirms
10. **System** stores in database (v2), logs audit trail
11. **User** proceeds to ML training → Feature store ready

**Human validation at 4 checkpoints** ✅

---

## 🗄️ **Revised Database Schema (Flexible Design)**

### **Core Entities (High-Level)**

```sql
-- DIMENSION: Patients (High-Level Entity)
CREATE TABLE dim_patients (
    patient_id UUID PRIMARY KEY,
    anonymous_id VARCHAR(64) UNIQUE,  -- SHA-256 hash
    age_range VARCHAR(20),  -- "20-30", "31-40", etc.
    gender VARCHAR(10),
    ethnicity VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- DIMENSION: Diseases (Flexible - Can Branch)
CREATE TABLE dim_diseases (
    disease_id SERIAL PRIMARY KEY,
    disease_name VARCHAR(100),  -- "SLE", "Lupus", "Sjogren", etc.
    disease_category VARCHAR(50),  -- "Autoimmune", "Infectious", etc.
    icd10_code VARCHAR(10),
    parent_disease_id INT REFERENCES dim_diseases(disease_id),  -- For hierarchies
    created_at TIMESTAMP
);

-- DIMENSION: Lab Tests (Dynamically Registered)
CREATE TABLE dim_lab_tests (
    test_id SERIAL PRIMARY KEY,
    test_name VARCHAR(100),
    category VARCHAR(50),  -- "Hematology", "Immunology", etc.
    unit VARCHAR(20),
    normal_range_min FLOAT,
    normal_range_max FLOAT,
    created_at TIMESTAMP
);

-- DIMENSION: Hospitals (10 USM Hospitals)
CREATE TABLE dim_hospitals (
    hospital_id SERIAL PRIMARY KEY,
    hospital_name VARCHAR(100),
    location VARCHAR(100),
    hospital_code VARCHAR(20),
    created_at TIMESTAMP
);

-- DIMENSION: Medications (Flexible Registry)
CREATE TABLE dim_medications (
    medication_id SERIAL PRIMARY KEY,
    drug_name VARCHAR(100),
    generic_name VARCHAR(100),
    dosage_form VARCHAR(50),  -- "Tablet", "Injection", etc.
    created_at TIMESTAMP
);

-- DIMENSION: Time (For Time-Series Analysis)
CREATE TABLE dim_time (
    date_id INT PRIMARY KEY,
    full_date DATE,
    year INT,
    month INT,
    quarter INT,
    day_of_week INT,
    is_weekend BOOLEAN
);
```

### **Fact Tables (Measurable Events)**

```sql
-- FACT: Patient Visits (Central Fact Table)
CREATE TABLE fact_patient_visits (
    visit_id UUID PRIMARY KEY,
    patient_id UUID REFERENCES dim_patients(patient_id),
    hospital_id INT REFERENCES dim_hospitals(hospital_id),
    visit_date DATE,
    date_id INT REFERENCES dim_time(date_id),
    visit_type VARCHAR(50),  -- "Inpatient", "Outpatient", "Emergency"
    created_at TIMESTAMP
);

-- FACT: Lab Results (Measurable Data)
CREATE TABLE fact_lab_results (
    result_id UUID PRIMARY KEY,
    visit_id UUID REFERENCES fact_patient_visits(visit_id),
    patient_id UUID REFERENCES dim_patients(patient_id),
    test_id INT REFERENCES dim_lab_tests(test_id),
    result_value FLOAT,
    result_text TEXT,  -- For qualitative results
    is_abnormal BOOLEAN,
    result_date DATE,
    date_id INT REFERENCES dim_time(date_id),
    created_at TIMESTAMP
);

-- FACT: Diagnoses (Patient-Disease Associations)
CREATE TABLE fact_diagnoses (
    diagnosis_id UUID PRIMARY KEY,
    visit_id UUID REFERENCES fact_patient_visits(visit_id),
    patient_id UUID REFERENCES dim_patients(patient_id),
    disease_id INT REFERENCES dim_diseases(disease_id),
    diagnosis_date DATE,
    date_id INT REFERENCES dim_time(date_id),
    severity VARCHAR(20),  -- "Mild", "Moderate", "Severe"
    created_at TIMESTAMP
);

-- FACT: Medication Prescriptions
CREATE TABLE fact_prescriptions (
    prescription_id UUID PRIMARY KEY,
    visit_id UUID REFERENCES fact_patient_visits(visit_id),
    patient_id UUID REFERENCES dim_patients(patient_id),
    medication_id INT REFERENCES dim_medications(medication_id),
    dosage VARCHAR(50),
    frequency VARCHAR(50),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP
);
```

### **Metadata & Governance Tables**

```sql
-- METADATA: Uploaded Datasets
CREATE TABLE metadata_datasets (
    dataset_id UUID PRIMARY KEY,
    dataset_name VARCHAR(200),
    file_type VARCHAR(20),  -- "CSV", "PDF", "Image", etc.
    uploaded_by VARCHAR(100),
    uploaded_at TIMESTAMP,
    version INT,  -- Dataset versioning
    parent_dataset_id UUID REFERENCES metadata_datasets(dataset_id),
    row_count INT,
    column_count INT,
    file_size_mb FLOAT,
    status VARCHAR(20)  -- "Uploaded", "Validated", "Processed"
);

-- METADATA: Column Registry (Automatic Extraction)
CREATE TABLE metadata_columns (
    column_id SERIAL PRIMARY KEY,
    dataset_id UUID REFERENCES metadata_datasets(dataset_id),
    column_name VARCHAR(100),
    data_type VARCHAR(50),
    entity_type VARCHAR(50),  -- "patient_id", "lab_test", "diagnosis", etc.
    mapped_to_table VARCHAR(100),  -- Which dimension/fact table
    created_at TIMESTAMP
);

-- AUDIT TRAIL: User Actions
CREATE TABLE audit_trail (
    audit_id UUID PRIMARY KEY,
    user_id VARCHAR(100),
    action VARCHAR(100),  -- "Upload", "Validate", "Execute Cleaning", etc.
    target_entity VARCHAR(100),  -- "Dataset", "OCR", "Feature"
    target_id UUID,
    timestamp TIMESTAMP,
    changes JSONB,  -- Before/after state
    ip_address VARCHAR(50)
);

-- VALIDATION QUEUE: Human Checkpoints
CREATE TABLE validation_queue (
    validation_id UUID PRIMARY KEY,
    dataset_id UUID REFERENCES metadata_datasets(dataset_id),
    stage VARCHAR(50),  -- "Column Mapping", "OCR Review", "Feature Extraction"
    status VARCHAR(20),  -- "Pending", "Approved", "Rejected"
    assigned_to VARCHAR(100),
    submitted_at TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewer_comments TEXT
);
```

---

## 🔥 **Why This Schema is Flexible**

### **Example 1: Adding New Disease**

**Old Schema (Rigid):**
```sql
-- Need to create new table
CREATE TABLE sjogren_patients (...);  ❌ Breaks system
```

**New Schema (Flexible):**
```sql
-- Just insert new row
INSERT INTO dim_diseases (disease_name, disease_category)
VALUES ('Sjogren Syndrome', 'Autoimmune');  ✅ No schema change
```

### **Example 2: New Lab Test from Hospital**

**Old Schema:**
```sql
-- Need to alter table or create specific column
ALTER TABLE lab_results ADD COLUMN new_test_xyz FLOAT;  ❌ Manual work
```

**New Schema:**
```sql
-- Register test dynamically
INSERT INTO dim_lab_tests (test_name, category, unit)
VALUES ('Anti-dsDNA', 'Immunology', 'IU/mL');  ✅ Automatic

-- Store results in fact table
INSERT INTO fact_lab_results (patient_id, test_id, result_value)
VALUES (...);  ✅ Works immediately
```

---

## 📈 **GPU Memory Constraint Handling**

**Your Limit: RTX 3090 = 24 GB VRAM**

### **Strategy:**

```
Qwen-VL (Vision) = 4 GB
Qwen-1.5B (Embeddings) = 3 GB
────────────────────────────
ML Model Training = 17 GB FREE  ✅

If training requires > 17 GB:
→ Use model quantization (4-bit/8-bit)
→ Reduce batch size
→ Unload Qwen models during training
```

---

## ✅ **System is a Framework, Not Automation**

**Key Principle:**

> "Provide tools, user controls execution, system executes only after approval"

**Before:**
```
User uploads → System processes → Done  ❌ Too automatic
```

**After:**
```
User uploads → Review → Approve → System processes → Done  ✅ Guided framework
```

---

## 🎯 **Action Items for You**

### **Priority 1: Database Schema Implementation** (Today)

```bash
# Create new schema migration file
cd /home/mtuser2/usm-autoimmune-ml-platform/init-db
nano 02-flexible-schema.sql
```

### **Priority 2: Add Validation Queue System** (Tomorrow)

```python
# app/services/validation_service.py
class ValidationService:
    def submit_for_review(self, dataset_id, stage):
        # Add to validation_queue
        pass
    
    def get_pending_validations(self, user_id):
        # Show pending items for user
        pass
    
    def approve(self, validation_id, user_id):
        # Approve and proceed
        pass
```

### **Priority 3: Add Audit Trail** (Tomorrow)

```python
# app/services/audit_service.py
class AuditService:
    def log_action(self, user_id, action, target_id, changes):
        # Log every user action
        pass
```

### **Priority 4: Test End-to-End** (This Week)

Use sample SLE data to test:
1. Upload → Column extraction
2. User validates columns
3. OCR processing → User reviews
4. Cleaning → User selects operations
5. Feature extraction → User confirms
6. Check audit trail

---

## 📊 **Deliverables for PM Meeting**

1. ✅ **Flexible schema design** (Fact/Dimension tables)
2. ✅ **Revised architecture** (User-controlled framework)
3. ⏳ **Implementation plan** (Next 2 weeks)
4. ⏳ **Sample data flow test** (Working demo)

---

**Next Step: Implement flexible schema in PostgreSQL NOW** 🚀
