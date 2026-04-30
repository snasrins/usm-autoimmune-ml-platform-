# 🔄 Complete Pipeline Integration Guide

**Date:** April 22, 2026  
**Purpose:** End-to-end workflow from data upload to clinical scorecard

---

## 📊 **TWO PIPELINES**

### **Pipeline A: UNSTRUCTURED DATA (PDF/Images → Qwen OCR)**
```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Upload PDF/Image → Qwen OCR Processing                       │
│    Page: DataIngestionPage                                      │
│    API: unstructuredPipelineAPI.uploadForOCR(file)             │
│    Result: validation_id, extracted_text                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Review OCR Extraction                                        │
│    Page: DataIngestionPage (OCR Preview Tab)                    │
│    API: unstructuredPipelineAPI.getOCRPreview(validation_id)   │
│    Result: Show extracted text, entities                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Convert OCR to Tabular Format                                │
│    Page: DataIngestionPage (Convert Button)                     │
│    API: unstructuredPipelineAPI.convertToTabular(validation_id)│
│    Result: session_id (goes to Preview)                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [Continue to Step 4 - Preview]
```

### **Pipeline B: STRUCTURED DATA (CSV/Excel)**
```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Upload CSV/Excel                                             │
│    Page: DataIngestionPage                                      │
│    API: structuredPipelineAPI.uploadForPreview(file, type)     │
│    Result: session_id, row_count, columns                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [Continue to Step 4 - Preview]
```

---

## 🔄 **SHARED PIPELINE (Both A & B merge here)**

