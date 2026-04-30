# 🔧 FLEXIBLE DATABASE DESIGN STRATEGY

**Challenge:** Each autoimmune disease has different biomarkers and test types  
**Solution:** Hybrid approach with fixed + flexible schemas

---

## 🎯 DESIGN PRINCIPLES

### 1. **Core Tables (Fixed Schema)**
Store common fields that ALL patients have:
- Demographics (age, gender)
- Basic identifiers
- Audit trails

### 2. **Test Results (Flexible Schema)**
Store lab results using **Entity-Attribute-Value (EAV) + JSONB** pattern:
- Lab test names are not hardcoded
- Values stored with metadata (units, reference ranges)
- New tests can be added without schema changes

### 3. **Mixed Approach**
- **Common tests** (CBC, CRP, ESR): Use dedicated columns for fast queries
- **Disease-specific tests**: Use JSONB flexible storage
- **Both approaches** coexist in same database

---

## 🗄️ REVISED FLEXIBLE SCHEMA

### **1. patients** (Fixed - Core Demographics)
```sql
CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    anonymous_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Demographics (common to all)
    age INTEGER,
    age_range VARCHAR(20),  -- 20-29, 30-39, etc.
    gender VARCHAR(10),
    
    -- Metadata
    data_source VARCHAR(100),
    import_batch_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_anonymous_id (anonymous_id)
);
```

### **2. diagnoses** (Fixed)
```sql
CREATE TABLE diagnoses (
    diagnosis_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id),
    disease_code VARCHAR(20),
    disease_name VARCHAR(200) NOT NULL,
    diagnosis_date DATE,
    severity VARCHAR(20),
    
    INDEX idx_patient_disease (patient_id, disease_name)
);
```

### **3. lab_test_definitions** (Catalog of All Tests)
```sql
CREATE TABLE lab_test_definitions (
    test_id SERIAL PRIMARY KEY,
    test_code VARCHAR(50) UNIQUE NOT NULL,  -- wbc, crp, ana, cxcl10, etc.
    test_name VARCHAR(200) NOT NULL,
    test_category VARCHAR(100),  -- Hematology, Immunology, Cytokine, etc.
    
    -- Reference ranges (can vary by age/gender)
    default_reference_range JSONB,
    -- Example: {"min": 3.5, "max": 9.5, "unit": "10^9/L"}
    
    unit VARCHAR(50),
    data_type VARCHAR(20),  -- numeric, qualitative, text
    
    -- Related diseases
    relevant_diseases TEXT[],  -- ['SLE', 'Sjogren', 'RA']
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_test_code (test_code),
    INDEX idx_test_category (test_category)
);
```

### **4. lab_results_flexible** (FLEXIBLE - All Lab Results)
```sql
CREATE TABLE lab_results_flexible (
    result_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id),
    test_id INTEGER REFERENCES lab_test_definitions(test_id),
    test_date DATE NOT NULL,
    
    -- Flexible value storage
    value_numeric DECIMAL(15,4),  -- For numeric results
    value_text TEXT,  -- For qualitative (+, ++, Positive, etc) or free text
    value_jsonb JSONB,  -- For complex results (multi-part tests)
    
    -- Metadata about this result
    unit VARCHAR(50),
    reference_range JSONB,
    is_abnormal BOOLEAN,
    abnormal_flag VARCHAR(10),  -- H (high), L (low), etc.
    
    -- Quality indicators
    result_status VARCHAR(20) DEFAULT 'final',  -- preliminary, final, corrected
    specimen_type VARCHAR(50),  -- serum, plasma, saliva, etc.
    
    -- Audit
    uploaded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_patient_test_date (patient_id, test_id, test_date),
    INDEX idx_test_date (test_date),
    
    -- Ensure we have at least one value
    CONSTRAINT chk_has_value CHECK (
        value_numeric IS NOT NULL OR 
        value_text IS NOT NULL OR 
        value_jsonb IS NOT NULL
    )
);
```

### **5. lab_results_batch** (Group Related Tests)
```sql
CREATE TABLE lab_results_batch (
    batch_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id),
    batch_name VARCHAR(200),  -- "CBC Panel", "Autoantibody Panel", "Cytokine Panel"
    test_date DATE NOT NULL,
    
    -- All test results in this batch stored as JSONB
    results JSONB NOT NULL,
    -- Example:
    -- {
    --   "WBC": {"value": 6.5, "unit": "10^9/L", "normal": true},
    --   "NEU%": {"value": 79.1, "unit": "%", "normal": true},
    --   "HGB": {"value": 149, "unit": "g/L", "normal": true}
    -- }
    
    -- Metadata
    panel_type VARCHAR(100),  -- CBC, Autoantibody, Cytokine, etc.
    uploaded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_patient_test_date (patient_id, test_date),
    INDEX idx_panel_type (panel_type),
    INDEX idx_results_gin (results) USING GIN  -- Fast JSON queries
);
```

