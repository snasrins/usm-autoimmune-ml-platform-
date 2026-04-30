/**
 * Comprehensive API Extensions for All Pages
 * Handles backend integration for: Scorecard, Data Quality, EDA, Explainability, 
 * Model Comparison, Batch Prediction, Training Jobs
 */
import api from './api';

// ========== CLINICAL SCORECARD API ==========
export const scorecardAPI = {
  /**
   * Generate scorecard from trained model
   */
  generateScorecard: async (modelId, config) => {
    const response = await api.post('/scorecard/scorecard', {
      model_id: modelId,
      binning_method: config.binningMethod || 'rolling_mean',
      num_bins: config.numBins || 4,
      use_youden_optimization: config.useYouden !== false
    });
    return response.data;
  },

  /**
   * Get bin-score tables for features
   */
  getBinScoreTables: async (scorecardId, featureName = null) => {
    const response = await api.get(`/scorecard/${scorecardId}/bin-tables`, {
      params: { feature_name: featureName }
    });
    return response.data;
  },

  /**
   * Get risk stratification metrics
   */
  getRiskStratification: async (scorecardId) => {
    const response = await api.get(`/scorecard/${scorecardId}/risk-stratification`);
    return response.data;
  },

  /**
   * Calculate patient score
   */
  calculatePatientScore: async (scorecardId, patientData) => {
    const response = await api.post(`/scorecard/${scorecardId}/calculate-score`, {
      patient_data: patientData
    });
    return response.data;
  },

  /**
   * Export scorecard to CSV
   */
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
  /**
   * Get quality report for a batch
   */
  getQualityReport: async (batchId) => {
    const response = await api.get(`/data-quality/report/${batchId}`);
    return response.data;
  },

  /**
   * Get quality summary
   */
  getQualitySummary: async () => {
    const response = await api.get('/data-quality/summary');
    return response.data;
  },

  /**
   * Apply preprocessing configuration
   */
  applyPreprocessing: async (batchId, config) => {
    const response = await api.post(`/data-quality/preprocess/${batchId}`, {
      apply_imputation: config.applyImputation,
      imputation_numeric_strategy: config.missingStrategy,
      imputation_categorical_strategy: config.categoricalStrategy || 'mode',
      
      apply_winsorization: config.applyWinsorization,
      winsorize_limits: config.winsorizePercentiles || [0.01, 0.01],
      
      apply_composite_features: config.enableComposite,
      composite_low_percentile: config.lowPercentile || 10.0,
      composite_high_percentile: config.highPercentile || 70.0,
      
      apply_standardization: config.enableStandardization,
      scaling_strategy: config.scalingMethod || 'standard'
    });
    return response.data;
  },

  /**
   * Get preview of processed data
   */
  getProcessedPreview: async (batchId, rows = 20) => {
    const response = await api.get(`/data-quality/preview/${batchId}`, {
      params: { rows }
    });
    return response.data;
  },

  /**
   * Export quality report
   */
  exportQualityReport: async (batchId, format = 'csv') => {
    const response = await api.get(`/data-quality/export/${batchId}`, {
      params: { format },
      responseType: 'blob'
    });
    return response.data;
  }
};

// ========== EDA (Exploratory Data Analysis) API ==========
export const edaAPI = {
  /**
   * Get statistical summary
   */
  getStatisticalSummary: async (batchId) => {
    const response = await api.get(`/eda/summary/${batchId}`);
    return response.data;
  },

  /**
   * Get correlation matrix
   */
  getCorrelationMatrix: async (batchId, method = 'pearson') => {
    const response = await api.get(`/eda/correlation/${batchId}`, {
      params: { method }
    });
    return response.data;
  },

  /**
   * Get feature distribution
   */
  getFeatureDistribution: async (batchId, featureName) => {
    const response = await api.get(`/eda/distribution/${batchId}`, {
      params: { feature_name: featureName }
    });
    return response.data;
  },

  /**
   * Get missing data heatmap
   */
  getMissingDataHeatmap: async (batchId) => {
    const response = await api.get(`/eda/missing-data/${batchId}`);
    return response.data;
  },

  /**
   * Generate automated insights
   */
  generateInsights: async (batchId) => {
    const response = await api.post(`/eda/insights/${batchId}`);
    return response.data;
  },

  /**
   * Get dataset info
   */
  getDatasetInfo: async (datasetId) => {
    const response = await api.get(`/eda/datasets/${datasetId}`);
    return response.data;
  }
};

