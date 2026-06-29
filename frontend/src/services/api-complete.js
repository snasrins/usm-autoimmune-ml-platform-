/**
 * Complete API Integration for USM Autoimmune ML Platform
 * Wires all frontend pages to backend endpoints
 * Follows correct pipeline: Unstructured → Structured → Preprocessing → ML → Scorecard
 */
import api from './api';

const API_BASE = '/api/v1';

// ========================================
// UNSTRUCTURED DATA PIPELINE (Qwen OCR)
// ========================================
export const unstructuredPipelineAPI = {
  /**
   * Step 1: Upload PDF/Image for Qwen OCR processing
   * @param {File} file - PDF, PNG, JPG, or TXT file
   * @returns {Promise<{success: boolean, validation_id: number, extracted_text: string, page_count: number}>}
   */
  uploadForOCR: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/unstructured/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  /**
   * Step 2: Get OCR extraction preview
   * @param {number} validationId - OCR record ID
   * @returns {Promise<{validation_id: number, extracted_text: string, medical_entities: array, page_count: number}>}
   */
  getOCRPreview: async (validationId) => {
    const response = await api.get(`/unstructured/preview/${validationId}`);
    return response.data;
  },

  /**
   * Step 3: Convert OCR result to editable tabular format
   * @param {number} validationId - OCR record ID
   * @param {string} datasetType - Dataset classification
   * @param {string} conversionMode - 'grouped' or 'individual'
   * @returns {Promise<{success: boolean, session_id: string, row_count: number}>}
   */
  convertToTabular: async (validationId, datasetType = 'OCR_Medical_Report', conversionMode = 'grouped') => {
    const response = await api.post('/flexible/unstructured/convert', {
      validation_id: validationId,
      dataset_type: datasetType,
      conversion_mode: conversionMode
    });
    return response.data;
  },

  /**
   * List all OCR processed files
   * @param {number} limit - Max results
   * @returns {Promise<Array>}
   */
  listOCRFiles: async (limit = 50) => {
    const response = await api.get(`/unstructured/list?limit=${limit}`);
    return response.data;
  }
};

