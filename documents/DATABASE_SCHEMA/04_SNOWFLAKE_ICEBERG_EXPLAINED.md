# 🏛️ Database Schema Design for USM Autoimmune Platform
## Snowflake vs Star vs EAV - What Your Supervisor Recommended

**Date:** March 23, 2026  
**Context:** SV conversation about rigid database & Snowflake example  
**Question:** What's the best way and plan?

---

## 🤔 The Problem Your SV Identified

**Your Original Approach (Rigid):**
```
patients_table
├── sle_specific_columns (61 columns)
├── sjogren_specific_columns (106 columns)
└── [What happens when we add Rheumatoid Arthritis with 200 columns?]
```

**Issue:** Every new disease = new schema migration = system downtime

---

## 🏗️ Three Design Patterns (What SV Was Comparing)

### **1. Star Schema (Simple)**

```
         ┌─────────────┐
         │ FACT_VISITS │ ← Central fact table
         │ (measures)  │
         └─────────────┘
              │ │ │
      ┌───────┴─┴───────┐
      ↓       ↓     ↓     ↓
┌─────────┐ ┌─────┐ ┌──────┐ ┌──────┐
│DIM      │ │DIM  │ │DIM   │ │DIM   │
│PATIENTS │ │DATE │ │TESTS │ │HOSPS │
└─────────┘ └─────┘ └──────┘ └──────┘
```

**Pros:**
- ✅ Simple queries (1 join)
- ✅ Fast performance
- ✅ Easy to understand

**Cons:**
- ❌ Data duplication (denormalized dimensions)
- ❌ Harder to update dimension data

**Example:**
```sql
-- All patient info repeated in every visit
FACT_VISITS
├── visit_id
├── patient_name  ← Duplicated
├── patient_age   ← Duplicated
├── hospital_name ← Duplicated
└── test_result
```

---

### **2. Snowflake Schema (Normalized) ← YOUR SV RECOMMENDED THIS**

```
         ┌─────────────┐
         │ FACT_VISITS │ ← Central fact table
         │ (measures)  │
         └─────────────┘
              │ │ │
      ┌───────┴─┴───────┐
      ↓       ↓     ↓     ↓
┌─────────┐ ┌─────┐ ┌──────┐ ┌──────┐
│DIM      │ │DIM  │ │DIM   │ │DIM   │
│PATIENTS │ │DATE │ │TESTS │ │HOSPS │
└─────────┘ └─────┘ └──────┘ └──────┘
      ↓                │         ↓
┌──────────┐     ┌─────────┐ ┌──────────┐
│DIM       │     │DIM TEST │ │DIM       │
│DISEASES  │     │CATEGORY │ │LOCATIONS │
│(sub-dim) │     └─────────┘ └──────────┘
└──────────┘
```

**Pros:**
- ✅ **No data duplication** (fully normalized)
- ✅ **Easy to add new diseases** (just INSERT into dim_diseases)
- ✅ **Referential integrity** (foreign keys)
- ✅ **Storage efficient**

**Cons:**
- ❌ More joins in queries (can be slower)
- ❌ Slightly more complex

**Example:**
```sql
-- Fact table only stores IDs
FACT_LAB_RESULTS
├── result_id
├── patient_id  ← FK to dim_patients
├── test_id     ← FK to dim_lab_tests
├── disease_id  ← FK to dim_diseases
└── value

-- Dimension tables normalized
DIM_DISEASES
├── disease_id (PK)
├── disease_name ("SLE")
├── parent_disease_id ← FK to self (hierarchies)
└── category ("Autoimmune")

-- Adding new disease = ONE INSERT
INSERT INTO dim_diseases (disease_name, category) 
VALUES ('Rheumatoid Arthritis', 'Autoimmune');
-- Done! No schema migration needed
```

---

### **3. EAV (Entity-Attribute-Value) Pattern**

```
PATIENTS             LAB_RESULTS (EAV)
├── patient_id       ├── patient_id
└── name             ├── attribute_name ← "WBC", "CRP", etc.
                     └── attribute_value

-- One row per measurement
patient_id | attribute_name | attribute_value
-----------+----------------+----------------
1          | WBC            | 6.5
1          | CRP            | 3.2
1          | IL-12          | 45.7
2          | WBC            | 8.1
```

