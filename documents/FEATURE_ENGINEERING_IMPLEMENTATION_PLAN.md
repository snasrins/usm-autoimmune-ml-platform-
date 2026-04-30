# Feature Engineering UI Implementation Plan

## Current State
- ✅ Features tab exists in DataPreparationPage.jsx (line 1843)
- ❌ Shows LASSO (disabled)
- ❌ No UI for actual feature engineering (ratios, temporal, etc.)

## What to Implement

### Backend API (New Endpoint)
**File:** `app/api/endpoints/ml_features.py` (new file)

```python
@router.post("/ml/engineer-features")
async def engineer_features(
    request: FeatureEngineeringRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Apply feature engineering to a dataset
    - Ratio features (CRP/ESR, NLR, PLR)
    - Temporal features (disease duration)
    - Derived features (inflammation score)
    - Categorical encoding (automatic)
    """
    # Use FeatureEngineeringPipeline
    # Return engineered dataset
```

### Frontend UI Replacement

**Replace LASSO section with:**

1. **Biomarker Ratios** (`calculate ratios`)
   - CRP/ESR Ratio ☑️
   - Neutrophil-Lymphocyte Ratio (NLR) ☑️  
   - Platelet-Lymphocyte Ratio (PLR) ☑️

2. **Temporal Features** (`extract temporal features`)
   - Disease Duration (years) ☑️
   - Time Since Diagnosis ☑️

3. **Derived Features** (`derive longitudinal features`)
   - Inflammation Score (mean of CRP, ESR) ☑️
   - Organ Involvement Count ☑️

4. **Categorical Encoding** (automatic, already in pipeline)
   - One-hot encoding ✓ (happens automatically)

## Files to Modify

1. **`app/api/endpoints/ml_features.py`** (NEW) - Feature engineering endpoint
2. **`app/schemas/feature_engineering.py`** (NEW) - Request/Response models
3. **`frontend/src/pages/DataPreparationPage.jsx`** - Replace LASSO UI
4. **`frontend/src/services/api.js`** - Add API method

## Implementation Steps

1. Create backend endpoint
2. Create UI controls for selecting features
3. Wire frontend → backend
4. Show results (new features added)

---

**Ready to implement?** Say yes and I'll create the code!
