# ML Training Pipeline - Implementation Summary & Testing Guide

**Date:** April 7, 2026  
**Project:** USM Autoimmune ML Platform  
**Phase:** Layers 6-8 (ML Training & Evaluation)

---

## 🎯 What We've Built

### 1. Sprint Ticket Breakdown
**File:** `SPRINT_TICKETS_ML_TRAINING.md`

Complete breakdown of 24 sprint tickets covering:
- Dataset preparation & feature engineering (Layer 6)
- 10 base model implementations (Layer 7)
- Stacking ensemble meta-learner (Layer 7.5)
- Comprehensive evaluation metrics (Layer 8)
- API endpoints and infrastructure

**Total:** 85 story points, estimated 4-6 weeks

---

### 2. Training Module Structure

```
app/ml/training/
├── __init__.py                 # Module initialization
├── dataset_generator.py        # Layer 6: Dataset generation & feature engineering
├── feature_selection.py        # Layer 6: LASSO feature selection
├── base_models.py              # Layer 7: 10 base model trainers
├── ensemble.py                 # Layer 7.5: Stacking ensemble
└── evaluation.py               # Layer 8: Metrics & visualization
```

#### Key Components

**DatasetGenerator** (`dataset_generator.py`)
- Extracts features from `fact_clinical_events` and dimension tables
- Engineers temporal, longitudinal, and calculated features
- Stratified train/test split (65/35)
- Returns feature matrix ready for training

**LassoFeatureSelector** (`feature_selection.py`)
- Uses LassoCV with 5-fold cross-validation
- Reduces ~100 features to 30-50 most important
- Exports feature importance report for clinical review

**BaseModelTrainer** (`base_models.py`)
- Implements 10 algorithms with Optuna hyperparameter tuning
- Generates out-of-fold (OOF) predictions for stacking
- Currently implemented:
  - ✅ XGBoost
  - ✅ LightGBM  
  - ✅ CatBoost
  - 🔄 Random Forest (TODO)
  - 🔄 AdaBoost (TODO)
  - 🔄 SVM (TODO)
  - 🔄 MLP (TODO)
  - 🔄 KNN (TODO)
  - 🔄 Decision Tree (TODO)
  - 🔄 Logistic Regression (TODO)

**StackingEnsemble** (`ensemble.py`)
- Meta-learner using Logistic Regression
- Trains on OOF predictions from base models
- Learns which models to trust
- Expected AUC: 0.85-0.95

**ModelEvaluator** (`evaluation.py`)
- AUC-ROC, Precision, Recall, F1, Specificity
- ROC curves, PR curves, confusion matrices
- Calibration metrics (Brier score, reliability diagrams)
- Model comparison tables

---

### 3. API Endpoints

**Base URL:** `http://100.106.132.15:8000/api/v1/ml`

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/train/prepare-dataset` | POST | Generate training dataset | ✅ Ready to test |
| `/train/feature-selection` | POST | Run LASSO selection | ✅ Ready to test |
| `/train/base-model` | POST | Train individual model | ✅ Ready to test |
| `/train/ensemble` | POST | Train stacking ensemble | 🔄 TODO |
| `/train/full-pipeline` | POST | Run end-to-end pipeline | 🔄 TODO |
| `/train/status/{job_id}` | GET | Check training job status | ✅ Ready to test |
| `/models/list` | GET | List all trained models | 🔄 TODO |
| `/evaluate/{model_id}` | GET | Get model metrics | 🔄 TODO |
| `/evaluate/compare` | GET | Compare multiple models | 🔄 TODO |

---

## 🧪 Testing Guide

### Prerequisites

1. **Update dependencies on server**
```bash
ssh shaggy@100.106.132.15
cd ~/usm-autoimmune-ml-platform
git pull  # Get latest code
pip install -r requirements.txt  # Install new ML packages
```

Newly added packages:
- `catboost==1.2.2`
- `lightgbm==4.1.0`
- `optuna==3.5.0`
- `shap==0.44.0`
- `mlflow==2.9.2`
- `matplotlib==3.8.2`
- `seaborn==0.13.0`

2. **Restart FastAPI service**
```bash
docker compose restart fastapi
# OR if running directly:
# pkill -f "uvicorn app.main:app"
# uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. **Get authentication token**
```bash
curl -X POST http://100.106.132.15:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_email@example.com&password=your_password"
```