```
┌─────────────────────────────────────────────────────────────────┐
│ 4. PREVIEW & EDIT DATA                                          │
│    Page: DataPreparationPage (Preview Tab)                      │
│    API: structuredPipelineAPI.getPreview(session_id, page)     │
│    Actions:                                                      │
│      - View data in table                                       │
│      - Edit cells: editCell(session_id, row_id, col, value)    │
│      - Delete rows: deleteRow(session_id, row_id)              │
│    Navigation: [Next: Preprocessing →]                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. DATA QUALITY CHECK                                           │
│    Page: DataPreparationPage (Quality Tab)                      │
│    API: preprocessingAPI.getQualityReport(session_id)          │
│    Shows:                                                        │
│      - Quality score                                            │
│      - Missing values %                                         │
│      - Outliers detected                                        │
│      - Duplicates count                                         │
│    Navigation: [Next: Apply Preprocessing →]                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. PREPROCESSING CONFIGURATION                                  │
│    Page: DataPreparationPage (Preprocessing Tab)                │
│    Configure:                                                    │
│      ☑ Missing Values: preprocessingAPI.handleMissingValues()  │
│        - Method: median/mean/mode/drop                          │
│      ☑ Duplicates: preprocessingAPI.removeDuplicates()         │
│      ☑ Outliers: preprocessingAPI.handleOutliers()             │
│        - Method: winsorize/remove                               │
│      ☑ Normalization: preprocessingAPI.normalizeData()         │
│        - Method: standard/minmax/robust                         │
│    Action: Apply all preprocessing steps                        │
│    Navigation: [Next: Save to Database →]                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. SAVE PREPROCESSED DATA                                       │
│    Page: DataPreparationPage (Save Button)                      │
│    API: preprocessingAPI.savePreprocessed(session_id, type)    │
│    Result: batch_id (UUID) - CRITICAL FOR NEXT STEPS           │
│    Storage: flexible_dataset_wide table                         │
│    Navigation: [Next: Label Assignment →]                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. LABEL ASSIGNMENT                                             │
│    Page: LabelAssignmentPage                                    │
│    Select batch_id from dropdown                                │
│    Actions:                                                      │
│      - View unlabeled: labelingAPI.getUnlabeledRecords(batch) │
│      - Assign single: labelingAPI.assignLabel(record, label)   │
│      - Bulk assign: labelingAPI.bulkAssignLabels(records)      │
│      - Batch assign: labelingAPI.batchAssignLabel(batch)       │
│      - Auto-label: labelingAPI.autoLabel(batch, source_col)    │
│    Check progress: labelingAPI.getLabelStatistics(batch_id)    │
│    Target: Get to 90%+ labeled                                  │
│    Navigation: [Next: ML Validation →]                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. ML VALIDATION                                                │
│    Page: LabelAssignmentPage (Validation Section)               │
│    API: mlPreparationAPI.validateForML(batch_id)               │
│    Checks:                                                       │
│      ✓ Sufficient samples (>100)                               │
│      ✓ Labeling coverage (>90%)                                │
│      ✓ Class distribution                                       │
│      ✓ Feature availability                                     │
│    Result: can_proceed: true/false                             │
│    Navigation: [If valid → ML Preparation →]                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 10. EXPLORATORY DATA ANALYSIS (Optional but Recommended)        │
│     Page: EDAExplorerPage                                       │
│     Select batch_id                                             │
│     APIs:                                                        │
│       - edaAPI.getStatisticalSummary(batch_id)                 │
│       - edaAPI.getCorrelationMatrix(batch_id)                  │
│       - edaAPI.getFeatureDistribution(batch_id, feature)       │
│       - edaAPI.getMissingDataHeatmap(batch_id)                 │
│       - edaAPI.generateInsights(batch_id)                      │
│     Purpose: Understand data before training                    │
│     Navigation: [Next: Training →]                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 11. ML DATASET PREPARATION                                      │
│     Page: TrainingJobsPage (Dataset Config Section)             │
│     API: mlPreparationAPI.prepareDataset(batch_id, config)     │
│     Configuration:                                               │
│       - Target column                                           │
│       - Test size (default: 0.2)                               │
│       - Imputation strategy                                     │
│       - Winsorization limits                                    │
│       - Composite features                                      │
│       - LASSO feature selection                                 │
│       - Scaling method                                          │
│     Result: dataset_id, metadata                                │
│     Navigation: [Next: Model Selection →]                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 12. MODEL TRAINING                                              │
│     Page: TrainingJobsPage                                      │
│     Step 12.1: Select Models                                    │
│       ☑ XGBoost, LightGBM, CatBoost                            │
│       ☑ Random Forest, AdaBoost                                │
│       ☑ Logistic Regression, SVM, KNN, MLP                     │
│                                                                 │
│     Step 12.2: Configure Hyperparameter Tuning                  │
│       - Method: Optuna (default)                               │
│       - N Trials: 50                                            │
│       - CV Folds: 5                                             │
│                                                                 │
│     Step 12.3: Train Models                                     │
│       API: trainingAPI.trainBaseModel(config) for each         │
│       Polling: trainingAPI.getJobStatus(job_id) every 3s       │
│                                                                 │
│     Step 12.4: Monitor Progress                                 │
│       - Show progress bars                                      │
│       - Display metrics as training completes                   │
│       - Update status: pending → training → completed           │
│                                                                 │
│     Navigation: [After all complete → Model Comparison →]       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 13. MODEL COMPARISON                                            │
│     Page: ModelComparisonPage                                   │
│     API: trainingAPI.compareModels([model_ids])                │
│     Shows:                                                       │
│       - Side-by-side metrics                                    │
│       - ROC curves overlay                                      │
│       - Confusion matrices                                      │
│       - Training time comparison                                │
│       - Winner recommendation                                   │
│     Select Best Model → model_id                                │
│     Navigation: [Next: Generate Scorecard →]                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 14. CLINICAL SCORECARD GENERATION (FINAL STEP)                  │
│     Page: ClinicalScorecardPage                                 │
│                                                                 │
│     Step 14.1: Select Model                                     │
│       - Choose best model from comparison                       │
│                                                                 │
│     Step 14.2: Configure Scorecard                              │
│       - Binning method: Rolling Mean (research-grade)          │
│       - Number of bins: 4                                       │
│       - Use Youden Index: ✓ (optimal threshold)                │
│                                                                 │
│     Step 14.3: Generate Scorecard                               │
│       API: scorecardAPI.generateScorecard(model_id, config)    │
│       Result: scorecard_id                                      │
│                                                                 │
│     Step 14.4: View Bin-Score Tables                            │
│       API: scorecardAPI.getBinScoreTables(scorecard_id)        │
│       Shows: Transparent lookup tables for each feature         │
│                                                                 │
│     Step 14.5: View Risk Stratification                         │
│       API: scorecardAPI.getRiskStratification(scorecard_id)    │
│       Shows: Threshold, sensitivity, specificity, Youden Index  │
│                                                                 │
│     Step 14.6: Patient Calculator                               │
│       Input: Patient lab values                                 │
│       API: scorecardAPI.calculatePatientScore(scorecard, data) │
│       Output: Total score, risk group, recommendation           │
│                                                                 │
│     Step 14.7: Export Reports                                   │
│       API: scorecardAPI.exportScorecardCSV(scorecard_id, type) │
│       Types: bin_tables, threshold_report, comprehensive        │
│                                                                 │
│     🎉 COMPLETE PIPELINE! 🎉                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔑 **CRITICAL STATE MANAGEMENT**

### **Session Storage Keys:**
```javascript
// After each step, store these in sessionStorage or Redux:

// Step 1-3: Unstructured
sessionStorage.setItem('ocr_validation_id', validationId);

// Step 1: Structured OR Step 3: Unstructured Convert
sessionStorage.setItem('preview_session_id', sessionId);

// Step 7: After Save
sessionStorage.setItem('current_batch_id', batchId);  // MOST IMPORTANT!

// Step 11: After Dataset Prep
sessionStorage.setItem('dataset_id', datasetId);

// Step 12: After Training
sessionStorage.setItem('trained_model_ids', JSON.stringify(modelIds));

// Step 13: After Comparison
sessionStorage.setItem('best_model_id', modelId);

// Step 14: After Scorecard
sessionStorage.setItem('scorecard_id', scorecardId);
```

---

## 🎯 **PAGE-BY-PAGE API WIRING**

### **DataIngestionPage.jsx**
```javascript
import { unstructuredPipelineAPI, structuredPipelineAPI } from '../services/api-complete';

// UNSTRUCTURED TAB
const handleUnstructuredUpload = async (file) => {
  setUploading(true);
  try {
    // Step 1: Upload for OCR
    const result = await unstructuredPipelineAPI.uploadForOCR(file);
    setValidationId(result.validation_id);
    setExtractedText(result.extracted_text);
    
    // Show OCR preview
    setActiveTab('ocr-preview');
  } catch (error) {
    setError('OCR processing failed');
  } finally {
    setUploading(false);
  }
};

const handleConvertToTabular = async () => {
  try {
    // Step 3: Convert OCR to table
    const result = await unstructuredPipelineAPI.convertToTabular(validationId);
    sessionStorage.setItem('preview_session_id', result.session_id);
    
    // Navigate to Data Preparation page
    navigate('/data-preparation');
  } catch (error) {
    setError('Conversion failed');
  }
};

// STRUCTURED TAB
const handleStructuredUpload = async (file) => {
  setUploading(true);
  try {
    // Step 1: Upload for preview
    const result = await structuredPipelineAPI.uploadForPreview(file, datasetType);
    sessionStorage.setItem('preview_session_id', result.session_id);
    
    // Navigate to Data Preparation page
    navigate('/data-preparation');
  } catch (error) {
    setError('Upload failed');
  } finally {
    setUploading(false);
  }
};
```

### **DataPreparationPage.jsx**
```javascript
import { structuredPipelineAPI, preprocessingAPI } from '../services/api-complete';

useEffect(() => {
  const sessionId = sessionStorage.getItem('preview_session_id');
  if (sessionId) {
    loadPreview(sessionId);
    loadQualityReport(sessionId);
  }
}, []);

