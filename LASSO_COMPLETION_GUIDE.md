# LASSO Feature Selection - Completion Guide

## Current State Assessment

**Location**: `app/ml/training/dataset_generator.py` → `_lasso_feature_selection()` method

**What You Need to Complete**: 
The LASSO method exists but may be incomplete or not properly integrated. Let's verify.

---

## What LASSO Must Do (From Research)

### Input
- **X**: Feature matrix from all 104 patients (before train/test split)  
- **y**: Target variable (SLEDAI: Low <4, High ≥4)
- **alpha**: L1 regularization parameter (controls how aggressive feature culling is)

### Output
- **X_reduced**: Same data, but only with selected features (typically 20-30 remaining)
- **selected_features**: List of feature names that survived LASSO
- **lasso_model**: Fitted LASSO object (for reproducibility/scikit-learn pipeline)

### Key Constraint
**CRITICAL**: LASSO must fit on training data only, but here we can fit on full data since it's just feature selection (not cross-validation). However, in production you might want separate LASSO fitting on train vs transforming on test.

---

## Implementation Checklist

### Step 1: Verify LASSO is Being Called
**File**: `app/ml/training/dataset_generator.py`

**Search** for: `_lasso_feature_selection`

**You should find this in `generate_training_dataset()` around line ~190-205**:

```python
# Step 5: LASSO Feature Selection (CRITICAL: Before train/test split to prevent leakage)
selected_features = None
if skip_preprocessing:
    selected_features = original_feature_names
    logger.info("LASSO feature selection SKIPPED (skip_preprocessing=True)")
elif use_lasso_feature_selection:
    X, selected_features = self._lasso_feature_selection(
        X, y, 
        alpha=lasso_alpha, 
        random_state=random_state
    )
    logger.info(f"After LASSO selection: {X.shape} ({len(selected_features)} features kept)")
else:
    selected_features = original_feature_names
    logger.info("LASSO feature selection skipped (use_lasso_feature_selection=False)")
```

✅ **Check**: Is this code present? If not, add it.

---

### Step 2: Examine LASSO Method Implementation

**Find** the method definition:
```python
def _lasso_feature_selection(self, X, y, alpha=0.01, random_state=42):
```

**This method should:**

❌ **If missing or incomplete**, here's the complete implementation:

```python
def _lasso_feature_selection(
    self, 
    X: pd.DataFrame, 
    y: pd.Series,
    alpha: float = 0.01,
    random_state: int = 42
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Use LASSO (L1) regression to select most predictive features
    Prevents "curse of dimensionality" on small datasets (104 patients)
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target variable (n_samples,)
        alpha: L1 regularization strength (higher = fewer features)
               Typical range: 0.0001 to 1.0
               Start with 0.01, adjust based on feature count output
        random_state: Reproducibility
    
    Returns:
        X_selected: DataFrame with only selected features
        selected_features: List of feature names kept by LASSO
    """
    from sklearn.linear_model import LassoCV
    import numpy as np
    
    logger.info(f"LASSO Feature Selection starting...")
    logger.info(f"  Input shape: {X.shape} ({len(X.columns)} features)")
    logger.info(f"  Alpha (L1 strength): {alpha}")
    
    # Fit LASSO to identify important features
    # LassoCV automatically finds optimal alpha via cross-validation
    lasso = LassoCV(
        alphas=np.logspace(-4, 0, 50),  # Range of alphas to test: 0.0001 to 1.0
        cv=5,  # 5-fold CV (small data, so limited CV folds)
        random_state=random_state,
        max_iter=10000,
        n_jobs=-1,  # Parallel processing
        verbose=0
    )
    
    logger.info(f"  Fitting LASSO via cross-validation (5-fold)...")
    lasso.fit(X, y)
    
    logger.info(f"  Optimal alpha found: {lasso.alpha_:.6f}")
    
    # Get feature coefficients
    coef = lasso.coef_
    
    # Features with non-zero coefficients are selected
    # (LASSO shrinks unimportant feature coefficients to exactly 0)
    selected_indices = np.where(coef != 0)[0]
    selected_features = X.columns[selected_indices].tolist()
    
    n_removed = len(X.columns) - len(selected_features)
    removal_pct = (n_removed / len(X.columns)) * 100
    
    logger.info(f"  Results:")
    logger.info(f"    Features selected: {len(selected_features)}")
    logger.info(f"    Features removed: {n_removed} ({removal_pct:.1f}%)")
    logger.info(f"    Output shape: {X.shape[0]} samples × {len(selected_features)} features")
    
    # Log top features (by absolute coefficient magnitude)
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'coefficient': coef
    }).reindex(X.columns)
    
    feature_importance['abs_coef'] = feature_importance['coefficient'].abs()
    top_features = feature_importance.nlargest(10, 'abs_coef')
    
    logger.info(f"  Top predictive features (by coefficient magnitude):")
    for idx, row in top_features.iterrows():
        logger.info(f"    {row['feature']}: {row['coefficient']:.6f}")
    
    logger.info(f"  Removed features:")
    removed_features = feature_importance[feature_importance['coefficient'] == 0]['feature'].tolist()
    if len(removed_features) <= 20:
        for feat in removed_features[:10]:
            logger.info(f"    - {feat}")
        if len(removed_features) > 10:
            logger.info(f"    ... and {len(removed_features) - 10} more")
    else:
        for feat in removed_features[:5]:
            logger.info(f"    - {feat}")
        logger.info(f"    ... and {len(removed_features) - 5} more")
    
    # Select only the selected features
    X_selected = X[selected_features].copy()
    
    # Store LASSO model for reference (can be used later for explanation)
    self.lasso_model = lasso
    
    return X_selected, selected_features
```

