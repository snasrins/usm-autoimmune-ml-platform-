# ML Pipeline Review - April 16, 2026

## Pipeline Architecture Analysis

### ✅ WORKING Components

#### Layer 6: Dataset Generation
- **Status**: ✅ COMPLETE
- **Location**: `app/ml/training/dataset_generator.py`
- **Flow**:
  1. Validates data for ML training (flexible warnings)
  2. Extracts base features from FlexibleDatasetWide
  3. Engineers features dynamically via FeatureEngineeringPipeline
  4. Applies LASSO feature selection (configurable)
  5. Performs stratified train/test split (80/20 default)
  6. Creates scaled versions for linear models (StandardScaler, MinMaxScaler, RobustScaler)
  7. Tracks metadata including class distribution, feature counts

- **Output Structure**:
```python
{
    'X_train': DataFrame (raw),
    'X_test': DataFrame (raw),
    'X_train_scaled': DataFrame (scaled),
    'X_test_scaled': DataFrame (scaled),
    'y_train': Series,
    'y_test': Series,
    'feature_names': List[str],
    'feature_pipeline': FeatureEngineeringPipeline,
    'metadata': Dict
}
```

#### Layer 7: Base Model Training
- **Status**: ✅ COMPLETE WITH TEST EVALUATION
- **Location**: `app/ml/training/base_models.py`
- **Models**: 10 algorithms with hyperparameter tuning via Optuna
  - Tree-based: XGBoost, LightGBM, CatBoost, Random Forest, AdaBoost, Decision Tree
  - Linear: SVM, MLP, KNN, Logistic Regression
  
- **Flow for Each Model**:
  1. Hyperparameter tuning with cross-validation (Optuna)
  2. Out-of-fold (OOF) training with stratified K-fold CV
  3. ✅ **Test evaluation** (newly added):
     - AUC, Precision, Recall, F1-score, Brier Score on held-out test set
     - Results stored in dictionary: `test_auc`, `test_precision`, `test_recall`, `test_f1`, `test_brier_score`
  4. Proper scaling handling for scaled-feature models (SVM, MLP, KNN, LogisticRegression)
  5. Scaler persistence for inference

- **Output Structure**:
```python
{
    'model_name': str,
    'fold_models': List[model],  # CV fold models
    'oof_predictions': np.ndarray,  # Shape: (n_train,)
    'oof_auc': float,
    'test_auc': float,  # ✅ NEW
    'test_precision': float,  # ✅ NEW
    'test_recall': float,  # ✅ NEW
    'test_f1': float,  # ✅ NEW
    'test_brier_score': float,  # ✅ NEW
    'best_params': Dict,
    'cv_auc': float,
    'scaler': object or None,  # For scaled-feature models
}
```

#### Layer 7.5: Stacking Ensemble
- **Status**: ✅ CORE COMPLETE, ❌ TEST EVALUATION MISSING
- **Location**: `app/ml/training/ensemble.py`
- **Features**:
  - Configurable meta-learner (7 options: LogReg, XGBoost, LightGBM, RF, MLP, Ridge, ElasticNet)
  - Out-of-fold stacking (prevents overfitting)
  - Probability calibration for clinical reliability (isotonic or sigmoid)
  - Meta-learner weight extraction for interpretability

- **Current Flow**:
  1. Collects OOF predictions from base models
  2. Builds OOF matrix: [n_samples, n_base_models]
  3. Trains meta-learner on OOF predictions
  4. Applies probability calibration
  5. ❌ **MISSING**: Test evaluation on held-out test set
  6. ❌ **MISSING**: Test predictions from base models

- **Output Structure**:
```python
{
    'ensemble_oof_auc': float,
    'meta_weights': Dict[str, float],
    'base_models_included': List[str],
    'calibration_method': str,
    'is_calibrated': bool,
    # ❌ MISSING: Test metrics (test_auc, test_precision, etc.)
}
```

#### Layer 8: API Endpoints
- **Status**: ✅ PARTIAL - Background task orchestration working
- **Location**: `app/api/endpoints/training.py`

**Working Endpoints**:
1. ✅ `/train/dataset` - Dataset generation with background task
2. ✅ `/train/base-model` - Individual base model training
3. ✅ `/train/ensemble` - Ensemble training from base model jobs
4. ✅ `/train/status/{job_id}` - Get job status
5. ✅ `List models`, `Get trained models`

**Non-functional/TODO Endpoints**:
1. ❌ `/train/full-pipeline` - Not implemented (placeholder returns "not yet implemented")
2. ❌ Model evaluation endpoint - Not implemented
3. ❌ Model comparison endpoint - Not implemented
4. ❌ Full metrics report - Not implemented
5. ❌ Model artifact persistence - Not implemented

---

## ⚠️ CRITICAL ISSUES IDENTIFIED

### Issue #1: Ensemble Test Evaluation Missing
**Severity**: HIGH
**Impact**: Cannot evaluate ensemble on test set; no test metrics for clinical validation

