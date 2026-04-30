# 🔧 Complete Backend Integration Guide

**Quick Reference:** How to wire each page with backend APIs

---

## 📦 Step 1: Import API Services

Add this to the top of each page file:

```javascript
// For Clinical Scorecard Page
import { scorecardAPI } from '../services/api-extensions';

// For Data Quality Page
import { dataQualityAPI } from '../services/api-extensions';

// For EDA Page
import { edaAPI } from '../services/api-extensions';

// For Model Explainability Page
import { explainabilityAPI } from '../services/api-extensions';

// For Model Comparison Page
import { modelComparisonAPI } from '../services/api-extensions';

// For Batch Prediction Page
import { batchPredictionAPI } from '../services/api-extensions';

// For Training Jobs Page
import { trainingAPI } from '../services/api-extensions';

// For Label Assignment Page
import { labelingAPI } from '../services/api-extensions';
```

---

## 1️⃣ Clinical Scorecard Page (`ClinicalScorecardPage.jsx`)

### Current State: 100% Mock Data
### Target: Wire to `/scorecard/*` endpoints

### Changes Needed:

```javascript
import { useState, useEffect } from 'react';
import { scorecardAPI } from '../services/api-extensions';
import { trainingAPI } from '../services/api-extensions';

export default function ClinicalScorecardPage() {
  // Add state for real data
  const [models, setModels] = useState([]);
  const [selectedModelId, setSelectedModelId] = useState('');
  const [scorecardData, setScorecardData] = useState(null);
  const [binScoreTables, setBinScoreTables] = useState(null);
  const [riskStratification, setRiskStratification] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Load available models
  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const result = await trainingAPI.listModels({ limit: 50 });
      setModels(result.models || []);
      if (result.models?.length > 0) {
        setSelectedModelId(result.models[0].model_id);
      }
    } catch (err) {
      setError('Failed to load models: ' + err.message);
    }
  };

  // Generate scorecard
  const handleGenerate = async () => {
    if (!selectedModelId) {
      setError('Please select a model first');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Step 1: Generate scorecard
      const config = {
        binningMethod: binningMethod,
        numBins: numBins,
        useYouden: useYouden
      };
      
      const scorecardResult = await scorecardAPI.generateScorecard(selectedModelId, config);
      setScorecardData(scorecardResult);

      // Step 2: Get bin-score tables
      const binTables = await scorecardAPI.getBinScoreTables(scorecardResult.scorecard_id);
      setBinScoreTables(binTables);

      // Step 3: Get risk stratification
      const riskStrat = await scorecardAPI.getRiskStratification(scorecardResult.scorecard_id);
      setRiskStratification(riskStrat);

      setScorecardGenerated(true);
    } catch (err) {
      setError('Failed to generate scorecard: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  // Calculate patient score
  const handleCalculateScore = async () => {
    if (!scorecardData) {
      setError('Please generate scorecard first');
      return;
    }

    try {
      const patientData = {
        NK: parseFloat(manualInputs.NK),
        C4: parseFloat(manualInputs.C4),
        IgM: parseFloat(manualInputs.IgM),
        ALB: parseFloat(manualInputs.ALB),
        CRP: parseFloat(manualInputs.CRP),
        Pancytopenia: manualInputs.Pancytopenia === 'Yes' ? 1 : 0
      };

      const result = await scorecardAPI.calculatePatientScore(
        scorecardData.scorecard_id,
        patientData
      );

      setCalculatedScore(result.total_score);
      setRiskDecision(result.risk_level);
    } catch (err) {
      setError('Failed to calculate score: ' + err.message);
    }
  };

  // Export scorecard
  const handleExport = async (exportType) => {
    if (!scorecardData) {
      setError('No scorecard to export');
      return;
    }

    try {
      const blob = await scorecardAPI.exportScorecardCSV(scorecardData.scorecard_id, exportType);
      
      // Download file
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scorecard_${exportType}_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Failed to export: ' + err.message);
    }
  };

  // Rest of component...
}
```

