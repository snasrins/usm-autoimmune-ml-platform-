# Enterprise ML Platform - Page Redesign Specifications

## Overview
This document specifies the production-grade redesign of Model Registry, Training Jobs, and Hyperparameter Tuning pages for a stacking ensemble workflow, following enterprise ML platform standards (W&B, SageMaker, Vertex AI).

---

## 1. MODEL REGISTRY

### Purpose
Source of truth for every model artifact with version control, role-based filtering, and ensemble composition visualization.

### Key Features

#### A. Version Control System
- **Version badges**: Display current version (e.g., v3.2, v2.4, v1.0-draft)
- **Version history**: Dropdown showing all historical versions
- **Rollback capability**: One-click revert to previous version
- **Version comparison**: Side-by-side diff of two versions

#### B. Role-Based Classification
- **Base Learner**: Models that train on original data (5 slots in ensemble)
- **Meta-Learner**: Model that trains on base learner predictions (1 slot)
- **Role pill**: Color-coded badge (blue for base, purple for meta)
- **Role filter**: Dropdown to show only base or meta learners

#### C. Status Management
- **Promoted**: Approved for use in active ensemble (green badge)
- **Draft**: Under development, not production-ready (amber badge)
- **Deprecated**: Retired from use (gray badge)
- **Status actions**: Promote/Demote buttons based on current status

#### D. Ensemble Composition Viewer
**Visual representation of current production stack:**

```
[STAGE 1: BASE LEARNERS]
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ RF v3.2 │ │ XGB v2.4│ │ GB v1.8 │ │ SVM v2.1│ │ LR v3.0 │
│ 87.3%   │ │ 84.7%   │ │ 86.2%   │ │ 82.9%   │ │ 79.4%   │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
     │           │           │           │           │
     └───────────┴───────────┴───────────┴───────────┘
                          │
                 [Out-of-fold predictions]
                          │
                    [STAGE 2: META-LEARNER]
                    ┌──────────────┐
                    │  LR Stack    │
                    │  v2.0        │
                    │  91.8%       │
                    └──────────────┘
```

- Shows 5 base learner slots + 1 meta-learner slot
- Empty slots show dashed outline with "+" indicator
- Active models highlighted with border accent
- Displays model name, version, and accuracy in each slot

#### E. Model Card Structure
Each card contains:
- **Header**: Model name + version badge
- **Role pill**: Color-coded base/meta indicator
- **Status badge**: Promoted/Draft/Deprecated with icon
- **Active indicator**: Green "Active" badge if in current ensemble
- **Lineage text**: Brief description of model's purpose and dependencies
- **Metrics strip**: Accuracy, Precision, Recall, F1 (4 columns)
- **Metadata**: Dataset version, training date, version count
- **Actions**: View Details, Promote/Demote, Retrain buttons

#### F. Search & Filter Toolbar
- **Search box**: By model name or algorithm
- **Role filter**: All / Base Learner / Meta-Learner
- **Status filter**: All / Promoted / Draft / Deprecated
- **Algorithm filter**: All / Random Forest / XGBoost / etc.

#### G. Stats Dashboard
- Total Models count
- Promoted models count
- Base Learners count (of promoted)
- Average accuracy of promoted models

---

## 2. TRAINING JOBS

### Purpose
Execution layer showing real-time training progress with dependency-aware two-stage workflow for stacking.

### Key Features

#### A. GPU Quota Tracker
**Fixed bar at top of page:**
- Shows current GPU hours consumed vs. weekly limit
- Color-coded: Green (< 50%), Amber (50-80%), Red (> 80%)
- Visual progress bar
- Warning at 6 hours if limit is 8 hours

#### B. Two-Stage Dependency View
**Toggle between List View and DAG View:**

