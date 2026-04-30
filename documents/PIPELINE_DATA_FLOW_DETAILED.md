# ML Pipeline Data Flow - Current Implementation (April 16, 2026)

## Complete End-to-End Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│                    LAYER 6: DATASET GENERATION (WORKING ✅)                         │
│                                                                                     │
│  Input: batch_id, target_column, test_size=0.2, random_state=42                  │
│                                                                                     │
│  ┌──────────────────────────────────────┐                                         │
│  │ 1. Data Validation                    │                                         │
│  │    - Check labeled/unlabeled records  │                                         │
│  │    - Verify min classes (≥2)          │                                         │
│  │    - Warnings (non-blocking)          │                                         │
│  └──────────────────────────────────────┘                                         │
│                    ↓                                                                │
│  ┌──────────────────────────────────────┐                                         │
│  │ 2. Feature Extraction                 │                                         │
│  │    - Demographics, labs, medications  │                                         │
│  │    - Longitudinal trends              │                                         │
│  │    - Temporal features                │                                         │
│  └──────────────────────────────────────┘                                         │
│                    ↓                                                                │
│  ┌──────────────────────────────────────┐                                         │
│  │ 3. LASSO Feature Selection            │                                         │
│  │    - Remove redundant features        │                                         │
│  │    - Configurable alpha               │                                         │
│  └──────────────────────────────────────┘                                         │
│                    ↓                                                                │
│  ┌──────────────────────────────────────┐                                         │
│  │ 4. Train/Test Split                   │                                         │
│  │    - Stratified split (default 80/20) │                                         │
│  │    - Random state for reproducibility │                                         │
│  └──────────────────────────────────────┘                                         │
│                    ↓                                                                │
│  ┌──────────────────────────────────────┐                                         │
│  │ 5. Feature Scaling (for linear models)│                                         │
│  │    - StandardScaler (default)         │                                         │
│  │    - MinMaxScaler or RobustScaler     │                                         │
│  │    - FIT on train data ONLY           │                                         │
│  └──────────────────────────────────────┘                                         │
│                                                                                     │
│  Output: X_train, X_test, X_train_scaled, X_test_scaled, y_train, y_test         │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                            ↓
                                  job_results[dataset_job] = {
                                      'X_train': DF,
                                      'X_test': DF ✅,
                                      'X_train_scaled': DF,
                                      'X_test_scaled': DF ✅,
                                      'y_train': Series,
                                      'y_test': Series ✅,
                                      'feature_names': [...]
                                  }
                                            ↓
        ┌───────────────────────────────────┴───────────────────────────────────┐
        │                                                                       │
        │ PARALLEL EXECUTION (10 BASE MODELS)                                  │
        │                                                                       │
        ├────────────┬────────────┬────────────┬────────────┬────────────┐      │
        │            │            │            │            │            │      │
        ↓            ↓            ↓            ↓            ↓            ↓      │
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  XGBoost     │ │  LightGBM    │ │  CatBoost    │ │ RandomForest │ │  AdaBoost    │
│ (Tree #1)    │ │ (Tree #2)    │ │ (Tree #3)    │ │ (Tree #4)    │ │ (Tree #5)    │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        │            │            │            │            │            │
        │     EACH MODEL EXECUTES:                           │            │
        │     ┌──────────────────────────────────────┐       │            │
        │     │ 1. Hyperparameter Tuning (Optuna)     │       │            │
        │     │ 2. CV Training (OOF predictions) ✅   │       │            │
        │     │ 3. Test Evaluation NEW ✅             │       │            │
        │     │    - AUC, Precision, Recall, F1, Brier │       │            │
        │     │ 4. Store Scaler (if needed)          │       │            │
        │     └──────────────────────────────────────┘       │            │
        │            │            │            │            │            │
        ↓            ↓            ↓            ↓            ↓            ↓      │
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Decision    │ │    SVM       │ │    MLP       │ │    KNN       │ │    LogisticReg
│   Tree       │ │ (Linear #1)  │ │ (Linear #2)  │ │ (Linear #3)  │ │ (Linear #4)
│ (Tree #6)    │ │ *Scaled ✅   │ │ *Scaled ✅   │ │ *Scaled ✅   │ │ *Scaled ✅
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        │            │            │            │            │            │      │
        │            │            │            │            │            │      │
        └────────────┴────────────┴────────────┴────────────┴────────────┘      │
                                            ↓
        All base models complete, each stores in job_results:
        {
            'model_name': str (e.g., 'xgboost'),
            'oof_predictions': array (n_train,),         ✅ Used by ensemble
            'oof_auc': float                              ✅ Training metric
            'test_auc': float,                   ✅ NEW  Used for comparison
            'test_precision': float,             ✅ NEW  Diagnostic metric
            'test_recall': float,                ✅ NEW  Diagnostic metric
            'test_f1': float,                    ✅ NEW  Diagnostic metric
            'test_brier_score': float,           ✅ NEW  Calibration metric
            'best_params': Dict,                          Hyperparameters
            'cv_auc': float,                              CV performance
            'scaler': object or None,                     For inference
        }
                                            ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│                    LAYER 7.5: ENSEMBLE TRAINING (PARTIALLY WORKING ⚠️)             │
│                                                                                     │
│  Input: [base_model_job_1, ..., base_model_job_10], dataset_job_id                │
│                                                                                     │
│  ┌──────────────────────────────────────────────────────────────────┐             │
│  │ STEP 1: Validate all base models completed                     │             │
│  │         ✅ Check all base_model_job status = COMPLETED         │             │
│  └──────────────────────────────────────────────────────────────────┘             │
│                             ↓                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐             │
│  │ STEP 2: Collect OOF predictions from base models               │             │
│  │         OOF Matrix = [n_train, 10] ✅ WORKING                   │             │
│  │         Column 0: XGBoost OOF                                   │             │
│  │         Column 1: LightGBM OOF                                  │             │
│  │         ...                                                     │             │
│  │         Column 9: LogisticRegression OOF                        │             │
│  └──────────────────────────────────────────────────────────────────┘             │
│                             ↓                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐             │
│  │ STEP 3: Train meta-learner on OOF matrix                       │             │
│  │         ✅ Logistic Regression (default), XGBoost, etc.        │             │
│  │         ✅ Extract meta-weights for interpretability           │             │
│  │         ✅ Calculate OOF AUC before calibration                │             │
│  └──────────────────────────────────────────────────────────────────┘             │
│                             ↓                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐             │
│  │ STEP 4: Probability Calibration (Isotonic/Sigmoid)            │             │
│  │         ✅ Fit on OOF predictions (no leakage)                 │             │
│  │         ✅ Calibrate ensemble probabilities                     │             │
│  │         ✅ Compare Brier scores before/after                   │             │
│  │         ✅ Track calibration applied                            │             │
│  └──────────────────────────────────────────────────────────────────┘             │
│                             ↓                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐             │
│  │ STEP 5: ❌ MISSING - Test Evaluation                           │             │
│  │         1. Need to collect test predictions from base models   │             │
│  │         2. Need to build test prediction matrix [n_test, 10]   │             │
│  │         3. Need to evaluate ensemble on test data              │             │
│  │         4. Need to calculate test AUC/prec/recall/F1/Brier    │             │
│  │         5. Need to return test metrics in result dict          │             │
│  └──────────────────────────────────────────────────────────────────┘             │
│                                                                                     │
│  Output: ❌ INCOMPLETE - Missing test metrics                                     │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│              LAYER 8: EVALUATION & REPORTING (NOT IMPLEMENTED ❌)                   │
│                                                                                     │
│  Input: All base model results + ensemble result                                  │
│                                                                                     │
│  ┌──────────────────────────────────────────────────────────────────┐             │
│  │ ❌ MISSING: Model Evaluation Endpoint                          │             │
│  │    - Get all metrics for single model                          │             │
│  │    - Get test predictions for visualization                    │             │
│  │    - Get feature importance (if available)                     │             │
│  └──────────────────────────────────────────────────────────────────┘             │
│                                                                                     │
│  ┌──────────────────────────────────────────────────────────────────┐             │
│  │ ❌ MISSING: Model Comparison Endpoint                          │             │
│  │    - Side-by-side metrics table                                │             │
│  │    - Rank models by test AUC                                   │             │
│  │    - Show test metrics for all 11 models (10 base + ensemble) │             │
│  │    - Show OOF vs Test comparison                               │             │
│  └──────────────────────────────────────────────────────────────────┘             │
│                                                                                     │
│  ┌──────────────────────────────────────────────────────────────────┐             │
│  │ ❌ MISSING: Comprehensive Report Generation                   │             │
│  │    - JSON export of all results                                │             │
│  │    - PDF report generation                                     │             │
│  │    - CSV export of metrics                                     │             │
│  └──────────────────────────────────────────────────────────────────┘             │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│        LAYER 9: MODEL PERSISTENCE & DEPLOYMENT (NOT IMPLEMENTED ❌)                 │
│                                                                                     │
│  ❌ MISSING: MinIO Integration                                                    │
│  ❌ MISSING: Model Serialization                                                  │
│  ❌ MISSING: Artifact Storage                                                     │
│  ❌ MISSING: Model Versioning                                                     │
│  ❌ MISSING: Inference Service                                                    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Critical Data Flow Issues

### Issue 1: Ensemble Test Evaluation Missing ⚠️ CRITICAL

**Current Flow** (Incomplete):
```
Base Model Job Results:
  ├─ model_name: str ✅
  ├─ oof_predictions: array ✅
  ├─ test_predictions: ❌ NOT COLLECTED
  └─ test_metrics: array ✅

Ensemble Receives:
  ├─ oof_predictions from base models ✅
  ├─ y_train from dataset job ✅
  ├─ test_predictions from base models ❌ MISSING
  ├─ y_test from dataset job ❌ MISSING
  └─ Can evaluate on OOF only ⚠️
```

**Required Fix**:
```
Base Model Job Results: (Update)
  ├─ model_name: str ✅
  ├─ oof_predictions: array ✅
  ├─ test_predictions: array ⬅️ ADD THIS
  └─ test_metrics: dict ✅

Update run_ensemble_training():
  1. Collect test_predictions from each base model job
  2. Get y_test from dataset job
  3. Build test_predictions matrix [n_test, 10]
  4. Evaluate ensemble on test data
  5. Calculate test AUC/precision/recall/F1/Brier
  6. Return in result: {
       'ensemble_oof_auc': float,
       'ensemble_test_auc': float,  ⬅️ ADD
       'ensemble_test_metrics': {...},  ⬅️ ADD
       'meta_weights': dict,
       'calibration_method': str,
       'is_calibrated': bool
     }
```

### Issue 2: No Full Pipeline Orchestration ⚠️ CRITICAL

**Current**:
```
train_full_pipeline() → NOT IMPLEMENTED
  → Returns message: "not yet implemented"
```

**Required**:
```
train_full_pipeline() should:
  1. Create dataset job (dataset_generator)
  2. Wait for dataset completion
  3. Create 10 parallel base model jobs (all depend on dataset_job)
  4. Wait for all base models to complete
  5. Create ensemble job (depends on all base_model_jobs)
  6. Wait for ensemble completion
  7. Create evaluation job (optional, depends on ensemble)
  8. Return comprehensive result with all metrics
```

### Issue 3: No Model Persistence ⚠️ HIGH

**Current**:
```
Trained models stored in-memory dict: training_jobs[job_id]
  - Lost when server restarts
  - Not available for inference
  - No versioning
  - No audit trail
```

**Required**:
```
Should save to MinIO:
  ├─ Base model artifacts:
  │  ├─ model_name.pkl
  │  ├─ scaler.pkl
  │  ├─ metadata.json
  │  ├─ test_predictions.npy
  │  └─ test_metrics.json
  ├─ Ensemble artifacts:
  │  ├─ meta_learner.pkl
  │  ├─ calibrated_meta_learner.pkl
  │  ├─ meta_weights.json
  │  ├─ test_predictions.npy
  │  └─ test_metrics.json
  └─ Training metadata:
     ├─ dataset_info.json
     ├─ feature_pipeline.pkl
     ├─ training_log.txt
     └─ evaluation_report.json
```

---

## Summary of Current Implementation Status

| Component | Status | Working | Issues |
|-----------|--------|---------|--------|
| Dataset Generation | 95% | ✅ | Minor: DB migration for history |
| Data Validation | 95% | ✅ | Minor: More validation rules |
| LASSO Selection | 90% | ✅ | Minor: Feature importance tracking |
| Feature Scaling | 100% | ✅ | None |
| Train/Test Split | 100% | ✅ | None |
| Base Model Training | 98% | ✅ | ✅ Test evaluation now added! |
| OOF Predictions | 100% | ✅ | None |
| Hyperparameter Tuning | 95% | ✅ | Minor: Better trial allocation |
| Ensemble Meta-Learning | 70% | ⚠️ | ❌ Missing test evaluation |
| Probability Calibration | 95% | ✅ | Minor: Calibration curve plots |
| Model Comparison | 0% | ❌ | Needs implementation |
| Evaluation Reports | 0% | ❌ | Needs implementation |
| Model Persistence | 0% | ❌ | Needs implementation |
| Full Orchestration | 0% | ❌ | Needs implementation |
| **Overall** | **~60%** | | **Critical issues: 2** |

---

## Next Steps to Complete Pipeline

1. **Fix Ensemble Test Evaluation** (4 hours)
   - Collect test predictions from base models
   - Evaluate ensemble on test data
   - Return test metrics

2. **Implement Full Pipeline** (6 hours)
   - Create orchestration logic
   - Handle task dependencies
   - Add progress tracking

3. **Add Artifact Persistence** (8 hours)
   - MinIO integration
   - Model serialization
   - Versioning system

4. **Create Evaluation UI** (10 hours)
   - Model comparison endpoint
   - Visualization data preparation
   - Report generation

**Total Estimated Effort**: 28 hours to complete pipeline
