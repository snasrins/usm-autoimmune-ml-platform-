# 100% Flexible Unstructured Data Pipeline

## Philosophy: **Data Defines Schema, Not Schema Defines Data**

This pipeline follows modern **data lake/lakehouse architecture** principles where:
- ✅ NO hardcoded field names
- ✅ NO assumptions about data structure  
- ✅ NO forced categorization
- ✅ Raw data stored in flexible JSONB format
- ✅ Users define schema downstream (in UI, SQL, or Python)

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: Document Upload                                    │
│ Input: PDF / TXT / IMG (ANY document type)                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: OCR (Optical Character Recognition)                │
│ Engine: Qwen3-VL-2B-Instruct                                 │
│ Output: Raw text as string                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 3: NER (Named Entity Recognition)                     │
│ Extract: Key-value pairs WITHOUT type labels                │
│ Example: "Hemoglobin: 15.8 g/dL" (NO "lab_test" label)      │
│          "Patient Name: John Doe" (NO "demographics" label)  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 4: Store in PostgreSQL (JSONB)                        │
│ Table: unstructured_document_processed                       │
│ Column: data (JSONB) - NO structure enforced                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 5: Convert to Tabular (Generic Flattening)            │
│ Strategy: Flatten ALL JSON keys → columns                   │
│ NO categorization, NO hardcoded fields                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 6: Preview & Edit in UI                               │
│ View: Editable table with dynamic columns                   │
│ Edit: Modify any field                                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 7: Save to flexible_dataset_wide                      │
│ Table: flexible_dataset_wide                                 │
│ Column: data (JSONB) - Organized but still flexible          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 8: User-Defined Schema (OPTIONAL)                     │
│ UI: Define PK/FK, normalize, create relationships            │
│ OR: Train ML model directly on JSONB data                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Before vs After Refactoring

### ❌ **BEFORE (Hardcoded Assumptions)**

```python
# OLD CODE - HARDCODED field names
record_id = metadata.get('lab_no') or metadata.get('mrn')  # Assumes "lab_no", "mrn" exist
row['hemoglobin'] = parsed['value_numeric']  # Assumes "hemoglobin" is a field
row['diseases'] = diseases  # Assumes categorization into "diseases"

# OLD CONVERSION - HARDCODED categories
if entity_type == 'lab_test':
    lab_tests[field_name] = value
elif entity_type == 'disease':
    diseases.append(value)
elif entity_type == 'medication':
    medications.append(value)
```

**Problems:**
- ❌ Only works for medical documents
- ❌ Breaks if document has different structure
- ❌ Requires code changes for new document types
- ❌ Assumes "lab_no", "mrn", "hemoglobin" exist
- ❌ Forces categorization (lab_test, disease, medication)

---

### ✅ **AFTER (100% Flexible)**

```python
# NEW CODE - NO assumptions
record_id = str(uuid.uuid4())  # Pure UUID, no field assumptions

# Flatten ALL keys dynamically
for key, value in metadata.items():
    row[f"meta_{key}"] = value  # Whatever keys exist

# Flatten ALL entities as enumerated columns
for idx, entity in enumerate(entities):
    row[f"entity_{idx}_value"] = entity.get('value')
    row[f"entity_{idx}_type"] = entity.get('type')
```

**Benefits:**
- ✅ Works with ANY document type (medical, legal, financial, scientific)
- ✅ No code changes needed for new structures
- ✅ NO assumptions about field names
- ✅ NO forced categorization
- ✅ Users decide schema downstream

---

## Data Storage Format

### **unstructured_document_processed** Table

```sql
CREATE TABLE unstructured_document_processed (
    id SERIAL PRIMARY KEY,
    record_id VARCHAR(100) NOT NULL,  -- Pure UUID
    document_type VARCHAR(50),         -- 'pdf', 'txt', 'jpg'
    data JSONB NOT NULL,               -- Pure JSONB, NO structure enforced
    import_method VARCHAR(50),         -- 'ocr_processed'
    import_batch_id UUID,
    created_by INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Index for fast JSONB queries
CREATE INDEX idx_unstructured_data ON unstructured_document_processed USING GIN (data);
```

### **Example Stored Data**

