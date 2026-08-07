import axios from 'axios';

const API_BASE_URL = '/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(
            `${API_BASE_URL}/auth/refresh?refresh_token=${refreshToken}`
          );
          
          const { access_token, refresh_token } = response.data;
          
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, logout
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await axios.post(`${API_BASE_URL}/auth/login`, formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    
    return response.data;
  },

  register: async (userData) => {
    const response = await axios.post(`${API_BASE_URL}/auth/register`, userData);
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  logout: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    const accessToken = localStorage.getItem('access_token');
    
    if (refreshToken && accessToken) {
      await api.post(
        `/auth/logout?refresh_token=${refreshToken}`,
        {},
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
    }
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  getSessions: async () => {
    const response = await api.get('/auth/sessions');
    return response.data;
  },
};

// Admin API
export const adminAPI = {
  getTokenStats: async () => {
    const response = await api.get('/auth/admin/token-stats');
    return response.data;
  },

  getAllSessions: async (params = {}) => {
    const response = await api.get('/auth/admin/sessions', { params });
    return response.data;
  },

  revokeSession: async (tokenId) => {
    const response = await api.delete(`/auth/admin/sessions/${tokenId}`);
    return response.data;
  },
  
  getStats: async () => {
    const response = await api.get('/admin/stats');
    return response.data;
  },
};

// Unstructured Data Pipeline API
export const unstructuredAPI = {
  /**
   * Upload unstructured file (PDF, TXT, Image) for OCR processing
   * @param {File} file - File object to upload
   * @returns {Promise<{success: boolean, validation_id: number, filename: string, minio_path: string, extracted_text: string, medical_entities: array}>}
   */
  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/unstructured/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    return response.data;
  },

  /**
   * Get preview of processed unstructured data
   * @param {number} validationId - Validation queue ID
   * @returns {Promise<{validation_id: number, stage: string, status: string, data: object}>}
   */
  getPreview: async (validationId) => {
    const response = await api.get(`/unstructured/preview/${validationId}`);
    return response.data;
  },

  /**
   * Approve processed data and move to production
   * @param {number} validationId - Validation queue ID
   * @returns {Promise<{success: boolean, message: string, validation_id: number}>}
   */
  approve: async (validationId) => {
    const response = await api.post(`/unstructured/approve/${validationId}`);
    return response.data;
  },

  /**
   * Reject processed data with reason
   * @param {number} validationId - Validation queue ID
   * @param {string} reason - Rejection reason
   * @returns {Promise<{success: boolean, message: string, validation_id: number}>}
   */
  reject: async (validationId, reason) => {
    const response = await api.post(`/unstructured/reject/${validationId}`, { reason });
    return response.data;
  },

  /**
   * List all processed unstructured files
   * @param {number} limit - Maximum number of results (default: 50)
   * @returns {Promise<Array<{validation_id: number, filename: string, status: string, created_at: string, page_count: number, entity_count: number}>>}
   */
  list: async (limit = 50) => {
    const response = await api.get(`/unstructured/list?limit=${limit}`);
    return response.data;
  },
};

