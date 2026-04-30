# 🔧 Frontend Integration Implementation Steps

**Date:** April 22, 2026  
**Purpose:** Step-by-step guide to wire frontend to backend  
**Status:** Ready to implement

---

## 📦 **STEP 1: Import API Complete Module**

In each page file, replace mock data with real API calls:

### **Add to all pages:**
```javascript
// Add this import at the top of each page
import {
  unstructuredPipelineAPI,
  structuredPipelineAPI,
  preprocessingAPI,
  labelingAPI,
  mlPreparationAPI,
  edaAPI,
  trainingAPI,
  scorecardAPI,
  explainabilityAPI,
  batchPredictionAPI
} from '../services/api-complete';
```

---

## 🔄 **STEP 2: Replace Mock Data - Page by Page**

### **2.1 DataIngestionPage.jsx**

**Current state:** Using `MOCK_BATCHES` array

**Changes needed:**

```javascript
// REMOVE: const MOCK_BATCHES = [...]

// ADD: Real API state
const [batches, setBatches] = useState([]);
const [loading, setLoading] = useState(false);
const [uploading, setUploading] = useState(false);
const [error, setError] = useState(null);

// ADD: Load real batches on mount
useEffect(() => {
  loadRecentBatches();
}, []);

const loadRecentBatches = async () => {
  setLoading(true);
  try {
    // Use existing flexibleAPI from api.js
    const { flexibleAPI } = await import('../services/api');
    const response = await flexibleAPI.getRecentUploads(50, false, true);
    
    // Transform to match expected format
    const transformedBatches = response.uploads?.map(upload => ({
      id: upload.id,
      dataset: upload.file_name,
      user: 'Current User',  // Get from auth context
      fileType: upload.file_name?.split('.').pop().toUpperCase(),
      uploaded: upload.uploaded_at,
      records: upload.row_count || 0,
      status: upload.row_count > 0 ? 'ready' : 'processing'
    })) || [];
    
    setBatches(transformedBatches);
  } catch (err) {
    setError('Failed to load batches');
    console.error(err);
  } finally {
    setLoading(false);
  }
};

// CHANGE: Handle structured upload
const handleStructuredUpload = async (file) => {
  setUploading(true);
  setError(null);
  try {
    const result = await structuredPipelineAPI.uploadForPreview(file, datasetType);
    
    // Store session ID for next step
    sessionStorage.setItem('preview_session_id', result.session_id);
    sessionStorage.setItem('workflow_stage', 'preview');
    
    // Show success and navigate
    alert(`Upload successful! ${result.row_count} rows loaded.`);
    navigate('/data-preparation');
  } catch (err) {
    setError(err.response?.data?.detail || 'Upload failed');
  } finally {
    setUploading(false);
  }
};

// CHANGE: Handle unstructured upload (Qwen OCR)
const handleUnstructuredUpload = async (file) => {
  setUploading(true);
  setError(null);
  try {
    const result = await unstructuredPipelineAPI.uploadForOCR(file);
    
    // Store validation ID
    sessionStorage.setItem('ocr_validation_id', result.validation_id);
    
    // Show OCR preview
    setOCRPreview({
      validationId: result.validation_id,
      extractedText: result.extracted_text,
      pageCount: result.page_count
    });
    
    setActiveTab('ocr-preview');
  } catch (err) {
    setError(err.response?.data?.detail || 'OCR processing failed');
  } finally {
    setUploading(false);
  }
};

// ADD: Convert OCR to tabular
const handleConvertToTabular = async () => {
  setUploading(true);
  try {
    const validationId = sessionStorage.getItem('ocr_validation_id');
    const result = await unstructuredPipelineAPI.convertToTabular(validationId);
    
    sessionStorage.setItem('preview_session_id', result.session_id);
    sessionStorage.setItem('workflow_stage', 'preview');
    
    navigate('/data-preparation');
  } catch (err) {
    setError('Conversion failed');
  } finally {
    setUploading(false);
  }
};
```

