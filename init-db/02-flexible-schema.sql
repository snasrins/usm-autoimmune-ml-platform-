-- =====================================================
-- USM Autoimmune ML Platform - Flexible Schema Design
-- Fact/Dimension Tables (Data Warehouse Style)
-- Date: March 20, 2026
-- Based on PM Feedback - Snowflake/Iceberg Compatible
-- =====================================================

-- =====================================================
-- DIMENSION TABLES (Descriptive Attributes)
-- =====================================================

-- DIMENSION: Patients (High-Level Entity)
CREATE TABLE dim_patients (
    patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anonymous_id VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 hash of real ID
    age_range VARCHAR(20),  
    gender VARCHAR(10),
    ethnicity VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_age_range CHECK (age_range ~ '^\d+-\d+$')
);

CREATE INDEX idx_patients_anonymous ON dim_patients(anonymous_id);
COMMENT ON TABLE dim_patients IS 'High-level patient entity - flexible, can branch to specific cohorts';

-- DIMENSION: Diseases (Flexible - Can Add New Without Schema Change)
CREATE TABLE dim_diseases (
    disease_id SERIAL PRIMARY KEY,
    disease_name VARCHAR(100) NOT NULL UNIQUE,  -- "SLE", "Lupus", "Sjogren", "IBD", etc.
    disease_category VARCHAR(50),  -- "Autoimmune", "Infectious", "Metabolic", etc.
    icd10_code VARCHAR(10),
    parent_disease_id INT REFERENCES dim_diseases(disease_id),  -- For hierarchies (e.g., Lupus → SLE)
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_diseases_category ON dim_diseases(disease_category);
COMMENT ON TABLE dim_diseases IS 'Flexible disease registry - new diseases can be added dynamically';

-- SEED DATA: Standard disease codes (ICD-10) - Can be customized for your institution
-- OPTIONAL: Comment out if you want to add diseases manually
INSERT INTO dim_diseases (disease_name, disease_category, icd10_code) VALUES
('Systemic Lupus Erythematosus (SLE)', 'Autoimmune', 'M32.9'),
('Rheumatoid Arthritis (RA)', 'Autoimmune', 'M06.9'),
('Multiple Sclerosis (MS)', 'Autoimmune', 'G35'),
('Inflammatory Bowel Disease (IBD)', 'Autoimmune', 'K50-K51'),
('Sjogren Syndrome', 'Autoimmune', 'M35.0'),
('Lupus Nephritis', 'Autoimmune', 'M32.14'),
('Chronic Kidney Disease (CKD)', 'Renal', 'N18'),
('Cardiovascular Disease (CVD)', 'Cardiovascular', 'I25.10'),
('Type 2 Diabetes', 'Metabolic', 'E11'),
('Cancer (General)', 'Oncology', 'C80'),
('Mental Health Disorders', 'Psychiatric', 'F99'),
('Obesity', 'Metabolic', 'E66');

-- DIMENSION: Lab Tests (Dynamically Registered)
CREATE TABLE dim_lab_tests (
    test_id SERIAL PRIMARY KEY,
    test_name VARCHAR(100) NOT NULL,
    test_code VARCHAR(50) UNIQUE,  -- LOINC or local code
    category VARCHAR(50),  -- "Hematology", "Immunology", "Chemistry", etc.
    unit VARCHAR(20),
    normal_range_min FLOAT,
    normal_range_max FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lab_tests_category ON dim_lab_tests(category);
COMMENT ON TABLE dim_lab_tests IS 'Dynamically registered lab tests - auto-populated on first encounter';

-- Pre-populate with common autoimmune tests
INSERT INTO dim_lab_tests (test_name, test_code, category, unit, normal_range_min, normal_range_max) VALUES
('White Blood Cell Count (WBC)', 'WBC', 'Hematology', 'x10^9/L', 4.0, 11.0),
('Hemoglobin (Hb)', 'HB', 'Hematology', 'g/dL', 12.0, 16.0),
('Platelet Count', 'PLT', 'Hematology', 'x10^9/L', 150.0, 400.0),
('Erythrocyte Sedimentation Rate (ESR)', 'ESR', 'Hematology', 'mm/hr', 0.0, 20.0),
('C-Reactive Protein (CRP)', 'CRP', 'Immunology', 'mg/L', 0.0, 5.0),
('Anti-Nuclear Antibody (ANA)', 'ANA', 'Immunology', 'titer', 0.0, 1.0),
('Anti-dsDNA', 'DSDNA', 'Immunology', 'IU/mL', 0.0, 30.0),
('Complement C3', 'C3', 'Immunology', 'g/L', 0.9, 1.8),
('Complement C4', 'C4', 'Immunology', 'g/L', 0.1, 0.4),
('Creatinine', 'CREAT', 'Chemistry', 'mg/dL', 0.6, 1.2);

-- DIMENSION: Hospitals (10 USM Hospitals)
CREATE TABLE dim_hospitals (
    hospital_id SERIAL PRIMARY KEY,
    hospital_name VARCHAR(100) NOT NULL,
    hospital_code VARCHAR(20) UNIQUE,
    location VARCHAR(100),
    region VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE dim_hospitals IS 'USM hospitals providing data - Add your actual hospitals via admin interface';

-- IMPORTANT: Replace these placeholder hospitals with your actual hospital data!
-- RECOMMENDED: Add hospitals via admin API endpoint instead of hardcoding here
-- 
-- Example API call to add hospital:
-- POST /api/v1/admin/hospitals
-- {
--   "hospital_name": "Hospital Universiti Sains Malaysia",
--   "hospital_code": "HUSM",
--   "location": "Kubang Kerian, Kelantan",
--   "region": "East Coast"
-- }
--
-- PLACEHOLDER DATA (DELETE AFTER ADDING REAL HOSPITALS):
/*
INSERT INTO dim_hospitals (hospital_name, hospital_code, location, region) VALUES
('Hospital USM 1', 'HUSM1', 'Kuala Lumpur', 'Central'),
('Hospital USM 2', 'HUSM2', 'Penang', 'North'),
('Hospital USM 3', 'HUSM3', 'Johor', 'South'),
('Hospital USM 4', 'HUSM4', 'Sabah', 'East Malaysia'),
('Hospital USM 5', 'HUSM5', 'Sarawak', 'East Malaysia'),
('Hospital USM 6', 'HUSM6', 'Perak', 'North'),
('Hospital USM 7', 'HUSM7', 'Melaka', 'South'),
('Hospital USM 8', 'HUSM8', 'Kedah', 'North'),
('Hospital USM 9', 'HUSM9', 'Terengganu', 'East Coast'),
('Hospital USM 10', 'HUSM10', 'Kelantan', 'East Coast');
*/

-- DIMENSION: Medications (Flexible Registry)
CREATE TABLE dim_medications (
    medication_id SERIAL PRIMARY KEY,
    drug_name VARCHAR(100) NOT NULL,
    generic_name VARCHAR(100),
    brand_name VARCHAR(100),
    drug_class VARCHAR(50),  -- "Immunosuppressant", "Corticosteroid", etc.
    dosage_form VARCHAR(50),  -- "Tablet", "Injection", "Capsule", etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_medications_class ON dim_medications(drug_class);
COMMENT ON TABLE dim_medications IS 'Flexible medication registry - auto-populated from prescriptions';

-- Pre-populate with common autoimmune medications
INSERT INTO dim_medications (drug_name, generic_name, drug_class, dosage_form) VALUES
('Hydroxychloroquine', 'Hydroxychloroquine Sulfate', 'Antimalarial', 'Tablet'),
('Prednisolone', 'Prednisolone', 'Corticosteroid', 'Tablet'),
('Methotrexate', 'Methotrexate', 'Immunosuppressant', 'Tablet'),
('Azathioprine', 'Azathioprine', 'Immunosuppressant', 'Tablet'),
('Mycophenolate', 'Mycophenolate Mofetil', 'Immunosuppressant', 'Capsule'),
('Rituximab', 'Rituximab', 'Biologic', 'Injection'),
('Belimumab', 'Belimumab', 'Biologic', 'Injection');

-- DIMENSION: Time (For Time-Series Analysis)
CREATE TABLE dim_time (
    date_id INT PRIMARY KEY,  -- Format: YYYYMMDD (e.g., 20260320)
    full_date DATE NOT NULL UNIQUE,
    year INT NOT NULL,
    month INT NOT NULL,
    quarter INT NOT NULL,
    day_of_week INT NOT NULL,  -- 1=Monday, 7=Sunday
    is_weekend BOOLEAN NOT NULL,
    month_name VARCHAR(20),
    quarter_name VARCHAR(5)  -- "Q1", "Q2", etc.
);

CREATE INDEX idx_time_year_month ON dim_time(year, month);
COMMENT ON TABLE dim_time IS 'Time dimension for temporal analysis';

-- Populate time dimension (2020-2030)
INSERT INTO dim_time (date_id, full_date, year, month, quarter, day_of_week, is_weekend, month_name, quarter_name)
SELECT 
    TO_CHAR(d, 'YYYYMMDD')::INT,
    d,
    EXTRACT(YEAR FROM d)::INT,
    EXTRACT(MONTH FROM d)::INT,
    EXTRACT(QUARTER FROM d)::INT,
    EXTRACT(ISODOW FROM d)::INT,
    EXTRACT(ISODOW FROM d) IN (6, 7),
    TO_CHAR(d, 'Month'),
    'Q' || EXTRACT(QUARTER FROM d)::TEXT
FROM generate_series('2020-01-01'::DATE, '2030-12-31'::DATE, '1 day'::INTERVAL) AS d;

-- =====================================================
-- FACT TABLES (Measurable Events)
-- =====================================================

-- FACT: Patient Visits (Central Fact Table)
CREATE TABLE fact_patient_visits (
    visit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES dim_patients(patient_id),
    hospital_id INT NOT NULL REFERENCES dim_hospitals(hospital_id),
    visit_date DATE NOT NULL,
    date_id INT NOT NULL REFERENCES dim_time(date_id),
    visit_type VARCHAR(50),  -- "Inpatient", "Outpatient", "Emergency"
    admission_reason TEXT,
    discharge_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_visits_patient ON fact_patient_visits(patient_id);
CREATE INDEX idx_visits_date ON fact_patient_visits(visit_date);
CREATE INDEX idx_visits_hospital ON fact_patient_visits(hospital_id);
COMMENT ON TABLE fact_patient_visits IS 'Central fact table - patient hospital visits';

-- FACT: Lab Results (Measurable Data)
CREATE TABLE fact_lab_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    visit_id UUID REFERENCES fact_patient_visits(visit_id),
    patient_id UUID NOT NULL REFERENCES dim_patients(patient_id),
    test_id INT NOT NULL REFERENCES dim_lab_tests(test_id),
    result_value FLOAT,
    result_text TEXT,  -- For qualitative results (e.g., "Positive", "Negative")
    is_abnormal BOOLEAN,
    result_date DATE NOT NULL,
    date_id INT NOT NULL REFERENCES dim_time(date_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lab_results_patient ON fact_lab_results(patient_id);
CREATE INDEX idx_lab_results_test ON fact_lab_results(test_id);
CREATE INDEX idx_lab_results_date ON fact_lab_results(result_date);
COMMENT ON TABLE fact_lab_results IS 'Lab test results - measurable clinical data';

-- FACT: Diagnoses (Patient-Disease Associations)
CREATE TABLE fact_diagnoses (
    diagnosis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    visit_id UUID REFERENCES fact_patient_visits(visit_id),
    patient_id UUID NOT NULL REFERENCES dim_patients(patient_id),
    disease_id INT NOT NULL REFERENCES dim_diseases(disease_id),
    diagnosis_date DATE NOT NULL,
    date_id INT NOT NULL REFERENCES dim_time(date_id),
    severity VARCHAR(20),  -- "Mild", "Moderate", "Severe"
    is_primary BOOLEAN DEFAULT FALSE,  -- Primary vs secondary diagnosis
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_diagnoses_patient ON fact_diagnoses(patient_id);
CREATE INDEX idx_diagnoses_disease ON fact_diagnoses(disease_id);
CREATE INDEX idx_diagnoses_date ON fact_diagnoses(diagnosis_date);
COMMENT ON TABLE fact_diagnoses IS 'Patient diagnoses - disease associations';

-- FACT: Medication Prescriptions
CREATE TABLE fact_prescriptions (
    prescription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    visit_id UUID REFERENCES fact_patient_visits(visit_id),
    patient_id UUID NOT NULL REFERENCES dim_patients(patient_id),
    medication_id INT NOT NULL REFERENCES dim_medications(medication_id),
    dosage VARCHAR(50),  -- "200mg", "5mg/kg", etc.
    frequency VARCHAR(50),  -- "Once daily", "Twice daily", etc.
    route VARCHAR(30),  -- "Oral", "IV", "Subcutaneous", etc.
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prescriptions_patient ON fact_prescriptions(patient_id);
CREATE INDEX idx_prescriptions_medication ON fact_prescriptions(medication_id);
COMMENT ON TABLE fact_prescriptions IS 'Medication prescriptions over time';

-- =====================================================
-- FACT: Disease-Specific Measurements (Flexible Storage)
-- =====================================================
/*
 * TERMINOLOGY & RATIONALE:
 * 
 * - fact_lab_results: For STANDARDIZED, COMMON lab tests shared across diseases
 *   Examples: WBC, Hemoglobin, CRP, ESR, Creatinine
 *   Storage: Structured columns (test_id, result_value, result_text)
 *   Query Speed: FAST (indexed, optimized for aggregations)
 *   Use Case: "Show me all patients with WBC > 11"
 * 
 * - fact_disease_specific_data: For DISEASE-UNIQUE measurements (EAV pattern)
 *   Examples: SLEDAI score (SLE only), ESSDAI score (Sjogren only), DAS28 (RA only)
 *   Storage: JSONB (flexible key-value pairs)
 *   Query Speed: Moderate (GIN indexed for JSON queries)
 *   Use Case: "Show me SLE patients with SLEDAI > 10"
 * 
 * WHY SEPARATE TABLES?
 * 1. Performance: Common tests queried frequently → optimized structure
 * 2. Flexibility: Disease-specific measurements vary wildly → flexible storage
 * 3. Maintainability: Adding new common test = INSERT into dim_lab_tests
 *                      Adding new disease metric = just store in JSONB (no schema change)
 * 
 * EAV (Entity-Attribute-Value) Pattern:
 * - Entity = patient_id
 * - Attribute = keys in JSONB (e.g., "SLEDAI_score", "kidney_biopsy_class")
 * - Value = values in JSONB (e.g., 8, "Class III")
 * 
 * This is a HYBRID approach: Structured (fact_lab_results) + Flexible (fact_disease_specific_data)
 */

CREATE TABLE fact_disease_specific_data (
    measurement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES dim_patients(patient_id),
    disease_id INT NOT NULL REFERENCES dim_diseases(disease_id),
    visit_id UUID REFERENCES fact_patient_visits(visit_id),  -- Optional: link to specific visit
    measurement_date DATE NOT NULL,
    date_id INT NOT NULL REFERENCES dim_time(date_id),
    measurement_type VARCHAR(100),  -- "Clinical Score", "Imaging Result", "Biopsy", "Physical Exam", etc.
    
    -- FLEXIBLE STORAGE: Store any disease-specific data as JSON
    -- JSONB = Binary JSON format (faster than TEXT JSON, supports indexing)
    data JSONB NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint: Ensure JSONB is not empty
    CONSTRAINT chk_data_not_empty CHECK (jsonb_typeof(data) = 'object' AND data != '{}'::jsonb)
);

-- Indexes for performance
CREATE INDEX idx_disease_data_patient ON fact_disease_specific_data(patient_id);
CREATE INDEX idx_disease_data_disease ON fact_disease_specific_data(disease_id);
CREATE INDEX idx_disease_data_date ON fact_disease_specific_data(measurement_date);

-- GIN (Generalized Inverted Index) for JSONB: Enables fast searches inside JSON
-- Allows queries like: WHERE data->>'SLEDAI_score' > '10'
CREATE INDEX idx_disease_data_jsonb ON fact_disease_specific_data USING GIN(data);

COMMENT ON TABLE fact_disease_specific_data IS 'Flexible fact table for disease-specific measurements (clinical scores, imaging, biopsies, physical exams) that do not fit standard lab test structure. Uses JSONB for schema-less storage.';
COMMENT ON COLUMN fact_disease_specific_data.data IS 'JSONB storage for disease-unique measurements. Examples: SLE → {"SLEDAI_score": 8, "kidney_biopsy_class": "III"}, Sjogren → {"ESSDAI_score": 12, "salivary_flow": 0.3}';

-- =====================================================
-- EXAMPLE DATA: How to use fact_disease_specific_data
-- =====================================================
/*
 * EXAMPLE 1: Store SLE-specific measurements
 * 
 * INSERT INTO fact_disease_specific_data 
 * (patient_id, disease_id, measurement_date, date_id, measurement_type, data)
 * VALUES (
 *     'patient-uuid-123',
 *     1,  -- SLE disease_id from dim_diseases
 *     '2026-03-24',
 *     20260324,
 *     'Clinical Score',
 *     '{
 *         "SLEDAI_score": 8,
 *         "SLEDAI_category": "moderate",
 *         "kidney_biopsy_class": "III",
 *         "kidney_biopsy_activity_index": 5,
 *         "kidney_biopsy_chronicity_index": 2,
 *         "proteinuria_24h": 1.5,
 *         "proteinuria_unit": "g/24h",
 *         "complement_C3": 0.7,
 *         "complement_C4": 0.08
 *     }'::jsonb
 * );
 * 
 * EXAMPLE 2: Store Sjogren-specific measurements
 * 
 * INSERT INTO fact_disease_specific_data 
 * (patient_id, disease_id, measurement_date, date_id, measurement_type, data)
 * VALUES (
 *     'patient-uuid-456',
 *     5,  -- Sjogren disease_id from dim_diseases
 *     '2026-03-24',
 *     20260324,
 *     'Physical Exam',
 *     '{
 *         "ESSDAI_score": 12,
 *         "ESSDAI_category": "moderate",
 *         "salivary_flow_unstimulated": 0.05,
 *         "salivary_flow_stimulated": 0.3,
 *         "salivary_flow_unit": "ml/min",
 *         "schirmer_test_left_eye": 3,
 *         "schirmer_test_right_eye": 4,
 *         "schirmer_unit": "mm/5min",
 *         "focus_score": 2.5,
 *         "parotid_sialography": "punctate"
 *     }'::jsonb
 * );
 * 
 * EXAMPLE 3: Store Rheumatoid Arthritis-specific measurements
 * 
 * INSERT INTO fact_disease_specific_data 
 * (patient_id, disease_id, measurement_date, date_id, measurement_type, data)
 * VALUES (
 *     'patient-uuid-789',
 *     2,  -- RA disease_id from dim_diseases
 *     '2026-03-24',
 *     20260324,
 *     'Clinical Score',
 *     '{
 *         "DAS28_score": 5.2,
 *         "DAS28_category": "high_activity",
 *         "DAS28_ESR": 45,
 *         "swollen_joint_count_28": 8,
 *         "tender_joint_count_28": 12,
 *         "patient_global_assessment_VAS": 60,
 *         "HAQ_score": 1.8,
 *         "morning_stiffness_minutes": 120,
 *         "RF_positive": true,
 *         "anti_CCP_positive": true
 *     }'::jsonb
 * );
 * 
 * QUERY EXAMPLES:
 * 
 * -- Query 1: Get all SLE patients with high disease activity (SLEDAI > 10)
 * SELECT 
 *     p.anonymous_id,
 *     f.measurement_date,
 *     f.data->>'SLEDAI_score' AS sledai_score,
 *     f.data->>'kidney_biopsy_class' AS kidney_biopsy
 * FROM fact_disease_specific_data f
 * JOIN dim_patients p ON f.patient_id = p.patient_id
 * WHERE f.disease_id = 1  -- SLE
 *   AND (f.data->>'SLEDAI_score')::INT > 10
 * ORDER BY (f.data->>'SLEDAI_score')::INT DESC;
 * 
 * -- Query 2: Get all Sjogren patients with severe dry eyes (Schirmer < 5mm)
 * SELECT 
 *     p.anonymous_id,
 *     f.measurement_date,
 *     f.data->>'schirmer_test_left_eye' AS left_eye,
 *     f.data->>'schirmer_test_right_eye' AS right_eye,
 *     f.data->>'ESSDAI_score' AS essdai_score
 * FROM fact_disease_specific_data f
 * JOIN dim_patients p ON f.patient_id = p.patient_id
 * WHERE f.disease_id = 5  -- Sjogren
 *   AND ((f.data->>'schirmer_test_left_eye')::FLOAT < 5 
 *        OR (f.data->>'schirmer_test_right_eye')::FLOAT < 5);
 * 
 * -- Query 3: Compare disease activity scores across all diseases
 * SELECT 
 *     d.disease_name,
 *     COUNT(DISTINCT f.patient_id) AS patient_count,
 *     AVG((f.data->>'SLEDAI_score')::FLOAT) AS avg_sledai,
 *     AVG((f.data->>'ESSDAI_score')::FLOAT) AS avg_essdai,
 *     AVG((f.data->>'DAS28_score')::FLOAT) AS avg_das28
 * FROM fact_disease_specific_data f
 * JOIN dim_diseases d ON f.disease_id = d.disease_id
 * GROUP BY d.disease_name;
 * 
 * -- Query 4: Full patient profile combining structured and flexible data
 * SELECT 
 *     p.anonymous_id,
 *     p.age_range,
 *     d.disease_name,
 *     -- Structured lab results
 *     lr.test_name,
 *     lr.result_value AS lab_value,
 *     -- Flexible disease-specific data
 *     fds.data->>'SLEDAI_score' AS sledai_score,
 *     fds.data->>'kidney_biopsy_class' AS kidney_status
 * FROM dim_patients p
 * JOIN fact_diagnoses fd ON p.patient_id = fd.patient_id
 * JOIN dim_diseases d ON fd.disease_id = d.disease_id
 * LEFT JOIN fact_lab_results lr ON p.patient_id = lr.patient_id
 * LEFT JOIN dim_lab_tests lt ON lr.test_id = lt.test_id
 * LEFT JOIN fact_disease_specific_data fds ON p.patient_id = fds.patient_id
 * WHERE p.patient_id = 'specific-patient-uuid'
 * ORDER BY lr.result_date DESC, fds.measurement_date DESC;
 */

-- =====================================================
-- HOW TO EXPLAIN THIS TO YOUR SUPERVISOR:
-- =====================================================
/*
 * PRESENTATION TALKING POINTS:
 * 
 * 1. THE PROBLEM:
 *    "Some measurements are common across all diseases (WBC, CRP), 
 *     but others are unique to specific diseases (SLEDAI for SLE,
 *     ESSDAI for Sjogren, DAS28 for RA). If we put everything in 
 *     one table, we'd have hundreds of mostly-NULL columns."
 * 
 * 2. THE SOLUTION:
 *    "We use a TWO-TIER measurement system:
 *     
 *     TIER 1: fact_lab_results (Structured, Fast)
 *     - Common lab tests: WBC, Hemoglobin, CRP, ESR
 *     - Shared across all diseases
 *     - Optimized for fast aggregations
 *     - Example: 'Show me all patients with high CRP'
 *     
 *     TIER 2: fact_disease_specific_data (Flexible, JSONB)
 *     - Disease-unique measurements: SLEDAI, ESSDAI, DAS28
 *     - Stored as JSON (key-value pairs)
 *     - No schema changes needed
 *     - Example: 'Show me SLE patients with SLEDAI > 10'"
 * 
 * 3. THE BENEFIT:
 *    "When we discover a new disease with 50 unique biomarkers:
 *     - OLD WAY: Add 50 new columns (schema migration, downtime)
 *     - NEW WAY: Just store JSON (no schema change, instant)
 *     
 *     Example:
 *     INSERT INTO fact_disease_specific_data 
 *     VALUES (..., '{"new_biomarker_1": 123, "new_biomarker_2": 456}'::jsonb);
 *     
 *     Done! The system immediately knows about these new measurements."
 * 
 * 4. TERMINOLOGY:
 *    "This is called a HYBRID approach:
 *     - Snowflake Schema for structured data (normalized dimensions + facts)
 *     - EAV Pattern (Entity-Attribute-Value) for flexible data (JSONB)
 *     
 *     It's the best of both worlds: performance + flexibility."
 * 
 * 5. REAL-WORLD ANALOGY:
 *    "Think of it like a hospital form:
 *     - Section 1: Basic info (name, age, blood pressure) → Everyone fills this (structured)
 *     - Section 2: Additional notes (varies by doctor/condition) → Flexible text field (JSONB)
 *     
 *     We don't create a new form for every possible combination of notes!"
 * 
 * 6. ICEBERG COMPATIBILITY:
 *    "JSONB in PostgreSQL maps perfectly to Iceberg's nested struct types.
 *     When we migrate to Iceberg for long-term analytics, this data 
 *     translates seamlessly. No rewriting needed."
 */

-- =====================================================
-- METADATA & GOVERNANCE TABLES
-- =====================================================

-- METADATA: Uploaded Datasets (Versioning)
CREATE TABLE metadata_datasets (
    dataset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_name VARCHAR(200) NOT NULL,
    file_type VARCHAR(20),  -- "CSV", "Excel", "PDF", "Image", etc.
    uploaded_by VARCHAR(100) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INT DEFAULT 1,  -- Dataset versioning (v1, v2, v3, etc.)
    parent_dataset_id UUID REFERENCES metadata_datasets(dataset_id),  -- For version chain
    row_count INT,
    column_count INT,
    file_size_mb FLOAT,
    file_hash VARCHAR(64),  -- SHA-256 for deduplication
    status VARCHAR(20) DEFAULT 'Uploaded',  -- "Uploaded", "Validated", "Processed", "Rejected"
    metadata JSONB  -- Flexible metadata storage
);

CREATE INDEX idx_datasets_uploaded_by ON metadata_datasets(uploaded_by);
CREATE INDEX idx_datasets_status ON metadata_datasets(status);
COMMENT ON TABLE metadata_datasets IS 'Dataset registry with versioning support';

-- METADATA: Column Registry (Automatic Extraction)
CREATE TABLE metadata_columns (
    column_id SERIAL PRIMARY KEY,
    dataset_id UUID NOT NULL REFERENCES metadata_datasets(dataset_id),
    column_name VARCHAR(100) NOT NULL,
    data_type VARCHAR(50),  -- "INTEGER", "FLOAT", "VARCHAR", "DATE", etc.
    entity_type VARCHAR(50),  -- "patient_id", "lab_test", "diagnosis", etc.
    mapped_to_table VARCHAR(100),  -- Which dimension/fact table
    is_required BOOLEAN DEFAULT FALSE,
    sample_values TEXT[],  -- Array of sample values for preview
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_columns_dataset ON metadata_columns(dataset_id);
COMMENT ON TABLE metadata_columns IS 'Automatic column extraction and mapping';

-- AUDIT TRAIL: User Actions (Full Transparency)
CREATE TABLE audit_trail (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    user_role VARCHAR(50),  -- "Data Engineer", "Clinician", "Admin", etc.
    action VARCHAR(100) NOT NULL,  -- "Upload", "Validate", "Execute Cleaning", "Approve", etc.
    target_entity VARCHAR(100),  -- "Dataset", "OCR", "Feature", "Model", etc.
    target_id UUID,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changes JSONB,  -- Before/after state in JSON format
    ip_address VARCHAR(50),
    session_id VARCHAR(100)
);

CREATE INDEX idx_audit_user ON audit_trail(user_id);
CREATE INDEX idx_audit_timestamp ON audit_trail(timestamp);
CREATE INDEX idx_audit_target ON audit_trail(target_entity, target_id);
COMMENT ON TABLE audit_trail IS 'Complete audit trail for governance and compliance';

-- VALIDATION QUEUE: Human Checkpoints (User-Controlled Framework)
CREATE TABLE validation_queue (
    validation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES metadata_datasets(dataset_id),
    stage VARCHAR(50) NOT NULL,  -- "Column Mapping", "OCR Review", "Cleaning Confirmation", "Feature Extraction"
    status VARCHAR(20) DEFAULT 'Pending',  -- "Pending", "Approved", "Rejected"
    assigned_to VARCHAR(100),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewer_comments TEXT,
    validation_data JSONB  -- Stores data awaiting validation (e.g., OCR output, extracted features)
);

CREATE INDEX idx_validation_status ON validation_queue(status);
CREATE INDEX idx_validation_assigned ON validation_queue(assigned_to);
COMMENT ON TABLE validation_queue IS 'Human validation checkpoints - framework approach';

-- =====================================================
-- FUNCTIONS & TRIGGERS
-- =====================================================

-- Function: Update timestamp on row update
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update dim_patients timestamp
CREATE TRIGGER update_patients_timestamp
    BEFORE UPDATE ON dim_patients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function: Auto-increment dataset version
CREATE OR REPLACE FUNCTION auto_increment_dataset_version()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.parent_dataset_id IS NOT NULL THEN
        SELECT COALESCE(MAX(version), 0) + 1 INTO NEW.version
        FROM metadata_datasets
        WHERE parent_dataset_id = NEW.parent_dataset_id OR dataset_id = NEW.parent_dataset_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-version datasets
CREATE TRIGGER auto_version_dataset
    BEFORE INSERT ON metadata_datasets
    FOR EACH ROW
    EXECUTE FUNCTION auto_increment_dataset_version();

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- View: Patient Complete Profile
CREATE VIEW view_patient_profiles AS
SELECT 
    p.patient_id,
    p.anonymous_id,
    p.age_range,
    p.gender,
    COUNT(DISTINCT v.visit_id) AS total_visits,
    COUNT(DISTINCT d.disease_id) AS disease_count,
    COUNT(DISTINCT lr.test_id) AS lab_tests_count,
    MAX(v.visit_date) AS last_visit_date
FROM dim_patients p
LEFT JOIN fact_patient_visits v ON p.patient_id = v.patient_id
LEFT JOIN fact_diagnoses d ON p.patient_id = d.patient_id
LEFT JOIN fact_lab_results lr ON p.patient_id = lr.patient_id
GROUP BY p.patient_id, p.anonymous_id, p.age_range, p.gender;

-- View: Disease Statistics
CREATE VIEW view_disease_statistics AS
SELECT 
    d.disease_id,
    d.disease_name,
    d.disease_category,
    COUNT(DISTINCT fd.patient_id) AS patient_count,
    COUNT(DISTINCT fd.visit_id) AS total_diagnoses,
    MIN(fd.diagnosis_date) AS first_diagnosis_date,
    MAX(fd.diagnosis_date) AS latest_diagnosis_date
FROM dim_diseases d
LEFT JOIN fact_diagnoses fd ON d.disease_id = fd.disease_id
GROUP BY d.disease_id, d.disease_name, d.disease_category;

-- View: Lab Test Abnormalities
CREATE VIEW view_lab_abnormalities AS
SELECT 
    lt.test_name,
    lt.category,
    COUNT(*) AS total_results,
    SUM(CASE WHEN lr.is_abnormal THEN 1 ELSE 0 END) AS abnormal_count,
    ROUND(100.0 * SUM(CASE WHEN lr.is_abnormal THEN 1 ELSE 0 END) / COUNT(*), 2) AS abnormal_percentage,
    AVG(lr.result_value) AS avg_value,
    MIN(lr.result_value) AS min_value,
    MAX(lr.result_value) AS max_value
FROM dim_lab_tests lt
JOIN fact_lab_results lr ON lt.test_id = lr.test_id
WHERE lr.result_value IS NOT NULL
GROUP BY lt.test_id, lt.test_name, lt.category;

-- =====================================================
-- GRANTS (Security - RBAC Foundation)
-- =====================================================

-- Grant appropriate permissions (will be configured after RBAC implementation in Sprint 2)
-- Commented out until roles are created:
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO data_scientist_role;
-- GRANT SELECT, INSERT, UPDATE ON metadata_datasets, metadata_columns, validation_queue TO data_engineer_role;
-- GRANT SELECT, INSERT ON audit_trail TO ALL;

-- =====================================================
-- SCHEMA VALIDATION
-- =====================================================

COMMENT ON SCHEMA public IS 'USM Autoimmune ML Platform - Flexible Data Warehouse Schema - Designed for scalability, adaptability, and comprehensive data capture';

--SELECT 'Flexible schema created successfully!' AS status;
