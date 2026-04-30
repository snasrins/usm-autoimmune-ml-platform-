# 🔌 UI → Backend Integration Gaps & Improvement Plan

**Date:** April 20, 2026  
**Purpose:** Identify what needs to be wired between frontend UI and backend APIs  
**Status:** 🔴 **CRITICAL GAPS FOUND** - Most pages using mock data

---

## 📊 **EXECUTIVE SUMMARY**

Your frontend has **beautiful, production-ready UI** with comprehensive pages, but **90% is disconnected from the backend**. Here's what needs to be done:

### **Current State:**
- ✅ **Auth System**: Fully integrated (login, register, token refresh)
- ✅ **Data Ingestion**: Mostly integrated (upload, preview, save)
- ✅ **Label Assignment**: Partially integrated
- 🟡 **Training Jobs**: 30% integrated (needs real-time polling, better error handling)
- 🔴 **Data Quality/Preprocessing**: **0% integrated** - entirely mock data
- 🔴 **Clinical Scorecard**: **0% integrated** - entirely mock data
- 🔴 **Model Explainability**: **0% integrated** - page doesn't exist yet
- 🔴 **Patient Monitoring**: **0% integrated** - entirely mock data
- 🔴 **Model Comparison**: **0% integrated** - entirely mock data

---

## 🚨 **CRITICAL GAPS (Fix These First)**

### **1. Clinical Scorecard Page** (`ClinicalScorecardPage.jsx`)

**Current State:** 100% MOCK DATA
```jsx
// MOCK DATA - NOT REAL
const BIN_SCORE_DATA_NK = [
  { range: '≤ 1.10', score: 1.7, count: 15, pct: '13.5%', mild: 20, severe: 80 },
  // ... hardcoded values
];
```

**What's Missing:**
```javascript
// Missing in api.js:
export const scorecardAPI = {
  // 1. Generate scorecard from model
  generateScorecard: async (modelId, config) => {
    const response = await api.post('/scorecard/generate', {
      model_id: modelId,
      binning_method: config.binningMethod,      // 'rolling_mean', 'quantile', etc.
      num_bins: config.numBins,                  // 4, 5, 10
      use_youden_optimization: config.useYouden  // true/false
    });
    return response.data;
  },

  // 2. Get bin-score tables for a feature
  getBinScoreTables: async (scorecardId, featureName = null) => {
    const response = await api.get(`/scorecard/${scorecardId}/bin-tables`, {
      params: { feature_name: featureName }
    });
    return response.data;
  },

  // 3. Get risk stratification metrics
  getRiskStratification: async (scorecardId) => {
    const response = await api.get(`/scorecard/${scorecardId}/risk-stratification`);
    return response.data;
  },

  // 4. Calculate patient score
  calculatePatientScore: async (scorecardId, patientData) => {
    const response = await api.post(`/scorecard/${scorecardId}/calculate-score`, {
      patient_data: patientData
    });
    return response.data;
  },

  // 5. Export scorecard to CSV
  exportScorecardCSV: async (scorecardId, exportType) => {
    const response = await api.get(`/scorecard/${scorecardId}/export`, {
      params: { export_type: exportType },  // 'bin_tables', 'threshold_report', 'patient_scores'
      responseType: 'blob'
    });
    return response.data;
  }
};
```

**Action Required:**
1. Add `scorecardAPI` to `api.js`
2. Update `ClinicalScorecardPage.jsx` to:
   - Call `generateScorecard()` instead of mock generation
   - Fetch real bin-score tables with `getBinScoreTables()`
   - Use real risk stratification data
   - Connect calculator to `calculatePatientScore()`

---

### **2. Data Quality & Preprocessing Page** (`DataQualityWorkbenchPage.jsx`)

**Current State:** 100% MOCK DATA
```jsx
// MOCK - NOT REAL
const QUALITY_TREND = [
  { date: 'Apr 14', score: 81 },
  // ... hardcoded
];
```

