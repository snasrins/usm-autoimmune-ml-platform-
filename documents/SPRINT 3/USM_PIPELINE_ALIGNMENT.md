# USM Autoimmune ML Platform - Research Framework Alignment

## Executive Summary

This document demonstrates how our ML platform pipeline aligns with the USM Systemic Lupus Erythematosus (SLE) research methodology. The platform implements the complete research framework from data acquisition through to transparent risk scoring.

---

## 1. Research Framework Overview

### Study Design (As per USM Methodology)
| Component | USM Research | Platform Implementation |
|-----------|--------------|-------------------------|
| **Dataset** | 104 Female SLE Patients | ✅ Flexible data import supporting any cohort |
| **Initial Features** | 149 features (demographics, blood, immunology) | ✅ Dynamic schema - no hardcoded columns |
| **Target Variable** | SLEDAI-2000 binary (≤4 low, >4 high) | ✅ Configurable target via labeling UI |
| **Train/Test Split** | 65% / 35% stratified | ✅ Default: 65%/35% with stratification option |

---

## 2. Data Preprocessing Pipeline Alignment

### USM Methodology → Platform Implementation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA PREPROCESSING PIPELINE                       │
├─────────────────────────────────────────────────────────────────────┤
│  USM Research Step              │  Platform Component               │
├─────────────────────────────────┼───────────────────────────────────┤
│  1. Variable Filtration         │  DataPreparationPage              │
│     Remove >50% missing vars    │  → filter-variables endpoint      │
│                                 │  → threshold=0.5 (configurable)   │
├─────────────────────────────────┼───────────────────────────────────┤
│  2. Imputation                  │  DataPreparationPage              │
│     - Continuous: Median        │  → preprocess/missing-values      │
│     - Categorical: Mode         │  → strategy: 'median' (default)   │
├─────────────────────────────────┼───────────────────────────────────┤
│  3. Outlier Handling            │  DataPreparationPage              │
│     Winsorize 1st & 99th %ile   │  → preprocess/winsorize           │
│                                 │  → lower=0.01, upper=0.99         │
├─────────────────────────────────┼───────────────────────────────────┤
│  4. Standardization             │  DataPreparationPage              │
│     Z-score normalization       │  → preprocess/normalize           │
│                                 │  → method='standard' (Z-score)    │
└─────────────────────────────────┴───────────────────────────────────┘
```

### Platform API Endpoints (Matching USM Steps)
```python
# Step 1: Variable Filtration (Remove >50% missing)
POST /api/v1/eda/datasets/{batch_id}/preprocess/filter-variables?threshold=0.5

# Step 2: Imputation (Median for continuous, Mode for categorical)
POST /api/v1/eda/datasets/{batch_id}/preprocess/missing-values
Body: {"strategy": "median"}

# Step 3: Outlier Handling (Winsorize at 1st and 99th percentiles)
POST /api/v1/eda/datasets/{batch_id}/preprocess/winsorize?lower_percentile=0.01&upper_percentile=0.99

# Step 4: Standardization (Z-score)
POST /api/v1/eda/datasets/{batch_id}/preprocess/normalize?method=standard
```

---

## 3. Target Variable Configuration (SLEDAI-2000 Binary)

### USM Methodology
- **Target**: SLEDAI-2000 score dichotomized as binary classification
- **Low Activity**: SLEDAI ≤ 4
- **High Activity**: SLEDAI > 4

### Platform Implementation
The platform supports rule-based labeling that exactly matches USM methodology:

```javascript
// RuleBasedLabelingWorkflow.jsx - Disease Classification Preset
{
  sourceColumn: 'SLEDAI',
  targetColumn: 'labels_disease_classification',
  rules: [
    { condition: '<= 4', label: 'Low', description: 'Low disease activity (SLEDAI ≤4)' },
    { condition: '> 4', label: 'High', description: 'High disease activity (SLEDAI >4)' }
  ]
}
```

**API Endpoint:**
```python
POST /api/v1/labeling/rule-based-label
Body: {
    "batch_id": "uuid",
    "source_column": "SLEDAI",
    "target_column": "labels_disease_classification",
    "rules": [
        {"condition": "<= 4", "label": "Low"},
        {"condition": "> 4", "label": "High"}
    ]
}
```

---

## 4. Feature Engineering & Selection

### USM Feature Selection Pipeline
1. **Clinical Features** → Extract from raw data
2. **Correlation Detection** → Identify redundant features
3. **Derived Features** → Create composite pathological features
4. **Clinician Selection** → Domain expert curation
5. **LASSO Feature Selection** → Automatic feature importance ranking

### Platform Feature Engineering
```
┌────────────────────────────────────────────────────────────────────┐
│              FEATURE ENGINEERING PIPELINE                          │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐ │
│  │   Clinical   │───►│  Derived     │───►│  LASSO Feature       │ │
│  │   Features   │    │  Features    │    │  Selection           │ │
│  └──────────────┘    └──────────────┘    └──────────────────────┘ │
│        ▲                   ▲                       ▲               │
│        │                   │                       │               │
│  FeatureEngineering   Composite         DatasetGenerator          │
│  Pipeline             Features          (LASSO enabled)            │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### Composite Pathological Features (USM Methodology)
| Feature | Definition | Platform Implementation |
|---------|------------|------------------------|
| **Pancytopenia** | Low HGB + Low PLT + Low WBC | ✅ `create_composite_pathological_features()` |
| **Liver Damage** | ALT or AST > 70th percentile | ✅ Percentile-based thresholds |
| **Cytopenia Index** | Count of low blood cell types | ✅ Composite scoring |
| **WBC_low, WBC_high** | < 10th, > 90th percentile | ✅ Percentile binning |
| **PLT_low, PLT_high** | < 10th, > 90th percentile | ✅ Percentile binning |
| **HGB_low, HGB_high** | < 10th, > 90th percentile | ✅ Percentile binning |
| **CRP_high, ESR_high** | > 79th percentile | ✅ Inflammation markers |