**DAG View Structure:**
```
[STAGE 1: BASE LEARNERS - PARALLEL EXECUTION]
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ RF Training  │  │ XGB Training │  │ GB Training  │  │ SVM Training │  │ LR Training  │
│ ████████░░ 80%│  │ ██████░░░░ 60%│  │ ██████████ 100%│  │ █████░░░░░ 50%│  │ ███░░░░░░░ 30%│
│ 2.1h / 2.5h  │  │ 1.5h / 2.2h  │  │ Completed    │  │ 1.0h / 1.8h  │  │ 0.8h / 2.0h  │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
       │                  │                 │                  │                 │
       └──────────────────┴─────────────────┴──────────────────┴─────────────────┘
                                          │
                            [DEPENDENCY: All Stage 1 complete]
                                          │
                        [STAGE 2: META-LEARNER - LOCKED STATE]
                        ┌──────────────────────────┐
                        │ Stack Meta-Learner       │
                        │ 🔒 Waiting for Stage 1   │
                        │ Will start automatically │
                        └──────────────────────────┘
```

**When Stage 1 completes:**
- Meta-learner card unlocks
- "Start Meta-Learner Training" button appears
- One-click to kick off Stage 2

#### C. Job Card Structure
- **Header**: Job name + timestamp
- **Status chip**: Running (pulsing), Queued, Completed, Failed
- **Model + Dataset**: Which model, which data version
- **Progress bar**: (if running) % complete + ETA
- **GPU hours**: Consumed for this specific job
- **Live metrics**: (if running) Current loss and accuracy streaming
- **Completed metrics**: (if done) Final accuracy, precision, recall
- **Error message**: (if failed) Inline reason, no need to check logs
- **Actions**: Compare (checkbox), View Details

#### D. Comparison Tray
**Floating bar at bottom when jobs selected:**
- Shows up to 5 selected job cards in mini format
- "Compare Selected" button opens side-by-side diff view
- Diff shows: Hyperparameters changed, Metrics difference, Dataset versions

#### E. Status Filters
**Tab row at top:**
- All
- Running (with count badge)
- Queued
- Completed
- Failed

#### F. Side-by-Side Comparison Modal
When comparing 2+ jobs:
- **Left/Right columns**: One job per column
- **Hyperparameters**: Highlight differences in yellow
- **Metrics**: Show delta (e.g., +2.3% accuracy)
- **Training curves**: Overlay loss/accuracy plots
- **Dataset versions**: Flag if different data used

---

## 3. HYPERPARAMETER TUNING

### Purpose
Researcher playground for manual experimentation and automated hyperparameter search with separate base/meta-learner tuning.

### Key Features

#### A. Three-Tab Interface

**Tab 1: Manual Run**
- Model selector dropdown (all 11 models)
- Hyperparameter form with sliders and tooltips
- "Launch Run" button
- "Save as Template" button

**Tab 2: Automated Sweep**
- Model selector
- Search strategy: Grid / Random / Bayesian (with descriptions)
- Parameter range table (min, max, step for each param)
- "Max Trials" input
- **Compute cost estimator**: Live calculation of GPU hours
- "Launch Sweep" button

**Tab 3: Meta-Learner Tuning**
- Same structure as Manual/Sweep
- Scoped only to meta-learner algorithms
- Additional toggle: "Include original features alongside base learner outputs"

#### B. Hyperparameter Controls
- **Range sliders**: Visual adjustment + numeric input
- **Dropdowns**: For categorical (kernel type, optimizer)
- **Text fields**: For complex configs (layer architecture)
- **Info icons**: Tooltip explaining what each parameter does
- **Live value display**: Current value shown next to slider

#### C. Leaderboard
**Table of all trial runs (ranked by validation accuracy):**

| Trial | n_estimators | max_depth | learning_rate | Accuracy | Precision | Recall | Duration | Actions |
|-------|--------------|-----------|---------------|----------|-----------|--------|----------|---------|
| 47    | 200          | 12        | 0.05          | **91.2%**| 92.1%     | 90.3%  | 1.2h     | [Promote] [View] |
| 23    | 150          | 10        | 0.08          | 89.7%    | 90.2%     | 89.2%  | 0.9h     | [Promote] [View] |
| 12    | 100          | 15        | 0.1           | 88.3%    | 89.1%     | 87.5%  | 0.8h     | [Promote] [View] |

- **Best row highlighted**: Green background
- **Sortable columns**: Click any column header
- **Promote to Training Job button**: Pre-fills training form with exact hyperparameters
- **Trial detail modal**: Click "View" to see full config and metrics

#### D. Parallel Coordinates Visualization
**Interactive plot showing hyperparameter relationships:**