**Pros:**
- ✅ **Maximum flexibility** (any attribute, any time)
- ✅ **No schema changes ever**

**Cons:**
- ❌ **Terrible query performance** (many rows)
- ❌ **Data type issues** (everything stored as string)
- ❌ **Hard to enforce constraints**

---

### **4. Iceberg Tables (Modern Data Lakehouse) ← YOUR SV ALSO MENTIONED THIS**

```
         Cloud Object Storage (S3/Azure/MinIO)
         ┌─────────────────────────────────────┐
         │ Parquet Files (columnar storage)    │
         │ ├── data_v1.parquet                 │
         │ ├── data_v2.parquet (new version)   │
         │ └── data_v3.parquet                 │
         └─────────────────────────────────────┘
                          ↑
         ┌─────────────────────────────────────┐
         │ Iceberg Metadata Layer              │
         │ ├── Schema versioning               │
         │ ├── Partition evolution             │
         │ ├── Time travel (query any version) │
         │ └── ACID transactions               │
         └─────────────────────────────────────┘
                          ↑
         ┌─────────────────────────────────────┐
         │ Query Engines                        │
         │ Spark, Presto, Trino, Dremio       │
         └─────────────────────────────────────┘
```

**What is Iceberg?**
- Open table format for huge analytic datasets
- Built by Netflix, now Apache project
- **Schema evolution** = add/remove columns without migration
- **Time travel** = query data as it was at any point in time
- **ACID transactions** = consistency across distributed files
- **Hidden partitioning** = users don't need to know data layout

**Key Features:**

1. **Schema Evolution:**
   ```sql
   -- Day 1: Original schema
   CREATE TABLE patients (id INT, name STRING, age INT);
   
   -- Day 30: Add new column (no downtime!)
   ALTER TABLE patients ADD COLUMN disease STRING;
   
   -- Old queries still work!
   SELECT id, name FROM patients;
   
   -- Time travel: Query old schema
   SELECT * FROM patients VERSION AS OF 'v1';
   ```

2. **Snapshot Isolation:**
   ```sql
   -- Each write creates a new snapshot
   Snapshot 1: patients_v1 (100 rows)
   Snapshot 2: patients_v2 (150 rows, added 50)
   Snapshot 3: patients_v3 (140 rows, deleted 10)
   
   -- Query any version
   SELECT * FROM patients FOR SYSTEM_TIME AS OF '2026-03-01';
   ```

3. **Hidden Partitioning:**
   ```sql
   -- Traditional: User must know partitioning
   SELECT * FROM patients 
   WHERE year=2026 AND month=3;  ← User specifies partition
   
   -- Iceberg: Automatic
   SELECT * FROM patients 
   WHERE visit_date = '2026-03-15';  ← Iceberg finds right partition
   ```

**Pros:**
- ✅ **Schema evolution** without downtime
- ✅ **Time travel** for audit/compliance
- ✅ **ACID transactions** on object storage
- ✅ **Works with existing tools** (Spark, Presto, Trino)
- ✅ **Handles petabyte-scale** data

**Cons:**
- ❌ More complex setup (needs metadata layer)
- ❌ Requires object storage (S3/Azure/MinIO)
- ❌ Learning curve for operations team

**When to Use Iceberg:**
- ✅ Data warehouse needs to evolve frequently
- ✅ Need historical queries (time travel)
- ✅ Multi-petabyte datasets
- ✅ Multiple teams querying same data
- ❌ **NOT needed for small OLTP applications**

**Example:**
```sql
-- Iceberg table with your USM data
CREATE TABLE usm_patients (
    patient_id STRING,
    disease_name STRING,
    lab_results MAP<STRING, DOUBLE>  ← Flexible key-value
)
USING iceberg
PARTITIONED BY (days(visit_date))  ← Hidden partitioning
TBLPROPERTIES (
    'format-version'='2',
    'write.metadata.delete-after-commit.enabled'='true'
);

-- Add new disease column (instant, no migration)
ALTER TABLE usm_patients ADD COLUMN genetic_data STRING;

-- Query historical data
SELECT * FROM usm_patients 
TIMESTAMP AS OF '2026-01-01 00:00:00'
WHERE disease_name = 'SLE';
```

---

