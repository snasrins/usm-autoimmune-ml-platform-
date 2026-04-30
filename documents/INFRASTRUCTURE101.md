# INFRASTRUCTURE.md

## High-Performance GPU Computing Environment

### 1. GPU Server Provisioning
- **Server:** Dedicated Ubuntu 24.04.2 LTS instance
- **GPU:** NVIDIA RTX 3090 (24GB VRAM)
- **CPU:** 16-core Xeon
- **RAM:** 128GB
- **Storage:** 1TB NVMe SSD
- **Network:** ZeroTier VPN for secure remote access

### 2. CUDA & Deep Learning Libraries
- **CUDA Version:** 12.1.0
- **cuDNN:** Installed via NVIDIA container
- **NVIDIA Drivers:** 550+
- **Python:** 3.10 (in /opt/venv)
- **PyTorch, TensorFlow, scikit-learn:** Installed in venv
- **Docker:** Used for containerized deployment
- **Docker Compose:** Orchestrates API and PostgreSQL containers

### 3. Container Setup
- **API Container:** FastAPI app with all dependencies
- **Database Container:** PostgreSQL 15
- **Volumes:** Persistent storage for database and uploads
- **Environment Variables:** Managed via .env file

### 4. Security & Compliance
- **SSH:** Key-based authentication
- **Firewall:** Only required ports open (8000, 5432, 22)
- **Data Anonymization:** SHA-256, age ranges, no direct identifiers
- **NMRR Compliance:** All patient data anonymized

### 5. Monitoring & Maintenance
- **Docker logs:** Used for debugging
- **Uptime checks:** Health endpoints
- **Backups:** Manual pg_dump and file sync

---

# DATA_PIPELINE.md

## Data Ingestion & Processing Pipeline

### 1. File Upload & Validation
- **Supported Formats:** CSV, XLSX, Parquet, JSON, XML, PDF, TXT, IMG
- **Upload Endpoint:** `/api/v1/upload/import` (JWT required)
- **Validation:** FileParser checks format, encoding, required columns, missing data
- **Preview:** First 5 rows, column stats

### 2. Column Mapping & Test Catalog
- **ColumnMapper:** Fuzzy matches columns to known lab tests
- **TestManager:** Approves new tests, manages catalog
- **Auto-creation:** New tests added to catalog if unmapped

### 3. Patient Anonymization
- **Anonymizer:** Generates `USMA-2026-XXXX` IDs, hashes sensitive fields
- **Age:** Converted to age range
- **Dates:** Shifted for privacy

### 4. Data Transformation
- **DataTransformer:** Converts rows to SQLAlchemy models
- **Handles:** Numeric/text/mixed values, abnormal detection
- **Unit normalization:** Standardizes units

### 5. Batch Import & Audit Trail
- **BatchImporter:** Imports all patients/labs in transaction
- **Audit Trail:** DataIngestionAudit logs every import (file, status, errors)
- **Rollback:** Per-patient rollback on error

### 6. Disease-Specific Data
- **JSONB Storage:** Flexible for any disease-specific fields
- **No schema changes needed for new diseases**

---

# API_GUIDE.md

## Authentication
- **Login:** `POST /api/v1/auth/login` (returns JWT)
- **Authorize:** Use JWT as `Bearer` token in Swagger or API calls

## Core Endpoints
- **Upload:** `POST /api/v1/upload/import` (file, disease info)
- **List Uploads:** `GET /api/v1/upload/files`
- **Patient Search:** `GET /api/v1/patients/` (filters: disease, age, gender, test, etc.)
- **Patient Details:** `GET /api/v1/patients/{id}`
- **Lab Results:** `GET /api/v1/patients/{id}/labs`
- **Lab Trends:** `GET /api/v1/patients/{id}/labs/trends`
- **Test Statistics:** `GET /api/v1/patients/tests/{test_code}/statistics`
- **Admin Test Catalog:** `GET /api/v1/admin/tests/`

## Example API Calls
- **Login:**
  ```bash
  curl -X POST http://host:8000/api/v1/auth/login -d '{"username":"admin","password":"admin123"}'
  ```
- **Upload File:**
  ```bash
  curl -X POST http://host:8000/api/v1/upload/import -F 'file=@patients.xlsx' -F 'disease_name=SLE' -H 'Authorization: Bearer <token>'
  ```
- **Search Patients:**
  ```bash
  curl -X GET 'http://host:8000/api/v1/patients/?disease_name=sle&limit=10' -H 'Authorization: Bearer <token>'
  ```
- **Get WBC Statistics:**
  ```bash
  curl -X GET 'http://host:8000/api/v1/patients/tests/wbc/statistics' -H 'Authorization: Bearer <token>'
  ```

---

# ARCHITECTURE.md

## System Architecture Diagram

```
+-------------------+      +-------------------+      +-------------------+
|   User/Client     | ---> |   FastAPI Server  | ---> |   PostgreSQL DB   |
+-------------------+      +-------------------+      +-------------------+
        |                        |                          |
        |   (Swagger UI,         |                          |
        |    API calls,          |                          |
        |    File upload)        |                          |
        |                        |                          |
        +------------------------+--------------------------+
                                 |
                                 v
                        +-------------------+
                        |   GPU/ML Server   |
                        +-------------------+
```

- **User/Client:** Swagger UI, API clients, WinSCP for file upload
- **FastAPI Server:** Handles all API logic, data validation, anonymization, ingestion, queries
- **PostgreSQL DB:** Stores all patient, lab, and audit data
- **GPU/ML Server:** (Future) For model training and inference

---

# DEMO_SCRIPT.md

## USM Backend Demo Walkthrough

### 1. Show Swagger UI
- Open `http://<host>:8000/docs`
- Login via `POST /api/v1/auth/login` (admin/admin123)
- Click "Authorize" and paste JWT

### 2. Upload Data
- Use `POST /api/v1/upload/import`
- Upload SLE or Sjogren dataset (CSV/XLSX)
- Fill in disease name, code
- Execute and show response

### 3. Query Data
- Use `GET /api/v1/patients/` to search patients
- Use `GET /api/v1/patients/{id}/labs` to show lab results
- Use `GET /api/v1/patients/tests/wbc/statistics` for statistics

### 4. Show Audit Trail
- Use `GET /api/v1/upload/files` to show upload history
- Show error handling (try uploading bad file)

### 5. Multi-Disease Support
- Upload Sjogren dataset
- Query by `disease_name=sjogren` in patient search

### 6. Q&A
- Invite USM to try endpoints
- Ask for feedback on workflows, missing features

---

# README.md (Sprint 1 Status)

## USM Autoimmune ML Platform - Sprint 1

### What We Built
- High-performance GPU server (RTX 3090, CUDA 12.1)
- Secure Dockerized API (FastAPI + PostgreSQL)
- Flexible database schema (multi-disease, JSONB)
- Data ingestion pipeline (validation, anonymization, audit trail)
- Patient/lab/test query endpoints (40+)
- Admin test management
- Multi-disease support (SLE, Sjogren, ready for more)

### How to Use
1. Upload data via Swagger UI or API
2. Query patients, labs, statistics
3. Review audit trail
4. (Future) Train ML models

### Next Steps
- Import more datasets
- Build EDA dashboard
- Add ML framework shell
- Get USM feedback

---

