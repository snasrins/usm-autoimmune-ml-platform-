# 📊 MinIO Storage Status & Missing Features

**Date:** April 23, 2026 (UPDATED)  
**Purpose:** Track what's saved to MinIO - ALL 5 FEATURES NOW IMPLEMENTED ✅

---

## ✅ **ALL FEATURES IMPLEMENTED**

### **1. Unstructured Raw Data** ✅
**Location:** `app/services/unstructured_pipeline_service.py` line 530  
**Bucket:** `usm-raw`  
**What:** PDF, TXT, PNG, JPG files uploaded via OCR pipeline  
**Code:**
```python
object_path = self.minio_client.upload_file(file_data, filename, content_type=f"application/{file_type}")
```

### **2. Trained ML Models** ✅
**Location:** `app/api/endpoints/training.py` line 279-320  
**Bucket:** `ml-models`  
**What:** Trained models (XGBoost, LightGBM, etc.) with metadata  
**Code:**
```python
minio_service = MinIOService(...)
minio_path = minio_service.save_model(
    model=result['model'],
    model_name=algo_name,
    metadata=metadata
)
```

### **3. Preprocessed/Cleaned Structured Data** ✅ NEW!
**Location:** `app/api/endpoints/preview.py` line 600+  
**Bucket:** `usm-preprocessed`  
**What:** CSV data after preprocessing (imputation, outlier handling, normalization)  
**Code:**
```python
minio_path = minio_service.save_preprocessed_data(
    df_csv=csv_bytes,
    batch_id=result['batch_id'],
    stage='final_preprocessed',
    metadata={...}
)
```

### **4. ML-Ready Datasets** ✅ NEW!
**Location:** `app/api/endpoints/training.py` line 140+  
**Bucket:** `ml-datasets`  
**What:** Pickled train/test datasets with features  
**Code:**
```python
minio_path = minio_service.save_ml_dataset(
    dataset_pickle=pickle_data,
    batch_id=params['batch_id'],
    metadata={...}
)
```

### **5. Scorecard Artifacts** ✅ NEW!
**Location:** `app/api/endpoints/scorecard.py` line 150+  
**Bucket:** `clinical-scorecards`  
**What:** CSV reports, JSON summaries, risk group distributions  
**Code:**
```python
minio_paths = minio_service.save_scorecard_artifacts(
    scorecard_id=scorecard_id,
    artifacts=artifacts,
    metadata={...}
)
```

### **6. Batch Prediction Results** ✅ NEW!
**Location:** `app/api/endpoints/inference.py` line 110+  
**Bucket:** `predictions`  
**What:** CSV files with batch prediction results  
**Code:**
```python
minio_path = minio_service.save_prediction_results(
    predictions_csv=csv_bytes,
    batch_id=batch_id,
    model_name=request.model_name,
    metadata={...}
)
```

### **7. EDA/Visualization Artifacts** ✅ NEW!
**Location:** `app/api/endpoints/eda.py` line 340+  
**Bucket:** `analytics`  
**What:** JSON summaries, statistics, correlation matrices  
**Code:**
```python
minio_path = minio_service.save_eda_artifact(
    artifact_data=summary_json,
    batch_id=str(dataset.id),
    artifact_name='summary_statistics.json',
    artifact_type='json',
    metadata={...}
)
```

---

## 🎯 **NEW MinIO SERVICE METHODS ADDED**

**File:** `app/services/minio_service.py`

### **1. save_preprocessed_data()**
- Saves CSV + metadata to `usm-preprocessed` bucket
- Auto-creates bucket if missing
- Includes NMRR compliance checking
- Returns MinIO path

### **2. save_ml_dataset()**
- Saves pickled dataset to `ml-datasets` bucket
- Stores X_train, X_test, y_train, y_test
- Includes feature names and metadata
- Returns MinIO path

### **3. save_scorecard_artifacts()**
- Saves multiple files (CSV, JSON) to `clinical-scorecards` bucket
- Supports batch saving with timestamps
- Returns dictionary of paths
- Perfect for regulatory compliance

### **4. save_prediction_results()**
- Saves CSV predictions to `predictions` bucket
- Includes batch ID and model name
- Metadata includes prediction timestamp
- Audit trail compliant

### **5. save_eda_artifact()**
- Saves analysis artifacts to `analytics` bucket
- Supports PNG, JSON, CSV formats
- Auto-detects content type
- Organized by batch_id and artifact type

---

## ✅ **IMPLEMENTATION COMPLETE**

All 5 missing features have been implemented:

1. ✅ **Preprocessed Data** - Wired to `/preview/{session_id}/save-preprocessed`
2. ✅ **ML Datasets** - Wired to dataset generation background task
3. ✅ **Scorecard Artifacts** - Wired to `/scorecard/batch`
4. ✅ **Batch Predictions** - Wired to `/predict/batch`
5. ✅ **EDA Artifacts** - Wired to `/datasets/{dataset_id}/summary`

---

## 📋 **BUCKET STRUCTURE (FINAL)**

```
usm-raw/                    # ✅ Exists
  └── 2026/04/23/pdf_file.pdf

ml-models/                  # ✅ Exists
  └── xgboost/v1/model.pkl

usm-preprocessed/          # ✅ NOW CREATED
  └── batch_<uuid>/
      ├── final_preprocessed_<timestamp>.csv
      └── final_preprocessed_<timestamp>_metadata.json

ml-datasets/               # ✅ NOW CREATED
  └── dataset_<batch_id>/
      ├── dataset_<timestamp>.pkl
      └── metadata_<timestamp>.json

clinical-scorecards/       # ✅ NOW CREATED
  └── scorecard_<id>/
      ├── batch_scorecards.csv
      ├── risk_group_summary.csv
      ├── comprehensive_report.json
      └── metadata_<timestamp>.json

predictions/               # ✅ NOW CREATED
  └── batch_<uuid>/
      ├── predictions_<model>_<timestamp>.csv
      └── predictions_<model>_<timestamp>_metadata.json

analytics/                 # ✅ NOW CREATED
  └── eda_<batch_id>/
      ├── json/summary_statistics.json
      └── json/summary_statistics_metadata.json
```

---

## 🔒 **NMRR COMPLIANCE**

All MinIO methods include `_check_nmrr_compliance()` to prevent patient identifiers:
- ❌ Blocks: patient_id, IC, NRIC, passport, medical record numbers
- ❌ Blocks: names, emails, phone numbers, addresses, birthdates
- ✅ Allows: feature names, aggregate stats, model parameters

---

## 🚀 **READY FOR PRODUCTION**

✅ All MinIO saves are **non-blocking** (wrapped in try/except)  
✅ Failures are logged but don't break user workflow  
✅ Metadata includes timestamps, usernames, and batch IDs  
✅ All buckets auto-created on first use  
✅ NMRR compliance enforced on all saves  

**Status:** PRODUCTION READY 🎉

---

## ✅ **ALREADY SAVED TO MinIO**

### **1. Unstructured Raw Data** ✅
**Location:** `app/services/unstructured_pipeline_service.py` line 530  
**Bucket:** `usm-raw`  
**What:** PDF, TXT, PNG, JPG files uploaded via OCR pipeline  
**Code:**
```python
object_path = self.minio_client.upload_file(file_data, filename, content_type=f"application/{file_type}")
```

### **2. Trained ML Models** ✅
**Location:** `app/api/endpoints/training.py` line 279-320  
**Bucket:** `ml-models`  
**What:** Trained models (XGBoost, LightGBM, etc.) with metadata  
**Code:**
```python
minio_service = MinIOService(...)
minio_path = minio_service.save_model(
    model=result['model'],
    model_name=algo_name,
    metadata=metadata
)
```

---

## ❌ **NOT YET SAVED TO MinIO**

### **1. Preprocessed/Cleaned Structured Data** ❌
**Should Save:** After preprocessing (missing value imputation, outlier handling, normalization)  
**Current:** Only saved to PostgreSQL `flexible_dataset_wide` table  
**Bucket:** `usm-preprocessed` (recommended)  
**Why:** Backup, version control, reproducibility

### **2. ML-Ready Datasets** ❌
**Should Save:** After dataset preparation (train/test split, feature engineering, LASSO selection)  
**Current:** Only in memory during training  
**Bucket:** `ml-datasets` (recommended)  
**Why:** Reproducibility, auditing, re-training

### **3. Scorecard Artifacts** ❌
**Should Save:** Generated scorecards (bin tables, threshold reports)  
**Current:** Only in memory/temporary storage  
**Bucket:** `clinical-scorecards` (recommended)  
**Why:** Clinical validation, regulatory compliance, archiving

### **4. Batch Prediction Results** ❌
**Should Save:** Inference results for batches  
**Current:** Only returned in API response  
**Bucket:** `predictions` (recommended)  
**Why:** Audit trail, analysis, reporting

### **5. EDA/Visualization Artifacts** ❌
**Should Save:** Correlation matrices, distribution plots, SHAP plots  
**Current:** Generated on-the-fly  
**Bucket:** `analytics` (recommended)  
**Why:** Documentation, presentations, reproducibility

