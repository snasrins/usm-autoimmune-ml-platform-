# Complete ML Pipeline Flow - Login to Training

## 🎯 Pipeline Overview
This document maps the **complete end-to-end workflow** from user login to ML training, ensuring logical progression matching research methodology.

---

## 📋 User Journey: Login → ML Training

### **Phase 1: Authentication & Access**
```
1. Login Page → User Authentication
   ├─ Enter credentials
   ├─ JWT token generation
   └─ Redirect to Dashboard
```

### **Phase 2: Data Management**
```
2. Dashboard → Data Catalog
   ├─ View uploaded datasets
   ├─ Check data quality status
   ├─ Select dataset for ML prep
   └─ Navigate to Data Preparation Page
```

### **Phase 3: Data Preparation Workflow (8 Tabs)**

#### **Tab 1: Upload & Import** 📤
```
Purpose: Load raw data into platform
Actions:
  ├─ Select existing dataset from batch list
  ├─ OR upload new CSV/Excel file
  ├─ View dataset metadata (rows, columns, owner)
  ├─ Check upload status
Completion: selectedBatch !== null
Next Tab: Labeling
```

#### **Tab 2: Labeling** 🏷️
```
Purpose: Assign target labels for supervised learning
Features:
  ├─ Rule-Based Labeling (Dynamic rule builder)
  │  ├─ Select source column (e.g., other.sledai, lab_results.crp)
  │  ├─ Build conditional rules (numeric: <, >, <=, >=, ==, !=)
  │  ├─ Assign labels (Mild, Moderate, Severe)
  │  └─ View labeling statistics
  ├─ Manual Labeling (Record-by-record review)
  └─ Label Type Selection:
     ├─ Disease Classification (SLE, RA, MCTD, Sjögren)
     ├─ Disease Severity (Mild, Moderate, Severe)
     ├─ Disease Activity (Remission, Active, Flare)
     ├─ Organ Involvement (Renal, Neuropsychiatric, etc.)
     ├─ Treatment Response (Complete, Partial, Non-responder)
     └─ Flare Risk (Low-risk, High-risk)
Completion: labeling_progress >= 80%
Next Tab: Target Selection
```

#### **Tab 3: Target Selection** 🎯
```
Purpose: Define prediction target and validation strategy
Configuration:
  ├─ Select Target Column (what to predict)
  ├─ Validation Strategy:
  │  ├─ Simple Train/Test Split (65/35 - matches research)
  │  │  ├─ Adjustable split ratio
  │  │  └─ Stratified sampling enabled
  │  └─ Cross-Validation (3-10 folds)
  │     ├─ Default: 5-fold CV
  │     ├─ Preset options: 3, 5, 10 folds
  │     └─ Stratified CV enabled
  └─ View Target Distribution (class balance check)
Completion: targetColumn !== null
Next Tab: Preprocessing ✨ NEW!
```

#### **Tab 4: Preprocessing** ⚙️ **[NEWLY IMPLEMENTED - MATCHES RESEARCH FRAMEWORK]**
```
Purpose: Transform raw data following research methodology
Research Framework: Variable Filtration → Imputation → Winsorization → Standardization

Quick Start:
  └─ Run Complete Pipeline
     ├─ Executes all 4 steps automatically
     ├─ Research-standard settings (50% threshold, median, 1%/99%, Z-score)
     └─ Returns comprehensive pipeline report

Individual Steps:
  
  Step 1: Variable Filtration
     ├─ Remove variables with >50% missing data (research standard)
     ├─ Adjustable threshold (30%-80%)
     ├─ Returns: removed_columns[], kept_columns[]
     └─ API: POST /datasets/{id}/preprocess/filter-variables
  
  Step 2: Imputation
     ├─ Fill remaining missing values
     ├─ Strategies:
     │  ├─ Median (numeric) / Mode (categorical) - Research Standard
     │  ├─ Mean (numeric) / Mode (categorical)
     │  └─ Mode (all variables)
     ├─ Returns: imputation report with fill counts
     └─ API: POST /datasets/{id}/preprocess/missing-values
  
  Step 3: Winsorization (NOT outlier removal)
     ├─ Cap outliers at 1st & 99th percentiles (research standard)
     ├─ PRESERVES SAMPLE SIZE (critical for n=104)
     ├─ Adjustable percentiles (0.1%-5% / 95%-99.9%)
     ├─ Returns: total_capped_values, capped_columns[]
     └─ API: POST /datasets/{id}/preprocess/winsorize
  
  Step 4: Standardization
     ├─ Scale features to common range
     ├─ Methods:
     │  ├─ Z-Score (mean=0, std=1) - Research Standard
     │  ├─ Min-Max (0 to 1)
     │  └─ Robust (median-based, resistant to outliers)
     ├─ Returns: scaled_columns[], scaling_parameters
     └─ API: POST /datasets/{id}/preprocess/normalize

Complete Pipeline API:
  └─ POST /datasets/{id}/preprocess/complete-pipeline
     ├─ Runs all 4 steps in sequence
     ├─ Config: { filter_threshold, imputation_strategy, winsorize_bounds, standardization_method }
     ├─ Returns: { original_shape, final_shape, columns_removed, rows_preserved, step_reports[] }
     └─ Saves: *_preprocessed.csv/xlsx

Completion: preprocessingStep === 'complete'
Next Tab: Feature Engineering
```

