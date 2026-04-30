# ML Training Pipeline - Complete Workflow Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LAYER 6: ML PREP                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Derive     │  │  Calculate   │  │   Extract    │             │
│  │ longitudinal │→ │   ratios     │→ │  temporal    │             │
│  │  features    │  │              │  │  features    │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│  ┌──────────────────────────────────────────────────┐             │
│  │         Encode categorical variables              │             │
│  └──────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      LAYER 7: ML TRAINING                           │
│                                                                      │
│  BASE MODELS (Parallel Training):                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ XGBoost  │ │ LightGBM │ │ CatBoost │ │   SVM    │              │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │   KNN    │ │ AdaBoost │ │ Decision │ │   MLP    │              │
│  │          │ │          │ │  Trees   │ │          │              │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │
│  ┌──────────┐ ┌──────────┐                                         │
│  │  Random  │ │ Logistic │                                         │
│  │  Forest  │ │Regression│                                         │
│  └──────────┘ └──────────┘                                         │
│                                                                      │
│                         ↓ OOF Predictions                           │
│                                                                      │
│  META-LEARNER (Ensemble Layer):                                     │
│  ┌────────────────────────────────────────────────┐                │
│  │    Stacking Ensemble (Logistic Regression)     │                │
│  │    Learns to combine base model predictions     │                │
│  └────────────────────────────────────────────────┘                │
│                                                                      │
│  MODEL EVALUATION:                                                  │
│  ┌────────────────────────────────────────────────┐                │
│  │         Compare all models + ensemble           │                │
│  └────────────────────────────────────────────────┘                │
│                                                                      │
│  MODEL REGISTRY:                                                    │
│  ┌────────────────────────────────────────────────┐                │
│  │    Save best models to MinIO with metadata      │                │
│  └────────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   LAYER 8: EVALUATION METRIC                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ Accuracy │ │Precisions│ │Confusion │ │ AUC-ROC  │              │
│  │          │ │          │ │  Matrix  │ │          │              │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │
│  ┌──────────┐ ┌──────────┐                                         │
│  │    F1    │ │  Model   │                                         │
│  │          │ │Comparison│                                         │
│  └──────────┘ └──────────┘                                         │
└─────────────────────────────────────────────────────────────────────┘
```

## UI Navigation Flow

### Existing Pages (Keep & Enhance):
1. **Training Jobs** (`/training`) - START HERE
2. **Hyperparameter Tuning** (`/tuning`) - Optional advanced tuning
3. **Model Registry** (`/models`) - View deployed models

### Deleted:
- ❌ MLPlaygroundPage.jsx (redundant - integrate into Training Jobs)

---

## Complete Workflow

### Step 1: Training Jobs Page (Enhanced)

**Purpose:** Start new training runs, monitor progress

**Components:**
1. **Header** with "New Training Run" button
2. **Model Selection Panel** (10 algorithms with Lucide icons)
   - XGBoost (Zap icon)
   - LightGBM (Cpu icon)
   - CatBoost (Database icon)
   - Random Forest (GitBranch icon)
   - AdaBoost (TrendingUp icon)
   - SVM (Layers icon)
   - MLP (Brain icon)
   - KNN (Users icon)
   - Decision Tree (GitBranch icon)
   - Logistic Regression (BarChart3 icon)

3. **Active Training Runs** (existing DAG view)
   - Stage 1: Base learners (parallel)
   - Stage 2: Meta-learner (depends on Stage 1)

4. **Training History** (past runs with results)

**Workflow:**
```
Click "New Training Run"
  ↓
Select models (checkboxes with icons)
  ↓
Configure (test size, trials, CV folds)
  ↓
Click "Start Training"
  ↓
Dataset generation (background)
  ↓
Models train in parallel
  ↓
View real-time progress
  ↓
Results appear in Model Registry
```

---

### Step 2: Hyperparameter Tuning Page (Existing - Optional)

**Purpose:** Advanced tuning for specific models

**When to use:**
- After initial training run
- Want to fine-tune a specific model
- Experiment with different hyperparameters

**Workflow:**
```
Select trained model from dropdown
  ↓