---

## 📋 **PRIORITY FOR IMPLEMENTATION**

### **HIGH PRIORITY** (Critical for production)
1. ⭐ **Preprocessed Data** - Needed for data lineage
2. ⭐ **ML-Ready Datasets** - Needed for reproducibility
3. ⭐ **Scorecard Artifacts** - Needed for clinical validation

### **MEDIUM PRIORITY** (Important for compliance)
4. **Batch Prediction Results** - Audit trail
5. **SHAP Explanations** - Regulatory compliance

### **LOW PRIORITY** (Nice to have)
6. **EDA Visualizations** - Documentation

---

## 🔧 **IMPLEMENTATION PLAN**

### **Quick Wins (Can add today):**

#### **1. Save Preprocessed Data**
**File:** `app/api/endpoints/preprocessing.py`  
**After:** `save_preprocessed()` endpoint  
**Add:**
```python
# After saving to PostgreSQL
minio_service = get_minio_service()
csv_buffer = df.to_csv(index=False)
minio_path = minio_service.upload_file(
    csv_buffer.encode(),
    f"preprocessed_{batch_id}.csv",
    bucket_name="usm-preprocessed"
)
# Store minio_path in database
```

#### **2. Save ML Datasets**
**File:** `app/ml/training/dataset_generator.py`  
**After:** `generate_training_dataset()` function  
**Add:**
```python
# After creating X_train, X_test, y_train, y_test
minio_service = get_minio_service()
import pickle
dataset_artifact = {
    'X_train': X_train,
    'X_test': X_test,
    'y_train': y_train,
    'y_test': y_test,
    'feature_names': feature_names,
    'metadata': metadata
}
pickle_data = pickle.dumps(dataset_artifact)
minio_path = minio_service.upload_file(
    pickle_data,
    f"dataset_{batch_id}_{timestamp}.pkl",
    bucket_name="ml-datasets"
)
```

#### **3. Save Scorecard Artifacts**
**File:** `app/api/endpoints/scorecard.py`  
**After:** Scorecard generation  
**Add:**
```python
# After generating scorecard
minio_service = get_minio_service()

# Save bin tables CSV
bin_tables_csv = scorecard.export_bin_tables_to_csv()
minio_service.upload_file(
    bin_tables_csv.encode(),
    f"scorecard_{scorecard_id}_bins.csv",
    bucket_name="clinical-scorecards"
)

# Save comprehensive report
comprehensive_csv = scorecard.export_comprehensive_report()
minio_service.upload_file(
    comprehensive_csv.encode(),
    f"scorecard_{scorecard_id}_comprehensive.csv",
    bucket_name="clinical-scorecards"
)
```

---

## ✅ **RECOMMENDED MinIO BUCKET STRUCTURE**

```
usm-raw/                    # ✅ Already exists
  └── 2026/04/22/pdf_file.pdf

ml-models/                  # ✅ Already exists
  └── xgboost_v1.pkl

usm-preprocessed/          # ❌ Need to create
  └── batch_<uuid>/
      ├── original.csv
      ├── after_imputation.csv
      ├── after_outlier_handling.csv
      └── final_preprocessed.csv

ml-datasets/               # ❌ Need to create
  └── dataset_<uuid>/
      ├── dataset.pkl
      ├── metadata.json
      └── feature_importance.csv

clinical-scorecards/       # ❌ Need to create
  └── scorecard_<id>/
      ├── bin_tables.csv
      ├── threshold_report.csv
      ├── patient_scores.csv
      └── comprehensive_report.csv

predictions/               # ❌ Need to create
  └── batch_<uuid>/
      ├── input.csv
      └── predictions.csv

analytics/                 # ❌ Need to create (future)
  └── eda_<batch_id>/
      ├── correlation_matrix.png
      ├── distributions.png
      └── shap_summary.png
```

---

## 🎯 **DECISION: SHOULD WE ADD MINIO SAVES TODAY?**

**Recommendation:** 

✅ **YES for Scorecard** - Critical for clinical validation  
✅ **YES for Preprocessed Data** - Important for data lineage  
⏳ **OPTIONAL for ML Datasets** - Can add later if time permits  
⏳ **SKIP for now:** EDA visualizations, batch predictions (lower priority)

**Estimated Time:**
- Preprocessed data save: ~30 minutes
- Scorecard artifact save: ~20 minutes
- **Total:** ~1 hour (can add after Day 1 Morning if time permits)

---

**Ready to proceed with Day 1 implementation now!**