```json
{
  "document": {
    "filename": "lab_report.pdf",
    "file_type": "pdf",
    "page_count": 7,
    "confidence_score": 0.87,
    "ocr_engine": "Qwen3-VL-2B-Instruct"
  },
  "metadata": {
    "facility": "Premier Labs",
    "branch": "Kuala Lumpur",
    "collected_date": "06.04.2026"
  },
  "extracted_text": "HAEMATOLOGY\nHemoglobin 血红蛋白 15.8 g/dL (13.0 - 18.0)\n...",
  "medical_entities": [
    {
      "type": "extracted_from_document",
      "value": "Hemoglobin 血红蛋白: 15.8 g/dL (13.0 - 18.0)",
      "confidence": 0.9
    },
    {
      "type": "extracted_from_document",
      "value": "WBC 白血细胞: 6.5 x10^9/L (4.0 - 11.0)",
      "confidence": 0.9
    }
  ]
}
```

**Note:** NO hardcoded categories like "lab_results", "demographics", "clinical" - just raw extracted entities.

---

## Tabular Conversion (Generic Flattening)

### **Grouped Mode** (1 row with all data)

```python
# INPUT: OCR result from unstructured_document_processed
{
  "document": {...},
  "metadata": {"facility": "Premier Labs", "branch": "KL"},
  "medical_entities": [
    {"value": "Hemoglobin: 15.8 g/dL", "confidence": 0.9},
    {"value": "WBC: 6.5 x10^9/L", "confidence": 0.9},
    {"value": "SLE", "confidence": 0.95}
  ]
}

# OUTPUT: Flattened tabular row
{
  "source_document": "lab_report.pdf",
  "document_type": "ocr_processed",
  "ocr_engine": "Qwen3-VL-2B-Instruct",
  "ocr_confidence": 0.87,
  "page_count": 7,
  "meta_facility": "Premier Labs",
  "meta_branch": "KL",
  "entity_0_value": "Hemoglobin: 15.8 g/dL",
  "entity_0_confidence": 0.9,
  "entity_1_value": "WBC: 6.5 x10^9/L",
  "entity_1_confidence": 0.9,
  "entity_2_value": "SLE",
  "entity_2_confidence": 0.95
}
```

### **Individual Mode** (1 row per entity)

```python
# OUTPUT: One row per entity
[
  {
    "source_document": "lab_report.pdf",
    "entity_value": "Hemoglobin: 15.8 g/dL",
    "entity_confidence": 0.9,
    "meta_facility": "Premier Labs",
    "meta_branch": "KL"
  },
  {
    "source_document": "lab_report.pdf",
    "entity_value": "WBC: 6.5 x10^9/L",
    "entity_confidence": 0.9,
    "meta_facility": "Premier Labs",
    "meta_branch": "KL"
  },
  {
    "source_document": "lab_report.pdf",
    "entity_value": "SLE",
    "entity_confidence": 0.95,
    "meta_facility": "Premier Labs",
    "meta_branch": "KL"
  }
]
```

---

## Downstream Analysis Options

### **Option 1: Direct SQL Queries (No Schema Needed)**

```sql
-- Query: Find all documents mentioning "SLE"
SELECT 
    record_id,
    data->>'document'->>'filename' as filename,
    data->'medical_entities' as entities
FROM unstructured_document_processed
WHERE data->'medical_entities' @> '[{"value": "SLE"}]';

-- Query: Extract Hemoglobin values
SELECT 
    record_id,
    entity->>'value' as entity_value,
    entity->>'confidence' as confidence
FROM unstructured_document_processed,
     jsonb_array_elements(data->'medical_entities') as entity
WHERE entity->>'value' LIKE 'Hemoglobin%';
```

### **Option 2: Python/Pandas Analysis**

```python
import pandas as pd
import json

# Load from PostgreSQL
df = pd.read_sql("""
    SELECT record_id, data 
    FROM unstructured_document_processed
""", connection)

# Parse JSONB
df['entities'] = df['data'].apply(lambda x: json.loads(x)['medical_entities'])

# Extract specific entities dynamically
hemoglobin_values = []
for row in df.itertuples():
    for entity in row.entities:
        if 'Hemoglobin' in entity['value']:
            hemoglobin_values.append({
                'record_id': row.record_id,
                'value': entity['value']
            })

hgb_df = pd.DataFrame(hemoglobin_values)
```

### **Option 3: User Defines Schema in UI (Future)**

```
UI Workflow:
1. User uploads PDF → OCR → Preview table
2. User sees columns: entity_0_value, entity_1_value, meta_facility, ...
3. User defines schema:
   - "entity_0_value" → Rename to "hemoglobin"
   - "entity_1_value" → Rename to "wbc"
   - "meta_facility" → Keep as "facility"
4. User defines PK: "record_id" (or generate from meta fields)
5. User defines FK: "facility" → facilities.name (if normalizing)
6. Save schema mapping to metadata
7. Future imports automatically apply schema
```