### Top LASSO-Selected Features (USM Study Results)
Based on USM research, the most predictive features were:
1. **CRP_high** (0.080) - Inflammation marker
2. **C4** (0.071) - Complement level
3. **Urine protein quantification** (0.066)
4. **ACR** (0.065)
5. **C3** (0.058) - Complement level
6. **PLT_high** (0.050)
7. **ALB** (0.043)
8. **NK** (0.038) - Natural killer cells
9. **PLT_low** (0.035)
10. **IgM** (0.028)

---

## 5. Machine Learning Models

### USM Research Models (11 Algorithms)
All models from the USM framework are implemented:

| Model | USM CV-AUC | Platform Status |
|-------|------------|-----------------|
| Random Forest | 0.844 ± 0.105 | ✅ Implemented |
| LightGBM | 0.832 ± 0.079 | ✅ Implemented |
| SVM | 0.812 ± 0.114 | ✅ Implemented |
| Logistic Regression | 0.814 ± 0.050 | ✅ Implemented |
| XGBoost | 0.777 ± 0.051 | ✅ Implemented |
| Ridge Classifier | 0.773 ± 0.122 | ✅ Implemented |
| Linear Discriminant Analysis | 0.793 ± 0.126 | ✅ Implemented |
| Gradient Boosting | 0.626 ± 0.116 | ✅ Implemented |
| K-Nearest Neighbors | 0.587 ± 0.107 | ✅ Implemented |
| Decision Tree | 0.718 ± 0.155 | ✅ Implemented |
| ANN (MLP) | 0.718 ± - | ✅ Implemented |

### Two-Stage Validation Strategy
```
┌─────────────────────────────────────────────────────────────────────┐
│                    VALIDATION STRATEGY                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  STAGE 1: INTERNAL VALIDATION                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Stratified 5-Fold Cross-Validation                          │   │
│  │  - Hyperparameter tuning (Optuna: 30 trials)                 │   │
│  │  - Model stability assessment                                 │   │
│  │  - Out-of-fold (OOF) predictions for ensemble                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▼                                       │
│  STAGE 2: EXTERNAL VALIDATION                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  35% Held-out Test Set                                        │   │
│  │  - Simulate real clinical deployment                          │   │
│  │  - Final performance metrics                                  │   │
│  │  - ROC-AUC, Accuracy, Precision, F1, Specificity             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Platform Implementation
```python
# TrainingJobsPage.jsx - Default Configuration (Matches USM)
config = {
    testSize: 0.35,        # 35% test (USM: 35%)
    nTrials: 30,           # Optuna optimization trials
    cvFolds: 5,            # 5-fold cross-validation (USM standard)
    randomState: 42        # Reproducibility
}
```

---

## 6. Performance Metrics (USM Test Set Results)

### Comprehensive Evaluation Metrics
| Model | Accuracy | Precision | F1-Score | Specificity | AUC |
|-------|----------|-----------|----------|-------------|-----|
| Logistic Regression | 0.8448 | 0.8571 | 0.7359 | 0.9545 | 0.8667 |
| SVM | 0.8378 | 0.8000 | 0.7273 | 0.9200 | 0.8667 |
| Random Forest | 0.7568 | 0.6667 | 0.5714 | 0.8800 | 0.8833 |
| Ridge Classifier | 0.8108 | 0.6923 | 0.7200 | 0.8400 | 0.8600 |
| LDA | 0.8108 | 0.6923 | 0.7200 | 0.8400 | 0.8533 |
| LightGBM | 0.7568 | 0.6364 | 0.6087 | 0.8400 | 0.8333 |
| Decision Tree | 0.8108 | 0.7778 | 0.6667 | 0.9200 | 0.7017 |

### Platform Evaluation Endpoints
```python
# Model performance metrics available via:
GET /api/v1/ml/train/status/{job_id}