// Structured Data Upload API
export const uploadAPI = {
  /**
   * Preview structured data WITHOUT saving to database
   * Allows researcher to review and edit before import
   * @param {File} file - CSV or Excel file
   * @param {Object} metadata - Import metadata
   * @returns {Promise<{success: boolean, preview_id: string, rows: array, columns: array, mapping_summary: object}>}
   */
  previewFile: async (file, metadata) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('disease_name', metadata.diseaseName);
    formData.append('dataset_type', metadata.datasetType);
    if (metadata.diseaseCode) {
      formData.append('disease_code', metadata.diseaseCode);
    }
    
    const response = await api.post('/preview/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    return response.data;
  },

  /**
   * Import edited preview data to database
   * This is called AFTER user reviews and edits preview
   * Duplicate checking happens here
   * @param {Object} editedData - Edited data with metadata
   * @returns {Promise<{success: boolean, patients_created: number, statistics: object}>}
   */
  importFromPreview: async (editedData) => {
    const response = await api.post('/preview/import-from-preview', editedData);
    return response.data;
  },

  /**
   * Import structured data from CSV/Excel file
   * @param {File} file - CSV or Excel file
   * @param {Object} metadata - Import metadata
   * @param {string} metadata.diseaseName - Disease name (e.g., 'Systemic Lupus Erythematosus')
   * @param {string} metadata.datasetType - Dataset identifier (e.g., 'SLE', 'SJOGREN')
   * @param {string} metadata.diseaseCode - ICD-10 code (optional)
   * @param {boolean} metadata.autoApprove - Auto-approve new test definitions (default: false)
   * @returns {Promise<{success: boolean, patients_created: number, rows_imported: number, errors: array}>}
   */
  importFile: async (file, metadata) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('disease_name', metadata.diseaseName);
    formData.append('dataset_type', metadata.datasetType);
    if (metadata.diseaseCode) {
      formData.append('disease_code', metadata.diseaseCode);
    }
    formData.append('auto_approve_tests', metadata.autoApprove || false);
    
    const response = await api.post('/upload/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    return response.data;
  },
};

// Dataset Versioning API
export const datasetVersionsAPI = {
  /**
   * Create new dataset version
   * @param {Object} versionData - Version metadata
   * @returns {Promise<{dataset_id: string, semantic_version: string, is_production: boolean}>}
   */
  createVersion: async (versionData) => {
    const response = await api.post('/dataset-versions/versions', versionData);
    return response.data;
  },

  /**
   * List all versions of a dataset
   * @param {string} datasetName - Dataset name
   * @param {Object} params - Query parameters
   * @returns {Promise<Array>}
   */
  listVersions: async (datasetName, params = {}) => {
    const response = await api.get(`/dataset-versions/datasets/${datasetName}/versions`, { params });
    return response.data;
  },

  /**
   * Get version lineage (family tree)
   * @param {string} datasetId - Dataset UUID
   * @returns {Promise<{current: object, all_versions: array, ancestors_count: number, descendants_count: number}>}
   */
  getLineage: async (datasetId) => {
    const response = await api.get(`/dataset-versions/datasets/${datasetId}/lineage`);
    return response.data;
  },

  /**
   * Promote version to production
   * @param {string} datasetId - Dataset UUID
   * @param {string} notes - Promotion notes
   * @returns {Promise<{message: string, dataset_id: string, version: string}>}
   */
  promote: async (datasetId, notes) => {
    const response = await api.post(`/dataset-versions/datasets/${datasetId}/promote`, { notes });
    return response.data;
  },

  /**
   * Add tags to version
   * @param {string} datasetId - Dataset UUID
   * @param {Array<string>} tags - Tags to add
   * @returns {Promise<{message: string, dataset_id: string, version: string}>}
   */
  addTags: async (datasetId, tags) => {
    const params = new URLSearchParams();
    tags.forEach(tag => params.append('tags', tag));
    
    const response = await api.post(`/dataset-versions/datasets/${datasetId}/tag?${params.toString()}`);
    return response.data;
  },

  /**
   * List all production datasets
   * @returns {Promise<Array>}
   */
  listProduction: async () => {
    const response = await api.get('/dataset-versions/production');
    return response.data;
  },
};

// Patients Data API
export const patientsAPI = {
  /**
   * Search/list patients with pagination
   * @param {Object} params - Query parameters
   * @param {number} params.limit - Results per page (default: 50)
   * @param {number} params.offset - Page offset (default: 0)
   * @param {string} params.disease_name - Filter by disease name
   * @param {string} params.gender - Filter by gender
   * @param {number} params.age_min - Minimum age
   * @param {number} params.age_max - Maximum age
   * @param {string} params.batch_id - Filter by import batch ID (UUID)
   * @returns {Promise<{patients: Array, total: number, limit: number, offset: number}>}
   */
  listPatients: async (params = {}) => {
    const response = await api.get('/patients/', { params });
    return response.data;
  },

  /**
   * Get single patient details
   * @param {number} patientId - Patient ID
   * @returns {Promise<Object>}
   */
  getPatient: async (patientId) => {
    const response = await api.get(`/patients/${patientId}`);
    return response.data;
  },

  /**
   * Get patient summary statistics
   * @param {number} patientId - Patient ID
   * @returns {Promise<Object>}
   */
  getPatientSummary: async (patientId) => {
    const response = await api.get(`/patients/${patientId}/summary`);
    return response.data;
  },
};