// ========================================
// STRUCTURED DATA PIPELINE (CSV/Excel)
// ========================================
export const structuredPipelineAPI = {
  /**
   * Step 1: Upload CSV/Excel for preview
   * @param {File} file - CSV or Excel file
   * @param {string} datasetType - Dataset type
   * @returns {Promise<{success: boolean, session_id: string, row_count: number, columns: array}>}
   */
  uploadForPreview: async (file, datasetType = 'Clinical_Data') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('dataset_type', datasetType);
    
    const response = await api.post('/flexible/preview/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  /**
   * Step 2: Get editable preview with pagination
   * @param {string} sessionId - Preview session UUID
   * @param {number} page - Page number
   * @param {number} pageSize - Rows per page
   * @returns {Promise<{session_id: string, total_rows: number, rows: array, schema: object}>}
   */
  getPreview: async (sessionId, page = 1, pageSize = 20) => {
    const response = await api.get(`/flexible/preview/${sessionId}`, {
      params: { page, page_size: pageSize }
    });
    return response.data;
  },

  /**
   * Step 3: Edit a cell in preview
   * @param {string} sessionId - Preview session UUID
   * @param {number} stagingId - Row staging ID
   * @param {string} columnName - Column to edit
   * @param {any} newValue - New value
   * @returns {Promise<{success: boolean}>}
   */
  editCell: async (sessionId, stagingId, columnName, newValue) => {
    const response = await api.patch(`/flexible/preview/${sessionId}/row/${stagingId}`, {
      column_name: columnName,
      new_value: newValue
    });
    return response.data;
  },

  /**
   * Step 4: Delete a row from preview
   * @param {string} sessionId - Preview session UUID
   * @param {number} stagingId - Row staging ID
   * @returns {Promise<{success: boolean}>}
   */
  deleteRow: async (sessionId, stagingId) => {
    const response = await api.delete(`/flexible/preview/${sessionId}/row/${stagingId}`);
    return response.data;
  }
};

// ========================================
// PREPROCESSING API (Layer 5)
// ========================================
export const preprocessingAPI = {
  /**
   * Get data quality report for preview session
   * @param {string} sessionId - Preview session UUID
   * @returns {Promise<{quality_score: number, issues: array, recommendations: array}>}
   */
  getQualityReport: async (sessionId) => {
    const response = await api.get(`/preview/${sessionId}/quality`);
    return response.data;
  },

  /**
   * Apply imputation to handle missing values
   * @param {string} sessionId - Preview session UUID
   * @param {string} method - 'median', 'mean', 'mode', 'drop'
   * @param {number} threshold - Drop threshold (0-1)
   * @returns {Promise<{success: boolean, rows_affected: number}>}
   */
  handleMissingValues: async (sessionId, method = 'median', threshold = 0.5) => {
    const response = await api.post(`/preview/${sessionId}/preprocess/missing-values`, null, {
      params: { method, threshold }
    });
    return response.data;
  },

  /**
   * Remove duplicate records
   * @param {string} sessionId - Preview session UUID
   * @param {boolean} keepFirst - Keep first occurrence
   * @returns {Promise<{success: boolean, duplicates_removed: number}>}
   */
  removeDuplicates: async (sessionId, keepFirst = true) => {
    const response = await api.post(`/preview/${sessionId}/preprocess/duplicates`, null, {
      params: { keep_first: keepFirst }
    });
    return response.data;
  },

  /**
   * Handle outliers using winsorization or removal
   * @param {string} sessionId - Preview session UUID
   * @param {string} method - 'winsorize' or 'remove'
   * @param {number} threshold - Z-score threshold
   * @returns {Promise<{success: boolean, outliers_handled: number}>}
   */
  handleOutliers: async (sessionId, method = 'winsorize', threshold = 3.0) => {
    const response = await api.post(`/preview/${sessionId}/preprocess/outliers`, null, {
      params: { method, threshold }
    });
    return response.data;
  },

  /**
   * Normalize/standardize data
   * @param {string} sessionId - Preview session UUID
   * @param {string} method - 'standard', 'minmax', 'robust'
   * @param {Array<string>} columns - Columns to normalize (null = all numeric)
   * @returns {Promise<{success: boolean}>}
   */
  normalizeData: async (sessionId, method = 'standard', columns = null) => {
    const response = await api.post(`/preview/${sessionId}/preprocess/normalize`, null, {
      params: { 
        method,
        columns: columns ? columns.join(',') : null
      }
    });
    return response.data;
  },

  /**
   * Save preprocessed data to flexible_dataset_wide
   * @param {string} sessionId - Preview session UUID
   * @param {string} datasetType - Final dataset type
   * @param {string} datasetSource - Source description
   * @returns {Promise<{success: boolean, batch_id: string, records_saved: number}>}
   */
  savePreprocessed: async (sessionId, datasetType, datasetSource = null) => {
    const response = await api.post(`/preview/${sessionId}/save-preprocessed`, null, {
      params: { dataset_type: datasetType, dataset_source: datasetSource }
    });
    return response.data;
  },

  /**
   * Get preview of preprocessing changes (before/after)
   * @param {string} sessionId - Preview session UUID
   * @param {number} rows - Number of rows to preview
   * @returns {Promise<{before: array, after: array}>}
   */
  getPreprocessingPreview: async (sessionId, rows = 20) => {
    const response = await api.get(`/preview/${sessionId}/preview`, {
      params: { rows }
    });
    return response.data;
  }
};

// ========================================
// LABEL ASSIGNMENT API
// ========================================
export const labelingAPI = {
  /**
   * Assign label to single record
   * @param {string} recordId - Record ID
   * @param {string} label - Label value
   * @param {number} confidence - Confidence (0-1)
   * @param {string} notes - Optional notes
   * @param {string} targetColumn - Target column path
   * @returns {Promise<{success: boolean}>}
   */
  assignLabel: async (recordId, label, confidence = 1.0, notes = null, targetColumn = 'labels_disease_classification') => {
    const response = await api.post('/labeling/assign', {
      record_id: recordId,
      label: label,
      confidence: confidence,
      notes: notes
    }, {
      params: { target_column: targetColumn }
    });
    return response.data;
  },

  /**
   * Bulk assign same label to multiple records
   * @param {Array<string>} recordIds - Array of record IDs
   * @param {string} label - Label value
   * @param {number} confidence - Confidence
   * @param {string} targetColumn - Target column
   * @returns {Promise<{success: boolean, records_labeled: number}>}
   */
  bulkAssignLabels: async (recordIds, label, confidence = 1.0, targetColumn = 'labels_disease_classification') => {
    const response = await api.post('/labeling/bulk-assign', {
      record_ids: recordIds,
      label: label,
      confidence: confidence
    }, {
      params: { target_column: targetColumn }
    });
    return response.data;
  },

  /**
   * Assign label to entire batch
   * @param {string} batchId - Batch UUID
   * @param {string} label - Label value
   * @param {string} targetColumn - Target column
   * @returns {Promise<{success: boolean, records_labeled: number}>}
   */
  batchAssignLabel: async (batchId, label, targetColumn = 'labels_disease_classification') => {
    const response = await api.post('/labeling/batch-assign', {
      batch_id: batchId,
      label: label,
      confidence: 1.0
    }, {
      params: { target_column: targetColumn }
    });
    return response.data;
  },

  /**
   * Get unlabeled records
   * @param {string} batchId - Filter by batch ID
   * @param {string} targetColumn - Target column
   * @param {number} limit - Max results
   * @returns {Promise<{records: array, total: number}>}
   */
  getUnlabeledRecords: async (batchId = null, targetColumn = 'labels_disease_classification', limit = 100) => {
    const params = {
      target_column: targetColumn,
      limit: limit
    };
    if (batchId) params.batch_id = batchId;

    const response = await api.get('/labeling/unlabeled', { params });
    return response.data;
  },

  /**
   * Get label statistics for a batch
   * @param {string} batchId - Batch UUID
   * @param {string} targetColumn - Target column
   * @returns {Promise<{total: number, labeled_count: number, label_distribution: object}>}
   */
  getLabelStatistics: async (batchId = null, targetColumn = 'labels_disease_classification') => {
    const params = { target_column: targetColumn };
    if (batchId) params.import_batch_id = batchId;

    const response = await api.get('/labeling/statistics', { params });
    return response.data;
  },

  /**
   * Auto-label based on existing column (e.g., SLEDAI scores)
   * @param {string} batchId - Batch UUID (optional)
   * @param {string} sourceColumn - Source column to derive labels from
   * @param {string} targetColumn - Target column to store labels
   * @param {string} labelType - Label type: 'severity', 'kidney', 'activity'
   * @returns {Promise<{success: boolean, labeled_count: number, skipped_count: number}>}
   */
  autoLabel: async (batchId, sourceColumn, targetColumn = 'labels_disease_severity', labelType = 'severity') => {
    const response = await api.post('/labeling/auto-label', {
      batch_id: batchId || null,
      source_column: sourceColumn,
      target_column: targetColumn,
      label_type: labelType
    });
    return response.data;
  },

  /**
   * Preview auto-labeling (dry run to show what would be labeled)
   * @param {string} batchId - Batch UUID
   * @param {string} sourceColumn - Source column
   * @param {string} labelType - Label type
   * @returns {Promise<{preview: object}>}
   */
  previewAutoLabel: async (batchId, sourceColumn, labelType = 'severity') => {
    // This would be implemented on backend to return preview without saving
    // For now, we'll use client-side preview
    const stats = await labelingAPI.getLabelStatistics(batchId);
    return { preview: stats };
  }
};

// ========================================
// ML VALIDATION & PREPARATION API
// ========================================
export const mlPreparationAPI = {
  /**
   * Validate batch is ready for ML training
   * @param {string} batchId - Batch UUID
   * @param {string} targetColumn - Target column
   * @param {number} minSamples - Minimum samples required
   * @returns {Promise<{status: string, can_proceed: boolean, issues: array, warnings: array}>}
   */
  validateForML: async (batchId, targetColumn = 'labels_disease_classification', minSamples = 100) => {
    const response = await api.get(`/ml/validate/${batchId}`, {
      params: { target_column: targetColumn, min_samples: minSamples }
    });
    return response.data;
  },

  /**
   * Get labeling progress for batch
   * @param {string} batchId - Batch UUID
   * @param {string} targetColumn - Target column
   * @returns {Promise<{total: number, labeled: number, unlabeled: number, percentage: number}>}
   */
  getLabelingProgress: async (batchId, targetColumn = 'labels_disease_classification') => {
    const response = await api.get(`/ml/labeling-progress/${batchId}`, {
      params: { target_column: targetColumn }
    });
    return response.data;
  },

  /**
   * Prepare dataset for training (with preprocessing)
   * @param {string} batchId - Batch UUID
   * @param {object} config - Training dataset configuration
   * @returns {Promise<{success: boolean, dataset_id: string, metadata: object}>}
   */
  prepareDataset: async (batchId, config) => {
    const response = await api.post('/ml/train/prepare-dataset', {
      batch_id: batchId,
      target_column: config.targetColumn || 'labels_disease_classification',
      test_size: config.testSize || 0.2,
      random_state: config.randomState || 42,
      
      // Preprocessing options (research-aligned)
      apply_imputation: config.applyImputation !== false,
      imputation_numeric_strategy: config.imputationNumericStrategy || 'median',
      imputation_categorical_strategy: config.imputationCategoricalStrategy || 'most_frequent',
      
      apply_winsorization: config.applyWinsorization !== false,
      winsorize_limits: config.winsorize_limits || [0.01, 0.01],
      
      apply_composite_features: config.applyCompositeFeatures !== false,
      composite_low_percentile: config.compositeLowPercentile || 10.0,
      composite_high_percentile: config.compositeHighPercentile || 70.0,
      
      // LASSO feature selection
      use_lasso_feature_selection: config.useLASSO !== false,
      lasso_alpha: config.lassoAlpha || 0.01,
      
      // Scaling
      scaling_strategy: config.scalingStrategy || 'standard',
      create_separate_feature_sets: config.createSeparateSets !== false
    });
    return response.data;
  }
};

// ========================================
// EDA (Exploratory Data Analysis) API
// ========================================
export const edaAPI = {
  /**
   * Get statistical summary for dataset
   * @param {string} batchId - Batch UUID
   * @returns {Promise<{summary_stats: object, column_types: object}>}
   */
  getStatisticalSummary: async (batchId) => {
    const response = await api.get(`/eda/summary/${batchId}`);
    return response.data;
  },

  /**
   * Get correlation matrix
   * @param {string} batchId - Batch UUID
   * @param {string} method - 'pearson', 'spearman', 'kendall'
   * @returns {Promise<{correlation_matrix: array, feature_names: array}>}
   */
  getCorrelationMatrix: async (batchId, method = 'pearson') => {
    const response = await api.get(`/eda/correlation/${batchId}`, {
      params: { method }
    });
    return response.data;
  },

  /**
   * Get feature distribution
   * @param {string} batchId - Batch UUID
   * @param {string} featureName - Feature to analyze
   * @returns {Promise<{histogram: array, kde: array, stats: object}>}
   */
  getFeatureDistribution: async (batchId, featureName) => {
    const response = await api.get(`/eda/distribution/${batchId}`, {
      params: { feature_name: featureName }
    });
    return response.data;
  },

  /**
   * Get missing data heatmap
   * @param {string} batchId - Batch UUID
   * @returns {Promise<{missing_matrix: array, missing_percentage: object}>}
   */
  getMissingDataHeatmap: async (batchId) => {
    const response = await api.get(`/eda/missing-data/${batchId}`);
    return response.data;
  },

  /**
   * Generate automated insights using AI
   * @param {string} batchId - Batch UUID
   * @returns {Promise<{insights: array, recommendations: array}>}
   */
  generateInsights: async (batchId) => {
    const response = await api.post(`/eda/insights/${batchId}`);
    return response.data;
  }
};

// ========================================
// ML TRAINING API
// ========================================
export const trainingAPI = {
  /**
   * Train a single base model
   * @param {object} config - Training configuration
   * @returns {Promise<{job_id: string, status: string}>}
   */
  trainBaseModel: async (config) => {
    const response = await api.post('/ml/train/base-model', {
      model_name: config.model_name,
      dataset_id: config.dataset_id,
      n_trials: config.n_trials || 100,
      cv_folds: config.cv_folds || 5,
      use_selected_features: config.use_selected_features !== undefined ? config.use_selected_features : true
    });
    return response.data;
  },

  /**
   * Train ensemble model
   * @param {object} config - Ensemble configuration
   * @returns {Promise<{job_id: string, status: string}>}
   */
  trainEnsemble: async (config) => {
    const response = await api.post('/ml/train/ensemble', {
      dataset_id: config.datasetId || config.dataset_id,  // Dataset job ID
      base_model_jobs: config.baseModelJobs || config.base_model_jobs,  // Base model job IDs
      meta_learner_type: config.metaLearnerType || config.meta_learner_type || 'logistic_regression',
      target_column: config.targetColumn || 'labels_disease_classification',
      batch_id: config.batchId || config.batch_id  // Optional, for metadata
    });
    return response.data;
  },

  /**
   * Get training job status (for polling)
   * @param {string} jobId - Training job ID
   * @returns {Promise<{status: string, progress: object, result: object}>}
   */
  getJobStatus: async (jobId) => {
    const response = await api.get(`/ml/train/status/${jobId}`);
    return response.data;
  },

  /**
   * Get training history
   * @param {number} limit - Max results
   * @returns {Promise<{jobs: array, total_count: number}>}
   */
  getTrainingHistory: async (limit = 50) => {
    const response = await api.get('/ml/training-history', {
      params: { limit }
    });
    return response.data;
  },

  /**
   * Get list of all trained models
   * @param {number} limit - Maximum number of models to return
   * @returns {Promise<{models: array, total_count: number}>}
   */
  getModels: async (limit = 1000) => {
    const response = await api.get(`/ml/models/list?limit=${limit}`);
    return response.data;
  },

  /**
   * Sync models from MinIO to database
   * @returns {Promise<Object>}
   */
  syncModelsFromMinIO: async () => {
    const response = await api.post('/ml/models/sync-from-minio');
    return response.data;
  },

  /**
   * Get detailed metrics for a model
   * @param {string} modelId - Model ID
   * @returns {Promise<{metrics: object, confusion_matrix: array, roc_curve: object}>}
   */
  getModelMetrics: async (modelId) => {
    const response = await api.get(`/ml/models/${modelId}/metrics`);
    return response.data;
  },

  /**
   * Compare multiple models
   * @param {Array<string>} modelIds - Array of model IDs
   * @returns {Promise<{models: array, best_by_metric: object, recommendations: array}>}
   */
  compareModels: async (modelIds) => {
    const response = await api.post('/ml/models/compare', {
      model_ids: modelIds
    });
    return response.data;
  }
};

// ========================================
// CLINICAL SCORECARD API (Final Step)
// ========================================
export const scorecardAPI = {
  /**
   * Generate clinical scorecard from trained model
   * @param {string} modelId - Model ID
   * @param {object} config - Scorecard configuration
   * @returns {Promise<{scorecard_id: string, bin_tables: array, threshold: number}>}
   */
  generateScorecard: async (modelId, config = {}) => {
    const response = await api.post('/scorecard/generate', {
      model_id: modelId,
      binning_method: config.binningMethod || 'rolling_mean',
      num_bins: config.numBins || 4,
      use_youden_optimization: config.useYouden !== false
    });
    return response.data;
  },

  /**
   * Get bin-score tables for a feature
   * @param {string} scorecardId - Scorecard ID
   * @param {string} featureName - Feature name (null = all features)
   * @returns {Promise<{feature_name: string, bin_tables: array}>}
   */
  getBinScoreTables: async (scorecardId, featureName = null) => {
    const response = await api.get(`/scorecard/${scorecardId}/bin-tables`, {
      params: { feature_name: featureName }
    });
    return response.data;
  },

  /**
   * Get risk stratification metrics
   * @param {string} scorecardId - Scorecard ID
   * @returns {Promise<{threshold: number, youden_index: number, sensitivity: number, specificity: number}>}
   */
  getRiskStratification: async (scorecardId) => {
    const response = await api.get(`/scorecard/${scorecardId}/risk-stratification`);
    return response.data;
  },

  /**
   * Calculate patient score
   * @param {string} scorecardId - Scorecard ID
   * @param {object} patientData - Patient feature values
   * @returns {Promise<{total_score: number, risk_group: string, feature_scores: array}>}
   */
  calculatePatientScore: async (scorecardId, patientData) => {
    const response = await api.post(`/scorecard/${scorecardId}/calculate-score`, {
      patient_data: patientData
    });
    return response.data;
  },

  /**
   * Export scorecard to CSV
   * @param {string} scorecardId - Scorecard ID
   * @param {string} exportType - 'bin_tables', 'threshold_report', 'patient_scores', 'comprehensive'
   * @returns {Promise<Blob>}
   */
  exportScorecardCSV: async (scorecardId, exportType = 'comprehensive') => {
    const response = await api.get(`/scorecard/${scorecardId}/export`, {
      params: { export_type: exportType },
      responseType: 'blob'
    });
    return response.data;
  }
};

// ========================================
// MODEL EXPLAINABILITY API
// ========================================
export const explainabilityAPI = {
  /**
   * Get SHAP explanation for a prediction
   * @param {string} modelId - Model ID
   * @param {object} patientData - Patient features
   * @param {number} topK - Number of top features
   * @returns {Promise<{base_value: number, shap_values: object, waterfall_plot: string}>}
   */
  getSHAPExplanation: async (modelId, patientData, topK = 10) => {
    const response = await api.post('/ml/explain', {
      model_name: modelId,
      patient_data: patientData,
      top_k: topK,
      generate_plot: true
    });
    return response.data;
  },

  /**
   * Get SHAP explanation using a training job ID (recommended)
   * @param {string} jobId - Training job ID from models/list (model_id field)
   * @param {object} patientData - Patient features
   * @param {number} topK - Number of top features
   * @returns {Promise<SHAPExplanationResponse>}
   */
  getSHAPByJobId: async (jobId, patientData, topK = 10) => {
    const response = await api.post('/ml/explain/by-job', {
      job_id: jobId,
      patient_data: patientData,
      top_k: topK,
      generate_plot: true
    });
    return response.data;
  },

  /**
   * Get global feature importance
   * @param {string} modelId - Model ID
   * @returns {Promise<{feature_importance: array}>}
   */
  getGlobalFeatureImportance: async (modelId) => {
    const response = await api.get(`/ml/global-importance/${modelId}`);
    return response.data;
  },

  /**
   * Generate LLM-powered natural language explanation
   * @param {string} modelId - Model ID
   * @param {object} patientData - Patient features
   * @param {string} detailLevel - 'brief', 'moderate', 'detailed'
   * @returns {Promise<{explanation: string, key_factors: array, recommendations: array}>}
   */
  generateLLMExplanation: async (modelId, patientData, detailLevel = 'moderate') => {
    const response = await api.post('/ml/explain-prediction-nl', {
      prediction_result: {
        model_id: modelId,
        detail_level: detailLevel,
        patient_data: patientData,
      },
      shap_explanation: null,
    });
    return response.data;
  },

  /**
   * Chat with Dr. Myra AI assistant (Gemma + SHAP)
   * @param {string} message - User's message
   * @param {object} context - Optional context (prediction, SHAP, patient data)
   * @param {array} conversationHistory - Previous messages
   * @param {number} temperature - Sampling temperature (0-1)
   * @returns {Promise<{response: string, model: string, tokens_generated: number}>}
   */
  chatWithDrMyra: async (message, context = null, conversationHistory = null, temperature = 0.7) => {
    console.log('🤖 Dr. Myra API Call:', { message, context, historyLength: conversationHistory?.length || 0 });
    const response = await api.post('/ml/chat', {
      message,
      context,
      conversation_history: conversationHistory,
      temperature
    });
    console.log('✅ Dr. Myra Response:', response.data);
    return response.data;
  }
};

// ========================================
// BATCH PREDICTION API
// ========================================
export const batchPredictionAPI = {
  /**
   * Upload CSV for batch prediction
   * @param {string} modelId - Model ID
   * @param {File} file - CSV file with patient features
   * @param {boolean} includeSHAP - Include SHAP explanations
   * @returns {Promise<{prediction_job_id: string, patients_count: number}>}
   */
  uploadForPrediction: async (modelId, file, includeSHAP = false) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_id', modelId);
    formData.append('include_shap', includeSHAP);
    
    const response = await api.post('/predict/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  /**
   * Get prediction results
   * @param {string} predictionJobId - Prediction job ID
   * @returns {Promise<{predictions: array, summary: object}>}
   */
  getPredictionResults: async (predictionJobId) => {
    const response = await api.get(`/predict/results/${predictionJobId}`);
    return response.data;
  },

  /**
   * Export predictions to CSV
   * @param {string} predictionJobId - Prediction job ID
   * @returns {Promise<Blob>}
   */
  exportPredictions: async (predictionJobId) => {
    const response = await api.get(`/predict/export/${predictionJobId}`, {
      responseType: 'blob'
    });
    return response.data;
  }
};

// PREDICTION HISTORY API
// ========================================
export const predictionHistoryAPI = {
  /**
   * Get list of all batch predictions
   * @param {number} limit - Max results
   * @returns {Promise<{predictions: array, total_count: number}>}
   */
  getHistory: async (limit = 50) => {
    const response = await api.get('/ml/predictions/history', {
      params: { limit }
    });
    return response.data;
  },

  /**
   * Download prediction results CSV
   * @param {string} batchId - Batch ID
   * @param {string} minioPath - MinIO path
   * @returns {Promise<Blob>}
   */
  downloadResults: async (batchId, minioPath) => {
    const response = await api.get(`/predict/predictions/${batchId}/download`, {
      params: { minio_path: minioPath },
      responseType: 'blob'
    });
    return response.data;
  }
};

// Export all APIs
export default {
  unstructuredPipelineAPI,
  structuredPipelineAPI,
  preprocessingAPI,
  labelingAPI,
  mlPreparationAPI,
  edaAPI,
  trainingAPI,
  scorecardAPI,
  explainabilityAPI,
  batchPredictionAPI,
  predictionHistoryAPI
};
