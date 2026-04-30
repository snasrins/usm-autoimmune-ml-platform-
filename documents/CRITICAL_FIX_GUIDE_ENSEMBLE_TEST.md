# Pipeline Review - Technical Fix Guide

## Status Summary

✅ **Working**: Dataset generation, feature engineering, LASSO, base model training with test evaluation
⚠️ **Partially Working**: Ensemble training (OOF only, no test evaluation)
❌ **Missing**: Full pipeline orchestration, model persistence, comprehensive evaluation

---

## Critical Issue #1: Ensemble Test Evaluation

### Problem
Ensemble is trained only on OOF predictions. Cannot evaluate on held-out test set.

### Root Cause
- `run_ensemble_training()` receives only base model OOF predictions
- Test subset predictions not collected from base models  
- No mechanism to pass y_test to ensemble for evaluation

### Fix Required (Detailed Technical Steps)

#### Step 1: Modify base model result storage to include test predictions

**Current** (in `run_base_model_training()`):
```python
result = {
    'model_name': model_name,
    'oof_predictions': oof_preds,  # array of shape (n_train,)
    'test_auc': test_auc,
    'test_precision': test_precision,
    # ... other test metrics
}
```

**Fix**: Add test predictions array
```python
result = {
    'model_name': model_name,
    'oof_predictions': oof_preds,  # shape (n_train,)
    'test_predictions': test_proba,  # ⬅️ ADD THIS - shape (n_test,)
    'test_auc': test_auc,
    'test_precision': test_precision,
    # ... other test metrics
}
```

**Where**: Line ~210 in `app/api/endpoints/training.py`
**Changes Required**: Update the result dict after line 206

---

#### Step 2: Modify ensemble training to collect test predictions

**Current** (in `run_ensemble_training()`, line ~220-235):
```python
oof_predictions = {}
for bm_job_id in base_model_jobs:
    bm_job = training_jobs[bm_job_id]
    bm_result = bm_job.get('result', {})
    model_name = bm_result.get('model_name')
    oof_preds = bm_result.get('oof_predictions')
    
    oof_predictions[model_name] = np.array(oof_preds)
```

**Fix**: Collect both OOF and test predictions
```python
oof_predictions = {}
test_predictions = {}  # ⬅️ ADD THIS

for bm_job_id in base_model_jobs:
    bm_job = training_jobs[bm_job_id]
    bm_result = bm_job.get('result', {})
    model_name = bm_result.get('model_name')
    oof_preds = bm_result.get('oof_predictions')
    test_preds = bm_result.get('test_predictions')  # ⬅️ ADD THIS
    
    oof_predictions[model_name] = np.array(oof_preds)
    test_predictions[model_name] = np.array(test_preds)  # ⬅️ ADD THIS
```

---

#### Step 3: Get y_test from dataset job

**Current** (line ~240):
```python
dataset_job = training_jobs[dataset_id]
dataset_result = dataset_job['result']
y_train = np.array(dataset_result['y_train'])
# Missing y_test!
```

**Fix**: Also retrieve y_test
```python
dataset_job = training_jobs[dataset_id]
dataset_result = dataset_job['result']
y_train = np.array(dataset_result['y_train'])
y_test = np.array(dataset_result['y_test'])  # ⬅️ ADD THIS
```

---

#### Step 4: Evaluate ensemble on test data

**Current** (line ~270):
```python
# Train ensemble
ensemble = StackingEnsemble()
ensemble.fit(oof_predictions, y_train)

# Get results
meta_weights = ensemble.get_meta_weights()
ensemble_oof_auc = ensemble._calculate_auc(y_train, ensemble.predict_proba(oof_predictions))

result = {
    'ensemble_oof_auc': ensemble_oof_auc,
    'meta_weights': meta_weights,
    'base_models_included': list(oof_predictions.keys()),
    'calibration_method': ensemble.calibration_method,
    'is_calibrated': ensemble.is_calibrated
}
```