Adjust hyperparameters manually OR
Run grid search / Optuna optimization
  ↓
Compare with baseline
  ↓
Save if better
```

---

### Step 3: Model Registry Page (Existing - Enhanced)

**Purpose:** View, compare, and deploy models

**Shows:**
- All trained models (base + ensemble)
- Version history
- Performance metrics
- Deployment status

**Actions:**
- Deploy to production
- Download model artifacts
- View SHAP explanations
- Compare models side-by-side

---

## API Endpoint Mapping

### Training Jobs Page Uses:
```
POST   /api/v1/ml/train/prepare-dataset       # Generate training dataset
POST   /api/v1/ml/train/feature-selection     # LASSO selection
POST   /api/v1/ml/train/base-model            # Train single model
POST   /api/v1/ml/train/ensemble              # Train meta-learner
GET    /api/v1/ml/train/status/{job_id}       # Poll job status
```

### Model Registry Page Uses:
```
GET    /api/v1/ml/models/list                 # List all models
GET    /api/v1/ml/evaluate/{model_id}         # Get metrics
GET    /api/v1/ml/feature-importance/{model_id} # SHAP values
```

### Hyperparameter Tuning Page Uses:
```
POST   /api/v1/ml/train/base-model            # With custom params
GET    /api/v1/ml/train/status/{job_id}       # Monitor tuning
```

---

## Data Flow

### 1. Dataset Preparation (Happens in Background)
```javascript
// User clicks "Start Training"
const datasetResponse = await axios.post('/api/v1/ml/train/prepare-dataset', {
  target_column: 'diagnosis_category',
  test_size: 0.35,
  random_state: 42
});

// Poll until dataset ready
const datasetJobId = datasetResponse.data.job_id;
// Wait for status === 'completed'
```

### 2. Model Training (Parallel)
```javascript
// For each selected model
for (const modelName of selectedModels) {
  await axios.post('/api/v1/ml/train/base-model', {
    model_name: modelName,
    dataset_id: datasetJobId,
    n_trials: 50,
    cv_folds: 5
  });
}

// Poll each job status every 10 seconds
// Update progress bars in UI
```

### 3. Ensemble Training (After Base Models Complete)
```javascript
// Check if all base models completed
const allComplete = baseJobs.every(job => job.status === 'completed');

if (allComplete) {
  await axios.post('/api/v1/ml/train/ensemble', {
    dataset_id: datasetJobId,
    base_model_jobs: baseJobIds
  });
}
```

### 4. View Results
```javascript
// Get all models
const models = await axios.get('/api/v1/ml/models/list');