---

### **2.2 DataPreparationPage.jsx** (formerly DataQualityWorkbenchPage.jsx)

**Changes needed:**

```javascript
const [sessionId, setSessionId] = useState(null);
const [previewData, setPreviewData] = useState({ rows: [], total_rows: 0 });
const [qualityReport, setQualityReport] = useState(null);
const [currentPage, setCurrentPage] = useState(1);
const [preprocessing, setPreprocessing] = useState(false);

useEffect(() => {
  const savedSessionId = sessionStorage.getItem('preview_session_id');
  if (savedSessionId) {
    setSessionId(savedSessionId);
    loadPreview(savedSessionId);
    loadQualityReport(savedSessionId);
  }
}, []);

const loadPreview = async (sessionId, page = 1) => {
  try {
    const data = await structuredPipelineAPI.getPreview(sessionId, page, 20);
    setPreviewData(data);
  } catch (err) {
    setError('Failed to load preview');
  }
};

const loadQualityReport = async (sessionId) => {
  try {
    const report = await preprocessingAPI.getQualityReport(sessionId);
    setQualityReport(report);
  } catch (err) {
    console.error('Quality report error:', err);
  }
};

const handleEditCell = async (stagingId, columnName, newValue) => {
  try {
    await structuredPipelineAPI.editCell(sessionId, stagingId, columnName, newValue);
    await loadPreview(sessionId, currentPage);
  } catch (err) {
    setError('Failed to edit cell');
  }
};

const handleApplyPreprocessing = async () => {
  setPreprocessing(true);
  try {
    // Apply selected preprocessing steps
    if (config.handleMissing) {
      await preprocessingAPI.handleMissingValues(sessionId, config.missingMethod, 0.5);
    }
    
    if (config.removeDuplicates) {
      await preprocessingAPI.removeDuplicates(sessionId, true);
    }
    
    if (config.handleOutliers) {
      await preprocessingAPI.handleOutliers(sessionId, 'winsorize', 3.0);
    }
    
    if (config.normalize) {
      await preprocessingAPI.normalizeData(sessionId, config.normalizeMethod);
    }
    
    // Reload preview to show changes
    await loadPreview(sessionId, currentPage);
    await loadQualityReport(sessionId);
    
    alert('Preprocessing applied successfully!');
  } catch (err) {
    setError('Preprocessing failed');
  } finally {
    setPreprocessing(false);
  }
};

const handleSaveToDatabase = async () => {
  try {
    const result = await preprocessingAPI.savePreprocessed(
      sessionId,
      datasetType,
      'Manual Upload'
    );
    
    // CRITICAL: Store batch ID for next steps
    sessionStorage.setItem('current_batch_id', result.batch_id);
    sessionStorage.setItem('workflow_stage', 'labeling');
    
    alert(`Data saved! Batch ID: ${result.batch_id}`);
    navigate('/label-assignment');
  } catch (err) {
    setError('Failed to save data');
  }
};
```

---

### **2.3 LabelAssignmentPage.jsx**

**Changes needed:**