const loadPreview = async (sessionId) => {
  const data = await structuredPipelineAPI.getPreview(sessionId, currentPage, 20);
  setPreviewData(data.rows);
  setTotalRows(data.total_rows);
};

const loadQualityReport = async (sessionId) => {
  const report = await preprocessingAPI.getQualityReport(sessionId);
  setQualityScore(report.quality_score);
  setIssues(report.issues);
};

const handleApplyPreprocessing = async () => {
  const sessionId = sessionStorage.getItem('preview_session_id');
  
  // Apply all preprocessing steps
  if (config.handleMissing) {
    await preprocessingAPI.handleMissingValues(sessionId, config.missingMethod);
  }
  if (config.removeDuplicates) {
    await preprocessingAPI.removeDuplicates(sessionId);
  }
  if (config.handleOutliers) {
    await preprocessingAPI.handleOutliers(sessionId, 'winsorize');
  }
  
  // Refresh preview
  await loadPreview(sessionId);
};

const handleSaveToDatabase = async () => {
  const sessionId = sessionStorage.getItem('preview_session_id');
  const result = await preprocessingAPI.savePreprocessed(sessionId, datasetType);
  
  // CRITICAL: Store batch_id for next steps
  sessionStorage.setItem('current_batch_id', result.batch_id);
  
  // Navigate to labeling
  navigate('/label-assignment');
};
```

### **LabelAssignmentPage.jsx**
```javascript
import { labelingAPI, mlPreparationAPI } from '../services/api-complete';

useEffect(() => {
  const batchId = sessionStorage.getItem('current_batch_id');
  if (batchId) {
    loadUnlabeledRecords(batchId);
    loadLabelStatistics(batchId);
  }
}, []);

const loadUnlabeledRecords = async (batchId) => {
  const data = await labelingAPI.getUnlabeledRecords(batchId, targetColumn);
  setUnlabeledRecords(data.records);
};

const handleAssignLabel = async (recordId, label) => {
  await labelingAPI.assignLabel(recordId, label, 1.0, null, targetColumn);
  await loadUnlabeledRecords(batchId);
  await loadLabelStatistics(batchId);
};

const handleBatchAssign = async (label) => {
  const batchId = sessionStorage.getItem('current_batch_id');
  await labelingAPI.batchAssignLabel(batchId, label, targetColumn);
  await loadLabelStatistics(batchId);
};

const handleValidateForML = async () => {
  const batchId = sessionStorage.getItem('current_batch_id');
  const validation = await mlPreparationAPI.validateForML(batchId, targetColumn);
  
  setValidationResult(validation);
  
  if (validation.can_proceed) {
    setShowProceedButton(true);
  }
};

const handleProceedToTraining = () => {
  navigate('/training-jobs');
};
```

### **TrainingJobsPage.jsx**
```javascript
import { mlPreparationAPI, trainingAPI } from '../services/api-complete';

useEffect(() => {
  const batchId = sessionStorage.getItem('current_batch_id');
  if (batchId) {
    setSelectedBatchId(batchId);
  }
}, []);

const handlePrepareDataset = async () => {
  const result = await mlPreparationAPI.prepareDataset(batchId, {
    targetColumn: config.targetColumn,
    testSize: config.testSize,
    applyImputation: true,
    applyWinsorization: true,
    applyCompositeFeatures: true,
    useLASSO: true,
    scalingStrategy: 'standard'
  });
  
  sessionStorage.setItem('dataset_id', result.dataset_id);
  setDatasetReady(true);
};

const handleTrainModels = async () => {
  const trainedModelIds = [];
  
  for (const algorithm of selectedAlgorithms) {
    const result = await trainingAPI.trainBaseModel({
      batchId: batchId,
      algorithm: algorithm,
      targetColumn: config.targetColumn,
      nTrials: config.nTrials,
      cvFolds: config.cvFolds
    });
    
    setActiveJobs(prev => [...prev, { jobId: result.job_id, algorithm }]);
    
    // Start polling
    pollJobStatus(result.job_id, algorithm);
  }
};

