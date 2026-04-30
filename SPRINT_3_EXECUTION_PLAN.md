# Sprint 3 Execution Plan - USM SLE Research Platform
## April 16 - May 14, 2026

---

## Research Context Mapping

### Your Research Foundation
**Paper**: "A Small-Data Machine Learning Framework with Interpretable Scorecards for SLE Disease Activity Prediction" (USM)

**Key Constraints** (Making Your Platform Reliable):
- Small dataset: 104 female SLE patients (not typical ML volume)
- SLEDAI-2000 binary target: Low (≤4) vs High (>4) disease activity
- 65% train / 35% test split (stratified)
- LASSO for feature reduction: Prevents overfitting on small data
- Logistic Regression + Scorecard for clinical interpretability
- Calibration critical: Clinical decisions depend on trustworthy probabilities

**Why This Matters for Malaysian Researchers**:
- Resource-constrained: Small datasets are realistic for many hospitals
- Interpretability-first: Clinicians must understand *why* model predicts High risk
- Robustness: LASSO + LR beats black-box models on small data
- Auditability: Every decision traceable to specific clinical features

---

## Phase 1: Complete Core ML Pipeline (Weeks 1-2)
### Goal: Working end-to-end ensemble with test evaluation

### Week 1: Data Processing & Base Models (Days 1-5)

#### Day 1-2: Complete LASSO Feature Selection ⚠️ CRITICAL
**Status**: You noted LASSO is incomplete

**What LASSO Must Do** (from research):
1. Take all X_train after initial preprocessing
2. Fit L1 penalty to identify most predictive features
3. Remove features with coefficient → 0
4. Return: selected_features list, selected X_train, selected X_test
5. Log removed features and alpha value

**Current Code Location**: `app/ml/training/dataset_generator.py` → `_lasso_feature_selection()`

**Missing Pieces to Complete**:
```python
# Should return:
# 1. X_selected (DataFrame with selected features only)
# 2. selected_features (list of feature names that survived LASSO)
# 3. Alpha value used (should be tunable)

# Example from research:
# - Input: 149 features
# - After LASSO: ~20-30 features (CRP_high, C4, Urine protein, C3, ACR, etc.)
# - This is normal and expected for small data!
```

**Action Items**:
- [ ] Verify LASSO alpha parameter is tunable (research likely used different alphas)
- [ ] Ensure feature selection happens BEFORE train/test split (prevent data leakage)
- [ ] Log removed vs selected features for interpretability
- [ ] Test: Run with test data, verify selected feature count reasonable

**Estimated Time**: 2 hours

---

#### Day 2-3: Verify Base Model Test Evaluation ✅ DONE
**Status**: You just completed this!

**What's Now In Place**:
- ✅ All 10 base models evaluate on held-out test set
- ✅ Test metrics: AUC, precision, recall, F1, Brier score
- ✅ Proper scaling for linear models (SVM, MLP, KNN, LogReg)
- ✅ OOF predictions for ensemble

**What's Next**:
- [ ] Verify test metrics make clinical sense (AUC typically 0.7-0.9 for medical data)
- [ ] Check Brier scores (< 0.25 is good, > 0.25 indicates calibration issues)
- [ ] Collect test predictions from base models for ensemble

**Estimated Time**: 1 hour (verification only)

---

#### Day 3-4: Fix Ensemble Test Evaluation 🔴 CRITICAL
**Status**: Missing - prevents full pipeline

**Research Requirement**: Ensemble must be evaluated on test set separately to:
1. Verify stacking improves over individual base learners
2. Ensure calibration is reliable for clinical use
3. Compare test vs OOF to detect overfitting

**Implementation** (See CRITICAL_FIX_GUIDE_ENSEMBLE_TEST.md for detailed code):

**Step 1**: Base models must return test_predictions
```python
# In run_base_model_training() result dict, add:
'test_predictions': test_proba,  # shape (n_test,)
```

**Step 2**: Ensemble collects test predictions
```python
# In run_ensemble_training(), collect:
test_predictions = {}
for model_name, preds in base_test_preds.items():
    test_predictions[model_name] = np.array(preds)
```

**Step 3**: Ensemble evaluates on test set
```python
ensemble_test_proba = ensemble.predict_proba(test_predictions)
ensemble_test_auc = roc_auc_score(y_test, ensemble_test_proba)
# Also: precision, recall, F1, Brier score
```