```javascript
const [batchId, setBatchId] = useState(null);
const [unlabeledRecords, setUnlabeledRecords] = useState([]);
const [labelStats, setLabelStats] = useState(null);
const [validationResult, setValidationResult] = useState(null);
const [targetColumn, setTargetColumn] = useState('labels_disease_classification');

useEffect(() => {
  const savedBatchId = sessionStorage.getItem('current_batch_id');
  if (savedBatchId) {
    setBatchId(savedBatchId);
    loadUnlabeledRecords(savedBatchId);
    loadLabelStatistics(savedBatchId);
  }
}, []);

const loadUnlabeledRecords = async (batchId) => {
  try {
    const data = await labelingAPI.getUnlabeledRecords(batchId, targetColumn, 100);
    setUnlabeledRecords(data.records || []);
  } catch (err) {
    console.error('Failed to load unlabeled records:', err);
  }
};

const loadLabelStatistics = async (batchId) => {
  try {
    const stats = await labelingAPI.getLabelStatistics(batchId, targetColumn);
    setLabelStats(stats);
  } catch (err) {
    console.error('Failed to load label statistics:', err);
  }
};

const handleAssignLabel = async (recordId, label) => {
  try {
    await labelingAPI.assignLabel(recordId, label, 1.0, null, targetColumn);
    
    // Refresh data
    await loadUnlabeledRecords(batchId);
    await loadLabelStatistics(batchId);
  } catch (err) {
    setError('Failed to assign label');
  }
};

const handleBulkAssign = async (recordIds, label) => {
  try {
    await labelingAPI.bulkAssignLabels(recordIds, label, 1.0, targetColumn);
    
    await loadUnlabeledRecords(batchId);
    await loadLabelStatistics(batchId);
  } catch (err) {
    setError('Bulk assignment failed');
  }
};

const handleBatchAssign = async (label) => {
  if (!confirm(`Assign "${label}" to entire batch?`)) return;
  
  try {
    await labelingAPI.batchAssignLabel(batchId, label, targetColumn);
    
    await loadUnlabeledRecords(batchId);
    await loadLabelStatistics(batchId);
    
    alert('Batch labeled successfully!');
  } catch (err) {
    setError('Batch assignment failed');
  }
};

const handleValidateForML = async () => {
  try {
    const validation = await mlPreparationAPI.validateForML(batchId, targetColumn, 100);
    setValidationResult(validation);
    
    if (validation.can_proceed) {
      alert('Validation passed! Ready for ML training.');
    } else {
      alert('Validation failed. Please address the issues shown.');
    }
  } catch (err) {
    setError('Validation failed');
  }
};

const handleProceedToTraining = () => {
  if (validationResult?.can_proceed) {
    sessionStorage.setItem('workflow_stage', 'training');
    navigate('/training-jobs');
  }
};
```

---

### **2.4 TrainingJobsPage.jsx**

**Changes needed:**