### **6. disease_specific_data** (Pure JSONB Storage)
```sql
CREATE TABLE disease_specific_data (
    data_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id),
    disease_name VARCHAR(100) NOT NULL,
    data_category VARCHAR(100),  -- clinical_scores, imaging, genetics, etc.
    
    -- Completely flexible storage
    data JSONB NOT NULL,
    -- Example for SLE:
    -- {
    --   "SLEDAI": {"score": 8, "category": "moderate", "date": "2026-03-01"},
    --   "kidney_biopsy": {"class": "III", "activity": 5, "chronicity": 2}
    -- }
    
    -- Example for Sjogren's:
    -- {
    --   "ESSDAI": {"score": 12, "date": "2026-02-15"},
    --   "salivary_flow": {"unstimulated": 0.05, "stimulated": 0.3, "unit": "ml/min"}
    -- }
    
    collection_date DATE,
    
    -- Audit
    uploaded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_patient_disease (patient_id, disease_name),
    INDEX idx_data_gin (data) USING GIN
);
```

### **7. uploaded_files** (Same as before)
```sql
CREATE TABLE uploaded_files (
    file_id SERIAL PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    
    -- Column mapping (important for flexibility!)
    column_mapping JSONB,
    -- Example:
    -- {
    --   "source_columns": ["IL-12 p70", "TNF-alpha", "IFN-gamma"],
    --   "mapped_to": ["il12_p70", "tnf_alpha", "ifn_gamma"],
    --   "unmapped": ["some_unknown_test"]
    -- }
    
    upload_status VARCHAR(20) DEFAULT 'pending',
    validation_errors JSONB,
    
    uploaded_by INTEGER REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_upload_status (upload_status)
);
```

---

## 🔄 HANDLING NEW DATA TYPES

### **Workflow for New Tests/Columns:**

#### 1. **Automatic Detection**
```python
# When new Excel file is uploaded:
def analyze_new_columns(df):
    existing_tests = get_known_test_codes()
    new_columns = []
    
    for col in df.columns:
        normalized_code = normalize_test_name(col)
        if normalized_code not in existing_tests:
            new_columns.append({
                'original_name': col,
                'suggested_code': normalized_code,
                'data_type': detect_data_type(df[col]),
                'sample_values': df[col].head(5).tolist()
            })
    
    return new_columns
```

#### 2. **Admin Approval Required**
```python
POST /api/v1/admin/new-tests/approve
{
    "new_tests": [
        {
            "test_code": "il12_p70",
            "test_name": "IL-12 p70",
            "category": "Cytokine",
            "unit": "pg/ml",
            "reference_range": {"min": 0, "max": 100},
            "relevant_diseases": ["Sjogren", "RA"]
        }
    ]
}
```

#### 3. **Automatic Registration**
```python
def register_new_test(test_info):
    # Insert into lab_test_definitions
    test_id = db.execute("""
        INSERT INTO lab_test_definitions 
        (test_code, test_name, test_category, unit, relevant_diseases)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING test_id
    """, test_info)
    
    # Now available for all future uploads
    return test_id
```

#### 4. **Backward Compatible Storage**
```python
# Even if test is not yet registered, store it anyway:
if test_id is None:
    # Store in disease_specific_data as JSONB
    store_as_jsonb(patient_id, {col: value})
else:
    # Store in lab_results_flexible
    store_as_structured(patient_id, test_id, value)
```

---

## 📊 QUERYING FLEXIBLE DATA

### **Example Queries:**

#### Query 1: Get all lab results for a patient
```sql
-- Structured results
SELECT 
    ltd.test_name,
    lrf.value_numeric,
    lrf.value_text,
    lrf.unit,
    lrf.test_date,
    lrf.is_abnormal
FROM lab_results_flexible lrf
JOIN lab_test_definitions ltd ON lrf.test_id = ltd.test_id
WHERE lrf.patient_id = 123
ORDER BY lrf.test_date DESC;

-- JSONB batch results
SELECT 
    batch_name,
    test_date,
    jsonb_pretty(results) as results
FROM lab_results_batch
WHERE patient_id = 123
ORDER BY test_date DESC;
```

#### Query 2: Find patients with high IL-12 (Sjogren's cytokine)
```sql
-- If IL-12 is registered:
SELECT patient_id, value_numeric, test_date
FROM lab_results_flexible lrf
JOIN lab_test_definitions ltd ON lrf.test_id = ltd.test_id
WHERE ltd.test_code = 'il12_p70'
  AND lrf.value_numeric > 100;

-- If stored in JSONB:
SELECT 
    patient_id,
    data->>'IL-12 p70' as il12_value,
    collection_date
FROM disease_specific_data
WHERE disease_name = 'Sjogren'
  AND (data->>'IL-12 p70')::numeric > 100;
```

