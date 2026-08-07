/**
 * Label Assignment Page
 * ====================
 * Allows users to assign disease classification labels to unlabeled data
 * Critical for ML training - provides target variable
 * 
 * Features:
 * - View unlabeled records with patient details
 * - Assign individual labels (clinician review)
 * - Bulk label assignment (select multiple)
 * - Batch label assignment (entire import batch)
 * - Track labeling progress
 * - Filter by dataset type/batch
 * 
 * User Workflow:
 * 1. User uploads data → Records saved unlabeled
 * 2. Navigate to Label Assignment page
 * 3. Review patient data (demographics, lab results)
 * 4. Select appropriate diagnosis category
 * 5. Assign label → Updates flexible_dataset_wide.data.labels
 * 6. Repeat or use bulk assignment
 * 7. Train ML model with labeled data!
 * 
 * Author: Syarifah Fajriyah
 * Date: April 8, 2026
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import * as Dialog from '@radix-ui/react-dialog';
import {
  Tag,
  CheckCircle,
  AlertCircle,
  Users,
  Filter,
  RefreshCw,
  ChevronRight,
  Search,
  TrendingUp,
  Database,
  Save,
  FileCheck,
  Zap,
  Loader2,
  ArrowRight,
  PlayCircle,
  ShieldCheck,
  Target
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import { labelingAPI, mlPreparationAPI } from '../services/api-complete';

// Label type configurations
const LABEL_TYPES = {
  'labels_disease_classification': {
    name: 'Disease Classification',
    description: 'For multi-disease datasets (RA vs SLE vs Mixed)',
    categories: [
      { value: 'SLE', label: 'Systemic Lupus Erythematosus (SLE)', color: 'bg-red-100 text-red-800' },
      { value: 'Sjogren', label: 'Sjögren\'s Syndrome', color: 'bg-blue-100 text-blue-800' },
      { value: 'RA', label: 'Rheumatoid Arthritis (RA)', color: 'bg-orange-100 text-orange-800' },
      { value: 'MCTD', label: 'Mixed Connective Tissue Disease', color: 'bg-purple-100 text-purple-800' },
      { value: 'Healthy', label: 'Healthy Control', color: 'bg-green-100 text-green-800' },
      { value: 'Unknown', label: 'Unknown/Undifferentiated', color: 'bg-gray-100 text-gray-800' }
    ]
  },
  'labels_disease_severity': {
    name: 'Disease Severity',
    description: 'For single-disease datasets - predict severity levels',
    categories: [
      { value: 'Mild', label: 'Mild (SLEDAI ≤4 or minimal symptoms)', color: 'bg-green-100 text-green-800' },
      { value: 'Moderate', label: 'Moderate (SLEDAI 5-12 or moderate symptoms)', color: 'bg-yellow-100 text-yellow-800' },
      { value: 'Severe', label: 'Severe (SLEDAI >12 or severe/organ-threatening)', color: 'bg-red-100 text-red-800' }
    ]
  },
  'labels_disease_activity': {
    name: 'Disease Activity',
    description: 'Current disease activity status',
    categories: [
      { value: 'Remission', label: 'Remission (No active disease)', color: 'bg-green-100 text-green-800' },
      { value: 'Active', label: 'Active (Ongoing disease activity)', color: 'bg-orange-100 text-orange-800' },
      { value: 'Flare', label: 'Flare (Acute exacerbation)', color: 'bg-red-100 text-red-800' }
    ]
  },
  'labels_organ_involvement': {
    name: 'Organ Involvement',
    description: 'Primary organ system affected',
    categories: [
      { value: 'Renal', label: 'Renal (Lupus nephritis)', color: 'bg-blue-100 text-blue-800' },
      { value: 'Neuropsychiatric', label: 'Neuropsychiatric (CNS involvement)', color: 'bg-purple-100 text-purple-800' },
      { value: 'Hematologic', label: 'Hematologic (Blood disorders)', color: 'bg-red-100 text-red-800' },
      { value: 'Musculoskeletal', label: 'Musculoskeletal (Joint involvement)', color: 'bg-orange-100 text-orange-800' },
      { value: 'Cutaneous', label: 'Cutaneous (Skin involvement only)', color: 'bg-pink-100 text-pink-800' },
      { value: 'Non-organ-specific', label: 'Non-organ-specific', color: 'bg-gray-100 text-gray-800' }
    ]
  },
  'labels_treatment_response': {
    name: 'Treatment Response',
    description: 'Response to current treatment',
    categories: [
      { value: 'Complete-responder', label: 'Complete Responder (Full response)', color: 'bg-green-100 text-green-800' },
      { value: 'Partial-responder', label: 'Partial Responder (Partial response)', color: 'bg-yellow-100 text-yellow-800' },
      { value: 'Non-responder', label: 'Non-responder (No response)', color: 'bg-red-100 text-red-800' }
    ]
  },
  'labels_flare_risk': {
    name: 'Flare Risk',
    description: 'Risk of disease flare',
    categories: [
      { value: 'Low-risk', label: 'Low Risk (Stable, good control)', color: 'bg-green-100 text-green-800' },
      { value: 'High-risk', label: 'High Risk (Unstable, multiple risk factors)', color: 'bg-red-100 text-red-800' }
    ]
  }
};

// Backward compatibility
const DISEASE_CATEGORIES = LABEL_TYPES['labels_disease_classification'].categories;

export default function LabelAssignmentPage() {
  const navigate = useNavigate();
  
  // Session management
  const [batchId, setBatchId] = useState(null);
  const [sessionReady, setSessionReady] = useState(false);
  
  // State
  const [unlabeledRecords, setUnlabeledRecords] = useState([]);
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Label type selection
  const [labelType, setLabelType] = useState('labels_disease_classification');
  const currentLabelConfig = LABEL_TYPES[labelType];
  
  // Filters
  const [datasetTypeFilter, setDatasetTypeFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Labeling state
  const [selectedLabel, setSelectedLabel] = useState('');
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [expandedRecordId, setExpandedRecordId] = useState(null);
  
  // Load batch from session storage
  useEffect(() => {
    const savedBatchId = sessionStorage.getItem('current_batch_id');
    if (savedBatchId) {
      setBatchId(savedBatchId);
      setSessionReady(true);
    } else {
      setError('No batch found. Please upload and preprocess data first.');
    }
  }, []);
  
  // Load data when session is ready
  useEffect(() => {
    if (sessionReady && batchId) {
      loadUnlabeledRecords();
      loadStatistics();
    }
  }, [sessionReady, batchId, labelType]);
  
  const loadUnlabeledRecords = async () => {
    if (!batchId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await labelingAPI.getUnlabeledRecords(batchId, labelType, 100, 0);
      setUnlabeledRecords(data.records || []);
    } catch (err) {
      console.error('Failed to load unlabeled records:', err);
      setError(err.response?.data?.detail || 'Failed to load unlabeled records');
    } finally {
      setIsLoading(false);
    }
  };
  
  const loadStatistics = async () => {
    if (!batchId) return;
    
    try {
      const data = await labelingAPI.getLabelStatistics(batchId, labelType);
      setStatistics(data);
    } catch (err) {
      console.error('Failed to load statistics:', err);
    }
  };
  
  const assignLabelToRecord = async (recordId, label) => {
    setIsSaving(true);
    setError(null);
    
    try {
      await labelingAPI.assignLabel(recordId, label, 1.0, 'Manual assignment', labelType);
      
      setSuccess(`Label "${label}" assigned successfully!`);
      
      // Reload data
      await loadUnlabeledRecords();
      await loadStatistics();
      
      // Clear success message after 3s
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Failed to assign label:', err);
      setError(err.response?.data?.detail || 'Failed to assign label');
    } finally {
      setIsSaving(false);
    }
  };
  
  const bulkAssignLabels = async () => {
    if (selectedRecords.length === 0 || !selectedLabel) {
      setError('Please select records and a label');
      return;
    }
    
    setIsSaving(true);
    setError(null);
    
    try {
      const data = await labelingAPI.bulkAssignLabels(
        selectedRecords,
        selectedLabel,
        1.0,
        labelType,
        'Bulk assignment'
      );
      
      setSuccess(`Bulk assigned "${selectedLabel}" to ${data.updated_count} records!`);
      setSelectedRecords([]);
      setSelectedLabel('');
      setShowBulkModal(false);
      
      // Reload data
      await loadUnlabeledRecords();
      await loadStatistics();
      
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Failed to bulk assign:', err);
      setError(err.response?.data?.detail || 'Failed to bulk assign labels');
    } finally {
      setIsSaving(false);
    }
  };
  
  // Batch label assignment (assign to entire batch)
  const batchAssignLabels = async () => {
    if (!batchId || !selectedLabel) {
      setError('Please select a label for batch assignment');
      return;
    }
    
    if (!confirm(`Assign "${selectedLabel}" to ALL records in this batch?`)) {
      return;
    }
    
    setIsSaving(true);
    setError(null);
    
    try {
      const data = await labelingAPI.batchAssignLabel(
        batchId,
        selectedLabel,
        labelType,
        'Batch assignment'
      );
      
      setSuccess(`Batch assigned "${selectedLabel}" to ${data.updated_count} records!`);
      setSelectedLabel('');
      setShowBatchModal(false);
      
      // Reload data
      await loadUnlabeledRecords();
      await loadStatistics();
      
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Failed to batch assign:', err);
      setError(err.response?.data?.detail || 'Failed to batch assign labels');
    } finally {
      setIsSaving(false);
    }
  };
  
  // Validate dataset for ML training
  const validateForML = async () => {
    if (!batchId) return;
    
    setIsValidating(true);
    setError(null);
    
    try {
      const result = await mlPreparationAPI.validateForML(batchId, labelType, 100);
      setValidationResult(result);
      
      if (result.can_proceed) {
        setSuccess('Validation passed! Dataset is ready for ML training.');
      } else {
        setError('Validation failed. Please address the issues shown below.');
      }
    } catch (err) {
      console.error('Validation failed:', err);
      setError(err.response?.data?.detail || 'Validation failed');
    } finally {
      setIsValidating(false);
    }
  };
  
  // Navigate to training page
  const proceedToTraining = () => {
    if (!validationResult || !validationResult.can_proceed) {
      setError('Please run validation first and ensure it passes');
      return;
    }
    
    sessionStorage.setItem('workflow_stage', 'training');
    navigate('/training-jobs');
  };
  
  const toggleRecordSelection = (recordId) => {
    if (selectedRecords.includes(recordId)) {
      setSelectedRecords(selectedRecords.filter(id => id !== recordId));
    } else {
      setSelectedRecords([...selectedRecords, recordId]);
    }
  };
  
  const toggleAll = () => {
    if (selectedRecords.length === unlabeledRecords.length) {
      setSelectedRecords([]);
    } else {
      setSelectedRecords(unlabeledRecords.map(r => r.record_id));
    }
  };
  
  const filteredRecords = unlabeledRecords.filter(record => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      record.record_id.toLowerCase().includes(query) ||
      record.dataset_type?.toLowerCase().includes(query) ||
      JSON.stringify(record.data_preview).toLowerCase().includes(query)
    );
  });
  
  return (
    <DashboardLayout>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Label Assignment</h1>
                <p className="text-sm text-gray-600 mt-1">
                  Assign labels for ML training - {currentLabelConfig.description}
                </p>
              </div>
              <div className="flex items-center gap-3">
                {/* Label Type Selector */}
                <select
                  value={labelType}
                  onChange={(e) => {
                    setLabelType(e.target.value);
                    setSelectedLabel('');
                    setSelectedRecords([]);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {Object.entries(LABEL_TYPES).map(([key, config]) => (
                    <option key={key} value={key}>
                      {config.name}
                    </option>
                  ))}
                </select>
                
                <button
                  onClick={loadUnlabeledRecords}
                  disabled={isLoading}
                  className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                  <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
                
                {selectedRecords.length > 0 && (
                  <button
                    onClick={() => setShowBulkModal(true)}
                    className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    <Tag className="w-4 h-4" />
                    Bulk Assign ({selectedRecords.length})
                  </button>
                )}
                
                <button
                  onClick={() => setShowBatchModal(true)}
                  disabled={!batchId}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                >
                  <Database className="w-4 h-4" />
                  Batch Assign All
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 py-6">
          {/* Success/Error Messages */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 text-sm text-red-800">{error}</div>
            </div>
          )}
          
          {success && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 text-sm text-green-800">{success}</div>
            </div>
          )}

          {/* Statistics Cards */}
          {statistics && (
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg shadow-sm p-6">
                <Database className="w-8 h-8 text-blue-600 mb-2" />
                <div className="text-2xl font-bold text-gray-900">{statistics.total_records}</div>
                <div className="text-sm text-gray-600">Total Records</div>
              </div>
              <div className="bg-white rounded-lg shadow-sm p-6">
                <CheckCircle className="w-8 h-8 text-green-600 mb-2" />
                <div className="text-2xl font-bold text-gray-900">{statistics.labeled_count}</div>
                <div className="text-sm text-gray-600">Labeled</div>
              </div>
              <div className="bg-white rounded-lg shadow-sm p-6">
                <AlertCircle className="w-8 h-8 text-orange-600 mb-2" />
                <div className="text-2xl font-bold text-gray-900">{statistics.unlabeled_count}</div>
                <div className="text-sm text-gray-600">Unlabeled</div>
              </div>
              <div className="bg-white rounded-lg shadow-sm p-6">
                <TrendingUp className="w-8 h-8 text-purple-600 mb-2" />
                <div className="text-2xl font-bold text-gray-900">{statistics.progress_percentage}%</div>
                <div className="text-sm text-gray-600">Progress</div>
              </div>
            </div>
          )}

          {/* ML Validation Section */}
          {statistics && statistics.progress_percentage >= 80 && (
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg shadow-sm p-6 mb-6 border-2 border-indigo-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <ShieldCheck className="w-6 h-6 text-indigo-600" />
                    <h3 className="text-lg font-bold text-gray-900">ML Training Validation</h3>
                  </div>
                  <p className="text-sm text-gray-600 mb-4">
                    {statistics.progress_percentage}% of records are labeled. Validate dataset before proceeding to ML training.
                  </p>

                  {validationResult && (
                    <div className={`p-4 rounded-lg mb-4 ${
                      validationResult.can_proceed 
                        ? 'bg-green-50 border border-green-200' 
                        : 'bg-red-50 border border-red-200'
                    }`}>
                      <div className="flex items-start gap-3">
                        {validationResult.can_proceed ? (
                          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        ) : (
                          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                        )}
                        <div className="flex-1">
                          <p className={`text-sm font-semibold ${
                            validationResult.can_proceed ? 'text-green-800' : 'text-red-800'
                          }`}>
                            {validationResult.can_proceed ? 'Validation Passed!' : 'Validation Failed'}
                          </p>
                          <div className="text-xs mt-2 space-y-1">
                            <p className="text-gray-700">
                              <strong>Total Samples:</strong> {validationResult.total_samples}
                            </p>
                            <p className="text-gray-700">
                              <strong>Labeled:</strong> {validationResult.labeled_samples} ({validationResult.labeled_percentage}%)
                            </p>
                            {validationResult.class_distribution && (
                              <div className="mt-2">
                                <strong className="text-gray-700">Class Distribution:</strong>
                                <div className="ml-4 mt-1 space-y-0.5">
                                  {Object.entries(validationResult.class_distribution).map(([label, count]) => (
                                    <p key={label} className="text-gray-600 text-xs">
                                      {label}: {count}
                                    </p>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                          {validationResult.issues && validationResult.issues.length > 0 && (
                            <div className="mt-3">
                              <p className="text-xs font-semibold text-red-800">Issues:</p>
                              <ul className="ml-4 mt-1 space-y-0.5 text-xs text-red-700">
                                {validationResult.issues.map((issue, idx) => (
                                  <li key={idx}>• {issue}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex items-center gap-3">
                    <button
                      onClick={validateForML}
                      disabled={isValidating || !batchId}
                      className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                    >
                      {isValidating ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Validating...
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="w-4 h-4" />
                          Validate for ML Training
                        </>
                      )}
                    </button>

                    {validationResult && validationResult.can_proceed && (
                      <button
                        onClick={proceedToTraining}
                        className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 shadow-lg transition-all"
                      >
                        <PlayCircle className="w-4 h-4" />
                        Proceed to ML Training
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Search records..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <select
                value={datasetTypeFilter}
                onChange={(e) => setDatasetTypeFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg bg-white"
              >
                <option value="">All Dataset Types</option>
                <option value="SLE">SLE</option>
                <option value="Sjogren">Sjögren</option>
                <option value="RA">RA</option>
              </select>
            </div>
          </div>

          {/* Records Table */}
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <div className="border-b p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selectedRecords.length === filteredRecords.length && filteredRecords.length > 0}
                  onChange={toggleAll}
                  className="w-4 h-4 text-blue-600"
                />
                <span className="text-sm font-medium text-gray-700">
                  Select All ({filteredRecords.length} records)
                </span>
              </div>
              <div className="text-sm text-gray-600">
                {selectedRecords.length} selected
              </div>
            </div>

            {isLoading ? (
              <div className="p-12 text-center">
                <RefreshCw className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-4" />
                <p className="text-gray-600">Loading unlabeled records...</p>
              </div>
            ) : filteredRecords.length === 0 ? (
              <div className="p-12 text-center">
                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">All Records Labeled!</h3>
                <p className="text-gray-600">No unlabeled records found. Ready for ML training.</p>
              </div>
            ) : (
              <div className="divide-y">
                {filteredRecords.map(record => (
                  <div
                    key={record.record_id}
                    className={`p-4 hover:bg-gray-50 ${selectedRecords.includes(record.record_id) ? 'bg-blue-50' : ''}`}
                  >
                    <div className="flex items-start gap-4">
                      <input
                        type="checkbox"
                        checked={selectedRecords.includes(record.record_id)}
                        onChange={() => toggleRecordSelection(record.record_id)}
                        className="mt-1 w-4 h-4 text-blue-600"
                      />
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <div>
                            <div className="font-medium text-gray-900">{record.record_id}</div>
                            <div className="text-sm text-gray-600">{record.dataset_type}</div>
                          </div>
                          <button
                            onClick={() => setExpandedRecordId(expandedRecordId === record.record_id ? null : record.record_id)}
                            className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center gap-1"
                          >
                            View Details
                            <ChevronRight className={`w-4 h-4 transition-transform ${expandedRecordId === record.record_id ? 'rotate-90' : ''}`} />
                          </button>
                        </div>
                        
                        {expandedRecordId === record.record_id && (
                          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                            <h4 className="font-semibold text-gray-700 mb-2">Patient Data Preview</h4>
                            <pre className="text-xs text-gray-600 overflow-auto">
                              {JSON.stringify(record.data_preview, null, 2)}
                            </pre>
                          </div>
                        )}
                        
                        <div className="mt-3 flex items-center gap-2 flex-wrap">
                          {currentLabelConfig.categories.map(category => (
                            <button
                              key={category.value}
                              onClick={() => assignLabelToRecord(record.record_id, category.value)}
                              disabled={isSaving}
                              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${category.color} hover:opacity-80 disabled:opacity-50`}
                            >
                              {category.value}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Bulk Assignment Modal */}
        <Dialog.Root open={showBulkModal} onOpenChange={setShowBulkModal}>
          <Dialog.Portal>
            <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
            <Dialog.Content className="fixed left-[50%] top-[50%] translate-x-[-50%] translate-y-[-50%] bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl z-50">
              <Dialog.Title className="text-lg font-semibold text-gray-900 mb-4">Bulk Label Assignment</Dialog.Title>
              <Dialog.Description className="text-sm text-gray-600 mb-4">
                Assign the same label to {selectedRecords.length} selected records
              </Dialog.Description>
              
              <div className="space-y-3 mb-6">
                {currentLabelConfig.categories.map(category => (
                  <button
                    key={category.value}
                    onClick={() => setSelectedLabel(category.value)}
                    className={`w-full px-4 py-3 rounded-lg text-left transition-colors ${
                      selectedLabel === category.value
                        ? category.color + ' ring-2 ring-blue-500'
                        : 'bg-gray-50 hover:bg-gray-100 text-gray-800'
                    }`}
                  >
                    <div className="font-medium">{category.value}</div>
                    <div className="text-xs opacity-75">{category.label}</div>
                  </button>
                ))}
              </div>
              
              <div className="flex items-center gap-3">
                <Dialog.Close asChild>
                  <button
                    className="flex-1 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                </Dialog.Close>
                <button
                  onClick={bulkAssignLabels}
                  disabled={!selectedLabel || isSaving}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSaving ? 'Assigning...' : 'Assign Label'}
                </button>
              </div>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>

        {/* Batch Assignment Modal */}
        <Dialog.Root open={showBatchModal} onOpenChange={setShowBatchModal}>
          <Dialog.Portal>
            <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
            <Dialog.Content className="fixed left-[50%] top-[50%] translate-x-[-50%] translate-y-[-50%] bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl z-50">
              <Dialog.Title className="text-lg font-semibold text-gray-900 mb-4">Batch Label Assignment</Dialog.Title>
              <Dialog.Description className="text-sm text-gray-600 mb-4">
                Assign the same label to ALL records in this batch
              </Dialog.Description>
              
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg mb-4">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-amber-800">
                    <strong>Warning:</strong> This will assign the selected label to all unlabeled records in the current batch. This action cannot be undone.
                  </p>
                </div>
              </div>
              
              <div className="space-y-3 mb-6">
                {currentLabelConfig.categories.map(category => (
                  <button
                    key={category.value}
                    onClick={() => setSelectedLabel(category.value)}
                    className={`w-full px-4 py-3 rounded-lg text-left transition-colors ${
                      selectedLabel === category.value
                        ? category.color + ' ring-2 ring-purple-500'
                        : 'bg-gray-50 hover:bg-gray-100 text-gray-800'
                    }`}
                  >
                    <div className="font-medium">{category.value}</div>
                    <div className="text-xs opacity-75">{category.label}</div>
                  </button>
                ))}
              </div>
              
              <div className="flex items-center gap-3">
                <Dialog.Close asChild>
                  <button
                    className="flex-1 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                </Dialog.Close>
                <button
                  onClick={batchAssignLabels}
                  disabled={!selectedLabel || isSaving}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSaving ? 'Assigning...' : 'Assign to All'}
                </button>
              </div>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
      </div>
    </DashboardLayout>
  );
}