## 🎯 What Your SV Recommended: **HYBRID APPROACH**

**Combine Snowflake + Iceberg + JSONB where appropriate:**

```sql
-- Layer 1: PostgreSQL (Operational DB) - Snowflake schema for STRUCTURED data
FACT_LAB_RESULTS (Snowflake)
├── patient_id → dim_patients
├── test_id → dim_lab_tests (normalized test catalog)
├── result_value (numeric)
└── result_date → dim_time

-- Layer 2: PostgreSQL - JSONB for VARIABLE disease-specific data
DISEASE_SPECIFIC_DATA (JSONB)
├── patient_id
├── disease_name
├── data JSONB ← Flexible storage
    {
      "SLEDAI_score": 8,
      "kidney_biopsy_class": "III",
      "custom_biomarker_X": 123.4
    }

-- Layer 3: Iceberg (Data Lakehouse) - For long-term storage & analytics
USM_PATIENTS_ICEBERG (Object Storage: MinIO/S3)
├── patient_id
├── disease_name
├── lab_results (nested struct)
├── visit_history (array)
└── metadata (schema version, snapshot ID)
```

**Why This 3-Layer Architecture?**

| Layer | Technology | Purpose | Data Age | Size | Performance |
|-------|------------|---------|----------|------|-------------|
| **Operational DB** | PostgreSQL (Snowflake schema) | Real-time queries, transactions | Last 2 years | <1 TB | Milliseconds |
| **Flexible Storage** | PostgreSQL (JSONB) | Variable disease columns | Last 2 years | <100 GB | Milliseconds |
| **Analytics Lake** | Iceberg (MinIO/S3) | Historical analytics, time travel | All history (10+ years) | 10+ TB | Seconds |

**Your SV's Vision:**
1. **Hot data (PostgreSQL):** Recent 2 years, Snowflake schema, fast OLTP
2. **Cold data (Iceberg):** All historical data, time travel, cheap object storage
3. **Auto-archival:** Move data older than 2 years: PostgreSQL → Iceberg
4. **Unified queries:** Presto/Trino can query both layers together

**Example Workflow:**
```sql
-- Recent data (PostgreSQL - fast!)
SELECT AVG(wbc_count) FROM fact_lab_results 
WHERE patient_id = '123' 
AND result_date > '2024-03-01';  ← Last 2 years
-- Response: 8ms

-- Historical data (Iceberg - still fast!)
SELECT AVG(wbc_count) FROM usm_patients_iceberg
WHERE patient_id = '123'
AND result_date BETWEEN '2015-01-01' AND '2024-03-01';  ← 9 years of history
-- Response: 450ms

-- Combined query (Presto/Trino)
SELECT AVG(wbc_count) FROM (
  SELECT wbc_count FROM fact_lab_results WHERE patient_id = '123'
  UNION ALL
  SELECT wbc_count FROM usm_patients_iceberg WHERE patient_id = '123'
);  ← All 11 years of data!
-- Response: 500ms
```

---

## 📋 The Best Plan (What You Implemented)

### **Your Implementation = Snowflake + JSONB Hybrid**

**1. Snowflake Schema for Core Entities:**
```sql
-- File: init-db/02-flexible-schema.sql

-- Dimension tables (normalized)
dim_patients         (demographics)
dim_diseases         (disease registry - dynamically growable)
dim_lab_tests        (test catalog - dynamically growable)
dim_hospitals        (10 USM hospitals)
dim_medications      (drug registry)
dim_time             (date dimension)

-- Fact tables (measurable events)
fact_patient_visits  (central fact)
fact_lab_results     (measurements)
fact_diagnoses       (patient-disease associations)
fact_prescriptions   (medication history)
```

**2. JSONB for Variable/Unknown Data:**
```sql
-- For disease-specific fields that vary
CREATE TABLE disease_specific_data (
    patient_id UUID,
    disease_name VARCHAR(100),
    data JSONB  ← Flexible storage for unknown attributes
);
```

**3. Metadata Catalog (Auto-Discovery):**
```sql
-- Track what columns we've seen
CREATE TABLE metadata_columns (
    column_id SERIAL PRIMARY KEY,
    source_dataset_id INT,
    column_name VARCHAR(200),
    data_type VARCHAR(50),
    is_registered BOOLEAN  ← Did we add this to schema?
);
```