**Step 4**: Return ensemble test metrics
```python
result = {
    'ensemble_oof_auc': oof_auc,
    'ensemble_test_auc': test_auc,      # ✅ NEW
    'ensemble_test_precision': prec,     # ✅ NEW
    'ensemble_test_recall': rec,         # ✅ NEW
    'ensemble_test_f1': f1,              # ✅ NEW
    'ensemble_test_brier': brier,        # ✅ NEW (critical for calibration)
    'meta_weights': weights,
    'is_calibrated': bool,
}
```

**Why Brier Score Matters**:
- Brier = average(probability error)²
- < 0.15: Excellent calibration
- 0.15-0.25: Good calibration
- > 0.25: Poor calibration (don't use for clinical decisions!)
- In research: Ensemble Brier should be ≤ base model Brier

**Estimated Time**: 1-2 hours

**Related Files to Update**:
- `app/api/endpoints/training.py` → `run_ensemble_training()`
- `app/ml/training/ensemble.py` → Already has calibration, just need test eval

---

#### Day 4-5: Implement Full Pipeline Orchestration 🔴 CRITICAL
**Status**: Not implemented (placeholder exists)

**Research Requirement**: 
Malaysian researchers need ONE endpoint to:
```
Generate Dataset 
    ↓
Train 10 Base Models (parallel) 
    ↓
Train Ensemble 
    ↓
Generate Evaluation Report
```

**Implementation**:

**Endpoint**: `POST /train/full-pipeline`
```json
{
  "batch_id": "batch_001",
  "target_column": "labels_disease_classification",
  "test_size": 0.35,
  "n_trials": 50
}
```

**Background Task** (`run_full_pipeline()`):
```python
async def run_full_pipeline(job_id, params, db):
    # Stage 1: Dataset generation (required by all downstream)
    dataset_job_id = create_job('dataset', params)
    await run_dataset_generation(dataset_job_id, params, db)
    
    # Stage 2: Train 10 base models in parallel (all depend on dataset)
    base_model_jobs = []
    for model_name in MODEL_NAMES:
        bm_job_id = create_job('base_model', {'dataset_id': dataset_job_id, ...})
        base_model_jobs.append(bm_job_id)
        # Execute in background without waiting
    
    # Wait for all base models to complete
    wait_for_jobs(base_model_jobs)
    
    # Stage 3: Train ensemble (depends on all base models)
    ensemble_job_id = create_job('ensemble', {'base_model_jobs': base_model_jobs, ...})
    await run_ensemble_training(ensemble_job_id, params, db)
    
    # Stage 4: Generate evaluation report
    report = generate_evaluation_report(
        base_model_jobs,
        ensemble_job_id,
        dataset_job_id
    )
    
    return report
```

**Estimated Time**: 3-4 hours

**Success Criteria**:
- [ ] Single endpoint orchestrates entire pipeline
- [ ] All base models train in parallel
- [ ] Ensemble waits for all base models to complete
- [ ] Progress trackable via `/train/status/{job_id}`
- [ ] Final report includes all metrics (base + ensemble)

---

### Week 2: Scorecard & Inference (Days 6-10)

#### Day 6-7: Implement Scorecard Conversion 🔴 CRITICAL FOR CLINICIANS
**Status**: Not implemented

**Research Requirement** (From Paper):
The scorecard converts logistic regression to point-based system:
- Each feature → bins (e.g., C4: Low/Normal/High)
- Each bin → point weight (scaled from LR coefficient)
- Sum points → risk score
- Apply Youden threshold → risk category

**Why This Matters**:
- Clinicians can't use probabilities directly
- Scorecard is printable, offline-usable
- Each feature's contribution visible

**Implementation**:

**Module**: Create `app/ml/scoring/scorecard_builder.py`

**Class**: `ScorecardBuilder`
```python
class ScorecardBuilder:
    """Convert trained Logistic Regression to interpretable scorecard"""
    
    def __init__(self, lr_model, X_train, y_train, feature_names):
        self.model = lr_model
        self.coefficients = lr_model.coef_[0]
        self.intercept = lr_model.intercept_
        self.features = feature_names
        self.bins = {}  # feature → bin edges
        self.scores = {}  # feature:bin → point score
        
    def build_bins(self, X_train, method='percentile'):
        """Create feature bins using percentile or Youden method (from research)"""
        for feature in self.features:
            if method == 'percentile':
                # Cut at 25%, 50%, 75% percentiles
                self.bins[feature] = [
                    X_train[feature].quantile(0.25),
                    X_train[feature].quantile(0.50),
                    X_train[feature].quantile(0.75),
                ]
    
    def coef_to_points(self):
        """Convert LR coefficients to integer points (scale by 100)"""
        for feature, coef in zip(self.features, self.coefficients):
            # Scale coefficient to 0-100 point range
            # Higher coefficient → higher risk
            points = int(abs(coef) * 100)
            self.scores[feature] = points
    
    def calculate_youden_threshold(self, y_test, test_proba):
        """Optimal threshold = argmax(sensitivity + specificity - 1)"""
        from sklearn.metrics import confusion_matrix
        best_threshold = 0.5
        best_youden = 0
        
        for threshold in np.linspace(0, 1, 101):
            pred = (test_proba >= threshold).astype(int)
            tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
            sensitivity = tp / (tp + fn)
            specificity = tn / (tn + fp)
            youden = sensitivity + specificity - 1
            
            if youden > best_youden:
                best_youden = youden
                best_threshold = threshold
        
        return best_threshold
    
    def score_patient(self, patient_features):
        """Input: patient features dict
        Output: {
            'total_score': int,
            'risk_category': 'Low'|'Medium'|'High'|'Very High',
            'feature_breakdown': {'C4': 25, 'CRP_high': 32, ...},
            'probability': float,
            'confidence': float
        }
        """
        patient_score = 0
        breakdown = {}
        
        for feature, value in patient_features.items():
            if feature not in self.features:
                continue
            
            # Find which bin patient falls into
            bin_idx = self._get_bin(feature, value)
            
            # Get points for this bin
            points = self.scores.get((feature, bin_idx), 0)
            breakdown[feature] = points
            patient_score += points
        
        # Map score to risk category using Youden threshold
        risk_category = self._score_to_category(patient_score)
        
        return {
            'total_score': patient_score,
            'feature_breakdown': breakdown,
            'risk_category': risk_category
        }
```

**Output Schema** (for API response):
```python
class ScorecardResponse(BaseModel):
    total_score: int
    feature_breakdown: Dict[str, int]  # feature -> points
    risk_category: Literal['Low', 'Medium', 'High', 'Very High']
    probability: float  # From ensemble
    confidence: float   # How certain is prediction?
    explanation: str    # "High risk due to: C4 low (32 pts), CRP elevated (25 pts)"
```

**Research-Based Risk Categories** (from paper):
- Low Risk: Score < threshold (e.g., < 60)
- High Risk: Score ≥ threshold (e.g., ≥ 68.8)

**Estimated Time**: 4-5 hours

---

#### Day 7-8: Inference API Endpoint 🔴 CRITICAL
**Status**: Not implemented

**Endpoint**: `POST /predict/score-patient`

**Input**:
```json
{
  "patient_id": "PAT001",
  "model_version": "v1.0",
  "features": {
    "age": 35,
    "gender": "F",
    "c4": 12.5,
    "c3": 45.2,
    "crp": 8.5,
    "urine_protein": 0.5,
    "acr": 2.3
  }
}
```

**Output**:
```json
{
  "patient_id": "PAT001",
  "model_version": "v1.0",
  "ensemble_probability": 0.82,
  "prediction": "High",
  "scorecard": {
    "total_score": 72,
    "risk_category": "High",
    "feature_breakdown": {
      "c4": 25,
      "crp": 32,
      "acr": 15
    }
  },
  "confidence": 0.91,
  "explanation": "High risk: C4 low (25 pts) + CRP elevated (32 pts) + ACR abnormal (15 pts) = 72 pts (threshold 68.8)",
  "timestamp": "2026-04-16T10:30:00Z"
}
```

**Implementation**:
```python
@router.post("/predict/score-patient", response_model=PredictionResponse)
async def predict_patient_risk(
    request: PredictionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Predict SLE disease activity risk for patient using trained ensemble + scorecard
    
    Flow:
    1. Load trained ensemble + scaler + scorecard from MinIO/database
    2. Validate + preprocess patient features
    3. Apply scaling (same as training)
    4. Get base model predictions
    5. Ensemble them
    6. Convert to scorecard
    7. Audit log the prediction
    """
    
    try:
        # Load model artifacts
        ensemble = load_model(f"ensemble/v{request.model_version}/meta_learner.pkl")
        scaler = load_model(f"ensemble/v{request.model_version}/scaler.pkl")
        scorecard = load_model(f"ensemble/v{request.model_version}/scorecard.pkl")
        
        # Preprocess input
        X = preprocess_features(request.features)
        X_scaled = scaler.transform(X)
        
        # Get prediction
        proba = ensemble.predict_proba(X_scaled)[0, 1]
        scorecard_output = scorecard.score_patient(request.features)
        
        # Audit log
        audit_log(
            user_id=current_user.id,
            action='prediction',
            patient_id=request.patient_id,
            prediction=scorecard_output['risk_category'],
            probability=proba,
            timestamp=datetime.utcnow()
        )
        
        return PredictionResponse(
            patient_id=request.patient_id,
            ensemble_probability=float(proba),
            prediction='High' if proba >= 0.5 else 'Low',
            scorecard=scorecard_output,
            confidence=abs(proba - 0.5) * 2,  # 0.5 → 0, 1.0 → 1.0
            explanation=generate_explanation(scorecard_output)
        )
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
```

**Estimated Time**: 3-4 hours

**Success Criteria**:
- [ ] Endpoint accepts patient features
- [ ] Returns ensemble probability + scorecard
- [ ] Predictions logged for audit trail
- [ ] Confidence score calculated
- [ ] Natural language explanation provided

---

#### Day 9-10: Model Persistence (MinIO) ⚠️ IMPORTANT
**Status**: Not implemented

**Why Critical**: 
- Without this, models disappear on server restart
- Researchers can't reproduce findings
- Inference can't work

**What to Save**:
```
MinIO:/models/ensemble/v1.0/
├── meta_learner.pkl (trained ensemble meta learner)
├── calibrated_meta_learner.pkl (calibration wrapper)
├── base_models/ (10 base model fold models)
├── scaler.pkl (StandardScaler used on training)
├── feature_pipeline.pkl (FeatureEngineeringPipeline)
├── scorecard.pkl (ScorecardBuilder instance)
├── metadata.json {
    "model_version": "v1.0",
    "training_date": "2026-04-16",
    "dataset_id": "batch_001",
    "train_size": 67,
    "test_size": 37,
    "n_features": 28,  # After LASSO
    "ensemble_test_auc": 0.9167,
    "ensemble_test_brier": 0.15,
    "feature_names": [...],
    "threshold_youden": 68.8
  }
├── test_metrics.json {
    "ensemble_auc": 0.9167,
    "base_models": {
      "xgboost": {"test_auc": 0.89, "test_f1": 0.82, ...},
      "logistic_regression": {"test_auc": 0.8667, "test_f1": 0.79, ...},
      ...
    }
  }
└── training_log.txt (detailed training output)
```

**Implementation** (in `run_ensemble_training()` after training completes):
```python
# Serialize all artifacts
model_version = f"v{timestamp}"
artifacts = {
    'meta_learner': ensemble.meta_learner,
    'calibrated_meta_learner': ensemble.calibrated_meta_learner,
    'scaler': ensemble.meta_scaler,
    'scorecard': scorecard_builder,
    'base_models': base_models_list,
    'metadata': {
        'version': model_version,
        'training_date': datetime.utcnow().isoformat(),
        'test_metrics': final_results
    }
}

# Save to MinIO
minio_client = get_minio_client()
for name, obj in artifacts.items():
    path = f"models/ensemble/{model_version}/{name}.pkl"
    minio_client.save_object(path, pickle.dumps(obj))

logger.info(f"Model artifacts saved to MinIO: {model_version}")
```

**Estimated Time**: 2-3 hours

---

## Phase 2: Evaluation & Reporting (Week 3)

### Day 11-12: Model Comparison Report
**Research Requirement**: Compare all base models + ensemble to validate stacking benefit

**Output**: Comparison table showing:
| Model | Train AUC | Test AUC | Precision | Recall | F1 | Brier | Calibration |
|-------|-----------|----------|-----------|--------|----|----|---|
| XGBoost | 0.95 | 0.88 | 0.82 | 0.75 | 0.78 | 0.18 | Good |
| LightGBM | 0.94 | 0.87 | 0.81 | 0.74 | 0.77 | 0.19 | Good |
| ... | ... | ... | ... | ... | ... | ... | ... |
| **Ensemble** | **0.96** | **0.92** | **0.87** | **0.81** | **0.84** | **0.15** | **Excellent** |

**Estimated Time**: 2-3 hours

---

### Day 13-15: Dashboard Integration
**Connect DashboardPage.jsx to real prediction API**

**What to Display**:
1. Patient input form (age, labs, etc.)
2. Real-time prediction
3. Scorecard breakdown
4. Risk category + confidence
5. Feature contribution visualization

**Estimated Time**: 4-5 hours

---

## Phase 3: Deployment & Handover (Week 4)

### Day 16-17: End-to-End Testing
- Upload new data → Feature engineering → Model training → Evaluation → Dashboard display
- **Success Criteria**: All components integrated and working

### Day 18-20: Documentation & Handover
- Research methodology mapping (completed above)
- Platform usage guide for Malaysian researchers
- Troubleshooting guide
- Credential handover

---

## Critical Success Metrics (For Research Reliability)

### From USM Research Paper:
✅ **Model Performance Must Match**:
- Logistic Regression Test AUC: ≥ 0.85 (paper: 0.8667)
- Scorecard Test AUC: ≥ 0.91 (paper: 0.9167)
- Precision: ≥ 0.73 (paper: 0.7333)
- F1: ≥ 0.81 (paper: 0.8148)

✅ **Calibration Must Be Excellent**:
- Brier Score < 0.20 (paper likely had this)
- If > 0.25: Don't deploy, requires calibration tuning

✅ **LASSO Must Reduce Features**:
- Input: 149 features → Output: ~20-30 features (from research: identified CRP_high, C4, Urine protein, C3, ACR as top predictors)

✅ **Scorecard Threshold**:
- Youden index calculated (not fixed)
- Typically: Score ≥ 68.8 indicates High risk (or similar based on your data)

---

## Weekly Checklist

### Week 1: Core Pipeline
- [ ] Day 1-2: Complete LASSO feature selection
- [ ] Day 2-3: Verify base model test evaluation
- [ ] Day 3-4: Fix ensemble test evaluation
- [ ] Day 4-5: Implement full pipeline orchestration
- **Validation**: Run full pipeline end-to-end, verify all metrics

### Week 2: Scorecard & Inference
- [ ] Day 6-7: Implement scorecard conversion
- [ ] Day 7-8: Create inference API endpoint
- [ ] Day 9-10: Persist models to MinIO
- **Validation**: Make inference on sample patient, verify scorecard + probability

### Week 3: Evaluation & Dashboard
- [ ] Day 11-12: Generate model comparison report
- [ ] Day 13-15: Connect dashboard to live predictions
- **Validation**: Dashboard displays real predictions with scorecard

### Week 4: Deployment
- [ ] Day 16-17: End-to-end testing in staging
- [ ] Day 18-20: Documentation & handover
- **Validation**: Malaysian researchers can use platform independently

---

## Risk Mitigation

**Risk**: Small dataset (104 patients) causes overfitting
**Mitigation**: 
- LASSO aggressively reduces features
- Logistic Regression simpler than ensemble (but ensemble helps)
- Test set held-out (35%) validates on unseen data
- Cross-validation during training

**Risk**: Models perform worse on real patient data
**Mitigation**:
- Careful preprocessing matching research exactly
- Audit every inference call
- Allow model retraining as more data collected

**Risk**: Clinicians don't trust probabilities
**Mitigation**:
- Scorecard is easy to verify by hand
- Feature explanations provided
- Calibration curves shown
- Brier score tracked

---

## Next Immediate Action

**TODAY**: Start Day 1 work
1. Review current LASSO implementation in `app/ml/training/dataset_generator.py`
2. Identify what's missing vs research requirements
3. Create test to verify LASSO reduces 149 → ~30 features

**GOAL**: By end of tomorrow, full pipeline runs end-to-end (even if not perfect).

This keeps momentum and prevents analysis paralysis. Movement > perfection in sprints.