**Current State**:
- Ensemble is trained on OOF predictions only
- No test predictions collected from base models
- No mechanism to pass test predictions to ensemble
- Ensemble test_auc/test_metrics missing

**Root Cause**:
- `run_ensemble_training()` receives only `y_train` from dataset job
- Line 220-235 in training.py: Loads only y_train, not y_test or test predictions

**Solution Required**:
1. Modify `run_ensemble_training()` to accept test dataset info
2. Collect test predictions from each base model job
3. Build test prediction matrix for ensemble
4. Evaluate ensemble on test data (AUC, precision, recall, F1, Brier)
5. Return test metrics in ensemble result

---

### Issue #2: Test Data Not Passed Through Training Pipeline
**Severity**: HIGH
**Impact**: Base models cannot evaluate on test set during training

**Current State**:
- Dataset generator creates X_test, y_test ✅
- Base model training receives X_test, y_test ✅
- Base models compute test metrics ✅
- BUT: Base model results returned to training_jobs dictionary with test metrics ✅
- ✅ **Actually this is working now after our recent fix!**

**Status Update**: ✅ RESOLVED - Base models now evaluate on test set

---

### Issue #3: No Full Pipeline Orchestration
**Severity**: HIGH
**Impact**: Users cannot run end-to-end training in one request

**Current State**:
```python
async def train_full_pipeline(...):
    return FullPipelineTrainingResponse(
        message="Full pipeline training not yet implemented"
    )
```

**Required Implementation**:
```
1. Dataset Generation Job
   ↓
2. Base Model Training (parallel for all 10 models)
   ├─ Model 1 (dataset_job → output: oof_predictions + test_predictions)
   ├─ Model 2 (dataset_job → output: oof_predictions + test_predictions)
   ├─ ...
   ├─ Model 10 (dataset_job → output: oof_predictions + test_predictions)
   ↓
3. Ensemble Training (wait for all base models)
   ├─ Collect OOF predictions from all base models
   ├─ Collect test predictions from all base models ❌ MISSING
   ├─ Train meta-learner on OOF
   ├─ Evaluate on test data ❌ MISSING
   ↓
4. Model Evaluation & Comparison
   ├─ Evaluate each base model on test set ✅ NOW WORKING
   ├─ Evaluate ensemble on test set ❌ MISSING
   ├─ Compare all models side-by-side ❌ NOT IMPLEMENTED
   ↓
5. Save Artifacts
   ├─ Save all models to MinIO ❌ NOT IMPLEMENTED
   ├─ Save scalers to MinIO ❌ NOT IMPLEMENTED
   ├─ Save evaluation report to database ❌ NOT IMPLEMENTED
```

---

### Issue #4: No Model Persistence/Artifacts Management
**Severity**: HIGH
**Impact**: Cannot deploy models; no model versions/history

**Missing Components**:
1. MinIO integration for model artifact storage
2. Model serialization/deserialization
3. Model versioning system
4. Scaler persistence (critical for inference)
5. Feature pipeline persistence (for inference feature engineering)
6. Artifact metadata tracking

**Should Store**:
```
├── trained_models/{batch_id}/{model_name}/
│   ├── model.pkl (or .joblib)
│   ├── scaler.pkl
│   ├── metadata.json
│   ├── feature_pipeline.pkl
│   ├── test_predictions.npy
│   └── test_metrics.json
├── ensemble/{batch_id}/
│   ├── meta_learner.pkl
│   ├── calibrated_meta_learner.pkl
│   ├── meta_weights.json
│   ├── base_model_info.json
│   ├── test_predictions.npy
│   └── test_metrics.json
```

---

### Issue #5: No Comprehensive Evaluation/Reporting
**Severity**: MEDIUM
**Impact**: Users cannot see full results or compare models

**Missing Features**:
1. Individual model evaluation endpoint (returns all metrics for one model)
2. Model comparison endpoint (side-by-side metrics for all models + ensemble)
3. Full training report generation
4. Visualization data (confusion matrices, calibration curves, ROC curves)
5. Training history tracking (previous runs)
6. Model export/download functionality

---

## 🔄 Data Flow Analysis

