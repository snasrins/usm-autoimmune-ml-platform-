# JIRA Ticket Screenshot Guide
## Sprint 1 - USM Autoimmune ML Platform

**Purpose:** Quick reference for capturing evidence for each JIRA ticket  
**Date:** March 25, 2026  
**Status:** All tickets ✅ Complete

---

## How to Use This Guide

For each JIRA ticket, you'll find:
1. **📸 FILES TO SCREENSHOT** - Exact files and line numbers
2. **🖥️ TERMINAL/UI TO SCREENSHOT** - Live evidence (running systems, queries)
3. **📊 WHAT TO HIGHLIGHT** - Key points to emphasize

**Tip:** Screenshots should show **working code + results** (not just code)

---

## Quick Reference Table

| JIRA Code | Ticket Name | Category | Files | Status |
|-----------|-------------|----------|-------|--------|
| USMA-11 | GPU/CUDA/Python Environment | Infrastructure | 4 files | ✅ |
| USMA-58 | Python Development Environment | Infrastructure | 3 files | ✅ |
| USMA-15 | Autoimmune Disease Registry DB | Database | 6 files | ✅ |
| USMA-39 | PostgreSQL Integration | Database | 5 files | ✅ |
| USMA-66 | Evaluate DB Architecture | Database | 3 files | ✅ |
| USMA-67 | Schema Evolution Strategy | Database | 3 files | ✅ |
| USMA-69 | Metadata Management | Database | 3 files | ✅ |
| USMA-17 | Secure Data Upload Backend | Ingestion | 4 files | ✅ |
| USMA-19 | File Validation Pipeline | Ingestion | 3 files | ✅ |
| USMA-18 | Dataset Preview Backend | Ingestion | 2 files | ✅ |
| USMA-16 | Patient Data Anonymisation | Security | 3 files | ✅ |
| USMA-20 | Data Ingestion Audit Trail | Governance | 3 files | ✅ |
| USMA-65 | Data Validation Queue System | Governance | 2 files | ✅ |
| USMA-28 | Document OCR Processing | OCR/ML | 4 files | ✅ |
| USMA-29 | NLP Text Structuring (NER) | OCR/ML | 2 files | ✅ |
| USMA-70 | Unstructured Pipeline Optimization | OCR/ML | 4 files | ✅ |
| USMA-12 | User Authentication | Security | 3 files | ✅ |
| USMA-13 | RBAC (4 Roles) | Security | 3 files | ✅ |
| USMA-41 | JWT Token Verification | Security | 2 files | ✅ |
| USMA-14 | Secure Data Storage (MinIO) | Storage | 2 files | ✅ |
| USMA-68 | Data Lake (Raw/Unstructured) | Storage | 2 files | ✅ |
| USMA-40 | Admin Endpoints | API | 2 files | ✅ |
| USMA-35 | Documentation for Proposal | Docs | 20+ files | ✅ |
| USMA-36 | Design Data Architecture | Docs | 4 files | ✅ |

---

## Infrastructure & Environment

### ✅ USMA-11: Configure GPU/CUDA/Python ML Environment

#### 📸 Files to Screenshot:

1. **check_gpu_ready.py** (Lines 1-50)
   - Show: GPU detection script
   - Highlight: `torch.cuda.is_available()`, GPU name detection

2. **requirements.txt** (Lines 1-60)
   - Show: PyTorch with CUDA (torch==2.1.0+cu121)
   - Highlight: transformers, scikit-learn, pandas

3. **docker-compose.yml** (Lines 1-40)
   - Show: GPU passthrough configuration
   - Highlight: `deploy.resources.reservations.devices`

4. **documents/SPRINT 1/INFRASTRUCTURE.md** (Lines 30-100)
   - Show: GPU configuration section
   - Highlight: "CUDA Version: 12.1.0"

#### 🖥️ Terminal to Screenshot:

```bash
# 1. Show nvidia-smi output
nvidia-smi

# 2. Run GPU validation script
python check_gpu_ready.py

# 3. Show PyTorch CUDA availability
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
```

