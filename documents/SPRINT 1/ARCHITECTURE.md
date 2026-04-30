# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  Swagger UI  │  API Clients  │  WinSCP  │  Python SDK  │  cURL  │
└──────┬──────────────┬──────────────┬──────────────┬─────────────┘
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                        │
                        ▼ HTTPS/JWT
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                    FastAPI Application                           │
│                  (http://172.24.175.24:8000)                    │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Auth Router  │  │Upload Router │  │Patient Router│         │
│  │  /auth/*     │  │ /upload/*    │  │ /patients/*  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Admin Router │  │Predict Router│  │Health Router │         │
│  │  /admin/*    │  │ /predict/*   │  │   /health    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │  FileParser     │  │  ColumnMapper   │  │  Anonymizer    │ │
│  │  Validation     │  │  Fuzzy Match    │  │  SHA-256       │ │
│  └─────────────────┘  └─────────────────┘  └────────────────┘ │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │ DataTransformer │  │ BatchImporter   │  │  QueryService  │ │
│  │ Parse Values    │  │ Transaction Mgmt│  │  Advanced SQL  │ │
│  └─────────────────┘  └─────────────────┘  └────────────────┘ │
│                                                                  │
│  ┌─────────────────┐                                            │
│  │  TestManager    │                                            │
│  │  Catalog Mgmt   │                                            │
│  └─────────────────┘                                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼ SQLAlchemy ORM
┌─────────────────────────────────────────────────────────────────┐
│                      DATA ACCESS LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                   SQLAlchemy Models                              │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │
│  │  Patient    │  │  Diagnosis  │  │  LabTestDefinition  │    │
│  └─────────────┘  └─────────────┘  └─────────────────────┘    │
│                                                                  │
│  ┌──────────────────┐  ┌───────────────────┐  ┌──────────┐    │
│  │LabResultFlexible │  │  DiseaseSpecific  │  │  Upload  │    │
│  └──────────────────┘  └───────────────────┘  └──────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼ PostgreSQL Protocol
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│               PostgreSQL 15 (Docker Container)                   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               usm_autoimmune_registry                     │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  Tables: patients, diagnoses, lab_test_definitions,      │  │
│  │          lab_results_flexible, disease_specific_data,    │  │
│  │          uploaded_files, data_ingestion_audit,           │  │
│  │          lab_result_batch, users                         │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  Indexes: B-tree (FKs, IDs), GIN (JSONB fields)          │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  Storage: Persistent volume (/var/lib/postgresql/data)   │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│              GPU Server (Ubuntu 24.04.2 LTS)                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Docker Engine + Docker Compose                          │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  Containers:                                              │  │
│  │    • usm-autoimmune-api    (FastAPI)                     │  │
│  │    • usm-autoimmune-postgres (PostgreSQL 15)             │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  GPU: NVIDIA RTX 3090 (24GB VRAM)                        │  │
│  │  CUDA: 12.1.0                                             │  │
│  │  Python: 3.10 in /opt/venv                               │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  Network: ZeroTier VPN (172.24.175.24)                   │  │
│  │  Storage: 1TB NVMe SSD                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### Client Layer
**Purpose:** User interaction and API consumption

**Components:**
- **Swagger UI** - Interactive API documentation and testing
- **API Clients** - Python SDK, JavaScript fetch, curl
- **WinSCP** - File upload via SFTP (for large files)
- **Python SDK** - Programmatic access to API

**Authentication:** JWT Bearer tokens (12-hour expiry)

---

### API Gateway Layer
**Purpose:** Route requests, authenticate, validate input

**Technology:** FastAPI (Python 3.10)

**Routers:**
1. **Auth Router** (`/api/v1/auth/*`)
   - Login, token generation, user management
   
2. **Upload Router** (`/api/v1/upload/*`)
   - File upload, import datasets, list uploads
   
3. **Patient Router** (`/api/v1/patients/*`)
   - Search patients, get details, lab results, trends, statistics
   
4. **Admin Router** (`/api/v1/admin/*`)
   - Test catalog management, approval workflows
   
5. **Predict Router** (`/api/v1/predict/*`)
   - ML model inference (future implementation)
   
6. **Health Router** (`/health`)
   - System health checks

**Middleware:**
- CORS (allow all origins for now)
- JWT authentication
- Request logging
- Error handling

**Security:**
- JWT tokens with HS256 signing
- Password hashing (bcrypt)
- SQL injection protection (SQLAlchemy ORM)
- Input validation (Pydantic)

---

### Service Layer
**Purpose:** Business logic, data processing, aggregations

**Services:**

1. **FileParser** (`app/services/file_parser.py`)
   - Read CSV/Excel/Parquet/JSON/XML
   - Validate file format and structure
   - Generate preview and statistics
   
2. **ColumnMapper** (`app/services/column_mapper.py`)
   - Fuzzy match columns to lab test catalog
   - Confidence scoring
   - Suggest new tests
   
3. **PatientAnonymizer** (`app/services/anonymizer.py`)
   - Generate anonymous IDs (USMA-2026-XXXX)
   - Hash sensitive fields (SHA-256)
   - Age range conversion
   - Date shifting
   
4. **DataTransformer** (`app/services/data_transformer.py`)
   - Parse numeric/text/mixed values
   - Detect abnormal results
   - Build SQLAlchemy models
   - Extract JSONB disease-specific data
   
5. **BatchImporter** (`app/services/batch_importer.py`)
   - Transaction-based bulk insert
   - Per-patient error handling
   - Audit trail creation
   
6. **QueryService** (`app/services/query_service.py`)
   - Advanced SQL queries (joins, aggregations)
   - Patient search with filters
   - Lab trends (time series)
   - Test statistics (mean, median, std)
   - JSONB queries
   
7. **TestManager** (`app/services/test_manager.py`)
   - Lab test catalog CRUD
   - Approval workflows
   - Category management

---

### Data Access Layer
**Purpose:** ORM models, database abstraction

**Technology:** SQLAlchemy 2.0

**Models:**

1. **Patient** - Demographics, anonymous ID
2. **Diagnosis** - Disease diagnoses (1:N with Patient)
3. **LabTestDefinition** - Lab test catalog
4. **LabResultFlexible** - Individual lab results (1:N with Patient)
5. **LabResultBatch** - Panel test results (JSONB)
6. **DiseaseSpecificData** - Disease-specific fields (JSONB)
7. **UploadedFile** - File metadata and mappings
8. **DataIngestionAudit** - Import audit trail
9. **User** - Authentication users

**Relationships:**
```
Patient (1) ─┬─ (N) Diagnosis
             ├─ (N) LabResultFlexible
             ├─ (N) LabResultBatch
             └─ (N) DiseaseSpecificData

LabTestDefinition (1) ─── (N) LabResultFlexible

UploadedFile (1) ─── (N) DataIngestionAudit
```

**Cascade Deletes:**
- Delete Patient → Deletes all associated Diagnoses, LabResults, DiseaseData
- Delete LabTestDefinition → Restrict (cannot delete if results exist)

---

### Database Layer
**Purpose:** Persistent data storage

**Technology:** PostgreSQL 15

**Database:** `usm_autoimmune_registry`

**Schema Highlights:**
- **8 tables** (patients, diagnoses, lab tests, results, uploads, audit)
- **JSONB fields** for flexible data (additional_data, reference_ranges, disease_data)
- **GIN indexes** on JSONB for fast queries
- **B-tree indexes** on foreign keys and frequently queried columns
- **Nullable test_date** to handle missing dates

**Storage:**
- Docker volume: `/var/lib/postgresql/data` (persistent)
- Backups: Manual pg_dump (scheduled via cron)

**Performance:**
- Connection pooling (SQLAlchemy default: 5-20 connections)
- Batch inserts (500 rows per transaction)
- JSONB queries using operators (`@>`, `?`, `->>`)

---

### Infrastructure Layer
**Purpose:** Hosting, compute, GPU acceleration

**Server Specs:**
- **OS:** Ubuntu 24.04.2 LTS
- **GPU:** NVIDIA RTX 3090 (24GB VRAM)
- **CPU:** 16-core Xeon
- **RAM:** 128GB DDR4
- **Storage:** 1TB NVMe SSD
- **Network:** ZeroTier VPN (172.24.175.24)

**Containerization:**
- **Docker Engine** - Container runtime
- **Docker Compose** - Multi-container orchestration

**Containers:**
1. **usm-autoimmune-api**
   - Base: nvidia/cuda:12.1.0-base-ubuntu22.04
   - Python 3.10 + FastAPI + scikit-learn
   - Port: 8000 (exposed)
   - Volume: /app (code), /uploads (files)
   
2. **usm-autoimmune-postgres**
   - Base: postgres:15
   - Port: 5432 (internal only)
   - Volume: /var/lib/postgresql/data (persistent)
   - Init scripts: /docker-entrypoint-initdb.d/

**CUDA Setup:**
- CUDA Toolkit 12.1.0
- cuDNN (included in NVIDIA container)
- NVIDIA drivers 550+
- PyTorch, TensorFlow, scikit-learn installed

**Security:**
- SSH key-based authentication
- Firewall: Only ports 22, 8000 open
- Database not exposed externally
- JWT for API authentication

---

## Data Flow Diagrams

### Import Pipeline Flow

```
┌─────────────┐
│  User       │
│  uploads    │
│  Excel file │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────┐
│ 1. FileParser                     │
│    • Validate format              │
│    • Detect encoding              │
│    • Read into DataFrame          │
│    • Generate preview             │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 2. ColumnMapper                   │
│    • Fuzzy match to test catalog │
│    • Calculate confidence scores │
│    • Flag unmapped columns       │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 3. PatientAnonymizer              │
│    • Generate USMA-2026-XXXX ID  │
│    • Hash sensitive fields       │
│    • Convert age to range        │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 4. DataTransformer                │
│    • Parse numeric/text values   │
│    • Detect abnormal flags       │
│    • Build SQLAlchemy models     │
│    • Extract JSONB data          │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 5. BatchImporter                  │
│    • Start transaction            │
│    • Insert patients in batch    │
│    • Per-patient error handling  │
│    • Create audit record         │
│    • Commit successful           │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ PostgreSQL Database               │
│    • patients table               │
│    • diagnoses table              │
│    • lab_results_flexible table  │
│    • disease_specific_data table │
│    • data_ingestion_audit table  │
└───────────────────────────────────┘
```

---

### Query Pipeline Flow

```
┌─────────────┐
│  User       │
│  queries    │
│  patients   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────┐
│ Patient Router                    │
│    GET /api/v1/patients/          │
│    • Validate query params        │
│    • Authenticate JWT             │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ QueryService                      │
│    • Build SQL query              │
│    • Apply filters (disease, age) │
│    • Join tables (Patient ⟕      │
│      Diagnosis ⟕ LabResults)     │
│    • Aggregate if needed          │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ SQLAlchemy ORM                    │
│    • Generate SQL                 │
│    • Execute query                │
│    • Map results to models        │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ PostgreSQL Database               │
│    • Run query                    │
│    • Use indexes (B-tree, GIN)   │
│    • Return results               │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ Patient Router                    │
│    • Serialize to JSON            │
│    • Add pagination metadata      │
│    • Return HTTP 200              │
└──────┬───────────────────────────┘
       │
       ▼
┌─────────────┐
│  User       │
│  receives   │
│  JSON data  │
└─────────────┘
```

---

## Deployment Architecture

### Docker Compose Setup

```yaml
version: '3.8'

services:
  api:
    container_name: usm-autoimmune-api
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app
      - ./uploads:/uploads
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/usm_autoimmune_registry
      - JWT_SECRET_KEY=your-secret-key
    depends_on:
      - postgres
    restart: unless-stopped
    
  postgres:
    container_name: usm-autoimmune-postgres
    image: postgres:15
    ports:
      - "5432:5432"  # Only for local access
    volumes:
      - ./init-db:/docker-entrypoint-initdb.d
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=usm_admin
      - POSTGRES_PASSWORD=secure_password
      - POSTGRES_DB=usm_autoimmune_registry
    restart: unless-stopped

volumes:
  postgres_data:
```

### Network Diagram

```
Internet
    │
    │ SSH (Port 22)
    ▼
┌────────────────────────────────────┐
│  ZeroTier VPN (172.24.175.24)     │
│  Remote Access Gateway             │
└────────┬───────────────────────────┘
         │
         │ HTTPS (Port 8000)
         ▼
┌────────────────────────────────────┐
│  Docker Bridge Network             │
│  (172.17.0.0/16)                   │
│                                     │
│  ┌──────────────┐  ┌─────────────┐│
│  │ API:8000     │  │ DB:5432     ││
│  │ (172.17.0.2) │  │(172.17.0.3) ││
│  └──────────────┘  └─────────────┘│
└────────────────────────────────────┘
         │
         │ Internal Communication
         ▼
    PostgreSQL
```

---

## Scalability Considerations

### Current Scale (Sprint 1)
- **Patients:** 52 imported, tested up to 500
- **Lab Results:** ~5,000 results
- **Concurrent Users:** 1-5 (single admin)
- **Response Time:** <500ms for most queries

### Future Scaling Strategies

**For 10K-100K Patients:**
- Add read replicas (PostgreSQL streaming replication)
- Implement Redis caching (test catalog, frequent queries)
- Use connection pooling (PgBouncer)
- Partition tables by year or disease

**For 100K-1M Patients:**
- Migrate to TimescaleDB (optimized for time-series lab data)
- Add Elasticsearch for full-text search
- Implement async Celery workers for imports
- Add load balancer (multiple API instances)

**For >1M Patients:**
- Sharding by disease or geography
- Use object storage (S3/MinIO) for files
- Add message queue (RabbitMQ/Kafka) for events
- Consider Kubernetes orchestration

---

## Security Architecture

### Authentication Flow
```
User → Login (username/password)
       ↓
    Verify credentials (bcrypt hash check)
       ↓
    Generate JWT token (HS256, 12-hour expiry)
       ↓
    Return token to user
       ↓
User → API call with token in Authorization header
       ↓
    Validate JWT (signature, expiry)
       ↓
    Extract user info (username, permissions)
       ↓
    Execute request
```

### Data Security Layers
1. **Transport:** HTTPS (in production)
2. **Authentication:** JWT Bearer tokens
3. **Authorization:** Role-based (admin, researcher, viewer)
4. **Database:** Passwords hashed (bcrypt), data anonymized
5. **Network:** Internal database (not exposed), ZeroTier VPN

### Privacy Compliance
- **NMRR Compliant:** Patient data anonymized, no direct identifiers
- **SHA-256 Hashing:** One-way, cannot reverse
- **Age Ranges:** Not exact ages
- **Date Shifting:** Prevents temporal re-identification
- **Audit Trail:** All imports logged with timestamps

---

## Monitoring & Observability

### Current Status (Minimal)
- **Health Endpoint:** `/health` - Basic health check
- **Docker Logs:** `docker logs usm-autoimmune-api`
- **Database Logs:** PostgreSQL logs in container

### Future Implementation
- **Prometheus** - Metrics collection (request rate, latency, errors)
- **Grafana** - Dashboards (API performance, DB queries, imports)
- **Sentry** - Error tracking and alerting
- **ELK Stack** - Centralized logging (Elasticsearch, Logstash, Kibana)

**Metrics to Track:**
- API request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database query time
- Import success rate
- Active users

---

## Backup & Disaster Recovery

### Current Backup Strategy
- **Database:** Manual `pg_dump` (weekly)
- **Code:** Git repository (GitHub/GitLab)
- **Uploads:** Manual file sync

### Recommended Strategy
- **Automated Backups:** Daily pg_dump + S3/MinIO upload
- **Point-in-Time Recovery:** PostgreSQL WAL archiving
- **Retention:** 30 days hot, 1 year cold storage
- **Disaster Recovery:** Multi-region replication

---

## Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| **OS** | Ubuntu | 24.04.2 LTS |
| **Container** | Docker | 24.0+ |
| **Orchestration** | Docker Compose | 2.20+ |
| **Web Framework** | FastAPI | 0.108.0 |
| **Python** | Python | 3.10 |
| **ORM** | SQLAlchemy | 2.0+ |
| **Database** | PostgreSQL | 15 |
| **GPU** | NVIDIA RTX | 3090 (24GB) |
| **CUDA** | NVIDIA CUDA | 12.1.0 |
| **Auth** | JWT | HS256 |
| **Password** | bcrypt | Latest |
| **API Docs** | Swagger/OpenAPI | 3.0 |

---

## Future Architecture (Phase 2)

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND LAYER                          │
│   React/Vue Dashboard  │  Streamlit EDA  │  Jupyter Hub     │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY (Current)                   │
│                      + ML Prediction API                     │
└──────────────┬──────────────────────────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌──────────────┐  ┌───────────────────┐
│ Data Layer   │  │  ML Training Layer│
│ (Current)    │  │  • Feature Eng    │
│              │  │  • Model Training │
│              │  │  • Hyperparameter │
│              │  │  • Model Registry │
└──────────────┘  └───────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Model Serving   │
                  │ • Inference API │
                  │ • Batch Predict │
                  └─────────────────┘
```

---

## Next Steps

1. **Document Code:** Add docstrings, type hints
2. **Add Tests:** Unit tests for services, integration tests for API
3. **Implement Monitoring:** Prometheus + Grafana
4. **Add ML Layer:** Feature engineering, model training
5. **Build Frontend:** React dashboard or Streamlit
6. **Performance Testing:** Load testing with locust/k6
7. **Security Audit:** Penetration testing, code review