// Get evaluation metrics
for (const model of models) {
  const metrics = await axios.get(`/api/v1/ml/evaluate/${model.model_id}`);
  // Display: AUC-ROC, Precision, Recall, F1
}
```

---

## Training Jobs Page - Detailed Design

### Layout Structure:
```
┌─────────────────────────────────────────────────────────┐
│  Training Jobs                    [New Training Run]    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ACTIVE RUNS                                             │
│  ┌────────────────────────────────────────────────┐    │
│  │  Run #123: 10-Model Ensemble                   │    │
│  │  ━━━━━━━━━━ 60% (6/10 models completed)       │    │
│  │                                                  │    │
│  │  Stage 1: Base Models                           │    │
│  │  [✓] XGBoost      AUC: 0.847  (3m 24s)        │    │
│  │  [⚡] LightGBM    75% Training...              │    │
│  │  [○] CatBoost     Queued                       │    │
│  │  ...                                            │    │
│  │                                                  │    │
│  │  Stage 2: Meta-Learner                          │    │
│  │  [🔒] Locked - Waiting for Stage 1             │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  RECENT RUNS                                             │
│  ┌────────────────────────────────────────────────┐    │
│  │  Run #122: 3-Model Test   ✓ Complete           │    │
│  │  Best: XGBoost (AUC: 0.851)                    │    │
│  │  [View Results] [View in Registry]             │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### New Training Run Dialog:
```
┌─────────────────────────────────────────────────────────┐
│  Start New Training Run                     [X]         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  SELECT MODELS TO TRAIN                                  │
│                                                          │
│  Gradient Boosting:                                      │
│  [✓] XGBoost        [✓] LightGBM      [✓] CatBoost     │
│                                                          │
│  Ensemble Methods:                                       │
│  [ ] Random Forest  [ ] AdaBoost                        │
│                                                          │
│  Linear & Distance:                                      │
│  [ ] SVM            [ ] KNN           [ ] Logistic Reg  │
│                                                          │
│  Neural & Trees:                                         │
│  [ ] MLP            [ ] Decision Tree                   │
│                                                          │
│  ────────────────────────────────────────────────       │
│                                                          │
│  CONFIGURATION                                           │
│  Test Size:     [────●────] 35%                         │
│  Optuna Trials: [────●────] 50                          │
│  CV Folds:      [────●────] 5                           │
│                                                          │
│  [Cancel]                   [Start Training (3 models)] │
└─────────────────────────────────────────────────────────┘
```

---

## Icon Mapping (Lucide React)

| Model | Icon | Rationale |
|-------|------|-----------|
| XGBoost | `Zap` | Fast, powerful |
| LightGBM | `Cpu` | Efficient processing |
| CatBoost | `Database` | Handles categorical data |
| Random Forest | `GitBranch` | Many branching trees |
| AdaBoost | `TrendingUp` | Adaptive boosting |
| SVM | `Layers` | Multiple layers/margins |
| MLP | `Brain` | Neural network |
| KNN | `Users` | Neighbor-based |
| Decision Tree | `GitBranch` | Single branching tree |
| Logistic Regression | `BarChart3` | Statistical model |

---

## Testing Sequence

### 1. Navigate to Training Jobs
```
GET http://100.106.132.15:8000 → Login → Training Jobs
```

### 2. Start New Training Run
```
Click "New Training Run" button
Select: XGBoost, LightGBM, CatBoost
Set trials: 20 (quick test)
Click "Start Training"
```

### 3. Monitor Progress
```
Watch dataset generation (10-20 seconds)
Watch models train (5-15 minutes total)
See progress bars update every 10 seconds
```

### 4. View Results
```
Click "View Results" on completed run
Navigate to Model Registry
See all 3 models + ensemble (if implemented)
Compare AUC scores
```

### 5. Deploy Best Model
```
In Model Registry:
Click best model (highest AUC)
Click "Deploy to Production"
Model becomes active for predictions
```

---

## Implementation Priority

### Phase 1: Core Training (This Sprint)
1. ✅ Backend API endpoints (Done)
2. ⏳ Enhanced Training Jobs page with model selection
3. ⏳ API integration and polling
4. ⏳ Real-time progress display

### Phase 2: Ensemble & Evaluation (Next Sprint)
1. Ensemble training automation
2. Model comparison charts
3. SHAP feature importance
4. ROC curve visualization

### Phase 3: Advanced Features (Future)
1. Hyperparameter tuning integration
2. Model versioning
3. A/B testing deployment
4. Automated retraining

---

## Files to Modify

### Delete:
- `frontend/src/pages/MLPlaygroundPage.jsx` (redundant)

### Modify:
- `frontend/src/pages/TrainingJobsPage.jsx` - Add model selection + API integration
- `frontend/src/App.jsx` - Remove MLPlayground route
- `frontend/src/components/DashboardLayout.jsx` - Remove ML Playground link

### Keep as-is:
- `frontend/src/pages/ModelRegistryPage.jsx`
- `frontend/src/pages/HyperparameterTuningPage.jsx`
- All backend files

---

## Next Step: Implement Enhanced Training Jobs Page

Ready to build the integrated version without emojis?