#### 📊 Expected Output:
```
✅ CUDA Available: True
✅ CUDA Version: 12.1
✅ Number of GPUs: 1
✅ GPU Name: NVIDIA GeForce RTX 3090
✅ VRAM: 24576 MB
```

---

### ✅ USMA-58: Setup Python Development Environment

#### 📸 Files to Screenshot:

1. **requirements.txt** (All lines)
   - Show: Complete dependency list (50+ packages)

2. **requirements_qwen3vl.txt** (All lines)
   - Show: Qwen3-VL specific dependencies

3. **app/__init__.py** (Lines 1-10)
   - Show: Package initialization

#### 🖥️ Terminal to Screenshot:

```bash
# Show virtual environment and installed packages
source venv_qwen3/bin/activate
pip list | head -20
```

#### 📊 Key Packages to Highlight:
- torch==2.1.0+cu121
- transformers==4.36.0
- fastapi==0.109.0
- sqlalchemy==2.0.23
- pdfplumber==0.10.3

---

## Database & Schema

### ✅ USMA-15: Implement Autoimmune Disease Registry Database

#### 📸 Files to Screenshot:

1. **init-db/02-flexible-schema.sql** (Lines 1-100)
   - Show: Dimension tables (dim_patients, dim_diseases, dim_lab_tests)

2. **init-db/02-flexible-schema.sql** (Lines 150-250)
   - Show: Fact tables (fact_patient_visits, fact_lab_results, fact_diagnoses)

3. **init-db/02-flexible-schema.sql** (Lines 300-350)
   - Show: Metadata tables (metadata_datasets, audit_trail)

4. **app/models/patient.py** (Lines 1-50)
   - Show: Patient ORM model with SQLAlchemy

5. **app/models/diagnosis.py** (Lines 1-50)
   - Show: Diagnosis ORM model

6. **app/core/database.py** (All lines)
   - Show: SQLAlchemy engine configuration

#### 🖥️ pgAdmin to Screenshot:

```sql
-- 1. Show all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- 2. Show sample data from dim_diseases
SELECT * FROM dim_diseases LIMIT 10;

-- 3. Show schema diagram (if available in pgAdmin)
```