// ===================================================
// FLEXIBLE DATA PIPELINE API (NEW UNIFIED WORKFLOW)
// ===================================================
export const flexibleAPI = {
  // ========== STRUCTURED DATA (CSV/Excel) ==========
  
  /**
   * Upload CSV/Excel for preview and editing
   * @param {File} file - CSV or Excel file
   * @param {string} datasetType - Dataset type (e.g., 'SLE_Clinical', 'Lab_Results')
   * @returns {Promise<{success: boolean, session_id: string, row_count: number, columns: array}>}
   */
  uploadStructured: async (file, datasetType = 'General') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('dataset_type', datasetType);
    
    const response = await api.post('/flexible/preview/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    return response.data;
  },

  /**
   * Get editable preview with pagination
   * @param {string} sessionId - Preview session UUID
   * @param {number} page - Page number (1-indexed)
   * @param {number} pageSize - Rows per page
   * @returns {Promise<{session_id: string, total_rows: number, rows: array, schema: object}>}
   */
  getPreview: async (sessionId, page = 1, pageSize = 20) => {
    const response = await api.get(
      `/flexible/preview/${sessionId}`,
      { params: { page, page_size: pageSize } }
    );
    return response.data;
  },

  /**
   * Edit a single cell in preview
   * @param {string} sessionId - Preview session UUID
   * @param {number} stagingId - Row staging ID
   * @param {string} columnName - Column to edit
   * @param {any} newValue - New value (can be string, number, boolean, null)
   * @returns {Promise<{success: boolean, staging_id: number, updated_data: object}>}
   */
  editCell: async (sessionId, stagingId, columnName, newValue) => {
    const response = await api.patch(
      `/flexible/preview/${sessionId}/row/${stagingId}`,
      { column_name: columnName, new_value: newValue }
    );
    return response.data;
  },

  /**
   * Delete a row from preview
   * @param {string} sessionId - Preview session UUID
   * @param {number} stagingId - Row staging ID
   * @returns {Promise<{success: boolean, message: string}>}
   */
  deleteRow: async (sessionId, stagingId) => {
    const response = await api.delete(`/flexible/preview/${sessionId}/row/${stagingId}`);
    return response.data;
  },

  /**
   * Save preview to permanent storage (flexible_dataset_wide table)
   * @param {string} sessionId - Preview session UUID
   * @param {string} datasetName - Optional final dataset name
   * @returns {Promise<{success: boolean, batch_id: string, statistics: object}>}
   */
  saveToDatabase: async (sessionId, datasetName = null) => {
    const payload = datasetName ? { final_dataset_name: datasetName } : {};
    const response = await api.post(`/flexible/preview/${sessionId}/save`, payload);
    return response.data;
  },

  // ========== UNSTRUCTURED DATA (PDF/IMG/TXT) ==========
  
  /**
   * Upload unstructured file for OCR processing
   * @param {File} file - PDF, PNG, JPG, or TXT file
   * @returns {Promise<{success: boolean, validation_id: number, extracted_text: string, page_count: number}>}
   */
  uploadUnstructured: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/unstructured/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    return response.data;
  },

  /**
   * Convert OCR result to editable tabular preview
   * @param {number} validationId - OCR record ID from unstructured_document_processed 
   * @param {string} datasetType - Dataset classification (e.g., 'Medical_Lab_Report')
   * @param {string} conversionMode - 'grouped' or 'individual'
   * @returns {Promise<{success: boolean, session_id: string, row_count: number}>}
   */
  convertUnstructuredToTabular: async (validationId, datasetType = 'OCR_Generic', conversionMode = 'grouped') => {
    const response = await api.post('/flexible/unstructured/convert', {
      validation_id: validationId,
      dataset_type: datasetType,
      conversion_mode: conversionMode
    });
    return response.data;
  },

  /**
   * Get raw OCR data before conversion
   * @param {number} validationId - OCR record ID
   * @returns {Promise<{validation_id: number, extracted_text: string, medical_entities: array}>}
   */
  getOCRPreview: async (validationId) => {
    const response = await api.get(`/unstructured/preview/${validationId}`);
    return response.data;
  },

  // ========== DATASET MANAGEMENT ==========
  
  /**
   * List all datasets in flexible_dataset_wide
   * @param {number} limit - Results limit
   * @param {number} offset - Pagination offset
   * @returns {Promise<{datasets: array, total: number}>}
   */
  listDatasets: async (limit = 50, offset = 0) => {
    const response = await api.get('/flexible/datasets', { params: { limit, offset } });
    return response.data;
  },

  /**
   * Get dataset by type
   * @param {string} datasetType - Dataset type filter
   * @returns {Promise<{dataset_type: string, records: array, row_count: number}>}
   */
  getDatasetByType: async (datasetType) => {
    const response = await api.get(`/flexible/datasets/${datasetType}`);
    return response.data;
  },

  /**
   * Get recent uploads for ML Preparation Queue
   * @param {number} limit - Number of uploads to retrieve
   * @param {boolean} includeStaging - Include preview uploads
   * @param {boolean} includeSaved - Include saved datasets
   * @returns {Promise<{total: number, uploads: array}>}
   */
  getRecentUploads: async (limit = 20, includeStaging = true, includeSaved = true) => {
    const response = await api.get('/flexible/recent-uploads', {
      params: { limit, include_staging: includeStaging, include_saved: includeSaved }
    });
    return response.data;
  },

  /**
   * Delete an upload session from database
   * @param {string} sessionId - Session ID to delete
   * @returns {Promise<{success: boolean, message: string}>}
   */
  deleteUploadSession: async (sessionId) => {
    const response = await api.delete(`/flexible/preview/${sessionId}`);
    return response.data;
  },
};
// ========== LAYER 5: PREPROCESSING & DATA CLEANING API ==========
// Connected to import_preview_staging → Apply Preprocessing → flexible_dataset_wide → ML Pipeline
export const preprocessingAPI = {
  // Get quality report for staging session
  getQualityReport: async (sessionId) => {
    const response = await api.get(`/preview/${sessionId}/quality`);
    return response.data;
  },
  
  // Get problematic rows for interactive cleaning
  getProblematicRows: async (sessionId) => {
    const response = await api.get(`/preview/${sessionId}/problematic-rows`);
    return response.data;
  },
  
  // Clean selected rows
  cleanSelectedRows: async (sessionId, config) => {
    const response = await api.post(`/preview/${sessionId}/clean-selected`, config);
    return response.data;
  },

  // Handle missing values in staging data
  handleMissingValues: async (sessionId, config) => {
    const response = await api.post(`/preview/${sessionId}/preprocess/missing-values`, null, {
      params: {
        method: config.method,
        threshold: config.threshold
      }
    });
    return response.data;
  },

  // Remove duplicates from staging data
  removeDuplicates: async (sessionId, keepFirst = true) => {
    const response = await api.post(`/preview/${sessionId}/preprocess/duplicates`, null, {
      params: {
        keep_first: keepFirst
      }
    });
    return response.data;
  },

  // Handle outliers in staging data
  handleOutliers: async (sessionId, method, threshold) => {
    const response = await api.post(`/preview/${sessionId}/preprocess/outliers`, null, {
      params: {
        method,
        threshold
      }
    });
    return response.data;
  },
  
  // Aggregate patient records (consolidate duplicates)
  aggregatePatients: async (sessionId, patientIdColumn = 'patient_id', strategy = 'latest') => {
    const response = await api.post(`/preview/${sessionId}/preprocess/aggregate-patients`, null, {
      params: {
        patient_id_column: patientIdColumn,
        strategy: strategy
      }
    });
    return response.data;
  },

  // Normalize data in staging
  normalizeData: async (sessionId, method, columns = null) => {
    const response = await api.post(`/preview/${sessionId}/preprocess/normalize`, null, {
      params: {
        method,
        columns: columns ? columns.join(',') : null
      }
    });
    return response.data;
  },

  // Get preview of preprocessed data (before/after comparison)
  getPreview: async (sessionId, rows = 20) => {
    const response = await api.get(`/preview/${sessionId}/preview`, {
      params: { rows }
    });
    return response.data;
  },

  // Save preprocessed data to flexible_dataset_wide (final step)
  savePreprocessed: async (sessionId, datasetType, datasetSource = null) => {
    const response = await api.post(`/preview/${sessionId}/save-preprocessed`, null, {
      params: {
        dataset_type: datasetType,
        dataset_source: datasetSource
      }
    });
    return response.data;
  }
};