Save the returned `access_token`.

---

### Test 1: Dataset Generation

**Request:**
```bash
curl -X POST "http://100.106.132.15:8000/api/v1/ml/train/prepare-dataset" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "target_column": "diagnosis_category",
    "min_events_per_patient": 2,
    "test_size": 0.35,
    "random_state": 42
  }'
```

**Expected Response:**
```json
{
  "job_id": "abc123-def456-...",
  "status": "queued",
  "message": "Dataset generation job queued...",
  "generated_at": "2026-04-07T12:34:56.789Z"
}
```

**Check Job Status:**
```bash
curl -X GET "http://100.106.132.15:8000/api/v1/ml/train/status/abc123-def456-..." \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected Result:**
- `status`: "running" → "completed"
- `result`: Contains dataset metadata (n_samples, n_features, class distribution)

---

### Test 2: Feature Selection

**Request:**
```bash
curl -X POST "http://100.106.132.15:8000/api/v1/ml/train/feature-selection" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "abc123-def456-...",
    "alphas": [0.0001, 0.001, 0.01, 0.1, 1.0],
    "cv_folds": 5
  }'
```

**Expected Response:**
```json
{
  "job_id": "xyz789-...",
  "status": "queued"
}
```

---

### Test 3: Train XGBoost Model

**Request:**
```bash
curl -X POST "http://100.106.132.15:8000/api/v1/ml/train/base-model" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "xgboost",
    "dataset_id": "abc123-def456-...",
    "n_trials": 50,
    "cv_folds": 5,
    "use_selected_features": true
  }'
```

**Expected Response:**
```json
{
  "job_id": "model-job-123...",
  "status": "queued",
  "model_name": "xgboost"
}
```

**Monitor Progress:**
```bash
# Check every 30 seconds
watch -n 30 'curl -X GET "http://100.106.132.15:8000/api/v1/ml/train/status/model-job-123..." \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"'
```

**Expected Training Time:**
- XGBoost with 50 trials, 5-fold CV: ~5-10 minutes on GPU
- Final status: `"completed"`
- Result should contain `oof_auc`, `cv_auc`, `best_params`

---

### Test 4: Train LightGBM

```bash
curl -X POST "http://100.106.132.15:8000/api/v1/ml/train/base-model" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "lightgbm",
    "dataset_id": "abc123-def456-...",
    "n_trials": 50,
    "cv_folds": 5
  }'
```

---

### Test 5: Train CatBoost

```bash
curl -X POST "http://100.106.132.15:8000/api/v1/ml/train/base-model" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "catboost",
    "dataset_id": "abc123-def456-...",
    "n_trials": 50,
    "cv_folds": 5
  }'