**What's Missing:**
```javascript
// Missing in api.js:
export const dataQualityAPI = {
  // 1. Get quality report for a batch
  getQualityReport: async (batchId) => {
    const response = await api.get(`/data-quality/report/${batchId}`);
    return response.data;
    // Returns: {
    //   quality_score: 92,
    //   missing_values_pct: 8.2,
    //   outliers_pct: 3.1,
    //   duplicates_count: 5,
    //   issues: [...],
    //   recommendations: [...]
    // }
  },

  // 2. Apply preprocessing configuration
  applyPreprocessing: async (batchId, config) => {
    const response = await api.post(`/data-quality/preprocess/${batchId}`, {
      // Imputation
      apply_imputation: config.applyImputation,
      imputation_numeric_strategy: config.missingStrategy,  // 'median', 'mean'
      imputation_categorical_strategy: config.categoricalStrategy,
      
      // Winsorization
      apply_winsorization: config.applyWinsorization,
      winsorize_limits: config.winsorizePercentiles,  // [0.01, 0.01] = 1%/99%
      
      // Composite features
      apply_composite_features: config.enableComposite,
      composite_low_percentile: config.lowPercentile,   // 10.0
      composite_high_percentile: config.highPercentile, // 70.0
      
      // Standardization
      apply_standardization: config.enableStandardization,
      scaling_strategy: config.scalingMethod  // 'standard', 'minmax', 'robust'
    });
    return response.data;
  },

  // 3. Get preview of processed data (before/after)
  getProcessedPreview: async (batchId, rows = 20) => {
    const response = await api.get(`/data-quality/preview/${batchId}`, {
      params: { rows }
    });
    return response.data;
  },

  // 4. Export quality report
  exportQualityReport: async (batchId, format = 'csv') => {
    const response = await api.get(`/data-quality/export/${batchId}`, {
      params: { format },  // 'csv', 'pdf', 'json'
      responseType: 'blob'
    });
    return response.data;
  }
};
```

**Action Required:**
1. Add `dataQualityAPI` to `api.js`
2. Update `DataQualityWorkbenchPage.jsx`:
   - Fetch real quality metrics with `getQualityReport()`
   - Wire preprocessing controls to `applyPreprocessing()`
   - Show real before/after preview with `getProcessedPreview()`
   - Enable CSV/PDF export

---

### **3. Training Jobs Page** (`TrainingJobsPage.jsx`)

**Current State:** 30% integrated - has some API calls but incomplete