#### **Tab 5: Feature Engineering** ⚡ (formerly Tab 4)
```
Purpose: Derive new features from preprocessed data
Features:
  ├─ Clinical Ratios:
  │  ├─ CRP/ESR Ratio (inflammation marker)
  │  ├─ Neutrophil-to-Lymphocyte Ratio (NLR)
  │  └─ Platelet-to-Lymphocyte Ratio (PLR)
  ├─ Temporal Features:
  │  └─ Disease Duration (years since diagnosis)
  ├─ Derived Scores:
  │  ├─ Inflammation Score (composite)
  │  └─ Organ Involvement Count
  └─ Advanced Transformations:
     ├─ Log Transform (for skewed distributions)
     ├─ Polynomial Features (quadratic terms)
     └─ Interaction Terms (feature combinations)
Completion: featureEngineeringResults !== null
Next Tab: Feature Selection
```

#### **Tab 6: Feature Selection** 🔍 (formerly Tab 5)
```
Purpose: Select most predictive features
Methods:
  ├─ Manual Selection (Clinician expertise)
  │  ├─ Browse all available features
  │  ├─ Select based on domain knowledge
  │  └─ Correlation detection (threshold 0.7-0.95)
  ├─ LASSO Selection (L1 regularization)
  │  ├─ Alpha: 0.00001-0.01 (very low for small datasets)
  │  ├─ Automatic feature ranking
  │  └─ Returns: selected features with importance scores
  └─ Combined Mode (Manual + LASSO)
     ├─ Clinician selects core features
     ├─ LASSO adds data-driven features
     └─ Final union of both sets
Completion: finalFeatures.length > 0
Next Tab: Validation
```

#### **Tab 7: Validation** ✅ (formerly Tab 6)
```
Purpose: Pre-training quality checks
Validations:
  ├─ Data Quality:
  │  ├─ Check for remaining missing values
  │  ├─ Check for infinite/NaN values
  │  └─ Verify data types
  ├─ Label Quality:
  │  ├─ Check label balance (warn if imbalanced)
  │  ├─ Check for missing labels
  │  └─ Verify label values match expected categories
  ├─ Feature Quality:
  │  ├─ Check for zero-variance features
  │  ├─ Check for high correlation (multicollinearity)
  │  └─ Verify feature count > 0
  └─ Configuration Quality:
     ├─ Check train/test split ratio
     ├─ Verify CV fold count (if enabled)
     └─ Ensure sufficient samples per class
Completion: validationResults.errors === 0
Next Tab: Summary
```

#### **Tab 8: Summary** 📊 (formerly Tab 7)
```
Purpose: Final review before ML training
Displays:
  ├─ Dataset Overview:
  │  ├─ Total records, features
  │  ├─ Labeled vs unlabeled
  │  └─ Upload timestamp, owner
  ├─ Preprocessing Summary:
  │  ├─ Filtration: columns removed
  │  ├─ Imputation: strategy used
  │  ├─ Winsorization: percentiles applied
  │  └─ Standardization: method used
  ├─ Target Configuration:
  │  ├─ Target column, label type
  │  ├─ Validation strategy (Split or CV)
  │  └─ Class distribution
  ├─ Feature Summary:
  │  ├─ Total features (clinical + derived)
  │  ├─ Selected features for training
  │  └─ Feature engineering config
  └─ Validation Status:
     ├─ Checks passed/total
     ├─ Errors (blocking issues)
     └─ Warnings (non-blocking)

Actions:
  ├─ Save Configuration (persist to database)
  ├─ Export Prepared Dataset (download CSV)
  └─ Proceed to ML Training → Navigate to Training Page
```