```javascript
const [batchId, setBatchId] = useState(null);
const [datasetPrepared, setDatasetPrepared] = useState(false);
const [datasetId, setDatasetId] = useState(null);
const [selectedAlgorithms, setSelectedAlgorithms] = useState([]);
const [activeJobs, setActiveJobs] = useState([]);
const [completedModels, setCompletedModels] = useState([]);
const [config, setConfig] = useState({
  targetColumn: 'labels_disease_classification',
  testSize: 0.2,
  nTrials: 50,
  cvFolds: 5
});

useEffect(() => {
  const savedBatchId = sessionStorage.getItem('current_batch_id');
  if (savedBatchId) {
    setBatchId(savedBatchId);
  }
}, []);

const handlePrepareDataset = async () => {
  setPreparingDataset(true);
  try {
    const result = await mlPreparationAPI.prepareDataset(batchId, {
      targetColumn: config.targetColumn,
      testSize: config.testSize,
      randomState: 42,
      applyImputation: true,
      imputationNumericStrategy: 'median',
      applyWinsorization: true,
      winsorize_limits: [0.01, 0.01],
      applyCompositeFeatures: true,
      compositeLowPercentile: 10.0,
      compositeHighPercentile: 70.0,
      useLASSO: true,
      lassoAlpha: 0.01,
      scalingStrategy: 'standard',
      createSeparateSets: true
    });
    
    setDatasetId(result.dataset_id);
    sessionStorage.setItem('dataset_id', result.dataset_id);
    setDatasetPrepared(true);
    
    alert('Dataset prepared successfully!');
  } catch (err) {
    setError('Dataset preparation failed');
  } finally {
    setPreparingDataset(false);
  }
};

const handleStartTraining = async () => {
  if (selectedAlgorithms.length === 0) {
    alert('Please select at least one algorithm');
    return;
  }
  
  const modelIds = [];
  
  for (const algorithm of selectedAlgorithms) {
    try {
      const result = await trainingAPI.trainBaseModel({
        batchId: batchId,
        algorithm: algorithm,
        targetColumn: config.targetColumn,
        testSize: config.testSize,
        randomState: 42,
        tuningMethod: 'optuna',
        nTrials: config.nTrials,
        cvFolds: config.cvFolds
      });
      
      const jobInfo = {
        jobId: result.job_id,
        algorithm: algorithm,
        status: 'pending',
        progress: 0
      };
      
      setActiveJobs(prev => [...prev, jobInfo]);
      
      // Start polling this job
      pollJobStatus(result.job_id, algorithm);
      
    } catch (err) {
      console.error(`Failed to start training for ${algorithm}:`, err);
    }
  }
};

const pollJobStatus = (jobId, algorithm) => {
  const interval = setInterval(async () => {
    try {
      const status = await trainingAPI.getJobStatus(jobId);
      
      // Update job status in UI
      setActiveJobs(prev => prev.map(job => 
        job.jobId === jobId 
          ? { ...job, status: status.status, progress: status.progress?.percentage || 0 }
          : job
      ));
      
      if (status.status === 'completed') {
        clearInterval(interval);
        
        // Add to completed models
        setCompletedModels(prev => [...prev, status.result.model_id]);
        sessionStorage.setItem('trained_model_ids', JSON.stringify([...completedModels, status.result.model_id]));
      } else if (status.status === 'failed') {
        clearInterval(interval);
        console.error(`Training failed for ${algorithm}`);
      }
    } catch (err) {
      console.error('Polling error:', err);
    }
  }, 3000); // Poll every 3 seconds
};

const handleProceedToComparison = () => {
  if (completedModels.length === 0) {
    alert('No models completed yet');
    return;
  }
  
  navigate('/model-comparison');
};
```

---

### **2.5 ModelComparisonPage.jsx**

**Changes needed:**

```javascript
const [modelIds, setModelIds] = useState([]);
const [comparisonData, setComparisonData] = useState(null);
const [bestModel, setBestModel] = useState(null);

useEffect(() => {
  const savedModelIds = JSON.parse(sessionStorage.getItem('trained_model_ids') || '[]');
  if (savedModelIds.length > 0) {
    setModelIds(savedModelIds);
    loadComparison(savedModelIds);
  }
}, []);

const loadComparison = async (modelIds) => {
  setLoading(true);
  try {
    const comparison = await trainingAPI.compareModels(modelIds);
    setComparisonData(comparison);
    
    // Determine best model
    const bestModelId = comparison.best_by_metric?.accuracy || modelIds[0];
    setBestModel(bestModelId);
    sessionStorage.setItem('best_model_id', bestModelId);
  } catch (err) {
    setError('Failed to load comparison');
  } finally {
    setLoading(false);
  }
};

const handleGenerateScorecard = () => {
  if (!bestModel) {
    alert('Please select a model first');
    return;
  }
  
  sessionStorage.setItem('workflow_stage', 'scorecard');
  navigate('/clinical-scorecard');
};
```

---

### **2.6 ClinicalScorecardPage.jsx**

**Changes needed:**