---

## ✅ Why This Approach is Best

### **Addresses All SV's Concerns:**

1. ✅ **Not Rigid:** New disease = INSERT, not ALTER TABLE
   ```sql
   -- Add Rheumatoid Arthritis
   INSERT INTO dim_diseases (disease_name) VALUES ('RA');
   -- That's it!
   ```

2. ✅ **Snowflake-style Normalization:** No data duplication
   ```sql
   -- Disease info stored once
   dim_diseases: SLE, Lupus, Sjogren
   
   -- Patient-disease links in fact table
   fact_diagnoses: {patient_1 → SLE}, {patient_2 → Sjogren}
   ```

3. ✅ **Handles Variable Columns:** JSONB for unknowns
   ```sql
   -- SLE patient has 61 custom fields
   disease_specific_data: {
     patient_id: 1,
     disease_name: "SLE",
     data: {"SLEDAI": 8, "kidney_biopsy": "III", ...61 more}
   }
   ```

4. ✅ **Performance:** Indexed properly
   ```sql
   CREATE INDEX idx_results_patient ON fact_lab_results(patient_id);
   CREATE INDEX idx_diseases_name ON dim_diseases(disease_name);
   CREATE INDEX idx_data_gin ON disease_specific_data USING GIN(data);
   ```

5. ✅ **Future-proof:** Compatible with Iceberg (data lakehouse)
   ```sql
   -- Comment in your schema file:
   -- "Snowflake/Iceberg Compatible"
   ```

---

## 🗺️ The Complete Plan (What You Documented)

### **Phase 1: Core Schema (Done ✅)**
- [x] Create Snowflake-style Fact/Dimension tables
- [x] Pre-populate dimension catalogs (diseases, tests, hospitals)
- [x] Add metadata tracking tables
- [x] Add audit trail for governance
- [x] Add validation queue for human oversight

**Files:**
- ✅ `init-db/02-flexible-schema.sql` (actual schema)
- ✅ `documents/ARCHITECTURE_REVISION.md` (architecture)
- ✅ `documents/FLEXIBLE-SCHEMA-DESIGN.md` (detailed design)

### **Phase 2: Import Pipeline (In Progress)**
- [ ] Auto-detect new columns in uploads
- [ ] Auto-register new tests in `dim_lab_tests`
- [ ] Store structured data in fact tables
- [ ] Store variable data in JSONB
- [ ] User validates new fields before registration

### **Phase 3: Iceberg Layer (Future - Optional)**
- [ ] Setup MinIO object storage
- [ ] Configure Iceberg catalog (REST or Hive)
- [ ] Create Iceberg tables mirroring PostgreSQL schema
- [ ] Implement auto-archival (PostgreSQL → Iceberg after 2 years)
- [ ] Setup Presto/Trino for unified queries
- [ ] Enable time travel for audit compliance

---

## 🎓 Summary: What Your SV Wanted

**Your SV Said:** "Look at Snowflake schema and Iceberg as examples"

**What SV Meant:**
1. **Use Fact/Dimension tables** (Snowflake schema - not flat tables)
2. **Normalize your dimensions** (no duplication)
3. **Make dimensions growable** (new diseases = INSERT, not ALTER)
4. **Use hierarchies** (parent_disease_id for sub-types)
5. **Keep it flexible** (JSONB for unknowns)
6. **Think long-term** (Iceberg for historical data & time travel)

**What You Delivered:**
- ✅ Snowflake schema with normalized dimensions
- ✅ Flexible disease/test registries
- ✅ JSONB fallback for variable fields
- ✅ Metadata catalog for auto-discovery
- ✅ Audit trail for governance
- ✅ Human validation checkpoints
- ✅ **Iceberg-compatible design** (can migrate to lakehouse later)

**Your Plan Covers:**
1. ✅ Rigid DB problem (solved with Snowflake dimensions)
2. ✅ Variable columns (solved with JSONB hybrid)
3. ✅ New diseases (solved with dynamic registries)
4. ✅ Performance (solved with proper indexing)
5. ✅ Governance (solved with audit trail + validation)
6. ✅ Scalability (Iceberg-ready for future growth)

---

## 📂 Where Everything is Documented

**Your SV's concerns addressed in these files:**