# Returns:
{
    "metrics": {
        "oof_auc": 0.85,        # Cross-validation AUC
        "test_auc": 0.87,       # Held-out test AUC
        "accuracy": 0.84,
        "precision": 0.86,
        "recall": 0.73,
        "f1_score": 0.79,
        "specificity": 0.95
    }
}
```

---

## 7. Scorecard System (White-Box Model)

### USM Scorecard Methodology
The USM study developed a transparent scorecard system for clinical interpretability:

1. **Dynamic Binning** - Data-driven bin creation using rolling mean algorithm
2. **Score Scaling** - Convert model coefficients to point-based scoring
3. **Risk Classification** - Map total scores to risk groups

### Binning Strategy
| Step | Description | Platform Support |
|------|-------------|------------------|
| Feature Binning | Divide continuous variables into value ranges | ✅ `create_composite_pathological_features()` |
| Score Assignment | Assign points based on coefficient weights | ✅ Feature importance extraction |
| Total Score | Sum of feature scores | ✅ Prediction probabilities |
| Risk Group | Threshold-based classification | ✅ Binary classification output |

### Scorecard Performance (USM Results)
```
┌────────────────────────────────────────────────────────────────────┐
│                WHITE-BOX SCORECARD PERFORMANCE                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  AUC = 0.917 [95% CI: 0.880 - 0.937]                              │
│                                                                     │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐        │
│  │  Accuracy   │  Precision  │  F1-Score   │    AUC      │        │
│  ├─────────────┼─────────────┼─────────────┼─────────────┤        │
│  │   0.8649    │   0.7333    │   0.8148    │   0.9167    │        │
│  └─────────────┴─────────────┴─────────────┴─────────────┘        │
│                                                                     │
│  OUTPERFORMS all individual ML models!                             │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### Top Scorecard Features (Weight-Based)
| Feature | Score Weight |
|---------|-------------|
| CRP_high | ~16 points |
| C3 | ~14 points |
| IgM | ~12 points |
| Urine protein quantification | ~11 points |
| PLT_high | ~9 points |
| PLT_low | ~8 points |
| HGB_high | ~7 points |
| ALB | ~6 points |

---

## 8. Platform Pipeline Flow (Complete Alignment)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    USM AUTOIMMUNE ML PLATFORM PIPELINE                    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────┐                                                         │
│  │  Data       │  Upload Excel/CSV with clinical data                    │
│  │  Import     │  → ImportPreviewStaging table                           │
│  └──────┬──────┘                                                         │
│         │                                                                 │
│         ▼                                                                 │
│  ┌─────────────┐                                                         │
│  │  Labeling   │  Rule-based labeling: SLEDAI ≤4 → Low, >4 → High       │
│  │  (Target)   │  → labels_disease_classification column                 │
│  └──────┬──────┘                                                         │
│         │                                                                 │
│         ▼                                                                 │
│  ┌─────────────┐  ┌───────────────────────────────────────────────────┐ │
│  │  Preproc-   │  │ 1. Filter variables (>50% missing)                │ │
│  │  essing     │──│ 2. Imputation (median/mode)                       │ │
│  │  (Layer 5)  │  │ 3. Winsorize (1st & 99th percentile)              │ │
│  └──────┬──────┘  │ 4. Z-score standardization                        │ │
│         │         └───────────────────────────────────────────────────┘ │
│         ▼                                                                 │
│  ┌─────────────┐  ┌───────────────────────────────────────────────────┐ │
│  │  Feature    │  │ • Composite features (pancytopenia, liver damage) │ │
│  │  Engineering│──│ • Percentile-based binning (low/high)             │ │
│  │  (Layer 6)  │  │ • LASSO feature selection                         │ │
│  └──────┬──────┘  └───────────────────────────────────────────────────┘ │
│         │                                                                 │
│         ▼                                                                 │
│  ┌─────────────┐  ┌───────────────────────────────────────────────────┐ │
│  │  ML         │  │ • 11 models (RF, LR, SVM, XGBoost, LightGBM...)   │ │
│  │  Training   │──│ • 5-fold stratified CV                            │ │
│  │  (Layer 7)  │  │ • 65%/35% train/test split                        │ │
│  └──────┬──────┘  │ • Optuna hyperparameter optimization              │ │
│         │         └───────────────────────────────────────────────────┘ │
│         ▼                                                                 │
│  ┌─────────────┐  ┌───────────────────────────────────────────────────┐ │
│  │  Evaluation │  │ • ROC-AUC, Accuracy, Precision, F1, Specificity  │ │
│  │  & Scoring  │──│ • Model comparison dashboard                      │ │
│  │  (Layer 8)  │  │ • Scorecard generation (clinically interpretable) │ │
│  └─────────────┘  └───────────────────────────────────────────────────┘ │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Key Files Implementing USM Methodology