### Replace Mock Data:
- Replace `MOCK_BATCHES` with `binScoreTables` from API
- Replace `SCORE_DISTRIBUTION` with `riskStratification` from API
- Replace hardcoded model name with dropdown of real models

---

## 2️⃣ Data Quality Workbench Page (`DataQualityWorkbenchPage.jsx`)

### Current State: 100% Mock Data
### Target: Wire to `/data-quality/*` endpoints

### Changes Needed:

```javascript
import { useState, useEffect } from 'react';
import { dataQualityAPI } from '../services/api-extensions';
import { dataIngestionAPI } from '../services/api-ingestion';

export default function DataQualityWorkbenchPage() {
  const [batches, setBatches] = useState([]);
  const [selectedBatchId, setSelectedBatchId] = useState('');
  const [qualityReport, setQualityReport] = useState(null);
  const [processedPreview, setProcessedPreview] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Load batches
  useEffect(() => {
    loadBatches();
  }, []);

  const loadBatches = async () => {
    try {
      const result = await dataIngestionAPI.getRecentUploads(50);
      setBatches(result.uploads || []);
      if (result.uploads?.length > 0) {
        setSelectedBatchId(result.uploads[0].batch_id);
      }
    } catch (err) {
      console.error('Failed to load batches:', err);
    }
  };

  // Load quality report
  useEffect(() => {
    if (selectedBatchId) {
      loadQualityReport();
    }
  }, [selectedBatchId]);

  const loadQualityReport = async () => {
    setIsLoading(true);
    try {
      const report = await dataQualityAPI.getQualityReport(selectedBatchId);
      setQualityReport(report);
    } catch (err) {
      setError('Failed to load quality report: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Apply preprocessing
  const handleApplyPreprocessing = async () => {
    if (!selectedBatchId) {
      setError('Please select a batch first');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const config = {
        applyImputation: true,
        missingStrategy: missingStrategy,  // 'median', 'mean', 'mode'
        categoricalStrategy: 'mode',
        
        applyWinsorization: outlierStrategy === 'winsorize',
        winsorizePercentiles: [0.01, 0.01],
        
        enableComposite: enableComposite,
        lowPercentile: lowPercentile,
        highPercentile: highPercentile,
        
        enableStandardization: enableStandardization,
        scalingMethod: scalingMethod  // 'standard', 'minmax', 'robust'
      };

      const result = await dataQualityAPI.applyPreprocessing(selectedBatchId, config);
      
      // Load preview of processed data
      const preview = await dataQualityAPI.getProcessedPreview(selectedBatchId, 20);
      setProcessedPreview(preview);

      setMessage('Preprocessing applied successfully!');
    } catch (err) {
      setError('Failed to apply preprocessing: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  // Export quality report
  const handleExport = async (format) => {
    try {
      const blob = await dataQualityAPI.exportQualityReport(selectedBatchId, format);
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `quality_report_${selectedBatchId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Failed to export: ' + err.message);
    }
  };

  // Rest of component...
}
```

---

## 3️⃣ Model Explainability Page (`ModelExplainabilityPage.jsx`)

### Current State: Has mock data
### Target: Wire to `/explainability/*` endpoints

### Changes Needed:

```javascript
import { useState, useEffect } from 'react';
import { explainabilityAPI } from '../services/api-extensions';
import { trainingAPI } from '../services/api-extensions';

export default function ModelExplainabilityPage() {
  const [models, setModels] = useState([]);
  const [selectedModelId, setSelectedModelId] = useState('');
  const [shapValues, setShapValues] = useState(null);
  const [llmExplanation, setLLMExplanation] = useState('');
  const [globalImportance, setGlobalImportance] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Load models
  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const result = await trainingAPI.listModels({ limit: 50 });
      setModels(result.models || []);
      if (result.models?.length > 0) {
        setSelectedModelId(result.models[0].model_id);
        loadGlobalImportance(result.models[0].model_id);
      }
    } catch (err) {
      console.error('Failed to load models:', err);
    }
  };

  // Load global feature importance
  const loadGlobalImportance = async (modelId) => {
    try {
      const result = await explainabilityAPI.getGlobalFeatureImportance(modelId);
      setGlobalImportance(result);
    } catch (err) {
      console.error('Failed to load global importance:', err);
    }
  };

  // Get SHAP explanation for patient
  const handleExplainPrediction = async () => {
    if (!selectedModelId) {
      setError('Please select a model first');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Collect patient data from form
      const patientData = {
        NK: parseFloat(patientInputs.NK),
        C4: parseFloat(patientInputs.C4),
        CRP: parseFloat(patientInputs.CRP),
        ESR: parseFloat(patientInputs.ESR),
        // ... other features
      };

      // Get SHAP values
      const shapResult = await explainabilityAPI.getSHAPValues(selectedModelId, patientData);
      setShapValues(shapResult);

      // Get LLM explanation
      const llmResult = await explainabilityAPI.generateLLMExplanation(
        selectedModelId,
        patientData,
        detailLevel  // 'brief', 'moderate', 'detailed'
      );
      setLLMExplanation(llmResult.explanation);

    } catch (err) {
      setError('Failed to explain prediction: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  // Batch SHAP analysis
  const handleBatchAnalysis = async (file) => {
    setIsLoading(true);
    try {
      const result = await explainabilityAPI.batchSHAPAnalysis(selectedModelId, file);
      setBatchResults(result);
    } catch (err) {
      setError('Batch analysis failed: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Rest of component...
}
```

---

## 4️⃣ Model Comparison Page (`ModelComparisonPage.jsx`)

### Changes Needed:

```javascript
import { useState, useEffect } from 'react';
import { modelComparisonAPI, trainingAPI } from '../services/api-extensions';

export default function ModelComparisonPage() {
  const [models, setModels] = useState([]);
  const [selectedModelIds, setSelectedModelIds] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [rocCurves, setRocCurves] = useState(null);
  const [confusionMatrices, setConfusionMatrices] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Load models
  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const result = await trainingAPI.listModels({ limit: 50 });
      setModels(result.models || []);
    } catch (err) {
      console.error('Failed to load models:', err);
    }
  };

  // Compare models
  const handleCompare = async () => {
    if (selectedModelIds.length < 2) {
      setError('Please select at least 2 models to compare');
      return;
    }

    if (selectedModelIds.length > 4) {
      setError('Maximum 4 models can be compared');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Get comparison data
      const comparison = await modelComparisonAPI.compareModels(selectedModelIds);
      setComparisonData(comparison);

      // Get ROC curves
      const roc = await modelComparisonAPI.getROCCurves(selectedModelIds);
      setRocCurves(roc);

      // Get confusion matrices
      const cm = await modelComparisonAPI.getConfusionMatrices(selectedModelIds);
      setConfusionMatrices(cm);

    } catch (err) {
      setError('Comparison failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  // Export comparison
  const handleExport = async (format) => {
    try {
      const blob = await modelComparisonAPI.exportComparison(selectedModelIds, format);
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `model_comparison.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Export failed: ' + err.message);
    }
  };

  // Rest of component...
}
```

---

## 5️⃣ Batch Prediction Page (`BatchPredictionPage.jsx`)

### Changes Needed:

```javascript
import { useState, useEffect } from 'react';
import { batchPredictionAPI, trainingAPI } from '../services/api-extensions';

export default function BatchPredictionPage() {
  const [models, setModels] = useState([]);
  const [selectedModelId, setSelectedModelId] = useState('');
  const [file, setFile] = useState(null);
  const [predictionResults, setPredictionResults] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');

  // Load models
  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const result = await trainingAPI.listModels({ limit: 50 });
      setModels(result.models || []);
      if (result.models?.length > 0) {
        setSelectedModelId(result.models[0].model_id);
      }
    } catch (err) {
      console.error('Failed to load models:', err);
    }
  };

  // Upload and predict
  const handleUploadAndPredict = async () => {
    if (!file) {
      setError('Please select a CSV file');
      return;
    }

    if (!selectedModelId) {
      setError('Please select a model');
      return;
    }

    setIsProcessing(true);
    setError('');

    try {
      const options = {
        includeSHAP: includeSHAP,
        includeConfidence: true
      };

      const result = await batchPredictionAPI.uploadPatientsForPrediction(
        selectedModelId,
        file,
        options
      );

      setPredictionResults(result);
      setMessage(`Processed ${result.total_patients} patients successfully`);

    } catch (err) {
      setError('Prediction failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsProcessing(false);
    }
  };

  // Export results
  const handleExport = async (format) => {
    if (!predictionResults?.prediction_job_id) {
      setError('No results to export');
      return;
    }

    try {
      const blob = await batchPredictionAPI.exportPredictions(
        predictionResults.prediction_job_id,
        format
      );

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `predictions.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Export failed: ' + err.message);
    }
  };

  // Rest of component...
}
```

---

## 6️⃣ EDA Workbench Page (`EDAWorkbenchPage.jsx`)

### Changes Needed:

```javascript
import { useState, useEffect } from 'react';
import { edaAPI } from '../services/api-extensions';
import { dataIngestionAPI } from '../services/api-ingestion';

export default function EDAWorkbenchPage() {
  const [batches, setBatches] = useState([]);
  const [selectedBatchId, setSelectedBatchId] = useState('');
  const [statisticalSummary, setStatisticalSummary] = useState(null);
  const [correlationMatrix, setCorrelationMatrix] = useState(null);
  const [featureDistributions, setFeatureDistributions] = useState(null);
  const [missingDataHeatmap, setMissingDataHeatmap] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Load batches
  useEffect(() => {
    loadBatches();
  }, []);

  const loadBatches = async () => {
    try {
      const result = await dataIngestionAPI.getRecentUploads(50);
      setBatches(result.uploads || []);
      if (result.uploads?.length > 0) {
        setSelectedBatchId(result.uploads[0].batch_id);
      }
    } catch (err) {
      console.error('Failed to load batches:', err);
    }
  };

  // Load EDA data
  useEffect(() => {
    if (selectedBatchId) {
      loadEDAData();
    }
  }, [selectedBatchId]);

  const loadEDAData = async () => {
    setIsLoading(true);
    try {
      // Load statistical summary
      const summary = await edaAPI.getStatisticalSummary(selectedBatchId);
      setStatisticalSummary(summary);

      // Load correlation matrix
      const correlation = await edaAPI.getCorrelationMatrix(selectedBatchId, 'pearson');
      setCorrelationMatrix(correlation);

      // Load missing data heatmap
      const missingData = await edaAPI.getMissingDataHeatmap(selectedBatchId);
      setMissingDataHeatmap(missingData);

    } catch (err) {
      setError('Failed to load EDA data: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  // Load feature distribution
  const loadFeatureDistribution = async (featureName) => {
    try {
      const distribution = await edaAPI.getFeatureDistribution(selectedBatchId, featureName);
      setFeatureDistributions(prev => ({
        ...prev,
        [featureName]: distribution
      }));
    } catch (err) {
      console.error('Failed to load distribution:', err);
    }
  };

  // Generate insights
  const handleGenerateInsights = async () => {
    setIsLoading(true);
    try {
      const insights = await edaAPI.generateInsights(selectedBatchId);
      setAutoInsights(insights);
    } catch (err) {
      setError('Failed to generate insights: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Rest of component...
}
```

---

## 7️⃣ Training Jobs Page (`TrainingJobsPage.jsx`)

### Enhancement for Better Status Polling:

```javascript
import { useState, useEffect } from 'react';
import { trainingAPI } from '../services/api-extensions';
import { dataIngestionAPI } from '../services/api-ingestion';

export default function TrainingJobsPage() {
  const [batches, setBatches] = useState([]);
  const [selectedBatchId, setSelectedBatchId] = useState('');
  const [trainingJobs, setTrainingJobs] = useState([]);
  const [activeJobId, setActiveJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [isTraining, setIsTraining] = useState(false);
  const [error, setError] = useState('');

  // Load batches
  useEffect(() => {
    loadBatches();
    loadTrainingHistory();
  }, []);

  const loadBatches = async () => {
    try {
      const result = await dataIngestionAPI.getRecentUploads(50);
      setBatches(result.uploads || []);
    } catch (err) {
      console.error('Failed to load batches:', err);
    }
  };

  const loadTrainingHistory = async () => {
    try {
      const result = await trainingAPI.getTrainingHistory(50);
      setTrainingJobs(result.jobs || []);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  // Start training
  const handleStartTraining = async () => {
    if (!selectedBatchId) {
      setError('Please select a batch');
      return;
    }

    setIsTraining(true);
    setError('');

    try {
      const config = {
        targetColumn: targetColumn,
        algorithms: selectedAlgorithms,  // ['xgboost', 'lightgbm', etc.]
        testSize: testSize,
        nTrials: nTrials,
        cvFolds: cvFolds
      };

      const result = await trainingAPI.trainFullPipeline(selectedBatchId, config);
      setActiveJobId(result.job_id);

      // Start polling for status
      startStatusPolling(result.job_id);

    } catch (err) {
      setError('Training failed: ' + (err.response?.data?.detail || err.message));
      setIsTraining(false);
    }
  };

  // Poll job status
  const startStatusPolling = (jobId) => {
    const interval = setInterval(async () => {
      try {
        const status = await trainingAPI.getJobStatus(jobId);
        setJobStatus(status);

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval);
          setIsTraining(false);
          loadTrainingHistory();  // Refresh history
        }
      } catch (err) {
        console.error('Status poll failed:', err);
        clearInterval(interval);
        setIsTraining(false);
      }
    }, 3000);  // Poll every 3 seconds

    return () => clearInterval(interval);
  };

  // Rest of component...
}
```

---

## 🎯 Common Patterns Across All Pages

### 1. Loading States
```javascript
{isLoading && (
  <div className="flex items-center justify-center py-12">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
    <span className="ml-3 text-gray-600">Loading...</span>
  </div>
)}
```

### 2. Error Handling
```javascript
{error && (
  <div className="p-4 rounded-lg bg-red-50 border border-red-200">
    <div className="flex items-start gap-3">
      <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
      <div className="text-sm text-red-700">{error}</div>
    </div>
  </div>
)}
```

### 3. Success Messages
```javascript
{message && (
  <div className="p-4 rounded-lg bg-green-50 border border-green-200">
    <div className="flex items-start gap-3">
      <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
      <div className="text-sm text-green-700">{message}</div>
    </div>
  </div>
)}
```

### 4. File Download Helper
```javascript
const downloadFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};
```

---

## ✅ Testing Checklist

After wiring each page:

- [ ] Loading spinner appears during API calls
- [ ] Error messages display correctly
- [ ] Success messages show appropriate feedback
- [ ] Data displays correctly from backend
- [ ] Actions trigger correct API calls
- [ ] Export buttons download files
- [ ] Form validations work
- [ ] Empty states handle gracefully

---

## 🚀 Deployment Readiness

Once all pages are wired:

1. **Test with real backend** - Run `npm run dev` and test each page
2. **Build for production** - Run `npm run build`
3. **Check console** - No errors in browser console
4. **Verify endpoints** - All API calls return 200/201
5. **Test edge cases** - Empty data, errors, timeouts
6. **Performance check** - No memory leaks, fast loading

---

**Last Updated:** April 21, 2026  
**Status:** Ready for implementation