// ========== ML VALIDATION API ==========
// Check if data is ready for ML training (flexible - warns but doesn't block)
export const mlValidationAPI = {
  // Validate specific batch for ML training
  validateBatch: async (batchId, targetColumn = 'labels_disease_classification', minSamples = 100) => {
    const response = await api.get(`/ml/validate/${batchId}`, {
      params: {
        target_column: targetColumn,
        min_samples: minSamples
      }
    });
    return response.data;
  },

  // Validate entire dataset type
  validateDatasetType: async (datasetType, targetColumn = 'labels_disease_classification', minSamples = 100) => {
    const response = await api.get(`/ml/validate/dataset-type/${datasetType}`, {
      params: {
        target_column: targetColumn,
        min_samples: minSamples
      }
    });
    return response.data;
  },

  // Get labeling progress for batch
  getLabelingProgress: async (batchId, targetColumn = 'labels_disease_classification') => {
    const response = await api.get(`/ml/labeling-progress/${batchId}`, {
      params: {
        target_column: targetColumn
      }
    });
    return response.data;
  }
};

// ========== LABEL ASSIGNMENT API ==========
// User-controlled labeling for ML training target variable
export const labelingAPI = {
  // Assign label to single record
  assignLabel: async (recordId, label, confidence = 1.0, notes = null, targetColumn = 'labels_disease_classification') => {
    const response = await api.post('/labeling/assign', {
      record_id: recordId,
      label: label,
      confidence: confidence,
      notes: notes
    }, {
      params: {
        target_column: targetColumn
      }
    });
    return response.data;
  },

  // Bulk assign same label to multiple records
  bulkAssignLabels: async (recordIds, label, confidence = 1.0, notes = null, targetColumn = 'labels_disease_classification') => {
    const response = await api.post('/labeling/bulk-assign', {
      record_ids: recordIds,
      label: label,
      confidence: confidence,
      notes: notes
    }, {
      params: {
        target_column: targetColumn
      }
    });
    return response.data;
  },

  // Assign same label to entire import batch
  batchAssignLabel: async (batchId, label, confidence = 1.0, notes = null, targetColumn = 'labels_disease_classification') => {
    const response = await api.post('/labeling/batch-assign', {
      batch_id: batchId,
      label: label,
      confidence: confidence,
      notes: notes
    }, {
      params: {
        target_column: targetColumn
      }
    });
    return response.data;
  },

  // Get unlabeled records
  getUnlabeledRecords: async (datasetType = null, batchId = null, limit = 100, offset = 0, targetColumn = 'labels_disease_classification') => {
    const params = {
      target_column: targetColumn,
      limit: limit,
      offset: offset
    };
    if (datasetType) params.dataset_type = datasetType;
    if (batchId) params.batch_id = batchId;

    const response = await api.get('/labeling/unlabeled', { params });
    return response.data;
  },

  // Get label statistics
  getLabelStatistics: async (datasetType = null, batchId = null, targetColumn = 'labels_disease_classification') => {
    const params = {
      target_column: targetColumn
    };
    if (datasetType) params.dataset_type = datasetType;
    if (batchId) params.import_batch_id = batchId;

    const response = await api.get('/labeling/statistics', { params });
    return response.data;
  },

  // Auto-label records based on existing data (e.g., SLEDAI scores)
  autoLabel: async (batchId, sourceColumn, targetColumn = 'labels_disease_severity', labelTypeStrategy = 'severity') => {
    const response = await api.post('/labeling/auto-label', {
      batch_id: batchId,
      source_column: sourceColumn,
      target_column: targetColumn,
      label_type: labelTypeStrategy
    });
    return response.data;
  },

  // Rule-based labeling with custom conditions
  ruleBasedLabel: async (batchId, sourceColumn, rules, targetColumn = 'labels_custom', overwriteExisting = false) => {
    const response = await api.post('/labeling/rule-based-label', {
      batch_id: batchId,
      source_column: sourceColumn,
      rules: rules, // Array of {condition, label, description?}
      target_column: targetColumn,
      overwrite_existing: overwriteExisting
    });
    return response.data;
  }
};