---

## 🔄 Pipeline Logic & Validation

### **Tab Progression Rules**
```javascript
Tab Completion Checks:
  1. isUploadComplete = selectedBatch !== null
  2. isLabelingComplete = labeling_progress >= 80%
  3. isTargetComplete = targetColumn !== null
  4. isPreprocessingComplete = preprocessingStep === 'complete'  ✨ NEW
  5. isFeaturesComplete = featureEngineeringResults !== null
  6. isFeatureSelectionComplete = finalFeatures.length > 0
  7. isValidationComplete = validationResults.errors === 0
  8. isReadyForTraining = all above checks pass

Auto-Navigation (Enter key):
  Upload ────→ Labeling ────→ Target ────→ Preprocessing ────→ Features ────→ Feature Selection ────→ Validation ────→ Summary
    (if batch selected)  (if ≥80% labeled)  (if target selected)  (if preprocessing done)  (if features created)  (if features selected)  (if no errors)
```

### **Data Quality First Pattern** (From User Memory)
```
Research Best Practice:
  ✅ Check Quality → Transform → Verify Transformation
  ❌ Transform → Hope for best → Discover garbage data

Current Implementation:
  1. Data Catalog: Quality checks on raw data (missing %, duplicates, outliers)
  2. Data Preparation Tab 1-3: Upload, Label, Configure
  3. Data Preparation Tab 4: PREPROCESSING (Quality-first transformation) ✨ NEW
  4. Data Preparation Tab 5-8: Feature engineering, selection, validation
  5. ML Training: Model training on clean, validated data
```

---

## 🏗️ Research Methodology Alignment

### **Your Research Framework → Platform Implementation**

| Research Step | Platform Tab | Implementation |
|---------------|--------------|----------------|
| Data Collection | Tab 1: Upload | Flexible JSONB structure, batch management |
| Label Assignment | Tab 2: Labeling | Rule-based + manual labeling with 6 label types |
| Train/Test Split | Tab 3: Target | 65/35 split OR 5-fold CV (stratified) |
| **Variable Filtration** | **Tab 4: Preprocessing Step 1** | **Remove >50% missing variables** ✨ |
| **Imputation** | **Tab 4: Preprocessing Step 2** | **Median/Mode imputation** ✨ |
| **Winsorization** | **Tab 4: Preprocessing Step 3** | **Cap at 1%/99% percentiles** ✨ |
| **Standardization** | **Tab 4: Preprocessing Step 4** | **Z-score normalization** ✨ |
| Feature Engineering | Tab 5: Features | Clinical ratios, temporal, derived scores |
| Feature Selection | Tab 6: Feature Selection | LASSO (α=0.00001) + manual selection |
| Model Validation | Tab 7: Validation | Pre-flight quality checks |
| Model Training | (Next: ML Training Page) | Random Forest, XGBoost, etc. |

✨ **NEW** = Just implemented to match research exactly!

---

## 🔑 Key Implementation Details

### **Preprocessing API Integration**
```javascript
// Complete Pipeline (All 4 Steps)
POST /api/v1/eda/datasets/{dataset_id}/preprocess/complete-pipeline
Body: {
  filter_missing_threshold: 0.5,
  imputation_strategy: { default: "median" },
  winsorize_lower: 0.01,
  winsorize_upper: 0.99,
  standardization_method: "standard"
}
Response: {
  success: true,
  pipeline_report: {
    original_columns: 45,
    final_columns: 38,
    columns_removed: 7,
    final_rows: 104,  // Preserved!
    steps: [filtration_report, imputation_report, winsorization_report, standardization_report]
  },
  processed_file: "dataset_preprocessed.csv"
}

// Individual Step APIs:
POST /api/v1/eda/datasets/{id}/preprocess/filter-variables?threshold=0.5
POST /api/v1/eda/datasets/{id}/preprocess/missing-values
POST /api/v1/eda/datasets/{id}/preprocess/winsorize?lower_percentile=0.01&upper_percentile=0.99
POST /api/v1/eda/datasets/{id}/preprocess/normalize
```