**Fix**: Add test evaluation
```python
# Train ensemble
ensemble = StackingEnsemble()
ensemble.fit(oof_predictions, y_train)

# Get results
meta_weights = ensemble.get_meta_weights()
ensemble_oof_auc = ensemble._calculate_auc(y_train, ensemble.predict_proba(oof_predictions))

# ⬅️ ADD THIS: Test evaluation
ensemble_test_proba = ensemble.predict_proba(test_predictions)
ensemble_test_auc = ensemble._calculate_auc(y_test, ensemble_test_proba)

ensemble_test_pred = (ensemble_test_proba >= 0.5).astype(int)
from sklearn.metrics import precision_score, recall_score, f1_score, brier_score_loss
ensemble_test_precision = precision_score(y_test, ensemble_test_pred, zero_division=0)
ensemble_test_recall = recall_score(y_test, ensemble_test_pred, zero_division=0)
ensemble_test_f1 = f1_score(y_test, ensemble_test_pred, zero_division=0)
ensemble_test_brier = brier_score_loss(y_test, ensemble_test_proba)

result = {
    'ensemble_oof_auc': ensemble_oof_auc,
    'ensemble_test_auc': ensemble_test_auc,  # ⬅️ ADD
    'ensemble_test_precision': ensemble_test_precision,  # ⬅️ ADD
    'ensemble_test_recall': ensemble_test_recall,  # ⬅️ ADD
    'ensemble_test_f1': ensemble_test_f1,  # ⬅️ ADD
    'ensemble_test_brier_score': ensemble_test_brier,  # ⬅️ ADD
    'meta_weights': meta_weights,
    'base_models_included': list(oof_predictions.keys()),
    'calibration_method': ensemble.calibration_method,
    'is_calibrated': ensemble.is_calibrated
}

logger.info(f"Ensemble Test Results:")
logger.info(f"  Test AUC: {ensemble_test_auc:.4f}")
logger.info(f"  Test F1: {ensemble_test_f1:.4f}")
logger.info(f"  Test Brier Score: {ensemble_test_brier:.4f}")
```

**Where**: Line ~260-280 in `app/api/endpoints/training.py`

---

### Complete Fixed Function

Here's the full corrected `run_ensemble_training()`:

```python
async def run_ensemble_training(job_id: str, params: dict, db: Session):
    """Background task to train stacking ensemble WITH TEST EVALUATION"""
    try:
        update_job_status(job_id, TrainingStatus.RUNNING, started_at=datetime.utcnow())
        
        from app.ml.training.ensemble import StackingEnsemble
        import numpy as np
        
        base_model_jobs = params['base_model_jobs']
        dataset_id = params['dataset_id']
        
        logger.info(f"Training ensemble with {len(base_model_jobs)} base models from dataset {dataset_id}")
        
        # Validate all base model jobs are completed
        oof_predictions = {}
        test_predictions = {}  # ✅ NEW
        
        for bm_job_id in base_model_jobs:
            if bm_job_id not in training_jobs:
                raise ValueError(f"Base model job {bm_job_id} not found")
            
            bm_job = training_jobs[bm_job_id]
            if bm_job['status'] != TrainingStatus.COMPLETED:
                raise ValueError(f"Base model job {bm_job_id} not completed (status: {bm_job['status']})")
            
            bm_result = bm_job.get('result', {})
            model_name = bm_result.get('model_name', f'model_{bm_job_id}')
            oof_preds = bm_result.get('oof_predictions')
            test_preds = bm_result.get('test_predictions')  # ✅ NEW
            
            if oof_preds is None:
                raise ValueError(f"No OOF predictions found in base model job {bm_job_id}")
            
            if test_preds is None:  # ✅ NEW - Validate test predictions exist
                raise ValueError(f"No test predictions found in base model job {bm_job_id}")
            
            oof_predictions[model_name] = np.array(oof_preds)
            test_predictions[model_name] = np.array(test_preds)  # ✅ NEW
        
        # Get y_train and y_test from dataset job
        if dataset_id not in training_jobs:
            raise ValueError(f"Dataset job {dataset_id} not found")
        
        dataset_job = training_jobs[dataset_id]
        if dataset_job['status'] != TrainingStatus.COMPLETED:
            raise ValueError(f"Dataset job {dataset_id} not completed")
        
        dataset_result = dataset_job['result']
        y_train = np.array(dataset_result['y_train'])
        y_test = np.array(dataset_result['y_test'])  # ✅ NEW
        
        logger.info(f"OOF matrix shape: {list(oof_predictions.values())[0].shape}")
        logger.info(f"Test matrix shape: {list(test_predictions.values())[0].shape}")  # ✅ NEW
        logger.info(f"Target train shape: {y_train.shape}")
        logger.info(f"Target test shape: {y_test.shape}")  # ✅ NEW
        
        # Train ensemble
        ensemble = StackingEnsemble()
        ensemble.fit(oof_predictions, y_train)
        
        # Get OOF results
        meta_weights = ensemble.get_meta_weights()
        ensemble_oof_auc = ensemble._calculate_auc(y_train, ensemble.predict_proba(oof_predictions))
        
        # ✅ NEW: Test evaluation
        ensemble_test_proba = ensemble.predict_proba(test_predictions)
        ensemble_test_auc = ensemble._calculate_auc(y_test, ensemble_test_proba)
        
        ensemble_test_pred = (ensemble_test_proba >= 0.5).astype(int)
        from sklearn.metrics import precision_score, recall_score, f1_score, brier_score_loss
        ensemble_test_precision = precision_score(y_test, ensemble_test_pred, zero_division=0)
        ensemble_test_recall = recall_score(y_test, ensemble_test_pred, zero_division=0)
        ensemble_test_f1 = f1_score(y_test, ensemble_test_pred, zero_division=0)
        ensemble_test_brier = brier_score_loss(y_test, ensemble_test_proba)
        
        result = {
            'ensemble_oof_auc': ensemble_oof_auc,
            # ✅ NEW: Test metrics
            'ensemble_test_auc': float(ensemble_test_auc),
            'ensemble_test_precision': float(ensemble_test_precision),
            'ensemble_test_recall': float(ensemble_test_recall),
            'ensemble_test_f1': float(ensemble_test_f1),
            'ensemble_test_brier_score': float(ensemble_test_brier),
            'meta_weights': meta_weights,
            'base_models_included': list(oof_predictions.keys()),
            'calibration_method': ensemble.calibration_method,
            'is_calibrated': ensemble.is_calibrated
        }
        
        update_job_status(
            job_id,
            TrainingStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            result=result
        )
        
        logger.info(f"Ensemble training completed - OOF AUC: {ensemble_oof_auc:.4f}, Test AUC: {ensemble_test_auc:.4f}")
        logger.info(f"Ensemble Test Metrics - Precision: {ensemble_test_precision:.4f}, Recall: {ensemble_test_recall:.4f}, F1: {ensemble_test_f1:.4f}")
        
    except Exception as e:
        logger.error(f"Ensemble training job {job_id} failed: {e}", exc_info=True)
        update_job_status(
            job_id,
            TrainingStatus.FAILED,
            completed_at=datetime.utcnow(),
            error_message=str(e)
        )
```