// Dashboard API - aggregates data from multiple endpoints
export const dashboardAPI = {
  /**
   * Get all dashboard statistics
   * Aggregates data from multiple sources
   */
  getAllStats: async (options = {}) => {
    try {
      const { includeAdminStats = false } = options;
      const [uploadsData, labelingData, platformData, modelsData, trainingData] = await Promise.allSettled([
        flexibleAPI.getRecentUploads(100, true, true),
        labelingAPI.getLabelStatistics('labels_disease_classification'),
        includeAdminStats ? adminAPI.getStats() : Promise.resolve({ users: {}, patients: {} }),
        mlAPI.getModels(),
        mlAPI.getTrainingHistory(100),
      ]);
      
      return {
        uploads: uploadsData.status === 'fulfilled' ? uploadsData.value : { total: 0, uploads: [] },
        labeling: labelingData.status === 'fulfilled' ? labelingData.value : { total: 0, labeled_count: 0, unlabeled_count: 0 },
        platform: platformData.status === 'fulfilled' ? platformData.value : { users: {}, patients: {} },
        models: modelsData.status === 'fulfilled' ? modelsData.value : { models: [], total_count: 0 },
        training: trainingData.status === 'fulfilled' ? trainingData.value : { jobs: [], total_count: 0 },
      };
    } catch (error) {
      console.error('Dashboard stats error:', error);
      return {
        uploads: { total: 0, uploads: [] },
        labeling: { total: 0, labeled_count: 0, unlabeled_count: 0 },
        platform: { users: {}, patients: {} },
        models: { models: [], total_count: 0 },
        training: { jobs: [], total_count: 0 },
      };
    }
  },
};