#### 📊 ER Diagrams to Include:
- Screenshot: 4 PNG files (ER diagrams from user's attachments)
- Show: Snowflake schema with fact-dimension relationships

---

### ✅ USMA-39: Integrated PostgreSQL and Build Database Models

#### 📸 Files to Screenshot:

1. **docker-compose.yml** (Lines 40-70)
   - Show: PostgreSQL service configuration
   - Highlight: Port 5432, volume mount

2. **app/core/database.py** (All lines)
   - Show: SQLAlchemy engine + session management

3. **app/models/patient.py** (All lines)
   - Show: Complete Patient model with relationships

4. **app/models/diagnosis.py** (All lines)
   - Show: Diagnosis model

5. **app/models/lab_test.py** (All lines)
   - Show: LabTest model

#### 🖥️ Terminal to Screenshot:

```bash
# Show Docker containers running
docker ps

# Expected containers:
# - usm-autoimmune-postgres (Port 5432)
# - usm-autoimmune-api (Port 8000)
# - usm-autoimmune-minio (Port 9000)
```

---

### ✅ USMA-66: Evaluate Database Architecture Options

#### 📸 Files to Screenshot:

1. **documents/SNOWFLAKE_SCHEMA_EXPLAINED.md** (Lines 1-200)
   - Show: Comparison table (Star vs Snowflake vs EAV vs Iceberg)
   - Highlight: Pros/cons of each pattern

2. **documents/DATABASE_SCHEMA/04_SNOWFLAKE_ICEBERG_EXPLAINED.md** (Lines 50-150)
   - Show: Snowflake schema diagram
   - Highlight: "Why Snowflake Schema?" section

3. **documents/FLEXIBLE-SCHEMA-DESIGN.md** (Lines 1-100)
   - Show: Hybrid approach (Snowflake + JSONB)

#### 📊 Key Comparison to Highlight:

| Pattern | When to Use | Your Choice |
|---------|-------------|-------------|
| Star Schema | Small, static datasets | ❌ No |
| **Snowflake Schema** | Multi-disease registry | ✅ **YES** |
| EAV Pattern | Dynamic attributes only | 🟡 Hybrid (JSONB) |
| Iceberg | Future-proofing | ✅ Compatible |

---

### ✅ USMA-67: Design Schema Evolution Strategy

#### 📸 Files to Screenshot:

1. **documents/FLEXIBLE-SCHEMA-DESIGN.md** (Lines 1-150)
   - Show: Schema evolution principles
   - Highlight: "Design Principles" section

2. **init-db/02-flexible-schema.sql** (Lines 200-250)
   - Show: JSONB columns in fact_disease_specific_data table

3. **scripts/migrations/001_create_flexible_schema.sql** (All lines)
   - Show: Migration script

#### 📊 Key Concept to Highlight:

```sql
-- OLD WAY (RIGID - requires schema migration):
CREATE TABLE sle_patients (...);
CREATE TABLE sjogren_patients (...);
-- ❌ New disease = new table = downtime!

-- NEW WAY (FLEXIBLE - no schema change):
INSERT INTO dim_diseases (disease_name, icd10_code) 
VALUES ('New Disease', 'X99.9');
-- ✅ Just add a row!
```

**Screenshot:** Show this comparison in your slides

---

### ✅ USMA-69: Create Metadata Management System

#### 📸 Files to Screenshot:

1. **init-db/02-flexible-schema.sql** (Lines 400-500)
   - Show: Metadata table definitions
   - Tables: metadata_datasets, metadata_columns, audit_trail, validation_queue

2. **app/models/upload.py** (All lines)
   - Show: Upload metadata model

3. **app/services/batch_importer.py** (Lines 100-150)
   - Show: Audit trail logging implementation

#### 🖥️ pgAdmin to Screenshot:

```sql
-- 1. Show metadata_datasets table
SELECT * FROM metadata_datasets LIMIT 5;

-- 2. Show audit_trail (recent actions)
SELECT * FROM audit_trail 
ORDER BY created_at DESC 
LIMIT 10;

-- 3. Show validation_queue (pending approvals)
SELECT * FROM validation_queue 
WHERE status = 'pending';
```

---

## Data Ingestion & Processing

### ✅ USMA-17: Develop Secure Data Upload Backend

#### 📸 Files to Screenshot:

1. **app/api/endpoints/upload.py** (Lines 1-100)
   - Show: Upload endpoint with multipart/form-data
   - Highlight: `@router.post("/import")`

2. **app/api/endpoints/upload_multiformat.py** (Lines 1-150)
   - Show: Multi-format support (CSV, Excel, PDF, JSON, XML)

3. **app/services/file_parser.py** (Lines 1-100)
   - Show: FileParser class initialization
   - Highlight: `parse_file()` method

4. **app/services/file_parser.py** (Lines 200-250)
   - Show: `calculate_file_hash()` method (SHA-256)

#### 🖥️ Swagger UI to Screenshot:

1. Go to: `http://172.24.175.24:8000/docs`
2. Screenshot: `POST /api/v1/upload/import` endpoint
3. Show: Parameters (file, disease_name, icd10_code)
4. Screenshot: Example request/response

#### 📊 API Test Example:

```bash
curl -X POST "http://172.24.175.24:8000/api/v1/upload/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sample.xlsx" \
  -F "disease_name=SLE" \
  -F "icd10_code=M32.9"
```

**Expected Response:**
```json
{
  "message": "Import completed",
  "file_id": 5,
  "results": {
    "total_rows": 110,
    "successful_patients": 109,
    "failed_patients": 1
  }
}
```

---

### ✅ USMA-19: Implement File Validation Pipeline

#### 📸 Files to Screenshot:

1. **app/services/file_parser.py** (Lines 1-200)
   - Show: Complete FileParser class

2. **app/services/file_parser.py** (Lines 50-100)
   - Show: `validate_data()` method
   - Highlight: Validation checks (encoding, columns, data types)

3. **app/services/file_parser.py** (Lines 150-200)
   - Show: `get_column_stats()` method

#### 📊 Validation Checks to Highlight:

```python
# Screenshot this section:
def validate_data(self, df: pd.DataFrame) -> Dict:
    """
    Validation checks:
    ✅ Required columns present
    ✅ Data types correct
    ✅ Missing data percentage < 30%
    ✅ No duplicate patient IDs
    ✅ Encoding detection (UTF-8, Latin-1)
    """
```

---

### ✅ USMA-18: Implement Dataset Preview Backend

#### 📸 Files to Screenshot:

1. **app/api/endpoints/upload.py** (Lines 100-150)
   - Show: `/upload/preview` endpoint

2. **app/services/file_parser.py** (Lines 200-250)
   - Show: `preview_data()` method

#### 🖥️ Swagger UI to Screenshot:

```bash
# API call:
GET /api/v1/upload/preview?file_id=5

# Expected response:
{
  "preview": [
    {"patient_id": "P001", "age": 35, "wbc": 6.5},
    {"patient_id": "P002", "age": 42, "wbc": 8.2}
  ],
  "column_stats": {
    "age": {"nulls": 2, "min": 18, "max": 75},
    "wbc": {"nulls": 5, "min": 3.5, "max": 11.0}
  }
}
```

---

### ✅ USMA-16: Implement Patient Data Anonymisation

#### 📸 Files to Screenshot:

1. **app/services/anonymizer.py** (Lines 1-150)
   - Show: Complete Anonymizer class

2. **app/services/anonymizer.py** (Lines 50-80)
   - Show: `anonymize_patient_id()` method (SHA-256 hashing)
   - Highlight: `hashlib.sha256()`

3. **app/services/anonymizer.py** (Lines 100-130)
   - Show: `convert_age_to_range()` method
   - Highlight: Age → "30-39" conversion

#### 📊 Anonymization Example:

```python
# Input:
original_id = "IC-920815-08-5678"
age = 35

# Output:
anonymous_id = "USMA-2026-A3F7B1C9"  # SHA-256 hash
age_range = "30-39"  # No exact age stored
```

#### 🖥️ NMRR Compliance Checklist:

**Screenshot from documents/SPRINT 1/DATA_PIPELINE.md:**
- ✅ No raw IC/NRIC stored
- ✅ SHA-256 anonymization
- ✅ Age ranges only (no exact DOB)
- ✅ Private network (ZeroTier VPN)
- ✅ Audit trail for all actions

---

### ✅ USMA-20: Implement Data Ingestion Audit Trail

#### 📸 Files to Screenshot:

1. **init-db/02-flexible-schema.sql** (Lines 450-500)
   - Show: audit_trail table definition

2. **app/services/batch_importer.py** (Lines 200-250)
   - Show: Audit logging implementation
   - Highlight: `INSERT INTO audit_trail`

3. **app/models/** (if exists: audit.py)
   - Show: AuditTrail model

#### 🖥️ pgAdmin to Screenshot:

```sql
SELECT 
    audit_id,
    action,
    entity_type,
    user_id,
    timestamp,
    details::json
FROM audit_trail
ORDER BY timestamp DESC
LIMIT 10;
```

**Expected Output:**
```
audit_id | action | entity_type | user_id | timestamp           | details
1        | INSERT | patient     | user_1  | 2026-03-25 10:30:00 | {"file": "sle_data.xlsx"}
2        | UPDATE | lab_result  | user_1  | 2026-03-25 10:31:00 | {"test": "WBC"}
```

---

### ✅ USMA-65: Create Data Validation Queue System

#### 📸 Files to Screenshot:

1. **init-db/02-flexible-schema.sql** (Lines 350-400)
   - Show: validation_queue table definition

2. **documents/ARCHITECTURE_REVISION.md** (Lines 100-300)
   - Show: "LAYER 3: VALIDATION QUEUE" section
   - Highlight: 4 checkpoints diagram

#### 📊 4 Validation Checkpoints:

**Screenshot this diagram:**

```
CHECKPOINT 1: Column Mapping Review
└─> User confirms detected columns

CHECKPOINT 2: OCR Output Review
└─> User approves extracted text (confidence: 87%)

CHECKPOINT 3: Cleaning Operations Selection
└─> User selects data cleaning steps

CHECKPOINT 4: Feature Extraction Validation
└─> User verifies extracted entities
```

---

## OCR & NER Pipeline

### ✅ USMA-28: Implement Document OCR Processing

#### 📸 Files to Screenshot:

1. **standalone_unstructured_pipeline.py** (Lines 1-100)
   - Show: Main pipeline configuration
   - Highlight: MODEL_VARIANT, OPTIMIZATION_TIER

2. **standalone_unstructured_pipeline.py** (Lines 1800-1900)
   - Show: PDF processing with pdfplumber + Qwen3-VL

3. **app/services/qwen_ocr_service.py** (Lines 1-150)
   - Show: Qwen3VLEngine class

4. **app/services/unstructured_pipeline_service.py** (Lines 1-200)
   - Show: UnstructuredPipelineService orchestration

#### 🖥️ Terminal to Screenshot:

```bash
# Run OCR pipeline on sample PDF
python standalone_unstructured_pipeline.py "Sample Medical Report.pdf"
```

#### 📊 Expected Output:

```
================================================================================
🏥 USM AUTOIMMUNE - UNSTRUCTURED DATA PIPELINE
================================================================================
📄 Processing: Sample Medical Report.pdf (6 pages)

⏱️  TIMING RESULTS:
├─ Page 1: 37.2s
├─ Page 2: 38.1s
├─ Page 3: 36.9s
├─ Page 4: 37.5s
├─ Page 5: 37.8s
└─ Page 6: 48.3s

Total time: 235.8s (3m 55.8s)
Average per page: 39.3s

📊 EXTRACTION RESULTS:
├─ Text extracted: 8,091 characters
├─ Entities found: 37
├─ Confidence: 85%
└─ Quality: ✅ PASSED

🎮 GPU VRAM: 19.3% (4.66GB / 24GB)
```

**Screenshot:** The entire terminal output

---

### ✅ USMA-29: Implement NLP Text Structuring Engine (NER Pipeline)

#### 📸 Files to Screenshot:

1. **standalone_unstructured_pipeline.py** (Lines 1400-1500)
   - Show: Regex NER patterns
   - Highlight: `ENTITY_PATTERNS` dictionary

2. **standalone_unstructured_pipeline.py** (Lines 1500-1600)
   - Show: `extract_entities_from_text()` method

#### 📊 NER Patterns to Highlight:

```python
# Screenshot these regex patterns:
ENTITY_PATTERNS = {
    'patient_name': r'Patient Name[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
    'diagnosis': r'Diagnosis[:\s]+([A-Z][a-z]+(?: [A-Z][a-z]+)*)',
    'medication': r'Medication[:\s]+([A-Z][a-z]+)',
    'lab_test': r'(WBC|CRP|ESR|HGB|PLT)[:\s]+([\d.]+)',
    'date': r'(?:Date|Collected)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
}
```

#### 🖥️ Output JSON to Screenshot:

```json
{
  "file_name": "Sample Medical Report.pdf",
  "text_length": 8091,
  "confidence": 0.85,
  "entities": [
    {"type": "patient_name", "value": "Ahmad Bin Ali", "confidence": 0.92},
    {"type": "diagnosis", "value": "Systemic Lupus Erythematosus", "confidence": 0.95},
    {"type": "medication", "value": "Hydroxychloroquine", "confidence": 0.88},
    {"type": "lab_test", "value": "WBC: 6.5", "confidence": 0.90},
    {"type": "date", "value": "2026-03-15", "confidence": 0.95}
  ]
}
```

---

### ✅ USMA-70: Optimization of Unstructured Pipeline

#### 📸 Files to Screenshot:

1. **SAFE_OPTIMIZATION_PLAN.md** (Lines 1-200)
   - Show: Complete 4-phase optimization strategy

2. **standalone_unstructured_pipeline.py** (Lines 70-90)
   - Show: `MODEL_VARIANT = "instruct"`, `OPTIMIZATION_TIER = "tier2"`

3. **standalone_unstructured_pipeline.py** (Lines 1840-1850)
   - Show: `dpi=120` setting

4. **standalone_unstructured_pipeline.py** (Lines 1320-1340)
   - Show: `max_new_tokens=768`, `min_new_tokens=100`

#### 📊 Performance Comparison Table:

**Screenshot this table from SAFE_OPTIMIZATION_PLAN.md:**

| Metric | Baseline | After Tier 1 | After Phase 1 | Improvement |
|--------|----------|--------------|---------------|-------------|
| **Total time** | 430s | 376s | 236s | **45% faster** |
| **Per page** | 71.6s | 62.7s | 37.2s | **48% faster** |
| **Entities** | 39 | 39 | 37 | -5% (acceptable) |
| **Confidence** | 85% | 85% | 85% | Maintained ✅ |
| **Text chars** | 7,971 | 7,985 | 8,091 | +1.5% MORE ✅ |
| **VRAM** | 19.5% | 19.4% | 19.3% | Efficient ✅ |

---

## Authentication & Security

### ✅ USMA-12: Implement User Authentication (Login/Session/Logout)

#### 📸 Files to Screenshot:

1. **app/api/endpoints/auth.py** (Lines 1-100)
   - Show: Login, register, token endpoints

2. **app/core/security.py** (Lines 1-100)
   - Show: JWT token generation, password hashing

3. **app/core/security.py** (Lines 100-150)
   - Show: Token verification, user extraction

#### 🖥️ Swagger UI to Screenshot:

1. **Login endpoint:**
   ```
   POST /api/v1/auth/login
   Body: {"username": "admin", "password": "admin123"}
   ```

2. **Response:**
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer",
     "expires_in": 43200
   }
   ```

3. **Test authenticated endpoint:**
   ```
   GET /api/v1/auth/me
   Headers: Authorization: Bearer <token>
   ```

4. **Response:**
   ```json
   {
     "user_id": "uuid",
     "username": "admin",
     "email": "admin@usm.my",
     "role": "ADMIN"
   }
   ```

---

### ✅ USMA-13: Implement RBAC (Admin/Researcher/Viewer/Engineer Roles)

#### 📸 Files to Screenshot:

1. **app/models/user.py** (Lines 1-50)
   - Show: User model with `role` enum field

2. **app/core/security.py** (Lines 50-100)
   - Show: `require_role()` decorator

3. **app/api/deps.py** (Lines 1-50)
   - Show: Role checking dependency

#### 📊 Role Permissions Table:

**Create this table in slides:**

| Role | Upload | View | Edit | Manage Users | Admin Panel |
|------|--------|------|------|--------------|-------------|
| **ADMIN** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **RESEARCHER** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **VIEWER** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **ENGINEER** | ✅ | ✅ | ✅ | ❌ | ✅ (system) |

---

### ✅ USMA-41: Verified JWT Token Generation and Authentication Flow

#### 📸 Files to Screenshot:

1. **app/core/security.py** (Lines 1-150)
   - Show: Complete JWT implementation

2. **app/api/deps.py** (Lines 1-50)
   - Show: `get_current_user()` dependency

#### 🖥️ Test Script to Screenshot:

```python
# test_jwt_flow.py
import requests

BASE_URL = "http://172.24.175.24:8000"

# 1. Login
response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
    json={"username": "admin", "password": "admin123"})
token = response.json()["access_token"]
print(f"✅ Token received: {token[:20]}...")

# 2. Test authenticated endpoint
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
print(f"✅ User info: {response.json()}")

# 3. Test protected endpoint
response = requests.get(f"{BASE_URL}/api/v1/patients/", headers=headers)
print(f"✅ Protected endpoint accessible: {len(response.json())} patients")
```

**Output:**
```
✅ Token received: eyJhbGciOiJIUzI1NiIs...
✅ User info: {'username': 'admin', 'role': 'ADMIN'}
✅ Protected endpoint accessible: 109 patients
```

---

### ✅ USMA-14: Implement Secure Data Storage System (MinIO)

#### 📸 Files to Screenshot:

1. **docker-compose.yml** (Lines 80-120)
   - Show: MinIO service configuration

2. **app/core/config.py** (if exists)
   - Show: MinIO connection settings

#### 🖥️ MinIO Console to Screenshot:

1. Go to: `http://172.24.175.24:9001`
2. Login with MINIO_ROOT_USER/PASSWORD
3. Screenshot: Bucket list showing:
   - `usm-raw`
   - `usm-processed`
   - `usm-models`
4. Screenshot: Sample file in `usm-raw` bucket

#### 🖥️ Docker Containers to Screenshot:

```bash
docker ps

# Expected output:
# usm-autoimmune-minio (Ports: 9000, 9001)
```

---

### ✅ USMA-68: Implement Data Lake for Raw/Unstructured Files

#### 📸 Files to Screenshot:

1. **docker-compose.yml** (Lines 80-120)
   - Show: MinIO configuration

2. **app/services/unstructured_pipeline_service.py** (Lines 50-100)
   - Show: MinIO upload logic

#### 📊 Data Lake Architecture Diagram:

**Screenshot this from documentation or create slide:**

```
┌─────────────────────────────────┐
│      MinIO Data Lake (S3)       │
├─────────────────────────────────┤
│                                 │
│  Bucket: usm-raw                │
│  └─> Raw PDF, Images, CSVs      │
│                                 │
│  Bucket: usm-processed          │
│  └─> Cleaned Parquet, JSON      │
│                                 │
│  Bucket: usm-models             │
│  └─> ML model artifacts         │
└─────────────────────────────────┘
```

---

## Admin & Monitoring

### ✅ USMA-40: Created Admin Endpoints for Monitoring and System Stats

#### 📸 Files to Screenshot:

1. **app/api/endpoints/admin.py** (Lines 1-100)
   - Show: Admin router with endpoints

2. **app/services/test_manager.py** (Lines 1-150)
   - Show: TestManager class

#### 🖥️ Swagger UI to Screenshot:

**Admin endpoints:**
- `GET /api/v1/admin/tests/` - List all lab tests
- `POST /api/v1/admin/tests/` - Create new test
- `POST /api/v1/admin/tests/approve` - Approve pending test
- `GET /api/v1/admin/stats/database` - Database statistics
- `GET /api/v1/health` - System health

#### 📊 Health Endpoint Response:

```json
{
  "status": "healthy",
  "database": "connected",
  "minio": "connected",
  "gpu": {
    "available": true,
    "name": "NVIDIA GeForce RTX 3090",
    "vram_total": "24GB",
    "vram_used": "4.66GB"
  }
}
```

---

## Documentation & Planning

### ✅ USMA-35: Prepare Slides and Documentation for Proposal

#### 📸 Files to Screenshot:

**20+ documentation files created:**

| File | Purpose |
|------|---------|
| `documents/README.md` | Project overview |
| `documents/SPRINT 1/TECHNICAL_SPECIFICATION.md` | **This document** |
| `documents/SPRINT 1/ARCHITECTURE.md` | System architecture |
| `documents/SPRINT 1/DATA_PIPELINE.md` | Data pipeline details |
| `documents/SPRINT 1/API_GUIDE.md` | API usage guide |
| `documents/ARCHITECTURE_REVISION.md` | Architecture redesign |
| `documents/SNOWFLAKE_SCHEMA_EXPLAINED.md` | Schema comparison |

#### 📊 Presentation Slides Outline:

**Slide 1:** Project Overview
- Screenshot: `documents/README.md` (Lines 1-50)

**Slide 2:** System Architecture
- Screenshot: 5-layer architecture diagram (from TECHNICAL_SPECIFICATION.md)

**Slide 3:** Database Schema
- Screenshot: ER diagrams (4 PNG files from attachments)

**Slide 4:** Data Pipeline Flow
- Screenshot: `ARCHITECTURE_REVISION.md` (Lines 100-300)

**Slide 5:** OCR Performance
- Screenshot: Performance comparison table (from USMA-70)

**Slide 6:** Security & Compliance
- Screenshot: NMRR compliance checklist

**Slide 7:** API Endpoints
- Screenshot: Swagger UI (`http://172.24.175.24:8000/docs`)

**Slide 8:** Next Steps
- Sprint 2 roadmap

---

### ✅ USMA-36: Design Data Architecture

#### 📸 Files to Screenshot:

1. **revised architecture.txt** (All lines)
   - Show: Complete 5-layer architecture

2. **documents/ARCHITECTURE_REVISION.md** (Lines 1-300)
   - Show: Revised architecture with validation checkpoints

3. **documents/DATABASE_SCHEMA/02_ARCHITECTURE_REVISION.md** (Lines 1-200)
   - Show: End-to-end flow

4. **documents/SNOWFLAKE_SCHEMA_EXPLAINED.md** (Lines 1-100)
   - Show: Schema pattern comparison

#### 📊 Key Architecture Diagram:

**Screenshot:** The complete 5-layer diagram showing:
- Layer 1: Ingestion & Upload
- Layer 2A: Structured Processing
- Layer 2B: Unstructured Processing (OCR + NER)
- Layer 3: Validation Queue (4 checkpoints)
- Layer 4: PostgreSQL (Snowflake schema)
- Layer 4.5: Data Preparation & Quality Assurance

---

## Summary: Which Files to Screenshot

### Priority 1 (Must Have) - 15 Screenshots

1. **GPU Environment** - `check_gpu_ready.py` output + `nvidia-smi`
2. **Database Schema** - pgAdmin showing all 15 tables
3. **ER Diagrams** - 4 PNG files (from attachments)
4. **OCR Performance** - Terminal output showing 236s result
5. **Performance Table** - From SAFE_OPTIMIZATION_PLAN.md
6. **Architecture Diagram** - 5-layer system architecture
7. **Validation Checkpoints** - 4 checkpoints diagram
8. **Anonymization Code** - `anonymizer.py` SHA-256 implementation
9. **Audit Trail** - pgAdmin query showing audit_trail table
10. **Swagger UI** - Main page showing 40+ endpoints
11. **JWT Login** - Swagger UI login endpoint with response
12. **MinIO Console** - Showing 3 buckets (usm-raw, usm-processed, usm-models)
13. **Docker Containers** - `docker ps` output
14. **NER Patterns** - Regex patterns from standalone_unstructured_pipeline.py
15. **NMRR Compliance** - Checklist from documentation

### Priority 2 (Nice to Have) - 10 Screenshots

16. File Parser validation logic
17. Column Mapper fuzzy matching
18. Data Transformer implementation
19. Batch Importer with audit logging
20. RBAC permission matrix
21. Health endpoint response
22. Database performance benchmarks
23. File structure tree
24. Requirements.txt (dependencies)
25. OCR JSON output (extracted entities)

---

## Quick Screenshot Checklist

### Before Starting:
- [ ] SSH to server: `ssh shaggy@gpulab1` or `ssh mtuser2@172.24.175.24`
- [ ] Activate venv: `source venv_qwen3/bin/activate`
- [ ] Docker containers running: `docker ps`
- [ ] Open pgAdmin (connect to 172.24.175.24:5432)
- [ ] Open Swagger UI: `http://172.24.175.24:8000/docs`
- [ ] Open MinIO Console: `http://172.24.175.24:9001`

### During Screenshots:
- [ ] Use high resolution (at least 1920x1080)
- [ ] Zoom in for code screenshots (font size 14-16pt)
- [ ] Show line numbers in code editors
- [ ] Highlight key sections (use arrows/boxes in post-processing)
- [ ] Include timestamps where relevant
- [ ] Show complete context (don't crop important info)

### After Screenshots:
- [ ] Organize by JIRA ticket number
- [ ] Name files: `USMA-XX_description.png`
- [ ] Create slides presentation
- [ ] Add brief captions to each screenshot
- [ ] Review for sensitive data (remove if any)

---

**Document Version:** 1.0  
**Last Updated:** March 25, 2026  
**Created By:** GitHub Copilot + Syarifah Fajriyah  
**Total JIRA Tickets:** 24  
**Status:** ✅ All Complete