// ========== MODEL EXPLAINABILITY API ==========
export const explainabilityAPI = {
  /**
   * Get SHAP values for a prediction
   */
  getSHAPValues: async (modelId, patientData) => {
    const response = await api.post('/explainability/explain', {
      model_id: modelId,
      patient_data: patientData
    });
    return response.data;
  },

  /**
   * Get global feature importance
   */
  getGlobalFeatureImportance: async (modelId) => {
    const response = await api.get(`/explainability/global-importance/${modelId}`);
    return response.data;
  },

  /**
   * Generate LLM explanation (AI-powered)
   */
  generateLLMExplanation: async (modelId, patientData, detailLevel = 'moderate') => {
    const response = await api.post('/explainability/llm-explain', {
      model_id: modelId,
      patient_data: patientData,
      detail_level: detailLevel,
      include_clinical_context: true,
      include_recommendations: true
    });
    return response.data;
  },

  /**
   * Batch SHAP analysis
   */
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

// ========== MODEL COMPARISON API ==========
export const modelComparisonAPI = {
  /**
   * Compare 2-4 models side-by-side
   */
  compareModels: async (modelIds) => {
    const response = await api.post('/ml/models/compare', {
      model_ids: modelIds
    });
    return response.data;
  },

  /**
   * Get ROC curves for comparison
   */
  getROCCurves: async (modelIds) => {
    const response = await api.get('/ml/models/roc-curves', {
      params: { model_ids: modelIds.join(',') }
    });
    return response.data;
  },

  /**
   * Get confusion matrices
   */
  getConfusionMatrices: async (modelIds) => {
    const response = await api.get('/ml/models/confusion-matrices', {
      params: { model_ids: modelIds.join(',') }
    });
    return response.data;
  },

  /**
   * Export comparison report
   */
  exportComparison: async (modelIds, format = 'pdf') => {
    const response = await api.post('/ml/models/export-comparison', {
      model_ids: modelIds,
      format: format
    }, {
      responseType: 'blob'
    });
    return response.data;
  }
};

// ========== BATCH PREDICTION API ==========
export const batchPredictionAPI = {
  /**
   * Upload patients for prediction
   */
  uploadPatientsForPrediction: async (modelId, patientsFile, options = {}) => {
    const formData = new FormData();
    formData.append('file', patientsFile);
    formData.append('model_id', modelId);
    formData.append('include_shap', options.includeSHAP || false);
    formData.append('include_confidence', options.includeConfidence || true);
    
    const response = await api.post('/predict/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  /**
   * Get prediction results
   */
  getPredictionResults: async (predictionJobId) => {
    const response = await api.get(`/predict/results/${predictionJobId}`);
    return response.data;
  },

  /**
   * Export predictions
   */
  exportPredictions: async (predictionJobId, format = 'csv') => {
    const response = await api.get(`/predict/export/${predictionJobId}`, {
      params: { format },
      responseType: 'blob'
    });
    return response.data;
  }
};

// ========== TRAINING JOBS API (Enhanced) ==========
export const trainingAPI = {
  /**
   * Prepare dataset for training
   */
  prepareDataset: async (batchId, config) => {
    const response = await api.post('/ml/train/prepare-dataset', {
      batch_id: batchId,
      target_column: config.targetColumn,
      test_size: config.testSize || 0.2,
      random_state: config.randomState || 42,
      use_lasso_feature_selection: config.useLASSO || false,
      lasso_alpha: config.lassoAlpha || 0.01,
      scaling_strategy: config.scalingStrategy || 'standard'
    });
    return response.data;
  },

  /**
   * Train single model
   */
  trainModel: async (datasetId, modelConfig) => {
    const response = await api.post('/ml/train/base-model', {
      dataset_id: datasetId,
      algorithm: modelConfig.algorithm,
      hyperparameter_tuning: {
        method: 'optuna',
        n_trials: modelConfig.nTrials || 50,
        cv_folds: modelConfig.cvFolds || 5
      }
    });
    return response.data;
  },

  /**
   * Train full pipeline (dataset prep + model training)
   */
  trainFullPipeline: async (batchId, config) => {
    const response = await api.post('/ml/train/full-pipeline', {
      batch_id: batchId,
      target_column: config.targetColumn,
      algorithms: config.algorithms || ['xgboost', 'lightgbm'],
      test_size: config.testSize || 0.2,
      n_trials: config.nTrials || 50,
      cv_folds: config.cvFolds || 5
    });
    return response.data;
  },

  /**
   * Get training job status
   */
  getJobStatus: async (jobId) => {
    const response = await api.get(`/ml/train/status/${jobId}`);
    return response.data;
  },

  /**
   * Get training history
   */
  getTrainingHistory: async (limit = 50) => {
    const response = await api.get('/ml/training-history', {
      params: { limit }
    });
    return response.data;
  },

  /**
   * List trained models
   */
  listModels: async (params = {}) => {
    const response = await api.get('/ml/models', {
      params: {
        limit: params.limit || 50,
        algorithm: params.algorithm,
        min_accuracy: params.minAccuracy
      }
    });
    return response.data;
  }
};

// ========== LABEL ASSIGNMENT API ==========
export const labelingAPI = {
  /**
   * Get unlabeled patients
   */
  getUnlabeledPatients: async (params = {}) => {
    const response = await api.get('/labeling/unlabeled', {
      params: {
        limit: params.limit || 50,
        batch_id: params.batchId
      }
    });
    return response.data;
  },

  /**
   * Assign label to single patient
   */
  assignLabel: async (patientId, label, confidence = null) => {
    const response = await api.post('/labeling/assign', {
      patient_id: patientId,
      label: label,
      confidence: confidence
    });
    return response.data;
  },

  /**
   * Bulk assign labels
   */
  bulkAssignLabels: async (assignments) => {
    const response = await api.post('/labeling/bulk-assign', {
      assignments: assignments
    });
    return response.data;
  },

  /**
   * Get labeling statistics
   */
  getLabelingStats: async () => {
    const response = await api.get('/labeling/stats');
    return response.data;
  },

  /**
   * Auto-label using model
   */
  autoLabel: async (modelId, batchId, confidenceThreshold = 0.9) => {
    const response = await api.post('/labeling/auto-label', {
      model_id: modelId,
      batch_id: batchId,
      confidence_threshold: confidenceThreshold
    });
    return response.data;
  }
};

export default {
  scorecardAPI,
  dataQualityAPI,
  edaAPI,
  explainabilityAPI,
  modelComparisonAPI,
  batchPredictionAPI,
  trainingAPI,
  labelingAPI
};