---

## Implementation checklist for base model fix:

- [ ] Find line where `result = {...}` is created in `run_base_model_training()`
- [ ] Add `'test_predictions': test_proba,` to result dict
- [ ] Ensure test_proba variable exists and has shape (n_test,)
- [ ] Test with one model to verify

---

## Implementation checklist for ensemble fix:

- [ ] Add `test_predictions = {}` dict at start of `run_ensemble_training()`
- [ ] In loop, add line: `test_preds = bm_result.get('test_predictions')`  
- [ ] In loop, add validation: `if test_preds is None: raise ValueError(...)`
- [ ] In loop, add: `test_predictions[model_name] = np.array(test_preds)`
- [ ] After getting `y_train`, add: `y_test = np.array(dataset_result['y_test'])`
- [ ] After trained ensemble, add test evaluation block (see code above)
- [ ] Update result dict with new test metrics
- [ ] Add logging for test metrics
- [ ] Test with small dataset to verify works

---

## Validation

After implementing fix, test with:

```bash
# 1. Check base model result contains test predictions
curl -X GET http://localhost:8000/api/v1/train/status/[base_model_job_id]
# Should see: 'test_predictions' in result

# 2. Check ensemble result contains test metrics
curl -X GET http://localhost:8000/api/v1/train/status/[ensemble_job_id]
# Should see: 'ensemble_test_auc', 'ensemble_test_f1', etc. in result

# 3. Verify test AUC makes sense
# ensemble_test_auc should be reasonable (0.5-1.0 typically for medical data, often 0.7-0.9)
# ensemble_test_auc might be lower than oof_auc (normal due to holdout set)
```

---

## Estimated Implementation Time

- Code changes: 15 minutes
- Testing: 20 minutes
- Debugging: 15-30 minutes
- **Total: ~1 hour**

---

## Next Priority Issues

After ensemble test evaluation is complete:

### Issue #2: Full Pipeline Orchestration (6 hours)
Current: `train_full_pipeline()` returns "not implemented"
Need: Implement task dependency chain

### Issue #3: Model Persistence (8 hours)
Current: Models lost when server restarts
Need: Save to MinIO with versioning

### Issue #4: Evaluation Reports (6 hours)
Current: No way to compare models
Need: Comparison endpoint + report generation