### **State Management**
```javascript
Preprocessing State Variables (NEW):
  - preprocessingResults: Complete pipeline report
  - preprocessingStep: Current step ('filtration', 'imputation', 'winsorization', 'standardization', 'complete')
  - filtrationThreshold: 0.5 (50% missing threshold)
  - imputationStrategy: 'median'
  - winsorLower: 0.01, winsorUpper: 0.99
  - standardizationMethod: 'standard'
  - preprocessingInProgress: Boolean (loading state)
  - Individual step reports: filtrationReport, imputationReport, winsorizeReport, standardizationReport
```

---

## 📝 Testing Checklist

### **End-to-End Workflow Test**
```
□ 1. Login with valid credentials
□ 2. Navigate to Dashboard → Data Catalog
□ 3. Select dataset OR upload new one
□ 4. Navigate to Data Preparation Page
□ 5. Tab 1: Confirm dataset selected
□ 6. Tab 2: Apply rule-based labeling (e.g., SLEDAI → Severity)
□ 7. Tab 2: Verify 80%+ labeling progress
□ 8. Tab 3: Select target column (labels_disease_severity)
□ 9. Tab 3: Configure validation (65/35 split OR 5-fold CV)
□ 10. Tab 4: Run Complete Preprocessing Pipeline  ✨ NEW
□ 11. Tab 4: Verify 4/4 steps complete
□ 12. Tab 4: Check preprocessing report (columns removed, rows preserved)
□ 13. Tab 5: Enable feature engineering (CRP/ESR ratio, NLR, etc.)
□ 14. Tab 5: Run feature engineering
□ 15. Tab 6: Select features (Manual, LASSO, or Combined)
□ 16. Tab 6: Verify finalFeatures.length > 0
□ 17. Tab 7: Run validation checks
□ 18. Tab 7: Confirm 0 errors
□ 19. Tab 8: Review summary
□ 20. Tab 8: Click "Proceed to ML Training"
□ 21. Verify navigation to ML Training Page with prepared dataset
```

---

## 🎉 Summary

### **Pipeline Flow: Login → ML Training**
```
Login → Dashboard → Data Catalog → Data Preparation (8 tabs) → ML Training

Tab Flow:
  Upload → Labeling → Target → Preprocessing → Features → Feature Selection → Validation → Summary
    ↓         ↓          ↓           ↓             ↓              ↓                ↓           ↓
  Select    Label    Configure   Transform       Derive        Select         Validate    Review
  Dataset   Records  Validation   Data (NEW!)   Features      Best Ones      Quality     & Launch

Research Alignment:
  ✅ Variable Filtration (>50% missing)
  ✅ Imputation (Median/Mode)
  ✅ Winsorization (1%/99% percentiles) - Preserves n=104
  ✅ Standardization (Z-score)
  ✅ Feature Engineering (Clinical ratios, temporal, derived)
  ✅ Feature Selection (LASSO α=0.00001 + manual)
  ✅ Cross-Validation (5-fold, stratified)
  ✅ 65/35 Train/Test Split

Sample Size Protection:
  - Winsorization CAPS outliers (doesn't remove rows)
  - Imputation FILLS missing values (doesn't remove rows)
  - Variable filtration removes COLUMNS (not rows)
  - Final dataset: 104 Female SLE patients PRESERVED
```

---

## 🚀 Next Steps

1. **Transfer Files:**
   - `app/services/preprocessing.py` (winsorization + filtration methods)
   - `app/api/endpoints/eda.py` (3 new preprocessing endpoints)
   - `frontend/src/pages/DataPreparationPage.jsx` (Tab 4 UI + renumbering)

2. **Restart Backend:**
   ```bash
   cd ~/usm-autoimmune-ml-platform
   docker compose restart fastapi
   ```

3. **Test Complete Pipeline:**
   - Upload/select dataset
   - Label records (rule-based)
   - Configure target + CV
   - Run preprocessing pipeline
   - Verify all 4 steps complete
   - Continue to feature engineering

4. **Validate Research Alignment:**
   - Compare platform output with research framework diagram
   - Verify preprocessing steps match exactly
   - Confirm sample size preserved (n=104)

---

**The pipeline now matches your research methodology exactly from login to ML training!** 🎯