### Current Flow (After test evaluation fix):
```
1. Dataset Generation
   INPUT: batch_id, target_column, test_size=0.2
   OUTPUT: 
      - training_jobs[dataset_job_id] = {
          'X_train': DataFrame,
          'X_test': DataFrame,  ✅
          'X_train_scaled': DataFrame,
          'X_test_scaled': DataFrame,
          'y_train': Series,
          'y_test': Series,  ✅
          'feature_names': List,
          'metadata': Dict
        }

2. Base Model Training (×10 models, parallel)
   INPUT: dataset_job_id, model_name, X_train, X_test, y_train, y_test
   OUTPUT:
      - training_jobs[bm_job_id] = {
          'model_name': str,
          'oof_predictions': np.ndarray,  ✅
          'oof_auc': float,
          'test_auc': float,  ✅ NEW
          'test_precision': float,  ✅ NEW
          'test_recall': float,  ✅ NEW
          'test_f1': float,  ✅ NEW
          'test_brier_score': float,  ✅ NEW
          'best_params': Dict,
        }

3. Ensemble Training
   INPUT: [base_model_job_1, base_model_job_2, ..., base_model_job_10], dataset_job_id
   MISSING INPUT: Test predictions from base models ❌
   OUTPUT:
      - training_jobs[ensemble_job_id] = {
          'ensemble_oof_auc': float,
          'meta_weights': Dict,
          'base_models_included': List,
          # ❌ MISSING: test_auc, test_metrics
        }

4. Evaluation Report (NOT IMPLEMENTED)
   INPUT: All job results
   OUTPUT: Comprehensive report with all metrics
```

---

## 📋 Implementation Checklist for Sprint 3 Completion

### Phase 1: Fix Ensemble Test Evaluation (CRITICAL - High Impact)
- [ ] Modify ensemble training to collect test predictions from base models
- [ ] Add test evaluation for ensemble (AUC, precision, recall, F1, Brier)
- [ ] Update ensemble result dictionary with test metrics
- [ ] Add ensemble test metrics to job status

**Effort**: 2-3 hours
**Priority**: CRITICAL
**Blocking**: Full pipeline, evaluation reports

### Phase 2: Implement Full Pipeline Orchestration (HIGH - Enables E2E workflows)
- [ ] Create `run_full_pipeline()` background task
- [ ] Implement task dependency chain (dataset → base models → ensemble → evaluation)
- [ ] Add progress tracking for multi-stage pipeline
- [ ] Handle cancellation/rollback for failed stages
- [ ] Return comprehensive pipeline result

**Effort**: 4-5 hours
**Priority**: HIGH
**Blocking**: User workflows

### Phase 3: Model Artifact Persistence (HIGH - Enables deployment)
- [ ] Set up MinIO integration
- [ ] Implement model serialization/deserialization
- [ ] Create artifact storage schema
- [ ] Save models, scalers, pipelines with metadata
- [ ] Implement model versioning

**Effort**: 5-6 hours
**Priority**: HIGH
**Blocking**: Production deployment

### Phase 4: Evaluation & Reporting (MEDIUM - Enables insights)
- [ ] Create model evaluation endpoint
- [ ] Create model comparison endpoint
- [ ] Implement training report generation
- [ ] Add visualization data endpoints
- [ ] Create training history tracking

**Effort**: 4-6 hours
**Priority**: MEDIUM
**Blocking**: User insights

---

## ✅ What's Working Well

1. **Data Quality First Approach**: Validation before training is excellent ✅
2. **Flexible Schema**: Dataset generator handles arbitrary columns ✅
3. **10 Base Models**: Comprehensive algorithm coverage ✅
4. **Hyperparameter Tuning**: Optuna integration solid ✅
5. **OOF Predictions**: Proper cross-validation framework ✅
6. **Feature Engineering Pipeline**: Reproducible transformations ✅
7. **Calibration**: Probability calibration for clinical reliability ✅
8. **Test Evaluation**: Now working for base models ✅
9. **Scalers**: Proper handling of scaled-feature models ✅
10. **Logging**: Comprehensive logging throughout ✅

---

## ⚠️ What Needs Attention

### Critical Issues (Blocking Production):
1. ❌ Ensemble test evaluation
2. ❌ Full pipeline orchestration
3. ❌ Model artifact persistence
4. ❌ No inference capability

### Important Issues (High Impact):
1. ❌ Comprehensive evaluation reports
2. ❌ Model comparison interface
3. ❌ Training history tracking
4. ❌ Model versioning

### Nice-to-Have (Technical Debt):
1. In-memory job storage → move to database
2. Trained model registry → move to database + MinIO
3. Error recovery/retry logic
4. Distributed training support
5. GPU optimization profile

---

## 🎯 Recommended Next Steps

1. **Immediate (Today)**: Fix ensemble test evaluation (Issue #1)
2. **Short-term (This week)**: Implement full pipeline orchestration (Issue #2, #3)
3. **Medium-term (Next sprint)**: Add artifact persistence (Issue #4)
4. **Long-term (Following sprint)**: Build comprehensive evaluation UI (Issue #5)

---

## Summary

**Overall Status**: 73% Complete

**Strengths**: Data pipeline, base model training, feature engineering all solid
**Gaps**: Ensemble evaluation, pipeline orchestration, artifact management
**Recommendation**: Fix critical issues (1 & 2) before proceeding to testing

The pipeline foundation is strong. The recent addition of test evaluation to all base models was essential. Now focus on:
1. Getting ensemble test metrics
2. Completing end-to-end orchestration
3. Enabling model persistence for deployment