1. **Schema Design Theory:**
   - `documents/FLEXIBLE-SCHEMA-DESIGN.md` ← EAV + JSONB approach
   - `documents/ARCHITECTURE_REVISION.md` ← Snowflake + validation checkpoints

2. **Actual Implementation:**
   - `init-db/02-flexible-schema.sql` ← The real schema (Snowflake-style)

3. **Action Plan:**
   - `documents/PM_FEEDBACK_ACTION_PLAN.md` ← Timeline and tasks

4. **Deployment:**
   - `DEPLOYMENT_CHECKLIST.md` ← How to deploy when server is back

**Missing Document (I just created):**
   - `documents/SNOWFLAKE_SCHEMA_EXPLAINED.md` ← This file (explicit comparison)

---

## ✅ Final Answer to Your SV's Question

**SV's Question:** "What's the best way and plan?"

**Your Answer (Implemented + Future Plan):**

> "We're using a **3-layer architecture: Snowflake (operational) + JSONB (flexible) + Iceberg (analytics)**:
> 
> **Phase 1 (Implemented - Sprint 1):**
> 1. **Core data** (patients, visits, common tests) uses **Snowflake-style Fact/Dimension tables** with full normalization
> 2. **Disease-specific data** (variable columns) uses **JSONB flexible storage** in PostgreSQL
> 3. **New diseases/tests** can be added via **INSERT** (no schema migration)
> 4. **Unknown fields** are **auto-detected** and **await admin approval** before registration
> 5. **Human validation** required at **4 checkpoints** before data is committed
> 6. **Complete audit trail** for governance and compliance
> 
> **Phase 2 (Future - When Data Grows):**
> 7. **Iceberg tables** on MinIO object storage for **long-term historical data** (>2 years)
> 8. **Time travel** capability for audit compliance ("show me data as of Jan 2023")
> 9. **Schema evolution** in Iceberg allows adding columns without downtime
> 10. **Auto-archival** moves old PostgreSQL data → Iceberg for cost savings
> 11. **Presto/Trino** for unified queries across hot (PostgreSQL) and cold (Iceberg) data
> 
> **Benefits:**
> - ✅ Fast operational queries (PostgreSQL Snowflake schema)
> - ✅ Flexible schema (JSONB for unknowns)
> - ✅ Scalable to petabytes (Iceberg lakehouse)
> - ✅ Cost-effective (cold data on cheap object storage)
> - ✅ Time travel for compliance (Iceberg snapshots)
> - ✅ No vendor lock-in (open formats: PostgreSQL, Parquet, Iceberg)"

---

## 🎯 Current Status & Recommendation

### **What's Implemented Now (Sprint 1):**
- ✅ PostgreSQL Snowflake schema (Fact/Dimension tables)
- ✅ JSONB flexible storage for variable columns
- ✅ Dynamic disease/test registries
- ✅ Metadata catalog & audit trail
- ✅ Human validation checkpoints

**SQL File:** `init-db/02-flexible-schema.sql`

### **What's Iceberg-Ready:**
Your current schema is already compatible with Iceberg! The design uses:
- ✅ UUID primary keys (Iceberg-friendly)
- ✅ Timestamp columns for time travel
- ✅ Normalized structure (easy to convert to Parquet)
- ✅ JSONB maps to Iceberg's nested types

### **When to Add Iceberg Layer:**
- ⏰ **1-2 years from now** when data exceeds 1TB
- ⏰ When you need multi-year historical analytics
- ⏰ When storage costs become significant
- ⏰ When audit requires time travel beyond PostgreSQL backups

### **For Your SV Presentation:**
**Present this progression:**
```
TODAY (Sprint 1):
PostgreSQL (Snowflake schema + JSONB)
↓
FUTURE (Year 2):
PostgreSQL (hot data, <2 years) + Iceberg (cold data, >2 years)
↓
LONG-TERM (Year 3+):
Full Data Lakehouse (Iceberg primary, PostgreSQL cache)
```

Show SV you're thinking **strategically** - solving today's problem (flexible schema) while being **future-proof** (Iceberg-compatible design).

---

**Status:** ✅ Your design is solid and addresses all SV's concerns  
**Next:** Deploy when server is stable (40 minutes via DEPLOYMENT_CHECKLIST.md)
