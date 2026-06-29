/**
 * Data Ingestion API Extensions
 * Handles Upload -> Validate -> Preview -> Version -> Audit Trail workflow
 */
import api from './api';

export const dataIngestionAPI = {
  /**
   * Step 1: Upload file for validation (no save)
   * Returns validation results and file metadata
   */
  validateFile: async (file, metadata) => {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata.diseaseCode) {
      formData.append('disease_code', metadata.diseaseCode);
    }

    const response = await api.post('/upload/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    return response.data;
  },

  /**
   * Step 2: Preview file data (structured view)
   * Returns parsed data with column mappings
   */
  previewFile: async (file, metadata) => {
    return await dataIngestionAPI.validateFile(file, metadata);
  },

  /**
   * Step 3: Import validated data to database
   * Creates dataset version and audit trail
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

  /**
   * Step 4: Import from edited preview data
   * Used after user edits preview
   */
  importFromPreview: async (editedData) => {
    const response = await api.post('/preview/import-from-preview', editedData);
    return response.data;
  },

  /**
   * Get recent uploads with metadata
   * For "Recent Uploads" tab
   */
  getRecentUploads: async (limit = 50) => {
    const response = await api.get('/flexible/recent-uploads', {
      params: { limit }
    });
    return response.data;
  },

  /**
   * Get upload history for activity log
   */
  getUploadHistory: async (params = {}) => {
    const response = await api.get('/dashboard/uploads', {
      params: {
        limit: params.limit || 100,
        offset: params.offset || 0
      }
    });
    return response.data;
  },

  /**
   * Get audit trail for a specific upload
   */
  getUploadAuditTrail: async (uploadId) => {
    const response = await api.get(`/audit/upload/${uploadId}`);
    return response.data;
  },

  /**
   * Delete/Archive an upload
   */
  deleteUpload: async (uploadId) => {
    const response = await api.delete(`/uploads/${uploadId}`);
    return response.data;
  },
};

// Dataset Versioning API (enhanced)
export const versioningAPI = {
  /**
   * Create new dataset version after import
   */
  createVersion: async (versionData) => {
    const response = await api.post('/dataset-versions/versions', {
      dataset_name: versionData.datasetName,
      parent_version_id: versionData.parentVersionId || null,
      change_type: versionData.changeType || 'major', // major, minor, patch
      description: versionData.description || '',
      is_production: versionData.isProduction || false,
      tags: versionData.tags || []
    });
    return response.data;
  },

  /**
   * List all versions of a dataset
   */
  listVersions: async (datasetName, params = {}) => {
    const response = await api.get(`/dataset-versions/datasets/${datasetName}/versions`, {
      params: {
        include_archived: params.includeArchived || false,
        limit: params.limit || 50
      }
    });
    return response.data;
  },

  /**
   * Get version lineage (family tree)
   */
  getVersionLineage: async (datasetId) => {
    const response = await api.get(`/dataset-versions/lineage/${datasetId}`);
    return response.data;
  },

  /**
   * Promote version to production
   */
  promoteToProduction: async (datasetId) => {
    const response = await api.post(`/dataset-versions/datasets/${datasetId}/promote`);
    return response.data;
  },

  /**
   * Tag a version (e.g., 'validated', 'approved', 'published')
   */
  tagVersion: async (datasetId, tag) => {
    const response = await api.post(`/dataset-versions/datasets/${datasetId}/tag`, { tag });
    return response.data;
  },

  /**
   * Get dataset statistics
   */
  getDatasetStats: async (datasetId) => {
    const response = await api.get(`/dataset-versions/datasets/${datasetId}/stats`);
    return response.data;
  },
};

// Quality Checks API
export const qualityCheckAPI = {
  /**
   * Run automated quality checks on upload
   */
  runQualityChecks: async (uploadId) => {
    const response = await api.post(`/data-quality/check/${uploadId}`);
    return response.data;
  },

  /**
   * Get quality report for upload
   */
  getQualityReport: async (uploadId) => {
    const response = await api.get(`/data-quality/report/${uploadId}`);
    return response.data;
  },
};

export default {
  dataIngestionAPI,
  versioningAPI,
  qualityCheckAPI
};
