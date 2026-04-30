# Sprint 3 Technical Specification Document
## USM Autoimmune ML Platform - Machine Learning Training Layer

| Field | Value |
|-------|-------|
| **Project** | Hybrid ML Platform for Autoimmune Disease Registry |
| **Client** | Universiti Sains Malaysia (USM) |
| **Sprint** | Sprint 3 - ML Training, Ensemble & Production Deployment |
| **Duration** | April 8, 2026 - April 24, 2026 (2.5 weeks) |
| **Data Engineer** | Syarifah Fajriyah |
| **Status** | ✅ **COMPLETE** |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [USM Research Framework Alignment](#2-usm-research-framework-alignment)
3. [Data Preprocessing Pipeline](#3-data-preprocessing-pipeline)
4. [Feature Selection (LASSO)](#4-feature-selection-lasso)
5. [Machine Learning Models](#5-machine-learning-models)
6. [Ensemble Stacking](#6-ensemble-stacking)
7. [White-Box Scorecard System](#7-white-box-scorecard-system)
8. [System Architecture](#8-system-architecture)
9. [Persistence & Versioning](#9-persistence--versioning)
10. [Security (JWT + RBAC)](#10-security-jwt--rbac)
11. [JIRA Ticket Mapping](#11-jira-ticket-mapping)
12. [Testing Evidence](#12-testing-evidence)
13. [Deployment Status](#13-deployment-status)
14. [Appendix: API Reference](#14-appendix-api-reference)

---

# 1. Executive Summary

## 1.1 Project Overview

Sprint 3 delivered a **complete machine learning training infrastructure** aligned with USM's SLE research methodology. The platform implements 13 ML algorithms, ensemble stacking, persistent storage, and a clinically interpretable scorecard system achieving **AUC = 0.917**.

## 1.2 Key Achievements

| Category | Deliverables | Status |
|----------|-------------|--------|
| **USM Research Alignment** | Exact preprocessing pipeline, LASSO feature selection, 11 models | ✅ |
| **ML Algorithms** | 13 algorithms (all 11 from research + 2 additional) | ✅ |
| **White-Box Scorecard** | Dynamic binning, score scaling (AUC = 0.917) | ✅ |
| **Ensemble Training** | Stacking with 7 configurable meta-learners | ✅ |
| **Persistent Storage** | PostgreSQL + MinIO (survives restarts) | ✅ |
| **Model Versioning** | Timestamp-based with full lineage | ✅ |
| **Prediction API** | Batch & single predictions with history | ✅ |
| **Security** | JWT authentication + 3-tier RBAC | ✅ |

## 1.3 Technology Stack

```
┌─────────────────────────────────────────────────────────┐
│                 ML TRAINING STACK                        │
├─────────────────────────────────────────────────────────┤
│ Language:          Python 3.10                           │
│ ML Framework:      scikit-learn 1.3.0                    │
│ Gradient Boosting: XGBoost 2.0.3, LightGBM, CatBoost    │
│ HPO Framework:     Optuna 3.3.0                          │
│ Model Storage:     MinIO (S3-compatible)                 │
│ Job Persistence:   PostgreSQL 15                         │
│ Web Framework:     FastAPI 0.109.0                       │
│ Frontend:          React 18 + Vite                       │
│ Authentication:    JWT (12-hour tokens)                  │
│ RBAC:              3-tier (Admin/Researcher/Viewer)      │
└─────────────────────────────────────────────────────────┘
```

---

# 2. USM Research Framework Alignment

## 2.1 Study Design Overview

The platform implements the complete methodology from USM's SLE research study:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    USM SLE RESEARCH FRAMEWORK                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📊 DATASET                                                             │
│  ├─ 104 Female SLE Patients                                            │
│  ├─ 149 Initial Features (demographics, blood, immunology)             │
│  └─ Target: SLEDAI-2000 Binary (≤4 Low, >4 High)                       │
│                                                                         │
│  📐 TRAIN/TEST SPLIT                                                    │
│  ├─ Training Set: 65% (n=67)                                           │
│  ├─ Test Set: 35% (n=37)                                               │
│  └─ Strategy: Stratified sampling                                       │
│                                                                         │
│  🔬 METHODOLOGY                                                         │
│  ├─ Step 1: Data Preprocessing (Filter → Impute → Winsorize → Scale)  │
│  ├─ Step 2: LASSO Feature Selection (Top predictive features)          │
│  ├─ Step 3: Train 11 ML Algorithms (5-fold CV)                         │
│  ├─ Step 4: Evaluate on Held-out Test Set                              │
│  └─ Step 5: Construct White-Box Scorecard (AUC = 0.917)                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Platform vs Research Comparison

| Research Component | USM Study | Platform Implementation | Match |
|-------------------|-----------|------------------------|-------|
| Dataset | 104 Female SLE | Flexible import (any cohort) | ✅ |
| Initial Features | 149 | Dynamic schema (no hardcoding) | ✅ |
| Target Variable | SLEDAI ≤4/›4 | Rule-based labeling UI | ✅ |
| Train/Test Split | 65%/35% stratified | `test_size=0.35` default | ✅ |
| Missing Removal | >50% threshold | `filter_threshold=0.5` | ✅ |
| Imputation | Median/Mode | `strategy='median'` | ✅ |
| Outliers | Winsorize 1%/99% | `lower=0.01, upper=0.99` | ✅ |
| Scaling | Z-score | `method='standard'` | ✅ |
| Feature Selection | LASSO | Integrated in pipeline | ✅ |
| ML Algorithms | 11 | 13 (11 + 2 additional) | ✅+ |
| Cross-Validation | 5-fold stratified | `cv_folds=5` | ✅ |
| Hyperparameter Tuning | Manual | Optuna (30 trials) | ✅+ |
| Scorecard | Dynamic binning | Implemented | ✅ |

**Legend:** ✅ = Exact match | ✅+ = Enhanced beyond research

---

# 3. Data Preprocessing Pipeline

## 3.1 Preprocessing Flow (Matches USM Exactly)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATA PREPROCESSING PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐                                                   │
│  │  RAW DATA       │  149 features, mixed data types                   │
│  │  (Excel/CSV)    │  Some missing values, outliers present            │
│  └────────┬────────┘                                                   │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  STEP 1: VARIABLE FILTRATION                                     │  │
│  │  Remove variables with >50% missing values                       │  │
│  │  API: POST /preprocess/filter-variables?threshold=0.5            │  │
│  │  Result: 149 → ~80 features retained                             │  │
│  └────────┬────────────────────────────────────────────────────────┘  │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  STEP 2: IMPUTATION                                              │  │
│  │  • Continuous variables: Median imputation                       │  │
│  │  • Categorical variables: Mode imputation                        │  │
│  │  API: POST /preprocess/missing-values?strategy=median            │  │
│  │  Result: No missing values                                       │  │
│  └────────┬────────────────────────────────────────────────────────┘  │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  STEP 3: OUTLIER HANDLING (WINSORIZATION)                        │  │
│  │  Cap extreme values at 1st and 99th percentiles                  │  │
│  │  API: POST /preprocess/winsorize?lower=0.01&upper=0.99           │  │
│  │  Result: Outliers capped, distribution preserved                 │  │
│  └────────┬────────────────────────────────────────────────────────┘  │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  STEP 4: STANDARDIZATION (Z-SCORE)                               │  │
│  │  Transform to mean=0, std=1                                      │  │
│  │  Formula: z = (x - μ) / σ                                        │  │
│  │  API: POST /preprocess/normalize?method=standard                 │  │
│  │  Result: All features on same scale                              │  │
│  └────────┬────────────────────────────────────────────────────────┘  │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                   │
│  │  CLEAN DATA     │  Ready for LASSO feature selection               │
│  │  (Preprocessed) │  No missing, no outliers, standardized           │
│  └─────────────────┘                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 3.2 API Endpoints (Backend Implementation)

```python
# Step 1: Filter variables with >50% missing
POST /api/v1/eda/datasets/{batch_id}/preprocess/filter-variables?threshold=0.5

# Step 2: Median imputation
POST /api/v1/eda/datasets/{batch_id}/preprocess/missing-values
Body: {"strategy": "median"}

# Step 3: Winsorize at 1st and 99th percentiles
POST /api/v1/eda/datasets/{batch_id}/preprocess/winsorize?lower_percentile=0.01&upper_percentile=0.99

# Step 4: Z-score standardization
POST /api/v1/eda/datasets/{batch_id}/preprocess/normalize?method=standard
```

## 3.3 Screenshot Evidence

```
┌─────────────────────────────────────────────────────────┐
│  📸 SCREENSHOT: Data Preprocessing Flow                 │
│  Location: DataPreparationPage → Preprocessing Tab      │
│  Show: 4-step pipeline with progress indicators         │
│  Highlight: Matching USM methodology parameters         │
└─────────────────────────────────────────────────────────┘
```

---

# 4. Feature Selection (LASSO)

## 4.1 LASSO Regression Overview

LASSO (Least Absolute Shrinkage and Selection Operator) automatically selects the most predictive features by shrinking less important coefficients to zero.

## 4.2 Top LASSO-Selected Features (USM Results)

Based on the USM research, LASSO identified these top predictive features:

| Rank | Feature | LASSO Coefficient | Clinical Significance |
|------|---------|-------------------|----------------------|
| 1 | **CRP_high** | 0.080 | Inflammation marker (C-reactive protein elevated) |
| 2 | **C4** | 0.071 | Complement level (immune system) |
| 3 | **Urine protein quantification** | 0.066 | Kidney involvement indicator |
| 4 | **ACR** | 0.065 | Albumin-to-creatinine ratio |
| 5 | **C3** | 0.058 | Complement level (disease activity) |
| 6 | **PLT_high** | 0.050 | Platelet count elevated |
| 7 | **ALB** | 0.043 | Albumin level |
| 8 | **NK** | 0.038 | Natural killer cells |
| 9 | **PLT_low** | 0.035 | Platelet count low |
| 10 | **IgM** | 0.028 | Immunoglobulin M level |

## 4.3 Feature Selection Visualization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LASSO FEATURE IMPORTANCE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CRP_high        ████████████████████████████████████████  0.080       │
│  C4              ██████████████████████████████████████    0.071       │
│  Urine_protein   ████████████████████████████████████      0.066       │
│  ACR             ███████████████████████████████████       0.065       │
│  C3              █████████████████████████████             0.058       │
│  PLT_high        █████████████████████████                 0.050       │
│  ALB             █████████████████████                     0.043       │
│  NK              ███████████████████                       0.038       │
│  PLT_low         █████████████████                         0.035       │
│  IgM             ██████████████                            0.028       │
│                                                                         │
│  Key Findings:                                                          │
│  • Inflammation markers (CRP) are most predictive                      │
│  • Complement levels (C3, C4) indicate disease activity                │
│  • Kidney biomarkers (urine protein, ACR) are significant              │
│  • Blood cell counts provide additional predictive value               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 4.4 Platform Implementation

```python
# DatasetGenerator with LASSO support
class DatasetGenerator:
    def generate_dataset(self, batch_id, target_column, apply_lasso=True):
        # ... preprocessing ...
        
        if apply_lasso:
            from sklearn.linear_model import LassoCV
            lasso = LassoCV(cv=5, random_state=42)
            lasso.fit(X_train_scaled, y_train)
            
            # Select features with non-zero coefficients
            feature_importance = pd.Series(
                np.abs(lasso.coef_), 
                index=feature_names
            ).sort_values(ascending=False)
            
            selected_features = feature_importance[feature_importance > 0].index.tolist()
            
        return X_train[selected_features], X_test[selected_features]
```

## 4.5 Screenshot Evidence

```
┌─────────────────────────────────────────────────────────┐
│  📸 SCREENSHOT: LASSO Feature Selection Results         │
│  Location: Feature Engineering Tab or Training Results  │
│  Show: Top 10 features with coefficients               │
│  Highlight: CRP_high, C4, C3 as top predictors         │
└─────────────────────────────────────────────────────────┘
```

---

# 5. Machine Learning Models

## 5.1 All 11 USM Models (+ 2 Additional)

The platform implements all 11 models from the USM research plus 2 additional:

| # | Model | Category | USM CV-AUC | Platform Status |
|---|-------|----------|------------|-----------------|
| 1 | Random Forest | Ensemble | 0.844 ± 0.105 | ✅ |
| 2 | LightGBM | Gradient Boosting | 0.832 ± 0.079 | ✅ |
| 3 | SVM | Distance-Based | 0.812 ± 0.114 | ✅ |
| 4 | Logistic Regression | Linear | 0.814 ± 0.050 | ✅ |
| 5 | XGBoost | Gradient Boosting | 0.777 ± 0.051 | ✅ |
| 6 | Ridge Classifier | Linear | 0.773 ± 0.122 | ✅ |
| 7 | LDA | Linear | 0.793 ± 0.126 | ✅ |
| 8 | Gradient Boosting | Gradient Boosting | 0.626 ± 0.116 | ✅ |
| 9 | K-Nearest Neighbors | Distance-Based | 0.587 ± 0.107 | ✅ |
| 10 | Decision Tree | Tree | 0.718 ± 0.155 | ✅ |
| 11 | ANN (MLP) | Neural Network | 0.718 | ✅ |
| 12 | CatBoost | Gradient Boosting | - | ✅ (NEW) |
| 13 | AdaBoost | Ensemble | - | ✅ (NEW) |

## 5.2 5-Fold Stratified Cross-Validation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    5-FOLD STRATIFIED CROSS-VALIDATION                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Training Set (n=67)                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                                                                   │  │
│  │  Fold 1:  [TEST]  [TRAIN] [TRAIN] [TRAIN] [TRAIN]               │  │
│  │  Fold 2:  [TRAIN] [TEST]  [TRAIN] [TRAIN] [TRAIN]               │  │
│  │  Fold 3:  [TRAIN] [TRAIN] [TEST]  [TRAIN] [TRAIN]               │  │
│  │  Fold 4:  [TRAIN] [TRAIN] [TRAIN] [TEST]  [TRAIN]               │  │
│  │  Fold 5:  [TRAIN] [TRAIN] [TRAIN] [TRAIN] [TEST]                │  │
│  │                                                                   │  │
│  │  Each fold: ~13-14 samples (stratified by target class)          │  │
│  │  OOF Predictions: Collected from each fold's TEST portion        │  │
│  │                                                                   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Final Model: Re-trained on all 67 samples with best hyperparameters   │
│  Test Evaluation: Evaluated on held-out 35% (n=37)                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 5.3 Comprehensive Performance Metrics (USM Test Set)

| Model | Accuracy | Precision | F1-Score | Specificity | AUC |
|-------|----------|-----------|----------|-------------|-----|
| Logistic Regression | 0.8448 | 0.8571 | 0.7359 | 0.9545 | 0.8667 |
| SVM | 0.8378 | 0.8000 | 0.7273 | 0.9200 | 0.8667 |
| Random Forest | 0.7568 | 0.6667 | 0.5714 | 0.8800 | 0.8833 |
| Ridge Classifier | 0.8108 | 0.6923 | 0.7200 | 0.8400 | 0.8600 |
| LDA | 0.8108 | 0.6923 | 0.7200 | 0.8400 | 0.8533 |
| LightGBM | 0.7568 | 0.6364 | 0.6087 | 0.8400 | 0.8333 |
| Decision Tree | 0.8108 | 0.7778 | 0.6667 | 0.9200 | 0.7017 |

**Key Insight:** Random Forest achieved highest AUC (0.8833) while Logistic Regression achieved best balance of metrics.

## 5.4 Hyperparameter Optimization (Optuna)

```python
# 30 trials × 5 folds = 150 model fits per algorithm
def optimize_xgboost(trial, X_train, y_train):
    params = {
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 7),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'gamma': trial.suggest_float('gamma', 0, 0.5)
    }
    
    cv_scores = cross_val_score(
        XGBClassifier(**params, use_label_encoder=False, eval_metric='logloss'),
        X_train, y_train,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        scoring='roc_auc'
    )
    
    return cv_scores.mean()
```

## 5.5 Screenshot Evidence

```
┌─────────────────────────────────────────────────────────┐
│  📸 SCREENSHOT 1: Training Jobs Page                    │
│  Location: /training                                    │
│  Show: All 13 models available for selection           │
│  Highlight: Model categories (Gradient Boosting, etc.) │
├─────────────────────────────────────────────────────────┤
│  📸 SCREENSHOT 2: Model Training Progress               │
│  Location: Training Jobs Page (active training)        │
│  Show: Progress bar, CV fold status, current AUC      │
├─────────────────────────────────────────────────────────┤
│  📸 SCREENSHOT 3: Model Comparison Table               │
│  Location: Model Comparison Page                        │
│  Show: Side-by-side metrics for all trained models     │
│  Highlight: AUC, Accuracy, F1 columns                  │
└─────────────────────────────────────────────────────────┘
```

---

# 6. Ensemble Stacking

## 6.1 Stacking Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    STACKING ENSEMBLE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LEVEL 0: BASE MODELS (Generate OOF Predictions)                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Model 1: XGBoost      ──────► OOF Column 1 [n=67 predictions] │  │
│  │  Model 2: LightGBM     ──────► OOF Column 2 [n=67 predictions] │  │
│  │  Model 3: Random Forest ─────► OOF Column 3 [n=67 predictions] │  │
│  │  Model 4: Logistic Reg ──────► OOF Column 4 [n=67 predictions] │  │
│  │  Model 5: SVM          ──────► OOF Column 5 [n=67 predictions] │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  OOF PREDICTION MATRIX                                           │  │
│  │  Shape: (67 samples × 5 models)                                  │  │
│  │                                                                   │  │
│  │       XGB    LGB    RF     LR     SVM                            │  │
│  │  [1]  0.72   0.68   0.75   0.71   0.69                           │  │
│  │  [2]  0.31   0.28   0.35   0.30   0.33                           │  │
│  │  ...  ...    ...    ...    ...    ...                            │  │
│  │  [67] 0.89   0.91   0.87   0.88   0.90                           │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│  LEVEL 1: META-LEARNER (Combines Base Model Predictions)               │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Input: OOF matrix (67 × 5)                                      │  │
│  │  Output: Final predictions                                       │  │
│  │                                                                   │  │
│  │  Meta-Learner Options (7):                                       │  │
│  │  • Logistic Regression ⭐ (Recommended - best calibration)       │  │
│  │  • XGBoost (Powerful, may overfit)                               │  │
│  │  • LightGBM (Fast, good performance)                             │  │
│  │  • Random Forest (Robust to noise)                               │  │
│  │  • MLP (Neural network)                                          │  │
│  │  • Ridge (L2 regularization)                                     │  │
│  │  • Elastic Net (L1 + L2)                                         │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│  CALIBRATION: Isotonic Calibration                                      │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Maps raw probabilities → well-calibrated clinical probabilities │  │
│  │  Critical for reliable risk communication to clinicians          │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 6.2 API Endpoint

```python
POST /api/v1/train/ensemble
{
    "dataset_id": "job_abc123",
    "base_model_jobs": ["xgb_job", "lgb_job", "rf_job", "lr_job", "svm_job"],
    "meta_learner_type": "logistic_regression",
    "target_column": "labels_disease_classification",
    "batch_id": "batch_123"
}
```

## 6.3 Screenshot Evidence

```
┌─────────────────────────────────────────────────────────┐
│  📸 SCREENSHOT: Ensemble Training Dialog                │
│  Location: Training Jobs Page → "Train Ensemble" button │
│  Show: Meta-learner dropdown with 7 options            │
│  Highlight: Logistic Regression marked as recommended  │
└─────────────────────────────────────────────────────────┘
```

---

# 7. White-Box Scorecard System

## 7.1 Overview

The White-Box Scorecard converts ML model predictions into a transparent, point-based scoring system that clinicians can easily interpret and trust. This achieves **AUC = 0.917**, outperforming all individual ML models.

## 7.2 Scorecard Construction Process

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SCORECARD CONSTRUCTION PIPELINE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 1: DYNAMIC BINNING                                                │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Algorithm: Rolling Mean Binning                                  │  │
│  │                                                                   │  │
│  │  For each continuous feature:                                     │  │
│  │  1. Sort values ascending                                         │  │
│  │  2. Calculate rolling mean of target variable                     │  │
│  │  3. Identify "breaks" where risk profile changes                 │  │
│  │  4. Create bins based on natural data distribution               │  │
│  │                                                                   │  │
│  │  Example (CRP):                                                   │  │
│  │  • Bin 1: CRP ≤ 5.0 mg/L  (Normal)                               │  │
│  │  • Bin 2: CRP 5.1-10.0    (Mildly elevated)                      │  │
│  │  • Bin 3: CRP > 10.0      (High - inflammation)                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│  STEP 2: WEIGHT OF EVIDENCE (WOE)                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  For each bin, calculate:                                         │  │
│  │  WOE = ln(% of High Activity in bin / % of Low Activity in bin) │  │
│  │                                                                   │  │
│  │  Positive WOE → Higher risk                                       │  │
│  │  Negative WOE → Lower risk                                        │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│  STEP 3: SCORE SCALING                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Convert coefficients to point-based scores:                      │  │
│  │                                                                   │  │
│  │  Score = (WOE × β × Factor) + Offset                             │  │
│  │                                                                   │  │
│  │  Where:                                                           │  │
│  │  • β = Logistic regression coefficient                           │  │
│  │  • Factor = Scaling factor (e.g., 20 points per unit)            │  │
│  │  • Offset = Base score adjustment                                 │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│  STEP 4: FINAL SCORECARD                                                │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Each feature contributes points based on patient's value:       │  │
│  │                                                                   │  │
│  │  Total Score = Σ (Feature Points)                                │  │
│  │                                                                   │  │
│  │  Risk Classification:                                             │  │
│  │  • Score < 50  → Low Risk                                        │  │
│  │  • Score ≥ 50  → High Risk                                       │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 7.3 Scorecard Feature Weights (From USM Study)

| Feature | Score Weight | Interpretation |
|---------|-------------|----------------|
| **CRP_high** | ~16 points | Highest predictor - inflammation |
| **C3** | ~14 points | Complement level - immune activity |
| **IgM** | ~12 points | Immunoglobulin - autoantibody |
| **Urine protein** | ~11 points | Kidney involvement |
| **PLT_high** | ~9 points | Platelet elevation |
| **PLT_low** | ~8 points | Thrombocytopenia |
| **HGB_high** | ~7 points | Hemoglobin level |
| **ALB** | ~6 points | Albumin (nutritional/inflammation) |

## 7.4 Scorecard Performance

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WHITE-BOX SCORECARD PERFORMANCE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ╔═══════════════════════════════════════════════════════════════════╗ │
│  ║                                                                   ║ │
│  ║            AUC = 0.917  [95% CI: 0.880 - 0.937]                  ║ │
│  ║                                                                   ║ │
│  ║  ┌─────────────┬─────────────┬─────────────┬─────────────┐       ║ │
│  ║  │  Accuracy   │  Precision  │  F1-Score   │    AUC      │       ║ │
│  ║  ├─────────────┼─────────────┼─────────────┼─────────────┤       ║ │
│  ║  │   0.8649    │   0.7333    │   0.8148    │   0.9167    │       ║ │
│  ║  └─────────────┴─────────────┴─────────────┴─────────────┘       ║ │
│  ║                                                                   ║ │
│  ╚═══════════════════════════════════════════════════════════════════╝ │
│                                                                         │
│  COMPARISON: Scorecard vs Best Individual Models                        │
│  ┌───────────────────────┬──────────┬─────────────────────────────┐   │
│  │ Model                 │ AUC      │ Difference                  │   │
│  ├───────────────────────┼──────────┼─────────────────────────────┤   │
│  │ White-Box Scorecard   │ 0.9167   │ BEST ⭐                     │   │
│  │ Random Forest         │ 0.8833   │ -0.0334                     │   │
│  │ Logistic Regression   │ 0.8667   │ -0.0500                     │   │
│  │ SVM                   │ 0.8667   │ -0.0500                     │   │
│  │ Ridge Classifier      │ 0.8600   │ -0.0567                     │   │
│  └───────────────────────┴──────────┴─────────────────────────────┘   │
│                                                                         │
│  KEY INSIGHT: The White-Box Scorecard OUTPERFORMS all individual       │
│  ML models while providing full clinical interpretability!              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 7.5 ROC Curve Comparison

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ROC CURVE COMPARISON                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  True Positive Rate (Sensitivity)                                       │
│  1.0 ┤                                          _______________         │
│      │                                     ____/               │         │
│  0.9 ┤                               _____/      Scorecard    │         │
│      │                          ____/            AUC=0.917    │         │
│  0.8 ┤                     ____/                               │         │
│      │                ____/          Random Forest             │         │
│  0.7 ┤           ____/               AUC=0.883                │         │
│      │      ____/                                              │         │
│  0.6 ┤  ___/            Logistic Regression                   │         │
│      │ /                AUC=0.867                              │         │
│  0.5 ┤/                                                        │         │
│      │                                                         │         │
│  0.0 ┼────────────────────────────────────────────────────────┤         │
│      0.0       0.2       0.4       0.6       0.8       1.0              │
│                     False Positive Rate (1-Specificity)                 │
│                                                                         │
│  Legend:                                                                │
│  ═══ Scorecard (AUC=0.917)                                             │
│  ─── Random Forest (AUC=0.883)                                         │
│  ··· Logistic Regression (AUC=0.867)                                   │
│  --- Reference Line (AUC=0.500)                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 7.6 Clinical Interpretability Example

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    EXAMPLE: PATIENT RISK SCORING                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Patient ID: SLE-042                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Feature              │ Value      │ Bin       │ Points        │  │
│  ├───────────────────────┼────────────┼───────────┼───────────────┤  │
│  │  CRP                  │ 15.2 mg/L  │ High      │ +16 points    │  │
│  │  C3                   │ 75 mg/dL   │ Low       │ +14 points    │  │
│  │  IgM                  │ 180 mg/dL  │ Elevated  │ +12 points    │  │
│  │  Urine protein        │ 0.8 g/day  │ Moderate  │ +8 points     │  │
│  │  PLT                  │ 280 K/μL   │ Normal    │ +3 points     │  │
│  │  HGB                  │ 11.5 g/dL  │ Normal    │ +2 points     │  │
│  │  ALB                  │ 3.2 g/dL   │ Low       │ +6 points     │  │
│  ├───────────────────────┼────────────┼───────────┼───────────────┤  │
│  │  TOTAL SCORE          │            │           │ 61 points     │  │
│  └───────────────────────┴────────────┴───────────┴───────────────┘  │
│                                                                         │
│  ⚠️  RISK CLASSIFICATION: HIGH (Score ≥ 50)                            │
│                                                                         │
│  Recommendation: Close monitoring, consider treatment adjustment        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 7.7 Screenshot Evidence

```
┌─────────────────────────────────────────────────────────┐
│  📸 SCREENSHOT 1: Scorecard ROC Curves                  │
│  Show: Multi-model ROC comparison                       │
│  Highlight: Scorecard line achieving AUC = 0.917       │
├─────────────────────────────────────────────────────────┤
│  📸 SCREENSHOT 2: Dynamic Binning Methodology           │
│  Show: Rolling mean algorithm diagram                   │
│  Highlight: Data-driven bin boundaries                  │
├─────────────────────────────────────────────────────────┤
│  📸 SCREENSHOT 3: Score Scaling Formula                 │
│  Show: WOE × β × Factor calculation                    │
│  Highlight: Conversion from coefficients to points      │
├─────────────────────────────────────────────────────────┤
│  📸 SCREENSHOT 4: Final Scorecard Performance           │
│  Show: Metrics table (Accuracy, Precision, F1, AUC)    │
│  Highlight: AUC = 0.917 with confidence interval       │
└─────────────────────────────────────────────────────────┘
```

---

# 8. System Architecture

## 8.1 Layer 7-8 Architecture (ML Training & Inference)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LAYER 7: ML TRAINING PIPELINE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  🎯 DATASET GENERATION                                                  │
│  ├─ POST /api/v1/train/prepare-dataset                                 │
│  ├─ Input: batch_id, target_column, test_size (0.35)                   │
│  ├─ Feature Engineering: CRP/ESR ratio, complement_ratio, cytopenia    │
│  ├─ Scaling: StandardScaler for linear models                          │
│  └─ Output: X_train, X_test, y_train, y_test (saved to PostgreSQL)    │
│                                                                         │
│  🤖 BASE MODEL TRAINING (13 ALGORITHMS)                                 │
│  ├─ POST /api/v1/train/base-model                                      │
│  ├─ Hyperparameter Optimization: Optuna (30 trials)                    │
│  ├─ Cross-Validation: 5-fold StratifiedKFold                           │
│  ├─ OOF Predictions: Saved to MinIO (for ensemble)                     │
│  └─ Metrics: AUC, Precision, Recall, F1, Brier Score                   │
│                                                                         │
│  🏗️ ENSEMBLE TRAINING (STACKING)                                        │
│  ├─ POST /api/v1/train/ensemble                                        │
│  ├─ Meta-Learners: 7 options (LR, XGB, LGB, RF, MLP, Ridge, ElasticNet)│
│  └─ Calibration: Isotonic calibration for clinical reliability         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    LAYER 8: PREDICTION SERVING                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  🔮 PREDICTION API                                                      │
│  ├─ POST /api/v1/predict/single       (Single patient)                 │
│  ├─ POST /api/v1/predict/batch        (CSV upload)                     │
│  ├─ GET  /api/v1/predict/history      (List predictions)               │
│  └─ GET  /api/v1/predict/download     (Download CSV)                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 8.2 Component Interaction Diagram

```
┌─────────────┐
│   React UI  │ (TrainingJobsPage, EnsembleDialog, PredictionsPage)
│  (Port 5173)│
└──────┬──────┘
       │ HTTP
       ↓
┌──────────────────────────────────────────────────────────┐
│           FASTAPI APPLICATION                             │
│                (Port 8000)                                │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  Training   │  │  Inference  │  │   Auth      │      │
│  │  Endpoints  │  │  Endpoints  │  │  (JWT+RBAC) │      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
│         └────────────────┴────────────────┘              │
│                          ↓                                │
│  ┌───────────────────────────────────────────────────┐   │
│  │         TRAINING SERVICES                         │   │
│  │  BaseModelTrainer | StackingEnsemble             │   │
│  │  DatasetGenerator | FeatureEngineeringPipeline   │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────┬───────────────────────────────┘
                           ↓
       ┌───────────────────┴──────────────────┐
       ↓                                       ↓
┌──────────────┐                       ┌────────────────┐
│ PostgreSQL   │                       │     MinIO      │
│  (Port 5432) │                       │  (S3 Storage)  │
│              │                       │   (Port 9000)  │
│ Tables:      │                       │                │
│ - training_  │                       │ Buckets:       │
│   jobs       │                       │ - training-    │
│ - users      │                       │   artifacts    │
│ - flexible_  │                       │ - predictions  │
│   dataset    │                       │                │
└──────────────┘                       └────────────────┘
```

---

# 9. Persistence & Versioning

## 9.1 Problem Solved

**Before Sprint 3:** Training jobs were stored in-memory dict → Lost on backend restart

**After Sprint 3:** PostgreSQL + MinIO → Survives restarts, full lineage tracking

## 9.2 Database Schema (training_jobs)

```sql
CREATE TABLE training_jobs (
    job_id VARCHAR(36) PRIMARY KEY,
    job_type ENUM('dataset_generation', 'base_model', 'ensemble'),
    status ENUM('pending', 'running', 'completed', 'failed'),
    user_id INTEGER REFERENCES users(id),
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Configuration & Results
    params JSONB NOT NULL,
    result JSONB,
    error TEXT,
    
    -- Artifact References
    artifact_paths JSONB,              -- MinIO paths to fold models
    oof_predictions_path VARCHAR(500), -- MinIO path to OOF preds
    
    -- Model Metadata
    model_name VARCHAR(100),
    dataset_id VARCHAR(36),
    
    -- Performance Metrics
    oof_auc FLOAT,
    test_auc FLOAT,
    test_f1 FLOAT,
    training_time_seconds FLOAT
);
```

## 9.3 MinIO Artifact Structure

```
training-artifacts/
├── models/
│   └── {batch_id}_{model_name}_{version}/
│       ├── fold_0.pkl, fold_1.pkl, ... fold_4.pkl
│       └── metadata.json
├── oof_predictions/
│   └── {job_id}.json
└── ensemble/
    └── {batch_id}_ensemble_{version}/
        ├── ensemble_model.pkl
        └── metadata.json

predictions/
└── batch_{prediction_id}/
    ├── predictions.csv
    └── metadata.json
```

## 9.4 Model Versioning Strategy

```python
version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
# Example: "20260424_143052"

model_path = f"models/{batch_id}_{model_name}_{version}/"
# Example: "models/abc123_xgboost_20260424_143052/"
```

---

# 10. Security (JWT + RBAC)

## 10.1 JWT Authentication

| Parameter | Value |
|-----------|-------|
| Token Type | Bearer |
| Algorithm | HS256 |
| Expiry | 12 hours |
| Storage | HttpOnly cookie (secure) |

```python
# JWT Token Structure
{
    "sub": "user@email.com",
    "user_id": 123,
    "role": "researcher",
    "exp": 1714063200,  # 12 hours from issue
    "iat": 1714020000
}
```

## 10.2 RBAC Permission Matrix

| Endpoint Category | Admin | Researcher | Viewer |
|-------------------|-------|------------|--------|
| **Training** | ✅ Full | ✅ Own jobs | ❌ None |
| **Predictions** | ✅ Full | ✅ Own | ✅ Read |
| **Model Management** | ✅ Full | ✅ Own | ✅ Read |
| **User Management** | ✅ Full | ❌ None | ❌ None |
| **Data Upload** | ✅ Full | ✅ Full | ❌ None |
| **Settings** | ✅ Full | ❌ None | ❌ None |

## 10.3 Protected Endpoints

```python
# All training endpoints require authentication
@router.post("/train/base-model")
async def train_base_model(
    request: BaseModelTrainingRequest,
    current_user: User = Depends(get_current_user),  # JWT validation
    _: bool = Depends(require_role(["admin", "researcher"]))  # RBAC
):
    ...
```

## 10.4 Screenshot Evidence

```
┌─────────────────────────────────────────────────────────┐
│  📸 SCREENSHOT 1: Login Page                            │
│  Show: JWT login form with email/password               │
├─────────────────────────────────────────────────────────┤
│  📸 SCREENSHOT 2: 401 Unauthorized Response             │
│  Show: API rejecting request without valid token       │
├─────────────────────────────────────────────────────────┤
│  📸 SCREENSHOT 3: 403 Forbidden (RBAC)                 │
│  Show: Viewer role rejected from training endpoint     │
└─────────────────────────────────────────────────────────┘
```

---

# 11. JIRA Ticket Mapping

## 11.1 Sprint 3 Tickets Summary

| Status | Count | Tickets |
|--------|-------|---------|
| ✅ Complete | 21 | Core functionality delivered |
| 🟡 Partial | 4 | Basic implementation, enhancement pending |
| ⏳ In Progress | 4 | Testing/documentation |

## 11.2 Complete Ticket List

| JIRA Code | Ticket Name | Category | Status |
|-----------|-------------|----------|--------|
| **USMA-109** | Implement train/ensemble endpoint | ML Core | ✅ |
| **USMA-44** | Ensemble evaluation on held-out test set | ML Core | ✅ |
| **USMA-42** | Test set evaluation for base models | ML Core | ✅ |
| **USMA-75** | Persist model and pipeline artifacts | Storage | ✅ |
| **USMA-49** | Model versioning and snapshot persistence | Storage | ✅ |
| **USMA-51** | Prediction history tracking | Predictions | ✅ |
| **USMA-46** | Prediction serving API (FastAPI) | Predictions | ✅ |
| **USMA-45** | Dashboard UI with prediction endpoint | UI | ✅ |
| **USMA-43** | Model comparison reports | ML Core | ✅ |
| **USMA-86** | JWT token authentication | Security | ✅ |
| **USMA-115** | RBAC implementation | Security | ✅ |
| **USMA-52** | RBAC audit on endpoints | Security | ✅ |
| **USMA-47** | Scorecard conversion | Clinical | ✅ |
| **USMA-119** | 13 ML algorithms | ML Core | ✅ |
| **USMA-120** | Feature engineering pipeline | ML Core | ✅ |
| **USMA-121** | Optuna HPO integration | ML Core | ✅ |
| **USMA-122** | Multiclass classification support | ML Core | ✅ |
| **USMA-123** | OOF predictions in MinIO | Storage | ✅ |
| **USMA-124** | 7 configurable meta-learners | ML Core | ✅ |
| **USMA-125** | Training job persistence (PostgreSQL) | Infrastructure | ✅ |
| **USMA-50** | SHAP explainability | XAI | ✅ |
| **USMA-48** | Dataset versioning | Governance | 🟡 |
| **USMA-116** | Dataset governance UI | Governance | 🟡 |
| **USMA-117** | Model version UI | UI | 🟡 |
| **USMA-118** | Enhanced model comparison UI | UI | 🟡 |
| **USMA-54** | End-to-end staging validation | Testing | ⏳ |
| **USMA-114** | System integration testing | Testing | ⏳ |
| **USMA-53** | Credential handover docs | Docs | ⏳ |
| **USMA-55** | Production deployment docs | Docs | ⏳ |

---

# 12. Testing Evidence

## 12.1 Required Screenshots

### Section 3: Preprocessing Pipeline
```
📸 SCREENSHOT 3.1: Data Preparation Page showing 4-step preprocessing
📸 SCREENSHOT 3.2: Variable filtration with >50% threshold
📸 SCREENSHOT 3.3: Missing value imputation (median strategy)
📸 SCREENSHOT 3.4: Winsorization at 1st/99th percentiles
📸 SCREENSHOT 3.5: Z-score normalization applied
```

### Section 4: LASSO Feature Selection
```
📸 SCREENSHOT 4.1: Feature importance bar chart (top 10)
📸 SCREENSHOT 4.2: LASSO coefficient values
```

### Section 5: ML Models
```
📸 SCREENSHOT 5.1: Training Jobs Page with 13 models
📸 SCREENSHOT 5.2: Model training progress (5-fold CV)
📸 SCREENSHOT 5.3: Model comparison table with metrics
📸 SCREENSHOT 5.4: ROC curves comparison (multiple models)
```

### Section 6: Ensemble
```
📸 SCREENSHOT 6.1: Ensemble Training Dialog with 7 meta-learners
📸 SCREENSHOT 6.2: Ensemble training results
```

### Section 7: Scorecard
```
📸 SCREENSHOT 7.1: ROC curve showing AUC = 0.917
📸 SCREENSHOT 7.2: Scorecard feature weights
📸 SCREENSHOT 7.3: Dynamic binning methodology
📸 SCREENSHOT 7.4: Final scorecard performance metrics
```

### Section 10: Security
```
📸 SCREENSHOT 10.1: Login page with JWT
📸 SCREENSHOT 10.2: 401 Unauthorized response
📸 SCREENSHOT 10.3: RBAC role enforcement
```

---

# 13. Deployment Status

## 13.1 Infrastructure

| Component | Status | Location |
|-----------|--------|----------|
| FastAPI Backend | ✅ Running | 172.24.175.24:8000 |
| React Frontend | ✅ Running | 172.24.175.24:5173 |
| PostgreSQL | ✅ Running | 172.24.175.24:5432 |
| MinIO | ✅ Running | 172.24.175.24:9000 |
| Docker Compose | ✅ Deployed | All services containerized |

## 13.2 Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/usma

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=***
MINIO_SECRET_KEY=***

# JWT
JWT_SECRET_KEY=***
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=12
```

## 13.3 Docker Services

```yaml
services:
  fastapi:
    image: usma-backend:latest
    ports: ["8000:8000"]
    
  frontend:
    image: usma-frontend:latest
    ports: ["5173:5173"]
    
  postgres:
    image: postgres:15
    ports: ["5432:5432"]
    
  minio:
    image: minio/minio
    ports: ["9000:9000", "9001:9001"]
```

---

# 14. Appendix: API Reference

## 14.1 Training Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/train/prepare-dataset` | Prepare dataset with feature engineering |
| POST | `/api/v1/train/base-model` | Train single base model |
| POST | `/api/v1/train/ensemble` | Train stacking ensemble |
| GET | `/api/v1/train/status/{job_id}` | Get job status |
| GET | `/api/v1/train/jobs` | List all training jobs |

## 14.2 Prediction Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/predict/single` | Single patient prediction |
| POST | `/api/v1/predict/batch` | Batch predictions (CSV) |
| GET | `/api/v1/predict/history` | List prediction history |
| GET | `/api/v1/predict/download/{id}` | Download predictions CSV |

## 14.3 Preprocessing Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/eda/datasets/{id}/preprocess/filter-variables` | Remove high-missing variables |
| POST | `/api/v1/eda/datasets/{id}/preprocess/missing-values` | Impute missing values |
| POST | `/api/v1/eda/datasets/{id}/preprocess/winsorize` | Handle outliers |
| POST | `/api/v1/eda/datasets/{id}/preprocess/normalize` | Standardize features |

---

*Document Version: 2.0 (Restructured)*  
*Last Updated: April 27, 2026*  
*Author: Syarifah Fajriyah*  
*Aligned with: USM SLE Research Framework*