const pollJobStatus = async (jobId, algorithm) => {
  const interval = setInterval(async () => {
    const status = await trainingAPI.getJobStatus(jobId);
    
    updateJobStatus(jobId, status);
    
    if (status.status === 'completed') {
      clearInterval(interval);
      setCompletedModels(prev => [...prev, status.result.model_id]);
    }
  }, 3000);
};

const handleProceedToComparison = () => {
  sessionStorage.setItem('trained_model_ids', JSON.stringify(completedModels));
  navigate('/model-comparison');
};
```

### **ModelComparisonPage.jsx**
```javascript
import { trainingAPI } from '../services/api-complete';

useEffect(() => {
  const modelIds = JSON.parse(sessionStorage.getItem('trained_model_ids') || '[]');
  if (modelIds.length > 0) {
    loadComparison(modelIds);
  }
}, []);

const loadComparison = async (modelIds) => {
  const comparison = await trainingAPI.compareModels(modelIds);
  setComparisonData(comparison);
  
  // Auto-select best model
  const bestModelId = comparison.best_by_metric.accuracy;
  setBestModel(bestModelId);
  sessionStorage.setItem('best_model_id', bestModelId);
};

const handleGenerateScorecard = () => {
  navigate('/clinical-scorecard');
};
```

### **ClinicalScorecardPage.jsx**
```javascript
import { scorecardAPI } from '../services/api-complete';

useEffect(() => {
  const modelId = sessionStorage.getItem('best_model_id');
  if (modelId) {
    setSelectedModel(modelId);
  }
}, []);

const handleGenerateScorecard = async () => {
  setGenerating(true);
  try {
    const result = await scorecardAPI.generateScorecard(selectedModel, {
      binningMethod: 'rolling_mean',
      numBins: 4,
      useYouden: true
    });
    
    setScorecardId(result.scorecard_id);
    sessionStorage.setItem('scorecard_id', result.scorecard_id);
    
    // Load bin tables and stratification
    await loadBinTables(result.scorecard_id);
    await loadRiskStratification(result.scorecard_id);
    
    setScorecardGenerated(true);
  } finally {
    setGenerating(false);
  }
};

const loadBinTables = async (scorecardId) => {
  const tables = await scorecardAPI.getBinScoreTables(scorecardId);
  setBinTables(tables);
};

const loadRiskStratification = async (scorecardId) => {
  const stratification = await scorecardAPI.getRiskStratification(scorecardId);
  setThreshold(stratification.threshold);
  setSensitivity(stratification.sensitivity);
  setSpecificity(stratification.specificity);
};

const handleCalculatePatientScore = async () => {
  const score = await scorecardAPI.calculatePatientScore(scorecardId, patientData);
  setTotalScore(score.total_score);
  setRiskGroup(score.risk_group);
};

const handleExportCSV = async (exportType) => {
  const blob = await scorecardAPI.exportScorecardCSV(scorecardId, exportType);
  
  // Download file
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `scorecard_${exportType}.csv`;
  a.click();
};
```

---

## ✅ **VALIDATION CHECKLIST**

Before proceeding to next step, verify:

- [ ] **Step 1-3:** `preview_session_id` stored in sessionStorage
- [ ] **Step 7:** `current_batch_id` stored (UUID format)
- [ ] **Step 9:** Validation shows `can_proceed: true`
- [ ] **Step 11:** `dataset_id` stored
- [ ] **Step 12:** All training jobs show `status: 'completed'`
- [ ] **Step 13:** `best_model_id` stored
- [ ] **Step 14:** `scorecard_id` stored, bin tables loaded

---

## 🚀 **DEPLOYMENT NOTES**

1. **Error Handling:** Every API call should have try-catch
2. **Loading States:** Show spinners during async operations
3. **Navigation Guards:** Check required session data before rendering
4. **Polling Interval:** 3 seconds for training status
5. **File Download:** Use blob handling for CSV exports
6. **Session Cleanup:** Clear sessionStorage when starting new workflow

---

**🎯 This is your complete end-to-end integration!**