```

---

## 📊 Expected Results

### Minimum Viable Success Criteria

✅ **Dataset Generation**
- Successfully extracts features from database
- Generates train/test split
- Returns metadata with feature names and class distribution

✅ **Feature Selection**
- LASSO runs without errors
- Reduces feature count by 40-70%
- Returns selected feature list

✅ **Base Model Training**
- XGBoost, LightGBM, CatBoost train successfully
- OOF AUC ≥ 0.70 (baseline for clinical data)
- Best hyperparameters logged
- Training time < 15 minutes per model

### Performance Benchmarks

| Metric | Target | Excellent |
|--------|--------|-----------|
| XGBoost OOF AUC | ≥ 0.75 | ≥ 0.85 |
| LightGBM OOF AUC | ≥ 0.75 | ≥ 0.85 |
| CatBoost OOF AUC | ≥ 0.75 | ≥ 0.85 |
| Ensemble AUC (future) | ≥ 0.80 | ≥ 0.90 |

---

## 🚧 Known Limitations (Current Phase)

### Implemented ✅
- Dataset generation API endpoint
- Feature selection API endpoint
- Base model training API (XGBoost, LightGBM, CatBoost)
- Job status tracking
- Background task execution

### TODO 🔄
1. **Dataset Generator:** Currently uses placeholder data — needs to be connected to actual `fact_clinical_events` table
2. **Remaining Models:** SVM, MLP, KNN, Random Forest, AdaBoost, Decision Tree, Logistic Regression
3. **Ensemble Training:** Meta-learner endpoint not fully implemented
4. **Model Persistence:** Models not yet saved to MinIO (currently in memory)
5. **Evaluation Endpoints:** Metrics retrieval endpoints not implemented
6. **Database Integration:** Training jobs not persisted to database (in-memory only)

---

## 🔧 Troubleshooting

### Error: "Module 'catboost' not found"
**Solution:**
```bash
ssh shaggy@100.106.132.15
cd ~/usm-autoimmune-ml-platform
pip install catboost lightgbm optuna shap matplotlib seaborn
docker compose restart fastapi
```

### Error: "CUDA out of memory"
**Solution:**
- Reduce `n_trials` from 100 to 50
- Reduce `cv_folds` from 5 to 3
- Train models sequentially, not in parallel

### Error: "Dataset job still running after 10 minutes"
**Check logs:**
```bash
docker compose logs fastapi --tail 100
```

Look for:
- Database connection errors
- SQL query errors
- Feature engineering errors

### Job Status Never Completes
**Cause:** Background task failed without updating status  
**Solution:**
- Check FastAPI logs
- Verify database connectivity
- Add more logging to background task functions

---

## 📝 Next Steps

### Immediate (Week 1)
1. ✅ Test dataset generation endpoint
2. ✅ Test feature selection endpoint
3. ✅ Test XGBoost training
4. ✅ Test LightGBM training
5. ✅ Test CatBoost training

### Short-term (Week 2-3)
6. Implement remaining 7 base models
7. Connect dataset generator to real database tables
8. Implement model persistence to MinIO
9. Test full training pipeline with real data
10. Implement ensemble training endpoint

### Medium-term (Week 4-6)
11. Implement evaluation endpoints
12. Add SHAP interpretability
13. Create model comparison visualizations
14. Integrate with frontend UI
15. Add training job persistence to database

---

## 🎓 Implementation Reference

### For Each New Base Model

**Template** (e.g., Random Forest):

1. **Add method to `base_models.py`:**
```python
def train_random_forest(self, X_train, y_train, n_trials=100):
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 100, 500),
            'max_depth': trial.suggest_int('max_depth', 5, 15),
            # ... more params
        }
        model = RandomForestClassifier(**params)
        score = cross_val_score(model, X_train, y_train, cv=self.skf, scoring='roc_auc').mean()
        return score
    
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials)
    
    # Train with CV and return OOF predictions
    oof_preds, fold_models = self._train_with_cv(
        X_train, y_train,
        model_class=RandomForestClassifier,
        params=study.best_params
    )
    
    return {
        'model_name': 'random_forest',
        'fold_models': fold_models,
        'oof_predictions': oof_preds,
        'oof_auc': self._calculate_auc(y_train, oof_preds),
        'best_params': study.best_params
    }
```

2. **Update `training.py` background task:**
```python
async def run_base_model_training(job_id, params, db):
    # ... existing code ...
    
    if model_name == 'random_forest':
        result = trainer.train_random_forest(X_train, y_train, n_trials=n_trials)
```

3. **Test via API:**
```bash
curl -X POST ".../train/base-model" \
  -d '{"model_name": "random_forest", ...}'
```

---

## 📚 References

- **ML Algorithm Guide:** See the 11-algorithm guide you provided (XGBoost, LightGBM, CatBoost, etc.)
- **Sprint Tickets:** `SPRINT_TICKETS_ML_TRAINING.md`
- **Architecture Diagram:** Your Layer 1-8 architecture image

---

## ✅ Ready to Test

**Current Status:** Infrastructure complete, ready for endpoint testing

**Next Action:** Test dataset generation endpoint on your GPU server

Run this command to get started:
```bash
ssh shaggy@100.106.132.15
cd ~/usm-autoimmune-ml-platform
git pull
pip install -r requirements.txt
docker compose restart fastapi

# Then test the health endpoint
curl http://100.106.132.15:8000/health

# Test training endpoint
curl -X POST http://100.106.132.15:8000/api/v1/ml/train/prepare-dataset \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target_column": "diagnosis_category", "test_size": 0.35, "random_state": 42}'
```

---

**Created by:** GitHub Copilot  
**Date:** April 7, 2026  
**For:** USM Autoimmune ML Platform - Sprint Planning & Implementation