```
    n_estimators    max_depth    learning_rate   Accuracy
        │               │              │              │
   50 ──┤          5 ───┤         0.01─┤         70%──┤
  100 ──┤         10 ───┤         0.05─┤         80%──┤
  150 ──┤         15 ───┤          0.1─┤         90%──┤
  200 ──┤         20 ───┤          0.2─┤        100%──┤
        │               │              │              │
```

- Each trial is a line crossing all parameter axes
- Lines colored by accuracy (red = low, green = high)
- Hover shows trial number and exact values
- Click to highlight specific trial
- Reveals patterns: "High accuracy trials cluster around max_depth 10-12"

#### E. Compute Cost Estimator
**Live calculation as researcher adjusts sweep settings:**

```
┌─────────────────────────────────┐
│ Estimated Compute Cost          │
│                                 │
│ Configurations: 120             │
│ Avg time per trial: 45 min     │
│ Total GPU hours: ~90 hours      │
│                                 │
│ ⚠️ Exceeds weekly quota (8h)   │
│ Suggestion: Reduce trials to 20│
└─────────────────────────────────┘
```

- Updates instantly as max_trials or parameter ranges change
- Warns if sweep will exceed quota
- Suggests reduction to fit within limits

#### F. Template System
- **Save Configuration**: Stores entire hyperparam setup with name
- **Load Template**: Dropdown of saved templates
- **Quick variations**: Load template + change one parameter = ablation study

---

## Data Structure Examples

### Model Registry - Model Object
```javascript
{
  id: 1,
  name: 'Random Forest Classifier',
  version: 'v3.2',
  versionHistory: ['v1.0', 'v2.0', 'v2.1', 'v3.0', 'v3.1', 'v3.2'],
  algorithm: 'Random Forest',
  role: 'base',  // or 'meta'
  status: 'promoted',  // or 'draft', 'deprecated'
  accuracy: 87.3,
  precision: 89.1,
  recall: 85.7,
  f1Score: 87.3,
  datasetVersion: 'AAM-SLE-E v2.1',
  trainedDate: '2024-03-28',
  hyperparameters: { n_estimators: 100, max_depth: 15, min_samples_split: 5 },
  lineage: 'Base learner for ensemble stack',
  inActiveEnsemble: true,
  baseLearnerDependencies: []  // for meta-learners only
}
```

### Training Jobs - Job Object
```javascript
{
  id: 1,
  name: 'RF_v3.2_training',
  modelId: 1,
  modelName: 'Random Forest',
  datasetVersion: 'AAM-SLE-E v2.1',
  role: 'base',  // determines which stage
  status: 'running',  // or 'queued', 'completed', 'failed'
  progress: 67,
  currentEpoch: 67,
  totalEpochs: 100,
  accuracy: 87.3,  // live updating
  loss: 0.234,  // live updating
  gpuHoursConsumed: 2.1,
  runtime: '2h 14m',
  estimatedCompletion: '45 minutes',
  startedAt: '2024-03-28 14:23',
  dependencies: [],  // job IDs this job depends on
  dependenciesMet: true,
  errorMessage: null  // populated if failed
}
```

### Hyperparameter Tuning - Trial Object
```javascript
{
  id: 47,
  modelType: 'Random Forest',
  hyperparameters: {
    n_estimators: 200,
    max_depth: 12,
    min_samples_split: 5,
    max_features: 'sqrt'
  },
  accuracy: 91.2,
  precision: 92.1,
  recall: 90.3,
  f1Score: 91.2,
  duration: '1.2h',
  gpuHoursUsed: 1.2,
  datasetVersion: 'AAM-SLE-E v2.1',
  cvFolds: 5,
  timestamp: '2024-03-28 15:42',
  isBestTrial: true
}
```

---

## Implementation Priority

1. **Model Registry** - Foundation (version control, roles, ensemble viewer)
2. **Training Jobs** - Execution layer (two-stage DAG, dependencies)
3. **Hyperparameter Tuning** - Optimization layer (leaderboard, parallel coords)

Each page builds on the concepts from the previous, creating a cohesive researcher workflow.

---

## Next Steps

Ready to implement these designs systematically. Shall we start with the Model Registry redesign?