#### Query 3: Get all tests available per disease
```sql
SELECT 
    disease_name,
    COUNT(DISTINCT test_id) as test_count,
    array_agg(DISTINCT ltd.test_name) as available_tests
FROM lab_results_flexible lrf
JOIN lab_test_definitions ltd ON lrf.test_id = ltd.test_id
JOIN diagnoses d ON lrf.patient_id = d.patient_id
GROUP BY disease_name;
```

---

## 🚀 MIGRATION STRATEGY

### **Phase 1: Import Existing Data**
```python
# For SLE dataset (61 columns)
def import_sle_data():
    for col in sle_columns:
        # Register test if not exists
        test_id = get_or_create_test(col)
        
        # Import values
        for patient in patients:
            insert_lab_result(patient, test_id, value)

# For Sjogren dataset (106 columns)
def import_sjogren_data():
    for col in sjogren_columns:
        # Register test if not exists
        test_id = get_or_create_test(col)
        
        # Import values
        for patient in patients:
            insert_lab_result(patient, test_id, value)
```

### **Phase 2: Handle Future Datasets**
```python
def import_new_disease_data(file_path, disease_name):
    df = pd.read_excel(file_path)
    
    # Auto-detect columns
    new_tests = detect_new_columns(df)
    
    if new_tests:
        # Ask admin to approve
        approval = request_admin_approval(new_tests)
        
        if approval:
            # Register new tests
            for test in new_tests:
                register_test(test)
    
    # Import data (works for any disease)
    import_generic_data(df, disease_name)
```

---

## 🎯 ADVANTAGES OF THIS APPROACH

### ✅ **Flexibility**
- Add new diseases without changing schema
- Add new lab tests without migration
- Support any number of columns

### ✅ **Backward Compatibility**
- Old data still queryable
- No data loss when adding new fields
- Can migrate JSONB to structured later

### ✅ **Performance**
- GIN indexes on JSONB for fast queries
- Common tests in dedicated columns (fast)
- Can add materialized views for frequent queries

### ✅ **Data Integrity**
- Reference data in lab_test_definitions
- Foreign keys for patient/test relationships
- Validation rules in application layer

### ✅ **Future-Proof**
- Supports unknown test types
- Can handle imaging data, genetic data, etc.
- Easy to extend with new categories

---

## 🔮 HANDLING FUTURE SCENARIOS

### Scenario 1: "New disease: Rheumatoid Arthritis with 200 new biomarkers"
**Solution:**
1. Upload file → System detects 200 new columns
2. Admin reviews and approves tests with categories
3. Tests registered in `lab_test_definitions`
4. Data imported to `lab_results_flexible`
5. RA patients queryable alongside SLE/Sjogren patients

### Scenario 2: "Researcher wants to add genetic data (SNPs, variants)"
**Solution:**
1. Create new category: "Genetics"
2. Store in `disease_specific_data` with JSONB:
   ```json
   {
     "snp_data": {
       "rs1234": {"allele": "A/G", "zygosity": "heterozygous"},
       "rs5678": {"allele": "T/T", "zygosity": "homozygous"}
     }
   }
   ```
3. No schema change needed

### Scenario 3: "Need to track medication history"
**Solution:**
1. Add new table OR use `disease_specific_data`:
   ```json
   {
     "medications": [
       {"name": "Hydroxychloroquine", "dose": "200mg", "start": "2025-01-15"},
       {"name": "Prednisone", "dose": "10mg", "start": "2025-03-01"}
     ]
   }
   ```

### Scenario 4: "Lab changes reference ranges"
**Solution:**
1. Update in `lab_test_definitions.default_reference_range`
2. Old results keep their original reference ranges in `lab_results_flexible.reference_range`
3. Historical comparison possible

---

## 📝 IMPLEMENTATION CHECKLIST

### Sprint 1 (This Sprint)
- [ ] Create flexible schema tables
- [ ] Build `lab_test_definitions` catalog (seed with SLE + Sjogren tests)
- [ ] Implement JSONB storage for batch results
- [ ] Create import pipeline with auto-detection
- [ ] Admin UI for approving new tests
- [ ] Query functions for both structured + JSONB data

### Sprint 2 (Future)
- [ ] Materialized views for common queries
- [ ] Full-text search on test names
- [ ] Advanced analytics across diseases
- [ ] Data visualization for mixed data types
- [ ] Machine learning feature extraction from JSONB

---

**Status:** ✅ Design Complete - Ready for Implementation  
**Next:** Create migration scripts with flexible schema