### **Option 4: Train ML Model on Raw JSONB**

```python
from sklearn.ensemble import RandomForestClassifier
import json

# Load data
df = pd.read_sql("SELECT * FROM flexible_dataset_wide", connection)

# Parse JSONB and create feature vectors
features = []
labels = []

for row in df.itertuples():
    data = json.loads(row.data)
    
    # Extract features dynamically (no hardcoded fields)
    feature_vector = []
    for entity in data.get('medical_entities', []):
        # Use entity embeddings, counts, or other ML features
        feature_vector.append(extract_feature(entity))
    
    features.append(feature_vector)
    labels.append(row.label)

# Train model
model = RandomForestClassifier()
model.fit(features, labels)
```

---

## Benefits of 100% Flexible Approach

### ✅ **Research Benefits:**
1. **Exploratory Analysis** - Discover patterns without preconceived structure
2. **Cross-Domain Studies** - Combine medical + legal + financial documents
3. **Novel Datasets** - Works with completely new document types
4. **Reproducibility** - Raw data preserved, schema changes don't break pipelines

### ✅ **Engineering Benefits:**
1. **Zero Maintenance** - New document types require NO code changes
2. **Future-Proof** - Schema evolution happens in UI/queries, not codebase
3. **Scalable** - Works with any domain (not just medical)
4. **Simple** - Less code, fewer assumptions, fewer bugs

### ✅ **ML Benefits:**
1. **Feature Engineering** - Extract features from raw data programmatically
2. **Auto ML** - Let algorithms discover useful features
3. **Transfer Learning** - Pre-trained models work across domains
4. **Data Versioning** - Easy to track changes with JSONB diffs

---

## Comparison with Other Architectures

| Approach | Flexibility | Code Changes | Works With | Best For |
|----------|-------------|--------------|------------|----------|
| **Hardcoded Schema** (old) | ❌ Low | Every new field | Medical only | Production systems (fixed domains) |
| **100% Flexible** (new) | ✅ High | Zero | ANY document | Research, ML, exploratory analysis |
| **Hybrid** | 🟡 Medium | Minimal | Similar documents | Enterprise systems |

---

## Migration Path (If Needed)

If researchers later want structured schema:

```sql
-- Option 1: Extract structured view from JSONB
CREATE VIEW structured_lab_results AS
SELECT 
    id,
    data->>'document'->>'filename' as filename,
    (SELECT entity->>'value' 
     FROM jsonb_array_elements(data->'medical_entities') as entity
     WHERE entity->>'value' LIKE 'Hemoglobin%' 
     LIMIT 1) as hemoglobin,
    (SELECT entity->>'value' 
     FROM jsonb_array_elements(data->'medical_entities') as entity
     WHERE entity->>'value' LIKE 'WBC%' 
     LIMIT 1) as wbc
FROM flexible_dataset_wide;

-- Option 2: Materialize structured table (for performance)
CREATE TABLE lab_results_structured AS
SELECT * FROM structured_lab_results;
```

---

## Summary

| Aspect | Implementation |
|--------|----------------|
| **Field Names** | NO hardcoding - dynamic flattening |
| **Entity Types** | NO hardcoding - store as-is |
| **Categories** | NO hardcoding - user defines downstream |
| **PK/FK** | User defines in UI (optional) |
| **Schema** | Schema-on-read (like Snowflake, Databricks) |
| **Works With** | ANY document type |
| **Code Changes** | ZERO for new document types |

---

## Next Steps

1. ✅ **Test with medical PDF** - Verify OCR → JSONB → Tabular → Preview works
2. ✅ **Test with non-medical document** - Legal contract, financial report, scientific paper
3. ⏳ **Build UI schema editor** - Let users define PK/FK, rename columns
4. ⏳ **Add ML feature extraction** - Entity embeddings, counts, patterns
5. ⏳ **Add schema versioning** - Track how users define schemas over time

---

**This architecture follows modern data platform best practices used by:**
- Snowflake (schema-on-read)
- Databricks Delta Lake (flexible data lakes)
- BigQuery (flexible schema evolution)
- AWS Glue (schema discovery)

**Perfect for research platforms where data structure is unknown upfront!** 🚀