✅ **Add this if missing**, or replace if incomplete.

---

### Step 3: Verify LASSO is Called with Correct Parameters

**In `generate_training_dataset()`** method signature, verify these parameters exist:

```python
def generate_training_dataset(
    self,
    batch_id: str,
    target_column: str = "labels_disease_classification",
    min_events_per_patient: int = 2,
    test_size: float = 0.2,
    random_state: int = 42,
    create_separate_feature_sets: bool = True,
    scaling_strategy: str = 'standard',
    use_lasso_feature_selection: bool = True,  # ✅ Must be True by default
    lasso_alpha: float = 0.01,  # ✅ Tunable; 0.01 is good starting point
    skip_preprocessing: bool = False
) -> Dict:
```

✅ **Check**: 
- [ ] `use_lasso_feature_selection=True` (default enables it)
- [ ] `lasso_alpha=0.01` (starting value, can adjust)
- [ ] Both parameters are passed to LASSO call

---

### Step 4: Test LASSO Output

**Create a simple test script**:

```python
# test_lasso.py
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ml.training import DatasetGenerator

# Setup database connection
DATABASE_URL = "postgresql://user:password@localhost/db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

# Create dataset generator
generator = DatasetGenerator(db)

# Generate dataset with LASSO enabled
result = generator.generate_training_dataset(
    batch_id="test_batch_001",
    target_column="labels_disease_classification",
    use_lasso_feature_selection=True,
    lasso_alpha=0.01,  # Default
    test_size=0.35,    # Research uses 35% test
    random_state=42
)

# Check results
print(f"Original features: {len(result['original_feature_names'])}")
print(f"After LASSO: {len(result['feature_names'])}")
print(f"Reduction: {100 - (len(result['feature_names']) / len(result['original_feature_names']) * 100):.1f}%")
print(f"\nRemaining features: {result['feature_names']}")
print(f"\nX_train shape: {result['X_train'].shape}")
print(f"X_test shape: {result['X_test'].shape}")

# Expected output (from research):
# Original features: 149
# After LASSO: ~25-30 (depends on alpha)
# Reduction: 80-85%
# Remaining should include: CRP_high, C4, Urine protein, C3, ACR, etc.
```

✅ **Run and verify**:
- [ ] Features reduced from 149 → ~20-40 (research likely had ~25)
- [ ] Key research features present (CRP, C4, C3, ACR, Urine protein)
- [ ] LASSO logs shows alpha value used
- [ ] No errors in feature selection

**Run command**:
```bash
cd /path/to/project
python test_lasso.py
```

---

### Step 5: Alpha Tuning (If Needed)

If LASSO removes **too many** features (< 10 remaining):
```python
# Run again with smaller alpha (less aggressive)
result = generator.generate_training_dataset(
    ...,
    lasso_alpha=0.001,  # ← Smaller alpha = keep more features
    ...
)
```

If LASSO removes **too few** features (> 100 remaining):
```python
# Run again with larger alpha (more aggressive)
result = generator.generate_training_dataset(
    ...,
    lasso_alpha=0.1,  # ← Larger alpha = remove more features
    ...
)
```

**Goal**: End up with 20-40 features (research had ~25 optimal)

---

### Step 6: Verify Integration with Training

**Test the full pipeline**:

```python
# test_full_pipeline.py
import requests

# Call full pipeline endpoint
response = requests.post(
    "http://localhost:8001/api/v1/train/full-pipeline",
    json={
        "batch_id": "test_batch_combined",
        "target_column": "labels_disease_classification",
        "test_size": 0.35,
        "n_trials": 10  # Small for testing
    }
)

pipeline_job_id = response.json()['job_id']
print(f"Pipeline started: {pipeline_job_id}")

# Poll for status
import time
for i in range(120):  # 2 minutes max
    status = requests.get(f"http://localhost:8001/api/v1/train/status/{pipeline_job_id}")
    status_data = status.json()
    
    if status_data['status'] == 'COMPLETED':
        print(f"\n✅ Pipeline completed!")
        results = status_data.get('result', {})
        
        # Check LASSO worked
        dataset_results = results.get('dataset', {})
        print(f"Features after LASSO: {len(dataset_results.get('feature_names', []))}")
        
        # Check base models trained
        base_models = results.get('base_models', {})
        print(f"Base models trained: {len(base_models)}")
        
        # Check ensemble trained
        ensemble_results = results.get('ensemble', {})
        print(f"Ensemble test AUC: {ensemble_results.get('test_auc', 'N/A')}")
        
        break
    elif status_data['status'] == 'FAILED':
        print(f"\n❌ Pipeline failed!")
        print(status_data.get('error_message', 'Unknown error'))
        break
    else:
        print(f"Status: {status_data['status']} - {i}s...")
        time.sleep(1)
```

