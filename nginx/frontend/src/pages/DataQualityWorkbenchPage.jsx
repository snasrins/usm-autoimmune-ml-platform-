import { useMemo, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ChevronRight,
  ShieldCheck,
  AlertTriangle,
  SlidersHorizontal,
  Download,
  FileText,
  Sparkles,
  CheckCircle2,
  Wand2,
  Loader2,
  Save,
  ArrowRight,
  Edit,
  Trash2,
  Upload,
  Users,
  Calendar,
  FileType,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import DashboardLayout from '../components/DashboardLayout';
import { structuredPipelineAPI, preprocessingAPI, unstructuredPipelineAPI } from '../services/api-complete';
import { flexibleAPI } from '../services/api';

const QUALITY_TREND = [
  { date: 'Apr 14', score: 81 },
  { date: 'Apr 15', score: 84 },
  { date: 'Apr 16', score: 86 },
  { date: 'Apr 17', score: 88 },
  { date: 'Apr 18', score: 90 },
  { date: 'Apr 19', score: 92 },
  { date: 'Apr 20', score: 94 },
];

const ISSUE_BREAKDOWN = [
  { name: 'Missing Values', value: 38, color: '#ef4444' },
  { name: 'Outliers', value: 27, color: '#f59e0b' },
  { name: 'Duplicates', value: 21, color: '#6366f1' },
  { name: 'Invalid Formats', value: 14, color: '#06b6d4' },
];

const BEFORE_AFTER = [
  { metric: 'Missing %', before: 21.6, after: 3.2 },
  { metric: 'Outlier %', before: 9.4, after: 2.1 },
  { metric: 'Duplicate %', before: 4.8, after: 0.8 },
  { metric: 'Valid Rows %', before: 73.3, after: 95.4 },
];

const ISSUE_LIST = [
  {
    title: 'Missing Values in ANA_Titer',
    severity: 'high',
    summary: '22.4% of records missing ANA_Titer values.',
    rows: ['Patient_ID 1034', 'Patient_ID 1098', 'Patient_ID 1112'],
  },
  {
    title: 'Outliers in ESR_Value',
    severity: 'medium',
    summary: 'Detected values above physiological thresholds.',
    rows: ['Patient_ID 0988', 'Patient_ID 1020'],
  },
  {
    title: 'Inconsistent Date Formats',
    severity: 'low',
    summary: 'Mixed YYYY/MM/DD and DD-MM-YYYY patterns.',
    rows: ['Patient_ID 0760', 'Patient_ID 0775', 'Patient_ID 0812'],
  },
];

export default function DataQualityWorkbenchPage() {
  const navigate = useNavigate();
  
  // Session management
  const [sessionId, setSessionId] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [qualityReport, setQualityReport] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalRows, setTotalRows] = useState(0);
  const rowsPerPage = 20;
  
  // Upload state
  const [uploadType, setUploadType] = useState('structured'); // 'structured' | 'unstructured'
  const [uploading, setUploading] = useState(false);
  const [recentUploads, setRecentUploads] = useState([]);
  const [loadingUploads, setLoadingUploads] = useState(true);
  
  // UI state
  const [dataset, setDataset] = useState('Loading...');
  const [tab, setTab] = useState('preview');
  const [expandedIssue, setExpandedIssue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const [preprocessing, setPreprocessing] = useState(false);
  const [saving, setSaving] = useState(false);

  // Preprocessing configuration
  const [missingStrategy, setMissingStrategy] = useState('median');
  const [outlierStrategy, setOutlierStrategy] = useState('winsorize');
  const [normalizeMethod, setNormalizeMethod] = useState('standard');
  const [removeDuplicates, setRemoveDuplicates] = useState(true);
  const [enableComposite, setEnableComposite] = useState(true);
  const [enableStandardization, setEnableStandardization] = useState(true);
  const [targetColumn, setTargetColumn] = useState('ANA_Titer');

  // Load recent uploads on mount
  useEffect(() => {
    loadRecentUploads();
  }, []);

  // Load recent uploads
  const loadRecentUploads = async () => {
    setLoadingUploads(true);
    try {
      // Include both staging (just uploaded) and saved files
      const response = await flexibleAPI.getRecentUploads(50, true, true);
      setRecentUploads(response.uploads || []);
    } catch (err) {
      console.error('Failed to load recent uploads:', err);
    } finally {
      setLoadingUploads(false);
    }
  };

  // Handle file upload (structured CSV/Excel)
  const handleStructuredUpload = async (file) => {
    setUploading(true);
    setError(null);
    try {
      const response = await structuredPipelineAPI.uploadForPreview(file, 'Clinical_Data');
      sessionStorage.setItem('preview_session_id', response.session_id);
      setSessionId(response.session_id);
      setMessage('File uploaded successfully!');
      loadPreview(response.session_id);
      loadQualityReport(response.session_id);
      loadRecentUploads(); // Refresh list
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Upload failed: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  // Handle file upload (unstructured PDF/Image)
  const handleUnstructuredUpload = async (file) => {
    setUploading(true);
    setError(null);
    try {
      const response = await unstructuredPipelineAPI.uploadForOCR(file);
      setMessage('OCR processing completed! Converting to tabular...');
      
      // Convert to tabular
      const convertResponse = await unstructuredPipelineAPI.convertToTabular(response.validation_id);
      sessionStorage.setItem('preview_session_id', convertResponse.session_id);
      setSessionId(convertResponse.session_id);
      loadPreview(convertResponse.session_id);
      loadQualityReport(convertResponse.session_id);
      loadRecentUploads(); // Refresh list
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Upload failed: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  // Handle file selection
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (uploadType === 'structured') {
      handleStructuredUpload(file);
    } else {
      handleUnstructuredUpload(file);
    }
  };

  // Select existing upload from recent list
  const selectUpload = async (upload) => {
    const sessionId = upload.id;
    sessionStorage.setItem('preview_session_id', sessionId);
    setSessionId(sessionId);
    setDataset(upload.file_name);
    loadPreview(sessionId);
    loadQualityReport(sessionId);
  };

  // Load preview data on mount
  useEffect(() => {
    const savedSessionId = sessionStorage.getItem('preview_session_id');
    if (savedSessionId) {
      setSessionId(savedSessionId);
      loadPreview(savedSessionId);
      loadQualityReport(savedSessionId);
    }
  }, []);

  // Load preview data from backend
  const loadPreview = async (sessionId, page = 1) => {
    setLoading(true);
    try {
      const data = await structuredPipelineAPI.getPreview(sessionId, page, rowsPerPage);
      setPreviewData(data);
      setTotalRows(data.total_rows || 0);
      setDataset(data.filename || 'Uploaded Dataset');
    } catch (err) {
      console.error('Failed to load preview:', err);
      setError('Failed to load preview data');
    } finally {
      setLoading(false);
    }
  };

  // Load quality report from backend
  const loadQualityReport = async (sessionId) => {
    try {
      const report = await preprocessingAPI.getQualityReport(sessionId);
      setQualityReport(report);
    } catch (err) {
      console.error('Failed to load quality report:', err);
    }
  };

  // Handle cell edit
  const handleEditCell = async (stagingId, columnName, newValue) => {
    try {
      await structuredPipelineAPI.editCell(sessionId, stagingId, columnName, newValue);
      await loadPreview(sessionId, currentPage);
      setMessage('Cell updated successfully');
    } catch (err) {
      setError('Failed to update cell');
    }
  };

  // Handle row delete
  const handleDeleteRow = async (stagingId) => {
    if (!confirm('Are you sure you want to delete this row?')) return;
    
    try {
      await structuredPipelineAPI.deleteRow(sessionId, stagingId);
      await loadPreview(sessionId, currentPage);
      setMessage('Row deleted successfully');
    } catch (err) {
      setError('Failed to delete row');
    }
  };

  // Apply preprocessing operations
  const handleApplyPreprocessing = async () => {
    setPreprocessing(true);
    setError(null);
    setMessage(null);
    
    try {
      // Apply missing values handling
      if (missingStrategy !== 'none') {
        await preprocessingAPI.handleMissingValues(sessionId, missingStrategy, 0.5);
      }
      
      // Remove duplicates
      if (removeDuplicates) {
        await preprocessingAPI.removeDuplicates(sessionId, true);
      }
      
      // Handle outliers
      if (outlierStrategy !== 'none') {
        await preprocessingAPI.handleOutliers(sessionId, outlierStrategy, 3.0);
      }
      
      // Normalize data
      if (enableStandardization) {
        await preprocessingAPI.normalizeData(sessionId, normalizeMethod);
      }
      
      // Reload preview and quality report
      await loadPreview(sessionId, currentPage);
      await loadQualityReport(sessionId);
      
      setMessage('Preprocessing applied successfully!');
      setTab('preview'); // Switch to preview to see results
      
    } catch (err) {
      console.error('Preprocessing failed:', err);
      setError(err.response?.data?.detail || 'Preprocessing failed');
    } finally {
      setPreprocessing(false);
    }
  };

  // Save preprocessed data to database
  const handleSaveToDatabase = async () => {
    setSaving(true);
    setError(null);
    
    try {
      const result = await preprocessingAPI.savePreprocessed(
        sessionId,
        'structured', // dataset_type
        'Manual Upload via Data Quality Workbench' // description
      );
      
      // CRITICAL: Store batch ID for next steps
      sessionStorage.setItem('current_batch_id', result.batch_id);
      sessionStorage.setItem('workflow_stage', 'labeling');
      
      setMessage(`Data saved successfully! Batch ID: ${result.batch_id}`);
      
      // Navigate to label assignment after 2 seconds
      setTimeout(() => {
        navigate('/label-assignment');
      }, 2000);
      
    } catch (err) {
      console.error('Save failed:', err);
      setError(err.response?.data?.detail || 'Failed to save data');
    } finally {
      setSaving(false);
    }
  };

  const qualityScore = useMemo(() => {
    if (qualityReport) {
      return Math.round(qualityReport.quality_score || 0);
    }
    return 0;
  }, [qualityReport]);

  return (
    <DashboardLayout>
      <div className="h-[70px] flex items-center gap-8 px-6 bg-white/85 border-b border-emerald-100 backdrop-blur-md">
        <div className="flex flex-col gap-1">
          <h1 className="font-syne text-[18px] font-bold text-[#0F0F11] leading-none">Data Preparation</h1>
          <div className="flex items-center gap-3 text-[12px] text-[#8585A0]">
            <span>USM Autoimmune ML Platform</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-emerald-600">Upload & Preview & Preprocess</span>
          </div>
        </div>
      </div>

      <main className="flex-1 overflow-y-auto p-6 bg-gradient-to-br from-[#eef7f3] via-[#f8fcfb] to-[#edf3ff]">
        <div className="max-w-7xl mx-auto space-y-6">
          
          {/* Upload Section */}
          <section className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-white to-emerald-50/70 p-6 shadow-[0_16px_40px_rgba(13,148,136,0.12)]">
            <div className="flex items-center justify-between gap-5 mb-4">
              <div>
                <h2 className="font-syne text-xl font-bold text-gray-900">Upload New Data</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Upload structured (CSV/Excel) or unstructured (PDF/Image) files
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setUploadType('structured')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    uploadType === 'structured'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Structured (CSV/Excel)
                </button>
                <button
                  onClick={() => setUploadType('unstructured')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    uploadType === 'unstructured'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Unstructured (PDF/Image)
                </button>
              </div>
            </div>

            <div className="border-2 border-dashed border-emerald-300 rounded-xl p-8 text-center bg-white/50">
              <Upload className="w-12 h-12 text-emerald-600 mx-auto mb-3" />
              <p className="text-sm font-semibold text-gray-900 mb-1">
                {uploadType === 'structured' ? 'Drop CSV or Excel file here' : 'Drop PDF or Image file here'}
              </p>
              <p className="text-xs text-gray-600 mb-4">
                {uploadType === 'structured' 
                  ? 'Supported: .csv, .xlsx, .xls'
                  : 'Supported: .pdf, .png, .jpg (OCR will extract text)'}
              </p>
              <label className="inline-block">
                <input
                  type="file"
                  accept={uploadType === 'structured' ? '.csv,.xlsx,.xls' : '.pdf,.png,.jpg,.jpeg'}
                  onChange={handleFileSelect}
                  className="hidden"
                  disabled={uploading}
                />
                <span className="px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium cursor-pointer hover:bg-emerald-700 disabled:opacity-50 inline-block">
                  {uploading ? 'Uploading...' : 'Select File'}
                </span>
              </label>
            </div>
          </section>

          {/* Recent Uploads Section */}
          <section className="rounded-2xl border border-emerald-100 bg-white/90 p-6 shadow-[0_14px_34px_rgba(13,148,136,0.12)]">
            <h2 className="font-syne text-lg font-bold text-gray-900 mb-4">Recent Uploads</h2>
            {loadingUploads ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
              </div>
            ) : recentUploads.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-2 opacity-40" />
                <p className="text-sm">No uploads yet. Upload your first file above.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {recentUploads.slice(0, 10).map((upload) => (
                  <button
                    key={upload.id}
                    onClick={() => selectUpload(upload)}
                    className={`w-full p-3 rounded-lg border transition-all text-left ${
                      sessionId === upload.id
                        ? 'border-emerald-500 bg-emerald-50'
                        : 'border-gray-200 hover:border-emerald-300 hover:bg-emerald-50/30'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-gray-900">{upload.file_name}</p>
                        <div className="flex items-center gap-4 mt-1 text-xs text-gray-600">
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {upload.uploaded_by || 'Unknown'}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {new Date(upload.uploaded_at).toLocaleString()}
                          </span>
                          <span className="flex items-center gap-1">
                            <FileType className="w-3 h-3" />
                            {upload.dataset_type || 'CSV'}
                          </span>
                          <span>{upload.row_count || 0} rows</span>
                        </div>
                      </div>
                      {sessionId === upload.id && (
                        <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </section>

          {/* Only show tabs if we have a session */}
          {sessionId && (
          <section className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-white to-emerald-50/70 p-6 shadow-[0_16px_40px_rgba(13,148,136,0.12)]">
            <div className="flex items-center justify-between gap-5">
              <div>
                <h2 className="font-syne text-xl font-bold text-gray-900">Quality Control & Preprocessing</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Validate, clean, and standardize before ML preparation
                </p>
              </div>
              <div className="w-[280px]">
                <label className="text-sm font-semibold text-gray-700">Selected Dataset</label>
                <div className="text-sm font-medium text-emerald-600 mt-1">{dataset}</div>
              </div>
            </div>
          </section>
          )}

          <section className="rounded-2xl border border-emerald-100 bg-white/90 overflow-hidden shadow-[0_14px_34px_rgba(13,148,136,0.12)]">
            <div className="flex border-b border-emerald-100 bg-white/90">
              {[
                { id: 'quality-summary', label: 'Quality Summary' },
                { id: 'preprocessing', label: 'Preprocessing Config' },
                { id: 'preview', label: 'Preview Data' },
                { id: 'reports', label: 'Reports' },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setTab(item.id)}
                  className={`px-5 py-3 text-sm font-semibold transition-all ${
                    tab === item.id
                      ? 'text-emerald-700 border-b-2 border-emerald-600 bg-emerald-50/70'
                      : 'text-gray-500 hover:text-emerald-700'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <div className="p-6">
              {/* Error Display */}
              {error && (
                <div className="mb-4 p-4 rounded-lg bg-red-50 border border-red-200 flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
                  <p className="text-sm text-red-700">{error}</p>
                  <button onClick={() => setError(null)} className="ml-auto text-red-600 hover:text-red-800">✕</button>
                </div>
              )}

              {/* Success Message */}
              {message && (
                <div className="mb-4 p-4 rounded-lg bg-green-50 border border-green-200 flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
                  <p className="text-sm text-green-700">{message}</p>
                  <button onClick={() => setMessage(null)} className="ml-auto text-green-600 hover:text-green-800">✕</button>
                </div>
              )}

              {loading && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
                  <span className="ml-3 text-gray-600">Loading data...</span>
                </div>
              )}

              {!loading && tab === 'quality-summary' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-3 gap-4">
                    <SummaryCard 
                      icon={ShieldCheck} 
                      title="Quality Score" 
                      value={`${qualityScore}%`} 
                      accent="emerald" 
                      subtitle="Composite score across data quality checks" 
                    />
                    <SummaryCard 
                      icon={AlertTriangle} 
                      title="Issues Found" 
                      value={qualityReport?.issues?.length || 0} 
                      accent="amber" 
                      subtitle={`${qualityReport?.total_issues || 0} total issues detected`}
                    />
                    <SummaryCard 
                      icon={CheckCircle2} 
                      title="Total Rows" 
                      value={totalRows} 
                      accent="indigo" 
                      subtitle="Rows in current dataset" 
                    />
                  </div>

                  {qualityReport?.issues && qualityReport.issues.length > 0 && (
                    <div className="rounded-xl border border-emerald-100 bg-white p-4">
                      <h3 className="text-sm font-bold text-gray-900 mb-4">Detected Issues</h3>
                      <div className="space-y-3">
                        {qualityReport.issues.map((issue, idx) => (
                          <div key={idx} className="rounded-lg border border-gray-200 overflow-hidden">
                            <button
                              onClick={() => setExpandedIssue(expandedIssue === idx ? -1 : idx)}
                              className="w-full px-4 py-3 flex items-center justify-between text-left bg-gray-50 hover:bg-gray-100"
                            >
                              <div>
                                <p className="text-sm font-semibold text-gray-900">{issue.type}</p>
                                <p className="text-xs text-gray-600 mt-0.5">{issue.description}</p>
                              </div>
                              <span className="text-[11px] font-bold px-2 py-1 rounded-full bg-amber-100 text-amber-700">
                                {issue.severity?.toUpperCase() || 'MEDIUM'}
                              </span>
                            </button>
                            {expandedIssue === idx && issue.details && (
                              <div className="px-4 py-3 text-sm text-gray-700">
                                <p className="font-semibold mb-2">Details</p>
                                <pre className="text-xs text-gray-600 overflow-x-auto">
                                  {JSON.stringify(issue.details, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {(!qualityReport || !qualityReport.issues || qualityReport.issues.length === 0) && (
                    <div className="rounded-xl border border-emerald-100 bg-white p-8 text-center">
                      <CheckCircle2 className="w-12 h-12 text-emerald-600 mx-auto mb-3" />
                      <p className="text-sm font-semibold text-gray-900">No Issues Detected</p>
                      <p className="text-xs text-gray-600 mt-1">Your data looks good! Ready for preprocessing.</p>
                    </div>
                  )}
                </div>
              )}

              {!loading && tab === 'preprocessing' && (
                <div className="space-y-5">
                  <div className="rounded-xl border border-emerald-100 bg-gradient-to-br from-white to-emerald-50/50 p-4">
                    <h3 className="text-sm font-bold text-gray-900 mb-4 inline-flex items-center gap-2">
                      <SlidersHorizontal className="w-4 h-4 text-emerald-600" />
                      Data Cleaning Configuration
                    </h3>

                    <ConfigField label="Missing Value Strategy">
                      <select
                        value={missingStrategy}
                        onChange={(e) => setMissingStrategy(e.target.value)}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                      >
                        <option value="median">Median Imputation (numeric)</option>
                        <option value="mean">Mean Imputation (numeric)</option>
                        <option value="mode">Mode Imputation (categorical)</option>
                        <option value="drop">Drop Rows with Missing Values</option>
                        <option value="none">No Handling</option>
                      </select>
                    </ConfigField>

                    <ConfigField label="Outlier Handling">
                      <select
                        value={outlierStrategy}
                        onChange={(e) => setOutlierStrategy(e.target.value)}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                      >
                        <option value="winsorize">Winsorize at 1st/99th percentile</option>
                        <option value="remove">Remove outlier rows</option>
                        <option value="clip">Clip to threshold</option>
                        <option value="none">No Handling</option>
                      </select>
                    </ConfigField>

                    <ConfigField label="Normalization Method">
                      <select
                        value={normalizeMethod}
                        onChange={(e) => setNormalizeMethod(e.target.value)}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                        disabled={!enableStandardization}
                      >
                        <option value="standard">Standard Scaler (z-score)</option>
                        <option value="minmax">Min-Max Scaler (0-1)</option>
                        <option value="robust">Robust Scaler (median/IQR)</option>
                      </select>
                    </ConfigField>

                    <ConfigField label="Additional Options">
                      <label className="flex items-center gap-2 text-sm text-gray-700 mb-2">
                        <input 
                          type="checkbox" 
                          checked={removeDuplicates} 
                          onChange={(e) => setRemoveDuplicates(e.target.checked)} 
                        />
                        Remove duplicate rows
                      </label>
                      <label className="flex items-center gap-2 text-sm text-gray-700">
                        <input
                          type="checkbox"
                          checked={enableStandardization}
                          onChange={(e) => setEnableStandardization(e.target.checked)}
                        />
                        Apply normalization/standardization
                      </label>
                    </ConfigField>

                    <div className="mt-6 flex items-center gap-3">
                      <button 
                        onClick={handleApplyPreprocessing}
                        disabled={preprocessing || !sessionId}
                        className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 text-white text-sm font-semibold hover:from-emerald-700 hover:to-teal-700 transition-all disabled:opacity-50 inline-flex items-center gap-2"
                      >
                        {preprocessing ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Applying...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4" />
                            Apply Preprocessing
                          </>
                        )}
                      </button>

                      <p className="text-xs text-gray-600">
                        {preprocessing ? 'Processing data...' : 'Apply selected preprocessing operations'}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-xl border border-amber-100 bg-amber-50 p-4">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                      <div className="text-sm text-amber-800">
                        <p className="font-semibold mb-1">Preview Changes First</p>
                        <p>Preprocessing operations will modify your data. Review the preview tab to see changes before saving.</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {!loading && tab === 'preview' && (
                <div className="space-y-4">
                  {previewData && previewData.rows && previewData.rows.length > 0 ? (
                    <>
                      <div className="rounded-xl border border-gray-200 overflow-hidden">
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead className="bg-gray-900 text-white">
                              <tr>
                                {previewData.columns?.map((col) => (
                                  <th key={col} className="px-3 py-2 text-left whitespace-nowrap">
                                    {col}
                                  </th>
                                ))}
                                <th className="px-3 py-2 text-left">Actions</th>
                              </tr>
                            </thead>
                            <tbody className="bg-white">
                              {previewData.rows.map((row, rowIdx) => (
                                <tr key={row.staging_id || rowIdx} className="border-t border-gray-100 hover:bg-gray-50">
                                  {previewData.columns?.map((col) => (
                                    <td key={col} className="px-3 py-2 text-gray-700">
                                      {row[col]?.toString() || '-'}
                                    </td>
                                  ))}
                                  <td className="px-3 py-2">
                                    <button
                                      onClick={() => handleDeleteRow(row.staging_id)}
                                      className="text-red-600 hover:text-red-800 p-1"
                                      title="Delete row"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* Pagination */}
                      <div className="flex items-center justify-between">
                        <p className="text-sm text-gray-600">
                          Showing {((currentPage - 1) * rowsPerPage) + 1} to {Math.min(currentPage * rowsPerPage, totalRows)} of {totalRows} rows
                        </p>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              if (currentPage > 1) {
                                setCurrentPage(currentPage - 1);
                                loadPreview(sessionId, currentPage - 1);
                              }
                            }}
                            disabled={currentPage === 1}
                            className="px-3 py-1.5 rounded-lg border border-gray-300 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            Previous
                          </button>
                          <span className="text-sm text-gray-600">
                            Page {currentPage} of {Math.ceil(totalRows / rowsPerPage)}
                          </span>
                          <button
                            onClick={() => {
                              if (currentPage < Math.ceil(totalRows / rowsPerPage)) {
                                setCurrentPage(currentPage + 1);
                                loadPreview(sessionId, currentPage + 1);
                              }
                            }}
                            disabled={currentPage >= Math.ceil(totalRows / rowsPerPage)}
                            className="px-3 py-1.5 rounded-lg border border-gray-300 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            Next
                          </button>
                        </div>
                      </div>

                      {/* Save to Database Button */}
                      <div className="flex items-center justify-between p-4 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl border-2 border-emerald-200">
                        <div>
                          <p className="text-sm font-bold text-gray-900">Ready to save?</p>
                          <p className="text-xs text-gray-600 mt-0.5">
                            Save preprocessed data to database and continue to label assignment
                          </p>
                        </div>
                        <button
                          onClick={handleSaveToDatabase}
                          disabled={saving}
                          className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 text-white text-sm font-semibold shadow-lg hover:from-emerald-700 hover:to-teal-700 transition-all disabled:opacity-50 inline-flex items-center gap-2"
                        >
                          {saving ? (
                            <>
                              <Loader2 className="w-4 h-4 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            <>
                              <Save className="w-4 h-4" />
                              Save to Database
                            </>
                          )}
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-12 text-gray-500">
                      <p>No preview data available</p>
                    </div>
                  )}
                </div>
              )}

              {tab === 'reports' && (
                <div className="grid grid-cols-3 gap-4">
                  <ReportCard title="Data Quality Report" description="Missing values, outliers, format checks, and recommendations." action="Download PDF" icon={FileText} />
                  <ReportCard title="Transformation Summary" description="What changed before vs after cleaning and feature engineering." action="Download CSV" icon={Download} />
                  <ReportCard title="Model Readiness Snapshot" description="Trainability score and production readiness checklist." action="Export JSON" icon={Sparkles} />
                </div>
              )}
            </div>
          </section>
        </div>
      </main>
    </DashboardLayout>
  );
}

function SummaryCard({ icon: Icon, title, value, subtitle, accent }) {
  const accentMap = {
    emerald: 'from-emerald-500 to-teal-600',
    amber: 'from-amber-500 to-orange-600',
    indigo: 'from-indigo-500 to-violet-600',
  };

  return (
    <article className="rounded-xl border border-emerald-100 bg-gradient-to-br from-white to-emerald-50/60 p-4">
      <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${accentMap[accent]} text-white flex items-center justify-center mb-3`}>
        <Icon className="w-4.5 h-4.5" />
      </div>
      <p className="text-xs text-gray-600 font-semibold">{title}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </article>
  );
}

function ConfigField({ label, children }) {
  return (
    <div className="mb-4">
      <label className="block text-sm font-semibold text-gray-700 mb-1">{label}</label>
      {children}
    </div>
  );
}

function ReportCard({ title, description, action, icon: Icon }) {
  return (
    <div className="rounded-xl border border-emerald-100 bg-gradient-to-br from-white to-emerald-50/60 p-4">
      <div className="w-9 h-9 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center mb-3">
        <Icon className="w-4.5 h-4.5" />
      </div>
      <h3 className="text-sm font-bold text-gray-900">{title}</h3>
      <p className="text-xs text-gray-600 mt-1 min-h-[40px]">{description}</p>
      <button className="mt-3 px-3 py-2 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 transition-colors">
        {action}
      </button>
    </div>
  );
}