```javascript
const [modelId, setModelId] = useState(null);
const [scorecardId, setScorecardId] = useState(null);
const [binTables, setBinTables] = useState([]);
const [riskStratification, setRiskStratification] = useState(null);
const [generating, setGenerating] = useState(false);
const [config, setConfig] = useState({
  binningMethod: 'rolling_mean',
  numBins: 4,
  useYouden: true
});

useEffect(() => {
  const savedModelId = sessionStorage.getItem('best_model_id');
  if (savedModelId) {
    setModelId(savedModelId);
  }
}, []);

const handleGenerateScorecard = async () => {
  setGenerating(true);
  try {
    const result = await scorecardAPI.generateScorecard(modelId, config);
    
    setScorecardId(result.scorecard_id);
    sessionStorage.setItem('scorecard_id', result.scorecard_id);
    
    // Load bin tables and stratification
    await loadBinTables(result.scorecard_id);
    await loadRiskStratification(result.scorecard_id);
    
    alert('Scorecard generated successfully!');
  } catch (err) {
    setError('Scorecard generation failed');
  } finally {
    setGenerating(false);
  }
};

const loadBinTables = async (scorecardId) => {
  try {
    const tables = await scorecardAPI.getBinScoreTables(scorecardId);
    setBinTables(tables);
  } catch (err) {
    console.error('Failed to load bin tables:', err);
  }
};

const loadRiskStratification = async (scorecardId) => {
  try {
    const stratification = await scorecardAPI.getRiskStratification(scorecardId);
    setRiskStratification(stratification);
  } catch (err) {
    console.error('Failed to load risk stratification:', err);
  }
};

const handleCalculatePatientScore = async () => {
  try {
    const score = await scorecardAPI.calculatePatientScore(scorecardId, patientData);
    
    setCalculatedScore({
      totalScore: score.total_score,
      riskGroup: score.risk_group,
      featureScores: score.feature_scores
    });
  } catch (err) {
    setError('Score calculation failed');
  }
};

const handleExportCSV = async (exportType) => {
  try {
    const blob = await scorecardAPI.exportScorecardCSV(scorecardId, exportType);
    
    // Trigger download
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scorecard_${exportType}_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (err) {
    setError('Export failed');
  }
};
```

---

## ⚠️ **STEP 3: Add Error Handling Component**

Create `frontend/src/components/ApiErrorBoundary.jsx`:

```javascript
import { AlertTriangle, RefreshCw } from 'lucide-react';

export const ErrorDisplay = ({ error, onRetry }) => {
  if (!error) return null;
  
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4">
      <div className="flex items-center gap-3">
        <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-red-900">Error</h3>
          <p className="text-sm text-red-700 mt-1">{error}</p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export const LoadingSpinner = ({ message = 'Loading...' }) => (
  <div className="flex items-center justify-center py-12">
    <div className="flex items-center gap-3">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      <span className="text-gray-600">{message}</span>
    </div>
  </div>
);
```

---

## ✅ **STEP 4: Testing Checklist**

Test each page in order:

### **4.1 Data Ingestion**
- [ ] Upload CSV → Check `preview_session_id` in sessionStorage
- [ ] Upload PDF → Check OCR extraction works
- [ ] Convert OCR → Check navigates to Data Preparation

### **4.2 Data Preparation**
- [ ] Preview loads from session ID
- [ ] Edit cell updates data
- [ ] Preprocessing applies changes
- [ ] Save creates `current_batch_id`

### **4.3 Label Assignment**
- [ ] Loads unlabeled records from batch
- [ ] Single label assignment works
- [ ] Bulk/batch labeling works
- [ ] Validation shows correct status

### **4.4 Training Jobs**
- [ ] Dataset preparation succeeds
- [ ] Model training starts
- [ ] Polling updates progress
- [ ] Completed models stored

### **4.5 Model Comparison**
- [ ] Loads trained models
- [ ] Shows comparison metrics
- [ ] Selects best model

### **4.6 Clinical Scorecard**
- [ ] Generates scorecard
- [ ] Loads bin tables
- [ ] Calculates patient scores
- [ ] CSV export downloads

---

## 🚀 **STEP 5: Deployment**

1. Update `vite.config.js` proxy to point to backend:
```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://100.106.132.15:8001',
        changeOrigin: true
      }
    }
  }
});
```

2. Build for production:
```bash
npm run build
```

3. Test on staging environment

4. Deploy to production

---

**🎯 Follow these steps in order, testing each page before moving to the next!**