**What's Missing:**
```javascript
// Existing in api.js but INCOMPLETE:
export const mlAPI = {
  // ✅ Already exists: trainModel, getJobStatus
  
  // ❌ MISSING: Real-time training progress polling
  streamTrainingProgress: async (jobId, onProgress) => {
    // Option 1: WebSocket (best for real-time)
    const ws = new WebSocket(`ws://100.106.132.15:8001/ws/training/${jobId}`);
    ws.onmessage = (event) => {
      const progress = JSON.parse(event.data);
      onProgress(progress);
    };
    return ws;
    
    // Option 2: Server-Sent Events (SSE)
    const eventSource = new EventSource(`${API_BASE_URL}/ml/train/stream/${jobId}`);
    eventSource.onmessage = (event) => {
      const progress = JSON.parse(event.data);
      onProgress(progress);
    };
    return eventSource;
  },

  // ❌ MISSING: Prepare dataset for training
  prepareDataset: async (batchId, config) => {
    const response = await api.post('/ml/train/prepare-dataset', {
      batch_id: batchId,
      target_column: config.targetColumn,
      test_size: config.testSize,
      random_state: config.randomState,
      
      // Feature selection
      use_lasso_feature_selection: config.useLASSO,
      lasso_alpha: config.lassoAlpha,
      
      // Preprocessing (should already be done in Data Quality step)
      skip_preprocessing: config.skipPreprocessing,
      
      // Scaling
      scaling_strategy: config.scalingStrategy,
      create_separate_feature_sets: config.createSeparateSets
    });
    return response.data;
  },

  // ❌ MISSING: Train multiple models simultaneously
  trainMultipleModels: async (batchId, modelConfigs, datasetConfig) => {
    const response = await api.post('/ml/train/multi-model', {
      batch_id: batchId,
      dataset_config: datasetConfig,
      models: modelConfigs.map(m => ({
        algorithm: m.id,
        hyperparameter_tuning: {
          method: 'optuna',  // or 'grid_search'
          n_trials: m.nTrials || 50,
          cv_folds: m.cvFolds || 5
        }
      }))
    });
    return response.data;
  },

  // ❌ MISSING: Get all models comparison
  getAllModelsComparison: async (jobId) => {
    const response = await api.get(`/ml/train/comparison/${jobId}`);
    return response.data;
  }
};
```

**Action Required:**
1. Implement `prepareDataset()` API call
2. Implement `trainMultipleModels()` for batch training
3. Add real-time progress polling (WebSocket or SSE)
4. Better error handling and recovery
5. Show detailed training logs

---

### **4. Model Comparison Page** (`ModelComparisonPage.jsx`)

**Current State:** Exists in pages but NOT INTEGRATED

**What's Missing:**
```javascript
// Missing in api.js:
export const modelComparisonAPI = {
  // 1. Compare 2-4 models side-by-side
  compareModels: async (modelIds) => {
    const response = await api.post('/ml/models/compare', {
      model_ids: modelIds  // ['model_1', 'model_2', 'model_3']
    });
    return response.data;
    // Returns: {
    //   models: [
    //     {
    //       model_id: 'lr_2026_04_20_...',
    //       algorithm: 'Logistic Regression',
    //       metrics: { accuracy: 0.8649, precision: 0.8571, ... },
    //       training_time_sec: 45,
    //       inference_time_ms: 2
    //     },
    //     ...
    //   ],
    //   best_by_metric: {
    //     accuracy: 'model_1',
    //     auc: 'model_2',
    //     ...
    //   }
    // }
  },

  // 2. Get ROC curves for comparison
  getROCCurves: async (modelIds) => {
    const response = await api.get('/ml/models/roc-curves', {
      params: { model_ids: modelIds.join(',') }
    });
    return response.data;
  },

  // 3. Get confusion matrices
  getConfusionMatrices: async (modelIds) => {
    const response = await api.get('/ml/models/confusion-matrices', {
      params: { model_ids: modelIds.join(',') }
    });
    return response.data;
  },

  // 4. Export comparison report
  exportComparison: async (modelIds, format = 'pdf') => {
    const response = await api.post('/ml/models/export-comparison', {
      model_ids: modelIds,
      format: format  // 'pdf', 'csv', 'xlsx'
    }, {
      responseType: 'blob'
    });
    return response.data;
  }
};
```

**Action Required:**
1. Add `modelComparisonAPI` to `api.js`
2. Wire `ModelComparisonPage.jsx` to real backend data
3. Show real metrics, ROC curves, confusion matrices

---

### **5. Model Explainability Page** (NEW - DOESN'T EXIST YET)

**Current State:** ❌ **PAGE NOT CREATED**

**What Needs to be Built:**
```javascript
// Missing in api.js:
export const explainabilityAPI = {
  // 1. Get SHAP values for a prediction
  getSHAPValues: async (modelId, patientData) => {
    const response = await api.post('/explainability/shap', {
      model_id: modelId,
      patient_data: patientData
    });
    return response.data;
    // Returns: {
    //   prediction: 0.73,
    //   base_value: 0.45,
    //   shap_values: {
    //     'CRP_high': 0.18,
    //     'ESR_high': 0.12,
    //     'Low_C3': 0.08,
    //     ...
    //   },
    //   feature_contributions: [...]
    // }
  },

  // 2. Get global feature importance
  getGlobalFeatureImportance: async (modelId) => {
    const response = await api.get(`/explainability/global-importance/${modelId}`);
    return response.data;
  },

  // 3. Generate LLM explanation (AI-powered)
  generateLLMExplanation: async (modelId, patientData, detailLevel = 'moderate') => {
    const response = await api.post('/explainability/llm-explain', {
      model_id: modelId,
      patient_data: patientData,
      detail_level: detailLevel,  // 'brief', 'moderate', 'detailed'
      include_clinical_context: true,
      include_recommendations: true
    });
    return response.data;
    // Returns: {
    //   explanation: "The model predicts this patient is at HIGH RISK...",
    //   key_factors: [...],
    //   recommendations: [...]
    // }
  },

  // 4. Batch SHAP analysis
  batchSHAPAnalysis: async (modelId, patientsFile) => {
    const formData = new FormData();
    formData.append('file', patientsFile);
    formData.append('model_id', modelId);
    
    const response = await api.post('/explainability/batch-shap', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }
};
```

**Action Required:**
1. Create `ModelExplainabilityPage.jsx` (doesn't exist yet)
2. Add `explainabilityAPI` to `api.js`
3. Implement SHAP force plots, waterfall charts
4. Integrate LLM-generated explanations
5. Add batch analysis view

---

### **6. Patient Monitoring Page** (`PatientMonitoringPage.jsx`)

**Current State:** Exists but NOT INTEGRATED (likely mock data)

**What's Missing:**
```javascript
// Missing in api.js:
export const patientMonitoringAPI = {
  // 1. Get all monitored patients
  getMonitoredPatients: async (filters = {}) => {
    const response = await api.get('/patient-monitoring/list', {
      params: {
        risk_level: filters.riskLevel,     // 'high', 'medium', 'low'
        trending: filters.trending,        // 'increasing', 'decreasing', 'stable'
        limit: filters.limit || 50
      }
    });
    return response.data;
  },

  // 2. Get patient longitudinal data
  getPatientHistory: async (patientId) => {
    const response = await api.get(`/patient-monitoring/history/${patientId}`);
    return response.data;
    // Returns: {
    //   patient_id: 'P001',
    //   demographics: {...},
    //   risk_scores: [
    //     { date: '2025-05-15', score: 45.2, risk_level: 'low' },
    //     { date: '2026-04-18', score: 68.3, risk_level: 'high' }
    //   ],
    //   lab_values: [...]
    // }
  },

  // 3. Get patient alerts
  getPatientAlerts: async (patientId) => {
    const response = await api.get(`/patient-monitoring/alerts/${patientId}`);
    return response.data;
  },

  // 4. Add patient to monitoring
  addPatientMonitoring: async (patientId, config) => {
    const response = await api.post('/patient-monitoring/add', {
      patient_id: patientId,
      alert_threshold: config.alertThreshold,
      notify_on_change: config.notifyOnChange
    });
    return response.data;
  },

  // 5. Get cohort statistics
  getCohortStats: async () => {
    const response = await api.get('/patient-monitoring/cohort-stats');
    return response.data;
  }
};
```

**Action Required:**
1. Add `patientMonitoringAPI` to `api.js`
2. Wire `PatientMonitoringPage.jsx` to real data
3. Implement longitudinal charts (risk score over time)
4. Show real alerts and trending patients

---

## 🔧 **MEDIUM PRIORITY GAPS**

### **7. EDA (Exploratory Data Analysis)**

**Current State:** Pages exist (`EDAExplorerPage.jsx`, `EDAWorkbenchPage.jsx`) but likely using mock data

**What's Missing:**
```javascript
export const edaAPI = {
  // 1. Get statistical summary
  getStatisticalSummary: async (batchId) => {
    const response = await api.get(`/eda/summary/${batchId}`);
    return response.data;
  },

  // 2. Get correlation matrix
  getCorrelationMatrix: async (batchId, method = 'pearson') => {
    const response = await api.get(`/eda/correlation/${batchId}`, {
      params: { method }
    });
    return response.data;
  },

  // 3. Get feature distributions
  getFeatureDistribution: async (batchId, featureName) => {
    const response = await api.get(`/eda/distribution/${batchId}`, {
      params: { feature_name: featureName }
    });
    return response.data;
  },

  // 4. Get missing data heatmap
  getMissingDataHeatmap: async (batchId) => {
    const response = await api.get(`/eda/missing-data/${batchId}`);
    return response.data;
  },

  // 5. Generate automated insights
  generateInsights: async (batchId) => {
    const response = await api.post(`/eda/insights/${batchId}`);
    return response.data;
  }
};
```

---

### **8. Batch Prediction**

**Current State:** Page exists (`BatchPredictionPage.jsx`) but needs better integration

**What's Missing:**
```javascript
export const batchPredictionAPI = {
  // 1. Upload patients for prediction
  uploadPatientsForPrediction: async (modelId, patientsFile, options = {}) => {
    const formData = new FormData();
    formData.append('file', patientsFile);
    formData.append('model_id', modelId);
    formData.append('include_shap', options.includeSHAP || false);
    formData.append('include_confidence', options.includeConfidence || true);
    
    const response = await api.post('/prediction/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // 2. Get prediction results
  getPredictionResults: async (predictionJobId) => {
    const response = await api.get(`/prediction/results/${predictionJobId}`);
    return response.data;
  },

  // 3. Export predictions
  exportPredictions: async (predictionJobId, format = 'csv') => {
    const response = await api.get(`/prediction/export/${predictionJobId}`, {
      params: { format },
      responseType: 'blob'
    });
    return response.data;
  }
};
```

---

## 📋 **IMPLEMENTATION CHECKLIST**

### **Phase 1: Critical Integrations (Week 1-2)**
- [ ] **1.1** Add `scorecardAPI` to `api.js`
- [ ] **1.2** Wire `ClinicalScorecardPage.jsx` to backend
  - [ ] Generate scorecard
  - [ ] Fetch bin-score tables
  - [ ] Risk stratification
  - [ ] Patient calculator
  - [ ] CSV export
- [ ] **1.3** Add `dataQualityAPI` to `api.js`
- [ ] **1.4** Wire `DataQualityWorkbenchPage.jsx` to backend
  - [ ] Quality report
  - [ ] Preprocessing configuration
  - [ ] Before/after preview
  - [ ] Export reports
- [ ] **1.5** Improve `TrainingJobsPage.jsx`
  - [ ] Real-time progress polling (WebSocket/SSE)
  - [ ] Multi-model training
  - [ ] Better error handling

### **Phase 2: Model Features (Week 3-4)**
- [ ] **2.1** Add `modelComparisonAPI` to `api.js`
- [ ] **2.2** Wire `ModelComparisonPage.jsx` to backend
- [ ] **2.3** Add `explainabilityAPI` to `api.js`
- [ ] **2.4** Create `ModelExplainabilityPage.jsx` (NEW PAGE)
  - [ ] SHAP force plots
  - [ ] SHAP waterfall charts
  - [ ] Global feature importance
  - [ ] LLM-generated explanations
  - [ ] Batch analysis

### **Phase 3: Patient Monitoring (Week 5)**
- [ ] **3.1** Add `patientMonitoringAPI` to `api.js`
- [ ] **3.2** Wire `PatientMonitoringPage.jsx` to backend
  - [ ] Monitored patients list
  - [ ] Longitudinal tracking
  - [ ] Alerts system
  - [ ] Cohort statistics

### **Phase 4: Analytics & Utilities (Week 6)**
- [ ] **4.1** Add `edaAPI` to `api.js`
- [ ] **4.2** Wire EDA pages to backend
- [ ] **4.3** Improve `batchPredictionAPI`
- [ ] **4.4** Add error boundaries and loading states globally

---

## 🎯 **QUICK WINS (Do These Today)**

### **1. Add Missing API Functions**

Create a new file: `frontend/src/services/api-extensions.js`

```javascript
import api from './api';

// ========== SCORECARD API ==========
export const scorecardAPI = {
  generateScorecard: async (modelId, config) => {
    const response = await api.post('/scorecard/generate', {
      model_id: modelId,
      binning_method: config.binningMethod || 'rolling_mean',
      num_bins: config.numBins || 4,
      use_youden_optimization: config.useYouden !== false
    });
    return response.data;
  },
  
  getBinScoreTables: async (scorecardId, featureName = null) => {
    const response = await api.get(`/scorecard/${scorecardId}/bin-tables`, {
      params: { feature_name: featureName }
    });
    return response.data;
  },
  
  getRiskStratification: async (scorecardId) => {
    const response = await api.get(`/scorecard/${scorecardId}/risk-stratification`);
    return response.data;
  },
  
  calculatePatientScore: async (scorecardId, patientData) => {
    const response = await api.post(`/scorecard/${scorecardId}/calculate-score`, {
      patient_data: patientData
    });
    return response.data;
  },
  
  exportScorecardCSV: async (scorecardId, exportType) => {
    const response = await api.get(`/scorecard/${scorecardId}/export`, {
      params: { export_type: exportType },
      responseType: 'blob'
    });
    return response.data;
  }
};

// ========== DATA QUALITY API ==========
export const dataQualityAPI = {
  getQualityReport: async (batchId) => {
    const response = await api.get(`/data-quality/report/${batchId}`);
    return response.data;
  },
  
  applyPreprocessing: async (batchId, config) => {
    const response = await api.post(`/data-quality/preprocess/${batchId}`, config);
    return response.data;
  },
  
  getProcessedPreview: async (batchId, rows = 20) => {
    const response = await api.get(`/data-quality/preview/${batchId}`, {
      params: { rows }
    });
    return response.data;
  }
};

// ========== MODEL COMPARISON API ==========
export const modelComparisonAPI = {
  compareModels: async (modelIds) => {
    const response = await api.post('/ml/models/compare', {
      model_ids: modelIds
    });
    return response.data;
  },
  
  getROCCurves: async (modelIds) => {
    const response = await api.get('/ml/models/roc-curves', {
      params: { model_ids: modelIds.join(',') }
    });
    return response.data;
  }
};

// ========== EXPLAINABILITY API ==========
export const explainabilityAPI = {
  getSHAPValues: async (modelId, patientData) => {
    const response = await api.post('/explainability/shap', {
      model_id: modelId,
      patient_data: patientData
    });
    return response.data;
  },
  
  getGlobalFeatureImportance: async (modelId) => {
    const response = await api.get(`/explainability/global-importance/${modelId}`);
    return response.data;
  },
  
  generateLLMExplanation: async (modelId, patientData, detailLevel = 'moderate') => {
    const response = await api.post('/explainability/llm-explain', {
      model_id: modelId,
      patient_data: patientData,
      detail_level: detailLevel,
      include_clinical_context: true,
      include_recommendations: true
    });
    return response.data;
  }
};
```

### **2. Update Import in Pages**

In each page that needs these APIs:
```javascript
// OLD:
// Using mock data

// NEW:
import { scorecardAPI, dataQualityAPI, modelComparisonAPI, explainabilityAPI } from '../services/api-extensions';
```

### **3. Add Error Handling Component**

Create: `frontend/src/components/ErrorBoundary.jsx`
```javascript
import { Component } from 'react';
import { AlertTriangle } from 'lucide-react';

class ErrorBoundary extends Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-red-50">
          <div className="max-w-md p-6 bg-white rounded-lg border border-red-200">
            <AlertTriangle className="w-12 h-12 text-red-600 mb-4" />
            <h2 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h2>
            <p className="text-gray-600 mb-4">{this.state.error?.message}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

---

## 📚 **DOCUMENTATION NEEDED**

Create these files to help frontend devs:

1. **`frontend/API_INTEGRATION_GUIDE.md`**
   - Document all backend endpoints
   - Show request/response examples
   - Authentication requirements
   - Error handling patterns

2. **`frontend/COMPONENT_REFACTOR_GUIDE.md`**
   - How to replace mock data with API calls
   - State management patterns
   - Loading states and error handling
   - Polling patterns for long-running jobs

3. **`frontend/TESTING_BACKEND_INTEGRATION.md`**
   - How to test API integration locally
   - Mock API server setup for development
   - E2E testing with Cypress/Playwright

---

## 🚀 **DEPLOYMENT READINESS**

Before going to production, ensure:

### **Backend Requirements:**
- [ ] All endpoints return consistent error formats
- [ ] CORS configured for frontend domain
- [ ] Rate limiting on expensive endpoints
- [ ] WebSocket/SSE for real-time features
- [ ] API versioning (`/api/v1/`, `/api/v2/`)
- [ ] Comprehensive API documentation (Swagger/OpenAPI)

### **Frontend Requirements:**
- [ ] All pages connected to real backend
- [ ] Error boundaries on all major components
- [ ] Loading states for all async operations
- [ ] Retry logic for failed requests
- [ ] Offline detection and user feedback
- [ ] Analytics tracking on API calls
- [ ] Performance monitoring (measure API response times)

---

## 💡 **BEST PRACTICES**

### **1. Consistent Error Handling**
```javascript
// Use this pattern everywhere:
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);
const [data, setData] = useState(null);

const fetchData = async () => {
  setLoading(true);
  setError(null);
  try {
    const result = await scorecardAPI.generateScorecard(modelId, config);
    setData(result);
  } catch (err) {
    setError(err.response?.data?.detail || 'Failed to generate scorecard');
    console.error('Scorecard generation error:', err);
  } finally {
    setLoading(false);
  }
};
```

### **2. Loading States**
```javascript
{loading && (
  <div className="flex items-center justify-center p-8">
    <RefreshCw className="w-6 h-6 animate-spin text-indigo-600" />
    <span className="ml-2 text-gray-600">Loading...</span>
  </div>
)}

{error && (
  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
    <AlertTriangle className="w-5 h-5 text-red-600 inline mr-2" />
    <span className="text-red-800">{error}</span>
  </div>
)}
```

### **3. Real-Time Polling**
```javascript
useEffect(() => {
  if (!jobId) return;
  
  const interval = setInterval(async () => {
    try {
      const status = await mlAPI.getJobStatus(jobId);
      setJobStatus(status);
      
      if (status.status === 'completed' || status.status === 'failed') {
        clearInterval(interval);
      }
    } catch (err) {
      console.error('Polling error:', err);
    }
  }, 2000); // Poll every 2 seconds
  
  return () => clearInterval(interval);
}, [jobId]);
```

---

## 🎯 **SUCCESS METRICS**

Track these to measure integration success:

1. **API Call Success Rate**: > 98%
2. **Average Response Time**: < 500ms
3. **Error Rate**: < 2%
4. **Real-Time Update Lag**: < 3 seconds
5. **User-Reported Bugs**: < 5 per week
6. **Page Load Time**: < 2 seconds

---

## 📞 **NEXT STEPS**

1. **Today:** Create `api-extensions.js` with missing APIs
2. **This Week:** Wire Clinical Scorecard page (highest priority)
3. **Next Week:** Wire Data Quality page
4. **Week 3-4:** Model comparison and explainability
5. **Week 5-6:** Patient monitoring and EDA

**Questions?** Review this doc with your backend team to align on endpoint contracts!

---

**🔥 Bottom Line:** Your UI is **production-ready visually** but needs **backend wiring ASAP**. Start with scorecard and data quality pages - they're the most critical for your research workflow.