| Component | File | Purpose |
|-----------|------|---------|
| Data Import | `app/api/endpoints/flexible.py` | Upload clinical Excel/CSV |
| Labeling | `app/api/endpoints/labeling.py` | Rule-based SLEDAI classification |
| Preprocessing | `app/api/endpoints/eda.py` | Filter, impute, winsorize, normalize |
| Feature Engineering | `app/ml/feature_engineering_pipeline.py` | Composite features, LASSO |
| Dataset Generation | `app/ml/training/dataset_generator.py` | Train/test split, scaling |
| Model Training | `app/ml/training/base_model_trainer.py` | 11 ML algorithms |
| Evaluation | `app/api/endpoints/training.py` | Metrics, comparison |
| Frontend Workflow | `frontend/src/pages/DataPreparationPage.jsx` | Complete ML prep UI |

---

## 10. Summary: Platform ↔ USM Alignment

| USM Research Component | Platform Feature | Status |
|------------------------|------------------|--------|
| 104 Female SLE dataset | Flexible data import | ✅ |
| 149 initial features | Dynamic schema (no hardcoding) | ✅ |
| SLEDAI-2000 binary target | Rule-based labeling UI | ✅ |
| 65%/35% stratified split | Configurable train/test split | ✅ |
| Remove >50% missing variables | Variable filtration endpoint | ✅ |
| Median/mode imputation | Missing values preprocessing | ✅ |
| Winsorize 1%/99% | Outlier handling endpoint | ✅ |
| Z-score standardization | Normalization endpoint | ✅ |
| Composite pathological features | Feature engineering pipeline | ✅ |
| LASSO feature selection | Dataset generator with LASSO | ✅ |
| 11 ML algorithms | All models implemented | ✅ |
| 5-fold stratified CV | Cross-validation with Optuna | ✅ |
| ROC-AUC, Accuracy, Precision, F1, Specificity | Complete metrics dashboard | ✅ |
| White-box scorecard | Feature importance extraction | ✅ |

---

## Appendix: Quick Start for USM Methodology Replication

### Step 1: Upload Data
```bash
POST /api/v1/flexible/upload
Content-Type: multipart/form-data
file: SLE_clinical_data.xlsx
```

### Step 2: Apply Labels (SLEDAI Binary)
```bash
POST /api/v1/labeling/rule-based-label
{
    "batch_id": "your-batch-id",
    "source_column": "SLEDAI",
    "target_column": "labels_disease_classification",
    "rules": [
        {"condition": "<= 4", "label": "Low"},
        {"condition": "> 4", "label": "High"}
    ]
}
```

### Step 3: Run Preprocessing Pipeline
```bash
POST /api/v1/eda/datasets/{batch_id}/preprocess/complete-pipeline
{
    "filter_threshold": 0.5,
    "imputation_strategy": "median",
    "winsorize_lower": 0.01,
    "winsorize_upper": 0.99,
    "normalize_method": "standard"
}
```

### Step 4: Train Models
```bash
POST /api/v1/ml/train/prepare-dataset
{
    "batch_id": "your-batch-id",
    "target_column": "labels_disease_classification",
    "test_size": 0.35
}
```

### Step 5: Start Training
```bash
POST /api/v1/ml/train/start
{
    "dataset_id": "dataset-job-id",
    "models": ["random_forest", "logistic_regression", "svm", "xgboost", ...],
    "n_trials": 30,
    "cv_folds": 5
}
```

---

*Document Version: 1.0*
*Last Updated: April 27, 2026*
*Aligned with: USM SLE Research Framework (Sprint 3 TSD)*