// ML API
export const mlAPI = {
  /**
   * Get list of all trained models
   * @param {number} limit - Maximum number of models to return
   * @returns {Promise<{models: Array}>}
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
   * Get detailed metrics for a specific model
   * @param {string|number} modelId - Model ID
   * @returns {Promise<Object>}
   */
  getModelMetrics: async (modelId) => {
    const response = await api.get(`/ml/models/${modelId}/metrics`);
    return response.data;
  },

  /**
   * Train a new model
   * @param {Object} config - Training configuration
   * @returns {Promise<Object>}
   */
  trainModel: async (config) => {
    const response = await api.post('/ml/train', config);
    return response.data;
  },

  /**
   * Train ensemble model
   * @param {Object} config - Ensemble configuration
   * @returns {Promise<Object>}
   */
  trainEnsemble: async (config) => {
    const response = await api.post('/ml/train/ensemble', config);
    return response.data;
  },

  /**
   * Compare multiple models
   * @param {Array<string|number>} modelIds - Array of model IDs to compare
   * @returns {Promise<Object>}
   */
  compareModels: async (modelIds) => {
    const response = await api.post('/ml/models/compare', { model_ids: modelIds });
    return response.data;
  },

  /**
   * Get training history
   * @param {number} limit - Maximum number of jobs to return
   * @param {string} jobType - Filter by job type
   * @param {string} statusFilter - Filter by status
   * @returns {Promise<Object>}
   */
  getTrainingHistory: async (limit = 50, jobType = null, statusFilter = null) => {
    const params = { limit };
    if (jobType) params.job_type = jobType;
    if (statusFilter) params.status_filter = statusFilter;
    const response = await api.get('/ml/training-history', { params });
    return response.data;
  },

  /**
   * Run LASSO feature selection
   * @param {string} datasetId - Dataset ID
   * @param {number} lambda - Lambda value (alpha) for LASSO
   * @param {number} cvFolds - Number of cross-validation folds
   * @returns {Promise<{job_id: string, status: string}>}
   */
  runFeatureSelection: async (datasetId, lambda = 0.01, cvFolds = 5) => {
    const alphas = [lambda * 0.1, lambda, lambda * 10]; // Try 3 values around lambda
    const response = await api.post('/ml/train/feature-selection', {
      dataset_id: datasetId,
      alphas: alphas,
      cv_folds: cvFolds
    });
    return response.data;
  },

  /**
   * Get training job status
   * @param {string} jobId - Training job ID
   * @returns {Promise<Object>}
   */
  getJobStatus: async (jobId) => {
    const response = await api.get(`/ml/train/status/${jobId}`);
    return response.data;
  },

  /**
   * Apply feature engineering to dataset
   * @param {string} importBatchId - Batch ID to engineer features for
   * @param {Object} config - Feature engineering configuration
   * @returns {Promise<Object>}
   */
  engineerFeatures: async (importBatchId, config = {}) => {
    const response = await api.post('/ml/engineer-features', {
      import_batch_id: importBatchId,
      target_column: config.targetColumn || 'labels_disease_classification',
      // Ratios
      enable_ratios: config.enableRatios !== false,
      crp_esr_ratio: config.crpEsrRatio !== false,
      nlr_ratio: config.nlrRatio !== false,
      plr_ratio: config.plrRatio !== false,
      // Temporal
      enable_temporal: config.enableTemporal !== false,
      disease_duration: config.diseaseDuration !== false,
      // Derived
      enable_derived: config.enableDerived !== false,
      inflammation_score: config.inflammationScore !== false,
      organ_involvement: config.organInvolvement || false
    });
    return response.data;
  },

  /**
   * Get feature engineering status for dataset
   * @param {string} importBatchId - Batch ID
   * @returns {Promise<Object>}
   */
  getFeatureStatus: async (importBatchId) => {
    const response = await api.get(`/ml/feature-status/${importBatchId}`);
    return response.data;
  },

  /**
   * Get target column distribution for a dataset
   * @param {string} sessionId - Dataset session ID
   * @param {string} targetColumn - Target column name
   * @returns {Promise<Object>}
   */
  getTargetDistribution: async (sessionId, targetColumn) => {
    const response = await api.get(`/flexible/preview/${sessionId}`);
    const data = response.data;
    
    // Calculate distribution from rows
    const distribution = {};
    data.rows.forEach(row => {
      const value = row[targetColumn];
      distribution[value] = (distribution[value] || 0) + 1;
    });
    
    return { distribution, total: data.total_rows };
  },

  /**
   * Validate dataset schema for ML training
   * @param {string} batchId - Batch ID to validate
   * @param {string} targetColumn - Target column name
   * @returns {Promise<Object>}
   */
  validateDataset: async (batchId, targetColumn = 'labels_disease_classification') => {
    const response = await api.post(
      `/ml-utils/validate-schema/${batchId}`,
      null,
      {
        params: {
          import_batch_id: batchId,
          target_column: targetColumn,
          min_records: 50
        }
      }
    );
    return response.data;
  },

  /**
   * Get target column distribution for a batch
   * @param {string} batchId - Batch ID
   * @param {string} targetColumn - Target column path (e.g., 'labels_disease_classification')
   * @returns {Promise<{distribution: Object, total: number}>}
   */
  getTargetDistribution: async (batchId, targetColumn = 'labels_disease_classification') => {
    // Use labeling statistics endpoint to get label distribution
    const stats = await labelingAPI.getLabelStatistics(null, batchId);
    
    return {
      distribution: stats.label_distribution || {},
      total: stats.total_records || 0,
      labeled_count: stats.labeled_count || 0
    };
  },

  /**
   * Get available columns from a batch (dynamically from JSONB data)
   * @param {string} batchId - Batch ID
   * @returns {Promise<Array<string>>}
   */
  getAvailableColumns: async (batchId) => {
    try {
      // Fetch a sample record to get column names
      const response = await api.get(`/flexible/datasets`, {
        params: { limit: 1 }
      });
      
      if (response.data.datasets && response.data.datasets.length > 0) {
        const sampleData = response.data.datasets[0].data || {};
        
        // Extract nested column paths from JSONB structure
        const columns = [];
        
        // Check for labels section (primary target columns)
        if (sampleData.labels) {
          const labelKeys = Object.keys(sampleData.labels);
          labelKeys.forEach(key => {
            columns.push(`labels_${key}`);
          });
        }
        
        // Check for other potential target columns
        const potentialTargets = [
          'diagnosis_category',
          'disease_classification', 
          'disease_severity',
          'treatment_outcome',
          'treatment_response',
          'response_status',
          'patient_status',
          'risk_category'
        ];
        
        potentialTargets.forEach(col => {
          if (sampleData[col] !== undefined && !columns.includes(col)) {
            columns.push(col);
          }
        });
        
        // If no specific targets found, return default
        if (columns.length === 0) {
          columns.push('labels_disease_classification');
        }
        
        return columns;
      }
      
      // Default fallback
      return ['labels_disease_classification', 'labels_disease_severity'];
    } catch (error) {
      console.error('Failed to fetch columns:', error);
      return ['labels_disease_classification']; // Fallback
    }
  },

  /**
   * Batch prediction
   * @param {string} modelId - Model ID
   * @param {File} file - CSV file with features
   * @returns {Promise<Object>}
   */
  batchPredict: async (modelId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_id', modelId);
    
    const response = await api.post('/ml/predict/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    return response.data;
  },

  /**
   * Run complete preprocessing pipeline (all 4 steps)
   * @param {string} datasetId - Dataset ID
   * @param {Object} config - Pipeline configuration
   * @returns {Promise<Object>}
   */
  runCompletePipeline: async (datasetId, config) => {
    const response = await api.post(`/eda/datasets/${datasetId}/preprocess/complete-pipeline`, config);
    return response.data;
  },

  /**
   * Run variable filtration (remove variables with high missing data)
   * @param {string} datasetId - Dataset ID
   * @param {number} threshold - Missing data threshold (default 0.5 = 50%)
   * @returns {Promise<Object>}
   */
  filterVariables: async (datasetId, threshold = 0.5) => {
    const response = await api.post(`/eda/datasets/${datasetId}/preprocess/filter-variables`, null, {
      params: { threshold }
    });
    return response.data;
  },

  /**
   * Run imputation (fill missing values)
   * @param {string} datasetId - Dataset ID
   * @param {Object} strategy - Imputation strategy config
   * @returns {Promise<Object>}
   */
  imputeMissingValues: async (datasetId, strategy) => {
    const response = await api.post(`/eda/datasets/${datasetId}/preprocess/missing-values`, strategy);
    return response.data;
  },

  /**
   * Run winsorization (cap outliers at percentiles)
   * @param {string} datasetId - Dataset ID
   * @param {number} lowerPercentile - Lower bound (default 0.01 = 1%)
   * @param {number} upperPercentile - Upper bound (default 0.99 = 99%)
   * @returns {Promise<Object>}
   */
  winsorizeData: async (datasetId, lowerPercentile = 0.01, upperPercentile = 0.99) => {
    const response = await api.post(`/eda/datasets/${datasetId}/preprocess/winsorize`, null, {
      params: {
        lower_percentile: lowerPercentile,
        upper_percentile: upperPercentile
      }
    });
    return response.data;
  },

  /**
   * Run standardization/normalization
   * @param {string} datasetId - Dataset ID
   * @param {string} method - Normalization method ('standard', 'minmax', 'robust')
   * @returns {Promise<Object>}
   */
  normalizeData: async (datasetId, method = 'standard') => {
    const response = await api.post(`/eda/datasets/${datasetId}/preprocess/normalize`, null, {
      params: { method }
    });
    return response.data;
  }
};

export default api;