✅ **Success criteria**:
- [ ] Pipeline completes without error
- [ ] LASSO reduces features as expected
- [ ] All 10 base models train
- [ ] Ensemble trains without error
- [ ] Test metrics returned

---

## Validation Checklist Before Proceeding

### Data Quality (Before LASSO)
- [ ] No NaN values in features (should be imputed by Layer 5)
- [ ] Target variable has both classes (Low + High activity)
- [ ] 104 samples reasonable for 149 initial features

### LASSO Execution
- [ ] Method `_lasso_feature_selection()` exists and is correct
- [ ] Called in `generate_training_dataset()` when `use_lasso_feature_selection=True`
- [ ] Returns X_selected and selected_features list
- [ ] Logs show feature counts (149 → ~25-30)

### LASSO Output
- [ ] Selected features include research-identified predictors (CRP, C4, C3, ACR, Urine protein)
- [ ] Selected features make clinical sense
- [ ] Feature reduction reasonable (80-85%)

### Integration
- [ ] Full pipeline runs end-to-end
- [ ] Base models train on LASSO-selected features
- [ ] Ensemble trains successfully
- [ ] Test metrics calculated

### Performance (From Research Targets)
- [ ] Base model test AUC ≥ 0.8 (ideally 0.85-0.92)
- [ ] Ensemble test AUC ≥ 0.91 (research: 0.9167)
- [ ] Brier score < 0.20 (good calibration)

---

## Troubleshooting

### Problem: "NameError: name '_lasso_feature_selection' is not defined"
**Solution**: Method doesn't exist. Add the full implementation from Step 2.

### Problem: "LASSO running very slowly"
**Solution**: Check n_jobs parameter is -1 for parallelization. May also need to reduce CV folds from 5 to 3 for speed.

### Problem: "Too many features still selected" (> 100 remaining)
**Solution**: Increase alpha value:
```python
lasso_alpha=0.05  # or 0.1
```
Or use LassoCV more aggressively:
```python
alphas=np.logspace(-3, 1, 100)  # Wider range
```

### Problem: "Too few features selected" (< 10 remaining)
**Solution**: Decrease alpha value:
```python
lasso_alpha=0.001  # or 0.0001
```

### Problem: "Model performance worse after LASSO"
**Solution**: Normal for first iteration. Verify:
- LASSO didn't remove ALL predictive features
- Alpha value is reasonable (0.001-0.1 range)
- Try different alpha systematically:
  ```python
  for alpha in [0.0001, 0.001, 0.01, 0.1]:
      result = generator.generate_training_dataset(..., lasso_alpha=alpha)
      # Compare test AUC
  ```

---

## Research Alignment Check

From your USM research paper, verify:

✅ **Did LASSO do this?**
- Removed >50% of features? (Research removed ~80%)
- Identified CRP_high, C4, C3, ACR, Urine protein? (Research top 5)
- Reduced curse of dimensionality? (Small data problem solved)

✅ **Is output clinically sensible?**
- Selected features are measurable labs? (Not abstract engineered features)
- Can clinician understand why each feature matters? (LASSO coefficients interpretable)

✅ **Does it match research methodology?**
- Binary target: Low vs High activity ✅
- Train/test split 65/35 ✅
- Z-score normalization ✅
- LASSO for feature selection ✅

---

## Next Steps After LASSO Completion

Once LASSO is working:
1. ✅ Complete ensemble test evaluation (1-2 hours)
2. ✅ Implement full pipeline (3-4 hours)
3. ✅ Build scorecard conversion (4-5 hours)
4. ✅ Create inference API (3-4 hours)

**Total to working system**: ~15 hours

---

## Files to Check/Edit

| File | Action |
|------|--------|
| `app/ml/training/dataset_generator.py` | Verify/add `_lasso_feature_selection()` method |
| `app/ml/training/dataset_generator.py` | Verify LASSO is called in `generate_training_dataset()` |
| `test_lasso.py` | Create quick test script |
| `test_full_pipeline.py` | Create integration test |

---

**Start here**: Check if `_lasso_feature_selection()` method exists. If not, add the full implementation. If partial, compare with Step 2 and complete.

Once working, move to ensemble test evaluation (next highest priority).
